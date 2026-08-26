#!/usr/bin/env python3
"""Derive planning completeness, authorization and resumable work for LKS-SDD."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

from contract_engine import build_project_model, resolve_active_increment
from delivery_engine import parse_tables, validate_delivery_contract
from profile_registry import load_profile_bundle


PLANNING_TARGET_HEADERS = (
    "Target", "Type", "State", "Objective", "Increments", "Planning policy",
    "Decision", "Integration task", "Review trigger",
)
COVERAGE_HEADERS = (
    "Target", "Increment", "Contract items", "Primary task",
    "Contributing tasks", "Responsibility", "Rationale",
)
AUTHORIZATION_HEADERS = (
    "ID", "State", "Target", "Increment", "Release", "Tasks",
    "Specification fingerprint", "Planning fingerprint", "Authorized by role",
    "Authorized on", "Decision", "Constraints",
)
CHANGE_HEADERS = (
    "ID", "State", "Classification", "Affected contract", "Affected tasks",
    "Previous fingerprint", "Current fingerprint", "Decision", "Reason",
)
COVERABLE_PREFIXES = {
    "FR", "NFR", "TR", "BR", "AC", "TEST", "CON", "ADR", "INT",
    "DATA", "SEC", "PRIV", "UX", "VIS", "RISK", "DEP",
}
REQUIRED_DEFINITION_FIELDS = (
    "Objective", "In scope", "Out of scope", "Requirements", "Acceptance",
    "Required capabilities", "Technical gates",
)
REQUIRED_PLAN_FIELDS = (
    "Tests", "Decisions and constraints", "Risks and blockers",
    "Responsible role", "Review entry conditions", "Definition of done",
    "Required evidence", "Integration points", "Parallel constraints",
)
ID_TOKEN_RE = re.compile(
    r"(?<![A-Z0-9-])([A-Z][A-Z0-9]*-[0-9]{3})(?:\.\.([A-Z][A-Z0-9]*-[0-9]{3}))?(?![A-Z0-9-])"
)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
PLANNING_ARTIFACT_IDS = {"ART-PLANS", "ART-PLANNING", "ART-TASKS"}


def _meaningful(value: str) -> bool:
    normalized = (value or "").strip().casefold()
    return normalized not in {
        "", "pending", "none", "unknown", "pending-assignment",
        "not-applicable", "not-run", "tbd", "todo",
    } and not normalized.startswith(
        ("pending:", "unknown:", "not-run:", "tbd:", "todo:")
    )


def _artifact_path(manifest: dict[str, Any], artifact_id: str) -> str | None:
    for item in manifest.get("artifacts", []):
        if isinstance(item, dict) and item.get("id") == artifact_id:
            value = item.get("path")
            return value if isinstance(value, str) else None
    return None


def _table_rows(
    tables: Iterable[tuple[tuple[str, ...], list[dict[str, str]]]],
    headers: tuple[str, ...],
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for actual, rows in tables:
        if actual == headers:
            result.extend(rows)
    return result


def expand_ids(value: str) -> tuple[list[str], list[str]]:
    """Expand explicit IDs and inclusive same-prefix ranges."""

    found: list[str] = []
    errors: list[str] = []
    for match in ID_TOKEN_RE.finditer(value or ""):
        start, end = match.groups()
        if end is None:
            found.append(start)
            continue
        start_prefix, start_number = start.rsplit("-", 1)
        end_prefix, end_number = end.rsplit("-", 1)
        if start_prefix != end_prefix or int(start_number) > int(end_number):
            errors.append(f"Rango inválido {start}..{end}.")
            continue
        if int(end_number) - int(start_number) > 998:
            errors.append(f"Rango excesivo {start}..{end}.")
            continue
        found.extend(
            f"{start_prefix}-{number:03d}"
            for number in range(int(start_number), int(end_number) + 1)
        )
    return list(dict.fromkeys(found)), errors


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _confirmed_decision_ids(model: Any) -> set[str]:
    return {
        key
        for key, row in model.nodes.items()
        if key.startswith("ADR-") and row.state_class == "active"
    }


def _specification_fingerprint(active: Any) -> str:
    """Hash implementation inputs without mutable planning/task tracking.

    The legacy active-contract fingerprint intentionally includes scoped TASK
    rows.  A durable authorization needs a separate specification fingerprint
    that survives normal workflow, checkpoint and evidence updates while still
    changing for functional, technical, UX, governance, binding or asset input.
    """

    rows = [
        row
        for row in active.rows
        if row.artifact_id not in PLANNING_ARTIFACT_IDS
        and not row.artifact_id.startswith("ART-TASK-")
    ]
    row_uids = {row.uid for row in rows}
    excluded_prefixes = {"PLAN", "REL", "TASK", "AUTH", "EXEC", "CKPT", "PCH"}
    return _canonical_hash(
        {
            "fingerprint_schema": "lks-sdd-specification-v1",
            "project": active.project,
            "increment": active.increment,
            "rows": sorted(
                (
                    {
                        "artifact_id": row.artifact_id,
                        "table_id": row.table_id,
                        "key": row.key,
                        "state_class": row.state_class,
                        "cells": {
                            key: row.cells[key] for key in sorted(row.cells)
                        },
                    }
                    for row in rows
                ),
                key=lambda item: json.dumps(
                    item, sort_keys=True, ensure_ascii=True
                ),
            ),
            "edges": sorted(
                (
                    {
                        "source": edge.source_id or edge.source_uid,
                        "column": edge.column,
                        "target": edge.target_id,
                    }
                    for edge in active.edges
                    if edge.source_uid in row_uids
                    and edge.target_id.split("-", 1)[0]
                    not in excluded_prefixes
                ),
                key=lambda item: json.dumps(
                    item, sort_keys=True, ensure_ascii=True
                ),
            ),
            "assets": sorted(
                (
                    {
                        "owner_id": asset.owner_id,
                        "path": asset.path,
                        "sha256": asset.sha256,
                    }
                    for asset in active.assets
                ),
                key=lambda item: (item["owner_id"], item["path"]),
            ),
        }
    )


def _select_release(
    manifest: dict[str, Any],
    delivery: dict[str, Any],
    increment: str,
    requested: str | None,
) -> str | None:
    if requested:
        return requested
    planning = manifest.get("planning", {})
    if isinstance(planning, dict) and planning.get("target_type") == "release":
        target = planning.get("target_id")
        if isinstance(target, str):
            return target
    candidates = {
        row.get("Release")
        for row in delivery.get("tasks", {}).values()
        if row.get("Increment") == increment and row.get("Workflow state") != "cancelled"
    }
    candidates.discard(None)
    return next(iter(candidates)) if len(candidates) == 1 else None


def _task_definition(
    task_id: str,
    detail: dict[str, list[dict[str, str]]],
    schema_version: str,
) -> tuple[bool, list[str], dict[str, Any]]:
    definition_rows = detail.get("definition", [])
    definition = definition_rows[0] if len(definition_rows) == 1 else {}
    missing = [
        field for field in REQUIRED_DEFINITION_FIELDS
        if not _meaningful(definition.get(field, ""))
    ]
    plan: dict[str, str] = {}
    continuity: dict[str, str] = {}
    if schema_version in {"1.3", "1.4"}:
        plan_rows = detail.get("plan", [])
        plan = plan_rows[0] if len(plan_rows) == 1 else {}
        missing.extend(
            field for field in REQUIRED_PLAN_FIELDS
            if not _meaningful(plan.get(field, ""))
        )
        continuity_rows = detail.get("continuity", [])
        continuity = continuity_rows[0] if len(continuity_rows) == 1 else {}
        if continuity.get("Definition status") != "executable":
            missing.append("Definition status=executable")
    else:
        missing.extend(REQUIRED_PLAN_FIELDS)
    return not missing, list(dict.fromkeys(missing)), {
        "task": task_id,
        "definition": definition,
        "plan": plan,
        "continuity": continuity,
    }


def _dependency_analysis(
    tasks: dict[str, dict[str, str]],
) -> dict[str, Any]:
    graph: dict[str, list[str]] = {}
    external: dict[str, list[str]] = {}
    for task_id, row in tasks.items():
        dependencies, _ = expand_ids(row.get("Dependencies", ""))
        task_dependencies = [item for item in dependencies if item.startswith("TASK-")]
        graph[task_id] = sorted(item for item in task_dependencies if item in tasks)
        external[task_id] = sorted(item for item in task_dependencies if item not in tasks)

    indegree = {task_id: 0 for task_id in graph}
    dependents: dict[str, list[str]] = defaultdict(list)
    for task_id, dependencies in graph.items():
        indegree[task_id] = len(dependencies)
        for dependency in dependencies:
            dependents[dependency].append(task_id)
    frontier = sorted(task_id for task_id, degree in indegree.items() if degree == 0)
    levels: list[list[str]] = []
    processed: list[str] = []
    while frontier:
        levels.append(frontier)
        next_frontier: list[str] = []
        for task_id in frontier:
            processed.append(task_id)
            for dependent in dependents.get(task_id, []):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    next_frontier.append(dependent)
        frontier = sorted(next_frontier)

    longest: dict[str, list[str]] = {}
    for level in levels:
        for task_id in level:
            dependencies = graph[task_id]
            longest[task_id] = (
                max((longest[item] for item in dependencies), key=len) + [task_id]
                if dependencies
                else [task_id]
            )
    structural_chain = max(longest.values(), key=len, default=[])
    return {
        "acyclic": len(processed) == len(graph),
        "roots": levels[0] if levels else [],
        "parallel_frontiers": levels,
        "external_dependencies": {
            task_id: items for task_id, items in external.items() if items
        },
        "structural_longest_chain": structural_chain,
        "critical_path": {
            "status": "undetermined",
            "reason": "No hay duraciones confirmadas; no se inventan esfuerzo, velocidad o capacidad.",
        },
    }


def _authorization_index_matches(
    manifest_rows: list[dict[str, Any]], markdown_rows: list[dict[str, str]]
) -> list[str]:
    errors: list[str] = []
    by_id = {
        row.get("ID"): row for row in markdown_rows if isinstance(row.get("ID"), str)
    }
    if len(by_id) != len(markdown_rows):
        errors.append("Hay autorizaciones Markdown duplicadas o sin ID.")
    indexed_ids = {
        item.get("authorization_id")
        for item in manifest_rows
        if isinstance(item, dict)
    }
    if len(indexed_ids) != len(manifest_rows) or None in indexed_ids:
        errors.append("Hay autorizaciones duplicadas o sin ID en project.json.")
    if indexed_ids != set(by_id):
        errors.append("authorizations diverge entre planning-coverage.md y project.json.")
        return errors
    for item in manifest_rows:
        row = by_id.get(item.get("authorization_id"), {})
        task_ids, range_errors = expand_ids(row.get("Tasks", ""))
        errors.extend(range_errors)
        comparisons = {
            "state": row.get("State"),
            "target": row.get("Target"),
            "increment": row.get("Increment"),
            "release": row.get("Release"),
            "specification_fingerprint": row.get("Specification fingerprint"),
            "planning_fingerprint": row.get("Planning fingerprint"),
            "authorized_by_role": row.get("Authorized by role"),
            "authorized_on": row.get("Authorized on"),
            "decision": row.get("Decision"),
            "constraints": row.get("Constraints"),
        }
        for field, observed in comparisons.items():
            if item.get(field) != observed:
                errors.append(
                    f"{item.get('authorization_id')}: {field} diverge entre Markdown e índice."
                )
        if sorted(item.get("task_ids", [])) != sorted(
            task for task in task_ids if task.startswith("TASK-")
        ):
            errors.append(
                f"{item.get('authorization_id')}: task_ids diverge entre Markdown e índice."
            )
    return errors


def assess_planning(
    root: Path,
    manifest: dict[str, Any],
    increment: str,
    *,
    release: str | None = None,
) -> dict[str, Any]:
    """Assess whole-target coverage separately from selected-task readiness."""

    root = root.expanduser().resolve()
    schema_version = str(manifest.get("schema_version", ""))
    delivery = validate_delivery_contract(root, manifest)
    model = build_project_model(root)
    confirmed_decisions = _confirmed_decision_ids(model)
    release_id = _select_release(manifest, delivery, increment, release)
    integrity_errors: list[str] = []
    gaps: list[dict[str, Any]] = []
    checked_files = list(delivery.get("checked_files", []))
    target_rows: list[dict[str, str]] = []
    coverage_rows: list[dict[str, str]] = []
    authorization_rows: list[dict[str, str]] = []
    change_rows: list[dict[str, str]] = []

    if schema_version in {"1.3", "1.4"}:
        relative = _artifact_path(manifest, "ART-PLANNING")
        if relative is None:
            integrity_errors.append("Falta ART-PLANNING en el índice 1.3.")
        else:
            path = root / relative
            try:
                tables = parse_tables(path.read_text(encoding="utf-8"))
                checked_files.append(relative)
            except (OSError, UnicodeError) as exc:
                integrity_errors.append(f"No se puede leer ART-PLANNING: {exc}")
                tables = []
            target_rows = _table_rows(tables, PLANNING_TARGET_HEADERS)
            coverage_rows = _table_rows(tables, COVERAGE_HEADERS)
            authorization_rows = _table_rows(tables, AUTHORIZATION_HEADERS)
            change_rows = _table_rows(tables, CHANGE_HEADERS)
    else:
        gaps.append({
            "kind": "migration-required",
            "items": ["ART-PLANNING", "task execution plan", "checkpoints"],
            "explanation": "Schema 1.2 no puede acreditar por sí solo la planificación integral 1.3.",
        })

    target_id = release_id or increment
    target_increments = [increment]
    matching_targets = [row for row in target_rows if row.get("Target") == target_id]
    target = matching_targets[0] if len(matching_targets) == 1 else {}
    if schema_version in {"1.3", "1.4"} and len(matching_targets) != 1:
        gaps.append({
            "kind": "planning-target",
            "items": [target_id],
            "explanation": "El objetivo necesita exactamente una definición de planificación.",
        })
    if target:
        if target.get("Type") != ("release" if release_id else "increment"):
            integrity_errors.append(f"{target_id}: Type no coincide con el identificador.")
        for field in ("Objective", "Review trigger"):
            if not _meaningful(target.get(field, "")):
                gaps.append({"kind": "target-field", "items": [field], "explanation": f"{target_id} no cierra {field}."})
        target_increments, range_errors = expand_ids(target.get("Increments", ""))
        integrity_errors.extend(range_errors)
        if not target_increments:
            gaps.append({
                "kind": "target-scope",
                "items": [target_id],
                "explanation": f"{target_id} no declara ningún incremento.",
            })
        invalid_target_increments = sorted(
            item for item in target_increments if not item.startswith("INC-")
        )
        if invalid_target_increments:
            integrity_errors.append(
                f"{target_id}: Increments solo admite INC-*: "
                + ", ".join(invalid_target_increments)
                + "."
            )
        if increment not in target_increments:
            gaps.append({"kind": "target-scope", "items": [increment], "explanation": f"{target_id} no declara el incremento evaluado."})
        policy = target.get("Planning policy")
        if policy not in {"complete-before-implementation", "incremental-authorized"}:
            integrity_errors.append(f"{target_id}: Planning policy inválida: {policy!r}.")
        if policy == "incremental-authorized":
            decisions, decision_errors = expand_ids(target.get("Decision", ""))
            integrity_errors.extend(decision_errors)
            policy_decisions = [
                item for item in decisions if item.startswith("ADR-")
            ]
            if (
                len(policy_decisions) != 1
                or policy_decisions[0] not in confirmed_decisions
            ):
                gaps.append({"kind": "incremental-decision", "items": [target_id], "explanation": "La planificación incremental exige una decisión ADR humana."})

    evaluated_increments = sorted(
        set(target_increments if release_id and target_increments else [increment])
    )
    active_contracts = {
        item: resolve_active_increment(model, item)
        for item in evaluated_increments
    }
    for item, active_contract in active_contracts.items():
        checked_files.extend(active_contract.checked_files)
        integrity_errors.extend(
            f"{item}: {diagnostic.message}"
            for diagnostic in active_contract.diagnostics
            if diagnostic.severity == "error"
        )
    specification_fingerprint = (
        _specification_fingerprint(active_contracts[increment])
        if evaluated_increments == [increment]
        else _canonical_hash(
            {
                "fingerprint_schema": "lks-sdd-release-specification-v1",
                "target": target_id,
                "increments": {
                    item: _specification_fingerprint(active_contracts[item])
                    for item in evaluated_increments
                },
            }
        )
    )
    expected_items = sorted(
        {
            item
            for active_contract in active_contracts.values()
            for item in active_contract.node_ids
            if item.split("-", 1)[0] in COVERABLE_PREFIXES
        }
    )

    target_tasks = {
        task_id: row
        for task_id, row in delivery.get("tasks", {}).items()
        if row.get("Increment") in evaluated_increments
        and row.get("Workflow state") != "cancelled"
        and (release_id is None or row.get("Release") == release_id)
    }
    if not target_tasks:
        gaps.append({"kind": "tasks-not-defined", "items": [increment], "explanation": "No hay tareas activas para el objetivo."})

    release_row = delivery.get("releases", {}).get(release_id) if release_id else None
    release_task_ids: set[str] = set()
    if release_id and release_row is None:
        integrity_errors.append(f"La release objetivo {release_id} no existe.")
    elif release_row:
        declared, range_errors = expand_ids(release_row.get("Tasks", ""))
        integrity_errors.extend(range_errors)
        release_task_ids = {item for item in declared if item.startswith("TASK-")}
        missing_release_tasks = sorted(set(target_tasks) - release_task_ids)
        unknown_release_tasks = sorted(release_task_ids - set(delivery.get("tasks", {})))
        foreign_release_tasks = sorted(
            (release_task_ids & set(delivery.get("tasks", {}))) - set(target_tasks)
        )
        if missing_release_tasks:
            gaps.append({"kind": "release-task-gap", "items": missing_release_tasks, "explanation": f"{release_id} no enumera todas sus tareas activas."})
        if unknown_release_tasks:
            integrity_errors.append(f"{release_id} enumera tareas inexistentes: {', '.join(unknown_release_tasks)}.")
        if foreign_release_tasks:
            integrity_errors.append(
                f"{release_id} enumera tareas que no pertenecen al objetivo evaluado: "
                + ", ".join(foreign_release_tasks)
                + "."
            )

    ownership: dict[str, list[str]] = defaultdict(list)
    contributors: dict[str, list[str]] = defaultdict(list)
    for row in coverage_rows:
        if row.get("Increment") not in evaluated_increments or row.get("Target") != target_id:
            continue
        contract_ids, range_errors = expand_ids(row.get("Contract items", ""))
        integrity_errors.extend(range_errors)
        primary_ids, primary_errors = expand_ids(row.get("Primary task", ""))
        integrity_errors.extend(primary_errors)
        primary = [item for item in primary_ids if item.startswith("TASK-")]
        contributor_ids, contributor_errors = expand_ids(row.get("Contributing tasks", ""))
        integrity_errors.extend(contributor_errors)
        if len(primary) != 1:
            integrity_errors.append("Cada fila de cobertura debe declarar una única Primary task.")
            continue
        for field in ("Responsibility", "Rationale"):
            if not _meaningful(row.get(field, "")):
                gaps.append(
                    {
                        "kind": "coverage-definition",
                        "items": [primary[0], field],
                        "explanation": "La propiedad de cobertura necesita responsabilidad y justificación comprensibles.",
                    }
                )
        if primary[0] not in target_tasks:
            integrity_errors.append(f"La cobertura asigna elementos a {primary[0]}, que no pertenece al objetivo.")
        invalid_contributors = sorted(
            {
                task
                for task in contributor_ids
                if task.startswith("TASK-") and task not in target_tasks
            }
        )
        if invalid_contributors:
            integrity_errors.append(
                "La cobertura atribuye contribución fuera del objetivo: "
                + ", ".join(invalid_contributors)
                + "."
            )
        if primary[0] in contributor_ids:
            integrity_errors.append(
                f"{primary[0]} no puede figurar como contribuyente de su propia propiedad primaria."
            )
        for item in contract_ids:
            if item not in expected_items:
                integrity_errors.append(
                    f"La cobertura incluye {item}, que no pertenece al contrato activo "
                    f"del objetivo {target_id}."
                )
            ownership[item].append(primary[0])
            contributors[item].extend(
                task for task in contributor_ids
                if task.startswith("TASK-") and task != primary[0]
            )

    task_definitions: dict[str, dict[str, Any]] = {}
    incomplete_tasks: list[dict[str, Any]] = []
    for task_id in sorted(target_tasks):
        complete, missing, payload = _task_definition(
            task_id, delivery.get("task_details", {}).get(task_id, {}), schema_version
        )
        task_definitions[task_id] = payload
        if not complete:
            incomplete_tasks.append({"task": task_id, "missing": missing})
    if incomplete_tasks:
        gaps.append({"kind": "task-definition", "items": incomplete_tasks, "explanation": "Hay tareas que no permiten ejecución y reanudación autónomas."})

    binding_index = {
        item.get("binding_id"): item
        for item in manifest.get("technology", {}).get("profile_bindings", [])
        if isinstance(item, dict)
    }
    for task_id, payload in task_definitions.items():
        binding_id = target_tasks.get(task_id, {}).get("Profile binding")
        binding = binding_index.get(binding_id)
        if not isinstance(binding, dict):
            continue
        profile_id = str(binding.get("profile_id", ""))
        bundle = load_profile_bundle(profile_id)
        if bundle.errors:
            gaps.append(
                {
                    "kind": "task-automation-contract",
                    "items": [task_id, str(binding_id), profile_id],
                    "explanation": (
                        f"{task_id}: no se puede comprobar que capacidades y gates "
                        f"sean aplicables porque el contrato de {profile_id} no está disponible."
                    ),
                }
            )
            continue
        allowed_capabilities = {
            str(item.get("id"))
            for item in bundle.lock.get("capabilities", [])
            if isinstance(item, dict) and item.get("id")
        }
        allowed_gates = {
            str(item.get("id"))
            for item in bundle.lock.get("gates", [])
            if isinstance(item, dict) and item.get("id")
        } | {"GATE-VISUAL-BROWSER-REVIEW"}
        definition = payload.get("definition", {})
        requested_capabilities = set(
            re.findall(
                r"\bCAP-[A-Z0-9-]{3,80}\b",
                definition.get("Required capabilities", ""),
            )
        )
        requested_gates = set(
            re.findall(
                r"\bGATE-[A-Z0-9-]{3,80}\b",
                definition.get("Technical gates", ""),
            )
        )
        unknown_capabilities = sorted(
            requested_capabilities - allowed_capabilities
        )
        unknown_gates = sorted(requested_gates - allowed_gates)
        if unknown_capabilities:
            integrity_errors.append(
                f"{task_id}: capacidades no incluidas en {binding_id}: "
                + ", ".join(unknown_capabilities)
                + "."
            )
        if unknown_gates:
            integrity_errors.append(
                f"{task_id}: gates no aplicables a {binding_id}: "
                + ", ".join(unknown_gates)
                + "."
            )

    if schema_version not in {"1.3", "1.4"}:
        for task_id, payload in task_definitions.items():
            definition = payload["definition"]
            for column in ("Requirements", "Acceptance"):
                ids, _ = expand_ids(definition.get(column, ""))
                for item in ids:
                    if item in expected_items:
                        ownership[item].append(task_id)

    uncovered = sorted(set(expected_items) - set(ownership))
    duplicate_primary = {
        item: sorted(set(tasks))
        for item, tasks in ownership.items()
        if len(set(tasks)) != 1
    }
    if uncovered:
        gaps.append({"kind": "unassigned-contract", "items": uncovered, "explanation": "Alcance activo sin tarea primaria."})
    if duplicate_primary:
        integrity_errors.append(
            "Propiedad primaria duplicada: "
            + "; ".join(f"{item} -> {', '.join(tasks)}" for item, tasks in sorted(duplicate_primary.items()))
        )

    field_for_prefix = {
        "FR": ("definition", "Requirements"),
        "NFR": ("definition", "Requirements"),
        "TR": ("definition", "Requirements"),
        "BR": ("definition", "Requirements"),
        "AC": ("definition", "Acceptance"),
        "TEST": ("plan", "Tests"),
    }
    definition_gaps: list[dict[str, str]] = []
    for item, owners in ownership.items():
        prefix = item.split("-", 1)[0]
        location = field_for_prefix.get(prefix)
        if location is None or len(set(owners)) != 1:
            continue
        task_id = owners[0]
        payload = task_definitions.get(task_id, {})
        table = payload.get(location[0], {})
        mapped, _ = expand_ids(table.get(location[1], ""))
        if item not in mapped:
            definition_gaps.append({"item": item, "task": task_id, "field": location[1]})
    if definition_gaps:
        gaps.append({"kind": "task-trace-gap", "items": definition_gaps, "explanation": "La propiedad de cobertura no coincide con la definición ejecutable."})

    task_claims: dict[str, set[str]] = defaultdict(set)
    for task_id, payload in task_definitions.items():
        for table_name, field in (
            ("definition", "Requirements"),
            ("definition", "Acceptance"),
            ("plan", "Tests"),
        ):
            claimed, claim_errors = expand_ids(
                payload.get(table_name, {}).get(field, "")
            )
            integrity_errors.extend(claim_errors)
            for item in claimed:
                if item in expected_items:
                    task_claims[item].add(task_id)
    undeclared_overlap: dict[str, list[str]] = {}
    for item, claimers in task_claims.items():
        allowed = set(ownership.get(item, [])) | set(contributors.get(item, []))
        unexpected = sorted(claimers - allowed)
        if unexpected:
            undeclared_overlap[item] = unexpected
    if undeclared_overlap:
        integrity_errors.append(
            "Solapamiento de responsabilidad no declarado: "
            + "; ".join(
                f"{item} -> {', '.join(tasks)}"
                for item, tasks in sorted(undeclared_overlap.items())
            )
            + ". Declare la contribución o delimite el alcance de las tareas."
        )

    integration_task: str | None = None
    if target:
        integration_ids, range_errors = expand_ids(target.get("Integration task", ""))
        integrity_errors.extend(range_errors)
        integrations = [item for item in integration_ids if item.startswith("TASK-")]
        if len(integrations) == 1 and integrations[0] in target_tasks:
            integration_task = integrations[0]
        else:
            gaps.append({"kind": "joint-verification", "items": [target_id], "explanation": "Falta una tarea de integración/verificación conjunta perteneciente al objetivo."})

    dependency = _dependency_analysis(target_tasks)
    if not dependency["acyclic"]:
        integrity_errors.append("El grafo de dependencias del objetivo contiene un ciclo.")
    if dependency["external_dependencies"]:
        unresolved: dict[str, list[str]] = {}
        all_tasks = delivery.get("tasks", {})
        for task_id, dependencies in dependency["external_dependencies"].items():
            pending = [
                item for item in dependencies
                if all_tasks.get(item, {}).get("Workflow state") != "done"
            ]
            if pending:
                unresolved[task_id] = pending
        if unresolved:
            gaps.append({"kind": "unresolved-dependency", "items": unresolved, "explanation": "Hay dependencias externas no terminadas; cancelled no equivale a resuelta."})

    plan_id = release_row.get("Plan") if release_row else manifest.get("active_plan")
    plan_row = delivery.get("plans", {}).get(plan_id, {})
    planning_payload = {
        "fingerprint_schema": "lks-sdd-planning-v1",
        "target": {key: value for key, value in target.items() if key != "State"},
        "plan": (
            {
                key: plan_row.get(key)
                for key in (
                    "ID", "Name", "Delivery model", "Major horizon", "Objective",
                    "Increments", "Dependencies", "Owner", "Review date",
                )
            }
            if plan_row
            else None
        ),
        "release": (
            {
                key: release_row.get(key)
                for key in (
                    "ID", "Version", "Plan", "Target date", "Branch or stream",
                    "Environments", "Tasks",
                )
            }
            if release_row
            else None
        ),
        "increment": increment,
        "increments": evaluated_increments,
        "specification_fingerprint": specification_fingerprint,
        "expected_items": expected_items,
        "coverage": {
            item: {
                "primary": sorted(set(ownership.get(item, []))),
                "contributors": sorted(set(contributors.get(item, []))),
                "responsibility": sorted(
                    {
                        row.get("Responsibility", "")
                        for row in coverage_rows
                        if row.get("Target") == target_id
                        and row.get("Increment") in evaluated_increments
                        and item in expand_ids(row.get("Contract items", ""))[0]
                    }
                ),
                "rationale": sorted(
                    {
                        row.get("Rationale", "")
                        for row in coverage_rows
                        if row.get("Target") == target_id
                        and row.get("Increment") in evaluated_increments
                        and item in expand_ids(row.get("Contract items", ""))[0]
                    }
                ),
            }
            for item in expected_items
        },
        "tasks": {
            task_id: {
                "definition": {
                    "identity": {
                        key: target_tasks[task_id].get(key)
                        for key in (
                            "Plan", "Title", "Release", "Increment", "Unit",
                            "Profile binding", "Dependencies", "Owner",
                        )
                    },
                    "definition": task_definitions.get(task_id, {}).get(
                        "definition", {}
                    ),
                    "plan": task_definitions.get(task_id, {}).get("plan", {}),
                },
            }
            for task_id in sorted(target_tasks)
        },
        "dependency": dependency,
        "integration_task": integration_task,
    }
    planning_fingerprint = _canonical_hash(planning_payload)

    planning_index = (
        manifest.get("planning", {})
        if schema_version in {"1.3", "1.4"}
        else {}
    )
    stored_spec = planning_index.get("specification_fingerprint") if isinstance(planning_index, dict) else None
    stored_plan = planning_index.get("planning_fingerprint") if isinstance(planning_index, dict) else None
    fingerprint_stale = bool(
        (stored_spec and stored_spec != specification_fingerprint)
        or (stored_plan and stored_plan != planning_fingerprint)
    )
    recorded_changes: list[dict[str, Any]] = []
    confirmed_changes: list[dict[str, Any]] = []
    applicable_confirmed_changes: list[dict[str, Any]] = []
    affected_contract_items: set[str] = set()
    affected_tasks: set[str] = set()
    for row in change_rows:
        contract_items, contract_errors = expand_ids(
            row.get("Affected contract", "")
        )
        task_items, task_errors = expand_ids(row.get("Affected tasks", ""))
        decision_items, decision_errors = expand_ids(row.get("Decision", ""))
        integrity_errors.extend(contract_errors + task_errors + decision_errors)
        pch_decisions = [
            item for item in decision_items if item.startswith("ADR-")
        ]
        if row.get("Classification") not in {
            "original-contract-failure",
            "new-scope",
        }:
            integrity_errors.append(
                f"{row.get('ID', 'PCH')}: Classification debe ser "
                "original-contract-failure o new-scope."
            )
        for field in ("Previous fingerprint", "Current fingerprint"):
            if not SHA256_RE.fullmatch(row.get(field, "")):
                integrity_errors.append(
                    f"{row.get('ID', 'PCH')}: {field} debe ser SHA-256 hexadecimal."
                )
        if (
            SHA256_RE.fullmatch(row.get("Previous fingerprint", ""))
            and row.get("Previous fingerprint") == row.get("Current fingerprint")
        ):
            integrity_errors.append(
                f"{row.get('ID', 'PCH')}: las huellas anterior y actual no pueden coincidir."
            )
        record = {
            "id": row.get("ID"),
            "state": row.get("State"),
            "classification": row.get("Classification"),
            "previous_fingerprint": row.get("Previous fingerprint"),
            "current_fingerprint": row.get("Current fingerprint"),
            "affected_contract": contract_items,
            "affected_tasks": [
                item for item in task_items if item.startswith("TASK-")
            ],
            "decision": row.get("Decision"),
            "reason": row.get("Reason"),
        }
        recorded_changes.append(record)
        if row.get("State") == "confirmed":
            confirmed_changes.append(record)
            decision_confirmed = (
                len(pch_decisions) == 1
                and pch_decisions[0] in confirmed_decisions
            )
            if not decision_confirmed:
                integrity_errors.append(
                    f"{row.get('ID', 'PCH')}: un PCH confirmed exige una ADR confirmada."
                )
            if (
                decision_confirmed
                and stored_plan
                and row.get("Previous fingerprint") == stored_plan
                and row.get("Current fingerprint") == planning_fingerprint
            ):
                applicable_confirmed_changes.append(record)
                affected_contract_items.update(contract_items)
                affected_tasks.update(record["affected_tasks"])
    if fingerprint_stale and not applicable_confirmed_changes:
        gaps.append(
            {
                "kind": "change-record-required",
                "items": [target_id],
                "explanation": (
                    "La huella cambió y falta un PCH confirmed que enlace exactamente "
                    "planning_fingerprint anterior y actual."
                ),
            }
        )
    conservative_tasks = sorted(
        {
            task
            for owners in ownership.values()
            for task in owners
            if task in target_tasks
        }
    ) if fingerprint_stale and not affected_tasks else []
    if schema_version in {"1.3", "1.4"} and isinstance(planning_index, dict):
        index_is_bound = bool(
            planning_index.get("confirmed_on")
            or stored_spec
            or stored_plan
            or (target and target.get("State") == "confirmed")
        )
        if index_is_bound and planning_index.get("target_id") != target_id:
            gaps.append({"kind": "index-target", "items": [target_id], "explanation": "planning.target_id no coincide con el objetivo evaluado."})
        if (
            index_is_bound
            and target
            and planning_index.get("policy") != target.get("Planning policy")
        ):
            integrity_errors.append("La política de planificación diverge entre Markdown e índice.")
        if index_is_bound and target:
            target_decisions, decision_errors = expand_ids(
                target.get("Decision", "")
            )
            integrity_errors.extend(decision_errors)
            expected_policy_decision = next(
                (
                    item
                    for item in target_decisions
                    if item.startswith("ADR-")
                ),
                None,
            )
            if planning_index.get("policy_decision") != expected_policy_decision:
                integrity_errors.append(
                    "La decisión de política de planificación diverge entre Markdown e índice."
                )
        latest_confirmed_change = max(
            (
                str(item["id"])
                for item in confirmed_changes
                if item.get("id")
            ),
            default=None,
        )
        if (
            index_is_bound
            and not fingerprint_stale
            and planning_index.get("last_change") != latest_confirmed_change
        ):
            integrity_errors.append(
                "planning.last_change no coincide con el último PCH confirmado."
            )
        integrity_errors.extend(
            _authorization_index_matches(
                [item for item in manifest.get("authorizations", []) if isinstance(item, dict)],
                authorization_rows,
            )
        )

    for row in authorization_rows:
        if row.get("State") != "authorized":
            continue
        decision_items, decision_errors = expand_ids(row.get("Decision", ""))
        integrity_errors.extend(decision_errors)
        authorization_decisions = [
            item for item in decision_items if item.startswith("ADR-")
        ]
        if (
            len(authorization_decisions) != 1
            or authorization_decisions[0] not in confirmed_decisions
        ):
            integrity_errors.append(
                f"{row.get('ID', 'AUTH')}: una autorización vigente exige una ADR confirmada."
            )

    confirmed = bool(
        target
        and target.get("State") == "confirmed"
        and stored_spec == specification_fingerprint
        and stored_plan == planning_fingerprint
        and isinstance(planning_index, dict)
        and _meaningful(str(planning_index.get("confirmed_by_role") or ""))
    )
    if (
        not confirmed
        and schema_version in {"1.3", "1.4"}
        and not fingerprint_stale
    ):
        gaps.append({"kind": "human-confirmation", "items": [target_id], "explanation": "La descomposición debe confirmarse y fijar ambos fingerprints."})

    integrity_errors.extend(delivery.get("errors", []))
    integrity_errors = list(dict.fromkeys(integrity_errors))
    integrity = "invalid" if integrity_errors else "valid"
    if fingerprint_stale:
        completeness = "stale"
    elif not target_tasks and not coverage_rows:
        completeness = "not-started"
    elif integrity_errors or gaps or not confirmed:
        completeness = "partial"
    else:
        completeness = "complete"

    policy = (
        target.get("Planning policy")
        if target
        else planning_index.get("policy")
        if isinstance(planning_index, dict)
        else "legacy-undecided"
    )
    target_decision_ids, _ = (
        expand_ids(target.get("Decision", "")) if target else ([], [])
    )
    incremental_decision = (
        planning_index.get("policy_decision")
        if confirmed and isinstance(planning_index, dict)
        else next(
            (item for item in target_decision_ids if item.startswith("ADR-")),
            None,
        )
    )
    partial_allowed = bool(
        confirmed
        and integrity == "valid"
        and completeness == "partial"
        and policy == "incremental-authorized"
        and isinstance(incremental_decision, str)
        and re.fullmatch(r"ADR-[0-9]{3}", incremental_decision)
    )

    return {
        "status": completeness,
        "integrity": integrity,
        "target": {
            "id": target_id,
            "type": "release" if release_id else "increment",
            "increment": increment,
            "increments": evaluated_increments,
            "release": release_id,
        },
        "policy": policy,
        "partial_implementation_policy_satisfied": partial_allowed,
        "specification_fingerprint": specification_fingerprint,
        "planning_fingerprint": planning_fingerprint,
        "stored_fingerprints": {"specification": stored_spec, "planning": stored_plan},
        "confirmed_by_role": (
            planning_index.get("confirmed_by_role")
            if isinstance(planning_index, dict)
            else None
        ),
        "coverage": {
            "expected_items": expected_items,
            "assigned_items": sorted(set(ownership) & set(expected_items)),
            "unassigned_items": uncovered,
            "primary_owners": {item: sorted(set(tasks)) for item, tasks in sorted(ownership.items())},
            "by_task": {
                task_id: sorted(
                    item
                    for item, owners in ownership.items()
                    if task_id in owners and item in expected_items
                )
                for task_id in sorted(target_tasks)
            },
        },
        "tasks": {
            "all": sorted(target_tasks),
            "executable": sorted(set(target_tasks) - {item["task"] for item in incomplete_tasks}),
            "incomplete": incomplete_tasks,
            "initial": dependency["roots"],
            "parallel_frontiers": dependency["parallel_frontiers"],
        },
        "dependency_graph": dependency,
        "integration_task": integration_task,
        "gaps": gaps,
        "integrity_errors": integrity_errors,
        "changes": change_rows,
        "confirmed_decisions": sorted(confirmed_decisions),
        "change_impact": {
            "fingerprint_changed": fingerprint_stale,
            "recorded_changes": recorded_changes,
            "confirmed_changes": confirmed_changes,
            "applicable_confirmed_changes": applicable_confirmed_changes,
            "affected_contract_items": sorted(affected_contract_items),
            "affected_tasks": sorted(affected_tasks),
            "conservative_tasks_pending_pch": conservative_tasks,
            "requires_change_record": fingerprint_stale and not bool(applicable_confirmed_changes),
            "explanation": (
                "La huella cambió sin PCH confirmado; las tareas propietarias se tratan de forma conservadora hasta registrar el impacto."
                if fingerprint_stale and not applicable_confirmed_changes
                else "El impacto procede de PCH versionados; no se infieren decisiones adicionales."
                if applicable_confirmed_changes
                else "No se detecta divergencia de huellas."
            ),
        },
        "checked_files": list(dict.fromkeys(checked_files)),
        "next_action": (
            "replanning-required" if integrity_errors
            else "reconciliation-required" if completeness == "stale"
            else "task-selection-required" if partial_allowed
            else "planning-required" if completeness != "complete"
            else "task-selection-required"
        ),
        "limitations": [
            "El camino crítico queda indeterminado sin duraciones confirmadas.",
            "No se infieren fechas, esfuerzo, capacidad, avance, autoridad ni evidencia.",
        ],
    }


def assess_authorization(
    manifest: dict[str, Any],
    planning: dict[str, Any],
    task_ids: Iterable[str],
) -> dict[str, Any]:
    """Resolve a durable authorization bound to current contract fingerprints."""

    requested = sorted(set(task_ids))
    target = planning.get("target", {})
    stale: list[str] = []
    for item in manifest.get("authorizations", []):
        if not isinstance(item, dict) or item.get("state") != "authorized":
            continue
        if item.get("increment") != target.get("increment"):
            continue
        if target.get("release") and item.get("release") != target.get("release"):
            continue
        authorized_tasks = set(item.get("task_ids", []))
        if not set(requested) <= authorized_tasks:
            continue
        if item.get("specification_fingerprint") != planning.get("specification_fingerprint"):
            stale.append(str(item.get("authorization_id")))
            continue
        if item.get("planning_fingerprint") != planning.get("planning_fingerprint"):
            stale.append(str(item.get("authorization_id")))
            continue
        policy_ok = planning.get("integrity") == "valid" and (
            planning.get("status") == "complete"
            or planning.get("partial_implementation_policy_satisfied") is True
        )
        if not policy_ok:
            stale.append(str(item.get("authorization_id")))
            continue
        return {
            "status": "authorized",
            "authorization_id": item.get("authorization_id"),
            "task_ids": requested,
            "authorized_by_role": item.get("authorized_by_role"),
            "decision": item.get("decision"),
            "constraints": item.get("constraints"),
            "persists_across_pause": True,
            "invalidation_triggers": [
                "specification fingerprint change",
                "planning fingerprint change",
                "scope divergence",
                "revocation",
            ],
        }
    return {
        "status": "invalidated" if stale else "required",
        "authorization_id": None,
        "task_ids": requested,
        "stale_authorizations": sorted(set(stale)),
        "persists_across_pause": False,
    }


def next_tasks(
    delivery: dict[str, Any], planning: dict[str, Any]
) -> dict[str, Any]:
    """Return safe runnable tasks without treating cancelled dependencies as done."""

    tasks = delivery.get("tasks", {})
    candidates: list[str] = []
    blocked: dict[str, list[str]] = {}
    for task_id in planning.get("tasks", {}).get("all", []):
        row = tasks.get(task_id, {})
        if row.get("Workflow state") != "ready":
            continue
        dependencies, _ = expand_ids(row.get("Dependencies", ""))
        unresolved = [
            item for item in dependencies
            if item.startswith("TASK-")
            and tasks.get(item, {}).get("Workflow state") != "done"
        ]
        if unresolved:
            blocked[task_id] = unresolved
        else:
            candidates.append(task_id)
    return {
        "ready": sorted(candidates),
        "blocked_by_dependencies": blocked,
        "parallel": len(candidates) > 1,
        "recommended": candidates[0] if candidates else None,
        "reason": (
            "Primera tarea ready por orden estable; las demás pueden avanzar en paralelo si no comparten restricciones."
            if candidates else "No hay una tarea ready con dependencias done."
        ),
    }
