"""Explicit, reversible document-method cutover without invented decisions."""
from __future__ import annotations

from v2_contract import ContractError, METHOD, canonical, load
from v2_storage import apply, preview


def diagnose(root):
    model = load(root)
    active = [e.id for e in model.by_kind("execution")
              if e.meta.get("state") in {"in-progress", "in-review", "paused", "blocked"}]
    return {"status": "current" if model.manifest["method_version"] == METHOD else
            "blocked" if active else "upgrade-available",
            "from_method": model.manifest["method_version"], "to_method": METHOD,
            "active_executions": sorted(active),
            "tasks_needing_request_reconciliation": sorted(e.id for e in model.by_kind("task")
                                                         if e.meta["state"] not in {"cancelled", "retired"}),
            "old_authorizations": sorted(e.id for e in model.by_kind("authorization")
                                         if e.meta["state"] == "active"),
            "writes": []}


def upgrade(root, authorized_hash=None):
    assessment = diagnose(root)
    if assessment["status"] == "current":
        return assessment
    if assessment["status"] != "upgrade-available":
        raise ContractError("Resolve active executions before method cutover: " +
                            ", ".join(assessment["active_executions"]))
    model = load(root)
    manifest = dict(model.manifest, method_version=METHOD)
    changes = {".lks-sdd/project.json": canonical(manifest) + b"\n"}
    result = preview(root, changes, sources=model.hashes, operation="upgrade-method-2.1.0")
    result.update({"from_method": model.manifest["method_version"], "to_method": METHOD,
                   "tasks_needing_request_reconciliation": assessment["tasks_needing_request_reconciliation"],
                   "old_authorizations": assessment["old_authorizations"],
                   "implementation_authorized": False})
    return apply(root, changes, result, authorized_hash, validator=lambda: load(root).require_valid()) if authorized_hash else result
