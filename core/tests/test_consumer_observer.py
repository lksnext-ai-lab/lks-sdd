"""Regression coverage for consumer observer error normalization."""
from __future__ import annotations

import sys
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from consumer_observer import ObserverError, validate_output, validate_schema
from observation_contract import gate_observation_errors, persistence_errors
from v2_quality import observation_errors


class ConsumerObserverTests(unittest.TestCase):
    def test_schema_validation_error_is_normalized(self):
        with self.assertRaisesRegex(ObserverError, "Observer schema validation failed"):
            validate_schema({}, "consumer-observation.schema.json")


class PersistenceObserverTests(unittest.TestCase):
    def observation(self, observer="oracle-independent-connection", resource="CTPWEB_TEST_RUN"):
        return {
            "mutation": {"record_id": "synthetic-row-001"},
            "read_back": {"observer": observer, "resource": resource, "record_id": "synthetic-row-001", "matches": True},
            "persistence": True, "domain_mocks": False,
        }

    def test_oracle_independent_read_accepts_exact_catalog_identifiers(self):
        for resource in ("CTPWEB_TEST_RUN", "QA_OWNER.CTPWEB_TEST_ROW", "QA$OWNER.ROW#1", "A" * 128):
            with self.subTest(resource=resource):
                self.assertEqual(persistence_errors(self.observation(resource=resource)), [])

    def test_oracle_rejects_noncanonical_ambiguous_or_expression_resources(self):
        for resource in (None, [], "", "ctpweb_test_run", "OWNER.*", ".TABLE", "OWNER.",
                         "OWNER.TABLE.COLUMN", '"TABLE"', "TABLE@DBLINK", "TABLE;DELETE", "TABLE WHERE 1=1",
                         " TABLE", "TABLE\n", "A" * 129, "1TABLE", "TÁBLE"):
            with self.subTest(resource=resource):
                self.assertIn("database read has no exact resource", persistence_errors(self.observation(resource=resource)))

    def test_postgresql_read_contract_is_unchanged(self):
        for observer in ("postgresql-psql", "postgresql-independent-connection"):
            with self.subTest(observer=observer):
                self.assertEqual(persistence_errors(self.observation(observer, "rows_123")), [])
                self.assertEqual(persistence_errors(self.observation(observer, "_rows")), [])
                for resource in ("ROWS", "public.rows", "rows$", "rows#", "rows;drop table rows"):
                    self.assertIn("database read has no exact resource", persistence_errors(self.observation(observer, resource)))

    def test_unsupported_or_nonindependent_observers_fail_closed(self):
        for observer in (None, [], {}, "", "oracle", "oracle-same-connection", "http", "in-memory", "postgresql"):
            with self.subTest(observer=observer):
                self.assertTrue(persistence_errors(self.observation(observer)))

    def test_oracle_still_requires_matching_record_true_read_and_persistence(self):
        for field, value in (("record_id", "different-row"), ("record_id", None), ("matches", False), ("matches", 1)):
            facts = self.observation()
            facts["read_back"][field] = value
            with self.subTest(field=field, value=value):
                self.assertTrue(persistence_errors(facts))
        for value in (False, None, 1):
            facts = self.observation()
            facts["persistence"] = value
            self.assertTrue(persistence_errors(facts))
        facts = self.observation()
        del facts["read_back"]
        self.assertTrue(persistence_errors(facts))
        self.assertTrue(persistence_errors(None))

    def test_oracle_uses_same_shared_fullstack_and_v2_validation(self):
        facts = self.observation()
        facts.update(reload=True, console_errors=[], screenshots=[{"sha256": "a" * 64}] * 3)
        check = {"gate_id": "GATE-BROWSER-FULLSTACK-E2E", "status": "passed", "scopes": ["persistence"],
                 "observations": facts, "artifacts": [{"path": "synthetic-observation.json", "sha256": "b" * 64}]}
        self.assertEqual(gate_observation_errors(check), [])
        self.assertEqual(observation_errors(check, {"gate_id": check["gate_id"]}), [])
        invalid = copy.deepcopy(check)
        invalid["observations"]["read_back"]["record_id"] = "unrelated-row"
        self.assertTrue(gate_observation_errors(invalid))
        self.assertTrue(observation_errors(invalid, {"gate_id": check["gate_id"]}))

    def test_oracle_consumer_output_preserves_nonce_mocks_and_artifact_guards(self):
        nonce = "a" * 32
        data = b"synthetic contract test; no database contacted"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "observation.txt").write_bytes(data)
            output = {"schema_version": "1.0", "run_nonce": nonce, "gate_id": "GATE-ORACLE-PERSISTENCE",
                      "status": "passed", "scopes": ["persistence"], "interfaces": [], "observations": self.observation(),
                      "artifacts": [{"path": "observation.txt", "sha256": hashlib.sha256(data).hexdigest()}]}
            gate = {"id": output["gate_id"], "scopes": output["scopes"], "interfaces": []}
            self.assertEqual(validate_output(output, gate, nonce, root)["status"], "passed")
            with self.assertRaisesRegex(ObserverError, "not from this invocation"):
                validate_output(output, gate, "b" * 32, root)
            for mocks in (True, None):
                invalid = copy.deepcopy(output)
                invalid["observations"]["domain_mocks"] = mocks
                with self.assertRaisesRegex(ObserverError, "absence of domain mocks"):
                    validate_output(invalid, gate, nonce, root)
            (root / "observation.txt").write_bytes(b"changed")
            with self.assertRaisesRegex(ObserverError, "artifact hash mismatch"):
                validate_output(output, gate, nonce, root)


if __name__ == "__main__":
    unittest.main()
