#!/usr/bin/env python3
"""High-level, human-facing façade for the normal lifecycle of one task."""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from experience_engine import ExperienceError, load_status, management_json, render_management
from delivery_engine import repository_revision, validate_delivery_contract
from manage_continuity import (
    ContinuityError,
    _next_checkpoint_id,
    _render_checkpoint,
)
from manage_tasks import TaskManagementError, _transition
from planning_engine import assess_authorization, assess_planning
from validate_project import validate_project


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = PLUGIN_ROOT / "scripts/lks_sdd.py"
IMPLEMENT_SCRIPT_ROOT = PLUGIN_ROOT / "skills/lks-sdd-implement/scripts"
if str(IMPLEMENT_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(IMPLEMENT_SCRIPT_ROOT))

from prepare_increment import PreparationError, prepare as prepare_increment  # noqa: E402


def _run(command: list[str]) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, str(ENTRYPOINT), *command, "--json"],
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ExperienceError(
            f"La operación interna no devolvió JSON válido: {completed.stdout or completed.stderr}"
        ) from exc
    return completed.returncode, value


def _management(root: Path, task: str | None) -> dict[str, Any]:
    return management_json(load_status(root, task_id=task))


def _next_evidence_id(root: Path) -> str:
    values = []
    for path in (root / "docs/lks-sdd/evidence").glob("EVID-*.json"):
        try:
            values.append(int(path.stem.split("-")[1]))
        except (IndexError, ValueError):
            continue
    return f"EVID-{(max(values, default=0) + 1):03d}"


def _verification_arguments(root: Path, task: str, supplied: list[str]) -> list[str]:
    arguments = list(supplied)
    if arguments and arguments[0] == "--":
        arguments.pop(0)
    status = load_status(root, task_id=task)
    if "--task" not in arguments:
        arguments.extend(["--task", task])
    if "--increment" not in arguments:
        increment = status["audit"]["manifest"].get("active_increment")
        if not isinstance(increment, str):
            raise ExperienceError("No se puede derivar el incremento activo para verificar.")
        arguments.extend(["--increment", increment])
    if "--plan" not in arguments and "--execute" not in arguments:
        if status["current_task"]["human_decision"] != "Ninguna":
            raise ExperienceError("La verificación necesita una decisión humana material previa.")
        arguments.extend(["--execute", "--authorize"])
    if "--record-evidence" not in arguments and "--plan" not in arguments:
        arguments.extend(["--record-evidence", _next_evidence_id(root)])
    if "--reuse-evidence" not in arguments and "--plan" not in arguments:
        verification = status["audit"]["manifest"].get("verification", {})
        for evidence_id in reversed(verification.get("evidence_ids", [])):
            path = root / "docs/lks-sdd/evidence" / f"{evidence_id}.json"
            try:
                evidence = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if isinstance(evidence, dict) and isinstance(evidence.get("verification_subject"), dict):
                arguments.extend(["--reuse-evidence", evidence_id])
                break
    return arguments


def _table_update(
    lines: list[str],
    required_headers: set[str],
    predicate: Any,
    updates: dict[str, str],
) -> bool:
    for index, line in enumerate(lines[:-1]):
        if not line.strip().startswith("|"):
            continue
        headers = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not required_headers <= set(headers):
            continue
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
            cells = [cell.strip() for cell in lines[cursor].strip().strip("|").split("|")]
            if len(cells) == len(headers):
                row = dict(zip(headers, cells, strict=True))
                if predicate(row):
                    for key, value in updates.items():
                        cells[headers.index(key)] = value
                    lines[cursor] = "| " + " | ".join(cells) + " |"
                    return True
            cursor += 1
    return False


def _append_history(lines: list[str], values: list[str]) -> bool:
    expected = {"Date", "From", "To", "Reason", "Actor or authority", "Evidence"}
    for index, line in enumerate(lines[:-1]):
        headers = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if set(headers) != expected or len(headers) != len(values):
            continue
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
            cursor += 1
        lines.insert(cursor, "| " + " | ".join(values) + " |")
        return True
    return False


def _apply_project_transaction(
    root: Path,
    replacements: dict[Path, tuple[bytes | None, bytes]],
) -> None:
    """Apply one fail-closed local transaction and roll back every member."""

    temporaries: dict[Path, Path] = {}
    replaced: list[Path] = []
    created_parent: set[Path] = set()
    try:
        for path, (original, content) in replacements.items():
            if not path.parent.exists():
                path.parent.mkdir(parents=True)
                created_parent.add(path.parent)
            temporary = path.with_name(path.name + ".lks-sdd-work.tmp")
            with temporary.open("xb") as stream:
                stream.write(content)
            temporaries[path] = temporary
            if original is None:
                if path.exists():
                    raise ExperienceError(f"{path.name} apareció durante la operación.")
            elif path.read_bytes() != original:
                raise ExperienceError(f"{path.name} cambió durante la operación.")
        for path, temporary in temporaries.items():
            os.replace(temporary, path)
            replaced.append(path)
        report, _, _ = validate_project(root)
        if not report.valid:
            raise ExperienceError(
                "La operación compuesta no supera validate-project: "
                + "; ".join(report.errors[:8])
            )
    except (OSError, ExperienceError):
        for temporary in temporaries.values():
            if temporary.exists():
                try:
                    temporary.unlink()
                except OSError:
                    pass
        for path in reversed(replaced):
            original = replacements[path][0]
            if original is None:
                try:
                    path.unlink()
                except OSError:
                    pass
            else:
                path.write_bytes(original)
        for parent in sorted(created_parent, key=lambda item: len(item.parts), reverse=True):
            try:
                parent.rmdir()
            except OSError:
                pass
        raise


def _compose_checkpoint_transaction(
    root: Path,
    task: str,
    target_state: str,
    actor: str,
    next_action: str,
    *,
    board_new: bytes,
    detail_new: bytes,
    manifest_new: dict[str, Any],
    completed: str | None = None,
    blocked: str | None = None,
    execution_id: str | None = None,
) -> str:
    """Combine task state, problem/index bookkeeping and one useful checkpoint."""

    manifest_path = root / ".lks-sdd/project.json"
    board_path = root / "docs/lks-sdd/04-delivery/tasks.md"
    detail_path = root / f"docs/lks-sdd/04-delivery/tasks/{task}.md"
    manifest_original = manifest_path.read_bytes()
    board_original = board_path.read_bytes()
    detail_original = detail_path.read_bytes()
    current_manifest = json.loads(manifest_original.decode("utf-8"))
    current_delivery = validate_delivery_contract(root, current_manifest)
    if current_delivery.get("errors"):
        raise ExperienceError(
            "El contrato de tareas previo no es válido: "
            + "; ".join(current_delivery["errors"][:5])
        )
    projected_delivery = copy.deepcopy(current_delivery)
    projected_delivery["tasks"][task]["Workflow state"] = (
        "done" if target_state == "completed" else target_state
    )
    row = projected_delivery["tasks"][task]
    planning = assess_planning(
        root,
        current_manifest,
        row["Increment"],
        release=row["Release"],
    )
    authorization = assess_authorization(current_manifest, planning, [task])
    if authorization.get("status") != "authorized":
        raise ExperienceError("La tarea ya no tiene una autorización exacta vigente.")
    executions = [
        item
        for item in manifest_new.get("executions", [])
        if isinstance(item, dict) and task in item.get("task_ids", [])
        and item.get("authorization_id") == authorization.get("authorization_id")
        and (execution_id is None or item.get("execution_id") == execution_id)
    ]
    if len(executions) != 1:
        raise ExperienceError("La tarea necesita una única ejecución autorizada.")
    execution = executions[0]
    revision = repository_revision(root)
    checkpoint_id = _next_checkpoint_id(root)
    checkpoint_args = argparse.Namespace(
        date=date.today().isoformat(),
        owner_role=actor,
        state=target_state,
        completed=completed,
        partial=None,
        pending=None,
        blocked=blocked,
        next_action=next_action,
        independent_task=None,
        changed_path=None,
    )
    try:
        checkpoint, changed_paths, task_replacements = _render_checkpoint(
            root,
            manifest_new,
            execution,
            checkpoint_id,
            checkpoint_args,
            planning,
            authorization,
            revision,
            task_source_overrides={
                detail_path.relative_to(root).as_posix(): detail_new,
            },
            projected_delivery=projected_delivery,
            extra_replacement_bytes={
                board_path.relative_to(root).as_posix(): board_new,
                manifest_path.relative_to(root).as_posix(): json.dumps(
                    manifest_new, sort_keys=True, ensure_ascii=False
                ).encode("utf-8"),
            },
        )
    except ContinuityError as exc:
        raise ExperienceError(str(exc)) from exc
    final_detail = next(
        replacement
        for path, _, replacement in task_replacements
        if path == detail_path
    )
    execution["status"] = target_state
    execution["last_observed_revision"] = revision["revision"]
    execution["latest_checkpoint"] = (
        f"docs/lks-sdd/04-delivery/checkpoints/{checkpoint_id}.md"
    )
    execution["changed_paths"] = sorted(
        set(execution.get("changed_paths", [])) | set(changed_paths)
    )
    manifest_new_bytes = (
        json.dumps(manifest_new, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    checkpoint_path = (
        root / f"docs/lks-sdd/04-delivery/checkpoints/{checkpoint_id}.md"
    )
    _apply_project_transaction(
        root,
        {
            board_path: (board_original, board_new),
            detail_path: (detail_original, final_detail),
            manifest_path: (manifest_original, manifest_new_bytes),
            checkpoint_path: (None, checkpoint),
        },
    )
    return checkpoint_id


def _completion_fields(root: Path, status: dict[str, Any]) -> dict[str, Any]:
    verification = status["audit"].get("verification", {})
    if verification.get("status") != "verified":
        raise ExperienceError(
            "work complete requiere una verificación superada y evidencia canónica."
        )
    evidence_ids = verification.get("evidence_ids", [])
    artifact_digests = verification.get("artifact_digests", [])
    gate_ids = verification.get("gate_ids", [])
    if not evidence_ids or not artifact_digests or not gate_ids:
        raise ExperienceError(
            "La verificación no contiene evidencia, artefacto y gates suficientes para cerrar."
        )
    evidence_id = str(evidence_ids[-1])
    evidence_path = root / f"docs/lks-sdd/evidence/{evidence_id}.json"
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExperienceError(
            f"No se puede leer la evidencia de cierre {evidence_id}: {exc}"
        ) from exc
    if not isinstance(evidence, dict) or evidence.get("classification") != "verified":
        raise ExperienceError(f"{evidence_id} no es evidencia verificada utilizable.")
    return {
        "evidence": evidence_id,
        "revision": str(verification.get("revision", "")),
        "build": str(verification.get("build_id", "")),
        "artifact_digest": str(artifact_digests[0]),
        "environment": str(verification.get("environment", "")),
        "gate": list(gate_ids),
    }


def _resolve_problem(
    root: Path,
    task: str,
    problem: str,
    resolution: str,
    cause: str,
    evidence: str,
    actor: str,
) -> tuple[int, dict[str, Any]]:
    if not cause.strip() or not evidence.strip() or evidence.strip().casefold() in {"none", "pending", "not-run"}:
        raise ExperienceError("Resolver un problema requiere causa y evidencia concreta.")
    status = load_status(root, task_id=task)
    relative = status["developer"]["files"][0]
    detail_path = root / relative
    board_path = root / "docs/lks-sdd/04-delivery/tasks.md"
    detail_original = detail_path.read_bytes()
    board_original = board_path.read_bytes()
    detail_lines = detail_original.decode("utf-8").splitlines()
    board_lines = board_original.decode("utf-8").splitlines()
    active_states = {"active"}
    changed_problem = _table_update(
        detail_lines,
        {"ID", "State", "Description", "Evidence"},
        lambda row: row.get("ID") == problem and row.get("State", "").casefold() in active_states,
        {"State": resolution, "Evidence": evidence},
    )
    if not changed_problem:
        raise ExperienceError(f"{problem} no existe o ya no está activo en {task}.")
    current_state = status["audit"]["task"].get("Workflow state", "blocked")
    execution_snapshot = status["audit"].get("execution", {})
    target_state = (
        "in-review"
        if status["current_task"]["development"].startswith("Código terminado")
        else "in-progress"
    )
    if not _table_update(
        detail_lines,
        {"Workflow state", "Health", "Updated"},
        lambda row: True,
        {"Workflow state": target_state, "Health": "on-track", "Updated": date.today().isoformat()},
    ):
        raise ExperienceError("No se encontró el estado ejecutable de la tarea.")
    if not _table_update(
        board_lines,
        {"ID", "Workflow state", "Health", "Blockers", "Updated"},
        lambda row: row.get("ID") == task,
        {"Workflow state": target_state, "Health": "on-track", "Blockers": "none", "Updated": date.today().isoformat()},
    ):
        raise ExperienceError("No se encontró la tarea en el tablero.")
    if not _append_history(
        detail_lines,
        [date.today().isoformat(), current_state, target_state, f"{problem} {resolution}: {cause}", actor, evidence],
    ):
        raise ExperienceError("La tarea no contiene la tabla histórica requerida.")
    manifest_new = copy.deepcopy(status["audit"]["manifest"])
    execution_id = execution_snapshot.get("execution_id")
    matching_executions = [
        item
        for item in manifest_new.get("executions", [])
        if isinstance(item, dict)
        and task in item.get("task_ids", [])
        and (execution_id is None or item.get("execution_id") == execution_id)
    ]
    if len(matching_executions) != 1:
        raise ExperienceError("No se puede identificar una única ejecución bloqueada.")
    matching_executions[0]["status"] = target_state
    manifest_new["active_task"] = task
    manifest_new["active_tasks"] = sorted(
        set(manifest_new.get("active_tasks", [])) | {task}
    )
    implementation = manifest_new.get("implementation")
    if isinstance(implementation, dict) and task in implementation.get("task_ids", []):
        implementation["status"] = (
            "completed" if target_state == "in-review" else "in-progress"
        )
    checkpoint_id = _compose_checkpoint_transaction(
        root,
        task,
        target_state,
        actor,
        (
            "Ejecutar únicamente la verificación pendiente."
            if target_state == "in-review"
            else "Reanudar el desarrollo autorizado."
        ),
        board_new=("\n".join(board_lines) + "\n").encode("utf-8"),
        detail_new=("\n".join(detail_lines) + "\n").encode("utf-8"),
        manifest_new=manifest_new,
        completed=(
            f"{problem} cerrado; el código previo permanece listo para revisión"
            if target_state == "in-review"
            else f"{problem} cerrado"
        ),
        execution_id=str(execution_id) if execution_id else None,
    )
    return 0, {
        "status": resolution,
        "changed": True,
        "problem": problem,
        "summary": _management(root, task),
        "administrative_operations": 1,
        "human_confirmations_required": 0,
        "technical_reference": checkpoint_id,
    }


def _start(root: Path, increment: str, task: str, actor: str) -> tuple[int, dict[str, Any]]:
    status = load_status(root, task_id=task)
    if status["current_task"]["human_decision"] != "Ninguna":
        return 3, {
            "status": "decision-required",
            "changed": False,
            "preview": _management(root, task),
            "decision": "Confirmar una única autorización exacta para iniciar esta tarea.",
            "administrative_operations": 0,
            "human_confirmations_required": 1,
        }
    common = {
        "project_root": root,
        "increment": increment,
        "task": [task],
        "date": date.today().isoformat(),
        "actor": actor,
        "authorize": False,
        "preview_hash": None,
        "as_json": True,
    }
    try:
        preview_code, preview = prepare_increment(
            argparse.Namespace(**common, dry_run=True, apply=False)
        )
    except PreparationError as exc:
        raise ExperienceError(str(exc)) from exc
    if preview_code != 0:
        return preview_code, {"status": "blocked", "changed": False, "cause": preview, "summary": _management(root, task)}
    try:
        apply_code, applied = prepare_increment(
            argparse.Namespace(
                **{
                    **common,
                    "authorize": True,
                    "preview_hash": str(preview["preview_hash"]),
                },
                dry_run=False,
                apply=True,
            )
        )
    except PreparationError as exc:
        raise ExperienceError(str(exc)) from exc
    return apply_code, {
        "status": "started" if apply_code == 0 else "blocked",
        "changed": apply_code == 0,
        "summary": _management(root, task),
        "administrative_operations": 1,
        "human_confirmations_required": 0,
        "technical_reference": applied.get("execution_id"),
        "detail": applied if apply_code == 0 else None,
    }


def _checkpoint(root: Path, task: str, state: str, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    status = load_status(root, task_id=task)
    manifest = copy.deepcopy(status["audit"]["manifest"])
    completion = _completion_fields(root, status) if state == "completed" else {}
    task_state = "done" if state == "completed" else state
    reason = (
        args.reason
        or args.completed
        or {
            "in-review": "Implementation completed and ready for verification",
            "completed": "Verified task completed",
        }.get(state)
    )
    transition_args = argparse.Namespace(
        task=task,
        to_state=task_state,
        reason=reason,
        actor=args.actor,
        date=date.today().isoformat(),
        health=None,
        progress=None,
        blocker=args.reason if state == "blocked" else None,
        branch=None,
        revision_start=None,
        revision=completion.get("revision"),
        build=completion.get("build"),
        environment=completion.get("environment"),
        artifact_digest=completion.get("artifact_digest"),
        gate=completion.get("gate"),
        evidence=completion.get("evidence"),
        classification=None,
        change_id=None,
        auto_verified_deliverables=state == "completed",
    )
    try:
        board_new, detail_new, manifest_new, _ = _transition(
            root, manifest, transition_args
        )
        checkpoint_id = _compose_checkpoint_transaction(
            root,
            task,
            state,
            args.actor,
            args.next_action or {
                "in-review": "Ejecutar la verificación pendiente.",
                "blocked": "Resolver el bloqueo activo y reanudar desde este checkpoint.",
                "completed": "Revisar la entrega y cerrar el hito.",
            }[state],
            board_new=board_new,
            detail_new=detail_new,
            manifest_new=manifest_new,
            completed=args.completed or (
                "Código y pruebas listos para verificación"
                if state == "in-review"
                else "Tarea verificada y cerrada"
                if state == "completed"
                else None
            ),
            blocked=args.reason if state == "blocked" else None,
            execution_id=status["audit"].get("execution", {}).get("execution_id"),
        )
    except (TaskManagementError, ContinuityError) as exc:
        raise ExperienceError(str(exc)) from exc
    return 0, {
        "status": state,
        "changed": True,
        "summary": _management(root, task),
        "administrative_operations": 1,
        "human_confirmations_required": 0,
        "technical_reference": checkpoint_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    for name in ("status", "start", "resume", "resolve", "review", "verify", "block", "complete", "sync-jira"):
        item = sub.add_parser(name)
        item.add_argument("project_root", type=Path)
        item.add_argument("--task")
        item.add_argument("--json", action="store_true", dest="as_json")
        if name == "start":
            item.add_argument("--increment", required=True)
            item.add_argument("--actor", default="codex")
        elif name in {"review", "block", "complete"}:
            item.add_argument("--actor", default="codex")
            item.add_argument("--reason")
            item.add_argument("--completed")
            item.add_argument("--next-action")
        elif name == "resolve":
            item.add_argument("--problem", required=True)
            item.add_argument("--resolution", choices=("resolved", "superseded"), default="resolved")
            item.add_argument("--cause", required=True)
            item.add_argument("--evidence", required=True)
            item.add_argument("--actor", default="codex")
        elif name == "verify":
            item.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    try:
        if args.operation == "status":
            status = load_status(root, task_id=args.task)
            result, code = management_json(status), 0
        elif not args.task:
            raise ExperienceError(f"work {args.operation} requiere --task TASK-###.")
        elif args.operation == "start":
            code, result = _start(root, args.increment, args.task, args.actor)
        elif args.operation == "resume":
            status = load_status(root, task_id=args.task)
            if status["current_task"].get("active_blocker"):
                code, result = 3, {
                    "status": "blocked", "changed": False,
                    "cause": status["current_task"]["active_blocker"],
                    "next_action": "Resolver o sustituir explícitamente el problema activo.",
                    "summary": management_json(status),
                }
            else:
                code, detail = _run(["continuity", str(root), "resume"])
                result = {"status": "resumable" if code == 0 else "blocked", "changed": False, "summary": _management(root, args.task), "detail": detail}
        elif args.operation == "resolve":
            code, result = _resolve_problem(
                root, args.task, args.problem, args.resolution,
                args.cause, args.evidence, args.actor,
            )
        elif args.operation in {"review", "block", "complete"}:
            if args.operation == "block" and not args.reason:
                raise ExperienceError("work block requiere --reason.")
            state = {"review": "in-review", "block": "blocked", "complete": "completed"}[args.operation]
            code, result = _checkpoint(root, args.task, state, args)
        elif args.operation == "verify":
            verification_arguments = _verification_arguments(
                root, args.task, args.arguments
            )
            code, detail = _run(["verify", str(root), *verification_arguments])
            result = {"status": detail.get("status", "verified" if code == 0 else "blocked"), "changed": bool(detail.get("evidence_recorded")), "summary": _management(root, args.task), "detail": detail}
        else:
            status = load_status(root, task_id=args.task)
            tracking = status["audit"]["manifest"].get("task_tracking", {})
            needs_decision = tracking.get("mode") == "jira-hybrid" and tracking.get("reporting_scope") != "milestone-reporting"
            result = {
                "status": "decision-required" if needs_decision else "ready-for-peer",
                "changed": False,
                "summary": _management(root, args.task),
                "visible_operation": "Actualizar Jira para el hito actual",
                "human_confirmations_required": 1 if needs_decision else 0,
                "peer_steps": ["fresh-read", "duplicate-check", "write", "reread", "receipt", "reconcile"],
            }
            code = 3 if needs_decision else 0
        if args.as_json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.operation == "status":
            print(render_management(load_status(root, task_id=args.task)))
        else:
            print(result["status"])
            print(render_management(load_status(root, task_id=args.task)))
        return code
    except ExperienceError as exc:
        print(json.dumps({"status": "error", "changed": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
