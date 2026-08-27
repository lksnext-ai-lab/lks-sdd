import asyncio
import base64
import hashlib
from dataclasses import replace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport, AsyncClient, Response

from lks_sdd_app import security
from lks_sdd_app.config import Settings
from lks_sdd_app.main import app


@pytest.fixture(autouse=True)
def explicit_test_identity_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("OIDC_ISSUER", "http://127.0.0.1:8000/__test__/oidc")
    security._authorization_codes.clear()


async def request(path: str, token: str | None = None) -> Response:
    headers = {"Authorization": f"Bearer {token}"} if token else None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path, headers=headers)


async def post(path: str, payload: dict[str, object]) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=payload)


def settings() -> Settings:
    return Settings(
        environment="test",
        database_url=None,
        oidc_issuer="http://127.0.0.1:8000/__test__/oidc",
        oidc_audience="api://reference",
        simulated_tenant_id="synthetic-tenant",
        simulated_subject_id="synthetic-user",
        simulated_object_id="synthetic-object-001",
        simulated_username="synthetic.user@example.invalid",
        required_scope="api.read",
        required_role="Api.Read.All",
    )


def verifier_and_challenge() -> tuple[str, str]:
    verifier = "a" * 64
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def issue_token(configured: Settings | None = None) -> str:
    selected = configured or settings()
    verifier, challenge = verifier_and_challenge()
    code = security.begin_authorization(
        selected,
        subject=selected.simulated_subject_id,
        object_id=selected.simulated_object_id,
        username="synthetic.user@example.invalid",
        code_challenge=challenge,
        scopes=["api.read"],
        roles=[],
    )
    return security.exchange_code(selected, code=code, code_verifier=verifier)


def test_health_and_readiness_are_distinct() -> None:
    assert asyncio.run(request("/health")).json() == {"status": "ok"}
    assert asyncio.run(request("/ready")).status_code == 200


def test_readiness_fails_closed_for_invalid_identity_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OIDC_ISSUER", "https://identity.example/oidc")
    assert asyncio.run(request("/health")).status_code == 200
    assert asyncio.run(request("/ready")).status_code == 503


def test_openapi_is_generated_and_api_authentication_is_protected() -> None:
    schema = asyncio.run(request("/openapi.json")).json()
    assert schema["openapi"].startswith("3.1.")
    assert "/api/v1/me" in schema["paths"]
    assert asyncio.run(request("/api/v1/me")).status_code == 401


def test_oidc_discovery_and_jwks_are_bound_to_the_exact_issuer() -> None:
    metadata = security.discovery_document(settings())
    assert metadata["issuer"] == settings().oidc_issuer
    assert metadata["jwks_uri"] == f"{settings().oidc_issuer}/jwks"
    keys = security.jwks_document(settings())["keys"]
    assert len(keys) == 1
    assert keys[0]["kid"] == security.KEY_ID


def test_oidc_contract_uses_one_time_pkce_codes() -> None:
    configured = settings()
    verifier, challenge = verifier_and_challenge()
    code = security.begin_authorization(
        configured,
        subject=configured.simulated_subject_id,
        object_id=configured.simulated_object_id,
        username="synthetic.user@example.invalid",
        code_challenge=challenge,
        scopes=["api.read"],
        roles=[],
    )
    with pytest.raises(HTTPException, match="PKCE"):
        security.exchange_code(configured, code=code, code_verifier="b" * 64)
    with pytest.raises(HTTPException, match="invalid or expired"):
        security.exchange_code(configured, code=code, code_verifier=verifier)


def test_authorization_endpoint_rejects_non_s256_pkce() -> None:
    _, challenge = verifier_and_challenge()
    response = asyncio.run(
        post(
            "/__test__/oidc/authorize",
            {
                "code_challenge": challenge,
                "code_challenge_method": "plain",
            },
        )
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "only S256 is supported"}


def test_api_authentication_accepts_a_signed_synthetic_token() -> None:
    configured = settings()
    payload = security.decode_access_token(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=issue_token(configured)),
        configured,
    )
    assert payload["sub"] == "synthetic-user"
    assert payload["oid"] == "synthetic-object-001"
    assert payload["synthetic"] is True


def test_api_authorization_rejects_missing_permission() -> None:
    configured = replace(settings(), required_scope="orders.read", required_role="Orders.Read.All")
    with pytest.raises(HTTPException) as raised:
        security.decode_access_token(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=issue_token(settings())),
            configured,
        )
    assert raised.value.status_code == 403


def test_simulated_identity_safety_fails_closed_in_production() -> None:
    configured = replace(settings(), environment="production")
    with pytest.raises(HTTPException) as raised:
        security.discovery_document(configured)
    assert raised.value.status_code == 503


@pytest.mark.parametrize(
    "environment",
    ["", "production", " Production ", "staging", "preprod", "unknown"],
)
def test_simulated_identity_safety_rejects_every_unapproved_environment(
    environment: str,
) -> None:
    configured = replace(settings(), environment=environment)
    with pytest.raises(HTTPException) as raised:
        security.discovery_document(configured)
    assert raised.value.status_code == 503


def test_simulated_identity_safety_requires_an_explicit_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    configured = Settings.from_environment()
    assert configured.environment == ""
    with pytest.raises(HTTPException) as raised:
        security.discovery_document(configured)
    assert raised.value.status_code == 503


def test_oidc_discovery_accepts_loopback_and_https_test_issuers() -> None:
    loopback = replace(settings(), oidc_issuer="http://127.1.2.3:8000/__test__/oidc/")
    remote = replace(settings(), oidc_issuer="https://identity.acceptance.example/__test__/oidc/")
    assert security.discovery_document(loopback)["issuer"] == "http://127.1.2.3:8000/__test__/oidc"
    assert security.discovery_document(remote)["issuer"] == "https://identity.acceptance.example/__test__/oidc"


@pytest.mark.parametrize(
    "issuer",
    [
        "http://identity.example/__test__/oidc",
        "https://identity.example/oidc",
        "https://user@identity.example/__test__/oidc",
        "https://identity.example/__test__/oidc?tenant=real",
        "https://identity.example/__test__/oidc#fragment",
        "https://identity.example/__test__/other/../oidc",
        "https://login.microsoftonline.com/tenant/v2.0",
        "https://identity.example/%5f%5ftest%5f%5f/oidc",
    ],
)
def test_simulated_identity_safety_rejects_ambiguous_issuers(issuer: str) -> None:
    configured = replace(settings(), oidc_issuer=issuer)
    with pytest.raises(HTTPException) as raised:
        security.discovery_document(configured)
    assert raised.value.status_code == 503


def test_oidc_contract_rejects_identity_outside_the_stable_fixture() -> None:
    _, challenge = verifier_and_challenge()
    response = asyncio.run(
        post(
            "/__test__/oidc/authorize",
            {
                "subject": "another-user",
                "object_id": "another-object",
                "code_challenge": challenge,
            },
        )
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Synthetic identity must match the configured stable fixture"
    }


def test_oidc_contract_rejects_non_ascii_pkce_verifier_with_400() -> None:
    verifier, challenge = verifier_and_challenge()
    authorization = asyncio.run(
        post("/__test__/oidc/authorize", {"code_challenge": challenge})
    ).json()
    response = asyncio.run(
        post(
            "/__test__/oidc/token",
            {"code": authorization["code"], "code_verifier": "é" * len(verifier)},
        )
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "A valid PKCE code verifier is required"}
