from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import release_observability  # noqa: E402


WORKFLOW_RUN = {
    "id": 42,
    "run_attempt": 1,
    "head_sha": "a" * 40,
    "head_branch": "v2.0.3",
    "created_at": "2026-09-19T07:00:00Z",
    "run_started_at": "2026-09-19T07:00:10Z",
    "updated_at": "2026-09-19T07:00:50Z",
}
WORKFLOW_JOBS = {
    "jobs": [
        {
            "name": "release",
            "started_at": "2026-09-19T07:00:10Z",
            "completed_at": "2026-09-19T07:00:50Z",
            "steps": [
                {
                    "name": "Install locked runtime dependencies",
                    "started_at": "2026-09-19T07:00:11Z",
                    "completed_at": "2026-09-19T07:00:15Z",
                },
                {
                    "name": "Compact release gate",
                    "started_at": "2026-09-19T07:00:16Z",
                    "completed_at": "2026-09-19T07:00:35Z",
                },
                {
                    "name": "Build and validate release package",
                    "started_at": "2026-09-19T07:00:36Z",
                    "completed_at": "2026-09-19T07:00:45Z",
                },
                {
                    "name": "Upload release evidence",
                    "started_at": "2026-09-19T07:00:46Z",
                    "completed_at": "2026-09-19T07:00:48Z",
                },
            ],
        }
    ]
}


class ReleaseObservabilityTests(unittest.TestCase):
    def test_report_measures_release_phases_and_preserves_review_unknown(self) -> None:
        report = release_observability.build_report(WORKFLOW_RUN, WORKFLOW_JOBS)

        self.assertEqual("release-observability-1.1", report["schema_version"])
        self.assertEqual("revalidated", report["validation"]["mode"])
        self.assertEqual(10.0, report["timings_seconds"]["queue"])
        self.assertEqual(4.0, report["timings_seconds"]["dependencies"])
        self.assertEqual(19.0, report["timings_seconds"]["gate"])
        self.assertEqual(9.0, report["timings_seconds"]["build"])
        self.assertEqual(2.0, report["timings_seconds"]["artifact_upload"])
        self.assertEqual("not-observed", report["unobserved"]["human_review"]["status"])

    def test_report_rejects_missing_required_release_step(self) -> None:
        jobs = deepcopy(WORKFLOW_JOBS)
        jobs["jobs"][0]["steps"] = jobs["jobs"][0]["steps"][:-1]

        with self.assertRaisesRegex(
            release_observability.ReleaseObservabilityError, "Upload release evidence"
        ):
            release_observability.build_report(WORKFLOW_RUN, jobs)

    def test_report_measures_reused_preflight_without_claiming_tag_gate(self) -> None:
        jobs = deepcopy(WORKFLOW_JOBS)
        steps = jobs["jobs"][0]["steps"]
        jobs["jobs"][0]["steps"] = [
            steps[0],
            {
            "name": "Resolve reusable stable preflight",
            "started_at": "2026-09-19T07:00:16Z",
            "completed_at": "2026-09-19T07:00:18Z",
            },
            {
            "name": "Verify reusable preflight evidence",
            "started_at": "2026-09-19T07:00:19Z",
            "completed_at": "2026-09-19T07:00:22Z",
            },
            steps[-1],
        ]

        report = release_observability.build_report(WORKFLOW_RUN, jobs)

        self.assertEqual("reused-stable-preflight", report["validation"]["mode"])
        self.assertEqual("not-run", report["validation"]["tag_gate"])
        self.assertEqual(2.0, report["timings_seconds"]["preflight_resolution"])
        self.assertEqual(3.0, report["timings_seconds"]["preflight_verification"])
        self.assertNotIn("gate", report["timings_seconds"])
        self.assertNotIn("build", report["timings_seconds"])


if __name__ == "__main__":
    unittest.main()
