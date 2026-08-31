"""Real HTTP probe without serializing authentication material."""
import argparse
import json
import os
import time
from pathlib import Path

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", required=True)
parser.add_argument("--record-id")
parser.add_argument("--database-unavailable", action="store_true")
args = parser.parse_args()
fixture = json.loads(Path(os.environ["LKS_AUTH_FIXTURE_FILE"]).read_text())
with httpx.Client(base_url=args.base_url, headers={"Origin": os.environ["LKS_AUTH_ORIGIN"], "X-CSRF": "1"}, timeout=15) as client:
    if args.database_unavailable:
        def denied(path, **kwargs):
            started = time.monotonic()
            try:
                response = client.post(path, **kwargs)
                assert response.status_code == 503 and "access_token" not in response.json()
                return {"outcome": "service-unavailable", "status": 503}
            except httpx.TimeoutException:
                # A paused database is different from a rejected connection.
                # Record the actual bounded client timeout; never invent HTTP 503.
                assert time.monotonic() - started < 20
                return {"outcome": "client-timeout", "timeout_seconds": 15}
        identity = denied("/auth/login", json={"username": fixture["users"][0]["username"], "password": fixture["users"][0]["password"], "organization": fixture["organizations"][0]})
        session = denied("/auth/refresh", json={}, headers={"Cookie": "__Host-lks-refresh=" + "x" * 64})
        print(json.dumps({"identity": identity, "session": session, "fallback": False}))
        raise SystemExit(0)
    login = client.post("/auth/login", json={"username": fixture["users"][0]["username"], "password": fixture["users"][0]["password"], "organization": fixture["organizations"][0]})
    assert login.status_code == 200
    client.headers["Authorization"] = "Bearer " + login.json()["access_token"]
    if args.record_id:
        import uuid
        uuid.UUID(args.record_id)
        read = client.get("/records/" + args.record_id)
        assert read.status_code == 200 and read.json()["id"] == args.record_id
        print(json.dumps({"observer": "httpx-real-http", "record_id": args.record_id, "status": 200}))
        raise SystemExit(0)
    response = client.post("/records", json={"label": "synthetic-http-probe"})
    assert response.status_code == 201
    identifier = response.json()["id"]
    read = client.get("/records/" + identifier)
    assert read.status_code == 200 and read.json()["label"] == "synthetic-http-probe"
    renewal = client.cookies.get("__Host-lks-refresh")
    signed_out = client.post("/auth/logout", json={}, headers={"Cookie": "__Host-lks-refresh="+renewal})
    assert signed_out.status_code == 200 and signed_out.json()["revoked"] is True
    assert client.get("/records/"+identifier).status_code == 401
    print(json.dumps({"requests": [{"method": "POST", "path": "/records", "status": 201}, {"method": "GET", "path": "/records/"+identifier, "status": 200}], "response_bytes": len(response.content), "record_id": identifier, "logout_revoked": True, "native_application_certified": False}))
