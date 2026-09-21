"""Governed v2 planning, authorization, scope checks and durable continuity.

Local records attest declared decisions, not authenticated organizational roles.
Only explicit preview-bound mutations write; assessments remain read-only.
"""
from __future__ import annotations

from datetime import datetime, timezone
import fnmatch
import json
import os
from pathlib import Path
import re
import uuid

from query_sources import SKIP_DIRS, SECRET_NAME, is_link, is_root_git_metadata
from v2_contract import (ContractError, DOCS, Element, Model, canonical, execution_context, fingerprint,
                         load, make_element, path_at, read_bytes, render_document, sha)
from v2_authoring import edit_elements
from v2_storage import apply, ensure_idle, preview

ACTIVE_EXECUTION_STATES = frozenset({"in-progress", "in-review", "paused", "blocked"})


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ContractError("Timezone-aware timestamp required")
    return result


def next_id(model: Model, prefix: str) -> str:
    maximum = max((int(e.id.split("-")[-1]) for e in model.elements.values()
                   if re.fullmatch(prefix + r"-\d{3,}", e.id)), default=0)
    return f"{prefix}-{maximum + 1:03}"


def record(model: Model, identifier: str, kind: str, title: str, body: str, **values) -> tuple[str, bytes]:
    uid = str(uuid.uuid5(uuid.NAMESPACE_URL, str(model.manifest["project_id"]) + ":" + identifier))
    element = make_element(identifier, kind, title, body, uid=uid, nature="decision" if kind == "authorization" else "fact", **values)
    directory = "00-control/authorizations" if kind == "authorization" else "04-delivery/" + {
        "execution": "executions", "checkpoint": "checkpoints", "problem": "problems"}[kind]
    return DOCS + "/" + directory + "/" + identifier + ".md", render_document(kind, title, [element])


def reservation_continuations(model: Model, tasks: list[str]) -> tuple[list[dict], list[str]]:
    """Resolve only explicit receipts that let a dependent continue with inherited risk."""
    continuations, missing = [], []
    for task_id in tasks:
        task = model.elements[task_id]
        for dependency_id in sorted(task.targets("depends_on")):
            dependency = model.elements[dependency_id]
            if dependency.kind != "task" or dependency.meta["state"] != "done-with-reservations":
                continue
            evidence_ids = dependency.meta.get("evidence_ids", [])
            if not evidence_ids:
                raise ContractError("Reserved dependency has no terminal verification evidence: " + dependency_id)
            terminal_evidence = evidence_ids[-1]
            receipts = [
                receipt for receipt in model.by_kind("receipt")
                if receipt.meta.get("category") == "dependency-reservation-continuation"
                and receipt.meta.get("state") == "approved"
                and task_id in receipt.targets("affects")
                and dependency_id in receipt.targets("depends_on")
                and any(item.get("task_id") == dependency_id and item.get("evidence_id") == terminal_evidence
                        for item in receipt.meta.get("dependency_evidence", [])
                        if isinstance(item, dict))
            ]
            if not receipts:
                missing.append(dependency_id)
                continue
            receipt = max(receipts, key=lambda item: (item.meta.get("recorded_at", ""), item.id))
            source = next(item for item in receipt.meta["dependency_evidence"]
                          if item["task_id"] == dependency_id)
            from v2_verification import evidence
            value = evidence(model, source["evidence_id"])
            if (value["integrity_sha256"] != source.get("evidence_sha256")
                    or receipt.meta.get("dependency_evidence") is None
                    or not isinstance(receipt.meta.get("inherited_reservations"), list)):
                raise ContractError("Reservation continuation receipt no longer binds exact dependency evidence")
            continuations.append({
                "task_id": task_id,
                "dependency_task_id": dependency_id,
                "receipt_id": receipt.id,
                "dependency_evidence": [
                    item for item in receipt.meta["dependency_evidence"] if item["task_id"] == dependency_id
                ],
            })
    return continuations, sorted(set(missing))


def planning(model: Model, tasks: list[str], *, check_tracking=True) -> dict:
    context = execution_context(model, tasks)
    blockers = list(context["blockers"])
    governance = [e for e in model.by_kind("decision") if e.meta.get("category") == "delivery-governance"]
    if len(governance) != 1 or governance[0].meta["state"] not in {"confirmed", "approved"}:
        blockers.append("A confirmed delivery governance decision is required")
    else:
        policy = governance[0].meta
        for field in ("delivery_model", "versioning", "branching", "ci", "recovery", "review_policy", "tracking"):
            if not policy.get(field):
                blockers.append("Delivery governance incomplete: " + field)
        if policy.get("tracking") not in {"repository-only", "jira-hybrid"}:
            blockers.append("Tracking choice must be explicit")
        if policy.get("tracking") == "jira-hybrid" and check_tracking:
            from v2_tracking import readiness as tracking_readiness
            pending_start = [t for t in tasks if model.elements[t].meta["state"] in {"ready", "backlog"}]
            if pending_start:
                blockers.extend(tracking_readiness(model, pending_start)["blockers"])
    all_tasks = model.by_kind("task")
    selected = [model.elements[t] for t in tasks]
    plans = {p for task in selected for p in task.targets("plan")}
    if not plans:
        blockers.append("No plan owns this TASK scope")
    completeness = []
    for identifier in sorted(plans):
        plan = model.elements[identifier]
        if plan.kind != "plan" or plan.meta["state"] not in {"confirmed", "approved"}:
            blockers.append("Unconfirmed plan: " + identifier)
        requested = plan.targets("requirements")
        owned = [t for t in all_tasks if identifier in t.targets("plan") and t.meta["state"] != "cancelled"]
        from v2_features import task_requirements
        covered = set()
        for task in owned:
            covered.update(task_requirements(model, task))
        missing = sorted(requested - covered)
        extra = sorted(covered - requested)
        policy = plan.meta.get("planning_policy")
        if policy not in {"complete", "incremental-authorized"}:
            blockers.append("Explicit planning policy required: " + identifier)
        if missing and policy != "incremental-authorized":
            blockers.append("Full plan incomplete: " + ", ".join(missing))
        if extra:
            blockers.append("Tasks add undeclared plan scope: " + ", ".join(extra))
        completeness.append({"plan": identifier, "status": "partial" if missing else "complete",
                             "missing": missing, "extra": extra, "policy": policy})
    continuations, missing_reservation_dependencies = reservation_continuations(model, tasks)
    continued_dependencies = {(item["task_id"], item["dependency_task_id"]) for item in continuations}
    for task in selected:
        primary = [i for i in task.targets("implements") if model.elements[i].kind == "feature"]
        if len(primary) != 1:
            blockers.append("TASK requires exactly one primary feature; other features are contributors: " + task.id)
        if not task.meta.get("owner") or task.meta.get("risk") not in {"low", "medium", "high", "critical"}:
            blockers.append("TASK requires a confirmed owner and risk classification: " + task.id)
        changes = task.meta.get("change_types", [])
        if not changes or set(changes) - {"correction", "evolution", "refactor"}:
            blockers.append("Classify behavior/data/interface change, not just branch name: " + task.id)
        if task.meta.get("reconciliation_required"):
            blockers.append("Migrated TASK semantics require reconciliation: " + task.id)
        if not task.targets("acceptance") or not task.targets("tests"):
            blockers.append("TASK needs acceptance and negative/regression test obligations: " + task.id)
        cases = {c for t in task.targets("tests") for c in model.elements[t].meta.get("cases", [])}
        if not {"positive", "negative", "regression"} <= cases:
            blockers.append("TASK tests must explicitly cover positive, negative and regression cases: " + task.id)
        if not task.meta.get("paths") or not task.meta.get("gates") or not task.meta.get("evidence_scopes"):
            blockers.append("TASK lacks paths, gates or typed evidence scopes: " + task.id)
        for pattern in task.meta.get("paths", []):
            validate_scope_path(pattern)
        for dependency in task.targets("depends_on"):
            target = model.elements[dependency]
            if target.kind == "task" and target.meta["state"] != "done" and (
                    target.meta["state"] != "done-with-reservations"
                    or (task.id, dependency) not in continued_dependencies):
                blockers.append("Unfinished dependency: " + dependency)
    from v2_quality import obligations
    blockers.extend(obligations(model, tasks)["blockers"])
    return {"status": "blocked" if blockers else "ready", "specification": context["status"],
            "full_plan": completeness, "selected_tasks": tasks, "blockers": sorted(set(blockers)),
            "fingerprint": context["fingerprint"], "context": context, "authorization": "not-assessed",
            "reservation_continuations": continuations,
            "pending_reservation_dependencies": missing_reservation_dependencies}


def validate_scope_path(value: str):
    if (not value or value.startswith(("/", "\\", ".git/", ".lks-sdd/", DOCS + "/")) or
            "\\" in value or ":" in value or ".." in value.split("/") or value in {"*", "**", "."}):
        raise ContractError("Unsafe or blanket implementation scope: " + value)


def work_inventory(root: Path) -> dict[str, str]:
    """Hash all bounded nonsecret working files, including untracked ones; no Git hooks."""
    hashes, entries, size = {}, 0, 0
    for directory, folders, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in folders:
            path = parent / name
            if is_root_git_metadata(root, parent, name) and is_link(path):
                raise ContractError("Working tree link/junction requires explicit reconciliation")
        folders[:] = sorted(d for d in folders if d.casefold() not in SKIP_DIRS and d != ".lks-sdd"
                            and (parent / d).relative_to(root).as_posix() != DOCS)
        for name in folders + files:
            entries += 1
            if entries > 50000:
                raise ContractError("Working tree inventory exceeds bound")
            path = parent / name
            if is_link(path):
                raise ContractError("Working tree link/junction requires explicit reconciliation")
            if is_root_git_metadata(root, parent, name):
                continue
            if path.is_dir() and (path / ".git").exists():
                raise ContractError("Nested repository needs its own explicit scope")
        for name in sorted(files):
            if is_root_git_metadata(root, parent, name):
                continue
            if SECRET_NAME.search(name):
                continue
            path = parent / name
            relative = path.relative_to(root).as_posix()
            data = read_bytes(root, relative, limit=64 * 1024 * 1024)
            size += len(data)
            if size > 256 * 1024 * 1024:
                raise ContractError("Working tree byte budget exceeded")
            hashes[relative] = sha(data)
    return hashes


def current_authorization(model: Model, tasks: list[str], environment: str, *, at: str | None = None) -> dict:
    assessment = planning(model, tasks)
    if assessment["status"] != "ready":
        raise ContractError("; ".join(assessment["blockers"]))
    at_time = timestamp(at or now())
    matches = []
    for item in model.by_kind("authorization"):
        value = item.meta
        if value["state"] != "active" or value.get("environment") != environment or not set(tasks) <= item.targets("authorizes"):
            continue
        if not timestamp(value["approved_at"]) <= at_time < timestamp(value["expires_at"]):
            continue
        scope = sorted(item.targets("authorizes"))
        current = planning(model, scope)
        if current["status"] == "ready" and value.get("contract_fingerprint") == current["fingerprint"]:
            matches.append(item)
    if not matches:
        raise ContractError("AUTH absent, revoked, expired or stale for this scope/environment")
    chosen = max(matches, key=lambda e: (e.meta["approved_at"], e.id))
    return {"status": "authorized", "authorization_id": chosen.id, "scope": sorted(chosen.targets("authorizes")),
            "fingerprint": chosen.meta["contract_fingerprint"], "identity_assurance": "declared-not-authenticated"}


def authorize(model: Model, tasks: list[str], *, actor: str, role: str, environment: str,
              approved_at: str, expires_at: str, reason: str, authorized_hash: str | None = None) -> dict:
    model.require_valid()
    ensure_idle(model.root)
    assessment = planning(model, tasks)
    if assessment["status"] != "ready":
        raise ContractError("; ".join(assessment["blockers"]))
    if not all(v.strip() for v in (actor, role, environment, reason)):
        raise ContractError("Declared actor/role, environment and reason required")
    if timestamp(expires_at) <= timestamp(approved_at) or timestamp(approved_at) > timestamp(now()):
        raise ContractError("Invalid authorization validity window")
    try:
        existing = current_authorization(model, tasks, environment)
        return {**existing, "status": "reused", "writes": [], "human_confirmations_required": 0}
    except ContractError:
        pass
    identifier = next_id(model, "AUTH")
    path, data = record(model, identifier, "authorization", "Autorización de implementación", reason,
                        state="active", actor=actor, role=role, environment=environment,
                        approved_at=approved_at, expires_at=expires_at,
                        contract_fingerprint=assessment["fingerprint"],
                        relations={"authorizes": sorted(tasks)}, identity_assurance="declared-not-authenticated")
    changes = {path: data}
    result = preview(model.root, changes, sources=model.hashes, operation="authorize-execution")
    return apply(model.root, changes, result, authorized_hash, validator=lambda: load(model.root).require_valid()) if authorized_hash else result


def is_active_execution(execution: Element) -> bool:
    """Whether a v2 execution remains in its normative, continuable lifecycle."""
    return execution.kind == "execution" and execution.meta.get("state") in ACTIVE_EXECUTION_STATES


def is_active_execution_state(state: str) -> bool:
    """Classify a serialized execution state without granting record authority."""
    return state in ACTIVE_EXECUTION_STATES


def active_execution(model: Model, tasks: list[str] | None = None):
    scope = set(tasks or [])
    matches = [e for e in model.by_kind("execution") if is_active_execution(e)
               and (not scope or scope <= e.targets("implements"))]
    if len(matches) != 1:
        raise ContractError("Exactly one active execution is required for this TASK scope")
    return matches[0]


def start(model: Model, tasks: list[str], environment: str, *, actor: str, at: str,
          authorized_hash: str | None = None, technology=None) -> dict:
    assessment = planning(model, tasks)
    if assessment["status"] != "ready":
        raise ContractError("; ".join(assessment["blockers"]))
    auth = current_authorization(model, tasks, environment)
    for existing in model.by_kind("execution"):
        if is_active_execution(existing) and existing.targets("implements") & set(tasks):
            raise ContractError("Existing execution: resume or reconcile; do not create another")
    if any(model.elements[t].meta["state"] != "ready" for t in tasks):
        raise ContractError("Only ready TASKs may start")
    # Test seams inject an assessor; public commands always use the strict adapter.
    if technology is None:
        from v2_verification import technology_readiness
        technology = technology_readiness
    technical = technology(model, tasks, environment)
    if technical["status"] != "documented":
        raise ContractError("Technology is not authorized: " + str(technical))
    inventory = work_inventory(model.root)
    identifier, checkpoint = next_id(model, "EXEC"), next_id(model, "CKPT")
    path, data = record(model, identifier, "execution", "Ejecución autorizada", "Ámbito y base fijados antes de modificar código.",
                        state="in-progress", actor=actor, environment=environment, started_at=at,
                        contract_fingerprint=auth["fingerprint"], baseline_files=inventory,
                        source_hashes=dict(model.hashes), technology_assessment=technical,
                        inherited_reservations=assessment["reservation_continuations"],
                        relations={"implements": tasks, "authorizes": [auth["authorization_id"]]})
    ckpath, ckdata = record(model, checkpoint, "checkpoint", "Inicio de trabajo", "Implementación pendiente; no hay verificación ni entrega acreditadas.",
                            state="active", recorded_at=at, next_action="Implementar las tareas autorizadas", files=inventory,
                            relations={"execution": [identifier], "implements": tasks})
    changes = {path: data, ckpath: ckdata, **edit_elements(model, {
        t: dict(model.elements[t].meta, state="in-progress", execution_id=identifier) for t in tasks})}
    corrective = {p.id: dict(p.meta, correction_execution=identifier) for p in model.by_kind("problem")
                  if p.meta.get("correction_authorized") and p.targets("affects") <= set(tasks) and p.meta["state"] != "resolved"}
    changes.update(edit_elements(model, corrective))
    result = preview(model.root, changes, sources=model.hashes, operation="start-execution")
    return apply(model.root, changes, result, authorized_hash, validator=lambda: load(model.root).require_valid()) if authorized_hash else result


def diff_guard(model: Model, execution=None, *, tasks: list[str] | None = None) -> dict:
    execution = execution or active_execution(model, tasks)
    if "baseline_files" not in execution.meta:
        raise ContractError("Historical execution has no v2 baseline: reconcile and authorize a new execution")
    current = work_inventory(model.root)
    baseline = execution.meta["baseline_files"]
    changed = sorted(p for p in set(baseline) | set(current) if baseline.get(p) != current.get(p))
    tasks = sorted(execution.targets("implements"))
    patterns = [p for t in tasks for p in model.elements[t].meta.get("paths", [])]
    unauthorized = [p for p in changed if not any(fnmatch.fnmatchcase(p, pattern) for pattern in patterns)]
    critical = [p for p in changed if re.search(r"(?i)(^|[/_.-])(tests?|gates?|polic(?:y|ies)|observers?|lock|security|ci)([/_.-]|$)", p)
                or Path(p).name.lower() in {"package.json", "pyproject.toml", "requirements.txt", "pom.xml", "build.gradle",
                                           "cargo.toml", "go.mod", "composer.json", "gemfile", "dockerfile"}
                or Path(p).suffix.lower() in {".csproj", ".fsproj", ".props", ".targets"}]
    context = execution_context(model, tasks)
    contract_changed = context["fingerprint"] != execution.meta["contract_fingerprint"]
    review = execution.meta.get("reviewed_diff")
    subject = fingerprint({"files": current, "changed": changed, "contract": context["fingerprint"]})
    blockers = (["Changes outside authorized paths: " + ", ".join(unauthorized)] if unauthorized else [])
    if contract_changed:
        blockers.append("Contract differs from approved execution baseline; replan/reauthorize")
    if critical and review != subject:
        blockers.append("Changes to tests/policy/dependencies require exact diff review")
    return {"status": "blocked" if blockers else "within-scope", "changed": changed,
            "unauthorized": unauthorized, "sensitive_review": critical, "contract_changed": contract_changed,
            "diff_fingerprint": subject, "blockers": blockers, "files": current,
            "semantic_review": "required", "identity_assurance": "not-authenticated"}


def review_diff(model: Model, *, tasks: list[str] | None = None, actor: str, reason: str, observed_diff: str,
                authorized_hash: str | None = None) -> dict:
    execution = active_execution(model, tasks)
    guard = diff_guard(model, execution)
    if guard["unauthorized"] or guard["contract_changed"] or guard["diff_fingerprint"] != observed_diff:
        raise ContractError("A diff review cannot authorize changed scope or stale material")
    if not actor.strip() or not reason.strip():
        raise ContractError("Explicit reviewer and reason required")
    changes = edit_elements(model, {execution.id: dict(execution.meta, reviewed_diff=observed_diff,
                                                      diff_reviewer=actor, diff_reason=reason)})
    result = preview(model.root, changes, sources=model.hashes, operation="review-exact-diff")
    return apply(model.root, changes, result, authorized_hash) if authorized_hash else result


def resume(model: Model, tasks: list[str]) -> dict:
    execution = active_execution(model, tasks)
    reasons = []
    try:
        current_authorization(model, tasks, execution.meta["environment"])
    except ContractError as exc:
        reasons.append(str(exc))
    guard = diff_guard(model, execution)
    reasons += guard["blockers"]
    if execution.meta["state"] == "blocked":
        reasons.append("Execution requires reconciliation")
    for problem in model.by_kind("problem"):
        if problem.meta["state"] != "resolved" and problem.targets("affects") & set(tasks):
            reasons.append("Open problem: " + problem.id)
    checkpoints = [e for e in model.by_kind("checkpoint") if execution.id in e.targets("execution")]
    checkpoint = max(checkpoints, key=lambda e: (e.meta.get("recorded_at", ""), e.id), default=None)
    if checkpoint and checkpoint.meta.get("files") != guard["files"]:
        reasons.append("Working files changed after checkpoint; reconcile observed changes")
    return {"status": "reconcile-recommended" if reasons else "continue-recommended", "execution": execution.id,
            "task_ids": tasks, "reasons": reasons, "checkpoint": checkpoint.id if checkpoint else None,
            "next_action": checkpoint.meta.get("next_action") if checkpoint else "Review execution context",
            "writes": []}


def checkpoint(model: Model, *, tasks: list[str] | None = None, state: str, actor: str, at: str, summary: str, next_action: str,
               authorized_hash: str | None = None) -> dict:
    if state not in {"paused", "blocked", "in-progress", "in-review", "cancelled"}:
        raise ContractError("Unsupported continuity state")
    execution = active_execution(model, tasks)
    tasks = sorted(execution.targets("implements"))
    if state in {"in-progress", "in-review"}:
        current_authorization(model, tasks, execution.meta["environment"])
        guard = diff_guard(model, execution)
        if guard["status"] == "blocked":
            raise ContractError("; ".join(guard["blockers"]))
        if any(p.meta["state"] != "resolved" and p.targets("affects") & set(tasks)
               and p.meta.get("correction_execution") != execution.id for p in model.by_kind("problem")):
            raise ContractError("Open problems prevent normal resumption/review")
    if not summary.strip() or not next_action.strip() or not actor.strip():
        raise ContractError("Checkpoint requires observed summary, actor and safe next action")
    inventory = work_inventory(model.root)
    previous = [entry for entry in model.by_kind("checkpoint") if execution.id in entry.targets("execution")]
    latest = max(previous, key=lambda item: (item.meta.get("recorded_at", ""), item.id), default=None)
    if (latest and latest.meta.get("lifecycle_state") == state
            and latest.meta.get("next_action") == next_action
            and latest.body.strip().endswith(summary.strip())):
        return {"status": "reused", "checkpoint": latest.id, "execution": execution.id,
                "task_ids": tasks, "writes": []}
    identifier = next_id(model, "CKPT")
    path, data = record(model, identifier, "checkpoint", "Continuidad de trabajo", summary,
                        state="active", lifecycle_state=state, actor=actor, recorded_at=at, next_action=next_action,
                        files=inventory, relations={"execution": [execution.id], "implements": tasks})
    changes = {path: data, **edit_elements(model, {
        execution.id: dict(execution.meta, state=state),
        **{t: dict(model.elements[t].meta, state=state if state != "paused" else "in-progress") for t in tasks}})}
    if state == "blocked":
        problem = next_id(model, "PROB")
        ppath, pdata = record(model, problem, "problem", "Bloqueo observado", summary, state="open",
                              recorded_at=at, relations={"affects": tasks, "execution": [execution.id]})
        changes[ppath] = pdata
    result = preview(model.root, changes, sources=model.hashes, operation="checkpoint-" + state)
    return apply(model.root, changes, result, authorized_hash, validator=lambda: load(model.root).require_valid()) if authorized_hash else result


def report_problem(model: Model, tasks: list[str], *, description: str, actor: str, at: str,
                   authorized_hash: str | None = None) -> dict:
    if not tasks or any(t not in model.elements or model.elements[t].kind != "task" for t in tasks):
        raise ContractError("Problem needs existing TASKs")
    identifier = next_id(model, "PROB")
    path, data = record(model, identifier, "problem", "Hallazgo posterior", description, state="open",
                        actor=actor, recorded_at=at, relations={"affects": tasks})
    changes = {path: data, **edit_elements(model, {t: dict(model.elements[t].meta, health="needs-reverification") for t in tasks})}
    result = preview(model.root, changes, sources=model.hashes, operation="report-problem")
    return apply(model.root, changes, result, authorized_hash) if authorized_hash else result


def semantic_merge(base: Model, incoming: Model, current: Model) -> dict:
    """Conservative three-way conflicts; no assertion of universal semantic compatibility."""
    errors, review = [], []
    for model in (base, incoming, current):
        errors.extend(model.errors)
    if len({m.manifest["project_id"] for m in (base, incoming, current)}) != 1:
        raise ContractError("Cannot merge different projects")
    def values(model):
        return {i: fingerprint(e.normative()) for i, e in model.elements.items()}
    original, left, right = values(base), values(incoming), values(current)
    left_changes = {i for i in set(original) | set(left) if original.get(i) != left.get(i)}
    right_changes = {i for i in set(original) | set(right) if original.get(i) != right.get(i)}
    for identifier in left_changes & right_changes:
        if left.get(identifier) != right.get(identifier):
            errors.append("Concurrent identity/contract edit: " + identifier)
    for identifier in left_changes:
        entry = incoming.elements.get(identifier)
        if not entry:
            continue
        impact = entry.targets()
        impact.update(e.id for e in incoming.elements.values() if identifier in e.targets())
        if impact & right_changes or entry.kind in {"rule", "constraint", "applicability"} and right_changes:
            review.append(identifier)
    return {"status": "conflict" if errors else "semantic-review-required" if review else "no-structural-conflict",
            "errors": sorted(set(errors)), "shared_contract_review": sorted(set(review)),
            "semantic_acceptance": "not-assessed", "distributed_lock": False, "writes": []}
