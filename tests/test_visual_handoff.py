from __future__ import annotations

from argparse import Namespace
import json
from pathlib import Path
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import manage_visual_handoff as handoff
import test_visual_contract as visual_fixture


class VisualHandoffTests(unittest.TestCase):
    def setUp(self):
        self.fixture = visual_fixture.VisualContractTests()
        self.fixture.setUp()
        self.root = self.fixture.root
        self.fixture._materialize_visual_contract(state="proposal")
        self.brief = "docs/lks-sdd/03-solution/visual-briefs/BRIEF-001.md"
        path = self.root / self.brief
        path.parent.mkdir()
        path.write_text("# Synthetic brief\nUX-001, UX-002; FR-001. One primary action, responsive and accessible.\n", encoding="utf-8")
        ux = self.root / "docs/lks-sdd/03-solution/ux-accessibility.md"
        ux.write_text(ux.read_text(encoding="utf-8").replace("synthetic UI brief", self.brief), encoding="utf-8")

    def tearDown(self):
        self.fixture.tearDown()

    def args(self, **updates):
        values = dict(action="prepare", host="copilot", brief=self.brief, increment="INC-001",
                      scope="Synthetic interface proposal", exclude="Implementation", owner_role="synthetic-reviewer",
                      revision="1", input=[], task=None, execution=None, apply=False, authorize=None)
        values.update(updates)
        return Namespace(**values)

    def prepare(self):
        args = self.args()
        preview = handoff.run(self.root, args)
        args.apply, args.authorize = True, preview["preview_hash"]
        return handoff.run(self.root, args)["id"]

    def approve(self):
        ux = self.root / "docs/lks-sdd/03-solution/ux-accessibility.md"
        lines = ux.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines):
            if line.startswith("| VIS-001 |"):
                lines[number] = line.replace("| proposal |", "| confirmed |", 1).replace(
                    "| pending |", "| user-confirmed; role=synthetic-reviewer; date=2026-08-20; ref=ADR-001 |", 1)
        ux.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_codex_native_no_files_no_invitation(self):
        result = handoff.run(self.root, self.args(host="codex"))
        self.assertEqual(result["writes"], [])
        self.assertIsNone(result["invitation"])
        self.assertFalse((self.root / handoff.BASE).exists())

    def test_preview_idempotence_and_request_transfer(self):
        preview = handoff.run(self.root, self.args())
        self.assertFalse((self.root / handoff.BASE).exists())
        request_id = self.prepare()
        self.assertEqual(preview["id"], request_id)
        self.assertEqual(handoff.run(self.root, self.args())["writes"], [])
        with __import__("tempfile").TemporaryDirectory() as temporary:
            clone = Path(temporary) / "clone"
            shutil.copytree(self.root, clone)
            self.assertEqual(handoff.inspect(clone, request_id)["status"], "pending-visual-approval")

    def test_pending_approval_cannot_complete(self):
        request_id = self.prepare()
        with self.assertRaises(ValueError):
            handoff.run(self.root, self.args(action="complete", id=request_id, visual=["VIS-001"]))
        self.assertFalse((self.root / handoff.BASE / request_id / "result.json").exists())

    def test_complete_revalidates_canonical_approval(self):
        request_id = self.prepare()
        self.approve()
        args = self.args(action="complete", id=request_id, visual=["VIS-001"])
        preview = handoff.run(self.root, args)
        args.apply, args.authorize = True, preview["preview_hash"]
        handoff.run(self.root, args)
        self.assertEqual(handoff.inspect(self.root, request_id)["status"], "completed")
        with __import__("tempfile").TemporaryDirectory() as temporary:
            clone = Path(temporary) / "completed clone"
            shutil.copytree(self.root, clone)
            self.assertEqual(handoff.inspect(clone, request_id)["status"], "completed")
        self.assertFalse(any("EXEC" in p.name for p in (self.root / handoff.BASE / request_id).iterdir()))
        ux = self.root / "docs/lks-sdd/03-solution/ux-accessibility.md"
        ux.write_text(ux.read_text().replace("| VIS-001 | confirmed |", "| VIS-001 | proposal |"), encoding="utf-8")
        with self.assertRaises(ValueError):
            handoff.inspect(self.root, request_id)

    def test_source_drift_requires_reconciliation(self):
        request_id = self.prepare()
        (self.root / self.brief).write_text("Changed requirements", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "drift"):
            handoff.inspect(self.root, request_id)

    def test_ux_substantive_change_is_not_hidden_as_output(self):
        request_id = self.prepare()
        ux = self.root / "docs/lks-sdd/03-solution/ux-accessibility.md"
        ux.write_text(ux.read_text().replace("One primary action", "Two primary actions"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "drift"):
            handoff.inspect(self.root, request_id)

    def test_image_reference_change_rejected(self):
        request_id = self.prepare()
        (self.root / "docs/lks-sdd/03-solution/ui-prototypes/VIS-001.png").write_bytes(b"not an image")
        with self.assertRaisesRegex(ValueError, "drift"):
            handoff.inspect(self.root, request_id)

    def test_wrong_project_and_tampered_request_rejected(self):
        request_id = self.prepare()
        path = self.root / handoff.BASE / request_id / "request.json"
        data = json.loads(path.read_text())
        data["project_id"] = "foreign"
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "identity"):
            handoff.inspect(self.root, request_id)

    def test_cancellation_preserves_history_and_requires_revision(self):
        request_id = self.prepare()
        args = self.args(action="cancel", id=request_id, reason="Synthetic cancellation")
        preview = handoff.run(self.root, args)
        args.apply, args.authorize = True, preview["preview_hash"]
        handoff.run(self.root, args)
        self.assertEqual(handoff.inspect(self.root, request_id)["status"], "cancelled")
        with self.assertRaisesRegex(ValueError, "Cancelled"):
            handoff.run(self.root, self.args())
        self.assertNotEqual(handoff.run(self.root, self.args(revision="2"))["id"], request_id)

    def test_input_path_escape_and_missing_reference_rejected(self):
        for path in ("../outside.md", "missing.png"):
            with self.subTest(path=path), self.assertRaises((ValueError, OSError)):
                handoff.run(self.root, self.args(input=[path]))

    def test_unknown_increment_and_task_rejected(self):
        with self.assertRaisesRegex(ValueError, "Increment"):
            handoff.run(self.root, self.args(increment="INC-999"))
        with self.assertRaisesRegex(ValueError, "TASK"):
            handoff.run(self.root, self.args(task="TASK-999"))

    def test_no_index_or_permission_is_inferred_from_status(self):
        before = (self.root / ".lks-sdd/project.json").read_bytes()
        request_id = self.prepare()
        result = handoff.run(self.root, self.args(action="status"))
        self.assertEqual(result["handoffs"][0]["id"], request_id)
        self.assertEqual(before, (self.root / ".lks-sdd/project.json").read_bytes())

    def test_wrong_brief_reference_cannot_close_valid_image(self):
        request_id = self.prepare()
        self.approve()
        ux = self.root / "docs/lks-sdd/03-solution/ux-accessibility.md"
        ux.write_text(ux.read_text().replace(self.brief, "other-brief.md"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "brief"):
            handoff.run(self.root, self.args(action="complete", id=request_id, visual=["VIS-001"]))

    def test_new_decision_rows_are_outputs_but_old_decisions_remain_inputs(self):
        base = b"| ID | State | Decision |\n|---|---|---|\n| ADR-001 | decision | existing |\n"
        extra = base + b"| ADR-002 | decision | visual approval |\n"
        self.assertEqual(handoff.normalize_source(base, "ART-SOLUTION", ["ADR-001"]),
                         handoff.normalize_source(extra, "ART-SOLUTION", ["ADR-001"]))
        self.assertNotEqual(handoff.normalize_source(base, "ART-SOLUTION", ["ADR-001"]),
                            handoff.normalize_source(base.replace(b"existing", b"changed"), "ART-SOLUTION", ["ADR-001"]))

    def test_missing_execution_is_not_invented(self):
        with self.assertRaisesRegex(ValueError, "execution"):
            handoff.run(self.root, self.args(execution="EXEC-999"))


if __name__ == "__main__":
    unittest.main()
