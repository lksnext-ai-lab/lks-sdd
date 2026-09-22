"""Offline integration guard: execute THIS verifier from a trusted checkout.

Never select its baseline, policy or expected result from the untrusted patch.
This detects violations; actual branch protection and identity are external.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

from v2_contract import ContractError, execution_context, fingerprint, load
from v2_lifecycle import active_execution, current_authorization, planning, work_inventory


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


def assess_strict(code_base: Path, approved_root: Path, proposed_root: Path, tasks: list[str],
                  environment: str) -> dict:
    """Check the whole candidate against an independently supplied approved contract.

    The caller must select this verifier and approved_root outside the patch.
    Structural compliance does not establish human semantics or authenticate actors.
    """
    roots = [Path(p).resolve() for p in (code_base, approved_root, proposed_root)]
    if len(set(roots)) != 3:
        raise ContractError("Code base, approved contract and candidate must be independent roots")
    approved, candidate = load(approved_root), load(proposed_root)
    approved.require_valid()
    candidate.require_valid()
    if approved.manifest["project_id"] != candidate.manifest["project_id"]:
        raise ContractError("Approved contract and candidate identify different projects")
    blockers = []
    if approved.manifest["method_version"] != "2.1.0":
        blockers.append("Strict integration requires method 2.1.0")
    expected = planning(approved, tasks)
    actual = planning(candidate, tasks)
    blockers.extend(expected["blockers"])
    blockers.extend(actual["blockers"])
    if expected["fingerprint"] != actual["fingerprint"]:
        blockers.append("Candidate contract differs from independently approved scope")
    before, after = work_inventory(code_base), work_inventory(proposed_root)
    changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    if not changed:
        blockers.append("No implementation patch to assess")
    paths = [p for task_id in tasks for p in approved.elements[task_id].meta.get("paths", [])]
    outside = [p for p in changed if not any(fnmatch.fnmatchcase(p, scope) for scope in paths)]
    if outside:
        blockers.append("Candidate patch exceeds approved TASK paths")
    overlaps = {}
    for path in changed:
        owners = [task_id for task_id in tasks if any(
            fnmatch.fnmatchcase(path, pattern) for pattern in approved.elements[task_id].meta.get("paths", []))]
        if len(owners) > 1:
            overlaps[path] = owners
            if any(not any(fnmatch.fnmatchcase(path, pattern) for pattern in
                           approved.elements[task_id].meta.get("joint_ownership", [])) for task_id in owners):
                blockers.append("Overlapping TASK paths need explicit joint ownership: " + path)
    diff = fingerprint({"contract": expected["fingerprint"], "before": before,
                        "after": after, "tasks": sorted(tasks)})
    import re
    sensitive = [p for p in changed if re.search(r"(?i)(test|gate|observer|policy|lock|security|(^|/)ci[/.-])", p)
                 or Path(p).name.lower() in {"package.json", "pyproject.toml", "requirements.txt", "pom.xml", "go.mod", "cargo.toml", "dockerfile"}]
    reviewed = any(e.meta.get("category") == "integration-diff-review"
                   and e.meta.get("diff_fingerprint") == diff
                   and e.meta["state"] == "approved" and e.meta.get("actor")
                   for e in approved.by_kind("receipt"))
    if sensitive and not reviewed:
        blockers.append("Sensitive patch requires exact independent diff review")
    authorization_id = execution_id = None
    try:
        authorization = current_authorization(approved, tasks, environment)
        authorization_id = authorization["authorization_id"]
        execution = active_execution(approved, tasks)
        execution_id = execution.id
        if set(execution.targets("implements")) != set(tasks):
            blockers.append("EXEC task scope differs from selected patch scope")
        if execution.meta.get("contract_fingerprint") != expected["fingerprint"]:
            blockers.append("EXEC contract basis is stale")
        if execution.meta.get("basis_algorithm") != "spec-plan-task/1":
            blockers.append("EXEC lacks the current basis algorithm")
        if execution.meta.get("baseline_files") != before:
            blockers.append("EXEC was not recorded over the trusted code baseline")
        if authorization_id not in execution.targets("authorizes"):
            blockers.append("EXEC does not cite the current AUTH")
        if (authorization_id not in candidate.elements or
                candidate.elements[authorization_id].meta != approved.elements[authorization_id].meta):
            blockers.append("Candidate lacks the exact approved AUTH record: " + authorization_id)
        if execution_id not in candidate.elements:
            blockers.append("Candidate lacks approved EXEC record: " + execution_id)
        else:
            candidate_execution = candidate.elements[execution_id]
            immutable = ("uid", "started_at", "contract_fingerprint", "baseline_files",
                         "basis_algorithm", "specification_digest", "planning_digest", "source_hashes")
            if (any(candidate_execution.meta.get(key) != execution.meta.get(key) for key in immutable)
                    or candidate_execution.targets("implements") != execution.targets("implements")
                    or candidate_execution.targets("authorizes") != execution.targets("authorizes")):
                blockers.append("Candidate EXEC differs from approved execution basis: " + execution_id)
    except ContractError as exc:
        blockers.append(str(exc))
    return {"status": "blocked" if blockers else "structurally-compliant",
            "mode": "strict", "code_base": str(roots[0]), "approved_contract": str(roots[1]),
            "candidate": str(roots[2]), "task_ids": sorted(tasks), "changed": changed,
            "outside_scope": outside, "overlapping_paths": overlaps,
            "sensitive_changes": sensitive,
            "diff_fingerprint": diff, "authorization_id": authorization_id,
            "execution_id": execution_id, "blockers": sorted(set(blockers)),
            "semantic_review": "required", "identity_assurance": "declared-not-authenticated",
            "external_enforcement": "not-assessed", "writes": []}


def review(trusted_root, proposed_root, tasks, request, *, authorized_hash=None):
    result = assess(trusted_root, proposed_root, tasks)
    if result["outside_scope"] or any("obligations or controls" in b for b in result["blockers"]):
        raise ContractError("A diff review cannot waive changed obligations or out-of-scope work")
    from v2_controls import receipt
    return receipt(load(trusted_root), "integration-diff-review", request.get("reason", ""),
        {"actor": request.get("actor"), "recorded_at": request.get("recorded_at"), "state": "approved",
         "diff_fingerprint": result["diff_fingerprint"], "relations": {"verifies": tasks}},
        authorized_hash=authorized_hash)
