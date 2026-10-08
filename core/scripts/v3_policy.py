"""Explicit project process and authority. Repository content never executes predicates."""
from datetime import datetime, timezone
from v3_contract import ContractError, now

PROFILES = ("individual-brief", "coordinated-team", "independent-review")
ROLES = {"owner", "specifier", "developer", "reviewer", "integrator"}
PERMISSIONS = {"govern": {"owner"}, "define": {"owner", "specifier"}, "approve": {"owner", "specifier", "reviewer"},
               "plan": {"owner", "specifier"}, "authorize": {"owner", "specifier"},
               "implement": {"owner", "developer"}, "verify": {"owner", "reviewer"},
               "integrate": {"owner", "integrator"}, "exception": {"owner"}, "assign": {"owner", "specifier"}}
PREDICATES = {"proposal-approved", "plan-approved", "authorized", "assigned", "quality", "implemented", "verified", "closed", "integrated", "accepted"}


def active_period(value):
    current = datetime.now(timezone.utc)
    for field, op in (("valid_from", "start"), ("expires_at", "end")):
        if value.get(field):
            try:
                date = datetime.fromisoformat(value[field].replace("Z", "+00:00"))
                if date.tzinfo is None: raise ValueError()
            except (ValueError, TypeError) as exc: raise ContractError("Vigencia debe tener zona horaria: " + field) from exc
            if (op == "start" and date > current) or (op == "end" and date <= current): return False
    return not value.get("revoked", False)


def profile(name, controls):
    if name not in PROFILES: raise ContractError("Seleccione un recorrido conocido")
    value = {"profile": name, "lifecycle": "evolution", "identity": "declared",
             "permissions": {key: sorted(roles) for key, roles in PERMISSIONS.items()}, "acceptance_order": "after-integration",
             "independent_review": name == "independent-review", "offline_actions": ["query"],
             "controls": controls, "steps": [
                 {"id": "definition", "label": "Propuesta", "requires": [], "conditions": [], "complete_when": ["proposal-approved"], "actions": ["approve-proposal"]},
                 {"id": "planning", "label": "Planificación", "requires": ["definition"], "conditions": ["proposal-approved"], "complete_when": ["plan-approved", "authorized"], "actions": ["authorize-plan"]},
                 {"id": "implementation", "label": "Implementación", "requires": ["planning"], "conditions": ["plan-approved", "authorized", "assigned"], "complete_when": ["implemented"], "actions": ["start", "resume", "implement"]},
                 {"id": "verification", "label": "Comprobación", "requires": ["implementation"], "conditions": ["quality"], "complete_when": ["verified", "closed"], "actions": ["verify", "close"]},
                 {"id": "integration", "label": "Integración", "requires": ["verification"], "conditions": ["verified"], "complete_when": ["integrated"], "actions": ["integrate"]},
                 {"id": "acceptance", "label": "Aceptación funcional", "requires": ["integration"], "conditions": ["integrated"], "complete_when": ["accepted"], "actions": ["accept"]}]}
    validate_policy(value)
    return value


def validate_policy(data):
    if data.get("identity") not in {"declared", "observed", "authenticated"}:
        raise ContractError("Falta el grado de comprobación de identidad")
    controls = data.get("controls", {})
    permissions = data.get("permissions", {})
    if set(permissions) != set(PERMISSIONS) or any(not roles or set(roles)-ROLES for roles in permissions.values()):
        raise ContractError("Defina funciones competentes para cada decisión del proyecto")
    if data.get("acceptance_order") not in {"before-integration", "after-integration"}:
        raise ContractError("Decida el orden entre aceptación e integración")
    if set(controls) != {"sonar", "dependency-check"}: raise ContractError("Decida por separado Sonar y Dependency-Check")
    for name, control in controls.items():
        if control.get("mode") not in {"required", "informative", "not-used"}:
            raise ContractError("Falta decisión de uso: " + name)
        if not control.get("reason"): raise ContractError("Falta motivo del control: " + name)
        if control["mode"] != "not-used":
            availability = control.get("availability", {})
            if availability.get("state") != "available" or not availability.get("source") or availability.get("phase") != "implementation":
                raise ContractError("Confirme un medio disponible durante implementación antes de activar " + name + "; un análisis disponible solo en PR no permite este cierre")
            if not control.get("executor") or not control.get("scope"):
                raise ContractError("Falta medio viable/ámbito de análisis: " + name)
            if control.get("executor") not in {"existing-command", "existing-report"}:
                raise ContractError("Ejecutor no soportado; no se instalará infraestructura")
            if control["executor"] == "existing-command" and (not control.get("executable_sha256") or not control.get("arguments_digest")):
                raise ContractError("Autorice el ejecutor existente y sus argumentos exactos: " + name)
            if not isinstance(control["scope"], list) or any(not isinstance(p, str) or not p for p in control["scope"]):
                raise ContractError("Ámbito de análisis debe contener rutas concretas")
            if not 0 < control.get("timeout_seconds", 0) <= 3600 or not 0 <= control.get("max_retries", -1) <= 10:
                raise ContractError("Faltan límites de espera/reintentos: " + name)
    steps = data.get("steps", [])
    ids = [s.get("id") for s in steps]
    if not ids or len(set(ids)) != len(ids): raise ContractError("Pasos vacíos o duplicados")
    remaining = set(ids)
    while remaining:
        ready = {s["id"] for s in steps if s["id"] in remaining and all(d in set(ids)-remaining for d in s.get("requires", []))}
        if not ready: raise ContractError("Proceso con dependencia desconocida o ciclo sin salida")
        remaining -= ready
    for step in steps:
        if not step.get("label") or (set(step.get("conditions", [])) | set(step.get("complete_when", [])))-PREDICATES:
            raise ContractError("Condición no interpretable; requiere decisión concreta")
        if not step.get("complete_when"): raise ContractError("El paso necesita un resultado de terminación comprobable")
        when = step.get("when")
        if when and (set(when) != {"flag", "equals"} or not isinstance(when["equals"], bool)):
            raise ContractError("Condición de aplicabilidad no interpretable")
    def ancestors(key):
        item = next(s for s in steps if s["id"] == key)
        return set(item.get("requires", [])) | {a for parent in item.get("requires", []) for a in ancestors(parent)}
    integration = {s["id"] for s in steps if "integrate" in s.get("actions", [])}
    acceptance = {s["id"] for s in steps if "accept" in s.get("actions", [])}
    if data["acceptance_order"] == "before-integration":
        if any(integration & ancestors(key) for key in acceptance) or any("integrated" in s.get("conditions", []) for s in steps if s["id"] in acceptance):
            raise ContractError("El proceso exige integración antes de una aceptación declarada previa; ajuste ambos pasos")
    elif any(acceptance & ancestors(key) for key in integration) or any("accepted" in s.get("conditions", []) for s in steps if s["id"] in integration):
        raise ContractError("El proceso exige aceptación antes de una integración declarada previa; ajuste ambos pasos")
    return data


def steps_state(policy, facts, flags=None):
    flags = flags or {}
    result = {}
    pending = list(policy["steps"])
    while pending:
        step = next(s for s in pending if all(k in result for k in s.get("requires", [])))
        pending.remove(step)
        when = step.get("when")
        applies = None if when and when["flag"] not in flags else not when or flags[when["flag"]] == when["equals"]
        complete = all(facts.get(k) is True for k in step["complete_when"])
        ready = all(result[k]["state"] in {"completed", "not-applicable"} for k in step.get("requires", []))
        result[step["id"]] = {"id": step["id"], "label": step["label"], "state":
            "needs-decision" if applies is None else "not-applicable" if not applies else "completed" if complete else "available" if ready else "pending",
            "conditions": step.get("conditions", []), "actions": step.get("actions", []), "ready": ready}
    return list(result.values())


def process_requirements(policy, action, facts, flags=None):
    needed = set()
    configured = {step["id"]: step for step in policy["steps"]}
    for step in steps_state(policy, facts, flags):
        if action not in step["actions"] or step["state"] == "not-applicable": continue
        needed.update(configured[step["id"]].get("conditions", []))
        if step["state"] == "needs-decision" or not step["ready"]: needed.add("process:" + step["id"])
    return needed


def require_process(policy, action, facts, flags=None):
    missing = [rule for rule in sorted(process_requirements(policy, action, facts, flags)) if facts.get(rule) is not True]
    if missing: raise ContractError("Antes de " + action + ", complete el proceso configurado: " + ", ".join(missing))


def member(model, actor, permission, policy=None):
    if not actor: raise ContractError("Identifique al operador de esta sesión antes de atribuir actuaciones")
    person = model.get(actor, "member")
    if person.retired or not active_period(person.data) or not person.data.get("active", True):
        raise ContractError("El miembro o su función ya no están activos")
    roles = set(person.data.get("roles", []))
    allowed = (policy or policy_for(model)).data.get("permissions", PERMISSIONS)[permission]
    current = policy_for(model).data["permissions"][permission]
    if not roles.intersection(allowed) or not roles.intersection(current):
        raise ContractError("La función vigente no autoriza: " + permission)
    return person


def policy_for(model, request=None):
    current = model.get(model.project.data["policy"], "policy")
    if request:
        e = model.get(request) if isinstance(request, str) else request
        if e.kind == "task": e = model.get(e.data["request"], "request")
        selected = model.at(e.data["policy"], e.data["policy_digest"])
    else: selected = current
    validate_policy(selected.data)
    return selected


def operator(model, actor, permission, policy=None):
    policy = policy or policy_for(model)
    person = member(model, actor, permission, policy)
    # Identity claims are deliberately not promoted to authentication by a JSON field.
    assurance = next((p.data["identity"] for p in (policy, policy_for(model)) if p.data["identity"] != "declared"), "declared")
    if assurance != "declared":
        raise ContractError("El proyecto exige identidad " + assurance + "; aporte un mecanismo de comprobación admitido antes de operar")
    return {"member": person.uid, "name": person.meta["title"], "member_source": person.source(), "roles": person.data["roles"],
            "assurance": "declared", "source": "explicit-session-declaration", "observed_at": now()}
