"""Local credential and token primitives; never log supplied credentials."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError

HASH_POLICY = "argon2id-v1-m19456-t2-p1"
HASHER = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1, hash_len=32, salt_len=16, type=Type.ID)
HASH_SLOTS = threading.BoundedSemaphore(4)
DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(32))
ACCESS_SECONDS = 900
ABSOLUTE_SECONDS = 8 * 3600
IDLE_SECONDS = 30 * 60


class HashCapacityExceeded(Exception):
    """The shared bounded password-work capacity is exhausted."""


@dataclass(frozen=True)
class Settings:
    database_url: str
    keyring_file: Path
    issuer: str
    audience: str
    origin: str
    environment: str

    @classmethod
    def load(cls) -> Settings:
        environment = os.environ.get("LKS_AUTH_ENVIRONMENT", "")
        if environment not in {"isolated-development", "ci"}:
            raise ValueError("This profile is certified only for isolated development and CI")
        origin = os.environ["LKS_AUTH_ORIGIN"]
        from urllib.parse import urlsplit
        parsed = urlsplit(origin)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("An exact HTTPS origin is required")
        settings = cls(os.environ["DATABASE_URL"], Path(os.environ["LKS_AUTH_KEYRING_FILE"]),
                       os.environ["LKS_AUTH_ISSUER"], os.environ["LKS_AUTH_AUDIENCE"], origin.rstrip("/"), environment)
        if not settings.database_url.startswith("postgresql+psycopg://") or not settings.issuer or not settings.audience:
            raise ValueError("Explicit PostgreSQL and token configuration is required")
        keyring(settings)
        return settings


def keyring(settings: Settings) -> tuple[str, dict[str, bytes]]:
    raw = json.loads(settings.keyring_file.read_text(encoding="utf-8"))
    current, keys = raw["current"], raw["keys"]
    if not isinstance(keys, dict) or not 1 <= len(keys) <= 5:
        raise ValueError("Invalid keyring")
    decoded = {}
    for kid, value in keys.items():
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", kid):
            raise ValueError("Invalid key identifier")
        key = base64.b64decode(value, validate=True)
        if len(key) < 32:
            raise ValueError("Signing keys require at least 256 bits")
        decoded[kid] = key
    if current not in decoded:
        raise ValueError("Missing current signing key")
    return current, decoded


def secret_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def password_hash(password: str) -> str:
    if not 12 <= len(password) <= 128:
        raise ValueError("Password length must be between 12 and 128 characters")
    if not HASH_SLOTS.acquire(blocking=False):
        raise HashCapacityExceeded()
    try:
        return HASHER.hash(password)
    finally:
        HASH_SLOTS.release()


def password_matches(stored: str, password: str) -> bool:
    if not isinstance(password, str) or len(password) > 128:
        return False
    if not HASH_SLOTS.acquire(blocking=False):
        raise HashCapacityExceeded()
    try:
        return HASHER.verify(stored, password)
    except (VerificationError, InvalidHashError):
        return False
    finally:
        HASH_SLOTS.release()


def bucket(settings: Settings, label: str) -> str:
    _, keys = keyring(settings)
    # Rate identifiers are never emitted. Rotating signing keys starts a new
    # bounded rate window, while the global bucket remains unchanged.
    return hmac.new(keys[sorted(keys)[0]], label.casefold().encode(), hashlib.sha256).hexdigest()


def access_token(settings: Settings, session: dict[str, Any]) -> str:
    now = int(datetime.now(timezone.utc).timestamp())
    kid, keys = keyring(settings)
    return jwt.encode({"iss": settings.issuer, "aud": settings.audience, "sub": str(session["user_id"]),
                       "sid": str(session["id"]), "org": str(session["org_id"]), "jti": secrets.token_hex(16),
                       "iat": now, "nbf": now, "exp": now + ACCESS_SECONDS, "token_use": "access"},
                      keys[kid], algorithm="HS256", headers={"kid": kid, "typ": "JWT"})


def decode_access(settings: Settings, token: str) -> dict[str, Any]:
    if len(token) > 4096:
        raise ValueError("Invalid credential")
    header = jwt.get_unverified_header(token)
    _, keys = keyring(settings)
    if set(header) - {"alg", "kid", "typ"} or header.get("alg") != "HS256" or header.get("typ") != "JWT" or header.get("kid") not in keys:
        raise ValueError("Invalid credential")
    claims = jwt.decode(token, keys[header["kid"]], algorithms=["HS256"], issuer=settings.issuer,
                        audience=settings.audience, options={"require": ["iss", "aud", "sub", "sid", "org", "jti", "iat", "nbf", "exp", "token_use"]})
    if claims["token_use"] != "access" or not all(isinstance(claims[k], str) and claims[k] for k in ("sub", "sid", "org", "jti")):
        raise ValueError("Invalid credential")
    if not all(type(claims[k]) is int for k in ("iat", "nbf", "exp")) or claims["exp"] - claims["iat"] > ACCESS_SECONDS or claims["exp"] <= claims["iat"]:
        raise ValueError("Invalid credential")
    return claims
