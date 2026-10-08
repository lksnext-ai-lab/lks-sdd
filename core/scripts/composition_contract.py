"""Resolve generic documented interface bindings without technology selection."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from contract_engine import expand_reference_ids
from integration_contract import interface_policy


def resolve_compositions(root: Path, delivery: dict[str, Any], task_ids: Iterable[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Materialize confirmed interface participants from local generic bindings only."""
    selected = set(task_ids)
    results, errors = [], []
    bindings = delivery.get("bindings", {})
    for identifier, row in sorted(delivery.get("interfaces", {}).items()):
        if row.get("State") != "confirmed" or not selected & expand_reference_ids(row.get("Verification task", ""), {"TASK"}):
            continue
        binding_ids = expand_reference_ids(row.get("Bindings", ""), {"BIND"})
        participants = []
        for binding_id in sorted(binding_ids):
            binding = bindings.get(binding_id)
            if not isinstance(binding, dict) or binding.get("state") not in {"confirmed", "approved"}:
                errors.append(f"{identifier}: binding {binding_id} must be locally confirmed")
                continue
            participants.append({
                "binding_id": binding_id,
                "unit_id": binding.get("unit_id", ""),
                "unit_path": binding.get("unit_path", "."),
            })
        endpoint_units = expand_reference_ids(row.get("Consumer unit", ""), {"UNIT"}) | expand_reference_ids(row.get("Producer unit", ""), {"UNIT"})
        if endpoint_units and not endpoint_units <= {p["unit_id"] for p in participants}:
            errors.append(f"{identifier}: endpoint unit is outside the documented bindings")
        policy = interface_policy(row)
        material = {"schema_version": "2.0", "interface_id": identifier, "gate_id": policy["gate_id"], "participants": participants}
        content = json.dumps(material, sort_keys=True, indent=2) + "\n"
        results.append({"interface_id": identifier, "interface_ids": [identifier], "gate_id": policy["gate_id"],
                        "path": f".lks-sdd/compositions/{identifier}.json", "sha256": hashlib.sha256(content.encode()).hexdigest(),
                        "material": material, "content": content})
    return results, sorted(set(errors))
