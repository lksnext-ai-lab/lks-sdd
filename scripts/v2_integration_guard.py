"""Offline integration guard: execute THIS verifier from a trusted checkout.

Never select its baseline, policy or expected result from the untrusted patch.
This detects violations; actual branch protection and identity are external.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

from v2_contract import ContractError, execution_context, fingerprint, load
from v2_lifecycle import work_inventory


def assess(trusted_root: Path, proposed_root: Path, tasks: list[str]) -> dict:
    if trusted_root.resolve() == proposed_root.resolve():
        raise ContractError("Trusted baseline must be independent of evaluated worktree")
    baseline, candidate = load(trusted_root), load(proposed_root)
    baseline.require_valid()
    candidate.require_valid()
    if baseline.manifest["project_id"] != candidate.manifest["project_id"]:
        raise ContractError("Integration roots identify different projects")
    expected = execution_context(baseline, tasks)
    actual = execution_context(candidate, tasks)
    before, after = work_inventory(trusted_root), work_inventory(proposed_root)
    changes = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    paths = [p for t in tasks for p in baseline.elements[t].meta.get("paths", [])]
    outside = [p for p in changes if not any(fnmatch.fnmatchcase(p, scope) for scope in paths)]
    import re
    sensitive = [p for p in changes if re.search(r"(?i)(test|gate|observer|policy|lock|security|(^|/)ci[/.-])", p)
                 or Path(p).name.lower() in {"package.json", "pyproject.toml", "requirements.txt", "pom.xml", "go.mod", "cargo.toml", "dockerfile"}]
    diff = fingerprint({"contract": expected["fingerprint"], "before": before, "after": after, "tasks": sorted(tasks)})
    reviewed = any(e.meta.get("category") == "integration-diff-review" and e.meta.get("diff_fingerprint") == diff
                   and e.meta["state"] == "approved" and e.meta.get("actor") for e in baseline.by_kind("receipt"))
    blockers = list(expected["blockers"]) + list(actual["blockers"])
    if expected["fingerprint"] != actual["fingerprint"]:
        blockers.append("Approved obligations or controls changed; independent approval required")
    if outside:
        blockers.append("Diff exceeds trusted task scope")
    if sensitive and not reviewed:
        blockers.append("Test/gate/dependency changes require an exact review held in the trusted baseline")
    return {"status": "blocked" if blockers else "structurally-within-scope", "changed": changes,
            "outside_scope": outside, "sensitive_changes": sensitive, "diff_fingerprint": diff,
            "blockers": blockers, "semantic_review": "required",
            "human_acceptance": "not-assessed", "external_enforcement": "not-assessed", "writes": []}


def review(trusted_root, proposed_root, tasks, request, *, authorized_hash=None):
    result = assess(trusted_root, proposed_root, tasks)
    if result["outside_scope"] or any("obligations or controls" in b for b in result["blockers"]):
        raise ContractError("A diff review cannot waive changed obligations or out-of-scope work")
    from v2_controls import receipt
    return receipt(load(trusted_root), "integration-diff-review", request.get("reason", ""),
        {"actor": request.get("actor"), "recorded_at": request.get("recorded_at"), "state": "approved",
         "diff_fingerprint": result["diff_fingerprint"], "relations": {"verifies": tasks}},
        authorized_hash=authorized_hash)
