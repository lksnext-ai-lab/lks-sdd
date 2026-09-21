"""Regression coverage for historical execution records and v2 continuity."""
from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path

from eval_support import V2_CLI, authorize_implementation, materialize_ready_project, run_json
from v2_authoring import catalog, catalog_markdown
from v2_contract import DOCS, ContractError, Element, load, render_document
from v2_controls import correction
from v2_lifecycle import (
    active_execution,
    checkpoint,
    diff_guard,
    is_active_execution,
    record,
    start,
)
from v2_storage import apply, preview
from v2_verification import verification_plan


def _apply(root: Path, changes: dict[str, bytes], operation: str) -> dict:
    model = load(root)
    plan = preview(root, changes, sources=model.hashes, operation=operation)
    return apply(
        root,
        changes,
        plan,
        plan["preview_hash"],
        validator=lambda: load(root).require_valid(),
    )


def _record_execution(
    root: Path, identifier: str, state: str, relations: dict[str, list[str]]
) -> Path:
    model = load(root)
    path, data = record(
        model,
        identifier,
        "execution",
        "Historical execution" if state == "reconciliation-required" else "Execution",
        "Preserved operational record for lifecycle selection tests.",
        state=state,
        relations=relations,
    )
    _apply(root, {path: data}, "record-test-execution")
    return root / path


def _add_second_task(root: Path) -> None:
    model = load(root)
    source = model.elements["TASK-001"]
    meta = dict(source.meta)
    meta.update(
        id="TASK-002",
        uid=str(uuid.uuid4()),
        title="Implement independent acknowledgement",
        revision=1,
        state="ready",
    )
    meta["relations"] = {
        relation: list(targets) for relation, targets in source.relations.items()
    }
    path = DOCS + "/04-delivery/fixture-task-two.md"
    _apply(
        root,
        {
            path: render_document(
                "fixture-task",
                "Independent synthetic task",
                [{"meta": meta, "body": source.body}],
            )
        },
        "add-independent-test-task",
    )


def _start(root: Path, task: str = "TASK-001") -> str:
    authorize_implementation(root, task_ids=(task,))
    first = start(
        load(root),
        [task],
        "test",
        actor="fixture-owner",
        at="2026-09-19T10:00:00+00:00",
    )
    start(
        load(root),
        [task],
        "test",
        actor="fixture-owner",
        at="2026-09-19T10:00:00+00:00",
        authorized_hash=first["preview_hash"],
    )
    return active_execution(load(root), [task]).id


class V2ExecutionReconciliationTests(unittest.TestCase):
    def test_identical_checkpoint_handoff_is_reused(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-checkpoint-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "checkpoint-dedupe")
            _start(root)
            first = checkpoint(
                load(root), tasks=["TASK-001"], state="paused", actor="fixture-owner",
                at="2026-09-19T11:00:00+00:00", summary="Pause at reviewed boundary",
                next_action="Resume after review",
            )
            checkpoint(
                load(root), tasks=["TASK-001"], state="paused", actor="fixture-owner",
                at="2026-09-19T11:00:00+00:00", summary="Pause at reviewed boundary",
                next_action="Resume after review", authorized_hash=first["preview_hash"],
            )
            repeated = checkpoint(
                load(root), tasks=["TASK-001"], state="paused", actor="fixture-owner",
                at="2026-09-19T11:05:00+00:00", summary="Pause at reviewed boundary",
                next_action="Resume after review",
            )
            self.assertEqual(repeated["status"], "reused")
            self.assertEqual(len(load(root).by_kind("checkpoint")), 2)

    def test_only_documented_continuable_states_are_active(self):
        def execution(state: str) -> Element:
            return Element(
                {"id": "EXEC-001", "kind": "execution", "state": state},
                "",
                "fixture.md",
                1,
            )

        for state in ("in-progress", "in-review", "paused", "blocked"):
            self.assertTrue(is_active_execution(execution(state)), state)
        for state in ("reconciliation-required", "completed", "cancelled"):
            self.assertFalse(is_active_execution(execution(state)), state)

    def test_start_ignores_historical_execution_and_preserves_it(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-reconciliation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reconciliation-start")
            historical_path = _record_execution(
                root,
                "EXEC-001",
                "reconciliation-required",
                {"affects": ["TASK-001"]},
            )
            historical_bytes = historical_path.read_bytes()

            current_id = _start(root)
            model = load(root)
            history = model.elements["EXEC-001"]

            self.assertEqual(current_id, "EXEC-002")
            self.assertEqual(active_execution(model, ["TASK-001"]).id, current_id)
            self.assertFalse(is_active_execution(history))
            self.assertEqual(history.targets("implements"), set())
            self.assertEqual(history.targets("affects"), {"TASK-001"})
            self.assertEqual(historical_path.read_bytes(), historical_bytes)

    def test_checkpoint_diff_review_and_resume_honor_the_task_selector(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-reconciliation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reconciliation-task-selector")
            _add_second_task(root)
            current_id = _start(root)
            _record_execution(
                root, "EXEC-003", "in-progress", {"implements": ["TASK-002"]}
            )

            _, checkpoint_preview = run_json(
                V2_CLI,
                "checkpoint",
                str(root),
                "--task",
                "TASK-001",
                "--state",
                "in-review",
                "--actor",
                "fixture-owner",
                "--at",
                "2026-09-19T10:01:00+00:00",
                "--summary",
                "Ready for review.",
                "--next-action",
                "Run declared observers.",
            )
            run_json(
                V2_CLI,
                "checkpoint",
                str(root),
                "--task",
                "TASK-001",
                "--state",
                "in-review",
                "--actor",
                "fixture-owner",
                "--at",
                "2026-09-19T10:01:00+00:00",
                "--summary",
                "Ready for review.",
                "--next-action",
                "Run declared observers.",
                "--apply",
                "--authorize",
                checkpoint_preview["preview_hash"],
            )
            _, guarded = run_json(
                V2_CLI, "diff", str(root), "--task", "TASK-001"
            )
            _, reviewed = run_json(
                V2_CLI,
                "review-diff",
                str(root),
                "--task",
                "TASK-001",
                "--actor",
                "fixture-reviewer",
                "--reason",
                "Reviewed exact bounded diff.",
                "--diff-fingerprint",
                guarded["diff_fingerprint"],
            )
            _, resumed = run_json(
                V2_CLI, "resume", str(root), "--task", "TASK-001"
            )

            model = load(root)
            self.assertEqual(model.elements[current_id].meta["state"], "in-review")
            self.assertEqual(model.elements["EXEC-003"].meta["state"], "in-progress")
            self.assertEqual(guarded["status"], "within-scope")
            self.assertEqual(reviewed["operation"], "review-exact-diff")
            self.assertEqual(resumed["execution"], current_id)

    def test_blocked_execution_remains_active(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-reconciliation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reconciliation-blocked")
            _record_execution(
                root, "EXEC-001", "blocked", {"implements": ["TASK-001"]}
            )

            execution = active_execution(load(root), ["TASK-001"])

            self.assertEqual(execution.id, "EXEC-001")
            self.assertTrue(is_active_execution(execution))

    def test_two_normative_executions_for_one_task_remain_an_error(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-reconciliation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reconciliation-duplicate")
            _record_execution(
                root, "EXEC-001", "in-progress", {"implements": ["TASK-001"]}
            )
            _record_execution(
                root, "EXEC-002", "paused", {"implements": ["TASK-001"]}
            )

            with self.assertRaisesRegex(
                ContractError, "Exactly one active execution"
            ):
                active_execution(load(root), ["TASK-001"])

    def test_active_executions_for_independent_tasks_do_not_interfere(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-reconciliation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reconciliation-independent")
            _add_second_task(root)
            _record_execution(
                root, "EXEC-001", "in-progress", {"implements": ["TASK-001"]}
            )
            _record_execution(
                root, "EXEC-002", "paused", {"implements": ["TASK-002"]}
            )
            model = load(root)

            self.assertEqual(active_execution(model, ["TASK-001"]).id, "EXEC-001")
            self.assertEqual(active_execution(model, ["TASK-002"]).id, "EXEC-002")

    def test_historical_records_remain_visible_and_replan_does_not_rewrite_them(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-reconciliation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reconciliation-history")
            historical_path = _record_execution(
                root,
                "EXEC-001",
                "reconciliation-required",
                {"affects": ["TASK-001"]},
            )
            historical_bytes = historical_path.read_bytes()
            current_id = _start(root)

            plan = correction(
                load(root),
                ["TASK-001"],
                actor="fixture-owner",
                reason="Replan only the current task semantics.",
                at="2026-09-19T10:00:00+00:00",
                replan=True,
            )
            correction(
                load(root),
                ["TASK-001"],
                actor="fixture-owner",
                reason="Replan only the current task semantics.",
                at="2026-09-19T10:00:00+00:00",
                replan=True,
                authorized_hash=plan["preview_hash"],
            )
            result = catalog(load(root))
            _, status = run_json(V2_CLI, "status", str(root))

            self.assertEqual(historical_path.read_bytes(), historical_bytes)
            self.assertEqual(load(root).elements[current_id].meta["state"], "cancelled")
            execution = next(e for e in result["executions"] if e["id"] == "EXEC-001")
            self.assertFalse(execution["active"])
            self.assertEqual(execution["normative_tasks"], [])
            self.assertEqual(execution["historical_antecedents"], ["TASK-001"])
            self.assertIn("EXEC-001", catalog_markdown(load(root)))
            self.assertIn(
                {"id": "EXEC-001", "state": "reconciliation-required", "active": False,
                 "normative_tasks": [], "historical_antecedents": ["TASK-001"]},
                status["executions"],
            )

    def test_historical_execution_cannot_create_verification_or_evidence(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-reconciliation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reconciliation-evidence")
            _record_execution(
                root,
                "EXEC-001",
                "reconciliation-required",
                {"affects": ["TASK-001"]},
            )
            authorize_implementation(root)

            with self.assertRaisesRegex(
                ContractError, "Exactly one active execution"
            ):
                verification_plan(load(root), ["TASK-001"], "test", "development")

            code, accepted = run_json(
                V2_CLI,
                "accept-result",
                str(root),
                "--task",
                "TASK-001",
                "--evidence-id",
                "EVID-001",
                "--actor",
                "fixture-owner",
                "--at",
                "2026-09-19T10:00:00+00:00",
                "--reason",
                "No historical record may be accepted as new evidence.",
                expected_codes={2},
            )

            self.assertEqual(code, 2)
            self.assertEqual(accepted["status"], "blocked")
            self.assertEqual(accepted["writes"], [])
            self.assertFalse((root / DOCS / "evidence" / "EVID-001.json").exists())

    def test_verification_and_closure_still_require_gates_and_evidence(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-reconciliation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reconciliation-controls")
            _record_execution(
                root,
                "EXEC-001",
                "reconciliation-required",
                {"affects": ["TASK-001"]},
            )
            _start(root)
            checkpoint_preview = checkpoint(
                load(root),
                tasks=["TASK-001"],
                state="in-review",
                actor="fixture-owner",
                at="2026-09-19T10:01:00+00:00",
                summary="Ready for verification.",
                next_action="Run declared observers.",
            )
            checkpoint(
                load(root),
                tasks=["TASK-001"],
                state="in-review",
                actor="fixture-owner",
                at="2026-09-19T10:01:00+00:00",
                summary="Ready for verification.",
                next_action="Run declared observers.",
                authorized_hash=checkpoint_preview["preview_hash"],
            )

            code, verified = run_json(
                V2_CLI,
                "verify",
                str(root),
                "--task",
                "TASK-001",
                "--environment",
                "test",
                "--evidence-id",
                "EVID-001",
                expected_codes={2},
            )
            code_close, closed = run_json(
                V2_CLI,
                "close",
                str(root),
                "--task",
                "TASK-001",
                "--evidence-id",
                "EVID-001",
                "--actor",
                "fixture-reviewer",
                "--at",
                "2026-09-19T10:02:00+00:00",
                expected_codes={2},
            )

            self.assertEqual(code, 2)
            self.assertEqual(verified["status"], "blocked")
            self.assertIn("GATE-UNIT", verified["missing_critical_gates"])
            self.assertEqual(verified["writes"], [])
            self.assertEqual(code_close, 2)
            self.assertEqual(closed["status"], "blocked")
            self.assertEqual(closed["writes"], [])
            self.assertEqual(load(root).elements["TASK-001"].meta["state"], "in-review")

    def test_non_migrated_v2_project_uses_the_same_active_execution_rules(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-reconciliation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reconciliation-new-project")
            execution_id = _start(root)

            self.assertEqual(
                diff_guard(load(root), tasks=["TASK-001"])["status"],
                "within-scope",
            )
            self.assertEqual(active_execution(load(root), ["TASK-001"]).id, execution_id)


if __name__ == "__main__":
    unittest.main()
