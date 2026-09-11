"""Real PostgreSQL security tests; no mocked session or permission repository."""
import base64
import concurrent.futures
import json
import secrets
import time
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from local_auth.main import COOKIE, app, engine, settings
from local_auth.security import HASH_POLICY, HASHER, password_hash, secret_hash

ORG = uuid.UUID("10000000-0000-4000-8000-000000000001")
OTHER_ORG = uuid.UUID("10000000-0000-4000-8000-000000000002")
USER = uuid.UUID("20000000-0000-4000-8000-000000000001")
PASSWORD = "Synthetic-test-only-credential-018"
HEADERS = {"Origin": settings.origin, "X-CSRF": "1", "Content-Type": "application/json"}


@pytest.fixture(autouse=True)
def database():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE auth_organizations,auth_users,auth_memberships,records,auth_sessions,auth_refresh_tokens,auth_recovery,auth_rate_limits,security_audit CASCADE"))
        conn.execute(text("INSERT INTO auth_organizations (id) VALUES (:id),(:other)"), {"id": ORG, "other": OTHER_ORG})
        conn.execute(text("INSERT INTO auth_users (id,username,password_hash,hash_policy) VALUES (:id,'synthetic-user',:hash,:policy)"),
                     {"id": USER, "hash": password_hash(PASSWORD), "policy": HASH_POLICY})
        conn.execute(text("INSERT INTO auth_memberships (user_id,org_id,permissions) VALUES (:id,:org,'[\"read\",\"write\",\"admin\"]'::jsonb)"), {"id": USER, "org": ORG})


def client():
    return TestClient(app, base_url=settings.origin, headers=HEADERS)


def sign_in(c, **changes):
    body = {"username": "synthetic-user", "password": PASSWORD, "organization": str(ORG)}
    body.update(changes)
    return c.post("/auth/login", json=body)


def bearer(c):
    response = sign_in(c)
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def sql(statement, **params):
    with engine.begin() as conn:
        return conn.execute(text(statement), params)


def test_argon2_policy_individual_salt_and_no_plaintext():
    first, second = password_hash(PASSWORD), password_hash(PASSWORD)
    assert first != second
    assert first.startswith("$argon2id$v=19$m=19456,t=2,p=1$")
    assert HASHER.verify(first, PASSWORD)
    with engine.connect() as conn:
        assert PASSWORD not in conn.execute(text("SELECT password_hash FROM auth_users")).scalar_one()


@pytest.mark.parametrize("name,value", [("LKS_AUTH_ENVIRONMENT", "production"), ("LKS_AUTH_ORIGIN", "http://localhost"),
                                        ("LKS_AUTH_ORIGIN", "https://localhost/path"), ("LKS_AUTH_AUDIENCE", "")])
def test_security_config_fails_closed(monkeypatch, name, value):
    from local_auth.security import Settings
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        Settings.load()


def test_body_limit_counts_bytes_without_trusting_content_length():
    c = client()
    response = c.post("/auth/login", content=iter([b"x" * 4096, b"x" * 4097]))
    assert response.status_code == 413
    assert "x" * 20 not in response.text


def test_hash_capacity_bounds_all_password_operations():
    from local_auth.security import HASH_SLOTS, HashCapacityExceeded, password_matches
    for _ in range(4):
        assert HASH_SLOTS.acquire(blocking=False)
    try:
        with pytest.raises(HashCapacityExceeded):
            password_hash(PASSWORD)
        with pytest.raises(HashCapacityExceeded):
            password_matches("untrusted-hash", PASSWORD)
    finally:
        for _ in range(4):
            HASH_SLOTS.release()


@pytest.mark.parametrize("condition", ["wrong-password", "unknown", "inactive-user", "inactive-membership", "inactive-org", "no-membership"])
def test_generic_login_denials(condition):
    changes = {}
    if condition == "wrong-password":
        changes["password"] = "wrong"
    elif condition == "unknown":
        changes["username"] = "does-not-exist"
    elif condition == "no-membership":
        sql("DELETE FROM auth_memberships")
    else:
        table = {"inactive-user": "auth_users", "inactive-membership": "auth_memberships", "inactive-org": "auth_organizations"}[condition]
        sql(f"UPDATE {table} SET active=false")
    response = sign_in(client(), **changes)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credential"}


def test_access_cookie_and_real_database_persistence():
    c = client()
    response = sign_in(c)
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=strict" in cookie
    token = c.cookies.get(COOKIE)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT token_hash FROM auth_refresh_tokens")).scalar_one() == secret_hash(token)
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    created = c.post("/records", headers=headers, json={"label": "persisted"})
    assert created.status_code == 201
    with engine.connect() as conn:
        assert conn.execute(text("SELECT label FROM records WHERE id=:id"), {"id": created.json()["id"]}).scalar_one() == "persisted"
    assert c.get("/records", headers=headers).json()[0]["label"] == "persisted"


@pytest.mark.parametrize("change", ["signature", "expired", "issuer", "audience", "subject", "missing", "type", "sid", "algorithm", "kid", "future", "lifetime"])
def test_invalid_tokens_are_rejected(change):
    c = client()
    raw = sign_in(c).json()["access_token"]
    keyring = json.loads(settings.keyring_file.read_text())
    kid = keyring["current"]
    key = base64.b64decode(keyring["keys"][kid])
    claims = jwt.decode(raw, options={"verify_signature": False})
    header = {"kid": kid, "typ": "JWT"}
    alg = "HS256"
    if change == "signature": key = secrets.token_bytes(32)
    elif change == "expired": claims["exp"] = int(time.time()) - 1
    elif change == "issuer": claims["iss"] = "another-issuer"
    elif change == "audience": claims["aud"] = "another-audience"
    elif change == "subject": claims["sub"] = str(uuid.uuid4())
    elif change == "missing": del claims["jti"]
    elif change == "type": claims["token_use"] = "refresh"
    elif change == "sid": claims["sid"] = str(uuid.uuid4())
    elif change == "algorithm": alg = "HS384"
    elif change == "kid": header["kid"] = "../../not-permitted"
    elif change == "future": claims["iat"] = int(time.time()) + 600
    elif change == "lifetime": claims["exp"] = claims["iat"] + 3600
    changed = jwt.encode(claims, key, algorithm=alg, headers=header)
    assert c.get("/auth/me", headers={"Authorization": "Bearer " + changed}).status_code == 401


def test_key_rotation_allows_known_previous_key_then_retires_it():
    original = settings.keyring_file.read_bytes()
    try:
        c = client()
        headers = bearer(c)
        ring = json.loads(original)
        ring["keys"]["next"] = base64.b64encode(secrets.token_bytes(32)).decode()
        previous = ring["current"]
        ring["current"] = "next"
        settings.keyring_file.write_text(json.dumps(ring))
        assert c.get("/auth/me", headers=headers).status_code == 200
        assert jwt.get_unverified_header(sign_in(c).json()["access_token"])["kid"] == "next"
        del ring["keys"][previous]
        settings.keyring_file.write_text(json.dumps(ring))
        assert c.get("/auth/me", headers=headers).status_code == 401
    finally:
        settings.keyring_file.write_bytes(original)


def test_refresh_rotation_and_replay_revoke_entire_family():
    c = client()
    headers = bearer(c)
    old = c.cookies.get(COOKIE)
    assert c.post("/auth/refresh", json={}).status_code == 200
    assert c.cookies.get(COOKIE) != old
    replay = client()
    replay.cookies.set(COOKIE, old)
    assert replay.post("/auth/refresh", json={}).status_code == 401
    assert c.get("/auth/me", headers=headers).status_code == 401
    assert c.post("/auth/refresh", json={}).status_code == 401


def test_simultaneous_refresh_has_one_rotation_and_replay_revocation():
    c = client()
    headers = bearer(c)
    old = c.cookies.get(COOKIE)
    def attempt(_):
        other = client()
        other.cookies.set(COOKIE, old)
        return other.post("/auth/refresh", json={}).status_code
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == [200, 401]
    assert c.get("/auth/me", headers=headers).status_code == 401


@pytest.mark.parametrize("expiration", ["absolute", "idle"])
def test_session_expiration(expiration):
    c = client()
    headers = bearer(c)
    sql("UPDATE auth_sessions SET " + ("expires_at=now()-interval '1 second'" if expiration == "absolute" else "last_seen=now()-interval '31 minutes'"))
    assert c.get("/auth/me", headers=headers).status_code == 401
    assert c.post("/auth/refresh", json={}).status_code == 401


def test_logout_idempotent_and_bearer_revoked():
    c = client()
    headers = bearer(c)
    assert c.post("/auth/logout", json={}).json() == {"revoked": True}
    assert c.post("/auth/logout", json={}).json() == {"revoked": True}
    assert c.get("/auth/me", headers=headers).status_code == 401


def test_live_permissions_membership_and_organization():
    c = client()
    headers = bearer(c)
    sql("UPDATE auth_memberships SET permissions='[\"read\"]'")
    assert c.post("/records", headers=headers, json={"label": "denied"}).status_code == 403
    assert c.get("/records", headers=headers).status_code == 200
    sql("UPDATE auth_memberships SET active=false")
    assert c.get("/records", headers=headers).status_code == 401
    sql("UPDATE auth_memberships SET active=true")
    sql("UPDATE auth_organizations SET active=false")
    assert c.get("/records", headers=headers).status_code == 401


def test_tenant_object_and_relationship_isolation():
    foreign = uuid.uuid4()
    sql("INSERT INTO records (id,org_id,label) VALUES (:id,:org,'foreign')", id=foreign, org=OTHER_ORG)
    c = client()
    headers = bearer(c)
    assert c.get("/records", headers=headers).json() == []
    assert c.get(f"/records/{foreign}", headers=headers).status_code == 404
    assert c.post("/records", headers=headers, json={"label": "cross-link", "parent_id": str(foreign)}).status_code == 404


def test_password_change_requires_reauth_and_invalidates_sessions():
    c = client()
    headers = bearer(c)
    assert c.post("/auth/password", headers=headers, json={"current_password": "wrong", "new_password": PASSWORD + "new"}).status_code == 401
    assert c.post("/auth/password", headers=headers, json={"current_password": PASSWORD, "new_password": PASSWORD + "new"}).status_code == 200
    assert c.get("/auth/me", headers=headers).status_code == 401
    assert sign_in(client(), password=PASSWORD + "new").status_code == 200


def test_admin_provision_recovery_once_and_disable():
    c = client()
    headers = bearer(c)
    created = c.post("/admin/users", headers=headers, json={"username": "another", "password": PASSWORD, "current_password": PASSWORD})
    assert created.status_code == 201
    target = created.json()["id"]
    recovery = c.post(f"/admin/users/{target}/recovery", headers=headers, json={})
    assert recovery.status_code == 200
    body = {"token": recovery.json()["recovery_token"], "new_password": PASSWORD + "new"}
    assert client().post("/auth/recovery", json=body).status_code == 200
    assert client().post("/auth/recovery", json=body).status_code == 401
    assert c.post(f"/admin/users/{target}/disable", headers=headers, json={}).status_code == 200
    assert sign_in(client(), username="another", password=PASSWORD + "new").status_code == 401


def test_csrf_origin_and_content_type_fail_closed():
    c = client()
    bearer(c)
    for headers in [{"Origin": "https://evil.invalid"}, {"X-CSRF": ""}, {"Content-Type": "text/plain"}]:
        assert c.post("/auth/refresh", headers=headers, json={}).status_code in {403, 415}
    assert c.post("/auth/login", headers={"Origin": "null"}, json={}).status_code == 403


def test_concurrent_login_abuse_is_bounded():
    def attempt(_):
        return sign_in(client(), password="wrong").status_code
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        statuses = list(pool.map(attempt, range(20)))
    assert set(statuses) <= {401, 429}
    assert statuses.count(429) >= 12


def test_validation_and_audit_exclude_credentials():
    c = client()
    response = sign_in(c, password=PASSWORD * 10)
    assert response.status_code == 422
    assert PASSWORD not in response.text
    bearer(c)
    with engine.connect() as conn:
        events = conn.execute(text("SELECT event FROM security_audit")).scalars().all()
    assert events and all(event in {"login-succeeded", "login-denied"} for event in events)
