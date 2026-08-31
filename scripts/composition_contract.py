"""Resolve INT-selected systems without introducing a deployable system unit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from contract_engine import expand_reference_ids
from integration_contract import BROWSER_GATE, interface_policy
from profile_registry import load_profile_bundle, validate_profile_bundle


def resolve_compositions(root: Path, delivery: dict[str, Any], task_ids: Iterable[str], *, require_locks: bool = False, require_certified: bool = True) -> tuple[list[dict[str, Any]], list[str]]:
    selected = set(task_ids)
    results, errors = [], []
    bindings = delivery.get("bindings", {})
    for identifier, row in sorted(delivery.get("interfaces", {}).items()):
        if row.get("State") != "confirmed" or not selected & expand_reference_ids(row.get("Verification task", ""), {"TASK"}):
            continue
        exact = str(row.get("Exact composition", ""))
        profile_id, separator, version = exact.partition("@")
        bundle = load_profile_bundle(profile_id)
        policy = interface_policy(row)
        if not separator or bundle.profile.get("version") != version or (policy["gate_id"] == BROWSER_GATE and bundle.profile.get("profile_scope") != "system"):
            errors.append(f"{identifier}: exact system composition is unresolved")
            continue
        errors.extend(validate_profile_bundle(profile_id, require_validated=require_certified))
        if policy["gate_id"] not in {c.get("id") for c in bundle.driver.get("verify", {}).get("checks", [])}:
            errors.append(f"{identifier}: composition does not implement {policy['gate_id']}")
        participants = []
        declared = bundle.driver.get("variant", {}).get("participants", {})
        declared_bindings = expand_reference_ids(row.get("Profile bindings", ""), {"BIND"})
        if bundle.profile.get("profile_scope") == "deployable":
            declared = {"observer": exact}
        for role, required in sorted(declared.items()):
            required_id, _, required_version = required.partition("@")
            matches = [b for b in bindings.values() if b.get("profile_id") == required_id and b.get("state") == "confirmed"
                       and b.get("binding_id") in declared_bindings]
            if len(matches) != 1:
                errors.append(f"{identifier}: {role} needs exactly one confirmed {required} binding")
                continue
            binding = matches[0]
            member = load_profile_bundle(required_id)
            errors.extend(validate_profile_bundle(required_id, require_validated=require_certified))
            if member.profile.get("version") != required_version or member.profile.get("profile_scope") != "deployable":
                errors.append(f"{identifier}: participant version or scope mismatch for {role}")
                continue
            expected = (member.root / "technology-profile.lock.json").read_bytes() if member.root else b""
            path = root / str(binding["lock_path"])
            try:
                path.resolve().relative_to(root.resolve())
                actual = path.read_bytes() if path.is_file() else None
            except (ValueError, OSError):
                actual = None
            if (require_locks and actual is None) or (actual is not None and actual != expected):
                errors.append(f"{identifier}: participant lock missing or changed for {binding['binding_id']}")
            participants.append({"role": role, "binding_id": binding["binding_id"], "unit_id": binding["unit_id"],
                                 "unit_path": binding.get("unit_path", "."), "profile": required,
                                 "lock_sha256": hashlib.sha256(expected).hexdigest()})
        if declared and bundle.profile.get("profile_scope") == "system" and declared_bindings != {p["binding_id"] for p in participants}:
            errors.append(f"{identifier}: INT participants are outside the exact composition")
        endpoint_units = expand_reference_ids(row.get("Consumer unit", ""), {"UNIT"}) | expand_reference_ids(row.get("Producer unit", ""), {"UNIT"})
        if declared and bundle.profile.get("profile_scope") == "system" and not endpoint_units <= {p["unit_id"] for p in participants}:
            errors.append(f"{identifier}: endpoint unit is outside the exact composition")
        if declared and len({p["unit_id"] for p in participants}) != len(participants):
            errors.append(f"{identifier}: distinct participants must retain distinct deployable units")
        lock = (bundle.root / "technology-profile.lock.json").read_bytes() if bundle.root else b""
        material = {"schema_version": "1.0", "profile": exact, "profile_lock_sha256": hashlib.sha256(lock).hexdigest(), "participants": participants}
        content = (json.dumps(material, sort_keys=True, indent=2) + "\n").encode()
        relative = f".lks-sdd/compositions/{exact}.lock.json"
        path = root / relative
        if require_locks and (not path.is_file() or path.read_bytes() != content):
            errors.append(f"{identifier}: composition lock missing or changed")
        prior = next((c for c in results if c["profile_id"] == profile_id and c["gate_id"] == policy["gate_id"] and c["content"] == content.decode()), None)
        if prior is not None:
            prior["interface_ids"].append(identifier)
            continue
        results.append({"interface_id": identifier, "interface_ids": [identifier], "profile_id": profile_id, "profile_version": version,
                        "gate_id": policy["gate_id"], "path": relative, "sha256": hashlib.sha256(content).hexdigest(),
                        "material": material, "content": content.decode()})
    return results, sorted(set(errors))
