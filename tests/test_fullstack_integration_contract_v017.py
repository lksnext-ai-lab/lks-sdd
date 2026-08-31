from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from evidence_contract import (  # noqa: E402
    FULLSTACK_GATE_ID,
    integration_evidence_errors,
    integration_gate_applicability,
)


def delivery(*, integrated: bool = True) -> dict:
    value = {
        "tasks": {
            "TASK-001": {"Unit": "UNIT-001", "Profile binding": "BIND-001"},
            "TASK-002": {"Unit": "UNIT-002", "Profile binding": "BIND-002"},
            "TASK-003": {"Unit": "UNIT-001", "Profile binding": "BIND-001"},
        },
        "task_details": {
            "TASK-001": {"integration": []},
            "TASK-002": {"integration": []},
            "TASK-003": {"integration": []},
        },
        "interfaces": {},
    }
    if integrated:
        value["interfaces"]["INT-001"] = {
            "State": "confirmed",
            "Consumer unit": "UNIT-001",
            "Producer unit": "UNIT-002",
            "Profile bindings": "BIND-001, BIND-002",
            "Operations": "read,write",
            "Required evidence": "contract,composition,user-flow,persistence",
            "Verification task": "TASK-003",
            "Exact composition": "WEB-FASTAPI-REACT-KEYCLOAK-PG@2.1.0",
        }
    return value


def fullstack_check() -> dict:
    return {
        "name": "browser-fullstack-e2e",
        "gate_id": FULLSTACK_GATE_ID,
        "status": "passed",
        "evidence_scopes": ["contract", "composition", "user-flow", "persistence"],
        "interface_ids": ["INT-001"],
        "mocks": [
            {"kind": "identity-provider", "path": "/__test__/oidc", "reason": "non-production"}
        ],
        "observations": {
            "runtime_units": ["frontend", "api", "database", "identity"],
            "browser": "chromium",
            "viewport": {"width": 1280, "height": 800},
            "requests": [
                {"path": "/api/v1/items", "method": "POST", "status": 201, "correlation_id": "synthetic-correlation"},
                {"path": "/api/v1/items", "method": "GET", "status": 200},
            ],
            "mutation": {"action": "save synthetic item"},
            "read_back": True,
            "reload": True,
            "persistence": True,
            "screenshots": [
                {"state": "before", "path": "before.png", "sha256": "a" * 64},
                {"state": "after", "path": "after.png", "sha256": "b" * 64},
                {"state": "reloaded", "path": "reloaded.png", "sha256": "c" * 64},
            ],
            "console_errors": [],
        },
    }


class FullstackIntegrationContractV017Tests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = json.loads(
            (PLUGIN_ROOT / "tests/fixtures/fullstack-integration-v017.json").read_text(encoding="utf-8")
        )
        self.assertFalse(fixture["contains_consumer_data"])
        self.assertEqual(len(fixture["scenarios"]), 10)
        self.obligations = integration_gate_applicability(["TASK-003"], delivery())

    def test_components_only_never_verify_cross_unit_interface(self) -> None:
        evidence = {
            "checks": [
                {"name": "frontend", "status": "passed", "evidence_scopes": ["component"], "interface_ids": []},
                {"name": "api", "status": "passed", "evidence_scopes": ["component", "contract"], "interface_ids": []},
                {"name": "database", "status": "passed", "evidence_scopes": ["component"], "interface_ids": []},
            ]
        }
        errors = integration_evidence_errors(evidence, self.obligations)
        self.assertTrue(any("evidencia insuficiente" in item for item in errors))
        self.assertTrue(any(FULLSTACK_GATE_ID in item for item in errors))

    def test_real_fullstack_observation_satisfies_typed_scopes(self) -> None:
        self.assertEqual(
            integration_evidence_errors({"checks": [fullstack_check()]}, self.obligations),
            [],
        )

    def test_backend_only_slice_keeps_gate_not_applicable(self) -> None:
        applicability = integration_gate_applicability(["TASK-002"], delivery())
        self.assertEqual(applicability[0]["status"], "not-applicable")
        no_backend = integration_gate_applicability(["TASK-001"], delivery(integrated=False))
        self.assertEqual(no_backend[0]["status"], "not-applicable")

    def test_frontend_only_slice_keeps_gate_not_applicable(self) -> None:
        applicability = integration_gate_applicability(["TASK-001"], delivery())
        self.assertEqual(applicability[0]["status"], "not-applicable")

    def test_mixed_integration_task_requires_all_bindings_and_scopes(self) -> None:
        obligation = self.obligations[0]
        self.assertEqual(obligation["status"], "applicable")
        self.assertEqual(obligation["binding_ids"], ["BIND-001", "BIND-002"])
        self.assertEqual(
            obligation["required_evidence_scopes"],
            ["composition", "contract", "persistence", "user-flow"],
        )

    def test_functional_domain_mock_is_rejected_for_joint_scopes(self) -> None:
        mocked = fullstack_check()
        mocked["mocks"].append({"kind": "domain-endpoint", "path": "/api/v1/items"})
        errors = integration_evidence_errors({"checks": [mocked]}, self.obligations)
        self.assertTrue(any("mock funcional" in item for item in errors))

    def test_controlled_identity_double_is_allowed(self) -> None:
        self.assertEqual(
            integration_evidence_errors({"checks": [fullstack_check()]}, self.obligations),
            [],
        )

    def test_historical_component_evidence_requires_reconciliation_without_mutation(self) -> None:
        historical = {"schema_version": "1.2", "checks": [{"name": "legacy", "status": "passed"}]}
        before = copy.deepcopy(historical)
        errors = integration_evidence_errors(historical, self.obligations)
        self.assertTrue(errors)
        self.assertEqual(historical, before)

    def test_failed_postvalidation_is_deterministic_and_precedes_any_write(self) -> None:
        invalid = {"checks": [fullstack_check()]}
        invalid["checks"][0]["observations"]["persistence"] = False
        first = integration_evidence_errors(invalid, self.obligations)
        second = integration_evidence_errors(copy.deepcopy(invalid), self.obligations)
        self.assertEqual(first, second)
        self.assertTrue(any("persistencia" in item for item in first))

    def test_relevant_evidence_change_invalidates_the_result(self) -> None:
        valid = fullstack_check()
        self.assertFalse(integration_evidence_errors({"checks": [valid]}, self.obligations))
        changed = copy.deepcopy(valid)
        changed["evidence_scopes"].remove("persistence")
        self.assertTrue(integration_evidence_errors({"checks": [changed]}, self.obligations))


if __name__ == "__main__":
    unittest.main()
