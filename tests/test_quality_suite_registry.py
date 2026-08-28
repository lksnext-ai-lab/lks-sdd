from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from quality_execution import (  # noqa: E402
    QualityExecutionError,
    impacted_modules,
    load_impact_map,
    load_performance_policy,
    load_suite_registry,
    modules_for_suite,
    performance_assessment,
)
from update_performance_baseline import build_baseline  # noqa: E402


class QualitySuiteRegistryTests(unittest.TestCase):
    def test_v015_e2e_matrix_assigns_all_34_mandatory_scenarios(self):
        matrix = json.loads(
            (PLUGIN_ROOT / "quality/v0.15-e2e-matrix.json").read_text(
                encoding="utf-8"
            )
        )
        scenarios = matrix["scenarios"]
        self.assertEqual([item["id"] for item in scenarios], list(range(1, 35)))
        self.assertTrue(all(item["status"] == "automated" for item in scenarios))
        for item in scenarios:
            module, class_name, method = item["test_id"].split(".")
            source_path = PLUGIN_ROOT / "tests" / f"{module}.py"
            self.assertTrue(source_path.is_file(), item)
            source = source_path.read_text(encoding="utf-8")
            self.assertIn(f"class {class_name}", source, item)
            self.assertIn(f"def {method}(", source, item)

    def test_registry_assigns_every_module_exactly_once(self):
        registry = load_suite_registry()
        all_modules = [module for module, _tier, _timeout in modules_for_suite("all", registry)]
        self.assertEqual(len(all_modules), len(set(all_modules)))
        self.assertIn("test_m5_pilot", registry["tiers"]["package"]["modules"])
        self.assertIn(
            "test_visual_contract", registry["tiers"]["integration"]["modules"]
        )
        self.assertEqual(registry["tiers"]["integration"]["max_workers"], 4)
        self.assertNotIn("test_m5_pilot", registry["tiers"]["fast"]["modules"])

    def test_registry_rejects_unassigned_module(self):
        registry = load_suite_registry()
        registry["tiers"]["fast"]["modules"].remove("test_v06_quality")
        with tempfile.TemporaryDirectory(prefix="lks-sdd-suite-registry-") as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaisesRegex(QualityExecutionError, "missing=.*test_v06_quality"):
                load_suite_registry(path)

    def test_registry_rejects_invalid_worker_concurrency(self):
        registry = copy.deepcopy(load_suite_registry())
        registry["tiers"]["integration"]["max_workers"] = 0
        with tempfile.TemporaryDirectory(prefix="lks-sdd-suite-workers-") as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaisesRegex(QualityExecutionError, "concurrencia válida"):
                load_suite_registry(path)

    def test_impact_map_selects_known_modules_and_fails_safe_for_unknown_paths(self):
        impact_map = load_impact_map()
        known = impacted_modules(["scripts/jira_reporting_engine.py"], impact_map)
        self.assertFalse(known["fallback_applied"])
        self.assertEqual(
            known["modules"],
            [
                "test_jira_reporting_v15",
                "test_task_tracking_v14",
                "test_task_tracking_v14_extended",
                "test_task_tracking_v14_fifth",
                "test_task_tracking_v14_final",
                "test_task_tracking_v14_fourth",
                "test_task_tracking_v14_initial_tail",
                "test_task_tracking_v14_middle",
            ],
        )
        unknown = impacted_modules(["new-area/unknown.py"], impact_map)
        self.assertTrue(unknown["fallback_applied"])
        self.assertEqual(
            unknown["modules"],
            sorted(load_suite_registry()["tiers"]["integration"]["modules"]),
        )

    def test_performance_policy_blocks_absolute_and_comparable_regressions(self):
        policy = load_performance_policy()
        fingerprint = policy["baseline"]["runner_fingerprint"]
        policy["baseline"]["durations_seconds"] = {"fast": 60}
        absolute = performance_assessment({"fast": 121}, policy, fingerprint)
        self.assertEqual(absolute["status"], "failed")
        self.assertTrue(absolute["baseline_comparable"])
        relative = performance_assessment({"fast": 91}, policy, fingerprint)
        self.assertEqual(relative["status"], "failed")
        self.assertTrue(relative["comparisons"][0]["regressed"])

    def test_non_comparable_runner_still_enforces_absolute_budget(self):
        policy = load_performance_policy()
        result = performance_assessment(
            {"fast": 121},
            policy,
            {"os": "other", "architecture": "other", "python": "0.0", "implementation": "other"},
        )
        self.assertFalse(result["baseline_comparable"])
        self.assertEqual(result["status"], "failed")

    def test_baseline_requires_three_identical_complete_runs(self):
        fingerprint = {
            "os": "windows",
            "architecture": "amd64",
            "python": "3.14",
            "implementation": "cpython",
            "runner_class": "fixture",
        }
        comparisons = [
            {"suite": suite, "actual_seconds": duration}
            for suite, duration in {
                "fast": 1,
                "integration": 400,
                "package": 80,
                "profile": 120,
                "candidate": 601,
            }.items()
        ]
        result = {
            "selected_suite": "all",
            "passed": True,
            "termination": "normal",
            "runner_fingerprint": fingerprint,
            "performance": {"comparisons": comparisons},
            "results": [{"id": "fixture.test", "status": "passed"}],
        }
        baseline = build_baseline(
            [result, json.loads(json.dumps(result)), json.loads(json.dumps(result))],
            reason="Medición deliberada para el fixture",
            commit="a" * 40,
        )
        self.assertEqual(baseline["sample_count"], 3)
        self.assertEqual(baseline["durations_seconds"]["integration"], 400)
        with self.assertRaisesRegex(QualityExecutionError, "exactamente tres"):
            build_baseline(
                [result], reason="Medición deliberada para el fixture", commit="a" * 40
            )


if __name__ == "__main__":
    unittest.main()
