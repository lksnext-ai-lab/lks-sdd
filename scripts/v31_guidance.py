"""One derived journey for CLI and hosts; roles never multiply human prompts."""
from v3_contract import ContractError, fingerprint
from v3_policy import operator, policy_for
from v3_workflow import request_facts, state, plan_for
from v3_approval import task_authority
from v3_team import owners
from v31_review import (config, roster, reviewers, review_status, closure_valid,
                        task_reviewed, task_review_basis, records, waivers)
from v31_corrections import unresolved

LABELS = ["Propuesta preparada", "Propuesta validada y cerrada", "Plan aprobado y ejecución autorizada",
          "Encargos revisados", "Tareas verificadas y cerradas", "Conjunto integrado y aceptado", "Entrega al PR preparada"]


def request_readiness(model, request_id, actor, action):
    from v31_review import check_close, designated
    request = model.get(request_id, "request")
    causes = []
    try:
        if action == "close-proposal":
            designated(model, request, actor, "responsible", "approve"); check_close(model, request)
        else:
            role, permission, facts_needed = {
                "authorize-plan": ("responsible", "authorize", ["proposal-approved"]),
                "integrate": ("integration_validator", "integrate", ["proposal-approved", "closed", "quality"]),
                "accept": ("functional_validator", "approve", ["integrated", "closed", "quality"]),
                "prepare-delivery": ("functional_validator", "approve", ["accepted", "integrated"])}[action]
            designated(model, request, actor, role, permission)
            facts = request_facts(model, request)
            if action == "accept" and policy_for(model, request).data["acceptance_order"] == "before-integration":
                facts_needed.remove("integrated")
            causes += ["Falta acreditar " + key for key in facts_needed if not facts.get(key)]
            from v3_policy import require_process
            if action in {"integrate", "accept"}:
                require_process(policy_for(model, request).data, action, facts, request.data.get("flags", {}))
            from v3_git import branch_check
            branch_check(model, request)
            if action == "authorize-plan" and not any(p.data.get("request") == request.uid for p in model.by_kind("plan")):
                causes.append("Prepare y presente el plan concreto antes de autorizarlo")
            if unresolved(model, request, external=action == "prepare-delivery"): causes.append("Correcciones pendientes")
    except (ContractError, KeyError) as exc: causes.append(str(exc))
    return {"status": "blocked" if causes else "available", "causes": causes, "action": action,
            "journey": interventions(model, request.uid, actor=actor), "writes": [],
            "next": "Resuelva las causas indicadas" if causes else "El contenido está preparado; la operación volverá a comprobar la base y evidencia exactas"}


def interventions(model, request_id, *, actor=None, offset=0, limit=20, object_offset=0):
    if offset < 0 or object_offset < 0 or not 1 <= limit <= 50: raise ContractError("Página de intervenciones inválida")
    request = model.get(request_id, "request")
    if not config(model, request): return {"request": request.source(), "enabled": False, "writes": []}
    people = roster(model, request); pending = []; automatic = []; issues = []
    def add(person, actions, objects, reason, permission, basis=None):
        row = {"actor": person, "actions": actions, "objects": objects[object_offset:object_offset+limit],
               "object_total": len(objects), "next_object_offset": object_offset+limit if object_offset+limit < len(objects) else None,
               "reason": reason, "domains": next((r["domains"] for r in reviewers(model, request) if r["member"] == person), []), "basis_digest": fingerprint(basis) if basis else None}
        try:
            row["name"] = model.get(person, "member").meta["title"]
            operator(model, person, permission, policy_for(model, request))
            if "accept" in actions: operator(model, person, "approve", policy_for(model, request))
            if "review-own-tasks" in actions: operator(model, person, "implement", policy_for(model, request))
        except ContractError as exc: row["blocked"] = str(exc)
        if actor is None or person == actor: pending.append(row)
    tasks = sorted([t for t in model.by_kind("task") if t.data.get("request") == request.uid and not t.retired], key=lambda t: t.uid)
    try:
        review = review_status(model, request); prepared = True
    except ContractError as exc:
        review = None; prepared = False; issues.append(str(exc))
    try: facts = request_facts(model, request, tasks=tasks)
    except ContractError as exc: facts = {}; issues.append(str(exc))
    closed = bool(prepared and closure_valid(model, request))
    if not prepared:
        automatic.append({"action": "prepare-proposal", "actor": people["responsible"], "reason": "Concrete el contenido o resuelva las decisiones críticas"})
    elif not closed:
        dispensed = bool(waivers(model, request, "integral-review", "close-proposal"))
        missing = review["pending"] if config(model, request)["proposal_review_required"] and not dispensed else []
        for person in missing:
            can_close = person == people["responsible"] and len(missing) == 1 and not review["open_comments"]
            add(person, ["review-proposal", "close-proposal"] if can_close else ["review-proposal"], [request.uid],
                "Una conformidad integral por persona; cierre conjunto cuando todas las condiciones estén disponibles", "approve", review["basis"])
        if not missing and (not review["open_comments"] or dispensed):
            add(people["responsible"], ["close-proposal"], [request.uid], "Revisiones vigentes: no vuelva a solicitarlas", "approve", review["basis"])
        if review["open_comments"]: issues.append("Resolver observaciones: " + ", ".join(review["open_comments"]))
    reviewed = True
    if closed and not tasks:
        automatic.append({"action": "prepare-plan", "actor": people["responsible"], "reason": "Prepare el plan; su aprobación exige presentarlo primero"})
    if closed:
        plans = {}
        for task in tasks:
            try: plans[plan_for(model, task).uid] = plan_for(model, task)
            except ContractError as exc: issues.append(str(exc))
        for plan in plans.values():
            selected = [t for t in tasks if t.uid in plan.relations["tasks"]]
            if not all(task_authority(model, t, plan, "execution")["valid"] for t in selected):
                own = [t.uid for t in selected if any(o["member"] == people["responsible"] for o in owners(model, t))
                       and not task_reviewed(model, t, people["responsible"])]
                actions = ["authorize-plan"] + (["review-own-tasks"] if own else [])
                add(people["responsible"], actions, [plan.uid, *own],
                    "Aprobar este plan y autorizarlo puede cubrir el detalle explícito de las tareas propias", "authorize",
                    {t.uid: task_review_basis(model, t, people["responsible"]) for t in selected if t.uid in own})
        groups = {}
        for task in tasks:
            for owner in owners(model, task):
                person = owner["member"]
                done = state(model, task) in {"verified", "closed", "closed-with-reservations"}
                valid = task_reviewed(model, task, person)
                reviewed &= valid or done
                if not valid and not done:
                    plan = plan_for(model, task)
                    if person == people["responsible"] and not task_authority(model, task, plan, "execution")["valid"]: continue
                    groups.setdefault(person, []).append(task)
            if state(model, task) in {"backlog", "ready", "paused", "in-progress", "implemented", "verified"}:
                automatic.append({"action": "task-next", "task": task.uid, "reason": "Consulte readiness; continúe solo las transiciones acreditadas y autorizadas"})
        for person, selected in groups.items():
            add(person, ["review-task"], [t.uid for t in selected],
                "Revise juntos los encargos disponibles; recibir tareas no acredita revisar su contenido", "implement",
                {t.uid: task_review_basis(model, t, person) for t in selected})
    defects = unresolved(model, request, external=True)
    if defects: issues.append("Correcciones pendientes: " + ", ".join(defects))
    if facts.get("closed") and not (facts.get("integrated") and facts.get("accepted")) and not defects and closed:
        same = people["integration_validator"] == people["functional_validator"]
        before = policy_for(model, request).data["acceptance_order"] == "before-integration"
        if before and not facts.get("accepted") and not same:
            add(people["functional_validator"], ["accept"], [request.uid], "La política exige aceptación funcional antes de integrar este candidato", "approve")
        elif not facts.get("integrated"):
            add(people["integration_validator"], ["integrate", "accept"] if same else ["integrate"], [request.uid],
                "Revise la evidencia técnica y el candidato concreto" + (" y confirme su aceptación funcional" if same else ""), "integrate")
        else:
            add(people["functional_validator"], ["accept"], [request.uid], "Acepte el resultado concreto; la integración ya está acreditada", "approve")
    deliveries = records(model, "delivery-preparation", request)
    from v3_git import subject
    from v3_verification import result_current
    from v3_approval import decisions
    accepted = {e.uid for e in decisions(model, "acceptance") if e.data.get("request") == request.uid and result_current(model, e, tasks)}
    delivered = bool(facts.get("accepted") and not defects and any(
        e.data.get("acceptance") in accepted and e.data.get("subject") == subject(model.root, e.data["subject"]["scope"]) for e in deliveries))
    if facts.get("accepted") and facts.get("integrated") and not defects and not delivered:
        automatic.append({"action": "prepare-delivery", "actor": people["functional_validator"], "reason": "Aceptación vigente; preparar el resumen no necesita otra firma SDD"})
    completed = [prepared, closed, bool(facts.get("plan-approved") and facts.get("authorized")), bool(tasks) and reviewed,
                 bool(facts.get("closed")), bool(facts.get("integrated") and facts.get("accepted")), delivered]
    milestones = [{"id": "H" + str(i+1), "label": label, "state": "completed" if completed[i] else "pending"}
                  for i, label in enumerate(LABELS)]
    reservations = waivers(model, request, "integral-review", "close-proposal") if prepared else []
    if closed and reservations:
        milestones[1].update(state="completed-with-reservations", exceptions=[e.uid for e in reservations],
                             missing_conformities=review["pending"], unresolved_comments=review["open_comments"])
    if not config(model, request)["task_review_required"]:
        milestones[3].update(state="not-required", reason="La política de esta petición no exige revisión del encargo")
    if policy_for(model, request).data.get("independent_review"):
        for task in tasks:
            implementers = {e.data["actor"]["member"] for e in model.by_kind("execution") if e.data.get("task") == task.uid and e.data.get("action") in {"start", "resume", "implement"}}
            eligible = []
            for member in model.by_kind("member"):
                try: operator(model, member.uid, "verify", policy_for(model, request))
                except ContractError: continue
                if member.uid not in implementers: eligible.append(member.uid)
            if implementers and not eligible: issues.append("Revisión independiente sin otra persona habilitada; configure un revisor o una decisión de gobierno explícita")
            if state(model, task) in {"implemented", "in-review"} and eligible:
                issues.append("Revisión independiente pendiente: " + task.id + "; personas habilitadas: " + ", ".join(eligible))
    return {"request": request.source(), "enabled": True, "milestones": milestones, "interventions": pending[offset:offset+limit],
            "intervention_total": len(pending), "next_offset": offset+limit if offset+limit < len(pending) else None,
            "automatic_actions": automatic[offset:offset+limit], "automatic_total": len(automatic),
            "issues": issues[offset:offset+limit], "issue_total": len(issues),
            "observation": "Estado del checkout; no acredita otros chats ni clones", "writes": []}
