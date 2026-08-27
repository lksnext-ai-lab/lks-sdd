from __future__ import annotations

import base64
import hashlib
import json
import urllib.request

BASE = "http://127.0.0.1:18000"
VERIFIER = "a" * 64
CHALLENGE = base64.urlsafe_b64encode(
    hashlib.sha256(VERIFIER.encode("ascii")).digest()
).decode("ascii").rstrip("=")


def post(path: str, body: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


authorization = post(
    "/__test__/oidc/authorize",
    {
        "subject": "synthetic-user",
        "object_id": "synthetic-object-001",
        "username": "synthetic.user@example.invalid",
        "code_challenge": CHALLENGE,
        "code_challenge_method": "S256",
        "scopes": ["api.read"],
        "roles": [],
    },
)
token = post(
    "/__test__/oidc/token",
    {"code": authorization["code"], "code_verifier": VERIFIER},
)
request = urllib.request.Request(
    BASE + "/api/v1/me",
    headers={"Authorization": f"Bearer {token['access_token']}"},
)
with urllib.request.urlopen(request, timeout=15) as response:
    identity = json.load(response)
assert identity["subject"] == "synthetic-user"
assert identity["object_id"] == "synthetic-object-001"
