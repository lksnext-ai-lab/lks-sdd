"""Explicit revocation, correction, acceptance and delivery observations for v2."""
from __future__ import annotations

import uuid
from v2_contract import ContractError, DOCS, fingerprint, load, make_element, render_document
from v2_authoring import edit_elements, history_changes
from v2_lifecycle import (active_execution, current_authorization, diff_guard, is_active_execution,
                          next_id, timestamp, now)
from v2_storage import apply, preview


def finish(model, changes, operation, authorized_hash):
    plan = preview(model.root, changes, sources=model.hashes, operation=operation)
    return apply(model.root, changes, plan, authorized_hash, validator=lambda: load(model.root).require_valid()) if authorized_hash else plan


def receipt_record(model, category, body, values):
    """Build one immutable receipt so compound transitions can stay atomic."""
    identifier = next_id(model, "REC")
    if not values.get("actor") or not values.get("recorded_at") or not body.strip():
        raise ContractError("Explicit actor, observed time and reason are required")
    if timestamp(values["recorded_at"]) > timestamp(now()):
        raise ContractError("Cannot record a future observation as fact")
    data = make_element(identifier, "receipt", category, body,
                        uid=str(uuid.uuid5(uuid.NAMESPACE_URL, model.manifest["project_id"] + ":" + identifier)),
                        nature="decision" if category in {"result-review", "result-reservation-review",
                                                           "visual-proposal-review", "delivery-approval",
                                                           "integration-diff-review", "dependency-reservation-continuation"} else "fact", category=category, **values)
    changes = {DOCS + "/04-delivery/receipts/" + identifier + ".md": render_document("receipt", category, [data])}
    return identifier, changes


def receipt(model, category, body, values, *, authorized_hash=None):
    identifier, changes = receipt_record(model, category, body, values)
    return finish(model, changes, "record-" + category, authorized_hash)


def revoke(model, identifier, *, actor, reason, at, authorized_hash=None):
    item = model.elements.get(identifier)
    execution_auth = item and item.kind == "authorization" and item.meta["state"] == "active"
    delivery_auth = item and item.kind == "receipt" and item.meta.get("category") == "delivery-approval" and item.meta["state"] == "approved"
    if not (execution_auth or delivery_auth):
        raise ContractError("Select an active AUTH or approved delivery receipt to revoke")
    if not actor.strip() or not reason.strip():
        raise ContractError("Revocation requires actor and reason")
    timestamp(at)
    changes = edit_elements(model, {identifier: dict(item.meta, state="revoked", revoked_at=at,
                                                    revoked_by=actor, revocation_reason=reason)})
    return finish(model, changes, "revoke-authorization", authorized_hash)


def correction(model, tasks, *, actor, reason, at, replan=False, authorized_hash=None):
    if not tasks or not actor.strip() or not reason.strip():
        raise ContractError("Correction needs TASK scope, actor and observed reason")
    problems = [p for p in model.by_kind("problem") if p.meta["state"] != "resolved" and p.targets("affects") & set(tasks)]
    if not replan and not problems:
        raise ContractError("Record the problem before reopening/correcting work")
    executions = [e for e in model.by_kind("execution") if is_active_execution(e)
                  and e.targets("implements") & set(tasks)]
    if len(executions) > 1 or any(e.targets("implements") != set(tasks) for e in executions):
        raise ContractError("Reconcile the complete affected execution scope explicitly")
    if not replan:
        env = executions[0].meta["environment"] if executions else None
        if env:
            current_authorization(model, tasks, env)
        if executions and diff_guard(model, executions[0])["status"] != "within-scope":
            raise ContractError("Corrective resume cannot waive an out-of-scope or stale diff")
    updates = {}
    for task in tasks:
        entry = model.elements.get(task)
        if not entry or entry.kind != "task":
            raise ContractError("Existing TASKs required")
        updates[task] = dict(entry.meta, state="ready" if replan or not executions else "in-progress", health="needs-reverification")
    for entry in executions:
        updates[entry.id] = dict(entry.meta, state="cancelled" if replan else "in-progress",
                                reconciliation={"actor": actor, "reason": reason, "at": at})
    for problem in problems:
        updates[problem.id] = dict(problem.meta, correction_authorized=True,
                                  correction_execution=executions[0].id if executions and not replan else None)
    if replan:
        for auth in model.by_kind("authorization"):
            if auth.meta["state"] == "active" and auth.targets("authorizes") & set(tasks):
                updates[auth.id] = dict(auth.meta, state="revoked", revocation_reason="Explicit replan: " + reason)
    _, archive = history_changes(model)
    return finish(model, {**archive, **edit_elements(model, updates)}, "replan" if replan else "corrective-resume", authorized_hash)


def accept_result(model, tasks, evidence_id, *, actor, at, reason, authorized_hash=None,
                  reservation_request=None):
    from v2_verification import evidence, engine_hash, reservation_acceptance
    value = evidence(model, evidence_id)
    if value["classification"] not in {"verified", "verified-with-reservations", "not-verified"} or not set(tasks) <= set(value["task_ids"]):
        raise ContractError("Human review requires evidence for the exact selected TASK scope")
    if value["material"]["engine"] != engine_hash():
        raise ContractError("Evidence engine changed")
    if value["classification"] == "verified":
        if reservation_request is not None:
            raise ContractError("Verified evidence does not need reservation acceptance")
        return receipt(model, "result-review", reason, {"actor": actor, "recorded_at": at, "state": "approved",
                       "evidence_id": evidence_id, "evidence_sha256": value["integrity_sha256"],
                       "technical_classification": value["classification"],
                       "identity_assurance": "declared-not-authenticated", "relations": {"verifies": tasks}}, authorized_hash=authorized_hash)
    reservations, reservation_digest = reservation_acceptance(model, tasks, value, reservation_request)
    return receipt(model, "result-reservation-review", reason, {
        "actor": actor, "recorded_at": at, "state": "approved", "evidence_id": evidence_id,
        "evidence_sha256": value["integrity_sha256"], "technical_classification": value["classification"],
        "execution_id": value["execution_id"], "subject": value["subject"], "reservations": reservations,
        "reservation_digest": reservation_digest, "identity_assurance": "declared-not-authenticated",
        "relations": {"verifies": tasks},
    }, authorized_hash=authorized_hash)


def continue_with_reservations(model, tasks, request, *, actor, at, reason, authorized_hash=None):
    """Record one explicit, bounded decision to continue after reserved dependencies."""
    if (not isinstance(request, dict) or request.get("decision") != "continue-with-reservations"
            or not isinstance(request.get("dependency_task_ids"), list) or not request["dependency_task_ids"]):
        raise ContractError("Continuation requires decision and explicit dependency TASK ids")
    if not tasks or any(task not in model.elements or model.elements[task].kind != "task" for task in tasks):
        raise ContractError("Continuation requires existing dependent TASKs")
    dependencies = sorted({
        dependency for task in tasks for dependency in model.elements[task].targets("depends_on")
        if model.elements[dependency].kind == "task" and model.elements[dependency].meta["state"] == "done-with-reservations"
    })
    if dependencies != sorted(set(request["dependency_task_ids"])):
        raise ContractError("Continuation must name exactly the reserved direct dependencies")
    dependency_evidence, inherited = [], []
    for dependency in dependencies:
        evidence_ids = model.elements[dependency].meta.get("evidence_ids", [])
        if not evidence_ids:
            raise ContractError("Reserved dependency has no terminal verification evidence: " + dependency)
        terminal_evidence = evidence_ids[-1]
        receipts = [
            receipt for receipt in model.by_kind("receipt")
            if receipt.meta.get("category") == "result-reservation-review"
            and receipt.meta.get("state") == "approved"
            and dependency in receipt.targets("verifies")
            and receipt.meta.get("evidence_id") == terminal_evidence
        ]
        if not receipts:
            raise ContractError("Reserved dependency lacks an approved reservation receipt: " + dependency)
        receipt_value = max(receipts, key=lambda item: (item.meta.get("recorded_at", ""), item.id)).meta
        from v2_verification import evidence
        value = evidence(model, receipt_value["evidence_id"])
        if (dependency not in value["task_ids"]
                or value["integrity_sha256"] != receipt_value.get("evidence_sha256")
                or receipt_value.get("reservation_digest") != fingerprint(receipt_value.get("reservations", []))):
            raise ContractError("Reserved dependency acceptance receipt is no longer bound to exact evidence")
        dependency_evidence.append({
            "task_id": dependency,
            "evidence_id": value["evidence_id"],
            "evidence_sha256": value["integrity_sha256"],
            "reservation_digest": receipt_value["reservation_digest"],
        })
        inherited.extend({"dependency_task_id": dependency, **reservation}
                         for reservation in receipt_value["reservations"])
    return receipt(model, "dependency-reservation-continuation", reason, {
        "actor": actor, "recorded_at": at, "state": "approved",
        "dependency_evidence": dependency_evidence, "inherited_reservations": inherited,
        "identity_assurance": "declared-not-authenticated",
        "relations": {"affects": sorted(tasks), "depends_on": dependencies},
    }, authorized_hash=authorized_hash)


def validate_flags(request):
    if request.get("operation") not in {"flag-enabled", "flag-disabled"}:
        return
    flags = request.get("flags")
    expected = request["operation"] == "flag-enabled"
    if not isinstance(flags, dict) or not flags or any(not name or value is not expected for name, value in flags.items()):
        raise ContractError("Flag operation requires explicit flag names and matching boolean values")


def delivery_observation(model, request, *, authorized_hash=None):
    """Record separately observed delivery; never deploy or infer it from TASK done."""
    from v2_verification import evidence
    required = ("actor", "recorded_at", "environment", "version", "artifact_digest", "evidence_id", "operation", "reason", "features")
    if any(not request.get(k) for k in required):
        raise ContractError("Delivery observation requires exact environment/version/artifact/evidence/features")
    if request["operation"] not in {"deployed", "rolled-back", "flag-enabled", "flag-disabled", "withdrawn"}:
        raise ContractError("Unsupported observed delivery operation")
    validate_flags(request)
    if request["environment"] not in model.elements or model.elements[request["environment"]].kind != "environment":
        raise ContractError("Explicit documented delivery environment required")
    value = evidence(model, request["evidence_id"])
    if value["classification"] != "verified":
        raise ContractError("Delivery record requires fully verified evidence; accepted reservations cannot promote delivery")
    if request["artifact_digest"] not in value.get("deliverable_artifact_digests", []):
        raise ContractError("Delivered artifact was not captured by the referenced verification")
    if value["environment"] != request["environment"]:
        raise ContractError("Delivery needs verification for its exact environment, not implicit promotion")
    if any(i not in model.elements or model.elements[i].kind != "feature" for i in request["features"]):
        raise ContractError("Delivery references existing feature identities")
    authorization = model.elements.get(request.get("authorization_id"))
    bound = ("environment", "version", "artifact_digest", "operation")
    if not authorization or authorization.meta.get("category") != "delivery-approval" or authorization.meta["state"] != "approved":
        raise ContractError("Separate, explicit delivery approval is required")
    if any(authorization.meta.get(k) != request[k] for k in bound) or authorization.targets("affects") != set(request["features"]):
        raise ContractError("Delivery observation differs from its exact approved scope")
    if (authorization.meta.get("evidence_id") != request["evidence_id"] or
            authorization.meta.get("evidence_sha256") != value["integrity_sha256"] or
            authorization.meta.get("flags", {}) != request.get("flags", {})):
        raise ContractError("Delivery observation changed the exact approved evidence or flag scope")
    if not timestamp(authorization.meta["recorded_at"]) <= timestamp(request["recorded_at"]) <= timestamp(authorization.meta["expires_at"]):
        raise ContractError("Delivery approval was not valid at the observed time")
    from v2_contract import read_bytes, sha
    for gate in ("smoke", "observability", "recovery"):
        proof = request.get("delivery_evidence", {}).get(gate, {})
        if proof.get("status") != "passed" or not proof.get("path") or not proof.get("sha256"):
            raise ContractError("Separate G4 delivery evidence required: " + gate)
        raw = read_bytes(model.root, proof["path"])
        if sha(raw) != proof["sha256"]:
            raise ContractError("Delivery evidence changed: " + gate)
        import json
        observed = json.loads(raw)
        if observed.get("kind") != gate or observed.get("status") != "passed" or any(
                observed.get(k) != request[k] for k in ("environment", "version", "artifact_digest", "operation")):
            raise ContractError("Delivery proof does not identify the exact observed subject: " + gate)
        if observed.get("flags", {}) != request.get("flags", {}):
            raise ContractError("Delivery proof does not identify the observed flag values: " + gate)
        if not timestamp(authorization.meta["recorded_at"]) <= timestamp(observed["observed_at"]) <= timestamp(request["recorded_at"]):
            raise ContractError("Delivery evidence is outside the authorized observation window")
        model.hashes[proof["path"]] = proof["sha256"]
    values = {k: v for k, v in request.items() if k not in {"reason", "features"}}
    values.update(state="completed", evidence_sha256=value["integrity_sha256"],
                  relations={"affects": request["features"], "environments": [request["environment"]]})
    return receipt(model, "delivery-observation", request["reason"], values, authorized_hash=authorized_hash)


def authorize_delivery(model, request, *, authorized_hash=None):
    from v2_verification import evidence
    required = ("actor", "recorded_at", "expires_at", "environment", "version", "artifact_digest", "evidence_id", "operation", "features", "reason")
    if any(not request.get(k) for k in required):
        raise ContractError("Delivery approval requires exact scope, actor, expiry and verification")
    if timestamp(request["expires_at"]) <= timestamp(request["recorded_at"]):
        raise ContractError("Delivery approval expiry must follow approval")
    value = evidence(model, request["evidence_id"])
    if value["classification"] != "verified" or request["artifact_digest"] not in value.get("deliverable_artifact_digests", []):
        raise ContractError("Delivery approval requires a verified deployable artifact, not a log or prototype")
    if request["environment"] not in model.elements or model.elements[request["environment"]].kind != "environment":
        raise ContractError("Document the exact delivery environment")
    if value.get("environment") != request["environment"]:
        raise ContractError("Verification does not cover the delivery environment")
    role = model.elements[request["environment"]].meta.get("role")
    allowed_stages = {"release", "production"} if role == "production" else {"preproduction", "release", "production"}
    if role in {"production", "preproduction"} and value.get("stage") not in allowed_stages:
        raise ContractError("Production delivery cannot inherit development verification")
    if request["operation"] not in {"deployed", "rolled-back", "flag-enabled", "flag-disabled", "withdrawn"}:
        raise ContractError("Unsupported delivery operation")
    validate_flags(request)
    if any(i not in model.elements or model.elements[i].kind != "feature" for i in request["features"]):
        raise ContractError("Document all affected features")
    values = {k: v for k, v in request.items() if k not in {"reason", "features"}}
    values.update(state="approved", evidence_sha256=value["integrity_sha256"],
                  identity_assurance="declared-not-authenticated", relations={"affects": request["features"], "environments": [request["environment"]]})
    return receipt(model, "delivery-approval", request["reason"], values, authorized_hash=authorized_hash)
