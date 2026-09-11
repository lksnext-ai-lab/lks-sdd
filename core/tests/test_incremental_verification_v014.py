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
from eval_support import (  # noqa: E402
    IMPLEMENT_SCRIPT,
    VALIDATE_SCRIPT,
    authorize_implementation,
    confirm_planning,
    initialize,
    materialize_ready_increment,
    run_json,
)
from jira_reporting_engine import _source_exists  # noqa: E402
from test_jira_reporting_v15 import (  # noqa: E402
    TRACKING_SCRIPT,
    _prepare_started_project,
)
from test_task_tracking_v14 import _configure, _manifest, _record  # noqa: E402


VERIFY_SCRIPT = (
    PLUGIN_ROOT / "skills/lks-sdd-verify/scripts/run_verification.py"
)
TASKS_SCRIPT = PLUGIN_ROOT / "scripts/manage_tasks.py"
TRACEABILITY_SCRIPT = PLUGIN_ROOT / "scripts/check_traceability.py"


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


def _prepare_started_project_with_empty_evidence(
    root: Path, project_id: str
) -> dict:
    initialize(root, project_id)
    materialize_ready_increment(root, confirm_plan=False)
    traceability = root / "docs/lks-sdd/05-quality/traceability.md"
    traceability.write_text(
        traceability.read_text(encoding="utf-8").replace(
            "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | none |",
            "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 |  |",
        ),
        encoding="utf-8",
        newline="\n",
    )
    confirm_planning(root)
    _configure(
        root,
        "jira-hybrid",
        decision="ADR-001",
        reporting_scope="milestone-reporting",
        coordination_gate="advisory",
    )
    from task_tracking_engine import build_projection_preview  # noqa: PLC0415

    projection = build_projection_preview(root, _manifest(root), ["TASK-001"])
    _record(
        root,
        projection,
        result="succeeded",
        external_id="10001",
        external_key="SYN-1",
    )
    authorize_implementation(root)
    _, preview = run_json(
        IMPLEMENT_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "--task",
        "TASK-001",
        "--dry-run",
    )
    _, implementation = run_json(
        IMPLEMENT_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "--task",
        "TASK-001",
        "--apply",
        "--authorize",
        "--preview-hash",
        preview["preview_hash"],
    )
    return implementation


def _append_table_row(path: Path, header_prefix: str, row: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith(header_prefix):
            cursor = index + 2
            while cursor < len(lines) and lines[cursor].startswith("|"):
                cursor += 1
            lines.insert(cursor, row)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            return
    raise AssertionError(f"Missing table {header_prefix} in {path}")


def _prepare_backend_slice_in_multibinding_project(root: Path) -> dict:
    initialize(root, "evidence-contract-0142")
    materialize_ready_increment(root, confirm_plan=False)
    docs = root / "docs/lks-sdd"
    manifest_path = root / ".lks-sdd/project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["active_task"] = None
    manifest["technology"]["selected_profile"] = None
    manifest["technology"]["selection_decision"] = None
    manifest["technology"]["profile_bindings"].append(
        {
            "binding_id": "BIND-002",
            "unit_id": "UNIT-002",
            "unit_path": "web",
            "profile_id": "WEB-REACT-VITE-STATIC",
            "profile_scope": "deployable",
            "selection_decision": "ADR-003",
            "lock_path": ".lks-sdd/profiles/BIND-002.lock.json",
            "state": "confirmed",
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _append_table_row(
        docs / "03-solution/solution-overview.md",
        "| ID | State | Decision",
        "| ADR-003 | confirmed | Select WEB-REACT-VITE-STATIC for UNIT-002 and BIND-002. | FR-001 | Limited to the static web deployable |",
    )
    _append_table_row(
        docs / "03-solution/architecture.md",
        "| Unit | State | Component",
        "| UNIT-002 | confirmed | Static frontend SPA | Human-facing browser interface | Browser | UI over HTTP | none: client state only | FR-001 | BIND-002 |",
    )
    _append_table_row(
        docs / "04-delivery/tasks.md",
        "| ID | Plan | Title",
        "| TASK-002 | PLAN-001 | Implement synthetic frontend | REL-001 | INC-001 | UNIT-002 | BIND-002 | ready | on-track | 0 | not-applicable: no prerequisite task | none | fixture-owner | ./tasks/TASK-002.md | 2026-08-19 |",
    )
    plans = docs / "04-delivery/plans.md"
    plans.write_text(
        plans.read_text(encoding="utf-8").replace(
            "| REL-001 | active | 0.1.0 | PLAN-001 | 2026-08-19 | continuous stream | ENV-001 | TASK-001 | pending | pending | pending: G3/G4 not executed |",
            "| REL-001 | active | 0.1.0 | PLAN-001 | 2026-08-19 | continuous stream | ENV-001 | TASK-001, TASK-002 | pending | pending | pending: G3/G4 not executed |",
        ),
        encoding="utf-8",
        newline="\n",
    )
    coverage = docs / "04-delivery/planning-coverage.md"
    coverage.write_text(
        coverage.read_text(encoding="utf-8").replace(
            "| REL-001 | INC-001 | FR-001, AC-001, ADR-001, TEST-001 | TASK-001 | not-applicable: single-task release | Implement and jointly verify the complete synthetic increment | All active items are owned by the only executable task |",
            "| REL-001 | INC-001 | FR-001, AC-001, ADR-001, TEST-001 | TASK-001 | TASK-002 | Keep backend ownership while the frontend remains a future slice | TASK-001 owns FR-001 and TASK-002 is independently bound |",
        ),
        encoding="utf-8",
        newline="\n",
    )
    detail_1 = docs / "04-delivery/tasks/TASK-001.md"
    detail_2 = docs / "04-delivery/tasks/TASK-002.md"
    task_text = detail_1.read_text(encoding="utf-8")
    task_text = task_text.replace("ART-TASK-001", "ART-TASK-002")
    task_text = task_text.replace("TASK-001", "TASK-002")
    task_text = task_text.replace("UNIT-001", "UNIT-002")
    task_text = task_text.replace("BIND-001", "BIND-002")
    task_text = task_text.replace(
        "Implement synthetic acknowledgement",
        "Implement synthetic frontend browser interface",
    )
    task_text = task_text.replace(
        "CAP-API-CONTRACT, CAP-OCI-RUNTIME",
        "CAP-FRONTEND-QUALITY, CAP-BROWSER-PLAYWRIGHT",
    )
    task_text = task_text.replace(
        "GATE-API-TEST, GATE-API-OPENAPI, GATE-OCI-BUILD",
        "GATE-FRONTEND-TEST, GATE-FRONTEND-BUILD, GATE-BROWSER-SMOKE",
    )
    detail_2.write_text(task_text, encoding="utf-8", newline="\n")
    trace = docs / "05-quality/traceability.md"
    trace.write_text(
        trace.read_text(encoding="utf-8").replace(
            "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | none |",
            "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 |  |",
        ),
        encoding="utf-8",
        newline="\n",
    )
    confirm_planning(root)
    _configure(root, "repository-only")
    authorize_implementation(root, task_ids=("TASK-001",))
    _, preview = run_json(
        IMPLEMENT_SCRIPT,
        str(root),
        "--increment", "INC-001",
        "--task", "TASK-001",
        "--dry-run",
    )
    _, implementation = run_json(
        IMPLEMENT_SCRIPT,
        str(root),
        "--increment", "INC-001",
        "--task", "TASK-001",
        "--apply",
        "--authorize",
        "--preview-hash", preview["preview_hash"],
    )
    return implementation


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
                "problems": [{"ID": "PROB-001", "State": "active"}],
            }))
            self.assertFalse(_source_exists(root, manifest, "TASK-001", "PROB-999", details))


class EmptyTraceabilityEvidenceRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_verification_module()

    @staticmethod
    def _passed(check, env):
        return {
            "name": check["name"],
            "gate_id": check["gate_id"],
            "binding_id": check["binding_id"],
            "status": "passed",
            "duration_seconds": 1.0,
        }

    def test_empty_schema_15_evidence_completes_g3_g4_and_records_consistently(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            implementation = _prepare_started_project_with_empty_evidence(
                root, "empty-evidence-schema-15"
            )
            self.assertEqual(implementation["execution_id"], "EXEC-001")
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], "1.5")
            manifest["implementation"]["status"] = "completed"
            next(
                item
                for item in manifest["executions"]
                if item["execution_id"] == "EXEC-001"
            )["status"] = "completed"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )

            _, validation = run_json(VALIDATE_SCRIPT, str(root))
            _, preimplementation = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--phase",
                "preimplementation",
            )
            self.assertTrue(validation["valid"], validation)
            self.assertTrue(preimplementation["valid"], preimplementation)

            relative = Path("docs/lks-sdd/evidence/delivery/REL-001-ENV-001.json")
            args = argparse.Namespace(
                project_root=root,
                increment="INC-001",
                task=["TASK-001"],
                execution_id="EXEC-001",
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
            with mock.patch.object(
                self.module, "_execute_profile_command", side_effect=self._passed
            ), mock.patch.object(
                self.module, "_cleanup_profile_compositions", return_value=[]
            ):
                g3_code, g3 = self.module.run(args)
            self.assertEqual(g3_code, 0, g3)
            self.assertEqual(g3["classification"], "verified-with-reservations")

            delivery_path = root / relative
            delivery = json.loads(delivery_path.read_text(encoding="utf-8"))
            delivery["evidence_state"] = "complete"
            for key in ("promotion", "smoke", "observability", "recovery", "authorization"):
                delivery[key]["status"] = "passed"
                delivery[key]["recorded_at"] = "2026-08-28T10:00:00Z"
                delivery[key]["reference"] = f"evidence:{key}:001"
            delivery["authorization"]["authority"] = "release-owner"
            delivery_path.write_text(
                json.dumps(delivery, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            args.materialize_delivery_template = None
            args.delivery_evidence = relative
            args.record_evidence = "EVID-001"
            with mock.patch.object(
                self.module, "_execute_profile_command", side_effect=self._passed
            ), mock.patch.object(
                self.module, "_cleanup_profile_compositions", return_value=[]
            ):
                g4_code, g4 = self.module.run(args)

            self.assertEqual(g4_code, 0, g4)
            self.assertEqual(g4["classification"], "verified")
            self.assertTrue(g4["evidence_recorded"])
            self.assertEqual(g3["build_id"], g4["build_id"])
            evidence_path = root / "docs/lks-sdd/evidence/EVID-001.json"
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            recorded_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            execution = next(
                item
                for item in recorded_manifest["executions"]
                if item["execution_id"] == "EXEC-001"
            )
            traceability = (
                root / "docs/lks-sdd/05-quality/traceability.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | EVID-001 |",
                traceability,
            )
            self.assertEqual(evidence["evidence_id"], "EVID-001")
            self.assertEqual(evidence["execution_id"], "EXEC-001")
            self.assertEqual(evidence["build_id"], g4["build_id"])
            self.assertEqual(
                recorded_manifest["verification"]["evidence_ids"], ["EVID-001"]
            )
            self.assertEqual(execution["evidence_ids"], ["EVID-001"])
            self.assertEqual(
                recorded_manifest["last_delivery"]["evidence_ids"], ["EVID-001"]
            )
            _, verification = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--phase",
                "verification",
            )
            self.assertTrue(verification["valid"], verification)

    def test_blank_variants_share_pending_contract(self) -> None:
        for value in ("", " ", "\t", "none", "Pending", "not-run"):
            with self.subTest(value=value):
                self.assertTrue(
                    self.module.is_pending_traceability_evidence(value)
                )

    def test_existing_evidence_and_other_increment_are_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "traceability.md"
            original = (
                "| Requirement | Acceptance | Decision | Increment | Test | Evidence |\n"
                "|---|---|---|---|---|---|\n"
                "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | EVID-777 |\n"
                "| FR-002 | AC-002 | ADR-002 | INC-002 | TEST-002 |   |\n"
            ).encode("utf-8")
            path.write_bytes(original)
            with self.assertRaises(self.module.VerificationError):
                self.module._updated_traceability(path, "INC-001", "EVID-001")
            self.assertEqual(path.read_bytes(), original)

            path.write_bytes(original.replace(b"EVID-777", b"         "))
            _, updated = self.module._updated_traceability(
                path, "INC-001", "EVID-001"
            )
            text = updated.decode("utf-8")
            self.assertIn("| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | EVID-001 |", text)
            self.assertIn("| FR-002 | AC-002 | ADR-002 | INC-002 | TEST-002 |   |", text)

    def test_malformed_table_fails_without_mutating_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "traceability.md"
            original = (
                "| Requirement | Acceptance | Decision | Increment | Test | Evidence |\n"
                "|---|---|---|---|---|---|\n"
                "| FR-001 | AC-001 | INC-001 | TEST-001 | |\n"
            ).encode("utf-8")
            path.write_bytes(original)
            with self.assertRaises(self.module.VerificationError):
                self.module._updated_traceability(path, "INC-001", "EVID-001")
            self.assertEqual(path.read_bytes(), original)

    def test_record_rolls_back_evidence_traceability_and_manifest_together(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project_with_empty_evidence(root, "atomic-evidence")
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["implementation"]["status"] = "completed"
            next(
                item
                for item in manifest["executions"]
                if item["execution_id"] == "EXEC-001"
            )["status"] = "completed"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            trace_path = root / "docs/lks-sdd/05-quality/traceability.md"
            original_manifest = manifest_path.read_bytes()
            original_trace = trace_path.read_bytes()
            args = argparse.Namespace(
                project_root=root,
                increment="INC-001",
                task=["TASK-001"],
                execution_id="EXEC-001",
                plan=False,
                execute=True,
                authorize=True,
                containers=True,
                environment="ENV-001",
                delivery_evidence=None,
                materialize_delivery_template=None,
                visual_evidence=None,
                record_evidence="EVID-001",
            )
            real_replace = self.module.os.replace
            replace_calls = 0

            def fail_manifest_replace(source, target):
                nonlocal replace_calls
                replace_calls += 1
                if replace_calls == 2:
                    raise OSError("synthetic manifest replace failure")
                return real_replace(source, target)

            with mock.patch.object(
                self.module, "_execute_profile_command", side_effect=self._passed
            ), mock.patch.object(
                self.module, "_cleanup_profile_compositions", return_value=[]
            ), mock.patch.object(
                self.module.os, "replace", side_effect=fail_manifest_replace
            ), self.assertRaises(OSError):
                self.module.run(args)

            self.assertEqual(manifest_path.read_bytes(), original_manifest)
            self.assertEqual(trace_path.read_bytes(), original_trace)
            self.assertFalse(
                (root / "docs/lks-sdd/evidence/EVID-001.json").exists()
            )
            self.assertFalse(list(root.rglob("*.lks-sdd.tmp")))


class EvidenceContractV0142RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_verification_module()

    @staticmethod
    def _passed(check, env):
        return {
            "name": check["name"],
            "gate_id": check["gate_id"],
            "binding_id": check["binding_id"],
            "status": "passed",
            "duration_seconds": 1.0,
        }

    @staticmethod
    def _complete_execution(root: Path) -> None:
        manifest_path = root / ".lks-sdd/project.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["implementation"]["status"] = "completed"
        next(
            item
            for item in manifest["executions"]
            if item["execution_id"] == "EXEC-001"
        )["status"] = "completed"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    @staticmethod
    def _args(root: Path, delivery: Path | None = None) -> argparse.Namespace:
        return argparse.Namespace(
            project_root=root,
            increment="INC-001",
            task=["TASK-001"],
            execution_id="EXEC-001",
            plan=False,
            execute=True,
            authorize=True,
            containers=True,
            environment="ENV-001",
            delivery_evidence=delivery,
            materialize_delivery_template=None,
            visual_evidence=None,
            record_evidence=None,
        )

    @staticmethod
    def _complete_delivery(path: Path) -> None:
        delivery = json.loads(path.read_text(encoding="utf-8"))
        delivery["evidence_state"] = "complete"
        for key in ("promotion", "smoke", "observability", "recovery", "authorization"):
            delivery[key]["status"] = "passed"
            delivery[key]["recorded_at"] = "2026-08-28T12:00:00Z"
            delivery[key]["reference"] = f"evidence:{key}:0142"
        delivery["authorization"]["authority"] = "release-owner"
        path.write_text(
            json.dumps(delivery, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def test_multi_binding_top_level_identity_is_omitted_and_legacy_12_is_readable(self) -> None:
        bindings = [
            {"binding_id": "BIND-001", "profile_id": "API-FASTAPI-STATELESS-OCI", "profile_version": "1.0.0"},
            {"binding_id": "BIND-002", "profile_id": "WEB-REACT-VITE-STATIC", "profile_version": "2.0.0"},
        ]
        self.assertEqual(
            self.module.canonical_top_level_profile_identity(bindings), {}
        )
        self.assertEqual(
            self.module.canonical_top_level_profile_identity(bindings[:1]),
            {
                "profile_id": "API-FASTAPI-STATELESS-OCI",
                "profile_version": "1.0.0",
            },
        )
        material = {
            "identity_contract": "lks-sdd-build-1.0",
            "revision": "a" * 40,
            "tree_id": "b" * 40,
            "tree_sha256": "c" * 64,
            "locks": [{
                "binding_id": "BIND-001",
                "profile_id": "API-FASTAPI-STATELESS-OCI",
                "profile_version": "1.0.0",
                "sha256": "d" * 64,
            }],
            "profile_bindings": [bindings[0]],
            "artifact_digests": [],
        }
        legacy = {
            "schema_version": "1.2",
            "profile_id": None,
            "profile_version": None,
            "profile_bindings": ["BIND-001"],
            "profile_locks": material["locks"],
            "build_identity_material": material,
            "build_id": self.module._build_id(material),
        }
        manifest = {
            "technology": {
                "selected_profile": None,
                "profile_bindings": [{
                    "binding_id": "BIND-001",
                    "profile_id": "API-FASTAPI-STATELESS-OCI",
                }],
            }
        }
        self.assertEqual(
            self.module.evidence_profile_identity_errors(legacy, manifest), []
        )
        historical = json.loads(json.dumps(legacy))
        historical["profile_locks"][0].pop("profile_version")
        historical["build_identity_material"]["locks"][0].pop("profile_version")
        historical["build_id"] = self.module._build_id(
            historical["build_identity_material"]
        )
        self.assertEqual(
            self.module.evidence_profile_identity_errors(historical, manifest), []
        )
        self.assertTrue(
            self.module.evidence_profile_identity_errors(
                legacy, manifest, require_canonical_single=True
            )
        )

    def test_backend_slice_records_valid_single_profile_evidence_in_multibinding_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            implementation = _prepare_backend_slice_in_multibinding_project(root)
            self.assertEqual(implementation["profile_bindings"], ["BIND-001"])
            self._complete_execution(root)
            manifest_path = root / ".lks-sdd/project.json"
            before = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIsNone(before["technology"]["selected_profile"])
            self.assertEqual(len(before["technology"]["profile_bindings"]), 2)
            _, valid_before = run_json(VALIDATE_SCRIPT, str(root))
            self.assertTrue(valid_before["valid"], valid_before)

            delivery_relative = Path("docs/lks-sdd/evidence/delivery/REL-001-ENV-001.json")
            args = self._args(root)
            args.materialize_delivery_template = delivery_relative
            with mock.patch.object(
                self.module, "_execute_profile_command", side_effect=self._passed
            ), mock.patch.object(
                self.module, "_cleanup_profile_compositions", return_value=[]
            ):
                g3_code, g3 = self.module.run(args)
            self.assertEqual(g3_code, 0, g3)
            delivery_path = root / delivery_relative
            self._complete_delivery(delivery_path)
            snapshot = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            args.materialize_delivery_template = None
            args.delivery_evidence = delivery_relative
            args.record_evidence = "EVID-001"
            with mock.patch.object(
                self.module, "_execute_profile_command", side_effect=self._passed
            ), mock.patch.object(
                self.module, "_cleanup_profile_compositions", return_value=[]
            ):
                g4_code, g4 = self.module.run(args)
            self.assertEqual(g4_code, 0, g4)
            self.assertEqual(g4["classification"], "verified")
            self.assertTrue(g4["evidence_recorded"])
            self.assertEqual(g3["build_id"], g4["build_id"])

            evidence_path = root / "docs/lks-sdd/evidence/EVID-001.json"
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["profile_id"], "API-FASTAPI-STATELESS-OCI")
            self.assertEqual(evidence["profile_version"], "1.0.0")
            self.assertEqual(evidence["profile_bindings"], ["BIND-001"])
            self.assertEqual(
                [item["binding_id"] for item in evidence["profile_locks"]],
                ["BIND-001"],
            )
            self.assertEqual(
                [item["binding_id"] for item in evidence["build_identity_material"]["profile_bindings"]],
                ["BIND-001"],
            )
            applicability = evidence["gate_applicability"]
            self.assertEqual(applicability[0]["status"], "not-applicable")
            self.assertEqual(applicability[0]["scope"], "task-slice")
            self.assertEqual(applicability[0]["task_ids"], ["TASK-001"])
            self.assertFalse(
                any(item["name"] == "visual-browser-review" for item in evidence["checks"])
            )
            _, valid_after = run_json(VALIDATE_SCRIPT, str(root))
            _, trace_after = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment", "INC-001",
                "--task", "TASK-001",
                "--phase", "verification",
            )
            self.assertTrue(valid_after["valid"], valid_after)
            self.assertTrue(trace_after["valid"], trace_after)
            changed = {
                relative
                for relative, content in snapshot.items()
                if (root / relative).read_bytes() != content
            }
            self.assertEqual(
                changed,
                {".lks-sdd/project.json", "docs/lks-sdd/05-quality/traceability.md"},
            )
            current_files = {
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(
                current_files - set(snapshot),
                {
                    "docs/lks-sdd/evidence/EVID-001.json",
                    ".lks-sdd/summaries/task-evidence/TASK-001.json",
                    ".lks-sdd/summaries/task-evidence/TASK-002.json",
                },
            )
            self.assertEqual(g4["task_summaries_generated_in_one_pass"], 2)
            for task_id in ("TASK-001", "TASK-002"):
                summary = json.loads(
                    (root / f".lks-sdd/summaries/task-evidence/{task_id}.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(summary["kind"], "derived-task-evidence-summary")

    def test_invalid_post_write_evidence_rolls_back_every_recorded_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _prepare_started_project_with_empty_evidence(root, "invalid-candidate-rollback")
            self._complete_execution(root)
            manifest_path = root / ".lks-sdd/project.json"
            trace_path = root / "docs/lks-sdd/05-quality/traceability.md"
            original_manifest = manifest_path.read_bytes()
            original_trace = trace_path.read_bytes()
            evidence_path = root / "docs/lks-sdd/evidence/EVID-001.json"
            real_validate = self.module.validate_project

            def reject_materialized_evidence(project_root):
                report, manifest, definitions = real_validate(project_root)
                if evidence_path.exists():
                    report.errors.append("synthetic invalid evidence candidate")
                return report, manifest, definitions

            args = self._args(root)
            args.record_evidence = "EVID-001"
            with mock.patch.object(
                self.module, "_execute_profile_command", side_effect=self._passed
            ), mock.patch.object(
                self.module, "_cleanup_profile_compositions", return_value=[]
            ), mock.patch.object(
                self.module, "validate_project", side_effect=reject_materialized_evidence
            ), self.assertRaisesRegex(
                self.module.VerificationError, "validate-project"
            ):
                self.module.run(args)
            self.assertEqual(manifest_path.read_bytes(), original_manifest)
            self.assertEqual(trace_path.read_bytes(), original_trace)
            self.assertFalse(evidence_path.exists())
            self.assertFalse((root / ".lks-sdd/summaries/task-evidence").exists())
            self.assertFalse(list(root.rglob("*.lks-sdd.tmp")))


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


INCREMENTAL_VERIFICATION_CLASSES = (
    DeterministicBuildIdentityTests,
    EmptyTraceabilityEvidenceRegressionTests,
    EvidenceContractV0142RegressionTests,
    ExistingSchema15CompatibilityTests,
    G4TemplateContractTests,
    JiraCanonicalSourceRegressionTests,
    SliceVisualApplicabilityTests,
)
INCREMENTAL_VERIFICATION_SHARD_BOUNDARY = 6
INCREMENTAL_VERIFICATION_SECOND_BOUNDARY = 12
INCREMENTAL_VERIFICATION_THIRD_BOUNDARY = 18


def incremental_verification_tests(
    loader: unittest.TestLoader,
) -> list[unittest.TestCase]:
    """Return every incremental verification case in deterministic order."""
    return [
        test_class(name)
        for test_class in INCREMENTAL_VERIFICATION_CLASSES
        for name in loader.getTestCaseNames(test_class)
    ]


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    """Keep the first deterministic shard below the profile tier budget."""
    del standard_tests, pattern
    return unittest.TestSuite(
        incremental_verification_tests(loader)[:INCREMENTAL_VERIFICATION_SHARD_BOUNDARY]
    )


if __name__ == "__main__":
    unittest.main()
