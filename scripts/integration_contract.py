"""Shared interpretation of declared INT operations and required observers.

This module does not execute requests, SQL, migrations or consumer commands.
It deliberately cannot turn a URL prefix or successful login into proof of a
business operation. Unresolved contracts remain explicit blockers.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

BROWSER_GATE = "GATE-BROWSER-FULLSTACK-E2E"
HTTP_GATE = "GATE-HTTP-CONTRACT-INTEGRATION"
POSTGRES_GATE = "GATE-DATA-INTEGRATION"
MIGRATION_GATE = "GATE-DATA-MIGRATION"
INTEGRATION_GATES = frozenset({BROWSER_GATE, HTTP_GATE, POSTGRES_GATE, MIGRATION_GATE})
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
HTTP_OPERATION = re.compile(r"\b(GET|HEAD|POST|PUT|PATCH|DELETE|OPTIONS)\s+(/[A-Za-z0-9_./{}~-]*)", re.I)


def interface_policy(interface: dict[str, Any]) -> dict[str, Any]:
    protocol = str(interface.get("Protocol", "")).strip().casefold()
    scopes = {s.strip().casefold() for s in str(interface.get("Required evidence", "")).split(",") if s.strip()}
    operations = {s.strip().casefold() for s in str(interface.get("Operations", "")).split(",") if s.strip()}
    if protocol in {"postgresql", "postgres", "sql"}:
        observer, gate = "postgresql", POSTGRES_GATE
    elif protocol in {"alembic", "migration", "alembic/postgresql"}:
        observer, gate = "migration", MIGRATION_GATE
    elif "user-flow" in scopes:
        observer, gate = "browser-http", BROWSER_GATE
    else:
        observer, gate = "http", HTTP_GATE
    required = {"contract", "composition"}
    if observer == "browser-http":
        required.add("user-flow")
    if "write" in operations:
        required.add("persistence")
    declared = sorted({(m.upper(), p) for m, p in HTTP_OPERATION.findall(str(interface.get("Contract", "")))})
    return {"observer": observer, "gate_id": gate, "required_scopes": sorted(required),
            "contract": str(interface.get("Contract", "")),
            "http_operations": [{"method": m, "path": p} for m, p in declared]}


def operation_matches(request: dict[str, Any], operation: dict[str, Any]) -> bool:
    if str(request.get("method", "")).upper() != operation.get("method"):
        return False
    # Compare the complete contract path. A parameter is exactly one segment.
    path = urlsplit(str(request.get("path", ""))).path
    template = str(operation.get("path", ""))
    pattern = re.escape(template)
    pattern = re.sub(r"\\\{[^{}]+\\\}", r"[^/]+", pattern)
    return bool(template and re.fullmatch(pattern, path))


def http_observation_errors(observations: dict[str, Any], obligation: dict[str, Any]) -> list[str]:
    declared = obligation.get("http_operations", [])
    if not declared:
        return ["Contract no declara operaciones HTTP exactas METHOD /path; información insuficiente"]
    requests = observations.get("requests")
    if not isinstance(requests, list):
        return ["faltan observaciones HTTP del contrato"]
    successful = [r for r in requests if isinstance(r, dict) and type(r.get("status")) is int and 200 <= r["status"] < 300]
    errors = []
    for action, methods in [("read", {"GET", "HEAD"}), ("write", WRITE_METHODS)]:
        if action not in obligation.get("operations", []):
            continue
        if not any(operation_matches(r, op) for r in successful for op in declared if op.get("method") in methods):
            errors.append(f"no se observó operación {action} real del contrato declarado")
    if "persistence" in obligation.get("required_evidence_scopes", []):
        # The observer must link its independent SQL read to the very operation
        # declared in INT, not to login, audit, refresh or another successful POST.
        mutation = observations.get("mutation")
        if not isinstance(mutation, dict) or not any(
            operation_matches(mutation, op) for op in declared if op.get("method") in WRITE_METHODS
        ):
            errors.append("mutation no identifica una escritura del contrato declarado")
    return errors


def resource_observation_errors(observations: dict[str, Any], obligation: dict[str, Any]) -> list[str]:
    contract = str(obligation.get("contract", ""))
    if obligation.get("observer") == "postgresql":
        resources = re.findall(r"\bTABLE\s*:?\s+([a-z_][a-z0-9_]*)\b", contract, re.I)
        read = observations.get("read_back", {})
        if not resources:
            return ["Contract no declara TABLE <recurso>; información insuficiente"]
        if not isinstance(read, dict) or read.get("resource") not in resources:
            return ["la observación PostgreSQL no corresponde al recurso del contrato"]
    elif obligation.get("observer") == "migration":
        revisions = re.search(r"\bREVISION\s*:?\s+([A-Za-z0-9_-]+)\s*->\s*([A-Za-z0-9_-]+)", contract, re.I)
        if not revisions:
            return ["Contract no declara REVISION <origen> -> <destino>; información insuficiente"]
        if (observations.get("from"), observations.get("to")) != revisions.groups() or observations.get("data_preserved") is not True or observations.get("forward_fix_rehearsed") is not True:
            return ["la migración observada no corresponde al contrato o carece de recuperación"]
    return []
