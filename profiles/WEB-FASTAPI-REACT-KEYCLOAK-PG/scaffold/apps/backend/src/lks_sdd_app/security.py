from __future__ import annotations

from typing import Any

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jwt import PyJWKClient

from .config import Settings


def decode_access_token(
    credentials: HTTPAuthorizationCredentials,
    settings: Settings,
) -> dict[str, Any]:
    if not settings.oidc_issuer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC issuer is not configured",
        )
    try:
        client = PyJWKClient(f"{settings.oidc_issuer.rstrip('/')}/protocol/openid-connect/certs")
        signing_key = client.get_signing_key_from_jwt(credentials.credentials)
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return dict(payload)
