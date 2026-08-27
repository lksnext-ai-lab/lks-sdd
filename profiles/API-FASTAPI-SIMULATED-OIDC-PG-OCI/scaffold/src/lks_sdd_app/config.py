from __future__ import annotations

import os
from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlsplit, urlunsplit

ALLOWED_NON_PRODUCTION_ENVIRONMENTS = frozenset(
    {
        "development",
        "test",
        "ci",
        "integration",
        "verification",
        "acceptance",
        "preproduction",
        "acceptance-preproduction",
    }
)
SIMULATED_OIDC_PATH = "/__test__/oidc"


def canonical_simulated_oidc_issuer(value: str) -> str:
    raw = value.strip()
    if (
        not raw
        or any(ord(character) < 33 for character in raw)
        or "?" in raw
        or "#" in raw
    ):
        raise ValueError("Simulated OIDC issuer must be an absolute test endpoint")
    try:
        parsed = urlsplit(raw)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("Simulated OIDC issuer has an invalid authority") from exc
    if (
        parsed.scheme.casefold() not in {"http", "https"}
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or "%" in parsed.path
        or parsed.path not in {SIMULATED_OIDC_PATH, f"{SIMULATED_OIDC_PATH}/"}
    ):
        raise ValueError("Simulated OIDC issuer must use the dedicated test path")
    normalized_host = hostname.casefold()
    try:
        loopback = ip_address(normalized_host).is_loopback
    except ValueError:
        loopback = normalized_host == "localhost"
    if parsed.scheme.casefold() == "http" and not loopback:
        raise ValueError("HTTP simulated OIDC issuers must use loopback")
    return urlunsplit(
        (parsed.scheme.casefold(), parsed.netloc, SIMULATED_OIDC_PATH, "", "")
    )


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str | None
    oidc_issuer: str
    oidc_audience: str
    simulated_tenant_id: str
    simulated_subject_id: str
    simulated_object_id: str
    simulated_username: str
    required_scope: str
    required_role: str

    @property
    def simulated_identity_enabled(self) -> bool:
        return self.environment.strip().casefold() in ALLOWED_NON_PRODUCTION_ENVIRONMENTS

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            environment=os.getenv("APP_ENV", ""),
            database_url=os.getenv("DATABASE_URL"),
            oidc_issuer=os.getenv(
                "OIDC_ISSUER", "http://127.0.0.1:8000/__test__/oidc"
            ).rstrip("/"),
            oidc_audience=os.getenv("OIDC_AUDIENCE", "api://lks-sdd-reference-api"),
            simulated_tenant_id=os.getenv("SIMULATED_TENANT_ID", "synthetic-tenant"),
            simulated_subject_id=os.getenv("SIMULATED_SUBJECT_ID", "synthetic-user"),
            simulated_object_id=os.getenv("SIMULATED_OBJECT_ID", "synthetic-object-001"),
            simulated_username=os.getenv(
                "SIMULATED_USERNAME", "synthetic.user@example.invalid"
            ),
            required_scope=os.getenv("OIDC_REQUIRED_SCOPE", "api.read"),
            required_role=os.getenv("OIDC_REQUIRED_ROLE", "Api.Read.All"),
        )
