"""End-to-end v2 workflow coverage without global technology presets."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from eval_support import (
    V2_CLI,
    authorize_implementation,
    materialize_ready_project,
    run_json,
    tree_digest,
    update_technology_declaration,
)
from v2_contract import ContractError, load
from v2_lifecycle import current_authorization


class WorkflowTests(unittest.TestCase):
    def test_init_preview_is_read_only_and_apply_creates_local_declaration(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-workflow-") as directory:
            root = Path(directory)
            before = tree_digest(root)

            _, preview = run_json(
                V2_CLI,
                "init",
                str(root),
                "--name",
                "Workflow preview",
                "--project-id",
                "workflow-preview",
            )

            self.assertEqual(preview["status"], "preview")
            self.assertEqual(before, tree_digest(root))
            self.assertIn(
                "docs/lks-sdd/03-solution/technology-declaration.md",
                preview["writes"],
            )

            _, applied = run_json(
                V2_CLI,
                "init",
                str(root),
                "--name",
                "Workflow preview",
                "--project-id",
                "workflow-preview",
                "--apply",
                "--authorize",
                preview["preview_hash"],
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )

            self.assertEqual(applied["status"], "applied")
            self.assertNotIn("technology", manifest)

    def test_unknown_local_declaration_blocks_readiness_without_writing(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-workflow-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "workflow-blocked")
            update_technology_declaration(
                root, value="Technology remains undecided", state="unknown"
            )
            before = tree_digest(root)

            _, readiness = run_json(
                V2_CLI,
                "readiness",
                str(root),
                "--task",
                "TASK-001",
                expected_codes={2},
            )

            self.assertEqual(readiness["status"], "blocked")
            self.assertTrue(
                any("TECH-001" in blocker for blocker in readiness["blockers"])
            )
            self.assertEqual(before, tree_digest(root))

    def test_ready_fixture_uses_generic_binding_not_a_profile(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-workflow-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "workflow-ready")

            _, readiness = run_json(
                V2_CLI, "readiness", str(root), "--task", "TASK-001"
            )
            fixture = (
                root / "docs/lks-sdd/04-delivery/fixture-task.md"
            ).read_text(encoding="utf-8")

            self.assertEqual(readiness["status"], "ready")
            self.assertIn('"kind":"binding"', fixture)
            self.assertNotIn("profile", fixture.casefold())
            self.assertFalse((root / ".lks-sdd" / "profiles").exists())

    def test_context_and_catalog_are_read_only(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-workflow-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "workflow-context")
            before = tree_digest(root)

            _, context = run_json(
                V2_CLI, "context", str(root), "--task", "TASK-001"
            )
            _, catalog = run_json(V2_CLI, "catalog", str(root))

            self.assertEqual(context["status"], "sufficient")
            self.assertEqual(catalog["kind"], "derived-catalog")
            self.assertEqual(before, tree_digest(root))

    def test_preparation_never_scaffolds_a_technology_selection(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-workflow-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "workflow-preparation")
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

            self.assertEqual(preview["operation"], "prepare-local-records")
            self.assertEqual(preview["writes"], [])
            self.assertFalse((root / ".lks-sdd" / "profiles").exists())

    def test_local_technology_change_invalidates_task_authorization(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-workflow-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "workflow-stale-technology")
            authorize_implementation(root)

            update_technology_declaration(
                root, value="Changed local technology declaration"
            )

            with self.assertRaisesRegex(ContractError, "stale"):
                current_authorization(load(root), ["TASK-001"], "test")


if __name__ == "__main__":
    unittest.main()
