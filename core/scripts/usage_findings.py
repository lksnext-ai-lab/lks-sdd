"""Evidence-led detectors. Repetition is observable; waste and cause require review."""
import copy

from v3_contract import ContractError, fingerprint, canonical
from v3_usage import check_batch, validate

RULES = {
    "UF-01": ("scripts/v3_context.py", "Contrastar ambas invocaciones, revisiones y motivos; probar reutilización conservando obligaciones.", "La alternativa devuelve el mismo contrato y resultado con menos preparación repetida."),
    "UF-02": ("scripts/v3_scope.py", "Contrastar clasificación de alcance y fuentes conservadas; corregir metadatos solo con evidencia.", "El alcance decidido conserva todas las obligaciones aplicables."),
    "UF-03": ("scripts/v3_cli.py", "Reproducir la entrada y el fallo; contrastar los motivos de los reintentos antes de proponer recuperación.", "La recuperación conserva guards y evita el mismo fallo en este caso."),
    "UF-04": ("scripts/v3_storage.py", "Contrastar la base preparada con el cambio intervenido y el rechazo de frescura.", "El flujo anticipa la base obsoleta y mantiene el rechazo de previews obsoletos."),
    "UF-05": ("scripts/v3_context.py", "Reproducir la selección inicial con su contrato y contrastar aplicabilidad, defecto y corrección.", "La selección corregida conserva el contrato aplicable y la comprobación del defecto pasa."),
    "UF-06": ("docs/USER-DECISIONS.md", "Contrastar pregunta, decisión vigente, alcance y motivo; comprobar si sigue siendo necesaria.", "Se reutiliza una decisión aún vigente y las decisiones nuevas siguen consultándose."),
    "UF-07": ("scripts/v3_usage.py", "Medir recogida, conservación, reporte y exportación por separado; revisar aislamiento y crecimiento.", "No hay recursión ni contaminación normativa y el crecimiento corresponde a datos nuevos."),
}


def detect(rows, *, offset=0, limit=100):
    from v3_usage import WINDOW_COUNT
    if len(rows) > WINDOW_COUNT: raise ContractError("Usage window exceeds 20000 observations")
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
        raise ContractError("Finding page outside limits")
    unique, size = {}, 0
    for row in rows:
        size += len(canonical(row))
        if size > 64*1024*1024: raise ContractError("Usage window exceeds 64 MiB; select a focal case")
        validate(row, "usage-observation")
        key = row["observation_id"]
        if key in unique and unique[key] != row: raise ContractError("Observation ID collision")
        unique[key] = row
    rows = list(unique.values())
    found, repeated, failures, occurrence_ids = {}, {}, {}, {}

    def add(rule, row, scope, fact, hypothesis, *, state="improvement-candidate", target="unknown", material=()):
        binding = row["binding"]
        signature = fingerprint({"rule": rule, "version": 1, "run": row["run_id"], "binding": binding, "scope": scope})
        component, action, criterion = RULES[rule]
        if signature not in found:
            if len(found) >= 10000: raise ContractError("Finding catalog exceeds budget; select a focal run/task")
            found[signature] = {"format": "lks-sdd-usage-finding/1", "finding_id": "UF-" + signature[:20],
                                "signature": signature, "rule": rule, "rule_version": 1, "state": state, "target": target,
                                "fact": fact, "hypothesis": hypothesis, "impact": "Trabajo o riesgo del caso; ahorro y causalidad no medidos.",
                                "priority": "review", "priority_reason": "Disparador concreto; falta contrastar causa e impacto.",
                                "next_action": action, "success_criterion": criterion, "component": component,
                                "occurrences": [], "materials": list(material), "history": []}
            occurrence_ids[signature] = set()
        value = found[signature]
        if row["observation_id"] not in occurrence_ids[signature]:
            value["occurrences"].append(row["observation_id"]); occurrence_ids[signature].add(row["observation_id"])
        for name in material:
            if name not in value["materials"]: value["materials"].append(name)

    for r in rows:
        scope = (r["run_id"], fingerprint(r["binding"]))
        if r["stage"] in {"query", "prepared"}:
            for f in r["fragments"]:
                key = (*scope, r["operation"], f["source"], f["revision"], f["locator"], f["start"], f["end"])
                # Shared logical fragments are counted once per invocation.
                previous = repeated.setdefault(key, [])
                if previous and r.get("invocation_id",r["observation_id"]) != previous[0].get("invocation_id",previous[0]["observation_id"]):
                    for event in [previous[0], r]:
                        add("UF-01", event, key, "En las observaciones consta el mismo fragmento y revisión preparados en invocaciones distintas.",
                            "Puede haber una oportunidad de reutilización; la repetición puede estar justificada.", material=[f["source"]])
                if not previous: previous.append(r)
        widened = r["result"].get("widened")
        if widened:
            add("UF-02", r, widened, "La selección se amplió por incertidumbre o conflicto de alcance.",
                "Mejorar la clasificación podría acotar trabajo; las fuentes ampliadas no se consideran irrelevantes.", material=["selection and scope reasons"])
        if r["stage"] == "failed":
            cause = r["result"].get("cause") or r["result"].get("causes")
            key = (*scope, r["operation"], fingerprint(r["input"]), fingerprint(cause))
            previous = failures.setdefault(key, [])
            if previous:
                for event in [previous[0], r]:
                    add("UF-03", event, key, "Dos llamadas equivalentes fallaron con la misma causa observada.",
                        "Contrastar si el reintento fue necesario; el fallo repetido no demuestra desperdicio.", material=["exact input and error"])
            if not previous: previous.append(r)
            if r.get("preview_hash") and any(x in str(cause).lower() for x in ("changed", "camb", "stale", "obsolet", "fresh")):
                add("UF-04", r, r["preview_hash"], "Un guard rechazó la base preparada tras un cambio observado.",
                    "Investigar anticipación del cambio; el rechazo conserva su función.", material=["prepared base and intervening change"])
        for d in r.get("declarations", []):
            if d.get("type") == "late-context":
                complete = all(d.get(k) for k in ("before", "after", "contract", "defect", "check"))
                add("UF-05", r, d.get("case", d.get("contract", "unknown")),
                    "Se declara recuperación tardía de un contrato y una corrección vinculada; conservar antes/después.",
                    "La causa permanece pendiente; contrastar aplicabilidad previa y selección inicial.",
                    state="improvement-candidate" if complete else "needs-evidence", material=[str(d[k]) for k in ("before", "after", "contract", "defect", "check") if d.get(k)])
                # A declaration alone never becomes a confirmed runtime omission.
            elif d.get("type") == "repeated-question" and not d.get("new_decision"):
                complete = all(d.get(k) for k in ("question", "decision", "scope", "intervention"))
                add("UF-06", r, d.get("case", "question"), "Se declara repetición de una pregunta o paso respecto a una decisión vigente.",
                    "La vigencia y el motivo requieren contraste; declaración del agente.", state="improvement-candidate" if complete else "needs-evidence",
                    material=[str(d[k]) for k in ("question", "decision", "scope", "intervention") if d.get(k)])
            elif d.get("type") == "diagnostic-overhead" and (d.get("contamination") or d.get("recursive") or d.get("unexpected_growth")):
                add("UF-07", r, d.get("case", "diagnostic"), "Se aporta una observación de crecimiento, recursión o contaminación diagnóstica.",
                    "Verificar medición focal y bases normativas; no aplicar un umbral universal.", state="needs-evidence" if not d.get("evidence") else "improvement-candidate", material=[str(d.get("evidence", "overhead measurement"))])
    values = sorted(found.values(), key=lambda f: (f["rule"], f["signature"]))
    for row in rows:
        for change in row.get("declarations", []):
            if change.get("type") != "finding-disposition": continue
            matches = [f for f in values if f["finding_id"] == change.get("finding_id")]
            if not matches: raise ContractError("Disposition references an absent finding")
            f = matches[0]
            updated = disposition(f, change["state"], reason=change.get("reason"), evidence=change.get("evidence"),
                                  plugin_version=change.get("plugin_version"), change=change.get("change"))
            f.update(updated)
    for value in values: validate(value, "usage-finding")
    return {"findings": values[offset:offset+limit], "total": len(values), "next_offset": offset+limit if offset+limit < len(values) else None}


def disposition(finding, state, *, reason, evidence=None, plugin_version=None, change=None):
    if state not in {"dismissed-with-reason", "resolved-with-evidence"} or not reason:
        raise ContractError("Disposition requires an explicit reason")
    if state == "resolved-with-evidence" and not (evidence and plugin_version and change):
        raise ContractError("Resolution requires version, change and verification evidence")
    result = copy.deepcopy(finding)
    result["state"] = state
    result["history"].append({"state": state, "reason": reason, "evidence": evidence, "plugin_version": plugin_version, "change": change})
    return validate(result, "usage-finding")
