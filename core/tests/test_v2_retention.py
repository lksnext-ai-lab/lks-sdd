"""Closed operational records can be inspected, archived and restored explicitly."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from eval_support import authorize_implementation, materialize_ready_project
from v2_authoring import edit_elements
from v2_contract import load
from v2_retention import compact, report, restore
from v2_storage import apply, preview


class V2RetentionTests(unittest.TestCase):
    def test_report_preserves_active_authorization(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-retention-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "retention-active")
            authorize_implementation(root)
            value = report(load(root))
            self.assertEqual(value["candidate_count"], 0)
            self.assertIn("TASK-001", value["active"]["tasks"])
            self.assertEqual(value["preserved"][0], "normative Markdown")

    def test_closed_records_are_archived_and_restored(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-retention-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "retention-closed")
            authorize_implementation(root)
            model = load(root)
            auth = model.by_kind("authorization")[0]
            task = model.elements["TASK-001"]
            changes = edit_elements(model, {auth.id: dict(auth.meta, state="revoked"),
                                            task.id: dict(task.meta, state="done")})
            plan = preview(root, changes, sources=model.hashes, operation="fixture-revoke")
            apply(root, changes, plan, plan["preview_hash"], validator=lambda: load(root).require_valid())

            model = load(root)
            candidate = report(model)
            self.assertEqual([item["id"] for item in candidate["candidates"]], ["AUTH-001"])
            compact_preview = compact(model, at="2026-01-02T00:00:00+00:00")
            self.assertEqual(compact_preview["archived_records"], ["AUTH-001"])
            compact(model, at="2026-01-02T00:00:00+00:00", authorized_hash=compact_preview["preview_hash"])
            self.assertFalse((root / "docs/lks-sdd/00-control/authorizations/AUTH-001.md").exists())
            self.assertTrue((root / "docs/lks-sdd/00-control/history/operational/authorization/AUTH-001.md").is_file())

            restore_preview = restore(load(root), ["AUTH-001"])
            restore(load(root), ["AUTH-001"], authorized_hash=restore_preview["preview_hash"])
            self.assertTrue((root / "docs/lks-sdd/00-control/authorizations/AUTH-001.md").is_file())
            self.assertFalse((root / "docs/lks-sdd/00-control/history/operational/authorization/AUTH-001.md").exists())


if __name__ == "__main__":
    unittest.main()
