from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from doctor_project import quick_doctor  # noqa: E402
from experience_engine import (  # noqa: E402
    CACHE_SCHEMA,
    compare_subject,
    load_status,
    management_json,
    read_cache,
    render_management,
    verification_subject,
)
from contract_engine import expand_reference_ids  # noqa: E402
from evidence_contract import evidence_profile_identity_errors  # noqa: E402
from experience_fixture import create_representative_fixture  # noqa: E402
from eval_support import authorize_implementation, materialize_ready_project  # noqa: E402


VERIFIED_REVISION = "2" * 40
VERIFIED_BUILD = "build-sha256:" + "3" * 64
VERIFIED_ARTIFACT = "sha256:" + "4" * 64
VERIFIED_GATES = ["GATE-API-TEST", "GATE-API-OPENAPI", "GATE-OCI-BUILD"]


def run_work(root: Path, operation: str, *arguments: str) -> tuple[int, dict]:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "lks_sdd.py"),
            "work",
            operation,
            str(root),
            *arguments,
            "--json",
        ],
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"work {operation} returned non-JSON output: {completed.stdout}\n{completed.stderr}"
        ) from exc
    return completed.returncode, payload


def record_synthetic_verified_evidence(root: Path) -> None:
    """Materialize exact, generic verification bytes as E2E fixture input."""

    manifest_path = root / ".lks-sdd/project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["verification"] = {
        "status": "verified",
        "increment": "INC-001",
        "task_ids": ["TASK-001"],
        "revision": VERIFIED_REVISION,
        "tree_id": "5" * 40,
        "tree_sha256": "6" * 64,
        "build_id": VERIFIED_BUILD,
        "artifact_digests": [VERIFIED_ARTIFACT],
        "environment": "ENV-001",
        "gate_ids": VERIFIED_GATES,
        "evidence_ids": ["EVID-001"],
        "limitations": [],
    }
    for execution in manifest["executions"]:
        if "TASK-001" in execution.get("task_ids", []):
            execution["evidence_ids"] = ["EVID-001"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    evidence_path = root / "docs/lks-sdd/evidence/EVID-001.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(
            {
                "schema_version": "1.2",
                "evidence_id": "EVID-001",
                "increment": "INC-001",
                "task_ids": ["TASK-001"],
                "revision": VERIFIED_REVISION,
                "build_id": VERIFIED_BUILD,
                "artifact_digests": [VERIFIED_ARTIFACT],
                "environment": "ENV-001",
                "classification": "verified",
                "gate_ids": VERIFIED_GATES,
                "checks": [
                    {"gate_id": gate_id, "status": "passed"}
                    for gate_id in VERIFIED_GATES
                ],
                "limitations": [],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def tree_digest(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class ProductExperienceV015Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = create_representative_fixture(Path(self.temporary.name) / "project")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_management_is_compact_current_and_free_of_internal_jargon(self) -> None:
        status = load_status(self.root)
        compact = management_json(status)
        rendered = render_management(status)
        self.assertLess(len(json.dumps(compact, ensure_ascii=False).encode("utf-8")), 8192)
        self.assertEqual(compact["project"]["release"], "REL-001")
        self.assertEqual(
            {key: compact["project"][key] for key in ("tasks_total", "verified", "in_progress", "blocked", "pending")},
            {"tasks_total": 13, "verified": 1, "in_progress": 1, "blocked": 1, "pending": 10},
        )
        self.assertIn("historically_verified", compact["project"])
        self.assertIn("test_coverage", compact["project"])
        self.assertIn("visual_coverage", compact["project"])
        self.assertEqual(compact["current_task"]["human_decision"], "Ninguna")
        self.assertIn("Evidence recorder", compact["current_task"]["active_blocker"])
        self.assertNotIn("Production promotion", compact["current_task"]["active_blocker"])
        self.assertEqual(len(status["audit"]["problems"]["historical"]), 1)
        self.assertEqual(len(status["audit"]["problems"]["deferred"]), 1)
        for jargon in ("AUTH-", "EXEC-", "CKPT-", "BIND-", "GATE-", "fingerprint", "slice"):
            self.assertNotIn(jargon, rendered)

    def test_views_separate_developer_and_audit_detail(self) -> None:
        status = load_status(self.root)
        self.assertEqual(status["developer"]["components"], ["BIND-001", "UNIT-001"])
        self.assertIn("manifest", status["audit"])
        self.assertNotIn("manifest", management_json(status))
        self.assertEqual(status["instrumentation"]["gate_execution_ms"], 0.0)
        self.assertEqual(status["instrumentation"]["external_sync_ms"], 0.0)

    def test_status_cli_defaults_to_management_and_does_not_mutate(self) -> None:
        before = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "lks_sdd.py"), "status", str(self.root)],
            check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE,
        )
        self.assertIn("PROYECTO · Release REL-001", completed.stdout)
        after = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_quick_doctor_never_runs_internal_suite(self) -> None:
        result = quick_doctor(self.root)
        self.assertEqual(result["status"], "operational")
        self.assertFalse(result["internal_plugin_suite_executed"])
        self.assertEqual(result["jira"]["summary"], "no necesario para la operación actual")

    def test_schema_15_accepts_historical_plugin_provenance(self) -> None:
        manifest_path = self.root / ".lks-sdd/project.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["plugin_version"] = "0.12.0"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        status = load_status(self.root)
        doctor = quick_doctor(self.root)
        self.assertEqual(
            status["audit"]["compatibility"]["materialized_with_plugin_version"],
            "0.12.0",
        )
        self.assertTrue(doctor["project_compatible"])
        self.assertEqual(doctor["materialized_with_plugin_version"], "0.12.0")

    def test_pre15_project_schema_is_rejected_without_mutation(self) -> None:
        manifest_path = self.root / ".lks-sdd/project.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["schema_version"] = "1.4"
        manifest["method_version"] = "1.4.0"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        before = tree_digest(self.root)
        with self.assertRaisesRegex(ValueError, "requiere schema 1.5"):
            load_status(self.root)
        doctor = quick_doctor(self.root)
        self.assertEqual(doctor["status"], "blocked")
        self.assertFalse(doctor["project_compatible"])
        commands = [
            ["tasks", str(self.root), "validate"],
            ["planning", str(self.root), "--increment", "INC-001", "assess"],
            ["tracking", "status", str(self.root)],
            ["continuity", str(self.root), "resume"],
        ]
        for command in commands:
            with self.subTest(command=command[0]):
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPTS / "lks_sdd.py"),
                        *command,
                        "--json",
                    ],
                    check=False,
                    text=True,
                    encoding="utf-8",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(completed.returncode, 2, completed.stdout)
                self.assertIn("schema 1.5", completed.stdout)
        self.assertEqual(before, tree_digest(self.root))

    def test_shared_parser_expands_interior_traceability_ids(self) -> None:
        self.assertEqual(
            expand_reference_ids("TR-001..TR-014", {"TR"}),
            {f"TR-{number:03d}" for number in range(1, 15)},
        )
        self.assertIn("TR-002", expand_reference_ids("TR-001..TR-014", {"TR"}))

    def test_historical_evidence_12_accepts_null_top_level_identity(self) -> None:
        manifest = json.loads(
            (self.root / ".lks-sdd/project.json").read_text(encoding="utf-8")
        )
        lock = {
            "binding_id": "BIND-001",
            "profile_id": "WEB-REACT-VITE-STATIC",
            "profile_version": "1.0.0",
            "sha256": "a" * 64,
        }
        evidence = {
            "schema_version": "1.2",
            "profile_bindings": ["BIND-001"],
            "profile_locks": [lock],
            "profile_id": None,
            "profile_version": None,
            "build_identity_material": {
                "profile_bindings": [
                    {
                        "binding_id": "BIND-001",
                        "profile_id": "WEB-REACT-VITE-STATIC",
                        "profile_version": "1.0.0",
                    }
                ],
                "locks": [lock],
            },
        }
        self.assertEqual(evidence_profile_identity_errors(evidence, manifest), [])

    def test_new_single_and_multiprofile_evidence_identity_is_unambiguous(self) -> None:
        manifest = json.loads(
            (self.root / ".lks-sdd/project.json").read_text(encoding="utf-8")
        )

        def identity(binding_id: str, profile_id: str) -> tuple[dict, dict]:
            lock = {
                "binding_id": binding_id,
                "profile_id": profile_id,
                "profile_version": "1.0.0",
                "sha256": binding_id[-3:] * 21 + "0",
            }
            built = {
                "binding_id": binding_id,
                "profile_id": profile_id,
                "profile_version": "1.0.0",
            }
            return lock, built

        first_lock, first_built = identity(
            "BIND-001", "WEB-REACT-VITE-STATIC"
        )
        single = {
            "schema_version": "1.2",
            "profile_bindings": ["BIND-001"],
            "profile_locks": [first_lock],
            "profile_id": "WEB-REACT-VITE-STATIC",
            "profile_version": "1.0.0",
            "build_identity_material": {
                "profile_bindings": [first_built],
                "locks": [first_lock],
            },
        }
        self.assertEqual(
            evidence_profile_identity_errors(
                single, manifest, require_canonical_single=True
            ),
            [],
        )
        second_lock, second_built = identity(
            "BIND-002", "API-FASTAPI-STATELESS-OCI"
        )
        multiple = {
            "schema_version": "1.2",
            "profile_bindings": ["BIND-001", "BIND-002"],
            "profile_locks": [first_lock, second_lock],
            "profile_id": None,
            "profile_version": None,
            "build_identity_material": {
                "profile_bindings": [first_built, second_built],
                "locks": [first_lock, second_lock],
            },
        }
        self.assertEqual(
            evidence_profile_identity_errors(
                multiple, manifest, require_canonical_single=True
            ),
            [],
        )

    def test_verification_subject_mutation_matrix_is_fail_closed(self) -> None:
        baseline = verification_subject(self.root)
        checkpoint = self.root / "docs/lks-sdd/04-delivery/checkpoints/CKPT-001.md"
        checkpoint.write_text("administrative checkpoint\n", encoding="utf-8")
        administrative = verification_subject(self.root)
        self.assertTrue(compare_subject(baseline, administrative)["reusable"])
        mutations = [
            "src/app.py", "tests/test_app.py", "migrations/001.sql",
            "config/runtime.json", "Dockerfile", "package-lock.json",
            ".lks-sdd/profiles/BIND-001.lock.json",
            "docs/lks-sdd/04-delivery/tasks/TASK-001.md",
        ]
        for relative in mutations:
            path = self.root / relative
            original = path.read_bytes()
            path.write_bytes(original + b"\nmutation")
            changed = verification_subject(self.root)
            with self.subTest(relative=relative):
                comparison = compare_subject(administrative, changed)
                self.assertFalse(comparison["reusable"])
                self.assertIn(relative, comparison["technical_changes"])
            path.write_bytes(original)

    def test_administrative_evidence_projection_preserves_technical_subject(self) -> None:
        baseline = verification_subject(self.root)
        manifest_path = self.root / ".lks-sdd/project.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["last_verified_revision"] = "d" * 40
        manifest["verification"]["evidence_ids"] = ["EVID-002"]
        manifest["verification"]["reuse_attestation"] = {"subject_unchanged": True}
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        trace_path = self.root / "docs/lks-sdd/05-quality/traceability.md"
        trace_path.write_text(
            trace_path.read_text(encoding="utf-8").replace("| pending |", "| EVID-002 |"),
            encoding="utf-8",
            newline="\n",
        )
        current = verification_subject(self.root)
        comparison = compare_subject(baseline, current)
        self.assertTrue(comparison["reusable"])
        self.assertEqual(comparison["technical_changes"], [])

    def test_corrupt_cache_is_safe_miss(self) -> None:
        path = self.root / ".lks-sdd/cache/experience.json"
        path.parent.mkdir(parents=True)
        path.write_text("{broken", encoding="utf-8")
        self.assertIsNone(read_cache(path, "anything"))
        path.write_text(json.dumps({"schema": CACHE_SCHEMA, "entries": {"k": 1}}), encoding="utf-8")
        self.assertEqual(read_cache(path, "k"), 1)
        expected = verification_subject(self.root, use_cache=False)
        subject_cache = self.root / ".lks-sdd/cache/verification-subject.json"
        subject_cache.write_text("{broken", encoding="utf-8")
        recalculated = verification_subject(self.root, use_cache=True)
        self.assertEqual(
            recalculated["verification_subject_hash"],
            expected["verification_subject_hash"],
        )
        self.assertGreater(recalculated["instrumentation"]["cache_misses"], 0)

    def test_cached_and_uncached_results_are_semantically_identical(self) -> None:
        uncached = load_status(self.root, use_cache=False)
        cached = load_status(self.root, use_cache=True)
        repeated = load_status(self.root, use_cache=True)
        self.assertEqual(management_json(uncached), management_json(cached))
        self.assertEqual(management_json(cached), management_json(repeated))
        self.assertGreater(repeated["instrumentation"]["cache_hits"], 0)

        first_subject = verification_subject(self.root, use_cache=True)
        second_subject = verification_subject(self.root, use_cache=True)
        uncached_subject = verification_subject(self.root, use_cache=False)
        self.assertEqual(
            first_subject["verification_subject_hash"],
            second_subject["verification_subject_hash"],
        )
        self.assertEqual(
            second_subject["verification_subject_hash"],
            uncached_subject["verification_subject_hash"],
        )
        self.assertGreater(second_subject["instrumentation"]["cache_hits"], 0)

    def test_work_status_uses_one_visible_operation(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "lks_sdd.py"), "work", "status", str(self.root), "--task", "TASK-001", "--json"],
            check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["current_task"]["id"], "TASK-001")

    def test_work_resume_fails_closed_while_problem_is_active(self) -> None:
        before = tree_digest(self.root)
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "lks_sdd.py"), "work", "resume", str(self.root), "--task", "TASK-001", "--json"],
            check=False, text=True, encoding="utf-8", stdout=subprocess.PIPE,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(before, tree_digest(self.root))

    def test_problem_resolution_rolls_back_an_invalid_candidate(self) -> None:
        before = tree_digest(self.root)
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "lks_sdd.py"),
                "work",
                "resolve",
                str(self.root),
                "--task",
                "TASK-001",
                "--problem",
                "PROB-001",
                "--resolution",
                "resolved",
                "--cause",
                "Synthetic recorder restored",
                "--evidence",
                "EVID-901",
                "--actor",
                "fixture-authority",
                "--json",
            ],
            check=False,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["changed"])
        self.assertEqual(before, tree_digest(self.root))

    def test_problem_resolution_requires_correction_and_current_reverification(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v015-resolve-") as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            materialize_ready_project(root, "v015-resolve")
            authorize_implementation(root)
            code, _ = run_work(
                root, "start", "--increment", "INC-001", "--task", "TASK-001"
            )
            self.assertEqual(code, 0)
            code, _ = run_work(
                root,
                "review",
                "--task",
                "TASK-001",
                "--actor",
                "fixture-authority",
            )
            self.assertEqual(code, 0)
            code, _ = run_work(
                root,
                "block",
                "--task",
                "TASK-001",
                "--reason",
                "Synthetic recorder unavailable",
                "--actor",
                "fixture-authority",
            )
            self.assertEqual(code, 0)
            code, corrected = run_work(
                root,
                "correct",
                "--task",
                "TASK-001",
                "--problem",
                "PROB-001",
                "--cause",
                "Synthetic recorder restored and checked",
                "--actor",
                "fixture-authority",
            )
            self.assertEqual(code, 0, corrected)
            self.assertEqual(corrected["status"], "pending-reverification")
            record_synthetic_verified_evidence(root)
            code, payload = run_work(
                root,
                "resolve",
                "--task",
                "TASK-001",
                "--problem",
                "PROB-001",
                "--resolution",
                "resolved",
                "--cause",
                "Synthetic recorder restored and checked",
                "--evidence",
                "EVID-001",
                "--actor",
                "fixture-authority",
            )
            self.assertEqual(code, 0, payload)
            self.assertEqual(payload["status"], "resolved")
            self.assertTrue(payload["changed"])
            self.assertEqual(payload["administrative_operations"], 1)
            self.assertEqual(
                payload["summary"]["current_task"]["development"],
                "Código terminado; revisión en curso",
            )
            self.assertIsNone(
                payload["summary"]["current_task"]["active_blocker"]
            )
            audit = load_status(root, task_id="TASK-001")["audit"]
            self.assertEqual(audit["task"]["Workflow state"], "in-review")
            self.assertEqual(audit["problems"]["active"], [])

    def test_public_fast_path_completes_verified_task_with_one_operation_per_hito(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v015-complete-") as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            materialize_ready_project(root, "v015-complete")
            authorize_implementation(root)
            code, started = run_work(
                root, "start", "--increment", "INC-001", "--task", "TASK-001"
            )
            self.assertEqual(code, 0, started)
            code, reviewed = run_work(
                root,
                "review",
                "--task",
                "TASK-001",
                "--actor",
                "fixture-authority",
            )
            self.assertEqual(code, 0, reviewed)
            record_synthetic_verified_evidence(root)
            code, completed = run_work(
                root,
                "complete",
                "--task",
                "TASK-001",
                "--actor",
                "fixture-authority",
            )
            self.assertEqual(code, 0, completed)
            for result in (started, reviewed, completed):
                self.assertEqual(result["administrative_operations"], 1)
                self.assertEqual(result["human_confirmations_required"], 0)
            self.assertEqual(completed["status"], "completed")
            self.assertEqual(completed["summary"]["project"]["verified"], 1)
            self.assertEqual(
                completed["summary"]["current_task"]["verification"],
                "Verificación superada",
            )
            self.assertTrue(
                (root / completed["technical_reference"].replace(
                    "CKPT-", "docs/lks-sdd/04-delivery/checkpoints/CKPT-"
                )).with_suffix(".md").is_file()
            )

    def test_public_fast_path_starts_authorized_task_in_one_operation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v015-fast-path-") as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            materialize_ready_project(root, "v015-fast-path")
            authorize_implementation(root)
            started = time.perf_counter()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "lks_sdd.py"),
                    "work",
                    "start",
                    str(root),
                    "--increment",
                    "INC-001",
                    "--task",
                    "TASK-001",
                    "--actor",
                    "fixture-authority",
                    "--json",
                ],
                check=False,
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            duration = time.perf_counter() - started
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "started")
            self.assertEqual(payload["administrative_operations"], 1)
            self.assertEqual(payload["human_confirmations_required"], 0)
            self.assertLess(duration, 8.0)

    def test_public_benchmark_meets_status_transition_and_reduction_budgets(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "benchmark_experience.py"),
                "--iterations",
                "1",
                "--json",
            ],
            check=False,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["passed"])
        self.assertTrue(payload["status_management"]["passed"])
        self.assertTrue(payload["local_composed_transition"]["passed"])
        self.assertGreaterEqual(
            payload["administrative_cycle"]["command_reduction_percent"], 50.0
        )


PRODUCT_EXPERIENCE_SHARD_BOUNDARY = 7
PRODUCT_EXPERIENCE_SECOND_BOUNDARY = 14


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    """Keep the first deterministic shard below the fast module budget."""
    del standard_tests, pattern
    names = loader.getTestCaseNames(ProductExperienceV015Tests)
    return unittest.TestSuite(
        ProductExperienceV015Tests(name)
        for name in names[:PRODUCT_EXPERIENCE_SHARD_BOUNDARY]
    )


if __name__ == "__main__":
    unittest.main()
