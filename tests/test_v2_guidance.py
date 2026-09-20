"""Regression coverage for functional blocked-operation guidance."""
from __future__ import annotations

import unittest

from eval_support import SCRIPTS_ROOT
from v2_cli import human_guidance
from v2_guidance import enrich


class V2GuidanceTests(unittest.TestCase):
    def test_authorization_block_is_explained_as_a_user_decision(self):
        value = enrich(
            {"status": "blocked", "error": "AUTH absent, revoked, expired or stale for this scope/environment"},
            operation="verify",
        )

        self.assertEqual(value["guidance"]["kind"], "authorization")
        self.assertNotIn("AUTH", value["guidance"]["summary"])
        self.assertIn("nueva autorización", value["guidance"]["next_step"])
        self.assertTrue(value["guidance"]["decision_required"])

    def test_observer_block_explains_safe_recovery_without_implicit_execution(self):
        value = enrich(
            {"status": "blocked", "blockers": ["No approved observer applies to required gate GATE-A for test/development"]},
            operation="verify",
        )

        self.assertEqual(value["guidance"]["kind"], "verification-availability")
        self.assertIn("comprobación acordada", value["guidance"]["summary"])
        self.assertIn("no se debe sustituir por un script casual", value["guidance"]["next_step"])
        self.assertTrue(any("reservas" in option for option in value["guidance"]["options"]))

    def test_scope_block_offers_replan_without_claiming_completion(self):
        value = enrich(
            {"status": "blocked", "blockers": ["Changes outside authorized paths: src/unrelated.py"]},
            operation="close",
        )

        self.assertEqual(value["guidance"]["kind"], "scope")
        self.assertIn("no puede verificarse ni cerrarse", value["guidance"]["impact"])
        self.assertTrue(any("replanificar" in option for option in value["guidance"]["options"]))

    def test_human_guidance_hides_raw_diagnostic_but_keeps_the_next_step(self):
        value = enrich(
            {"status": "blocked", "error": "AUTH absent, revoked, expired or stale for this scope/environment"},
            operation="close",
        )

        rendered = human_guidance(value)

        self.assertNotIn("AUTH absent", rendered)
        self.assertIn("La autorización para continuar", rendered)
        self.assertIn("Siguiente paso:", rendered)
        self.assertIn("--json", rendered)

    def test_invalid_contract_is_explained_instead_of_returning_an_opaque_status(self):
        value = enrich(
            {"status": "invalid", "diagnostics": ["Invalid document contract"]},
            operation="validate",
        )

        self.assertEqual(value["guidance"]["kind"], "contract")
        self.assertIn("documentación", value["guidance"]["next_step"])

    def test_nonblocked_result_is_not_enriched(self):
        value = {"status": "planned", "checks": []}

        self.assertIs(enrich(value, operation="verify"), value)


if __name__ == "__main__":
    unittest.main()
