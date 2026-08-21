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
from eval_support import initialize, materialize_ready_increment  # noqa: E402

TASK_SCRIPT = PLUGIN_ROOT / "scripts" / "manage_tasks.py"


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


class TaskManagementV12Tests(unittest.TestCase):
    def test_professional_transition_flow_records_blocker_and_done_evidence(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-v12-") as directory:
            root = Path(directory)
            initialize(root, "task-flow")
            materialize_ready_increment(root)

            board = _run(root, "board")
            self.assertTrue(board["valid"], board["errors"])
            self.assertEqual(board["summary"]["workflow"], {"ready": 1})

            _transition(
                root,
                "in-progress",
                "--branch",
                "codex/task-001",
                "--revision-start",
                "1" * 40,
                "--progress",
                "25",
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
            self.assertIn("| PROB-001 | open |", detail)
            self.assertIn("External synthetic dependency unavailable", detail)

            _transition(root, "in-progress", "--progress", "50")
            _transition(root, "in-review", "--progress", "95")
            applied = _transition(
                root,
                "done",
                "--evidence",
                "EVID-001",
                "--revision",
                "2" * 40,
                "--build",
                "build-sha256:" + "3" * 64,
                "--artifact-digest",
                "sha256:" + "4" * 64,
                "--environment",
                "ENV-001",
                "--gate",
                "GATE-API-TEST",
                "--gate",
                "GATE-API-OPENAPI",
            )
            self.assertTrue(applied["changed"])
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
            self.assertIn("| AC-001 | GATE-API-TEST, GATE-API-OPENAPI | passed |", detail)
            self.assertIn("| 2026-08-21 | in-review | done |", detail)

    def test_invalid_transition_and_table_injection_leave_files_unchanged(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-task-guard-") as directory:
            root = Path(directory)
            initialize(root, "task-guard")
            materialize_ready_increment(root)
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
            self.assertEqual({path: path.read_bytes() for path in watched}, before)


if __name__ == "__main__":
    unittest.main()
