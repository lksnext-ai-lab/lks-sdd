"""Read-only, source-backed decision views. Formatting never grants authority."""
import copy
import html
import re
from pathlib import Path

from v3_contract import ContractError, load, fingerprint, sha, read_bytes, EVENTS
from v3_decision_profiles import VERSION, PROFILES, HISTORICAL, INFORMATION, profiles, instruction_refs

LABELS = {
    "objective": "Objetivo", "included": "Incluido", "excluded": "Excluido", "behavior": "Comportamiento",
    "solution": "Solución", "impact": "Impacto", "acceptance": "Criterios de aceptación", "unresolved": "Pendientes",
    "name": "Nombre", "actor_name": "Persona responsable", "profile": "Forma de trabajo", "process": "Forma de trabajo",
    "target": "Destino", "lifecycle": "Ciclo de vida", "members": "Personas", "roles": "Responsabilidades",
    "controls": "Controles", "collaboration": "Revisiones acordadas", "coordination": "Responsables de la petición",
    "owner": "Responsable", "scope": "Alcance", "tests": "Pruebas", "dependencies": "Dependencias",
    "recipient": "Destinatario", "reason": "Motivo", "expected": "Resultado esperado", "observed": "Resultado observado",
    "artifact": "Evidencia", "outcome": "Resultado", "source": "Procedencia", "explanation": "Explicación",
    "classification": "Tratamiento", "effect": "Consecuencias", "expires_at": "Vigencia hasta", "rule": "Condición",
    "observations": "Observaciones", "confirmed_intent": "Intención confirmada", "inspection": "Inspección",
    "purpose": "Finalidad", "alternatives": "Alternativas", "recommendation": "Recomendación",
    "screens": "Pantallas y estados", "assets": "Imágenes", "selection_scope": "Alcance de la selección",
    "content": "Contenido", "destination": "Destino", "audience": "Destinatarios", "action": "Actuación",
    "pending": "Pendientes", "constraints": "Restricciones", "interfaces": "Interfaces", "technology": "Tecnología",
    "current": "Situación actual", "change": "Cambio propuesto", "contracts": "Contratos e interfaces",
    "data": "Datos", "errors": "Errores y seguridad", "verification": "Comprobación", "status": "Estado",
    "responsibility": "Responsabilidad", "interactions": "Interacciones", "evidence": "Fuentes",
    "result": "Resultado", "availability": "Disponibilidad", "mode": "Uso acordado", "permissions": "Permisos",
    "proposal_review_required": "Revisión de propuesta", "task_review_required": "Revisión del encargo",
    "responsible": "Responsable", "integration_validator": "Revisión técnica", "functional_validator": "Validación funcional",
    "reviewers": "Revisores", "required": "Obligatorio", "domains": "Especialidades", "defaults": "Configuración común",
    "member": "Persona", "active": "Activo", "type": "Tipo", "paths": "Fuentes inspeccionadas",
    "treatment": "Tratamiento", "blocking": "Impide continuar", "critical": "Decisión crítica",
    "limits": "Límites", "recovery": "Recuperación", "changes": "Cambios", "preserved": "Información conservada",
    "part": "Parte de la propuesta", "components": "Componentes", "sonar": "Análisis de calidad y seguridad",
    "dependency-check": "Revisión de dependencias", "independent_review": "Revisión por otra persona",
    "acceptance_order": "Momento de la aceptación", "executor": "Medio de comprobación",
    "timeout_seconds": "Tiempo máximo en segundos", "max_retries": "Reintentos máximos",
    "phase": "Momento de comprobación", "key": "Referencia de la persona", "state": "Estado",
    "integration": "Revisión del conjunto", "coverage": "Cobertura", "tool": "Herramienta",
    "report": "Informe", "pr_url": "Revisión de los cambios", "revokes": "Sustituye a",
    "nature": "Naturaleza de la observación", "intent": "Intención", "text": "Descripción",
    "flags": "Condiciones específicas", "operational_limit": "Límite de operación",
    "identity": "Comprobación de identidad", "steps": "Secuencia de trabajo", "label": "Etapa",
    "requires": "Requisitos previos", "conditions": "Condiciones", "complete_when": "Se completa cuando",
    "actions": "Acciones permitidas", "offline_actions": "Trabajo sin conexión",
    "govern": "Modificar reglas del proyecto", "define": "Definir cambios", "approve": "Validar contenido",
    "plan": "Planificar", "authorize": "Autorizar ejecución", "implement": "Implementar",
    "verify": "Comprobar", "integrate": "Integrar", "exception": "Autorizar excepciones", "assign": "Asignar trabajo",
}
PRIVATE = set("presentation presented statement request tasks task plan units requests items runtime_bundle packet_directory refresh _model previous offer decision correction problem comment uid id revision basis descriptor policy_digest recorded_at decided_at review_tasks review accept_result operator invocation".split())
PRIVATE |= {"observed_assets", "method", "pin_runtime", "sources", "task_bases", "subject", "git", "candidate_snapshot", "policy", "authorization", "dispositions", "exceptions", "receipt", "comparison", "evidence_before", "artifact_sha256", "basis_digest", "subject_digest", "config_digest", "analysis_id", "previous_state", "intervention"}
PRIVATE |= set("base branch head refs observed_at refresh_error unborn proposal_units proposal_basis original_state files_ref document_inventory coordination_digest identity_history recorded_by".split())
PRIVATE |= {"sha256", "bytes", "executable_sha256", "arguments_digest", "format", "schema_version"}
WORDS = dict(zip(
    "proposed observed joint functional technical individual-brief team-evolution team-brief not-used required optional available unavailable backlog in-progress implemented verified closed closed-with-reservations passed failed not-run automated human-observation existing-report owner specifier developer reviewer integrator evolution new before-integration after-integration paused cancelled".split(),
    ["Propuesto", "Observado", "Funcional y técnica", "Funcional", "Técnica", "Trabajo individual", "Evolución en equipo", "Trabajo en equipo", "No se utilizará", "Obligatorio", "Opcional", "Disponible", "No disponible", "Pendiente de iniciar", "En curso", "Implementado", "Verificado", "Cerrado", "Cerrado con reservas", "Superada", "Fallida", "Sin ejecutar", "Prueba automatizada", "Observación humana", "Informe existente", "Responsable del proyecto", "Definición", "Desarrollo", "Revisión", "Integración", "Evolución del sistema", "Proyecto nuevo", "Antes de integrar", "Después de integrar", "En pausa", "Cancelado"]))
WORDS.update({"coordinated-team": "Equipo coordinado", "fact": "Hecho observado", "inference": "Inferencia pendiente de confirmar", "pending": "Pendiente", "partial": "Parcial", "unconfirmed": "Sin confirmar", "existing-command": "Comprobación existente", "$owner": "Responsable declarado del proyecto"})
WORDS.update({"incorporated": "Incorporar la observación", "dismissed": "Descartar la observación con justificación", "defect": "Corregir un incumplimiento del acuerdo", "agreement-change": "Modificar el acuerdo", "new-request": "Definir una nueva petición", "external": "Resolver fuera del alcance de desarrollo", "integral-review": "Revisión conjunta de la propuesta", "close-proposal": "Cerrar la validación de la propuesta", "proposal": "Especificación", "execution": "Ejecución", "plan": "Plan", "technology": "Decisión tecnológica"})
WORDS.update({"declared": "Identidad declarada", "authenticated": "Identidad autenticada", "independent-review": "Revisión independiente", "maintenance": "Mantenimiento", "proposal-approved": "Especificación validada", "plan-approved": "Plan validado", "authorized": "Ejecución autorizada", "assigned": "Responsable asignado", "quality": "Controles de calidad satisfechos", "integrated": "Conjunto integrado", "accepted": "Resultado aceptado", "query": "Consultar", "approve-proposal": "Validar especificaciones", "authorize-plan": "Aprobar el plan y autorizar su ejecución", "start": "Iniciar", "resume": "Reanudar", "implement": "Implementar", "verify": "Comprobar", "close": "Cerrar", "integrate": "Integrar", "accept": "Aceptar el resultado"})
TECH_FIELDS = ("name", "responsibility", "current", "change", "contracts", "data", "errors", "verification", "status")


def safe(text):
    """Literal source prose cannot create headings, HTML or executable links."""
    text = html.escape(str(text), quote=False)
    text = re.sub(r"([\\`*_{}\[\]<>#|!])", r"\\\1", text)
    return "\n".join(line if not re.match(r"^\s*(?:[-+>]|\d+[.)])\s", line) else "\\" + line for line in text.splitlines())


def title(value):
    return safe(" ".join(str(value).split()))


def human(value, model=None):
    if isinstance(value, str) and model:
        try: return model.get(value).meta["title"]
        except ContractError: pass
    if isinstance(value, bool): return "Sí" if value else "No"
    if value is None: return "No indicado"
    if isinstance(value, str): return WORDS.get(value, value)
    return value


def text(value, model=None):
    if isinstance(value, dict):
        rows = []
        for key, entry in value.items():
            if key == "context_scopes" and isinstance(entry, dict):
                declarations = []
                for scope in entry.get("sources", []):
                    if not isinstance(scope, dict): continue
                    applies = "Todo el trabajo del proyecto" if scope.get("global") else text(scope.get("units", []), model)
                    declarations.append("**Documento:** " + safe(scope.get("path", "Fuente pendiente")) +
                                        "\n\n**Aplica a:** " + applies + "\n\n**Motivo:** " + safe(scope.get("reason", "Pendiente de justificar")))
                rows.append("**Alcance documental propuesto**\n\n" + ("\n\n".join(declarations) or "Sin declaraciones; la prosa permanece incluida."))
                continue
            if key == "uid" and model:
                rows.append("**Trabajo del que depende:** " + safe(human(entry, model)))
                continue
            if key in PRIVATE: continue
            label = LABELS.get(key, key.replace("_", " "))
            rows.append("**" + title(label) + ":** " + text(entry, model))
        return "\n\n".join(rows) or "No se ha concretado el contenido."
    if isinstance(value, (list, tuple)):
        return "\n".join("- " + text(v, model).replace("\n", "\n  ") for v in value) or "Ninguno declarado."
    return safe(human(value, model))


def normalize(data):
    value = copy.deepcopy({k: v for k, v in (data or {}).items() if k not in {"presented", "presentation", "statement", "_model", "packet_directory", "refresh", "usage_context"}})
    aliases = {"request_id": "request", "task_id": "task", "plan_uid": "plan", "identifiers": "units", "decision_id": "decision", "correction_id": "correction", "problem_id": "problem", "process": "profile"}
    for old, new in aliases.items():
        if old in value: value[new] = value.pop(old)
    # Optional defaults do not make a distinct decision; the exact non-default
    # choices (including recipient, scope and destination) remain in the basis.
    def portable(v):
        if isinstance(v, Path): return str(v.resolve())
        if isinstance(v, dict): return {k: portable(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)): return [portable(x) for x in v]
        return v
    return portable({k: v for k, v in value.items() if v is not None})


def roots_for(model, data):
    keys = []
    for name in ("request", "task", "plan", "decision", "problem", "correction", "comment", "previous", "offer", "analysis"):
        if data.get(name): keys.append(data[name])
    for name in ("units", "tasks", "requests", "review_tasks", "requirements"):
        keys.extend(data.get(name, []))
    return list(dict.fromkeys(model.get(k).uid for k in keys))


def _historical_task(model, task, cache):
    """Only recoverable migration lineage permits a task to be shown as history."""
    continuation = task.data.get("continuation")
    if continuation not in {"historical", "reconciliation-required"}: return None
    if task.uid in cache: return cache[task.uid]
    try:
        legacy = task.data["legacy"]
        if legacy["schema"] != "2.0": raise ContractError("Formato de origen no soportado")
        migration = model.get(legacy["migration"], "migration")
        if migration.data["source"].get("format") != legacy["schema"] or migration.data["source"].get("method") != legacy["method"]:
            raise ContractError("El formato o método no coinciden con la migración")
        if migration.data["mapping"].get(legacy["id"]) != task.uid:
            raise ContractError("La migración no identifica esta tarea")
        inventory_key = ("inventory", migration.uid)
        if inventory_key not in cache:
            inventory = migration.data.get("inventory")
            support = {}
            if "inventory_ref" in migration.data:
                import json
                from content_store import read_object, object_path
                ref = migration.data["inventory_ref"]
                inventory = json.loads(read_object(model.root, ref))["entries"]
                support[object_path(ref)] = ref["sha256"]
            entries = {r["path"]: r for r in inventory}
            hashes = {path: row["sha256"] for path, row in entries.items()}
            if len(entries) != len(inventory) or fingerprint(hashes) != migration.data["source"]["snapshot"]:
                raise ContractError("El inventario no coincide con el origen")
            cache[inventory_key] = (entries, support)
        inventory, support = cache[inventory_key]
        original = inventory.get(legacy["path"])
        if not original or any(original[k] != legacy[v] for k, v in
                                   (("original", "original"), ("sha256", "source_sha256"))):
            raise ContractError("El original no coincide con el inventario")
        path = legacy["original"]
        original_key = ("original", path)
        if original_key not in cache:
            from v2_contract import parse_document
            raw = read_bytes(model.root, path, limit=64*1024*1024)
            literal = raw.decode("utf-8")
            cache[original_key] = (sha(raw), len(raw), literal, parse_document(literal, path)[0])
        digest, size, literal, originals = cache[original_key]
        if digest != legacy["source_sha256"]: raise ContractError("Hash del original modificado")
        originals = [e for e in originals if e.id == legacy["id"] and e.meta["uid"] == task.uid and e.kind == "task"]
        if len(originals) != 1 or originals[0].meta["state"] != legacy["state"]:
            raise ContractError("La identidad o el estado no coinciden con el original")
        expected = "historical" if legacy["state"] in {"done", "completed", "cancelled", "done-with-reservations"} else "reconciliation-required"
        if continuation != expected: raise ContractError("Continuidad contradictoria con el original")
        from document_state import LINK, dependencies
        support = dict(support)
        if LINK.fullmatch(path): support.update(dependencies(model.root, path))
        result = (migration, {"path": path, "sha256": digest, "bytes": size,
                              "text": literal, "reason": "Original verificable de la tarea migrada"}, support)
        cache[task.uid] = result
        return result
    except (ContractError, KeyError, TypeError, ValueError, OSError, AttributeError) as exc:
        raise ContractError("Procedencia histórica no verificable para " + task.id + ": " + str(exc)) from exc


def _historical_text(value):
    """Historical identifiers and technical data stay literal, with no current aliases."""
    if isinstance(value, dict):
        return "\n\n".join("**" + title(LABELS.get(k, k.replace("_", " "))) + ":** " +
                           _historical_text(v) for k, v in value.items()) or "Ninguno declarado."
    if isinstance(value, (list, tuple)):
        return "\n".join("- " + _historical_text(v).replace("\n", "\n  ") for v in value) or "Ninguno declarado."
    return safe(value)


def collect(model, roots, selected=()):
    """One applicability closure plus necessary continuity and recoverable evidence."""
    from v3_context import select, TEXT_SUFFIXES, EDGE
    historical = {}; proof_cache = {}
    for key in roots:
        task = model.get(key)
        if task.kind == "task" and _historical_task(model, task, proof_cache): historical[key] = True
    # Detached cancelled history is not an executable work root. Keep its full
    # applicability closure by selecting its references and restoring its source.
    normative = []; detached = set()
    def work_root(key):
        obj = model.get(key)
        if obj.kind in EVENTS | {"member", "legacy"}: return
        if obj.retired and obj.kind == "task" and _historical_task(model, obj, proof_cache):
            if obj.uid in detached: return
            detached.add(obj.uid); historical[obj.uid] = True
            for rel in EDGE:
                for child in obj.relations.get(rel, []): work_root(child)
            for dep in obj.data.get("dependencies", []): work_root(dep["uid"])
            if obj.data.get("request"): work_root(obj.data["request"])
        else: normative.append(obj.uid)
    for key in roots: work_root(key)
    for key in roots:
        obj = model.get(key)
        if obj.data.get("request"): normative.append(obj.data["request"])
        if obj.data.get("task"): normative.append(obj.data["task"])
        if obj.kind in EVENTS:
            normative += [k for k in obj.relations.get("sources", []) if model.get(k).kind not in EVENTS]
    if not normative:
        normative = [model.project.uid]
    # Results are decided for the whole current request. Its task membership is
    # inverse (task.data.request), not a relation on request; do not omit it.
    request_roots = {model.get(k).uid for k in normative if model.get(k).kind == "request"}
    if any(p in selected for p in ("verification", "integration", "acceptance", "correction", "continuity")):
        normative += [t.uid for t in model.by_kind("task") if not t.retired and t.data.get("request") in request_roots]
    packet = select(model, list(dict.fromkeys(normative)), "decision-view")
    sources = packet["sources"]
    seen = {s["key"] for s in sources}
    selected_keys = set(seen)
    # Event-specific evidence, comments, offers and reservations have content too.
    related = set(roots) | detached | {s["key"] for s in sources}
    requests = {model.get(k).data.get("request") for k in roots}
    requests |= {k for k in roots if model.get(k).kind == "request"}
    recent = {}
    for e in model.by_kind("checkpoint"):
        group = (e.data.get("task"), e.data.get("request"))
        rank = (e.data.get("recorded_at", ""), e.uid)
        if group not in recent or rank > recent[group][0]: recent[group] = (rank, e.uid)
    omitted = 0
    for e in model.elements.values():
        from v3_usage import diagnostic
        if diagnostic(e): continue
        if e.uid in set(roots) | detached or (e.kind in EVENTS and (e.data.get("request") in requests - {None} or e.data.get("task") in related or set(e.data.get("tasks", [])) & related)):
            simple = (e.kind == "checkpoint" and e.data.get("classification") == "progress" and e.meta.get("nature") == "fact"
                      and not e.data.get("pending") and not e.data.get("analysis") and not e.data.get("critical")
                      and e.data.get("outcome") in (None, "passed"))
            if e.kind == "checkpoint" and e.uid not in roots and simple:
                group = (e.data.get("task"), e.data.get("request"))
                if e.uid != recent[group][1]:
                    omitted += 1
                    continue
            if e.uid not in seen:
                sources.append({"key": e.uid, "source": e.source(), "meta": e.meta, "text": e.body, "reason": "Evidencia o decisión del alcance"})
                seen.add(e.uid)
    packet["historical_tasks"] = historical
    packet["historical_source_files"] = {}
    asset_paths = {a["path"] for a in packet["attachments"]}
    for row in list(sources):
        if row.get("meta", {}).get("kind") != "task": continue
        task = model.get(row["key"])
        proof = _historical_task(model, task, proof_cache)
        if not proof: continue
        historical[task.uid] = True
        migration, original, support = proof
        packet["historical_source_files"].update(support)
        if migration.uid not in seen:
            sources.append({"key": migration.uid, "source": migration.source(), "meta": migration.meta,
                            "text": migration.body, "reason": "Procedencia verificable de la tarea migrada"})
            seen.add(migration.uid)
        if original["path"] not in asset_paths:
            packet["attachments"].append(original); asset_paths.add(original["path"])
    # A directly consulted cancelled task was added after the normal work closure;
    # recover its linked attachments under the same observation rules too.
    from v3_context import linked_assets
    extra = [s for s in sources if s["key"] in historical and s["key"] not in selected_keys]
    packet["attachments"].extend(linked_assets(model, extra, included_paths=asset_paths | {s["source"]["path"] for s in sources}))
    asset_paths.update(a["path"] for a in packet["attachments"])
    for row in sources:
        if row.get("meta", {}).get("kind") not in {"evidence", "problem", "analysis"}: continue
        path = row["meta"]["data"].get("artifact") or row["meta"]["data"].get("report_path")
        if not isinstance(path, str) or path in asset_paths: continue
        raw = read_bytes(model.root, path)
        asset = {"path": path, "sha256": sha(raw), "bytes": len(raw), "reason": "Evidencia recuperable del resultado"}
        if Path(path).suffix.lower() in TEXT_SUFFIXES:
            asset["text"] = raw.decode("utf-8")
        else: asset["requires_observation"] = True
        packet["attachments"].append(asset); asset_paths.add(path)
    packet["history"] = {"omitted_checkpoints": omitted, "query": {"action": "trace", "uid": normative[0]}}
    return packet


def _covered(model, event, data, roots):
    """Reuse the existing predicates, never infer authority from presentation."""
    if not model: return False
    try:
        from v3_approval import approved, task_authority
        from v31_review import closure_valid, review_status, task_reviewed
        from v3_workflow import plan_for, request_facts
        if event == "approve": return approved(model, data.get("units", []), data.get("purpose"))["valid"]
        if event == "close-proposal": return closure_valid(model, model.get(data["request"]))
        if event == "review-proposal": return data.get("actor") in review_status(model, model.get(data["request"]))["conformities"]
        if event == "review-task": return bool(data.get("tasks")) and all(task_reviewed(model, model.get(k), data.get("actor")) for k in data["tasks"])
        if event == "authorize-plan":
            plan = model.get(data["plan"])
            tasks = [model.get(k) for k in plan.relations.get("tasks", [])]
            return bool(tasks) and all(task_authority(model, t, plan, "execution")["valid"] for t in tasks) and all(task_reviewed(model, model.get(k), data.get("actor")) for k in data.get("review_tasks", []))
        if event == "accept": return request_facts(model, model.get(data["request"]))["accepted"]
    except (ContractError, KeyError): pass
    return False


def _technical(solution, issues):
    if not isinstance(solution, dict) or not isinstance(solution.get("components"), list) or not solution["components"]:
        issues.append("Concrete la solución técnica por componentes, interfaces y comprobaciones.")
        return text(solution) if solution else "Pendiente de concretar."
    blocks = []
    for component in solution["components"]:
        if not isinstance(component, dict):
            issues.append("Hay un componente sin contenido estructurado."); continue
        missing = [k for k in TECH_FIELDS if not component.get(k)]
        if missing: issues.append("Complete " + str(component.get("name", "el componente")) + ": " + ", ".join(LABELS.get(k, k) for k in missing))
        if component.get("status") not in {"proposed", "observed", "propuesta", "observado"}:
            issues.append("Indique si el componente es observado o propuesto.")
        if component.get("status") in {"observed", "observado"} and not component.get("evidence"):
            issues.append("Aporte la fuente de la arquitectura observada.")
        ordered = {k: component[k] for k in TECH_FIELDS if k != "name" and k in component}
        ordered.update({k: v for k, v in component.items() if k not in TECH_FIELDS})
        blocks.append("### " + title(component.get("name", "Componente pendiente")) + "\n\n" + text(ordered))
    if not solution.get("interactions"): issues.append("Explique la interacción entre componentes o por qué el cambio es aislado.")
    blocks.append("### Interacción del conjunto\n\n" + text(solution.get("interactions", "Pendiente de concretar.")))
    additional = {k: v for k, v in solution.items() if k not in {"components", "interactions"}}
    if additional: blocks.append("### Condiciones técnicas adicionales\n\n" + text(additional))
    return "\n\n".join(blocks)


def _specification(model, roots, data, issues):
    units = data.get("units")
    if units is None:
        units = [k for key in roots if model.get(key).kind == "request" for k in model.get(key).relations.get("proposal", [])]
    if not units: issues.append("Prepare la propuesta concreta que se quiere revisar.")
    blocks = [[] for _ in range(7)]
    for key in units or []:
        e = model.get(key)
        if e.kind not in {"proposal", "feature"}: raise ContractError("Seleccione unidades de propuesta")
        d = e.data
        fields = ["objective", "included", "excluded", "impact", "acceptance"]
        if d.get("part") in {"joint", "functional"}: fields.append("behavior")
        if d.get("part") not in {"joint", "functional", "technical"}: issues.append("Declare la parte funcional, técnica o conjunta de la propuesta.")
        for field in fields:
            if field not in d or (field != "excluded" and not d[field]): issues.append("Complete " + LABELS[field].lower() + " de " + e.meta["title"])
        values = [text(d.get("objective", "Pendiente")), "**Incluido:**\n" + text(d.get("included", [])) + "\n\n**Excluido:**\n" + text(d.get("excluded", [])),
                  text(d.get("behavior", "La parte funcional se revisa por separado.")),
                  _technical(d.get("solution"), issues) if d.get("part") in {"technical", "joint"} else "La solución técnica se revisa por separado.",
                  text(d.get("impact", "Pendiente")), text(d.get("acceptance", [])), text(d.get("unresolved", []))]
        for index, value in enumerate(values):
            prefix = ("**" + title(e.meta["title"]) + "**\n\n") if len(units) > 1 else ""
            blocks[index].append(prefix + value)
        if d.get("unresolved"): issues.append("Resuelva las decisiones críticas indicadas para esta porción.")
    return ["\n\n".join(b) or "Pendiente de concretar." for b in blocks]


def _sources_text(model, packet, primary, specification=False):
    blocks = []
    for row in packet.get("sources", []):
        meta = row.get("meta", {}); kind = meta.get("kind")
        if kind in {"member", "project", "policy"} or kind in EVENTS: continue
        label = meta.get("title", "Condición adicional del proyecto")
        if row["key"] in packet.get("historical_tasks", {}):
            if row["key"] in primary and not specification: continue  # Placed literally by the primary adapter.
            blocks.append("**" + title(label) + "**\n\nAntecedente migrado; no confiere autoridad actual.\n\n" +
                          safe(row["text"]) + "\n\n" + _historical_text(meta))
            continue
        # Body is always literal; structured normative data is not silently dropped.
        content = safe(row["text"])
        d = {k: v for k, v in meta.get("data", {}).items() if k not in PRIVATE}
        if kind in {"task", "plan", "request"}:
            # These bodies and typed fields are placed by the adapter. Preserve
            # any additional normative condition instead of silently dropping it.
            placed = {"owner", "scope", "tests", "dependencies", "acceptance", "objective", "coordination"}
            d = {k: v for k, v in d.items() if k not in placed}
            if kind == "request": d = {k: v for k, v in d.items() if k not in {"branches", "target"}}
            content = ""
            if (specification and kind in {"request", "plan", "task"}) or (kind in {"request", "plan"} and row["key"] not in primary):
                content = safe(row["text"])
        if kind == "proposal" and specification:
            d = {k: v for k, v in d.items() if k not in {"part", "objective", "included", "excluded", "behavior", "solution", "impact", "acceptance", "unresolved"}}
        if d: content += "\n\n" + text(d, model)
        if content.strip(): blocks.append("**" + title(label) + "**\n\n" + content)
    for asset in packet.get("attachments", []):
        if "text" in asset: blocks.append("**Documento relacionado: " + title(asset["path"]) + "**\n\n" + safe(asset["text"]))
        else:
            from urllib.parse import quote
            path = quote((model.root / asset["path"]).resolve().as_posix(), safe="/:.")
            link = "[Abrir adjunto](<" + path + ">)"
            if Path(asset["path"]).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                link = "![Imagen que se somete a revisión](<" + path + ">)"
            blocks.append("**Adjunto que debe observarse:** " + title(asset["path"]) + "\n\n" + link)
    return "\n\n".join(blocks)


def _generic(model, selected, data, packet, roots, issues):
    """Place typed project facts in relevant sections, keeping every distinct fact."""
    rows = []
    if model:
        for key in roots:
            e = model.get(key)
            if key in packet.get("historical_tasks", {}):
                rows.append("**" + title(e.meta["title"]) + "**\n\nAntecedente migrado; no confiere autoridad actual.\n\n" +
                            safe(e.body) + "\n\n" + _historical_text(e.meta))
            elif e.kind not in {"task"} | EVENTS:
                rows.append("**" + title(e.meta["title"]) + "**\n\n" + safe(e.body))
    public = {k: v for k, v in data.items() if k not in PRIVATE and k not in {"actor", "trusted_root"}}
    if data.get("items"):
        for item in data["items"]:
            meta = item.get("meta", item)
            rows.append("**Cambio propuesto: " + title(meta.get("title", "Configuración")) + "**\n\n" + safe(item.get("body", "")) + "\n\n" + text(meta.get("data", {}), model))
    # These fields are proposals, not fake approvals or inferred observations.
    if not rows and not public and not roots: issues.append("Falta el contenido concreto de esta decisión.")
    content = "\n\n".join(rows)
    titles = list(dict.fromkeys(h for p in selected for h in PROFILES[p][1].split("|")))
    buckets = {h: [] for h in titles}
    # Distribute fields by meaning. Full primary source prose remains in the first
    # section; every other section supplies relevant facts, not a boilerplate claim.
    if content: buckets[titles[0]].append(content)
    field_sets = {
        "configuration": [("name",), ("profile", "lifecycle", "collaboration"), ("actor_name", "members", "coordination"), ("controls",), ("changes",), ("impact", "pending")],
        "adoption": [("paths", "inspection"), ("observations",), ("confirmed_intent",), ("pending",), ("changes",), ("unresolved",)],
        "migration": [("target",), ("changes", "collaboration"), ("preserved",), ("scope",), ("recovery",), ("pending",)],
        "planning": [("objective",), ("owner", "members"), ("dependencies",), ("tests", "acceptance"), ("scope", "target", "limits"), ("pending",)],
        "assignment": [("objective",), ("scope", "owner", "recipient"), ("observed",), ("dependencies", "interfaces"), ("tests", "acceptance"), ("pending",)],
        "verification": [("expected",), ("tests", "acceptance"), ("artifact", "source", "observed"), ("outcome", "pending"), ("classification", "effect")],
        "integration": [("expected",), ("interfaces", "scope"), ("tests", "artifact"), ("pending",), ("effect",), ("unresolved",)],
        "acceptance": [("expected",), ("artifact",), ("acceptance", "tests"), ("pending",), ("scope", "effect"), ("unresolved",)],
        "correction": [("expected",), ("observed",), ("classification", "treatment"), ("scope", "changes"), ("tests", "acceptance", "artifact"), ("pending",)],
        "exception": [("rule",), ("reason", "alternatives"), ("scope", "action"), ("effect",), ("expires_at",), ("effect",)],
        "continuity": [("current",), ("reason",), ("scope",), ("effect",), ("pending",)],
        "recovery": [("current",), ("changes",), ("preserved",), ("pending",), ("tests",), ("unresolved",)],
        "delivery": [("content",), ("destination", "audience"), ("changes", "action"), ("limits",), ("scope",), ("pending",)],
        "technology": [("objective",), ("alternatives",), ("recommendation",), ("interfaces", "solution"), ("impact", "tests"), ("pending",)],
        "visual": [("screens",), ("assets",), ("alternatives", "recommendation"), ("selection_scope",), ("pending",)],
        "clarification": [("pending", "objective", "actor_name"), ("alternatives", "effect")],
        "information": [("result",), ("pending",)],
    }
    facts = [(None, data)]
    tasks = []
    if model:
        related = set(roots)
        for key in roots:
            related.update(model.get(key).relations.get("tasks", []))
        if any(p in selected for p in ("verification", "integration", "acceptance", "correction", "continuity")):
            related.update(row["key"] for row in packet.get("sources", []) if row.get("meta", {}).get("kind") == "task")
        for k in sorted(related):
            e = model.get(k)
            if k in packet.get("historical_tasks", {}):
                if "information" in selected:
                    buckets["Impedimentos y siguiente paso"].append("**" + title(e.meta["title"]) + "**\n\n" +
                        _historical_text({field: e.data[field] for field in ("continuation", "pending", "unresolved") if field in e.data}))
                continue
            if e.kind == "task": tasks.append(e)
            if e.kind not in {"request", "project", "policy"} and e.kind not in EVENTS:
                values = e.data
                if e.kind == "task":
                    from v3_team import owners
                    values = {**e.data, "owner": owners(model, e)}
                facts.append((e.meta["title"], values))
        if "configuration" in selected:
            from v3_policy import policy_for
            current = policy_for(model).data
            facts.append(("Configuración vigente; solo se modifica lo indicado en la propuesta", current))
            facts.append((None, {"actor_name": human(data.get("actor"), model)}))
            buckets[PROFILES["configuration"][1].split("|")[4]].append("**Configuración actual**\n\n" + text({k: current[k] for k in ("profile", "controls", "collaboration", "independent_review", "acceptance_order") if k in current}, model))
        if "assignment" in selected:
            from v3_workflow import state
            for item in tasks:
                buckets["Estado recibido y entregables"].append("**" + title(item.meta["title"]) + ":** " + text(state(model, item)))
        for item in data.get("items", []):
            meta = item.get("meta", item)
            facts.append(("Configuración propuesta: " + meta.get("title", "Cambio"), meta.get("data", {})))
        if any(p in selected for p in ("continuity", "information")):
            for row in packet.get("sources", []):
                meta = row.get("meta", {}); d = meta.get("data", {})
                if meta.get("kind") not in {"checkpoint", "problem"}: continue
                content = {"explanation": row["text"], "outcome": d["outcome"]} if d.get("outcome") is not None else row["text"]
                facts.append((meta["title"], {"current": content, "result": content, "pending": d.get("pending", [])}))
        if any(p in selected for p in ("verification", "integration", "acceptance", "correction")):
            for row in packet.get("sources", []):
                meta = row.get("meta", {}); d = meta.get("data", {})
                if meta.get("kind") not in {"evidence", "problem", "analysis", "exception", "correction"}: continue
                linked = [d["task"]] if d.get("task") else d.get("tasks", [])
                label = " / ".join(str(human(k, model)) for k in linked) or "Resultado del conjunto"
                label += " · " + {"evidence": "Comprobación registrada", "problem": "Desacuerdo registrado", "analysis": "Análisis registrado", "exception": "Excepción registrada", "correction": "Corrección"}[meta["kind"]]
                if d.get("report_path"):
                    d = {**d, "artifact": d["report_path"]}
                facts.append((label, {**d, "explanation": row["text"]}))
                if d.get("evidence_pending"):
                    facts.append((label, {"pending": "El desacuerdo se registró sin archivo de evidencia. Su resolución exige comprobaciones nuevas y recuperables."}))
    for p in selected:
        for heading, fields in zip(PROFILES[p][1].split("|"), field_sets[p]):
            for label, fact in facts:
                found = {k: fact[k] for k in fields if k in fact}
                if found: buckets[heading].append(("**" + title(label) + "**\n\n" if label else "") + text(found, model))
    for task in tasks:
        prefix = "**" + title(task.meta["title"]) + "**\n\n"
        body_heading = "Tareas y responsables" if "planning" in selected else titles[0]
        buckets[body_heading].insert(0, prefix + safe(task.body))
        if "planning" in selected and not task.data.get("dependencies"):
            buckets["Orden y dependencias"].append(prefix + "No tiene dependencias declaradas; puede iniciarse cuando se cumplan sus condiciones de ejecución.")
        if "assignment" in selected and not task.data.get("dependencies"):
            buckets["Contratos y dependencias"].append(prefix + "No tiene dependencias declaradas. Se mantienen las condiciones de las fuentes relacionadas.")
        if "assignment" in selected and "planning" in selected:
            buckets["Resultado esperado"].append(prefix + text({"acceptance": task.data.get("acceptance", [])}, model))
    # A result is comprehensible only when its tasks, tests and recoverable
    # evidence remain associated. Do not flatten different tasks into field bags.
    if model and any(p in selected for p in ("integration", "acceptance", "verification")):
        if not tasks: issues.append("Faltan las tareas concretas cuyo resultado se quiere comprobar.")
        evidence = [r for r in packet.get("sources", []) if r.get("meta", {}).get("kind") in {"evidence", "analysis"}]
        if not evidence: issues.append("Falta evidencia recuperable de las comprobaciones del resultado.")
        for p in selected:
            if p not in {"integration", "acceptance", "verification"}: continue
            hs = PROFILES[p][1].split("|")
            criterion_heading = hs[2] if p == "acceptance" else hs[1] if p == "verification" else hs[2]
            for task in tasks:
                if p == "acceptance" and "integration" in selected:
                    buckets[hs[0]].append("**" + title(task.meta["title"]) + "**\n\n" + text({"acceptance": task.data.get("acceptance", [])}, model))
                criterion = {k: task.data[k] for k in ("acceptance", "tests") if k in task.data}
                block = "**" + title(task.meta["title"]) + "**\n\n" + text(criterion, model)
                buckets[criterion_heading].append(block)
                if p in {"integration", "acceptance"}:
                    buckets[hs[4]].append("**" + title(task.meta["title"]) + "**\n\n" + text({"scope": task.data.get("scope", [])}, model))
            ev_heading = hs[1] if p == "acceptance" else hs[2]
            for label, fact in facts:
                if not fact.get("artifact") and not fact.get("report"): continue
                displayed = {k: fact[k] for k in ("tests", "outcome", "source", "artifact", "report", "explanation") if k in fact}
                buckets[ev_heading].append("**" + title(label or "Comprobación") + "**\n\n" + text(displayed, model))
            from v3_quality import checks
            for task in tasks:
                values = checks(model, task)
                buckets[criterion_heading].append("**Controles de " + title(task.meta["title"]) + "**\n\n" + text({name: {k: value[k] for k in ("mode", "status", "reason") if k in value} for name, value in values.items()}, model))
    if model:
        from v3_policy import active_period
        reservations = []
        for row in packet.get("sources", []):
            meta = row.get("meta", {}); d = meta.get("data", {})
            if meta.get("kind") != "exception": continue
            block = {k: d[k] for k in ("rule", "action", "effect", "expires_at") if k in d}
            block.update(reason=row["text"], status="Vigente según su fecha" if active_period(d) else "Fuera de vigencia")
            reservations.append(text(block, model))
        if reservations:
            target = next((h for h in titles if h in {"Limitaciones y reservas", "Incidencias y reservas", "Riesgos y pendientes", "Pendientes", "Fallos y límites"}), titles[-1])
            buckets[target].append("### Excepciones registradas\n\n" + "\n\n".join(reservations))
    if "planning" in selected and model:
        requests = {t.data.get("request") for t in tasks} - {None}
        for key in requests:
            request = model.get(key)
            branches = request.data.get("branches", [])
            if branches: buckets["Alcance de la ejecución"].append("Ramas de trabajo: " + ", ".join(safe(branch) for branch in branches) + ".")
            if request.data.get("target"): buckets["Alcance de la ejecución"].append("Base de integración: " + safe(request.data["target"]) + ".")
        if not tasks: issues.append("El plan no contiene tareas concretas.")
    if "adoption" in selected:
        observations = data.get("observations", [])
        buckets["Diferencias y desconocidos"].append(text([o for o in observations if isinstance(o, dict) and o.get("nature") != "fact"], model) if any(isinstance(o, dict) and o.get("nature") != "fact" for o in observations) else "La inspección es parcial; no acredita ausencia de funciones fuera de las fuentes revisadas.")
        buckets["Documentación que se incorporará"].append("Se conservarán las fuentes inspeccionadas, las observaciones con su naturaleza y la intención confirmada que figuran arriba.")
    if "configuration" in selected and model:
        affected = [model.get(k) for k in data.get("requests", [])]
        buckets["Impacto y pendientes"].append("Peticiones afectadas: " + (", ".join(title(e.meta["title"]) for e in affected) if affected else "se modifica la configuración general; las peticiones conservan sus acuerdos salvo adopción expresa del cambio") + ".")
    # Data not owned by a specific section remains visible; do not silently discard
    # a configuration limit just because this renderer has no specialized label.
    placed = {key for p in selected for fields in field_sets[p] for key in fields}
    remainder = {k: v for k, v in public.items() if k not in placed and k != "title"}
    if remainder: buckets[titles[0]].append(text(remainder, model))
    empty = {
        "Cambios respecto a la situación actual": "Se propone la configuración inicial del proyecto.",
        "Impacto y pendientes": "No se han declarado condiciones adicionales. Las personas y controles anteriores delimitan el trabajo.",
        "Riesgos y pendientes": "No se han declarado riesgos adicionales. La autorización se limita a las tareas y condiciones mostradas.",
        "Pendientes": "No se han declarado pendientes adicionales para esta decisión.",
        "Decisiones pendientes": "No se han declarado decisiones adicionales.",
        "Limitaciones y reservas": "No se han declarado reservas adicionales en las fuentes revisadas.",
        "Incidencias y reservas": "No se han declarado incidencias adicionales en las fuentes revisadas.",
        "Fallos y límites": "Consulte los resultados y su procedencia; una comprobación registrada solo acredita su alcance.",
        "Pruebas y condiciones de inicio": "El inicio requiere la cobertura y las comprobaciones indicadas para el encargo.",
        "Contratos y dependencias": "Se mantienen los contratos y las condiciones de las fuentes relacionadas.",
        "Comprobaciones y límites": "El permiso se limita al contenido y destino mostrados; no acredita su publicación ni recepción.",
        "Continuación y pendientes": "La continuación conserva las condiciones vigentes y requiere revisar cualquier cambio material.",
        "Tratamiento y siguiente acción": "Revise los resultados y resuelva los fallos antes de decidir el siguiente paso.",
        "Consecuencias": "El cambio afecta únicamente al trabajo y las decisiones identificados. Sus condiciones se volverán a comprobar antes de continuar.",
        "Efecto de la decisión": "La excepción permite solo la actuación declarada durante su vigencia; no convierte la condición pendiente en superada.",
        "Consecuencias y medidas": "La condición indicada queda pendiente y visible. El permiso excepcional se limita a la actuación y vigencia declaradas; las demás condiciones siguen siendo exigibles.",
        "Objetivo": "Aplicar el cambio de personas o reglas descrito, conservando los acuerdos no modificados.",
        "Situación actual": "La situación y el trabajo afectado figuran en las fuentes relacionadas que se muestran en este mensaje.",
    }
    bodies = []
    for h in titles:
        body = "\n\n".join(dict.fromkeys(buckets[h]))
        if not body:
            body = empty.get(h, "Pendiente de concretar: " + h.lower() + ".")
            if h not in empty: issues.append("Concrete " + h.lower() + " antes de decidir.")
        bodies.append(body)
    return titles, bodies


def _requirements(event, data, model, roots, issues):
    required = {
        "init": ("name", "actor_name", "profile", "controls", "target"),
        "configure-collaboration": ("actor", "collaboration"), "governance": ("actor", "items", "reason"),
        "adopt": ("inspection", "observations", "confirmed_intent"),
        "authorize-plan": ("plan", "actor"), "review-task": ("tasks", "actor"),
        "assign": ("task", "recipient", "reason"), "handoff": ("task", "recipient", "scope", "reason"),
        "integrate": ("request", "actor", "trusted_root"), "accept": ("request", "actor"),
        "exception": ("task", "rule", "action", "reason", "expires_at"),
        "review-exception": ("request", "rule", "action", "effect", "expires_at"),
        "revoke": ("decision", "reason"), "define-correction": ("correction", "classification", "acceptance"),
        "resolve-defect": ("problem",), "resolve-comment": ("comment", "treatment"),
        "technology-choice": ("objective", "alternatives", "recommendation", "impact"),
        "visual-choice": ("screens", "assets", "selection_scope"),
        "external-action": ("content", "destination", "action", "scope"), "client-view": ("content", "audience"),
    }.get(event, ())
    for field in required:
        if not data.get(field): issues.append("Falta concretar: " + LABELS.get(field, {"task": "encargo", "tasks": "encargos", "plan": "plan", "actor": "persona que decide", "request": "cambio solicitado", "trusted_root": "base de integración", "items": "cambios propuestos", "decision": "decisión afectada", "problem": "problema", "correction": "corrección", "comment": "observación"}.get(field, field)))
    if event == "migration-preview":
        for field in (("actor", "collaboration", "runtime_bundle") if model else ("actor_name", "profile", "controls", "target", "collaboration", "runtime_bundle")):
            if not data.get(field): issues.append("Complete las personas, configuración y versión de destino de la migración.")
    if model and event in {"authorize-plan", "integrate", "accept", "resolve-defect"}:
        if event in {"integrate", "accept"} and data.get("request") and data.get("actor"):
            if any(t.data.get("request") == model.get(data["request"]).uid and not t.retired
                   and t.data.get("continuation") in {"historical", "reconciliation-required"}
                   for t in model.by_kind("task")):
                issues.append("La petición incluye resultados migrados pendientes de reconciliación y autorización actuales.")
                return
            from v3_workflow import request_facts
            try:
                facts = request_facts(model, model.get(data["request"], "request"))
                for field, label in (("closed", "tareas verificadas y cerradas"), ("quality", "controles de calidad")):
                    if not facts.get(field): issues.append("Falta acreditar " + label + ".")
                from v3_policy import policy_for
                if event == "accept" and policy_for(model, model.get(data["request"])).data["acceptance_order"] == "after-integration" and not facts.get("integrated"):
                    issues.append("La configuración acordada exige integrar este resultado antes de su aceptación funcional.")
                from v31_corrections import unresolved
                if unresolved(model, model.get(data["request"])):
                    issues.append("Hay desacuerdos o correcciones pendientes que deben resolverse antes de validar el resultado.")
            except ContractError as exc: issues.append(str(exc))
        if event == "authorize-plan" and data.get("plan"):
            from v3_approval import plan_coverage
            try: plan_coverage(model, model.get(data["plan"], "plan"))
            except ContractError as exc: issues.append(str(exc))


def operation_facts(root, event, data, model, issues):
    """Read operation-specific facts; never accept a caller's summary as observation."""
    shown = copy.deepcopy(data); extra_basis = {}
    if event == "review-exception":
        shown.setdefault("reason", data.get("effect"))
    if event == "migration-reconcile" and model:
        proposed = data.get("items", data.get("changes", []))
        shown.update(target="Reconciliar el trabajo abierto con la configuración actual del proyecto.",
                     changes=[{"name": i.get("meta", i).get("title", "Cambio propuesto"), "content": i.get("body", ""), "data": i.get("meta", i).get("data", {})} for i in proposed],
                     preserved="Se conservan identidades e historia. Las confirmaciones solo se reutilizan mientras siga vigente el contenido que cubren.",
                     scope=[i.get("meta", i).get("title", "Elemento afectado") for i in proposed],
                     recovery="Se validará la documentación resultante mediante una operación recuperable. Reconciliar no concede nueva autorización de ejecución.")
    if event in {"migration-preview", "migration-diagnose"}:
        from v3_current import diagnose
        diagnostic = diagnose(root, include_inventory=True)
        extra_basis["migration"] = diagnostic
        shown["target"] = "Versión actual: " + str(diagnostic.get("method", "sin identificar")) + "; versión de destino: 3.1.0."
        shown["changes"] = "Se actualizarán la documentación activa, la configuración de revisiones y la versión de herramientas fijada al proyecto en una sola operación."
        shown["preserved"] = "Se conservarán la identidad de los elementos, la historia y los acuerdos anteriores. El trabajo abierto se contrastará con las condiciones actuales antes de ejecutarse."
        tasks = [t for t in model.by_kind("task") if not t.retired] if model else []
        from v3_workflow import state as task_state
        shown["scope"] = [{"name": t.meta["title"], "state": task_state(model, t)} for t in tasks] if model else [{"name": t.get("id", "Tarea de origen"), "state": t.get("state")} for t in diagnostic.get("tasks", [])]
        if not shown["scope"]: shown["scope"] = "No hay tareas activas identificadas en el diagnóstico."
        shown["recovery"] = "Se comprobarán la integridad documental y las herramientas fijadas. La operación conservará un registro recuperable; una reversión preservará el trabajo posterior que entre en conflicto."
        if diagnostic.get("status") not in {"compatible", "current", "needs-migration"}:
            issues.append("No se ha acreditado un origen migrable: " + str(diagnostic.get("cause", diagnostic.get("status"))))
        bundle = data.get("runtime_bundle")
        if bundle:
            path = Path(bundle).resolve()
            if not path.is_dir(): issues.append("No se puede recuperar el paquete de herramientas de destino.")
            else:
                # Target bytes, not only a mutable directory name, bind the choice.
                extra_basis["runtime_target"] = {p.relative_to(path).as_posix(): sha(p.read_bytes()) for p in sorted(path.rglob("*")) if p.is_file()}
    if event in {"recover", "rollback"}:
        from v2_storage import _load_transaction
        try:
            journal, _ = _load_transaction(root, data["authorized_hash"], data.get("receipt"))
            preview = journal["preview"]
            extra_basis["transaction"] = journal
            shown["current"] = "Operación registrada: " + ("revertir los cambios" if event == "rollback" else "completar los cambios interrumpidos") + "."
            shown["changes"] = list(preview.get("after", {}))
            shown["preserved"] = "Se preserva el estado previo registrado y se comprueban los conflictos con ediciones posteriores."
            shown["tests"] = "La operación comprobará las huellas de los archivos y, al completar, la integridad documental y de las herramientas."
            shown["pending"] = "Cualquier conflicto se resolverá conservando el trabajo posterior; el registro no constituye por sí solo permiso para sobrescribirlo."
        except (ContractError, KeyError, OSError, ValueError) as exc:
            issues.append("Falta recuperar el registro de la operación y su estado exacto: " + str(exc))
    if event == "adopt" and isinstance(data.get("inspection"), dict):
        sources = data["inspection"].get("sources", [])
        shown["paths"] = [s.get("path") for s in sources]
        shown["observations"] = [{**observation, "evidence": observation.get("sources", [])} for observation in data.get("observations", [])]
        extra_basis["inspection"] = {s["path"]: sha(read_bytes(root, s["path"])) for s in sources}
        for source in sources:
            if extra_basis["inspection"][source["path"]] != source.get("sha256"):
                issues.append("Ha cambiado una fuente inspeccionada: " + source["path"])
    if model and event == "resolve-comment" and data.get("comment"):
        comment = model.get(data["comment"])
        target = model.get(comment.data["target"])
        shown.update(expected=target.body, observed=comment.body, scope=target.meta["title"],
                     tests="El tratamiento de esta observación no aprueba el resto de la propuesta; se revisará su contenido actualizado antes del cierre.")
    if model and event == "resolve-defect" and data.get("problem"):
        problem = model.get(data["problem"])
        corrections = [e for e in model.by_kind("change") if e.data.get("problem") == problem.uid and not e.retired]
        shown["classification"] = [{"name": c.meta["title"], "classification": c.data.get("classification"), "acceptance": c.data.get("acceptance")} for c in corrections]
        shown["expected"] = problem.data.get("expected"); shown["observed"] = problem.data.get("observed")
    if model and event == "revoke" and data.get("decision"):
        old = model.get(data["decision"])
        shown["current"] = {"purpose": old.data.get("purpose"), "content": old.body}
        keys = old.relations.get("sources", []) or list(old.data.get("descriptor", {}).get("units", {}))
        shown["scope"] = [model.get(k).meta["title"] for k in keys] or [human(old.data.get("task") or old.data.get("request"), model)]
        shown["effect"] = "La decisión dejará de proporcionar cobertura. Se volverán a comprobar las tareas y decisiones que dependan de ella; el trabajo ya realizado se conserva."
    return shown, extra_basis


def decision_view(root, event, data=None, *, model=None):
    data = normalize(data); issues = []; selected = profiles(event, data)
    if "outcome" in data and event not in {"review-proposal", "review-task", "evidence"}:
        raise ContractError("Esta operación no admite outcome; seleccione la acción que realmente corresponda a la decisión")
    refs = instruction_refs(selected, event=event)
    root = Path(root).resolve(); roots = []; packet = {"sources": [], "attachments": []}
    if model is not None and model.root != root:
        raise ContractError("El modelo de evaluación pertenece a otro proyecto")
    from v3_cli import is_v3
    if is_v3(root):
        model = model if model is not None else load(root)
        if model.errors and selected == ["recovery"]:
            issues.append("El estado documental está incompleto; la recuperación debe contrastarse con el paquete conservado.")
            model = None
        else:
            model.require_valid(); roots = roots_for(model, data)
            packet = collect(model, roots, selected)
    elif event not in {"init", "clarify", "identity", "migration-preview", "migration-diagnose", "recover", "rollback", "external-action", "client-view"} | HISTORICAL:
        issues.append("Faltan fuentes válidas del proyecto para esta decisión.")
    if event == "governance" and model:
        # A proposed scope change must show the affected prose even if its old
        # declaration excluded it. Metadata alone cannot justify a new exclusion.
        extra = []
        for item in data.get("items", []):
            meta = item.get("meta", item)
            if meta.get("kind") != "project": continue
            declarations = meta.get("data", {}).get("context_scopes", {})
            if not isinstance(declarations, dict) or not isinstance(declarations.get("sources", []), list):
                issues.append("Declaraciones de prosa inválidas"); continue
            for row in declarations.get("sources", []):
                if not isinstance(row, dict):
                    issues.append("Declaración de prosa inválida"); continue
                path = row.get("path")
                if not isinstance(path, str):
                    issues.append("Fuente de prosa inválida"); continue
                prose = model.prose.get(path)
                if prose is None or sha(prose.encode("utf-8")) != row.get("sha256"):
                    issues.append("La declaración no identifica la prosa vigente: " + str(path)); continue
                if "prose:"+path not in {s["key"] for s in packet["sources"]}:
                    extra.append({"key": "prose:"+path, "source": {"path": path, "sha256": model.hashes[path]},
                                  "reason": "prosa cuyo alcance se propone cambiar", "text": prose})
        from v3_context import linked_assets
        packet["attachments"].extend(linked_assets(model, extra, included_paths=[s["source"]["path"] for s in packet["sources"]] + [a["path"] for a in packet["attachments"]]))
        packet["sources"].extend(extra)
    if event in HISTORICAL: issues.append("Esta operación histórica no está disponible para escritura en el recorrido actual.")
    _requirements(event, data, model, roots, issues)
    shown, operation_basis = operation_facts(root, event, data, model, issues)
    if "visual" in selected or ("delivery" in selected and data.get("assets")):
        for asset in data.get("assets", []):
            path = asset.get("path") if isinstance(asset, dict) else asset
            if not isinstance(path, str):
                issues.append("Indique una ruta local recuperable para cada propuesta visual."); continue
            try:
                raw = read_bytes(root, path)
                packet["attachments"].append({"path": path, "sha256": sha(raw), "bytes": len(raw), "requires_observation": True})
            except (ContractError, OSError): issues.append("No se puede observar la propuesta visual: " + path)
    name = data.get("title") or data.get("name")
    if not name and event == "identity": name = "Confirmar quién solicita el cambio"
    if not name and event == "clarify": name = data.get("objective") or "Resolver la decisión pendiente"
    if model and not name:
        request = next((model.get(k) for k in roots if model.get(k).kind == "request"), None)
        if not request:
            request_key = next((model.get(k).data.get("request") for k in roots if model.get(k).data.get("request")), None)
            request = model.get(request_key) if request_key else None
        name = (request or (model.get(roots[0]) if roots else model.project)).meta["title"]
    if not name: name = "Revisar " + {"configuration": "la configuración del proyecto", "migration": "el cambio de versión", "recovery": "la recuperación", "delivery": "el contenido y su destino"}.get(selected[0], "la decisión pendiente")
    if "specification" in selected and model:
        headings = PROFILES["specification"][1].split("|"); bodies = _specification(model, roots, data, issues)
    else: headings, bodies = _generic(model, selected, shown, packet, roots, issues)
    if model:
        informational_pending = []
        for uncertainty in packet.get("widened", []):
            if uncertainty.get("code") != "conflicting-membership": continue
            message = "Aclare la discrepancia entre petición y pertenencia por relaciones de: " + model.get(uncertainty["uid"]).meta["title"]
            if any(p in selected for p in ("configuration", "migration", "recovery", "continuity", "clarification", "information")):
                informational_pending.append(message)
            else: issues.append(message)
        for row in packet["sources"]:
            meta = row.get("meta", {}); d = meta.get("data", {})
            if row["key"] in packet.get("historical_tasks", {}): continue
            if d.get("critical") and (d.get("unresolved") or meta.get("state") in {"unknown", "draft", "conflict"}):
                message = "Hay una condición crítica pendiente: " + str(meta.get("title", "condición del proyecto"))
                if any(p in selected for p in ("configuration", "migration", "recovery", "continuity", "clarification", "information")) or event in {"resolve-comment", "review-comment", "reject-result", "define-correction"}:
                    informational_pending.append(message)
                else: issues.append(message)
        if informational_pending:
            bodies[-1] = text(informational_pending, model) + "\n\nLa operación mostrada conserva estos pendientes; no autoriza implementar su contenido."
    # Exact code/evidence and target configuration are part of result decisions.
    subject = None
    if model and any(p in selected for p in ("integration", "acceptance", "verification", "correction", "assignment")):
        from v3_git import subject as observe_subject
        scopes = {path for row in packet["sources"] if row.get("meta", {}).get("kind") == "task"
                  and row["key"] not in packet.get("historical_tasks", {}) for path in row["meta"]["data"].get("scope", [])}
        if scopes: subject = observe_subject(root, sorted(scopes))
    assets = packet.get("attachments", [])
    for asset in assets:
        if asset.get("requires_observation"):
            observed = data.get("observed_assets", {})
            if observed.get(asset["path"]) != asset["sha256"]:
                issues.append("Debe observar el adjunto antes de validar: " + asset["path"])
    literal = _sources_text(model, packet, roots, "specification" in selected) if model else ""
    if literal:
        index = 3 if "specification" in selected else next((i for i, h in enumerate(headings) if h in {"Criterios y pruebas", "Cumplimiento de criterios", "Comprobaciones del conjunto", "Contratos y dependencias"}), 0)
        bodies[index] += "\n\n### Contenido y condiciones de las fuentes\n\n" + literal
    covered = _covered(model, event, data, roots)
    informative = event in INFORMATION or (event in {"start", "resume"} and not data.get("review") and not data.get("offer"))
    negative = event in {"reject-result", "review-comment", "clarify", "identity"} or data.get("outcome") == "changes-requested"
    state = "already-authorized" if covered else "information" if informative else "clarification" if issues or negative else "decision-needed"
    effect = "La decisión vigente se conserva; continúe únicamente el trabajo que ya cubre." if covered else "Este mensaje informa del estado; no solicita otra aprobación." if informative else "Indique las correcciones o decisiones pendientes; el contenido incompleto no permite una aprobación global." if issues else "Indique su respuesta a la cuestión planteada; se conservará como aclaración del alcance afectado." if negative else "La respuesta se aplicará solo al contenido, alcance y efectos mostrados."
    if selected == ["specification"]:
        effect += " Validar la especificación permite preparar el plan; ejecutar se autoriza sobre ese plan concreto."
    if issues:
        if bodies[-1] in {"Ninguno declarado.", "No se han declarado pendientes adicionales para esta decisión.", "No se han declarado decisiones adicionales."}:
            bodies[-1] = ""
        bodies[-1] += "\n\n" + text(list(dict.fromkeys(issues)), model)
    bodies[-1] += "\n\n" + effect
    if model and data.get("actor"):
        bodies[-1] += "\n\nPersona que decide: " + title(human(data["actor"], model)) + "."
    sections = [{"title": h, "body": b} for h, b in zip(headings, bodies)]
    markdown = "# " + title(name) + "\n\n" + "\n\n".join("## " + s["title"] + "\n\n" + s["body"] for s in sections) + "\n"
    trusted = None
    if data.get("trusted_root"):
        from v3_git import observe, code_inventory
        trusted_model = load(data["trusted_root"]).require_valid()
        git_state = observe(trusted_model.root)
        trusted = {"documents": trusted_model.snapshot(), "git": {k: git_state[k] for k in ("branch", "head", "refs")}, "code": code_inventory(trusted_model.root)}
    runtime = Path(__file__).resolve().parent
    implementation = {name: sha((runtime / name).read_bytes()) for name in ("v3_decision_presentation.py", "v3_decision_profiles.py", "v3_presentation_guard.py")}
    source_files = {s["source"]["path"]: model.hashes[s["source"]["path"]] for s in packet["sources"]} if model else {}
    source_files.update(packet.get("historical_source_files", {}))
    for source in packet.get("scope_provenance", []):
        source_files[source["path"]] = model.hashes[source["path"]]
    basis = {"version": VERSION, "implementation": implementation, "event": event, "inputs": data, "sources": [s["source"] for s in packet["sources"]], "source_files": source_files, "trusted": trusted, "instructions": refs,
             "attachments": [{k: a[k] for k in ("path", "sha256")} for a in assets], "subject": subject, "operation": operation_basis,
             "scope_provenance": packet.get("scope_provenance", [])}
    # A file may contain several independent units. Bind the receipt to the
    # selected literal content, while retaining fresh whole-file hashes in the
    # transaction guard. An unrelated edit before the guard needs no new assent;
    # an edit after the guard still fails stamp/prepare/apply concurrency checks.
    semantic_basis = {k: v for k, v in basis.items() if k not in {"sources", "source_files"}}
    semantic_basis["sources"] = [{"key": row["key"], "path": row["source"]["path"],
                                  "digest": row["source"].get("digest", sha(row["text"].encode("utf-8")))}
                                 for row in packet["sources"]]
    semantic_basis["scope_provenance"] = [{k: row[k] for k in ("uid", "path", "digest")} for row in packet.get("scope_provenance", [])]
    receipt = {"version": VERSION, "event": event, "basis_digest": fingerprint(semantic_basis), "content_digest": sha(markdown.encode("utf-8"))}
    return {"version": VERSION, "event": event, "profiles": selected, "title": str(name), "sections": sections,
            "sources": packet["sources"], "attachments": assets, "basis": basis, "receipt": receipt,
            "instruction_refs": refs, "intervention": state, "issues": list(dict.fromkeys(issues)),
            "complete": not issues, "markdown": markdown, "history": packet.get("history"), "writes": []}


def compact(view):
    """One visible body and receipt; details remain available through --json."""
    result = {k: view[k] for k in ("version", "event", "profiles", "markdown", "receipt", "instruction_refs", "intervention", "complete", "issues", "writes")}
    if view.get("history"): result["history"] = view["history"]
    return result
