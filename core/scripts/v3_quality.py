"""Subject-bound Sonar/Dependency-Check results; no server, connector or scheduler."""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import subprocess
import uuid
import tempfile

from v3_contract import ContractError, DOCS, element, fingerprint, load, now, read_bytes, sha
from v3_policy import operator, policy_for
from v3_git import subject, observe
from v3_storage import prepare

TOOLS = {"sonar", "dependency-check"}


def config_digest(control):
    return fingerprint({k: v for k, v in control.items() if k not in {"reason", "label"}})


def age_seconds(text):
    try:
        date = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if date.tzinfo is None: raise ValueError()
        age = (datetime.now(timezone.utc)-date).total_seconds()
        if age < -60: raise ValueError()
        return max(0, age)
    except (ValueError, TypeError, AttributeError) as exc: raise ContractError("Fecha de evidencia inválida") from exc


def analysis_context(model, tasks):
    requests = [model.get(t.data["request"], "request") for t in tasks]
    bases = [{"target": r.data["target"], "base_head": r.data["base"]["head"]} for r in requests]
    if any(value != bases[0] for value in bases): raise ContractError("El grupo mezcla bases de integración distintas")
    return bases[0]


def normalize(tool, report, control):
    for key in ("analysis_id", "generated_at", "tool_version", "subject_digest", "config_digest", "state"):
        if not report.get(key): raise ContractError("Informe sin procedencia: " + key)
    age_seconds(report["generated_at"])
    state = report["state"]
    if state in {"pending", "error", "cancelled"}: return state, report.get("findings", [])
    if state != "completed": raise ContractError("Estado de análisis desconocido")
    if tool == "sonar":
        gate = report.get("projectStatus", {})
        if gate.get("status") not in {"OK", "ERROR"}: raise ContractError("Falta el Quality Gate terminal aplicable")
        if report.get("gate_analysis_id") != report["analysis_id"]: raise ContractError("Quality Gate de otra ejecución")
        return ("passed" if gate["status"] == "OK" else "failed"), gate.get("conditions", [])
    if tool == "dependency-check":
        if not report.get("data_updated_at") or "dependencies" not in report:
            raise ContractError("Faltan dependencias o vigencia de datos de Dependency-Check")
        if age_seconds(report["data_updated_at"]) > control.get("max_data_age_seconds", 86400):
            raise ContractError("Datos de vulnerabilidades desactualizados")
        findings = []
        for dep in report["dependencies"]:
            for vulnerability in dep.get("vulnerabilities", []):
                score = vulnerability.get("cvssv3", {}).get("baseScore", vulnerability.get("cvssv2", {}).get("score"))
                if not isinstance(score, (int, float)): raise ContractError("Hallazgo sin severidad interpretable")
                findings.append({"dependency": dep.get("fileName"), "name": vulnerability.get("name"), "score": score})
        suppressed = report.get("suppression_digest")
        if suppressed != control.get("suppression_digest"): raise ContractError("Supresiones distintas de la política")
        return ("failed" if any(f["score"] >= control.get("fail_cvss", 7) for f in findings) else "passed"), findings
    raise ContractError("Herramienta no admitida")


def record(root, actor, task_ids, tool, report):
    model = load(root).require_valid()
    if tool not in TOOLS or not task_ids: raise ContractError("Herramienta y tareas requeridas")
    tasks = [model.get(k, "task") for k in task_ids]
    provenance = analysis_context(model, tasks)
    if report.get("context") != provenance: raise ContractError("El análisis no acredita la base/destino de estas tareas")
    identity = operator(model, actor, "implement", policy_for(model, tasks[0]))
    control = policy_for(model, tasks[0]).data["controls"][tool]
    if control["mode"] == "not-used": raise ContractError("El control está declarado no utilizado")
    allowed_groups = [g for t in tasks for g in required_groups(t, tool, control)]
    scope = report.get("scope", sorted({p for g in allowed_groups for p in g}))
    if not scope or any(p not in {p for g in allowed_groups for p in g} for p in scope):
        raise ContractError("Ámbito de análisis no declarado en las tareas/política")
    observed = subject(model.root, scope)
    if report.get("subject_digest") != observed["digest"] or report.get("config_digest") != config_digest(control):
        raise ContractError("El informe no representa las entradas/configuración actuales")
    for t in tasks:
        operator(model, actor, "implement", policy_for(model, t))
        if config_digest(policy_for(model, t).data["controls"][tool]) != config_digest(control):
            raise ContractError("El grupo de análisis mezcla políticas incompatibles")
    result, findings = normalize(tool, report, control)
    key = fingerprint({"tool": tool, "inputs": observed, "config": config_digest(control), "analysis_id": report["analysis_id"], "report": report})
    for old in model.by_kind("analysis"):
        if old.data.get("key") == key:
            return {"status": "reused", "analysis": old.uid, "result": old.data["result"], "writes": []}
    item = element("analysis", "Análisis " + tool, "Resultado observado; no equivale a aceptación del PR.",
                   actor=identity, tool=tool, tasks=[t.uid for t in tasks], subject=observed,
                   config_digest=config_digest(control), result=result, findings=findings[:20], findings_count=len(findings), context=provenance,
                   git=observe(model.root),
                   analysis_id=report["analysis_id"], tool_version=report["tool_version"], generated_at=report["generated_at"],
                   data_updated_at=report.get("data_updated_at"), recorded_at=now(), key=key,
                   previous=report.get("previous"), scope=scope)
    item["meta"].update(state="observed", nature="fact")
    path = DOCS + "/evidence/" + item["meta"]["uid"] + ".json"
    raw = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
    item["meta"]["data"].update(report_path=path, report_sha256=sha(raw))
    packet = prepare(root, [item], "analysis", changes={path: raw}, guards={"subject": observed, "git": observe(model.root)})
    packet["summary"].update(analysis=item["meta"]["uid"], result=result)
    return packet


def required_groups(task, tool, control):
    groups = task.data.get("analysis_groups", {}).get(tool, [control["scope"]])
    if not isinstance(groups, list) or not groups or any(not isinstance(g, list) or not g for g in groups):
        raise ContractError("Declare grupos de análisis con rutas concretas")
    return groups


def checks(model, task):
    policy = policy_for(model, task)
    result = {}
    from v3_team import contains
    for tool, control in policy.data["controls"].items():
        if control["mode"] == "not-used":
            result[tool] = {"mode": "not-used", "status": "not-used", "reason": control["reason"]}; continue
        applicability = task.data.get("control_applicability", {}).get(tool)
        if applicability and applicability.get("state") == "not-applicable":
            if not applicability.get("reason"): raise ContractError("No aplicabilidad sin motivo")
            from v3_approval import approved
            if not approved(model, [task.uid], "plan")["valid"]:
                raise ContractError("La no aplicabilidad necesita validación expresa del plan que la contiene")
            result[tool] = {"mode": control["mode"], "status": "not-applicable", "reason": applicability["reason"]}; continue
        groups = []
        for group in required_groups(task, tool, control):
            candidates = []
            for analysis in model.by_kind("analysis"):
                data = analysis.data
                if data.get("tool") != tool or data.get("config_digest") != config_digest(control): continue
                if data.get("context") != analysis_context(model, [task]): continue
                if not all(contains(data.get("scope", []), p) for p in group): continue
                try:
                    if subject(model.root, data["scope"])["digest"] != data["subject"]["digest"]: continue
                    if sha(read_bytes(model.root, data["report_path"], limit=64*1024*1024)) != data["report_sha256"]: continue
                    if age_seconds(data["generated_at"]) > control.get("max_age_seconds", 86400): continue
                    if tool == "dependency-check" and data["result"] in {"passed", "failed"} and age_seconds(data["data_updated_at"]) > control.get("max_data_age_seconds", 86400): continue
                    candidates.append(analysis)
                except (ContractError, OSError, KeyError): continue
            candidates.sort(key=lambda e: (e.data["generated_at"], e.data["recorded_at"], e.uid))
            latest = candidates[-1] if candidates else None
            groups.append({"scope": group, "status": latest.data["result"] if latest else "pending", "analysis": latest.uid if latest else None})
        bad = next((g["status"] for g in groups if g["status"] != "passed"), None)
        result[tool] = {"mode": control["mode"], "status": bad or "passed", "groups": groups}
    return result


def valid_until(model, tasks):
    limits = []
    for task in tasks:
        for tool, check in checks(model, task).items():
            control = policy_for(model, task).data["controls"][tool]
            if control["mode"] != "required": continue
            for group in check.get("groups", []):
                if not group.get("analysis"): continue
                data = model.get(group["analysis"]).data
                limits.append(datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00")) + timedelta(seconds=control.get("max_age_seconds", 86400)))
                if tool == "dependency-check" and data.get("data_updated_at"):
                    limits.append(datetime.fromisoformat(data["data_updated_at"].replace("Z", "+00:00")) + timedelta(seconds=control.get("max_data_age_seconds", 86400)))
    return min(limits).isoformat() if limits else None


def findings(root, analysis_id, *, offset=0, limit=20):
    model = load(root).require_valid(); analysis = model.get(analysis_id, "analysis")
    if offset < 0 or not 1 <= limit <= 100: raise ContractError("Página de hallazgos fuera de límites")
    raw = read_bytes(model.root, analysis.data["report_path"], limit=64*1024*1024)
    if sha(raw) != analysis.data["report_sha256"]: raise ContractError("Informe original alterado")
    report = json.loads(raw)
    # Findings are retained in the original report, independently of its current age.
    if analysis.data["tool"] == "sonar": values = report.get("projectStatus", {}).get("conditions", report.get("findings", []))
    else: values = [{"dependency": d.get("fileName"), **v} for d in report.get("dependencies", []) for v in d.get("vulnerabilities", [])]
    return {"analysis": analysis.source(), "items": values[offset:offset+limit], "total": len(values),
            "next_offset": offset+limit if offset+limit < len(values) else None}


def run_existing(root, actor, task_ids, tool, executable, arguments, *, retry_of=None):
    """The caller explicitly supplies an already authorized executable/argv; no shell or repo script discovery."""
    model = load(root).require_valid()
    tasks = [model.get(k, "task") for k in task_ids]
    operator(model, actor, "implement", policy_for(model, tasks[0]))
    control = policy_for(model, tasks[0]).data["controls"][tool]
    if control.get("executor") != "existing-command": raise ContractError("No hay ejecutor autorizado en la política")
    executable = Path(executable).resolve()
    if not executable.is_file() or sha(executable.read_bytes()) != control.get("executable_sha256"):
        raise ContractError("El ejecutor no coincide con el archivo aprobado")
    if fingerprint(arguments) != control.get("arguments_digest"):
        raise ContractError("Los argumentos no coinciden con la configuración aprobada")
    attempts = 0
    predecessor = retry_of
    while predecessor:
        old = model.get(predecessor, "analysis")
        if old.data.get("tool") != tool or set(old.data["tasks"]) != {t.uid for t in tasks}:
            raise ContractError("El reintento pertenece a otro análisis")
        attempts += 1; predecessor = old.data.get("previous")
        if attempts > control["max_retries"]: raise ContractError("Límite de reintentos alcanzado")
    before = subject(model.root, sorted({p for t in tasks for g in required_groups(t, tool, control) for p in g}))
    failure = None
    try:
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            completed = subprocess.run([str(executable), *arguments], cwd=model.root, stdout=output, stderr=errors,
                                       timeout=control["timeout_seconds"], shell=False)
            output.seek(0); report_bytes = output.read(64*1024*1024+1)
    except subprocess.TimeoutExpired: failure = "timeout"
    except OSError: failure = "executor-unavailable"
    if not failure:
        if len(report_bytes) > 64*1024*1024: failure = "report-too-large"
        elif completed.returncode: failure = "executor-error"
    if failure:
        report = {"state": "error", "analysis_id": str(uuid.uuid4()), "generated_at": now(), "tool_version": "unobserved",
                  "subject_digest": before["digest"], "config_digest": config_digest(control), "findings": [{"failure": failure}]}
    else:
        try: report = json.loads(report_bytes)
        except (ValueError, UnicodeError):
            report = {"state": "error", "analysis_id": str(uuid.uuid4()), "generated_at": now(), "tool_version": "unobserved",
                      "subject_digest": before["digest"], "config_digest": config_digest(control), "findings": [{"failure": "invalid-report"}]}
    if report.get("subject_digest") != before["digest"]: raise ContractError("El ejecutor no acreditó las entradas observadas")
    report["previous"] = retry_of
    if failure or report.get("tool_version") == "unobserved": report["context"] = analysis_context(model, tasks)
    return record(root, actor, task_ids, tool, report)
