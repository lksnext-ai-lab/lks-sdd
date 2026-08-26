#!/usr/bin/env python3
"""Manage LKS-SDD 1.4/1.5 task tracking without network operations."""

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
from urllib.parse import urlparse

from delivery_engine import validate_delivery_contract
from jira_reporting_engine import build_milestone_preview
from task_tracking_engine import (
    BINDING_HEADERS,
    MAPPING_HEADERS,
    OPERATION_HEADERS,
    REPORTING_HEADERS,
    WORKFLOW_HEADERS,
    MILESTONE_OPERATION_HEADERS,
    PERSONAL_DATA_RE,
    SENSITIVE_VALUE_RE,
    TrackingContractError,
    TrackingPlanningBlocked,
    assess_tracking,
    build_projection_preview,
    correlation_marker,
    external_key_matches_project,
    load_tracking_contract,
    require_confirmed_tracking_decision,
    unsafe_persisted_text,
    url_matches_external_key,
)


class TrackingCommandError(ValueError):
    """An expected, user-facing command error."""


SENSITIVE_MARKERS = (
    "authorization:",
    "bearer ",
    "basic ",
    "api_token",
    "api-token",
    "api_key",
    "api-key",
    "password=",
    "passwd=",
    "cookie:",
    "set-cookie:",
    "client_secret",
    "refresh_token",
    "access_token",
)


def _load_manifest(root: Path) -> tuple[Path, dict[str, Any], bytes]:
    path = root / ".lks-sdd" / "project.json"
    try:
        original = path.read_bytes()
        manifest = json.loads(original.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TrackingCommandError(f"No se puede leer project.json: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") not in {
        "1.4",
        "1.5",
    }:
        raise TrackingCommandError("La gestión de tracking requiere schema 1.4 o 1.5.")
    return path, manifest, original


def _safe_cell(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized or any(marker in normalized for marker in ("|", "\r", "\n")):
        raise TrackingCommandError(
            f"{label} es obligatorio y debe caber en una celda Markdown."
        )
    lowered = normalized.casefold()
    if (
        any(marker in lowered for marker in SENSITIVE_MARKERS)
        or SENSITIVE_VALUE_RE.search(normalized)
        or PERSONAL_DATA_RE.search(normalized)
        or unsafe_persisted_text(normalized)
        or re.search(
            r"https?://[^/@:]+:[^/@]+@", normalized, flags=re.IGNORECASE
        )
    ):
        raise TrackingCommandError(
            f"{label} parece contener credenciales o datos personales, o markup; "
            "LKS-SDD nunca los persiste."
        )
    return normalized


def _iso_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise TrackingCommandError("--date debe usar AAAA-MM-DD.") from exc


def _https_url(label: str, value: str) -> str:
    normalized = _safe_cell(label, value)
    try:
        parsed = urlparse(normalized)
        parsed.port
    except ValueError as exc:
        raise TrackingCommandError(
            f"{label} debe ser una URL HTTPS con un puerto válido."
        ) from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or bool(parsed.query)
        or bool(parsed.fragment)
    ):
        raise TrackingCommandError(
            f"{label} debe ser una URL HTTPS sin credenciales, query ni fragmento."
        )
    if label == "--site" and parsed.path not in {"", "/"}:
        raise TrackingCommandError(
            "--site debe identificar el origen Jira, sin una ruta de recurso."
        )
    return normalized


def _cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [item.strip() for item in stripped[1:-1].split("|")]


def _replace_row(
    text: str,
    headers: tuple[str, ...],
    row_id: str,
    updates: dict[str, str],
) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _cells(line) != list(headers):
            continue
        cursor = index + 2
        while cursor < len(lines):
            values = _cells(lines[cursor])
            if values is None:
                break
            if len(values) == len(headers) and values[0] == row_id:
                row = dict(zip(headers, values, strict=True))
                row.update(updates)
                lines[cursor] = "| " + " | ".join(row[item] for item in headers) + " |"
                return "\n".join(lines) + "\n"
            cursor += 1
    raise TrackingCommandError(f"No se encontró la fila {row_id}.")


def _append_row(
    text: str, headers: tuple[str, ...], values: list[str]
) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _cells(line) != list(headers):
            continue
        cursor = index + 2
        while cursor < len(lines) and _cells(lines[cursor]) is not None:
            cursor += 1
        lines.insert(cursor, "| " + " | ".join(values) + " |")
        return "\n".join(lines) + "\n"
    raise TrackingCommandError(f"No se encontró la tabla {headers[0]}.")


def _frontmatter_date(text: str, change_date: str) -> str:
    updated, count = re.subn(
        r'^last_updated: "[0-9]{4}-[0-9]{2}-[0-9]{2}"$',
        f'last_updated: "{change_date}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise TrackingCommandError("No se pudo actualizar last_updated.")
    return updated


def _mutation_hash(
    originals: list[bytes], replacements: list[bytes], payload: dict[str, Any]
) -> str:
    digest = hashlib.sha256()
    for original, replacement in zip(originals, replacements, strict=True):
        digest.update(hashlib.sha256(original).digest())
        digest.update(hashlib.sha256(replacement).digest())
    digest.update(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    )
    return digest.hexdigest()


def _apply_atomic(
    paths: list[Path], originals: list[bytes], replacements: list[bytes]
) -> None:
    temporaries: list[Path] = []
    replaced = 0
    try:
        for path, content in zip(paths, replacements, strict=True):
            temporary = path.with_name(path.name + ".lks-sdd-tracking.tmp")
            with temporary.open("xb") as stream:
                stream.write(content)
            temporaries.append(temporary)
        for path, original in zip(paths, originals, strict=True):
            if path.read_bytes() != original:
                raise TrackingCommandError(f"{path.name} cambió después del preview.")
        for path, temporary in zip(paths, temporaries, strict=True):
            os.replace(temporary, path)
            replaced += 1
    except (OSError, TrackingCommandError):
        for index in range(replaced):
            paths[index].write_bytes(originals[index])
        for temporary in temporaries[replaced:]:
            try:
                temporary.unlink()
            except OSError:
                pass
        raise


def _apply_and_validate(
    root: Path,
    paths: list[Path],
    originals: list[bytes],
    replacements: list[bytes],
) -> None:
    """Commit local contract changes atomically and roll them back if invalid."""

    _apply_atomic(paths, originals, replacements)
    try:
        from validate_project import validate_project

        report, _, _ = validate_project(root)
        if not report.valid:
            raise TrackingCommandError(
                "La mutación dejaría inválido el proyecto: "
                + "; ".join(report.errors)
            )
    except Exception as exc:
        try:
            _apply_atomic(paths, replacements, originals)
        except Exception as rollback_exc:
            raise TrackingCommandError(
                "Falló la validación posterior y no se pudo restaurar el contrato: "
                f"{rollback_exc}"
            ) from exc
        if isinstance(exc, TrackingCommandError):
            raise
        raise TrackingCommandError(
            f"Falló la validación posterior; se restauró el contrato: {exc}"
        ) from exc


def _configuration_replacement(
    root: Path, manifest: dict[str, Any], args: argparse.Namespace
) -> tuple[Path, bytes, bytes, dict[str, Any]]:
    contract = load_tracking_contract(root, manifest)
    binding_id = contract["binding"].get("Binding")
    if not re.fullmatch(r"TRK-[0-9]{3}", binding_id or ""):
        raise TrackingCommandError("El binding activo no usa TRK-###.")
    decision = _safe_cell("--decision", args.decision)
    if not re.fullmatch(r"ADR-[0-9]{3}", decision):
        raise TrackingCommandError("--decision debe usar ADR-###.")
    try:
        require_confirmed_tracking_decision(root, decision, args.mode)
    except TrackingContractError as exc:
        raise TrackingCommandError(str(exc)) from exc
    change_date = _iso_date(args.date)
    durable_mappings = [
        mapping
        for mapping in contract["mapping_rows"]
        if any(
            mapping.get(column) not in {
                "",
                "pending",
                "none",
                "unknown",
                "not-recorded",
            }
            for column in (
                "External ID",
                "External key",
                "URL",
                "Projection fingerprint",
                "Last operation",
            )
        )
    ]
    durable_state = bool(durable_mappings or contract["operations"])
    coordination_gate = "not-required"
    if args.mode == "repository-only":
        if durable_state and contract["binding"].get("Mode") != "repository-only":
            raise TrackingCommandError(
                "No se puede abandonar Jira mientras existan mappings durables; "
                "0.10 no ofrece detach/rebind y exige preservar este binding o iniciar "
                "un nuevo contrato de proyecto."
            )
        row = {
            "State": "confirmed",
            "Mode": "repository-only",
            "Provider": "none",
            "Site": "not-applicable",
            "Project": "not-applicable",
            "Issue type": "not-applicable",
            "Sync policy": "not-required",
            "Write policy": "local-only",
            "Decision": decision,
            "Last reviewed": change_date,
        }
        index_updates: dict[str, Any] = {
            "state": "confirmed",
            "mode": "repository-only",
            "provider": None,
            "decision": decision,
            "site": None,
            "project_key": None,
            "issue_type": None,
            "sync_policy": "not-required",
            "write_policy": "local-only",
            "projection_fingerprint": None,
            "sync_status": "not-required",
            "last_sync_on": None,
        }
    else:
        site = _https_url("--site", args.site or "")
        project = _safe_cell("--project", args.project or "")
        issue_type = _safe_cell("--issue-type", args.issue_type or "")
        if not re.fullmatch(r"[A-Z][A-Z0-9]+", project):
            raise TrackingCommandError(
                "--project debe ser una clave Jira Cloud de al menos 2 caracteres, "
                "iniciada por mayúscula y formada solo por mayúsculas o números."
            )
        current_target = (
            contract["binding"].get("Site"),
            contract["binding"].get("Project"),
            contract["binding"].get("Issue type"),
        )
        requested_target = (site, project, issue_type)
        if durable_state and (
            contract["binding"].get("Mode") != "jira-hybrid"
            or current_target != requested_target
        ):
            raise TrackingCommandError(
                "No se puede cambiar o recuperar el destino Jira mientras existan "
                "mappings durables; 0.10 no ofrece detach/rebind y exige preservar "
                "este binding o iniciar un nuevo contrato de proyecto."
            )
        coordination_gate = (
            getattr(args, "coordination_gate", None)
            or "required-before-execution"
        )
        if manifest.get("schema_version") == "1.4":
            coordination_gate = "required-before-execution"
        row = {
            "State": "confirmed",
            "Mode": "jira-hybrid",
            "Provider": "atlassian-rovo",
            "Site": site,
            "Project": project,
            "Issue type": issue_type,
            "Sync policy": coordination_gate,
            "Write policy": "preview-and-confirm",
            "Decision": decision,
            "Last reviewed": change_date,
        }
        index_updates = {
            "state": "confirmed",
            "mode": "jira-hybrid",
            "provider": "atlassian-rovo",
            "decision": decision,
            "site": site,
            "project_key": project,
            "issue_type": issue_type,
            "sync_policy": coordination_gate,
            "write_policy": "preview-and-confirm",
            "projection_fingerprint": None,
            "sync_status": "pending",
            "last_sync_on": None,
        }
        if durable_state:
            current_index = manifest.get("task_tracking", {})
            for field in (
                "projection_fingerprint",
                "sync_status",
                "last_sync_on",
            ):
                index_updates[field] = current_index.get(field)
    updated_text = _replace_row(contract["text"], BINDING_HEADERS, binding_id, row)
    if manifest.get("schema_version") == "1.5":
        reporting_scope = (
            "not-applicable"
            if args.mode == "repository-only"
            else getattr(args, "reporting_scope", None) or "projection-only"
        )
        reporting_state = "confirmed"
        reporting_row = {
            "State": reporting_state,
            "Scope": reporting_scope,
            "Coordination gate": (
                "not-required"
                if args.mode == "repository-only"
                else coordination_gate
            ),
            "Comment policy": (
                "milestones-only"
                if reporting_scope == "milestone-reporting"
                else "not-applicable"
            ),
            "Decision": decision,
            "Last reviewed": change_date,
        }
        updated_text = _replace_row(
            updated_text,
            REPORTING_HEADERS,
            contract["reporting"].get("Reporting", "RPT-001"),
            reporting_row,
        )
        index_updates.update(
            reporting_scope=reporting_scope,
            coordination_gate=(
                "not-required"
                if args.mode == "repository-only"
                else coordination_gate
            ),
            reporting_status=(
                "not-required"
                if reporting_scope in {"not-applicable", "projection-only"}
                else "ready"
            ),
            last_reported_on=None,
        )
    updated_text = _frontmatter_date(updated_text, change_date)
    updated_manifest = json.loads(json.dumps(manifest))
    task_tracking = updated_manifest.get("task_tracking")
    if not isinstance(task_tracking, dict):
        raise TrackingCommandError("project.json no contiene task_tracking.")
    task_tracking.update(index_updates)
    replacement = (json.dumps(updated_manifest, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    payload = {
        "action": "configure-task-tracking",
        "binding_id": binding_id,
        "mode": args.mode,
        "decision": decision,
        "date": change_date,
        "jira_target": None
        if args.mode == "repository-only"
        else {"site": args.site, "project": args.project, "issue_type": args.issue_type},
        "reporting_scope": index_updates.get("reporting_scope"),
        "coordination_gate": index_updates.get("coordination_gate"),
    }
    return contract["path"], contract["text"].encode("utf-8"), updated_text.encode(
        "utf-8"
    ), {"manifest": replacement, "payload": payload}


def configure(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    manifest_path, manifest, manifest_original = _load_manifest(root)
    tracking_path, tracking_original, tracking_replacement, detail = (
        _configuration_replacement(root, manifest, args)
    )
    replacements = [detail["manifest"], tracking_replacement]
    originals = [manifest_original, tracking_original]
    mutation_hash = _mutation_hash(originals, replacements, detail["payload"])
    result = {**detail["payload"], "mutation_hash": mutation_hash, "applied": False}
    if args.apply:
        if args.authorize != mutation_hash:
            raise TrackingCommandError(
                "--apply exige --authorize con el mutation_hash exacto del preview."
            )
        _apply_and_validate(
            root, [manifest_path, tracking_path], originals, replacements
        )
        result["applied"] = True
    return result


def _next_operation_id(operations: list[dict[str, str]]) -> str:
    numbers = [
        int(match.group(1))
        for row in operations
        if (match := re.fullmatch(r"SYNC-([0-9]{3})", row.get("ID", "")))
    ]
    number = max(numbers, default=0) + 1
    if number > 999:
        raise TrackingCommandError("Se agotó el espacio SYNC-###.")
    return f"SYNC-{number:03d}"


def _projection_set_hash(operations: list[dict[str, Any]]) -> str:
    projected = {
        item["task_id"]: item["payload"]["projection_fingerprint"]
        for item in operations
    }
    return hashlib.sha256(
        json.dumps(
            projected, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def _aggregate_sync_state(
    operations: list[dict[str, Any]],
    task_id: str,
    result: str,
    *,
    selected_action: str | None = None,
) -> tuple[str, str | None]:
    actions = {
        item["task_id"]: (
            selected_action or {
                "succeeded": "noop",
                "failed": "failed",
                "conflict": "blocked-reconciliation",
                "uncertain": "blocked-reconciliation",
            }[result]
            if item["task_id"] == task_id
            else item["action"]
        )
        for item in operations
    }
    if any(action == "blocked-reconciliation" for action in actions.values()):
        return "reconciliation-required", None
    if any(action == "failed" for action in actions.values()):
        return "failed", None
    if any(action in {"create", "awaiting-execution"} for action in actions.values()):
        return "pending", None
    if any(action == "update" for action in actions.values()):
        return "out-of-sync", None
    return "in-sync", _projection_set_hash(operations)


def _ledger_operations(
    root: Path,
    manifest: dict[str, Any],
    contract: dict[str, Any],
    task_id: str,
    projection_fingerprint: str,
) -> list[dict[str, Any]]:
    action_by_state = {
        "pending": "awaiting-execution",
        "synced": "update",
        "out-of-sync": "update",
        "conflict": "blocked-reconciliation",
        "reconciliation-required": "blocked-reconciliation",
        "failed": "failed",
        "unlinked": "create",
    }
    delivery = validate_delivery_contract(root, manifest)
    rows_by_task = {
        row["Task"]: row for row in contract["mapping_rows"]
    }
    candidates = (
        set(delivery.get("tasks", {})) | set(rows_by_task) | {task_id}
    )
    operations: list[dict[str, Any]] = []
    for candidate in sorted(candidates):
        try:
            candidate_preview = build_projection_preview(
                root, manifest, [candidate]
            )
        except TrackingPlanningBlocked:
            row = rows_by_task.get(candidate)
            if row is None and candidate != task_id:
                continue
            row = row or {
                "Task": candidate,
                "State": "unlinked",
                "Projection fingerprint": projection_fingerprint,
            }
            operations.append(
                {
                    "task_id": candidate,
                    "action": action_by_state.get(
                        row.get("State", ""), "create"
                    ),
                    "payload": {
                        "projection_fingerprint": (
                            projection_fingerprint
                            if candidate == task_id
                            else row.get("Projection fingerprint", "")
                        )
                    },
                }
            )
            continue
        except TrackingContractError:
            row = rows_by_task.get(candidate)
            operations.append(
                {
                    "task_id": candidate,
                    "action": (
                        action_by_state.get(row.get("State", ""), "failed")
                        if row is not None
                        else "failed"
                    ),
                    "payload": {
                        "projection_fingerprint": (
                            projection_fingerprint
                            if candidate == task_id
                            else (row or {}).get("Projection fingerprint", "")
                        )
                    },
                }
            )
            continue
        operations.append(candidate_preview["operations"][0])
    return operations


IDENTITY_PLACEHOLDERS = {"", "pending", "none", "unknown", "not-recorded"}


def _known_identity(value: str | None) -> bool:
    return value not in IDENTITY_PLACEHOLDERS and value is not None


def _same_origin(left: str, right: str) -> bool:
    try:
        first = urlparse(left)
        second = urlparse(right)
        return (
            first.scheme.casefold(),
            first.hostname.casefold() if first.hostname else None,
            first.port,
        ) == (
            second.scheme.casefold(),
            second.hostname.casefold() if second.hostname else None,
            second.port,
        )
    except ValueError:
        return False


def _validate_external_identity(
    contract: dict[str, Any],
    task_id: str,
    external_id: str,
    external_key: str,
    url: str,
    *,
    require_complete: bool,
) -> None:
    binding = contract["binding"]
    if require_complete and not (
        _known_identity(external_id)
        and _known_identity(external_key)
        and _known_identity(url)
    ):
        raise TrackingCommandError(
            "Un resultado succeeded exige --external-id, --external-key y --url."
        )
    if _known_identity(external_id) and not re.fullmatch(
        r"[1-9][0-9]{0,30}", external_id
    ):
        raise TrackingCommandError(
            "--external-id debe ser el identificador Jira numérico observado."
        )
    if _known_identity(external_key) and not external_key_matches_project(
        binding.get("Project", ""), external_key
    ):
        raise TrackingCommandError(
            "--external-key no pertenece exactamente al proyecto Jira configurado."
        )
    if _known_identity(url):
        normalized_url = _https_url("--url", url)
        if not _same_origin(binding.get("Site", ""), normalized_url):
            raise TrackingCommandError(
                "--url pertenece a otro site Jira distinto del binding confirmado."
            )
        if _known_identity(external_key) and not url_matches_external_key(
            normalized_url, external_key
        ):
            raise TrackingCommandError(
                "--url no corresponde a --external-key."
            )
    for other_task, mapping in contract["mappings"].items():
        if other_task == task_id:
            continue
        if _known_identity(external_id) and mapping.get("External ID") == external_id:
            raise TrackingCommandError(
                f"External ID ya está ligado a {other_task}; no se registra."
            )
        if _known_identity(external_key) and mapping.get(
            "External key", ""
        ).casefold() == external_key.casefold():
            raise TrackingCommandError(
                f"External key ya está ligada a {other_task}; no se registra."
            )
    if _known_identity(external_key):
        for receipt in contract["operations"]:
            historical_key = receipt.get("External key", "")
            if (
                not _known_identity(historical_key)
                or historical_key.casefold() != external_key.casefold()
            ):
                continue
            historical_task = receipt.get("Task", "")
            historical_id = receipt.get("External ID", "")
            id_conflict = (
                _known_identity(external_id)
                and _known_identity(historical_id)
                and historical_id != external_id
            )
            if historical_task != task_id or id_conflict:
                raise TrackingCommandError(
                    "External key ya figura en el historial con otra identidad "
                    f"({historical_task}/{historical_id}); no se registra."
                )


def _manifest_bytes(manifest: dict[str, Any]) -> bytes:
    return (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _operation_by_id(
    contract: dict[str, Any], sync_id: str
) -> dict[str, str]:
    matches = [row for row in contract["operations"] if row.get("ID") == sync_id]
    if len(matches) != 1:
        raise TrackingCommandError(f"{sync_id} no identifica un único recibo.")
    return matches[0]


def authorize_sync(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    """Persist the exact outbound intent before any Rovo write is attempted."""

    if not args.apply:
        raise TrackingCommandError(
            "authorize-sync persiste una autorización duradera y exige --apply."
        )
    manifest_path, manifest, manifest_original = _load_manifest(root)
    try:
        preview = build_projection_preview(root, manifest, [args.task])
    except TrackingContractError as exc:
        raise TrackingCommandError(str(exc)) from exc
    if preview["preview_hash"] != args.preview_hash:
        raise TrackingCommandError(
            "El preview actual no coincide con --preview-hash; no se autoriza."
        )
    operation = preview["operations"][0]
    if operation["action"] not in {"create", "update"}:
        raise TrackingCommandError(
            f"La operación actual es {operation['action']}; no admite una escritura Jira."
        )
    expected_duplicate_check = (
        "no-match" if operation["action"] == "create" else "matched"
    )
    if args.duplicate_check != expected_duplicate_check:
        raise TrackingCommandError(
            f"{operation['action']} exige --duplicate-check "
            f"{expected_duplicate_check}; la búsqueda Rovo debe preceder a la autorización."
        )
    authorized_on = _iso_date(args.authorized_on)
    authorized_by_role = _safe_cell(
        "--authorized-by-role", args.authorized_by_role
    )
    contract = load_tracking_contract(root, manifest)
    existing = contract["mappings"].get(args.task)
    if existing and existing.get("State") == "pending":
        raise TrackingCommandError(
            "La TASK ya tiene una escritura autorizada pendiente; registre su resultado."
        )
    projection_fingerprint = operation["payload"]["projection_fingerprint"]
    sync_id = _next_operation_id(contract["operations"])
    notes = _safe_cell(
        "--notes", args.notes or "authorized outbound Jira projection"
    )
    external_id = (
        existing.get("External ID", "pending")
        if existing and _known_identity(existing.get("External ID"))
        else "pending"
    )
    external_key = (
        existing.get("External key", "pending")
        if existing and _known_identity(existing.get("External key"))
        else "pending"
    )
    mapping_values = {
        "State": "pending",
        "External ID": external_id,
        "External key": external_key,
        "URL": existing.get("URL", "pending") if existing else "pending",
        "Projection fingerprint": existing.get(
            "Projection fingerprint", "pending"
        )
        if existing
        else "pending",
        "Remote status": existing.get("Remote status", "pending")
        if existing
        else "pending",
        "Last synced": existing.get("Last synced", "pending")
        if existing
        else "pending",
        "Last operation": sync_id,
        "Notes": notes,
    }
    if existing:
        updated_text = _replace_row(
            contract["text"], MAPPING_HEADERS, args.task, mapping_values
        )
    else:
        updated_text = _append_row(
            contract["text"],
            MAPPING_HEADERS,
            [args.task] + [mapping_values[item] for item in MAPPING_HEADERS[1:]],
        )
    updated_text = _append_row(
        updated_text,
        OPERATION_HEADERS,
        [
            sync_id,
            "authorized",
            args.task,
            operation["action"],
            preview["preview_hash"],
            projection_fingerprint,
            args.duplicate_check,
            authorized_by_role,
            authorized_on,
            external_id,
            external_key,
            authorized_on,
            "pending",
            notes,
        ],
    )
    updated_text = _frontmatter_date(updated_text, authorized_on)
    updated_manifest = json.loads(json.dumps(manifest))
    index = updated_manifest["task_tracking"]
    aggregate_operations = _ledger_operations(
        root, manifest, contract, args.task, projection_fingerprint
    )
    aggregate_status, aggregate_fingerprint = _aggregate_sync_state(
        aggregate_operations,
        args.task,
        "succeeded",
        selected_action="awaiting-execution",
    )
    index["projection_fingerprint"] = aggregate_fingerprint
    index["sync_status"] = aggregate_status
    manifest_replacement = _manifest_bytes(updated_manifest)
    _apply_and_validate(
        root,
        [manifest_path, contract["path"]],
        [manifest_original, contract["text"].encode("utf-8")],
        [manifest_replacement, updated_text.encode("utf-8")],
    )
    return {
        "applied": True,
        "sync_id": sync_id,
        "task": args.task,
        "action": operation["action"],
        "preview_hash": preview["preview_hash"],
        "projection_fingerprint": projection_fingerprint,
        "external_write_authorized": True,
        "projection": operation,
    }


def _result_identity(
    contract: dict[str, Any],
    task_id: str,
    args: argparse.Namespace,
    *,
    reconciliation: bool,
) -> tuple[str, str, str, str, str]:
    existing = contract["mappings"].get(task_id, {})
    if args.result == "succeeded" and not (
        args.external_id and args.external_key and args.url
    ):
        raise TrackingCommandError(
            "Un resultado succeeded exige observar y proporcionar --external-id, "
            "--external-key y --url en esta lectura Rovo."
        )
    existing_id = existing.get("External ID", "pending")
    supplied_id = _safe_cell("--external-id", args.external_id) if args.external_id else None
    if _known_identity(existing_id) and supplied_id and supplied_id != existing_id:
        raise TrackingCommandError(
            "External ID es inmutable; el resultado no coincide con el mapping."
        )
    external_id = supplied_id or existing_id or "pending"
    external_key = (
        _safe_cell("--external-key", args.external_key)
        if args.external_key
        else existing.get("External key", "pending")
    )
    url = (
        _https_url("--url", args.url)
        if args.url
        else existing.get("URL", "not-recorded")
    )
    remote_status = (
        _safe_cell("--remote-status", args.remote_status)
        if args.remote_status
        else existing.get("Remote status", "unknown")
    )
    notes = _safe_cell(
        "--notes",
        args.notes
        or ("recorded Jira reconciliation" if reconciliation else "recorded authorized Jira write"),
    )
    if args.result == "succeeded":
        _validate_external_identity(
            contract,
            task_id,
            external_id,
            external_key,
            url,
            require_complete=True,
        )
    else:
        _validate_external_identity(
            contract,
            task_id,
            external_id,
            external_key,
            url,
            require_complete=False,
        )
    if reconciliation and args.result == "failed" and _known_identity(existing_id):
        raise TrackingCommandError(
            "No se puede declarar not-found para una identidad estable; registre conflict o uncertain."
        )
    return external_id, external_key, url, remote_status, notes


def _finalize_tracking_result(
    root: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    manifest_original: bytes,
    contract: dict[str, Any],
    preview: dict[str, Any],
    task_id: str,
    sync_id: str,
    result: str,
    change_date: str,
    authorized_by_role: str,
    authorized_on: str,
    external_id: str,
    external_key: str,
    url: str,
    remote_status: str,
    notes: str,
    *,
    action: str,
    duplicate_check: str,
    replace_operation: bool,
    mapping_state_override: str | None = None,
    aggregate_operations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result_state = mapping_state_override or {
        "succeeded": "synced",
        "failed": "failed",
        "conflict": "conflict",
        "uncertain": "reconciliation-required",
    }[result]
    operation_state = {
        "succeeded": "recorded",
        "failed": "failed",
        "conflict": "conflict",
        "uncertain": "reconciliation-required",
    }[result]
    projection_fingerprint = preview["operations"][0]["payload"][
        "projection_fingerprint"
    ]
    existing = contract["mappings"].get(task_id, {})
    mapping_values = {
        "State": result_state,
        "External ID": external_id,
        "External key": external_key,
        "URL": url,
        "Projection fingerprint": projection_fingerprint
        if result == "succeeded"
        else existing.get("Projection fingerprint", projection_fingerprint),
        "Remote status": remote_status,
        "Last synced": change_date
        if result == "succeeded"
        else existing.get("Last synced", "pending"),
        "Last operation": sync_id,
        "Notes": notes,
    }
    if existing:
        updated_text = _replace_row(
            contract["text"], MAPPING_HEADERS, task_id, mapping_values
        )
    else:
        updated_text = _append_row(
            contract["text"],
            MAPPING_HEADERS,
            [task_id] + [mapping_values[item] for item in MAPPING_HEADERS[1:]],
        )
    operation_values = {
        "State": operation_state,
        "Task": task_id,
        "Action": action,
        "Preview hash": preview["preview_hash"],
        "Projection fingerprint": projection_fingerprint,
        "Duplicate check": duplicate_check,
        "Authorized by role": authorized_by_role,
        "Authorized on": authorized_on,
        "External ID": external_id,
        "External key": external_key,
        "Recorded on": change_date,
        "Result": result,
        "Notes": notes,
    }
    if replace_operation:
        updated_text = _replace_row(
            updated_text, OPERATION_HEADERS, sync_id, operation_values
        )
    else:
        updated_text = _append_row(
            updated_text,
            OPERATION_HEADERS,
            [sync_id] + [operation_values[item] for item in OPERATION_HEADERS[1:]],
        )
    updated_text = _frontmatter_date(updated_text, change_date)
    updated_manifest = json.loads(json.dumps(manifest))
    aggregate_status, aggregate_fingerprint = _aggregate_sync_state(
        aggregate_operations or [],
        task_id,
        result,
        selected_action=(
            "update" if mapping_state_override == "out-of-sync" else None
        ),
    )
    index = updated_manifest["task_tracking"]
    index["projection_fingerprint"] = aggregate_fingerprint
    index["sync_status"] = aggregate_status
    index["last_sync_on"] = change_date
    _apply_and_validate(
        root,
        [manifest_path, contract["path"]],
        [manifest_original, contract["text"].encode("utf-8")],
        [_manifest_bytes(updated_manifest), updated_text.encode("utf-8")],
    )
    return {
        "applied": True,
        "sync_id": sync_id,
        "task": task_id,
        "action": action,
        "result": result,
        "mapping_state": result_state,
        "external_id": None if not _known_identity(external_id) else external_id,
        "external_key": None if not _known_identity(external_key) else external_key,
        "preview_hash": preview["preview_hash"],
    }


def record_result(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    """Close one previously persisted outbound authorization receipt."""

    if not args.apply:
        raise TrackingCommandError("record-result exige --apply.")
    manifest_path, manifest, manifest_original = _load_manifest(root)
    contract = load_tracking_contract(root, manifest)
    receipt = _operation_by_id(contract, args.sync_id)
    if receipt.get("State") != "authorized" or receipt.get("Result") != "pending":
        raise TrackingCommandError(
            f"{args.sync_id} no es una escritura autorizada pendiente."
        )
    task_id = receipt["Task"]
    mapping = contract["mappings"].get(task_id, {})
    if mapping.get("Last operation") != args.sync_id or mapping.get("State") != "pending":
        raise TrackingCommandError(
            f"{task_id} no está pendiente del recibo {args.sync_id}."
        )
    intended_fingerprint = receipt.get("Projection fingerprint", "")
    if args.result == "succeeded":
        observed_marker = _safe_cell(
            "--observed-correlation-marker",
            args.observed_correlation_marker or "",
        )
        if observed_marker != correlation_marker(
            str(manifest.get("project_id", "")), task_id
        ):
            raise TrackingCommandError(
                "El marcador observado en Jira no corresponde a la TASK autorizada."
            )
        observed_fingerprint = _safe_cell(
            "--observed-projection-fingerprint",
            args.observed_projection_fingerprint or "",
        )
        if not re.fullmatch(r"[a-f0-9]{64}", observed_fingerprint):
            raise TrackingCommandError(
                "--observed-projection-fingerprint debe ser un SHA-256 hexadecimal."
            )
        if observed_fingerprint != intended_fingerprint:
            raise TrackingCommandError(
                "La huella observada en Jira no coincide con la intención autorizada; "
                "registre conflict o uncertain."
            )
    current_matches = False
    aggregate_operations = _ledger_operations(
        root, manifest, contract, task_id, intended_fingerprint
    )
    try:
        current_preview = build_projection_preview(root, manifest, [task_id])
        current_matches = (
            current_preview["operations"][0]["payload"]["projection_fingerprint"]
            == intended_fingerprint
        )
    except TrackingContractError:
        # The durable receipt still closes the external fact. Drift is represented
        # locally as out-of-sync instead of losing the already executed write.
        current_matches = False
    preview = {
        "preview_hash": receipt["Preview hash"],
        "operations": [
            {"payload": {"projection_fingerprint": intended_fingerprint}}
        ],
    }
    change_date = _iso_date(args.date)
    if receipt["Authorized on"] > change_date:
        raise TrackingCommandError("--date no puede preceder a la autorización.")
    identity = _result_identity(
        contract, task_id, args, reconciliation=False
    )
    return _finalize_tracking_result(
        root,
        manifest_path,
        manifest,
        manifest_original,
        contract,
        preview,
        task_id,
        args.sync_id,
        args.result,
        change_date,
        receipt["Authorized by role"],
        receipt["Authorized on"],
        *identity,
        action=receipt["Action"],
        duplicate_check=receipt["Duplicate check"],
        replace_operation=True,
        mapping_state_override=(
            "out-of-sync"
            if args.result == "succeeded" and not current_matches
            else None
        ),
        aggregate_operations=aggregate_operations,
    )


def reconcile_result(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    """Record an authorized Rovo read used to reconcile uncertain identity/state."""

    if not args.apply:
        raise TrackingCommandError("reconcile-result exige --apply.")
    manifest_path, manifest, manifest_original = _load_manifest(root)
    contract = load_tracking_contract(root, manifest)
    if args.task not in contract["mappings"]:
        raise TrackingCommandError(
            "reconcile-result exige un mapping previo que necesite observación remota."
        )
    mapping = contract["mappings"][args.task]
    if mapping.get("Last operation") != args.anchor_sync_id:
        raise TrackingCommandError(
            "--anchor-sync-id debe ser el último recibo durable de la TASK."
        )
    anchor = _operation_by_id(contract, args.anchor_sync_id)
    if anchor.get("Task") != args.task or anchor.get("State") == "authorized":
        raise TrackingCommandError(
            "El recibo ancla no es un resultado cerrado reconciliable para esta TASK."
        )
    anchor_fingerprint = anchor.get("Projection fingerprint", "")
    if not re.fullmatch(r"[a-f0-9]{64}", anchor_fingerprint):
        raise TrackingCommandError("El recibo ancla no conserva una huella válida.")
    current_fingerprint: str | None = None
    try:
        current = build_projection_preview(root, manifest, [args.task])
        current_fingerprint = current["operations"][0]["payload"][
            "projection_fingerprint"
        ]
    except TrackingContractError:
        # Reconciliation is anchored in the durable receipt precisely so that a
        # later plan drift cannot erase an already observed external fact.
        current_fingerprint = None
    reconciliation_intent = {
        "contract": "lks-sdd-jira-reconciliation/1.0",
        "project_id": manifest.get("project_id"),
        "binding_id": contract["binding"].get("Binding"),
        "task_id": args.task,
        "anchor_sync_id": args.anchor_sync_id,
        "anchor_projection_fingerprint": anchor_fingerprint,
        "current_projection_fingerprint": current_fingerprint,
        "correlation_marker": correlation_marker(
            str(manifest.get("project_id", "")), args.task
        ),
    }
    reconciliation_hash = hashlib.sha256(
        json.dumps(
            reconciliation_intent,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    preview = {
        "preview_hash": reconciliation_hash,
        "operations": [
            {
                "task_id": args.task,
                "correlation_marker": correlation_marker(
                    str(manifest.get("project_id", "")), args.task
                ),
                "payload": {"projection_fingerprint": anchor_fingerprint},
            }
        ],
    }
    change_date = _iso_date(args.date)
    authorized_on = _iso_date(args.authorized_on)
    if authorized_on > change_date:
        raise TrackingCommandError("--authorized-on no puede ser posterior a --date.")
    authorized_by_role = _safe_cell(
        "--authorized-by-role", args.authorized_by_role
    )
    identity = _result_identity(
        contract, args.task, args, reconciliation=True
    )
    if args.result == "succeeded":
        observed_marker = _safe_cell(
            "--observed-correlation-marker",
            args.observed_correlation_marker or "",
        )
        if observed_marker != correlation_marker(
            str(manifest.get("project_id", "")), args.task
        ):
            raise TrackingCommandError(
                "El marcador observado en Jira no corresponde a la TASK reconciliada."
            )
        observed_fingerprint = _safe_cell(
            "--observed-projection-fingerprint",
            args.observed_projection_fingerprint or "",
        )
        expected_fingerprint = preview["operations"][0]["payload"][
            "projection_fingerprint"
        ]
        if not re.fullmatch(r"[a-f0-9]{64}", observed_fingerprint):
            raise TrackingCommandError(
                "--observed-projection-fingerprint debe ser un SHA-256 hexadecimal."
            )
        if observed_fingerprint != expected_fingerprint:
            if observed_fingerprint != current_fingerprint:
                raise TrackingCommandError(
                    "La huella observada en Jira no coincide ni con el recibo ancla "
                    "ni con la proyección actual; registre conflict o uncertain."
                )
        preview["operations"][0]["payload"][
            "projection_fingerprint"
        ] = observed_fingerprint
    sync_id = _next_operation_id(contract["operations"])
    aggregate_operations = _ledger_operations(
        root,
        manifest,
        contract,
        args.task,
        preview["operations"][0]["payload"]["projection_fingerprint"],
    )
    duplicate_check = {
        "succeeded": "matched",
        "failed": "no-match",
        "conflict": "conflict",
        "uncertain": "uncertain",
    }[args.result]
    return _finalize_tracking_result(
        root,
        manifest_path,
        manifest,
        manifest_original,
        contract,
        preview,
        args.task,
        sync_id,
        args.result,
        change_date,
        authorized_by_role,
        authorized_on,
        *identity,
        action="reconcile",
        duplicate_check=duplicate_check,
        replace_operation=False,
        mapping_state_override=(
            "out-of-sync"
            if args.result == "succeeded"
            and observed_fingerprint != current_fingerprint
            else None
        ),
        aggregate_operations=aggregate_operations,
    )


def _next_shared_sync_id(contract: dict[str, Any]) -> str:
    numbers = [
        int(match.group(1))
        for row in [
            *contract.get("operations", []),
            *contract.get("milestone_operations", []),
        ]
        if (match := re.fullmatch(r"SYNC-([0-9]{3})", row.get("ID", "")))
    ]
    number = max(numbers, default=0) + 1
    if number > 999:
        raise TrackingCommandError("Se agotó el espacio SYNC-###.")
    return f"SYNC-{number:03d}"


def _reporting_status(
    reporting: dict[str, str], operations: list[dict[str, str]]
) -> str:
    if reporting.get("Scope") != "milestone-reporting":
        return "not-required"
    if reporting.get("State") == "paused":
        return "paused"
    latest: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in operations:
        latest[
            (
                row.get("Task", ""),
                row.get("Source ref", ""),
                row.get("Event kind", ""),
                row.get("Action", ""),
            )
        ] = row
    states = {row.get("State", "") for row in latest.values()}
    if states.intersection({"conflict", "reconciliation-required"}):
        return "reconciliation-required"
    if "failed" in states:
        return "failed"
    if "authorized" in states:
        return "pending"
    return "ready"


def configure_workflow(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    manifest_path, manifest, manifest_original = _load_manifest(root)
    if manifest.get("schema_version") != "1.5":
        raise TrackingCommandError("configure-workflow exige schema 1.5.")
    contract = load_tracking_contract(root, manifest)
    if (
        contract["binding"].get("Mode") != "jira-hybrid"
        or contract["reporting"].get("Scope") != "milestone-reporting"
    ):
        raise TrackingCommandError(
            "configure-workflow exige jira-hybrid con milestone-reporting."
        )
    local_state = _safe_cell("--local-state", args.local_state)
    status_id = _safe_cell("--jira-status-id", args.jira_status_id)
    if not re.fullmatch(r"[1-9][0-9]{0,30}", status_id):
        raise TrackingCommandError("--jira-status-id debe ser numérico.")
    status_name = _safe_cell("--jira-status-name", args.jira_status_name)
    decision = _safe_cell("--decision", args.decision)
    try:
        require_confirmed_tracking_decision(root, decision, "jira-hybrid")
    except TrackingContractError as exc:
        raise TrackingCommandError(str(exc)) from exc
    change_date = _iso_date(args.date)
    values = {
        "State": "confirmed",
        "Jira status ID": status_id,
        "Jira status name": status_name,
        "Decision": decision,
        "Last reviewed": change_date,
    }
    existing = contract["workflow"].get(local_state)
    if existing:
        updated_text = _replace_row(
            contract["text"], WORKFLOW_HEADERS, local_state, values
        )
    else:
        updated_text = _append_row(
            contract["text"],
            WORKFLOW_HEADERS,
            [local_state] + [values[item] for item in WORKFLOW_HEADERS[1:]],
        )
    updated_text = _frontmatter_date(updated_text, change_date)
    payload = {
        "action": "configure-jira-workflow",
        "local_state": local_state,
        "jira_status_id": status_id,
        "jira_status_name": status_name,
        "decision": decision,
        "date": change_date,
    }
    replacement = updated_text.encode("utf-8")
    original = contract["text"].encode("utf-8")
    mutation_hash = _mutation_hash([original], [replacement], payload)
    result = {**payload, "mutation_hash": mutation_hash, "applied": False}
    if args.apply:
        if args.authorize != mutation_hash:
            raise TrackingCommandError(
                "--apply exige --authorize con el mutation_hash exacto."
            )
        _apply_and_validate(root, [contract["path"]], [original], [replacement])
        result["applied"] = True
    return result


def set_reporting_state(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    manifest_path, manifest, manifest_original = _load_manifest(root)
    if manifest.get("schema_version") != "1.5":
        raise TrackingCommandError("pause-reporting/resume-reporting exige schema 1.5.")
    contract = load_tracking_contract(root, manifest)
    reporting = contract["reporting"]
    if reporting.get("Scope") != "milestone-reporting":
        raise TrackingCommandError("El proyecto no tiene milestone-reporting habilitado.")
    if any(
        row.get("State") == "authorized"
        for row in contract["milestone_operations"]
    ):
        raise TrackingCommandError(
            "Cierre o reconcilie las acciones Jira autorizadas antes de cambiar la pausa."
        )
    requested = "paused" if args.command == "pause-reporting" else "confirmed"
    change_date = _iso_date(args.date)
    updated_text = _replace_row(
        contract["text"],
        REPORTING_HEADERS,
        reporting["Reporting"],
        {"State": requested, "Last reviewed": change_date},
    )
    updated_text = _frontmatter_date(updated_text, change_date)
    updated_manifest = json.loads(json.dumps(manifest))
    updated_manifest["task_tracking"]["reporting_status"] = (
        "paused"
        if requested == "paused"
        else _reporting_status(
            {**reporting, "State": requested},
            contract["milestone_operations"],
        )
    )
    payload = {
        "action": args.command,
        "reporting_id": reporting["Reporting"],
        "state": requested,
        "date": change_date,
    }
    replacements = [
        _manifest_bytes(updated_manifest),
        updated_text.encode("utf-8"),
    ]
    originals = [manifest_original, contract["text"].encode("utf-8")]
    mutation_hash = _mutation_hash(originals, replacements, payload)
    result = {**payload, "mutation_hash": mutation_hash, "applied": False}
    if args.apply:
        if args.authorize != mutation_hash:
            raise TrackingCommandError(
                "--apply exige --authorize con el mutation_hash exacto."
            )
        _apply_and_validate(
            root,
            [manifest_path, contract["path"]],
            originals,
            replacements,
        )
        result["applied"] = True
    return result


def _event_preview(root: Path, manifest: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    return build_milestone_preview(
        root,
        manifest,
        task_id=args.task,
        source_ref=args.source_ref,
        event_kind=args.event_kind,
        observed_status_id=getattr(args, "observed_status_id", None),
        transition_id=getattr(args, "transition_id", None),
    )


def authorize_event(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not args.apply:
        raise TrackingCommandError("authorize-event exige --apply.")
    manifest_path, manifest, manifest_original = _load_manifest(root)
    contract = load_tracking_contract(root, manifest)
    preview = _event_preview(root, manifest, args)
    if preview["preview_hash"] != args.preview_hash:
        raise TrackingCommandError(
            "El preview cambió; repita la lectura Jira y confirme el hash nuevo."
        )
    dispositions = {
        item.get("disposition") for item in preview["operations"]
    }
    if dispositions != {"write"}:
        raise TrackingCommandError(
            "El hito no admite otra escritura: " + ", ".join(sorted(dispositions))
        )
    if args.comment_check != "no-match":
        raise TrackingCommandError(
            "Una autorización de comentario exige búsqueda exacta del marker sin coincidencias."
        )
    authorized_on = _iso_date(args.authorized_on)
    authorized_by_role = _safe_cell(
        "--authorized-by-role", args.authorized_by_role
    )
    updated_text = contract["text"]
    sync_ids: list[str] = []
    numeric = int(_next_shared_sync_id(contract).removeprefix("SYNC-"))
    for offset, operation in enumerate(preview["operations"]):
        sync_id = f"SYNC-{numeric + offset:03d}"
        if numeric + offset > 999:
            raise TrackingCommandError("Se agotó el espacio SYNC-###.")
        sync_ids.append(sync_id)
        duplicate_check = (
            "no-match" if operation["action"] == "comment" else "matched"
        )
        note = (
            f"event-marker={preview['event_marker']}"
            if operation["action"] == "comment"
            else f"target-status-id={operation['payload']['target_status_id']}"
        )
        updated_text = _append_row(
            updated_text,
            MILESTONE_OPERATION_HEADERS,
            [
                sync_id,
                "authorized",
                args.task,
                args.source_ref,
                args.event_kind,
                operation["action"],
                operation["event_hash"],
                preview["preview_hash"],
                duplicate_check,
                authorized_by_role,
                authorized_on,
                str(operation["external_id"]),
                str(operation["external_key"]),
                authorized_on,
                "pending",
                note,
            ],
        )
    updated_text = _frontmatter_date(updated_text, authorized_on)
    updated_manifest = json.loads(json.dumps(manifest))
    updated_manifest["task_tracking"]["reporting_status"] = "pending"
    _apply_and_validate(
        root,
        [manifest_path, contract["path"]],
        [manifest_original, contract["text"].encode("utf-8")],
        [_manifest_bytes(updated_manifest), updated_text.encode("utf-8")],
    )
    return {
        "applied": True,
        "preview_hash": preview["preview_hash"],
        "event_hash": preview["operations"][0]["event_hash"],
        "sync_ids": sync_ids,
        "external_write_authorized": True,
        "operations": [
            {**operation, "sync_id": sync_id}
            for operation, sync_id in zip(preview["operations"], sync_ids, strict=True)
        ],
    }


def _milestone_by_id(contract: dict[str, Any], sync_id: str) -> dict[str, str]:
    matches = [
        row
        for row in contract["milestone_operations"]
        if row.get("ID") == sync_id
    ]
    if len(matches) != 1:
        raise TrackingCommandError(f"No existe un único recibo de hito {sync_id}.")
    return matches[0]


def _event_marker(manifest: dict[str, Any], receipt: dict[str, str]) -> str:
    return (
        f"LKS-SDD-EVENT: {manifest.get('project_id')}; {receipt['Task']}; "
        f"{receipt['Source ref']}; {receipt['Event kind']}; "
        f"{receipt['Event hash'][:16]}"
    )


def record_event_result(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not args.apply:
        raise TrackingCommandError("record-event-result exige --apply.")
    manifest_path, manifest, manifest_original = _load_manifest(root)
    contract = load_tracking_contract(root, manifest)
    receipt = _milestone_by_id(contract, args.sync_id)
    if receipt.get("State") != "authorized" or receipt.get("Result") != "pending":
        raise TrackingCommandError(f"{args.sync_id} no está authorized/pending.")
    change_date = _iso_date(args.date)
    if change_date < receipt.get("Authorized on", ""):
        raise TrackingCommandError("--date no puede preceder a la autorización.")
    if args.result == "succeeded":
        external_id = _safe_cell("--external-id", args.external_id or "")
        external_key = _safe_cell("--external-key", args.external_key or "")
        if external_id != receipt.get("External ID") or external_key != receipt.get(
            "External key"
        ):
            raise TrackingCommandError(
                "La identidad Jira observada no coincide con el recibo autorizado."
            )
        if receipt.get("Action") == "comment":
            marker = _safe_cell(
                "--observed-event-marker", args.observed_event_marker or ""
            )
            if marker != _event_marker(manifest, receipt):
                raise TrackingCommandError(
                    "El marker observado no coincide con el hito autorizado."
                )
        else:
            observed = _safe_cell(
                "--observed-status-id", args.observed_status_id or ""
            )
            target = receipt.get("Notes", "").removeprefix("target-status-id=")
            if observed != target or not re.fullmatch(r"[1-9][0-9]{0,30}", target):
                raise TrackingCommandError(
                    "El estado Jira observado no coincide con la transición autorizada."
                )
    state = {
        "succeeded": "recorded",
        "failed": "failed",
        "conflict": "conflict",
        "uncertain": "reconciliation-required",
    }[args.result]
    updated_text = _replace_row(
        contract["text"],
        MILESTONE_OPERATION_HEADERS,
        args.sync_id,
        {"State": state, "Recorded on": change_date, "Result": args.result},
    )
    updated_text = _frontmatter_date(updated_text, change_date)
    rows = [
        {**row, **(
            {"State": state, "Recorded on": change_date, "Result": args.result}
            if row.get("ID") == args.sync_id
            else {}
        )}
        for row in contract["milestone_operations"]
    ]
    updated_manifest = json.loads(json.dumps(manifest))
    updated_manifest["task_tracking"].update(
        reporting_status=_reporting_status(contract["reporting"], rows),
        last_reported_on=max(
            row.get("Recorded on", "")
            for row in rows
            if row.get("State") != "authorized"
        ),
    )
    _apply_and_validate(
        root,
        [manifest_path, contract["path"]],
        [manifest_original, contract["text"].encode("utf-8")],
        [_manifest_bytes(updated_manifest), updated_text.encode("utf-8")],
    )
    return {
        "applied": True,
        "sync_id": args.sync_id,
        "task": receipt["Task"],
        "action": receipt["Action"],
        "result": args.result,
        "reporting_status": updated_manifest["task_tracking"]["reporting_status"],
    }


def reconcile_event(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not args.apply:
        raise TrackingCommandError("reconcile-event exige --apply.")
    manifest_path, manifest, manifest_original = _load_manifest(root)
    contract = load_tracking_contract(root, manifest)
    anchor = _milestone_by_id(contract, args.anchor_sync_id)
    if anchor.get("State") not in {"conflict", "reconciliation-required"}:
        raise TrackingCommandError(
            "El ancla debe ser un resultado conflict o reconciliation-required."
        )
    authorized_on = _iso_date(args.authorized_on)
    change_date = _iso_date(args.date)
    if authorized_on > change_date:
        raise TrackingCommandError("--authorized-on no puede ser posterior a --date.")
    role = _safe_cell("--authorized-by-role", args.authorized_by_role)
    if args.result == "succeeded":
        if anchor.get("Action") == "comment":
            if _safe_cell(
                "--observed-event-marker", args.observed_event_marker or ""
            ) != _event_marker(manifest, anchor):
                raise TrackingCommandError("El marker reconciliado no coincide.")
        else:
            target = anchor.get("Notes", "").removeprefix("target-status-id=")
            if _safe_cell(
                "--observed-status-id", args.observed_status_id or ""
            ) != target:
                raise TrackingCommandError("El estado reconciliado no coincide.")
    sync_id = _next_shared_sync_id(contract)
    state = {
        "succeeded": "recorded",
        "failed": "failed",
        "conflict": "conflict",
        "uncertain": "reconciliation-required",
    }[args.result]
    updated_text = _append_row(
        contract["text"],
        MILESTONE_OPERATION_HEADERS,
        [
            sync_id,
            state,
            anchor["Task"],
            anchor["Source ref"],
            anchor["Event kind"],
            anchor["Action"],
            anchor["Event hash"],
            anchor["Preview hash"],
            (
                "matched"
                if anchor["Action"] == "transition" or args.result == "succeeded"
                else "no-match"
                if args.result == "failed"
                else args.result
            ),
            role,
            authorized_on,
            anchor["External ID"],
            anchor["External key"],
            change_date,
            args.result,
            f"reconciles={args.anchor_sync_id};{anchor['Notes']}",
        ],
    )
    updated_text = _frontmatter_date(updated_text, change_date)
    rows = [
        *contract["milestone_operations"],
        {
            **anchor,
            "ID": sync_id,
            "State": state,
            "Result": args.result,
            "Recorded on": change_date,
        },
    ]
    updated_manifest = json.loads(json.dumps(manifest))
    updated_manifest["task_tracking"].update(
        reporting_status=_reporting_status(contract["reporting"], rows),
        last_reported_on=change_date,
    )
    _apply_and_validate(
        root,
        [manifest_path, contract["path"]],
        [manifest_original, contract["text"].encode("utf-8")],
        [_manifest_bytes(updated_manifest), updated_text.encode("utf-8")],
    )
    return {
        "applied": True,
        "sync_id": sync_id,
        "anchor_sync_id": args.anchor_sync_id,
        "result": args.result,
        "reporting_status": updated_manifest["task_tracking"]["reporting_status"],
    }


def _print(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("status") or result.get("action") or "ok")
        if result.get("mutation_hash"):
            print(f"mutation_hash: {result['mutation_hash']}")
        if result.get("preview_hash"):
            print(f"preview_hash: {result['preview_hash']}")
        for blocker in result.get("blockers", []):
            print(f"BLOCKER: {blocker}")
        for warning in result.get("warnings", []):
            print(f"WARNING: {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("project_root", type=Path)
    status_parser.add_argument("--task", action="append")
    status_parser.add_argument("--json", action="store_true", dest="as_json")

    configure_parser = subparsers.add_parser("configure")
    configure_parser.add_argument("project_root", type=Path)
    configure_parser.add_argument(
        "--mode", required=True, choices=("repository-only", "jira-hybrid")
    )
    configure_parser.add_argument("--decision", required=True)
    configure_parser.add_argument("--date", required=True)
    configure_parser.add_argument("--site")
    configure_parser.add_argument("--project")
    configure_parser.add_argument("--issue-type")
    configure_parser.add_argument(
        "--reporting-scope",
        choices=("projection-only", "milestone-reporting"),
        default="projection-only",
    )
    configure_parser.add_argument(
        "--coordination-gate",
        choices=("advisory", "required-before-execution"),
        default="advisory",
    )
    configure_parser.add_argument("--apply", action="store_true")
    configure_parser.add_argument("--authorize")
    configure_parser.add_argument("--json", action="store_true", dest="as_json")

    preview_parser = subparsers.add_parser("preview-sync")
    preview_parser.add_argument("project_root", type=Path)
    preview_parser.add_argument("--task", action="append", required=True)
    preview_parser.add_argument("--json", action="store_true", dest="as_json")

    authorize_parser = subparsers.add_parser("authorize-sync")
    authorize_parser.add_argument("project_root", type=Path)
    authorize_parser.add_argument("--task", required=True)
    authorize_parser.add_argument("--preview-hash", required=True)
    authorize_parser.add_argument("--authorized-by-role", required=True)
    authorize_parser.add_argument("--authorized-on", required=True)
    authorize_parser.add_argument(
        "--duplicate-check", required=True, choices=("no-match", "matched")
    )
    authorize_parser.add_argument("--notes")
    authorize_parser.add_argument("--apply", action="store_true")
    authorize_parser.add_argument("--json", action="store_true", dest="as_json")

    record_parser = subparsers.add_parser("record-result")
    record_parser.add_argument("project_root", type=Path)
    record_parser.add_argument("--sync-id", required=True)
    record_parser.add_argument(
        "--result", required=True, choices=("succeeded", "failed", "conflict", "uncertain")
    )
    record_parser.add_argument("--external-id")
    record_parser.add_argument("--external-key")
    record_parser.add_argument("--url")
    record_parser.add_argument("--remote-status")
    record_parser.add_argument("--observed-projection-fingerprint")
    record_parser.add_argument("--observed-correlation-marker")
    record_parser.add_argument("--notes")
    record_parser.add_argument("--date", required=True)
    record_parser.add_argument("--apply", action="store_true")
    record_parser.add_argument("--json", action="store_true", dest="as_json")

    reconcile_parser = subparsers.add_parser("reconcile-result")
    reconcile_parser.add_argument("project_root", type=Path)
    reconcile_parser.add_argument("--task", required=True)
    reconcile_parser.add_argument("--anchor-sync-id", required=True)
    reconcile_parser.add_argument(
        "--result", required=True, choices=("succeeded", "failed", "conflict", "uncertain")
    )
    reconcile_parser.add_argument("--authorized-by-role", required=True)
    reconcile_parser.add_argument("--authorized-on", required=True)
    reconcile_parser.add_argument("--external-id")
    reconcile_parser.add_argument("--external-key")
    reconcile_parser.add_argument("--url")
    reconcile_parser.add_argument("--remote-status")
    reconcile_parser.add_argument("--observed-projection-fingerprint")
    reconcile_parser.add_argument("--observed-correlation-marker")
    reconcile_parser.add_argument("--notes")
    reconcile_parser.add_argument("--date", required=True)
    reconcile_parser.add_argument("--apply", action="store_true")
    reconcile_parser.add_argument("--json", action="store_true", dest="as_json")

    workflow_parser = subparsers.add_parser("configure-workflow")
    workflow_parser.add_argument("project_root", type=Path)
    workflow_parser.add_argument(
        "--local-state",
        required=True,
        choices=("in-progress", "blocked", "in-review", "done"),
    )
    workflow_parser.add_argument("--jira-status-id", required=True)
    workflow_parser.add_argument("--jira-status-name", required=True)
    workflow_parser.add_argument("--decision", required=True)
    workflow_parser.add_argument("--date", required=True)
    workflow_parser.add_argument("--apply", action="store_true")
    workflow_parser.add_argument("--authorize")
    workflow_parser.add_argument("--json", action="store_true", dest="as_json")

    for command in ("pause-reporting", "resume-reporting"):
        state_parser = subparsers.add_parser(command)
        state_parser.add_argument("project_root", type=Path)
        state_parser.add_argument("--date", required=True)
        state_parser.add_argument("--apply", action="store_true")
        state_parser.add_argument("--authorize")
        state_parser.add_argument("--json", action="store_true", dest="as_json")

    event_preview_parser = subparsers.add_parser("preview-event")
    event_preview_parser.add_argument("project_root", type=Path)
    event_preview_parser.add_argument("--task", required=True)
    event_preview_parser.add_argument("--source-ref", required=True)
    event_preview_parser.add_argument(
        "--event-kind",
        required=True,
        choices=(
            "started",
            "progress",
            "blocked",
            "resumed",
            "in-review",
            "verification-pending",
            "verification-failed",
            "done",
        ),
    )
    event_preview_parser.add_argument("--observed-status-id")
    event_preview_parser.add_argument("--transition-id")
    event_preview_parser.add_argument("--json", action="store_true", dest="as_json")

    event_authorize_parser = subparsers.add_parser("authorize-event")
    event_authorize_parser.add_argument("project_root", type=Path)
    event_authorize_parser.add_argument("--task", required=True)
    event_authorize_parser.add_argument("--source-ref", required=True)
    event_authorize_parser.add_argument(
        "--event-kind", required=True, choices=event_preview_parser._option_string_actions["--event-kind"].choices
    )
    event_authorize_parser.add_argument("--observed-status-id")
    event_authorize_parser.add_argument("--transition-id")
    event_authorize_parser.add_argument("--preview-hash", required=True)
    event_authorize_parser.add_argument("--authorized-by-role", required=True)
    event_authorize_parser.add_argument("--authorized-on", required=True)
    event_authorize_parser.add_argument(
        "--comment-check", required=True, choices=("no-match", "matched")
    )
    event_authorize_parser.add_argument("--apply", action="store_true")
    event_authorize_parser.add_argument("--json", action="store_true", dest="as_json")

    event_record_parser = subparsers.add_parser("record-event-result")
    event_record_parser.add_argument("project_root", type=Path)
    event_record_parser.add_argument("--sync-id", required=True)
    event_record_parser.add_argument(
        "--result", required=True, choices=("succeeded", "failed", "conflict", "uncertain")
    )
    event_record_parser.add_argument("--external-id")
    event_record_parser.add_argument("--external-key")
    event_record_parser.add_argument("--observed-event-marker")
    event_record_parser.add_argument("--observed-status-id")
    event_record_parser.add_argument("--date", required=True)
    event_record_parser.add_argument("--apply", action="store_true")
    event_record_parser.add_argument("--json", action="store_true", dest="as_json")

    event_reconcile_parser = subparsers.add_parser("reconcile-event")
    event_reconcile_parser.add_argument("project_root", type=Path)
    event_reconcile_parser.add_argument("--anchor-sync-id", required=True)
    event_reconcile_parser.add_argument(
        "--result", required=True, choices=("succeeded", "failed", "conflict", "uncertain")
    )
    event_reconcile_parser.add_argument("--authorized-by-role", required=True)
    event_reconcile_parser.add_argument("--authorized-on", required=True)
    event_reconcile_parser.add_argument("--observed-event-marker")
    event_reconcile_parser.add_argument("--observed-status-id")
    event_reconcile_parser.add_argument("--date", required=True)
    event_reconcile_parser.add_argument("--apply", action="store_true")
    event_reconcile_parser.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    try:
        if args.command == "status":
            _, manifest, _ = _load_manifest(root)
            result = assess_tracking(root, manifest, args.task)
        elif args.command == "configure":
            result = configure(root, args)
        elif args.command == "preview-sync":
            if len(args.task) != 1:
                raise TrackingCommandError(
                    "preview-sync exige exactamente un único --task."
                )
            _, manifest, _ = _load_manifest(root)
            result = build_projection_preview(root, manifest, args.task)
        elif args.command == "authorize-sync":
            result = authorize_sync(root, args)
        elif args.command == "record-result":
            result = record_result(root, args)
        elif args.command == "reconcile-result":
            result = reconcile_result(root, args)
        elif args.command == "configure-workflow":
            result = configure_workflow(root, args)
        elif args.command in {"pause-reporting", "resume-reporting"}:
            result = set_reporting_state(root, args)
        elif args.command == "preview-event":
            _, manifest, _ = _load_manifest(root)
            result = _event_preview(root, manifest, args)
        elif args.command == "authorize-event":
            result = authorize_event(root, args)
        elif args.command == "record-event-result":
            result = record_event_result(root, args)
        else:
            result = reconcile_event(root, args)
    except (TrackingCommandError, TrackingContractError, OSError) as exc:
        if args.as_json:
            print(
                json.dumps(
                    {"status": "error", "changed": False, "error": str(exc)},
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    _print(result, args.as_json)
    if result.get("blockers"):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
