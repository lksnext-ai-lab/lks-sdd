"""Optional Jira projection receipts; no connector, network or remote authority."""
from __future__ import annotations

import uuid
from v2_contract import ContractError, DOCS, fingerprint, make_element, render_document
from v2_authoring import edit_elements
from v2_lifecycle import next_id
from v2_storage import apply, preview


def policy(model):
    entries = [e for e in model.by_kind("decision") if e.meta.get("category") == "tracking"]
    if len(entries) != 1 or entries[0].meta["state"] not in {"confirmed", "approved"}:
        raise ContractError("One confirmed tracking policy required")
    value = entries[0].meta
    if value.get("mode") not in {"repository-only", "jira-hybrid"}:
        raise ContractError("Invalid tracking mode")
    if value["mode"] == "jira-hybrid" and (
            not value.get("site") or not value.get("project_key") or
            value.get("reporting_scope") not in {"projection-only", "milestone-reporting"} or
            value.get("coordination_gate") not in {"advisory", "required-before-execution"}):
        raise ContractError("Jira projection needs explicit binding and reporting policy")
    for receipt in model.by_kind("receipt"):
        binding = receipt.meta.get("binding")
        if binding and (value["mode"] != "jira-hybrid" or binding != {k: value.get(k) for k in ("site", "project_key")}):
            raise ContractError("Durable remote receipts prohibit silent detach or rebind; reconcile the project identity explicitly")
    return value


def projection(model, task_id):
    if task_id not in model.elements or model.elements[task_id].kind != "task":
        raise ContractError("Projection requires a canonical TASK")
    task = model.elements[task_id]
    marker = "LKS-SDD-PROJECT: " + model.manifest["project_id"] + "; TASK: " + task_id
    material = {"marker": marker, "task": task.normative(), "state": task.meta["state"], "source": task.source()}
    return {"marker": marker, "fingerprint": fingerprint(material), "material": material}


def active_receipts(model, task_id):
    receipts = [e for e in model.by_kind("receipt") if task_id in e.targets("sources")]
    reconciled = {e.meta["reconciles"] for e in receipts if e.meta.get("reconciles")}
    return [e for e in receipts if e.id not in reconciled]


def readiness(model, tasks):
    blockers, warnings = [], []
    try:
        config = policy(model)
    except ContractError as exc:
        return {"status": "blocked", "blockers": [str(exc)], "warnings": []}
    if config["mode"] == "repository-only":
        return {"status": "local", "blockers": [], "warnings": [], "remote_access": "not-required"}
    for task in tasks:
        expected = projection(model, task)["fingerprint"]
        receipts = active_receipts(model, task)
        unresolved = [e for e in receipts if e.meta.get("result") in {"uncertain", "conflict", "authorized"}]
        matched = any(e.meta.get("result") == "succeeded" and e.meta.get("projection_fingerprint") == expected for e in receipts)
        if unresolved or not matched:
            message = task + ": projection requires reconciliation or synchronization"
            (blockers if config["coordination_gate"] == "required-before-execution" else warnings).append(message)
    return {"status": "blocked" if blockers else "advisory" if warnings else "synchronized",
            "blockers": blockers, "warnings": warnings, "remote_access": "not-performed"}


def authorize_projection(model, task_id, *, actor, at, duplicate_check, authorized_hash=None):
    config = policy(model)
    if config["mode"] != "jira-hybrid":
        raise ContractError("Repository-only does not authorize remote operations")
    from v2_lifecycle import planning, timestamp
    timestamp(at)
    assessment = planning(model, [task_id], check_tracking=False)
    if assessment["status"] != "ready":
        raise ContractError("Canonical plan must be ready before remote projection: " + "; ".join(assessment["blockers"]))
    if duplicate_check not in {"no-match", "matched"} or not actor.strip():
        raise ContractError("Explicit actor and fresh remote duplicate-check observation required")
    if any(e.meta.get("result") in {"authorized", "uncertain", "conflict"} for e in active_receipts(model, task_id)):
        raise ContractError("Reconcile the existing uncertain/in-flight receipt before another write")
    projected = projection(model, task_id)
    identifier = next_id(model, "SYNC")
    meta = make_element(identifier, "receipt", "Autorización de proyección Jira", "Autoriza una operación remota descrita; el plugin no la ejecuta.",
                        uid=str(uuid.uuid5(uuid.NAMESPACE_URL, model.manifest["project_id"] + ":" + identifier)),
                        state="active", nature="decision", result="authorized", actor=actor, recorded_at=at,
                        marker=projected["marker"], projection_fingerprint=projected["fingerprint"],
                        binding={k: config[k] for k in ("site", "project_key")},
                        action="create" if duplicate_check == "no-match" else "update", relations={"sources": [task_id]})
    path = DOCS + "/04-delivery/tracking/" + identifier + ".md"
    changes = {path: render_document("receipt", "Operación Jira", [meta])}
    result = preview(model.root, changes, sources=model.hashes, operation="authorize-jira-projection")
    return apply(model.root, changes, result, authorized_hash) if authorized_hash else {**result, "projection": projected, "remote_writes": []}


def record_result(model, identifier, observation, *, authorized_hash=None, reconcile=False):
    item = model.elements.get(identifier)
    if not item or item.kind != "receipt":
        raise ContractError("Receipt not found")
    if not any(e.id == identifier for t in item.targets("sources") for e in active_receipts(model, t)):
        raise ContractError("Receipt already has a result; preserve append-only history")
    allowed = {"uncertain", "conflict"} if reconcile else {"authorized"}
    if item.meta.get("result") not in allowed:
        raise ContractError("Receipt is not eligible; preserve terminal history")
    result = observation.get("result")
    if result not in {"succeeded", "failed", "conflict", "uncertain"}:
        raise ContractError("Unknown observed result")
    if result == "succeeded" and (observation.get("observed_marker") != item.meta["marker"] or
            observation.get("observed_projection_fingerprint") != item.meta["projection_fingerprint"] or
            not observation.get("external_id") or not str(observation.get("external_key", "")).startswith(item.meta["binding"]["project_key"] + "-") or
            observation.get("site") != item.meta["binding"]["site"] or
            observation.get("project_key") != item.meta["binding"]["project_key"]):
        raise ContractError("Observed remote identity/marker/fingerprint do not match authorized projection")
    # All remote results are append-only, including the result of an authorized
    # attempt. An uncertain write can only be reconciled by an explicit read.
    new_id = next_id(model, "SYNC")
    values = dict(item.meta, id=new_id, uid=str(uuid.uuid5(uuid.NAMESPACE_URL, model.manifest["project_id"] + ":" + new_id)),
                  state="completed", result=result, observation=observation, reconciles=identifier)
    data = render_document("receipt", "Resultado Jira", [{"meta": values, "body": "Resultado observado; no concede autorización ni verificación local."}])
    changes = {DOCS + "/04-delivery/tracking/" + new_id + ".md": data}
    plan = preview(model.root, changes, sources=model.hashes, operation="record-jira-result")
    return apply(model.root, changes, plan, authorized_hash) if authorized_hash else plan


def milestone(model, task_id, request, *, authorized_hash=None):
    config = policy(model)
    if config.get("mode") != "jira-hybrid" or config.get("reporting_scope") != "milestone-reporting":
        raise ContractError("Milestone reporting requires an explicit reporting policy")
    event = request.get("event")
    expected_states = {"started": {"in-progress"}, "paused": {"in-progress"}, "blocked": {"blocked"},
                       "review-requested": {"in-review"}, "verified": {"done"}, "cancelled": {"cancelled"}}
    task = model.elements.get(task_id)
    if event not in expected_states or not task or task.meta["state"] not in expected_states[event]:
        raise ContractError("Milestone does not match the canonical observed state")
    known = [e for e in active_receipts(model, task_id) if e.meta.get("result") == "succeeded" and e.meta.get("action") in {"create", "update"}]
    if not known or any(e.meta.get("result") in {"uncertain", "conflict", "authorized"} for e in active_receipts(model, task_id)):
        raise ContractError("Reconcile remote identity before reporting a milestone")
    issue = known[-1].meta["observation"]
    observation = request.get("observed_issue", {})
    if any(observation.get(k) != issue.get(k) for k in ("external_id", "external_key", "observed_marker")):
        raise ContractError("Fresh observed remote issue must match canonical receipt")
    actor, at, reason = request.get("actor"), request.get("recorded_at"), request.get("reason")
    if not actor or not at or not reason:
        raise ContractError("Milestone authorization needs actor, observation time and reason")
    action = request.get("action", "comment")
    transition = request.get("transition")
    if action not in {"comment", "transition"} or action == "transition" and config.get("transitions", {}).get(event) != transition:
        raise ContractError("Remote transition must be explicitly mapped by the tracking policy")
    material = projection(model, task_id)
    identifier = next_id(model, "SYNC")
    from v2_contract import make_element, render_document
    entry = make_element(identifier, "receipt", "Hito Jira: " + event,
                         reason + "\n\nFuente local: " + task.source()["path"] + "#" + task_id.lower(),
                         uid=str(uuid.uuid5(uuid.NAMESPACE_URL, model.manifest["project_id"] + ":" + identifier)),
                         state="active", nature="decision", result="authorized", action=action, event=event,
                         actor=actor, recorded_at=at, marker=material["marker"], projection_fingerprint=material["fingerprint"],
                         transition=transition, remote_identity={k: issue[k] for k in ("external_id", "external_key")},
                         binding={k: config[k] for k in ("site", "project_key")}, relations={"sources": [task_id]})
    path = DOCS + "/04-delivery/tracking/" + identifier + ".md"
    changes = {path: render_document("receipt", "Hito de seguimiento", [entry])}
    plan = preview(model.root, changes, sources=model.hashes, operation="authorize-jira-milestone")
    return apply(model.root, changes, plan, authorized_hash) if authorized_hash else {**plan, "remote_writes": []}
