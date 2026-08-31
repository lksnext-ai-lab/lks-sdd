import asyncio

from httpx import ASGITransport, AsyncClient, Response

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


def test_openapi_is_generated_and_identity_is_protected() -> None:
    schema = asyncio.run(request("/openapi.json")).json()
    assert schema["openapi"].startswith("3.1.")
    assert "/api/v1/me" in schema["paths"]
    assert "/api/v1/items" in schema["paths"]
    assert asyncio.run(request("/api/v1/me")).status_code in {401, 403}
    assert asyncio.run(request("/api/v1/items")).status_code in {401, 403}
