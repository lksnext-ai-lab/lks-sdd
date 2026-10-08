"""Method 2.1 request and SPEC-to-plan coverage analysis.

The Markdown elements remain authoritative. This module derives a view and never
turns a relation into a semantic approval of the underlying human request.
"""
from __future__ import annotations

from v2_contract import ContractError, fingerprint

METHOD = "2.1.0"
BASIS = "spec-plan-task/1"
DECIDED = {"confirmed", "approved", "active", "effective"}


def enabled(model) -> bool:
    return model.manifest.get("method_version") == METHOD


def _ids(model, values, kind, owner):
    if not isinstance(values, list) or len(values) != len(set(values)):
        raise ContractError(f"{owner}: expected unique {kind} IDs")
    for identifier in values:
        if not isinstance(identifier, str) or identifier not in model.elements or model.elements[identifier].kind != kind:
            raise ContractError(f"{owner}: invalid {kind} reference: {identifier}")
    return set(values)


def validate_request(model, change):
    """Validate typed references; incomplete draft decisions remain representable."""
    if change.kind != "change" or change.meta.get("category") != "implementation-request":
        raise ContractError("Select an implementation request")
    if not change.id.startswith("PCH-"):
        raise ContractError("Implementation request must use a PCH ID: " + change.id)
    if not change.path.startswith("docs/lks-sdd/00-control/changes/"):
        raise ContractError("Implementation request must live under changes/: " + change.id)
    if change.path not in {entry.get("path") for entry in model.manifest.get("artifacts", [])
                           if isinstance(entry, dict)}:
        raise ContractError("Implementation request is missing from project index: " + change.id)
    if change.meta.get("state") not in {"draft", "confirmed", "cancelled", "superseded"}:
        raise ContractError("Invalid implementation request state: " + change.id)
    points = change.meta.get("points")
    if not isinstance(points, list) or not points:
        raise ContractError("Implementation request needs material points: " + change.id)
    if not change.body.strip() or not change.meta.get("source_summary"):
        raise ContractError("Implementation request needs outcome and source summary: " + change.id)
    affected = _ids(model, list(change.targets("affects")), "feature", change.id)
    if not affected:
        raise ContractError("Implementation request needs affected feature: " + change.id)
    keys = set()
    for point in points:
        if not isinstance(point, dict) or not isinstance(point.get("key"), str) or not point["key"].strip():
            raise ContractError(change.id + ": point needs a stable key")
        key = point["key"]
        if key in keys:
            raise ContractError(change.id + ": duplicate point: " + key)
        keys.add(key)
        label = change.id + "/" + key
        if not point.get("summary"):
            raise ContractError(label + ": material outcome missing")
        _ids(model, point.get("requirements", []), "requirement", label)
        _ids(model, point.get("acceptance", []), "acceptance", label)
        _ids(model, point.get("tests", []), "test", label)
        _ids(model, point.get("tasks", []), "task", label)
        _ids(model, point.get("plans", []), "plan", label)
        requirements = set(point.get("requirements", []))
        if change.meta["state"] == "confirmed" and not requirements <= applicable_requirements(model, affected):
            raise ContractError(label + ": requirement is outside affected SPEC features")
        expected_acceptance = {a for requirement_id in requirements
                               for a in requirement_acceptance(model, requirement_id)}
        if change.meta["state"] == "confirmed" and not set(point.get("acceptance", [])) <= expected_acceptance:
            raise ContractError(label + ": acceptance is not linked to its SPEC requirement")
        disposition = point.get("disposition", "unknown")
        if disposition not in {"planned", "satisfied", "deferred", "excluded", "unknown"}:
            raise ContractError(label + ": invalid disposition")
        if disposition in {"satisfied", "deferred", "excluded"} and not point.get("decision_reason"):
            raise ContractError(label + ": disposition requires a reason")
        if disposition == "satisfied" and not point.get("evidence_ids"):
            raise ContractError(label + ": satisfied requires exact evidence IDs")
        if change.meta["state"] == "confirmed" and disposition == "planned":
            if any(not point.get(field) for field in
                   ("requirements", "acceptance", "tests", "plans", "tasks")):
                raise ContractError(label + ": confirmed planned point needs SPEC, PLAN, TASK and tests")


def applicable_requirements(model, feature_ids):
    """Use explicit feature/requirement edges; never infer scope from a folder."""
    result = set()
    for feature_id in feature_ids:
        feature = model.elements[feature_id]
        result.update(i for i in feature.targets("requirements") if model.elements[i].kind == "requirement")
        result.update(e.id for e in model.by_kind("requirement") if feature_id in e.targets("implements"))
    return {i for i in result if model.elements[i].meta.get("state") in DECIDED}


def requirement_acceptance(model, requirement_id):
    requirement = model.elements[requirement_id]
    return (set(requirement.targets("acceptance")) |
            {e.id for e in model.by_kind("acceptance") if requirement_id in e.targets("requirements")})


def assess_plan(model, plan_id):
    """One analysis drives decomposition and every lifecycle readiness gate."""
    plan = model.elements.get(plan_id)
    if plan is None or plan.kind != "plan":
        raise ContractError("Select a documented PLAN")
    tasks = [t for t in model.by_kind("task") if plan_id in t.targets("plan")
             and t.meta["state"] not in {"cancelled", "retired", "superseded"}]
    features = {i for t in tasks for i in t.targets("implements") if model.elements[i].kind == "feature"}
    changes = [c for c in model.by_kind("change") if c.meta.get("category") == "implementation-request"
               and c.meta.get("state") not in {"cancelled", "superseded"}
               and c.targets("affects") & features]
    for change in changes:
        validate_request(model, change)
    mapped_plans = {}
    for change in changes:
        if change.meta["state"] != "confirmed":
            continue
        for point in change.meta["points"]:
            for requirement_id in point.get("requirements", []):
                mapped_plans.setdefault(requirement_id, set()).update(point.get("plans", []))
    expected = {r for r in applicable_requirements(model, features)
                if not mapped_plans.get(r) or plan_id in mapped_plans[r]}
    declared = set(plan.targets("requirements"))
    blockers = []
    if not features:
        blockers.append("PLAN has no TASK with a primary feature: " + plan_id)
    missing_plan = sorted(expected - declared)
    extra_plan = sorted(declared - expected)
    deferred = {r for c in changes if c.meta["state"] == "confirmed"
                for point in c.meta["points"] if point.get("disposition") == "deferred"
                and plan_id in point.get("plans", []) and point.get("decision_reason")
                for r in point.get("requirements", [])}
    unresolved_missing = set(missing_plan)
    if plan.meta.get("planning_policy") == "incremental-authorized":
        unresolved_missing -= deferred
    if unresolved_missing:
        blockers.append("SPEC obligations absent from PLAN " + plan_id + ": " + ", ".join(sorted(unresolved_missing)))
    if extra_plan:
        blockers.append("PLAN obligations lack applicable SPEC scope " + plan_id + ": " + ", ".join(extra_plan))
    assignments = {}
    for requirement_id in sorted(expected):
        acceptance = requirement_acceptance(model, requirement_id)
        owners = [t for t in tasks if requirement_id in t.targets("requirements")]
        accepted = {i for t in owners for i in t.targets("acceptance")}
        missing_acceptance = sorted(acceptance - accepted)
        if not owners and requirement_id not in deferred:
            blockers.append("SPEC requirement has no TASK: " + requirement_id)
        if missing_acceptance and requirement_id not in deferred:
            blockers.append("Acceptance absent from TASK for " + requirement_id + ": " + ", ".join(missing_acceptance))
        for task in owners:
            if not task.targets("tests"):
                blockers.append("TASK lacks tests for " + requirement_id + ": " + task.id)
        assignments[requirement_id] = {"tasks": sorted(t.id for t in owners),
                                        "acceptance": sorted(acceptance),
                                        "missing_acceptance": missing_acceptance}
    point_rows = []
    for change in changes:
        if change.meta["state"] != "confirmed":
            blockers.append("Implementation request is not confirmed: " + change.id)
        for point in change.meta["points"]:
            relevant = set(point.get("requirements", [])) & expected
            if not relevant:
                continue
            point_rows.append({"change": change.id, **point})
            allowed_deferred = (point.get("disposition") == "deferred"
                                and plan.meta.get("planning_policy") == "incremental-authorized"
                                and relevant <= set(missing_plan))
            if point.get("disposition") != "planned" and not allowed_deferred:
                blockers.append("Request point needs planned coverage: " + change.id + "/" + point["key"])
            if plan_id not in point.get("plans", []):
                blockers.append("Request point does not select PLAN: " + change.id + "/" + point["key"])
            for task_id in point.get("tasks", []):
                task = model.elements[task_id]
                if not set(point.get("plans", [])) & task.targets("plan"):
                    blockers.append("Request point TASK is outside its PLAN: " + task_id)
                if not set(point.get("requirements", [])) & task.targets("requirements"):
                    blockers.append("Request point TASK lacks its SPEC requirement: " + task_id)
            for requirement_id in relevant:
                if allowed_deferred:
                    continue
                assigned = set(assignments[requirement_id]["tasks"])
                if not assigned & set(point.get("tasks", [])):
                    blockers.append("Request point omits TASK assignment for " + requirement_id)
                expected_ac = set(assignments[requirement_id]["acceptance"])
                if not expected_ac <= set(point.get("acceptance", [])):
                    blockers.append("Request point omits acceptance for " + requirement_id)
                required_tests = {test for task in owners if task.id in point.get("tasks", [])
                                  for test in task.targets("tests")}
                if not required_tests <= set(point.get("tests", [])):
                    blockers.append("Request point omits tests for " + requirement_id)
    covered_points = {i for row in point_rows for i in row.get("requirements", [])}
    if expected - covered_points:
        blockers.append("SPEC requirements lack a confirmed request point: " + ", ".join(sorted(expected - covered_points)))
    if not changes:
        blockers.append("Implementation request PCH absent for PLAN: " + plan_id)
    for requirement_id in sorted(set(missing_plan) & deferred):
        if any(requirement_id in model.elements[implemented].targets("depends_on")
               for task in tasks for implemented in task.targets("requirements")):
            blockers.append("Selected work depends on deferred requirement: " + requirement_id)
    return {"plan": plan_id, "expected": sorted(expected), "declared": sorted(declared),
            "missing": missing_plan, "extra": extra_plan, "assignments": assignments,
            "points": point_rows, "changes": sorted(c.id for c in changes),
            "blockers": sorted(set(blockers)), "status": "incomplete" if blockers else
                      "partial-covered" if missing_plan else "covered"}


def planning_projection(model, tasks):
    """Hash common PLAN rules and only assignments of the selected TASK slice."""
    selected = set(tasks)
    plans = {p for task_id in selected for p in model.elements[task_id].targets("plan")}
    projection = []
    for plan_id in sorted(plans):
        plan = model.elements[plan_id]
        meta = dict(plan.meta)
        for operational in ("revision", "progress", "updated_at", "health", "board_order"):
            meta.pop(operational, None)
        relations = dict(meta.get("relations", {}))
        relations.pop("requirements", None)
        meta["relations"] = relations
        analysis = assess_plan(model, plan_id)
        selected_requirements = {r for r, assignment in analysis["assignments"].items()
                                 if selected & set(assignment["tasks"])}
        point_rows = []
        for row in analysis["points"]:
            if selected & set(row.get("tasks", [])):
                point_rows.append({"change": row["change"], "key": row["key"],
                                   "summary": row["summary"], "disposition": row.get("disposition"),
                                   "requirements": sorted(selected_requirements & set(row.get("requirements", []))),
                                   "acceptance": sorted(set(row.get("acceptance", [])) &
                                                        {a for r in selected_requirements for a in analysis["assignments"][r]["acceptance"]}),
                                   "tests": sorted(set(row.get("tests", [])) &
                                                   {test for task_id in selected & set(row.get("tasks", []))
                                                    for test in model.elements[task_id].targets("tests")}),
                                   "tasks": sorted(selected & set(row.get("tasks", [])))})
        request_sources = [{"id": change_id,
                            "state": model.elements[change_id].meta["state"],
                            "source_summary": model.elements[change_id].meta["source_summary"],
                            "body": model.elements[change_id].body}
                           for change_id in sorted({row["change"] for row in point_rows})]
        projection.append({"plan": plan_id, "meta": meta, "body": plan.body,
                           "selected_requirements": sorted(selected_requirements),
                           "request_sources": request_sources, "request_points": point_rows})
    return {"algorithm": BASIS, "plans": projection,
            "digest": fingerprint(projection)}
