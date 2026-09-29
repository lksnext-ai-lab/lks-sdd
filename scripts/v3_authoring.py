"""Creation, authoring and explicit decisions. No application code is generated."""
import copy
from pathlib import Path
import tempfile

from v3_contract import (ContractError, DOCS, EVENTS, METHOD, INDEX, element, load, location,
                         render, fingerprint, now)
from v3_policy import profile, validate_policy, operator
from v3_approval import decision, descriptor, proposal_ready, approved, plan_coverage
from v3_git import observe, branch_check
from v3_storage import prepare, staged_write
from v2_storage import write_one
from v2_contract import read_bytes, canonical


def initialize(root, name, actor_name, process, controls, statement, *, target, lifecycle="evolution", members=None):
    root = Path(root).resolve()
    if (root / INDEX).exists() or (root / DOCS).exists():
        raise ContractError("El proyecto ya tiene documentación; adoptar o migrar explícitamente")
    if not statement.strip() or not actor_name.strip() or not target:
        raise ContractError("Confirme nombre del operador, configuración y destino")
    git = observe(root)
    if not git["branch"]: raise ContractError("Seleccione una rama de trabajo antes de inicializar")
    owner = element("member", actor_name, "Miembro inicial declarado por el interlocutor.",
                    roles=["owner", "specifier", "developer", "reviewer", "integrator"], active=True,
                    identity_history=[{"name": actor_name, "source": "explicit-declaration", "since": now()}])
    policy = element("policy", "Proceso del proyecto", "Configuración inicial expresamente confirmada.", **profile(process, controls))
    if lifecycle not in {"new", "bounded-delivery", "evolution", "maintenance"}: raise ContractError("Momento de vida no reconocido")
    policy["meta"]["data"]["lifecycle"] = lifecycle
    additional = []
    from v3_policy import ROLES
    for value in members or []:
        if not value.get("name") or not value.get("roles") or set(value["roles"])-ROLES:
            raise ContractError("Declare nombre y funciones de cada miembro inicial")
        person = element("member", value["name"], "Miembro declarado en la configuración inicial.", roles=value["roles"], active=True,
                         identity_history=[{"name": value["name"], "source": "explicit-bootstrap", "since": now()}])
        person["meta"].update(state="active", nature="decision"); additional.append(person)
    if policy["meta"]["data"]["independent_review"] and not any("reviewer" in m["meta"]["data"]["roles"] for m in additional):
        raise ContractError("La revisión separada necesita un segundo miembro con función de revisión")
    project = element("project", name, "Proyecto con Markdown canónico e índice derivado.",
                      method_version=METHOD, policy=policy["meta"]["uid"], target=target,
                      initialized_by=owner["meta"]["uid"], initialized_at=now())
    project["meta"]["relations"] = {"policy": [policy["meta"]["uid"]], "members": [owner["meta"]["uid"], *(m["meta"]["uid"] for m in additional)]}
    for obj in (owner, policy, project): obj["meta"].update(state="active", nature="decision")
    items = [project, owner, policy, *additional]
    from v3_contract import Element
    units = {obj["meta"]["uid"]: Element(obj["meta"], obj["body"], location(obj)).digest() for obj in items}
    bootstrap = element("decision", "Configuración inicial aceptada", statement, purpose="governance", outcome="approved",
                        actor={"member": owner["meta"]["uid"], "assurance": "declared", "source": "explicit-bootstrap"},
                        descriptor={"units": units, "digest": fingerprint(units)}, decided_at=now(), bootstrap=True)
    bootstrap["meta"].update(state="approved", nature="decision")
    items.append(bootstrap)
    packet = prepare(root, items, "initialize")
    packet["summary"].update(project=project["meta"]["uid"], member=owner["meta"]["uid"], policy=policy["meta"]["uid"], branch=git["branch"])
    return packet


def candidate(root, items, callback):
    """Read a prospective set without mutating the project or executing its content."""
    model = load(root).require_valid()
    from v3_policy import policy_for
    from v3_migration import include_confirmation_sources
    include_confirmation_sources(model)
    for request in model.by_kind("request"): policy_for(model, request)
    with tempfile.TemporaryDirectory(prefix="lks-v3-author-") as temp:
        stage = Path(temp)
        for path in model.hashes: staged_write(stage, path, read_bytes(model.root, path))
        for item in items:
            old = model.elements.get(item["meta"]["uid"])
            if old and sum(e.path == old.path for e in model.elements.values()) > 1:
                from v3_contract import BLOCK
                import json
                raw = read_bytes(stage, old.path).decode("utf-8")
                block = BLOCK.search(render(item).decode("utf-8"))[0]
                raw = BLOCK.sub(lambda m: block if json.loads(m[1])["uid"] == old.uid else m[0], raw)
                staged_write(stage, old.path, raw.encode("utf-8"))
            else: staged_write(stage, old.path if old else location(item), render(item))
        prospective = load(stage).require_valid()
        return callback(prospective)


def author(root, actor, items):
    model = load(root).require_valid()
    identity = operator(model, actor, "define")
    items = copy.deepcopy(items)
    plans = [obj for obj in items if obj["meta"]["kind"] == "plan"]
    for item in items:
        meta = item["meta"]
        if meta["kind"] == "task" and "proposal_units" not in meta["data"]:
            matching = [p for p in plans if meta["uid"] in p["meta"]["relations"].get("tasks", [])]
            if matching and matching[0]["meta"]["data"].get("proposal_units"):
                meta["data"]["proposal_units"] = matching[0]["meta"]["data"]["proposal_units"]
            elif meta["data"].get("request") in model.elements:
                meta["data"]["proposal_units"] = model.get(meta["data"]["request"]).relations.get("proposal", [])
        if meta["kind"] in EVENTS:
            raise ContractError("Decisiones y evidencia se registran mediante su operación específica")
        previous = model.elements.get(meta["uid"])
        if previous:
            if previous.kind != meta["kind"]: raise ContractError("No cambiar el tipo de una identidad")
            if meta["revision"] != previous.meta["revision"] + 1: raise ContractError("Incrementar la revisión normativa exacta")
            if meta["kind"] in {"project", "policy", "member"}: operator(model, actor, "govern")
        elif meta["revision"] != 1: raise ContractError("Una entidad nueva comienza en revisión 1")
        if meta["kind"] in {"policy", "member", "project"}:
            raise ContractError("Cambios de gobierno requieren governance con motivo y alcance explícitos")
        if meta["kind"] == "request":
            policy = model.get(model.project.data["policy"], "policy")
            meta["data"].setdefault("policy", policy.uid)
            meta["data"].setdefault("policy_digest", policy.digest())
            obs = observe(model.root)
            meta["data"].setdefault("branches", [obs["branch"]])
            meta["data"].setdefault("target", model.project.data["target"])
            meta["data"].setdefault("base", obs)
            if not obs["branch"] or obs["branch"] not in meta["data"]["branches"]: raise ContractError("Rama de petición incoherente")
            if obs["branch"] == meta["data"]["target"]: raise ContractError("Cree o seleccione la rama identificada de la petición antes de documentarla")
        elif meta["data"].get("request"):
            requests = {obj["meta"]["uid"]: obj for obj in items if obj["meta"]["kind"] == "request"}
            if meta["data"]["request"] not in requests: branch_check(model, model.get(meta["data"]["request"], "request"))
    def check(prospective):
        for obj in items:
            if obj["meta"]["kind"] == "plan": plan_coverage(prospective, prospective.get(obj["meta"]["uid"]))
            if obj["meta"]["kind"] == "task":
                task = prospective.get(obj["meta"]["uid"])
                request = prospective.get(task.data["request"], "request")
                if not approved(prospective, proposal_ready(prospective, request, task.data.get("proposal_units")))["valid"]:
                    raise ContractError("Validar la propuesta antes de crear tareas ejecutables")
    candidate(root, items, check)
    from v3_contract import Element
    entry = element("receipt", "Autoría del contrato", "Cambio documental dentro del encargo de definición.", purpose="authoring", actor=identity,
                    units=[{"uid": o["meta"]["uid"], "revision": o["meta"]["revision"], "digest": Element(o["meta"], o["body"], location(o)).digest()} for o in items], recorded_at=now())
    entry["meta"].update(state="observed", nature="fact")
    return prepare(root, items + [entry], "author", guards={"git": observe(model.root)})


def approve(root, actor, identifiers, purpose, statement, *, reason=""):
    model = load(root).require_valid()
    if purpose not in {"proposal", "plan", "execution", "technology"}:
        raise ContractError("Finalidad de aprobación desconocida")
    ids = [model.get(x).uid for x in identifiers]
    if purpose in {"plan", "execution"}:
        for key in ids: plan_coverage(model, model.get(key, "plan"))
        if purpose == "execution" and not approved(model, ids, "plan")["valid"]:
            raise ContractError("El plan concreto todavía no está aprobado")
    if purpose == "proposal":
        for request in model.by_kind("request"):
            selected = set(request.relations.get("proposal", [])) & set(ids)
            if selected:
                proposal_ready(model, request, sorted(selected), require_complete=False)
                approval_process(model, request, "approve-proposal", [], sorted(selected))
    if purpose in {"plan", "execution"}:
        for key in ids:
            plan = model.get(key, "plan")
            approval_process(model, model.get(plan.data["request"]), "authorize-plan",
                             [model.get(k) for k in plan.relations["tasks"]], plan.data.get("proposal_units"))
    record = decision(model, actor, ids, purpose, statement, reason=reason)
    return prepare(root, [record], "approve:" + purpose)


def approval_process(model, request, action, tasks, units):
    from v3_workflow import request_facts
    from v3_policy import require_process, policy_for
    facts = request_facts(model, request, tasks=tasks, proposal_units=units)
    require_process(policy_for(model, request).data, action, facts, request.data.get("flags", {}))


def approve_and_authorize(root, actor, plan_uid, statement):
    model = load(root).require_valid()
    plan = model.get(plan_uid, "plan")
    plan_coverage(model, plan)
    approval_process(model, model.get(plan.data["request"]), "authorize-plan",
                     [model.get(k) for k in plan.relations["tasks"]], plan.data.get("proposal_units"))
    records = [decision(model, actor, [plan.uid], purpose, statement) for purpose in ("plan", "execution")]
    return prepare(root, records, "approve-plan-and-authorize")


def governance(root, actor, items, statement, reason, *, requests=()):
    model = load(root).require_valid()
    identity = operator(model, actor, "govern")
    if not statement.strip() or not reason.strip(): raise ContractError("Confirme motivo y alcance del cambio de gobierno")
    items = copy.deepcopy(items)
    for obj in items:
        meta = obj["meta"]
        if meta["kind"] not in {"member", "policy", "project"}: raise ContractError("Objeto ajeno al gobierno")
        old = model.elements.get(meta["uid"])
        if old and (old.kind != meta["kind"] or meta["revision"] != old.meta["revision"]+1):
            raise ContractError("Conservar identidad/tipo e incrementar revisión de gobierno")
        if not old and meta["revision"] != 1: raise ContractError("Revisión inicial inválida")
        if meta["kind"] == "policy": validate_policy(meta["data"])
    def check(prospective):
        active = [m for m in prospective.by_kind("member") if m.data.get("active", True) and not m.retired]
        if not any("owner" in m.data.get("roles", []) for m in active): raise ContractError("El proyecto quedaría sin responsable de gobierno")
        policy = prospective.get(prospective.project.data["policy"], "policy")
        if policy.data.get("independent_review") and (len(active) < 2 or not any("reviewer" in m.data.get("roles", []) for m in active)):
            raise ContractError("La revisión independiente necesita otro miembro habilitado")
        return descriptor(prospective, [obj["meta"]["uid"] for obj in items])
    candidate(root, items, check)
    from v3_contract import Element
    policy_items = {o["meta"]["uid"]: o for o in items if o["meta"]["kind"] == "policy"}
    for key in requests:
        request = model.get(key, "request")
        updated = copy.deepcopy(request.item()); updated["meta"]["revision"] += 1
        policy = policy_items.get(request.data["policy"])
        if policy is None: raise ContractError("Indique la revisión de proceso que adoptan las peticiones afectadas")
        updated["meta"]["data"]["policy_digest"] = Element(policy["meta"], policy["body"], location(policy)).digest()
        items.append(updated)
    desc = candidate(root, items, check)
    record = element("decision", "Cambio de gobierno aceptado", statement, purpose="governance", outcome="approved",
                     actor=identity, descriptor=desc, reason=reason, requests=list(requests), decided_at=now())
    record["meta"].update(nature="decision", state="approved")
    return prepare(root, items+[record], "governance")
