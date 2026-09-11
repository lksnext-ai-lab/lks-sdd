"""Semantic sufficiency shared by live verification and profile certificates."""
from __future__ import annotations

import re
from typing import Any


def persistence_errors(observations: dict[str, Any]) -> list[str]:
    if not isinstance(observations, dict):
        return ["persistence observations must be an object"]
    mutation, read = observations.get("mutation"), observations.get("read_back")
    if not isinstance(mutation, dict) or not isinstance(read, dict):
        return ["persistence requires an independent structured database read"]
    identifier = mutation.get("record_id")
    if not isinstance(identifier, str) or not identifier or read.get("record_id") != identifier:
        return ["database read does not identify the observed mutation"]
    if read.get("observer") not in {"postgresql-psql", "postgresql-independent-connection"} or read.get("matches") is not True:
        return ["database read is not an independent PostgreSQL observation"]
    if not isinstance(read.get("resource"), str) or not re.fullmatch(r"[a-z_][a-z0-9_]*", read["resource"]):
        return ["database read has no exact resource"]
    if observations.get("persistence") is not True:
        return ["persistence was not observed"]
    return []


def gate_observation_errors(check: dict[str, Any], *, variant: bool = False) -> list[str]:
    if not isinstance(check, dict):
        return ["gate observation must be an object"]
    gate = check.get("gate_id")
    observations = check.get("observations")
    if check.get("status") != "passed":
        return ["gate did not pass"]
    if gate == "GATE-BROWSER-FULLSTACK-E2E":
        if not isinstance(observations, dict):
            return ["browser composition requires structured observations"]
        errors = persistence_errors(observations)
        if observations.get("reload") is not True or observations.get("console_errors") != []:
            errors.append("browser reload or console observation is incomplete")
        captures = observations.get("screenshots")
        if not isinstance(captures, list) or len(captures) < 3 or any(not isinstance(c, dict) or not re.fullmatch(r"[a-f0-9]{64}", str(c.get("sha256", ""))) for c in captures):
            errors.append("browser captures are incomplete")
        if variant:
            after = observations.get("read_after_restart", {})
            mutation = observations.get("mutation")
            if not isinstance(after, dict) or not isinstance(mutation, dict) or observations.get("api_restart") is not True or after.get("record_id") != mutation.get("record_id") or after.get("status") != 200:
                errors.append("business read after API restart is missing")
            if observations.get("offline_logout_honest") is not True or observations.get("credential_storage") is not False:
                errors.append("session browser observations are missing")
            outage = observations.get("database_unavailable")
            if not isinstance(outage, dict) or outage.get("fallback") is not False:
                errors.append("real database outage was not observed")
        return errors
    if variant and gate != "GATE-DELIVERY-EVIDENCE":
        if not isinstance(observations, dict) or not observations:
            return ["variant gate requires structured runtime observations"]
        if gate == "GATE-HTTP-CONTRACT-INTEGRATION":
            errors = persistence_errors(observations)
            if observations.get("logout_revoked") is not True or not observations.get("requests"):
                errors.append("HTTP business operation and server logout observations are missing")
            return errors
        if gate == "GATE-DATA-INTEGRATION" and not all(observations.get(k) for k in ["server_version", "independent_read", "restart_preserved"]):
            return ["PostgreSQL observation is incomplete"]
        if gate == "GATE-DATA-MIGRATION" and not all(observations.get(k) for k in ["from", "to", "empty_database", "data_preserved", "forward_fix_rehearsed"]):
            return ["migration observation is incomplete"]
    return []
