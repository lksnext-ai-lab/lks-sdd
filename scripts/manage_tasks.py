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
    parse_tables,
    task_board,
    validate_delivery_contract,
)


TRANSITIONS = {
    "backlog": {"ready", "blocked", "cancelled"},
    "ready": {"in-progress", "blocked", "cancelled"},
    "in-progress": {"in-review", "blocked", "cancelled"},
    "in-review": {"in-progress", "done", "blocked", "cancelled"},
    "blocked": {"backlog", "ready", "in-progress", "cancelled"},
    "done": set(),
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
    if not isinstance(value, dict) or value.get("schema_version") != "1.2":
        raise TaskManagementError("La gestión PLAN/TASK requiere schema 1.2.")
    return path, value, original


def _artifact_path(manifest: dict[str, Any], artifact_id: str) -> str:
    for item in manifest.get("artifacts", []):
        if item.get("id") == artifact_id:
            return str(item["path"])
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
    target: str, current_progress: int
) -> tuple[str, int]:
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
    current = row["Workflow state"]
    if args.to_state not in TRANSITIONS.get(current, set()):
        raise TaskManagementError(
            f"Transición no permitida: {current} -> {args.to_state}."
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
    health, progress = _default_tracking(args.to_state, current_progress)
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
    history = TASK_DETAIL_HEADERS["history"]
    detail_text = _append_table_row(
        detail_text,
        history,
        [
            transition_date,
            current,
            args.to_state,
            reason,
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
                "open",
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
        for acceptance in acceptance_ids:
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
    board_text = _replace_frontmatter_date(board_text, transition_date)
    detail_text = _replace_frontmatter_date(detail_text, transition_date)
    updated_manifest = json.loads(json.dumps(manifest))
    if args.to_state in {"in-progress", "in-review", "blocked"}:
        updated_manifest["active_task"] = args.task
    elif updated_manifest.get("active_task") == args.task:
        updated_manifest["active_task"] = None
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
                f"{row['Title']} · {state} · {row['Progress']}% · "
                f"{row['Health']} · {row['Release']}"
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
        if final["errors"]:
            _apply_atomic(
                [board_path, detail_path, manifest_path],
                [board_new, detail_new, manifest_new_bytes],
                [board_original, detail_original, manifest_original],
            )
            raise TaskManagementError(
                "La transición se revirtió: " + "; ".join(final["errors"])
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
