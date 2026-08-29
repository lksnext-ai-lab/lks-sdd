#!/usr/bin/env python3
"""Human-facing project status, safe cache and verification-subject helpers.

This module is deliberately derived from the canonical Markdown and the
operational index.  It never turns the cache or a generated summary into a
source of truth and it performs no gates, builds, Docker calls or external
operations while calculating status.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from evidence_contract import visual_gate_applicability
from validation_evidence import load_evidence_index, task_health


PLUGIN_VERSION = "0.16.0"
CACHE_SCHEMA = "lks-sdd-experience-cache-1"
PENDING = {"", "none", "pending", "not-run", "not-started", "unknown"}
ACTIVE_PROBLEM_STATES = {"active"}
INACTIVE_PROBLEM_STATES = {"resolved", "superseded", "historical"}
TECHNICAL_STATES = {"in-progress", "in-review", "completed"}
SUPPORTED_PROJECT_SCHEMA = "1.5"
SUPPORTED_METHOD_VERSION = "1.5.0"
_MEMORY_CACHE: dict[str, Any] = {}
_MEMORY_CACHE_LIMIT = 256

# Only paths which are demonstrably produced after a technical run are
# excluded.  Everything ambiguous remains part of the subject (fail closed).
ADMINISTRATIVE_PATHS = (
    re.compile(r"^\.lks-sdd/(?:cache|receipts|summaries)/.+$"),
    re.compile(r"^docs/lks-sdd/04-delivery/checkpoints/CKPT-[0-9]{3}\.md$"),
    re.compile(r"^docs/lks-sdd/evidence/EVID-[0-9]{3}\.json$"),
    re.compile(r"^docs/lks-sdd/evidence/delivery/.+\.json$"),
)


class ExperienceError(ValueError):
    """A safe, user-actionable experience-layer failure."""


@dataclass
class Metrics:
    started: float = field(default_factory=time.perf_counter)
    project_parse_ms: float = 0.0
    validation_ms: float = 0.0
    gate_execution_ms: float = 0.0
    external_sync_ms: float = 0.0
    files_read: int = 0
    files_written: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    gates_reused: int = 0
    gates_executed: int = 0
    administrative_operations: int = 0
    human_confirmations_required: int = 0

    def payload(self) -> dict[str, int | float]:
        elapsed = (time.perf_counter() - self.started) * 1000
        overhead = max(
            0.0,
            elapsed
            - self.project_parse_ms
            - self.validation_ms
            - self.gate_execution_ms
            - self.external_sync_ms,
        )
        return {
            "plugin_overhead_ms": round(overhead, 3),
            "project_parse_ms": round(self.project_parse_ms, 3),
            "validation_ms": round(self.validation_ms, 3),
            "gate_execution_ms": round(self.gate_execution_ms, 3),
            "external_sync_ms": round(self.external_sync_ms, 3),
            "files_read": self.files_read,
            "files_written": self.files_written,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "gates_reused": self.gates_reused,
            "gates_executed": self.gates_executed,
            "administrative_operations": self.administrative_operations,
            "human_confirmations_required": self.human_confirmations_required,
        }


def _read_text(path: Path, metrics: Metrics) -> str:
    try:
        value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ExperienceError(f"No se puede leer {path}: {exc}") from exc
    metrics.files_read += 1
    return value


def _read_json(path: Path, metrics: Metrics) -> dict[str, Any]:
    try:
        value = json.loads(_read_text(path, metrics))
    except json.JSONDecodeError as exc:
        raise ExperienceError(f"JSON inválido en {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExperienceError(f"{path} debe contener un objeto JSON.")
    return value


def parse_tables(text: str) -> list[dict[str, Any]]:
    """Parse simple Markdown tables without rewriting their source."""

    tables: list[dict[str, Any]] = []
    lines = text.splitlines()
    index = 0
    while index + 1 < len(lines):
        header = lines[index].strip()
        separator = lines[index + 1].strip()
        if not (header.startswith("|") and separator.startswith("|")):
            index += 1
            continue
        headers = [cell.strip() for cell in header.strip("|").split("|")]
        separators = [cell.strip() for cell in separator.strip("|").split("|")]
        if len(headers) != len(separators) or not all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in separators
        ):
            index += 1
            continue
        rows: list[dict[str, str]] = []
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
            cells = [cell.strip() for cell in lines[cursor].strip().strip("|").split("|")]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells, strict=True)))
            cursor += 1
        tables.append({"headers": headers, "rows": rows, "line": index + 1})
        index = cursor
    return tables


def _cache_enabled(requested: bool | None = None) -> bool:
    if requested is not None:
        return requested
    return os.environ.get("LKS_SDD_DISABLE_CACHE", "").strip().casefold() not in {
        "1", "true", "yes", "on",
    }


def _cached_tables(
    text: str,
    metrics: Metrics,
    *,
    contract_version: str,
    use_cache: bool,
) -> list[dict[str, Any]]:
    """Reuse deterministic parsing inside one plugin process without writing state."""

    if not use_cache:
        metrics.cache_misses += 1
        return parse_tables(text)
    key = cache_key(
        "markdown-tables",
        {
            "content": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "contract_version": contract_version,
        },
    )
    cached = _MEMORY_CACHE.get(key)
    if isinstance(cached, list):
        metrics.cache_hits += 1
        return deepcopy(cached)
    metrics.cache_misses += 1
    parsed = parse_tables(text)
    if len(_MEMORY_CACHE) >= _MEMORY_CACHE_LIMIT:
        _MEMORY_CACHE.pop(next(iter(_MEMORY_CACHE)))
    _MEMORY_CACHE[key] = deepcopy(parsed)
    return parsed


def _table(tables: Iterable[dict[str, Any]], *required: str) -> list[dict[str, str]]:
    wanted = set(required)
    for item in tables:
        if wanted <= set(item["headers"]):
            return list(item["rows"])
    return []


def _artifact_path(manifest: dict[str, Any], artifact_id: str) -> str | None:
    for item in manifest.get("artifacts", []):
        if isinstance(item, dict) and item.get("id") == artifact_id:
            path = item.get("path")
            return path if isinstance(path, str) else None
    return None


def _safe_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve()
    manifest = root / ".lks-sdd/project.json"
    if not root.is_dir() or not manifest.is_file():
        raise ExperienceError(
            "La raíz no contiene .lks-sdd/project.json; no es un proyecto LKS-SDD legible."
        )
    return root


def _task_detail_path(root: Path, row: dict[str, str], task_id: str) -> Path:
    raw = row.get("Detail", "")
    if raw.startswith("./"):
        return root / "docs/lks-sdd/04-delivery" / raw[2:]
    return root / "docs/lks-sdd/04-delivery/tasks" / f"{task_id}.md"


def _meaningful(value: Any) -> bool:
    return isinstance(value, str) and value.strip().casefold() not in PENDING


def _current_environment(manifest: dict[str, Any]) -> str:
    delivery = manifest.get("last_delivery")
    if isinstance(delivery, dict) and delivery.get("environment"):
        return str(delivery["environment"])
    verification = manifest.get("verification")
    if isinstance(verification, dict) and verification.get("environment"):
        return str(verification["environment"])
    return "local"


def _production_only(problem: dict[str, str]) -> bool:
    material = " ".join(
        problem.get(key, "")
        for key in ("Description", "Impact", "Resolution condition", "Kind")
    ).casefold()
    return any(token in material for token in ("production", "producción", "prod-only"))


def _exact_authorization(manifest: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    planning = manifest.get("planning") if isinstance(manifest.get("planning"), dict) else {}
    for item in reversed(manifest.get("authorizations", [])):
        if not isinstance(item, dict) or item.get("state") != "authorized":
            continue
        if task_id not in item.get("task_ids", []):
            continue
        if item.get("specification_fingerprint") != planning.get("specification_fingerprint"):
            continue
        if item.get("planning_fingerprint") != planning.get("planning_fingerprint"):
            continue
        return item
    return None


def _verification_for_task(manifest: dict[str, Any], task_id: str) -> dict[str, Any]:
    verification = manifest.get("verification")
    if isinstance(verification, dict) and task_id in verification.get("task_ids", []):
        return verification
    return {}


def _execution_for_task(manifest: dict[str, Any], task_id: str) -> dict[str, Any]:
    candidates = [
        item
        for item in manifest.get("executions", [])
        if isinstance(item, dict) and task_id in item.get("task_ids", [])
    ]
    active = [item for item in candidates if item.get("status") in TECHNICAL_STATES | {"blocked", "paused"}]
    return (active or candidates or [{}])[-1]


def _evidence_checks(root: Path, manifest: dict[str, Any], task_id: str, metrics: Metrics) -> tuple[int, list[str]]:
    verification = _verification_for_task(manifest, task_id)
    evidence_ids = verification.get("evidence_ids", []) if verification else []
    passed = 0
    commands: list[str] = []
    for evidence_id in evidence_ids:
        if not isinstance(evidence_id, str) or not re.fullmatch(r"EVID-[0-9]{3}", evidence_id):
            continue
        path = root / "docs/lks-sdd/evidence" / f"{evidence_id}.json"
        if not path.is_file():
            continue
        evidence = _read_json(path, metrics)
        for check in evidence.get("checks", []):
            if not isinstance(check, dict):
                continue
            if check.get("status") == "passed":
                passed += 1
            command = check.get("command")
            if isinstance(command, str) and command not in commands:
                commands.append(command)
    return passed, commands


def _development_label(
    state: str,
    execution: dict[str, Any],
    history: list[dict[str, str]] | None = None,
) -> str:
    execution_state = str(execution.get("status", ""))
    if state == "done" or execution_state == "completed":
        return "Código terminado"
    if state == "in-review" or execution_state == "in-review":
        return "Código terminado; revisión en curso"
    if state == "in-progress" or execution_state == "in-progress":
        return "Desarrollo en curso"
    if state == "blocked" and (
        execution_state in {"in-review", "completed"}
        or any(
            row.get("To") == "blocked"
            and row.get("From") in {"in-review", "done"}
            for row in (history or [])
        )
    ):
        return "Código terminado"
    return "Desarrollo no iniciado"


def _verification_label(verification: dict[str, Any], state: str, active_blocker: str | None) -> str:
    status = str(verification.get("status", "not-run"))
    if status == "verified":
        return "Verificación superada"
    if status == "verified-with-reservations":
        return "Verificación superada con reservas"
    if active_blocker and state in {"in-review", "blocked", "done"}:
        return "Verificación bloqueada"
    if state in {"in-review", "done", "blocked"}:
        return "Verificación pendiente"
    return "Verificación no iniciada"


def _delivery_label(manifest: dict[str, Any], verification: dict[str, Any]) -> str:
    delivery = manifest.get("last_delivery")
    if isinstance(delivery, dict):
        status = str(delivery.get("status", "pending"))
        return {
            "promoted": "Entrega realizada",
            "deployed": "Entrega realizada",
            "verified": "Entrega verificada",
            "rolled-back": "Entrega revertida",
            "failed": "Entrega fallida",
        }.get(status, "Entrega pendiente")
    return "Entrega pendiente" if verification.get("status") == "verified" else "Entrega no iniciada"


def load_status(
    project_root: Path,
    *,
    task_id: str | None = None,
    use_cache: bool | None = None,
) -> dict[str, Any]:
    metrics = Metrics()
    parse_started = time.perf_counter()
    root = _safe_project_root(project_root)
    manifest_path = root / ".lks-sdd/project.json"
    manifest = _read_json(manifest_path, metrics)
    schema = str(manifest.get("schema_version", ""))
    method = str(manifest.get("method_version", ""))
    if schema != SUPPORTED_PROJECT_SCHEMA or method != SUPPORTED_METHOD_VERSION:
        raise ExperienceError(
            "Contrato de proyecto no soportado: "
            f"schema {schema or 'ausente'} / método {method or 'ausente'}; "
            "LKS-SDD 0.15 requiere schema 1.5 y método 1.5.0."
        )
    cache_enabled = _cache_enabled(use_cache)
    contract_version = f"{schema}/{method}"
    tasks_relative = _artifact_path(manifest, "ART-TASKS") or "docs/lks-sdd/04-delivery/tasks.md"
    tasks_path = root / tasks_relative
    task_tables = _cached_tables(
        _read_text(tasks_path, metrics),
        metrics,
        contract_version=contract_version,
        use_cache=cache_enabled,
    )
    tasks = _table(task_tables, "ID", "Title", "Workflow state")
    by_id = {row.get("ID", ""): row for row in tasks if re.fullmatch(r"TASK-[0-9]{3}", row.get("ID", ""))}
    selected_id = task_id or manifest.get("active_task")
    if not selected_id:
        active = [item for item in manifest.get("active_tasks", []) if item in by_id]
        # A list with several candidates is not an actual current TASK.  The
        # management view must expose that ambiguity instead of selecting the
        # first row or backlog item arbitrarily.
        selected_id = active[0] if len(active) == 1 else None
    if task_id and task_id not in by_id:
        raise ExperienceError(f"No existe la tarea {task_id}.")
    selected = by_id.get(str(selected_id), {})
    all_detail_tables: dict[str, list[dict[str, Any]]] = {}
    detail_paths: dict[str, Path] = {}
    for candidate_id, candidate in by_id.items():
        candidate_path = _task_detail_path(root, candidate, candidate_id)
        detail_paths[candidate_id] = candidate_path
        if candidate_path.is_file():
            all_detail_tables[candidate_id] = _cached_tables(
                _read_text(candidate_path, metrics),
                metrics,
                contract_version=contract_version,
                use_cache=cache_enabled,
            )
        else:
            all_detail_tables[candidate_id] = []
    detail_path = detail_paths.get(str(selected_id)) if selected_id else None
    detail_tables = all_detail_tables.get(str(selected_id), []) if selected_id else []
    definition = (_table(detail_tables, "Objective", "Acceptance") or [{}])[0]
    execution_plan = (_table(detail_tables, "Tests", "Definition of done") or [{}])[0]
    deliverables = _table(detail_tables, "Deliverable", "State", "Acceptance")
    problems = _table(detail_tables, "ID", "State", "Description", "Impact")
    validations = _table(detail_tables, "Acceptance", "Gate", "Result", "Evidence")
    history = _table(
        detail_tables,
        "Date",
        "From",
        "To",
        "Reason",
        "Actor or authority",
        "Evidence",
    )
    environment = _current_environment(manifest)
    evidence_index = load_evidence_index(root)
    metrics.files_read += len(
        {
            item.get("_path")
            for items in evidence_index.values()
            for item in items
            if isinstance(item.get("_path"), str)
        }
    )
    all_active_problems: dict[str, list[dict[str, str]]] = {}
    delivery_like: dict[str, Any] = {
        "tasks": by_id,
        "task_details": {},
        "bindings": {
            item.get("binding_id"): item
            for item in manifest.get("technology", {}).get("profile_bindings", [])
            if isinstance(item, dict) and item.get("binding_id")
        },
        "units": {},
    }
    for candidate_id, tables in all_detail_tables.items():
        candidate_definition = _table(tables, "Objective", "Acceptance")
        candidate_problems = _table(tables, "ID", "State", "Description", "Impact")
        all_active_problems[candidate_id] = [
            item for item in candidate_problems
            if item.get("State", "").casefold() in ACTIVE_PROBLEM_STATES
        ]
        delivery_like["task_details"][candidate_id] = {
            "definition": candidate_definition,
            "problems": candidate_problems,
            "issues": candidate_problems,
        }
    active_problems = [
        item
        for item in problems
        if item.get("State", "").casefold() in ACTIVE_PROBLEM_STATES
        and not (_production_only(item) and environment.casefold() in {"local", "development", "dev", "test"})
    ]
    deferred_problems = [
        item
        for item in problems
        if item.get("State", "").casefold() in ACTIVE_PROBLEM_STATES and item not in active_problems
    ]
    historical_problems = [
        item for item in problems if item.get("State", "").casefold() in INACTIVE_PROBLEM_STATES
    ]
    active_blocker = active_problems[0].get("Description") if active_problems else None
    state = str(selected.get("Workflow state", "backlog"))
    execution = _execution_for_task(manifest, str(selected_id)) if selected_id else {}
    verification = _verification_for_task(manifest, str(selected_id)) if selected_id else {}
    passed_checks, test_commands = _evidence_checks(root, manifest, str(selected_id), metrics) if selected_id else (0, [])
    passed_checks += sum(1 for row in validations if row.get("Result", "").casefold() == "passed")
    exact_authorization = _exact_authorization(manifest, str(selected_id)) if selected_id else None
    completed_count = sum(1 for row in by_id.values() if row.get("Workflow state") == "done")
    active_count = sum(1 for row in by_id.values() if row.get("Workflow state") in {"in-progress", "in-review"})
    blocked_count = sum(1 for row in by_id.values() if row.get("Workflow state") == "blocked")
    pending_count = sum(1 for row in by_id.values() if row.get("Workflow state") in {"backlog", "ready"})
    task_healths = {
        candidate_id: task_health(
            candidate_id,
            evidence_index.get(candidate_id, []),
            all_active_problems.get(candidate_id, []),
            manifest.get("verification", {}) if isinstance(manifest.get("verification"), dict) else {},
        )
        for candidate_id in by_id
    }
    latest_evidence = {
        candidate_id: (items[-1] if items else {})
        for candidate_id, items in evidence_index.items()
    }
    executed_checks = [
        check
        for evidence in latest_evidence.values()
        for check in evidence.get("checks", [])
        if isinstance(check, dict) and check.get("name") != "visual-browser-review"
    ]
    visual_checks = [
        check
        for evidence in latest_evidence.values()
        for check in evidence.get("checks", [])
        if isinstance(check, dict) and check.get("name") == "visual-browser-review"
    ]
    applicable_tasks = [
        candidate_id for candidate_id in by_id
        if visual_gate_applicability([candidate_id], delivery_like).get("status") == "applicable"
    ]
    visual_task_rows = {
        item.get("task_id"): item
        for check in visual_checks
        for item in check.get("task_coverage", [])
        if isinstance(item, dict) and item.get("task_id")
    }
    progress_values = []
    for row in by_id.values():
        try:
            progress_values.append(int(row.get("Progress", "0")))
        except ValueError:
            progress_values.append(0)
    counts = {
        "tasks_total": len(by_id),
        "verified": completed_count,
        "in_progress": active_count,
        "blocked": blocked_count,
        "pending": pending_count,
    }
    development = _development_label(state, execution, history)
    tests_label = f"{passed_checks} pruebas superadas" if passed_checks else "Pruebas pendientes"
    verification_label = _verification_label(verification, state, active_blocker)
    delivery_label = _delivery_label(manifest, verification)
    selected_health = task_healths.get(str(selected_id), {
        "historical_verification": "not-verified",
        "current_health": "not-verified",
        "open_findings": [],
        "pending_reverification": False,
        "next_action": "Declarar una TASK activa real o solicitar una TASK explícita.",
    })
    if selected_id is None:
        next_action = "Declarar una TASK activa real o consultar una TASK explícita."
        decision = "Ninguna" if not by_id else "Seleccionar la siguiente TASK solo cuando vaya a iniciarse."
    elif active_blocker:
        next_action = active_problems[0].get("Resolution condition") or "Resolver el bloqueo activo y reanudar desde el último estado material."
        decision = "Ninguna" if exact_authorization else "Resolver o sustituir explícitamente el bloqueo."
    elif selected_health.get("current_health") == "compromised":
        next_action = selected_health["next_action"]
        decision = "Ninguna"
    elif verification.get("status") == "verified" and selected_health.get("current_health") == "healthy":
        next_action = "Revisar la entrega o cerrar formalmente la tarea."
        decision = "Ninguna"
    elif state in {"in-review", "done"} or execution.get("status") == "completed":
        next_action = "Ejecutar únicamente la verificación pendiente."
        decision = "Ninguna"
    elif exact_authorization:
        next_action = "Iniciar o reanudar el trabajo autorizado."
        decision = "Ninguna"
    else:
        next_action = "Confirmar una única vez el inicio de la tarea."
        decision = "Autorizar el inicio de la tarea."
        metrics.human_confirmations_required = 1
    release = (
        selected.get("Release")
        or manifest.get("planning", {}).get("target_id")
        or manifest.get("active_increment")
        or "sin release activa"
    )
    metrics.project_parse_ms = (time.perf_counter() - parse_started) * 1000
    project_status = {
        "release": release,
        "increment": manifest.get("active_increment") or manifest.get("planning", {}).get("target_id"),
        "progress_percent": round(sum(progress_values) / len(progress_values), 1) if progress_values else 0.0,
        **counts,
        "tasks": {
            "completed": completed_count,
            "active": active_count,
            "blocked": blocked_count,
            "pending": pending_count,
        },
        "historically_verified": sum(
            1 for value in task_healths.values()
            if value.get("historical_verification") == "verified"
        ),
        "health_compromised": sum(
            1 for value in task_healths.values()
            if value.get("current_health") == "compromised"
        ),
        "open_findings": sum(len(items) for items in all_active_problems.values()),
        "test_coverage": {
            "executed": len(executed_checks),
            "passed": sum(1 for item in executed_checks if item.get("status") == "passed"),
        },
        "visual_coverage": {
            "applicable_tasks": len(applicable_tasks),
            "covered_tasks": sum(
                1 for task_id in applicable_tasks
                if visual_task_rows.get(task_id, {}).get("status") == "passed"
            ),
            "images": sum(
                int(item.get("image_count", 0)) for item in visual_task_rows.values()
            ),
            "not_applicable_tasks": len(by_id) - len(applicable_tasks),
        },
        "delivery": _delivery_label(manifest, manifest.get("verification", {}) if isinstance(manifest.get("verification"), dict) else {}),
        "human_decisions_pending": ([] if decision == "Ninguna" else [decision]),
    }
    current_task = (
        {
            "id": selected_id,
            "title": selected.get("Title") or "Sin tarea actual",
            "goal": definition.get("Objective") or selected.get("Title") or "Pendiente de definición",
            "development": development,
            "code": development,
            "tests": tests_label,
            "verification": verification_label,
            "historical_verification": selected_health.get("historical_verification"),
            "current_health": selected_health.get("current_health"),
            "pending_reverification": selected_health.get("pending_reverification"),
            "open_findings": selected_health.get("open_findings", []),
            "visual_coverage": visual_task_rows.get(str(selected_id), {
                "status": (
                    "not-applicable"
                    if str(selected_id) not in applicable_tasks
                    else "not-verified"
                ),
                "image_count": 0,
            }),
            "delivery": delivery_label,
            "active_blocker": active_blocker,
            "next_action": next_action,
            "human_decision": decision,
        }
        if selected_id is not None
        else None
    )
    result = {
        "project": project_status,
        "current_task": current_task,
        "developer": {
            "components": sorted({value for value in (selected.get("Unit"), selected.get("Profile binding")) if _meaningful(value)}),
            "files": [detail_path.relative_to(root).as_posix()] if detail_path else [],
            "behavior": definition.get("In scope") or definition.get("Objective") or "Pendiente de definición",
            "test_commands": test_commands,
            "technical_errors": [item.get("Description") for item in active_problems],
            "services": [selected.get("Unit")] if _meaningful(selected.get("Unit")) else [],
            "pending_changes": [item.get("Deliverable") for item in deliverables if item.get("State", "").casefold() not in {"done", "completed", "verified"}],
            "cache": {"hits": metrics.cache_hits, "misses": metrics.cache_misses},
        },
        "audit": {
            "compatibility": {
                "runtime_plugin_version": PLUGIN_VERSION,
                "project_schema_version": schema,
                "method_version": method,
                "materialized_with_plugin_version": manifest.get("plugin_version"),
            },
            "manifest": manifest,
            "task": selected if selected_id is not None else None,
            "definition": definition,
            "execution_plan": execution_plan,
            "deliverables": deliverables,
            "validations": validations,
            "problems": {
                "active": active_problems,
                "deferred": deferred_problems,
                "historical": historical_problems,
            },
            "authorization": exact_authorization,
            "execution": execution,
            "verification": verification,
            "task_health": task_healths,
        },
    }
    result["instrumentation"] = metrics.payload()
    return result


def management_json(status: dict[str, Any]) -> dict[str, Any]:
    """Return the stable compact management contract."""

    return {"project": status["project"], "current_task": status["current_task"]}


def view_json(status: dict[str, Any], view: str) -> dict[str, Any]:
    if view == "management":
        return management_json(status)
    if view == "developer":
        return {
            **management_json(status),
            "developer": status["developer"],
            "instrumentation": status["instrumentation"],
        }
    if view == "audit":
        return status
    raise ExperienceError(f"Vista desconocida: {view}.")


def render_management(status: dict[str, Any]) -> str:
    project = status["project"]
    task = status["current_task"]
    lines = [
        f"PROYECTO · Release {project['release']}",
        f"Plan: {project['tasks_total']} tareas · avance {project['progress_percent']}%",
        f"✅ Terminadas: {project['tasks']['completed']} · históricamente verificadas: {project['historically_verified']}",
        f"🟦 Activas: {project['tasks']['active']}",
        f"⛔ Bloqueadas: {project['blocked']}",
        f"⚪ Pendientes: {project['pending']}",
        f"Salud comprometida: {project['health_compromised']} · hallazgos abiertos: {project['open_findings']}",
        f"Tests: {project['test_coverage']['passed']}/{project['test_coverage']['executed']} superados · Visual: {project['visual_coverage']['covered_tasks']}/{project['visual_coverage']['applicable_tasks']} TASK",
        f"Entrega: {project['delivery']}",
        "",
    ]
    if task is None:
        lines.extend(
            [
                "TAREA ACTUAL · ninguna declarada",
                "",
                "Siguiente paso: Declarar una TASK activa real o consultar una TASK explícita.",
                "Decisión necesaria: ninguna hasta iniciar trabajo.",
            ]
        )
        return "\n".join(lines)
    lines.extend(
        [
            f"TAREA ACTUAL · {task['title']}",
            f"{'✅' if task['development'].startswith('Código terminado') else '🟦' if 'curso' in task['development'] else '⚪'} {task['development']}",
            f"{'✅' if task['tests'][0].isdigit() else '⏳'} {task['tests']}",
            f"{'✅' if 'superada' in task['verification'] else '⛔' if 'bloqueada' in task['verification'] else '⏳'} {task['verification']}",
            f"Salud actual: {task['current_health']} · histórico: {task['historical_verification']}",
        ]
    )
    if task.get("active_blocker"):
        lines.append(f"⛔ Bloqueo: {task['active_blocker']}")
    lines.extend(
        [
            "",
            f"Siguiente paso: {task['next_action']}",
            f"Decisión necesaria: {task['human_decision']}",
            f"Referencias técnicas: {task['id'] or 'sin TASK'} · detalle disponible en audit",
        ]
    )
    return "\n".join(lines)


def render_developer(status: dict[str, Any]) -> str:
    base = render_management(status)
    developer = status["developer"]
    metrics = status["instrumentation"]
    extra = [
        "",
        "DETALLE DE DESARROLLO",
        "Componentes: " + (", ".join(developer["components"]) or "ninguno identificado"),
        "Archivos: " + (", ".join(developer["files"]) or "ninguno identificado"),
        "Comportamiento: " + developer["behavior"],
        "Pruebas: " + ("; ".join(developer["test_commands"]) or "sin comandos registrados"),
        "Pendiente: " + (", ".join(filter(None, developer["pending_changes"])) or "ningún cambio técnico registrado"),
        f"Rendimiento: parseo {metrics['project_parse_ms']} ms; overhead {metrics['plugin_overhead_ms']} ms; caché {metrics['cache_hits']}/{metrics['cache_misses']}",
    ]
    return base + "\n" + "\n".join(extra)


def _all_project_files(root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "-z"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return sorted({item for item in completed.stdout.decode("utf-8").split("\0") if item})
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        return sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        )


def is_administrative_path(relative: str) -> bool:
    normalized = relative.replace("\\", "/")
    return any(pattern.fullmatch(normalized) for pattern in ADMINISTRATIVE_PATHS)


_ADMIN_TABLE_COLUMNS = {
    "State",
    "Workflow state",
    "Health",
    "Progress",
    "Blockers",
    "Updated",
    "Evidence",
    "Revision",
    "Revision start",
    "Revision verified",
    "Artifact digest",
    "Environment",
    "Current checkpoint",
    "Next safe action",
    "Last checkpoint",
}


def _normalized_markdown_subject(text: str) -> bytes:
    """Remove only derived state cells while retaining all contract prose and relations."""

    lines = text.splitlines()
    normalized = list(lines)
    index = 0
    while index + 1 < len(lines):
        header = lines[index].strip()
        separator = lines[index + 1].strip()
        if not (header.startswith("|") and separator.startswith("|")):
            index += 1
            continue
        headers = [cell.strip() for cell in header.strip("|").split("|")]
        separators = [cell.strip() for cell in separator.strip("|").split("|")]
        if len(headers) != len(separators) or not all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in separators
        ):
            index += 1
            continue
        dynamic = {position for position, name in enumerate(headers) if name in _ADMIN_TABLE_COLUMNS}
        if {"Date", "From", "To", "Actor or authority", "Evidence"} <= set(headers):
            dynamic = set(range(len(headers)))
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
            cells = [cell.strip() for cell in lines[cursor].strip().strip("|").split("|")]
            if len(cells) == len(headers):
                for position in dynamic:
                    cells[position] = "<derived-administrative>"
                normalized[cursor] = "| " + " | ".join(cells) + " |"
            cursor += 1
        index = cursor
    return ("\n".join(normalized) + ("\n" if text.endswith("\n") else "")).encode("utf-8")


def _subject_content(relative: str, content: bytes) -> bytes:
    normalized = relative.replace("\\", "/")
    if normalized == ".lks-sdd/project.json":
        try:
            manifest = json.loads(content.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            return content
        if not isinstance(manifest, dict):
            return content
        technical = {
            "project_id": manifest.get("project_id"),
            "method_version": manifest.get("method_version"),
            "schema_version": manifest.get("schema_version"),
            "route": manifest.get("route"),
            "artifacts": manifest.get("artifacts"),
            "technology": manifest.get("technology"),
            "planning": {
                "target_id": manifest.get("planning", {}).get("target_id"),
                "specification_fingerprint": manifest.get("planning", {}).get("specification_fingerprint"),
                "planning_fingerprint": manifest.get("planning", {}).get("planning_fingerprint"),
            },
        }
        return json.dumps(technical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if normalized.startswith("docs/lks-sdd/") and normalized.endswith(".md"):
        try:
            return _normalized_markdown_subject(content.decode("utf-8"))
        except UnicodeError:
            return content
    return content


def verification_subject(
    project_root: Path,
    *,
    use_cache: bool | None = None,
    persist_cache: bool = True,
) -> dict[str, Any]:
    """Hash every technical/contract input and list explicit exclusions."""

    metrics = Metrics()
    root = _safe_project_root(project_root)
    manifest = _read_json(root / ".lks-sdd/project.json", metrics)
    enabled = _cache_enabled(use_cache)
    cache_path = root / ".lks-sdd/cache/verification-subject.json"
    cache_entries: dict[str, Any] = {}
    if enabled:
        try:
            cached_document = json.loads(cache_path.read_text(encoding="utf-8"))
            if (
                isinstance(cached_document, dict)
                and cached_document.get("schema") == CACHE_SCHEMA
                and isinstance(cached_document.get("entries"), dict)
            ):
                cache_entries = cached_document["entries"]
        except (OSError, UnicodeError, json.JSONDecodeError):
            cache_entries = {}
    included: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    digest = hashlib.sha256()
    for relative in _all_project_files(root):
        path = root / relative
        if not path.is_file():
            continue
        normalized = relative.replace("\\", "/")
        if normalized.startswith(".git/"):
            continue
        if is_administrative_path(normalized):
            content = path.read_bytes()
            metrics.files_read += 1
            excluded.append({
                "path": normalized,
                "reason": "derived-administrative",
                "sha256": hashlib.sha256(content).hexdigest(),
            })
            continue
        content = path.read_bytes()
        metrics.files_read += 1
        raw_hash = hashlib.sha256(content).hexdigest()
        subject_key = cache_key(
            "verification-subject-file",
            {
                "path": normalized,
                "content": raw_hash,
                "schema_version": manifest.get("schema_version"),
                "method_version": manifest.get("method_version"),
            },
        )
        cached_hash = cache_entries.get(subject_key) if enabled else None
        if isinstance(cached_hash, str) and re.fullmatch(r"[0-9a-f]{64}", cached_hash):
            file_hash = cached_hash
            metrics.cache_hits += 1
        else:
            file_hash = hashlib.sha256(_subject_content(normalized, content)).hexdigest()
            metrics.cache_misses += 1
            if enabled:
                cache_entries[subject_key] = file_hash
        included.append({"path": normalized, "sha256": file_hash})
        digest.update(normalized.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\0")
    contract_material = {
        "plugin_version": PLUGIN_VERSION,
        "method_version": manifest.get("method_version"),
        "schema_version": manifest.get("schema_version"),
        "planning_fingerprint": manifest.get("planning", {}).get("planning_fingerprint"),
        "specification_fingerprint": manifest.get("planning", {}).get("specification_fingerprint"),
        "profile_bindings": manifest.get("technology", {}).get("profile_bindings", []),
    }
    digest.update(json.dumps(contract_material, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    revision = "workspace"
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True,
            text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    if enabled and persist_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                {"schema": CACHE_SCHEMA, "entries": cache_entries},
                ensure_ascii=False,
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, cache_path)
        metrics.files_written += 1
    return {
        "schema": "lks-sdd-verification-subject-1",
        "observed_revision": revision,
        "verification_subject_hash": digest.hexdigest(),
        "contract_fingerprint": contract_material["specification_fingerprint"],
        "included": included,
        "excluded": excluded,
        "instrumentation": metrics.payload(),
    }


def compare_subject(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    reusable = (
        previous.get("verification_subject_hash") == current.get("verification_subject_hash")
        and previous.get("contract_fingerprint") == current.get("contract_fingerprint")
    )
    before = {item["path"]: item["sha256"] for item in previous.get("included", [])}
    after = {item["path"]: item["sha256"] for item in current.get("included", [])}
    changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
    excluded_before = {item.get("path"): item.get("sha256") for item in previous.get("excluded", [])}
    excluded_after = {item.get("path"): item.get("sha256") for item in current.get("excluded", [])}
    administrative_changes = sorted(
        path for path in set(excluded_before) | set(excluded_after)
        if path and excluded_before.get(path) != excluded_after.get(path)
    )
    return {
        "reusable": reusable,
        "gates_reused": 1 if reusable else 0,
        "gates_executed": 0,
        "technical_changes": changed,
        "continuity_attestation": {
            "previous_revision": previous.get("observed_revision"),
            "observed_revision": current.get("observed_revision"),
            "subject_unchanged": reusable,
            "administrative_changes": administrative_changes,
        } if reusable else None,
    }


def cache_key(namespace: str, material: Any) -> str:
    payload = {
        "schema": CACHE_SCHEMA,
        "plugin_version": PLUGIN_VERSION,
        "namespace": namespace,
        "material": material,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def read_cache(path: Path, key: str) -> Any | None:
    """Read a non-authoritative cache; corruption is a safe miss."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict) or value.get("schema") != CACHE_SCHEMA:
        return None
    entries = value.get("entries")
    return entries.get(key) if isinstance(entries, dict) else None


def write_cache(path: Path, key: str, value: Any) -> None:
    """Atomically write derived cache data outside canonical Markdown."""

    existing: dict[str, Any] = {"schema": CACHE_SCHEMA, "entries": {}}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict) and loaded.get("schema") == CACHE_SCHEMA:
            existing = loaded
    except (OSError, UnicodeError, json.JSONDecodeError):
        pass
    entries = existing.setdefault("entries", {})
    if not isinstance(entries, dict):
        entries = existing["entries"] = {}
    entries[key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(existing, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)
