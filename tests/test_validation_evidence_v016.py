from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "tests"))

from delivery_engine import repository_revision, validate_delivery_contract  # noqa: E402
from experience_engine import load_status, management_json, verification_subject  # noqa: E402
from test_product_experience_v015 import create_representative_fixture  # noqa: E402
import test_visual_contract as visual_fixture  # noqa: E402
from validation_evidence import (  # noqa: E402
    DEFAULT_VISUAL_POLICY,
    derive_task_summaries,
    task_health,
    validate_visual_review_v12,
)


class VisualEvidencePolicyV016Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = visual_fixture.VisualContractTests(methodName="test_confirmed_visual_contract_is_ready_and_fingerprinted")
        self.base.setUp()
        self.root = self.base.root
        self.docs = self.base.docs
        self.base._materialize_visual_contract()
        self.validator = visual_fixture._load_validator_module()
        report, self.manifest, self.definitions = self.validator.validate_project(self.root)
        self.assertTrue(report.valid, report.errors)
        self.delivery = validate_delivery_contract(self.root, self.manifest)
        self.assertEqual(self.delivery["errors"], [])

    def tearDown(self) -> None:
        self.base.tearDown()

    def _review(self, count: int, *, result: str = "passed", duplicate_reason: str | None = "same pixels, distinct governed state") -> tuple[Path, dict]:
        visual_root = self.docs / "evidence" / "visual"
        visual_root.mkdir(parents=True, exist_ok=True)
        revision_value = repository_revision(self.root)
        revision = {
            "revision": revision_value["revision"],
            "tree_id": revision_value["tree_id"],
            "tree_sha256": revision_value["tree_sha256"],
        }
        reviewer = {"role": "quality-reviewer", "alias": "reviewer-a"}
        screenshots = []
        shot_ids = []
        for index in range(1, count + 1):
            shot_id = f"SHOT-{index:03d}"
            image_path = visual_root / f"task-001-{index}.png"
            image_path.write_bytes(visual_fixture.PNG_BYTES)
            shot_ids.append(shot_id)
            screenshots.append(
                {
                    "id": shot_id,
                    "task_ids": ["TASK-001"],
                    "acceptance_ids": ["AC-001"],
                    "ux_ids": [],
                    "vis_ids": [],
                    "path": image_path.relative_to(self.root).as_posix(),
                    "sha256": hashlib.sha256(visual_fixture.PNG_BYTES).hexdigest(),
                    "surface": "synthetic request form",
                    "route": "/request",
                    "prior_state": f"state-{index}",
                    "interaction": "submit the synthetic request",
                    "expected": "acknowledgement is visible",
                    "observed": "acknowledgement is visible" if result == "passed" else "acknowledgement is absent",
                    "expectation_match": result == "passed",
                    "theme": "light",
                    "viewport": {"width": 1, "height": 1, "dpr": 1, "capture": "viewport"},
                    "dimensions": {"width": 1, "height": 1},
                    "browser": {"name": "Synthetic Browser", "version": "1.0"},
                    "revision": revision,
                    "reviewed_at": "2026-08-29T10:00:00+02:00",
                    "reviewer": reviewer,
                    "result": result,
                    "limitations": [],
                    "legibility": "readable",
                    "duplicate_justification": duplicate_reason if count > 1 else None,
                    "supersedes": None,
                }
            )
        value = {
            "schema_version": "1.2",
            "increment": "INC-001",
            "status": result,
            "review_type": "manual-browser",
            "reviewed_at": "2026-08-29T10:00:00+02:00",
            "reviewer": reviewer,
            "revision": revision,
            "task_reviews": [
                {
                    "task_id": "TASK-001",
                    "status": result,
                    "acceptance_ids": ["AC-001"],
                    "ux_ids": [],
                    "vis_ids": [],
                    "screenshots": shot_ids,
                    "not_applicable_reason": None,
                }
            ],
            "screenshots": screenshots,
            "limitations": [],
        }
        path = visual_root / f"review-{count}-{result}.json"
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        return path, value

    def _validate(self, path: Path):
        return self.validator.validate_visual_review_evidence(
            self.root,
            self.manifest,
            self.definitions,
            "INC-001",
            path,
            require_fresh=False,
            task_ids=["TASK-001"],
            policies={"TASK-001": dict(DEFAULT_VISUAL_POLICY)},
        )

    def test_frontend_zero_images_is_rejected(self):
        path, _ = self._review(0)
        errors, outcome, _, _ = self._validate(path)
        self.assertIsNone(outcome)
        self.assertTrue(any("al menos 1 imagen" in item for item in errors))

    def test_frontend_one_image_is_accepted(self):
        path, _ = self._review(1)
        errors, outcome, _, _ = self._validate(path)
        self.assertEqual(errors, [])
        self.assertEqual(outcome["task_coverage"][0]["image_count"], 1)

    def test_frontend_five_images_is_accepted(self):
        path, _ = self._review(5)
        errors, outcome, _, _ = self._validate(path)
        self.assertEqual(errors, [])
        self.assertEqual(outcome["task_coverage"][0]["image_count"], 5)

    def test_frontend_six_images_is_controlled_rejection(self):
        path, _ = self._review(6)
        errors, outcome, _, _ = self._validate(path)
        self.assertIsNone(outcome)
        self.assertTrue(any("demasiado amplia" in item and "priorice" in item for item in errors))

    def test_duplicate_image_without_justification_is_rejected(self):
        path, _ = self._review(2, duplicate_reason=None)
        errors, _, _, _ = self._validate(path)
        self.assertTrue(any("duplicadas sin justificación" in item for item in errors))

    def test_missing_file_and_wrong_hash_are_rejected(self):
        path, value = self._review(1)
        image = self.root / value["screenshots"][0]["path"]
        image.unlink()
        errors, _, _, _ = self._validate(path)
        self.assertTrue(any("archivo inexistente" in item for item in errors))
        image.write_bytes(visual_fixture.PNG_BYTES)
        value["screenshots"][0]["sha256"] = "0" * 64
        path.write_text(json.dumps(value), encoding="utf-8")
        errors, _, _, _ = self._validate(path)
        self.assertTrue(any("SHA-256 no coincide" in item for item in errors))

    def test_executed_failure_is_preserved_as_failed_outcome(self):
        path, _ = self._review(1, result="failed")
        errors, outcome, _, _ = self._validate(path)
        self.assertEqual(errors, [])
        self.assertEqual(outcome["status"], "failed")

    def test_passed_cannot_contradict_observed_behavior(self):
        path, value = self._review(1)
        value["screenshots"][0]["expectation_match"] = False
        path.write_text(json.dumps(value), encoding="utf-8")
        errors, _, _, _ = self._validate(path)
        self.assertTrue(any("passed contradice" in item for item in errors))

    def test_correction_replaces_failed_capture_for_same_state(self):
        old_path, old = self._review(1, result="failed")
        new_path, new = self._review(1, result="passed")
        new["screenshots"][0]["supersedes"] = {
            "evidence": old_path.relative_to(self.root).as_posix(),
            "screenshot_id": "SHOT-001",
            "sha256": old["screenshots"][0]["sha256"],
        }
        # A replacement must be new bytes. The alternative valid PNG is taken
        # from the established generic visual fixture.
        ALT_PNG_BYTES = visual_fixture.ALT_PNG_BYTES
        image = self.root / new["screenshots"][0]["path"]
        image.write_bytes(ALT_PNG_BYTES)
        new["screenshots"][0]["sha256"] = hashlib.sha256(ALT_PNG_BYTES).hexdigest()
        new_path.write_text(json.dumps(new), encoding="utf-8")
        errors, outcome, _, _ = self._validate(new_path)
        self.assertEqual(errors, [])
        self.assertEqual(len(outcome["screenshots"]), 1)

    def test_joint_release_reuses_one_image_without_duplication(self):
        visual_root = self.docs / "evidence" / "visual"
        visual_root.mkdir(parents=True, exist_ok=True)
        image_path = visual_root / "joint.png"
        image_path.write_bytes(visual_fixture.PNG_BYTES)
        revision_value = repository_revision(self.root)
        revision = {key: revision_value[key] for key in ("revision", "tree_id", "tree_sha256")}
        reviewer = {"role": "quality-reviewer", "alias": "reviewer-a"}
        delivery = {
            "tasks": {
                "TASK-001": {"Profile binding": "BIND-001", "Unit": "UNIT-001"},
                "TASK-002": {"Profile binding": "BIND-001", "Unit": "UNIT-001"},
            },
            "task_details": {
                task: {"definition": [{"Acceptance": acceptance, "Required capabilities": "CAP-FRONTEND-QUALITY", "Technical gates": "GATE-BROWSER-SMOKE"}]}
                for task, acceptance in (("TASK-001", "AC-001"), ("TASK-002", "AC-002"))
            },
            "bindings": {"BIND-001": {"profile_id": "WEB-REACT-VITE-STATIC"}},
            "units": {},
        }
        shot = {
            "id": "SHOT-001", "task_ids": ["TASK-001", "TASK-002"],
            "acceptance_ids": ["AC-001", "AC-002"], "ux_ids": [], "vis_ids": [],
            "path": image_path.relative_to(self.root).as_posix(), "sha256": hashlib.sha256(visual_fixture.PNG_BYTES).hexdigest(),
            "surface": "shared release surface", "route": "/shared", "prior_state": "ready",
            "interaction": "open shared surface", "expected": "shared surface visible", "observed": "shared surface visible",
            "expectation_match": True, "theme": "light",
            "viewport": {"width": 1, "height": 1, "dpr": 1, "capture": "viewport"},
            "dimensions": {"width": 1, "height": 1}, "browser": {"name": "Synthetic Browser", "version": "1.0"},
            "revision": revision, "reviewed_at": "2026-08-29T10:00:00+02:00", "reviewer": reviewer,
            "result": "passed", "limitations": [], "legibility": "readable", "duplicate_justification": None, "supersedes": None,
        }
        value = {
            "schema_version": "1.2", "increment": "INC-001", "status": "passed", "review_type": "manual-browser",
            "reviewed_at": shot["reviewed_at"], "reviewer": reviewer, "revision": revision,
            "task_reviews": [
                {"task_id": task, "status": "passed", "acceptance_ids": [acceptance], "ux_ids": [], "vis_ids": [], "screenshots": ["SHOT-001"], "not_applicable_reason": None}
                for task, acceptance in (("TASK-001", "AC-001"), ("TASK-002", "AC-002"))
            ],
            "screenshots": [shot], "limitations": [],
        }
        errors, outcome, _, _ = validate_visual_review_v12(
            self.root, value, increment="INC-001", task_ids=["TASK-001", "TASK-002"],
            delivery=delivery, policies={task: dict(DEFAULT_VISUAL_POLICY) for task in ("TASK-001", "TASK-002")},
            expected_revision=revision,
            resolve_path=lambda requested: self.validator._visual_evidence_path(self.root, requested),
            image_signature=self.validator._image_signature,
        )
        self.assertEqual(errors, [])
        self.assertEqual(len(outcome["screenshots"]), 1)

    def test_backend_not_applicable_and_ux_reference_rejection(self):
        delivery = {
            "tasks": {"TASK-001": {"Profile binding": "BIND-001", "Unit": "UNIT-001"}},
            "task_details": {"TASK-001": {"definition": [{"Acceptance": "AC-001", "In scope": "backend API", "Required capabilities": "CAP-API-CONTRACT", "Technical gates": "GATE-API-TEST"}]}},
            "bindings": {"BIND-001": {"profile_id": "API-FASTAPI-STATELESS-OCI"}}, "units": {},
        }
        reason = "selected-tasks-have-no-ux-vis-frontend-browser-or-interface-unit-signals:TASK-001"
        value = {
            "schema_version": "1.2", "increment": "INC-001", "status": "passed", "review_type": "manual-browser",
            "reviewed_at": "2026-08-29T10:00:00+02:00", "reviewer": {"role": "quality-reviewer", "alias": "reviewer-a"},
            "revision": {"revision": "a" * 40, "tree_id": "b" * 40, "tree_sha256": "c" * 64},
            "task_reviews": [{"task_id": "TASK-001", "status": "not-applicable", "acceptance_ids": [], "ux_ids": [], "vis_ids": [], "screenshots": [], "not_applicable_reason": reason}],
            "screenshots": [], "limitations": [],
        }
        callbacks = {
            "resolve_path": lambda requested: self.validator._visual_evidence_path(self.root, requested),
            "image_signature": self.validator._image_signature,
        }
        errors, outcome, _, _ = validate_visual_review_v12(
            self.root, value, increment="INC-001", task_ids=["TASK-001"], delivery=delivery,
            policies={"TASK-001": dict(DEFAULT_VISUAL_POLICY)}, expected_revision=value["revision"], **callbacks,
        )
        self.assertEqual(errors, [])
        self.assertEqual(outcome["task_coverage"][0]["status"], "not-applicable")
        delivery["task_details"]["TASK-001"]["definition"][0]["Acceptance"] = "AC-001, UX-001"
        errors, _, _, _ = validate_visual_review_v12(
            self.root, value, increment="INC-001", task_ids=["TASK-001"], delivery=delivery,
            policies={"TASK-001": dict(DEFAULT_VISUAL_POLICY)}, expected_revision=value["revision"], **callbacks,
        )
        self.assertTrue(any("no puede ser not-applicable" in item for item in errors))


class EvidenceHealthAndSummaryV016Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="lks-sdd-v016-health-")
        self.root = Path(self.temporary.name)
        create_representative_fixture(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_project_without_active_task_returns_null(self):
        manifest_path = self.root / ".lks-sdd/project.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["active_task"] = None
        manifest["active_tasks"] = []
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertIsNone(management_json(load_status(self.root))["current_task"])

    def test_historical_verification_and_current_health_are_separate(self):
        evidence = [{"evidence_id": "EVID-001", "classification": "verified"}]
        verification = {"status": "verified", "task_ids": ["TASK-001"], "evidence_ids": ["EVID-001"]}
        healthy = task_health("TASK-001", evidence, [], verification)
        self.assertEqual(healthy["historical_verification"], "verified")
        self.assertEqual(healthy["current_health"], "healthy")
        compromised = task_health(
            "TASK-001", evidence,
            [{"ID": "PROB-001", "State": "active", "Description": "generic later finding"}],
            verification,
        )
        self.assertEqual(compromised["historical_verification"], "verified")
        self.assertEqual(compromised["current_health"], "compromised")
        self.assertTrue(compromised["pending_reverification"])

    def test_derived_summary_does_not_change_verification_subject(self):
        before = verification_subject(self.root, persist_cache=False)
        manifest = json.loads((self.root / ".lks-sdd/project.json").read_text(encoding="utf-8"))
        from delivery_engine import validate_delivery_contract
        delivery = validate_delivery_contract(self.root, manifest)
        summaries = derive_task_summaries(self.root, manifest, delivery)
        target = self.root / ".lks-sdd/summaries/task-evidence"
        target.mkdir(parents=True, exist_ok=True)
        for task_id, value in summaries.items():
            (target / f"{task_id}.json").write_text(json.dumps(value), encoding="utf-8")
        after = verification_subject(self.root, persist_cache=False)
        self.assertEqual(before["verification_subject_hash"], after["verification_subject_hash"])


class JiraEvidenceMilestoneV016Tests(unittest.TestCase):
    def test_not_verified_milestone_never_transitions_to_done(self):
        import jira_reporting_fixture as jira_fixture
        from eval_support import run_json
        from jira_reporting_engine import build_milestone_preview

        with tempfile.TemporaryDirectory(prefix="lks-sdd-v016-jira-") as temporary:
            root = Path(temporary)
            jira_fixture.prepare_started_project(root, "jira-v016-failed")
            transition_args = (
                str(root), "transition", "--task", "TASK-001", "--to", "in-review",
                "--reason", "generic implementation ready", "--actor", "synthetic-agent",
                "--date", "2026-08-29",
            )
            _, task_preview = run_json(
                PLUGIN_ROOT / "scripts/manage_tasks.py", *transition_args, "--preview"
            )
            run_json(
                PLUGIN_ROOT / "scripts/manage_tasks.py", *transition_args,
                "--apply", "--authorize", "--preview-hash", task_preview["preview_hash"],
            )
            jira_fixture.apply_preview(
                root,
                "configure-workflow",
                "--local-state", "in-review",
                "--jira-status-id", "3",
                "--jira-status-name", "In Review",
                "--decision", "ADR-901",
                "--date", "2026-08-29",
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
                        "revision": "a" * 40,
                        "classification": "not-verified",
                        "checks": [{"name": "synthetic-tests", "status": "failed"}],
                        "limitations": [],
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["verification"] = {
                "status": "not-verified", "increment": "INC-001", "task_ids": ["TASK-001"],
                "revision": "a" * 40, "tree_id": "b" * 40, "tree_sha256": "c" * 64,
                "build_id": "build-sha256:" + "d" * 64,
                "artifact_digests": ["sha256:" + "e" * 64], "environment": "not-applicable",
                "gate_ids": ["GATE-API-TEST"], "evidence_ids": ["EVID-001"], "limitations": [],
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            preview = build_milestone_preview(
                root,
                manifest,
                task_id="TASK-001",
                source_ref="EVID-001",
                event_kind="verification-failed",
            )
            self.assertEqual([item["action"] for item in preview["operations"]], ["comment"])
            body = preview["operations"][0]["payload"]["body"]
            self.assertIn("Resultado: not-verified", body)
            self.assertIn("Imágenes: 0", body)
