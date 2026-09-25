"""v2 task-tracking receipts remain local and declaration-based."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eval_support import materialize_ready_project
from v2_authoring import edit_elements
from v2_contract import ContractError, DOCS, canonical, load, make_element, render_document
from v2_storage import apply, preview
from v2_tracking import authorize_projection, policy, projection, readiness


def _add_tracking_policy(root: Path) -> None:
    model = load(root)
    path = DOCS + "/00-control/tracking/ADR-002.md"
    decision = make_element(
        "ADR-002",
        "decision",
        "Synthetic task tracking policy",
        "Tracking is a local governance decision. Remote operations require a separate receipt.",
        state="confirmed",
        nature="decision",
        category="tracking",
        mode="repository-only",
    )
    index = dict(model.manifest)
    index["artifacts"] = [*index["artifacts"], {"id": "ADR-002", "path": path}]
    changes = {
        path: render_document("decision", "Task tracking", [decision]),
        ".lks-sdd/project.json": canonical(index) + b"\n",
    }
    proposal = preview(root, changes, sources=model.hashes, operation="add-tracking-policy")
    apply(root, changes, proposal, proposal["preview_hash"], validator=lambda: load(root).require_valid())


def _set_jira_policy(root: Path) -> None:
    model = load(root)
    decision = model.elements["ADR-002"]
    replacement = dict(
        decision.meta,
        revision=decision.meta["revision"] + 1,
        mode="jira-hybrid",
        site="https://jira.example.invalid",
        project_key="SYN",
        reporting_scope="projection-only",
        coordination_gate="required-before-execution",
    )
    changes = edit_elements(model, {decision.id: replacement})
    proposal = preview(root, changes, sources=model.hashes, operation="configure-test-jira-policy")
    apply(root, changes, proposal, proposal["preview_hash"], validator=lambda: load(root).require_valid())


class TaskTrackingV14Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="lks-sdd-tracking-")
        self.root = Path(self.temporary.name)
        materialize_ready_project(self.root, "tracking-v2")
        _add_tracking_policy(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_repository_only_tracking_requires_no_remote_access(self):
        assessment = readiness(load(self.root), ["TASK-001"])

        self.assertEqual(policy(load(self.root))["mode"], "repository-only")
        self.assertEqual(assessment["status"], "local")
        self.assertEqual(assessment["remote_access"], "not-required")

    def test_projection_uses_canonical_task_identity_and_generic_binding(self):
        value = projection(load(self.root), "TASK-001")
        task = load(self.root).elements["TASK-001"]

        self.assertIn("TASK-001", value["marker"])
        self.assertIn("tracking-v2", value["marker"])
        self.assertEqual(task.targets("bindings"), {"BIND-001"})
        self.assertNotIn("profile", str(value).casefold())

    def test_repository_only_policy_cannot_authorize_a_remote_operation(self):
        with self.assertRaisesRegex(ContractError, "Repository-only"):
            authorize_projection(
                load(self.root),
                "TASK-001",
                actor="tracking-owner",
                at="2026-09-19T10:00:00+00:00",
                duplicate_check="no-match",
            )

    def test_jira_projection_requires_reconciliation_before_execution(self):
        _set_jira_policy(self.root)

        assessment = readiness(load(self.root), ["TASK-001"])

        self.assertEqual(assessment["status"], "blocked")
        self.assertIn("TASK-001", assessment["blockers"][0])
        self.assertEqual(assessment["remote_access"], "not-performed")

    def test_jira_projection_preview_never_performs_a_network_write(self):
        _set_jira_policy(self.root)

        preview_result = authorize_projection(
            load(self.root),
            "TASK-001",
            actor="tracking-owner",
            at="2026-09-19T10:00:00+00:00",
            duplicate_check="no-match",
        )

        self.assertEqual(preview_result["operation"], "authorize-jira-projection")
        self.assertEqual(preview_result["remote_writes"], [])
        self.assertEqual(preview_result["projection"]["marker"].split("; ")[1], "TASK: TASK-001")


if __name__ == "__main__":
    unittest.main()
