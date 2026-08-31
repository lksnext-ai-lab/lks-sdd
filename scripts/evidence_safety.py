"""Minimize diagnostic output and reject credential-bearing evidence.

Returns locations, never the confidential values. Historical evidence is read
without mutation; contaminated input cannot be certified or published.
"""
from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEYS = frozenset({"authorization", "cookie", "set-cookie", "password", "password_hash",
                            "current_password", "new_password", "access_token", "refresh_token",
                            "recovery_token", "client_secret", "private_key", "signing_key"})
PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{8,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
    re.compile(r"(?im)^\s*(?:authorization|cookie|set-cookie)\s*:[^\r\n]+"),
    re.compile(r"(?i)\b(?:password|client_secret|refresh_token|access_token)\s*[=:]\s*['\"]?[^\s,'\"}]+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:postgresql(?:\+psycopg)?|https?)://[^\s/:]+:[^\s/@]+@"),
)


def sanitize(value: Any) -> tuple[Any, list[str]]:
    findings: list[str] = []
    def walk(item: Any, path: str) -> Any:
        if isinstance(item, dict):
            result = {}
            for key, val in item.items():
                location = path + "." + str(key)
                if str(key).casefold() in SENSITIVE_KEYS and isinstance(val, str) and val and val != "[redacted]":
                    findings.append(location)
                    result[key] = "[redacted]"
                else:
                    result[key] = walk(val, location)
            return result
        if isinstance(item, list):
            return [walk(val, f"{path}[{index}]") for index, val in enumerate(item)]
        if isinstance(item, str):
            for pattern in PATTERNS:
                if pattern.search(item):
                    findings.append(path)
                    item = pattern.sub("[redacted]", item)
            return item
        return item
    clean = walk(value, "evidence")
    return clean, sorted(set(findings))


def evidence_safety_errors(value: Any) -> list[str]:
    _, locations = sanitize(value)
    return ["credential-bearing evidence at " + path for path in locations]
