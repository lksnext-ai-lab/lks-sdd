"""Approval, isolation contract, scope and operational-cost regressions."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import time
import unittest
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
from project_variants import (
    VariantError,
    CONFIG,
    diagnose,
    proposal,
    approval_preview,
    apply_approval,
    current_approval,
    approved_status,
    input_hashes,
    markdown,
    digest,
)
from variant_verification import verify, completion_fields, visual_check
from consumer_observer import validate_output
from variant_fixture import materialize


class ProjectVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.TemporaryDirectory(prefix="lks-variant-fixture-")
        cls.base_root = Path(cls.base.name)
        cls.config = materialize(cls.base_root)

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lks-variant-test-")
        self.root = Path(self.temp.name)
        shutil.copytree(self.base_root, self.root, dirs_exist_ok=True)
        self.addCleanup(self.temp.cleanup)

    def approve(self, stage="development"):
        preview = approval_preview(
            self.root,
            "VAR-001",
            "ENV-001",
            stage,
            actor="synthetic-owner",
            reason="Equivalent acknowledgement API in a different layout",
            risks="Dependency/runtime compatibility limited to the selected tests",
            expires=(date.today() + timedelta(days=10)).isoformat(),
        )
        apply_approval(self.root, preview, preview["preview_hash"])
        return preview

    @staticmethod
    def fake_run(root, gate, hashes, *, profile_id):
        # A deterministic transport double; real Docker is exercised by variant_docker_smoke.py.
        raw = json.dumps({"gate": gate["id"], "input": digest(hashes)}).encode()
        sha = hashlib.sha256(raw).hexdigest()
        return {
            "gate_id": gate["id"],
            "name": gate["id"],
            "status": "passed",
            "evidence_scopes": ["component"],
            "interface_ids": [],
            "observations": {"test_transport": "synthetic"},
            "artifacts": [{"path": "proof.json", "sha256": sha, "size": len(raw)}],
        }, {sha: raw}

    def test_unknown_version_and_additional_dependency_are_not_incompatible(self):
        with (
            mock.patch(
                "subprocess.Popen",
                side_effect=AssertionError("diagnostic launched a process"),
            ),
            mock.patch(
                "subprocess.run",
                side_effect=AssertionError("diagnostic launched a process"),
            ),
        ):
            start = time.monotonic()
            result = diagnose(self.root / "component", "API-FASTAPI-STATELESS-OCI")
        self.assertEqual(result["compatibility"], "unassessed-variant")
        self.assertGreaterEqual(len(result["differences"]), 2)
        self.assertFalse(result["profile_certification"]["consumer_certified"])
        self.assertLess(time.monotonic() - start, 2)

    def test_manifest_lock_contradiction_is_incompatible(self):
        (self.root / "component/requirements.lock").write_text(
            "fastapi==0.139.0\nattrs==25.3.0\n"
        )
        result = diagnose(self.root / "component", "API-FASTAPI-STATELESS-OCI")
        self.assertEqual(result["compatibility"], "incompatible")
        with self.assertRaises(VariantError):
            self.approve()

    def test_approval_is_durable_and_idempotent_and_never_global(self):
        preview = self.approve()
        again = apply_approval(self.root, preview, preview["preview_hash"])
        self.assertFalse(again["changed"])
        value = approved_status(self.root, "VAR-001", "ENV-001", "development")
        self.assertEqual(value["human_confirmations_required"], 0)
        self.assertFalse(value["profile_certification"]["consumer_certified"])
        self.assertEqual(
            len(
                list(
                    (self.root / "docs/lks-sdd/02-design/technology-approvals").glob(
                        "*.md"
                    )
                )
            ),
            1,
        )

    def test_changed_dependency_scope_observer_policy_require_review(self):
        self.approve()
        path = self.root / "component/requirements.lock"
        path.write_text(path.read_text() + "typing-extensions==4.15.0\n")
        self.assertEqual(
            approved_status(self.root, "VAR-001", "ENV-001", "development")[
                "human_confirmations_required"
            ],
            1,
        )
        with self.assertRaises(VariantError):
            verify(self.root, "VAR-001", "ENV-001", "development")
        (self.root / "observer.py").write_text("print('changed')\n")
        with self.assertRaisesRegex(VariantError, "Observer hash mismatch"):
            proposal(self.root, "VAR-001", "ENV-001", "development")

    def test_expiry_out_of_scope_and_wrong_actor_fail_closed(self):
        preview = self.approve()
        with self.assertRaises(VariantError):
            current_approval(
                self.root, preview, today=date.today() + timedelta(days=10)
            )
        for environment, stage in [
            ("ENV-999", "development"),
            ("ENV-001", "production"),
            ("ENV-001", "integration"),
        ]:
            with (
                self.subTest(environment=environment, stage=stage),
                self.assertRaises(VariantError),
            ):
                verify(self.root, "VAR-001", environment, stage)
        with self.assertRaises(VariantError):
            approval_preview(
                self.root,
                "VAR-001",
                "ENV-001",
                "development",
                actor="unauthorized",
                reason="test",
                risks="test",
                expires=(date.today() + timedelta(days=3)).isoformat(),
            )

    def test_tampered_approval_and_preview_hash_are_rejected(self):
        preview = self.approve()
        with self.assertRaises(VariantError):
            apply_approval(self.root, preview, "0" * 64)
        path = next(
            (self.root / "docs/lks-sdd/02-design/technology-approvals").glob("*.md")
        )
        path.write_text(path.read_text().replace("synthetic-owner", "someone-else"))
        with self.assertRaisesRegex(VariantError, "integrity"):
            current_approval(self.root, preview)

    def test_unapproved_and_strict_policy_cannot_execute(self):
        with mock.patch(
            "consumer_observer.execute", side_effect=AssertionError("must not run")
        ):
            with self.assertRaises(VariantError):
                verify(
                    self.root,
                    "VAR-001",
                    "ENV-001",
                    "development",
                    execute=True,
                    evidence_id="EVID-001",
                )
            config = copy.deepcopy(self.config)
            config["policy"]["mode"] = "strict"
            (self.root / CONFIG).write_bytes(markdown(config, "Strict"))
            with self.assertRaises(VariantError):
                self.approve()

    def test_development_defers_heavy_gate_and_reuses_without_execution(self):
        self.approve()
        with mock.patch(
            "consumer_observer.execute", side_effect=self.fake_run
        ) as runner:
            first = verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "development",
                execute=True,
                evidence_id="EVID-001",
            )
            self.assertEqual(first["status"], "not-verified")
            self.assertEqual(first["accounting"]["omitted"], 1)
            second = verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "development",
                execute=True,
                evidence_id="EVID-002",
            )
            self.assertEqual(second["processes_executed"], 0)
            self.assertEqual(runner.call_count, 1)
        with self.assertRaises(VariantError):
            completion_fields(
                self.root,
                json.loads((self.root / ".lks-sdd/project.json").read_text()),
                "TASK-001",
            )

    def test_integration_evidence_enables_only_policy_controlled_task_closure(self):
        self.approve("integration")
        with mock.patch(
            "consumer_observer.execute", side_effect=self.fake_run
        ) as runner:
            result = verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                execute=True,
                evidence_id="EVID-001",
            )
            self.assertEqual(result["status"], "verified-with-reservations")
            self.assertEqual(result["delivery_readiness"], "not-assessed")
            self.assertEqual(runner.call_count, 2)
        manifest = json.loads((self.root / ".lks-sdd/project.json").read_text())
        fields = completion_fields(self.root, manifest, "TASK-001")
        self.assertEqual(fields["evidence"], "EVID-001")
        evidence = json.loads(
            (self.root / "docs/lks-sdd/evidence/EVID-001.json").read_text()
        )
        self.assertEqual(evidence["profile_certification"]["consumer_certified"], False)
        (self.root / "component/service.py").write_text(
            "raise RuntimeError('regression')\n"
        )
        with self.assertRaises(VariantError):
            completion_fields(self.root, manifest, "TASK-001")

    def test_tampered_artifacts_cannot_be_reused(self):
        self.approve("integration")
        with mock.patch("consumer_observer.execute", side_effect=self.fake_run):
            verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                execute=True,
                evidence_id="EVID-001",
            )
        artifact = next(
            (self.root / "docs/lks-sdd/evidence/variant-artifacts").iterdir()
        )
        artifact.write_bytes(b"tampered")
        with self.assertRaisesRegex(VariantError, "hash mismatch"):
            verify(self.root, "VAR-001", "ENV-001", "integration")

    def test_observer_contract_rejects_forged_scopes_nonce_and_artifacts(self):
        gate = self.config["variants"][0]["gates"][0]
        (self.root / "artifact").write_bytes(b"proof")
        value = {
            "schema_version": "1.0",
            "gate_id": gate["id"],
            "run_nonce": "a" * 32,
            "status": "passed",
            "scopes": ["component"],
            "interfaces": [],
            "observations": {"assertions": 2},
            "artifacts": [
                {"path": "artifact", "sha256": hashlib.sha256(b"proof").hexdigest()}
            ],
        }
        self.assertEqual(
            validate_output(value, gate, "a" * 32, self.root)["status"], "passed"
        )
        for changed in [
            {"run_nonce": "b" * 32},
            {"scopes": ["persistence"]},
            {"task_status": "done"},
            {"artifacts": [{"path": "artifact", "sha256": "0" * 64}]},
        ]:
            with self.subTest(changed=changed), self.assertRaises(VariantError):
                validate_output({**value, **changed}, gate, "a" * 32, self.root)

    def test_snapshot_cannot_mount_canonical_or_private_inputs(self):
        for path in [
            ".lks-sdd/project.json",
            "docs/lks-sdd/04-delivery/tasks.md",
            "../outside",
        ]:
            with self.subTest(path=path), self.assertRaises(VariantError):
                input_hashes(self.root, [path])

    def test_exact_profile_diagnosis_retains_certification_without_approval(self):
        result = diagnose(
            ROOT / "profiles/WEB-REACT-VITE-STATIC/scaffold", "WEB-REACT-VITE-STATIC"
        )
        self.assertEqual(result["compatibility"], "exact-certified")
        self.assertEqual(result["differences"], [])

    def test_failed_gate_never_becomes_passed_or_reusable(self):
        self.approve("integration")

        def failed(root, gate, hashes, *, profile_id):
            check, blobs = self.fake_run(root, gate, hashes, profile_id=profile_id)
            if gate["id"] == "GATE-API-TEST":
                check["status"] = "blocked"
            return check, blobs

        with mock.patch("consumer_observer.execute", side_effect=failed):
            first = verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                execute=True,
                evidence_id="EVID-001",
            )
        self.assertEqual(first["status"], "not-verified")
        planned = verify(self.root, "VAR-001", "ENV-001", "integration")
        dispositions = {c["gate_id"]: c["disposition"] for c in planned["checks"]}
        self.assertEqual(dispositions["GATE-API-TEST"], "execute")
        self.assertEqual(dispositions["GATE-API-OPENAPI"], "reused")

    def test_policy_can_forbid_closure_even_when_all_gates_pass(self):
        config = copy.deepcopy(self.config)
        config["policy"]["allow_task_closure"] = False
        (self.root / CONFIG).write_bytes(markdown(config, "No local closure"))
        self.approve("integration")
        with mock.patch("consumer_observer.execute", side_effect=self.fake_run):
            verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                execute=True,
                evidence_id="EVID-001",
            )
        with self.assertRaisesRegex(VariantError, "does not allow"):
            completion_fields(
                self.root,
                json.loads((self.root / ".lks-sdd/project.json").read_text()),
                "TASK-001",
            )

    def test_evidence_mutation_and_code_race_are_detected(self):
        self.approve("integration")
        before = (self.root / ".lks-sdd/project.json").read_bytes()

        def race(root, gate, hashes, *, profile_id):
            (root / "component/service.py").write_text(
                "# changed during verification\n"
            )
            return self.fake_run(root, gate, hashes, profile_id=profile_id)

        with (
            mock.patch("consumer_observer.execute", side_effect=race),
            self.assertRaisesRegex(VariantError, "changed during"),
        ):
            verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                execute=True,
                evidence_id="EVID-001",
            )
        self.assertEqual((self.root / ".lks-sdd/project.json").read_bytes(), before)
        self.assertFalse((self.root / "docs/lks-sdd/evidence/EVID-001.json").exists())

    def test_release_expands_required_gates_and_never_inherits_development(self):
        config = copy.deepcopy(self.config)
        config["policy"]["allowed_stages"].append("release")
        (self.root / CONFIG).write_bytes(markdown(config, "Release policy"))
        self.approve()
        with self.assertRaises(VariantError):
            verify(self.root, "VAR-001", "ENV-001", "release")
        self.approve("release")
        value = verify(self.root, "VAR-001", "ENV-001", "release")
        self.assertIn("GATE-OCI-BUILD", value["missing_critical_gates"])
        self.assertTrue(all(c["disposition"] == "execute" for c in value["checks"]))

    def test_experimental_observer_and_force_without_reason_are_rejected(self):
        self.approve()
        with self.assertRaisesRegex(VariantError, "reason"):
            verify(self.root, "VAR-001", "ENV-001", "development", force=True)
        config = copy.deepcopy(self.config)
        config["variants"][0]["gates"][0]["source"] = "experimental"
        (self.root / CONFIG).write_bytes(markdown(config, "Experimental"))
        with self.assertRaisesRegex(VariantError, "Experimental"):
            self.approve()

    def test_cold_preparation_preserves_consumer_and_registers_execution(self):
        from variant_preparation import prepare

        with tempfile.TemporaryDirectory(prefix="lks-variant-cold-") as directory:
            root = Path(directory).resolve()
            materialize(root, start_legacy=False)
            before = input_hashes(root, ["component", "observer.py"])
            approval = approval_preview(
                root,
                "VAR-001",
                "ENV-001",
                "development",
                actor="synthetic-owner",
                reason="Equivalent service",
                risks="Scoped validation",
                expires=(date.today() + timedelta(days=3)).isoformat(),
            )
            apply_approval(root, approval, approval["preview_hash"])
            preview = prepare(root, "VAR-001")
            with self.assertRaises(VariantError):
                prepare(root, "VAR-001", apply=True, preview_hash="wrong")
            applied = prepare(
                root, "VAR-001", apply=True, preview_hash=preview["preview_hash"]
            )
            self.assertEqual(applied["execution_id"], "EXEC-001")
            self.assertEqual(input_hashes(root, ["component", "observer.py"]), before)
            self.assertFalse((root / "pyproject.toml").exists())
            self.assertEqual(prepare(root, "VAR-001")["status"], "already-started")

    def test_cli_does_not_accept_allow_unvalidated_as_approval(self):
        from manage_project_variants import main

        with mock.patch("sys.stderr"), self.assertRaises(SystemExit) as caught:
            main(
                [
                    "verify",
                    str(self.root),
                    "--variant",
                    "VAR-001",
                    "--allow-unvalidated",
                ]
            )
        self.assertEqual(caught.exception.code, 2)

    def test_cache_retains_observation_age_and_expired_ids_are_immutable(self):
        self.approve("integration")
        with mock.patch("consumer_observer.execute", side_effect=self.fake_run):
            verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                execute=True,
                evidence_id="EVID-001",
            )
        original = json.loads(
            (self.root / "docs/lks-sdd/evidence/EVID-001.json").read_text()
        )
        with mock.patch(
            "consumer_observer.execute", side_effect=AssertionError("must reuse")
        ):
            verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                execute=True,
                evidence_id="EVID-002",
                reuse_evidence="EVID-001",
            )
        repeated = json.loads(
            (self.root / "docs/lks-sdd/evidence/EVID-002.json").read_text()
        )
        self.assertEqual(
            [c["observed_at"] for c in original["checks"]],
            [c["observed_at"] for c in repeated["checks"]],
        )
        # Time advances, not evidence bytes: recording a reuse never extends the TTL.
        future = datetime.now(timezone.utc) + timedelta(days=3)
        with mock.patch("variant_verification.datetime") as clock:
            clock.now.return_value = future
            clock.fromisoformat.side_effect = datetime.fromisoformat
            planned = verify(self.root, "VAR-001", "ENV-001", "integration")
            self.assertTrue(
                all(c["disposition"] == "execute" for c in planned["checks"])
            )
            with self.assertRaisesRegex(VariantError, "immutable"):
                verify(
                    self.root,
                    "VAR-001",
                    "ENV-001",
                    "integration",
                    execute=True,
                    evidence_id="EVID-002",
                )
        with self.assertRaisesRegex(VariantError, "absent"):
            verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                reuse_evidence="EVID-999",
            )

    def test_failed_preflight_persists_a_real_attributable_artifact(self):
        self.approve("integration")

        def blocked(root, gate, hashes, *, profile_id):
            return {
                "name": gate["id"],
                "gate_id": gate["id"],
                "status": "blocked",
                "evidence_scopes": ["component"],
                "interface_ids": [],
                "artifacts": [],
            }, {}

        with mock.patch("consumer_observer.execute", side_effect=blocked):
            result = verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                execute=True,
                evidence_id="EVID-001",
            )
        self.assertEqual(result["status"], "not-verified")
        evidence = json.loads(
            (self.root / "docs/lks-sdd/evidence/EVID-001.json").read_text()
        )
        for check in evidence["checks"]:
            artifact = check["artifacts"][0]
            raw = (self.root / artifact["evidence_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), artifact["sha256"])
            self.assertEqual(json.loads(raw)["status"], "blocked")

    def test_visual_review_uses_existing_canonical_contract_and_real_hashes(self):
        from test_validation_evidence_v016 import VisualEvidencePolicyV016Tests
        from delivery_engine import repository_revision

        fixture = VisualEvidencePolicyV016Tests(
            methodName="test_frontend_one_image_is_accepted"
        )
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        path, review = fixture._review(1)
        context = {
            "root": fixture.root,
            "manifest": fixture.manifest,
            "definitions": fixture.definitions,
            "delivery": fixture.delivery,
        }
        variant = {"task_ids": ["TASK-001"], "increment": "INC-001"}
        check, _ = visual_check(
            fixture.root,
            context,
            variant,
            path.relative_to(fixture.root).as_posix(),
            repository_revision(fixture.root),
        )
        self.assertEqual(check["status"], "passed")
        self.assertIn(review["screenshots"][0]["path"], check["visual_input_hashes"])
        (fixture.root / review["screenshots"][0]["path"]).write_bytes(b"tampered")
        with self.assertRaisesRegex(VariantError, "Invalid visual evidence"):
            visual_check(
                fixture.root,
                context,
                variant,
                path.relative_to(fixture.root).as_posix(),
            )
        config = copy.deepcopy(self.config)
        config["variants"][0]["gates"][0]["id"] = "GATE-VISUAL-BROWSER-REVIEW"
        (self.root / CONFIG).write_bytes(markdown(config, "Forbidden self-approval"))
        with self.assertRaisesRegex(VariantError, "cannot be replaced"):
            self.approve()

    def test_development_bundle_includes_variant_runtime_and_contracts(self):
        from build_dual_distribution import collect_development

        core = collect_development(ROOT)
        for path in (
            "scripts/project_variants.py",
            "scripts/variant_verification.py",
            "schemas/project-variants.schema.json",
            "docs/PROJECT-VARIANTS.md",
        ):
            self.assertIn(path, core)

    def test_nondeterministic_checks_cannot_use_same_id_or_cache_as_new_execution(self):
        config = copy.deepcopy(self.config)
        config["variants"][0]["gates"][0]["deterministic"] = False
        (self.root / CONFIG).write_bytes(markdown(config, "Nondeterministic gate"))
        self.approve("integration")
        with mock.patch(
            "consumer_observer.execute", side_effect=self.fake_run
        ) as runner:
            verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                execute=True,
                evidence_id="EVID-001",
            )
            with self.assertRaisesRegex(VariantError, "immutable"):
                verify(
                    self.root,
                    "VAR-001",
                    "ENV-001",
                    "integration",
                    execute=True,
                    evidence_id="EVID-001",
                )
            repeated = verify(
                self.root,
                "VAR-001",
                "ENV-001",
                "integration",
                execute=True,
                evidence_id="EVID-002",
            )
        self.assertEqual(repeated["processes_executed"], 1)
        self.assertEqual(runner.call_count, 3)

    def test_public_cli_verifies_and_variant_work_does_not_reuse_strict_history(self):
        from manage_project_variants import forward_verify
        from work_task import _verification_arguments
        from contextlib import redirect_stdout
        import io

        self.approve("integration")
        arguments = _verification_arguments(
            self.root, "TASK-001", ["--stage", "integration"]
        )
        self.assertIn("--variant", arguments)
        with (
            mock.patch("consumer_observer.execute", side_effect=self.fake_run),
            redirect_stdout(io.StringIO()) as output,
        ):
            code = forward_verify([str(self.root), *arguments])
        self.assertEqual(code, 0, output.getvalue())
        self.assertEqual(
            json.loads(output.getvalue())["verification_result"],
            "verified-with-reservations",
        )
        status = {
            "audit": {
                "manifest": {
                    "verification": {"evidence_ids": ["EVID-999"]},
                    "active_increment": "INC-001",
                }
            },
            "current_task": {"human_decision": "Ninguna"},
        }
        legacy = self.root / "docs/lks-sdd/evidence/EVID-999.json"
        legacy.write_text(json.dumps({"verification_subject": {"legacy": True}}))
        with mock.patch("work_task.load_status", return_value=status):
            inherited = _verification_arguments(self.root, "TASK-001", [])
        self.assertNotIn("--reuse-evidence", inherited)


if __name__ == "__main__":
    unittest.main()
