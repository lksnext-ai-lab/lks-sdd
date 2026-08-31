"""Regression of the two independent INT tables; all data is synthetic."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from contract_engine import build_project_model, load_registry
from delivery_engine import (
    ARCHITECTURE_HEADERS, EXTERNAL_INTEGRATION_HEADERS,
    INTEGRATION_INTERFACE_HEADERS, validate_delivery_contract,
)
from evidence_contract import integration_gate_applicability, integration_evidence_errors
from integration_contract import interface_policy, operation_matches
from tests.test_fullstack_integration_contract_v017 import delivery, fullstack_check


def table(headers, rows):
    return "\n".join("| " + " | ".join(row) + " |" for row in (headers, ["---"] * len(headers), *rows))


def materialize(root, tables, *, unit=False):
    path = "docs/lks-sdd/03-solution/integrations.md"
    artifacts = [{"id": "ART-INTEGRATIONS", "path": path, "required": False}]
    content = "---\nartifact_id: ART-INTEGRATIONS\nartifact_type: integrations\nschema_version: 1.5\n---\n\n" + "\n\n".join(tables)
    (root / path).parent.mkdir(parents=True)
    (root / path).write_text(content, encoding="utf-8")
    if unit:
        arch = "docs/lks-sdd/03-solution/architecture.md"
        artifacts.append({"id": "ART-ARCH", "path": arch, "required": True})
        (root / arch).write_text(table(ARCHITECTURE_HEADERS, [[
            "UNIT-001", "proposed", "API", "Receive external contracts", "backend",
            "INT-001", "synthetic", "FR-001", "pending",
        ]]), encoding="utf-8")
    manifest = {"schema_version": "1.5", "method_version": "1.5.0", "artifacts": artifacts}
    (root / ".lks-sdd").mkdir()
    (root / ".lks-sdd/project.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


EXTERNAL = ["INT-001", "proposed", "External mobile client", "Read synthetic data",
            "GET /items", "pending", "Fail closed", "FR-001"]
INTERNAL = ["INT-002", "proposed", "UNIT-001", "UNIT-002", "BIND-001, BIND-002",
            "HTTPS", "GET /items", "read", "contract,composition,user-flow",
            "delivery-owner", "TASK-001", "FR-001", "pending"]


class IntegrationTablesV018Tests(unittest.TestCase):
    def test_both_table_contracts_are_optional_in_15(self):
        contracts = load_registry("1.5").artifacts["ART-INTEGRATIONS"].tables
        self.assertEqual(len(contracts), 2)
        self.assertTrue(all(t.minimum_occurrences == 0 for t in contracts))

    def test_external_internal_both_and_not_applicable_round_trip(self):
        external = table(EXTERNAL_INTEGRATION_HEADERS, [EXTERNAL])
        internal = table(INTEGRATION_INTERFACE_HEADERS, [INTERNAL])
        for tables, ids in [([], set()), ([external], {"INT-001"}),
                            ([internal], {"INT-002"}), ([external, internal], {"INT-001", "INT-002"})]:
            with self.subTest(ids=ids), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                materialize(root, tables)
                model = build_project_model(root)
                self.assertEqual({n for n in model.nodes if n.startswith("INT-")}, ids)
                self.assertFalse([d for d in model.diagnostics if d.location.artifact_id == "ART-INTEGRATIONS"
                                  and d.code.startswith("LKS-TABLE")])

    def test_duplicate_ids_across_tables_are_rejected_without_rewrite(self):
        internal = ["INT-001", *INTERNAL[1:]]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = materialize(root, [table(EXTERNAL_INTEGRATION_HEADERS, [EXTERNAL]),
                                          table(INTEGRATION_INTERFACE_HEADERS, [internal])])
            path = root / manifest["artifacts"][0]["path"]
            before = path.read_bytes()
            model = build_project_model(root)
            self.assertIn("LKS-ID-DUPLICATE", [d.code for d in model.diagnostics])
            self.assertTrue(any("duplicado entre" in e for e in validate_delivery_contract(root, manifest)["errors"]))
            self.assertEqual(path.read_bytes(), before)

    def test_external_reference_does_not_require_fictional_internal_unit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = materialize(root, [table(EXTERNAL_INTEGRATION_HEADERS, [EXTERNAL])], unit=True)
            delivery = validate_delivery_contract(root, manifest)
            self.assertEqual(delivery["interfaces"], {})
            self.assertEqual(delivery["external_integrations"]["INT-001"]["State"], "proposed")
            self.assertFalse(any("contratos inexistentes" in e for e in delivery["errors"]))
            self.assertEqual(set(delivery["units"]), {"UNIT-001"})

    def test_duplicates_within_each_table_are_rejected(self):
        for headers, row in [(EXTERNAL_INTEGRATION_HEADERS, EXTERNAL), (INTEGRATION_INTERFACE_HEADERS, INTERNAL)]:
            with self.subTest(headers=headers), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = materialize(root, [table(headers, [row, row])])
                self.assertIn("LKS-ID-DUPLICATE", [d.code for d in build_project_model(root).diagnostics])
                self.assertTrue(any("duplicados" in e for e in validate_delivery_contract(root, manifest)["errors"]))

    def test_contract_operations_outside_api_v1_are_supported(self):
        document = delivery()
        document["interfaces"]["INT-001"]["Contract"] = "POST /records; GET /records"
        obligation = integration_gate_applicability(["TASK-003"], document)
        check = fullstack_check()
        for request in check["observations"]["requests"]:
            request["path"] = "/records"
        check["observations"]["mutation"]["path"] = "/records"
        self.assertEqual(integration_evidence_errors({"checks": [check]}, obligation), [])
        check["mocks"].append({"kind": "domain-endpoint", "path": "/records"})
        self.assertTrue(any("mock funcional" in e for e in integration_evidence_errors({"checks": [check]}, obligation)))

    def test_login_and_unrelated_write_do_not_prove_business_persistence(self):
        obligations = integration_gate_applicability(["TASK-003"], delivery())
        for path in ["/auth/login", "/api/v1/other", "/api/v1/items-elsewhere"]:
            check = fullstack_check()
            check["observations"]["requests"][0]["path"] = path
            check["observations"]["mutation"]["path"] = path
            self.assertTrue(integration_evidence_errors({"checks": [check]}, obligations), path)

    def test_unknown_contract_is_insufficient_not_inferred_from_success(self):
        document = delivery()
        document["interfaces"]["INT-001"]["Contract"] = "pending"
        obligations = integration_gate_applicability(["TASK-003"], document)
        self.assertTrue(any("información insuficiente" in e for e in integration_evidence_errors({"checks": [fullstack_check()]}, obligations)))

    def test_read_only_http_requires_no_mutation_or_browser(self):
        document = delivery()
        row = document["interfaces"]["INT-001"]
        row.update({"Operations": "read", "Required evidence": "contract,composition", "Contract": "GET /records"})
        obligations = integration_gate_applicability(["TASK-003"], document)
        check = {"status": "passed", "name": "http", "gate_id": obligations[0]["gate_id"],
                 "evidence_scopes": ["contract", "composition"], "interface_ids": ["INT-001"],
                 "observations": {"runtime_units": ["api"], "requests": [{"method": "GET", "path": "/records", "status": 200}]}}
        self.assertEqual(integration_evidence_errors({"checks": [check]}, obligations), [])

    def test_database_and_migration_observers_never_require_browser(self):
        for protocol, observer in [("PostgreSQL", "postgresql"), ("Alembic", "migration")]:
            policy = interface_policy({"Protocol": protocol, "Operations": "read,write", "Required evidence": "contract,composition,persistence"})
            self.assertEqual(policy["observer"], observer)
            self.assertNotIn("user-flow", policy["required_scopes"])
            self.assertNotIn("BROWSER", policy["gate_id"])

    def test_http_operation_parameters_match_one_complete_segment(self):
        operation = {"method": "GET", "path": "/records/{id}"}
        self.assertTrue(operation_matches({"method": "GET", "path": "/records/17"}, operation))
        self.assertFalse(operation_matches({"method": "GET", "path": "/records/17/private"}, operation))
        self.assertFalse(operation_matches({"method": "POST", "path": "/records/17"}, operation))


if __name__ == "__main__":
    unittest.main()
