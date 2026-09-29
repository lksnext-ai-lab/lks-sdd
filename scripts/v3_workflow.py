"""One workflow evaluator for entry, continuation, verification and closure."""
from v3_contract import ContractError, element, load, now, fingerprint
from v3_policy import operator, policy_for, active_period, process_requirements
from v3_approval import approved, proposal_ready, plan_coverage, descriptor, task_authority
from v3_git import branch_check, coordination, subject, code_inventory, scope_changes
from v3_quality import checks
from v3_team import permitted_scope
from v3_storage import prepare

TRANSITIONS = {
    "start": ({"backlog", "ready"}, "in-progress", {"proposal-approved", "plan-approved", "authorized", "assigned", "dependencies"}),
    "implement": ({"in-progress"}, "implemented", {"authorized", "assigned", "dependencies", "scope"}),
    "verify": ({"implemented", "in-review"}, "verified", {"authorized", "quality", "evidence", "scope"}),
    "close": ({"verified"}, "closed", {"authorized", "quality", "evidence", "scope"}),
    "pause": ({"in-progress", "implemented", "in-review", "verified"}, "paused", set()),
    "resume": ({"paused"}, "in-progress", {"proposal-approved", "plan-approved", "authorized", "assigned", "dependencies"}),
    "reopen": ({"implemented", "in-review", "verified", "closed", "closed-with-reservations"}, "in-progress", {"authorized", "assigned"}),
    "cancel": ({"backlog", "ready", "paused", "in-progress", "implemented", "in-review", "verified"}, "cancelled", set()),
}
EXEMPTIBLE = {"quality", "dependencies", "assigned", "branch"}


def latest(model, task):
    records = [e for e in model.by_kind("execution") if e.data.get("task") == task.uid]
    predecessors = {e.data.get("previous") for e in records}
    tips = [e for e in records if e.uid not in predecessors]
    if len(tips) > 1: raise ContractError("Progreso concurrente; reconciliar hechos antes de continuar")
    return tips[0] if tips else None


def state(model, task):
    if task.data.get("continuation") == "historical": return "historical-" + task.data["legacy"]["state"]
    if task.data.get("continuation") == "reconciliation-required": return "reconciliation-required"
    last = latest(model, task)
    if last is None: return "backlog"
    if last.data.get("basis") != task.digest(): return "reconciliation-required"
    if last.data["state"] in {"implemented", "verified", "closed", "closed-with-reservations"}:
        if last.data["subject"]["digest"] != subject(model.root, task.data["scope"])["digest"]:
            return "in-progress"
    return last.data["state"]


def plan_for(model, task):
    matches = [p for p in model.by_kind("plan") if task.uid in p.relations.get("tasks", []) and not p.retired]
    if len(matches) != 1: raise ContractError("La tarea necesita un único plan activo")
    return matches[0]


def dependencies(model, task):
    pending = []
    for dep in task.data.get("dependencies", []):
        other = model.get(dep["uid"])
        if dep["type"] == "contract":
            okay = bool(dep.get("digest")) and dep["digest"] == other.digest() and approved(model, [other.uid])["valid"]
        elif dep["type"] in {"available", "verified"}:
            event = latest(model, other) if other.kind == "task" else None
            current = state(model, other) if event else "unknown"
            accepted = {"verified", "closed"} if dep["type"] == "verified" else {"implemented", "verified", "closed"}
            okay = current in accepted and bool(dep.get("artifact"))
            if okay:
                artifact = subject(model.root, [dep["artifact"]])
                from v3_team import contains
                produced = {p: h for p, h in event.data["subject"]["files"].items() if contains([dep["artifact"]], p)}
                expected = dep.get("digest") or fingerprint(produced)
                okay = artifact["digest"] == expected and bool(produced) and all(v is not None for v in artifact["files"].values())
            if current == "closed-with-reservations":
                okay = bool(dep.get("accept_reservations") and dep.get("reservation") and dep.get("artifact") and dep.get("digest"))
                if okay:
                    reservation = model.get(dep["reservation"], "exception")
                    okay = reservation.data.get("task") == other.uid and reservation.data.get("basis") == other.digest() and active_period(reservation.data)
                    okay = okay and subject(model.root, [dep["artifact"]])["digest"] == dep["digest"]
        else: okay = False
        if not okay: pending.append({"dependency": other.uid, "type": dep.get("type"), "required": dep.get("artifact")})
    return pending


def dependency_subjects(model, task):
    result = {}
    for dep in task.data.get("dependencies", []):
        source = model.get(dep["uid"])
        if dep["type"] == "contract": result[source.uid] = {"contract": source.digest()}
        elif dep.get("artifact"):
            result[source.uid] = {"artifact": subject(model.root, [dep["artifact"]]), "basis": source.digest()}
    return result


def evaluate(action, current, facts, policy, exceptions=(), flags=None):
    """Pure: no Git, scanner, file I/O, persistence or user interaction."""
    if action not in TRANSITIONS: raise ContractError("Transición desconocida")
    allowed, target, predicates = TRANSITIONS[action]
    causes = []
    if current not in allowed: causes.append({"rule": "state", "reason": "Estado " + current + " incompatible con " + action})
    needed = set(predicates)
    needed.add("branch")
    needed.update(process_requirements(policy, action, facts, flags))
    waived = {e["rule"]: e for e in exceptions if e.get("action") == action}
    used = []
    for rule in sorted(needed):
        if facts.get(rule) is not True:
            if rule in waived and (rule in EXEMPTIBLE or rule.startswith("process:")): used.append(waived[rule]["uid"])
            else: causes.append({"rule": rule, "reason": "La petición corresponde a otra rama; registre el cambio o su excepción" if rule == "branch" else "Falta acreditar " + rule})
    if used and target == "closed": target = "closed-with-reservations"
    return {"status": "blocked" if causes else "allowed", "state": target, "causes": causes, "exceptions": used}


def evidence_valid(model, task, identity):
    observed = subject(model.root, task.data["scope"])
    expected = set(task.data["tests"])
    results = {}
    implementers = {e.data["actor"]["member"] for e in model.by_kind("execution")
                    if e.data.get("task") == task.uid and e.data.get("action") in {"start", "resume", "implement"}}
    from v3_contract import read_bytes, sha
    for e in sorted(model.by_kind("evidence"), key=lambda item: (item.data.get("recorded_at", ""), item.uid)):
        d = e.data
        if d.get("task") != task.uid or d.get("basis") != task.digest() or d.get("subject") != observed or d.get("dependencies", {}) != dependency_subjects(model, task):
            continue
        valid = d.get("outcome") == "passed"
        if policy_for(model, task).data.get("independent_review") and d["actor"]["member"] in implementers: valid = False
        try:
            valid = valid and sha(read_bytes(model.root, d["artifact"])) == d["artifact_sha256"]
        except ContractError: valid = False
        for test in d.get("tests", []): results[test] = valid
    return bool(expected) and all(results.get(test) is True for test in expected)


def facts_for(model, task, actor):
    plan = plan_for(model, task)
    request = model.get(task.data["request"], "request")
    quality = checks(model, task)
    try: permitted_scope(model, task, actor); assigned = True
    except ContractError: assigned = False
    last = latest(model, task)
    proposal_units = proposal_ready(model, request, task.data.get("proposal_units", plan.data.get("proposal_units")))
    if not set(proposal_units) <= set(request.relations.get("proposal", [])): raise ContractError("Porción de propuesta ajena a la petición")
    from v3_context import select
    context = select(model, [task.uid])
    unresolved = [s["source"] for s in context["sources"] if s.get("meta", {}).get("data", {}).get("critical") and
                  (s["meta"]["state"] in {"unknown", "conflict", "draft"} or s["meta"]["data"].get("unresolved"))]
    technologies = [s["key"] for s in context["sources"] if s.get("meta", {}).get("kind") == "technology"]
    technology_valid = all(approved(model, [key], "technology")["valid"] or approved(model, [key])["valid"] for key in technologies)
    current = state(model, task)
    facts = {"proposal-approved": approved(model, proposal_units)["valid"] and not unresolved and technology_valid,
             "plan-approved": task_authority(model, task, plan, "plan")["valid"],
             "authorized": task_authority(model, task, plan, "execution")["valid"], "assigned": assigned,
             "dependencies": not dependencies(model, task),
             "quality": all(v["mode"] != "required" or v["status"] in {"passed", "not-applicable"} for v in quality.values()),
             "implemented": current in {"implemented", "verified", "closed", "closed-with-reservations"},
             "closed": current in {"closed", "closed-with-reservations"},
             "evidence": evidence_valid(model, task, actor), "verified": current in {"verified", "closed"},
             "scope": bool(last and last.data.get("scope_verified")), "integrated": False, "accepted": False}
    try: branch_check(model, request); facts["branch"] = True
    except ContractError: facts["branch"] = False
    return facts, quality


def valid_exceptions(model, task, action):
    revoked = {e.data.get("revokes") for e in model.by_kind("exception")}
    result = []
    for e in model.by_kind("exception"):
        d = e.data
        if e.uid in revoked or d.get("task") != task.uid or d.get("basis") != task.digest() or d.get("action") != action: continue
        if not active_period(d): continue
        try: operator(model, d["actor"]["member"], "exception", policy_for(model, task))
        except ContractError: continue
        result.append({"uid": e.uid, "rule": d["rule"], "action": action})
    return result


def request_facts(model, request, *, tasks=None, proposal_units=None):
    tasks = tasks if tasks is not None else [t for t in model.by_kind("task") if t.data.get("request") == request.uid and not t.retired]
    try: proposal = approved(model, proposal_ready(model, request, proposal_units))["valid"]
    except ContractError: proposal = False
    states = [state(model, task) for task in tasks]
    facts = {"proposal-approved": proposal,
             "plan-approved": bool(tasks) and all(task_authority(model, t, plan_for(model, t), "plan")["valid"] for t in tasks),
             "authorized": bool(tasks) and all(task_authority(model, t, plan_for(model, t), "execution")["valid"] for t in tasks),
             "assigned": bool(tasks),
             "implemented": bool(tasks) and all(s in {"implemented", "verified", "closed", "closed-with-reservations"} for s in states),
             "verified": bool(tasks) and all(s in {"verified", "closed", "closed-with-reservations"} for s in states),
             "closed": bool(tasks) and all(s in {"closed", "closed-with-reservations"} for s in states),
             "quality": bool(tasks) and all(all(v["mode"] != "required" or v["status"] in {"passed", "not-applicable"} for v in checks(model, t).values()) for t in tasks)}
    from v3_verification import result_current
    from v3_approval import decisions
    facts["integrated"] = any(result_current(model, r, tasks) for r in model.by_kind("receipt") if r.data.get("purpose") == "integration" and r.data.get("request") == request.uid)
    facts["accepted"] = any(result_current(model, r, tasks) for r in decisions(model, "acceptance") if r.data.get("request") == request.uid)
    return facts


def transition(root, actor, task_id, action, reason, *, scope_verified=False, refresh=False):
    model = load(root).require_valid(); task = model.get(task_id, "task")
    permission = "verify" if action in {"verify", "close"} else "authorize" if action == "cancel" else "implement"
    identity = operator(model, actor, permission, policy_for(model, task))
    request = model.get(task.data["request"], "request")
    from v3_git import observe
    branch = observe(model.root)
    coordination(model, request, action=action, refresh=refresh)
    facts, quality = facts_for(model, task, identity["member"])
    previous = latest(model, task)
    baseline = previous.data.get("baseline", {}) if previous else code_inventory(model.root)
    if action in {"implement", "verify", "close"}:
        allowed = permitted_scope(model, task, identity["member"]) if action == "implement" else task.data["scope"]
        diff = scope_changes(model.root, baseline, allowed)
        facts["scope"] = not diff["outside"]
        if diff["outside"]: raise ContractError("Cambios fuera del alcance; conservar y reconciliar: " + ", ".join(diff["outside"][:20]))
    if action in {"verify", "close"} and policy_for(model, task).data.get("independent_review"):
        if identity["member"] in {e.data["actor"]["member"] for e in model.by_kind("execution")
            if e.data.get("task") == task.uid and e.data.get("action") in {"start", "resume", "implement"}}:
            raise ContractError("La revisión independiente corresponde a otra persona")
    result = evaluate(action, state(model, task), facts, policy_for(model, task).data, valid_exceptions(model, task, action), request.data.get("flags", {}))
    if result["status"] != "allowed": raise ContractError("; ".join(c["reason"] for c in result["causes"]))
    if not reason.strip(): raise ContractError("Explique el resultado o motivo del cambio")
    event = element("execution", "Avance de " + task.id, reason, task=task.uid, basis=task.digest(),
                    action=action, state=result["state"], previous=previous.uid if previous else None,
                    actor=identity, subject=subject(model.root, task.data["scope"]), git=branch,
                    dependencies=dependency_subjects(model, task),
                    quality=quality, exceptions=result["exceptions"], recorded_at=now(),
                    baseline=baseline, scope_verified=facts["scope"] if action != "reopen" else False)
    event["meta"].update(state="observed", nature="fact")
    guards = {"git": branch, "subject": event["meta"]["data"]["subject"], "code_inventory": fingerprint(code_inventory(model.root))}
    if result["exceptions"]:
        guards["expires_at"] = min(model.get(k).data["expires_at"] for k in result["exceptions"])
    if action in {"verify", "close"}:
        from v3_quality import valid_until
        expiry = valid_until(model, [task])
        if expiry: guards["expires_at"] = min(guards.get("expires_at", expiry), expiry)
    event["meta"]["data"].update(policy={"uid": policy_for(model, task).uid, "digest": policy_for(model, task).digest()},
                                authorization=task_authority(model, task, plan_for(model, task), "execution")["decisions"])
    from v3_team import assignment, owners
    current_assignment = assignment(model, task)
    event["meta"]["data"].update(assignment=current_assignment.uid if current_assignment else None,
                                contributors=owners(model, task) if facts["assigned"] else [], original_owner=task.data["owner"])
    sources = {p: h for p, h in code_inventory(model.root).items() if h is not None}
    sources.update(model.hashes)
    return prepare(root, [event], "transition:" + action, sources=sources, guards=guards)


def exception(root, actor, task_id, rule, action, reason, expires_at, *, revokes=None):
    model = load(root).require_valid(); task = model.get(task_id, "task")
    identity = operator(model, actor, "exception", policy_for(model, task))
    configured = {"process:" + s["id"] for s in policy_for(model, task).data["steps"]}
    if rule not in EXEMPTIBLE | configured or action not in set(TRANSITIONS) | {"integrate", "accept"} or not reason.strip() or not expires_at:
        raise ContractError("Concrete una excepción admitida, su motivo, transición y vencimiento")
    data = {"task": task.uid, "basis": task.digest(), "actor": identity, "rule": rule, "action": action,
            "expires_at": expires_at, "recorded_at": now(), "effect": "reserve-failure", "revokes": revokes}
    if not active_period(data): raise ContractError("La excepción ya está vencida")
    if revokes: model.get(revokes, "exception")
    event = element("exception", "Excepción delimitada de " + task.id, reason, **data)
    event["meta"].update(state="active", nature="decision")
    return prepare(root, [event], "exception")


def propose_exception(root, actor, task_id, rule, action, reason, effect):
    model = load(root).require_valid(); task = model.get(task_id, "task")
    identity = operator(model, actor, "implement", policy_for(model, task))
    if not all(isinstance(v, str) and v.strip() for v in (rule, action, reason, effect)):
        raise ContractError("Concrete la regla/caso, motivo y efecto solicitado")
    event = element("problem", "Solicitud de excepción", reason, task=task.uid, actor=identity,
                    rule=rule, action=action, requested_effect=effect, decision="pending", recorded_at=now())
    event["meta"].update(state="open", nature="proposal")
    return prepare(root, [event], "propose-exception")
