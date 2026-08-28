from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from run_quality_harness import (  # noqa: E402
    CATALOG_PATH,
    DEFINITION_CORPUS_PATH,
    HarnessError,
    _definition_corpus_matches_plugin_line,
    _load_json,
    evaluate_definition_conversation,
    validate_catalog,
    validate_definition_corpus,
)


class DefinitionQualityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = validate_catalog(_load_json(CATALOG_PATH))
        self.corpus = validate_definition_corpus(
            _load_json(DEFINITION_CORPUS_PATH), self.catalog
        )

    def test_fx01_no_longer_claims_automated_conversation_evidence(self) -> None:
        fx01 = next(case for case in self.catalog["cases"] if case["id"] == "FX-01")
        self.assertEqual(fx01["mode"], "semantic")
        self.assertEqual(fx01["evidence"], [])

    def test_definition_cases_are_versioned_for_v013_and_not_run(self) -> None:
        self.assertEqual(self.corpus["plugin_version"], "0.15.0")
        self.assertEqual(
            self.corpus["corpus_id"], "lks-sdd-definition-incremental-verification-es-0.15.0"
        )
        self.assertEqual(
            {case["id"] for case in self.catalog["extension_cases"]},
            {f"FX-{index:02d}" for index in range(20, 56)},
        )
        self.assertEqual(
            {case["id"] for case in self.corpus["cases"]},
            {"FX-01", "FX-20", "FX-21", "FX-36", "FX-53"},
        )
        channel = evaluate_definition_conversation(self.corpus)
        self.assertEqual(channel["status"], "not-run")
        self.assertEqual(channel["observed"], 0)
        self.assertEqual(channel["total"], 5)

    def test_definition_evidence_cannot_be_invented(self) -> None:
        changed = copy.deepcopy(self.corpus)
        changed["execution_status"] = "passed"
        changed["evidence"] = ["synthetic-result"]
        with self.assertRaisesRegex(HarnessError, "not-run"):
            validate_definition_corpus(changed, self.catalog)

    def test_definition_corpus_is_reusable_only_within_compatible_patches(self) -> None:
        self.assertTrue(_definition_corpus_matches_plugin_line("0.6.0", "0.6.1"))
        self.assertFalse(_definition_corpus_matches_plugin_line("0.6.2", "0.6.1"))
        self.assertFalse(_definition_corpus_matches_plugin_line("0.6.0", "0.7.0"))
        self.assertTrue(_definition_corpus_matches_plugin_line("0.7.0", "0.7.0"))
        self.assertTrue(_definition_corpus_matches_plugin_line("0.7.0", "0.7.1"))
        self.assertTrue(_definition_corpus_matches_plugin_line("0.10.0", "0.10.0"))
        self.assertTrue(_definition_corpus_matches_plugin_line("0.10.0", "0.10.1"))
        self.assertFalse(_definition_corpus_matches_plugin_line("0.9.0", "0.10.0"))
        self.assertTrue(_definition_corpus_matches_plugin_line("0.11.0", "0.11.0"))
        self.assertFalse(_definition_corpus_matches_plugin_line("0.10.0", "0.11.0"))
        self.assertTrue(_definition_corpus_matches_plugin_line("0.12.0", "0.12.0"))
        self.assertFalse(_definition_corpus_matches_plugin_line("0.11.0", "0.12.0"))
        self.assertTrue(_definition_corpus_matches_plugin_line("0.15.0", "0.15.0"))
        self.assertFalse(_definition_corpus_matches_plugin_line("0.12.0", "0.15.0"))


if __name__ == "__main__":
    unittest.main()
