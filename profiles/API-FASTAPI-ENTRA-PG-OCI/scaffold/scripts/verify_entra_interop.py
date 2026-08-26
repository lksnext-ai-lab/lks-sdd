from __future__ import annotations

import json
import os
from urllib.request import ProxyHandler, Request, build_opener


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required ephemeral environment input: {name}")
    return value


issuer = required("OIDC_ISSUER").rstrip("/")
tenant_id = required("ENTRA_TENANT_ID")
expected_issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
if issuer != expected_issuer:
    raise SystemExit("OIDC_ISSUER must be the tenant-specific Microsoft Entra public-cloud issuer")
token = required("ENTRA_TEST_ACCESS_TOKEN")
opener = build_opener(ProxyHandler({}))
with opener.open(f"{issuer}/.well-known/openid-configuration", timeout=15) as response:
    metadata = json.load(response)
if metadata.get("issuer") != issuer or not str(metadata.get("jwks_uri", "")).startswith("https://"):
    raise SystemExit("Microsoft Entra discovery does not match the configured issuer")
request = Request(
    "http://127.0.0.1:18000/api/v1/me",
    headers={"Authorization": f"Bearer {token}"},
)
with opener.open(request, timeout=15) as response:
    if response.status != 200:
        raise SystemExit(f"Protected API returned HTTP {response.status}")
    body = json.load(response)
if body.get("tenant") != tenant_id:
    raise SystemExit("Protected API did not return the configured tenant")
print("Microsoft Entra interoperability gate passed without persisting the token.")
