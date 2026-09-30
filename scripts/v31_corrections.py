"""Negative outcomes are facts, never fabricated positive integration receipts."""
from v3_contract import ContractError, element, load, now, read_bytes, sha, Element, location
from v3_storage import prepare
from v3_git import subject, branch_check, coordination
from v3_policy import operator, policy_for
from v31_review import config, designated, records, event


def affected(model, problem):
    return [model.get(k, "task") for k in problem.data["tasks"]]


def scope_for(tasks):
    return sorted({p for t in tasks for p in t.data["scope"]})


def defect_ids(model, request):
    return sorted(e.uid for e in records(model, "development-defect", request) if e.data["phase"] != "external")


def unresolved(model, request, task=None, *, external=False):
    from v3_verification import result_basis
    from v3_workflow import evidence_valid
    pending = []
    for p in records(model, "development-defect", request):
        if p.data["phase"] == "external" and not external: continue
        if task and task.uid not in p.data["tasks"]: continue
        tasks = affected(model, p)
        valid = False
        for resolution in records(model, "defect-resolution", request):
            d = resolution.data
            if d.get("problem") != p.uid or d.get("problem_basis") != p.digest(): continue
            try:
                if sha(read_bytes(model.root, p.data["artifact"])) != p.data["artifact_sha256"]:
                    raise ContractError("La evidencia original del defecto cambió")
                role = "functional_validator" if p.data["phase"] == "acceptance" else "integration_validator"
                designated(model, request, d["actor"]["member"], role, "approve" if role == "functional_validator" else "integrate")
                current_corrections = {e.uid: e.digest() for e in model.by_kind("change") if e.data.get("problem") == p.uid and not e.retired}
                if not current_corrections or current_corrections != d.get("correction_bases"): continue
                live_confirmations = {e.uid for e in records(model, "correction-classification", request)}
                if not set(d.get("confirmations", [])) <= live_confirmations or not d.get("confirmations"): continue
                for key in d["confirmations"]:
                    confirmation = model.get(key, "decision")
                    designated(model, request, confirmation.data["actor"]["member"], "responsible", "approve")
                proof = [model.get(key, "evidence") for key in d.get("evidence", [])]
                if not proof: continue
                if any(e.uid in p.data.get("evidence_before", []) or e.data.get("outcome") != "passed"
                       or sha(read_bytes(model.root, e.data["artifact"])) != e.data["artifact_sha256"] for e in proof): continue
                if any(not set(t.data["tests"]) <= {test for e in proof if e.data.get("task") == t.uid
                       and e.data.get("basis") == t.digest() and e.data.get("subject") == subject(model.root, t.data["scope"])
                       for test in e.data.get("tests", [])} for t in tasks): continue
                valid = (d.get("subject") == subject(model.root, scope_for(tasks)) and
                         d.get("basis") == result_basis(model, tasks) and
                         all(evidence_valid(model, t, None) for t in tasks))
            except ContractError: valid = False
            if valid: break
        if not valid: pending.append(p.uid)
    return pending


def reject(root, actor, request_id, statement, *, phase, tasks, expected, observed, artifact, requirements=(), refresh=False):
    model = load(root).require_valid(); request = model.get(request_id, "request")
    coordination(model, request, "reject-result", refresh=refresh)
    if not config(model, request): raise ContractError("El resultado negativo tipado requiere recorrido integral")
    if phase not in {"integration", "acceptance", "external"}: raise ContractError("Fase de rechazo inválida")
    identity = designated(model, request, actor, "functional_validator" if phase == "acceptance" else "integration_validator",
                          "approve" if phase == "acceptance" else "integrate")
    if not all(isinstance(x, str) and x.strip() for x in (statement, expected, observed, artifact)) or not tasks:
        raise ContractError("Describa esperado, observado, evidencia y tareas afectadas")
    selected = [model.get(k, "task") for k in dict.fromkeys(tasks)]
    if any(t.data["request"] != request.uid for t in selected): raise ContractError("Tareas de otra petición")
    for key in requirements: model.get(key)
    raw = read_bytes(model.root, artifact)
    candidate = subject(model.root, scope_for(selected))
    problem = element("problem", "Resultado no aceptable", statement, purpose="development-defect", phase=phase,
                      request=request.uid, tasks=[t.uid for t in selected], actor=identity, expected=expected,
                      observed=observed, requirements=list(requirements), subject=candidate, recorded_at=now())
    problem["meta"]["data"]["evidence_before"] = [e.uid for e in model.by_kind("evidence")]
    path = "docs/lks-sdd/evidence/" + problem["meta"]["uid"] + ".txt"
    problem["meta"]["data"].update(artifact=path, artifact_sha256=sha(raw))
    problem["meta"].update(state="open", nature="fact")
    correction = element("change", "Definición correctiva pendiente", statement,
                         purpose="correction-definition", request=request.uid, problem=problem["meta"]["uid"],
                         expected=expected, observed=observed, acceptance=expected, classification="pending",
                         tasks=[t.uid for t in selected], requirements=list(requirements))
    packet = prepare(root, [problem, correction], "reject:" + phase, changes={path: raw}, sources={artifact: sha(raw)},
                     guards={"git": branch_check(model, request), "subject": candidate})
    packet["summary"].update(problem=problem["meta"]["uid"], correction=correction["meta"]["uid"])
    return packet


def define(root, actor, correction_id, classification, statement, acceptance, *, tasks=None, requirements=None, refresh=False):
    import copy
    model = load(root).require_valid(); old = model.get(correction_id, "change")
    if old.data.get("purpose") != "correction-definition": raise ContractError("Seleccione una definición correctiva")
    request = model.get(old.data["request"], "request")
    coordination(model, request, "define-correction", refresh=refresh)
    identity = designated(model, request, actor, "responsible", "approve")
    if classification not in {"defect", "agreement-change", "new-request", "external"} or not statement.strip() or not acceptance.strip():
        raise ContractError("Confirme clasificación, alcance y criterio correctivo")
    item = copy.deepcopy(old.item()); item["meta"]["revision"] += 1
    item["body"] = statement
    item["meta"]["data"].update(classification=classification, acceptance=acceptance)
    if tasks is not None:
        if not tasks: raise ContractError("La corrección requiere tareas vinculadas")
        for key in tasks: model.get(key, "task")
        item["meta"]["data"]["tasks"] = list(tasks)
    if requirements is not None:
        for key in requirements: model.get(key)
        item["meta"]["data"]["requirements"] = list(requirements)
    from v31_review import proposal_basis
    confirmed = event("correction-classification", identity, request, statement, correction=old.uid,
                      proposal_basis=proposal_basis(model, request), basis=Element(item["meta"], item["body"], old.path).digest(), outcome="approved")
    return prepare(root, [item, confirmed], "define-correction", guards={"git": branch_check(model, request)})


def resolve(root, actor, problem_id, statement, *, refresh=False):
    from v3_workflow import evidence_valid, plan_for
    from v3_verification import result_basis
    from v3_approval import task_authority
    model = load(root).require_valid(); problem = model.get(problem_id, "problem")
    if problem.data.get("purpose") != "development-defect": raise ContractError("Defecto no reconocido")
    request = model.get(problem.data["request"], "request")
    coordination(model, request, "resolve-defect", refresh=refresh)
    role = "functional_validator" if problem.data["phase"] == "acceptance" else "integration_validator"
    identity = designated(model, request, actor, role, "approve" if role == "functional_validator" else "integrate")
    corrections = [e for e in model.by_kind("change") if e.data.get("problem") == problem.uid and not e.retired]
    confirmation_ids = []
    if not corrections: raise ContractError("Falta definir la corrección")
    for correction in corrections:
        confirmations = [e for e in records(model, "correction-classification", request)
                         if e.data.get("correction") == correction.uid and e.data.get("basis") == correction.digest()]
        if not confirmations:
            raise ContractError("Falta confirmar el alcance correctivo")
        for confirmation in confirmations:
            designated(model, request, confirmation.data["actor"]["member"], "responsible", "approve")
        confirmation_ids += [e.uid for e in confirmations]
        from v31_review import proposal_basis, closure_valid
        if correction.data["classification"] == "agreement-change":
            if any(e.data.get("proposal_basis") == proposal_basis(model, request) for e in confirmations) or not closure_valid(model, request):
                raise ContractError("Un cambio del acuerdo requiere propuesta revisada y cerrada")
        if correction.data["classification"] == "new-request" and not any(model.get(k, "task").data["request"] != request.uid for k in correction.data["tasks"]):
            raise ContractError("Vincule la nueva necesidad a otra petición definida y autorizada")
        if correction.data["classification"] != "new-request" and any(model.get(k, "task").data["request"] != request.uid for k in correction.data["tasks"]):
            raise ContractError("La corrección pertenece a otra petición")
        for key in correction.data["tasks"]:
            task = model.get(key, "task")
            if not task_authority(model, task, plan_for(model, task), "execution")["valid"] or not evidence_valid(model, task, None):
                raise ContractError("La corrección necesita autorización y evidencia vigente")
    tasks = affected(model, problem)
    if not all(evidence_valid(model, t, None) for t in tasks): raise ContractError("Repita las comprobaciones afectadas")
    evidence_used = []
    for task in tasks:
        fresh = [e for e in model.by_kind("evidence") if e.uid not in problem.data.get("evidence_before", [])
                 and e.data.get("task") == task.uid and e.data.get("outcome") == "passed"
                 and e.data.get("basis") == task.digest() and e.data.get("subject") == subject(model.root, task.data["scope"])]
        if not set(task.data["tests"]) <= {key for e in fresh for key in e.data.get("tests", [])}:
            raise ContractError("La resolución requiere comprobaciones posteriores al fallo, no evidencia anterior")
        evidence_used += [e.uid for e in fresh]
    candidate = subject(model.root, scope_for(tasks))
    record = event("defect-resolution", identity, request, statement, problem=problem.uid,
                   problem_basis=problem.digest(), subject=candidate, basis=result_basis(model, tasks), evidence=evidence_used,
                   correction_bases={c.uid: c.digest() for c in corrections}, confirmations=confirmation_ids, outcome="approved")
    return prepare(root, [record], "resolve-defect", guards={"subject": candidate, "git": branch_check(model, request)})


def delivery(root, actor, request_id, statement, *, pr_url=None, refresh=False):
    from v3_verification import result_current
    from v3_approval import decisions
    from v3_git import observe
    model = load(root).require_valid(); request = model.get(request_id, "request")
    coordination(model, request, "prepare-delivery", refresh=refresh)
    identity = designated(model, request, actor, "functional_validator", "approve")
    tasks = [t for t in model.by_kind("task") if t.data.get("request") == request.uid and not t.retired]
    valid = [e for e in decisions(model, "acceptance") if e.data.get("request") == request.uid and result_current(model, e, tasks)]
    integrated = any(result_current(model, e, tasks) for e in model.by_kind("receipt")
                     if e.data.get("purpose") == "integration" and e.data.get("request") == request.uid)
    if not valid or not integrated or unresolved(model, request, external=True): raise ContractError("Falta aceptación vigente o hay impedimentos de entrega")
    if pr_url:
        import re
        if not isinstance(pr_url, str) or not re.fullmatch(r"https://[A-Za-z0-9.-]+(?::[0-9]+)?/[^\s@]+", pr_url):
            raise ContractError("URL de PR inválida")
    candidate = subject(model.root, scope_for(tasks))
    record = element("receipt", "Entrega al PR preparada", statement, purpose="delivery-preparation", request=request.uid,
                     actor=identity, tasks=[t.uid for t in tasks], acceptance=valid[-1].uid, subject=candidate,
                     git=observe(model.root), pr_url=pr_url, pr_approval="not-granted", publication="not-performed", recorded_at=now())
    if not statement.strip(): raise ContractError("Describa la preparación de entrega")
    from v31_review import waivers
    record["meta"]["data"]["review_reservations"] = [e.uid for e in waivers(model, request, "integral-review", "close-proposal")]
    record["meta"].update(state="observed", nature="fact")
    return prepare(root, [record], "prepare-delivery", guards={"subject": candidate, "git": branch_check(model, request)})
