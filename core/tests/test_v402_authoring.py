"""Public authoring with large historical objects, before and after compaction."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
import test_v4_cli_presentation as presentation_fixture
from test_v4_cli_presentation import snapshot
from content_store import LIMIT, object_path, publish_object, read_object, reference
from v2_contract import ContractError, canonical, fingerprint, read_bytes, sha
from v2_storage import PENDING, write_one
from v3_authoring import candidate
from v3_contract import element, load, location, render


class AuthoringLargeSourceTests(unittest.TestCase):
    setUpClass = classmethod(presentation_fixture.MinimalPresentationTests.setUpClass.__func__)
    setUp = presentation_fixture.MinimalPresentationTests.setUp
    invoke = presentation_fixture.MinimalPresentationTests.invoke

    def add_catalog(self, size, label):
        value = {"format": "lks-sdd-migration-inventory/1", "entries": [], "annotation": label}
        raw = canonical(value)
        value["annotation"] += "x" * (size - len(raw))
        raw = canonical(value)
        self.assertEqual(size, len(raw))
        ref = reference(raw)
        publish_object(self.root, object_path(ref), raw)
        item = element("migration", "Synthetic historical catalog " + label,
                       "Preserved synthetic historical evidence, without execution authority.",
                       inventory_ref=ref, source={"snapshot": fingerprint({})})
        item["meta"].update(state="observed", nature="fact")
        write_one(self.root, location(item), render(item, "3.1"))
        return ref

    def revisions(self, state):
        model = load(self.root).require_valid()
        items = [copy.deepcopy(model.get(key).item()) for key in (self.case.task, self.case.plan_id)]
        for item in items:
            item["meta"]["revision"] += 1
            item["meta"]["state"] = state
        return items

    def test_public_author_retirement_before_and_after_compaction(self):
        from store_compaction import preview, apply, recover
        from v3_workflow import state
        self.case.close_proposal(); self.case.create_plan(); self.case.advance("cancel")
        refs = [self.add_catalog(size, str(i)) for i, size in
                enumerate((36_522_291, 5 * 1024 * 1024, 5 * 1024 * 1024 + 1))]
        original = load(self.root).require_valid()
        keys = (self.case.task, self.case.plan_id)
        identities = {key: (original.get(key).digest(), original.get(key).body) for key in keys}
        decisions = {e.uid: e.digest() for e in original.by_kind("decision")}
        for phase, editorial in (("loose", "superseded"), ("compacted", "retired")):
            with self.subTest(phase=phase):
                code, result, _ = self.invoke("author", {"actor": self.actor,
                    "items": self.revisions(editorial)}, ["--apply", "--json"])
                self.assertEqual(0, code, result)
                model = load(self.root).require_valid()
                self.assertEqual("cancelled", state(model, model.get(self.case.task)))
                self.assertEqual(identities, {key: (model.get(key).digest(), model.get(key).body) for key in keys})
                self.assertEqual(decisions, {e.uid: e.digest() for e in model.by_kind("decision")})
                for key in keys:
                    self.assertEqual(editorial, model.get(key).meta["state"])
                    self.assertEqual(original.get(key).meta["revision"] + (1 if phase == "loose" else 2),
                                     model.get(key).meta["revision"])
                for ref in refs:
                    self.assertEqual(ref["sha256"], sha(read_object(self.root, ref)))
                self.assertFalse((self.root / PENDING).exists())
            if phase == "loose":
                plan = preview(self.root, self.out / "backup", self.out / "restore")
                key = plan["preview_hash"]
                self.assertEqual("awaiting-removal-authorization", apply(self.root, plan, key)["status"])
                self.assertEqual("compacted", recover(self.root, key, remove_authorized=key)["status"])
                self.assertTrue((self.root / object_path(refs[0])).is_file())
                self.assertTrue(all(not (self.root / object_path(ref)).exists() for ref in refs[1:]))
        # A request branch edit also goes through the same public authoring path.
        model = load(self.root).require_valid()
        request = copy.deepcopy(model.get(self.req).item())
        request["meta"]["revision"] += 1
        request["meta"]["data"]["branches"].append("codex/synthetic-close")
        code, result, _ = self.invoke("author", {"actor": self.actor, "items": [request]}, ["--apply", "--json"])
        self.assertEqual(0, code, result)
        self.assertEqual(request["body"], load(self.root).get(self.req).body)

    def test_staging_groups_objects_and_preserves_regular_document_limit(self):
        refs = [self.add_catalog(512, str(i)) for i in range(12)]
        before = snapshot(self.root)
        def inspect(model):
            objects = model.root / ".lks-sdd/objects/sha256"
            self.assertEqual([], list(objects.glob("*")))
            self.assertLessEqual(len(list((model.root / ".lks-sdd/objects/packs").glob("*.zip"))), 2)
            for ref in refs: self.assertEqual(ref["sha256"], sha(read_object(model.root, ref)))
        candidate(self.root, [], inspect)
        self.assertEqual(before, snapshot(self.root))
        name = "docs/lks-sdd/oversized.md"
        write_one(self.root, name, b"x" * (4 * 1024 * 1024 + 1))
        before = snapshot(self.root)
        with self.assertRaisesRegex(ContractError, "bounded regular source"):
            candidate(self.root, [], lambda model: self.fail("Oversized canonical input accepted"))
        self.assertEqual(before, snapshot(self.root))
        with self.assertRaises(ContractError): reference(b"x" * (LIMIT + 1))

    def test_stale_copy_and_corrupt_object_fail_without_project_changes(self):
        before = snapshot(self.root)
        def changed(root, name, **kwargs):
            raw = read_bytes(root, name, **kwargs)
            return raw + b"\nchanged" if name.endswith(".md") else raw
        with patch("v3_authoring.read_bytes", side_effect=changed):
            with self.assertRaisesRegex(ContractError, "source changed"):
                candidate(self.root, [], lambda model: self.fail("Stale candidate accepted"))
        self.assertEqual(before, snapshot(self.root))
        ref = self.add_catalog(4 * 1024 * 1024 + 1, "corrupt")
        (self.root / object_path(ref)).write_bytes(b"tampered")
        before = snapshot(self.root)
        code, result, _ = self.invoke("author", {"actor": self.actor, "items": []}, ["--apply", "--json"])
        self.assertEqual(2, code, result)
        self.assertEqual(before, snapshot(self.root))
        self.assertFalse((self.root / PENDING).exists())


if __name__ == "__main__": unittest.main()
