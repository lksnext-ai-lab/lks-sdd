import asyncio
from dataclasses import replace
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport, AsyncClient, Response

from lks_sdd_app import security
from lks_sdd_app.config import Settings
from lks_sdd_app.main import app


async def request(path: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def test_health_and_readiness_are_distinct() -> None:
    assert asyncio.run(request("/health")).json() == {"status": "ok"}
    response = asyncio.run(request("/ready"))
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_openapi_is_generated_and_api_authentication_is_protected() -> None:
    schema = asyncio.run(request("/openapi.json")).json()
    assert schema["openapi"].startswith("3.1.")
    assert "/api/v1/me" in schema["paths"]
    assert asyncio.run(request("/api/v1/me")).status_code == 401


def settings() -> Settings:
    return Settings(
        environment="test",
        database_url=None,
        oidc_issuer="https://login.microsoftonline.com/11111111-1111-1111-1111-111111111111/v2.0",
        oidc_audience="api://reference",
        entra_tenant_id="11111111-1111-1111-1111-111111111111",
        required_scope="api.read",
        required_role="Api.Read.All",
    )


def test_oidc_discovery_uses_the_exact_issuer() -> None:
    issuer = settings().oidc_issuer
    assert issuer is not None
    assert security.discovery_url(issuer) == f"{issuer}/.well-known/openid-configuration"


def test_oidc_jwks_comes_from_discovery(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, str] = {}

    class FakeJwkClient:
        def __init__(self, uri: str) -> None:
            observed["jwks_uri"] = uri

        def get_signing_key_from_jwt(self, token: str) -> Any:
            return type("Key", (), {"key": "synthetic-key"})()

    configured = settings()
    monkeypatch.setattr(
        security,
        "fetch_oidc_metadata",
        lambda issuer: {
            "issuer": issuer,
            "jwks_uri": "https://login.microsoftonline.com/discovery/keys",
        },
    )
    monkeypatch.setattr(security, "PyJWKClient", FakeJwkClient)
    monkeypatch.setattr(
        security.jwt,
        "decode",
        lambda *args, **kwargs: {
            "sub": "user",
            "tid": configured.entra_tenant_id,
            "scp": "api.read",
            "exp": 4102444800,
            "iss": configured.oidc_issuer,
            "aud": configured.oidc_audience,
        },
    )
    security.decode_access_token(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="synthetic.token.value"),
        configured,
    )
    assert observed["jwks_uri"] == "https://login.microsoftonline.com/discovery/keys"


def test_oidc_contract_rejects_discovery_issuer_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        security,
        "fetch_oidc_metadata",
        lambda issuer: {
            "issuer": f"{issuer}/other",
            "jwks_uri": "https://login.microsoftonline.com/discovery/keys",
        },
    )
    with pytest.raises(HTTPException) as raised:
        security.decode_access_token(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="synthetic.token.value"),
            settings(),
        )
    assert raised.value.status_code == 503


def test_entra_issuer_is_bound_to_tenant_before_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        security,
        "fetch_oidc_metadata",
        lambda issuer: pytest.fail(f"unexpected discovery request to {issuer}"),
    )
    configured = replace(settings(), oidc_issuer="https://identity.example.invalid/v2.0")
    with pytest.raises(HTTPException) as raised:
        security.decode_access_token(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="synthetic.token.value"),
            configured,
        )
    assert raised.value.status_code == 503


def test_entra_tenant_identifier_must_be_canonical() -> None:
    configured = replace(
        settings(),
        entra_tenant_id="../common",
        oidc_issuer="https://login.microsoftonline.com/../common/v2.0",
    )
    with pytest.raises(HTTPException) as raised:
        security.decode_access_token(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="synthetic.token.value"),
            configured,
        )
    assert raised.value.status_code == 503


def test_entra_tenant_is_enforced() -> None:
    with pytest.raises(HTTPException) as raised:
        security.authorize_claims({"tid": "another-tenant", "scp": "api.read"}, settings())
    assert raised.value.status_code == 403


def test_entra_permissions_accept_scope_or_role() -> None:
    configured = settings()
    security.authorize_claims({"tid": configured.entra_tenant_id, "scp": "api.read"}, configured)
    security.authorize_claims(
        {"tid": configured.entra_tenant_id, "roles": ["Api.Read.All"]}, configured
    )


def test_api_authorization_rejects_missing_permission() -> None:
    configured = replace(settings(), required_scope="orders.read", required_role="Orders.Read.All")
    with pytest.raises(HTTPException) as raised:
        security.authorize_claims(
            {"tid": configured.entra_tenant_id, "scp": "api.read"}, configured
        )
    assert raised.value.status_code == 403
