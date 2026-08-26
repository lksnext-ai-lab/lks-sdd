#!/usr/bin/env python3
"""Create repository checkpoints and validate safe LKS-SDD 1.3-1.5 resumption."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from delivery_engine import (
    REVISION_RE,
    TASK_DETAIL_HEADERS,
    TASK_DETAIL_HEADERS_V13,
    parse_tables,
    repository_revision,
    validate_delivery_contract,
)
from planning_engine import assess_authorization, assess_planning, expand_ids, next_tasks
from validate_project import validate_project


CHECKPOINT_IDENTITY_HEADERS = (
    "Checkpoint", "Execution", "State", "Tasks", "Increment", "Release",
    "Authorization", "Branch", "Revision start", "Last observed revision",
    "Tree state", "Specification fingerprint", "Planning fingerprint", "Updated",
)
CHECKPOINT_FILE_HEADERS = ("Path", "State", "SHA-256", "Task", "Notes")
CHECKPOINT_DELIVERABLE_HEADERS = (
    "Task", "Deliverable", "State", "Acceptance", "Evidence", "Notes",
)
CHECKPOINT_CHECK_HEADERS = (
    "Task", "Contract item", "Kind", "Result", "Evidence", "Revision", "Notes",
)
CHECKPOINT_ISSUE_HEADERS = (
    "ID", "State", "Kind", "Description", "Resolution condition", "Owner role", "Evidence",
)
CHECKPOINT_RESUME_HEADERS = (
    "Completed", "Partial", "Pending", "Blocked", "Next safe action",
    "Independent ready tasks", "Reconciliation required",
)
EXECUTION_STATES = {"in-progress", "in-review", "paused", "blocked", "completed", "cancelled"}


class ContinuityError(ValueError):
    """Expected checkpoint or resume failure."""


def _load_manifest(root: Path) -> tuple[Path, dict[str, Any], bytes]:
    path = root / ".lks-sdd" / "project.json"
    try:
        original = path.read_bytes()
        value = json.loads(original.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContinuityError(f"No se puede leer project.json: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") not in {"1.3", "1.4", "1.5"}:
        raise ContinuityError("Los checkpoints reanudables requieren schema 1.3, 1.4 o 1.5.")
    return path, value, original


def _validate_checkpoint_schema(
    manifest_schema: str, checkpoint_schema: str | None
) -> None:
    allowed = {
        "1.3": {"1.3"},
        "1.4": {"1.3", "1.4"},
        "1.5": {"1.3", "1.4", "1.5"},
    }.get(manifest_schema, set())
    if checkpoint_schema not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ContinuityError(
            "El checkpoint no usa un schema_version compatible con el proyecto: "
            f"schema {manifest_schema} requiere checkpoint {expected}."
        )


def _safe_cell(label: str, value: str | None, *, default: str | None = None) -> str:
    normalized = (value or default or "").strip()
    if not normalized or any(marker in normalized for marker in ("|", "\r", "\n")):
        raise ContinuityError(f"{label} debe ser una celda Markdown no vacía.")
    return normalized


def _change_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ContinuityError("--date debe usar AAAA-MM-DD.") from exc


def _cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [item.strip() for item in stripped[1:-1].split("|")]


def _table_rows(text: str, headers: tuple[str, ...]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for actual, table_rows in parse_tables(text):
        if actual == headers:
            rows.extend(table_rows)
    return rows


def _single_table_rows(
    tables: list[tuple[tuple[str, ...], list[dict[str, str]]]],
    headers: tuple[str, ...],
) -> list[dict[str, str]]:
    matches = [rows for actual, rows in tables if actual == headers]
    if len(matches) != 1:
        raise ContinuityError(
            f"El checkpoint necesita exactamente una tabla {headers[0]}."
        )
    return matches[0]


def _frontmatter_scalar(text: str, key: str) -> str | None:
    match = re.search(
        rf'(?m)^{re.escape(key)}:\s*(?:"([^"]*)"|([^\s#]+))\s*$', text
    )
    return (match.group(1) or match.group(2)) if match else None


def _meaningful(value: str | None) -> bool:
    normalized = (value or "").strip().casefold()
    return normalized not in {
        "", "pending", "none", "unknown", "not-run", "not-applicable",
        "tbd", "todo",
    } and not normalized.startswith(
        ("pending:", "unknown:", "not-run:", "tbd:", "todo:")
    )


def _replace_single_row(
    text: str, headers: tuple[str, ...], updates: dict[str, str]
) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _cells(line) != list(headers):
            continue
        values = _cells(lines[index + 2]) if index + 2 < len(lines) else None
        if values is None or len(values) != len(headers):
            raise ContinuityError(f"La tabla {headers[0]} no tiene una fila única.")
        row = dict(zip(headers, values, strict=True))
        row.update(updates)
        lines[index + 2] = "| " + " | ".join(row[item] for item in headers) + " |"
        return "\n".join(lines) + "\n"
    raise ContinuityError(f"No se encontró la tabla {headers[0]}.")


def _frontmatter_date(text: str, change_date: str) -> str:
    updated, count = re.subn(
        r'^last_updated: "[0-9]{4}-[0-9]{2}-[0-9]{2}"$',
        f'last_updated: "{change_date}"', text, count=1, flags=re.MULTILINE,
    )
    if count != 1:
        raise ContinuityError("No se pudo actualizar last_updated de la tarea.")
    return updated


def _next_checkpoint_id(root: Path) -> str:
    folder = root / "docs/lks-sdd/04-delivery/checkpoints"
    used = {
        int(match.group(1))
        for path in folder.glob("CKPT-*.md") if folder.is_dir()
        if (match := re.fullmatch(r"CKPT-([0-9]{3})\.md", path.name))
    }
    for number in range(1, 1000):
        if number not in used:
            return f"CKPT-{number:03d}"
    raise ContinuityError("Se agotó el espacio CKPT-###.")


def _safe_relative_path(root: Path, raw: str, *, label: str) -> str:
    candidate = Path(raw)
    if (
        candidate.is_absolute()
        or not candidate.parts
        or ".." in candidate.parts
        or any(marker in raw for marker in ("|", "\x00", "\r", "\n"))
    ):
        raise ContinuityError(f"{label} no segura: {raw!r}.")
    relative = candidate.as_posix()
    resolved = (root / candidate).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ContinuityError(f"{label} fuera del proyecto: {raw!r}.") from exc
    return relative


def _git_changed_files(root: Path) -> list[tuple[str, str]]:
    if not (root / ".git").exists():
        return []
    try:
        output = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
            cwd=root, check=True, capture_output=True, text=True, encoding="utf-8",
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContinuityError(f"No se puede observar git status: {exc}") from exc
    result: list[tuple[str, str]] = []
    entries = output.split("\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        if len(entry) < 4 or entry[2] != " ":
            raise ContinuityError("git status devolvió una entrada porcelain inválida.")
        state_code = entry[:2]
        state = state_code.strip() or "modified"
        relative = _safe_relative_path(
            root, entry[3:], label="Ruta observada por Git"
        )
        if "R" in state_code or "C" in state_code:
            if index >= len(entries) or not entries[index]:
                raise ContinuityError("git status devolvió un rename/copy incompleto.")
            _safe_relative_path(
                root, entries[index], label="Ruta de origen observada por Git"
            )
            index += 1
        result.append((relative, state))
    return sorted(result)


def _file_rows(
    root: Path,
    tasks: list[str],
    *,
    replacement_bytes: dict[str, bytes] | None = None,
    declared_paths: list[str] | None = None,
) -> tuple[str, list[str]]:
    rows: list[str] = []
    paths: list[str] = []
    task = tasks[0] if len(tasks) == 1 else ", ".join(tasks)
    replacements = replacement_bytes or {}
    observed = dict(_git_changed_files(root))
    declared: set[str] = set()
    for raw in declared_paths or []:
        declared.add(
            _safe_relative_path(root, raw, label="Ruta modificada")
        )
    for relative in sorted(set(observed) | declared):
        state = observed.get(relative, "tracked-by-execution")
        path = root / relative
        digest = (
            "not-applicable"
            if relative == ".lks-sdd/project.json"
            else
            hashlib.sha256(replacements[relative]).hexdigest()
            if relative in replacements
            else hashlib.sha256(path.read_bytes()).hexdigest()
            if path.is_file() and not path.is_symlink()
            else "not-applicable"
        )
        note = (
            "managed execution index validated semantically"
            if relative == ".lks-sdd/project.json"
            else "observed by git status"
            if relative in observed
            else "declared from the authorized execution"
        )
        rows.append(f"| {relative} | {state} | {digest} | {task} | {note} |")
        paths.append(relative)
    if not rows:
        rows.append("| not-applicable | clean | not-applicable | not-applicable | no changed files observed |")
    return "\n".join(rows), paths


def _task_snapshot(
    root: Path, task_ids: list[str]
) -> tuple[str, str, str, list[tuple[Path, bytes, bytes]]]:
    deliverables: list[str] = []
    checks: list[str] = []
    issues: list[str] = []
    replacements: list[tuple[Path, bytes, bytes]] = []
    for task_id in task_ids:
        path = root / f"docs/lks-sdd/04-delivery/tasks/{task_id}.md"
        try:
            original = path.read_bytes()
            text = original.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            raise ContinuityError(f"No se puede leer {task_id}: {exc}") from exc
        for row in _table_rows(text, TASK_DETAIL_HEADERS_V13["deliverables"]):
            deliverables.append(
                "| " + " | ".join([
                    task_id, row.get("Deliverable", "pending"), row.get("State", "pending"),
                    row.get("Acceptance", "pending"), row.get("Evidence", "pending"),
                    row.get("Notes", "pending"),
                ]) + " |"
            )
        represented_checks: set[str] = set()
        validation_rows = _table_rows(text, TASK_DETAIL_HEADERS["validation"])
        for row in validation_rows:
            contract_items, _ = expand_ids(row.get("Acceptance", ""))
            contract_item = (
                contract_items[0]
                if contract_items
                else row.get("Acceptance", "pending")
            )
            represented_checks.update(contract_items)
            checks.append(
                "| " + " | ".join([
                    task_id,
                    contract_item,
                    "test" if contract_item.startswith("TEST-") else "acceptance",
                    row.get("Result", "not-run"), row.get("Evidence", "pending"),
                    row.get("Revision", "pending"), "task validation record",
                ]) + " |"
            )
            gates = re.findall(
                r"\bGATE-[A-Z0-9-]{3,80}\b", row.get("Gate", "")
            )
            represented_checks.update(gates)
            for gate in gates:
                checks.append(
                    "| " + " | ".join([
                        task_id, gate, "gate", row.get("Result", "not-run"),
                        row.get("Evidence", "pending"),
                        row.get("Revision", "pending"),
                        f"linked to {contract_item}",
                    ]) + " |"
                )
        planned_checks: dict[str, str] = {}
        definition_rows = _table_rows(
            text, TASK_DETAIL_HEADERS["definition"]
        )
        if len(definition_rows) == 1:
            for acceptance in re.findall(
                r"\bAC-[0-9]{3}\b", definition_rows[0].get("Acceptance", "")
            ):
                planned_checks[acceptance] = "acceptance"
            for gate in re.findall(
                r"\bGATE-[A-Z0-9-]{3,80}\b",
                definition_rows[0].get("Technical gates", ""),
            ):
                planned_checks[gate] = "gate"
        plan_rows = _table_rows(text, TASK_DETAIL_HEADERS_V13["plan"])
        if len(plan_rows) == 1:
            for test_id in re.findall(
                r"\bTEST-[0-9]{3}\b", plan_rows[0].get("Tests", "")
            ):
                planned_checks[test_id] = "test"
        for contract_item, kind in sorted(planned_checks.items()):
            if contract_item in represented_checks:
                continue
            checks.append(
                f"| {task_id} | {contract_item} | {kind} | not-run | pending | pending | no result recorded |"
            )
        for row in _table_rows(text, TASK_DETAIL_HEADERS["issues"]):
            issues.append(
                "| " + " | ".join([
                    row.get("ID", "pending"), row.get("State", "open"), "task-problem",
                    row.get("Description", "pending"), row.get("Resolution condition", "pending"),
                    row.get("Owner", "pending-assignment"), row.get("Evidence", "pending"),
                ]) + " |"
            )
        replacements.append((path, original, original))
    return (
        "\n".join(deliverables) or "| not-applicable | none | pending | pending | pending | no deliverable rows |",
        "\n".join(checks) or "| not-applicable | pending | check | not-run | pending | pending | no validation observed |",
        "\n".join(issues) or "| not-applicable | resolved | none | no open issue recorded | not-applicable | not-applicable | not-applicable |",
        replacements,
    )


def _render_checkpoint(
    root: Path,
    manifest: dict[str, Any],
    execution: dict[str, Any],
    checkpoint_id: str,
    args: argparse.Namespace,
    planning: dict[str, Any],
    authorization: dict[str, Any],
    revision: dict[str, Any],
) -> tuple[bytes, list[str], list[tuple[Path, bytes, bytes]]]:
    template = (
        Path(__file__).resolve().parents[1]
        / "skills/lks-sdd-define/assets/templates/04-delivery/checkpoint.md"
    ).read_text(encoding="utf-8")
    template = re.sub(
        r'^schema_version: "[^"]+"$',
        f'schema_version: "{manifest["schema_version"]}"',
        template,
        count=1,
        flags=re.MULTILINE,
    )
    template = re.sub(
        r'^method_version: "[^"]+"$',
        f'method_version: "{manifest["method_version"]}"',
        template,
        count=1,
        flags=re.MULTILINE,
    )
    template = re.sub(
        r'^created_with_plugin_version: "[^"]+"$',
        f'created_with_plugin_version: "{manifest["plugin_version"]}"',
        template,
        count=1,
        flags=re.MULTILINE,
    )
    task_ids = sorted(execution["task_ids"])
    deliverables, checks, issues, task_replacements = _task_snapshot(root, task_ids)
    change_date = _change_date(args.date)
    delivery = validate_delivery_contract(root, manifest)
    safe_independent = sorted(
        set(next_tasks(delivery, planning).get("ready", [])) - set(task_ids)
    )
    requested_independent = set(args.independent_task or [])
    invalid_independent = sorted(requested_independent - set(safe_independent))
    if invalid_independent:
        raise ContinuityError(
            "--independent-task solo admite tareas ready con dependencias done: "
            + ", ".join(invalid_independent)
        )
    independent = (
        sorted(requested_independent) if requested_independent else safe_independent
    )
    continuity_updates = {
        "Current checkpoint": f"../checkpoints/{checkpoint_id}.md",
        "Authorization": str(authorization["authorization_id"]),
        "Authorization scope": ", ".join(task_ids),
        "Specification fingerprint": str(planning["specification_fingerprint"]),
        "Planning fingerprint": str(planning["planning_fingerprint"]),
        "Next safe action": _safe_cell("--next-action", args.next_action),
    }
    updated_replacements: list[tuple[Path, bytes, bytes]] = []
    for path, original, _ in task_replacements:
        text = original.decode("utf-8")
        updated = _replace_single_row(
            text, TASK_DETAIL_HEADERS_V13["continuity"], continuity_updates
        )
        updated = _frontmatter_date(updated, change_date)
        updated_replacements.append((path, original, updated.encode("utf-8")))
    replacement_bytes = {
        path.relative_to(root).as_posix(): replacement
        for path, _, replacement in updated_replacements
    }
    file_rows, changed_paths = _file_rows(
        root,
        task_ids,
        replacement_bytes=replacement_bytes,
        declared_paths=[
            *execution.get("changed_paths", []),
            *(args.changed_path or []),
        ],
    )
    values = {
        "{{CHECKPOINT_ID}}": checkpoint_id,
        "{{PROJECT_ID}}": str(manifest["project_id"]),
        "{{BASELINE_ID}}": str(manifest["baseline_id"]),
        "{{OWNER_ROLE}}": _safe_cell("--owner-role", args.owner_role),
        "{{DATE}}": change_date,
        "{{EXECUTION_ID}}": str(execution["execution_id"]),
        "{{EXECUTION_STATE}}": args.state,
        "{{TASK_IDS}}": ", ".join(task_ids),
        "{{INCREMENT_ID}}": str(execution["increment"]),
        "{{RELEASE_ID}}": str(execution["release"]),
        "{{AUTHORIZATION_ID}}": str(authorization["authorization_id"]),
        "{{BRANCH}}": str(revision.get("branch") or "not-applicable"),
        "{{REVISION_START}}": str(execution["revision_start"]),
        "{{LAST_REVISION}}": str(revision["revision"]),
        "{{TREE_STATE}}": "dirty" if revision["dirty"] else "clean",
        "{{SPECIFICATION_FINGERPRINT}}": str(planning["specification_fingerprint"]),
        "{{PLANNING_FINGERPRINT}}": str(planning["planning_fingerprint"]),
        "{{FILE_ROWS}}": file_rows,
        "{{DELIVERABLE_ROWS}}": deliverables,
        "{{CHECK_ROWS}}": checks,
        "{{ISSUE_ROWS}}": issues,
        "{{COMPLETED}}": _safe_cell("--completed", args.completed, default="none observed"),
        "{{PARTIAL}}": _safe_cell("--partial", args.partial, default="none observed"),
        "{{PENDING}}": _safe_cell("--pending", args.pending, default="see task definitions"),
        "{{BLOCKED}}": _safe_cell("--blocked", args.blocked, default="none observed"),
        "{{NEXT_SAFE_ACTION}}": _safe_cell("--next-action", args.next_action),
        "{{INDEPENDENT_TASKS}}": ", ".join(independent) if independent else "none observed",
        "{{RECONCILIATION}}": "no",
    }
    for token, value in values.items():
        template = template.replace(token, value)
    remaining = re.findall(r"\{\{[A-Z0-9_]+\}\}", template)
    if remaining:
        raise ContinuityError(f"Tokens de checkpoint sin resolver: {remaining}")
    return template.encode("utf-8"), changed_paths, updated_replacements


def _preview_hash(
    manifest: bytes, task_replacements: list[tuple[Path, bytes, bytes]],
    checkpoint: bytes, payload: dict[str, Any],
) -> str:
    digest = hashlib.sha256(hashlib.sha256(manifest).digest())
    for path, original, replacement in task_replacements:
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(hashlib.sha256(original).digest())
        digest.update(hashlib.sha256(replacement).digest())
    digest.update(hashlib.sha256(checkpoint).digest())
    digest.update(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return digest.hexdigest()


def _apply_checkpoint(
    checkpoint_path: Path,
    checkpoint: bytes,
    manifest_path: Path,
    manifest_original: bytes,
    manifest_new: bytes,
    task_replacements: list[tuple[Path, bytes, bytes]],
) -> None:
    created = False
    parent_created = not checkpoint_path.parent.exists()
    manifest_replaced = False
    replaced: list[tuple[Path, bytes]] = []
    temporaries: list[Path] = []
    try:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with checkpoint_path.open("xb") as stream:
            stream.write(checkpoint)
        created = True
        for path, original, replacement in task_replacements:
            if path.read_bytes() != original:
                raise ContinuityError(f"{path.name} cambió después del preview.")
            temporary = path.with_name(path.name + ".lks-sdd-checkpoint.tmp")
            with temporary.open("xb") as stream:
                stream.write(replacement)
            temporaries.append(temporary)
            os.replace(temporary, path)
            temporaries.remove(temporary)
            replaced.append((path, original))
        if manifest_path.read_bytes() != manifest_original:
            raise ContinuityError("project.json cambió después del preview.")
        temporary = manifest_path.with_name("project.json.lks-sdd-checkpoint.tmp")
        with temporary.open("xb") as stream:
            stream.write(manifest_new)
        temporaries.append(temporary)
        os.replace(temporary, manifest_path)
        temporaries.remove(temporary)
        manifest_replaced = True
        report, _, _ = validate_project(manifest_path.parents[1])
        if not report.valid:
            raise ContinuityError(
                "El checkpoint produciría un contrato inválido: "
                + "; ".join(report.errors)
            )
    except (OSError, ContinuityError):
        for temporary in temporaries:
            try:
                temporary.unlink()
            except OSError:
                pass
        if manifest_replaced:
            manifest_path.write_bytes(manifest_original)
        for path, original in reversed(replaced):
            path.write_bytes(original)
        if created:
            try:
                checkpoint_path.unlink()
            except OSError:
                pass
        if parent_created:
            try:
                checkpoint_path.parent.rmdir()
            except OSError:
                pass
        raise


def _select_execution(manifest: dict[str, Any], execution_id: str | None) -> dict[str, Any]:
    executions = [item for item in manifest.get("executions", []) if isinstance(item, dict)]
    matches = (
        [item for item in executions if item.get("execution_id") == execution_id]
        if execution_id
        else [item for item in executions if item.get("status") in {"in-progress", "in-review", "paused", "blocked"}]
    )
    if len(matches) != 1:
        raise ContinuityError("Seleccione una única ejecución con --execution-id EXEC-###.")
    return matches[0]


def _validate_checkpoint_state(
    execution: dict[str, Any], delivery: dict[str, Any], requested: str
) -> None:
    task_states = {
        task_id: delivery.get("tasks", {}).get(task_id, {}).get("Workflow state")
        for task_id in execution.get("task_ids", [])
    }
    missing = sorted(task_id for task_id, state in task_states.items() if state is None)
    if missing:
        raise ContinuityError(
            "La ejecución contiene tareas inexistentes: " + ", ".join(missing) + "."
        )
    states = set(task_states.values())
    derived = (
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
    if requested == "paused":
        if derived not in {"in-progress", "in-review", "blocked", "paused"}:
            raise ContinuityError(
                f"No se puede pausar una ejecución cuyo estado derivado es {derived}."
            )
        return
    if requested != derived:
        details = ", ".join(
            f"{task_id}={state}" for task_id, state in sorted(task_states.items())
        )
        raise ContinuityError(
            f"El checkpoint {requested} contradice las tareas ({details}); "
            f"el estado derivado es {derived}."
        )


def _resume(root: Path, manifest: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    execution = _select_execution(manifest, args.execution_id)
    checkpoint_relative = execution.get("latest_checkpoint")
    if not isinstance(checkpoint_relative, str):
        raise ContinuityError("La ejecución no tiene latest_checkpoint.")
    checkpoint_relative = _safe_relative_path(
        root, checkpoint_relative, label="Ruta de checkpoint"
    )
    if not re.fullmatch(
        r"docs/lks-sdd/04-delivery/checkpoints/CKPT-[0-9]{3}\.md",
        checkpoint_relative,
    ):
        raise ContinuityError("latest_checkpoint no usa la ruta canónica CKPT-###.")
    checkpoint_path = root / checkpoint_relative
    try:
        text = checkpoint_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContinuityError(f"No se puede leer el checkpoint: {exc}") from exc
    if _frontmatter_scalar(text, "artifact_id") != f"ART-{checkpoint_path.stem}":
        raise ContinuityError("El checkpoint no conserva su artifact_id canónico.")
    if _frontmatter_scalar(text, "artifact_type") != "implementation-checkpoint":
        raise ContinuityError("El checkpoint no usa artifact_type implementation-checkpoint.")
    _validate_checkpoint_schema(
        str(manifest["schema_version"]),
        _frontmatter_scalar(text, "schema_version"),
    )
    tables = parse_tables(text)
    identity = _single_table_rows(tables, CHECKPOINT_IDENTITY_HEADERS)
    resume_rows = _single_table_rows(tables, CHECKPOINT_RESUME_HEADERS)
    files = _single_table_rows(tables, CHECKPOINT_FILE_HEADERS)
    deliverables = _single_table_rows(tables, CHECKPOINT_DELIVERABLE_HEADERS)
    checks = _single_table_rows(tables, CHECKPOINT_CHECK_HEADERS)
    issues = _single_table_rows(tables, CHECKPOINT_ISSUE_HEADERS)
    if len(identity) != 1 or len(resume_rows) != 1:
        raise ContinuityError("El checkpoint no contiene identidad y reanudación únicas.")
    planning = assess_planning(
        root, manifest, execution["increment"], release=execution["release"]
    )
    authorization = assess_authorization(manifest, planning, execution["task_ids"])
    revision = repository_revision(root)
    divergence: list[str] = []
    expected_identity = {
        "Checkpoint": checkpoint_path.stem,
        "Execution": str(execution["execution_id"]),
        "State": str(execution["status"]),
        "Increment": str(execution["increment"]),
        "Release": str(execution["release"]),
        "Authorization": str(execution["authorization_id"]),
        "Revision start": str(execution["revision_start"]),
        "Last observed revision": str(execution["last_observed_revision"]),
        "Specification fingerprint": str(
            execution["specification_fingerprint"]
        ),
        "Planning fingerprint": str(execution["planning_fingerprint"]),
    }
    for field, expected in expected_identity.items():
        if identity[0].get(field) != expected:
            divergence.append(f"checkpoint identity changed: {field}")
    checkpoint_tasks, task_errors = expand_ids(identity[0].get("Tasks", ""))
    if task_errors or sorted(
        item for item in checkpoint_tasks if item.startswith("TASK-")
    ) != sorted(execution.get("task_ids", [])):
        divergence.append("checkpoint identity changed: Tasks")
    if (
        authorization.get("status") == "authorized"
        and authorization.get("authorization_id")
        != execution.get("authorization_id")
    ):
        divergence.append("authorization changed")
    if identity[0].get("Branch") != str(revision.get("branch") or "not-applicable"):
        divergence.append("branch changed")
    if identity[0].get("Last observed revision") != str(revision["revision"]):
        divergence.append("revision changed")
    expected_tree_state = "dirty" if revision["dirty"] else "clean"
    if identity[0].get("Tree state") != expected_tree_state:
        divergence.append("tree state changed")
    recorded_paths = {
        row.get("Path", "")
        for row in files
        if row.get("Path") not in {"", "not-applicable"}
    }
    current_paths = {path for path, _ in _git_changed_files(root)}
    managed_paths = {
        ".lks-sdd/project.json",
        checkpoint_relative,
        "docs/lks-sdd/04-delivery/tasks.md",
        *(
            f"docs/lks-sdd/04-delivery/tasks/{task_id}.md"
            for task_id in execution.get("task_ids", [])
        ),
    }
    if revision.get("kind") == "git":
        for relative in sorted(current_paths - recorded_paths - managed_paths):
            divergence.append(f"unrecorded changed path: {relative}")
    for row in files:
        relative = row.get("Path", "")
        expected = row.get("SHA-256", "")
        if relative == "not-applicable":
            continue
        if not re.fullmatch(r"[a-f0-9]{64}|not-applicable", expected):
            divergence.append(f"invalid recorded digest: {relative}")
            continue
        if expected == "not-applicable":
            continue
        relative = _safe_relative_path(
            root, relative, label="Ruta registrada en checkpoint"
        )
        path = root / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != expected:
            divergence.append(f"file changed: {relative}")
    fingerprint_divergence = (
        identity[0].get("Specification fingerprint") != planning["specification_fingerprint"]
        or identity[0].get("Planning fingerprint") != planning["planning_fingerprint"]
        or planning["status"] == "stale"
        or planning["integrity"] != "valid"
    )
    if fingerprint_divergence:
        recommendation = "replan"
    elif authorization["status"] != "authorized" or divergence:
        recommendation = "reconcile"
    else:
        recommendation = "continue"
    delivery = validate_delivery_contract(root, manifest)
    recorded = resume_rows[0]
    substantive_checks = [
        row for row in checks if row.get("Task") != "not-applicable"
    ]
    verified_task_ids = {
        row.get("Task")
        for row in substantive_checks
        if row.get("Result") == "passed"
        and _meaningful(row.get("Evidence"))
        and REVISION_RE.fullmatch(row.get("Revision", ""))
    }
    code_written_is_verified = bool(substantive_checks) and all(
        row.get("Result") == "passed"
        and _meaningful(row.get("Evidence"))
        and REVISION_RE.fullmatch(row.get("Revision", ""))
        for row in substantive_checks
    ) and set(execution.get("task_ids", [])) <= verified_task_ids
    pending_checks = [
        row.get("Contract item", "pending check")
        for row in substantive_checks
        if row.get("Result") in {"not-run", "skipped", "blocked", "failed"}
    ]
    next_step = (
        recorded.get("Next safe action", "Continue the recorded task work.")
        if recommendation == "continue"
        else "Reconciliar rama, revisión, árbol, archivos o autorización antes de editar."
        if recommendation == "reconcile"
        else "Reevaluar impacto, cobertura, dependencias y autorización antes de continuar."
    )
    human_decision = (
        "Ninguna nueva; continuar dentro del checkpoint y la autorización vigentes."
        if recommendation == "continue"
        else "Aceptar la reconciliación propuesta o detener la ejecución."
        if recommendation == "reconcile"
        else "Confirmar una planificación revisada antes de reanudar."
    )
    return {
        "status": f"{recommendation}-recommended",
        "execution_id": execution["execution_id"],
        "checkpoint": checkpoint_relative,
        "tasks": execution["task_ids"],
        "repository": revision,
        "divergence": divergence,
        "fingerprint_divergence": fingerprint_divergence,
        "authorization": authorization,
        "recorded_state": recorded,
        "recorded_files": files,
        "recorded_deliverables": deliverables,
        "recorded_checks": checks,
        "recorded_issues": issues,
        "next_tasks": next_tasks(delivery, planning),
        "recommendation": recommendation,
        "code_written_is_verified": code_written_is_verified,
        "transition_summary": {
            "where_we_are": f"resume-{recommendation}",
            "completed": [recorded.get("Completed", "none observed")],
            "in_progress": execution["task_ids"],
            "pending": [
                recorded.get("Partial", "none observed"),
                recorded.get("Pending", "none observed"),
                *(f"check pendiente: {item}" for item in pending_checks),
            ],
            "blocked": [
                item
                for item in [recorded.get("Blocked", "none observed"), *divergence]
                if item and item != "none observed"
            ],
            "next_step": next_step,
            "human_decision": human_decision,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    resume = subparsers.add_parser("resume")
    resume.add_argument("--execution-id")
    resume.add_argument("--json", action="store_true", dest="as_json")
    checkpoint = subparsers.add_parser("checkpoint")
    checkpoint.add_argument("--execution-id")
    checkpoint.add_argument("--state", required=True, choices=sorted(EXECUTION_STATES))
    checkpoint.add_argument("--date", required=True)
    checkpoint.add_argument("--owner-role", required=True)
    checkpoint.add_argument("--completed")
    checkpoint.add_argument("--partial")
    checkpoint.add_argument("--pending")
    checkpoint.add_argument("--blocked")
    checkpoint.add_argument("--next-action", required=True)
    checkpoint.add_argument("--independent-task", action="append")
    checkpoint.add_argument(
        "--changed-path",
        action="append",
        help="Ruta relativa observada como modificada; repita para proyectos sin Git.",
    )
    mode = checkpoint.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--apply", action="store_true")
    checkpoint.add_argument("--authorize", action="store_true")
    checkpoint.add_argument("--preview-hash")
    checkpoint.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    try:
        manifest_path, manifest, manifest_original = _load_manifest(root)
        if args.command == "resume":
            result = _resume(root, manifest, args)
            code = 0 if result["recommendation"] == "continue" else 3
        else:
            execution = _select_execution(manifest, args.execution_id)
            planning = assess_planning(
                root, manifest, execution["increment"], release=execution["release"]
            )
            authorization = assess_authorization(manifest, planning, execution["task_ids"])
            if authorization["status"] != "authorized":
                raise ContinuityError("La ejecución ya no tiene una autorización vigente.")
            delivery = validate_delivery_contract(root, manifest)
            if delivery["errors"]:
                raise ContinuityError(
                    "El contrato de tareas es inválido: "
                    + "; ".join(delivery["errors"])
                )
            _validate_checkpoint_state(execution, delivery, args.state)
            revision = repository_revision(root)
            if (
                revision.get("kind") == "workspace"
                and revision.get("revision")
                != execution.get("last_observed_revision")
                and not args.changed_path
            ):
                raise ContinuityError(
                    "El workspace cambió desde el último checkpoint; declare cada "
                    "ruta observada con --changed-path antes de actualizarlo."
                )
            checkpoint_id = _next_checkpoint_id(root)
            checkpoint_bytes, changed_paths, task_replacements = _render_checkpoint(
                root, manifest, execution, checkpoint_id, args, planning, authorization, revision
            )
            manifest_new = json.loads(json.dumps(manifest))
            indexed = next(
                item for item in manifest_new["executions"]
                if item["execution_id"] == execution["execution_id"]
            )
            indexed.update({
                "status": args.state,
                "last_observed_revision": revision["revision"],
                "latest_checkpoint": f"docs/lks-sdd/04-delivery/checkpoints/{checkpoint_id}.md",
                "changed_paths": sorted(set(indexed.get("changed_paths", [])) | set(changed_paths)),
            })
            manifest_new_bytes = (
                json.dumps(manifest_new, indent=2, ensure_ascii=False) + "\n"
            ).encode("utf-8")
            payload = {
                "operation": "checkpoint", "checkpoint_id": checkpoint_id,
                "execution_id": execution["execution_id"], "state": args.state,
                "tasks": execution["task_ids"], "revision": revision,
                "changed_paths": changed_paths,
                "commit_created": False, "published": False,
            }
            preview_hash = _preview_hash(
                manifest_original, task_replacements, checkpoint_bytes, payload
            )
            result = {
                "status": "preview" if args.preview else "applied",
                "changed": False, "preview_hash": preview_hash, **payload,
                "transition_summary": {
                    "where_we_are": "checkpoint-preview" if args.preview else f"implementation-{args.state}",
                    "completed": [] if args.preview else [f"{checkpoint_id} registra el estado observado de {execution['execution_id']}."],
                    "in_progress": execution["task_ids"] if args.state in {"in-progress", "in-review", "paused", "blocked"} else [],
                    "pending": [args.pending or "see task definitions"],
                    "blocked": [args.blocked] if args.blocked else [],
                    "next_step": (
                        "Revisar el checkpoint propuesto antes de aplicarlo."
                        if args.preview
                        else args.next_action
                    ),
                    "human_decision": (
                        "Aplicar o corregir el checkpoint."
                        if args.preview
                        else "Ninguna nueva; usar este checkpoint como fuente de reanudación."
                    ),
                },
            }
            if args.preview:
                code = 0
            else:
                if not args.authorize or args.preview_hash != preview_hash:
                    raise ContinuityError("Aplicar requiere --authorize y el preview hash vigente.")
                checkpoint_path = root / f"docs/lks-sdd/04-delivery/checkpoints/{checkpoint_id}.md"
                _apply_checkpoint(
                    checkpoint_path, checkpoint_bytes, manifest_path,
                    manifest_original, manifest_new_bytes, task_replacements,
                )
                result.update({"status": "applied", "changed": True})
                code = 0
        if getattr(args, "as_json", False):
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result["status"])
            if result.get("preview_hash"):
                print(f"preview_hash={result['preview_hash']}")
        return code
    except (OSError, ContinuityError, ValueError) as exc:
        print(json.dumps({"status": "error", "changed": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
