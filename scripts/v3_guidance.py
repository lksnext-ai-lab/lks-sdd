"""Small didactic views; details remain recoverable by UID/path."""
from v3_contract import ContractError, load
from v3_policy import policy_for, steps_state
from v3_approval import approved, proposal_ready, task_authority
from v3_workflow import state, facts_for, evaluate, valid_exceptions, request_facts

LABELS = {"backlog": "Pendiente de empezar", "in-progress": "En implementación", "implemented": "Implementada; falta comprobar",
          "verified": "Comprobada; falta cerrar", "closed": "Cerrada", "closed-with-reservations": "Cerrada con reservas",
          "paused": "En pausa", "cancelled": "Cancelada", "reconciliation-required": "Necesita revisar un cambio de alcance"}
NEXT = {"backlog": "start", "in-progress": "implement", "implemented": "verify", "verified": "close", "paused": "resume"}


def status(root, *, request_id=None, task_id=None, offset=0, limit=10, task_offset=0, task_limit=10):
    model = load(root).require_valid()
    if limit < 1 or limit > 50 or offset < 0: raise ContractError("Página fuera de límites")
    if task_offset < 0 or not 1 <= task_limit <= 50: raise ContractError("Página de tareas fuera de límites")
    requests = [model.get(request_id, "request")] if request_id else model.by_kind("request")
    rows, issues = [], []
    for request in requests[offset:offset+limit]:
        policy = policy_for(model, request)
        tasks = [t for t in model.by_kind("task") if t.data.get("request") == request.uid and not t.retired and (not task_id or t.uid == model.get(task_id, "task").uid)]
        try: proposal = approved(model, proposal_ready(model, request))["valid"]
        except ContractError as exc: proposal = False; issues.append({"source": request.source(), "cause": str(exc)})
        task_rows = []
        from v3_team import owners, assignment
        for task in tasks[task_offset:task_offset+task_limit]:
            try: current = state(model, task)
            except ContractError as exc: current = "conflict"; issues.append({"source": task.source(), "cause": str(exc)})
            try: assigned = assignment(model, task)
            except ContractError as exc:
                assigned = None; current = "conflict"
                issues.append({"source": task.source(), "cause": str(exc)})
            owner = assigned.data["owner"] if assigned else task.data.get("owner")
            try: contributions = owners(model, task)
            except ContractError as exc: contributions = []; issues.append({"source": task.source(), "cause": str(exc)})
            task_rows.append({"uid": task.uid, "title": task.meta["title"], "state": current, "label": LABELS.get(current, current),
                              "owner": owner, "contributions": contributions, "next_action": NEXT.get(current), "source": task.source()})
        flags = {"proposal-approved": proposal}
        try: flags = request_facts(model, request)
        except ContractError as exc: issues.append({"source": request.source(), "cause": str(exc)})
        steps = steps_state(policy.data, flags, request.data.get("flags", {}))
        active_steps = [s for s in steps if s["state"] in {"available", "needs-decision"}]
        next_step = active_steps[0]["label"] if active_steps else None
        rows.append({"request": request.source(), "title": request.meta["title"], "policy": policy.source(), "steps": steps,
                     "task_total": len(tasks), "next_task_offset": task_offset+task_limit if task_offset+task_limit < len(tasks) else None,
                     "tasks": task_rows, "next": "Prepare y valide la propuesta funcional y técnica concreta" if not proposal else
                     "Prepare el plan de tareas para la propuesta validada" if not tasks else
                     "Siguiente paso: " + next_step + ". Revise sus condiciones y el resultado concreto que se espera" if next_step else
                     "El recorrido configurado está completo; puede consultar el resultado y sus reservas",
                     "recommendation_basis": "Propuesta vigente y evidencia de las tareas de esta petición"})
        if policy.data.get("collaboration"):
            from v31_guidance import interventions
            rows[-1]["journey"] = interventions(model, request.uid)
    return {"project": {"title": model.project.meta["title"], "source": model.project.source()},
            "requests": rows, "total": len(requests), "offset": offset,
            "next_offset": offset+limit if offset+limit < len(requests) else None, "issues": issues,
            "observation": "Documentos y evidencia del checkout actual; no acredita otros clones, PR o despliegue",
            "recommendations": exception_patterns(model),
            "next": "Defina la primera petición en una rama identificada" if not requests else None}


def exception_patterns(model):
    counts = {}
    for e in model.by_kind("exception"):
        if e.data.get("outcome") == "revoked" or not e.data.get("task"): continue
        task = model.get(e.data["task"])
        counts.setdefault(e.data["rule"], set()).add(task.data.get("request"))
    return [{"next": "Conviene revisar la configuración de " + rule + " con el responsable del proyecto",
             "basis": "Esta regla ha requerido excepciones en " + str(len(requests)) + " peticiones; la política vigente no cambia"}
            for rule, requests in counts.items() if len(requests) >= 2]


def trace(root, identifier, *, offset=0, limit=20):
    from v3_contract import EVENTS
    model = load(root).require_valid(); target = model.get(identifier)
    if offset < 0 or not 1 <= limit <= 100: raise ContractError("Página fuera de límites")
    anchors = {target.uid}
    if target.kind == "request":
        anchors.update(e.uid for e in model.elements.values() if e.data.get("request") == target.uid)
        anchors.update(target.relations.get("proposal", []))
    if target.kind == "task":
        anchors.update(p.uid for p in model.by_kind("plan") if target.uid in p.relations.get("tasks", []))
        anchors.update(target.data.get("proposal_units", []))
    def refs(value):
        if isinstance(value, str): return {value}
        if isinstance(value, list): return {v for item in value for v in refs(item)}
        if isinstance(value, dict): return set(value) | {v for item in value.values() for v in refs(item)}
        return set()
    events = [e for e in model.elements.values() if e.kind in EVENTS and (refs(e.data) | e.targets()) & anchors]
    events.sort(key=lambda e: (e.data.get("recorded_at", e.data.get("decided_at", "")), e.uid))
    rows = []
    for event in events[offset:offset+limit]:
        actor = event.data.get("actor")
        rows.append({"source": event.source(), "type": event.kind, "purpose": event.data.get("purpose", event.data.get("action")),
                     "actor": actor or {"assurance": "unknown", "name": "Autor histórico no acreditado"},
                     "policy": event.data.get("policy"), "assignment": event.data.get("assignment"),
                     "outcome": event.data.get("outcome", event.data.get("state", event.data.get("result"))),
                     "reason": event.body, "pending": event.data.get("pending", []),
                     "intervention": event.data.get("intervention"),
                     "authorization": event.data.get("authorization"), "exceptions": event.data.get("exceptions", []),
                     "git": event.data.get("git"), "subject": event.data.get("subject")})
    return {"target": target.source(), "requested_by": target.data.get("requested_by", "No consta el solicitante del negocio"),
            "events": rows, "total": len(events), "next_offset": offset+limit if offset+limit < len(events) else None,
            "observation": "Hechos del repositorio; una actuación no observada permanece desconocida", "writes": []}


def readiness(root, task_id, actor, action="start"):
    model = load(root).require_valid(); task = model.get(task_id, "task")
    try:
        from v3_policy import operator
        identity = operator(model, actor, "verify" if action in {"verify", "close"} else "authorize" if action == "cancel" else "implement", policy_for(model, task))
        facts, quality = facts_for(model, task, actor)
        if action in {"verify", "close"} and policy_for(model, task).data.get("independent_review"):
            if any(e.data.get("actor", {}).get("member") == identity["member"] and e.data.get("task") == task.uid and e.data.get("action") in {"start", "resume", "implement"} for e in model.by_kind("execution")):
                raise ContractError("La revisión independiente corresponde a otra persona")
        result = evaluate(action, state(model, task), facts, policy_for(model, task).data,
                          valid_exceptions(model, task, action), model.get(task.data["request"]).data.get("flags", {}))
        from v31_guidance import interventions
        return {**result, "task": task.source(), "quality": quality, "owner": task.data["owner"],
                "journey": interventions(model, task.data["request"], actor=actor),
                "next": "Puede continuar esta transición; se comprobará su base antes de escribir" if result["status"] == "allowed" else
                "Resuelva las causas indicadas con el responsable; el trabajo independiente puede continuar"}
    except ContractError as exc:
        return {"status": "blocked", "task": task.source(), "causes": [str(exc)],
                "next": "Revise esta causa concreta; no es necesario reiniciar todo el proyecto"}
