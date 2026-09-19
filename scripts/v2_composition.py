"""Persist local, generic interface composition records for v2 preparation."""
from __future__ import annotations

from v2_contract import ContractError, path_at


def resolve(model, tasks):
    from composition_contract import resolve_compositions
    bindings = {
        entry.id: {
            "binding_id": entry.id,
            "unit_id": entry.meta.get("unit_id", ""),
            "unit_path": entry.meta.get("unit_path", "."),
            "state": "confirmed" if entry.meta["state"] in {"confirmed", "approved"} else entry.meta["state"],
        }
        for entry in model.by_kind("binding")
    }
    selected = {identifier for task in tasks for identifier in model.elements[task].targets("interfaces")}
    interfaces = {}
    for identifier in selected:
        entry = model.elements[identifier]
        interfaces[identifier] = {
            "State": "confirmed" if entry.meta["state"] in {"confirmed", "approved"} else entry.meta["state"],
            "Verification task": ", ".join(tasks),
            "Protocol": entry.meta.get("protocol", ""),
            "Contract": entry.meta.get("contract", ""),
            "Operations": ", ".join(entry.meta.get("operations", [])),
            "Required evidence": ", ".join(entry.meta.get("evidence_scopes", [])),
            "Bindings": ", ".join(sorted(entry.targets("bindings"))),
            "Consumer unit": entry.meta.get("consumer_unit", ""),
            "Producer unit": entry.meta.get("producer_unit", ""),
        }
    result, errors = resolve_compositions(model.root, {"bindings": bindings, "interfaces": interfaces}, tasks)
    if errors:
        raise ContractError("; ".join(errors))
    return result


def preparation(model, tasks):
    changes = {}
    for composition in resolve(model, tasks):
        path = path_at(model.root, composition["path"], missing=True)
        raw = composition["content"].encode()
        if path.exists() and path.read_bytes() != raw:
            raise ContractError("Local composition record changed; explicit reconciliation required")
        if not path.exists():
            changes[composition["path"]] = raw
    return changes
