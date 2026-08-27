from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from build_candidate_package import PackageError, SECRET_PATTERNS, build  # noqa: E402
import run_quality_harness as quality_harness  # noqa: E402
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
                "route": "greenfield-certified-profile",
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
                "route": "candidate-or-external-profile",
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
            "previous_version": "0.12.0",
            "candidate_version": "0.13.0",
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


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _package_repository(root: Path) -> str:
    marketplace = {
        "name": "lks-sdd-development",
        "interface": {"displayName": "LKS-SDD Development"},
        "plugins": [
            {
                "name": "lks-sdd",
                "source": {"source": "local", "path": "./plugins/lks-sdd"},
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": "Developer Tools",
            }
        ],
    }
    manifest = {
        "name": "lks-sdd",
        "version": "0.9.0",
        "description": "Synthetic package fixture",
        "author": {"name": "LKS"},
        "skills": "./skills/",
    }
    files = {
        ".codex-plugin/plugin.json": (json.dumps(manifest) + "\n").encode(),
        ".gitignore": b"ignored.txt\n",
        "README.md": b"committed package source\n",
        "SECURITY.md": b"synthetic security policy\n",
        "SUPPORT.md": b"synthetic support policy\n",
        "distribution/marketplace.template.json": (
            json.dumps(marketplace) + "\n"
        ).encode(),
    }
    committed_quality_files = [
        "quality/baselines/v0.6.1.json",
        "quality/catalog.json",
        "quality/corpora/activation.json",
        "quality/corpora/definition-v0.9.0.json",
        "quality/fixture-manifest.json",
        "schemas/quality-report.schema.json",
    ]
    for relative in committed_quality_files:
        files[relative] = (PLUGIN_ROOT / relative).read_bytes()
    fixture_manifest = json.loads(
        files["quality/fixture-manifest.json"].decode("utf-8")
    )
    for fixture in fixture_manifest["fixtures"]:
        relative = f"tests/fixtures/{fixture['path']}"
        files[relative] = (PLUGIN_ROOT / relative).read_bytes()
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    _git(root, "init", "--quiet")
    _git(root, "config", "user.name", "Synthetic Test")
    _git(root, "config", "user.email", "synthetic@example.invalid")
    _git(root, "config", "commit.gpgsign", "false")
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "test: package fixture")
    return _git(root, "rev-parse", "HEAD")


def _forged_release_quality_report(
    path: Path,
    source_root: Path,
    source_commit: str,
    *,
    tree_state: str = "clean",
    gate_status: str = "passed",
) -> Path:
    baseline = json.loads(
        (source_root / "quality/baselines/v0.6.1.json").read_text(encoding="utf-8")
    )
    canonical_baseline = (
        json.dumps(baseline, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    passed = gate_status == "passed"
    report = {
        "schema_version": "1.1",
        "suite": "synthetic release gate",
        "plugin_version": "0.9.0",
        "evaluated_on": "2026-08-20",
        "channel": "candidate",
        "source": {"commit": source_commit, "tree_state": tree_state},
        "inputs": {
            "catalog_sha256": "1" * 64,
            "corpus_sha256": "2" * 64,
            "definition_corpus_sha256": "3" * 64,
            "fixture_manifest_sha256": "4" * 64,
            "observations_sha256": None,
            "pilot_summary_sha256": None,
            "baseline_sha256": hashlib.sha256(canonical_baseline).hexdigest(),
        },
        "checks": [],
        "channels": {
            "automated": {"status": "passed"},
            "fixture-integrity": {"status": "passed"},
            "profile-complete": {"status": "passed"},
            "regression": {"status": "passed"},
        },
        "metrics": {},
        "critical_failures": [],
        "comparison": {
            "baseline_version": "0.6.1",
            "baseline_commit": "7318ccc337570e296bffda68a8e49724bed94c99",
            "status": "passed",
            "comparisons": [],
            "regressions": [],
            "not_compared": [],
            "current_only": [],
        },
        "gate": {
            "status": gate_status,
            "eligible": passed,
            "blockers": [] if passed else ["synthetic failure"],
            "missing_evidence": [],
        },
    }
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def _harness_quality_report(
    path: Path, source_root: Path, source_commit: str
) -> Path:
    catalog = json.loads(
        (source_root / "quality/catalog.json").read_text(encoding="utf-8")
    )
    fixture_manifest = json.loads(
        (source_root / "quality/fixture-manifest.json").read_text(encoding="utf-8")
    )
    test_names = sorted(
        {
            reference.split(":", 1)[1]
            for case in [*catalog["cases"], *catalog["extension_cases"]]
            for reference in case["evidence"]
            if reference.startswith("test:")
        }
    )
    unit_results = [
        {
            "id": f"synthetic.AttestationTests.{name}",
            "name": name,
            "status": "passed",
        }
        for name in test_names
    ]
    for index in range(len(unit_results), 80):
        name = f"test_release_regression_{index:03d}"
        unit_results.append(
            {
                "id": f"synthetic.ReleaseTests.{name}",
                "name": name,
                "status": "passed",
            }
        )
    eval_results = [
        {"id": fixture["id"], "passed": True}
        for fixture in fixture_manifest["fixtures"]
        if fixture["id"].startswith("FX-M1-")
    ]

    def executed_check(check_id, _command, _json_output=False, _timeout=600):
        payload = None
        if check_id == "unit-tests":
            payload = {"passed": True, "results": unit_results}
        elif check_id == "deterministic-evals":
            payload = {"passed": True, "results": eval_results}
        elif check_id == "reference-profile-complete":
            payload = {"complete_gate": True}
        return (
            {
                "id": check_id,
                "status": "passed",
                "critical": True,
                "summary": "exit=0",
            },
            payload,
            "",
        )

    patched_paths = {
        "PLUGIN_ROOT": source_root,
        "CATALOG_PATH": source_root / "quality/catalog.json",
        "CORPUS_PATH": source_root / "quality/corpora/activation.json",
        "DEFINITION_CORPUS_PATH": source_root
        / "quality/corpora/definition-v0.9.0.json",
        "FIXTURE_MANIFEST_PATH": source_root / "quality/fixture-manifest.json",
        "MANIFEST_PATH": source_root / ".codex-plugin/plugin.json",
    }
    with patch.multiple(quality_harness, **patched_paths), patch.object(
        quality_harness, "_run_command", side_effect=executed_check
    ):
        report = quality_harness.build_report(
            "2026-08-20",
            "candidate",
            None,
            None,
            source_root / "quality/baselines/v0.6.1.json",
            True,
        )
    if report["source"] != {"commit": source_commit, "tree_state": "clean"}:
        raise AssertionError("El informe del harness no quedó ligado al repo sintético.")
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return path


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
    def test_secret_scanner_distinguishes_task_labels_from_openai_keys(self):
        benign = b"task-definitions-marked-incomplete"
        synthetic_key = b"credential=" + b"sk-" + (b"x" * 24)

        self.assertFalse(any(pattern.search(benign) for pattern in SECRET_PATTERNS))
        self.assertTrue(
            any(pattern.search(synthetic_key) for pattern in SECRET_PATTERNS)
        )

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
            source_root = root / "source"
            source_root.mkdir()
            source_commit = _package_repository(source_root)
            quality_report = _harness_quality_report(
                root / "quality-report.json", source_root, source_commit
            )
            with self.assertRaisesRegex(PackageError, "fuera del repositorio"):
                build(
                    source_root / "forbidden-output",
                    "2026-08-20",
                    source_commit,
                    source_root,
                    quality_report,
                )
            first = build(
                root / "first",
                "2026-08-20",
                source_commit,
                source_root,
                quality_report,
            )
            second = build(
                root / "second",
                "2026-08-20",
                source_commit,
                source_root,
                quality_report,
            )
            self.assertEqual(first["artifacts"], second["artifacts"])
            self.assertEqual(
                (root / "first" / "SHA256SUMS").read_text(encoding="utf-8"),
                (root / "second" / "SHA256SUMS").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "  release-manifest.json\n",
                (root / "first" / "SHA256SUMS").read_text(encoding="utf-8"),
            )
            checksum_entries = {}
            for line in (
                (root / "first" / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
            ):
                expected, relative = line.split(maxsplit=1)
                checksum_entries[relative] = expected
                self.assertEqual(
                    hashlib.sha256(
                        (root / "first" / relative).read_bytes()
                    ).hexdigest(),
                    expected,
                )
            self.assertEqual(
                set(checksum_entries),
                {
                    "lks-sdd-plugin-v0.9.0.zip",
                    "lks-sdd-marketplace-v0.9.0.zip",
                    "quality-report.json",
                    "release-manifest.json",
                },
            )
            self.assertEqual(
                (root / "first" / "quality-report.json").read_bytes(),
                quality_report.read_bytes(),
            )
            release_manifest = json.loads(
                (root / "first" / "release-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(release_manifest["quality"]["gate"], "passed")
            self.assertEqual(
                release_manifest["quality"]["baseline_commit"],
                "7318ccc337570e296bffda68a8e49724bed94c99",
            )
            marketplace_zip = root / "first" / "lks-sdd-marketplace-v0.9.0.zip"
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

    def test_candidate_builder_rejects_self_asserted_or_hollow_attestations(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-package-") as directory:
            root = Path(directory)
            source_root = root / "source"
            source_root.mkdir()
            source_commit = _package_repository(source_root)

            forged = _forged_release_quality_report(
                root / "forged.json", source_root, source_commit
            )
            with self.assertRaisesRegex(PackageError, "inputs comprometidos"):
                build(
                    root / "forged-output",
                    "2026-08-20",
                    source_commit,
                    source_root,
                    forged,
                )

            authentic = _harness_quality_report(
                root / "authentic.json", source_root, source_commit
            )
            authentic_payload = json.loads(authentic.read_text(encoding="utf-8"))
            hollow_variants = {
                "checks": {**authentic_payload, "checks": []},
                "metrics": {**authentic_payload, "metrics": {}},
                "evidence": json.loads(json.dumps(authentic_payload)),
            }
            hollow_variants["evidence"]["channels"]["automated"]["cases"][0][
                "evidence"
            ] = []
            for label, payload in hollow_variants.items():
                with self.subTest(label=label):
                    report_path = root / f"hollow-{label}.json"
                    report_path.write_text(
                        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
                    )
                    with self.assertRaises(PackageError):
                        build(
                            root / f"hollow-{label}-output",
                            "2026-08-20",
                            source_commit,
                            source_root,
                            report_path,
                        )
                    self.assertFalse((root / f"hollow-{label}-output").exists())

    def test_candidate_builder_requires_real_head_commit_and_clean_tree(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-package-") as directory:
            root = Path(directory)
            source_root = root / "source"
            source_root.mkdir()
            first_commit = _package_repository(source_root)
            quality_report = _harness_quality_report(
                root / "quality-report.json", source_root, first_commit
            )
            with self.assertRaisesRegex(PackageError, "Git no pudo ejecutar rev-parse"):
                build(
                    root / "missing",
                    "2026-08-20",
                    "0" * 40,
                    source_root,
                    quality_report,
                )
            self.assertFalse((root / "missing").exists())

            (source_root / "CHANGELOG.md").write_text(
                "second commit\n", encoding="utf-8"
            )
            _git(source_root, "add", "CHANGELOG.md")
            _git(source_root, "commit", "--quiet", "-m", "test: second commit")
            with self.assertRaisesRegex(PackageError, "debe coincidir con HEAD"):
                build(
                    root / "old-head",
                    "2026-08-20",
                    first_commit,
                    source_root,
                    quality_report,
                )
            self.assertFalse((root / "old-head").exists())

            head_commit = _git(source_root, "rev-parse", "HEAD")
            quality_report = _harness_quality_report(
                root / "quality-report.json", source_root, head_commit
            )
            (source_root / "README.md").write_text("dirty source\n", encoding="utf-8")
            with self.assertRaisesRegex(
                PackageError, "árbol de trabajo debe estar limpio"
            ):
                build(
                    root / "dirty",
                    "2026-08-20",
                    head_commit,
                    source_root,
                    quality_report,
                )
            self.assertFalse((root / "dirty").exists())

    def test_candidate_builder_requires_passed_quality_report_for_same_commit(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-package-") as directory:
            root = Path(directory)
            source_root = root / "source"
            source_root.mkdir()
            source_commit = _package_repository(source_root)

            with self.assertRaisesRegex(PackageError, "--quality-report"):
                build(root / "missing-report", "2026-08-20", source_commit, source_root)

            dirty_report = _harness_quality_report(
                root / "quality-report.json", source_root, source_commit
            )
            dirty_payload = json.loads(dirty_report.read_text(encoding="utf-8"))
            dirty_payload["source"]["tree_state"] = "dirty"
            dirty_report.write_text(
                json.dumps(dirty_payload, indent=2) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(PackageError, "árbol fuente clean"):
                build(
                    root / "dirty-report",
                    "2026-08-20",
                    source_commit,
                    source_root,
                    dirty_report,
                )

            mismatched_report = _harness_quality_report(
                root / "quality-report.json", source_root, source_commit
            )
            mismatched_payload = json.loads(
                mismatched_report.read_text(encoding="utf-8")
            )
            mismatched_payload["source"]["commit"] = "f" * 40
            mismatched_report.write_text(
                json.dumps(mismatched_payload, indent=2) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(PackageError, "commit fuente"):
                build(
                    root / "mismatched-report",
                    "2026-08-20",
                    source_commit,
                    source_root,
                    mismatched_report,
                )

            failed_report = _harness_quality_report(
                root / "quality-report.json", source_root, source_commit
            )
            failed_payload = json.loads(failed_report.read_text(encoding="utf-8"))
            failed_payload["gate"] = {
                "status": "failed",
                "eligible": False,
                "blockers": ["synthetic failure"],
                "missing_evidence": [],
            }
            failed_report.write_text(
                json.dumps(failed_payload, indent=2) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(PackageError, "gate candidate"):
                build(
                    root / "failed-report",
                    "2026-08-20",
                    source_commit,
                    source_root,
                    failed_report,
                )

    def test_candidate_builder_reads_exact_commit_not_ignored_workspace(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-package-") as directory:
            root = Path(directory)
            source_root = root / "source"
            source_root.mkdir()
            source_commit = _package_repository(source_root)
            quality_report = _harness_quality_report(
                root / "quality-report.json", source_root, source_commit
            )
            (source_root / "ignored.txt").write_text(
                "not committed\n", encoding="utf-8"
            )
            _git(
                source_root,
                "update-index",
                "--assume-unchanged",
                "README.md",
                ".codex-plugin/plugin.json",
            )
            (source_root / "README.md").write_text(
                "different worktree bytes\n", encoding="utf-8"
            )
            (source_root / ".codex-plugin" / "plugin.json").write_text(
                '{"name":"lks-sdd","version":"9.9.9"}\n', encoding="utf-8"
            )

            build(
                root / "built",
                "2026-08-20",
                source_commit,
                source_root,
                quality_report,
            )
            plugin_zip = root / "built" / "lks-sdd-plugin-v0.9.0.zip"
            with zipfile.ZipFile(plugin_zip) as archive:
                self.assertNotIn("lks-sdd/ignored.txt", archive.namelist())
                self.assertEqual(
                    archive.read("lks-sdd/README.md"),
                    b"committed package source\n",
                )
                committed_manifest = json.loads(
                    archive.read("lks-sdd/.codex-plugin/plugin.json")
                )
                self.assertEqual(committed_manifest["version"], "0.9.0")


if __name__ == "__main__":
    unittest.main()
