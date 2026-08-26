from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "tests"))

from eval_support import (  # noqa: E402
    IMPLEMENT_SCRIPT,
    authorize_implementation,
    initialize,
    materialize_ready_increment,
    run_json,
)
from task_tracking_engine import assess_tracking  # noqa: E402
from test_task_tracking_v14 import _configure, _manifest, _record  # noqa: E402
from validate_project import validate_project  # noqa: E402


TRACKING_SCRIPT = PLUGIN_ROOT / "scripts" / "manage_task_tracking.py"


def _apply_preview(root: Path, command: str, *arguments: str) -> dict:
    _, preview = run_json(TRACKING_SCRIPT, command, str(root), *arguments)
    _, applied = run_json(
        TRACKING_SCRIPT,
        command,
        str(root),
        *arguments,
        "--apply",
        "--authorize",
        preview["mutation_hash"],
    )
    return applied


def _prepare_started_project(root: Path, project_id: str = "jira-milestones") -> dict:
    initialize(root, project_id)
    materialize_ready_increment(root)
    _configure(
        root,
        "jira-hybrid",
        decision="ADR-001",
        reporting_scope="milestone-reporting",
        coordination_gate="advisory",
    )
    from jira_reporting_engine import build_milestone_preview  # noqa: PLC0415
    from task_tracking_engine import build_projection_preview  # noqa: PLC0415

    projection = build_projection_preview(root, _manifest(root), ["TASK-001"])
    _record(
        root,
        projection,
        result="succeeded",
        external_id="10001",
        external_key="SYN-1",
    )
    authorize_implementation(root)
    _, preview = run_json(
        IMPLEMENT_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "--task",
        "TASK-001",
        "--dry-run",
    )
    _, implementation = run_json(
        IMPLEMENT_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "--task",
        "TASK-001",
        "--apply",
        "--authorize",
        "--preview-hash",
        preview["preview_hash"],
    )
    assert implementation["execution_id"] == "EXEC-001"
    # Import exercised explicitly above so the test fails at setup if the offline
    # reporting module cannot be loaded alongside the established tracking engine.
    assert build_milestone_preview
    return implementation


def _event_preview(root: Path, *extra: str) -> dict:
    _, preview = run_json(
        TRACKING_SCRIPT,
        "preview-event",
        str(root),
        "--task",
        "TASK-001",
        "--source-ref",
        "EXEC-001",
        "--event-kind",
        "started",
        *extra,
    )
    return preview


def _authorize_event(root: Path, preview: dict, *extra: str) -> dict:
    _, result = run_json(
        TRACKING_SCRIPT,
        "authorize-event",
        str(root),
        "--task",
        "TASK-001",
        "--source-ref",
        "EXEC-001",
        "--event-kind",
        "started",
        *extra,
        "--preview-hash",
        preview["preview_hash"],
        "--authorized-by-role",
        "synthetic-release-owner",
        "--authorized-on",
        "2026-08-26",
        "--comment-check",
        "no-match",
        "--apply",
    )
    return result


class JiraMilestoneReportingV15Tests(unittest.TestCase):
    def test_repository_only_remains_complete_and_never_requests_jira(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "local-product")
            materialize_ready_increment(root)
            _configure(root, "repository-only", decision="ADR-001")
            report, _, _ = validate_project(root)
            self.assertTrue(report.valid, report.errors)
            tracking = assess_tracking(root, _manifest(root))
            self.assertEqual(tracking["status"], "not-required")
            code, payload = run_json(
                TRACKING_SCRIPT,
                "preview-event",
                str(root),
                "--task",
                "TASK-001",
                "--source-ref",
                "TASK-001",
                "--event-kind",
                "started",
                expected_codes={2},
            )
            self.assertEqual(code, 2)
            self.assertIn("repository-only", payload["error"])

    def test_comment_event_is_confirmed_once_recorded_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project(root)
            preview = _event_preview(root)
            self.assertEqual(["comment"], [item["action"] for item in preview["operations"]])
            self.assertEqual("write", preview["operations"][0]["disposition"])
            self.assertFalse(preview["external_write_authorized"])

            authorized = _authorize_event(root, preview)
            self.assertEqual(authorized["sync_ids"], ["SYNC-002"])
            operation = authorized["operations"][0]
            _, recorded = run_json(
                TRACKING_SCRIPT,
                "record-event-result",
                str(root),
                "--sync-id",
                operation["sync_id"],
                "--result",
                "succeeded",
                "--external-id",
                operation["external_id"],
                "--external-key",
                operation["external_key"],
                "--observed-event-marker",
                preview["event_marker"],
                "--date",
                "2026-08-26",
                "--apply",
            )
            self.assertEqual(recorded["reporting_status"], "ready")
            repeated = _event_preview(root)
            self.assertEqual("noop", repeated["operations"][0]["disposition"])
            self.assertEqual(_manifest(root)["task_tracking"]["reporting_status"], "ready")
            self.assertTrue(validate_project(root)[0].valid)

    def test_one_confirmation_authorizes_comment_and_exact_transition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project(root, "jira-workflow")
            _apply_preview(
                root,
                "configure-workflow",
                "--local-state",
                "in-progress",
                "--jira-status-id",
                "3",
                "--jira-status-name",
                "In Progress",
                "--decision",
                "ADR-901",
                "--date",
                "2026-08-26",
            )
            preview = _event_preview(
                root, "--observed-status-id", "1", "--transition-id", "21"
            )
            self.assertEqual(
                ["comment", "transition"],
                [item["action"] for item in preview["operations"]],
            )
            authorized = _authorize_event(
                root, preview, "--observed-status-id", "1", "--transition-id", "21"
            )
            self.assertEqual(authorized["sync_ids"], ["SYNC-002", "SYNC-003"])
            self.assertTrue(authorized["external_write_authorized"])
            self.assertEqual(
                "3", authorized["operations"][1]["payload"]["target_status_id"]
            )

    def test_uncertain_comment_requires_append_only_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project(root, "jira-reconcile")
            preview = _event_preview(root)
            authorized = _authorize_event(root, preview)
            _, uncertain = run_json(
                TRACKING_SCRIPT,
                "record-event-result",
                str(root),
                "--sync-id",
                authorized["sync_ids"][0],
                "--result",
                "uncertain",
                "--date",
                "2026-08-26",
                "--apply",
            )
            self.assertEqual(uncertain["reporting_status"], "reconciliation-required")
            self.assertEqual(
                "reconciliation-required",
                _event_preview(root)["operations"][0]["disposition"],
            )
            _, reconciled = run_json(
                TRACKING_SCRIPT,
                "reconcile-event",
                str(root),
                "--anchor-sync-id",
                authorized["sync_ids"][0],
                "--result",
                "succeeded",
                "--authorized-by-role",
                "synthetic-release-owner",
                "--authorized-on",
                "2026-08-26",
                "--observed-event-marker",
                preview["event_marker"],
                "--date",
                "2026-08-26",
                "--apply",
            )
            self.assertEqual(reconciled["sync_id"], "SYNC-003")
            self.assertEqual(reconciled["reporting_status"], "ready")
            ledger = (root / "docs/lks-sdd/04-delivery/task-tracking.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("reconciles=SYNC-002", ledger)
            self.assertTrue(validate_project(root)[0].valid)


if __name__ == "__main__":
    unittest.main()
