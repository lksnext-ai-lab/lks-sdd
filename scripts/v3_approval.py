"""Recoverable exact approval units and complete plan coverage."""
from v3_contract import ContractError, element, now, fingerprint
from v3_policy import operator, policy_for


def descriptor(model, identifiers):
    units, seen = {}, set()
    def add(e):
        if e.uid in seen: return
        seen.add(e.uid)
        if e.retired: raise ContractError("Unidad retirada: " + e.id)
        units[e.uid] = e.digest()
        for rel in ("depends_on", "interfaces", "requirements", "acceptance", "constraints", "uses", "tasks", "covers", "tests", "technology"):
            for key in e.relations.get(rel, []): add(model.get(key))
    for key in identifiers: add(model.get(key))
    from v3_scope import memberships
    classified = memberships(model)
    for shared in model.elements.values():
        uncertain = shared.kind in {"rule", "constraint", "requirement", "acceptance", "interface", "technology", "applicability"} and not shared.data.get("request") and shared.uid not in classified
        if (shared.data.get("global") or uncertain) and not shared.retired: add(shared)
    if not units: raise ContractError("Paquete de aprobación vacío")
    return {"units": units, "digest": fingerprint(units)}


def decisions(model, purpose=None):
    values = model.by_kind("decision") + model.by_kind("authorization")
    revoked = {e.data.get("revokes") for e in values if e.data.get("outcome") == "revoked"}
    return [e for e in values if not e.data.get("historical_only") and e.uid not in revoked and e.data.get("outcome") == "approved"
            and (purpose is None or e.data.get("purpose") == purpose)]


def approved(model, identifiers, purpose="proposal"):
    expected = descriptor(model, identifiers)["units"]
    from v3_migration import inherited_confirmations
    covered = inherited_confirmations(model, expected) if purpose in {"proposal", "technology"} else {}
    for decision in decisions(model, purpose):
        for key, digest in decision.data.get("descriptor", {}).get("units", {}).items():
            if expected.get(key) != digest: continue
            try:
                source = model.at(key, digest)
                dependencies = descriptor(model, [key])["units"]
                recorded = decision.data["descriptor"]["units"]
                if all(recorded.get(k) == v for k, v in dependencies.items()): covered[key] = decision.uid
            except ContractError: continue
    return {"valid": set(covered) == set(expected), "covered": covered,
            "pending": sorted(set(expected)-set(covered)), "descriptor": expected}


def decision(model, actor, identifiers, purpose, statement, *, outcome="approved", reason=""):
    if not statement.strip(): raise ContractError("Falta la decisión explícita observada; no inferirla del silencio")
    permission = "authorize" if purpose == "execution" else "govern" if purpose == "governance" else "approve"
    identity = operator(model, actor, permission)
    for key in identifiers:
        unit = model.get(key)
        request = unit if unit.kind == "request" else model.get(unit.data["request"]) if unit.data.get("request") else None
        if request: operator(model, actor, permission, policy_for(model, request))
    desc = descriptor(model, identifiers)
    result = element("authorization" if purpose == "execution" else "decision", "Decisión sobre " + purpose, statement,
                     purpose=purpose, actor=identity, descriptor=desc, outcome=outcome, reason=reason, decided_at=now())
    result["meta"].update(state="approved" if outcome == "approved" else "proposed", nature="decision")
    result["meta"]["relations"] = {"sources": list(desc["units"])}
    if purpose in {"plan", "execution"}:
        result["meta"]["data"]["task_bases"] = {task_id: task_basis(model, model.get(task_id), model.get(plan_id))
            for plan_id in identifiers if model.get(plan_id).kind == "plan"
            for task_id in model.get(plan_id).relations.get("tasks", [])}
    return result


def task_basis(model, task, plan):
    import copy
    rules = copy.deepcopy(plan.normative())
    rules["meta"].pop("revision", None)
    rules["meta"]["relations"].pop("tasks", None)
    rules["meta"]["data"].pop("proposal_units", None)
    request = model.get(task.data["request"], "request")
    units = proposal_ready(model, request, task.data.get("proposal_units", plan.data.get("proposal_units", request.relations.get("proposal", []))))
    return {"task": descriptor(model, [task.uid])["units"], "proposal": descriptor(model, units)["units"],
            "request_conditions": fingerprint(request.data.get("flags", {})),
            "plan": plan.uid, "plan_rules": fingerprint(rules)}


def task_authority(model, task, plan, purpose):
    expected = task_basis(model, task, plan)
    matches = []
    for entry in decisions(model, purpose):
        if entry.data.get("task_bases", {}).get(task.uid) != expected: continue
        try:
            for key, digest in {**expected["task"], **expected["proposal"]}.items(): model.at(key, digest)
            plan_digest = entry.data["descriptor"]["units"][plan.uid]
            model.at(plan.uid, plan_digest)
        except (ContractError, KeyError): continue
        matches.append(entry.uid)
    return {"valid": bool(matches), "decisions": matches, "basis": expected}


def proposal_ready(model, request, selected=None, *, require_complete=True):
    units = list(request.relations.get("proposal", []) if selected is None else selected)
    if not set(units) <= set(request.relations.get("proposal", [])): raise ContractError("La unidad no pertenece a esta petición")
    if not units: raise ContractError("Prepare una propuesta funcional y técnica concreta")
    types = set()
    for key in units:
        e = model.get(key)
        if e.kind == "feature" and e.data.get("legacy"):
            if not e.relations.get("requirements") or not e.body.strip():
                raise ContractError("Concrete la especificación heredada de esta porción")
            types.add("joint")
            continue
        if e.kind != "proposal": raise ContractError("Seleccione una propuesta o una especificación heredada identificable")
        types.add(e.data.get("part"))
        required = {"objective", "included", "excluded", "impact", "acceptance"}
        if e.data.get("part") in {"functional", "joint"}: required.add("behavior")
        if e.data.get("part") in {"technical", "joint"}: required.add("solution")
        if e.data.get("part") not in {"functional", "technical", "joint"}: raise ContractError("Declare la parte funcional, técnica o conjunta")
        for field in sorted(required):
            if field not in e.data or (field != "excluded" and not e.data[field]): raise ContractError("La propuesta debe concretar: " + field)
        if len(e.body.strip()) < 40: raise ContractError("La lista de títulos no describe lo que se valida")
        if e.data.get("unresolved"): raise ContractError("Resolver las decisiones críticas de la porción")
    if require_complete and not ({"functional", "technical"} <= types or "joint" in types):
        groups = {model.get(k).data.get("unit_group", request.uid) for k in units}
        for key in request.relations.get("proposal", []):
            other = model.get(key)
            if key in units or other.data.get("unit_group", request.uid) not in groups: continue
            if other.data.get("part") not in {"functional", "technical"}-types: continue
            if approved(model, [key])["valid"]:
                proposal_ready(model, request, [key], require_complete=False)
                units.append(key); types.add(other.data["part"])
        if not {"functional", "technical"} <= types: raise ContractError("Falta validar la propuesta funcional o técnica complementaria")
    return units


def plan_coverage(model, plan):
    request = model.get(plan.data["request"], "request")
    roots = proposal_ready(model, request, plan.data.get("proposal_units"))
    if not approved(model, roots)["valid"]: raise ContractError("Validar la propuesta exacta antes de planificar")
    tasks = [model.get(k, "task") for k in plan.relations.get("tasks", [])]
    if not tasks: raise ContractError("Plan sin tareas")
    obligations = set()
    for key in descriptor(model, roots)["units"]:
        e = model.get(key)
        if e.kind in {"requirement", "acceptance", "test", "interface"}: obligations.add(key)
    obligations |= set(request.data.get("obligations", []))
    covered, graph = {}, {}
    for task in tasks:
        for key in ("request", "owner", "scope", "acceptance", "tests"):
            if not task.data.get(key): raise ContractError("Tarea incompleta: " + task.id + ": " + key)
        model.get(task.data["owner"], "member")
        if task.data["request"] != request.uid: raise ContractError("Tarea de otra petición")
        if not set(task.data.get("proposal_units", roots)) <= set(roots): raise ContractError("La tarea excede la porción planificada")
        for key in task.relations.get("covers", []):
            if key in covered: raise ContractError("Propiedad principal duplicada: " + key)
            model.get(key); covered[key] = task.uid
        graph[task.uid] = set()
        for dep in task.data.get("dependencies", []):
            if dep.get("type") not in {"contract", "available", "verified"}: raise ContractError("Dependencia sin tipo válido")
            model.get(dep["uid"])
            graph[task.uid].add(dep["uid"])
    if obligations-set(covered): raise ContractError("Obligaciones sin tarea: " + ", ".join(sorted(obligations-set(covered))))
    pending = set(graph)
    while pending:
        ready = {k for k in pending if not (graph[k] & pending)}
        if not ready: raise ContractError("Plan con dependencias circulares")
        pending -= ready
    if len(tasks) > 1 and not any(t.data.get("integration") for t in tasks):
        raise ContractError("Asigne la integración conjunta de las porciones")
    return {"request": request.uid, "tasks": [t.uid for t in tasks], "covered": covered, "status": "complete"}
