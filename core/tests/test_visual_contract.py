"""Visual handoff contracts bound to current project-local sources."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eval_support import materialize_ready_project, update_technology_declaration
from v2_authoring import edit_elements
from v2_contract import ContractError, DOCS, canonical, load, make_element, render_document
from v2_storage import apply, preview
from v2_visual import inspect, request


def _add_visual_contract(root: Path) -> None:
    model = load(root)
    path = DOCS + "/03-solution/visual/VIS-001.md"
    visual = make_element(
        "VIS-001",
        "visual",
        "Synthetic visual handoff",
        "A documented visual proposal requires a reviewed, local handoff.",
        state="confirmed",
        nature="decision",
        relations={"uses": ["TECH-001"]},
    )
    manifest = dict(model.manifest)
    manifest["artifacts"] = [
        *manifest["artifacts"],
        {"id": "VIS-001", "path": path},
    ]
    changes = {
        path: render_document("visual", "Visual handoff", [visual]),
        ".lks-sdd/project.json": canonical(manifest) + b"\n",
    }
    plan = preview(root, changes, sources=model.hashes, operation="add-visual-test")
    apply(root, changes, plan, plan["preview_hash"], validator=lambda: load(root).require_valid())


class VisualContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="lks-sdd-visual-")
        self.root = Path(self.temporary.name)
        materialize_ready_project(self.root, "visual-contract")
        _add_visual_contract(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _request(self) -> dict:
        return {
            "from_host": "copilot",
            "to_host": "codex",
            "actor": "visual-reviewer",
            "brief": "Explore the confirmed local visual contract.",
            "visual_ids": ["VIS-001"],
        }

    def test_preview_is_bound_to_local_visual_and_technology_sources(self):
        result = request(load(self.root), self._request())

        self.assertEqual(result["operation"], "request-visual-handoff-v2")
        self.assertTrue(result["id"].startswith("VH-"))
        self.assertEqual(len(result["writes"]), 2)
        self.assertFalse(
            (self.root / ".lks-sdd" / "profiles").exists()
        )

    def test_visual_handoff_rejects_other_generation_routes(self):
        invalid = {**self._request(), "from_host": "external-service"}

        with self.assertRaisesRegex(ContractError, "Copilot to native Codex"):
            request(load(self.root), invalid)

    def test_local_technology_change_invalidates_an_unaccepted_visual_handoff(self):
        requested = request(load(self.root), self._request())
        request(
            load(self.root),
            self._request(),
            authorized_hash=requested["preview_hash"],
        )

        update_technology_declaration(
            self.root, value="Changed local visual implementation technology"
        )

        with self.assertRaisesRegex(ContractError, "sources changed"):
            inspect(load(self.root), requested["id"])


if __name__ == "__main__":
    unittest.main()
