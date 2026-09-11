import asyncio

from httpx import ASGITransport, AsyncClient, Response

from lks_sdd_api.main import app


async def request(path: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def test_health_and_readiness() -> None:
    assert asyncio.run(request("/health")).json() == {"status": "ok"}
    assert asyncio.run(request("/ready")).status_code == 200


def test_versioned_contract_and_negative_route() -> None:
    response = asyncio.run(request("/api/v1/status"))
    assert response.status_code == 200
    assert response.json() == {"service": "lks-sdd-api", "status": "ok"}
    assert asyncio.run(request("/api/v2/status")).status_code == 404


def test_openapi_is_versioned() -> None:
    contract = asyncio.run(request("/api/v1/openapi.json")).json()
    assert contract["openapi"].startswith("3.1.")
    assert contract["info"]["version"] == "1.0.0"
