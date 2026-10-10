import copy
import unittest
from usage_test_support import observation
from v3_usage import check_batch, imported, summary_metrics
from v3_contract import ContractError, sha


class ObservationTests(unittest.TestCase):
    def test_import_cannot_claim_measured_runtime(self):
        row = observation()
        self.assertEqual("runtime-derived", imported(row)["origin"]["kind"])
        row["observation_id"] = "forged-import"
        value = imported(row)
        self.assertEqual("agent-declared", value["origin"]["kind"])
        self.assertEqual("declared", value["metrics"]["elapsed"]["status"])

    def test_fragment_union_by_revision_and_shared_invocations(self):
        a, b = observation(text="abcdef"), observation(text="defghi")
        b["fragments"][0].update(start=3,end=9,revision=a["fragments"][0]["revision"])
        metrics = summary_metrics([a,b])
        self.assertEqual((12,9,2), (metrics["accumulated_characters"],metrics["unique_characters_by_revision"],metrics["invocations"]))
        b["fragments"][0]["revision"] = "new"
        self.assertEqual(12, summary_metrics([a,b])["unique_characters_by_revision"])

    def test_budget_collision_and_fragment_integrity_reject(self):
        row = observation()
        with self.assertRaises(ContractError): check_batch([row]*1001)
        other = copy.deepcopy(row); other["phase"] = "other"
        with self.assertRaises(ContractError): check_batch([row,other])
        other = copy.deepcopy(row); other["fragments"][0]["text"] = "tampered"
        with self.assertRaises(ContractError): check_batch([other])
        row["input"]["oversized"] = "x"*(1024*1024)
        with self.assertRaises(ContractError): check_batch([row])

    def test_caller_trace_metadata_cannot_merge_distinct_runtime_invocations(self):
        from v3_usage import observe
        context = {"run_id":"synthetic","invocation_id":"claimed-same"}
        first = observe("context",{}, {},context=context)
        second = observe("context",{}, {},context=context)
        self.assertNotEqual(first["invocation_id"],second["invocation_id"])

    def test_nested_contract_fields_are_preserved_and_claims_do_not_promote(self):
        from v3_usage import observe, logical
        data = {"items":[{"data":{"usage":"business contract", "usage_context":"nested business field"}}],"usage_context":{"run_id":"transport"}}
        self.assertEqual(data["items"],logical(data)["items"])
        row = observation(); row["observation_id"] = "imported"
        converted = imported(row)
        self.assertEqual("runtime-derived",converted["origin"]["claimed"]["kind"])
        self.assertEqual(converted,imported(converted))
