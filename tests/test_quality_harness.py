from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from run_quality_harness import (  # noqa: E402
    CATALOG_PATH,
    CORPUS_PATH,
    DEFAULT_BASELINE_PATH,
    FIXTURE_MANIFEST_PATH,
    PILOT_SUMMARY_SCHEMA_PATH,
    UNIT_TEST_TIMEOUT_SECONDS,
    _canonical_bytes,
    _load_json,
    _run_command,
    _sha256_bytes,
    _unit_test_metrics,
    build_report,
    compare_metrics,
    evaluate_activation,
    evaluate_automated_evidence,
    evaluate_document_reviews,
    evaluate_pilot,
    main,
    repository_binding,
    run_automated,
    validate_catalog,
    validate_corpus,
    validate_fixture_manifest,
    validate_observations,
    validate_pilot_summary,
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
        self.assertEqual(result["fixture_count"], 10)

    def test_fixture_hash_drift_is_reported(self):
        manifest = copy.deepcopy(_load_json(FIXTURE_MANIFEST_PATH))
        manifest["fixtures"][0]["sha256"] = "0" * 64
        result = validate_fixture_manifest(manifest_value=manifest)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("Hash" in error for error in result["errors"]))

    def test_failed_json_check_names_the_failing_inner_gate(self):
        payload = {
            "passed": False,
            "complete_gate": False,
            "checks": [
                {
                    "name": "frontend-tests",
                    "status": "failed",
                    "exit_code": 1,
                }
            ],
        }
        completed = subprocess.CompletedProcess(
            args=["synthetic"],
            returncode=2,
            stdout=json.dumps(payload),
            stderr="",
        )
        with patch("run_quality_harness.subprocess.run", return_value=completed):
            check, parsed, _ = _run_command(
                "reference-profile-complete",
                ["synthetic"],
                json_output=True,
            )

        self.assertEqual(parsed, payload)
        self.assertEqual(check["status"], "failed")
        self.assertEqual(
            check["summary"], "exit=2; failed=frontend-tests(exit=1)"
        )

    def test_failed_unit_result_names_are_visible_in_check_summary(self):
        payload = {
            "passed": False,
            "results": [
                {"name": "test_first", "status": "failed"},
                {"name": "test_second", "status": "failed"},
                {"name": "test_ok", "status": "passed"},
            ],
        }
        completed = subprocess.CompletedProcess(
            args=["synthetic"],
            returncode=1,
            stdout=json.dumps(payload),
            stderr="",
        )
        with patch("run_quality_harness.subprocess.run", return_value=completed):
            check, parsed, _ = _run_command(
                "unit-tests",
                ["synthetic"],
                json_output=True,
            )

        self.assertEqual(parsed, payload)
        self.assertEqual(check["status"], "failed")
        self.assertEqual(check["summary"], "exit=1; failed=test_first,test_second")

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
                "source_commit": "1" * 40,
                "metrics": {
                    "automated_eval_pass_rate": 1.0,
                    "critical_failures": 0,
                },
            },
        )
        self.assertEqual(comparison["status"], "failed")
        self.assertEqual(len(comparison["regressions"]), 2)
        self.assertEqual(
            {item["metric"]: item["direction"] for item in comparison["comparisons"]},
            {
                "automated_eval_pass_rate": "higher",
                "critical_failures": "lower",
            },
        )

    def test_release_comparison_treats_total_counts_as_neutral(self):
        comparison = compare_metrics(
            {
                "unit_tests_total": 3,
                "unit_tests_passed": 2,
                "unit_tests_skipped": 1,
            },
            {
                "plugin_version": "0.6.1",
                "source_commit": "2" * 40,
                "metrics": {
                    "unit_tests_total": 81,
                    "unit_tests_passed": 80,
                    "unit_tests_skipped": 0,
                },
            },
        )
        by_metric = {item["metric"]: item for item in comparison["comparisons"]}
        self.assertEqual(by_metric["unit_tests_total"]["direction"], "neutral")
        self.assertFalse(by_metric["unit_tests_total"]["regressed"])
        self.assertTrue(by_metric["unit_tests_passed"]["regressed"])
        self.assertTrue(by_metric["unit_tests_skipped"]["regressed"])

    def test_default_baseline_is_the_last_published_release(self):
        baseline = _load_json(DEFAULT_BASELINE_PATH)
        self.assertEqual(DEFAULT_BASELINE_PATH.name, "v0.12.0.json")
        self.assertEqual(baseline["plugin_version"], "0.12.0")
        self.assertEqual(
            baseline["source_commit"],
            "64d83cd1389e765521c698a35df90da61428d870",
        )
        self.assertEqual(
            {
                name: baseline["metrics"][name]
                for name in (
                    "unit_tests_total",
                    "unit_tests_passed",
                    "unit_tests_skipped",
                    "unit_tests_failed",
                )
            },
            {
                "unit_tests_total": 239,
                "unit_tests_passed": 238,
                "unit_tests_skipped": 1,
                "unit_tests_failed": 0,
            },
        )
        self.assertEqual(baseline["metrics"]["automated_eval_cases"], 5)
        self.assertEqual(baseline["metrics"]["profile_structure_gate"], 1)
        self.assertEqual(baseline["metrics"]["profile_complete_gate"], 1)

    def test_automated_evidence_resolves_test_eval_and_profile_results(self):
        catalog = {
            "cases": [
                {
                    "id": "FX-90",
                    "mode": "automated",
                    "critical": True,
                    "evidence": [
                        "test:test_contract",
                        "eval:EVAL-001",
                        "profile:complete-gate",
                    ],
                }
            ]
        }
        result = evaluate_automated_evidence(
            catalog,
            {
                "results": [
                    {
                        "id": "test_module.ContractTests.test_contract",
                        "name": "test_contract",
                        "status": "passed",
                    }
                ]
            },
            {"results": [{"id": "EVAL-001", "passed": True}]},
            {"complete_gate": True},
        )
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["counts"]["passed"], 1)
        self.assertEqual(
            [item["resolved_id"] for item in result["cases"][0]["evidence"]],
            [
                "test_module.ContractTests.test_contract",
                "EVAL-001",
                "complete-gate",
            ],
        )

    def test_missing_catalog_evidence_fails_closed(self):
        catalog = {
            "cases": [
                {
                    "id": "FX-91",
                    "mode": "automated",
                    "critical": True,
                    "evidence": ["test:test_does_not_exist"],
                }
            ]
        }
        result = evaluate_automated_evidence(
            catalog, {"results": []}, {"results": []}, None
        )
        self.assertEqual(result["status"], "failed")
        self.assertIn("evidence-not-found", result["failures"][0])

    def test_every_catalog_test_and_eval_reference_resolves(self):
        suite = unittest.defaultTestLoader.discover(
            str(PLUGIN_ROOT / "tests"),
            pattern="test_*.py",
            top_level_dir=str(PLUGIN_ROOT / "tests"),
        )

        def iter_tests(group):
            for item in group:
                if isinstance(item, unittest.TestSuite):
                    yield from iter_tests(item)
                else:
                    yield item

        unit_results = [
            {
                "id": test.id(),
                "name": test.id().rsplit(".", 1)[-1],
                "status": "passed",
            }
            for test in iter_tests(suite)
        ]
        eval_results = [
            {"id": entry["id"], "passed": True}
            for entry in _load_json(FIXTURE_MANIFEST_PATH)["fixtures"]
        ]
        result = evaluate_automated_evidence(
            self.catalog,
            {"results": unit_results},
            {"results": eval_results},
            {"complete_gate": True},
        )
        self.assertEqual(result["status"], "passed", result["failures"])
        self.assertEqual(
            result["counts"]["total"],
            sum(
                case["mode"] == "automated"
                for case in [
                    *self.catalog["cases"],
                    *self.catalog.get("extension_cases", []),
                ]
            ),
        )

    def test_skipped_critical_evidence_makes_automation_incomplete(self):
        catalog = {
            "cases": [
                {
                    "id": "FX-92",
                    "mode": "automated",
                    "critical": True,
                    "evidence": ["test:test_platform_guard"],
                }
            ]
        }
        result = evaluate_automated_evidence(
            catalog,
            {
                "results": [
                    {
                        "id": "test_module.SecurityTests.test_platform_guard",
                        "name": "test_platform_guard",
                        "status": "skipped",
                        "reason": "capability unavailable",
                    }
                ]
            },
            {"results": []},
            None,
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["critical_incomplete"], ["FX-92"])
        self.assertFalse(result["failures"])

    def test_skipped_noncritical_evidence_remains_visible_without_blocking(self):
        catalog = {
            "cases": [
                {
                    "id": "FX-93",
                    "mode": "automated",
                    "critical": False,
                    "evidence": ["test:test_optional_platform_guard"],
                }
            ]
        }
        result = evaluate_automated_evidence(
            catalog,
            {
                "results": [
                    {
                        "id": "test_module.OptionalTests.test_optional_platform_guard",
                        "name": "test_optional_platform_guard",
                        "status": "skipped",
                    }
                ]
            },
            {"results": []},
            None,
        )
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["pending"], ["FX-93"])
        self.assertFalse(result["critical_incomplete"])

    def test_unit_metrics_distinguish_passed_skipped_and_failed(self):
        metrics = _unit_test_metrics(
            {
                "results": [
                    {"id": "a", "status": "passed"},
                    {"id": "b", "status": "passed"},
                    {"id": "c", "status": "skipped"},
                    {"id": "d", "status": "failed"},
                ]
            }
        )
        self.assertEqual(metrics["unit_tests_total"], 4)
        self.assertEqual(metrics["unit_tests_executed"], 3)
        self.assertEqual(metrics["unit_tests_passed"], 2)
        self.assertEqual(metrics["unit_tests_skipped"], 1)
        self.assertEqual(metrics["unit_tests_failed"], 1)

    def test_pilot_decision_maps_to_explicit_channel_state(self):
        base = {
            "schema_version": "1.0",
            "pilot_id": "PILOT-SYNTHETIC",
            "observation_count": 5,
            "project_count": 3,
            "participant_count": 5,
            "route_coverage": ["define", "implement"],
            "completed_route_coverage": ["define", "implement"],
            "sample_sufficient": True,
            "metrics": {},
        }
        passed = evaluate_pilot(
            {**base, "decision": {"status": "go", "blockers": [], "conditions": []}}
        )
        incomplete = evaluate_pilot(
            {
                **base,
                "decision": {
                    "status": "go-conditioned",
                    "blockers": [],
                    "conditions": ["activation pending"],
                },
            }
        )
        failed = evaluate_pilot(
            {
                **base,
                "decision": {
                    "status": "no-go",
                    "blockers": ["security incident"],
                    "conditions": [],
                },
            }
        )
        self.assertEqual(passed["status"], "passed")
        self.assertEqual(incomplete["status"], "incomplete")
        self.assertEqual(failed["status"], "failed")

    def test_pilot_summary_is_fully_validated_against_its_schema(self):
        valid = {
            "schema_version": "1.0",
            "pilot_id": "PILOT-SYNTHETIC",
            "observation_count": 5,
            "project_count": 3,
            "participant_count": 5,
            "route_coverage": ["define", "implement"],
            "completed_route_coverage": ["define"],
            "sample_sufficient": True,
            "metrics": {},
            "decision": {"status": "go", "blockers": [], "conditions": []},
        }
        self.assertEqual(validate_pilot_summary(valid), valid)
        invalid_variants = {
            "missing-required": {key: value for key, value in valid.items() if key != "pilot_id"},
            "additional-property": {**valid, "undeclared": True},
            "wrong-type": {**valid, "participant_count": "5"},
            "below-minimum": {**valid, "project_count": -1},
            "duplicate-array-item": {
                **valid,
                "route_coverage": ["define", "define"],
            },
            "invalid-enum": {
                **valid,
                "decision": {
                    "status": "approved",
                    "blockers": [],
                    "conditions": [],
                },
            },
            "invalid-nested-array": {
                **valid,
                "decision": {
                    "status": "go",
                    "blockers": "none",
                    "conditions": [],
                },
            },
        }
        for label, payload in invalid_variants.items():
            with self.subTest(label=label):
                with self.assertRaisesRegex(Exception, "pilot-summary.schema.json"):
                    validate_pilot_summary(payload)

    def test_pilot_schema_vocabulary_is_covered_by_the_validator(self):
        schema = _load_json(PILOT_SUMMARY_SCHEMA_PATH)
        invalid_schema = copy.deepcopy(schema)
        invalid_schema["unevaluatedProperties"] = False
        with self.assertRaisesRegex(Exception, "no soportadas"):
            validate_pilot_summary({}, invalid_schema)

    def test_repository_binding_records_head_and_tree_state(self):
        with patch(
            "run_quality_harness._git_output",
            side_effect=[str(PLUGIN_ROOT), "A" * 40],
        ), patch(
            "run_quality_harness._repository_tree_matches_head", return_value=False
        ):
            self.assertEqual(
                repository_binding(),
                {"commit": "a" * 40, "tree_state": "dirty"},
            )
        with patch(
            "run_quality_harness._git_output",
            side_effect=[str(PLUGIN_ROOT), "b" * 40],
        ), patch(
            "run_quality_harness._repository_tree_matches_head", return_value=True
        ):
            self.assertEqual(
                repository_binding(),
                {"commit": "b" * 40, "tree_state": "clean"},
            )

    def test_complete_profile_gate_names_the_representative_profile(self):
        commands: dict[str, list[str]] = {}
        timeouts: dict[str, int] = {}

        def fake_run(check_id, command, json_output=False, timeout=600):
            commands[check_id] = command
            timeouts[check_id] = timeout
            payload = (
                {"results": []}
                if check_id in {"unit-tests", "deterministic-evals"}
                else {"complete_gate": True, "passed": True, "checks": []}
                if check_id == "reference-profile-complete"
                else None
            )
            return (
                {
                    "id": check_id,
                    "status": "passed",
                    "critical": True,
                    "summary": "exit=0",
                },
                payload,
                "",
            )

        with patch(
            "run_quality_harness.validate_fixture_manifest",
            return_value={"status": "passed", "fixture_count": 6, "errors": []},
        ), patch("run_quality_harness._run_command", side_effect=fake_run):
            run_automated(self.catalog, True)

        command = commands["reference-profile-complete"]
        profile_index = command.index("--profile")
        self.assertEqual(
            command[profile_index + 1], "WEB-FASTAPI-REACT-KEYCLOAK-PG"
        )
        self.assertEqual(timeouts["unit-tests"], UNIT_TEST_TIMEOUT_SECONDS)
        self.assertGreaterEqual(UNIT_TEST_TIMEOUT_SECONDS, 1800)

    def test_reuse_profile_mode_checks_exact_certifications_without_docker(self):
        commands: dict[str, list[str]] = {}

        def fake_run(check_id, command, json_output=False, timeout=600):
            commands[check_id] = command
            payload = (
                {"results": []}
                if check_id in {"unit-tests", "deterministic-evals"}
                else {"complete_gate": True, "passed": True}
                if check_id == "reference-profile-complete"
                else None
            )
            return (
                {
                    "id": check_id,
                    "status": "passed",
                    "critical": True,
                    "summary": "exit=0",
                },
                payload,
                "",
            )

        with patch(
            "run_quality_harness.validate_fixture_manifest",
            return_value={"status": "passed", "fixture_count": 6, "errors": []},
        ), patch("run_quality_harness._run_command", side_effect=fake_run):
            run_automated(self.catalog, "reuse", "2026-08-26")

        command = commands["reference-profile-complete"]
        self.assertIn("scripts/verify_profile_certifications.py", command)
        self.assertIn("--max-age-days", command)
        self.assertNotIn("--containers", command)

    def test_dirty_source_fails_candidate_gate_without_running_real_suite(self):
        automated = (
            [
                {
                    "id": "fixture-integrity",
                    "status": "passed",
                    "critical": True,
                    "summary": "synthetic fixture check",
                },
                {
                    "id": "reference-profile-complete",
                    "status": "passed",
                    "critical": True,
                    "summary": "synthetic complete profile",
                },
            ],
            {"critical_failures": 0},
            [],
            {
                "status": "passed",
                "counts": {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "incomplete": 0,
                },
                "cases": [],
                "critical_incomplete": [],
                "pending": [],
            },
        )
        with patch(
            "run_quality_harness.repository_binding",
            return_value={"commit": "c" * 40, "tree_state": "dirty"},
        ), patch("run_quality_harness.run_automated", return_value=automated):
            report = build_report(
                "2026-08-20",
                "candidate",
                None,
                None,
                DEFAULT_BASELINE_PATH,
                True,
            )

        self.assertEqual(report["source"]["tree_state"], "dirty")
        self.assertEqual(report["gate"]["status"], "failed")
        self.assertFalse(report["gate"]["eligible"])
        self.assertTrue(
            any(
                "source.tree_state=dirty" in blocker
                for blocker in report["gate"]["blockers"]
            )
        )

    def test_cli_returns_failure_for_dirty_source_gate(self):
        report = {
            "source": {"commit": "d" * 40, "tree_state": "dirty"},
            "gate": {
                "status": "failed",
                "eligible": False,
                "blockers": ["source.tree_state=dirty"],
                "missing_evidence": [],
            },
        }
        with patch.object(
            sys,
            "argv",
            ["run_quality_harness.py", "--channel", "candidate"],
        ), patch("run_quality_harness.build_report", return_value=report), patch(
            "builtins.print"
        ):
            self.assertEqual(main(), 2)

    def test_assume_unchanged_cannot_create_a_clean_release_attestation(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-hidden-dirty-") as directory:
            root = Path(directory).resolve()
            script = root / "scripts" / "run_quality_harness.py"
            script.parent.mkdir(parents=True)
            script.write_text("print('original')\n", encoding="utf-8")

            def git(*arguments: str) -> str:
                process = subprocess.run(
                    ["git", *arguments],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                    timeout=30,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                return process.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "LKS-SDD Test")
            git("config", "user.email", "lks-sdd-test@example.invalid")
            git("add", "--", "scripts/run_quality_harness.py")
            git("commit", "--quiet", "-m", "fixture")

            with patch("run_quality_harness.PLUGIN_ROOT", root):
                self.assertEqual(repository_binding()["tree_state"], "clean")
                git(
                    "update-index",
                    "--assume-unchanged",
                    "--",
                    "scripts/run_quality_harness.py",
                )
                script.write_text("print('tampered')\n", encoding="utf-8")
                self.assertEqual(
                    git("status", "--porcelain=v1", "--untracked-files=all"), ""
                )
                self.assertEqual(
                    repository_binding()["tree_state"],
                    "dirty",
                    "un cambio oculto no puede producir una atestación clean",
                )

    def test_info_exclude_cannot_hide_an_influential_untracked_python_file(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-hidden-untracked-") as directory:
            root = Path(directory).resolve()
            script = root / "scripts" / "run_quality_harness.py"
            script.parent.mkdir(parents=True)
            script.write_text("print('original')\n", encoding="utf-8")

            def git(*arguments: str) -> str:
                process = subprocess.run(
                    ["git", *arguments],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                    timeout=30,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                return process.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "LKS-SDD Test")
            git("config", "user.email", "lks-sdd-test@example.invalid")
            git("add", "--", "scripts/run_quality_harness.py")
            git("commit", "--quiet", "-m", "fixture")
            git_dir = Path(git("rev-parse", "--git-dir"))
            if not git_dir.is_absolute():
                git_dir = root / git_dir
            (git_dir / "info" / "exclude").write_text(
                "scripts/sitecustomize.py\n", encoding="utf-8"
            )
            (root / "scripts" / "sitecustomize.py").write_text(
                "raise RuntimeError('must never be hidden')\n", encoding="utf-8"
            )
            self.assertEqual(
                git("status", "--porcelain=v1", "--untracked-files=all"), ""
            )

            with patch("run_quality_harness.PLUGIN_ROOT", root):
                self.assertEqual(
                    repository_binding()["tree_state"],
                    "dirty",
                    ".git/info/exclude no puede ocultar código influyente",
                )

    def test_quality_report_schema_requires_release_binding(self):
        schema = _load_json(PLUGIN_ROOT / "schemas" / "quality-report.schema.json")
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.1")
        self.assertIn("source", schema["required"])
        source = schema["properties"]["source"]
        self.assertEqual(source["required"], ["commit", "tree_state"])
        self.assertEqual(
            source["properties"]["tree_state"]["enum"], ["clean", "dirty"]
        )

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
