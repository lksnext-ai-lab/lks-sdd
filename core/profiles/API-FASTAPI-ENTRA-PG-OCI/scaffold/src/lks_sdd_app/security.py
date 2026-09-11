from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jwt import PyJWKClient

from .config import Settings

TENANT_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def discovery_url(issuer: str) -> str:
    return f"{issuer.rstrip('/')}/.well-known/openid-configuration"


def expected_entra_issuer(tenant_id: str) -> str:
    if not TENANT_ID_RE.fullmatch(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Microsoft Entra tenant ID is invalid",
        )
    return f"https://login.microsoftonline.com/{tenant_id}/v2.0"


def fetch_oidc_metadata(issuer: str) -> dict[str, Any]:
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(discovery_url(issuer), timeout=10) as response:
            metadata = json.load(response)
    except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC discovery is unavailable",
        ) from exc
    if not isinstance(metadata, dict):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC discovery is invalid",
        )
    return metadata


def authorize_claims(payload: dict[str, Any], settings: Settings) -> None:
    if not settings.entra_tenant_id or payload.get("tid") != settings.entra_tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong tenant")
    scopes = set(str(payload.get("scp", "")).split())
    roles_value = payload.get("roles", [])
    roles = set(roles_value) if isinstance(roles_value, list) else set()
    if settings.required_scope not in scopes and settings.required_role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Required scope or application role is missing",
        )


def decode_access_token(
    credentials: HTTPAuthorizationCredentials,
    settings: Settings,
) -> dict[str, Any]:
    if not settings.oidc_issuer or not settings.entra_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Microsoft Entra identity is not configured",
        )
    if settings.oidc_issuer != expected_entra_issuer(settings.entra_tenant_id):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Microsoft Entra issuer does not match the configured tenant",
        )
    try:
        metadata = fetch_oidc_metadata(settings.oidc_issuer)
        if metadata.get("issuer") != settings.oidc_issuer:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC discovery issuer mismatch",
            )
        jwks_uri = metadata.get("jwks_uri")
        if not isinstance(jwks_uri, str) or not jwks_uri.startswith("https://"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC discovery jwks_uri is invalid",
            )
        client = PyJWKClient(jwks_uri)
        signing_key = client.get_signing_key_from_jwt(credentials.credentials)
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
            options={"require": ["exp", "iss", "aud", "sub", "tid"]},
        )
        result = dict(payload)
        authorize_claims(result, settings)
        return result
    except HTTPException:
        raise
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
