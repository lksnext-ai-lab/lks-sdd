from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import verify_preflight_provenance  # noqa: E402


SOURCE_COMMIT = "c" * 40
VERSION = "2.0.3"
REPOSITORY = "lksnext-ai-lab/lks-sdd"


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _run(run_id: int, updated_at: str, *, source_commit: str = SOURCE_COMMIT) -> dict:
    return {
        "id": run_id,
        "run_attempt": 1,
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "head_sha": source_commit,
        "head_branch": "main",
        "updated_at": updated_at,
        "repository": {"full_name": REPOSITORY},
    }


def _evidence(root: Path) -> tuple[Path, Path, dict]:
    evidence = root / "evidence"
    candidate = evidence / "candidate"
    candidate.mkdir(parents=True)
    manifest = {
        "plugin_version": VERSION,
        "source_commit": SOURCE_COMMIT,
        "artifacts": [],
    }
    manifest_bytes = json.dumps(manifest).encode("utf-8")
    (candidate / "release-manifest.json").write_bytes(manifest_bytes)
    (evidence / "release-readiness.json").write_text(
        json.dumps(
            {
                "readiness": "ready",
                "channel": "stable",
                "source_commit": SOURCE_COMMIT,
                "version": VERSION,
                "checks": [
                    {"id": check_id, "status": "passed"}
                    for check_id in (
                        "contract",
                        "distribution",
                        "worktree",
                        "approval",
                        "source",
                        "release-tag",
                    )
                ],
            }
        ),
        encoding="utf-8",
    )
    (evidence / "preflight-provenance.json").write_text(
        json.dumps(
            {
                "schema_version": "preflight-provenance-1.0",
                "workflow": "quality",
                "event": "workflow_dispatch",
                "run_id": 20,
                "run_attempt": 1,
                "source_commit": SOURCE_COMMIT,
                "source_ref": "main",
                "plugin_version": VERSION,
                "channel": "stable",
            }
        ),
        encoding="utf-8",
    )
    (evidence / "release-package-validation.json").write_text(
        json.dumps(
            {
                "schema_version": "release-package-validation-1.0",
                "status": "passed",
                "plugin_version": VERSION,
                "source_commit": SOURCE_COMMIT,
                "release_manifest_sha256": _sha256(manifest_bytes),
                "checks": [
                    {"id": "copilot-package", "status": "passed"},
                    {"id": "plugin-bundle", "status": "passed"},
                    {"id": "marketplace-bundle", "status": "passed"},
                ],
            }
        ),
        encoding="utf-8",
    )
    changelog = root / "CHANGELOG.md"
    changelog.write_text(f"## {VERSION}\n\n- Release.\n", encoding="utf-8")
    selection = {
        "schema_version": "preflight-run-selection-1.0",
        "status": "found",
        "run": {
            "id": 20,
            "run_attempt": 1,
            "event": "workflow_dispatch",
            "head_sha": SOURCE_COMMIT,
            "head_branch": "main",
            "updated_at": "2026-09-19T07:10:00Z",
            "repository": REPOSITORY,
        },
    }
    return evidence, changelog, selection


class PreflightProvenanceTests(unittest.TestCase):
    def test_selects_newest_matching_manual_run(self) -> None:
        selection = verify_preflight_provenance.select_run(
            {
                "workflow_runs": [
                    _run(10, "2026-09-19T07:00:00Z"),
                    _run(20, "2026-09-19T07:10:00Z"),
                    _run(30, "2026-09-19T07:20:00Z", source_commit="d" * 40),
                ]
            },
            source_commit=SOURCE_COMMIT,
            default_branch="main",
            repository=REPOSITORY,
        )

        self.assertEqual("found", selection["status"])
        self.assertEqual(20, selection["run"]["id"])

    def test_missing_when_no_exact_preflight_exists(self) -> None:
        selection = verify_preflight_provenance.select_run(
            {"workflow_runs": [_run(10, "2026-09-19T07:00:00Z", source_commit="d" * 40)]},
            source_commit=SOURCE_COMMIT,
            default_branch="main",
            repository=REPOSITORY,
        )

        self.assertEqual(
            {
                "schema_version": "preflight-run-selection-1.0",
                "status": "missing",
                "reason": "No existe un stable-preflight correcto para este SHA.",
            },
            selection,
        )

    def test_ignores_preflight_from_another_repository(self) -> None:
        run = _run(10, "2026-09-19T07:00:00Z")
        run["repository"]["full_name"] = "other/repository"

        selection = verify_preflight_provenance.select_run(
            {"workflow_runs": [run]},
            source_commit=SOURCE_COMMIT,
            default_branch="main",
            repository=REPOSITORY,
        )

        self.assertEqual("missing", selection["status"])

    def test_reads_paginated_github_cli_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "workflow-runs.json"
            output.write_text(
                "\n".join(
                    json.dumps(run)
                    for run in (
                        _run(10, "2026-09-19T07:00:00Z"),
                        _run(20, "2026-09-19T07:10:00Z"),
                    )
                ),
                encoding="utf-8",
            )

            payload = verify_preflight_provenance._read_json(
                output, "workflow-runs"
            )
            selection = verify_preflight_provenance.select_run(
                payload,
                source_commit=SOURCE_COMMIT,
                default_branch="main",
                repository=REPOSITORY,
            )

        self.assertEqual(20, selection["run"]["id"])

    @patch.object(verify_preflight_provenance.verify_draft_promotion, "build_plan")
    def test_verification_binds_selected_run_and_package_report(self, build_plan) -> None:
        build_plan.return_value = {"plugin_version": VERSION}
        with tempfile.TemporaryDirectory() as temporary:
            evidence, changelog, selection = _evidence(Path(temporary))
            report = verify_preflight_provenance.verify_reusable_preflight(
                evidence,
                selection,
                tag="v2.0.3",
                source_commit=SOURCE_COMMIT,
                changelog=changelog,
            )

        self.assertEqual("reused-stable-preflight", report["mode"])
        self.assertEqual(20, report["preflight"]["run_id"])

    @patch.object(verify_preflight_provenance.verify_draft_promotion, "build_plan")
    def test_mismatched_preflight_run_blocks_reuse(self, build_plan) -> None:
        build_plan.return_value = {"plugin_version": VERSION}
        with tempfile.TemporaryDirectory() as temporary:
            evidence, changelog, selection = _evidence(Path(temporary))
            selection["run"]["id"] = 21
            with self.assertRaisesRegex(
                verify_preflight_provenance.PreflightProvenanceError,
                "no coincide",
            ):
                verify_preflight_provenance.verify_reusable_preflight(
                    evidence,
                    selection,
                    tag="v2.0.3",
                    source_commit=SOURCE_COMMIT,
                    changelog=changelog,
                )

    @patch.object(verify_preflight_provenance.verify_draft_promotion, "build_plan")
    def test_incomplete_readiness_blocks_reuse(self, build_plan) -> None:
        build_plan.return_value = {"plugin_version": VERSION}
        with tempfile.TemporaryDirectory() as temporary:
            evidence, changelog, selection = _evidence(Path(temporary))
            readiness_path = evidence / "release-readiness.json"
            readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
            readiness["checks"] = readiness["checks"][:-1]
            readiness_path.write_text(json.dumps(readiness), encoding="utf-8")
            with self.assertRaisesRegex(
                verify_preflight_provenance.PreflightProvenanceError,
                "readiness",
            ):
                verify_preflight_provenance.verify_reusable_preflight(
                    evidence,
                    selection,
                    tag="v2.0.3",
                    source_commit=SOURCE_COMMIT,
                    changelog=changelog,
                )

    def test_fallback_provenance_is_explicit(self) -> None:
        result = verify_preflight_provenance.fallback_provenance(
            tag="v2.0.3",
            source_commit=SOURCE_COMMIT,
            plugin_version=VERSION,
            reason="preflight-missing",
        )

        self.assertEqual("revalidated-after-missing-preflight", result["mode"])
        self.assertEqual("preflight-missing", result["reason"])


if __name__ == "__main__":
    unittest.main()
