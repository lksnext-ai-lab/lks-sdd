#!/usr/bin/env python3
"""Select and verify stable-preflight evidence before a tag reuses it."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_release_artifacts
import verify_draft_promotion


SELECTION_SCHEMA_VERSION = "preflight-run-selection-1.0"
PROVENANCE_SCHEMA_VERSION = "preflight-provenance-1.0"
RELEASE_PROVENANCE_SCHEMA_VERSION = "release-provenance-1.0"


class PreflightProvenanceError(Exception):
    """Expected failure while selecting or verifying preflight evidence."""


def _read_json(path: Path, label: str) -> dict[str, Any] | list[Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreflightProvenanceError(f"No se puede leer {label}: {exc}") from exc
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        try:
            value = [json.loads(line) for line in content.splitlines() if line.strip()]
        except json.JSONDecodeError as exc:
            raise PreflightProvenanceError(
                f"{label} no contiene JSON válido: {exc}"
            ) from exc
    if not isinstance(value, (dict, list)):
        raise PreflightProvenanceError(f"{label} debe contener un objeto o lista JSON.")
    return value


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise PreflightProvenanceError(f"Falta {label}.")
    try:
        parsed = datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith("Z") else value
        )
    except ValueError as exc:
        raise PreflightProvenanceError(f"{label} no es una fecha ISO-8601 válida.") from exc
    if parsed.tzinfo is None:
        raise PreflightProvenanceError(f"{label} debe incluir zona horaria.")
    return parsed.astimezone(timezone.utc)


def _workflow_runs(value: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        runs = value.get("workflow_runs")
    else:
        runs = value
    if not isinstance(runs, list):
        raise PreflightProvenanceError(
            "La respuesta de GitHub Actions no contiene workflow_runs."
        )
    if not all(isinstance(run, dict) for run in runs):
        raise PreflightProvenanceError("workflow_runs contiene una ejecución inválida.")
    return runs


def _repository_name(run: dict[str, Any]) -> str | None:
    repository = run.get("repository")
    return repository.get("full_name") if isinstance(repository, dict) else None


def select_run(
    value: dict[str, Any] | list[Any],
    *,
    source_commit: str,
    default_branch: str,
    repository: str,
) -> dict[str, Any]:
    """Select the newest successful manual quality run for an exact commit."""

    candidates: list[tuple[datetime, int, dict[str, Any]]] = []
    for run in _workflow_runs(value):
        if (
            run.get("event") != "workflow_dispatch"
            or run.get("status") != "completed"
            or run.get("conclusion") != "success"
            or run.get("head_sha") != source_commit
            or run.get("head_branch") != default_branch
            or _repository_name(run) != repository
        ):
            continue
        run_id = run.get("id")
        attempt = run.get("run_attempt")
        if (
            not isinstance(run_id, int)
            or run_id < 1
            or not isinstance(attempt, int)
            or attempt < 1
        ):
            raise PreflightProvenanceError(
                "La ejecución candidata no declara id e intento válidos."
            )
        candidates.append((_timestamp(run.get("updated_at"), "updated_at"), run_id, run))
    if not candidates:
        return {
            "schema_version": SELECTION_SCHEMA_VERSION,
            "status": "missing",
            "reason": "No existe un stable-preflight correcto para este SHA.",
        }
    _, _, run = max(candidates, key=lambda item: (item[0], item[1]))
    return {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "status": "found",
        "run": {
            "id": run["id"],
            "run_attempt": run["run_attempt"],
            "event": run["event"],
            "head_sha": run["head_sha"],
            "head_branch": run["head_branch"],
            "updated_at": run["updated_at"],
            "repository": _repository_name(run),
        },
    }


def _validate_readiness(
    evidence: Path, *, source_commit: str, plugin_version: str
) -> None:
    readiness = _read_json(evidence / "release-readiness.json", "release-readiness.json")
    checks = readiness.get("checks")
    expected_checks = {
        "contract",
        "distribution",
        "worktree",
        "approval",
        "source",
        "release-tag",
    }
    check_ids = [
        check.get("id") for check in checks if isinstance(check, dict)
    ] if isinstance(checks, list) else []
    if (
        readiness.get("readiness") != "ready"
        or readiness.get("channel") != "stable"
        or readiness.get("source_commit") != source_commit
        or readiness.get("version") != plugin_version
        or not isinstance(checks, list)
        or len(check_ids) != len(checks)
        or set(check_ids) != expected_checks
        or any(check.get("status") != "passed" for check in checks)
    ):
        raise PreflightProvenanceError(
            "El readiness del preflight no acredita esta release stable."
        )


def _validate_preflight_record(
    evidence: Path,
    selection: dict[str, Any],
    *,
    source_commit: str,
    plugin_version: str,
) -> dict[str, Any]:
    if (
        selection.get("schema_version") != SELECTION_SCHEMA_VERSION
        or selection.get("status") != "found"
        or not isinstance(selection.get("run"), dict)
    ):
        raise PreflightProvenanceError("No se seleccionó un preflight reutilizable.")
    run = selection["run"]
    record = _read_json(
        evidence / "preflight-provenance.json", "preflight-provenance.json"
    )
    if (
        not isinstance(record, dict)
        or run.get("event") != "workflow_dispatch"
        or run.get("head_sha") != source_commit
        or not isinstance(run.get("head_branch"), str)
        or not run["head_branch"]
        or not isinstance(run.get("repository"), str)
        or not run["repository"]
        or not isinstance(run.get("updated_at"), str)
        or record.get("schema_version") != PROVENANCE_SCHEMA_VERSION
        or record.get("workflow") != "quality"
        or record.get("event") != "workflow_dispatch"
        or record.get("run_id") != run.get("id")
        or record.get("run_attempt") != run.get("run_attempt")
        or record.get("source_commit") != source_commit
        or record.get("source_ref") != run.get("head_branch")
        or record.get("plugin_version") != plugin_version
        or record.get("channel") != "stable"
    ):
        raise PreflightProvenanceError(
            "La procedencia del preflight no coincide con el run seleccionado."
        )
    return run


def verify_reusable_preflight(
    evidence: Path,
    selection: dict[str, Any],
    *,
    tag: str,
    source_commit: str,
    changelog: Path,
) -> dict[str, Any]:
    """Verify that a selected preflight can become exact tag evidence."""

    if not isinstance(selection, dict):
        raise PreflightProvenanceError("La selección de preflight debe ser un objeto.")
    try:
        plan = verify_draft_promotion.build_plan(
            evidence, tag, source_commit, changelog
        )
    except verify_draft_promotion.DraftPromotionError as exc:
        raise PreflightProvenanceError(str(exc)) from exc
    plugin_version = plan["plugin_version"]
    _validate_readiness(
        evidence, source_commit=source_commit, plugin_version=plugin_version
    )
    run = _validate_preflight_record(
        evidence,
        selection,
        source_commit=source_commit,
        plugin_version=plugin_version,
    )
    report = _read_json(
        evidence / "release-package-validation.json",
        "release-package-validation.json",
    )
    if not isinstance(report, dict):
        raise PreflightProvenanceError(
            "La validación de paquetes debe ser un objeto JSON."
        )
    try:
        validate_release_artifacts.validate_report(evidence / "candidate", report)
    except validate_release_artifacts.ReleasePackageValidationError as exc:
        raise PreflightProvenanceError(str(exc)) from exc
    return {
        "schema_version": RELEASE_PROVENANCE_SCHEMA_VERSION,
        "status": "passed",
        "mode": "reused-stable-preflight",
        "tag": tag,
        "source_commit": source_commit,
        "plugin_version": plugin_version,
        "preflight": {
            "run_id": run["id"],
            "run_attempt": run["run_attempt"],
            "updated_at": run["updated_at"],
        },
    }


def fallback_provenance(
    *, tag: str, source_commit: str, plugin_version: str, reason: str
) -> dict[str, Any]:
    return {
        "schema_version": RELEASE_PROVENANCE_SCHEMA_VERSION,
        "status": "passed",
        "mode": "revalidated-after-missing-preflight",
        "tag": tag,
        "source_commit": source_commit,
        "plugin_version": plugin_version,
        "reason": reason,
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    select = commands.add_parser("select")
    select.add_argument("--workflow-runs", type=Path, required=True)
    select.add_argument("--source-commit", required=True)
    select.add_argument("--default-branch", required=True)
    select.add_argument("--repository", required=True)
    select.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--evidence", type=Path, required=True)
    verify.add_argument("--selection", type=Path, required=True)
    verify.add_argument("--tag", required=True)
    verify.add_argument("--source-commit", required=True)
    verify.add_argument("--changelog", type=Path, required=True)
    verify.add_argument("--output", type=Path, required=True)
    fallback = commands.add_parser("fallback")
    fallback.add_argument("--tag", required=True)
    fallback.add_argument("--source-commit", required=True)
    fallback.add_argument("--plugin-version", required=True)
    fallback.add_argument("--reason", required=True)
    fallback.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "select":
            payload = _read_json(args.workflow_runs, "workflow-runs")
            result = select_run(
                payload,
                source_commit=args.source_commit,
                default_branch=args.default_branch,
                repository=args.repository,
            )
        elif args.command == "verify":
            result = verify_reusable_preflight(
                args.evidence,
                _read_json(args.selection, "la selección de preflight"),
                tag=args.tag,
                source_commit=args.source_commit,
                changelog=args.changelog,
            )
        else:
            result = fallback_provenance(
                tag=args.tag,
                source_commit=args.source_commit,
                plugin_version=args.plugin_version,
                reason=args.reason,
            )
    except PreflightProvenanceError as exc:
        result = {
            "schema_version": RELEASE_PROVENANCE_SCHEMA_VERSION,
            "status": "blocked",
            "error": str(exc),
        }
        _write_json(args.output, result)
        print(json.dumps(result, ensure_ascii=False))
        return 2
    _write_json(args.output, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
