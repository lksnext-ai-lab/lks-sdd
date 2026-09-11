from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str | None
    oidc_issuer: str | None
    oidc_jwks_url: str | None
    oidc_audience: str

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            environment=os.getenv("APP_ENV", "development"),
            database_url=os.getenv("DATABASE_URL"),
            oidc_issuer=os.getenv("OIDC_ISSUER"),
            oidc_jwks_url=os.getenv("OIDC_JWKS_URL"),
            oidc_audience=os.getenv("OIDC_AUDIENCE", "lks-sdd-api"),
        )
