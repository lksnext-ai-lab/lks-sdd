"""Verification evidence remains bound to the local technology declaration."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eval_support import (
    authorize_implementation,
    materialize_ready_project,
    update_technology_declaration,
)
from v2_contract import ContractError, load
from v2_lifecycle import checkpoint, start
from v2_verification import technology_readiness, verification_plan


def _start_review(root: Path) -> None:
    authorize_implementation(root)
    model = load(root)
    preview = start(
        model,
        ["TASK-001"],
        "test",
        actor="fixture-owner",
        at="2026-09-19T10:00:00+00:00",
    )
    start(
        load(root),
        ["TASK-001"],
        "test",
        actor="fixture-owner",
        at="2026-09-19T10:00:00+00:00",
        authorized_hash=preview["preview_hash"],
    )
    preview = checkpoint(
        load(root),
        state="in-review",
        actor="fixture-owner",
        at="2026-09-19T10:01:00+00:00",
        summary="Implementation handoff is ready for verification.",
        next_action="Run declared observers.",
    )
    checkpoint(
        load(root),
        state="in-review",
        actor="fixture-owner",
        at="2026-09-19T10:01:00+00:00",
        summary="Implementation handoff is ready for verification.",
        next_action="Run declared observers.",
        authorized_hash=preview["preview_hash"],
    )


class VisualEvidencePolicyV016Tests(unittest.TestCase):
    def test_documented_local_technology_is_the_verification_precondition(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-evidence-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "evidence-technology")

            readiness = technology_readiness(
                load(root), ["TASK-001"], "test"
            )

            self.assertEqual(readiness["status"], "documented")
            self.assertNotIn("profile", str(readiness).casefold())

    def test_unknown_local_technology_blocks_verification_before_observation(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-evidence-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "evidence-blocked")
            update_technology_declaration(
                root, value="Technology is not confirmed", state="unknown"
            )

            readiness = technology_readiness(
                load(root), ["TASK-001"], "test"
            )

            self.assertEqual(readiness["status"], "blocked")
            self.assertTrue(
                any("TECH-001" in blocker for blocker in readiness["blockers"])
            )

    def test_technology_change_invalidates_the_active_verification_subject(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-evidence-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "evidence-stale")
            _start_review(root)

            before = verification_plan(
                load(root), ["TASK-001"], "test", "development"
            )
            update_technology_declaration(
                root, value="Changed technology after implementation handoff"
            )

            self.assertIn("technology", before["material"])
            with self.assertRaisesRegex(ContractError, "stale"):
                verification_plan(load(root), ["TASK-001"], "test", "development")


if __name__ == "__main__":
    unittest.main()
