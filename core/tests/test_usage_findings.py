import copy
import unittest
from usage_test_support import observation, repeated, late
from usage_findings import detect, disposition
from v3_contract import ContractError


class FindingTests(unittest.TestCase):
    def test_repetition_distinct_invocations_and_countercases(self):
        rows = repeated()
        f = detect(rows)["findings"][0]
        self.assertEqual("UF-01", f["rule"]); self.assertEqual(2,len(f["occurrences"]))
        self.assertEqual([],detect([rows[0],rows[0]])["findings"])
        rows[1]["fragments"][0]["revision"] = "new"
        self.assertEqual([],detect(rows)["findings"])

    def test_widening_and_legitimate_scope(self):
        row = observation(result={"widened": [{"reason":"Unknown scope: preserve"}]})
        self.assertEqual("UF-02",detect([row])["findings"][0]["rule"])
        row["result"]["widened"] = []
        self.assertEqual([],detect([row])["findings"])

    def test_failed_retries_and_freshness(self):
        a,b = [observation("failed", "apply", result={"status":"blocked","cause":"source changed"}) for _ in range(2)]
        self.assertEqual([],detect([a])["findings"])
        self.assertEqual("UF-03",detect([a,b])["findings"][0]["rule"])
        a["preview_hash"] = "exact-preview"
        self.assertIn("UF-04", {f["rule"] for f in detect([a,b])["findings"]})
        a["result"]["cause"] = "input invalid"
        self.assertNotIn("UF-04", {f["rule"] for f in detect([a])["findings"]})

    def test_late_context_keeps_cause_pending_and_missing_evidence(self):
        rows,_ = late()
        f = detect(rows)["findings"][0]
        self.assertEqual("UF-05", f["rule"]); self.assertIn("pendiente",f["hypothesis"])
        del rows[0]["declarations"][0]["before"]
        self.assertEqual("needs-evidence",detect(rows)["findings"][0]["state"])
        rows[0]["declarations"] = []
        self.assertEqual([],detect(rows)["findings"])

    def test_question_and_overhead_positive_countercases(self):
        r = observation(stage="declared",operation="checkpoint")
        r["declarations"] = [{"type":"repeated-question","question":"q","decision":"d","scope":"s","intervention":"i"},
                              {"type":"diagnostic-overhead","unexpected_growth":True,"evidence":"measurement"}]
        self.assertEqual({"UF-06","UF-07"}, {f["rule"] for f in detect([r])["findings"]})
        r["declarations"][0]["new_decision"] = True
        r["declarations"][1]["unexpected_growth"] = False
        self.assertEqual([],detect([r])["findings"])

    def test_resolution_needs_version_change_and_evidence_retains_occurrences(self):
        f = detect(repeated())["findings"][0]
        with self.assertRaises(ContractError): disposition(f,"resolved-with-evidence",reason="Recommended caching")
        done = disposition(f,"resolved-with-evidence",reason="Case checked",plugin_version="synthetic",change="fixture change",evidence="case check")
        self.assertEqual(f["occurrences"],done["occurrences"])
        self.assertEqual("resolved-with-evidence",done["state"])
        discarded = disposition(f,"dismissed-with-reason",reason="Required reread after handoff")
        self.assertEqual(1,len(discarded["history"]))
