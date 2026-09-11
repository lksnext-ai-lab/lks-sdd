from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .config import Settings
from .security import (
    begin_authorization,
    decode_access_token,
    discovery_document,
    exchange_code,
    jwks_document,
    require_simulated_identity,
)

app = FastAPI(
    title="LKS-SDD simulated OIDC reference API",
    version="0.1.0",
    openapi_version="3.1.0",
)
bearer = HTTPBearer(auto_error=True)


class AuthorizationRequest(BaseModel):
    subject: str = "synthetic-user"
    object_id: str = "synthetic-object-001"
    username: str = "synthetic.user@example.invalid"
    code_challenge: str = Field(min_length=43, max_length=43)
    code_challenge_method: str = "S256"
    scopes: list[str] = Field(default_factory=lambda: ["api.read"])
    roles: list[str] = Field(default_factory=list)


class TokenRequest(BaseModel):
    code: str
    code_verifier: str = Field(min_length=43, max_length=128)


def current_settings() -> Settings:
    return Settings.from_environment()


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    settings: Annotated[Settings, Depends(current_settings)],
) -> dict[str, Any]:
    return decode_access_token(credentials, settings)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
def readiness(
    settings: Annotated[Settings, Depends(current_settings)],
) -> dict[str, object]:
    require_simulated_identity(settings)
    return {"status": "ready", "checks": [{"name": "api", "status": "ready"}]}


@app.get("/__test__/oidc/.well-known/openid-configuration", tags=["test-identity"])
def discovery(settings: Annotated[Settings, Depends(current_settings)]) -> dict[str, Any]:
    return discovery_document(settings)


@app.get("/__test__/oidc/jwks", tags=["test-identity"])
def jwks(settings: Annotated[Settings, Depends(current_settings)]) -> dict[str, Any]:
    return jwks_document(settings)


@app.post("/__test__/oidc/authorize", tags=["test-identity"])
def authorize(
    request: AuthorizationRequest,
    settings: Annotated[Settings, Depends(current_settings)],
) -> dict[str, str]:
    if request.code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="only S256 is supported")
    return {
        "code": begin_authorization(
            settings,
            subject=request.subject,
            object_id=request.object_id,
            username=request.username,
            code_challenge=request.code_challenge,
            scopes=request.scopes,
            roles=request.roles,
        )
    }


@app.post("/__test__/oidc/token", tags=["test-identity"])
def token(
    request: TokenRequest,
    settings: Annotated[Settings, Depends(current_settings)],
) -> dict[str, str | int]:
    return {
        "access_token": exchange_code(
            settings, code=request.code, code_verifier=request.code_verifier
        ),
        "token_type": "Bearer",
        "expires_in": 300,
    }


@app.get("/api/v1/me", tags=["identity"])
def me(user: Annotated[dict[str, Any], Depends(current_user)]) -> dict[str, str | None]:
    return {
        "subject": str(user["sub"]),
        "object_id": str(user["oid"]),
        "username": user.get("preferred_username"),
        "tenant": str(user["tid"]),
    }
