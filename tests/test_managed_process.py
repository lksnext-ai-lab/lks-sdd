from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from quality_execution import run_managed_command  # noqa: E402


def _pid_exists(pid: int) -> bool:
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=10,
        )
        return result.returncode == 0 and str(pid) in result.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


class ManagedProcessTests(unittest.TestCase):
    def test_timeout_terminates_the_descendant_process_tree(self):
        child_code = "import time; time.sleep(60)"
        parent_code = (
            "import subprocess,sys,time; "
            f"p=subprocess.Popen([sys.executable,'-c',{child_code!r}]); "
            "print(p.pid, flush=True); time.sleep(60)"
        )
        progress = io.StringIO()
        started = time.monotonic()
        result = run_managed_command(
            [sys.executable, "-c", parent_code],
            cwd=PLUGIN_ROOT,
            timeout=0.5,
            heartbeat_seconds=0.1,
            grace_seconds=2,
            label="synthetic-process-tree",
            progress_stream=progress,
        )
        self.assertTrue(result.timed_out)
        self.assertEqual(result.process_cleanup, "confirmed")
        self.assertLess(time.monotonic() - started, 8)
        child_pid = int(result.stdout.strip().splitlines()[0])
        for _ in range(20):
            if not _pid_exists(child_pid):
                break
            time.sleep(0.05)
        self.assertFalse(_pid_exists(child_pid))
        self.assertIn("HEARTBEAT synthetic-process-tree", progress.getvalue())

    def test_normal_command_preserves_stdout_for_machine_json(self):
        progress = io.StringIO()
        result = run_managed_command(
            [sys.executable, "-c", "print('{\"passed\": true}')"],
            cwd=PLUGIN_ROOT,
            timeout=5,
            label="synthetic-json",
            progress_stream=progress,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), '{"passed": true}')
        self.assertEqual(result.termination, "normal")
        self.assertIn("START synthetic-json", progress.getvalue())

    def test_runner_keeps_stdout_json_while_stderr_names_current_test(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(PLUGIN_ROOT / "tests/run_unit_tests.py"),
                "--suite",
                "fast",
                "--test",
                "test_registry_assigns_every_module_exactly_once",
            ],
            cwd=PLUGIN_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
            timeout=30,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(payload["passed"])
        self.assertIn("TEST test_quality_suite_registry", completed.stderr)
        self.assertIn("START fast:test_quality_suite_registry", completed.stderr)


if __name__ == "__main__":
    unittest.main()
