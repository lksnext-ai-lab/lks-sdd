"""Real PostgreSQL local authentication reference. No in-memory data fallback."""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from .body_limit import BodyLimit

from .security import (
    ABSOLUTE_SECONDS, DUMMY_HASH, HASHER, HASH_POLICY, IDLE_SECONDS, HashCapacityExceeded,
    Settings, access_token, bucket, decode_access, password_hash, password_matches, secret_hash,
)

COOKIE = "__Host-lks-refresh"
settings = Settings.load()
engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=3,
                       connect_args={"connect_timeout": 3, "options": "-c statement_timeout=5000 -c lock_timeout=3000"},
                       hide_parameters=True)
app = FastAPI(title="LKS-SDD isolated local-auth reference", debug=False)
app.add_middleware(BodyLimit)
app.add_middleware(CORSMiddleware, allow_origins=[settings.origin], allow_credentials=True,
                   allow_methods=["GET", "POST", "PATCH", "DELETE"],
                   allow_headers=["Authorization", "Content-Type", "X-CSRF"])


@app.exception_handler(SQLAlchemyError)
def database_unavailable(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    return JSONResponse({"detail": "Service unavailable"}, status_code=503)


@app.exception_handler(HashCapacityExceeded)
def hash_capacity_unavailable(request: Request, exc: HashCapacityExceeded) -> JSONResponse:
    return JSONResponse({"detail": "Try again later"}, status_code=429)


@app.exception_handler(RequestValidationError)
def invalid_input(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Pydantic's default errors may echo password/token values. Never return them.
    return JSONResponse({"detail": "Invalid request"}, status_code=422)


@app.middleware("http")
async def security_headers(request: Request, call_next: Any) -> Response:
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def csrf(request: Request) -> None:
    if request.headers.get("origin") != settings.origin or request.headers.get("x-csrf") != "1":
        raise HTTPException(403, "Request origin rejected")
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise HTTPException(415, "JSON required")


def audit(connection: Any, event: str) -> None:
    # Allowlisted event names only. No password, bearer, cookie, body or headers.
    connection.execute(text("INSERT INTO security_audit (event) VALUES (:event)"), {"event": event})


def refresh_cookie(response: Response, value: str) -> None:
    response.set_cookie(COOKIE, value, max_age=ABSOLUTE_SECONDS, httponly=True, secure=True, samesite="strict", path="/")


def authenticate(request: Request) -> dict[str, Any]:
    raw = request.headers.get("authorization", "")
    if not raw.startswith("Bearer "):
        raise HTTPException(401, "Invalid credential")
    try:
        claims = decode_access(settings, raw[7:])
        # Typed identifiers prevent malformed values reaching PostgreSQL casts.
        for field in ("sub", "sid", "org"):
            uuid.UUID(claims[field])
    except (jwt.PyJWTError, ValueError, KeyError, OSError):
        raise HTTPException(401, "Invalid credential") from None
    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT s.id, s.user_id, s.org_id, m.permissions, u.password_hash
            FROM auth_sessions s JOIN auth_users u ON u.id=s.user_id
            JOIN auth_memberships m ON m.user_id=s.user_id AND m.org_id=s.org_id
            JOIN auth_organizations o ON o.id=s.org_id
            WHERE s.id=:sid AND s.user_id=:sub AND s.org_id=:org
              AND s.revoked=false AND u.active AND m.active AND o.active
              AND s.expires_at>now() AND s.last_seen>now()-interval '30 minutes'
        """), claims).mappings().first()
        if row is None:
            raise HTTPException(401, "Invalid credential")
        conn.execute(text("UPDATE auth_sessions SET last_seen=now() WHERE id=:sid"), claims)
        return dict(row)


def require_permission(user: dict[str, Any], permission: str) -> None:
    if permission not in user["permissions"]:
        raise HTTPException(403, "Access denied")


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: SecretStr = Field(max_length=128)
    organization: uuid.UUID


class PasswordChange(BaseModel):
    current_password: SecretStr = Field(max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)


class Recovery(BaseModel):
    token: SecretStr = Field(min_length=32, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)


class NewUser(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: SecretStr = Field(min_length=12, max_length=128)
    current_password: SecretStr = Field(max_length=128)


class Record(BaseModel):
    label: str = Field(min_length=1, max_length=160)
    parent_id: uuid.UUID | None = None


def rate_limit(request: Request, username: str) -> None:
    peer = request.client.host if request.client else "unknown"
    # Do not trust X-Forwarded-For from the requester. Per-account limits remain
    # effective behind the isolated reverse proxy; global/origin bound the load.
    over_limit = False
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM auth_rate_limits WHERE window_start < now()-interval '2 minutes'"))
        for key, limit in [("global", 120), (bucket(settings, "origin:" + peer), 40), (bucket(settings, "account:" + username), 8)]:
            count = conn.execute(text("""
                INSERT INTO auth_rate_limits (key, attempts, window_start) VALUES (:key, 1, now())
                ON CONFLICT (key) DO UPDATE SET
                  attempts=CASE WHEN auth_rate_limits.window_start<now()-interval '1 minute' THEN 1 ELSE auth_rate_limits.attempts+1 END,
                  window_start=CASE WHEN auth_rate_limits.window_start<now()-interval '1 minute' THEN now() ELSE auth_rate_limits.window_start END
                RETURNING attempts
            """), {"key": key}).scalar_one()
            if count > limit:
                over_limit = True
                break
    if over_limit:
        raise HTTPException(429, "Try again later")


@app.post("/auth/login", dependencies=[Depends(csrf)])
def login(body: Login, request: Request, response: Response) -> dict[str, Any]:
    rate_limit(request, body.username)
    with engine.begin() as conn:
        user = conn.execute(text("""
            SELECT u.*, m.org_id FROM auth_users u
            JOIN auth_memberships m ON u.id=m.user_id JOIN auth_organizations o ON o.id=m.org_id
            WHERE lower(u.username)=:name AND m.org_id=:org AND u.active AND m.active AND o.active
            FOR UPDATE OF u
        """), {"name": body.username.lower(), "org": body.organization}).mappings().first()
        valid = password_matches(user["password_hash"] if user else DUMMY_HASH, body.password.get_secret_value())
        if not valid or user is None:
            audit(conn, "login-denied")
            failure = True
        else:
            failure = False
            sid, token = uuid.uuid4(), secrets.token_urlsafe(48)
            session = {"id": sid, "user_id": user["id"], "org_id": body.organization}
            conn.execute(text("""INSERT INTO auth_sessions (id,user_id,org_id,expires_at)
                VALUES (:id,:user_id,:org_id,now()+interval '8 hours')"""), session)
            conn.execute(text("INSERT INTO auth_refresh_tokens (token_hash,session_id) VALUES (:hash,:sid)"),
                         {"hash": secret_hash(token), "sid": sid})
            if HASHER.check_needs_rehash(user["password_hash"]):
                conn.execute(text("UPDATE auth_users SET password_hash=:hash, hash_policy=:policy WHERE id=:id"),
                             {"hash": password_hash(body.password.get_secret_value()), "policy": HASH_POLICY, "id": user["id"]})
            audit(conn, "login-succeeded")
    if failure:
        raise HTTPException(401, "Invalid credential")
    refresh_cookie(response, token)
    return {"access_token": access_token(settings, session), "token_type": "bearer", "expires_in": 900}


@app.post("/auth/refresh", dependencies=[Depends(csrf)])
def refresh(request: Request, response: Response) -> dict[str, Any]:
    token = request.cookies.get(COOKIE, "")
    if not 32 <= len(token) <= 128:
        raise HTTPException(401, "Invalid credential")
    denied = True
    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT t.consumed, s.*, u.active AS user_active, m.active AS member_active, o.active AS org_active
            FROM auth_refresh_tokens t JOIN auth_sessions s ON s.id=t.session_id
            JOIN auth_users u ON u.id=s.user_id
            JOIN auth_memberships m ON m.user_id=s.user_id AND m.org_id=s.org_id
            JOIN auth_organizations o ON o.id=s.org_id
            WHERE t.token_hash=:hash FOR UPDATE OF t,s,u
        """), {"hash": secret_hash(token)}).mappings().first()
        now = datetime.now(timezone.utc)
        if row and row["consumed"]:
            conn.execute(text("UPDATE auth_sessions SET revoked=true WHERE id=:id"), {"id": row["id"]})
            audit(conn, "refresh-reuse-revoked")
        elif row and not row["revoked"] and row["user_active"] and row["member_active"] and row["org_active"] and row["expires_at"] > now and row["last_seen"] > now-timedelta(seconds=IDLE_SECONDS):
            denied = False
            replacement = secrets.token_urlsafe(48)
            conn.execute(text("UPDATE auth_refresh_tokens SET consumed=true WHERE token_hash=:hash"), {"hash": secret_hash(token)})
            conn.execute(text("INSERT INTO auth_refresh_tokens (token_hash,session_id) VALUES (:hash,:sid)"),
                         {"hash": secret_hash(replacement), "sid": row["id"]})
            conn.execute(text("UPDATE auth_sessions SET last_seen=now() WHERE id=:id"), {"id": row["id"]})
            audit(conn, "refresh-rotated")
            session = dict(row)
    if denied:
        raise HTTPException(401, "Invalid credential")
    refresh_cookie(response, replacement)
    return {"access_token": access_token(settings, session), "token_type": "bearer", "expires_in": 900}


@app.post("/auth/logout", dependencies=[Depends(csrf)])
def logout(request: Request, response: Response) -> dict[str, bool]:
    token = request.cookies.get(COOKIE, "")
    with engine.begin() as conn:
        conn.execute(text("""UPDATE auth_sessions SET revoked=true WHERE id IN
            (SELECT session_id FROM auth_refresh_tokens WHERE token_hash=:hash)"""), {"hash": secret_hash(token)})
        audit(conn, "logout")
    response.delete_cookie(COOKIE, httponly=True, secure=True, samesite="strict", path="/")
    return {"revoked": True}


@app.get("/auth/me")
def me(user: dict[str, Any] = Depends(authenticate)) -> dict[str, Any]:
    return {"user_id": str(user["user_id"]), "organization": str(user["org_id"]), "permissions": user["permissions"]}


@app.post("/auth/password", dependencies=[Depends(csrf)])
def change_password(body: PasswordChange, user: dict[str, Any] = Depends(authenticate)) -> dict[str, bool]:
    with engine.begin() as conn:
        current = conn.execute(text("SELECT password_hash FROM auth_users WHERE id=:id FOR UPDATE"), {"id": user["user_id"]}).scalar_one()
        if not password_matches(current, body.current_password.get_secret_value()):
            raise HTTPException(401, "Invalid credential")
        conn.execute(text("UPDATE auth_users SET password_hash=:hash, hash_policy=:policy WHERE id=:id"),
                     {"id": user["user_id"], "hash": password_hash(body.new_password.get_secret_value()), "policy": HASH_POLICY})
        conn.execute(text("UPDATE auth_sessions SET revoked=true WHERE user_id=:id"), {"id": user["user_id"]})
        audit(conn, "password-changed")
    return {"sessions_revoked": True}


@app.post("/admin/users", dependencies=[Depends(csrf)], status_code=201)
def create_user(body: NewUser, user: dict[str, Any] = Depends(authenticate)) -> dict[str, str]:
    require_permission(user, "admin")
    if not password_matches(user["password_hash"], body.current_password.get_secret_value()):
        raise HTTPException(401, "Invalid credential")
    identifier = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO auth_users (id,username,password_hash,hash_policy) VALUES (:id,:name,:hash,:policy)"),
                     {"id": identifier, "name": body.username.lower(), "hash": password_hash(body.password.get_secret_value()), "policy": HASH_POLICY})
        conn.execute(text("INSERT INTO auth_memberships (user_id,org_id,permissions) VALUES (:id,:org,'[\"read\"]'::jsonb)"), {"id": identifier, "org": user["org_id"]})
        audit(conn, "user-provisioned")
    return {"id": str(identifier)}


def managed_user(conn: Any, target: uuid.UUID, user: dict[str, Any]) -> None:
    require_permission(user, "admin")
    member = conn.execute(text("SELECT 1 FROM auth_memberships WHERE user_id=:id AND org_id=:org"), {"id": target, "org": user["org_id"]}).first()
    if member is None:
        raise HTTPException(404, "Not found")
    if conn.execute(text("SELECT 1 FROM auth_memberships WHERE user_id=:id AND org_id<>:org"), {"id": target, "org": user["org_id"]}).first():
        raise HTTPException(403, "Cross-organization account administration requires a separate operator process")


@app.post("/admin/users/{target}/disable", dependencies=[Depends(csrf)])
def disable_user(target: uuid.UUID, user: dict[str, Any] = Depends(authenticate)) -> dict[str, bool]:
    with engine.begin() as conn:
        managed_user(conn, target, user)
        conn.execute(text("UPDATE auth_users SET active=false WHERE id=:id"), {"id": target})
        conn.execute(text("UPDATE auth_sessions SET revoked=true WHERE user_id=:id"), {"id": target})
        audit(conn, "user-disabled")
    return {"disabled": True}


@app.post("/admin/users/{target}/recovery", dependencies=[Depends(csrf)])
def issue_recovery(target: uuid.UUID, user: dict[str, Any] = Depends(authenticate)) -> dict[str, str]:
    token = secrets.token_urlsafe(48)
    with engine.begin() as conn:
        managed_user(conn, target, user)
        conn.execute(text("UPDATE auth_recovery SET consumed=true WHERE user_id=:id"), {"id": target})
        conn.execute(text("INSERT INTO auth_recovery (token_hash,user_id,expires_at) VALUES (:hash,:id,now()+interval '15 minutes')"), {"hash": secret_hash(token), "id": target})
        audit(conn, "recovery-issued")
    return {"recovery_token": token}


@app.post("/auth/recovery", dependencies=[Depends(csrf)])
def recover(body: Recovery) -> dict[str, bool]:
    with engine.begin() as conn:
        row = conn.execute(text("""SELECT r.user_id FROM auth_recovery r JOIN auth_users u ON u.id=r.user_id
            WHERE token_hash=:hash AND NOT consumed AND expires_at>now() AND u.active FOR UPDATE OF r,u"""), {"hash": secret_hash(body.token.get_secret_value())}).first()
        if row is None:
            raise HTTPException(401, "Invalid credential")
        conn.execute(text("UPDATE auth_recovery SET consumed=true WHERE user_id=:id"), {"id": row[0]})
        conn.execute(text("UPDATE auth_users SET password_hash=:hash,hash_policy=:policy WHERE id=:id"),
                     {"hash": password_hash(body.new_password.get_secret_value()), "policy": HASH_POLICY, "id": row[0]})
        conn.execute(text("UPDATE auth_sessions SET revoked=true WHERE user_id=:id"), {"id": row[0]})
        audit(conn, "recovery-used")
    return {"sessions_revoked": True}


@app.get("/records")
def records(user: dict[str, Any] = Depends(authenticate)) -> list[dict[str, Any]]:
    require_permission(user, "read")
    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(text("SELECT id,label,parent_id FROM records WHERE org_id=:org ORDER BY id"), {"org": user["org_id"]}).mappings()]


@app.get("/records/{identifier}")
def record(identifier: uuid.UUID, user: dict[str, Any] = Depends(authenticate)) -> dict[str, Any]:
    require_permission(user, "read")
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id,label,parent_id FROM records WHERE id=:id AND org_id=:org"), {"id": identifier, "org": user["org_id"]}).mappings().first()
        if row is None:
            raise HTTPException(404, "Not found")
        return dict(row)


@app.post("/records", status_code=201)
def create_record(body: Record, user: dict[str, Any] = Depends(authenticate)) -> dict[str, Any]:
    require_permission(user, "write")
    with engine.begin() as conn:
        if body.parent_id and conn.execute(text("SELECT 1 FROM records WHERE id=:id AND org_id=:org"), {"id": body.parent_id, "org": user["org_id"]}).first() is None:
            raise HTTPException(404, "Not found")
        identifier = uuid.uuid4()
        conn.execute(text("INSERT INTO records (id,org_id,label,parent_id) VALUES (:id,:org,:label,:parent)"),
                     {"id": identifier, "org": user["org_id"], "label": body.label, "parent": body.parent_id})
    return {"id": str(identifier), "label": body.label, "parent_id": str(body.parent_id) if body.parent_id else None}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/ready")
def ready() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1 FROM alembic_version"))
    return {"status": "ready"}
