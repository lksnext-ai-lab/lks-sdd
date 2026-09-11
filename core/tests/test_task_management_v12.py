from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "tests"))

from delivery_engine import validate_delivery_contract  # noqa: E402
from eval_support import (  # noqa: E402
    IMPLEMENT_SCRIPT,
    _append_row,
    authorize_implementation,
    initialize,
    materialize_ready_project,
    materialize_ready_increment,
    run_json,
)
from planning_engine import assess_planning  # noqa: E402

TASK_SCRIPT = PLUGIN_ROOT / "scripts" / "manage_tasks.py"
VERIFIED_REVISION = "2" * 40
VERIFIED_BUILD = "build-sha256:" + "3" * 64
VERIFIED_ARTIFACT = "sha256:" + "4" * 64
VERIFIED_GATES = [
    "GATE-API-TEST",
    "GATE-API-OPENAPI",
    "GATE-OCI-BUILD",
]


def _run(root: Path, *arguments: str, expected: int = 0) -> dict:
    process = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(TASK_SCRIPT),
            str(root),
            *arguments,
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if process.returncode != expected:
        raise AssertionError(
            f"exit={process.returncode}\nstdout={process.stdout}\nstderr={process.stderr}"
        )
    return json.loads(process.stdout)


def _transition(root: Path, target: str, *extra: str) -> dict:
    common = (
        "transition",
        "--task",
        "TASK-001",
        "--to",
        target,
        "--reason",
        f"Move task to {target}",
        "--actor",
        "fixture-authority",
        "--date",
        "2026-08-21",
        *extra,
    )
    preview = _run(root, *common, "--preview")
    return _run(
        root,
        *common,
        "--apply",
        "--authorize",
        "--preview-hash",
        preview["preview_hash"],
    )


def _start_implementation(root: Path) -> dict:
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
    return applied


def _record_verified_evidence(root: Path) -> None:
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


def _replace_task_row(root: Path, prefix: str, replacement: str) -> None:
    path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = replacement
            path.write_text(
                "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
            )
            return
    raise AssertionError(f"Task row not found: {prefix}")


class TaskManagementV12Tests(unittest.TestCase):
    def test_execution_transition_requires_current_authorization(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-auth-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "task-auth")

            rejected = _run(
                root,
                "transition",
                "--task",
                "TASK-001",
                "--to",
                "in-progress",
                "--reason",
                "Start without authorization",
                "--actor",
                "fixture-authority",
                "--date",
                "2026-08-21",
                "--preview",
                expected=2,
            )

            self.assertEqual(rejected["status"], "error")
            self.assertIn("AUTH-### vigente", rejected["error"])

    def test_professional_transition_flow_records_blocker_and_done_evidence(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-v12-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "task-flow")
            authorize_implementation(root)
            _start_implementation(root)

            board = _run(root, "board")
            self.assertTrue(board["valid"], board["errors"])
            self.assertEqual(board["summary"]["workflow"], {"in-progress": 1})
            self.assertEqual(
                board["plans"]["PLAN-001"][0]["Progress"],
                "0",
                "Starting a task must not invent a progress percentage.",
            )

            _transition(
                root,
                "blocked",
                "--blocker",
                "External synthetic dependency unavailable",
                "--progress",
                "25",
            )
            detail = (
                root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            ).read_text(encoding="utf-8")
            self.assertIn("| PROB-001 | active |", detail)
            self.assertIn("External synthetic dependency unavailable", detail)

            _transition(root, "in-progress", "--progress", "50")
            _transition(root, "in-review", "--progress", "95")
            rejected = _run(
                root,
                "transition",
                "--task",
                "TASK-001",
                "--to",
                "done",
                "--reason",
                "Claim done before verification",
                "--actor",
                "fixture-authority",
                "--date",
                "2026-08-21",
                "--evidence",
                "EVID-001",
                "--revision",
                VERIFIED_REVISION,
                "--build",
                VERIFIED_BUILD,
                "--artifact-digest",
                VERIFIED_ARTIFACT,
                "--environment",
                "ENV-001",
                "--gate",
                VERIFIED_GATES[0],
                "--gate",
                VERIFIED_GATES[1],
                "--gate",
                VERIFIED_GATES[2],
                "--preview",
                expected=2,
            )
            self.assertIn("verificación canónica", rejected["error"])
            _record_verified_evidence(root)
            incomplete_gates = _run(
                root,
                "transition",
                "--task",
                "TASK-001",
                "--to",
                "done",
                "--reason",
                "Claim done without every declared gate",
                "--actor",
                "fixture-authority",
                "--date",
                "2026-08-21",
                "--evidence",
                "EVID-001",
                "--revision",
                VERIFIED_REVISION,
                "--build",
                VERIFIED_BUILD,
                "--artifact-digest",
                VERIFIED_ARTIFACT,
                "--environment",
                "ENV-001",
                "--gate",
                VERIFIED_GATES[0],
                "--preview",
                expected=2,
            )
            self.assertIn("todos los gates técnicos", incomplete_gates["error"])
            unfinished_deliverable = _run(
                root,
                "transition",
                "--task",
                "TASK-001",
                "--to",
                "done",
                "--reason",
                "Claim done with a pending deliverable",
                "--actor",
                "fixture-authority",
                "--date",
                "2026-08-21",
                "--evidence",
                "EVID-001",
                "--revision",
                VERIFIED_REVISION,
                "--build",
                VERIFIED_BUILD,
                "--artifact-digest",
                VERIFIED_ARTIFACT,
                "--environment",
                "ENV-001",
                "--gate",
                VERIFIED_GATES[0],
                "--gate",
                VERIFIED_GATES[1],
                "--gate",
                VERIFIED_GATES[2],
                "--preview",
                expected=2,
            )
            self.assertIn("entregables terminados", unfinished_deliverable["error"])
            _replace_task_row(
                root,
                "| Acknowledgement behavior and tests | pending |",
                "| Acknowledgement behavior and tests | done | AC-001 | TEST-001 | EVID-001 | Verified output |",
            )
            open_problem = _run(
                root,
                "transition",
                "--task",
                "TASK-001",
                "--to",
                "done",
                "--reason",
                "Claim done with an open problem",
                "--actor",
                "fixture-authority",
                "--date",
                "2026-08-21",
                "--evidence",
                "EVID-001",
                "--revision",
                VERIFIED_REVISION,
                "--build",
                VERIFIED_BUILD,
                "--artifact-digest",
                VERIFIED_ARTIFACT,
                "--environment",
                "ENV-001",
                "--gate",
                VERIFIED_GATES[0],
                "--gate",
                VERIFIED_GATES[1],
                "--gate",
                VERIFIED_GATES[2],
                "--preview",
                expected=2,
            )
            self.assertIn("problemas abiertos", open_problem["error"])
            _replace_task_row(
                root,
                "| PROB-001 | active |",
                "| PROB-001 | resolved | External synthetic dependency unavailable | Synthetic fixture validation | fixture-authority | Resolve blocker and record evidence | EVID-001 |",
            )
            applied = _transition(
                root,
                "done",
                "--evidence",
                "EVID-001",
                "--revision",
                VERIFIED_REVISION,
                "--build",
                VERIFIED_BUILD,
                "--artifact-digest",
                VERIFIED_ARTIFACT,
                "--environment",
                "ENV-001",
                "--gate",
                "GATE-API-TEST",
                "--gate",
                "GATE-API-OPENAPI",
                "--gate",
                "GATE-OCI-BUILD",
            )
            self.assertTrue(applied["changed"])
            self.assertEqual(
                applied["transition_summary"]["where_we_are"],
                "release-tasks-complete",
            )
            self.assertIn(
                "verificación conjunta",
                applied["transition_summary"]["next_step"],
            )
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            delivery = validate_delivery_contract(root, manifest)
            self.assertEqual(delivery["errors"], [])
            self.assertEqual(delivery["tasks"]["TASK-001"]["Workflow state"], "done")
            self.assertIsNone(manifest["active_task"])
            detail = (
                root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "| AC-001 | GATE-API-TEST, GATE-API-OPENAPI, GATE-OCI-BUILD | passed |",
                detail,
            )
            self.assertIn("| 2026-08-21 | in-review | done |", detail)

    def test_invalid_transition_and_table_injection_leave_files_unchanged(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-guard-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "task-guard")
            authorize_implementation(root)
            _start_implementation(root)
            _transition(
                root,
                "blocked",
                "--blocker",
                "Synthetic blocker for transition guards",
            )
            watched = [
                root / ".lks-sdd/project.json",
                root / "docs/lks-sdd/04-delivery/tasks.md",
                root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md",
            ]
            before = {path: path.read_bytes() for path in watched}
            invalid = _run(
                root,
                "transition",
                "--task",
                "TASK-001",
                "--to",
                "done",
                "--reason",
                "Skip review",
                "--actor",
                "fixture-authority",
                "--date",
                "2026-08-21",
                "--preview",
                expected=2,
            )
            self.assertEqual(invalid["status"], "error")
            injected = _run(
                root,
                "transition",
                "--task",
                "TASK-001",
                "--to",
                "in-progress",
                "--reason",
                "unsafe | cell",
                "--actor",
                "fixture-authority",
                "--date",
                "2026-08-21",
                "--preview",
                expected=2,
            )
            self.assertIn("barras de tabla", injected["error"])
            unsafe_task = _run(
                root,
                "transition",
                "--task",
                "../../outside",
                "--to",
                "in-progress",
                "--reason",
                "unsafe path",
                "--actor",
                "fixture-authority",
                "--date",
                "2026-08-21",
                "--preview",
                expected=2,
            )
            self.assertIn("TASK-###", unsafe_task["error"])
            self.assertEqual({path: path.read_bytes() for path in watched}, before)

    def test_done_reopens_only_for_an_exact_confirmed_original_contract_failure(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-reopen-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "task-reopen")
            authorize_implementation(root)
            _start_implementation(root)
            _transition(root, "in-review")
            _record_verified_evidence(root)
            _replace_task_row(
                root,
                "| Acknowledgement behavior and tests | pending |",
                "| Acknowledgement behavior and tests | done | AC-001 | TEST-001 | EVID-001 | Verified output |",
            )
            _transition(
                root,
                "done",
                "--evidence",
                "EVID-001",
                "--revision",
                VERIFIED_REVISION,
                "--build",
                VERIFIED_BUILD,
                "--artifact-digest",
                VERIFIED_ARTIFACT,
                "--environment",
                "ENV-001",
                *(item for gate in VERIFIED_GATES for item in ("--gate", gate)),
            )

            detail_path = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
            detail_text = detail_path.read_text(encoding="utf-8")
            detail_path.write_text(
                detail_text.replace(
                    "AC-001 passed with required gates",
                    "AC-001 passed with required gates and repaired original behavior",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous = manifest["planning"]["planning_fingerprint"]
            changed = assess_planning(root, manifest, "INC-001")
            self.assertEqual(changed["status"], "stale")
            current = changed["planning_fingerprint"]
            _append_row(
                root / "docs/lks-sdd/04-delivery/planning-coverage.md",
                "| ID | State | Classification",
                f"| PCH-001 | confirmed | original-contract-failure | AC-001 | TASK-001 | {previous} | {current} | ADR-001 | Verified original behavior requires repair |",
            )
            planning_path = root / "docs/lks-sdd/04-delivery/planning-coverage.md"
            planning_text = planning_path.read_text(encoding="utf-8")
            planning_path.write_text(
                planning_text.replace(
                    "| AUTH-001 | authorized |",
                    "| AUTH-001 | invalidated |",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            manifest["authorizations"][0]["state"] = "invalidated"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            impacted = assess_planning(root, manifest, "INC-001")
            self.assertEqual(
                impacted["change_impact"]["affected_tasks"], ["TASK-001"]
            )

            reopened = _transition(
                root,
                "backlog",
                "--classification",
                "original-contract-failure",
                "--change-id",
                "PCH-001",
            )
            self.assertEqual(reopened["from"], "done")
            self.assertEqual(reopened["to"], "backlog")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            delivery = validate_delivery_contract(root, manifest)
            self.assertEqual(
                delivery["tasks"]["TASK-001"]["Workflow state"], "backlog"
            )
            self.assertEqual(
                delivery["tasks"]["TASK-001"]["Progress"], "100"
            )
            self.assertIsNone(manifest["planning"]["planning_fingerprint"])
            self.assertEqual(manifest["planning"]["last_change"], "PCH-001")
            self.assertEqual(manifest["executions"][0]["status"], "completed")
            self.assertEqual(manifest["implementation"]["status"], "blocked")
            self.assertEqual(manifest["verification"]["status"], "not-verified")
            self.assertIn(
                "prior evidence remains historical",
                " ".join(manifest["verification"]["limitations"]),
            )
            detail = detail_path.read_text(encoding="utf-8")
            self.assertIn("| stale |", detail)
            self.assertIn("PCH-001: original-contract-failure", detail)


if __name__ == "__main__":
    unittest.main()
