from __future__ import annotations

import importlib.util
import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "tests"))

from delivery_engine import (  # noqa: E402
    load_delivery_evidence,
    repository_revision,
    validate_delivery_contract,
)
from eval_support import run_json  # noqa: E402
from jira_reporting_engine import _source_exists  # noqa: E402
from test_jira_reporting_v15 import (  # noqa: E402
    TRACKING_SCRIPT,
    _prepare_started_project,
)


VERIFY_SCRIPT = (
    PLUGIN_ROOT / "skills/lks-sdd-verify/scripts/run_verification.py"
)
TASKS_SCRIPT = PLUGIN_ROOT / "scripts/manage_tasks.py"


def _load_verification_module():
    spec = importlib.util.spec_from_file_location(
        "lks_sdd_incremental_verification", VERIFY_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _delivery_contract() -> dict:
    return {
        "tasks": {
            "TASK-001": {
                "Release": "REL-001",
                "Unit": "UNIT-001",
                "Profile binding": "BIND-001",
            },
            "TASK-002": {
                "Release": "REL-001",
                "Unit": "UNIT-002",
                "Profile binding": "BIND-002",
            },
        },
        "task_details": {
            "TASK-001": {
                "definition": [{
                    "In scope": "Backend API and database transaction",
                    "Out of scope": "Frontend and browser interface",
                    "Requirements": "FR-001",
                    "Acceptance": "AC-001",
                    "Required capabilities": "CAP-API-CONTRACT, CAP-DATA-POSTGRES",
                    "Technical gates": "GATE-API-TEST",
                }]
            },
            "TASK-002": {
                "definition": [{
                    "In scope": "Frontend browser screen",
                    "Out of scope": "Backend API",
                    "Requirements": "FR-002, UX-001",
                    "Acceptance": "AC-002, VIS-001",
                    "Required capabilities": "CAP-FRONTEND-QUALITY, CAP-BROWSER-PLAYWRIGHT",
                    "Technical gates": "GATE-FRONTEND-TEST, GATE-BROWSER-SMOKE",
                }]
            },
        },
        "units": {
            "UNIT-001": {
                "Component": "Backend API",
                "Responsibility": "Persist records",
                "Runtime boundary": "OCI service",
                "Interfaces": "HTTP API",
            },
            "UNIT-002": {
                "Component": "Frontend SPA",
                "Responsibility": "Human-facing interface",
                "Runtime boundary": "Browser",
                "Interfaces": "UI",
            },
        },
        "bindings": {
            "BIND-001": {"profile_id": "API-FASTAPI-STATELESS-OCI"},
            "BIND-002": {"profile_id": "WEB-REACT-VITE-STATIC"},
        },
    }


class SliceVisualApplicabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_verification_module()

    def _applicability(self, tasks: list[str]) -> dict:
        with mock.patch.object(
            self.module, "_interface_is_applicable", return_value=True
        ):
            return self.module._visual_applicability(
                Path("."), {}, "INC-001", tasks, _delivery_contract()
            )

    def test_backend_task_in_interface_increment_is_not_applicable(self) -> None:
        contract = _delivery_contract()
        contract["units"]["UNIT-001"]["Interfaces"] = "HTTP API and shared browser UI"
        contract["bindings"]["BIND-001"]["profile_id"] = (
            "WEB-FASTAPI-REACT-KEYCLOAK-PG"
        )
        with mock.patch.object(
            self.module, "_interface_is_applicable", return_value=True
        ):
            result = self.module._visual_applicability(
                Path("."), {}, "INC-001", ["TASK-001"], contract
            )
        self.assertEqual(result["status"], "not-applicable")
        self.assertEqual(result["scope"], "task-slice")
        self.assertIn("TASK-001", result["reason"])
        self.assertEqual(
            self.module._binding_ids_for_tasks(["TASK-001"], contract),
            ["BIND-001"],
        )

    def test_frontend_and_mixed_slices_require_visual_review(self) -> None:
        frontend = self._applicability(["TASK-002"])
        mixed = self._applicability(["TASK-001", "TASK-002"])
        self.assertEqual(frontend["status"], "applicable")
        self.assertEqual(mixed["status"], "applicable")
        self.assertIn("UX-001", frontend["reason"])

    def test_complete_interface_release_requires_visual_review(self) -> None:
        result = self._applicability(["TASK-001", "TASK-002"])
        self.assertEqual(result["status"], "applicable")
        self.assertEqual(result["scope"], "release")

    def test_ux_or_vis_reference_can_never_be_not_applicable(self) -> None:
        contract = _delivery_contract()
        contract["task_details"]["TASK-001"]["definition"][0]["Requirements"] += ", UX-099"
        with mock.patch.object(
            self.module, "_interface_is_applicable", return_value=True
        ):
            result = self.module._visual_applicability(
                Path("."), {}, "INC-001", ["TASK-001"], contract
            )
        self.assertEqual(result["status"], "applicable")


class DeterministicBuildIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_verification_module()

    def _material(self, **changes):
        revision = {
            "revision": changes.get("revision", "a" * 40),
            "tree_id": changes.get("tree_id", "b" * 40),
            "tree_sha256": changes.get("tree_sha256", "c" * 64),
        }
        locks = [{
            "binding_id": "BIND-001",
            "profile_id": "API-FASTAPI-STATELESS-OCI",
            "profile_version": "1.0.0",
            "sha256": changes.get("lock", "d" * 64),
            "diagnostic": changes.get("diagnostic", "ignored"),
        }]
        bindings = [{
            "binding_id": "BIND-001",
            "unit_id": "UNIT-001",
            "unit_path": changes.get("unit_path", "apps\\backend"),
            "profile_id": "API-FASTAPI-STATELESS-OCI",
            "profile_scope": "deployable",
            "selection_decision": "ADR-001",
        }]
        artifacts = [changes.get("artifact", "sha256:" + "e" * 64)]
        return self.module._build_identity_material(
            revision, locks, bindings, artifacts
        )

    def test_duration_pid_logs_docker_name_and_collection_order_do_not_change_build(self) -> None:
        first = self._material(diagnostic="duration=1 pid=10 compose=alpha stdout=A")
        second = self._material(diagnostic="duration=99 pid=999 compose=beta stderr=B")
        second["locks"] = list(reversed(second["locks"]))
        second["artifact_digests"] = list(reversed(second["artifact_digests"]))
        self.assertEqual(self.module._build_id(first), self.module._build_id(second))
        self.assertNotIn("diagnostic", json.dumps(first))

    def test_revision_tree_lock_and_artifact_mutations_change_build(self) -> None:
        baseline = self.module._build_id(self._material())
        mutations = [
            self._material(revision="f" * 40),
            self._material(tree_sha256="f" * 64),
            self._material(lock="f" * 64),
            self._material(artifact="sha256:" + "f" * 64),
        ]
        self.assertTrue(all(self.module._build_id(item) != baseline for item in mutations))

    def test_windows_and_posix_unit_paths_hash_identically(self) -> None:
        windows = self.module._build_id(self._material(unit_path="apps\\backend"))
        posix = self.module._build_id(self._material(unit_path="apps/backend"))
        self.assertEqual(windows, posix)


class G4TemplateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_verification_module()

    def test_g3_materializes_g4_without_circular_build_dependency(self) -> None:
        revision = {
            "revision": "a" * 40,
            "tree_id": "b" * 40,
            "tree_sha256": "c" * 64,
        }
        build_id = "build-sha256:" + "d" * 64
        template = self.module._delivery_template(
            release="REL-001",
            environment="ENV-001",
            revision=revision,
            build_id=build_id,
            artifact_digests=["sha256:" + "e" * 64],
            technical_run_id="run-sha256:" + "f" * 64,
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "g4.json"
            path.write_text(json.dumps(template), encoding="utf-8")
            _, draft_errors = load_delivery_evidence(path)
            self.assertTrue(any("complete" in item for item in draft_errors))
            template["evidence_state"] = "complete"
            for key in ("promotion", "smoke", "observability", "recovery", "authorization"):
                template[key]["status"] = "passed"
                template[key]["recorded_at"] = "2026-08-27T10:00:00Z"
                template[key]["reference"] = f"evidence:{key}:001"
            template["authorization"]["authority"] = "release-owner"
            path.write_text(json.dumps(template), encoding="utf-8")
            value, errors = load_delivery_evidence(path)
        self.assertEqual(errors, [])
        self.assertEqual(value["build_id"], build_id)
        self.assertEqual(value["tree_sha256"], revision["tree_sha256"])

    def test_git_revision_and_tree_stay_fixed_while_only_g4_is_completed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "fixture@lks.invalid"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "LKS-SDD fixture"],
                cwd=root,
                check=True,
            )
            (root / "source.txt").write_text("stable\n", encoding="utf-8")
            subprocess.run(["git", "add", "source.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=root, check=True)
            before = repository_revision(root)
            relative = "docs/lks-sdd/evidence/delivery/REL-001-ENV-001.json"
            evidence = root / relative
            evidence.parent.mkdir(parents=True)
            evidence.write_text("{}\n", encoding="utf-8")
            during_g4 = repository_revision(root)
            self.assertEqual(before["revision"], during_g4["revision"])
            self.assertEqual(before["tree_id"], during_g4["tree_id"])
            self.assertEqual(before["tree_sha256"], during_g4["tree_sha256"])
            self.assertEqual(during_g4["dirty_paths"], [relative])
            self.assertFalse(
                self.module._has_unallowed_dirty_paths(during_g4, {relative})
            )
            (root / "source.txt").write_text("changed\n", encoding="utf-8")
            self.assertTrue(
                self.module._has_unallowed_dirty_paths(
                    repository_revision(root), {relative}
                )
            )

    def test_runner_g3_template_then_g4_finalization_reuses_build_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project(root, "g4-two-phase")
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["implementation"]["status"] = "completed"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            relative = Path("docs/lks-sdd/evidence/delivery/REL-001-ENV-001.json")
            args = argparse.Namespace(
                project_root=root,
                increment="INC-001",
                task=None,
                execution_id=None,
                plan=False,
                execute=True,
                authorize=True,
                containers=True,
                environment="ENV-001",
                delivery_evidence=None,
                materialize_delivery_template=relative,
                visual_evidence=None,
                record_evidence=None,
            )
            passed = lambda check, env: {
                "name": check["name"],
                "gate_id": check["gate_id"],
                "binding_id": check["binding_id"],
                "status": "passed",
                "duration_seconds": 1.0,
                "stdout": "first run",
            }
            with mock.patch.object(
                self.module, "_execute_profile_command", side_effect=passed
            ), mock.patch.object(self.module, "_cleanup_profile_compositions", return_value=[]):
                first_code, first = self.module.run(args)
            self.assertEqual(first_code, 0, first)
            self.assertEqual(first["classification"], "verified-with-reservations")
            delivery_path = root / relative
            completed = json.loads(delivery_path.read_text(encoding="utf-8"))
            completed["evidence_state"] = "complete"
            for key in ("promotion", "smoke", "observability", "recovery", "authorization"):
                completed[key]["status"] = "passed"
                completed[key]["recorded_at"] = "2026-08-27T10:00:00Z"
                completed[key]["reference"] = f"evidence:{key}:001"
            completed["authorization"]["authority"] = "release-owner"
            delivery_path.write_text(
                json.dumps(completed, indent=2) + "\n", encoding="utf-8", newline="\n"
            )
            args.materialize_delivery_template = None
            args.delivery_evidence = relative
            passed_second = lambda check, env: {
                "name": check["name"],
                "gate_id": check["gate_id"],
                "binding_id": check["binding_id"],
                "status": "passed",
                "duration_seconds": 99.0,
                "stderr": "second run with another diagnostic",
            }
            with mock.patch.object(
                self.module, "_execute_profile_command", side_effect=passed_second
            ), mock.patch.object(self.module, "_cleanup_profile_compositions", return_value=[]):
                second_code, second = self.module.run(args)
            self.assertEqual(second_code, 0, second)
            self.assertEqual(second["classification"], "verified")
            self.assertEqual(first["build_id"], second["build_id"])
            self.assertNotEqual(first["verification_run_id"], second["verification_run_id"])
            mismatches = {
                "revision": "f" * 40,
                "tree_id": "f" * 40,
                "tree_sha256": "f" * 64,
                "build_id": "build-sha256:" + "f" * 64,
                "artifact_digests": ["sha256:" + "f" * 64],
            }
            for field, changed in mismatches.items():
                with self.subTest(field=field):
                    invalid = json.loads(json.dumps(completed))
                    invalid[field] = changed
                    delivery_path.write_text(
                        json.dumps(invalid, indent=2) + "\n",
                        encoding="utf-8",
                        newline="\n",
                    )
                    with mock.patch.object(
                        self.module,
                        "_execute_profile_command",
                        side_effect=passed_second,
                    ), mock.patch.object(
                        self.module, "_cleanup_profile_compositions", return_value=[]
                    ):
                        code, result = self.module.run(args)
                    self.assertEqual(code, 3, result)
                    self.assertEqual(result["classification"], "not-verified")


class JiraCanonicalSourceRegressionTests(unittest.TestCase):
    def test_generated_checkpoint_is_immediately_accepted_with_quoted_or_plain_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project(root, "checkpoint-jira")
            checkpoint = root / "docs/lks-sdd/04-delivery/checkpoints/CKPT-001.md"
            original = checkpoint.read_text(encoding="utf-8")
            for quoted in (False, True):
                checkpoint.write_text(
                    original.replace(
                        "artifact_id: ART-CKPT-001",
                        'artifact_id: "ART-CKPT-001"' if quoted else "artifact_id: ART-CKPT-001",
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
                _, preview = run_json(
                    TRACKING_SCRIPT,
                    "preview-event",
                    str(root),
                    "--task", "TASK-001",
                    "--source-ref", "CKPT-001",
                    "--event-kind", "started",
                )
                self.assertIn("CKPT-001", preview["operations"][0]["payload"]["body"])

    def test_checkpoint_link_like_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project(root, "checkpoint-link")
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            with mock.patch("jira_reporting_engine._is_link_like", return_value=True):
                self.assertFalse(
                    _source_exists(root, manifest, "TASK-001", "CKPT-001", {})
                )

    def test_checkpoint_from_other_task_or_execution_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project(root, "checkpoint-foreign")
            checkpoint = root / "docs/lks-sdd/04-delivery/checkpoints/CKPT-001.md"
            original = checkpoint.read_text(encoding="utf-8")
            for old, new in (("| EXEC-001 |", "| EXEC-999 |"), ("| TASK-001 |", "| TASK-999 |")):
                checkpoint.write_text(original.replace(old, new, 1), encoding="utf-8", newline="\n")
                code, payload = run_json(
                    TRACKING_SCRIPT,
                    "preview-event",
                    str(root),
                    "--task", "TASK-001",
                    "--source-ref", "CKPT-001",
                    "--event-kind", "started",
                    expected_codes={2},
                )
                self.assertEqual(code, 2)
                self.assertIn("fuente canónica", payload["error"])

    def test_block_transition_problem_is_immediately_accepted_and_closed_foreign_missing_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project(root, "problem-jira")
            transition_args = [
                str(root), "transition", "--task", "TASK-001", "--to", "blocked",
                "--reason", "Synthetic dependency unavailable", "--actor", "fixture-owner",
                "--date", "2026-08-27", "--blocker", "Synthetic dependency",
            ]
            _, preview = run_json(TASKS_SCRIPT, *transition_args, "--preview")
            run_json(
                TASKS_SCRIPT, *transition_args, "--apply", "--authorize",
                "--preview-hash", preview["preview_hash"],
            )
            _, event = run_json(
                TRACKING_SCRIPT, "preview-event", str(root),
                "--task", "TASK-001", "--source-ref", "PROB-001",
                "--event-kind", "blocked",
            )
            self.assertIn("PROB-001", event["operations"][0]["payload"]["body"])
            self.assertRegex(event["event_marker"], r"^LKS-SDD-EVENT: .+; [a-f0-9]{16}$")

            manifest = json.loads((root / ".lks-sdd/project.json").read_text(encoding="utf-8"))
            details = {
                "identity": [{"Task": "TASK-001"}],
                "problems": [{"ID": "PROB-001", "State": "resolved"}],
            }
            self.assertFalse(_source_exists(root, manifest, "TASK-001", "PROB-001", details))
            self.assertFalse(_source_exists(root, manifest, "TASK-002", "PROB-001", {
                "identity": [{"Task": "TASK-001"}],
                "problems": [{"ID": "PROB-001", "State": "open"}],
            }))
            self.assertFalse(_source_exists(root, manifest, "TASK-001", "PROB-999", details))


class ExistingSchema15CompatibilityTests(unittest.TestCase):
    def test_existing_schema_15_project_remains_valid_without_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project(root, "schema-15-compatible")
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["schema_version"], "1.5")
            delivery = validate_delivery_contract(root, manifest)
            self.assertEqual(delivery["errors"], [])
            task = delivery["task_details"]["TASK-001"]
            self.assertEqual(task["problems"], task["issues"])


if __name__ == "__main__":
    unittest.main()
