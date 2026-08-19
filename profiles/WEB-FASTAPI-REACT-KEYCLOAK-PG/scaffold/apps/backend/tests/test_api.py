from fastapi.testclient import TestClient

from lks_sdd_app.main import app

client = TestClient(app)


def test_health_and_readiness_are_distinct() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_openapi_is_generated_and_identity_is_protected() -> None:
    schema = client.get("/openapi.json").json()
    assert schema["openapi"].startswith("3.1.")
    assert "/api/v1/me" in schema["paths"]
    assert client.get("/api/v1/me").status_code in {401, 403}
