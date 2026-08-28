from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "tests"))
sys.path.insert(
    0, str(PLUGIN_ROOT / "skills/lks-sdd-verify/scripts")
)

from delivery_engine import delivery_readiness, validate_delivery_contract  # noqa: E402
from eval_support import (  # noqa: E402
    IMPLEMENT_SCRIPT,
    PLANNING_SCRIPT,
    READINESS_SCRIPT,
    TASK_TEMPLATE,
    VERIFY_SCRIPT,
    _append_row,
    _replace_row,
    initialize,
    materialize_ready_project,
    materialize_ready_increment,
    run_json,
)
from planning_engine import (  # noqa: E402
    assess_authorization,
    assess_planning,
    next_tasks,
)
from validate_project import validate_project  # noqa: E402
from run_verification import _transition_summary as verification_summary  # noqa: E402

CONTINUITY_SCRIPT = PLUGIN_ROOT / "scripts" / "manage_continuity.py"
TASK_SCRIPT = PLUGIN_ROOT / "scripts" / "manage_tasks.py"
CALCULATOR_FIXTURE = (
    PLUGIN_ROOT / "tests" / "fixtures" / "prueba-calculadora-planning-partial.json"
)
_PARALLEL_TEMPLATE_DIRECTORY: tempfile.TemporaryDirectory[str] | None = None
_PARALLEL_TEMPLATE_ROOT: Path | None = None


def _replace_first_table_row(path: Path, header: str, row: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    index = lines.index(header)
    lines[index + 2] = row
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _render_task(
    root: Path,
    task_id: str,
    title: str,
    *,
    requirements: str,
    acceptance: str,
    tests: str,
    dependencies: str,
    workflow: str,
    integration: str,
    parallel: str,
) -> None:
    manifest = json.loads(
        (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
    )
    text = TASK_TEMPLATE.read_text(encoding="utf-8")
    for marker, value in {
        "{{TASK_ID}}": task_id,
        "{{TASK_TITLE}}": title,
        "{{PLAN_ID}}": "PLAN-001",
        "{{RELEASE_ID}}": "REL-001",
        "{{INCREMENT_ID}}": "INC-001",
        "{{UNIT_ID}}": "UNIT-001",
        "{{BINDING_ID}}": "BIND-001",
        "{{PROJECT_ID}}": manifest["project_id"],
        "{{BASELINE_ID}}": manifest["baseline_id"],
        "{{DATE}}": "2026-08-22",
    }.items():
        text = text.replace(marker, value)
    text = text.replace(
        "| pending | pending | pending | pending | pending | pending | pending | not-applicable |",
        f"| {title} | {title} and its tests | Scope owned by other tasks | {requirements} | {acceptance} | CAP-API-CONTRACT, CAP-OCI-RUNTIME | GATE-API-TEST, GATE-API-OPENAPI, GATE-OCI-BUILD | {dependencies} |",
    ).replace(
        "| pending | pending | pending | pending-assignment | pending | pending | pending | pending | pending |",
        f"| {tests} | ADR-001 and confirmed fixture constraints | not-applicable: no known synthetic risk | fixture-owner | Code and mapped tests complete | Mapped acceptance passed and integration handoff ready | EVID-{task_id[-3:]} tied to revision and artifact | {integration} | {parallel} |",
    ).replace(
        "| pending | pending | pending | pending | pending | pending |",
        f"| {title} deliverable | pending | {acceptance} | {tests} | EVID-{task_id[-3:]} | Verifiable output |",
    ).replace(
        "| backlog | unknown | 0 | pending-assignment | pending | pending | pending | pending | pending | 2026-08-22 |",
        f"| {workflow} | {'on-track' if workflow == 'ready' else 'unknown'} | 0 | fixture-owner | pending | pending | pending | pending | ENV-001 | 2026-08-22 |",
    ).replace(
        "| incomplete | none | none | none | pending | pending | complete task definition |",
        f"| executable | none | none | none | pending | pending | start when {dependencies} are done |",
    )
    destination = root / f"docs/lks-sdd/04-delivery/tasks/{task_id}.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8", newline="\n")


def _confirm_plan(root: Path) -> dict:
    _, preview = run_json(
        PLANNING_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "confirm",
        "--date",
        "2026-08-22",
        "--actor-role",
        "release-owner",
        "--preview",
    )
    _, applied = run_json(
        PLANNING_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "confirm",
        "--date",
        "2026-08-22",
        "--actor-role",
        "release-owner",
        "--apply",
        "--authorize",
        "--preview-hash",
        preview["preview_hash"],
    )
    return applied


def _authorize(root: Path, *tasks: str) -> dict:
    base = [
        str(root),
        "--increment",
        "INC-001",
        "authorize",
        "--authorization-id",
        "AUTH-001",
    ]
    for task in tasks:
        base.extend(["--task", task])
    base.extend(
        [
            "--date",
            "2026-08-22",
            "--actor-role",
            "release-owner",
            "--decision",
            "ADR-001",
            "--constraints",
            "Only the listed tasks and current fingerprints",
        ]
    )
    _, preview = run_json(PLANNING_SCRIPT, *base, "--preview")
    _, applied = run_json(
        PLANNING_SCRIPT,
        *base,
        "--apply",
        "--authorize",
        "--preview-hash",
        preview["preview_hash"],
    )
    return applied


def _transition(
    root: Path,
    task: str,
    target: str,
    *extra: str,
    expected_codes: set[int] | None = None,
) -> dict:
    base = [
        str(root),
        "transition",
        "--task",
        task,
        "--to",
        target,
        "--reason",
        f"Move {task} to {target}",
        "--actor",
        "delivery-owner",
        "--date",
        "2026-08-22",
        *extra,
    ]
    code, preview = run_json(
        TASK_SCRIPT,
        *base,
        "--preview",
        expected_codes=expected_codes or {0},
    )
    if code != 0:
        return preview
    _, applied = run_json(
        TASK_SCRIPT,
        *base,
        "--apply",
        "--authorize",
        "--preview-hash",
        preview["preview_hash"],
    )
    return applied


def _add_calculator_scope(root: Path) -> dict:
    fixture = json.loads(CALCULATOR_FIXTURE.read_text(encoding="utf-8"))
    docs = root / "docs/lks-sdd"
    requirement_ids = ["FR-001"]
    acceptance_ids = ["AC-001"]
    test_ids = ["TEST-001"]
    for item in fixture["unassigned_requirements"]:
        requirement_ids.append(item["id"])
        acceptance_ids.append(item["acceptance"])
        test_ids.append(item["test"])
        _append_row(
            docs / "02-requirements/functional-requirements.md",
            "| ID | State | Statement",
            f"| {item['id']} | confirmed | The product provides {item['capability']}. | user-confirmed | must | {item['acceptance']} | INC-001 |",
        )
        _append_row(
            docs / "02-requirements/acceptance-criteria.md",
            "| ID | State | Condition",
            f"| {item['acceptance']} | confirmed | The confirmed {item['capability']} behavior is observable. | {item['id']} | none |",
        )
        _append_row(
            docs / "05-quality/quality-strategy.md",
            "| ID | State | Purpose",
            f"| {item['test']} | planned | Verify {item['capability']} | INC-001 | {item['acceptance']} |",
        )
        _append_row(
            docs / "05-quality/test-strategy.md",
            "| Test | Level or type",
            f"| {item['test']} | acceptance | {item['capability']} | {item['acceptance']} | ENV-001 | pending: executed during G3 |",
        )
        _append_row(
            docs / "05-quality/traceability.md",
            "| Requirement | Acceptance",
            f"| {item['id']} | {item['acceptance']} | ADR-001 | INC-001 | {item['test']} | none |",
        )
    _replace_row(
        docs / "04-delivery/increments.md",
        "INC-001",
        "| INC-001 | confirmed | Complete calculator release including navigation, calculators, units, currencies, languages, settings, history, privacy, recovery and cross-browser quality | Unrelated backend and authentication | FR-001..FR-012 | AC-001..AC-012 | ADR-001 | TEST-001..TEST-012 |",
    )
    return fixture


def _build_parallel_complete_plan(root: Path) -> dict:
    materialize_ready_project(root, "parallel-plan", confirm_plan=False)
    docs = root / "docs/lks-sdd"
    _append_row(
        docs / "02-requirements/functional-requirements.md",
        "| ID | State | Statement",
        "| FR-002 | confirmed | A second independent request path is available. | user-confirmed | must | AC-002 | INC-001 |",
    )
    _append_row(
        docs / "02-requirements/acceptance-criteria.md",
        "| ID | State | Condition",
        "| AC-002 | confirmed | The second request path is acknowledged. | FR-002 | none |",
    )
    for test_id, purpose, acceptance in (
        ("TEST-002", "Verify the second request path", "AC-002"),
        ("TEST-003", "Verify joint release integration", "AC-001, AC-002"),
    ):
        _append_row(
            docs / "05-quality/quality-strategy.md",
            "| ID | State | Purpose",
            f"| {test_id} | planned | {purpose} | INC-001 | {acceptance} |",
        )
        _append_row(
            docs / "05-quality/test-strategy.md",
            "| Test | Level or type",
            f"| {test_id} | integration | {purpose} | {acceptance} | ENV-001 | pending: executed during G3 |",
        )
    _append_row(
        docs / "05-quality/traceability.md",
        "| Requirement | Acceptance",
        "| FR-002 | AC-002 | ADR-001 | INC-001 | TEST-002, TEST-003 | none |",
    )
    _replace_row(
        docs / "04-delivery/increments.md",
        "INC-001",
        "| INC-001 | confirmed | Submit two independent requests and verify their joint release | Reporting and administration | FR-001..FR-002 | AC-001..AC-002 | ADR-001 | TEST-001..TEST-003 |",
    )
    _replace_row(
        docs / "04-delivery/plans.md",
        "REL-001",
        "| REL-001 | active | 0.1.0 | PLAN-001 | 2026-08-19 | continuous stream | ENV-001 | TASK-001..TASK-003 | pending | pending | pending: G3/G4 not executed |",
    )
    tasks_path = docs / "04-delivery/tasks.md"
    _append_row(
        tasks_path,
        "| ID | Plan | Title",
        "| TASK-002 | PLAN-001 | Implement second request path | REL-001 | INC-001 | UNIT-001 | BIND-001 | ready | on-track | 0 | not-applicable: independent root | none | fixture-owner | ./tasks/TASK-002.md | 2026-08-22 |",
    )
    _append_row(
        tasks_path,
        "| ID | Plan | Title",
        "| TASK-003 | PLAN-001 | Integrate and verify release | REL-001 | INC-001 | UNIT-001 | BIND-001 | backlog | unknown | 0 | TASK-001, TASK-002 | none | fixture-owner | ./tasks/TASK-003.md | 2026-08-22 |",
    )
    _render_task(
        root,
        "TASK-002",
        "Implement second request path",
        requirements="FR-002",
        acceptance="AC-002",
        tests="TEST-002",
        dependencies="not-applicable: independent root",
        workflow="ready",
        integration="Provide output to TASK-003",
        parallel="May run in parallel with TASK-001",
    )
    _render_task(
        root,
        "TASK-003",
        "Integrate and verify release",
        requirements="FR-001, FR-002",
        acceptance="AC-001, AC-002",
        tests="TEST-003",
        dependencies="TASK-001, TASK-002",
        workflow="backlog",
        integration="Joint release verification and handoff",
        parallel="Starts only after TASK-001 and TASK-002 are done",
    )
    planning = docs / "04-delivery/planning-coverage.md"
    _replace_row(
        planning,
        "REL-001",
        "| REL-001 | release | proposed | Deliver both request paths with joint verification | INC-001 | complete-before-implementation | not-applicable: method default | TASK-003 | scope, contract or dependency change |",
    )
    _replace_first_table_row(
        planning,
        "| Target | Increment | Contract items | Primary task | Contributing tasks | Responsibility | Rationale |",
        "| REL-001 | INC-001 | FR-001, AC-001, TEST-001 | TASK-001 | TASK-003 | Implement the first request path | Primary ownership remains with TASK-001 |",
    )
    _append_row(
        planning,
        "| Target | Increment | Contract items",
        "| REL-001 | INC-001 | FR-002, AC-002, TEST-002 | TASK-002 | TASK-003 | Implement the second request path | Independent primary ownership |",
    )
    _append_row(
        planning,
        "| Target | Increment | Contract items",
        "| REL-001 | INC-001 | ADR-001, TEST-003 | TASK-003 | TASK-001, TASK-002 | Integrate and jointly verify the release | Explicit release-wide responsibility |",
    )
    confirmation = _confirm_plan(root)
    if confirmation.get("transition_summary", {}).get("where_we_are") != "planning-complete":
        raise AssertionError("Planning confirmation did not emit its transition summary.")
    report, _, _ = validate_project(root)
    if not report.valid:
        raise AssertionError(report.errors)
    manifest = json.loads(
        (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
    )
    return assess_planning(root, manifest, "INC-001")


def _materialize_parallel_complete_plan(root: Path) -> dict:
    """Clone the expensive immutable three-task plan for each isolated test."""
    global _PARALLEL_TEMPLATE_DIRECTORY
    global _PARALLEL_TEMPLATE_ROOT
    if any(root.iterdir()):
        raise AssertionError("parallel plan fixture requires an empty root")
    if _PARALLEL_TEMPLATE_ROOT is None:
        _PARALLEL_TEMPLATE_DIRECTORY = tempfile.TemporaryDirectory(
            prefix="lks-sdd-parallel-template-"
        )
        _PARALLEL_TEMPLATE_ROOT = (
            Path(_PARALLEL_TEMPLATE_DIRECTORY.name) / "project"
        )
        _PARALLEL_TEMPLATE_ROOT.mkdir()
        _build_parallel_complete_plan(_PARALLEL_TEMPLATE_ROOT)
    shutil.copytree(
        _PARALLEL_TEMPLATE_ROOT,
        root,
        dirs_exist_ok=True,
        copy_function=shutil.copy2,
    )
    manifest = json.loads(
        (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
    )
    return assess_planning(root, manifest, "INC-001")


def _git_commit(root: Path) -> None:
    commands = (
        ["git", "init", "-b", "main"],
        ["git", "config", "user.name", "Synthetic Test"],
        ["git", "config", "user.email", "synthetic@example.invalid"],
        ["git", "add", "--all"],
        ["git", "commit", "-m", "fixture baseline"],
    )
    for command in commands:
        subprocess.run(
            command,
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )


def _record_verified_task_001_evidence(root: Path) -> dict[str, object]:
    revision = "2" * 40
    build_id = "build-sha256:" + "3" * 64
    artifact_digest = "sha256:" + "4" * 64
    gate_ids = ["GATE-API-TEST", "GATE-API-OPENAPI", "GATE-OCI-BUILD"]
    manifest_path = root / ".lks-sdd/project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["verification"] = {
        "status": "verified",
        "increment": "INC-001",
        "task_ids": ["TASK-001"],
        "revision": revision,
        "tree_id": "5" * 40,
        "tree_sha256": "6" * 64,
        "build_id": build_id,
        "artifact_digests": [artifact_digest],
        "environment": "ENV-001",
        "gate_ids": gate_ids,
        "evidence_ids": ["EVID-001"],
        "limitations": [],
    }
    for execution in manifest["executions"]:
        if "TASK-001" in execution["task_ids"]:
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
                "revision": revision,
                "build_id": build_id,
                "artifact_digests": [artifact_digest],
                "environment": "ENV-001",
                "classification": "verified",
                "gate_ids": gate_ids,
                "checks": [
                    {"gate_id": gate_id, "status": "passed"}
                    for gate_id in gate_ids
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
    _replace_first_table_row(
        root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md",
        "| Deliverable | State | Acceptance | Tests | Evidence | Notes |",
        "| Acknowledgement behavior and tests | done | AC-001 | TEST-001 | EVID-001 | Verified output |",
    )
    return {
        "revision": revision,
        "build_id": build_id,
        "artifact_digest": artifact_digest,
        "gate_ids": gate_ids,
    }


class PlanningContinuityV13Tests(unittest.TestCase):
    def test_calculator_release_remains_partial_when_only_task_001_is_ready(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-calculator-partial-") as directory:
            root = Path(directory)
            materialize_ready_project(
                root, "prueba-calculadora-regression", confirm_plan=False
            )
            fixture = _add_calculator_scope(root)
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, fixture["increment"])
            self.assertEqual(planning["status"], "partial")
            self.assertEqual(planning["integrity"], "valid")
            self.assertEqual(planning["tasks"]["all"], ["TASK-001"])
            expected_unassigned = {
                item[key]
                for item in fixture["unassigned_requirements"]
                for key in ("id", "acceptance", "test")
            }
            self.assertTrue(
                expected_unassigned <= set(planning["coverage"]["unassigned_items"])
            )
            code, readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                fixture["increment"],
                expected_codes={3},
            )
            self.assertEqual(code, 3)
            self.assertEqual(readiness["status"], "planning-required")
            self.assertEqual(readiness["specification_readiness"]["status"], "ready")
            self.assertEqual(readiness["automation_support"]["status"], "supported")
            self.assertEqual(
                readiness["selected_portion_readiness"]["status"], "ready"
            )
            self.assertEqual(readiness["phase_states"]["selected_portion"], "ready")
            self.assertEqual(readiness["phase_states"]["planning_completeness"], "partial")
            self.assertEqual(readiness["phase_states"]["implementation"], "not-started")
            self.assertIn("Completar y validar la planificación", readiness["recommended_next_step"])
            completed_summary = " ".join(
                readiness["transition_summary"]["completed"]
            )
            self.assertIn("Alcance confirmado de INC-001", completed_summary)
            self.assertIn("UX e interfaz evaluadas", completed_summary)
            self.assertIn(
                "Datos, identidad, seguridad, privacidad e integraciones evaluados",
                completed_summary,
            )
            self.assertIn("No quedan bloqueos", completed_summary)

    def test_incremental_policy_authorizes_only_the_explicit_ready_slice(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-incremental-policy-") as directory:
            root = Path(directory)
            materialize_ready_project(
                root, "incremental-policy", confirm_plan=False
            )
            _add_calculator_scope(root)
            docs = root / "docs/lks-sdd"
            _append_row(
                docs / "03-solution/solution-overview.md",
                "| ID | State | Decision",
                "| ADR-003 | confirmed | Allow only explicitly authorized ready tasks to start while the release plan remains partial. | FR-001 | Does not represent complete release planning and requires bounded AUTH records |",
            )
            _replace_row(
                docs / "04-delivery/planning-coverage.md",
                "REL-001",
                "| REL-001 | release | proposed | Deliver the complete calculator increment | INC-001 | incremental-authorized | ADR-003 | TASK-001 | scope, contract or dependency change |",
            )

            confirmation = _confirm_plan(root)
            self.assertEqual(
                confirmation["transition_summary"]["where_we_are"],
                "planning-partial-confirmed",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            self.assertEqual(planning["status"], "partial")
            self.assertEqual(planning["policy"], "incremental-authorized")
            self.assertTrue(planning["partial_implementation_policy_satisfied"])
            self.assertIn("FR-012", planning["coverage"]["unassigned_items"])

            authorization = _authorize(root, "TASK-001")
            self.assertEqual(
                authorization["transition_summary"]["where_we_are"],
                "implementation-authorized",
            )
            code, readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-001",
            )
            self.assertEqual(code, 0)
            self.assertEqual(readiness["status"], "ready-to-implement")
            self.assertEqual(
                readiness["phase_states"]["planning_completeness"], "partial"
            )
            self.assertEqual(readiness["phase_states"]["selected_portion"], "ready")
            self.assertTrue(readiness["implementation_authorized"])
            self.assertTrue(readiness["transition_summary"]["pending"])

            _, implementation_preview = run_json(
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
                implementation_preview["preview_hash"],
            )
            resume_code, initial_resume = run_json(
                CONTINUITY_SCRIPT,
                str(root),
                "resume",
                "--execution-id",
                str(implementation["execution_id"]),
            )
            self.assertEqual(resume_code, 0)
            self.assertEqual(initial_resume["recommendation"], "continue")
            source_path = root / "src/lks_sdd_api/main.py"
            source_path.write_text(
                source_path.read_text(encoding="utf-8")
                + "\n# authorized partial implementation\n",
                encoding="utf-8",
                newline="\n",
            )
            checkpoint_args = [
                str(root),
                "checkpoint",
                "--execution-id",
                str(implementation["execution_id"]),
                "--state",
                "in-progress",
                "--date",
                "2026-08-22",
                "--owner-role",
                "delivery-owner",
                "--partial",
                "TASK-001 implementation remains in progress",
                "--pending",
                "review and verification remain not-run",
                "--next-action",
                "continue TASK-001",
            ]
            missing_path_code, missing_path = run_json(
                CONTINUITY_SCRIPT,
                *checkpoint_args,
                "--preview",
                expected_codes={2},
            )
            self.assertEqual(missing_path_code, 2)
            self.assertIn("--changed-path", missing_path["error"])
            checkpoint_args.extend(
                ["--changed-path", "src/lks_sdd_api/main.py"]
            )
            _, checkpoint_preview = run_json(
                CONTINUITY_SCRIPT, *checkpoint_args, "--preview"
            )
            run_json(
                CONTINUITY_SCRIPT,
                *checkpoint_args,
                "--apply",
                "--authorize",
                "--preview-hash",
                checkpoint_preview["preview_hash"],
            )
            resumed_code, resumed_after_checkpoint = run_json(
                CONTINUITY_SCRIPT,
                str(root),
                "resume",
                "--execution-id",
                str(implementation["execution_id"]),
            )
            self.assertEqual(resumed_code, 0)
            self.assertEqual(
                resumed_after_checkpoint["recommendation"], "continue"
            )
            _transition(root, "TASK-001", "in-review")
            verified = _record_verified_task_001_evidence(root)
            done = _transition(
                root,
                "TASK-001",
                "done",
                "--evidence",
                "EVID-001",
                "--revision",
                str(verified["revision"]),
                "--build",
                str(verified["build_id"]),
                "--artifact-digest",
                str(verified["artifact_digest"]),
                "--environment",
                "ENV-001",
                "--gate",
                "GATE-API-TEST",
                "--gate",
                "GATE-API-OPENAPI",
                "--gate",
                "GATE-OCI-BUILD",
            )
            self.assertEqual(
                done["transition_summary"]["where_we_are"],
                "release-tasks-complete-planning-partial",
            )
            self.assertTrue(
                any(
                    "FR-012" in item
                    for item in done["transition_summary"]["pending"]
                )
            )
            self.assertIn(
                "antes de presentar, verificar conjuntamente o promover",
                done["transition_summary"]["next_step"],
            )

    def test_complete_plan_exposes_parallel_frontier_and_authorization(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-complete-plan-") as directory:
            root = Path(directory)
            planning = _materialize_parallel_complete_plan(root)
            self.assertEqual(planning["status"], "complete")
            self.assertEqual(planning["tasks"]["initial"], ["TASK-001", "TASK-002"])
            self.assertEqual(
                planning["tasks"]["parallel_frontiers"],
                [["TASK-001", "TASK-002"], ["TASK-003"]],
            )
            self.assertEqual(planning["integration_task"], "TASK-003")
            self.assertEqual(planning["dependency_graph"]["critical_path"]["status"], "undetermined")
            authorization_result = _authorize(root, "TASK-001", "TASK-002")
            self.assertEqual(
                set(authorization_result["transition_summary"]),
                {"where_we_are", "completed", "in_progress", "pending", "blocked", "next_step", "human_decision"},
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["planning"]["confirmed_by_role"], "release-owner"
            )
            current = assess_planning(root, manifest, "INC-001")
            authorization = assess_authorization(
                manifest, current, ["TASK-001", "TASK-002"]
            )
            self.assertEqual(authorization["status"], "authorized")
            delivery = validate_delivery_contract(root, manifest)
            next_work = next_tasks(delivery, current)
            self.assertEqual(next_work["ready"], ["TASK-001", "TASK-002"])
            self.assertTrue(next_work["parallel"])

    def test_release_assessment_covers_every_declared_increment(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-release-scope-") as directory:
            root = Path(directory)
            _materialize_parallel_complete_plan(root)
            planning_path = root / "docs/lks-sdd/04-delivery/planning-coverage.md"
            _replace_row(
                planning_path,
                "REL-001",
                "| REL-001 | release | confirmed | Deliver both request paths with joint verification | INC-001, INC-999 | complete-before-implementation | not-applicable: method default | TASK-003 | scope, contract or dependency change |",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )

            planning = assess_planning(root, manifest, "INC-001")

            self.assertEqual(
                planning["target"]["increments"], ["INC-001", "INC-999"]
            )
            self.assertNotEqual(planning["status"], "complete")
            self.assertEqual(planning["integrity"], "invalid")
            self.assertTrue(
                any("INC-999" in item for item in planning["integrity_errors"]),
                planning["integrity_errors"],
            )

    def test_parallel_execution_start_preserves_existing_active_tasks(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-parallel-exec-") as directory:
            root = Path(directory)
            _materialize_parallel_complete_plan(root)
            _authorize(root, "TASK-001", "TASK-002")

            for task_id in ("TASK-002", "TASK-001"):
                _, preview = run_json(
                    IMPLEMENT_SCRIPT,
                    str(root),
                    "--increment",
                    "INC-001",
                    "--task",
                    task_id,
                    "--dry-run",
                )
                _, applied = run_json(
                    IMPLEMENT_SCRIPT,
                    str(root),
                    "--increment",
                    "INC-001",
                    "--task",
                    task_id,
                    "--apply",
                    "--authorize",
                    "--preview-hash",
                    preview["preview_hash"],
                )
                self.assertEqual(applied["status"], "prepared")

            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["active_tasks"], ["TASK-001", "TASK-002"])
            self.assertIsNone(manifest["active_task"])
            self.assertEqual(
                {item["execution_id"] for item in manifest["executions"]},
                {"EXEC-001", "EXEC-002"},
            )
            verification_code, verification_plan = run_json(
                VERIFY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-002",
                "--execution-id",
                "EXEC-001",
                "--plan",
            )
            self.assertEqual(verification_code, 0, verification_plan)
            self.assertEqual(verification_plan["execution_id"], "EXEC-001")
            self.assertEqual(verification_plan["task_ids"], ["TASK-002"])
            report, _, _ = validate_project(root)
            self.assertTrue(report.valid, report.errors)

    def test_coverage_rejects_contributors_outside_the_release_objective(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-foreign-contributor-") as directory:
            root = Path(directory)
            _materialize_parallel_complete_plan(root)
            planning_path = root / "docs/lks-sdd/04-delivery/planning-coverage.md"
            _replace_first_table_row(
                planning_path,
                "| Target | Increment | Contract items | Primary task | Contributing tasks | Responsibility | Rationale |",
                "| REL-001 | INC-001 | FR-001, AC-001, TEST-001 | TASK-001 | TASK-999 | Implement the first request path | Primary ownership remains with TASK-001 |",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            self.assertEqual(planning["integrity"], "invalid")
            self.assertTrue(
                any(
                    "contribución fuera del objetivo" in error
                    for error in planning["integrity_errors"]
                )
            )

    def test_readiness_cli_assesses_only_the_explicit_task_slice(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-selected-slice-") as directory:
            root = Path(directory)
            _materialize_parallel_complete_plan(root)
            code, readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-003",
                expected_codes={3},
            )
            self.assertEqual(code, 3)
            self.assertEqual(readiness["status"], "selected-portion-blocked")
            self.assertEqual(readiness["planning_completeness"]["status"], "complete")
            self.assertEqual(readiness["delivery_readiness"]["task_ids"], ["TASK-003"])
            self.assertEqual(readiness["phase_states"]["selected_portion"], "blocked")
            self.assertTrue(
                any("TASK-001" in item for item in readiness["delivery_readiness"]["blockers"])
            )

    def test_migrated_ready_task_keeps_workflow_but_loses_executable_readiness(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-migrated-ready-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "migrated-ready")
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            _replace_first_table_row(
                detail_path,
                "| Tests | Decisions and constraints | Risks and blockers | Responsible role | Review entry conditions | Definition of done | Required evidence | Integration points | Parallel constraints |",
                "| pending | pending | pending | pending-assignment | pending | pending | pending | pending | pending |",
            )
            _replace_first_table_row(
                detail_path,
                "| Definition status | Current checkpoint | Authorization | Authorization scope | Specification fingerprint | Planning fingerprint | Next safe action |",
                "| incomplete | none | none | none | pending | pending | complete the migrated task definition |",
            )
            report, manifest, _ = validate_project(root)
            self.assertTrue(report.valid, report.errors)
            self.assertIsNotNone(manifest)
            delivery = delivery_readiness(
                root, manifest, "INC-001", task_ids=["TASK-001"]
            )
            self.assertEqual(delivery["status"], "blocked")
            self.assertTrue(
                any("no tiene un plan ejecutable" in item for item in delivery["blockers"])
            )
            self.assertEqual(
                validate_delivery_contract(root, manifest)["tasks"]["TASK-001"]["Workflow state"],
                "ready",
            )

    def test_explanatory_pending_placeholder_is_not_executable_content(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-pending-placeholder-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "pending-placeholder")
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            text = detail_path.read_text(encoding="utf-8")
            detail_path.write_text(
                text.replace(
                    "| Implement the confirmed acknowledgement behavior |",
                    "| pending: confirm objective |",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            incomplete = {
                item["task"]: item["missing"]
                for item in planning["tasks"]["incomplete"]
            }
            self.assertIn("Objective", incomplete["TASK-001"])
            self.assertNotIn("TASK-001", planning["tasks"]["executable"])

    def test_task_capabilities_and_gates_must_belong_to_its_binding(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-gates-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "task-gates")
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            text = detail_path.read_text(encoding="utf-8")
            detail_path.write_text(
                text.replace("GATE-API-TEST", "GATE-UNKNOWN-FAKE", 1),
                encoding="utf-8",
                newline="\n",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            self.assertEqual(planning["integrity"], "invalid")
            self.assertTrue(
                any(
                    "GATE-UNKNOWN-FAKE" in item
                    and "no aplicables" in item
                    for item in planning["integrity_errors"]
                ),
                planning,
            )

    def test_plan_is_partial_when_binding_contract_cannot_be_loaded(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-missing-profile-") as directory:
            root = Path(directory)
            materialize_ready_project(
                root, "missing-profile-contract", confirm_plan=False
            )
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["technology"]["profile_bindings"][0]["profile_id"] = (
                "WEB-UNKNOWN-STACK"
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )

            planning = assess_planning(root, manifest, "INC-001")

            self.assertEqual(planning["status"], "partial")
            self.assertTrue(
                any(
                    gap.get("kind") == "task-automation-contract"
                    and "WEB-UNKNOWN-STACK" in gap.get("items", [])
                    for gap in planning["gaps"]
                ),
                planning,
            )

    def test_checkpoint_reconstructs_partial_blocked_and_independent_work(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-checkpoint-") as directory:
            root = Path(directory)
            _materialize_parallel_complete_plan(root)
            _authorize(root, "TASK-001")
            _git_commit(root)
            _, preview = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-001",
                "--dry-run",
            )
            _, applied = run_json(
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
            self.assertTrue(Path(root / applied["checkpoint"]).is_file())
            self.assertEqual(
                applied["transition_summary"]["where_we_are"],
                "implementation-in-progress",
            )
            blocked_transition = _transition(
                root,
                "TASK-003",
                "blocked",
                "--blocker",
                "Joint integration waits for both implementation tasks",
            )
            self.assertEqual(
                blocked_transition["transition_summary"]["where_we_are"],
                "task-blocked",
            )
            checkpoint_args = [
                str(root),
                "checkpoint",
                "--execution-id",
                "EXEC-001",
                "--state",
                "paused",
                "--date",
                "2026-08-22",
                "--owner-role",
                "delivery-owner",
                "--completed",
                "Technical scaffold and task start recorded",
                "--partial",
                "TASK-001 behavior remains partial",
                "--pending",
                "Acceptance and G3 gates remain not-run",
                "--blocked",
                "TASK-003 waits for both implementation tasks",
                "--next-action",
                "Continue TASK-001 without repeating preparation",
                "--independent-task",
                "TASK-002",
            ]
            invalid_state_args = list(checkpoint_args)
            invalid_state_args[invalid_state_args.index("paused")] = "completed"
            invalid_code, invalid_state = run_json(
                CONTINUITY_SCRIPT,
                *invalid_state_args,
                "--preview",
                expected_codes={2},
            )
            self.assertEqual(invalid_code, 2)
            self.assertIn("estado derivado", invalid_state["error"])
            _, checkpoint_preview = run_json(
                CONTINUITY_SCRIPT, *checkpoint_args, "--preview"
            )
            _, checkpoint = run_json(
                CONTINUITY_SCRIPT,
                *checkpoint_args,
                "--apply",
                "--authorize",
                "--preview-hash",
                checkpoint_preview["preview_hash"],
            )
            checkpoint_path = (
                root
                / "docs/lks-sdd/04-delivery/checkpoints"
                / f"{checkpoint['checkpoint_id']}.md"
            )
            text = checkpoint_path.read_text(encoding="utf-8")
            self.assertIn("TASK-001 behavior remains partial", text)
            self.assertIn("TASK-003 waits for both implementation tasks", text)
            self.assertIn("TASK-002", text)
            self.assertEqual(
                checkpoint["transition_summary"]["where_we_are"],
                "implementation-paused",
            )
            code, resumed = run_json(
                CONTINUITY_SCRIPT,
                str(root),
                "resume",
                "--execution-id",
                "EXEC-001",
                expected_codes={0, 3},
            )
            self.assertEqual(code, 0, resumed)
            self.assertEqual(resumed["recommendation"], "continue")
            self.assertFalse(resumed["code_written_is_verified"])
            self.assertTrue(resumed["recorded_files"])
            self.assertTrue(resumed["recorded_deliverables"])
            self.assertTrue(resumed["recorded_checks"])
            self.assertTrue(resumed["recorded_issues"])
            self.assertTrue(
                any(
                    item.get("Result") == "not-run"
                    for item in resumed["recorded_checks"]
                )
            )
            self.assertEqual(resumed["next_tasks"]["ready"], ["TASK-002"])
            self.assertEqual(
                resumed["transition_summary"]["where_we_are"],
                "resume-continue",
            )
            original_checkpoint = checkpoint_path.read_text(encoding="utf-8")
            checkpoint_path.write_text(
                original_checkpoint.replace("| EXEC-001 |", "| EXEC-999 |", 1),
                encoding="utf-8",
                newline="\n",
            )
            identity_code, identity_changed = run_json(
                CONTINUITY_SCRIPT,
                str(root),
                "resume",
                "--execution-id",
                "EXEC-001",
                expected_codes={3},
            )
            self.assertEqual(identity_code, 3)
            self.assertIn(
                "checkpoint identity changed: Execution",
                identity_changed["divergence"],
            )
            checkpoint_path.write_text(
                original_checkpoint, encoding="utf-8", newline="\n"
            )
            (root / "unexpected-session-change.txt").write_text(
                "unrecorded divergence\n", encoding="utf-8", newline="\n"
            )
            diverged_code, diverged = run_json(
                CONTINUITY_SCRIPT,
                str(root),
                "resume",
                "--execution-id",
                "EXEC-001",
                expected_codes={3},
            )
            self.assertEqual(diverged_code, 3)
            self.assertEqual(diverged["recommendation"], "reconcile")
            self.assertIn(
                "unrecorded changed path: unexpected-session-change.txt",
                diverged["divergence"],
            )
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["executions"][0]["latest_checkpoint"] = "../../outside.md"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            unsafe_code, unsafe = run_json(
                CONTINUITY_SCRIPT,
                str(root),
                "resume",
                "--execution-id",
                "EXEC-001",
                expected_codes={2},
            )
            self.assertEqual(unsafe_code, 2)
            self.assertIn("Ruta de checkpoint no segura", unsafe["error"])

    def test_scope_change_stales_planning_and_authorization(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-scope-change-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "scope-change")
            _authorize(root, "TASK-001")
            requirement = root / "docs/lks-sdd/02-requirements/functional-requirements.md"
            requirement.write_text(
                requirement.read_text(encoding="utf-8").replace(
                    "A user can submit one synthetic request.",
                    "A user can submit and cancel one synthetic request.",
                ),
                encoding="utf-8",
                newline="\n",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            self.assertEqual(planning["status"], "stale")
            self.assertTrue(planning["change_impact"]["fingerprint_changed"])
            self.assertTrue(planning["change_impact"]["requires_change_record"])
            self.assertEqual(
                planning["change_impact"]["conservative_tasks_pending_pch"],
                ["TASK-001"],
            )
            authorization = assess_authorization(manifest, planning, ["TASK-001"])
            self.assertEqual(authorization["status"], "invalidated")
            self.assertEqual(authorization["stale_authorizations"], ["AUTH-001"])

            refused_code, refused = run_json(
                PLANNING_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "confirm",
                "--date",
                "2026-08-22",
                "--actor-role",
                "release-owner",
                "--preview",
                expected_codes={2},
            )
            self.assertEqual(refused_code, 2)
            self.assertIn("PCH confirmed", refused["error"])

            planning_path = root / "docs/lks-sdd/04-delivery/planning-coverage.md"
            _append_row(
                planning_path,
                "| ID | State | Classification",
                "| PCH-001 | confirmed | new-scope | FR-001 | TASK-001 | "
                + str(planning["stored_fingerprints"]["planning"])
                + " | "
                + planning["planning_fingerprint"]
                + " | ADR-001 | Human-confirmed scope impact |",
            )
            confirmation = _confirm_plan(root)
            self.assertEqual(
                confirmation["transition_summary"]["where_we_are"],
                "planning-complete",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["planning"]["last_change"], "PCH-001")
            replanned = assess_planning(root, manifest, "INC-001")
            self.assertEqual(replanned["status"], "complete")
            self.assertEqual(
                replanned["change_impact"]["applicable_confirmed_changes"], []
            )

    def test_proposed_change_does_not_become_confirmed_impact(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-proposed-change-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "proposed-change")
            requirement = root / "docs/lks-sdd/02-requirements/functional-requirements.md"
            requirement.write_text(
                requirement.read_text(encoding="utf-8").replace(
                    "A user can submit one synthetic request.",
                    "A user can submit and cancel one synthetic request.",
                ),
                encoding="utf-8",
                newline="\n",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            changed_before_record = assess_planning(root, manifest, "INC-001")
            previous_fingerprint = changed_before_record["stored_fingerprints"][
                "planning"
            ]
            current_fingerprint = changed_before_record["planning_fingerprint"]
            planning_path = root / "docs/lks-sdd/04-delivery/planning-coverage.md"
            _append_row(
                planning_path,
                "| ID | State | Classification",
                "| PCH-001 | proposed | new-scope | FR-001 | TASK-001 | "
                + str(previous_fingerprint)
                + " | "
                + str(current_fingerprint)
                + " | ADR-001 | Candidate impact awaiting human confirmation |",
            )
            proposed = assess_planning(root, manifest, "INC-001")
            self.assertEqual(proposed["status"], "stale")
            self.assertEqual(
                proposed["change_impact"]["recorded_changes"][0]["state"],
                "proposed",
            )
            self.assertEqual(proposed["change_impact"]["confirmed_changes"], [])
            self.assertEqual(
                proposed["change_impact"]["applicable_confirmed_changes"], []
            )
            self.assertEqual(proposed["change_impact"]["affected_tasks"], [])
            self.assertTrue(proposed["change_impact"]["requires_change_record"])
            self.assertEqual(
                proposed["change_impact"]["conservative_tasks_pending_pch"],
                ["TASK-001"],
            )

            _replace_row(
                planning_path,
                "PCH-001",
                "| PCH-001 | confirmed | new-scope | FR-001 | TASK-001 | "
                + str(previous_fingerprint)
                + " | "
                + str(current_fingerprint)
                + " | ADR-001 | Human-confirmed impact classification |",
            )
            confirmed = assess_planning(root, manifest, "INC-001")
            self.assertEqual(
                confirmed["change_impact"]["affected_tasks"], ["TASK-001"]
            )
            self.assertFalse(confirmed["change_impact"]["requires_change_record"])
            self.assertEqual(
                confirmed["change_impact"]["applicable_confirmed_changes"][0]["id"],
                "PCH-001",
            )
            self.assertEqual(
                confirmed["change_impact"]["conservative_tasks_pending_pch"], []
            )

    def test_planning_change_rejects_unknown_classification_and_bad_hashes(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-invalid-change-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "invalid-change")
            _append_row(
                root / "docs/lks-sdd/04-delivery/planning-coverage.md",
                "| ID | State | Classification",
                "| PCH-001 | proposed | observation-only | FR-001 | TASK-001 | invalid | invalid | ADR-001 | Not a confirmed classification |",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            self.assertEqual(planning["integrity"], "invalid")
            self.assertTrue(
                any("Classification debe ser" in item for item in planning["integrity_errors"])
            )
            self.assertEqual(
                sum("debe ser SHA-256" in item for item in planning["integrity_errors"]),
                2,
            )

    def test_authorization_rejects_a_proposed_decision(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-proposed-auth-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "proposed-authorization")
            _append_row(
                root / "docs/lks-sdd/03-solution/solution-overview.md",
                "| ID | State | Decision",
                "| ADR-099 | proposed | Candidate implementation authorization | FR-001 | Pending human confirmation |",
            )
            code, result = run_json(
                PLANNING_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "authorize",
                "--authorization-id",
                "AUTH-001",
                "--task",
                "TASK-001",
                "--date",
                "2026-08-22",
                "--actor-role",
                "release-owner",
                "--decision",
                "ADR-099",
                "--constraints",
                "Only the selected task",
                "--preview",
                expected_codes={2},
            )
            self.assertEqual(code, 2)
            self.assertIn("no una propuesta", result["error"])

    def test_plan_change_stales_authorization_without_operational_noise(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-plan-change-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "plan-change")
            _authorize(root, "TASK-001")
            _replace_row(
                root / "docs/lks-sdd/04-delivery/plans.md",
                "PLAN-001",
                "| PLAN-001 | active | Synthetic continuous delivery | continuous-evolution | 0.x | Deliver INC-001 and its revised integration objective | INC-001 | not-applicable: initial plan | fixture-owner | 2026-11-19 |",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            self.assertEqual(planning["status"], "stale")
            authorization = assess_authorization(manifest, planning, ["TASK-001"])
            self.assertEqual(authorization["status"], "invalidated")
            self.assertEqual(authorization["stale_authorizations"], ["AUTH-001"])

    def test_authorization_constraints_cannot_diverge_from_canonical_markdown(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-auth-constraints-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "authorization-constraints")
            _authorize(root, "TASK-001")
            planning_path = root / "docs/lks-sdd/04-delivery/planning-coverage.md"
            text = planning_path.read_text(encoding="utf-8")
            planning_path.write_text(
                text.replace(
                    "Only the listed tasks and current fingerprints",
                    "Silently widened authorization",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            self.assertEqual(planning["integrity"], "invalid")
            self.assertTrue(
                any(
                    "constraints diverge" in item
                    for item in planning["integrity_errors"]
                ),
                planning,
            )
            authorization = assess_authorization(
                manifest, planning, ["TASK-001"]
            )
            self.assertEqual(authorization["status"], "invalidated")

    def test_coverage_responsibility_change_stales_authorization(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-coverage-change-") as directory:
            root = Path(directory)
            _materialize_parallel_complete_plan(root)
            _authorize(root, "TASK-001")
            planning_path = root / "docs/lks-sdd/04-delivery/planning-coverage.md"
            text = planning_path.read_text(encoding="utf-8")
            planning_path.write_text(
                text.replace(
                    "Implement the first request path | Primary ownership remains with TASK-001",
                    "Implement and own the first request path | Ownership boundary revised for TASK-001",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            self.assertEqual(planning["status"], "stale")
            authorization = assess_authorization(manifest, planning, ["TASK-001"])
            self.assertEqual(authorization["status"], "invalidated")

    def test_task_overlap_requires_explicit_contributor_responsibility(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-overlap-") as directory:
            root = Path(directory)
            _materialize_parallel_complete_plan(root)
            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-002.md"
            text = detail_path.read_text(encoding="utf-8")
            detail_path.write_text(
                text.replace(
                    "| FR-002 | AC-002 |",
                    "| FR-001, FR-002 | AC-002 |",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            self.assertEqual(planning["integrity"], "invalid")
            self.assertTrue(
                any(
                    "Solapamiento de responsabilidad no declarado" in item
                    and "FR-001 -> TASK-002" in item
                    for item in planning["integrity_errors"]
                ),
                planning,
            )

    def test_release_objective_with_unassigned_scope_is_partial(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-release-gap-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "release-gap", confirm_plan=False)
            _add_calculator_scope(root)
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            planning = assess_planning(root, manifest, "INC-001")
            self.assertEqual(planning["target"]["release"], "REL-001")
            self.assertEqual(planning["status"], "partial")
            self.assertIn("FR-012", planning["coverage"]["unassigned_items"])
            self.assertTrue(
                any(gap["kind"] == "unassigned-contract" for gap in planning["gaps"])
            )

    def test_cancelled_dependency_does_not_unlock_task(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-cancelled-dependency-") as directory:
            root = Path(directory)
            _materialize_parallel_complete_plan(root)
            _transition(root, "TASK-001", "cancelled")
            before = (root / "docs/lks-sdd/04-delivery/tasks.md").read_bytes()
            rejected = _transition(
                root,
                "TASK-003",
                "ready",
                expected_codes={2},
            )
            self.assertEqual(rejected["status"], "error")
            self.assertIn("dependencia", rejected["error"].lower())
            self.assertEqual(
                (root / "docs/lks-sdd/04-delivery/tasks.md").read_bytes(), before
            )

    def test_critical_path_is_undetermined_without_confirmed_durations(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-no-estimates-") as directory:
            planning = _materialize_parallel_complete_plan(Path(directory))
            critical = planning["dependency_graph"]["critical_path"]
            self.assertEqual(critical["status"], "undetermined")
            self.assertIn("No hay duraciones confirmadas", critical["reason"])
            self.assertEqual(
                planning["dependency_graph"]["structural_longest_chain"],
                ["TASK-001", "TASK-003"],
            )

    def test_verified_slice_does_not_invite_partial_release_promotion(self):
        summary = verification_summary(
            {
                "classification": "verified",
                "checks": [
                    {"name": "task-gates", "status": "passed"}
                ],
                "planning": {
                    "status": "partial",
                    "integrity": "valid",
                    "coverage": {"unassigned_items": ["FR-012", "AC-012"]},
                },
            }
        )
        self.assertIn("planificación partial/valid", summary["pending"])
        self.assertTrue(
            any("FR-012" in item for item in summary["pending"])
        )
        self.assertIn("antes de verificar conjuntamente", summary["next_step"])
        self.assertIn("no autoriza ni completa la release", summary["human_decision"])


if __name__ == "__main__":
    unittest.main()
