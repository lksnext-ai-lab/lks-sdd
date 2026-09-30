"""Integral review: exact subjects, named people and reusable human decisions."""
import copy

from v3_contract import ContractError, Element, element, fingerprint, load, location, now
from v3_policy import operator, policy_for, active_period
from v3_approval import descriptor, proposal_ready, decisions, task_basis
from v3_storage import prepare

REVIEW_PURPOSES = {"proposal-review", "proposal-closure", "task-review",
                   "review-comment", "comment-resolution", "review-exception"}


def config(model, request=None):
    return policy_for(model, request).data.get("collaboration", {})


def validate_config(value):
    from v3_schema import validate
    validate("collaboration", value, "3.1")
    if not isinstance(value, dict) or set(value) - {"proposal_review_required", "task_review_required", "defaults"}:
        raise ContractError("Configuración de colaboración desconocida")
    for key in ("proposal_review_required", "task_review_required"):
        if type(value.get(key)) is not bool:
            raise ContractError("Declare explícitamente " + key)
    validate_roster(value.get("defaults"))
    if value["proposal_review_required"] and not any(r["required"] for r in value["defaults"]["reviewers"]):
        raise ContractError("La revisión integral obligatoria requiere al menos una persona designada")


def validate_roster(value):
    if not isinstance(value, dict) or set(value) != {"responsible", "integration_validator", "functional_validator", "reviewers"}:
        raise ContractError("Designe responsable, validadores y revisores")
    from v3_contract import uid
    for name in ("responsible", "integration_validator", "functional_validator"): uid(value[name])
    if not isinstance(value["reviewers"], list): raise ContractError("Lista de revisores requerida")
    for row in value["reviewers"]:
        if set(row) != {"member", "required", "domains"} or type(row["required"]) is not bool:
            raise ContractError("Revisor incompleto")
        uid(row["member"])
        if not isinstance(row["domains"], list) or any(not isinstance(x, str) or not x.strip() for x in row["domains"]):
            raise ContractError("Ámbitos del revisor inválidos")


def validate_model(model):
    """Validate extension data on every load, including hand-written documents."""
    extended = model.project.data["method_version"] == "3.1.0"
    for e in model.elements.values():
        d = e.data
        if e.kind == "policy" and "collaboration" in d:
            if not extended: raise ContractError("La colaboración integral requiere adoptar formato 3.1")
            validate_config(d["collaboration"])
            roster = d["collaboration"]["defaults"]
            for key in {roster[x] for x in ("responsible", "integration_validator", "functional_validator")} | {r["member"] for r in roster["reviewers"]}:
                model.get(key, "member")
        if e.kind == "request" and "coordination" in d:
            if not extended: raise ContractError("La coordinación integral requiere formato 3.1")
            validate_roster(d["coordination"])
            if config(model, e).get("proposal_review_required") and not any(r["required"] for r in d["coordination"]["reviewers"]):
                raise ContractError("Designe un revisor obligatorio o cambie explícitamente la política")
            for key in {d["coordination"][x] for x in ("responsible", "integration_validator", "functional_validator")} | {r["member"] for r in d["coordination"]["reviewers"]}:
                model.get(key, "member")
        if d.get("purpose") in REVIEW_PURPOSES:
            expected_kind = "problem" if d["purpose"] == "review-comment" else "decision"
            if e.kind != expected_kind: raise ContractError("Una revisión debe registrarse con su operación y tipo, no como autoría normativa")
            if not extended: raise ContractError("Evento de revisión incompatible con formato 3.0")
            if d.get("outcome") == "revoked": continue
            for key in ("actor", "request", "recorded_at"):
                if not d.get(key): raise ContractError("Evento de revisión incompleto: " + key)
            model.get(d["actor"]["member"], "member"); model.get(d["request"], "request")
            if not e.body.strip(): raise ContractError("La revisión necesita una declaración")
            purpose = d["purpose"]
            if purpose in {"proposal-review", "proposal-closure", "task-review", "review-comment"} and not isinstance(d.get("basis"), dict):
                raise ContractError("Falta contenido exacto de revisión")
            if purpose in {"proposal-review", "task-review"} and d.get("outcome") not in {"approved", "changes-requested"}:
                raise ContractError("Resultado de revisión desconocido")
            if purpose == "task-review": model.get(d.get("task"), "task")
        if d.get("purpose") in {"development-defect", "defect-resolution", "correction-classification", "correction-definition", "delivery-preparation"}:
            expected = {"development-defect": "problem", "defect-resolution": "decision", "correction-classification": "decision",
                        "correction-definition": "change", "delivery-preparation": "receipt"}[d["purpose"]]
            if not extended or e.kind != expected: raise ContractError("Tipo/formato de corrección incompatible")
            if d.get("outcome") == "revoked": continue
            model.get(d.get("request"), "request")
            if d["purpose"] == "development-defect":
                if d.get("phase") not in {"integration", "acceptance", "external"} or not d.get("tasks"):
                    raise ContractError("Falta fase o tareas del defecto")
                for key in ("expected", "observed", "artifact", "artifact_sha256", "subject", "actor"):
                    if not d.get(key): raise ContractError("Defecto incompleto: " + key)


def roster(model, request):
    value = request.data.get("coordination", config(model, request).get("defaults"))
    validate_roster(value)
    return value


def reviewers(model, request):
    result = {}
    for row in roster(model, request)["reviewers"]:
        entry = result.setdefault(row["member"], {"member": row["member"], "required": False, "domains": []})
        entry["required"] |= row["required"]
        entry["domains"] = sorted(set(entry["domains"]) | set(row["domains"]))
    return list(result.values())


def designated(model, request, actor, role, permission):
    identity = operator(model, actor, permission, policy_for(model, request))
    if config(model, request) and roster(model, request)[role] != identity["member"]:
        raise ContractError("Corresponde a la persona designada como " + role)
    return identity


def proposal_basis(model, request):
    return {"descriptor": descriptor(model, proposal_ready(model, request)),
            "coordination": roster(model, request), "policy": policy_for(model, request).digest()}


def records(model, purpose, request=None):
    revoked = {e.data.get("revokes") for e in model.by_kind("decision") + model.by_kind("exception")}
    return [e for e in model.elements.values() if e.uid not in revoked and e.data.get("outcome") != "revoked"
            and e.data.get("purpose") == purpose and (request is None or e.data.get("request") == request.uid)]


def event(purpose, identity, request, statement, **data):
    if not isinstance(statement, str) or not statement.strip(): raise ContractError("Exprese la decisión concreta")
    obj = element("problem" if purpose == "review-comment" else "decision", purpose, statement,
                  purpose=purpose, actor=identity, request=request.uid, recorded_at=now(), **data)
    obj["meta"].update(state="observed" if purpose == "review-comment" else ("proposed" if data.get("outcome") == "changes-requested" else "approved"), nature="fact" if purpose == "review-comment" else "decision")
    return obj



def group_intervention(items):
    """A shared reference records one explicit answer covering several results."""
    if len(items) > 1:
        reference = items[0]["meta"]["uid"]
        for item in items:
            item["meta"]["data"]["intervention"] = reference
    return items


def overlay(model, items):
    for item in items:
        e = Element(item["meta"], item["body"], location(item)); model.elements[e.uid] = e


def review_event(model, request, actor, statement, outcome="approved"):
    identity = operator(model, actor, "approve", policy_for(model, request))
    if identity["member"] not in {r["member"] for r in reviewers(model, request)}:
        raise ContractError("No está designado para revisar esta propuesta")
    if outcome not in {"approved", "changes-requested"}: raise ContractError("Resultado de revisión inválido")
    basis = proposal_basis(model, request)
    previous = vote_tip(model, "proposal-review", identity["member"], basis)
    return event("proposal-review", identity, request, statement, outcome=outcome, basis=basis,
                 previous=previous.uid if previous else None, dispositions=dispositions(model, request, identity["member"]))


def dispositions(model, request, actor=None):
    return {e.uid: [r.uid for r in records(model, "comment-resolution", request) if r.data.get("comment") == e.uid]
            for e in records(model, "review-comment", request)
            if actor is None or (e.data["actor"]["member"] == actor and (e.data.get("blocking") or e.data.get("critical")))}


def vote_tip(model, purpose, actor, basis):
    votes = [e for e in records(model, purpose) if e.data["actor"]["member"] == actor and e.data.get("basis") == basis]
    replaced = {e.data.get("previous") for e in votes}
    tips = [e for e in votes if e.uid not in replaced]
    if len(tips) > 1: raise ContractError("Decisiones concurrentes: revoque las contradictorias y reconcilie explícitamente")
    return tips[0] if tips else None


def waivers(model, request, rule, action):
    result = []
    for e in records(model, "review-exception", request):
        d = e.data
        if d.get("rule") != rule or d.get("action") != action or d.get("basis") != proposal_basis(model, request) or not active_period(d): continue
        try: operator(model, d["actor"]["member"], "exception", policy_for(model, request))
        except ContractError: continue
        result.append(e)
    return result


def review_status(model, request):
    basis = proposal_basis(model, request)
    current_dispositions = dispositions(model, request)
    pending, accepted = [], {}
    for row in reviewers(model, request):
        person = row["member"]
        last = vote_tip(model, "proposal-review", person, basis)
        valid = bool(last and last.data["outcome"] == "approved" and last.data.get("dispositions") == dispositions(model, request, person))
        try: operator(model, person, "approve", policy_for(model, request))
        except ContractError: valid = False
        if valid: accepted[person] = last.uid
        elif row["required"]: pending.append(person)
    open_comments = []
    for comment in records(model, "review-comment", request):
        solutions = current_dispositions[comment.uid]
        person = comment.data["actor"]["member"]
        if (comment.data.get("blocking") or comment.data.get("critical")) and (len(solutions) != 1 or person not in accepted):
            open_comments.append(comment.uid)
    return {"basis": basis, "pending": pending, "conformities": accepted, "open_comments": open_comments}


def closure_valid(model, request):
    if not config(model, request): return True
    try: basis = proposal_basis(model, request)
    except ContractError: return False
    for e in records(model, "proposal-closure", request):
        if e.data.get("basis") != basis: continue
        try:
            designated(model, request, e.data["actor"]["member"], "responsible", "approve")
            check_close(model, request)
            return True
        except ContractError: pass
    return False


def check_close(model, request):
    state = review_status(model, request)
    for key in state["basis"]["descriptor"]["units"]:
        source = model.get(key)
        if source.data.get("critical") and (source.data.get("unresolved") or source.meta["state"] in {"unknown", "conflict", "draft"}):
            raise ContractError("Resolver la decisión crítica: " + source.id)
    missing = state["pending"] if config(model, request)["proposal_review_required"] else []
    if (missing or state["open_comments"]) and not waivers(model, request, "integral-review", "close-proposal"):
        raise ContractError("Faltan conformidades u objeciones resueltas: " + str(missing + state["open_comments"]))
    return state


def task_review_basis(model, task, actor):
    from v3_workflow import plan_for
    from v3_team import owners, assignment
    mine = [r for r in owners(model, task) if r["member"] == actor]
    if not mine: raise ContractError("No es destinatario de este encargo")
    assigned = assignment(model, task)
    return {"task": task_basis(model, task, plan_for(model, task)), "assignment": assigned.uid if assigned else None,
            "portions": mine}


def task_review_event(model, task, actor, statement, outcome="approved"):
    identity = operator(model, actor, "implement", policy_for(model, task))
    if outcome not in {"approved", "changes-requested"}: raise ContractError("Resultado de encargo inválido")
    request = model.get(task.data["request"], "request")
    basis = task_review_basis(model, task, identity["member"])
    previous = vote_tip(model, "task-review", identity["member"], basis)
    return event("task-review", identity, request, statement, task=task.uid,
                 basis=basis, outcome=outcome, previous=previous.uid if previous else None)


def task_reviewed(model, task, actor):
    if not config(model, task).get("task_review_required"): return True
    try: basis = task_review_basis(model, task, actor)
    except ContractError: return False
    last = vote_tip(model, "task-review", actor, basis)
    return bool(last and last.data["outcome"] == "approved")


def execute(action, root, data):
    model = load(root).require_valid(); actor = data.get("actor")
    request = model.get(data["request"], "request")
    if not config(model, request): raise ContractError("Active explícitamente el recorrido integral para esta petición")
    from v3_git import branch_check, coordination
    branch = branch_check(model, request)
    coordination(model, request, action, refresh=data.get("refresh", False))
    statement = data.get("statement", ""); items = []
    if action == "review-proposal":
        current = review_status(model, request)["conformities"].get(actor)
        if current and data.get("outcome", "approved") == "approved":
            return {"status": "already-recorded", "decisions": [current], "writes": []}
        items = [review_event(model, request, actor, statement, data.get("outcome", "approved"))]
    elif action == "close-proposal":
        identity = designated(model, request, actor, "responsible", "approve")
        if closure_valid(model, request):
            return {"status": "already-recorded", "request": request.uid, "writes": []}
        if data.get("review"):
            items.append(review_event(model, request, actor, statement)); overlay(model, items)
        state = check_close(model, request)
        from v3_approval import decision
        items += [event("proposal-closure", identity, request, statement, basis=state["basis"],
                        outcome="approved", conformities=state["conformities"],
                        exceptions=[e.uid for e in waivers(model, request, "integral-review", "close-proposal")]),
                  decision(model, actor, proposal_ready(model, request), "proposal", statement)]
    elif action == "review-task":
        for key in data["tasks"]:
            task = model.get(key, "task")
            if task.data["request"] != request.uid: raise ContractError("Encargo de otra petición")
            if data.get("outcome", "approved") != "approved" or not task_reviewed(model, task, actor):
                items.append(task_review_event(model, task, actor, statement, data.get("outcome", "approved")))
        if not items and data["tasks"]:
            return {"status": "already-recorded", "tasks": data["tasks"], "writes": []}
    elif action == "review-comment":
        identity = operator(model, actor, "approve", policy_for(model, request))
        if identity["member"] not in {r["member"] for r in reviewers(model, request)}: raise ContractError("Revisor no designado")
        target = model.get(data["target"])
        if target.uid not in proposal_basis(model, request)["descriptor"]["units"]: raise ContractError("Objeto fuera de la propuesta integral")
        items = [event("review-comment", identity, request, statement, basis=proposal_basis(model, request),
                       target=target.uid, blocking=bool(data.get("blocking", True)), critical=bool(data.get("critical", False)))]
    elif action == "resolve-comment":
        identity = designated(model, request, actor, "responsible", "approve")
        comment = model.get(data["comment"], "problem")
        if comment.data.get("request") != request.uid or comment.data.get("purpose") != "review-comment": raise ContractError("Observación ajena")
        if any(e.data.get("comment") == comment.uid for e in records(model, "comment-resolution", request)):
            raise ContractError("Resolución existente; revóquela explícitamente antes de sustituirla")
        if data.get("treatment") not in {"incorporated", "dismissed"}: raise ContractError("Tratamiento desconocido")
        items = [event("comment-resolution", identity, request, statement, comment=comment.uid,
                       treatment=data["treatment"], basis=proposal_basis(model, request), outcome="approved")]
    elif action == "review-exception":
        identity = operator(model, actor, "exception", policy_for(model, request))
        if data.get("rule") != "integral-review" or data.get("action") != "close-proposal": raise ContractError("Excepción de revisión no admitida")
        if not data.get("effect") or not active_period({"expires_at": data.get("expires_at")} ) or not data.get("expires_at"):
            raise ContractError("Concrete efecto y vencimiento futuro")
        items = [event("review-exception", identity, request, statement, rule=data["rule"], action=data["action"],
                       effect=data["effect"], expires_at=data["expires_at"], basis=proposal_basis(model, request), outcome="approved")]
    else: raise ContractError("Operación integral desconocida")
    if not items: raise ContractError("Seleccione una decisión concreta")
    guards = {"git": branch}
    if action == "close-proposal":
        exceptions = waivers(model, request, "integral-review", action)
        if exceptions: guards["expires_at"] = min(e.data["expires_at"] for e in exceptions)
    return prepare(root, group_intervention(items), action, guards=guards)


def configure(root, actor, collaboration, statement, *, requests=(), coordination=None, runtime_bundle=None):
    """Explicit 3.0 -> 3.1 adoption, also used for subsequent governance."""
    model = load(root).require_valid(); operator(model, actor, "govern")
    validate_config(collaboration)
    items = []
    project = copy.deepcopy(model.project.item()); project["meta"]["revision"] += 1
    project["meta"]["data"]["method_version"] = "3.1.0"; items.append(project)
    policy = copy.deepcopy(policy_for(model).item()); policy["meta"]["revision"] += 1
    policy["meta"]["data"]["collaboration"] = collaboration
    items.append(policy)
    pd = Element(policy["meta"], policy["body"], location(policy)).digest()
    for key in requests:
        request = model.get(key, "request"); item = copy.deepcopy(request.item())
        item["meta"]["revision"] += 1
        item["meta"]["data"].update(policy=policy["meta"]["uid"], policy_digest=pd,
                                    coordination=coordination or collaboration["defaults"])
        items.append(item)
    identity = operator(model, actor, "govern")
    if not statement.strip(): raise ContractError("Confirme configuración y alcance de la adopción")
    record = element("decision", "Recorrido integral configurado", statement, purpose="governance", outcome="approved",
                     actor=identity, recorded_at=now(), requests=list(requests), previous_policy=policy_for(model).digest(),
                     descriptor={"units": {i["meta"]["uid"]: Element(i["meta"], i["body"], location(i)).digest() for i in items}})
    record["meta"].update(state="approved", nature="decision"); items.append(record)
    changes = {}; guards = {}
    lock = model.root / ".lks-sdd/distribution-lock.json"
    if lock.exists() and model.project.data["method_version"] == "3.0.0":
        if not runtime_bundle: raise ContractError("Incluya el bundle del runtime compatible en la adopción explícita")
        import importlib.util
        from pathlib import Path
        spec = importlib.util.spec_from_file_location("review_runtime_install", Path(__file__).resolve().parents[1]/"distribution/install.py")
        installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
        install = installer.plan(Path(runtime_bundle), model.root, "copilot", contract_transition=("3.0", "3.1"))
        changes = {e["path"]: bytes.fromhex(e["content"]) if e["content"] is not None else None for e in install["changes"]}
        guards["target_runtime"] = True
    return prepare(root, items, "configure-collaboration", changes=changes, guards=guards)
