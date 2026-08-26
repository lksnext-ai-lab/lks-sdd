#!/usr/bin/env python3
"""Validate and project the optional LKS-SDD 1.4/1.5 Jira task tracker.

This module is deliberately offline.  It prepares deterministic operations and
assesses durable receipts; a skill may hand an authorized preview to the
separately installed Atlassian Rovo plugin, but no network client lives here.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

from contract_engine import build_project_model
from delivery_engine import parse_tables, validate_delivery_contract
from planning_engine import assess_planning


TRACKING_PATH = "docs/lks-sdd/04-delivery/task-tracking.md"
BINDING_HEADERS = (
    "Binding",
    "State",
    "Mode",
    "Provider",
    "Site",
    "Project",
    "Issue type",
    "Sync policy",
    "Write policy",
    "Decision",
    "Last reviewed",
)
MAPPING_HEADERS = (
    "Task",
    "State",
    "External ID",
    "External key",
    "URL",
    "Projection fingerprint",
    "Remote status",
    "Last synced",
    "Last operation",
    "Notes",
)
OPERATION_HEADERS = (
    "ID",
    "State",
    "Task",
    "Action",
    "Preview hash",
    "Projection fingerprint",
    "Duplicate check",
    "Authorized by role",
    "Authorized on",
    "External ID",
    "External key",
    "Recorded on",
    "Result",
    "Notes",
)
REPORTING_HEADERS = (
    "Reporting",
    "State",
    "Scope",
    "Coordination gate",
    "Comment policy",
    "Decision",
    "Last reviewed",
)
WORKFLOW_HEADERS = (
    "Local state",
    "State",
    "Jira status ID",
    "Jira status name",
    "Decision",
    "Last reviewed",
)
MILESTONE_OPERATION_HEADERS = (
    "ID",
    "State",
    "Task",
    "Source ref",
    "Event kind",
    "Action",
    "Event hash",
    "Preview hash",
    "Duplicate check",
    "Authorized by role",
    "Authorized on",
    "External ID",
    "External key",
    "Recorded on",
    "Result",
    "Notes",
)

MODES = {"pending", "repository-only", "jira-hybrid"}
BINDING_STATES = {"proposed", "confirmed"}
SYNC_POLICIES = {
    "pending",
    "not-required",
    "advisory",
    "required-before-execution",
}
WRITE_POLICIES = {"pending", "local-only", "preview-and-confirm"}
REPORTING_STATES = {"proposed", "confirmed", "paused"}
REPORTING_SCOPES = {
    "pending",
    "not-applicable",
    "projection-only",
    "milestone-reporting",
}
COORDINATION_GATES = {
    "pending",
    "not-required",
    "advisory",
    "required-before-execution",
}
COMMENT_POLICIES = {"pending", "not-applicable", "milestones-only"}
LOCAL_WORKFLOW_STATES = {"in-progress", "blocked", "in-review", "done"}
WORKFLOW_MAPPING_STATES = {"proposed", "confirmed"}
MILESTONE_EVENT_KINDS = {
    "started",
    "progress",
    "blocked",
    "resumed",
    "in-review",
    "verification-pending",
    "verification-failed",
    "done",
}
MILESTONE_ACTIONS = {"comment", "transition"}
MAPPING_STATES = {
    "unlinked",
    "pending",
    "synced",
    "out-of-sync",
    "conflict",
    "failed",
    "reconciliation-required",
}
OPERATION_STATES = {
    "authorized",
    "recorded",
    "failed",
    "conflict",
    "reconciliation-required",
}
OPERATION_RESULTS = {"pending", "succeeded", "failed", "conflict", "uncertain"}
DUPLICATE_CHECK_RESULTS = {
    "no-match",
    "matched",
    "not-required",
    "conflict",
    "uncertain",
}
IDENTITY_PLACEHOLDERS = {"", "pending", "none", "unknown"}
OPERATION_STATE_RESULT = {
    "authorized": "pending",
    "recorded": "succeeded",
    "failed": "failed",
    "conflict": "conflict",
    "reconciliation-required": "uncertain",
}
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
TASK_RE = re.compile(r"^TASK-[0-9]{3}$")
ADR_RE = re.compile(r"^ADR-[0-9]{3}$")
SYNC_RE = re.compile(r"^SYNC-[0-9]{3}$")
RPT_RE = re.compile(r"^RPT-[0-9]{3}$")
SOURCE_REF_RE = re.compile(r"^(?:TASK|EXEC|CKPT|EVID|PROB)-[0-9]{3}$")
PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+$")
EXTERNAL_ID_RE = re.compile(r"^[1-9][0-9]{0,30}$")
SENSITIVE_MARKERS = (
    "authorization:",
    "bearer ",
    "basic ",
    "api_token",
    "api-token",
    "api_key",
    "api-key",
    "password=",
    "cookie:",
    "set-cookie:",
    "client_secret",
    "refresh_token",
    "access_token",
)
SENSITIVE_VALUE_RE = re.compile(
    r"(?i)(?:authorization\s*:\s*(?:bearer|basic)\s+\S+|"
    r"(?:password|passwd|api[_-]?(?:key|token)|access_token|refresh_token|"
    r"client_secret|cookie|set-cookie)\s*[:=]\s*\S+|"
    r"[?&](?:token|jwt|key|secret|password)=[^&#\s]+|"
    r"https?://[^/@\s:]+:[^/@\s]+@)"
)
PERSONAL_DATA_RE = re.compile(
    r"(?i)(?:\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|"
    r"\b(?:[XYZ]\d{7}[A-Z]|\d{8}[A-Z])\b|"
    r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b)"
)
UNSAFE_MARKUP_RE = re.compile(r"[<>\[\]]")


class TrackingContractError(ValueError):
    """A deterministic task-tracking contract error."""


class TrackingPlanningBlocked(TrackingContractError):
    """The tracking contract is valid but the canonical plan is not projectable."""


def require_confirmed_tracking_decision(
    root: Path, decision: str, expected_mode: str | None = None
) -> None:
    """Require a confirmed ADR that explicitly records the tracking mode."""

    if not ADR_RE.fullmatch(decision):
        raise TrackingContractError("La decisión de tracking debe usar ADR-###.")
    model = build_project_model(root)
    row = model.nodes.get(decision)
    if row is None:
        raise TrackingContractError(
            f"La decisión de tracking {decision} no existe en el contrato Markdown."
        )
    if row.state != "confirmed":
        raise TrackingContractError(
            f"La decisión de tracking {decision} debe estar confirmed."
        )
    if expected_mode is not None:
        narrative = " ".join(
            str(row.cells.get(column, ""))
            for column in ("Decision", "Impact")
        ).casefold()
        if "tracking" not in narrative or expected_mode.casefold() not in narrative:
            raise TrackingContractError(
                f"La decisión {decision} no documenta explícitamente "
                f"tracking mode={expected_mode}."
            )


def _valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _valid_https_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not (parsed.username or parsed.password)
        and not parsed.query
        and not parsed.fragment
    )


def _same_origin(left: str, right: str) -> bool:
    try:
        first = urlparse(left)
        second = urlparse(right)
        first_origin = (
            first.scheme.casefold(),
            first.hostname.casefold() if first.hostname else None,
            first.port,
        )
        second_origin = (
            second.scheme.casefold(),
            second.hostname.casefold() if second.hostname else None,
            second.port,
        )
    except ValueError:
        return False
    return first_origin == second_origin


def url_matches_external_key(value: str, external_key: str) -> bool:
    try:
        path = urlparse(value).path
    except ValueError:
        return False
    segments = [
        unquote(segment).casefold() for segment in path.split("/") if segment
    ]
    return bool(segments) and segments[-1] == external_key.casefold()


def _looks_sensitive(value: str) -> bool:
    lowered = value.casefold()
    return bool(SENSITIVE_VALUE_RE.search(value)) or any(
        marker in lowered for marker in SENSITIVE_MARKERS
    )


def unsafe_persisted_text(value: str) -> bool:
    return bool(UNSAFE_MARKUP_RE.search(value))


def external_key_matches_project(project_key: str, external_key: str) -> bool:
    return bool(
        re.fullmatch(
            re.escape(project_key) + r"-[1-9][0-9]*",
            external_key,
        )
    )


def correlation_marker(project_id: str, task_id: str) -> str:
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", project_id) is None:
        raise TrackingContractError(
            "project_id no permite construir un marcador Jira estable."
        )
    if TASK_RE.fullmatch(task_id) is None:
        raise TrackingContractError(
            "La TASK no permite construir un marcador Jira estable."
        )
    return f"LKS-SDD-PROJECT: {project_id}; TASK: {task_id}"


def _task_classification(task_text: str, task_id: str) -> str:
    lines = task_text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise TrackingContractError(
            f"{task_id}: falta un front matter cerrado para revisar classification."
        )
    try:
        end = next(
            index for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise TrackingContractError(
            f"{task_id}: el front matter no está cerrado."
        ) from exc
    classification_rows = [
        line for line in lines[1:end] if re.match(r"^classification\s*:", line)
    ]
    if len(classification_rows) != 1:
        raise TrackingContractError(
            f"{task_id}: el front matter exige exactamente una classification."
        )
    raw = classification_rows[0].split(":", 1)[1].strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        raw = raw[1:-1]
    return raw


def _tracking_frontmatter(text: str, manifest: dict[str, Any]) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise TrackingContractError(
            "ART-TRACKING no contiene un front matter cerrado."
        )
    try:
        end = next(
            index for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise TrackingContractError(
            "ART-TRACKING no contiene un front matter cerrado."
        ) from exc
    metadata: dict[str, str] = {}
    duplicates: set[str] = set()
    for line in lines[1:end]:
        match = re.match(r"^([a-z][a-z0-9_]*)\s*:\s*(.*?)\s*$", line)
        if match is None:
            continue
        key, raw = match.groups()
        if key in metadata:
            duplicates.add(key)
        value = raw
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        metadata[key] = value
    expected = {
        "artifact_id": "ART-TRACKING",
        "artifact_type": "task-tracking",
        "schema_version": str(manifest.get("schema_version", "")),
        "method_version": str(manifest.get("method_version", "")),
        "created_with_plugin_version": str(manifest.get("plugin_version", "")),
        "project_id": str(manifest.get("project_id", "")),
        "baseline_id": str(manifest.get("baseline_id", "")),
        "source_of_truth": "true",
    }
    for key, wanted in expected.items():
        if key in duplicates or metadata.get(key) != wanted:
            raise TrackingContractError(
                f"ART-TRACKING exige front matter {key}={wanted!r} sin duplicados."
            )
    return metadata


def _payload_secret_path(value: Any, path: str = "payload") -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            found = _payload_secret_path(nested, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found = _payload_secret_path(nested, f"{path}[{index}]")
            if found:
                return found
    elif isinstance(value, str) and _looks_sensitive(value):
        return path
    return None


def _payload_personal_path(value: Any, path: str = "payload") -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            found = _payload_personal_path(nested, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found = _payload_personal_path(nested, f"{path}[{index}]")
            if found:
                return found
    elif isinstance(value, str) and PERSONAL_DATA_RE.search(value):
        return path
    return None


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _artifact_path(manifest: dict[str, Any]) -> str | None:
    for artifact in manifest.get("artifacts", []):
        if isinstance(artifact, dict) and artifact.get("id") == "ART-TRACKING":
            path = artifact.get("path")
            return path if isinstance(path, str) else None
    return None


def _safe_tracking_file(root: Path, manifest: dict[str, Any]) -> Path:
    relative = _artifact_path(manifest)
    if relative != TRACKING_PATH:
        raise TrackingContractError(
            f"ART-TRACKING debe usar la ruta canónica {TRACKING_PATH}."
        )
    root = root.expanduser().resolve()
    path = (root / relative).resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise TrackingContractError("ART-TRACKING queda fuera del proyecto.") from exc
    if not path.is_file() or path.is_symlink():
        raise TrackingContractError("ART-TRACKING no existe como archivo regular.")
    return path


def _table(
    tables: list[tuple[tuple[str, ...], list[dict[str, str]]]],
    headers: tuple[str, ...],
) -> list[dict[str, str]]:
    matches = [rows for actual, rows in tables if actual == headers]
    if len(matches) != 1:
        raise TrackingContractError(
            f"ART-TRACKING debe contener exactamente una tabla {headers[0]}."
        )
    return matches[0]


def load_tracking_contract(
    root: Path, manifest: dict[str, Any]
) -> dict[str, Any]:
    """Read the tracker tables without mutating the consumer project."""

    schema_version = str(manifest.get("schema_version"))
    if schema_version not in {"1.4", "1.5"}:
        raise TrackingContractError("El tracking operativo requiere schema 1.4 o 1.5.")
    path = _safe_tracking_file(root, manifest)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise TrackingContractError(f"No se puede leer ART-TRACKING: {exc}") from exc
    metadata = _tracking_frontmatter(text, manifest)
    tables = parse_tables(text)
    bindings = _table(tables, BINDING_HEADERS)
    mappings = _table(tables, MAPPING_HEADERS)
    operations = _table(tables, OPERATION_HEADERS)
    reporting_rows: list[dict[str, str]] = []
    workflow_rows: list[dict[str, str]] = []
    milestone_operations: list[dict[str, str]] = []
    if schema_version == "1.5":
        reporting_rows = _table(tables, REPORTING_HEADERS)
        workflow_rows = _table(tables, WORKFLOW_HEADERS)
        milestone_operations = _table(tables, MILESTONE_OPERATION_HEADERS)
    if len(bindings) != 1:
        raise TrackingContractError("ART-TRACKING necesita un único binding activo.")
    if schema_version == "1.5" and len(reporting_rows) != 1:
        raise TrackingContractError("ART-TRACKING necesita una única reporting policy.")
    return {
        "path": path,
        "text": text,
        "metadata": metadata,
        "binding": bindings[0],
        "mappings": {row.get("Task", ""): row for row in mappings},
        "mapping_rows": mappings,
        "operations": operations,
        "reporting": reporting_rows[0] if reporting_rows else {},
        "workflow_rows": workflow_rows,
        "workflow": {
            row.get("Local state", ""): row for row in workflow_rows
        },
        "milestone_operations": milestone_operations,
    }


def _confirmed_decision(root: Path, decision: str, purpose: str) -> str | None:
    """Return an error unless an ADR is confirmed and names the governed purpose."""

    if not ADR_RE.fullmatch(decision):
        return f"{purpose} exige una decisión ADR-###."
    model = build_project_model(root)
    row = model.nodes.get(decision)
    if row is None or row.state != "confirmed":
        return f"{purpose} exige que {decision} exista y esté confirmed."
    narrative = " ".join(str(value) for value in row.cells.values()).casefold()
    if "jira" not in narrative:
        return f"{decision} debe documentar explícitamente la decisión Jira de {purpose}."
    return None


def _validate_reporting_contract(
    root: Path,
    manifest: dict[str, Any],
    contract: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """Validate optional milestone reporting without importing Jira as authority."""

    reporting = contract["reporting"]
    workflow_rows = contract["workflow_rows"]
    milestone_operations = contract["milestone_operations"]
    binding = contract["binding"]
    mode = binding.get("Mode", "")
    index = manifest.get("task_tracking", {})

    if not RPT_RE.fullmatch(reporting.get("Reporting", "")):
        result["errors"].append("Reporting debe usar RPT-###.")
    if reporting.get("State") not in REPORTING_STATES:
        result["errors"].append("State de Reporting no es válida.")
    if reporting.get("Scope") not in REPORTING_SCOPES:
        result["errors"].append("Scope de Reporting no es válido.")
    if reporting.get("Coordination gate") not in COORDINATION_GATES:
        result["errors"].append("Coordination gate no es válido.")
    if reporting.get("Comment policy") not in COMMENT_POLICIES:
        result["errors"].append("Comment policy no es válida.")
    if not _valid_date(reporting.get("Last reviewed", "")):
        result["errors"].append("Last reviewed de Reporting debe usar AAAA-MM-DD.")
    if any(
        _looks_sensitive(reporting.get(column, ""))
        or PERSONAL_DATA_RE.search(reporting.get(column, ""))
        or unsafe_persisted_text(reporting.get(column, ""))
        for column in REPORTING_HEADERS
    ):
        result["errors"].append(
            "Reporting contiene secretos, datos personales o markup no persistible."
        )

    scope = reporting.get("Scope", "")
    if mode == "pending":
        expected = {
            "State": "proposed",
            "Scope": "pending",
            "Coordination gate": "pending",
            "Comment policy": "pending",
        }
    elif mode == "repository-only":
        expected = {
            "State": "confirmed",
            "Scope": "not-applicable",
            "Coordination gate": "not-required",
            "Comment policy": "not-applicable",
        }
    elif scope == "projection-only":
        expected = {
            "State": "confirmed",
            "Coordination gate": binding.get("Sync policy", ""),
            "Comment policy": "not-applicable",
        }
    else:
        expected = {
            "Comment policy": "milestones-only",
        }
        if reporting.get("State") not in {"confirmed", "paused"}:
            result["errors"].append(
                "milestone-reporting exige Reporting confirmed o paused."
            )
        if reporting.get("Coordination gate") not in {
            "advisory",
            "required-before-execution",
        }:
            result["errors"].append(
                "milestone-reporting exige un Coordination gate explícito."
            )
    for column, wanted in expected.items():
        if reporting.get(column) != wanted:
            result["errors"].append(
                f"{mode}/{scope} exige Reporting.{column}={wanted!r}."
            )
    if scope == "milestone-reporting":
        decision_error = _confirmed_decision(
            root, reporting.get("Decision", ""), "milestone-reporting"
        )
        if decision_error:
            result["errors"].append(decision_error)
    elif mode == "repository-only" and reporting.get("Decision") != binding.get(
        "Decision"
    ):
        result["errors"].append(
            "repository-only debe reutilizar la decisión confirmada del binding."
        )
    elif mode == "pending" and not reporting.get("Decision", "").startswith(
        "pending"
    ):
        result["errors"].append("Reporting pending no puede inventar una decisión.")
    elif scope == "projection-only" and reporting.get("Decision") != binding.get(
        "Decision"
    ):
        result["errors"].append(
            "projection-only debe reutilizar la decisión confirmada del binding."
        )

    if mode in {"pending", "repository-only"} or scope != "milestone-reporting":
        if workflow_rows or milestone_operations:
            result["errors"].append(
                f"{mode}/{scope} exige Workflow mapping y Milestone operations vacíos."
            )

    seen_states: set[str] = set()
    for row in workflow_rows:
        local_state = row.get("Local state", "")
        if local_state not in LOCAL_WORKFLOW_STATES:
            result["errors"].append(
                f"Workflow mapping contiene estado local inválido: {local_state!r}."
            )
        elif local_state in seen_states:
            result["errors"].append(
                f"Workflow mapping duplicado para {local_state}."
            )
        seen_states.add(local_state)
        if row.get("State") not in WORKFLOW_MAPPING_STATES:
            result["errors"].append(
                f"{local_state}: State del workflow mapping no es válida."
            )
        if not EXTERNAL_ID_RE.fullmatch(row.get("Jira status ID", "")):
            result["errors"].append(
                f"{local_state}: Jira status ID debe ser numérico y observado."
            )
        if row.get("Jira status name", "") in IDENTITY_PLACEHOLDERS:
            result["errors"].append(
                f"{local_state}: falta Jira status name observado."
            )
        if not _valid_date(row.get("Last reviewed", "")):
            result["errors"].append(f"{local_state}: Last reviewed inválido.")
        if any(
            _looks_sensitive(row.get(column, ""))
            or PERSONAL_DATA_RE.search(row.get(column, ""))
            or unsafe_persisted_text(row.get(column, ""))
            for column in WORKFLOW_HEADERS
        ):
            result["errors"].append(
                f"{local_state}: el workflow mapping contiene texto no persistible."
            )
        if row.get("State") == "confirmed":
            decision_error = _confirmed_decision(
                root, row.get("Decision", ""), f"workflow {local_state}"
            )
            if decision_error:
                result["errors"].append(decision_error)

    projection_ids = {
        row.get("ID", "") for row in contract["operations"]
    }
    milestone_ids: set[str] = set()
    pending_keys: set[tuple[str, str, str, str]] = set()
    last_number = 0
    for row in milestone_operations:
        operation_id = row.get("ID", "")
        match = re.fullmatch(r"SYNC-([0-9]{3})", operation_id)
        if match is None:
            result["errors"].append(f"Milestone operation inválida: {operation_id!r}.")
        else:
            number = int(match.group(1))
            if operation_id in projection_ids or operation_id in milestone_ids:
                result["errors"].append(f"SYNC duplicado entre ledgers: {operation_id}.")
            if number <= last_number:
                result["errors"].append(
                    "Milestone operations debe conservar orden SYNC-### creciente."
                )
            milestone_ids.add(operation_id)
            last_number = max(last_number, number)
        if row.get("State") not in OPERATION_STATES:
            result["errors"].append(f"{operation_id}: State inválido.")
        if row.get("Result") not in OPERATION_RESULTS:
            result["errors"].append(f"{operation_id}: Result inválido.")
        expected_result = OPERATION_STATE_RESULT.get(row.get("State", ""))
        if expected_result and row.get("Result") != expected_result:
            result["errors"].append(
                f"{operation_id}: State exige Result={expected_result}."
            )
        if not TASK_RE.fullmatch(row.get("Task", "")):
            result["errors"].append(f"{operation_id}: Task inválida.")
        if not SOURCE_REF_RE.fullmatch(row.get("Source ref", "")):
            result["errors"].append(f"{operation_id}: Source ref inválida.")
        if row.get("Event kind") not in MILESTONE_EVENT_KINDS:
            result["errors"].append(f"{operation_id}: Event kind inválido.")
        if row.get("Action") not in MILESTONE_ACTIONS:
            result["errors"].append(f"{operation_id}: Action inválida.")
        for column in ("Event hash", "Preview hash"):
            if not SHA256_RE.fullmatch(row.get(column, "")):
                result["errors"].append(f"{operation_id}: {column} inválido.")
        expected_duplicate = "matched" if row.get("Action") == "transition" else None
        if expected_duplicate and row.get("Duplicate check") != expected_duplicate:
            result["errors"].append(
                f"{operation_id}: transition exige Duplicate check=matched."
            )
        if row.get("Duplicate check") not in DUPLICATE_CHECK_RESULTS:
            result["errors"].append(f"{operation_id}: Duplicate check inválido.")
        if row.get("Authorized by role", "") in IDENTITY_PLACEHOLDERS:
            result["errors"].append(f"{operation_id}: falta Authorized by role.")
        for column in ("Authorized on", "Recorded on"):
            if not _valid_date(row.get(column, "")):
                result["errors"].append(f"{operation_id}: {column} inválido.")
        if any(
            _looks_sensitive(row.get(column, ""))
            or PERSONAL_DATA_RE.search(row.get(column, ""))
            or unsafe_persisted_text(row.get(column, ""))
            for column in MILESTONE_OPERATION_HEADERS
        ):
            result["errors"].append(
                f"{operation_id}: el recibo de hito contiene texto no persistible."
            )
        if row.get("State") == "authorized":
            key = (
                row.get("Task", ""),
                row.get("Source ref", ""),
                row.get("Event kind", ""),
                row.get("Action", ""),
            )
            if key in pending_keys:
                result["errors"].append(
                    f"{operation_id}: existe otra acción autorizada pendiente para el mismo hito."
                )
            pending_keys.add(key)

    if isinstance(index, dict):
        comparisons = {
            "reporting_scope": reporting.get("Scope"),
            "coordination_gate": reporting.get("Coordination gate"),
        }
        for key, wanted in comparisons.items():
            if index.get(key) != wanted:
                result["errors"].append(
                    f"task_tracking.{key} diverge de Reporting."
                )
        closed_dates = [
            row.get("Recorded on", "")
            for row in milestone_operations
            if row.get("State") != "authorized"
            and _valid_date(row.get("Recorded on", ""))
        ]
        expected_last = max(closed_dates) if closed_dates else None
        if index.get("last_reported_on") != expected_last:
            result["errors"].append(
                "task_tracking.last_reported_on no resume Milestone operations."
            )
        latest_milestones: dict[
            tuple[str, str, str, str], dict[str, str]
        ] = {}
        for row in milestone_operations:
            latest_milestones[
                (
                    row.get("Task", ""),
                    row.get("Source ref", ""),
                    row.get("Event kind", ""),
                    row.get("Action", ""),
                )
            ] = row
        operation_states = {
            row.get("State", "") for row in latest_milestones.values()
        }
        expected_status = (
            "decision-required"
            if mode == "pending"
            else "not-required"
            if mode == "repository-only" or scope == "projection-only"
            else "paused"
            if reporting.get("State") == "paused"
            else "reconciliation-required"
            if operation_states.intersection({"conflict", "reconciliation-required"})
            else "failed"
            if "failed" in operation_states
            else "pending"
            if "authorized" in operation_states
            else "ready"
        )
        if index.get("reporting_status") != expected_status:
            result["errors"].append(
                "task_tracking.reporting_status no resume la política y los recibos de hitos."
            )


def validate_tracking_contract(
    root: Path, manifest: dict[str, Any]
) -> dict[str, Any]:
    """Validate the Markdown authority and its project.json summary index."""

    result: dict[str, Any] = {
        "status": "not-applicable",
        "mode": None,
        "errors": [],
        "warnings": [],
        "checked_files": [],
        "binding": {},
        "mappings": {},
        "operations": [],
    }
    schema_version = str(manifest.get("schema_version"))
    if schema_version not in {"1.4", "1.5"}:
        return result
    try:
        contract = load_tracking_contract(root, manifest)
    except TrackingContractError as exc:
        result["status"] = "invalid"
        result["errors"].append(str(exc))
        return result

    result["checked_files"].append(TRACKING_PATH)
    binding = contract["binding"]
    mappings = contract["mappings"]
    operations = contract["operations"]
    result.update(binding=binding, mappings=mappings, operations=operations)
    result.update(
        reporting=contract.get("reporting", {}),
        workflow=contract.get("workflow", {}),
        milestone_operations=contract.get("milestone_operations", []),
    )
    mode = binding.get("Mode", "")
    result["mode"] = mode

    if any(
        _looks_sensitive(binding.get(column, ""))
        or unsafe_persisted_text(binding.get(column, ""))
        for column in BINDING_HEADERS
    ):
        result["errors"].append(
            "El binding contiene credenciales, datos o markup no persistible."
        )
    if any(
        PERSONAL_DATA_RE.search(binding.get(column, ""))
        for column in BINDING_HEADERS
    ):
        result["errors"].append(
            "El binding contiene datos personales detectables no persistibles."
        )

    if not re.fullmatch(r"TRK-[0-9]{3}", binding.get("Binding", "")):
        result["errors"].append("El binding debe usar TRK-###.")
    if binding.get("State") not in BINDING_STATES:
        result["errors"].append("State del binding debe ser proposed o confirmed.")
    if mode not in MODES:
        result["errors"].append(f"Modo de tracking inválido: {mode!r}.")
    if binding.get("Sync policy") not in SYNC_POLICIES:
        result["errors"].append("Sync policy del binding no es válida.")
    if schema_version == "1.4" and binding.get("Sync policy") == "advisory":
        result["errors"].append("schema 1.4 no admite Sync policy=advisory.")
    if binding.get("Write policy") not in WRITE_POLICIES:
        result["errors"].append("Write policy del binding no es válida.")
    if not _valid_date(binding.get("Last reviewed", "")):
        result["errors"].append("Last reviewed del binding debe usar AAAA-MM-DD.")
    decision = binding.get("Decision", "")
    confirmed_decision_required = (
        binding.get("State") == "confirmed" or mode == "jira-hybrid"
    )
    if confirmed_decision_required and not ADR_RE.fullmatch(decision):
        result["errors"].append("Un binding confirmado necesita una decisión ADR-###.")
    elif confirmed_decision_required:
        try:
            require_confirmed_tracking_decision(root, decision, mode)
        except TrackingContractError as exc:
            result["errors"].append(str(exc))
    if (
        mode == "repository-only"
        and binding.get("State") == "proposed"
        and decision != "pending: migration-preserved from schema 1.3"
    ):
        result["errors"].append(
            "Un modo repository-only propuesto solo puede proceder de migration-preserved."
        )
    if mode == "pending":
        expected = {
            "Provider": "pending",
            "Site": "pending",
            "Project": "pending",
            "Issue type": "pending",
            "Sync policy": "pending",
            "Write policy": "pending",
        }
    elif mode == "repository-only":
        expected = {
            "Provider": "none",
            "Site": "not-applicable",
            "Project": "not-applicable",
            "Issue type": "not-applicable",
            "Sync policy": "not-required",
            "Write policy": "local-only",
        }
    else:
        expected = {
            "Provider": "atlassian-rovo",
            "Write policy": "preview-and-confirm",
        }
        if schema_version == "1.4":
            expected["Sync policy"] = "required-before-execution"
        if not binding.get("Site") or binding.get("Site") == "pending":
            result["errors"].append("jira-hybrid necesita un sitio confirmado.")
        elif not _valid_https_url(binding["Site"]):
            result["errors"].append("jira-hybrid necesita una URL de sitio HTTPS segura.")
        elif urlparse(binding["Site"]).path not in {"", "/"}:
            result["errors"].append(
                "jira-hybrid necesita el origen del sitio, sin ruta de recurso."
            )
        if not PROJECT_KEY_RE.fullmatch(binding.get("Project", "")):
            result["errors"].append("jira-hybrid necesita una clave de proyecto válida.")
        if binding.get("Issue type", "") in {"", "pending", "unknown"}:
            result["errors"].append("jira-hybrid necesita un tipo de issue confirmado.")
    for column, wanted in expected.items():
        if binding.get(column) != wanted:
            result["errors"].append(
                f"{mode or 'binding'} exige {column}={wanted!r}."
            )
    if mode in {"pending", "repository-only"} and (
        contract["mapping_rows"] or operations
    ):
        result["errors"].append(
            f"{mode} exige Mapping y Operations vacíos; no puede ocultar estado Jira."
        )

    index = manifest.get("task_tracking")
    if not isinstance(index, dict):
        result["errors"].append("project.json no indexa task_tracking.")
    else:
        comparisons = {
            "source": TRACKING_PATH,
            "binding_id": binding.get("Binding"),
            "state": binding.get("State"),
            "mode": mode,
            "provider": None
            if binding.get("Provider") in {"none", "pending", ""}
            else binding.get("Provider"),
            "decision": None
            if decision == "" or decision.startswith("pending")
            else decision,
            "site": None
            if binding.get("Site") in {"", "pending", "not-applicable"}
            else binding.get("Site"),
            "project_key": None
            if binding.get("Project") in {"", "pending", "not-applicable"}
            else binding.get("Project"),
            "issue_type": None
            if binding.get("Issue type") in {"", "pending", "not-applicable"}
            else binding.get("Issue type"),
            "sync_policy": binding.get("Sync policy"),
            "write_policy": binding.get("Write policy"),
        }
        for key, wanted in comparisons.items():
            if index.get(key) != wanted:
                result["errors"].append(
                    f"task_tracking.{key} diverge de ART-TRACKING."
                )

    if schema_version == "1.5":
        _validate_reporting_contract(root, manifest, contract, result)

    task_ids: set[str] = set()
    external_ids: set[str] = set()
    external_keys: dict[str, tuple[str, str]] = {}
    operation_ids: set[str] = set()
    historical_id_by_task: dict[str, str] = {}
    historical_owner_by_id: dict[str, str] = {}
    historical_identity_by_key: dict[str, tuple[str, str]] = {}
    latest_operation_by_task: dict[str, str] = {}
    latest_success_date_by_task: dict[str, str] = {}
    last_operation_number = 0
    for row in contract["mapping_rows"]:
        task_id = row.get("Task", "")
        if not TASK_RE.fullmatch(task_id):
            result["errors"].append(f"Mapping con task inválida: {task_id!r}.")
        elif task_id in task_ids:
            result["errors"].append(f"Mapping duplicado para {task_id}.")
        task_ids.add(task_id)
        state = row.get("State", "")
        if state not in MAPPING_STATES:
            result["errors"].append(f"{task_id}: estado de mapping inválido.")
        external_id = row.get("External ID", "")
        external_key = row.get("External key", "")
        fingerprint = row.get("Projection fingerprint", "")
        if external_id not in IDENTITY_PLACEHOLDERS:
            if not EXTERNAL_ID_RE.fullmatch(external_id):
                result["errors"].append(
                    f"{task_id}: External ID debe ser el identificador Jira numérico."
                )
            if external_id in external_ids:
                result["errors"].append(f"External ID duplicado: {external_id}.")
            external_ids.add(external_id)
        if external_key not in IDENTITY_PLACEHOLDERS:
            previous = external_keys.get(external_key.casefold())
            if previous and previous != (external_id, task_id):
                result["errors"].append(
                    f"External key {external_key} está ligada a más de una identidad o TASK."
                )
            external_keys[external_key.casefold()] = (external_id, task_id)
            project_key = binding.get("Project", "")
            if mode == "jira-hybrid" and not external_key_matches_project(
                project_key, external_key
            ):
                result["errors"].append(
                    f"{task_id}: External key no pertenece al proyecto Jira confirmado."
                )
        if state in {"synced", "out-of-sync"}:
            if external_id in IDENTITY_PLACEHOLDERS or external_key in IDENTITY_PLACEHOLDERS:
                result["errors"].append(
                    f"{task_id}: {state} exige External ID y External key."
                )
            if not SHA256_RE.fullmatch(fingerprint):
                result["errors"].append(
                    f"{task_id}: {state} exige Projection fingerprint SHA-256."
                )
        if state == "unlinked":
            for column in (
                "External ID",
                "External key",
                "URL",
                "Projection fingerprint",
                "Last synced",
                "Last operation",
            ):
                if row.get(column, "") not in IDENTITY_PLACEHOLDERS | {
                    "not-recorded"
                }:
                    result["errors"].append(
                        f"{task_id}: unlinked no puede conservar {column}."
                    )
        mapping_url = row.get("URL", "")
        if state in {"synced", "out-of-sync"} and mapping_url in {
            "",
            "pending",
            "none",
            "not-recorded",
        }:
            result["errors"].append(
                f"{task_id}: {state} exige una URL Jira observada completa."
            )
        if mapping_url not in {"", "pending", "none", "not-recorded"}:
            if not _valid_https_url(mapping_url):
                result["errors"].append(f"{task_id}: URL externa inválida.")
            elif mode == "jira-hybrid" and not _same_origin(
                binding.get("Site", ""), mapping_url
            ):
                result["errors"].append(
                    f"{task_id}: URL externa pertenece a otro site Jira."
                )
            elif external_key not in IDENTITY_PLACEHOLDERS and not url_matches_external_key(
                mapping_url, external_key
            ):
                result["errors"].append(
                    f"{task_id}: URL externa no corresponde a External key."
                )
        if any(_looks_sensitive(row.get(column, "")) for column in MAPPING_HEADERS):
            result["errors"].append(
                f"{task_id}: el mapping parece contener credenciales o secretos."
            )
        if any(
            PERSONAL_DATA_RE.search(row.get(column, ""))
            for column in MAPPING_HEADERS
        ):
            result["errors"].append(
                f"{task_id}: el mapping contiene datos personales detectables."
            )
        if any(
            unsafe_persisted_text(row.get(column, ""))
            for column in MAPPING_HEADERS
        ):
            result["errors"].append(
                f"{task_id}: el mapping contiene markup no persistible."
            )
        last_synced = row.get("Last synced", "")
        if last_synced not in {"", "pending", "none"} and not _valid_date(last_synced):
            result["errors"].append(f"{task_id}: Last synced inválido.")
        if state in {"synced", "out-of-sync"} and not _valid_date(last_synced):
            result["errors"].append(
                f"{task_id}: {state} exige Last synced con fecha observada."
            )

    for row in operations:
        operation_id = row.get("ID", "")
        operation_match = re.fullmatch(r"SYNC-([0-9]{3})", operation_id)
        if operation_match is None:
            result["errors"].append(f"Operación inválida: {operation_id!r}.")
        elif operation_id in operation_ids:
            result["errors"].append(f"Operación duplicada: {operation_id}.")
        else:
            operation_number = int(operation_match.group(1))
            if operation_number <= last_operation_number:
                result["errors"].append(
                    f"{operation_id}: Operations debe conservar orden SYNC-### "
                    "estrictamente creciente."
                )
            last_operation_number = max(last_operation_number, operation_number)
            operation_task = row.get("Task", "")
            previous_latest = latest_operation_by_task.get(operation_task)
            if previous_latest is None or operation_number > int(
                previous_latest.removeprefix("SYNC-")
            ):
                latest_operation_by_task[operation_task] = operation_id
        operation_ids.add(operation_id)
        if row.get("State") not in OPERATION_STATES:
            result["errors"].append(f"{operation_id}: State inválido.")
        action = row.get("Action")
        if action not in {"create", "update", "reconcile"}:
            result["errors"].append(
                f"{operation_id}: la proyección solo admite create, update o reconcile."
            )
        operation_result = row.get("Result")
        if operation_result not in OPERATION_RESULTS:
            result["errors"].append(f"{operation_id}: Result inválido.")
        expected_result = OPERATION_STATE_RESULT.get(row.get("State", ""))
        if expected_result is not None and operation_result != expected_result:
            result["errors"].append(
                f"{operation_id}: State={row.get('State')} exige Result={expected_result}."
            )
        if row.get("State") == "authorized" and action == "reconcile":
            result["errors"].append(
                f"{operation_id}: reconcile registra una lectura ya observada, no una escritura autorizada pendiente."
            )
        if not TASK_RE.fullmatch(row.get("Task", "")):
            result["errors"].append(f"{operation_id}: Task inválida.")
        if not SHA256_RE.fullmatch(row.get("Preview hash", "")):
            result["errors"].append(f"{operation_id}: Preview hash inválido.")
        if not SHA256_RE.fullmatch(row.get("Projection fingerprint", "")):
            result["errors"].append(
                f"{operation_id}: Projection fingerprint inválido."
            )
        duplicate_check = row.get("Duplicate check", "")
        if duplicate_check not in DUPLICATE_CHECK_RESULTS:
            result["errors"].append(
                f"{operation_id}: Duplicate check inválido."
            )
        if action == "create" and duplicate_check != "no-match":
            result["errors"].append(
                f"{operation_id}: create exige Duplicate check=no-match."
            )
        if action == "update" and duplicate_check != "matched":
            result["errors"].append(
                f"{operation_id}: update exige Duplicate check=matched."
            )
        if action == "reconcile":
            expected_duplicate_check = {
                "succeeded": "matched",
                "failed": "no-match",
                "conflict": "conflict",
                "uncertain": "uncertain",
            }.get(operation_result)
            if expected_duplicate_check and duplicate_check != expected_duplicate_check:
                result["errors"].append(
                    f"{operation_id}: reconcile/{operation_result} exige "
                    f"Duplicate check={expected_duplicate_check}."
                )
        if row.get("Authorized by role", "") in {"", "pending", "unknown"}:
            result["errors"].append(
                f"{operation_id}: falta el rol que autorizó el preview externo."
            )
        if not _valid_date(row.get("Authorized on", "")):
            result["errors"].append(f"{operation_id}: Authorized on inválido.")
        if not _valid_date(row.get("Recorded on", "")):
            result["errors"].append(f"{operation_id}: Recorded on inválido.")
        if row.get("State") == "recorded" and (
            row.get("External ID", "") in IDENTITY_PLACEHOLDERS
            or row.get("External key", "") in IDENTITY_PLACEHOLDERS
        ):
            result["errors"].append(
                f"{operation_id}: succeeded exige identidad externa observada."
            )
        operation_external_id = row.get("External ID", "")
        operation_external_key = row.get("External key", "")
        if operation_external_id not in IDENTITY_PLACEHOLDERS and not EXTERNAL_ID_RE.fullmatch(
            operation_external_id
        ):
            result["errors"].append(
                f"{operation_id}: External ID debe ser el identificador Jira numérico."
            )
        elif operation_external_id not in IDENTITY_PLACEHOLDERS:
            operation_task = row.get("Task", "")
            previous_id = historical_id_by_task.get(operation_task)
            if previous_id is not None and previous_id != operation_external_id:
                result["errors"].append(
                    f"{operation_id}: External ID rompe la identidad inmutable de "
                    f"{operation_task} ({previous_id})."
                )
            historical_id_by_task.setdefault(operation_task, operation_external_id)
            previous_owner = historical_owner_by_id.get(operation_external_id)
            if previous_owner is not None and previous_owner != operation_task:
                result["errors"].append(
                    f"{operation_id}: External ID histórico también pertenece a "
                    f"{previous_owner}."
                )
            historical_owner_by_id.setdefault(operation_external_id, operation_task)
        if operation_external_key not in IDENTITY_PLACEHOLDERS and not external_key_matches_project(
            binding.get("Project", ""), operation_external_key
        ):
            result["errors"].append(
                f"{operation_id}: External key no pertenece exactamente al proyecto Jira."
            )
        elif operation_external_key not in IDENTITY_PLACEHOLDERS:
            operation_task = row.get("Task", "")
            key_identity = historical_identity_by_key.get(
                operation_external_key.casefold()
            )
            if key_identity is not None:
                previous_id, previous_task = key_identity
                id_conflict = (
                    previous_id not in IDENTITY_PLACEHOLDERS
                    and operation_external_id not in IDENTITY_PLACEHOLDERS
                    and previous_id != operation_external_id
                )
                if previous_task != operation_task or id_conflict:
                    result["errors"].append(
                        f"{operation_id}: External key histórica "
                        f"{operation_external_key} ya pertenece a "
                        f"{previous_task}/{previous_id}."
                    )
                elif (
                    previous_id in IDENTITY_PLACEHOLDERS
                    and operation_external_id not in IDENTITY_PLACEHOLDERS
                ):
                    historical_identity_by_key[
                        operation_external_key.casefold()
                    ] = (operation_external_id, operation_task)
            else:
                historical_identity_by_key[operation_external_key.casefold()] = (
                    operation_external_id,
                    operation_task,
                )
        if any(_looks_sensitive(row.get(column, "")) for column in OPERATION_HEADERS):
            result["errors"].append(
                f"{operation_id}: el recibo parece contener credenciales o secretos."
            )
        if any(
            PERSONAL_DATA_RE.search(row.get(column, ""))
            for column in OPERATION_HEADERS
        ):
            result["errors"].append(
                f"{operation_id}: el recibo contiene datos personales detectables."
            )
        if any(
            unsafe_persisted_text(row.get(column, ""))
            for column in OPERATION_HEADERS
        ):
            result["errors"].append(
                f"{operation_id}: el recibo contiene markup no persistible."
            )
        if (
            _valid_date(row.get("Authorized on", ""))
            and _valid_date(row.get("Recorded on", ""))
            and row["Authorized on"] > row["Recorded on"]
        ):
            result["errors"].append(
                f"{operation_id}: la autorización no puede ser posterior al registro."
            )
        if (
            row.get("State") == "recorded"
            and row.get("Result") == "succeeded"
            and _valid_date(row.get("Recorded on", ""))
        ):
            latest_success_date_by_task[row.get("Task", "")] = row["Recorded on"]

    operations_by_id = {
        row.get("ID", ""): row
        for row in operations
        if SYNC_RE.fullmatch(row.get("ID", ""))
    }
    authorized_by_task: dict[str, list[str]] = {}
    for operation_id, operation in operations_by_id.items():
        operation_task = operation.get("Task", "")
        mapping = mappings.get(operation_task)
        if mapping is None:
            result["errors"].append(
                f"{operation_id}: no existe Mapping para {operation_task}."
            )
            continue
        if operation.get("State") == "authorized":
            authorized_by_task.setdefault(operation_task, []).append(operation_id)
            if (
                mapping.get("State") != "pending"
                or mapping.get("Last operation") != operation_id
            ):
                result["errors"].append(
                    f"{operation_id}: una autorización pendiente debe ser el último "
                    f"recibo del Mapping pending de {operation_task}."
                )
    for operation_task, pending_ids in authorized_by_task.items():
        if len(pending_ids) > 1:
            result["errors"].append(
                f"{operation_task}: hay más de una escritura autorizada pendiente."
            )
    expected_mapping_state = {
        "authorized": "pending",
        "recorded": "synced",
        "failed": "failed",
        "conflict": "conflict",
        "reconciliation-required": "reconciliation-required",
    }
    for mapping in contract["mapping_rows"]:
        task_id = mapping.get("Task", "")
        state = mapping.get("State", "")
        last_operation = mapping.get("Last operation", "")
        if state in {
            "pending",
            "synced",
            "out-of-sync",
            "failed",
            "conflict",
            "reconciliation-required",
        } and last_operation in IDENTITY_PLACEHOLDERS:
            result["errors"].append(
                f"{task_id}: State={state} exige Last operation SYNC-###."
            )
            continue
        if last_operation in IDENTITY_PLACEHOLDERS:
            continue
        operation = operations_by_id.get(last_operation)
        if operation is None:
            result["errors"].append(
                f"{task_id}: Last operation {last_operation!r} no existe."
            )
            continue
        if operation.get("Task") != task_id:
            result["errors"].append(
                f"{task_id}: Last operation pertenece a otra TASK."
            )
        latest_operation = latest_operation_by_task.get(task_id)
        if latest_operation is not None and last_operation != latest_operation:
            result["errors"].append(
                f"{task_id}: Last operation debe apuntar al último recibo durable "
                f"{latest_operation}; no puede rebobinar el historial a {last_operation}."
            )
        wanted_state = expected_mapping_state.get(operation.get("State", ""))
        if state != "out-of-sync" and wanted_state and state != wanted_state:
            result["errors"].append(
                f"{task_id}: State={state} diverge de {last_operation}/{operation.get('State')}."
            )
        if state == "out-of-sync" and (
            operation.get("State") != "recorded"
            or operation.get("Result") != "succeeded"
        ):
            result["errors"].append(
                f"{task_id}: out-of-sync exige un recibo ancla recorded/succeeded."
            )
        for mapping_column, operation_column in (
            ("External ID", "External ID"),
            ("External key", "External key"),
        ):
            if mapping.get(mapping_column) != operation.get(operation_column):
                result["errors"].append(
                    f"{task_id}: {mapping_column} diverge del recibo "
                    f"{last_operation}; la identidad durable no puede reescribirse."
                )
        if state in {"synced", "out-of-sync"}:
            if mapping.get("Projection fingerprint") != operation.get(
                "Projection fingerprint"
            ):
                result["errors"].append(
                    f"{task_id}: Projection fingerprint diverge del recibo "
                    f"{last_operation}."
                )
        latest_success_date = latest_success_date_by_task.get(task_id)
        if latest_success_date is not None:
            if mapping.get("Last synced") != latest_success_date:
                result["errors"].append(
                    f"{task_id}: Last synced diverge del último recibo "
                    "recorded/succeeded."
                )
        elif mapping.get("Last synced", "") not in IDENTITY_PLACEHOLDERS | {
            "not-recorded"
        }:
            result["errors"].append(
                f"{task_id}: Last synced no puede inventar una observación sin "
                "recibo recorded/succeeded."
            )

    if isinstance(index, dict):
        indexed_status = index.get("sync_status")
        indexed_fingerprint = index.get("projection_fingerprint")
        mapping_states = {
            mapping.get("State", "") for mapping in contract["mapping_rows"]
        }
        unmapped_has_failed = False
        unmapped_has_pending = False
        if mode == "jira-hybrid":
            delivery_tasks = set(
                validate_delivery_contract(root, manifest).get("tasks", {})
            )
            mapped_tasks = {
                mapping.get("Task", "")
                for mapping in contract["mapping_rows"]
            }
            for task_id in sorted(delivery_tasks - mapped_tasks):
                try:
                    missing_preview = _build_projection_preview_from_contract(
                        root, manifest, result, [task_id]
                    )
                except TrackingPlanningBlocked:
                    continue
                except TrackingContractError:
                    unmapped_has_failed = True
                    continue
                if missing_preview["operations"]:
                    unmapped_has_pending = True
        allowed_index_statuses: set[str]
        if mode == "pending":
            allowed_index_statuses = {"decision-required"}
        elif mode == "repository-only":
            allowed_index_statuses = {"not-required"}
        elif not mapping_states and not operations:
            # Before the first durable sync attempt, pending remains the honest
            # index even if a current TASK is not externally projectable.
            allowed_index_statuses = {"pending"}
        elif mapping_states.intersection(
            {"conflict", "reconciliation-required"}
        ):
            allowed_index_statuses = {"reconciliation-required"}
        elif "failed" in mapping_states or unmapped_has_failed:
            allowed_index_statuses = {"failed"}
        elif not mapping_states or mapping_states.intersection(
            {"pending", "unlinked"}
        ) or unmapped_has_pending:
            allowed_index_statuses = {"pending"}
        elif "out-of-sync" in mapping_states:
            allowed_index_statuses = {"out-of-sync"}
        elif mapping_states == {"synced"}:
            # A confirmed planning change invalidates the aggregate index before
            # the next Jira write, while preserving the last observed mappings.
            allowed_index_statuses = {"in-sync", "out-of-sync"}
        else:
            allowed_index_statuses = {"invalid"}
        if indexed_status not in allowed_index_statuses:
            result["errors"].append(
                "task_tracking.sync_status no resume el estado durable de "
                f"ART-TRACKING; se esperaba {sorted(allowed_index_statuses)}."
            )

        closed_operation_dates = [
            operation.get("Recorded on", "")
            for operation in operations
            if operation.get("State") != "authorized"
            and _valid_date(operation.get("Recorded on", ""))
        ]
        expected_last_sync_on = (
            max(closed_operation_dates) if closed_operation_dates else None
        )
        if index.get("last_sync_on") != expected_last_sync_on:
            result["errors"].append(
                "task_tracking.last_sync_on no resume la fecha del último "
                "recibo cerrado de ART-TRACKING."
            )
        if indexed_status == "in-sync":
            if not contract["mapping_rows"]:
                result["errors"].append(
                    "task_tracking no puede declarar in-sync sin mappings observados."
                )
            if any(
                mapping.get("State") != "synced"
                for mapping in contract["mapping_rows"]
            ):
                result["errors"].append(
                    "task_tracking in-sync exige que todos los mappings sean synced."
                )
            projection_set = {
                mapping.get("Task", ""): mapping.get(
                    "Projection fingerprint", ""
                )
                for mapping in contract["mapping_rows"]
            }
            if (
                projection_set
                and all(SHA256_RE.fullmatch(value) for value in projection_set.values())
                and indexed_fingerprint != _canonical_hash(projection_set)
            ):
                result["errors"].append(
                    "task_tracking.projection_fingerprint no resume los mappings synced."
                )
        elif indexed_fingerprint is not None:
            result["errors"].append(
                "task_tracking.projection_fingerprint debe ser null fuera de in-sync."
            )

    result["errors"] = list(dict.fromkeys(result["errors"]))
    result["status"] = "invalid" if result["errors"] else (
        "decision-required"
        if mode == "pending" or binding.get("State") != "confirmed"
        else "not-required"
        if mode == "repository-only"
        else "configured"
    )
    return result


def _single_row(details: dict[str, Any], name: str) -> dict[str, str]:
    rows = details.get(name, [])
    return rows[0] if isinstance(rows, list) and len(rows) == 1 else {}


def _task_payload(
    root: Path,
    manifest: dict[str, Any],
    binding: dict[str, str],
    task_id: str,
    row: dict[str, str],
    details: dict[str, Any],
) -> dict[str, Any]:
    definition = _single_row(details, "definition")
    plan = _single_row(details, "plan")
    dependencies = sorted(
        set(re.findall(r"\bTASK-[0-9]{3}\b", row.get("Dependencies", "")))
    )
    marker = correlation_marker(str(manifest.get("project_id", "")), task_id)
    relative_path = f"docs/lks-sdd/04-delivery/tasks/{task_id}.md"
    try:
        task_text = (root / relative_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise TrackingContractError(
            f"No se puede revisar la clasificación de {task_id}: {exc}"
        ) from exc
    classification = _task_classification(task_text, task_id)
    if classification in {"confidential", "restricted"}:
        raise TrackingContractError(
            f"{task_id}: classification={classification} bloquea la proyección externa; "
            "use repository-only o prepare una definición saneada y reclasificada."
        )
    if classification not in {"internal", "public", "client"}:
        raise TrackingContractError(
            f"{task_id}: falta una classification externa válida y permitida; "
            "la proyección falla de forma cerrada."
        )
    governed = {
        "task_id": task_id,
        "summary": f"[{task_id}] {row.get('Title', '').strip()}",
        "description": {
            "marker": marker,
            "canonical_path": relative_path,
            "objective": definition.get("Objective", ""),
            "in_scope": definition.get("In scope", ""),
            "out_of_scope": definition.get("Out of scope", ""),
            "requirements": definition.get("Requirements", ""),
            "acceptance": definition.get("Acceptance", ""),
            "dependencies": dependencies,
            "tests": plan.get("Tests", ""),
            "definition_of_done": plan.get("Definition of done", ""),
            "required_evidence": plan.get("Required evidence", ""),
        },
        "context": {
            "plan": row.get("Plan", ""),
            "release": row.get("Release", ""),
            "increment": row.get("Increment", ""),
            "unit": row.get("Unit", ""),
            "profile_binding": row.get("Profile binding", ""),
        },
        "jira_target": {
            "site": binding.get("Site"),
            "project_key": binding.get("Project"),
            "issue_type": binding.get("Issue type"),
        },
    }
    sensitive_path = _payload_secret_path(governed)
    if sensitive_path:
        raise TrackingContractError(
            "La proyección se ha bloqueado porque un campo gobernado parece contener "
            f"un secreto ({sensitive_path}); sanee el Markdown antes de continuar."
        )
    personal_path = _payload_personal_path(governed)
    if personal_path:
        raise TrackingContractError(
            "La proyección se ha bloqueado porque un campo gobernado parece contener "
            f"datos personales ({personal_path}); sanee el Markdown antes de continuar."
        )
    fingerprint = _canonical_hash(governed)
    governed["projection_fingerprint"] = fingerprint
    governed["description"]["projection_fingerprint"] = fingerprint
    return governed


def _build_projection_preview_from_contract(
    root: Path,
    manifest: dict[str, Any],
    tracking: dict[str, Any],
    task_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a preview from an already validated local tracking contract."""

    if tracking["mode"] != "jira-hybrid":
        raise TrackingContractError("La proyección Jira requiere mode=jira-hybrid.")
    if tracking["binding"].get("State") != "confirmed":
        raise TrackingContractError("El binding Jira debe estar confirmed.")
    delivery = validate_delivery_contract(root, manifest)
    if delivery.get("errors"):
        raise TrackingContractError(
            "El contrato PLAN/TASK no es proyectable: " + "; ".join(delivery["errors"])
        )
    available = delivery.get("tasks", {})
    selected = sorted(
        set(available.keys() if task_ids is None else task_ids)
    )
    unknown = [task_id for task_id in selected if task_id not in available]
    if unknown:
        raise TrackingContractError(
            "Tareas no definidas: " + ", ".join(unknown) + "."
        )
    planning_blockers: list[str] = []
    by_increment: dict[str, list[str]] = {}
    for task_id in selected:
        increment = available[task_id].get("Increment", "")
        if not re.fullmatch(r"INC-[0-9]{3}", increment):
            planning_blockers.append(
                f"{task_id}: no declara un incremento proyectable."
            )
            continue
        by_increment.setdefault(increment, []).append(task_id)
        planning_blockers.extend(
            f"{task_id}: {message}"
            for message in delivery.get("task_readiness_blockers", {}).get(
                task_id, []
            )
        )
    for increment, increment_tasks in sorted(by_increment.items()):
        planning = assess_planning(root, manifest, increment)
        confirmed = bool(planning.get("confirmed_by_role"))
        stored_fingerprints = planning.get("stored_fingerprints", {})
        fingerprints_match = (
            planning.get("specification_fingerprint")
            == stored_fingerprints.get("specification")
            and planning.get("planning_fingerprint")
            == stored_fingerprints.get("planning")
        )
        eligible = planning.get("status") == "complete" or bool(
            planning.get("partial_implementation_policy_satisfied")
        )
        if (
            planning.get("integrity") != "valid"
            or not eligible
            or not confirmed
            or not fingerprints_match
        ):
            planning_blockers.append(
                f"{increment}: la planificación local no está confirmada, íntegra "
                "y vigente para proyectar tareas."
            )
            continue
        executable = set(planning.get("tasks", {}).get("executable", []))
        non_executable = sorted(set(increment_tasks) - executable)
        if non_executable:
            planning_blockers.append(
                f"{increment}: tareas sin definición ejecutable: "
                + ", ".join(non_executable)
                + "."
            )
    if planning_blockers:
        raise TrackingPlanningBlocked(
            "El plan confirmado no permite la proyección Jira: "
            + "; ".join(dict.fromkeys(planning_blockers))
        )
    operations: list[dict[str, Any]] = []
    receipts = {
        item.get("ID", ""): item for item in tracking.get("operations", [])
    }
    for task_id in selected:
        payload = _task_payload(
            root,
            manifest,
            tracking["binding"],
            task_id,
            available[task_id],
            delivery.get("task_details", {}).get(task_id, {}),
        )
        mapping = tracking["mappings"].get(task_id, {})
        mapping_state = mapping.get("State", "unlinked")
        last_receipt = receipts.get(mapping.get("Last operation", ""), {})
        if (
            mapping_state == "pending"
            and last_receipt.get("State") == "authorized"
        ):
            action = (
                "awaiting-execution"
                if last_receipt.get("Projection fingerprint")
                == payload["projection_fingerprint"]
                else "blocked-reconciliation"
            )
        elif mapping_state in {"conflict", "reconciliation-required"}:
            action = "blocked-reconciliation"
        elif mapping.get("External ID", "") not in {"", "pending", "none"}:
            action = (
                "noop"
                if mapping.get("Projection fingerprint")
                == payload["projection_fingerprint"]
                else "update"
            )
        else:
            action = "create"
        operations.append(
            {
                "action": action,
                "task_id": task_id,
                "external_id": None
                if mapping.get("External ID") in {None, "", "pending", "none", "unknown"}
                else mapping.get("External ID"),
                "external_key": None
                if mapping.get("External key") in {None, "", "pending", "none", "unknown"}
                else mapping.get("External key"),
                "correlation_marker": payload["description"]["marker"],
                "duplicate_check": {
                    "project_key": tracking["binding"].get("Project"),
                    "marker": payload["description"]["marker"],
                },
                "payload": payload,
            }
        )
    preview = {
        "contract": "lks-sdd-jira-projection/1.0",
        "project_id": manifest.get("project_id"),
        "binding_id": tracking["binding"].get("Binding"),
        "direction": "outbound-only",
        "authority": "markdown",
        "operations": operations,
        "external_write_authorized": False,
    }
    preview["preview_hash"] = _canonical_hash(preview)
    return preview


def build_projection_preview(
    root: Path,
    manifest: dict[str, Any],
    task_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build idempotent Jira create/update/no-op operations, without I/O."""

    tracking = validate_tracking_contract(root, manifest)
    if tracking["errors"]:
        raise TrackingContractError("; ".join(tracking["errors"]))
    return _build_projection_preview_from_contract(
        root, manifest, tracking, task_ids
    )


def assess_tracking(
    root: Path,
    manifest: dict[str, Any],
    task_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Return an orthogonal task-tracking readiness axis."""

    validation = validate_tracking_contract(root, manifest)
    result: dict[str, Any] = {
        "status": validation["status"],
        "mode": validation["mode"],
        "policy": validation.get("binding", {}).get("Sync policy"),
        "blockers": list(validation["errors"]),
        "warnings": list(validation["warnings"]),
        "tasks": {},
        "checked_files": validation["checked_files"],
    }
    if str(manifest.get("schema_version")) not in {"1.4", "1.5"} or validation["errors"]:
        return result
    if validation["mode"] == "pending":
        result["blockers"].append(
            "Debe decidir si la gestión de tareas será repository-only o jira-hybrid."
        )
        return result
    if validation.get("binding", {}).get("State") != "confirmed":
        result["status"] = "decision-required"
        result["blockers"].append(
            "Debe confirmar explícitamente el modo de tracking antes de autorizar "
            "o iniciar una implementación."
        )
        return result
    if validation["mode"] == "repository-only":
        result["status"] = "not-required"
        return result
    try:
        preview = build_projection_preview(root, manifest, task_ids)
    except TrackingPlanningBlocked as exc:
        result["status"] = "not-assessed"
        result["warnings"].append(str(exc))
        return result
    except TrackingContractError as exc:
        result["status"] = "invalid"
        result["blockers"].append(str(exc))
        return result
    actions = {item["task_id"]: item["action"] for item in preview["operations"]}
    result["tasks"] = actions
    if not actions:
        result["status"] = "not-assessed"
        result["warnings"].append(
            "No hay una TASK seleccionada para evaluar el tracking externo."
        )
        return result
    if any(action == "blocked-reconciliation" for action in actions.values()):
        result["status"] = "reconciliation-required"
    elif any(action == "create" for action in actions.values()):
        result["status"] = "pending"
    elif any(action == "awaiting-execution" for action in actions.values()):
        result["status"] = "pending"
    elif any(action == "update" for action in actions.values()):
        result["status"] = "out-of-sync"
    else:
        result["status"] = "in-sync"
    if result["status"] != "in-sync":
        message = (
            "La proyección Jira de las tareas seleccionadas no está sincronizada: "
            + ", ".join(f"{task}={action}" for task, action in actions.items())
            + "."
        )
        if validation["binding"].get("Sync policy") == "required-before-execution":
            result["blockers"].append(message)
        else:
            result["warnings"].append(message)
    return result


__all__ = [
    "BINDING_HEADERS",
    "DUPLICATE_CHECK_RESULTS",
    "MAPPING_HEADERS",
    "OPERATION_HEADERS",
    "REPORTING_HEADERS",
    "WORKFLOW_HEADERS",
    "MILESTONE_OPERATION_HEADERS",
    "MILESTONE_EVENT_KINDS",
    "OPERATION_RESULTS",
    "PERSONAL_DATA_RE",
    "SENSITIVE_VALUE_RE",
    "TRACKING_PATH",
    "TrackingContractError",
    "TrackingPlanningBlocked",
    "assess_tracking",
    "build_projection_preview",
    "correlation_marker",
    "load_tracking_contract",
    "require_confirmed_tracking_decision",
    "validate_tracking_contract",
    "external_key_matches_project",
    "unsafe_persisted_text",
    "url_matches_external_key",
]
