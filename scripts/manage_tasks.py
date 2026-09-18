#!/usr/bin/env python3
"""Validate, display and safely transition canonical LKS-SDD tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from delivery_engine import (
    REVISION_RE,
    TASK_DETAIL_HEADERS,
    TASK_HEALTH,
    TASK_HEADERS,
    TASK_DETAIL_HEADERS_V13,
    parse_tables,
    task_board,
    validate_delivery_contract,
)
from planning_engine import assess_authorization, assess_planning
from task_tracking_engine import assess_tracking
from validate_project import validate_project


TRANSITIONS = {
    "backlog": {"ready", "blocked", "cancelled"},
    "ready": {"in-progress", "blocked", "cancelled"},
    "in-progress": {"in-review", "blocked", "cancelled"},
    "in-review": {"in-progress", "done", "blocked", "cancelled"},
    "blocked": {"backlog", "ready", "in-progress", "in-review", "cancelled"},
    "done": {"backlog", "blocked"},
    "cancelled": set(),
}
SYMBOLS = {
    "backlog": "○",
    "ready": "◇",
    "in-progress": "▶",
    "in-review": "◆",
    "done": "✓",
    "blocked": "!",
    "cancelled": "×",
}


class TaskManagementError(ValueError):
    """Expected task management error."""


def _load_manifest(root: Path) -> tuple[Path, dict[str, Any], bytes]:
    path = root / ".lks-sdd" / "project.json"
    try:
        original = path.read_bytes()
        value = json.loads(original.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TaskManagementError(f"No se puede leer project.json: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "1.5":
        raise TaskManagementError("La gestión PLAN/TASK de 0.15 requiere schema 1.5.")
    return path, value, original


def _artifact_path(manifest: dict[str, Any], artifact_id: str) -> str:
    expected = {
        "ART-TASKS": "docs/lks-sdd/04-delivery/tasks.md",
    }.get(artifact_id)
    for item in manifest.get("artifacts", []):
        if isinstance(item, dict) and item.get("id") == artifact_id:
            observed = str(item.get("path", ""))
            if expected is not None and observed != expected:
                raise TaskManagementError(
                    f"{artifact_id} debe usar la ruta canónica {expected}."
                )
            return observed
    raise TaskManagementError(f"Falta {artifact_id} en el índice.")


def _cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [item.strip() for item in stripped[1:-1].split("|")]


def _replace_table_row(
    text: str,
    headers: tuple[str, ...],
    row_id: str,
    updates: dict[str, str],
) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        cells = _cells(line)
        if cells != list(headers):
            continue
        row_index = index + 2
        while row_index < len(lines):
            values = _cells(lines[row_index])
            if values is None:
                break
            if len(values) == len(headers) and values[0] == row_id:
                row = dict(zip(headers, values, strict=True))
                row.update(updates)
                lines[row_index] = "| " + " | ".join(
                    row[header] for header in headers
                ) + " |"
                return "\n".join(lines) + "\n"
            row_index += 1
    raise TaskManagementError(f"No se encontró la fila {row_id}.")


def _single_detail_row(
    text: str, headers: tuple[str, ...]
) -> dict[str, str]:
    matches = [rows for actual, rows in parse_tables(text) if actual == headers]
    if len(matches) != 1 or len(matches[0]) != 1:
        raise TaskManagementError(
            f"La tarea no tiene una tabla única {headers[0]}."
        )
    return matches[0][0]


def _append_table_row(
    text: str, headers: tuple[str, ...], values: list[str]
) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _cells(line) != list(headers):
            continue
        insert_at = index + 2
        while insert_at < len(lines) and _cells(lines[insert_at]) is not None:
            insert_at += 1
        lines.insert(insert_at, "| " + " | ".join(values) + " |")
        return "\n".join(lines) + "\n"
    raise TaskManagementError(f"No se encontró la tabla {headers[0]}.")


def _replace_frontmatter_date(text: str, value: str) -> str:
    updated, count = re.subn(
        r'^last_updated: "[0-9]{4}-[0-9]{2}-[0-9]{2}"$',
        f'last_updated: "{value}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise TaskManagementError("No se pudo actualizar last_updated.")
    return updated


def _default_tracking(
    target: str,
    current_progress: int,
    current_health: str,
    *,
    schema_version: str,
) -> tuple[str, int]:
    if schema_version in {"1.3", "1.4", "1.5"}:
        if target == "done":
            return "on-track", 100
        if target == "blocked":
            return "blocked", current_progress
        if target == "cancelled":
            return "unknown", current_progress
        # Progress is an observation, not a workflow-state estimate. Preserve
        # it unless the caller supplies --progress explicitly.
        return (
            "unknown" if current_health == "blocked" else current_health,
            current_progress,
        )
    if target == "backlog":
        return "unknown", 0
    if target == "ready":
        return "on-track", 0
    if target == "in-progress":
        return "on-track", min(99, max(1, current_progress))
    if target == "in-review":
        return "on-track", min(99, max(90, current_progress))
    if target == "done":
        return "on-track", 100
    if target == "blocked":
        return "blocked", min(99, max(0, current_progress))
    return "unknown", current_progress


def _safe_cell(label: str, value: str | None, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise TaskManagementError(f"{label} es obligatorio.")
        return None
    normalized = value.strip()
    if required and not normalized:
        raise TaskManagementError(f"{label} es obligatorio.")
    if "|" in normalized or "\n" in normalized or "\r" in normalized:
        raise TaskManagementError(f"{label} no puede contener barras de tabla ni saltos de línea.")
    return normalized


def _observed_evidence(value: str | None) -> bool:
    normalized = (value or "").strip().casefold()
    return normalized not in {
        "", "pending", "none", "unknown", "not-run", "not-applicable",
        "tbd", "todo",
    } and not normalized.startswith(
        ("pending:", "unknown:", "not-run:", "tbd:", "todo:")
    )


def _next_problem_id(detail_text: str) -> str:
    matches = [
        rows
        for actual, rows in parse_tables(detail_text)
        if actual == TASK_DETAIL_HEADERS["issues"]
    ]
    used = {
        int(match.group(1))
        for row in (matches[0] if len(matches) == 1 else [])
        if (match := re.fullmatch(r"PROB-([0-9]{3})", row.get("ID", "")))
    }
    for number in range(1, 1000):
        if number not in used:
            return f"PROB-{number:03d}"
    raise TaskManagementError("La tarea agotó el espacio de identificadores PROB-###.")


def _preview_hash(
    board: bytes,
    detail: bytes,
    manifest: bytes,
    payload: dict[str, Any],
) -> str:
    digest = hashlib.sha256()
    for value in (board, detail, manifest):
        digest.update(hashlib.sha256(value).digest())
    digest.update(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    )
    return digest.hexdigest()


def _require_verified_done_evidence(
    root: Path,
    manifest: dict[str, Any],
    row: dict[str, str],
    *,
    task_id: str,
    evidence_id: str,
    revision: str,
    build_id: str,
    artifact_digest: str,
    environment: str,
    gate_ids: list[str],
) -> None:
    """Reject a 1.3/1.4 done claim unless it matches recorded verification bytes."""

    verification = manifest.get("verification")
    if isinstance(verification, dict) and verification.get("status") == "verified-with-reservations":
        from variant_verification import completion_fields
        from project_variants import VariantError
        try:
            fields = completion_fields(root, manifest, task_id)
            if fields is not None:
                expected = {"evidence": evidence_id, "revision": revision, "build": build_id,
                            "artifact_digest": artifact_digest, "environment": environment, "gate": sorted(gate_ids)}
                if fields != expected:
                    raise VariantError("The closure request differs from current variant evidence")
                return
        except VariantError as exc:
            raise TaskManagementError(str(exc)) from exc
    if not isinstance(verification, dict) or verification.get("status") != "verified":
        raise TaskManagementError(
            "done en schema 1.5 exige una verificación canónica con status=verified."
        )
    if verification.get("increment") != row.get("Increment"):
        raise TaskManagementError("La verificación no pertenece al incremento de la tarea.")
    if task_id not in verification.get("task_ids", []):
        raise TaskManagementError(f"La verificación no incluye {task_id}.")
    if evidence_id not in verification.get("evidence_ids", []):
        raise TaskManagementError(f"La verificación no enlaza {evidence_id}.")
    comparisons = {
        "revision": (revision, verification.get("revision")),
        "build": (build_id, verification.get("build_id")),
        "environment": (environment, verification.get("environment")),
    }
    for label, (requested, recorded) in comparisons.items():
        if requested != recorded:
            raise TaskManagementError(
                f"El {label} declarado para done no coincide con la verificación."
            )
    if artifact_digest not in verification.get("artifact_digests", []):
        raise TaskManagementError(
            "El artifact-digest declarado para done no coincide con la verificación."
        )
    if not set(gate_ids) <= set(verification.get("gate_ids", [])):
        raise TaskManagementError(
            "Los gates declarados para done no coinciden con la verificación."
        )

    evidence_path = root / "docs" / "lks-sdd" / "evidence" / f"{evidence_id}.json"
    if evidence_path.is_symlink() or not evidence_path.is_file():
        raise TaskManagementError(f"No existe evidencia canónica regular para {evidence_id}.")
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TaskManagementError(
            f"No se puede validar la evidencia canónica {evidence_id}: {exc}"
        ) from exc
    if not isinstance(evidence, dict):
        raise TaskManagementError(f"La evidencia {evidence_id} no es un objeto JSON.")
    evidence_checks = [
        item for item in evidence.get("checks", []) if isinstance(item, dict)
    ]
    evidence_mismatches = []
    if evidence.get("evidence_id") != evidence_id:
        evidence_mismatches.append("evidence_id")
    if evidence.get("classification") != "verified":
        evidence_mismatches.append("classification")
    if evidence.get("increment") != row.get("Increment"):
        evidence_mismatches.append("increment")
    if task_id not in evidence.get("task_ids", []):
        evidence_mismatches.append("task_ids")
    if evidence.get("revision") != revision:
        evidence_mismatches.append("revision")
    if evidence.get("build_id") != build_id:
        evidence_mismatches.append("build_id")
    if artifact_digest not in evidence.get("artifact_digests", []):
        evidence_mismatches.append("artifact_digests")
    if evidence.get("environment") != environment:
        evidence_mismatches.append("environment")
    verification_execution_id = verification.get("execution_id")
    if verification_execution_id is not None and evidence.get(
        "execution_id"
    ) != verification_execution_id:
        evidence_mismatches.append("execution_id")
    for gate_id in gate_ids:
        outcomes = [
            item.get("status")
            for item in evidence_checks
            if item.get("gate_id") == gate_id
        ]
        if not outcomes or any(status != "passed" for status in outcomes):
            evidence_mismatches.append(f"gate:{gate_id}")
    if evidence_mismatches:
        raise TaskManagementError(
            f"{evidence_id} no demuestra done: "
            + ", ".join(sorted(set(evidence_mismatches)))
            + "."
        )

    execution_matches = [
        item
        for item in manifest.get("executions", [])
        if isinstance(item, dict)
        and task_id in item.get("task_ids", [])
        and evidence_id in item.get("evidence_ids", [])
        and (
            verification_execution_id is None
            or item.get("execution_id") == verification_execution_id
        )
    ]
    if not execution_matches:
        raise TaskManagementError(
            f"{evidence_id} no está enlazada a una EXEC-### que incluya {task_id}."
        )


def _transition(
    root: Path, manifest: dict[str, Any], args: argparse.Namespace
) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any]]:
    validated = validate_delivery_contract(root, manifest)
    if validated["errors"]:
        raise TaskManagementError(
            "El contrato actual no es válido: " + "; ".join(validated["errors"])
        )
    row = validated["tasks"].get(args.task)
    if row is None:
        raise TaskManagementError(f"No existe {args.task}.")
    planning_snapshot = (
        assess_planning(root, manifest, row["Increment"], release=row["Release"])
        if manifest.get("schema_version") in {"1.3", "1.4", "1.5"}
        else None
    )
    current = row["Workflow state"]
    if args.to_state not in TRANSITIONS.get(current, set()):
        raise TaskManagementError(
            f"Transición no permitida: {current} -> {args.to_state}."
        )
    if args.to_state in {"ready", "in-progress", "in-review"}:
        dependency_ids = re.findall(
            r"\bTASK-[0-9]{3}\b", row.get("Dependencies", "")
        )
        unresolved = [
            dependency
            for dependency in dependency_ids
            if validated["tasks"].get(dependency, {}).get("Workflow state")
            != "done"
        ]
        if unresolved:
            raise TaskManagementError(
                f"{args.task} no puede pasar a {args.to_state}: dependencias no done: "
                + ", ".join(sorted(set(unresolved)))
                + ". cancelled no equivale a resuelta."
            )
    if (
        manifest.get("schema_version") in {"1.3", "1.4", "1.5"}
        and args.to_state in {"ready", "in-progress", "in-review", "done"}
        and args.task not in planning_snapshot.get("tasks", {}).get(
            "executable", []
        )
    ):
        missing = next(
            (
                item.get("missing", [])
                for item in planning_snapshot.get("tasks", {}).get(
                    "incomplete", []
                )
                if item.get("task") == args.task
            ),
            [],
        )
        raise TaskManagementError(
            f"{args.task} no tiene una definición ejecutable"
            + (": " + ", ".join(missing) if missing else "")
            + "."
        )
    if (
        manifest.get("schema_version") in {"1.3", "1.4", "1.5"}
        and args.to_state in {"in-progress", "in-review", "done"}
    ):
        current_authorization = assess_authorization(
            manifest, planning_snapshot, [args.task]
        )
        if current_authorization.get("status") != "authorized":
            raise TaskManagementError(
                f"{args.task} no puede pasar a {args.to_state} sin una AUTH-### vigente para los fingerprints actuales."
            )
        execution_matches = [
            item
            for item in manifest.get("executions", [])
            if isinstance(item, dict)
            and args.task in item.get("task_ids", [])
            and item.get("status")
            in {"in-progress", "in-review", "paused", "blocked"}
        ]
        if len(execution_matches) != 1:
            raise TaskManagementError(
                f"{args.task} necesita una única EXEC-### activa; inicie tareas ready mediante implement apply o reconcilie la ejecución."
            )
        if execution_matches[0].get("authorization_id") != current_authorization.get(
            "authorization_id"
        ):
            raise TaskManagementError(
                "La ejecución activa no está ligada a la autorización vigente."
            )
    if (
        manifest.get("schema_version") in {"1.4", "1.5"}
        and current == "ready"
        and args.to_state == "in-progress"
    ):
        tracking = assess_tracking(root, manifest, [args.task])
        if tracking.get("blockers"):
            raise TaskManagementError(
                "La política de tracking bloquea el inicio: "
                + "; ".join(tracking["blockers"])
            )
    if current == "done" and args.to_state == "backlog":
        if args.classification == "new-scope":
            raise TaskManagementError(
                "El alcance nuevo debe crear otra TASK; no reabra una tarea terminada."
            )
        if args.classification != "original-contract-failure" or not re.fullmatch(
            r"PCH-[0-9]{3}", args.change_id or ""
        ):
            raise TaskManagementError(
                "Reabrir done exige --classification original-contract-failure y --change-id PCH-###."
            )
        if manifest.get("schema_version") not in {"1.3", "1.4", "1.5"}:
            raise TaskManagementError("La reapertura controlada requiere schema 1.5.")
        planning = assess_planning(root, manifest, row["Increment"], release=row["Release"])
        matching_changes = [
            item
            for item in planning.get("change_impact", {}).get(
                "applicable_confirmed_changes", []
            )
            if item.get("id") == args.change_id
            and item.get("classification") == "original-contract-failure"
            and args.task in item.get("affected_tasks", [])
        ]
        if len(matching_changes) != 1:
            raise TaskManagementError(
                f"{args.change_id} no confirma un fallo del contrato original que afecte a {args.task}."
            )
        if any(
            item.get("state") == "authorized"
            and args.task in item.get("task_ids", [])
            for item in manifest.get("authorizations", [])
            if isinstance(item, dict)
        ):
            raise TaskManagementError(
                "Invalide primero en Markdown e índice las autorizaciones que incluyen la tarea."
            )
    try:
        transition_date = date.fromisoformat(args.date).isoformat()
    except ValueError as exc:
        raise TaskManagementError("--date debe usar AAAA-MM-DD.") from exc
    reason = _safe_cell("--reason", args.reason, required=True)
    actor = _safe_cell("--actor", args.actor, required=True)
    blocker_text = _safe_cell("--blocker", args.blocker)
    branch = _safe_cell("--branch", args.branch)
    revision_start = _safe_cell("--revision-start", args.revision_start)
    revision = _safe_cell("--revision", args.revision)
    build = _safe_cell("--build", args.build)
    environment = _safe_cell("--environment", args.environment)
    evidence = _safe_cell("--evidence", args.evidence)
    current_progress = int(row["Progress"])
    health, progress = _default_tracking(
        args.to_state,
        current_progress,
        row.get("Health", "unknown"),
        schema_version=str(manifest.get("schema_version")),
    )
    if args.health is not None:
        health = args.health
    if args.progress is not None:
        progress = args.progress
    if health not in TASK_HEALTH:
        raise TaskManagementError(f"Health inválido: {health}.")
    if not 0 <= progress <= 100:
        raise TaskManagementError("--progress debe estar entre 0 y 100.")
    if args.to_state == "blocked" and not blocker_text:
        raise TaskManagementError("blocked requiere --blocker.")
    if args.to_state == "done":
        auto_verified_deliverables = bool(
            getattr(args, "auto_verified_deliverables", False)
        )
        if not (
            evidence
            and revision
            and build
            and args.artifact_digest
            and environment
            and args.gate
        ):
            raise TaskManagementError(
                "done requiere evidence, revision, build, artifact-digest, "
                "environment y al menos un gate."
            )
        if not re.fullmatch(r"EVID-[0-9]{3}", evidence):
            raise TaskManagementError("--evidence debe usar EVID-###.")
        if not REVISION_RE.fullmatch(revision):
            raise TaskManagementError(
                "--revision debe ser un commit hexadecimal de 40-64 caracteres "
                "o workspace-sha256:<64 hex>."
            )
        if not re.fullmatch(r"(?:ENV-[0-9]{3}|not-applicable)", environment):
            raise TaskManagementError(
                "--environment debe usar ENV-### o not-applicable."
            )
        invalid_gates = [
            gate for gate in args.gate
            if not re.fullmatch(r"GATE-[A-Z0-9-]{3,80}", gate)
        ]
        if invalid_gates:
            raise TaskManagementError(f"Gate inválido: {invalid_gates[0]}.")
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", args.artifact_digest):
            raise TaskManagementError(
                "--artifact-digest debe usar sha256:<64 hex>."
            )
        detail_contract = validated.get("task_details", {}).get(args.task, {})
        definition_rows = detail_contract.get("definition", [])
        required_gates = set(
            re.findall(
                r"\bGATE-[A-Z0-9-]{3,80}\b",
                definition_rows[0].get("Technical gates", "")
                if len(definition_rows) == 1
                else "",
            )
        )
        missing_gates = sorted(required_gates - set(args.gate))
        if missing_gates:
            raise TaskManagementError(
                "done exige todos los gates técnicos de la tarea: "
                + ", ".join(missing_gates)
                + "."
            )
        if manifest.get("schema_version") in {"1.3", "1.4", "1.5"}:
            _require_verified_done_evidence(
                root,
                manifest,
                row,
                task_id=args.task,
                evidence_id=evidence,
                revision=revision,
                build_id=build,
                artifact_digest=args.artifact_digest,
                environment=environment,
                gate_ids=args.gate,
            )
        deliverables = detail_contract.get("deliverables", [])
        unfinished_deliverables = [
            item.get("Deliverable", "unnamed deliverable")
            for item in deliverables
            if item.get("State") not in {"done", "verified"}
            or not _observed_evidence(item.get("Evidence"))
        ]
        if not deliverables or (
            unfinished_deliverables and not auto_verified_deliverables
        ):
            raise TaskManagementError(
                "done exige todos los entregables terminados y con evidencia: "
                + ", ".join(unfinished_deliverables or ["no deliverables declared"])
                + "."
            )
        open_issues = [
            item.get("ID", "PROB")
            for item in detail_contract.get("problems", detail_contract.get("issues", []))
            if item.get("State") == "active"
        ]
        if open_issues:
            raise TaskManagementError(
                "done no admite problemas abiertos: "
                + ", ".join(open_issues)
                + "."
            )
    blocker = blocker_text if args.to_state == "blocked" else "none"
    board_path = root / _artifact_path(manifest, "ART-TASKS")
    detail_path = (
        root
        / "docs"
        / "lks-sdd"
        / "04-delivery"
        / "tasks"
        / f"{args.task}.md"
    )
    board_original = board_path.read_bytes()
    detail_original = detail_path.read_bytes()
    board_text = board_original.decode("utf-8")
    detail_text = detail_original.decode("utf-8")
    board_text = _replace_table_row(
        board_text,
        TASK_HEADERS,
        args.task,
        {
            "Workflow state": args.to_state,
            "Health": health,
            "Progress": str(progress),
            "Blockers": blocker,
            "Updated": transition_date,
        },
    )
    execution_headers = TASK_DETAIL_HEADERS["execution"]
    detail_text = _replace_table_row(
        detail_text,
        execution_headers,
        current,
        {
            "Workflow state": args.to_state,
            "Health": health,
            "Progress": str(progress),
            "Branch": branch or _single_detail_row(
                detail_text, execution_headers
            )["Branch"],
            "Revision start": (
                revision_start
                or _single_detail_row(detail_text, execution_headers)[
                    "Revision start"
                ]
            ),
            "Revision verified": (
                revision
                or _single_detail_row(detail_text, execution_headers)[
                    "Revision verified"
                ]
            ),
            "Build": (
                build
                or _single_detail_row(detail_text, execution_headers)["Build"]
            ),
            "Environment": (
                environment
                or _single_detail_row(detail_text, execution_headers)[
                    "Environment"
                ]
            ),
            "Updated": transition_date,
        },
    )
    if args.to_state == "done" and bool(
        getattr(args, "auto_verified_deliverables", False)
    ):
        for deliverable in validated.get("task_details", {}).get(
            args.task, {}
        ).get("deliverables", []):
            detail_text = _replace_table_row(
                detail_text,
                TASK_DETAIL_HEADERS_V13["deliverables"],
                deliverable["Deliverable"],
                {"State": "verified", "Evidence": evidence},
            )
    history = TASK_DETAIL_HEADERS["history"]
    detail_text = _append_table_row(
        detail_text,
        history,
        [
            transition_date,
            current,
            args.to_state,
            (
                f"{reason} ({args.change_id}: original-contract-failure)"
                if current == "done" and args.to_state == "backlog"
                else reason
            ),
            actor,
            evidence or "not-applicable",
        ],
    )
    if args.to_state == "blocked":
        detail_text = _append_table_row(
            detail_text,
            TASK_DETAIL_HEADERS["issues"],
            [
                _next_problem_id(detail_text),
                "active",
                blocker_text,
                reason,
                actor,
                "Resolve blocker and record evidence",
                evidence or "pending",
            ],
        )
    if args.to_state == "done":
        definition = _single_detail_row(
            detail_text, TASK_DETAIL_HEADERS["definition"]
        )
        acceptance_ids = re.findall(
            r"\bAC-[0-9]{3}\b", definition.get("Acceptance", "")
        ) or [definition.get("Acceptance", "confirmed acceptance")]
        test_ids = []
        if manifest.get("schema_version") in {"1.3", "1.4", "1.5"}:
            plan = _single_detail_row(
                detail_text, TASK_DETAIL_HEADERS_V13["plan"]
            )
            test_ids = re.findall(
                r"\bTEST-[0-9]{3}\b", plan.get("Tests", "")
            )
        for acceptance in list(dict.fromkeys([*acceptance_ids, *test_ids])):
            detail_text = _append_table_row(
                detail_text,
                TASK_DETAIL_HEADERS["validation"],
                [
                    acceptance,
                    ", ".join(args.gate),
                    "passed",
                    evidence,
                    revision,
                    args.artifact_digest,
                    environment,
                ],
            )
    if (
        manifest.get("schema_version") in {"1.3", "1.4", "1.5"}
        and current == "done"
        and args.to_state == "backlog"
    ):
        continuity = TASK_DETAIL_HEADERS_V13["continuity"]
        detail_text = _replace_table_row(
            detail_text,
            continuity,
            _single_detail_row(detail_text, continuity)["Definition status"],
            {
                "Definition status": "stale",
                "Authorization": "none",
                "Authorization scope": "none",
                "Next safe action": "reconcile original contract failure and replan",
            },
        )
    board_text = _replace_frontmatter_date(board_text, transition_date)
    detail_text = _replace_frontmatter_date(detail_text, transition_date)
    updated_manifest = json.loads(json.dumps(manifest))
    prospective_states = {
        task_id: (
            args.to_state
            if task_id == args.task
            else task_row.get("Workflow state")
        )
        for task_id, task_row in validated["tasks"].items()
    }
    if args.to_state in {"in-progress", "in-review", "blocked"}:
        updated_manifest["active_task"] = args.task
    elif updated_manifest.get("active_task") == args.task:
        updated_manifest["active_task"] = None
    if manifest.get("schema_version") in {"1.3", "1.4", "1.5"}:
        active_tasks = set(updated_manifest.get("active_tasks", []))
        if args.to_state in {"in-progress", "in-review", "blocked"}:
            active_tasks.add(args.task)
        else:
            active_tasks.discard(args.task)
        updated_manifest["active_tasks"] = sorted(active_tasks)
        if len(active_tasks) != 1:
            updated_manifest["active_task"] = None
        for execution in updated_manifest.get("executions", []):
            if not isinstance(execution, dict) or args.task not in execution.get(
                "task_ids", []
            ):
                continue
            # EXEC records are historical once terminal. Reopening a task must
            # not rewrite a completed/cancelled execution; a subsequent
            # authorized implementation creates a new EXEC instead.
            if execution.get("status") in {"completed", "cancelled"}:
                continue
            states = {
                prospective_states.get(task_id, "cancelled")
                for task_id in execution.get("task_ids", [])
            }
            execution["status"] = (
                "blocked"
                if "blocked" in states
                else "in-progress"
                if "in-progress" in states
                else "in-review"
                if "in-review" in states
                else "completed"
                if states and states <= {"done"}
                else "cancelled"
                if states and states <= {"cancelled"}
                else "paused"
            )
        implementation = updated_manifest.get("implementation")
        if isinstance(implementation, dict) and args.task in implementation.get(
            "task_ids", []
        ):
            implementation_states = {
                prospective_states.get(task_id, "cancelled")
                for task_id in implementation.get("task_ids", [])
            }
            implementation["status"] = (
                "blocked"
                if implementation_states & {"blocked", "cancelled"}
                else "in-progress"
                if implementation_states
                - {"in-review", "done"}
                else "completed"
            )
        if current == "done" and args.to_state == "backlog":
            updated_manifest["planning"].update(
                {
                    "specification_fingerprint": None,
                    "planning_fingerprint": None,
                    "confirmed_by_role": None,
                    "confirmed_on": None,
                    "last_change": args.change_id,
                }
            )
            if (
                isinstance(implementation, dict)
                and args.task in implementation.get("task_ids", [])
            ):
                implementation["status"] = "blocked"
            verification = updated_manifest.get("verification")
            if (
                isinstance(verification, dict)
                and args.task in verification.get("task_ids", [])
            ):
                verification["status"] = "not-verified"
                verification["limitations"] = list(
                    dict.fromkeys(
                        [
                            *verification.get("limitations", []),
                            f"Invalidated for current planning by {args.change_id}; prior evidence remains historical.",
                        ]
                    )
                )
    release_id = row.get("Release")
    release_states = {
        task_id: prospective_states[task_id]
        for task_id, task_row in validated["tasks"].items()
        if task_row.get("Release") == release_id
    }
    release_complete = bool(release_states) and all(
        state == "done" for state in release_states.values()
    )
    completed_tasks = sorted(
        task_id for task_id, state in prospective_states.items() if state == "done"
    )
    in_progress_tasks = sorted(
        task_id
        for task_id, state in prospective_states.items()
        if state in {"in-progress", "in-review"}
    )
    pending_tasks = sorted(
        task_id
        for task_id, state in prospective_states.items()
        if state in {"backlog", "ready"}
    )
    blocked_tasks = sorted(
        task_id
        for task_id, state in prospective_states.items()
        if state in {"blocked", "cancelled"}
    )
    planning_status = (
        planning_snapshot.get("status") if planning_snapshot is not None else "legacy"
    )
    planning_integrity = (
        planning_snapshot.get("integrity")
        if planning_snapshot is not None
        else "not-assessed"
    )
    planning_pending: list[str] = []
    if planning_snapshot is not None and (
        planning_status != "complete" or planning_integrity != "valid"
    ):
        planning_pending.append(
            f"Planificación de {planning_snapshot['target']['id']}: "
            f"{planning_status}/{planning_integrity}."
        )
        unassigned = planning_snapshot.get("coverage", {}).get(
            "unassigned_items", []
        )
        if unassigned:
            planning_pending.append(
                "Contrato sin tarea primaria: " + ", ".join(unassigned) + "."
            )
    release_plan_complete = (
        planning_snapshot is None
        or (planning_status == "complete" and planning_integrity == "valid")
    )
    if release_complete and not release_plan_complete:
        planning_phase = (
            "invalid" if planning_integrity == "invalid" else planning_status
        )
        where_we_are = f"release-tasks-complete-planning-{planning_phase}"
        next_step = (
            "Completar o reconciliar la planificación y cubrir el contrato pendiente "
            "antes de presentar, verificar conjuntamente o promover la release completa."
        )
        human_decision = (
            "Confirmar la descomposición o replanificación restante; la terminación de "
            "las tareas registradas no autoriza la release completa."
        )
    elif release_complete:
        where_we_are = "release-tasks-complete"
        next_step = "Crear o actualizar el checkpoint y ejecutar la verificación conjunta de la release antes de promoverla."
        human_decision = "Autorizar la verificación o promoción solo después de revisar evidencia y gates reales."
    elif args.to_state == "blocked":
        where_we_are = "task-blocked"
        next_step = "Crear un checkpoint, resolver o replanificar el bloqueo y continuar solo tareas independientes ready."
        human_decision = "Decidir cómo resolver, sustituir o aceptar el bloqueo sin fingir progreso."
    elif args.to_state == "done":
        where_we_are = "task-done"
        next_step = "Crear un checkpoint, comprobar dependencias desbloqueadas y seleccionar la siguiente tarea segura."
        human_decision = "Ninguna nueva salvo que la siguiente porción o la verificación requieran autorización."
    elif args.to_state == "in-review":
        where_we_are = "task-in-review"
        next_step = "Revisar aceptación, gates, revisión y artefacto antes de permitir done."
        human_decision = "Aceptar o rechazar la revisión con evidencia concreta."
    else:
        where_we_are = f"task-{args.to_state}"
        next_step = "Continuar la definición autorizada y actualizar el checkpoint antes de cualquier pausa."
        human_decision = "Ninguna nueva mientras alcance, dependencias y autorización sigan vigentes."
    payload = {
        "task": args.task,
        "from": current,
        "to": args.to_state,
        "health": health,
        "progress": progress,
        "reason": reason,
        "actor": actor,
        "date": transition_date,
        "blocker": blocker,
        "evidence": evidence,
        "planning_status": planning_status,
        "planning_integrity": planning_integrity,
        "checkpoint_required": manifest.get("schema_version") in {"1.3", "1.4", "1.5"},
        "next_command": (
            "continuity checkpoint"
            if manifest.get("schema_version") in {"1.3", "1.4", "1.5"}
            else None
        ),
        "transition_summary": {
            "where_we_are": where_we_are,
            "completed": completed_tasks,
            "in_progress": in_progress_tasks,
            "pending": pending_tasks + planning_pending,
            "blocked": blocked_tasks,
            "next_step": next_step,
            "human_decision": human_decision,
        },
    }
    return (
        board_text.encode("utf-8"),
        detail_text.encode("utf-8"),
        updated_manifest,
        payload,
    )


def _apply_atomic(
    paths: list[Path],
    originals: list[bytes],
    replacements: list[bytes],
) -> None:
    temporary: list[Path] = []
    replaced = 0
    try:
        for path, content in zip(paths, replacements, strict=True):
            temp = path.with_name(path.name + ".lks-sdd-task.tmp")
            with temp.open("xb") as stream:
                stream.write(content)
            temporary.append(temp)
        for path, original in zip(paths, originals, strict=True):
            if path.read_bytes() != original:
                raise TaskManagementError(
                    f"{path.name} cambió después del preview."
                )
        for path, temp in zip(paths, temporary, strict=True):
            os.replace(temp, path)
            replaced += 1
    except (OSError, TaskManagementError):
        for index in range(replaced):
            paths[index].write_bytes(originals[index])
        for temp in temporary[replaced:]:
            try:
                temp.unlink()
            except OSError:
                pass
        raise


def _print_board(board: dict[str, Any]) -> None:
    summary = board["summary"]
    print(
        f"Tareas: {summary['total']} · bloqueadas: "
        f"{len(summary['blocked'])}"
    )
    for plan_id, rows in board["plans"].items():
        print(f"\n{plan_id}")
        for row in rows:
            state = row["Workflow state"]
            print(
                f" {SYMBOLS.get(state, '?')} {row['task_id']} "
                f"{row['Title']} · {state} · definición {row.get('definition_status', 'legacy')} · "
                f"{row['Health']} · {row['Release']} · checkpoint {row.get('checkpoint', 'none')}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("board", "validate"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--json", action="store_true", dest="as_json")
    transition = subparsers.add_parser("transition")
    transition.add_argument("--task", required=True)
    transition.add_argument("--to", required=True, choices=sorted(TRANSITIONS), dest="to_state")
    transition.add_argument("--reason", required=True)
    transition.add_argument("--actor", required=True)
    transition.add_argument("--date", required=True)
    transition.add_argument("--health", choices=sorted(TASK_HEALTH))
    transition.add_argument("--progress", type=int)
    transition.add_argument("--blocker")
    transition.add_argument("--branch")
    transition.add_argument("--revision-start")
    transition.add_argument("--revision")
    transition.add_argument("--build")
    transition.add_argument("--environment")
    transition.add_argument("--artifact-digest")
    transition.add_argument("--gate", action="append")
    transition.add_argument("--evidence")
    transition.add_argument(
        "--classification", choices=("original-contract-failure", "new-scope")
    )
    transition.add_argument("--change-id")
    mode = transition.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--apply", action="store_true")
    transition.add_argument("--authorize", action="store_true")
    transition.add_argument("--preview-hash")
    transition.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    try:
        manifest_path, manifest, manifest_original = _load_manifest(root)
        if args.command in {"board", "validate"}:
            result = task_board(root, manifest)
            if args.as_json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.command == "board":
                _print_board(result)
                for error in result["errors"]:
                    print(f"ERROR: {error}")
            else:
                print("VALID" if result["valid"] else "INVALID")
                for error in result["errors"]:
                    print(f"ERROR: {error}")
            return 0 if result["valid"] else 2

        board_path = root / _artifact_path(manifest, "ART-TASKS")
        if not re.fullmatch(r"TASK-[0-9]{3}", args.task):
            raise TaskManagementError("--task debe usar TASK-###.")
        detail_path = (
            root / "docs/lks-sdd/04-delivery/tasks" / f"{args.task}.md"
        )
        board_original = board_path.read_bytes()
        detail_original = detail_path.read_bytes()
        board_new, detail_new, manifest_new, payload = _transition(
            root, manifest, args
        )
        manifest_new_bytes = (
            json.dumps(manifest_new, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        preview_hash = _preview_hash(
            board_original, detail_original, manifest_original, payload
        )
        result = {
            "status": "preview" if args.preview else "applied",
            "changed": False,
            "preview_hash": preview_hash,
            **payload,
        }
        if args.preview:
            result["transition_summary"] = {
                "where_we_are": "task-transition-preview",
                "completed": [],
                "in_progress": [],
                "pending": [
                    f"Transición propuesta {payload['task']}: {payload['from']} → {payload['to']}; todavía no aplicada."
                ],
                "blocked": [],
                "next_step": "Revisar estado, evidencia, dependencias y checkpoint antes de aplicar.",
                "human_decision": "Aplicar o rechazar la transición propuesta.",
            }
            if args.as_json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"PREVIEW {payload['from']} -> {payload['to']}")
                print(f"preview_hash={preview_hash}")
            return 0
        if not args.authorize or args.preview_hash != preview_hash:
            raise TaskManagementError(
                "Aplicar requiere --authorize y el preview hash vigente."
            )
        _apply_atomic(
            [board_path, detail_path, manifest_path],
            [board_original, detail_original, manifest_original],
            [board_new, detail_new, manifest_new_bytes],
        )
        final = validate_delivery_contract(root, manifest_new)
        report, _, _ = validate_project(root)
        if final["errors"] or not report.valid:
            _apply_atomic(
                [board_path, detail_path, manifest_path],
                [board_new, detail_new, manifest_new_bytes],
                [board_original, detail_original, manifest_original],
            )
            raise TaskManagementError(
                "La transición se revirtió: "
                + "; ".join(list(final["errors"]) + list(report.errors))
            )
        result.update({"status": "applied", "changed": True})
        if args.as_json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"APPLIED {payload['from']} -> {payload['to']}")
        return 0
    except (OSError, TaskManagementError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
