#!/usr/bin/env python3
"""Run the small, deterministic gate required to publish this plugin."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CORE_TESTS = (
    "test_complex_handoff.ComplexCalculatorHandoffTests."
    "test_calculator_contract_1_5_reaches_the_guarded_handoff_without_execution",
    "test_m3_workflows.M3WorkflowTests."
    "test_inspection_is_read_only_and_never_reproduces_secret_values",
    "test_m3_workflows.M3WorkflowTests."
    "test_dirty_repository_can_be_materialized_without_touching_existing_files",
    "test_workflows.WorkflowTests.test_projects_are_isolated",
    "test_definition_experience.DefinitionExperienceTests."
    "test_unsupported_project_schema_is_rejected_without_mutation",
    "test_task_management_v12.TaskManagementV12Tests."
    "test_professional_transition_flow_records_blocker_and_done_evidence",
    "test_m3_workflows.M3WorkflowTests."
    "test_v2_migration_is_explicit_without_changing_the_legacy_initializer",
    "test_multi_profile_delivery.MultiProfileDeliveryTests."
    "test_active_profiles_with_structural_locks_are_supported",
    "test_planning_continuity_v13.PlanningContinuityV13Tests."
    "test_scope_change_stales_planning_and_authorization",
    "test_task_tracking_v14.TaskTrackingV14Tests."
    "test_jira_preview_is_deterministic_and_receipt_makes_it_idempotent",
    "test_task_tracking_v14.TaskTrackingV14Tests."
    "test_credentials_are_rejected_before_persistence",
    "test_validation_evidence_v016.VisualEvidencePolicyV016Tests."
    "test_missing_file_and_wrong_hash_are_rejected",
    "test_integrations_v018.IntegrationTablesV018Tests."
    "test_external_internal_both_and_not_applicable_round_trip",
    "test_variants_adoption_v018.VariantsAdoptionV018Tests."
    "test_adoption_of_both_layouts_preserves_every_consumer_byte",
)


class ReleaseGateError(Exception):
    """Expected release-gate validation failure."""


def _git(arguments: list[str]) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ReleaseGateError(f"Git no pudo validar la fuente: {detail}")
    return completed.stdout.strip()


def _source_binding() -> dict[str, str]:
    if _git(["status", "--porcelain", "--untracked-files=all"]):
        raise ReleaseGateError(
            "El gate de release exige un checkout limpio, incluidos archivos no versionados."
        )
    return {"commit": _git(["rev-parse", "HEAD"]).lower(), "tree_state": "clean"}


def _plugin_version() -> str:
    try:
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseGateError(f"No se puede leer el manifest del plugin: {exc}") from exc
    version = manifest.get("version") if isinstance(manifest, dict) else None
    if not isinstance(version, str) or not version:
        raise ReleaseGateError("El manifest del plugin no declara version.")
    return version


def _approved_release(path: Path, version: str) -> None:
    try:
        approval = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseGateError(f"No se puede leer la aprobación de release: {exc}") from exc
    if not isinstance(approval, dict):
        raise ReleaseGateError("La aprobación de release debe ser un objeto JSON.")
    decision = approval.get("decision")
    if (
        approval.get("release_version") != version
        or approval.get("scope") != "stable-release"
        or not isinstance(decision, dict)
        or decision.get("status") != "approved"
        or decision.get("blocking_findings") != []
    ):
        raise ReleaseGateError(
            "La aprobación de release no acredita esta versión sin bloqueantes."
        )


def _run(
    check_id: str, command: list[str], *, timeout_seconds: int
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=PLUGIN_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        status = "passed" if completed.returncode == 0 else "failed"
        detail = "" if status == "passed" else (completed.stderr or completed.stdout).strip()
    except subprocess.TimeoutExpired:
        status = "failed"
        detail = f"timeout after {timeout_seconds}s"
    return {
        "id": check_id,
        "status": status,
        "duration_seconds": round(time.monotonic() - started, 3),
        "timeout_seconds": timeout_seconds,
        "detail": detail[-2000:],
        "command": command,
        "_stdout": completed.stdout if "completed" in locals() else "",
    }


def _static_integrity() -> dict[str, Any]:
    checks = (
        [sys.executable, "-B", "-X", "utf8", "scripts/validate_fixture_manifest.py", "."],
        [sys.executable, "-B", "-X", "utf8", "scripts/validate_plugin_contract.py", "."],
        [
            sys.executable,
            "-B",
            "-X",
            "utf8",
            "scripts/validate_reference_profile.py",
            "--all",
            "--allow-unvalidated",
        ],
    )
    started = time.monotonic()
    details: list[str] = []
    status = "passed"
    for command in checks:
        result = _run("static-step", command, timeout_seconds=120)
        if result["status"] != "passed":
            status = "failed"
            details.append(result["detail"])
            break
    return {
        "id": "static-integrity",
        "status": status,
        "duration_seconds": round(time.monotonic() - started, 3),
        "timeout_seconds": 360,
        "detail": "\n".join(details),
        "command": "fixture manifest + plugin contract + profile structure",
    }


def _release_core() -> dict[str, Any]:
    command = [
        sys.executable,
        "-B",
        "-X",
        "utf8",
        "tests/run_unit_tests.py",
    ]
    for selector in CORE_TESTS:
        command.extend(["--test", selector])
    result = _run("release-core", command, timeout_seconds=180)
    if result["status"] == "passed":
        try:
            payload = json.loads(result.pop("_stdout"))
        except json.JSONDecodeError:
            result["status"] = "failed"
            result["detail"] = "El núcleo de release no devolvió JSON válido."
        else:
            results = payload.get("results")
            identifiers = {
                item.get("id")
                for item in results
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            } if isinstance(results, list) else set()
            if (
                payload.get("passed") is not True
                or not isinstance(results, list)
                or len(results) != len(CORE_TESTS)
                or identifiers != set(CORE_TESTS)
            ):
                result["status"] = "failed"
                result["detail"] = (
                    "El núcleo de release no ejecutó exactamente sus pruebas declaradas."
                )
    return result


def build_report(
    *, channel: str, evaluated_on: str, approval_path: Path | None
) -> dict[str, Any]:
    try:
        date.fromisoformat(evaluated_on)
    except ValueError as exc:
        raise ReleaseGateError("--date debe usar YYYY-MM-DD.") from exc
    source = _source_binding()
    version = _plugin_version()
    checks: list[dict[str, Any]] = []
    if channel == "stable":
        if approval_path is None:
            raise ReleaseGateError("Stable exige --release-approval.")
        _approved_release(approval_path, version)
        checks.append(
            {
                "id": "release-approval",
                "status": "passed",
                "duration_seconds": 0.0,
                "timeout_seconds": None,
                "detail": "",
                "command": str(approval_path),
            }
        )
    checks.extend(
        [
            _static_integrity(),
            _release_core(),
        ]
    )
    if channel == "stable":
        checks.append(
            _run(
                "windows-long-path-regression",
                [
                    sys.executable,
                    "-B",
                    "-X",
                    "utf8",
                    "tests/run_unit_tests.py",
                    "--module",
                    "test_windows_long_paths",
                ],
                timeout_seconds=600,
            )
        )
    for check in checks:
        check.pop("_stdout", None)
    failed = [check["id"] for check in checks if check["status"] != "passed"]
    return {
        "schema_version": "simple-release-gate-1.0",
        "plugin_version": version,
        "evaluated_on": evaluated_on,
        "channel": channel,
        "source": source,
        "checks": checks,
        "gate": {
            "status": "passed" if not failed else "failed",
            "blockers": failed,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=("candidate", "stable"), default="candidate")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--release-approval", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        print(json.dumps({"status": "error", "error": f"Ya existe: {output}"}))
        return 2
    try:
        report = build_report(
            channel=args.channel,
            evaluated_on=args.date,
            approval_path=args.release_approval,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["gate"]["status"] == "passed" else 1
    except ReleaseGateError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
