"""Adapt v2 interfaces to the existing exact certified composition engine."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
from v2_contract import ContractError, canonical, path_at

ROOT = Path(__file__).resolve().parents[1]


def resolve(model, tasks, *, require_locks=False):
    from composition_contract import resolve_compositions
    bindings = {}
    for entry in model.by_kind("binding"):
        bindings[entry.id] = {"binding_id": entry.id, "profile_id": entry.meta["profile_id"],
            "unit_id": entry.meta.get("unit_id", ""), "unit_path": entry.meta.get("unit_path", "."),
            "lock_path": entry.meta.get("lock_path", f".lks-sdd/profiles/{entry.id}.lock.json"),
            "state": "confirmed" if entry.meta["state"] in {"confirmed", "approved"} else entry.meta["state"]}
    interfaces = {}
    selected = {i for t in tasks for i in model.elements[t].targets("interfaces")}
    for identifier in selected:
        entry = model.elements[identifier]
        if any(not bindings[b]["unit_id"] for b in entry.targets("bindings")):
            raise ContractError("Composition participants require explicit documented unit identities")
        interfaces[identifier] = {"State": "confirmed", "Verification task": ", ".join(tasks),
            "Protocol": entry.meta.get("protocol", ""), "Contract": entry.meta.get("contract", ""),
            "Operations": ", ".join(entry.meta.get("operations", [])),
            "Required evidence": ", ".join(entry.meta.get("evidence_scopes", [])),
            "Exact composition": entry.meta.get("exact_composition", ""),
            "Profile bindings": ", ".join(sorted(entry.targets("bindings"))),
            "Consumer unit": entry.meta.get("consumer_unit", ""), "Producer unit": entry.meta.get("producer_unit", "")}
    result, errors = resolve_compositions(model.root, {"bindings": bindings, "interfaces": interfaces}, tasks, require_locks=require_locks)
    if errors:
        raise ContractError("; ".join(errors))
    return result


def preparation(model, tasks):
    from profile_registry import load_profile_bundle
    changes = {}
    for composition in resolve(model, tasks):
        candidates = {composition["path"]: composition["content"].encode()}
        bundle = load_profile_bundle(composition["profile_id"])
        if bundle.driver.get("variant"):
            config = json.loads((bundle.root / "scaffold/profile-runtime.json").read_text(encoding="utf-8"))
            config["unit_paths"] = {p["role"]: p["unit_path"] for p in composition["material"]["participants"]}
            candidates[".lks-sdd/verification/compositions/" + composition["profile_id"] + ".json"] = (json.dumps(config, sort_keys=True, indent=2) + "\n").encode()
        for relative, raw in candidates.items():
            path = path_at(model.root, relative, missing=True)
            if path.exists() and path.read_bytes() != raw:
                raise ContractError("Composition reference changed; explicit reconciliation required")
            if not path.exists():
                changes[relative] = raw
    return changes


def command(root, entry):
    from profile_registry import load_profile_bundle
    sys.path.insert(0, str(ROOT / "skills/lks-sdd-verify/scripts"))
    from run_verification import _variant_runtime_config
    composition, gate = entry["composition"], entry["packaged"]
    bundle = load_profile_bundle(composition["profile_id"])
    relative = ".lks-sdd/verification/compositions/" + composition["profile_id"] + ".json"
    config = path_at(root, relative)
    if not bundle.driver.get("variant"):
        raise ContractError("Composition has no packaged observer")
    _variant_runtime_config(root, config, bundle, {p["role"]: p["unit_path"] for p in composition["material"]["participants"]})
    return {"name": composition["profile_id"] + ":" + gate["name"], "gate_id": gate["id"], "binding_id": None,
        "profile_id": composition["profile_id"], "cwd": root,
        "command": [sys.executable, str(ROOT / "profiles/_shared/local-auth/verification/gate.py"), "--config", str(config), "--gate", gate["id"]],
        "timeout_seconds": gate["timeout_seconds"], "required": True, "requires_containers": True,
        "evidence_path": root / ".lks-sdd" / (gate["id"] + ".json"),
        "evidence_scopes": sorted({s for o in entry["interface_obligations"] for s in o["required_evidence_scopes"]}),
        "interface_ids": composition["interface_ids"]}
