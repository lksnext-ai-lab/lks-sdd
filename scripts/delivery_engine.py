#!/usr/bin/env python3
"""Validate and summarize the LKS-SDD 1.2 delivery and task contract."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable


DELIVERY_MODELS = {
    "bounded-release",
    "continuous-evolution",
    "maintenance-stream",
}
TASK_STATES = {
    "backlog",
    "ready",
    "in-progress",
    "in-review",
    "done",
    "blocked",
    "cancelled",
}
TASK_HEALTH = {"on-track", "at-risk", "blocked", "unknown"}
ACTIVE_PLAN_STATES = {"confirmed", "active"}
ACTIVE_RELEASE_STATES = {"planned", "active", "frozen"}
ID_RE = re.compile(
    r"\b(?:PLAN|TASK|REL|UNIT|BIND|CHG|ENV|INC|ADR|AC|TEST|EVID)-[0-9]{3}\b"
)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
REVISION_RE = re.compile(
    r"^(?:[a-f0-9]{40,64}|workspace-sha256:[a-f0-9]{64})$"
)
TREE_ID_RE = re.compile(r"^(?:[a-f0-9]{40,64}|workspace:[a-f0-9]{64})$")
BUILD_ID_RE = re.compile(r"^build-sha256:[a-f0-9]{64}$")
UTC_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)

GOVERNANCE_HEADERS = (
    "ID",
    "State",
    "Effective from",
    "Delivery model",
    "Versioning",
    "Branching",
    "Artifact promotion",
    "Deployment",
    "Recovery",
    "Decision",
    "Review trigger",
)
ENVIRONMENT_HEADERS = (
    "ID",
    "State",
    "Role",
    "Promotion order",
    "Deployables",
    "Approval",
    "Configuration",
    "Data",
    "Observability",
    "Recovery",
)
PLAN_HEADERS = (
    "ID",
    "State",
    "Name",
    "Delivery model",
    "Major horizon",
    "Objective",
    "Increments",
    "Dependencies",
    "Owner",
    "Review date",
)
RELEASE_HEADERS = (
    "ID",
    "State",
    "Version",
    "Plan",
    "Target date",
    "Branch or stream",
    "Environments",
    "Tasks",
    "Commit",
    "Artifact",
    "Evidence",
)
TASK_HEADERS = (
    "ID",
    "Plan",
    "Title",
    "Release",
    "Increment",
    "Unit",
    "Profile binding",
    "Workflow state",
    "Health",
    "Progress",
    "Dependencies",
    "Blockers",
    "Owner",
    "Detail",
    "Updated",
)
ARCHITECTURE_HEADERS = (
    "Unit",
    "State",
    "Component",
    "Responsibility",
    "Runtime boundary",
    "Interfaces",
    "Data ownership",
    "Requirements",
    "Profile binding",
)
TASK_DETAIL_HEADERS = {
    "identity": (
        "Task",
        "Plan",
        "Release",
        "Increment",
        "Unit",
        "Profile binding",
        "Type",
    ),
    "definition": (
        "Objective",
        "In scope",
        "Out of scope",
        "Requirements",
        "Acceptance",
        "Required capabilities",
        "Technical gates",
        "Dependencies",
    ),
    "execution": (
        "Workflow state",
        "Health",
        "Progress",
        "Owner",
        "Branch",
        "Revision start",
        "Revision verified",
        "Build",
        "Environment",
        "Updated",
    ),
    "issues": (
        "ID",
        "State",
        "Description",
        "Impact",
        "Owner",
        "Resolution condition",
        "Evidence",
    ),
    "validation": (
        "Acceptance",
        "Gate",
        "Result",
        "Evidence",
        "Revision",
        "Artifact digest",
        "Environment",
    ),
    "history": (
        "Date",
        "From",
        "To",
        "Reason",
        "Actor or authority",
        "Evidence",
    ),
}


class DeliveryContractError(ValueError):
    """Expected invalid or unsafe delivery contract."""


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def _safe_file(root: Path, relative: str) -> tuple[Path | None, str | None]:
    requested = Path(relative)
    if requested.is_absolute() or ".." in requested.parts:
        return None, f"Ruta no permitida: {relative}"
    current = root
    for part in requested.parts:
        current = current / part
        if _is_link_like(current):
            return None, f"La ruta usa un symlink o junction: {relative}"
    try:
        resolved = (root / requested).resolve(strict=False)
        resolved.relative_to(root)
    except ValueError:
        return None, f"Ruta fuera del proyecto: {relative}"
    return resolved, None


def _cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [item.strip() for item in stripped[1:-1].split("|")]


def _separator(cells: list[str] | None) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", item) for item in cells)


def parse_tables(text: str) -> list[tuple[tuple[str, ...], list[dict[str, str]]]]:
    """Parse ordinary pipe tables without interpreting their prose."""

    lines = text.splitlines()
    tables: list[tuple[tuple[str, ...], list[dict[str, str]]]] = []
    index = 0
    while index + 1 < len(lines):
        headers = _cells(lines[index])
        separator = _cells(lines[index + 1])
        if not headers or len(set(headers)) != len(headers) or not _separator(separator):
            index += 1
            continue
        rows: list[dict[str, str]] = []
        cursor = index + 2
        while cursor < len(lines):
            values = _cells(lines[cursor])
            if values is None or len(values) != len(headers):
                break
            rows.append(dict(zip(headers, values, strict=True)))
            cursor += 1
        tables.append((tuple(headers), rows))
        index = cursor
    return tables


def _table_rows(
    tables: Iterable[tuple[tuple[str, ...], list[dict[str, str]]]],
    headers: tuple[str, ...],
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for actual, rows in tables:
        if actual == headers:
            result.extend(rows)
    return result


def _ids(value: str, prefix: str | None = None) -> list[str]:
    found = ID_RE.findall(value or "")
    if prefix is not None:
        found = [item for item in found if item.startswith(prefix + "-")]
    return list(dict.fromkeys(found))


def _frontmatter_scalar(text: str, key: str) -> str | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    match = re.search(
        rf"(?m)^{re.escape(key)}:\s*(?:\"([^\"]*)\"|'([^']*)'|([^#\r\n]+))\s*$",
        parts[1],
    )
    if not match:
        return None
    return next((item.strip() for item in match.groups() if item is not None), None)


def _artifact_path(manifest: dict[str, Any], artifact_id: str) -> str | None:
    for item in manifest.get("artifacts", []):
        if isinstance(item, dict) and item.get("id") == artifact_id:
            path = item.get("path")
            return path if isinstance(path, str) else None
    return None


def _load_artifact(
    root: Path,
    manifest: dict[str, Any],
    artifact_id: str,
    errors: list[str],
    checked: list[str],
) -> tuple[str, list[tuple[tuple[str, ...], list[dict[str, str]]]]]:
    relative = _artifact_path(manifest, artifact_id)
    if relative is None:
        errors.append(f"Falta {artifact_id} en el índice operativo.")
        return "", []
    path, path_error = _safe_file(root, relative)
    if path_error or path is None or not path.is_file():
        errors.append(f"{artifact_id}: {path_error or 'archivo ausente'}")
        return "", []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{relative}: no se puede leer: {exc}")
        return "", []
    checked.append(relative)
    return text, parse_tables(text)


def _meaningful(value: str) -> bool:
    return (value or "").strip().casefold() not in {"", "pending", "none", "unknown"}


def _date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _validate_task_detail(
    root: Path,
    row: dict[str, str],
    errors: list[str],
    checked: list[str],
) -> dict[str, Any] | None:
    task_id = row["ID"]
    target = row.get("Detail", "").strip()
    match = re.fullmatch(r"(?:\./)?tasks/(TASK-[0-9]{3})\.md", target)
    if not match or match.group(1) != task_id:
        errors.append(
            f"{task_id}: Detail debe ser ./tasks/{task_id}.md."
        )
        return None
    relative = f"docs/lks-sdd/04-delivery/tasks/{task_id}.md"
    path, path_error = _safe_file(root, relative)
    if path_error or path is None or not path.is_file():
        errors.append(f"{task_id}: falta su definición independiente {relative}.")
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{task_id}: no se puede leer su detalle: {exc}")
        return None
    checked.append(relative)
    if _frontmatter_scalar(text, "artifact_id") != f"ART-{task_id}":
        errors.append(f"{task_id}: artifact_id debe ser ART-{task_id}.")
    if _frontmatter_scalar(text, "artifact_type") != "development-task":
        errors.append(f"{task_id}: artifact_type debe ser development-task.")
    if _frontmatter_scalar(text, "schema_version") != "1.2":
        errors.append(f"{task_id}: schema_version debe ser 1.2.")
    tables = parse_tables(text)
    resolved: dict[str, list[dict[str, str]]] = {}
    for name, headers in TASK_DETAIL_HEADERS.items():
        matches = [rows for actual, rows in tables if actual == headers]
        if len(matches) != 1:
            errors.append(
                f"{task_id}: falta o se repite la tabla de detalle {name}."
            )
            resolved[name] = []
        else:
            resolved[name] = matches[0]
    identity = resolved.get("identity", [])
    execution = resolved.get("execution", [])
    definition = resolved.get("definition", [])
    if len(identity) != 1:
        errors.append(f"{task_id}: la tabla Identidad necesita exactamente una fila.")
    else:
        identity_row = identity[0]
        expected = {
            "Task": task_id,
            "Plan": row["Plan"],
            "Release": row["Release"],
            "Increment": row["Increment"],
            "Unit": row["Unit"],
            "Profile binding": row["Profile binding"],
        }
        for column, value in expected.items():
            if identity_row.get(column) != value:
                errors.append(
                    f"{task_id}: {column} diverge entre tablero y detalle."
                )
    if len(execution) != 1:
        errors.append(f"{task_id}: la tabla Ejecución necesita exactamente una fila.")
    else:
        execution_row = execution[0]
        for column in ("Workflow state", "Health", "Progress", "Owner", "Updated"):
            if execution_row.get(column) != row.get(column):
                errors.append(
                    f"{task_id}: {column} diverge entre tablero y detalle."
                )
    if len(definition) != 1:
        errors.append(f"{task_id}: Definición ejecutable necesita una fila.")
    else:
        required = (
            "Objective",
            "In scope",
            "Out of scope",
            "Requirements",
            "Acceptance",
            "Required capabilities",
            "Technical gates",
        )
        missing = [column for column in required if not _meaningful(definition[0].get(column, ""))]
        if row["Workflow state"] not in {"backlog", "blocked", "cancelled"} and missing:
            errors.append(
                f"{task_id}: una tarea {row['Workflow state']} tiene campos sin cerrar: {', '.join(missing)}."
            )
    issues = resolved.get("issues", [])
    issue_ids: set[str] = set()
    for issue in issues:
        issue_id = issue.get("ID", "")
        if not re.fullmatch(r"PROB-[0-9]{3}", issue_id):
            errors.append(f"{task_id}: ID de problema inválido: {issue_id!r}.")
        elif issue_id in issue_ids:
            errors.append(f"{task_id}: problema duplicado {issue_id}.")
        issue_ids.add(issue_id)
        if issue.get("State") not in {"open", "mitigating", "resolved", "accepted"}:
            errors.append(f"{task_id}: estado de problema inválido en {issue_id}.")
        for column in ("Description", "Impact", "Owner", "Resolution condition"):
            if not _meaningful(issue.get(column, "")):
                errors.append(f"{task_id}: {issue_id or 'problema'} requiere {column}.")
    if row["Workflow state"] == "blocked" and not any(
        issue.get("State") in {"open", "mitigating"} for issue in issues
    ):
        errors.append(f"{task_id}: blocked exige un problema abierto o en mitigación.")

    validation = resolved.get("validation", [])
    if row["Workflow state"] == "done" and not validation:
        errors.append(f"{task_id}: done exige evidencia de validación.")
    for proof in validation:
        gates = [item.strip() for item in proof.get("Gate", "").split(",") if item.strip()]
        if not gates or any(
            not re.fullmatch(r"GATE-[A-Z0-9-]{3,80}", item) for item in gates
        ):
            errors.append(f"{task_id}: Gate de validación inválido.")
        if proof.get("Result") not in {"passed", "failed", "not-run", "accepted-limitation"}:
            errors.append(f"{task_id}: Result de validación inválido.")
        evidence = [
            item.strip() for item in proof.get("Evidence", "").split(",") if item.strip()
        ]
        if not evidence or any(not re.fullmatch(r"EVID-[0-9]{3}", item) for item in evidence):
            errors.append(f"{task_id}: Evidence de validación debe usar EVID-###.")
        if not REVISION_RE.fullmatch(proof.get("Revision", "")):
            errors.append(f"{task_id}: revisión de validación inválida.")
        if not re.fullmatch(
            r"sha256:[a-f0-9]{64}", proof.get("Artifact digest", "")
        ):
            errors.append(f"{task_id}: digest de artefacto inválido.")
        if not re.fullmatch(
            r"(?:ENV-[0-9]{3}|not-applicable)", proof.get("Environment", "")
        ):
            errors.append(f"{task_id}: entorno de validación inválido.")
    if row["Workflow state"] == "done" and any(
        proof.get("Result") != "passed" for proof in validation
    ):
        errors.append(f"{task_id}: done solo admite validaciones passed.")
    return resolved


def _dependency_cycles(tasks: dict[str, dict[str, str]]) -> list[list[str]]:
    graph = {
        task_id: [item for item in _ids(row.get("Dependencies", ""), "TASK") if item in tasks]
        for task_id, row in tasks.items()
    }
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            start = stack.index(node)
            cycle = stack[start:] + [node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        visiting.add(node)
        stack.append(node)
        for dependency in graph[node]:
            visit(dependency)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for task_id in graph:
        visit(task_id)
    return cycles


def validate_delivery_contract(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate delivery governance, plans, releases, tasks and task details."""

    if str(manifest.get("schema_version")) != "1.2":
        return {
            "errors": [],
            "warnings": [],
            "checked_files": [],
            "governance": {},
            "plans": {},
            "releases": {},
            "tasks": {},
            "units": {},
            "bindings": {},
        }

    root = root.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []
    _, governance_tables = _load_artifact(
        root, manifest, "ART-GOVERNANCE", errors, checked
    )
    _, plan_tables = _load_artifact(root, manifest, "ART-PLANS", errors, checked)
    _, task_tables = _load_artifact(root, manifest, "ART-TASKS", errors, checked)
    _, architecture_tables = _load_artifact(
        root, manifest, "ART-ARCH", errors, checked
    )

    governance_rows = _table_rows(governance_tables, GOVERNANCE_HEADERS)
    environment_rows = _table_rows(governance_tables, ENVIRONMENT_HEADERS)
    plan_rows = _table_rows(plan_tables, PLAN_HEADERS)
    release_rows = _table_rows(plan_tables, RELEASE_HEADERS)
    task_rows = _table_rows(task_tables, TASK_HEADERS)
    unit_rows = _table_rows(architecture_tables, ARCHITECTURE_HEADERS)

    governance = {row.get("ID", ""): row for row in governance_rows if row.get("ID")}
    environments = {row.get("ID", ""): row for row in environment_rows if row.get("ID")}
    plans = {row.get("ID", ""): row for row in plan_rows if row.get("ID")}
    releases = {row.get("ID", ""): row for row in release_rows if row.get("ID")}
    tasks = {row.get("ID", ""): row for row in task_rows if row.get("ID")}
    units = {row.get("Unit", ""): row for row in unit_rows if row.get("Unit")}
    bindings = {
        item.get("binding_id", ""): item
        for item in manifest.get("technology", {}).get("profile_bindings", [])
        if isinstance(item, dict) and item.get("binding_id")
    }

    for label, rows, values in (
        ("gobierno", governance_rows, governance),
        ("entornos", environment_rows, environments),
        ("planes", plan_rows, plans),
        ("releases", release_rows, releases),
        ("tareas", task_rows, tasks),
        ("unidades", unit_rows, units),
    ):
        if len(rows) != len(values):
            errors.append(f"Hay identificadores duplicados o vacíos en {label}.")

    index_governance = manifest.get("delivery_governance", {})
    active_change = index_governance.get("active_change")
    current_governance = governance.get(active_change)
    if current_governance is None:
        errors.append("delivery_governance.active_change no existe en ART-GOVERNANCE.")
    else:
        if current_governance.get("State") != index_governance.get("state"):
            errors.append("El estado del gobierno diverge entre Markdown e índice.")
        if (
            current_governance.get("Delivery model") != "pending"
            and current_governance.get("Delivery model") != index_governance.get("model")
        ):
            errors.append("El modelo de entrega diverge entre Markdown e índice.")
        decision = current_governance.get("Decision", "")
        if not decision.startswith("pending") and decision != index_governance.get("decision"):
            errors.append("La decisión de gobierno diverge entre Markdown e índice.")
        if current_governance.get("State") == "confirmed":
            if current_governance.get("Delivery model") not in DELIVERY_MODELS:
                errors.append("El gobierno confirmado debe seleccionar un modelo de entrega válido.")
            for column in (
                "Effective from",
                "Versioning",
                "Branching",
                "Artifact promotion",
                "Deployment",
                "Recovery",
                "Decision",
                "Review trigger",
            ):
                if not _meaningful(current_governance.get(column, "")):
                    errors.append(f"El gobierno confirmado no cierra {column}.")
            if not any(row.get("State") == "confirmed" for row in environments.values()):
                errors.append("El gobierno confirmado necesita al menos un entorno confirmado.")

    version_control = manifest.get("version_control", {})
    if index_governance.get("state") == "confirmed":
        if version_control.get("branching_model") is None:
            errors.append("Falta version_control.branching_model confirmado.")
        if version_control.get("type") == "git" and not version_control.get("main_branch"):
            errors.append("Un proyecto Git necesita main_branch en el índice 1.2.")
        if version_control.get("decision") != index_governance.get("decision"):
            errors.append("La decisión de versionado Git no coincide con el gobierno vigente.")

    for binding_id, binding in bindings.items():
        unit_id = binding.get("unit_id")
        if unit_id not in units:
            errors.append(f"{binding_id}: unit_id {unit_id!r} no existe en arquitectura.")
        if binding.get("state") == "confirmed" and not binding.get("selection_decision"):
            errors.append(f"{binding_id}: falta ADR de selección confirmada.")
        expected_lock = f".lks-sdd/profiles/{binding_id}.lock.json"
        if binding.get("lock_path") != expected_lock:
            errors.append(f"{binding_id}: lock_path debe ser {expected_lock}.")
    confirmed_bindings = [
        item for item in bindings.values() if item.get("state") == "confirmed"
    ]
    selected_profile = manifest.get("technology", {}).get("selected_profile")
    if len(confirmed_bindings) == 1 and selected_profile not in {
        None,
        confirmed_bindings[0].get("profile_id"),
    }:
        errors.append("technology.selected_profile diverge del único binding confirmado.")
    if len(confirmed_bindings) > 1 and selected_profile is not None:
        errors.append("technology.selected_profile debe ser null en una composición multiperfil.")

    active_plan = manifest.get("active_plan")
    if active_plan is not None and active_plan not in plans:
        errors.append(f"active_plan {active_plan!r} no existe en ART-PLANS.")
    for plan_id, row in plans.items():
        model = row.get("Delivery model")
        if model != "pending" and model not in DELIVERY_MODELS:
            errors.append(f"{plan_id}: Delivery model inválido: {model!r}.")
        review = row.get("Review date", "")
        if review != "pending" and not _date(review):
            errors.append(f"{plan_id}: Review date debe usar AAAA-MM-DD o pending.")
    for release_id, row in releases.items():
        if row.get("Plan") not in plans:
            errors.append(f"{release_id}: Plan no existe.")
        environments_for_release = _ids(row.get("Environments", ""), "ENV")
        for environment_id in environments_for_release:
            if environment_id not in environments:
                errors.append(f"{release_id}: entorno inexistente {environment_id}.")

    detail_contracts: dict[str, Any] = {}
    for task_id, row in tasks.items():
        state = row.get("Workflow state", "")
        health = row.get("Health", "")
        if state not in TASK_STATES:
            errors.append(f"{task_id}: Workflow state inválido: {state!r}.")
        if health not in TASK_HEALTH:
            errors.append(f"{task_id}: Health inválido: {health!r}.")
        try:
            progress = int(row.get("Progress", ""))
        except ValueError:
            errors.append(f"{task_id}: Progress debe ser un entero 0..100.")
            progress = -1
        if not 0 <= progress <= 100:
            errors.append(f"{task_id}: Progress queda fuera de 0..100.")
        if state == "done" and progress != 100:
            errors.append(f"{task_id}: done exige Progress=100.")
        if state in {"backlog", "ready"} and progress != 0:
            errors.append(f"{task_id}: {state} exige Progress=0.")
        if state in {"in-progress", "in-review"} and not 1 <= progress <= 99:
            errors.append(f"{task_id}: {state} exige Progress entre 1 y 99.")
        blockers = row.get("Blockers", "").strip().casefold()
        if state == "blocked" and (
            health != "blocked" or blockers in {"", "none", "not-applicable"}
        ):
            errors.append(f"{task_id}: blocked exige Health=blocked y un bloqueo visible.")
        if health == "blocked" and state != "blocked":
            errors.append(f"{task_id}: Health=blocked exige Workflow state=blocked.")
        if row.get("Plan") not in plans:
            errors.append(f"{task_id}: Plan no existe.")
        if row.get("Release") not in releases:
            errors.append(f"{task_id}: Release no existe.")
        if row.get("Unit") not in units:
            errors.append(f"{task_id}: Unit no existe.")
        if row.get("Profile binding") not in bindings:
            errors.append(f"{task_id}: Profile binding no existe.")
        updated = row.get("Updated", "")
        if not _date(updated):
            errors.append(f"{task_id}: Updated debe usar AAAA-MM-DD.")
        detail = _validate_task_detail(root, row, errors, checked)
        if detail is not None:
            detail_contracts[task_id] = detail

    for cycle in _dependency_cycles(tasks):
        errors.append("Ciclo de dependencias entre tareas: " + " -> ".join(cycle))
    for task_id, row in tasks.items():
        for dependency in _ids(row.get("Dependencies", ""), "TASK"):
            if dependency not in tasks:
                errors.append(f"{task_id}: dependencia inexistente {dependency}.")
            elif row.get("Workflow state") == "ready" and tasks[dependency].get(
                "Workflow state"
            ) not in {"done", "cancelled"}:
                errors.append(
                    f"{task_id}: no puede estar ready mientras {dependency} no esté resuelta."
                )

    return {
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
        "checked_files": list(dict.fromkeys(checked)),
        "governance": governance,
        "environments": environments,
        "plans": plans,
        "releases": releases,
        "tasks": tasks,
        "task_details": detail_contracts,
        "units": units,
        "bindings": bindings,
    }


def delivery_readiness(
    root: Path,
    manifest: dict[str, Any],
    increment: str,
    task_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Return deterministic G2 blockers for a schedulable task slice."""

    result = validate_delivery_contract(root, manifest)
    blockers = list(result["errors"])
    warnings = list(result["warnings"])
    if str(manifest.get("schema_version")) != "1.2":
        return {
            "status": "not-applicable",
            "blockers": [],
            "warnings": [
                "El contrato PLAN/TASK y el gobierno de entrega requieren schema 1.2."
            ],
            "task_ids": [],
            "binding_ids": [],
            "plan_id": None,
            "release_ids": [],
        }

    governance = manifest.get("delivery_governance", {})
    if governance.get("state") != "confirmed":
        blockers.append("El gobierno de entrega debe estar confirmed antes de G2.")
    if governance.get("model") not in DELIVERY_MODELS:
        blockers.append("Falta seleccionar un modelo de entrega válido.")
    if not governance.get("decision"):
        blockers.append("Falta la ADR confirmada del gobierno de entrega.")

    active_plan = manifest.get("active_plan")
    plan = result["plans"].get(active_plan)
    if plan is None or plan.get("State") not in ACTIVE_PLAN_STATES:
        blockers.append("El incremento necesita un PLAN confirmado o activo.")
    elif plan.get("Delivery model") != governance.get("model"):
        blockers.append("El PLAN activo no usa el modelo de entrega vigente.")

    increment_tasks = {
        task_id: row
        for task_id, row in result["tasks"].items()
        if row.get("Increment") == increment and row.get("Workflow state") != "cancelled"
    }
    requested = list(dict.fromkeys(task_ids or []))
    if not requested and manifest.get("active_task"):
        requested = [manifest["active_task"]]
    if not requested:
        requested = sorted(
            task_id
            for task_id, row in increment_tasks.items()
            if row.get("Workflow state") == "ready"
        )
    tasks = {
        task_id: increment_tasks[task_id]
        for task_id in requested
        if task_id in increment_tasks
    }
    missing_tasks = sorted(set(requested) - set(tasks))
    for task_id in missing_tasks:
        blockers.append(
            f"{task_id} no existe o no pertenece al incremento {increment}."
        )
    if not increment_tasks:
        blockers.append(f"{increment} no tiene tareas de desarrollo definidas.")
    elif not tasks:
        blockers.append(
            f"{increment} no tiene una tarea ready seleccionada para G2."
        )
    for task_id, row in tasks.items():
        if row.get("Workflow state") != "ready":
            blockers.append(
                f"{task_id} debe estar ready antes de iniciar implementación; "
                f"está {row.get('Workflow state')!r}."
            )
        binding = result["bindings"].get(row.get("Profile binding"))
        if binding is None or binding.get("state") != "confirmed":
            blockers.append(f"{task_id} no tiene un profile binding confirmado.")
        release = result["releases"].get(row.get("Release"))
        if release is None or release.get("State") not in ACTIVE_RELEASE_STATES:
            blockers.append(f"{task_id} no tiene una release planificable activa.")
        for dependency in _ids(row.get("Dependencies", ""), "TASK"):
            dependency_state = result["tasks"].get(dependency, {}).get(
                "Workflow state"
            )
            if dependency_state not in {"done", "cancelled"}:
                blockers.append(
                    f"{task_id} depende de {dependency}, que aún está "
                    f"{dependency_state or 'absent'}."
                )

    return {
        "status": "ready" if not blockers else "blocked",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
        "task_ids": sorted(tasks),
        "binding_ids": sorted(
            {
                row["Profile binding"]
                for row in tasks.values()
                if row.get("Profile binding")
            }
        ),
        "plan_id": active_plan,
        "release_ids": sorted(
            {row["Release"] for row in tasks.values() if row.get("Release")}
        ),
    }


def task_board(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Return a compact, derived task board; Markdown remains the source."""

    validated = validate_delivery_contract(root, manifest)
    tasks = validated["tasks"]
    by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task_id, row in sorted(tasks.items()):
        by_plan[row.get("Plan", "unknown")].append({"task_id": task_id, **row})
    return {
        "valid": not validated["errors"],
        "errors": validated["errors"],
        "warnings": validated["warnings"],
        "summary": {
            "total": len(tasks),
            "workflow": dict(sorted(Counter(row.get("Workflow state") for row in tasks.values()).items())),
            "health": dict(sorted(Counter(row.get("Health") for row in tasks.values()).items())),
            "blocked": sorted(
                task_id
                for task_id, row in tasks.items()
                if row.get("Workflow state") == "blocked"
            ),
        },
        "plans": dict(sorted(by_plan.items())),
        "source": "docs/lks-sdd/04-delivery/tasks.md",
    }


def repository_revision(root: Path) -> dict[str, Any]:
    """Bind evidence to Git HEAD or a deterministic workspace fingerprint."""

    root = root.expanduser().resolve()
    git_dir = root / ".git"
    if git_dir.exists():
        def git(*args: str) -> str:
            completed = subprocess.run(
                ["git", *args],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            return completed.stdout.strip()

        try:
            revision = git("rev-parse", "HEAD")
            branch = git("branch", "--show-current") or "detached"
            status = git("status", "--porcelain=v1", "--untracked-files=all")
            tree = git("rev-parse", "HEAD^{tree}")
            tree_listing = subprocess.run(
                ["git", "ls-tree", "-r", "-z", "--full-tree", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            raise DeliveryContractError(f"No se puede obtener la revisión Git: {exc}") from exc
        return {
            "kind": "git",
            "revision": revision,
            "branch": branch,
            "tree": tree,
            "tree_id": tree,
            "tree_sha256": hashlib.sha256(tree_listing).hexdigest(),
            "dirty": bool(status),
        }

    digest = hashlib.sha256()
    ignored = {
        ".git",
        ".lks-sdd/evidence",
        "node_modules",
        ".venv",
        "dist",
        "build",
        ".next",
        ".angular",
        "coverage",
        "test-results",
        "playwright-report",
    }
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_link_like(path):
            continue
        relative = path.relative_to(root).as_posix()
        if any(relative == item or relative.startswith(item + "/") for item in ignored):
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    value = digest.hexdigest()
    return {
        "kind": "workspace",
        "revision": f"workspace-sha256:{value}",
        "branch": None,
        "tree": value,
        "tree_id": f"workspace:{value}",
        "tree_sha256": value,
        "dirty": False,
    }


def canonical_tree_sha256(root: Path, paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(set(paths)):
        path, error = _safe_file(root, relative)
        if error or path is None or not path.is_file():
            raise DeliveryContractError(error or f"Falta {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def load_delivery_evidence(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Validate externally produced G4 evidence without performing a deployment."""

    errors: list[str] = []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {}, [f"No se puede leer la evidencia de entrega: {exc}"]
    if not isinstance(value, dict):
        return {}, ["La evidencia de entrega debe ser un objeto JSON."]
    required = {
        "schema_version",
        "release",
        "environment",
        "revision",
        "tree_id",
        "build_id",
        "artifact_digests",
        "promotion",
        "smoke",
        "observability",
        "recovery",
        "authorization",
    }
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"Evidencia de entrega incompleta; faltan {missing}.")
    unknown = sorted(set(value) - required)
    if unknown:
        errors.append(f"Evidencia de entrega contiene campos no admitidos: {unknown}.")
    if value.get("schema_version") != "1.0":
        errors.append("schema_version de evidencia de entrega debe ser 1.0.")
    if not re.fullmatch(r"REL-[0-9]{3}", str(value.get("release", ""))):
        errors.append("release debe ser REL-###.")
    if not re.fullmatch(r"ENV-[0-9]{3}", str(value.get("environment", ""))):
        errors.append("environment debe ser ENV-###.")
    if not REVISION_RE.fullmatch(str(value.get("revision", ""))):
        errors.append("revision debe ser un commit o workspace-sha256 exacto.")
    if not TREE_ID_RE.fullmatch(str(value.get("tree_id", ""))):
        errors.append("tree_id debe ser un árbol Git o workspace exacto.")
    if not BUILD_ID_RE.fullmatch(str(value.get("build_id", ""))):
        errors.append("build_id debe usar build-sha256:<64-hex>.")
    digests = value.get("artifact_digests")
    if not isinstance(digests, list) or not digests or not all(
        re.fullmatch(r"sha256:[a-f0-9]{64}", str(item)) for item in digests
    ):
        errors.append("artifact_digests debe contener digests sha256 inmutables.")
    elif len(digests) != len(set(digests)):
        errors.append("artifact_digests no admite duplicados.")
    for field in ("promotion", "smoke", "observability", "recovery", "authorization"):
        evidence = value.get(field)
        if not isinstance(evidence, dict):
            errors.append(f"{field} no contiene un objeto de evidencia.")
            continue
        expected_fields = {"status", "recorded_at", "reference"}
        if field == "authorization":
            expected_fields.add("authority")
        unknown_evidence = sorted(set(evidence) - expected_fields)
        if unknown_evidence:
            errors.append(
                f"{field} contiene campos no admitidos: {unknown_evidence}."
            )
        if evidence.get("status") != "passed":
            errors.append(f"{field} no contiene evidencia passed.")
        if not UTC_TIMESTAMP_RE.fullmatch(str(evidence.get("recorded_at", ""))):
            errors.append(f"{field}.recorded_at debe usar UTC AAAA-MM-DDTHH:MM:SSZ.")
        if not _meaningful(str(evidence.get("reference", ""))):
            errors.append(f"{field}.reference debe identificar evidencia verificable.")
        if field == "authorization" and not _meaningful(
            str(evidence.get("authority", ""))
        ):
            errors.append("authorization.authority debe identificar la autoridad.")
    return value, errors
