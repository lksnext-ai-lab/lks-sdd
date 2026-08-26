from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str | None
    oidc_issuer: str | None
    oidc_audience: str
    entra_tenant_id: str | None
    required_scope: str
    required_role: str

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            environment=os.getenv("APP_ENV", "development"),
            database_url=os.getenv("DATABASE_URL"),
            oidc_issuer=os.getenv("OIDC_ISSUER"),
            oidc_audience=os.getenv("OIDC_AUDIENCE", "api://lks-sdd-reference-api"),
            entra_tenant_id=os.getenv("ENTRA_TENANT_ID"),
            required_scope=os.getenv("ENTRA_REQUIRED_SCOPE", "api.read"),
            required_role=os.getenv("ENTRA_REQUIRED_ROLE", "Api.Read.All"),
        )
