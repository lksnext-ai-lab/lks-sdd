from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import time
from dataclasses import dataclass
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jwt.algorithms import RSAAlgorithm

from .config import Settings, canonical_simulated_oidc_issuer

KEY_ID = "lks-sdd-simulated-oidc"
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_KEY = PRIVATE_KEY.public_key()
PKCE_VERIFIER_RE = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")


@dataclass(frozen=True)
class PendingAuthorization:
    challenge: str
    subject: str
    object_id: str
    username: str
    scopes: tuple[str, ...]
    roles: tuple[str, ...]
    issued_at: int


_authorization_codes: dict[str, PendingAuthorization] = {}


def require_simulated_identity(settings: Settings) -> str:
    if not settings.simulated_identity_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulated identity is disabled outside explicit non-production environments",
        )
    try:
        return canonical_simulated_oidc_issuer(settings.oidc_issuer)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulated identity configuration is invalid",
        ) from exc


def _challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def discovery_document(settings: Settings) -> dict[str, Any]:
    issuer = require_simulated_identity(settings)
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/authorize",
        "token_endpoint": f"{issuer}/token",
        "jwks_uri": f"{issuer}/jwks",
        "response_types_supported": ["code"],
        "code_challenge_methods_supported": ["S256"],
        "id_token_signing_alg_values_supported": ["RS256"],
    }


def jwks_document(settings: Settings) -> dict[str, Any]:
    require_simulated_identity(settings)
    key = json.loads(RSAAlgorithm.to_jwk(PUBLIC_KEY))
    key.update({"kid": KEY_ID, "use": "sig", "alg": "RS256"})
    return {"keys": [key]}


def begin_authorization(
    settings: Settings,
    *,
    subject: str,
    object_id: str,
    username: str,
    code_challenge: str,
    scopes: list[str],
    roles: list[str],
) -> str:
    require_simulated_identity(settings)
    if (
        subject != settings.simulated_subject_id
        or object_id != settings.simulated_object_id
        or username != settings.simulated_username
    ):
        raise HTTPException(
            status_code=400,
            detail="Synthetic identity must match the configured stable fixture",
        )
    if len(code_challenge) != 43 or not code_challenge.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="A valid S256 code challenge is required")
    code = secrets.token_urlsafe(32)
    _authorization_codes[code] = PendingAuthorization(
        challenge=code_challenge,
        subject=subject,
        object_id=object_id,
        username=username,
        scopes=tuple(scopes),
        roles=tuple(roles),
        issued_at=int(time.time()),
    )
    return code


def exchange_code(settings: Settings, *, code: str, code_verifier: str) -> str:
    issuer = require_simulated_identity(settings)
    pending = _authorization_codes.pop(code, None)
    if pending is None or int(time.time()) - pending.issued_at > 120:
        raise HTTPException(status_code=400, detail="Authorization code is invalid or expired")
    if PKCE_VERIFIER_RE.fullmatch(code_verifier) is None:
        raise HTTPException(status_code=400, detail="A valid PKCE code verifier is required")
    if not secrets.compare_digest(_challenge(code_verifier), pending.challenge):
        raise HTTPException(status_code=400, detail="PKCE verification failed")
    now = int(time.time())
    payload = {
        "iss": issuer,
        "aud": settings.oidc_audience,
        "sub": pending.subject,
        "oid": pending.object_id,
        "tid": settings.simulated_tenant_id,
        "preferred_username": pending.username,
        "scp": " ".join(pending.scopes),
        "roles": list(pending.roles),
        "iat": now,
        "nbf": now,
        "exp": now + 300,
        "synthetic": True,
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256", headers={"kid": KEY_ID})


def authorize_claims(payload: dict[str, Any], settings: Settings) -> None:
    if payload.get("tid") != settings.simulated_tenant_id:
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
    issuer = require_simulated_identity(settings)
    try:
        payload = jwt.decode(
            credentials.credentials,
            PUBLIC_KEY,
            algorithms=["RS256"],
            audience=settings.oidc_audience,
            issuer=issuer,
            options={"require": ["exp", "iss", "aud", "sub", "oid", "tid"]},
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
