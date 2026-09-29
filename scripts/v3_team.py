"""Assignments and partial handoffs are immutable events, with explicit acceptance."""
from v3_contract import ContractError, element, load, now
from v3_policy import operator, member, policy_for, active_period
from v3_storage import prepare


def assignment(model, task):
    records = [e for e in model.by_kind("assignment") if e.data.get("task") == task.uid and e.data.get("status", "accepted") == "accepted"]
    replaced = {e.data.get("previous") for e in records}
    tips = [e for e in records if e.uid not in replaced]
    if len(tips) > 1: raise ContractError("Asignaciones concurrentes; reconciliar responsables antes de continuar")
    return tips[0] if tips else None


def owners(model, task):
    current = assignment(model, task)
    owner = current.data["owner"] if current else task.data["owner"]
    member(model, owner, "implement")
    result = [{"member": owner, "scope": task.data["scope"], "handoff": None}]
    handoffs = [e for e in model.by_kind("handoff") if e.data.get("task") == task.uid]
    replaced = {e.data.get("previous") for e in handoffs}
    for handoff in handoffs:
        if handoff.uid in replaced or handoff.data.get("status") != "accepted" or not active_period(handoff.data): continue
        if handoff.data.get("assignment") != (current.uid if current else None): continue
        if handoff.data.get("task_basis") != task.digest(): continue
        member(model, handoff.data["recipient"], "implement")
        result.append({"member": handoff.data["recipient"], "scope": handoff.data["scope"], "handoff": handoff.uid})
    return result


def contains(scope, path):
    return any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in scope)


def permitted_scope(model, task, actor):
    rows = owners(model, task)
    mine = [p for row in rows if row["member"] == actor for p in row["scope"]]
    if not mine: raise ContractError("La tarea corresponde a otro compañero; registre el traspaso")
    return mine


def assign(root, actor, task_id, recipient, reason, *, accept=False, previous=None):
    model = load(root).require_valid(); task = model.get(task_id, "task")
    policy = policy_for(model, task)
    identity = operator(model, actor, "implement" if accept else "assign", policy)
    target = member(model, recipient, "implement")
    if not reason.strip(): raise ContractError("Indique el motivo del cambio de responsable")
    old = assignment(model, task)
    requires = policy.data.get("assignment_acceptance", policy.data.get("profile") != "individual-brief")
    if accept:
        offer = model.get(previous, "assignment")
        if offer.data.get("status") != "offered" or offer.data["owner"] != identity["member"] or target.uid != identity["member"]:
            raise ContractError("La nueva persona responsable debe aceptar la asignación ofrecida")
        if offer.data["task"] != task.uid or offer.data["previous"] != (old.uid if old else None):
            raise ContractError("La responsabilidad cambió desde la oferta")
        if offer.data.get("task_basis") != task.digest(): raise ContractError("La tarea cambió desde la oferta; revise el relevo concreto")
        if any(e.data.get("offer") == offer.uid for e in model.by_kind("assignment")):
            raise ContractError("La oferta ya tiene respuesta")
    event = element("assignment", "Responsabilidad de " + task.id, reason, task=task.uid,
                    owner=target.uid, actor=identity, previous=old.uid if old else None, recorded_at=now(),
                    offer=previous if accept else None, status="accepted" if accept or not requires else "offered")
    from v3_workflow import state, plan_for
    from v3_approval import task_authority
    event["meta"]["data"].update(task_basis=task.digest(), delivered_state=state(model, task), pending=[reason], policy=policy.digest(),
                                previous_owner=old.data["owner"] if old else task.data["owner"],
                                authorization=task_authority(model, task, plan_for(model, task), "execution")["decisions"])
    event["meta"].update(state="active", nature="decision")
    return prepare(root, [event], "assign")


def handoff(root, actor, task_id, recipient, scope, reason, *, previous=None, accept=False):
    model = load(root).require_valid(); task = model.get(task_id, "task")
    identity = operator(model, actor, "implement", policy_for(model, task))
    recipient = member(model, recipient, "implement").uid
    old = assignment(model, task)
    owner = old.data["owner"] if old else task.data["owner"]
    if not scope or not all(contains(task.data["scope"], p) for p in scope) or not reason.strip():
        raise ContractError("Concrete alcance parcial y motivo dentro de la tarea")
    if accept:
        source = model.get(previous, "handoff")
        if source.data.get("status") != "offered" or source.data["recipient"] != identity["member"]:
            raise ContractError("La recepción debe aceptarla el compañero destinatario")
        if source.data["task"] != task.uid or source.data["scope"] != scope or recipient != identity["member"]:
            raise ContractError("La aceptación no coincide con el traspaso presentado")
        if source.data["assignment"] != (old.uid if old else None): raise ContractError("La responsabilidad cambió desde la oferta")
        if source.data.get("task_basis") != task.digest(): raise ContractError("La tarea cambió desde la oferta; revise la porción entregada")
        if any(e.data.get("previous") == source.uid for e in model.by_kind("handoff")):
            raise ContractError("El traspaso ya tiene respuesta")
    elif identity["member"] != owner:
        raise ContractError("El responsable actual debe ofrecer el traspaso")
    else:
        for row in owners(model, task)[1:]:
            if any(contains(row["scope"], p) for p in scope) or any(contains(scope, p) for p in row["scope"]):
                raise ContractError("El alcance ya tiene un traspaso aceptado; reasigne o reconcilie")
    event = element("handoff", "Traspaso de " + task.id, reason, task=task.uid, recipient=recipient,
                    scope=scope, actor=identity, assignment=old.uid if old else None, previous=previous,
                    status="accepted" if accept else "offered", recorded_at=now())
    from v3_workflow import state, plan_for
    from v3_approval import task_authority
    event["meta"]["data"].update(delivered_state=state(model, task), pending=[reason],
                                task_basis=task.digest(), policy=policy.digest() if (policy := policy_for(model, task)) else None,
                                authorization=task_authority(model, task, plan_for(model, task), "execution")["decisions"])
    event["meta"].update(state="active", nature="decision")
    return prepare(root, [event], "handoff")
