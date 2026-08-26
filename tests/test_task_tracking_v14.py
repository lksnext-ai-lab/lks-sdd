from __future__ import annotations

import ast
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
    PLANNING_SCRIPT,
    _append_row,
    _replace_row,
    authorize_implementation,
    confirm_planning,
    confirm_planning_change,
    initialize,
    materialize_ready_increment,
    run_json,
)
from planning_engine import assess_planning  # noqa: E402
from manage_task_tracking import _aggregate_sync_state  # noqa: E402
from task_tracking_engine import (  # noqa: E402
    BINDING_HEADERS,
    MAPPING_HEADERS,
    OPERATION_HEADERS,
    TrackingContractError,
    TrackingPlanningBlocked,
    assess_tracking,
    build_projection_preview,
    validate_tracking_contract,
)
from validate_project import validate_project  # noqa: E402
from validate_plugin_contract import _forbidden_runtime_imports  # noqa: E402


TRACKING_SCRIPT = PLUGIN_ROOT / "scripts" / "manage_task_tracking.py"
TASKS_SCRIPT = PLUGIN_ROOT / "scripts" / "manage_tasks.py"
READINESS_SCRIPT = (
    PLUGIN_ROOT
    / "skills"
    / "lks-sdd-assess-readiness"
    / "scripts"
    / "assess_readiness.py"
)


def _manifest(root: Path) -> dict:
    return json.loads(
        (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
    )


def _ensure_decision(
    root: Path, decision: str = "ADR-900", mode: str = "repository-only"
) -> None:
    solution = root / "docs/lks-sdd/03-solution/solution-overview.md"
    if f"| {decision} |" not in solution.read_text(encoding="utf-8"):
        _append_row(
            solution,
            "| ID | State | Decision | Requirements | Impact |",
            f"| {decision} | confirmed | Select {mode} task tracking mode |  | Task tracking governance |",
        )


def _configure(
    root: Path,
    mode: str,
    *,
    decision: str = "ADR-900",
    reporting_scope: str = "projection-only",
    coordination_gate: str = "required-before-execution",
) -> dict:
    if decision in {"ADR-001", "ADR-002"}:
        decision = "ADR-901" if mode == "jira-hybrid" else "ADR-900"
    _ensure_decision(root, decision, mode)
    arguments = [
        "configure",
        str(root),
        "--mode",
        mode,
        "--decision",
        decision,
        "--date",
        "2026-08-25",
    ]
    if mode == "jira-hybrid":
        arguments.extend(
            [
                "--site",
                "https://jira.example.invalid",
                "--project",
                "SYN",
                "--issue-type",
                "Synthetic Work Item",
                "--reporting-scope",
                reporting_scope,
                "--coordination-gate",
                coordination_gate,
            ]
        )
    _, preview = run_json(TRACKING_SCRIPT, *arguments)
    _, applied = run_json(
        TRACKING_SCRIPT,
        *arguments,
        "--apply",
        "--authorize",
        preview["mutation_hash"],
    )
    return applied


def _record(
    root: Path,
    preview: dict,
    *,
    result: str,
    external_id: str | None = None,
    external_key: str | None = None,
    remote_status: str = "To Do",
    change_date: str = "2026-08-25",
) -> dict:
    task_id = preview["operations"][0]["task_id"]
    authorized = _authorize(root, preview, task=task_id)
    arguments = [
        "record-result",
        str(root),
        "--sync-id",
        authorized["sync_id"],
        "--result",
        result,
        "--remote-status",
        remote_status,
        "--observed-projection-fingerprint",
        preview["operations"][0]["payload"]["projection_fingerprint"],
        "--observed-correlation-marker",
        preview["operations"][0]["correlation_marker"],
        "--date",
        change_date,
        "--apply",
    ]
    if external_id:
        arguments.extend(["--external-id", external_id])
    if external_key:
        arguments.extend(["--external-key", external_key])
    if external_key:
        arguments.extend(
            [
                "--url",
                f"https://jira.example.invalid/browse/{external_key}",
            ]
        )
    _, payload = run_json(TRACKING_SCRIPT, *arguments)
    return payload


def _authorize(root: Path, preview: dict, *, task: str = "TASK-001") -> dict:
    action = preview["operations"][0]["action"]
    _, payload = run_json(
        TRACKING_SCRIPT,
        "authorize-sync",
        str(root),
        "--task",
        task,
        "--preview-hash",
        preview["preview_hash"],
        "--authorized-by-role",
        "synthetic-release-owner",
        "--authorized-on",
        "2026-08-25",
        "--duplicate-check",
        "no-match" if action == "create" else "matched",
        "--apply",
    )
    return payload


def _reconcile(
    root: Path,
    preview: dict,
    *,
    result: str,
    external_id: str | None = None,
    external_key: str | None = None,
) -> dict:
    contract = validate_tracking_contract(root, _manifest(root))
    task_id = preview["operations"][0]["task_id"]
    anchor_sync_id = contract["mappings"][task_id]["Last operation"]
    arguments = [
        "reconcile-result",
        str(root),
        "--task",
        task_id,
        "--anchor-sync-id",
        anchor_sync_id,
        "--result",
        result,
        "--authorized-by-role",
        "synthetic-release-owner",
        "--authorized-on",
        "2026-08-25",
        "--date",
        "2026-08-25",
        "--remote-status",
        "To Do",
        "--apply",
    ]
    if result == "succeeded":
        arguments.extend(
            [
                "--observed-projection-fingerprint",
                preview["operations"][0]["payload"]["projection_fingerprint"],
                "--observed-correlation-marker",
                preview["operations"][0]["correlation_marker"],
            ]
        )
    if external_id:
        arguments.extend(["--external-id", external_id])
    if external_key:
        arguments.extend(
            [
                "--external-key",
                external_key,
                "--url",
                f"https://jira.example.invalid/browse/{external_key}",
            ]
        )
    _, payload = run_json(TRACKING_SCRIPT, *arguments)
    return payload


def _confirm_plan(root: Path) -> dict:
    return confirm_planning(root, change_date="2026-08-25")


class TaskTrackingV14Tests(unittest.TestCase):
    def test_aggregate_index_stays_pending_until_every_task_is_synced(self) -> None:
        operations = [
            {
                "task_id": "TASK-001",
                "action": "create",
                "payload": {"projection_fingerprint": "a" * 64},
            },
            {
                "task_id": "TASK-002",
                "action": "create",
                "payload": {"projection_fingerprint": "b" * 64},
            },
        ]
        status, fingerprint = _aggregate_sync_state(
            operations, "TASK-001", "succeeded"
        )
        self.assertEqual(status, "pending")
        self.assertIsNone(fingerprint)

        operations[1]["action"] = "noop"
        status, fingerprint = _aggregate_sync_state(
            operations, "TASK-001", "succeeded"
        )
        self.assertEqual(status, "in-sync")
        self.assertRegex(fingerprint or "", r"^[a-f0-9]{64}$")

        operations[1]["action"] = "blocked-reconciliation"
        status, fingerprint = _aggregate_sync_state(
            operations, "TASK-001", "failed"
        )
        self.assertEqual(status, "reconciliation-required")
        self.assertIsNone(fingerprint)

    def test_project_index_waits_for_every_projectable_task(self) -> None:
        from test_planning_continuity_v13 import (
            _materialize_parallel_complete_plan,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _materialize_parallel_complete_plan(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                preview,
                result="succeeded",
                external_id="10090",
                external_key="SYN-90",
            )
            manifest = _manifest(root)
            self.assertEqual(manifest["task_tracking"]["sync_status"], "pending")
            self.assertIsNone(
                manifest["task_tracking"]["projection_fingerprint"]
            )

    def test_project_index_keeps_other_task_drift_visible(self) -> None:
        from test_planning_continuity_v13 import (
            _materialize_parallel_complete_plan,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _materialize_parallel_complete_plan(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            for task_id, external_id, external_key in (
                ("TASK-001", "10601", "SYN-601"),
                ("TASK-002", "10602", "SYN-602"),
                ("TASK-003", "10603", "SYN-603"),
            ):
                preview = build_projection_preview(root, _manifest(root), [task_id])
                _record(
                    root,
                    preview,
                    result="succeeded",
                    external_id=external_id,
                    external_key=external_key,
                )
            self.assertEqual(
                _manifest(root)["task_tracking"]["sync_status"], "in-sync"
            )

            first = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            first.write_text(
                first.read_text(encoding="utf-8").replace(
                    "Implement the confirmed acknowledgement behavior",
                    "Implement the revised first acknowledgement behavior",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            second = root / "docs/lks-sdd/04-delivery/tasks/TASK-002.md"
            second.write_text(
                second.read_text(encoding="utf-8").replace(
                    "| Implement second request path | Implement second request path and its tests |",
                    "| Implement the revised second request path | Implement second request path and its tests |",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            confirm_planning_change(
                root,
                change_id="PCH-001",
                affected_contract="FR-001, FR-002",
                affected_tasks="TASK-001, TASK-002",
                decision="ADR-002",
                reason="Both independently projected task objectives changed.",
                change_date="2026-08-26",
            )
            first_update = build_projection_preview(
                root, _manifest(root), ["TASK-001"]
            )
            second_update = build_projection_preview(
                root, _manifest(root), ["TASK-002"]
            )
            self.assertEqual(first_update["operations"][0]["action"], "update")
            self.assertEqual(second_update["operations"][0]["action"], "update")
            _record(
                root,
                second_update,
                result="succeeded",
                external_id="10602",
                external_key="SYN-602",
                change_date="2026-08-26",
            )
            manifest = _manifest(root)
            self.assertEqual(
                manifest["task_tracking"]["sync_status"], "out-of-sync"
            )
            self.assertIsNone(
                manifest["task_tracking"]["projection_fingerprint"]
            )
            self.assertEqual(
                build_projection_preview(
                    root, manifest, ["TASK-001"]
                )["operations"][0]["action"],
                "update",
            )

    def test_aggregate_never_hides_an_unprojectable_mapped_task(self) -> None:
        from test_planning_continuity_v13 import (
            _materialize_parallel_complete_plan,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _materialize_parallel_complete_plan(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            for task_id, external_id, external_key in (
                ("TASK-001", "10701", "SYN-701"),
                ("TASK-002", "10702", "SYN-702"),
                ("TASK-003", "10703", "SYN-703"),
            ):
                preview = build_projection_preview(root, _manifest(root), [task_id])
                _record(
                    root,
                    preview,
                    result="succeeded",
                    external_id=external_id,
                    external_key=external_key,
                )

            first = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            first.write_text(
                first.read_text(encoding="utf-8").replace(
                    "Implement the confirmed acknowledgement behavior",
                    "Authorization: Bearer synthetic-secret",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            second = root / "docs/lks-sdd/04-delivery/tasks/TASK-002.md"
            second.write_text(
                second.read_text(encoding="utf-8").replace(
                    "| Implement second request path | Implement second request path and its tests |",
                    "| Implement the revised second request path | Implement second request path and its tests |",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            confirm_planning_change(
                root,
                change_id="PCH-001",
                affected_contract="FR-001, FR-002",
                affected_tasks="TASK-001, TASK-002",
                decision="ADR-002",
                reason="Two projected task objectives changed; one is unsafe.",
                change_date="2026-08-26",
            )
            second_update = build_projection_preview(
                root, _manifest(root), ["TASK-002"]
            )
            _record(
                root,
                second_update,
                result="succeeded",
                external_id="10702",
                external_key="SYN-702",
                change_date="2026-08-26",
            )
            manifest = _manifest(root)
            self.assertNotEqual(
                manifest["task_tracking"]["sync_status"], "in-sync"
            )
            self.assertIsNone(
                manifest["task_tracking"]["projection_fingerprint"]
            )
            assessed = assess_tracking(root, manifest)
            self.assertEqual(assessed["status"], "invalid")
            self.assertTrue(
                any("secreto" in item for item in assessed["blockers"])
            )

    def test_aggregate_reports_unmapped_unsafe_task_as_failed(self) -> None:
        from test_planning_continuity_v13 import (
            _materialize_parallel_complete_plan,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _materialize_parallel_complete_plan(root)
            _configure(root, "jira-hybrid", decision="ADR-901")
            unsafe = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            unsafe.write_text(
                unsafe.read_text(encoding="utf-8").replace(
                    "Implement the confirmed acknowledgement behavior",
                    "Authorization: Bearer synthetic-secret",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            confirm_planning_change(
                root,
                change_id="PCH-001",
                affected_contract="FR-001",
                affected_tasks="TASK-001",
                decision="ADR-002",
                reason="One unmapped task became unsafe for an external projection.",
                change_date="2026-08-26",
            )
            safe_preview = build_projection_preview(
                root, _manifest(root), ["TASK-002"]
            )
            _record(
                root,
                safe_preview,
                result="succeeded",
                external_id="15002",
                external_key="SYN-1502",
                change_date="2026-08-26",
            )

            manifest = _manifest(root)
            self.assertEqual(manifest["task_tracking"]["sync_status"], "failed")
            assessed = assess_tracking(root, manifest)
            self.assertEqual(assessed["status"], "invalid")
            self.assertTrue(
                any("secreto" in item for item in assessed["blockers"]),
                assessed["blockers"],
            )

    def test_new_project_requires_mode_choice_without_external_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-choice")
            manifest = _manifest(root)

            self.assertEqual(manifest["schema_version"], "1.5")
            self.assertEqual(manifest["task_tracking"]["mode"], "pending")
            tracking = validate_tracking_contract(root, manifest)
            self.assertEqual(tracking["status"], "decision-required")
            assessed = assess_tracking(root, manifest)
            self.assertEqual(assessed["status"], "decision-required")
            self.assertTrue(assessed["blockers"])

            scripts = (
                (PLUGIN_ROOT / "scripts/task_tracking_engine.py").read_text(
                    encoding="utf-8"
                )
                + (PLUGIN_ROOT / "scripts/manage_task_tracking.py").read_text(
                    encoding="utf-8"
                )
            )
            for forbidden in ("requests.", "httpx.", "urllib.request", "mcp__"):
                self.assertNotIn(forbidden, scripts)

    def test_offline_tracking_allowlist_only_permits_url_parsing(self) -> None:
        relative = "scripts/task_tracking_engine.py"
        self.assertFalse(
            _forbidden_runtime_imports(
                relative, ast.parse("from urllib.parse import urlparse")
            )
        )
        self.assertEqual(
            _forbidden_runtime_imports(
                relative, ast.parse("from urllib.request import urlopen")
            ),
            {"urllib.request"},
        )

    def test_in_sync_index_requires_a_real_aggregate_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-index-invariant")
            _configure(root, "jira-hybrid", decision="ADR-001")
            manifest_path = root / ".lks-sdd/project.json"
            for fingerprint in (None, "a" * 64):
                manifest = _manifest(root)
                manifest["task_tracking"]["sync_status"] = "in-sync"
                manifest["task_tracking"]["projection_fingerprint"] = fingerprint
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                report, _, _ = validate_project(root)
                self.assertFalse(report.valid)
                self.assertTrue(
                    any(
                        "projection_fingerprint" in item
                        or "sin mappings observados" in item
                        for item in report.errors
                    ),
                    report.errors,
                )

    def test_project_index_cannot_hide_synced_ledger_as_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-index-summary")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                preview,
                result="succeeded",
                external_id="13001",
                external_key="SYN-13",
            )
            manifest_path = root / ".lks-sdd/project.json"
            manifest = _manifest(root)
            manifest["task_tracking"].update(
                {
                    "sync_status": "pending",
                    "projection_fingerprint": None,
                    "last_sync_on": "1999-01-01",
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )

            report, _, _ = validate_project(root)
            self.assertFalse(report.valid)
            self.assertTrue(
                any("sync_status no resume" in item for item in report.errors),
                report.errors,
            )
            self.assertTrue(
                any("last_sync_on no resume" in item for item in report.errors),
                report.errors,
            )

    def test_repository_only_is_durable_and_needs_no_jira(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "repository-tracking")
            applied = _configure(root, "repository-only")

            self.assertTrue(applied["applied"])
            manifest = _manifest(root)
            self.assertEqual(manifest["task_tracking"]["mode"], "repository-only")
            assessed = assess_tracking(root, manifest)
            self.assertEqual(assessed["status"], "not-required")
            report, _, _ = validate_project(root)
            self.assertTrue(report.valid, report.errors)

    def test_tracking_status_rejects_corrupt_artifact_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-frontmatter")
            _configure(root, "repository-only")
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            tracking_path.write_text(
                tracking_path.read_text(encoding="utf-8").replace(
                    'schema_version: "1.5"', 'schema_version: "1.3"', 1
                ),
                encoding="utf-8",
                newline="\n",
            )

            assessed = assess_tracking(root, _manifest(root))
            self.assertEqual(assessed["status"], "invalid")
            self.assertTrue(
                any("front matter schema_version" in item for item in assessed["blockers"]),
                assessed["blockers"],
            )

    def test_jira_cloud_project_key_is_validated_before_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-project-key")
            _ensure_decision(root, "ADR-901", "jira-hybrid")
            manifest_path = root / ".lks-sdd/project.json"
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            before = (manifest_path.read_bytes(), tracking_path.read_bytes())

            for invalid_key in ("S", "syn", "SYN-TEST", "SYN_TEST"):
                _, rejected = run_json(
                    TRACKING_SCRIPT,
                    "configure",
                    str(root),
                    "--mode",
                    "jira-hybrid",
                    "--decision",
                    "ADR-901",
                    "--date",
                    "2026-08-25",
                    "--site",
                    "https://jira.example.invalid",
                    "--project",
                    invalid_key,
                    "--issue-type",
                    "Synthetic Work Item",
                    expected_codes={2},
                )
                self.assertIn("clave Jira Cloud", rejected["error"])
                self.assertEqual(
                    before,
                    (manifest_path.read_bytes(), tracking_path.read_bytes()),
                )

    def test_planning_confirmation_is_rejected_while_choice_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "pending-before-plan")
            materialize_ready_increment(root, confirm_plan=False)
            manifest_path = root / ".lks-sdd/project.json"
            manifest = _manifest(root)
            manifest["task_tracking"].update(
                {
                    "state": "proposed",
                    "mode": "pending",
                    "provider": None,
                    "decision": None,
                    "site": None,
                    "project_key": None,
                    "issue_type": None,
                    "sync_policy": "pending",
                    "write_policy": "pending",
                    "projection_fingerprint": None,
                    "sync_status": "decision-required",
                    "last_sync_on": None,
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            _replace_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                "TRK-001",
                "| TRK-001 | proposed | pending | pending | pending | pending | pending | pending | pending | pending | 2026-08-25 |",
            )
            _, payload = run_json(
                PLANNING_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "confirm",
                "--date",
                "2026-08-25",
                "--actor-role",
                "release-owner",
                "--preview",
                expected_codes={2},
            )
            self.assertEqual(payload["status"], "error")
            self.assertIn("repository-only o jira-hybrid", payload["error"])

    def test_migrated_repository_mode_needs_explicit_confirmation_before_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "migrated-tracking-choice")
            materialize_ready_increment(root, confirm_plan=False)
            manifest_path = root / ".lks-sdd/project.json"
            manifest = _manifest(root)
            manifest["task_tracking"].update(
                {
                    "state": "proposed",
                    "mode": "repository-only",
                    "provider": None,
                    "decision": None,
                    "site": None,
                    "project_key": None,
                    "issue_type": None,
                    "sync_policy": "not-required",
                    "write_policy": "local-only",
                    "projection_fingerprint": None,
                    "sync_status": "not-required",
                    "last_sync_on": None,
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            _replace_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                "TRK-001",
                "| TRK-001 | proposed | repository-only | none | not-applicable | not-applicable | not-applicable | not-required | local-only | pending: migration-preserved from schema 1.3 | 2026-08-25 |",
            )
            _replace_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                "RPT-001",
                "| RPT-001 | confirmed | not-applicable | not-required | not-applicable | pending: migration-preserved from schema 1.3 | 2026-08-25 |",
            )
            report, _, _ = validate_project(root)
            self.assertTrue(report.valid, report.errors)
            _, payload = run_json(
                PLANNING_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "confirm",
                "--date",
                "2026-08-25",
                "--actor-role",
                "release-owner",
                "--preview",
                expected_codes={2},
            )
            self.assertIn("confirmar explícitamente", payload["error"])
            self.assertIsNone(_manifest(root)["planning"]["confirmed_on"])

    def test_migrated_repository_mode_blocks_preserved_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "migrated-authorized-tracking-choice")
            materialize_ready_increment(root)
            authorize_implementation(root)

            manifest_path = root / ".lks-sdd/project.json"
            manifest = _manifest(root)
            manifest["task_tracking"].update(
                {
                    "state": "proposed",
                    "mode": "repository-only",
                    "provider": None,
                    "decision": None,
                    "site": None,
                    "project_key": None,
                    "issue_type": None,
                    "sync_policy": "not-required",
                    "write_policy": "local-only",
                    "projection_fingerprint": None,
                    "sync_status": "not-required",
                    "last_sync_on": None,
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            _replace_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                "TRK-001",
                "| TRK-001 | proposed | repository-only | none | not-applicable | not-applicable | not-applicable | not-required | local-only | pending: migration-preserved from schema 1.3 | 2026-08-25 |",
            )
            _replace_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                "RPT-001",
                "| RPT-001 | confirmed | not-applicable | not-required | not-applicable | pending: migration-preserved from schema 1.3 | 2026-08-25 |",
            )

            report, _, _ = validate_project(root)
            self.assertTrue(report.valid, report.errors)
            contract = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(contract["status"], "decision-required")
            assessed = assess_tracking(root, _manifest(root), ["TASK-001"])
            self.assertEqual(assessed["status"], "decision-required")
            self.assertTrue(assessed["blockers"])

            tracked_paths = [
                root / ".lks-sdd/project.json",
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                root / "docs/lks-sdd/04-delivery/tasks.md",
                root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md",
            ]
            before = tuple(path.read_bytes() for path in tracked_paths)
            code, rejected = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-001",
                "--dry-run",
                expected_codes={3},
            )
            self.assertEqual(code, 3)
            self.assertIn("confirmar explícitamente", " ".join(rejected["blockers"]))
            self.assertEqual(before, tuple(path.read_bytes() for path in tracked_paths))

    def test_jira_preview_is_deterministic_and_receipt_makes_it_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-projection")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")

            first = build_projection_preview(root, _manifest(root), ["TASK-001"])
            second = build_projection_preview(root, _manifest(root), ["TASK-001"])
            self.assertEqual(first, second)
            self.assertEqual(first["operations"][0]["action"], "create")
            self.assertEqual(
                first["operations"][0]["correlation_marker"],
                "LKS-SDD-PROJECT: jira-projection; TASK: TASK-001",
            )
            self.assertFalse(first["external_write_authorized"])

            receipt = _record(
                root,
                first,
                result="succeeded",
                external_id="10001",
                external_key="SYN-1",
            )
            self.assertEqual(receipt["mapping_state"], "synced")
            ledger = (
                root / "docs/lks-sdd/04-delivery/task-tracking.md"
            ).read_text(encoding="utf-8")
            self.assertIn("| SYN-1 | 2026-08-25 | succeeded |", ledger)
            self.assertIn("| synthetic-release-owner | 2026-08-25 | 10001 |", ledger)
            self.assertEqual(
                sum(line.startswith("| SYNC-001 |") for line in ledger.splitlines()),
                1,
            )
            after = build_projection_preview(root, _manifest(root), ["TASK-001"])
            self.assertEqual(after["operations"][0]["action"], "noop")
            self.assertEqual(after["operations"][0]["external_id"], "10001")

    def test_correlation_marker_is_namespaced_by_lks_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            container = Path(temporary)
            markers: list[str] = []
            for project_id in ("shared-jira-alpha", "shared-jira-beta"):
                root = container / project_id
                root.mkdir()
                initialize(root, project_id)
                materialize_ready_increment(root)
                _configure(root, "jira-hybrid", decision="ADR-001")
                preview = build_projection_preview(
                    root, _manifest(root), ["TASK-001"]
                )
                marker = preview["operations"][0]["correlation_marker"]
                self.assertEqual(
                    marker,
                    preview["operations"][0]["duplicate_check"]["marker"],
                )
                markers.append(marker)
            self.assertNotEqual(markers[0], markers[1])

    def test_uncertain_create_fails_closed_and_cannot_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-uncertain")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])

            receipt = _record(root, preview, result="uncertain")
            self.assertEqual(receipt["mapping_state"], "reconciliation-required")
            retry = build_projection_preview(root, _manifest(root), ["TASK-001"])
            self.assertEqual(
                retry["operations"][0]["action"], "blocked-reconciliation"
            )
            assessed = assess_tracking(root, _manifest(root), ["TASK-001"])
            self.assertEqual(assessed["status"], "reconciliation-required")

            reconciled = _reconcile(
                root,
                retry,
                result="succeeded",
                external_id="10009",
                external_key="SYN-9",
            )
            self.assertEqual(reconciled["mapping_state"], "synced")
            after = build_projection_preview(
                root, _manifest(root), ["TASK-001"]
            )
            self.assertEqual(after["operations"][0]["action"], "noop")

    def test_conflict_blocks_new_writes_until_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-conflict")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])

            receipt = _record(
                root,
                preview,
                result="conflict",
                external_id="10006",
                external_key="SYN-6",
            )
            self.assertEqual(receipt["mapping_state"], "conflict")
            retry = build_projection_preview(root, _manifest(root), ["TASK-001"])
            self.assertEqual(
                retry["operations"][0]["action"], "blocked-reconciliation"
            )
            assessed = assess_tracking(root, _manifest(root), ["TASK-001"])
            self.assertEqual(assessed["status"], "reconciliation-required")

    def test_failed_update_keeps_last_observed_fingerprint_out_of_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-failed-update")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            initial = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                initial,
                result="succeeded",
                external_id="10300",
                external_key="SYN-300",
            )
            old_fingerprint = initial["operations"][0]["payload"][
                "projection_fingerprint"
            ]
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            detail_path.write_text(
                detail_path.read_text(encoding="utf-8").replace(
                    "Implement the confirmed acknowledgement behavior",
                    "Implement the revised acknowledgement behavior",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            confirm_planning_change(
                root,
                change_id="PCH-001",
                affected_contract="FR-001",
                affected_tasks="TASK-001",
                decision="ADR-002",
                reason="The executable task objective changed after the first Jira projection.",
                change_date="2026-08-25",
            )
            after_confirmation = _manifest(root)["task_tracking"]
            self.assertEqual(after_confirmation["sync_status"], "out-of-sync")
            self.assertIsNone(after_confirmation["projection_fingerprint"])
            update = build_projection_preview(root, _manifest(root), ["TASK-001"])
            self.assertEqual(update["operations"][0]["action"], "update")
            _record(root, update, result="failed", change_date="2026-08-26")

            contract = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(
                contract["mappings"]["TASK-001"]["Projection fingerprint"],
                old_fingerprint,
            )
            self.assertEqual(
                contract["mappings"]["TASK-001"]["Last synced"],
                "2026-08-25",
            )
            retry = build_projection_preview(root, _manifest(root), ["TASK-001"])
            self.assertEqual(retry["operations"][0]["action"], "update")
            self.assertEqual(
                assess_tracking(root, _manifest(root), ["TASK-001"])["status"],
                "out-of-sync",
            )

    def test_reconciliation_after_plan_drift_preserves_remote_fact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-reconcile-drift")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(root, preview, result="uncertain")
            contract = validate_tracking_contract(root, _manifest(root))
            anchor = contract["mappings"]["TASK-001"]["Last operation"]
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            detail_path.write_text(
                detail_path.read_text(encoding="utf-8").replace(
                    "Implement the confirmed acknowledgement behavior",
                    "Implement a later acknowledgement behavior",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            _, reconciled = run_json(
                TRACKING_SCRIPT,
                "reconcile-result",
                str(root),
                "--task",
                "TASK-001",
                "--anchor-sync-id",
                anchor,
                "--result",
                "succeeded",
                "--authorized-by-role",
                "release-owner",
                "--authorized-on",
                "2026-08-25",
                "--external-id",
                "10200",
                "--external-key",
                "SYN-200",
                "--url",
                "https://jira.example.invalid/browse/SYN-200",
                "--observed-correlation-marker",
                preview["operations"][0]["correlation_marker"],
                "--observed-projection-fingerprint",
                preview["operations"][0]["payload"]["projection_fingerprint"],
                "--date",
                "2026-08-25",
                "--apply",
            )
            self.assertEqual(reconciled["mapping_state"], "out-of-sync")
            validation = validate_tracking_contract(root, _manifest(root))
            self.assertFalse(validation["errors"])
            self.assertEqual(
                validation["mappings"]["TASK-001"]["State"], "out-of-sync"
            )

    def test_visible_key_can_change_but_external_id_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-rekey")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            create = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                create,
                result="succeeded",
                external_id="10005",
                external_key="SYN-5",
            )
            observed = build_projection_preview(
                root, _manifest(root), ["TASK-001"]
            )
            self.assertEqual(observed["operations"][0]["action"], "noop")
            _reconcile(
                root,
                observed,
                result="succeeded",
                external_id="10005",
                external_key="SYN-500",
            )
            contract = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(contract["mappings"]["TASK-001"]["External ID"], "10005")
            self.assertEqual(contract["mappings"]["TASK-001"]["External key"], "SYN-500")

            mismatch = build_projection_preview(
                root, _manifest(root), ["TASK-001"]
            )
            _, rejected = run_json(
                TRACKING_SCRIPT,
                "reconcile-result",
                str(root),
                "--task",
                "TASK-001",
                "--anchor-sync-id",
                validate_tracking_contract(root, _manifest(root))["mappings"][
                    "TASK-001"
                ]["Last operation"],
                "--result",
                "succeeded",
                "--authorized-by-role",
                "synthetic-release-owner",
                "--authorized-on",
                "2026-08-25",
                "--external-id",
                "99999",
                "--external-key",
                "SYN-999",
                "--url",
                "https://jira.example.invalid/browse/SYN-999",
                "--observed-projection-fingerprint",
                mismatch["operations"][0]["payload"]["projection_fingerprint"],
                "--observed-correlation-marker",
                mismatch["operations"][0]["correlation_marker"],
                "--date",
                "2026-08-25",
                "--apply",
                expected_codes={2},
            )
            self.assertIn("inmutable", rejected["error"])
            still_bound = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(
                still_bound["mappings"]["TASK-001"]["External ID"], "10005"
            )
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            historical = dict(still_bound["operations"][0])
            historical["External ID"] = "99999"
            _replace_row(
                tracking_path,
                historical["ID"],
                "| "
                + " | ".join(
                    historical[column] for column in OPERATION_HEADERS
                )
                + " |",
            )
            tampered = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(tampered["status"], "invalid")
            self.assertTrue(
                any("identidad inmutable" in item for item in tampered["errors"])
            )

    def test_historical_jira_key_cannot_be_reused_by_another_task(self) -> None:
        from test_planning_continuity_v13 import (
            _materialize_parallel_complete_plan,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _materialize_parallel_complete_plan(root)
            _configure(root, "jira-hybrid", decision="ADR-001")

            first = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                first,
                result="succeeded",
                external_id="10005",
                external_key="SYN-5",
            )
            observed = build_projection_preview(
                root, _manifest(root), ["TASK-001"]
            )
            _reconcile(
                root,
                observed,
                result="succeeded",
                external_id="10005",
                external_key="SYN-500",
            )

            second = build_projection_preview(root, _manifest(root), ["TASK-002"])
            authorized = _authorize(root, second, task="TASK-002")
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            manifest_path = root / ".lks-sdd/project.json"
            before = (manifest_path.read_bytes(), tracking_path.read_bytes())
            _, rejected = run_json(
                TRACKING_SCRIPT,
                "record-result",
                str(root),
                "--sync-id",
                authorized["sync_id"],
                "--result",
                "succeeded",
                "--external-id",
                "10006",
                "--external-key",
                "SYN-5",
                "--url",
                "https://jira.example.invalid/browse/SYN-5",
                "--remote-status",
                "To Do",
                "--observed-projection-fingerprint",
                second["operations"][0]["payload"]["projection_fingerprint"],
                "--observed-correlation-marker",
                second["operations"][0]["correlation_marker"],
                "--date",
                "2026-08-25",
                "--apply",
                expected_codes={2},
            )
            self.assertIn("historial", rejected["error"])
            self.assertEqual(
                before, (manifest_path.read_bytes(), tracking_path.read_bytes())
            )

            contract = validate_tracking_contract(root, _manifest(root))
            pending = dict(
                next(
                    operation
                    for operation in contract["operations"]
                    if operation["ID"] == authorized["sync_id"]
                )
            )
            pending["External ID"] = "10006"
            pending["External key"] = "SYN-5"
            _replace_row(
                tracking_path,
                pending["ID"],
                "| "
                + " | ".join(pending[column] for column in OPERATION_HEADERS)
                + " |",
            )
            tampered = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(tampered["status"], "invalid")
            self.assertTrue(
                any("External key histórica" in item for item in tampered["errors"]),
                tampered["errors"],
            )

    def test_project_key_prefix_change_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-prefix-guard")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            create = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                create,
                result="succeeded",
                external_id="10015",
                external_key="SYN-15",
            )
            contract = validate_tracking_contract(root, _manifest(root))
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            manifest_path = root / ".lks-sdd/project.json"
            before = (manifest_path.read_bytes(), tracking_path.read_bytes())

            _, rejected = run_json(
                TRACKING_SCRIPT,
                "reconcile-result",
                str(root),
                "--task",
                "TASK-001",
                "--anchor-sync-id",
                contract["mappings"]["TASK-001"]["Last operation"],
                "--result",
                "succeeded",
                "--authorized-by-role",
                "synthetic-release-owner",
                "--authorized-on",
                "2026-08-25",
                "--external-id",
                "10015",
                "--external-key",
                "OTHER-15",
                "--url",
                "https://jira.example.invalid/browse/OTHER-15",
                "--observed-projection-fingerprint",
                preview["operations"][0]["payload"]["projection_fingerprint"],
                "--observed-correlation-marker",
                preview["operations"][0]["correlation_marker"],
                "--date",
                "2026-08-25",
                "--apply",
                expected_codes={2},
            )
            self.assertIn("proyecto Jira configurado", rejected["error"])
            self.assertEqual(
                before, (manifest_path.read_bytes(), tracking_path.read_bytes())
            )

    def test_reconciliation_mapping_cannot_rewrite_receipt_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-reconciliation-identity")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                preview,
                result="uncertain",
                external_id="11001",
                external_key="SYN-11",
            )
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            _replace_row(
                tracking_path,
                "TASK-001",
                "| TASK-001 | reconciliation-required | 22002 | SYN-22 | "
                "https://jira.example.invalid/browse/SYN-22 | pending | unknown | "
                "pending | SYNC-001 | tampered mapping |",
            )

            tampered = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(tampered["status"], "invalid")
            self.assertTrue(
                any(
                    "External ID diverge del recibo SYNC-001" in item
                    for item in tampered["errors"]
                ),
                tampered["errors"],
            )

    def test_mapping_cannot_rewind_past_latest_uncertain_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-history-rewind")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                preview,
                result="succeeded",
                external_id="12001",
                external_key="SYN-12",
            )
            initial_contract = validate_tracking_contract(root, _manifest(root))
            initial_mapping = dict(initial_contract["mappings"]["TASK-001"])
            initial_index = dict(_manifest(root)["task_tracking"])

            current = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _reconcile(root, current, result="uncertain")
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            _replace_row(
                tracking_path,
                "TASK-001",
                "| "
                + " | ".join(
                    initial_mapping[column] for column in MAPPING_HEADERS
                )
                + " |",
            )
            manifest_path = root / ".lks-sdd/project.json"
            manifest = _manifest(root)
            manifest["task_tracking"] = initial_index
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )

            tampered = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(tampered["status"], "invalid")
            self.assertTrue(
                any(
                    "no puede rebobinar el historial" in item
                    for item in tampered["errors"]
                ),
                tampered["errors"],
            )

    def test_durable_mapping_blocks_a_silent_jira_target_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-target-guard")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                preview,
                result="succeeded",
                external_id="10007",
                external_key="SYN-7",
            )
            manifest_path = root / ".lks-sdd/project.json"
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            before = (manifest_path.read_bytes(), tracking_path.read_bytes())

            _, rejected = run_json(
                TRACKING_SCRIPT,
                "configure",
                str(root),
                "--mode",
                "jira-hybrid",
                "--decision",
                "ADR-901",
                "--date",
                "2026-08-25",
                "--site",
                "https://jira.example.invalid",
                "--project",
                "OTHER",
                "--issue-type",
                "Synthetic Work Item",
                expected_codes={2},
            )
            self.assertIn("mappings durables", rejected["error"])
            self.assertEqual(
                before, (manifest_path.read_bytes(), tracking_path.read_bytes())
            )

    def test_same_jira_binding_reconfirmation_preserves_sync_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-binding-reconfirm")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-901")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                preview,
                result="succeeded",
                external_id="14001",
                external_key="SYN-14",
            )
            before_index = dict(_manifest(root)["task_tracking"])
            arguments = [
                "configure",
                str(root),
                "--mode",
                "jira-hybrid",
                "--decision",
                "ADR-901",
                "--date",
                "2026-08-26",
                "--site",
                "https://jira.example.invalid",
                "--project",
                "SYN",
                "--issue-type",
                "Synthetic Work Item",
            ]
            _, reconfirm = run_json(TRACKING_SCRIPT, *arguments)
            _, applied = run_json(
                TRACKING_SCRIPT,
                *arguments,
                "--apply",
                "--authorize",
                reconfirm["mutation_hash"],
            )
            self.assertTrue(applied["applied"])
            after_index = _manifest(root)["task_tracking"]
            for field in (
                "projection_fingerprint",
                "sync_status",
                "last_sync_on",
            ):
                self.assertEqual(after_index[field], before_index[field])
            self.assertFalse(
                validate_tracking_contract(root, _manifest(root))["errors"]
            )
    def test_remote_done_does_not_close_the_canonical_task(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-done-boundary")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                preview,
                result="succeeded",
                external_id="10002",
                external_key="SYN-2",
                remote_status="Done",
            )

            tasks = (
                root / "docs/lks-sdd/04-delivery/tasks.md"
            ).read_text(encoding="utf-8")
            detail = (
                root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            ).read_text(encoding="utf-8")
            self.assertIn("| TASK-001 | PLAN-001 |", tasks)
            self.assertIn("| ready | on-track | 0 |", detail)
            self.assertNotIn("| done |", detail)
            self.assertEqual(
                assess_tracking(root, _manifest(root), ["TASK-001"])["status"],
                "in-sync",
            )

    def test_tracker_receipts_do_not_change_planning_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-fingerprint")
            materialize_ready_increment(root)
            before = assess_planning(root, _manifest(root), "INC-001")
            self.assertEqual(before["status"], "complete")
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                preview,
                result="succeeded",
                external_id="10003",
                external_key="SYN-3",
            )
            after = assess_planning(root, _manifest(root), "INC-001")
            self.assertEqual(
                before["planning_fingerprint"], after["planning_fingerprint"]
            )
            self.assertEqual(
                before["specification_fingerprint"],
                after["specification_fingerprint"],
            )

    def test_required_policy_blocks_new_execution_until_selected_task_is_synced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-readiness")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")

            code, readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-001",
                expected_codes={3},
            )
            self.assertEqual(code, 3)
            self.assertEqual(readiness["phase_states"]["task_tracking"], "pending")
            self.assertEqual(readiness["status"], "tracking-sync-required")

            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                preview,
                result="succeeded",
                external_id="10004",
                external_key="SYN-4",
            )
            _, readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-001",
                expected_codes={0},
            )
            self.assertEqual(readiness["phase_states"]["task_tracking"], "in-sync")
            self.assertEqual(readiness["status"], "ready-for-implementation-authorization")

    def test_planning_authorization_cannot_bypass_required_tracking(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-authorization-guard")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-901")
            planning_path = root / "docs/lks-sdd/04-delivery/planning-coverage.md"
            manifest_path = root / ".lks-sdd/project.json"
            before = (planning_path.read_bytes(), manifest_path.read_bytes())
            _, rejected = run_json(
                PLANNING_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "authorize",
                "--authorization-id",
                "AUTH-001",
                "--task",
                "TASK-001",
                "--date",
                "2026-08-25",
                "--actor-role",
                "fixture-authority",
                "--decision",
                "ADR-002",
                "--constraints",
                "Only the selected task is authorized.",
                "--preview",
                expected_codes={2},
            )
            self.assertIn("tracking operativo", rejected["error"])
            self.assertEqual(
                before, (planning_path.read_bytes(), manifest_path.read_bytes())
            )

    def test_ready_transition_cannot_bypass_required_tracking(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-transition-guard")
            materialize_ready_increment(root)
            authorize_implementation(root)
            _, implementation_preview = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-001",
                "--dry-run",
            )
            run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-001",
                "--apply",
                "--authorize",
                "--preview-hash",
                implementation_preview["preview_hash"],
            )
            board_path = root / "docs/lks-sdd/04-delivery/tasks.md"
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            board_path.write_text(
                board_path.read_text(encoding="utf-8").replace(
                    "| in-progress | on-track |",
                    "| ready | on-track |",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            detail_path.write_text(
                detail_path.read_text(encoding="utf-8").replace(
                    "| in-progress | on-track |",
                    "| ready | on-track |",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            manifest_path = root / ".lks-sdd/project.json"
            manifest = _manifest(root)
            manifest["active_task"] = None
            manifest["active_tasks"] = []
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            _configure(root, "jira-hybrid", decision="ADR-901")
            before = (
                board_path.read_bytes(),
                detail_path.read_bytes(),
                manifest_path.read_bytes(),
            )
            _, rejected = run_json(
                TASKS_SCRIPT,
                str(root),
                "transition",
                "--task",
                "TASK-001",
                "--to",
                "in-progress",
                "--reason",
                "Attempt start while Jira projection is pending.",
                "--actor",
                "fixture-authority",
                "--date",
                "2026-08-25",
                "--preview",
                "--json",
                expected_codes={2},
            )
            self.assertIn("política de tracking bloquea", rejected["error"])
            self.assertEqual(
                before,
                (
                    board_path.read_bytes(),
                    detail_path.read_bytes(),
                    manifest_path.read_bytes(),
                ),
            )

    def test_credentials_are_rejected_before_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "jira-secret-guard")
            _ensure_decision(root, "ADR-901", "jira-hybrid")
            before = (root / "docs/lks-sdd/04-delivery/task-tracking.md").read_bytes()
            _, payload = run_json(
                TRACKING_SCRIPT,
                "configure",
                str(root),
                "--mode",
                "jira-hybrid",
                "--decision",
                "ADR-901",
                "--date",
                "2026-08-25",
                "--site",
                "https://user:password@jira.example.invalid",
                "--project",
                "SYN",
                "--issue-type",
                "Task",
                expected_codes={2},
            )
            self.assertEqual(payload["status"], "error")
            self.assertIn("credenciales", payload["error"])
            self.assertEqual(
                before,
                (root / "docs/lks-sdd/04-delivery/task-tracking.md").read_bytes(),
            )

            _, payload = run_json(
                TRACKING_SCRIPT,
                "configure",
                str(root),
                "--mode",
                "jira-hybrid",
                "--decision",
                "ADR-901",
                "--date",
                "2026-08-25",
                "--site",
                "https://user@jira.example.invalid",
                "--project",
                "SYN",
                "--issue-type",
                "Task",
                expected_codes={2},
            )
            self.assertIn("credenciales", payload["error"])
            self.assertEqual(
                before,
                (root / "docs/lks-sdd/04-delivery/task-tracking.md").read_bytes(),
            )

    def test_unknown_or_unconfirmed_tracking_decision_never_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "unknown-tracking-decision")
            manifest_path = root / ".lks-sdd/project.json"
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            before = (manifest_path.read_bytes(), tracking_path.read_bytes())
            _, rejected = run_json(
                TRACKING_SCRIPT,
                "configure",
                str(root),
                "--mode",
                "repository-only",
                "--decision",
                "ADR-999",
                "--date",
                "2026-08-25",
                expected_codes={2},
            )
            self.assertIn("no existe", rejected["error"])
            self.assertEqual(
                before, (manifest_path.read_bytes(), tracking_path.read_bytes())
            )
            _append_row(
                root / "docs/lks-sdd/03-solution/solution-overview.md",
                "| ID | State | Decision | Requirements | Impact |",
                "| ADR-998 | proposed | Consider repository-only tracking |  | Pending review |",
            )
            before = (manifest_path.read_bytes(), tracking_path.read_bytes())
            _, rejected = run_json(
                TRACKING_SCRIPT,
                "configure",
                str(root),
                "--mode",
                "repository-only",
                "--decision",
                "ADR-998",
                "--date",
                "2026-08-25",
                expected_codes={2},
            )
            self.assertIn("debe estar confirmed", rejected["error"])
            self.assertEqual(
                before, (manifest_path.read_bytes(), tracking_path.read_bytes())
            )
            _append_row(
                root / "docs/lks-sdd/03-solution/solution-overview.md",
                "| ID | State | Decision | Requirements | Impact |",
                "| ADR-997 | confirmed | Select API profile for UNIT-001 |  | "
                "Governs BIND-001 |",
            )
            before = (manifest_path.read_bytes(), tracking_path.read_bytes())
            _, rejected = run_json(
                TRACKING_SCRIPT,
                "configure",
                str(root),
                "--mode",
                "jira-hybrid",
                "--decision",
                "ADR-997",
                "--date",
                "2026-08-25",
                "--site",
                "https://jira.example.invalid",
                "--project",
                "SYN",
                "--issue-type",
                "Task",
                expected_codes={2},
            )
            self.assertIn("no documenta explícitamente", rejected["error"])
            self.assertEqual(
                before, (manifest_path.read_bytes(), tracking_path.read_bytes())
            )

    def test_unconfirmed_plan_does_not_make_tracking_contract_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "planning-axis")
            materialize_ready_increment(root, confirm_plan=False)
            _configure(root, "jira-hybrid", decision="ADR-001")
            manifest = _manifest(root)
            assessed = assess_tracking(root, manifest, ["TASK-001"])
            self.assertEqual(assessed["status"], "not-assessed")
            self.assertFalse(assessed["blockers"])
            self.assertTrue(assessed["warnings"])
            with self.assertRaises(TrackingPlanningBlocked):
                build_projection_preview(root, manifest, ["TASK-001"])

    def test_empty_selection_never_expands_to_all_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "empty-tracking-selection")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), [])
            self.assertEqual(preview["operations"], [])
            assessed = assess_tracking(root, _manifest(root), [])
            self.assertEqual(assessed["status"], "not-assessed")

    def test_authorization_persists_intent_and_requires_duplicate_search(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "durable-tracking-intent")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            before = tracking_path.read_bytes()
            _, rejected = run_json(
                TRACKING_SCRIPT,
                "authorize-sync",
                str(root),
                "--task",
                "TASK-001",
                "--preview-hash",
                preview["preview_hash"],
                "--authorized-by-role",
                "release-owner",
                "--authorized-on",
                "2026-08-25",
                "--duplicate-check",
                "matched",
                "--apply",
                expected_codes={2},
            )
            self.assertIn("búsqueda Rovo", rejected["error"])
            self.assertEqual(before, tracking_path.read_bytes())

            authorized = _authorize(root, preview)
            self.assertTrue(authorized["external_write_authorized"])
            contract = validate_tracking_contract(root, _manifest(root))
            receipt = contract["operations"][0]
            self.assertEqual(receipt["State"], "authorized")
            self.assertEqual(receipt["Result"], "pending")
            self.assertEqual(receipt["Duplicate check"], "no-match")
            waiting = build_projection_preview(
                root, _manifest(root), ["TASK-001"]
            )
            self.assertEqual(waiting["operations"][0]["action"], "awaiting-execution")

    def test_result_after_local_drift_closes_receipt_as_out_of_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-drift-recovery")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            authorized = _authorize(root, preview)
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            detail_path.write_text(
                detail_path.read_text(encoding="utf-8").replace(
                    "Implement the confirmed acknowledgement behavior",
                    "Implement the changed acknowledgement behavior",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            _, recorded = run_json(
                TRACKING_SCRIPT,
                "record-result",
                str(root),
                "--sync-id",
                authorized["sync_id"],
                "--result",
                "succeeded",
                "--external-id",
                "10100",
                "--external-key",
                "SYN-100",
                "--url",
                "https://jira.example.invalid/browse/SYN-100",
                "--observed-projection-fingerprint",
                preview["operations"][0]["payload"]["projection_fingerprint"],
                "--observed-correlation-marker",
                preview["operations"][0]["correlation_marker"],
                "--date",
                "2026-08-25",
                "--apply",
            )
            self.assertEqual(recorded["mapping_state"], "out-of-sync")
            contract = validate_tracking_contract(root, _manifest(root))
            self.assertFalse(contract["errors"])
            self.assertEqual(
                contract["mappings"]["TASK-001"]["State"], "out-of-sync"
            )

    def test_observed_fingerprint_and_exact_issue_url_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-untrusted-result")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            authorized = _authorize(root, preview)
            manifest_path = root / ".lks-sdd/project.json"
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            before = (manifest_path.read_bytes(), tracking_path.read_bytes())
            base = [
                "record-result",
                str(root),
                "--sync-id",
                authorized["sync_id"],
                "--result",
                "succeeded",
                "--external-id",
                "10101",
                "--external-key",
                "SYN-1",
                "--date",
                "2026-08-25",
                "--apply",
            ]
            _, rejected = run_json(
                TRACKING_SCRIPT,
                *base,
                "--url",
                "https://jira.example.invalid/browse/SYN-1",
                "--observed-projection-fingerprint",
                "f" * 64,
                "--observed-correlation-marker",
                preview["operations"][0]["correlation_marker"],
                expected_codes={2},
            )
            self.assertIn("huella observada", rejected["error"])
            self.assertEqual(before, (manifest_path.read_bytes(), tracking_path.read_bytes()))

            _, rejected = run_json(
                TRACKING_SCRIPT,
                *base,
                "--url",
                "https://jira.example.invalid/browse/SYN-10",
                "--observed-projection-fingerprint",
                preview["operations"][0]["payload"]["projection_fingerprint"],
                "--observed-correlation-marker",
                preview["operations"][0]["correlation_marker"],
                expected_codes={2},
            )
            self.assertIn("no corresponde", rejected["error"])
            self.assertEqual(before, (manifest_path.read_bytes(), tracking_path.read_bytes()))

    def test_update_success_requires_freshly_observed_identity_and_url(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-update-observation")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            initial = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                initial,
                result="succeeded",
                external_id="10801",
                external_key="SYN-801",
            )
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            detail_path.write_text(
                detail_path.read_text(encoding="utf-8").replace(
                    "Implement the confirmed acknowledgement behavior",
                    "Implement a freshly observed acknowledgement behavior",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            confirm_planning_change(
                root,
                change_id="PCH-001",
                affected_contract="FR-001",
                affected_tasks="TASK-001",
                decision="ADR-002",
                reason="The projected objective changed after the first observation.",
                change_date="2026-08-26",
            )
            update = build_projection_preview(root, _manifest(root), ["TASK-001"])
            authorized = _authorize(root, update)
            manifest_path = root / ".lks-sdd/project.json"
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            before = (manifest_path.read_bytes(), tracking_path.read_bytes())
            _, rejected = run_json(
                TRACKING_SCRIPT,
                "record-result",
                str(root),
                "--sync-id",
                authorized["sync_id"],
                "--result",
                "succeeded",
                "--observed-projection-fingerprint",
                update["operations"][0]["payload"]["projection_fingerprint"],
                "--observed-correlation-marker",
                update["operations"][0]["correlation_marker"],
                "--date",
                "2026-08-26",
                "--apply",
                expected_codes={2},
            )
            self.assertIn("--external-id", rejected["error"])
            self.assertEqual(
                before, (manifest_path.read_bytes(), tracking_path.read_bytes())
            )

    def test_confidential_or_personal_payload_is_not_projected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "confidential-tracking-payload")
            materialize_ready_increment(root, confirm_plan=False)
            _configure(root, "jira-hybrid", decision="ADR-001")
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            detail_path.write_text(
                detail_path.read_text(encoding="utf-8").replace(
                    "classification: internal", "classification: confidential", 1
                ),
                encoding="utf-8",
                newline="\n",
            )
            _confirm_plan(root)
            with self.assertRaisesRegex(TrackingContractError, "classification=confidential"):
                build_projection_preview(root, _manifest(root), ["TASK-001"])

        for invalid_classification in (
            'classification: "RESTRICTED"',
            "classification:",
        ):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                initialize(root, "invalid-classification-payload")
                materialize_ready_increment(root, confirm_plan=False)
                _configure(root, "jira-hybrid", decision="ADR-001")
                detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
                detail_path.write_text(
                    detail_path.read_text(encoding="utf-8").replace(
                        "classification: internal", invalid_classification, 1
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
                _confirm_plan(root)
                with self.assertRaisesRegex(
                    TrackingContractError, "classification externa válida"
                ):
                    build_projection_preview(root, _manifest(root), ["TASK-001"])

        for sensitive_value in (
            "Bearer super-secret-token",
            "Basic synthetic-secret-token",
        ):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                initialize(root, "sensitive-marker-payload")
                materialize_ready_increment(root, confirm_plan=False)
                _configure(root, "jira-hybrid", decision="ADR-001")
                detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
                detail_path.write_text(
                    detail_path.read_text(encoding="utf-8").replace(
                        "Implement the confirmed acknowledgement behavior",
                        sensitive_value,
                        1,
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
                _confirm_plan(root)
                with self.assertRaisesRegex(TrackingContractError, "secreto"):
                    build_projection_preview(root, _manifest(root), ["TASK-001"])

        for replacement, body_suffix in (
            ("owner_classification: internal", "\nclassification: public\n"),
            (
                "classification: internal\nclassification: public",
                "",
            ),
        ):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                initialize(root, "frontmatter-classification-guard")
                materialize_ready_increment(root, confirm_plan=False)
                _configure(root, "jira-hybrid", decision="ADR-001")
                detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
                task_text = detail_path.read_text(encoding="utf-8").replace(
                    "classification: internal", replacement, 1
                )
                detail_path.write_text(
                    task_text + body_suffix,
                    encoding="utf-8",
                    newline="\n",
                )
                _confirm_plan(root)
                with self.assertRaisesRegex(
                    TrackingContractError,
                    "exactamente una classification",
                ):
                    build_projection_preview(root, _manifest(root), ["TASK-001"])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "personal-tracking-payload")
            materialize_ready_increment(root, confirm_plan=False)
            _configure(root, "jira-hybrid", decision="ADR-001")
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            detail_path.write_text(
                detail_path.read_text(encoding="utf-8").replace(
                    "Implement the confirmed acknowledgement behavior",
                    "Contact jane@example.com before implementing acknowledgement",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            _confirm_plan(root)
            with self.assertRaisesRegex(TrackingContractError, "datos personales"):
                build_projection_preview(root, _manifest(root), ["TASK-001"])

    def test_receipt_notes_reject_secrets_and_personal_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-receipt-privacy")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            before = tracking_path.read_bytes()
            for note in ("password: secret-value", "contact jane@example.com"):
                _, rejected = run_json(
                    TRACKING_SCRIPT,
                    "authorize-sync",
                    str(root),
                    "--task",
                    "TASK-001",
                    "--preview-hash",
                    preview["preview_hash"],
                    "--authorized-by-role",
                    "release-owner",
                    "--authorized-on",
                    "2026-08-25",
                    "--duplicate-check",
                    "no-match",
                    "--notes",
                    note,
                    "--apply",
                    expected_codes={2},
                )
                self.assertIn("credenciales o datos personales", rejected["error"])
                self.assertEqual(before, tracking_path.read_bytes())

    def test_markup_and_malformed_jira_identity_never_persist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-markup-guard")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            authorized = _authorize(root, preview)
            manifest_path = root / ".lks-sdd/project.json"
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            before = (manifest_path.read_bytes(), tracking_path.read_bytes())
            common = [
                "record-result",
                str(root),
                "--sync-id",
                authorized["sync_id"],
                "--result",
                "succeeded",
                "--external-id",
                "10500",
                "--external-key",
                "SYN-500",
                "--url",
                "https://jira.example.invalid/browse/SYN-500",
                "--remote-status",
                "To Do",
                "--observed-projection-fingerprint",
                preview["operations"][0]["payload"]["projection_fingerprint"],
                "--observed-correlation-marker",
                preview["operations"][0]["correlation_marker"],
                "--date",
                "2026-08-25",
                "--apply",
            ]
            for flag, safe_value, unsafe_value in (
                ("--external-id", "10500", "<b>10500</b>"),
                ("--external-key", "SYN-500", "SYN-500<img>"),
                ("--remote-status", "To Do", "[To Do](javascript:alert(1))"),
            ):
                arguments = list(common)
                arguments[arguments.index(flag) + 1] = unsafe_value
                _, rejected = run_json(
                    TRACKING_SCRIPT, *arguments, expected_codes={2}
                )
                self.assertIn("markup", rejected["error"])
                self.assertEqual(
                    before, (manifest_path.read_bytes(), tracking_path.read_bytes())
                )

            for flag, malformed in (
                ("--external-id", "jira-id"),
                ("--external-key", "SYN-other"),
                ("--external-key", "SYN-0"),
            ):
                arguments = list(common)
                arguments[arguments.index(flag) + 1] = malformed
                _, rejected = run_json(
                    TRACKING_SCRIPT, *arguments, expected_codes={2}
                )
                self.assertIn("Jira", rejected["error"])
                self.assertEqual(
                    before, (manifest_path.read_bytes(), tracking_path.read_bytes())
                )

            contract = validate_tracking_contract(root, _manifest(root))
            binding = dict(contract["binding"])
            binding["Issue type"] = "contact jane@example.com"
            _replace_row(
                tracking_path,
                binding["Binding"],
                "| " + " | ".join(binding[column] for column in BINDING_HEADERS) + " |",
            )
            mapping = dict(contract["mappings"]["TASK-001"])
            mapping["Remote status"] = "<img src=x>"
            mapping["Notes"] = "contact jane@example.com"
            _replace_row(
                tracking_path,
                "TASK-001",
                "| " + " | ".join(mapping[column] for column in MAPPING_HEADERS) + " |",
            )
            operation = dict(contract["operations"][0])
            operation["Notes"] = "[unsafe](javascript:alert(1)); DNI 12345678Z"
            _replace_row(
                tracking_path,
                authorized["sync_id"],
                "| "
                + " | ".join(operation[column] for column in OPERATION_HEADERS)
                + " |",
            )
            validation = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(validation["status"], "invalid")
            self.assertTrue(
                any("mapping contiene markup" in item for item in validation["errors"])
            )
            self.assertTrue(
                any("recibo contiene markup" in item for item in validation["errors"])
            )
            self.assertTrue(
                any(
                    "binding contiene datos personales" in item
                    for item in validation["errors"]
                )
            )
            self.assertTrue(
                any(
                    "mapping contiene datos personales" in item
                    for item in validation["errors"]
                )
            )
            self.assertTrue(
                any(
                    "recibo contiene datos personales" in item
                    for item in validation["errors"]
                )
            )

    def test_synced_mapping_without_receipt_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-receipt-coherence")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            _append_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                "| Task | State | External ID | External key | URL | Projection fingerprint | Remote status | Last synced | Last operation | Notes |",
                "| TASK-001 | synced | 10102 | SYN-2 | https://jira.example.invalid/browse/SYN-2 | "
                + "a" * 64
                + " | To Do | 2026-08-25 | none | manual |",
            )
            validation = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(validation["status"], "invalid")
            self.assertTrue(
                any("Last operation" in item for item in validation["errors"])
            )

    def test_synced_mapping_requires_observed_url_and_sync_date(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-complete-provenance")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(
                root,
                preview,
                result="succeeded",
                external_id="10510",
                external_key="SYN-510",
            )
            tracking_path = root / "docs/lks-sdd/04-delivery/task-tracking.md"
            contract = validate_tracking_contract(root, _manifest(root))
            mapping = dict(contract["mappings"]["TASK-001"])
            mapping["Last synced"] = "1999-01-01"
            _replace_row(
                tracking_path,
                "TASK-001",
                "| " + " | ".join(mapping[column] for column in MAPPING_HEADERS) + " |",
            )
            validation = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(validation["status"], "invalid")
            self.assertTrue(
                any(
                    "Last synced diverge del último recibo" in item
                    for item in validation["errors"]
                )
            )
            mapping = dict(contract["mappings"]["TASK-001"])
            mapping["URL"] = "pending"
            mapping["Last synced"] = "pending"
            _replace_row(
                tracking_path,
                "TASK-001",
                "| " + " | ".join(mapping[column] for column in MAPPING_HEADERS) + " |",
            )
            validation = validate_tracking_contract(root, _manifest(root))
            self.assertEqual(validation["status"], "invalid")
            self.assertTrue(
                any("URL Jira observada completa" in item for item in validation["errors"])
            )
            self.assertTrue(
                any("Last synced con fecha observada" in item for item in validation["errors"])
            )

    def test_all_external_state_requires_coherent_mapping_and_receipt(self) -> None:
        mapping_header = (
            "| Task | State | External ID | External key | URL | Projection fingerprint | "
            "Remote status | Last synced | Last operation | Notes |"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-out-of-sync-provenance")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            _append_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                mapping_header,
                "| TASK-001 | out-of-sync | 10400 | SYN-400 | https://jira.example.invalid/browse/SYN-400 | "
                + "a" * 64
                + " | To Do | 2026-08-25 | pending | fabricated |",
            )
            validation = validate_tracking_contract(root, _manifest(root))
            self.assertTrue(
                any("out-of-sync exige Last operation" in item for item in validation["errors"])
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-unlinked-provenance")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            _append_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                mapping_header,
                "| TASK-001 | unlinked | 10401 | SYN-401 | https://jira.example.invalid/browse/SYN-401 | pending | unknown | pending | pending | fabricated |",
            )
            validation = validate_tracking_contract(root, _manifest(root))
            self.assertTrue(
                any("unlinked no puede conservar External ID" in item for item in validation["errors"])
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-standalone-receipt")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            _append_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                "| ID | State | Task | Action | Preview hash | Projection fingerprint | Duplicate check | Authorized by role | Authorized on | External ID | External key | Recorded on | Result | Notes |",
                "| SYNC-001 | recorded | TASK-001 | create | "
                + "a" * 64
                + " | "
                + "b" * 64
                + " | no-match | release-owner | 2026-08-25 | 10402 | SYN-402 | 2026-08-25 | succeeded | standalone |",
            )
            validation = validate_tracking_contract(root, _manifest(root))
            self.assertTrue(
                any("no existe Mapping" in item for item in validation["errors"])
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-failed-anchor")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            preview = build_projection_preview(root, _manifest(root), ["TASK-001"])
            _record(root, preview, result="failed")
            _replace_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                "TASK-001",
                "| TASK-001 | out-of-sync | 10403 | SYN-403 | https://jira.example.invalid/browse/SYN-403 | "
                + preview["operations"][0]["payload"]["projection_fingerprint"]
                + " | unknown | pending | SYNC-001 | fabricated from failed receipt |",
            )
            validation = validate_tracking_contract(root, _manifest(root))
            self.assertTrue(
                any("recibo ancla recorded/succeeded" in item for item in validation["errors"])
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "repository-hidden-jira-state")
            _configure(root, "repository-only")
            _append_row(
                root / "docs/lks-sdd/04-delivery/task-tracking.md",
                mapping_header,
                "| TASK-001 | unlinked | pending | pending | pending | pending | pending | pending | pending | hidden |",
            )
            validation = validate_tracking_contract(root, _manifest(root))
            self.assertTrue(
                any("Mapping y Operations vacíos" in item for item in validation["errors"])
            )

    def test_preview_cli_rejects_multiple_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize(root, "tracking-single-preview")
            materialize_ready_increment(root)
            _configure(root, "jira-hybrid", decision="ADR-001")
            _, rejected = run_json(
                TRACKING_SCRIPT,
                "preview-sync",
                str(root),
                "--task",
                "TASK-001",
                "--task",
                "TASK-001",
                expected_codes={2},
            )
            self.assertIn("exactamente un único", rejected["error"])

if __name__ == "__main__":
    unittest.main()
