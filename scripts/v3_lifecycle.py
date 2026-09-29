"""Reviewable decisions, corrections and checkpoints without rewriting prior facts."""
from v3_contract import ContractError, element, load, now
from v3_policy import operator, policy_for
from v3_approval import descriptor, proposal_ready, approved
from v3_workflow import state, latest
from v3_storage import prepare
from v3_git import subject, observe


def review(root, request_id, selected=None):
    model = load(root).require_valid(); request = model.get(request_id, "request")
    units = proposal_ready(model, request, selected, require_complete=False)
    try: proposal_ready(model, request, selected); planning_coverage = "complete"
    except ContractError as exc: planning_coverage = str(exc)
    validity = approved(model, units)
    desc = descriptor(model, units)
    return {"moment": "Validación de la propuesta funcional y técnica antes de planificar", "request": request.source(),
            "effect": "Aceptar este contenido permite preparar su plan; la implementación se autoriza después",
            "units": [{"source": model.get(k).source(), "part": model.get(k).data.get("part"),
                       "description": model.get(k).body, "details": model.get(k).data,
                       "decision": validity["covered"].get(k), "needs_validation": k not in validity["covered"]} for k in units],
            "descriptor": desc, "planning_coverage": planning_coverage, "next": "Revise qué se hará, qué queda fuera, su solución y criterios; exprese aceptación o cambios sobre estas unidades",
            "writes": []}


def revoke(root, actor, decision_id, reason):
    model = load(root).require_valid(); old = model.get(decision_id)
    if old.kind not in {"decision", "authorization", "exception"}: raise ContractError("Seleccione una decisión revocable")
    permission = "exception" if old.kind == "exception" else "authorize" if old.kind == "authorization" else "approve"
    identity = operator(model, actor, permission)
    if not reason.strip(): raise ContractError("Indique el motivo de revocación")
    event = element(old.kind, "Revocación actual", reason, revokes=old.uid, actor=identity, outcome="revoked",
                    purpose=old.data.get("purpose"), recorded_at=now())
    event["meta"].update(state="revoked", nature="decision")
    return prepare(root, [event], "revoke")


def checkpoint(root, actor, task_id, result, pending, *, classification="progress", analysis=None):
    model = load(root).require_valid(); task = model.get(task_id, "task")
    identity = operator(model, actor, "approve" if classification in {"false-positive", "accepted-risk"} else "implement", policy_for(model, task))
    if classification not in {"progress", "correction", "previous-debt", "deviation", "false-positive", "accepted-risk", "new-scope"}:
        raise ContractError("Tipo de seguimiento desconocido")
    if not result.strip(): raise ContractError("Describa el resultado y los pendientes útiles para continuar")
    if analysis:
        observed = model.get(analysis, "analysis")
        if task.uid not in observed.data["tasks"]: raise ContractError("El hallazgo pertenece a otra tarea")
    old = latest(model, task)
    event = element("problem" if classification != "progress" else "checkpoint", "Continuidad de " + task.id,
                    result, task=task.uid, basis=task.digest(), actor=identity, classification=classification,
                    pending=pending, analysis=analysis, execution=old.uid if old else None, state=state(model, task),
                    subject=subject(model.root, task.data["scope"]), recorded_at=now(),
                    effect="informative-does-not-change-quality-result")
    event["meta"].update(state="observed", nature="fact" if classification in {"progress", "correction", "previous-debt", "deviation"} else "decision")
    return prepare(root, [event], "checkpoint", guards={"git": observe(model.root), "subject": event["meta"]["data"]["subject"]})


def reconcile_migrated(root, actor, changes, statement):
    """Reconcile existing open entities; preserve their IDs and body unless explicitly edited."""
    from v3_authoring import author
    model = load(root).require_valid(); operator(model, actor, "plan")
    if not statement.strip(): raise ContractError("Indique qué correspondencia de trabajo abierto se valida")
    for item in changes:
        old = model.get(item["meta"]["uid"])
        if not old.data.get("legacy") or old.data.get("continuation") == "historical":
            raise ContractError("Solo se reconcilia trabajo heredado abierto; el cerrado conserva su resultado")
        if item["meta"]["data"].get("legacy") != old.data["legacy"]: raise ContractError("Conserve la procedencia original")
        item["meta"]["data"]["continuation"] = "reconciled-content-needs-current-authorization"
    return author(root, actor, changes)
