"""Planning continuity for the v2 local-technology contract."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eval_support import (
    V2_CLI,
    authorize_implementation,
    materialize_ready_project,
    run_json,
    update_technology_declaration,
)
from v2_contract import ContractError, load
from v2_lifecycle import current_authorization, planning


class PlanningContinuityV13Tests(unittest.TestCase):
    def test_ready_slice_has_complete_local_planning_and_generic_binding(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-planning-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "planning-ready")

            assessment = planning(load(root), ["TASK-001"])
            task = load(root).elements["TASK-001"]

            self.assertEqual(assessment["status"], "ready")
            self.assertEqual(task.targets("bindings"), {"BIND-001"})
            self.assertEqual(load(root).elements["BIND-001"].kind, "binding")

    def test_unresolved_local_declaration_blocks_only_the_affected_slice(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-planning-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "planning-unresolved")
            update_technology_declaration(
                root, value="Technology awaiting confirmation", state="unknown"
            )

            assessment = planning(load(root), ["TASK-001"])

            self.assertEqual(assessment["status"], "blocked")
            self.assertTrue(
                any("TECH-001" in blocker for blocker in assessment["blockers"])
            )

    def test_declaration_change_stales_authorization_without_mutating_history(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-planning-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "planning-stale-auth")
            authorize_implementation(root)
            authorization_path = next(
                (root / "docs/lks-sdd/00-control/authorizations").glob("AUTH-*.md")
            )
            before = authorization_path.read_bytes()

            update_technology_declaration(
                root, value="A changed project-local technology decision"
            )

            self.assertEqual(authorization_path.read_bytes(), before)
            with self.assertRaisesRegex(ContractError, "stale"):
                current_authorization(load(root), ["TASK-001"], "test")

    def test_readiness_cli_reports_the_same_local_contract_state(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-planning-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "planning-cli")

            _, result = run_json(
                V2_CLI, "readiness", str(root), "--task", "TASK-001"
            )

            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["selected_tasks"], ["TASK-001"])
            self.assertFalse(
                any("profile" in blocker.casefold() for blocker in result["blockers"])
            )


if __name__ == "__main__":
    unittest.main()
