from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from run_quality_harness import (  # noqa: E402
    CATALOG_PATH,
    CORPUS_PATH,
    FIXTURE_MANIFEST_PATH,
    _canonical_bytes,
    _load_json,
    _sha256_bytes,
    compare_metrics,
    evaluate_activation,
    evaluate_document_reviews,
    validate_catalog,
    validate_corpus,
    validate_fixture_manifest,
    validate_observations,
)


class QualityHarnessTests(unittest.TestCase):
    def setUp(self):
        self.catalog = validate_catalog(_load_json(CATALOG_PATH))
        self.corpus = validate_corpus(_load_json(CORPUS_PATH))

    def _observations(self) -> dict:
        return {
            "schema_version": "1.0",
            "corpus_id": self.corpus["corpus_id"],
            "corpus_sha256": _sha256_bytes(_canonical_bytes(self.corpus)),
            "evaluator_context": {
                "kind": "controlled-codex-session",
                "product": "Codex",
                "executed_on": "2026-08-19",
                "evidence_reference": "sanitized-evidence-001",
            },
            "activation_results": [
                {
                    "case_id": case["id"],
                    "actual_skill": case["expected_skill"],
                }
                for case in self.corpus["cases"]
            ],
            "document_reviews": [
                {
                    "artifact_reference": "synthetic-artifact-001",
                    "scores": {
                        "correctness": 4,
                        "completeness": 4,
                        "clarity": 4,
                        "verifiability": 4,
                        "traceability": 4,
                        "proportionality": 4,
                        "operational_utility": 4,
                        "audience_fit": 4,
                        "information_separation": 4,
                        "information_protection": 4,
                    },
                }
            ],
        }

    def test_catalog_covers_fx_01_to_fx_19(self):
        self.assertEqual(len(self.catalog["cases"]), 19)
        self.assertEqual(
            {case["id"] for case in self.catalog["cases"]},
            {f"FX-{index:02d}" for index in range(1, 20)},
        )

    def test_fixture_manifest_is_complete_and_hash_locked(self):
        result = validate_fixture_manifest()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["fixture_count"], 5)

    def test_fixture_hash_drift_is_reported(self):
        manifest = copy.deepcopy(_load_json(FIXTURE_MANIFEST_PATH))
        manifest["fixtures"][0]["sha256"] = "0" * 64
        result = validate_fixture_manifest(manifest_value=manifest)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("Hash" in error for error in result["errors"]))

    def test_perfect_activation_and_document_observations_pass(self):
        observations = validate_observations(self._observations(), self.corpus)
        activation, metrics, critical = evaluate_activation(
            self.corpus, observations, self.catalog["thresholds"]
        )
        documents, document_metrics = evaluate_document_reviews(
            observations, self.catalog["thresholds"]
        )
        self.assertEqual(activation["status"], "passed")
        self.assertEqual(metrics["activation_precision"], 1.0)
        self.assertEqual(metrics["activation_recall"], 1.0)
        self.assertFalse(critical)
        self.assertEqual(documents["status"], "passed")
        self.assertEqual(document_metrics["document_review_average"], 4.0)

    def test_critical_routing_mismatch_is_highlighted(self):
        observations = self._observations()
        observations["activation_results"][0]["actual_skill"] = None
        validated = validate_observations(observations, self.corpus)
        activation, _, critical = evaluate_activation(
            self.corpus, validated, self.catalog["thresholds"]
        )
        self.assertEqual(activation["status"], "failed")
        self.assertTrue(any("ACT-001" in failure for failure in critical))

    def test_stale_observations_are_rejected(self):
        observations = self._observations()
        observations["corpus_sha256"] = "0" * 64
        with self.assertRaisesRegex(Exception, "obsoletas"):
            validate_observations(observations, self.corpus)

    def test_release_comparison_detects_regression(self):
        comparison = compare_metrics(
            {"automated_eval_pass_rate": 0.9, "critical_failures": 1},
            {
                "plugin_version": "0.3.0",
                "metrics": {
                    "automated_eval_pass_rate": 1.0,
                    "critical_failures": 0,
                },
            },
        )
        self.assertEqual(comparison["status"], "failed")
        self.assertEqual(len(comparison["regressions"]), 2)

    def test_report_inputs_have_stable_canonical_hashes(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-quality-") as directory:
            path = Path(directory) / "copy.json"
            path.write_text(
                json.dumps(self.corpus, indent=4, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            reloaded = _load_json(path)
        self.assertEqual(
            _sha256_bytes(_canonical_bytes(self.corpus)),
            _sha256_bytes(_canonical_bytes(reloaded)),
        )


if __name__ == "__main__":
    unittest.main()
