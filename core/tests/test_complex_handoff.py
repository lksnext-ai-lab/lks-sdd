"""Cross-host visual handoffs use local v2 sources and explicit cancellation."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eval_support import materialize_ready_project, update_technology_declaration
from v2_contract import ContractError, DOCS, canonical, load, make_element, render_document
from v2_storage import apply, preview
from v2_visual import cancel, inspect, request


def _add_handoff_source(root: Path) -> None:
    model = load(root)
    path = DOCS + "/03-solution/visual/VIS-001.md"
    visual = make_element(
        "VIS-001",
        "visual",
        "Handoff source",
        "The local visual contract is reviewed through the documented handoff.",
        state="confirmed",
        nature="decision",
        relations={"uses": ["TECH-001"]},
    )
    index = dict(model.manifest)
    index["artifacts"] = [*index["artifacts"], {"id": "VIS-001", "path": path}]
    changes = {
        path: render_document("visual", "Handoff source", [visual]),
        ".lks-sdd/project.json": canonical(index) + b"\n",
    }
    proposal = preview(root, changes, sources=model.hashes, operation="add-handoff-source")
    apply(root, changes, proposal, proposal["preview_hash"], validator=lambda: load(root).require_valid())


class ComplexCalculatorHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="lks-sdd-handoff-")
        self.root = Path(self.temporary.name)
        materialize_ready_project(self.root, "complex-handoff")
        _add_handoff_source(self.root)
        self.request_data = {
            "from_host": "copilot",
            "to_host": "codex",
            "actor": "handoff-owner",
            "brief": "Review the local visual source before generating alternatives.",
            "visual_ids": ["VIS-001"],
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_handoff_is_preview_bound_and_never_grants_implementation_authority(self):
        proposal = request(load(self.root), self.request_data)
        applied = request(
            load(self.root),
            self.request_data,
            authorized_hash=proposal["preview_hash"],
        )
        state = inspect(load(self.root), proposal["id"])

        self.assertEqual(applied["status"], "applied")
        self.assertEqual(state["status"], "requested")
        self.assertEqual(
            state["request"]["implementation_authorization"], "not-granted"
        )
        self.assertEqual(state["request"]["acceptance"], "not-granted")

    def test_stale_local_technology_can_be_cancelled_but_not_inspected_as_current(self):
        proposal = request(load(self.root), self.request_data)
        request(
            load(self.root),
            self.request_data,
            authorized_hash=proposal["preview_hash"],
        )
        update_technology_declaration(
            self.root, value="Changed technology after handoff request"
        )

        with self.assertRaisesRegex(ContractError, "sources changed"):
            inspect(load(self.root), proposal["id"])

        cancellation = cancel(
            load(self.root),
            proposal["id"],
            {
                "actor": "handoff-owner",
                "recorded_at": "2026-09-19T10:00:00+00:00",
                "reason": "The local source changed before review.",
            },
        )
        cancelled = cancel(
            load(self.root),
            proposal["id"],
            {
                "actor": "handoff-owner",
                "recorded_at": "2026-09-19T10:00:00+00:00",
                "reason": "The local source changed before review.",
            },
            authorized_hash=cancellation["preview_hash"],
        )

        self.assertEqual(cancelled["status"], "applied")
        with self.assertRaisesRegex(ContractError, "cancelled"):
            inspect(load(self.root), proposal["id"])


if __name__ == "__main__":
    unittest.main()
