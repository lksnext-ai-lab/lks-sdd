from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings
from .security import decode_access_token

app = FastAPI(
    title="LKS-SDD reference API",
    version="0.1.0",
    openapi_version="3.1.0",
)
bearer = HTTPBearer(auto_error=True)


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
def readiness() -> dict[str, object]:
    return {"status": "ready", "checks": [{"name": "api", "status": "ready"}]}


@app.get("/api/v1/me", tags=["identity"])
def me(user: Annotated[dict[str, Any], Depends(current_user)]) -> dict[str, str | None]:
    return {
        "subject": str(user["sub"]),
        "username": user.get("preferred_username"),
    }
