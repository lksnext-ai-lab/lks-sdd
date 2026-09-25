"""Current v2 project experience without profile-derived identity."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eval_support import (
    V2_CLI,
    materialize_ready_project,
    run_json,
    tree_digest,
    update_technology_declaration,
)


class ProductExperienceV015Tests(unittest.TestCase):
    def test_status_is_compact_and_derived_from_the_local_project_contract(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-experience-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "experience-status")
            before = tree_digest(root)

            _, status = run_json(V2_CLI, "status", str(root))

            self.assertEqual(status["status"], "documented")
            self.assertEqual(status["tasks"][0]["id"], "TASK-001")
            self.assertEqual(status["delivery"], "not-assessed")
            self.assertEqual(status["migration"]["status"], "ready")
            self.assertEqual(before, tree_digest(root))

    def test_context_exposes_the_local_declaration_as_a_traced_source(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-experience-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "experience-context")

            _, context = run_json(
                V2_CLI, "context", str(root), "--task", "TASK-001"
            )

            technology = next(
                item
                for item in context["elements"]
                if item["source"]["id"] == "TECH-001"
            )
            self.assertIn(
                "local-technology-declaration",
                technology["included_because"],
            )
            self.assertNotIn("profile", str(context).casefold())

    def test_catalog_is_derived_and_does_not_become_technology_authority(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-experience-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "experience-catalog")
            before = tree_digest(root)

            _, catalog = run_json(V2_CLI, "catalog", str(root))

            self.assertEqual(catalog["kind"], "derived-catalog")
            self.assertNotIn("profile", str(catalog).casefold())
            self.assertEqual(before, tree_digest(root))

    def test_changed_technology_declaration_changes_the_execution_context(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-experience-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "experience-technology-change")

            _, before = run_json(
                V2_CLI, "context", str(root), "--task", "TASK-001"
            )
            update_technology_declaration(
                root, value="Changed local documented technology"
            )
            _, after = run_json(
                V2_CLI, "context", str(root), "--task", "TASK-001"
            )

            self.assertNotEqual(before["fingerprint"], after["fingerprint"])


if __name__ == "__main__":
    unittest.main()
