"""One public consumer fixture: large-history closure and explicit resource consent."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
import test_v4_cli_presentation as fixture
import test_v3_historical_presentation as historical
from capacity import DEFAULTS, MiB
from content_store import object_path, publish_object, read_object, reference
from v2_contract import canonical, sha
from v3_contract import load, render
from v3_storage import apply
from v3_authoring import author


class PublicCapacityTests(unittest.TestCase):
    setUpClass = classmethod(fixture.MinimalPresentationTests.setUpClass.__func__)
    setUp = fixture.MinimalPresentationTests.setUp
    invoke = fixture.MinimalPresentationTests.invoke

    def test_close_proposal_with_large_historical_cas_and_context_consent(self):
        from v3_decision_presentation import decision_view
        from v31_review import closure_valid
        key, migration_uid, original = historical.HistoricalPresentationTests.history(self, external_inventory=True)
        model = load(self.root).require_valid()
        migration = copy.deepcopy(model.get(migration_uid).item())
        value = json.loads(read_object(self.root, migration["meta"]["data"]["inventory_ref"]))
        value["annotation"] = "x" * (36_522_291 - len(canonical({**value, "annotation": ""})))
        raw = canonical(value); self.assertEqual(36_522_291, len(raw))
        ref = reference(raw); publish_object(self.root, object_path(ref), raw)
        migration["meta"]["data"]["inventory_ref"] = ref
        (self.root/model.get(migration_uid).path).write_bytes(render(migration, "3.1"))
        proposal = copy.deepcopy(load(self.root).get(self.prop).item())
        proposal["meta"]["revision"] += 1
        proposal["meta"]["relations"]["uses"] = [key]
        packet = author(self.root, self.actor, [proposal]); apply(self.root, packet, packet["preview"]["preview_hash"])
        data = {"actor": self.actor, "request": self.req,
                "statement": "Synthetic explicit review and closure of the presented proposal", "review": True}
        view = decision_view(self.root, "close-proposal", data)
        self.assertTrue(view["complete"], view["issues"])
        self.assertIn(object_path(ref), view["basis"]["source_files"])
        code, public_view, _ = self.invoke("decision-view", {"event": "close-proposal", "data": data}, ["--json", "--compact"])
        self.assertEqual(0, code, public_view)
        self.assertEqual(view["receipt"], public_view["receipt"])
        code, result, _ = self.invoke("close-proposal", {**data, "presented": public_view["receipt"]}, ["--apply", "--json"])
        self.assertEqual(0, code, result)
        self.assertTrue(closure_valid(load(self.root).require_valid(), load(self.root).get(self.req)))
        self.assertEqual(ref["sha256"], sha(read_object(self.root, ref)))
        # A distinct operation uses a large ordinary attachment, which DOES need
        # a resource decision; it must not be mistaken for another functional approval.
        log = self.root/"docs/lks-sdd/evidence/large.log"
        log.parent.mkdir(exist_ok=True); log.write_bytes(b"x" * (5*MiB))
        model = load(self.root)
        proposal = copy.deepcopy(model.get(self.prop).item()); proposal["meta"]["revision"] += 1
        proposal["body"] += "\n[Complete synthetic log](../evidence/large.log)\n"
        # Direct fixture authoring keeps this test about the public context boundary.
        (self.root/model.get(self.prop).path).write_bytes(render(proposal, "3.1"))
        before = fixture.snapshot(self.root)
        params = {"roots": [self.prop]}
        code, blocked, _ = self.invoke("context", params, ["--json"])
        self.assertEqual(2, code, blocked)
        self.assertEqual("capacity-approval-required", blocked["status"])
        self.assertEqual(before, fixture.snapshot(self.root))
        consent = self.out/"capacity-ok.json"
        consent.write_bytes(canonical({"request": blocked["capacity_request"], "approved": True,
                                       "statement": "Synthetic human OK for the stated capacity and recovery"}))
        code, allowed, _ = self.invoke("context", params, ["--json", "--capacity-approval", consent])
        self.assertEqual(0, code, allowed)
        self.assertEqual(before, fixture.snapshot(self.root))
        code, denied, _ = self.invoke("context", {"roots": [self.req]}, ["--json", "--capacity-approval", consent])
        self.assertEqual(2, code, denied)
        self.assertIn("stale", denied["cause"])


if __name__ == "__main__": unittest.main()
