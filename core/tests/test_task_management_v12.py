from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eval_support import (
    V2_CLI,
    authorize_implementation,
    materialize_ready_project,
    run_json,
)
from v2_contract import load
from v2_lifecycle import current_authorization


class TaskManagementV12Tests(unittest.TestCase):
    def test_generic_fixture_is_ready_without_a_profile_or_catalog(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-v2-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "task-ready")

            _, readiness = run_json(
                V2_CLI, "readiness", str(root), "--task", "TASK-001"
            )
            fixture = (
                root / "docs/lks-sdd/04-delivery/fixture-task.md"
            ).read_text(encoding="utf-8")

            self.assertEqual(readiness["status"], "ready")
            self.assertIn('"kind":"binding"', fixture)
            self.assertNotIn("profile", fixture.lower())
            self.assertNotIn("catalog", fixture.lower())

    def test_authorization_is_preview_bound_and_scoped_to_the_task(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-v2-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "task-authorization")

            authorization = authorize_implementation(root)
            status = current_authorization(
                load(root), ["TASK-001"], "test"
            )

            self.assertEqual(authorization["status"], "applied")
            self.assertEqual(status["status"], "authorized")
            self.assertEqual(status["scope"], ["TASK-001"])

    def test_preparation_does_not_create_technology_scaffolding(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-v2-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "task-preparation")
            authorize_implementation(root)

            _, preview = run_json(
                V2_CLI,
                "prepare",
                str(root),
                "--task",
                "TASK-001",
                "--environment",
                "test",
            )

            self.assertEqual(preview["status"], "preview")
            self.assertEqual(preview["operation"], "prepare-local-records")
            self.assertEqual(preview["writes"], [])


if __name__ == "__main__":
    unittest.main()
