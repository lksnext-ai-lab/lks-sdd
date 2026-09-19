from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import run_release_gate  # noqa: E402


class ReleaseGateTests(unittest.TestCase):
    def test_source_binding_rejects_uncommitted_files(self) -> None:
        with patch.object(
            run_release_gate, "_git", return_value=" M scripts/run_release_gate.py"
        ):
            with self.assertRaisesRegex(run_release_gate.ReleaseGateError, "checkout limpio"):
                run_release_gate._source_binding()

    def test_approval_requires_matching_unblocked_stable_release(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            approval_path = Path(temporary) / "approval.json"
            approval_path.write_text(
                json.dumps(
                    {
                        "release_version": "2.0.2",
                        "scope": "stable-release",
                        "decision": {"status": "approved", "blocking_findings": []},
                    }
                ),
                encoding="utf-8",
            )
            run_release_gate._approved_release(approval_path, "2.0.2")

            approval_path.write_text(
                json.dumps(
                    {
                        "release_version": "2.0.1",
                        "scope": "stable-release",
                        "decision": {"status": "approved", "blocking_findings": []},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                run_release_gate.ReleaseGateError, "sin bloqueantes"
            ):
                run_release_gate._approved_release(approval_path, "2.0.2")

    def test_release_core_accepts_exact_declared_inventory(self) -> None:
        stdout = json.dumps(
            {
                "passed": True,
                "results": [
                    {"id": test_id, "status": "passed"}
                    for test_id in run_release_gate.CORE_TESTS
                ],
            }
        )
        with patch.object(
            run_release_gate,
            "_run",
            return_value={"status": "passed", "detail": "", "_stdout": stdout},
        ):
            result = run_release_gate._release_core()
        self.assertEqual("passed", result["status"])

    def test_release_core_rejects_incomplete_inventory(self) -> None:
        stdout = json.dumps(
            {
                "passed": True,
                "results": [
                    {"id": test_id, "status": "passed"}
                    for test_id in run_release_gate.CORE_TESTS[:-1]
                ],
            }
        )
        with patch.object(
            run_release_gate,
            "_run",
            return_value={"status": "passed", "detail": "", "_stdout": stdout},
        ):
            result = run_release_gate._release_core()
        self.assertEqual("failed", result["status"])
        self.assertIn("exactamente", result["detail"])


if __name__ == "__main__":
    unittest.main()
