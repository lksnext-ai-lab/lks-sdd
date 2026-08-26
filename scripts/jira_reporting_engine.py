#!/usr/bin/env python3
"""Build deterministic Jira milestone intents from canonical LKS-SDD state.

The module is deliberately offline. It never imports a Jira client and never
interprets a remote status as authorization, implementation progress or proof.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from delivery_engine import validate_delivery_contract
from task_tracking_engine import (
    MILESTONE_EVENT_KINDS,
    PERSONAL_DATA_RE,
    SENSITIVE_VALUE_RE,
    TrackingContractError,
    load_tracking_contract,
)


SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
TASK_RE = re.compile(r"^TASK-[0-9]{3}$")
SOURCE_RE = re.compile(r"^(TASK|EXEC|CKPT|EVID|PROB)-([0-9]{3})$")
NUMERIC_ID_RE = re.compile(r"^[1-9][0-9]{0,30}$")
EVENT_TITLES = {
    "started": "Implementación iniciada",
    "progress": "Hito de progreso",
    "blocked": "Implementación bloqueada",
    "resumed": "Implementación reanudada",
    "in-review": "Lista para revisión",
    "verification-pending": "Verificación pendiente",
    "verification-failed": "Verificación no superada",
    "done": "Implementación verificada",
}
EXPECTED_TASK_STATES = {
    "started": {"in-progress"},
    "progress": {"in-progress"},
    "blocked": {"blocked"},
    "resumed": {"in-progress"},
    "in-review": {"in-review"},
    "verification-pending": {"in-review"},
    "verification-failed": {"in-review"},
    "done": {"done"},
}


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _single(details: dict[str, Any], key: str) -> dict[str, str]:
    rows = details.get(key, [])
    return rows[0] if isinstance(rows, list) and len(rows) == 1 else {}


def _meaningful(value: str | None) -> bool:
    return bool(value and value not in {"pending", "none", "not-applicable", "unknown"})


def _source_exists(
    root: Path,
    manifest: dict[str, Any],
    task_id: str,
    source_ref: str,
    details: dict[str, Any],
) -> bool:
    match = SOURCE_RE.fullmatch(source_ref)
    if match is None:
        return False
    kind = match.group(1)
    if kind == "TASK":
        return source_ref == task_id
    if kind == "EXEC":
        return any(
            item.get("execution_id") == source_ref
            and task_id in item.get("task_ids", [])
            for item in manifest.get("executions", [])
            if isinstance(item, dict)
        )
    if kind == "CKPT":
        relative = f"docs/lks-sdd/04-delivery/checkpoints/{source_ref}.md"
        path = root / relative
        if not path.is_file() or path.is_symlink():
            return False
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return False
        return task_id in text and f'artifact_id: "ART-{source_ref}"' in text
    if kind == "EVID":
        path = root / "docs" / "lks-sdd" / "evidence" / f"{source_ref}.json"
        if not path.is_file() or path.is_symlink():
            return False
        try:
            evidence = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return False
        return (
            isinstance(evidence, dict)
            and evidence.get("evidence_id") == source_ref
            and task_id in evidence.get("task_ids", [])
        )
    return any(
        row.get("ID") == source_ref
        for row in details.get("problems", [])
        if isinstance(row, dict)
    )


def _sanitize_snapshot(snapshot: dict[str, Any]) -> None:
    serialized = json.dumps(snapshot, ensure_ascii=False)
    if SENSITIVE_VALUE_RE.search(serialized):
        raise TrackingContractError(
            "El hito contiene un valor que parece secreto; sanee el Markdown antes de continuar."
        )
    if PERSONAL_DATA_RE.search(serialized):
        raise TrackingContractError(
            "El hito contiene datos personales detectables; sanee el Markdown antes de continuar."
        )
    if any(token in serialized for token in ("<script", "javascript:", "file://")):
        raise TrackingContractError(
            "El hito contiene markup o rutas no publicables en Jira."
        )


def _milestone_snapshot(
    task_id: str,
    task: dict[str, str],
    details: dict[str, Any],
    source_ref: str,
    event_kind: str,
) -> dict[str, Any]:
    execution = _single(details, "execution")
    continuity = _single(details, "continuity")
    open_problems = [
        row.get("ID", "")
        for row in details.get("problems", [])
        if isinstance(row, dict) and row.get("State") not in {"resolved", "retired"}
    ]
    validations = [
        {
            "acceptance": row.get("Acceptance", ""),
            "gate": row.get("Gate", ""),
            "result": row.get("Result", ""),
            "evidence": row.get("Evidence", ""),
        }
        for row in details.get("validation", [])
        if isinstance(row, dict)
    ]
    snapshot = {
        "task_id": task_id,
        "title": task.get("Title", "").strip(),
        "source_ref": source_ref,
        "event_kind": event_kind,
        "workflow_state": execution.get("Workflow state", ""),
        "health": execution.get("Health", ""),
        "progress": execution.get("Progress", ""),
        "updated": execution.get("Updated", ""),
        "current_checkpoint": continuity.get("Current checkpoint", "none"),
        "next_safe_action": continuity.get("Next safe action", "not-recorded"),
        "open_problems": sorted(item for item in open_problems if item),
        "validation": validations,
    }
    _sanitize_snapshot(snapshot)
    return snapshot


def _comment_body(snapshot: dict[str, Any], marker: str) -> str:
    problem_text = ", ".join(snapshot["open_problems"]) or "ninguno"
    evidence = sorted(
        {
            item["evidence"]
            for item in snapshot["validation"]
            if _meaningful(item.get("evidence"))
        }
    )
    evidence_text = ", ".join(evidence) or "todavía no registrada"
    return "\n".join(
        [
            f"[LKS-SDD] {snapshot['task_id']} · {EVENT_TITLES[snapshot['event_kind']]}",
            f"Estado local: {snapshot['workflow_state']} · avance {snapshot['progress']}% · salud {snapshot['health']}",
            f"Fuente canónica: {snapshot['source_ref']}",
            f"Checkpoint: {snapshot['current_checkpoint']}",
            f"Bloqueos abiertos: {problem_text}",
            f"Evidencia: {evidence_text}",
            f"Siguiente acción segura: {snapshot['next_safe_action']}",
            marker,
        ]
    )


def build_milestone_preview(
    root: Path,
    manifest: dict[str, Any],
    *,
    task_id: str,
    source_ref: str,
    event_kind: str,
    observed_status_id: str | None = None,
    transition_id: str | None = None,
) -> dict[str, Any]:
    """Build one exact comment plus an optional explicitly mapped transition."""

    if str(manifest.get("schema_version")) != "1.5":
        raise TrackingContractError("El reporting de hitos requiere schema 1.5.")
    if not TASK_RE.fullmatch(task_id):
        raise TrackingContractError("--task debe usar TASK-###.")
    if event_kind not in MILESTONE_EVENT_KINDS:
        raise TrackingContractError("Event kind no soportado.")
    contract = load_tracking_contract(root, manifest)
    reporting = contract["reporting"]
    if contract["binding"].get("Mode") != "jira-hybrid":
        raise TrackingContractError(
            "repository-only no usa Jira y conserva una experiencia local completa."
        )
    if reporting.get("Scope") != "milestone-reporting":
        raise TrackingContractError(
            "El proyecto usa projection-only; los hitos Jira no están habilitados."
        )
    if reporting.get("State") == "paused":
        raise TrackingContractError(
            "El reporting Jira está pausado; el trabajo local puede continuar según su gate."
        )
    if reporting.get("State") != "confirmed":
        raise TrackingContractError("La política de reporting Jira no está confirmed.")
    mapping = contract["mappings"].get(task_id)
    if mapping is None or mapping.get("State") != "synced":
        raise TrackingContractError(
            "El hito exige primero un mapping Jira synced e inequívoco para la TASK."
        )

    delivery = validate_delivery_contract(root, manifest)
    if delivery.get("errors"):
        raise TrackingContractError(
            "El contrato TASK no es válido: " + "; ".join(delivery["errors"])
        )
    task = delivery.get("tasks", {}).get(task_id)
    details = delivery.get("task_details", {}).get(task_id, {})
    if task is None:
        raise TrackingContractError(f"{task_id} no existe en el contrato canónico.")
    if not _source_exists(root, manifest, task_id, source_ref, details):
        raise TrackingContractError(
            f"{source_ref} no es una fuente canónica válida para {task_id}."
        )
    execution = _single(details, "execution")
    current_state = execution.get("Workflow state", "")
    if current_state not in EXPECTED_TASK_STATES[event_kind]:
        raise TrackingContractError(
            f"{event_kind} no coincide con el estado canónico {current_state!r}."
        )
    if event_kind == "blocked" and not any(
        row.get("State") not in {"resolved", "retired"}
        for row in details.get("problems", [])
        if isinstance(row, dict)
    ):
        raise TrackingContractError("blocked exige un PROB-### canónico abierto.")
    verification = manifest.get("verification", {})
    if event_kind == "done" and (
        verification.get("status") != "verified"
        or task_id not in verification.get("task_ids", [])
        or source_ref not in verification.get("evidence_ids", [])
    ):
        raise TrackingContractError(
            "done exige verificación canónica verified y el EVID-### indicado."
        )
    if event_kind == "verification-failed" and source_ref.split("-", 1)[0] != "EVID":
        raise TrackingContractError("verification-failed exige una fuente EVID-###.")

    snapshot = _milestone_snapshot(task_id, task, details, source_ref, event_kind)
    event_hash = _canonical_hash(snapshot)
    marker = (
        f"LKS-SDD-EVENT: {manifest.get('project_id')}; {task_id}; "
        f"{source_ref}; {event_kind}; {event_hash[:16]}"
    )
    operations: list[dict[str, Any]] = [
        {
            "action": "comment",
            "task_id": task_id,
            "source_ref": source_ref,
            "event_kind": event_kind,
            "event_hash": event_hash,
            "external_id": mapping.get("External ID"),
            "external_key": mapping.get("External key"),
            "duplicate_check": {"marker": marker},
            "payload": {"body": _comment_body(snapshot, marker)},
        }
    ]
    workflow = contract["workflow"].get(current_state)
    if workflow and workflow.get("State") == "confirmed":
        if not NUMERIC_ID_RE.fullmatch(observed_status_id or ""):
            raise TrackingContractError(
                "La transición mapeada exige --observed-status-id desde una lectura Jira fresca."
            )
        if not NUMERIC_ID_RE.fullmatch(transition_id or ""):
            raise TrackingContractError(
                "La transición mapeada exige --transition-id observado en Jira."
            )
        operations.append(
            {
                "action": "transition",
                "task_id": task_id,
                "source_ref": source_ref,
                "event_kind": event_kind,
                "event_hash": event_hash,
                "external_id": mapping.get("External ID"),
                "external_key": mapping.get("External key"),
                "duplicate_check": {
                    "observed_status_id": observed_status_id,
                    "target_status_id": workflow.get("Jira status ID"),
                },
                "payload": {
                    "transition_id": transition_id,
                    "target_status_id": workflow.get("Jira status ID"),
                    "target_status_name": workflow.get("Jira status name"),
                    "marker": marker,
                },
            }
        )
    elif observed_status_id or transition_id:
        raise TrackingContractError(
            "No se aceptan IDs remotos sin un workflow mapping confirmed para el estado local."
        )
    for operation in operations:
        history = [
            row
            for row in contract["milestone_operations"]
            if row.get("Task") == task_id
            and row.get("Source ref") == source_ref
            and row.get("Event kind") == event_kind
            and row.get("Action") == operation["action"]
        ]
        if any(row.get("Event hash") != event_hash for row in history):
            operation["disposition"] = "reconciliation-required"
            continue
        latest = history[-1] if history else None
        operation["disposition"] = (
            "write"
            if latest is None or latest.get("State") == "failed"
            else "noop"
            if latest.get("State") == "recorded"
            and latest.get("Result") == "succeeded"
            else "awaiting-result"
            if latest.get("State") == "authorized"
            else "reconciliation-required"
        )
    preview = {
        "contract": "lks-sdd-jira-milestone/1.0",
        "project_id": manifest.get("project_id"),
        "binding_id": contract["binding"].get("Binding"),
        "reporting_id": reporting.get("Reporting"),
        "authority": "markdown",
        "direction": "outbound-only",
        "snapshot": snapshot,
        "event_marker": marker,
        "operations": operations,
        "external_write_authorized": False,
    }
    preview["preview_hash"] = _canonical_hash(preview)
    return preview


__all__ = ["build_milestone_preview"]
