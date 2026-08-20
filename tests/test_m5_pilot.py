from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from build_candidate_package import build  # noqa: E402
from manage_pilot import (  # noqa: E402
    PilotError,
    decide,
    record_observation,
    summarize,
    validate_config,
    validate_observation,
)


def _valid_config() -> dict:
    participants = [f"USR-{index:03d}" for index in range(1, 6)]
    return {
        "schema_version": "1.0",
        "pilot_id": "pilot-lks-sdd-001",
        "status": "running",
        "duration_weeks": 8,
        "projects": [
            {
                "code": "PRJ-001",
                "route": "greenfield-h0",
                "environment": "synthetic",
                "data_classification": "synthetic",
                "authorization_confirmed": True,
            },
            {
                "code": "PRJ-002",
                "route": "adopt-existing",
                "environment": "sanitized-copy",
                "data_classification": "sanitized-internal",
                "authorization_confirmed": True,
            },
            {
                "code": "PRJ-003",
                "route": "alternative-stack",
                "environment": "non-production",
                "data_classification": "sanitized-internal",
                "authorization_confirmed": True,
            },
        ],
        "participants": participants,
        "roles": {
            "method_owner": "USR-001",
            "product_owner": "USR-002",
            "maintainer": "USR-003",
            "security_reviewer": "USR-004",
            "quality_reviewer": "USR-005",
            "workspace_admin": "USR-001",
            "support_owner": "USR-002",
        },
        "support": {
            "non_sensitive_url": "https://github.com/lksnext-ai-lab/lks-sdd/issues",
            "security_url": "https://security.example.invalid/lks-sdd",
        },
        "rollback": {
            "previous_version": "0.5.0",
            "candidate_version": "0.6.0",
            "package_sha256": "a" * 64,
            "procedure_confirmed": True,
        },
        "privacy": {
            "allow_client_content": False,
            "allow_secrets": False,
            "allow_personal_names": False,
            "retention_days": 90,
        },
    }


def _observation(index: int, project: dict, participant: str) -> dict:
    return {
        "schema_version": "1.0",
        "observation_id": f"OBS-{index:04d}",
        "pilot_id": "pilot-lks-sdd-001",
        "project_code": project["code"],
        "participant_code": participant,
        "week": min(index, 8),
        "route": project["route"],
        "metrics": {
            "activation_correct": True,
            "baseline_minutes": 60,
            "repeated_questions": 0,
            "open_points": 1,
            "incidents": 0,
            "documentation_load": "acceptable",
            "manual_changes": 1,
            "defects_before_codex": 1,
            "defects_after_codex": 0,
            "onboarding_completed": True,
            "sdd_comprehension": 4,
            "utility": 4,
            "clarity": 4,
            "confidence": 4,
            "reuse_intent": True,
            "document_quality": 4,
        },
        "outcomes": {
            "route_completed": True,
            "resume_correct": True,
            "edits_preserved": True,
            "permission_failures": 0,
            "build_passed": True,
            "tests_passed": True,
            "traceability_complete": True,
            "security_incidents": 0,
        },
    }


def _quality_report() -> dict:
    return {
        "metrics": {"critical_failures": 0, "profile_complete_gate": 1},
        "channels": {
            "activation": {"status": "passed"},
            "document-review": {"status": "passed"},
        },
    }


class M5PilotTests(unittest.TestCase):
    def test_example_config_is_explicitly_blocked(self):
        example = json.loads(
            (PLUGIN_ROOT / "pilot" / "pilot-config.example.json").read_text(
                encoding="utf-8"
            )
        )
        _, report = validate_config(example)
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["ready_to_start"])
        self.assertFalse(report["errors"])
        self.assertGreaterEqual(len(report["blockers"]), 5)

    def test_complete_sanitized_config_is_ready(self):
        _, report = validate_config(_valid_config())
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["project_count"], 3)
        self.assertEqual(report["participant_count"], 5)

    def test_observation_contract_rejects_free_text_fields(self):
        config = _valid_config()
        observation = _observation(1, config["projects"][0], "USR-001")
        observation["notes"] = "unstructured client content"
        with self.assertRaisesRegex(PilotError, "Campos de observación"):
            validate_observation(observation, config)

    def test_record_is_external_atomic_and_idempotent(self):
        config = _valid_config()
        observation = _observation(1, config["projects"][0], "USR-001")
        with tempfile.TemporaryDirectory(prefix="lks-sdd-pilot-") as directory:
            store = Path(directory)
            first = record_observation(config, observation, store)
            second = record_observation(config, observation, store)
            self.assertEqual(first["status"], "recorded")
            self.assertEqual(second["status"], "unchanged")
            stored = json.loads((store / "OBS-0001.json").read_text(encoding="utf-8"))
        self.assertEqual(stored, observation)

    def test_aggregate_summary_contains_no_project_or_participant_codes(self):
        config = _valid_config()
        with tempfile.TemporaryDirectory(prefix="lks-sdd-pilot-") as directory:
            store = Path(directory)
            for index, participant in enumerate(config["participants"], 1):
                project = config["projects"][(index - 1) % len(config["projects"])]
                record_observation(
                    config, _observation(index, project, participant), store
                )
            summary = summarize(config, store)
        encoded = json.dumps(summary)
        self.assertTrue(summary["sample_sufficient"])
        self.assertEqual(summary["project_count"], 3)
        self.assertEqual(summary["participant_count"], 5)
        self.assertNotIn("PRJ-", encoded)
        self.assertNotIn("USR-", encoded)

    def test_go_requires_complete_quality_and_pilot_evidence(self):
        config = _valid_config()
        with tempfile.TemporaryDirectory(prefix="lks-sdd-pilot-") as directory:
            store = Path(directory)
            for index, participant in enumerate(config["participants"], 1):
                project = config["projects"][(index - 1) % len(config["projects"])]
                record_observation(
                    config, _observation(index, project, participant), store
                )
            summary = summarize(config, store)
        result = decide(config, summary, _quality_report())
        self.assertEqual(result["decision"]["status"], "go")
        incomplete_quality = _quality_report()
        incomplete_quality["channels"]["activation"]["status"] = "not-run"
        conditioned = decide(config, summary, incomplete_quality)
        self.assertEqual(conditioned["decision"]["status"], "go-conditioned")

    def test_security_incident_forces_no_go(self):
        config = _valid_config()
        with tempfile.TemporaryDirectory(prefix="lks-sdd-pilot-") as directory:
            store = Path(directory)
            for index, participant in enumerate(config["participants"], 1):
                project = config["projects"][(index - 1) % len(config["projects"])]
                observation = _observation(index, project, participant)
                if index == 1:
                    observation["outcomes"]["security_incidents"] = 1
                record_observation(config, observation, store)
            summary = summarize(config, store)
        result = decide(config, summary, _quality_report())
        self.assertEqual(result["decision"]["status"], "no-go")
        self.assertTrue(
            any("seguridad" in blocker for blocker in result["decision"]["blockers"])
        )

    def test_candidate_bundles_are_reproducible_and_marketplace_valid(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-package-") as directory:
            root = Path(directory)
            source_commit = "0" * 40
            first = build(root / "first", "2026-08-20", source_commit)
            second = build(root / "second", "2026-08-20", source_commit)
            self.assertEqual(first["artifacts"], second["artifacts"])
            marketplace_zip = root / "first" / "lks-sdd-marketplace-v0.6.0.zip"
            with zipfile.ZipFile(marketplace_zip) as archive:
                names = set(archive.namelist())
                marketplace = json.loads(
                    archive.read(".agents/plugins/marketplace.json").decode("utf-8")
                )
            self.assertIn("plugins/lks-sdd/.codex-plugin/plugin.json", names)
            self.assertNotIn("plugins/lks-sdd/.git/config", names)
            self.assertEqual(
                marketplace["plugins"][0]["source"]["path"],
                "./plugins/lks-sdd",
            )


if __name__ == "__main__":
    unittest.main()
