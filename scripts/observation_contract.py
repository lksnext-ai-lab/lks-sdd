"""Semantic sufficiency shared by live verification observers."""
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


def gate_observation_errors(check: dict[str, Any]) -> list[str]:
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
        return errors
    return []
