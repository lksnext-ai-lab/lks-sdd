"""Typed evidence and integration remain separate from implementation and acceptance."""
from v3_contract import ContractError, DOCS, element, load, now, read_bytes, sha
from v3_policy import operator, policy_for, require_process
from v3_git import subject, coordination, integration_guard, observe, branch_check
from v3_workflow import state, facts_for, valid_exceptions, dependency_subjects, plan_for, request_facts, evidence_valid
from v3_approval import task_basis, task_authority, decisions
from v3_storage import prepare
from v3_quality import valid_until


def result_basis(model, tasks):
    return {t.uid: task_basis(model, t, plan_for(model, t)) for t in tasks}


def result_current(model, record, tasks):
    from v31_corrections import unresolved, defect_ids
    from v31_review import closure_valid
    if record.data.get("request"):
        request = model.get(record.data["request"], "request")
        if unresolved(model, request) or not closure_valid(model, request): return False
        if record.data.get("known_defects", []) != defect_ids(model, request): return False
    if not tasks or record.data.get("basis") != result_basis(model, tasks): return False
    if subject(model.root, record.data["subject"]["scope"]) != record.data["subject"]: return False
    return all(task_authority(model, t, plan_for(model, t), "execution")["valid"] and evidence_valid(model, t, None) for t in tasks)


def evidence(root, actor, task_id, tests, outcome, source, artifact, explanation):
    model = load(root).require_valid(); task = model.get(task_id, "task")
    identity = operator(model, actor, "verify", policy_for(model, task))
    if not tests or not set(tests) <= set(task.data["tests"]): raise ContractError("La evidencia debe cubrir pruebas de esta tarea")
    if source not in {"automated", "human-observation", "external-report"} or outcome not in {"passed", "failed", "not-run"}:
        raise ContractError("Tipo o resultado de evidencia no válido")
    if not explanation.strip(): raise ContractError("Describa qué acredita la evidencia y sus límites")
    raw = read_bytes(model.root, artifact)
    event = element("evidence", "Evidencia de " + task.id, explanation, task=task.uid, basis=task.digest(),
                    tests=tests, outcome=outcome, source=source, subject=subject(model.root, task.data["scope"]),
                    dependencies=dependency_subjects(model, task),
                    actor=identity, recorded_at=now())
    stored = DOCS + "/evidence/" + event["meta"]["uid"] + ".txt"
    event["meta"]["data"].update(artifact=stored, artifact_sha256=sha(raw), original_path=artifact)
    event["meta"].update(state="observed", nature="fact")
    return prepare(root, [event], "evidence", changes={stored: raw}, sources={artifact: sha(raw)},
                   guards={"subject": event["meta"]["data"]["subject"]})


def integrate(root, actor, request_id, trusted_root, statement, *, refresh=False, accept_result=False):
    model = load(root).require_valid(); request = model.get(request_id, "request")
    identity = operator(model, actor, "integrate", policy_for(model, request))
    from v31_review import designated, closure_valid
    from v31_corrections import unresolved
    designated(model, request, actor, "integration_validator", "integrate")
    if unresolved(model, request) or not closure_valid(model, request): raise ContractError("Corrija los pendientes antes de integrar")
    preceding = []
    if accept_result and policy_for(model, request).data["acceptance_order"] == "before-integration":
        from v31_review import overlay
        from v3_contract import parse
        import base64
        packet = accept(root, actor, request_id, statement, _model=model)
        for path, raw in packet["payload"].items():
            if path.startswith("docs/lks-sdd/elements/"):
                preceding += [e.item() for e in parse(base64.b64decode(raw), path)[0]]
        overlay(model, preceding)
    trusted = load(trusted_root).require_valid()
    branch_check(model, request)
    trusted_git = observe(trusted.root, refs=[request.data["target"]])
    if trusted_git["branch"] != request.data["target"] and (not trusted_git["head"] or trusted_git["refs"].get(request.data["target"]) != trusted_git["head"]):
        raise ContractError("La base de confianza debe representar la rama destino declarada")
    # Trust comes from the explicitly selected target, not the candidate's self-declared policy.
    operator(trusted, actor, "integrate")
    comparison = integration_guard(trusted, model)
    coordination(model, request, "integrate", refresh=refresh)
    tasks = [t for t in model.by_kind("task") if t.data.get("request") == request.uid and not t.retired]
    if not tasks or any(state(model, t) not in {"closed", "closed-with-reservations"} for t in tasks):
        raise ContractError("Faltan por cerrar porciones de la petición")
    require_process(policy_for(model, request).data, "integrate", request_facts(model, request), request.data.get("flags", {}))
    for task in tasks:
        facts, _ = facts_for(model, task, identity["member"])
        if not facts["authorized"] or not facts["evidence"]: raise ContractError("Contrato/evidencia ya no vigente para integrar")
        if not facts["quality"] and not any(e["rule"] == "quality" for e in valid_exceptions(model, task, "integrate")):
            raise ContractError("Calidad pendiente sobre las entradas de integración; requiere corrección o excepción específica")
    if comparison["status"] == "needs-decision":
        for change in comparison["changes"]:
            if not change["requires_review"]: continue
            if not change["after"]: raise ContractError("No retire una identidad compartida sin conservar su historia")
            changed = model.get(change["uid"])
            permission = "govern" if changed.kind in {"project", "policy", "member"} else "approve"
            matches = [d for d in decisions(model) if d.data.get("descriptor", {}).get("units", {}).get(changed.uid) == changed.digest()]
            valid = False
            for decision in matches:
                try: operator(trusted, decision.data["actor"]["member"], permission); valid = True
                except (ContractError, KeyError): continue
            if not valid: raise ContractError("La base de confianza requiere revisar este cambio compartido: " + changed.id)
    if not statement.strip(): raise ContractError("Falta revisión explícita de compatibilidad semántica")
    scope = sorted({p for t in tasks for p in t.data["scope"]})
    candidate_subject = subject(model.root, scope)
    if policy_for(model, request).data["acceptance_order"] == "before-integration":
        accepted = [d for d in decisions(model, "acceptance") if d.data.get("request") == request.uid]
        if not any(result_current(model, d, tasks) for d in accepted):
            raise ContractError("Este proyecto requiere aceptación funcional del candidato antes de integrarlo")
    event = element("receipt", "Integración comprobada", statement, purpose="integration", request=request.uid,
                    tasks=[t.uid for t in tasks], actor=identity, recorded_at=now(), trusted_snapshot=trusted.snapshot(),
                    candidate_snapshot=model.snapshot(), subject=candidate_subject, basis=result_basis(model, tasks), comparison=comparison,
                    trusted_git=trusted_git, semantic_review="explicitly-confirmed",
                    reservations=[t.uid for t in tasks if state(model, t) == "closed-with-reservations"],
                    pr_approval="not-granted", publication="not-performed")
    event["meta"].update(state="observed", nature="fact")
    items = preceding + [event]
    from v31_corrections import defect_ids
    event["meta"]["data"]["known_defects"] = defect_ids(model, request)
    from v31_review import config, waivers
    if config(model, request): event["meta"]["data"]["review_reservations"] = [e.uid for e in waivers(model, request, "integral-review", "close-proposal")]
    if accept_result and not preceding:
        from v31_review import overlay
        from v3_contract import parse
        import base64
        overlay(model, items)
        packet = accept(root, actor, request_id, statement, _model=model)
        for path, raw in packet["payload"].items():
            if path.startswith("docs/lks-sdd/elements/"):
                items += [e.item() for e in parse(base64.b64decode(raw), path)[0]]
    from v31_review import group_intervention
    return prepare(root, group_intervention(items), "integration", guards={"git": observe(model.root), "subject": candidate_subject, "expires_at": valid_until(model, tasks),
                   "trusted": {"root": str(trusted.root), "snapshot": trusted.snapshot(), "git": trusted_git}})


def accept(root, actor, request_id, statement, *, _model=None):
    model = _model or load(root).require_valid(); request = model.get(request_id, "request")
    identity = operator(model, actor, "approve", policy_for(model, request))
    from v31_review import designated, closure_valid
    from v31_corrections import unresolved
    designated(model, request, actor, "functional_validator", "approve")
    if unresolved(model, request) or not closure_valid(model, request): raise ContractError("Falta resolver correcciones o cerrar la propuesta vigente")
    tasks = [t for t in model.by_kind("task") if t.data.get("request") == request.uid and not t.retired]
    require_process(policy_for(model, request).data, "accept", request_facts(model, request), request.data.get("flags", {}))
    for task in tasks:
        if not task_authority(model, task, plan_for(model, task), "execution")["valid"] or not evidence_valid(model, task, None):
            raise ContractError("Revise la propuesta, autorización y evidencia vigentes antes de aceptar")
    if policy_for(model, request).data["acceptance_order"] == "before-integration":
        tasks = [t for t in model.by_kind("task") if t.data.get("request") == request.uid and not t.retired]
        if not tasks or any(state(model, t) not in {"closed", "closed-with-reservations"} for t in tasks):
            raise ContractError("Antes de aceptar, complete las porciones del resultado funcional")
        if not statement.strip(): raise ContractError("Falta decisión explícita sobre el resultado funcional")
        scope = sorted({p for t in tasks for p in t.data["scope"]})
        event = element("decision", "Aceptación previa a integración", statement, purpose="acceptance", outcome="approved",
                        actor=identity, request=request.uid, receipt=None, subject=subject(model.root, scope), basis=result_basis(model, tasks),
                        reservations=[t.uid for t in tasks if state(model, t) == "closed-with-reservations"], decided_at=now())
        event["meta"].update(state="approved", nature="decision")
        from v31_corrections import defect_ids
        event["meta"]["data"]["known_defects"] = defect_ids(model, request)
        return prepare(root, [event], "acceptance-before-integration", guards={"subject": event["meta"]["data"]["subject"], "expires_at": valid_until(model, tasks)})
    receipts = [e for e in model.by_kind("receipt") if e.data.get("purpose") == "integration" and e.data.get("request") == request.uid]
    if not receipts or not statement.strip(): raise ContractError("Antes de aceptar, revisar la integración concreta y expresar la decisión")
    receipts.sort(key=lambda e: (e.data["recorded_at"], e.uid))
    latest = receipts[-1]
    if not result_current(model, latest, tasks):
        raise ContractError("El resultado o su contrato cambió después de revisar la integración")
    event = element("decision", "Aceptación de la petición", statement, purpose="acceptance", outcome="approved",
                    actor=identity, request=request.uid, receipt=latest.uid, subject=latest.data["subject"], basis=result_basis(model, tasks),
                    reservations=latest.data["reservations"], decided_at=now())
    event["meta"].update(state="approved", nature="decision")
    from v31_corrections import defect_ids
    event["meta"]["data"]["known_defects"] = defect_ids(model, request)
    return prepare(root, [event], "acceptance", guards={"subject": latest.data["subject"], "expires_at": valid_until(model, tasks)})
