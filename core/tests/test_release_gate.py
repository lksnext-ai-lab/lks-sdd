from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import run_release_gate  # noqa: E402
import build_candidate_package  # noqa: E402


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

    def test_candidate_technical_checks_start_concurrently(self) -> None:
        barrier = threading.Barrier(2, timeout=1)

        def result(check_id: str) -> dict:
            barrier.wait()
            return {
                "id": check_id,
                "status": "passed",
                "duration_seconds": 0.0,
                "timeout_seconds": 1,
                "detail": "",
                "command": check_id,
            }

        with (
            patch.object(
                run_release_gate,
                "_static_integrity",
                side_effect=lambda: result("static-integrity"),
            ),
            patch.object(
                run_release_gate,
                "_release_core",
                side_effect=lambda: result("release-core"),
            ),
        ):
            checks = run_release_gate._technical_checks("candidate")

        self.assertEqual(
            ["static-integrity", "release-core"],
            [check["id"] for check in checks],
        )

    def test_report_declares_parallel_technical_checks(self) -> None:
        technical_checks = [
            {
                "id": "static-integrity",
                "status": "passed",
                "duration_seconds": 1.0,
                "timeout_seconds": 360,
                "detail": "",
                "command": "static",
            },
            {
                "id": "release-core",
                "status": "passed",
                "duration_seconds": 2.0,
                "timeout_seconds": 180,
                "detail": "",
                "command": "core",
            },
        ]
        with (
            patch.object(
                run_release_gate,
                "_source_binding",
                return_value={"commit": "a" * 40, "tree_state": "clean"},
            ),
            patch.object(run_release_gate, "_plugin_version", return_value="2.0.3"),
            patch.object(
                run_release_gate, "_technical_checks", return_value=technical_checks
            ),
        ):
            report = run_release_gate.build_report(
                channel="candidate",
                evaluated_on="2026-09-19",
                approval_path=None,
            )

        self.assertEqual(
            {"technical_checks": "parallel", "worker_count": 2},
            report["execution"],
        )
        self.assertEqual(
            ["static-integrity", "release-core"],
            [check["id"] for check in report["checks"]],
        )

    def test_builder_accepts_parallel_execution_metadata(self) -> None:
        report = {
            "schema_version": "simple-release-gate-1.0",
            "plugin_version": "2.0.3",
            "evaluated_on": "2026-09-19",
            "channel": "candidate",
            "source": {"commit": "a" * 40, "tree_state": "clean"},
            "execution": {"technical_checks": "parallel", "worker_count": 2},
            "checks": [
                {
                    "id": "static-integrity",
                    "status": "passed",
                    "duration_seconds": 1.0,
                    "timeout_seconds": 360,
                    "detail": "",
                    "command": "static",
                },
                {
                    "id": "release-core",
                    "status": "passed",
                    "duration_seconds": 2.0,
                    "timeout_seconds": 180,
                    "detail": "",
                    "command": "core",
                },
            ],
            "gate": {"status": "passed", "blockers": []},
        }

        quality, _ = build_candidate_package._validated_simple_release_gate(
            report,
            b"{}",
            plugin_version="2.0.3",
            source_commit="a" * 40,
            build_date="2026-09-19",
        )

        self.assertEqual("candidate", quality["channel"])

if __name__ == "__main__":
    unittest.main()
