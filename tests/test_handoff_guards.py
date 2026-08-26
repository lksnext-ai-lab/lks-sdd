from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from eval_support import (
    HELP_SCRIPT,
    IMPLEMENT_SCRIPT,
    READINESS_SCRIPT,
    VALIDATE_SCRIPT,
    VERIFY_SCRIPT,
    authorize_implementation,
    initialize,
    materialize_ready_increment,
    run_json,
    tree_digest,
)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TRACEABILITY_SCRIPT = PLUGIN_ROOT / "scripts" / "check_traceability.py"
PACKAGED_LOCK = (
    PLUGIN_ROOT
    / "profiles"
    / "API-FASTAPI-STATELESS-OCI"
    / "technology-profile.lock.json"
)


def _ready_project(root: Path) -> None:
    initialize(root, "handoff-guards")
    materialize_ready_increment(root)


def _downgrade_ready_project_to_legacy(root: Path) -> None:
    manifest_path = root / ".lks-sdd/project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current_version = manifest["plugin_version"]
    manifest.update(
        {
            "schema_version": "1.0",
            "method_version": "1.0.0",
            "plugin_version": "0.6.1",
            "open_blockers": [],
            "readiness": {
                "status": "not-assessed",
                "assessed_increment": None,
                "assessed_at": None,
            },
        }
    )
    for key in (
        "active_plan", "active_task", "active_tasks", "delivery_governance",
        "planning", "task_tracking", "authorizations", "executions",
    ):
        manifest.pop(key, None)
    manifest["technology"].pop("profile_bindings", None)
    manifest["version_control"] = {
        "type": manifest["version_control"]["type"],
        "origin": manifest["version_control"]["origin"],
    }
    v12_only = {
        "ART-ARCH",
        "ART-GOVERNANCE",
        "ART-PLANS",
        "ART-TASKS",
        "ART-TEST-STRATEGY",
        "ART-DEPLOYMENT",
        "ART-PLANNING",
        "ART-TRACKING",
    }
    manifest["artifacts"] = [
        item for item in manifest["artifacts"] if item["id"] not in v12_only
    ]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    for entry in manifest["artifacts"]:
        path = root / entry["path"]
        text = (
            path.read_text(encoding="utf-8")
            .replace('schema_version: "1.5"', 'schema_version: "1.0"', 1)
            .replace('method_version: "1.5.0"', 'method_version: "1.0.0"', 1)
            .replace(
                f'created_with_plugin_version: "{current_version}"',
                'created_with_plugin_version: "0.6.1"',
                1,
            )
        )
        if entry["id"] == "ART-INCREMENTS":
            if "## Aplicabilidad por dominio" in text:
                domain_start = text.index("## Aplicabilidad por dominio")
                interface_start = text.index(
                    "## Aplicabilidad de interfaz y contrato visual"
                )
                text = text[:domain_start] + text[interface_start:]
            text = text.replace(
                "| ID | State | In scope | Out of scope | Requirements | Acceptance | Decisions | Tests |\n"
                "|---|---|---|---|---|---|---|---|",
                "| ID | State | In scope | Out of scope | Requirements | Acceptance | Decisions | Data | Identity | Integrations | Tests |\n"
                "|---|---|---|---|---|---|---|---|---|---|---|",
                1,
            ).replace(
                "| INC-001 | confirmed | Submit and acknowledge one request | Reporting and administration | FR-001 | AC-001 | ADR-001 | TEST-001 |",
                "| INC-001 | confirmed | Submit and acknowledge one request | Reporting and administration | FR-001 | AC-001 | ADR-001 | not-applicable: no persistence | not-applicable: no identity | not-applicable: no integration | TEST-001 |",
                1,
            )
        for source, replacement in {
            "PLAN-001": "delivery horizon",
            "REL-001": "release horizon",
            "CHG-001": "governance transition",
            "ENV-001": "verification environment",
            "BIND-001": "technology binding",
            "UNIT-001": "deployable unit",
        }.items():
            text = text.replace(source, replacement)
        path.write_text(text, encoding="utf-8", newline="\n")


def _load_verification_module():
    spec = importlib.util.spec_from_file_location(
        "lks_sdd_handoff_verification", VERIFY_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_continuity_module():
    script = PLUGIN_ROOT / "scripts" / "manage_continuity.py"
    spec = importlib.util.spec_from_file_location(
        "lks_sdd_handoff_continuity", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    scripts_path = str(PLUGIN_ROOT / "scripts")
    sys.path.insert(0, scripts_path)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(scripts_path)
    return module


def _prepare_increment(root: Path) -> None:
    authorize_implementation(root)
    _, preview = run_json(
        IMPLEMENT_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "--dry-run",
    )
    _, applied = run_json(
        IMPLEMENT_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "--apply",
        "--authorize",
        "--preview-hash",
        preview["preview_hash"],
    )
    if applied["status"] != "prepared":
        raise AssertionError(applied)


class ContinuityCheckpointSchemaGuardsTests(unittest.TestCase):
    def test_checkpoint_schema_compatibility_is_directional(self) -> None:
        module = _load_continuity_module()

        for manifest_schema, checkpoint_schema in (
            ("1.3", "1.3"),
            ("1.4", "1.3"),
            ("1.4", "1.4"),
        ):
            with self.subTest(
                manifest_schema=manifest_schema,
                checkpoint_schema=checkpoint_schema,
            ):
                module._validate_checkpoint_schema(
                    manifest_schema, checkpoint_schema
                )

        with self.assertRaises(module.ContinuityError) as raised:
            module._validate_checkpoint_schema("1.3", "1.4")

        self.assertIn("schema 1.3 requiere checkpoint 1.3", str(raised.exception))

    def test_schema_13_resume_rejects_a_schema_14_checkpoint(self) -> None:
        module = _load_continuity_module()
        with tempfile.TemporaryDirectory(prefix="lks-sdd-ckpt-schema-") as temporary:
            root = Path(temporary).resolve()
            checkpoint = (
                root
                / "docs/lks-sdd/04-delivery/checkpoints/CKPT-001.md"
            )
            checkpoint.parent.mkdir(parents=True)
            checkpoint.write_text(
                "---\n"
                'artifact_id: "ART-CKPT-001"\n'
                'artifact_type: "implementation-checkpoint"\n'
                'schema_version: "1.4"\n'
                "---\n",
                encoding="utf-8",
                newline="\n",
            )
            manifest = {
                "schema_version": "1.3",
                "executions": [
                    {
                        "execution_id": "EXEC-001",
                        "latest_checkpoint": (
                            "docs/lks-sdd/04-delivery/checkpoints/CKPT-001.md"
                        ),
                    }
                ],
            }
            args = argparse.Namespace(execution_id="EXEC-001")

            with self.assertRaises(module.ContinuityError) as raised:
                module._resume(root, manifest, args)

            self.assertIn(
                "schema 1.3 requiere checkpoint 1.3", str(raised.exception)
            )


def _link_evidence(root: Path, evidence_id: str = "EVID-001") -> Path:
    traceability = root / "docs/lks-sdd/05-quality/traceability.md"
    traceability.write_text(
        traceability.read_text(encoding="utf-8").replace(
            "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | none |",
            f"| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | {evidence_id} |",
        ),
        encoding="utf-8",
        newline="\n",
    )
    evidence_path = root / f"docs/lks-sdd/evidence/{evidence_id}.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    return evidence_path


def _write_evidence(
    path: Path,
    *,
    classification: str,
    statuses: list[str],
) -> None:
    path.write_text(
        json.dumps(
            {
                "evidence_id": path.stem,
                "increment": "INC-001",
                "profile_id": "API-FASTAPI-STATELESS-OCI",
                "profile_version": "1.0.0",
                "revision": None,
                "classification": classification,
                "checks": [
                    {"name": f"check-{index}", "status": status}
                    for index, status in enumerate(statuses, start=1)
                ],
                "limitations": (
                    ["Synthetic reservation."]
                    if classification == "verified-with-reservations"
                    else []
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


class VerificationEvidenceGuardsTests(unittest.TestCase):
    def test_preimplementation_keeps_valid_legacy_happy_path_clear(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-trace-legacy-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            _downgrade_ready_project_to_legacy(root)
            before = tree_digest(root)

            validation_code, validation = run_json(VALIDATE_SCRIPT, str(root))
            trace_code, traceability = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--phase",
                "preimplementation",
            )
            _, context = run_json(HELP_SCRIPT, str(root))

            self.assertEqual(validation_code, 0, validation)
            self.assertTrue(validation["valid"])
            self.assertEqual(trace_code, 0, traceability)
            self.assertTrue(traceability["valid"], traceability["gaps"])
            self.assertEqual(traceability["diagnostics"], [])
            self.assertEqual(context["readiness_preflight"]["status"], "clear")
            self.assertEqual(context["readiness_preflight"]["diagnostics"], [])
            self.assertEqual(before, tree_digest(root))

    def test_preimplementation_does_not_require_passing_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-trace-pre-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            evidence = _link_evidence(root)
            _write_evidence(
                evidence, classification="not-verified", statuses=["failed"]
            )

            code, result = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--phase",
                "preimplementation",
            )

            self.assertEqual(code, 0, result)
            self.assertTrue(result["valid"])
            self.assertFalse(result["evidence_required"])

    def test_verification_accepts_only_nonempty_all_passed_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-trace-pass-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            evidence = _link_evidence(root)
            _write_evidence(
                evidence,
                classification="verified-with-reservations",
                statuses=["passed", "passed"],
            )

            code, result = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--phase",
                "verification",
            )

            self.assertEqual(code, 0, result)
            self.assertTrue(result["valid"])
            self.assertTrue(result["evidence_required"])

    def test_verification_rejects_non_successful_structured_evidence(self) -> None:
        for status in ("not-run", "blocked", "failed"):
            with self.subTest(status=status), tempfile.TemporaryDirectory(
                prefix=f"lks-sdd-trace-{status}-"
            ) as temporary:
                root = Path(temporary)
                _ready_project(root)
                evidence = _link_evidence(root)
                _write_evidence(
                    evidence, classification="not-verified", statuses=[status]
                )

                code, result = run_json(
                    TRACEABILITY_SCRIPT,
                    str(root),
                    "--increment",
                    "INC-001",
                    "--phase",
                    "verification",
                    expected_codes={3},
                )

                self.assertEqual(code, 3, result)
                self.assertIn(
                    "TRACE-EVIDENCE-NOT-PASSED",
                    {item["code"] for item in result["diagnostics"]},
                )

    def test_verification_rejects_skipped_or_missing_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-trace-skip-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            evidence = _link_evidence(root)
            _write_evidence(
                evidence, classification="not-verified", statuses=["skipped"]
            )
            code, result = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--phase",
                "verification",
                expected_codes={2},
            )
            self.assertEqual(code, 2, result)
            self.assertFalse(result["valid"])

        with tempfile.TemporaryDirectory(prefix="lks-sdd-trace-missing-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            _link_evidence(root)
            code, result = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--phase",
                "verification",
                expected_codes={2},
            )
            self.assertEqual(code, 2, result)
            self.assertFalse(result["valid"])


class ConsumerProfileLockGuardsTests(unittest.TestCase):
    def test_readiness_binds_packaged_lock_before_prepare(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-lock-ready-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            expected_hash = hashlib.sha256(PACKAGED_LOCK.read_bytes()).hexdigest()

            code, before = run_json(
                READINESS_SCRIPT, str(root), "--increment", "INC-001"
            )
            self.assertEqual(code, 0, before)
            self.assertEqual(
                before["status"], "ready-for-implementation-authorization"
            )
            self.assertEqual(
                before["profile_locks"][0]["expected_sha256"], expected_hash
            )
            self.assertIsNone(before["profile_locks"][0]["sha256"])

            consumer_lock = root / ".lks-sdd/profiles/BIND-001.lock.json"
            consumer_lock.parent.mkdir(parents=True, exist_ok=True)
            consumer_lock.write_bytes(PACKAGED_LOCK.read_bytes())
            code, after = run_json(
                READINESS_SCRIPT, str(root), "--increment", "INC-001"
            )
            self.assertEqual(code, 0, after)
            self.assertEqual(after["profile_locks"][0]["sha256"], expected_hash)
            self.assertEqual(
                after["active_contract_fingerprint"],
                before["active_contract_fingerprint"],
            )

    def test_substituted_consumer_lock_blocks_all_gates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-lock-bad-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            consumer_lock = root / ".lks-sdd/profiles/BIND-001.lock.json"
            consumer_lock.parent.mkdir(parents=True, exist_ok=True)
            consumer_lock.write_text("{}\n", encoding="utf-8", newline="\n")

            readiness_code, readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                expected_codes={3},
            )
            self.assertEqual(readiness_code, 3, readiness)
            self.assertEqual(readiness["status"], "automation-blocked")
            self.assertTrue(
                any(
                    "BIND-001" in item and "lock" in item.casefold()
                    for item in readiness["blockers"]
                )
            )

            prepare_code, preparation = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--dry-run",
                expected_codes={3},
            )
            self.assertEqual(prepare_code, 3, preparation)
            self.assertEqual(preparation["status"], "blocked")

            verify_code, verification = run_json(
                VERIFY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--plan",
                expected_codes={3},
            )
            self.assertEqual(verify_code, 3, verification)
            self.assertEqual(verification["classification"], "not-verified")

    def test_prepare_materializes_lock_and_verify_requires_it(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-lock-flow-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            authorize_implementation(root)

            verify_code, verification = run_json(
                VERIFY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--plan",
                expected_codes={3},
            )
            self.assertEqual(verify_code, 3, verification)
            self.assertTrue(
                any(
                    "implementation" in item.casefold()
                    or "bindings verificables" in item.casefold()
                    for item in verification["blockers"]
                )
            )

            prepare_code, preparation = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--dry-run",
            )
            self.assertEqual(prepare_code, 0, preparation)
            self.assertIn(
                ".lks-sdd/profiles/BIND-001.lock.json", preparation["created"]
            )


class VerificationImplementationCompletionGuardsTests(unittest.TestCase):
    def test_execute_and_record_fail_closed_while_implementation_is_in_progress(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-verify-progress-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            _prepare_increment(root)
            manifest_path = root / ".lks-sdd/project.json"
            traceability_path = root / "docs/lks-sdd/05-quality/traceability.md"
            original_manifest = manifest_path.read_bytes()
            original_traceability = traceability_path.read_bytes()

            module = _load_verification_module()
            args = argparse.Namespace(
                project_root=root,
                increment="INC-001",
                plan=False,
                execute=True,
                authorize=True,
                containers=False,
                record_evidence="EVID-001",
                visual_evidence=None,
            )
            with mock.patch.object(
                module,
                "_execute_check",
                side_effect=lambda check: {
                    "name": check["name"],
                    "status": "passed",
                },
            ) as execute_check:
                code, result = module.run(args)

            self.assertEqual(code, 3, result)
            self.assertEqual(result["classification"], "not-verified")
            self.assertFalse(result["execution_ready"])
            self.assertEqual(result["checks"], [])
            self.assertTrue(
                any("status=completed" in item for item in result["blockers"]),
                result,
            )
            execute_check.assert_not_called()
            self.assertFalse(
                (root / "docs/lks-sdd/evidence/EVID-001.json").exists()
            )
            self.assertEqual(manifest_path.read_bytes(), original_manifest)
            self.assertEqual(traceability_path.read_bytes(), original_traceability)

    def test_record_revalidates_implementation_after_checks_without_writing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-verify-race-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            _prepare_increment(root)
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["implementation"]["status"] = "completed"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            traceability_path = root / "docs/lks-sdd/05-quality/traceability.md"
            original_traceability = traceability_path.read_bytes()
            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }

            module = _load_verification_module()
            args = argparse.Namespace(
                project_root=root,
                increment="INC-001",
                plan=False,
                execute=True,
                authorize=True,
                containers=False,
                record_evidence="EVID-001",
                visual_evidence=None,
            )
            mutated_manifest: bytes | None = None

            def mutate_manifest_during_first_check(check, env):
                nonlocal mutated_manifest
                if mutated_manifest is None:
                    current = json.loads(manifest_path.read_text(encoding="utf-8"))
                    current["implementation"]["status"] = "in-progress"
                    manifest_path.write_text(
                        json.dumps(current, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                        newline="\n",
                    )
                    mutated_manifest = manifest_path.read_bytes()
                return {
                    "name": check["name"],
                    "gate_id": check["gate_id"],
                    "binding_id": check["binding_id"],
                    "status": "passed",
                }

            with mock.patch.object(
                module,
                "_execute_profile_command",
                side_effect=mutate_manifest_during_first_check,
            ) as execute_check, self.assertRaises(module.VerificationError) as raised:
                module.run(args)

            self.assertIn("project.json cambió", str(raised.exception))
            self.assertEqual(execute_check.call_count, 7)
            self.assertIsNotNone(mutated_manifest)
            self.assertEqual(manifest_path.read_bytes(), mutated_manifest)
            self.assertEqual(traceability_path.read_bytes(), original_traceability)
            self.assertFalse(
                (root / "docs/lks-sdd/evidence/EVID-001.json").exists()
            )
            expected = dict(before)
            expected[".lks-sdd/project.json"] = mutated_manifest
            after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, expected)

    def test_plan_blocks_an_increment_different_from_the_implementation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-verify-increment-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            _prepare_increment(root)
            manifest_path = root / ".lks-sdd/project.json"
            traceability_path = root / "docs/lks-sdd/05-quality/traceability.md"
            original_manifest = manifest_path.read_bytes()
            original_traceability = traceability_path.read_bytes()

            code, result = run_json(
                VERIFY_SCRIPT,
                str(root),
                "--increment",
                "INC-002",
                "--plan",
                expected_codes={3},
            )

            self.assertEqual(code, 3, result)
            self.assertEqual(result["checks"], [])
            self.assertTrue(
                any("implementation.increment no coincide" in item for item in result["blockers"]),
                result,
            )
            self.assertEqual(manifest_path.read_bytes(), original_manifest)
            self.assertEqual(traceability_path.read_bytes(), original_traceability)

    def test_plan_blocks_an_implementation_profile_mismatch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-verify-profile-") as temporary:
            root = Path(temporary)
            _ready_project(root)
            _prepare_increment(root)
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["implementation"]["profile_bindings"] = ["BIND-999"]
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            original_manifest = manifest_path.read_bytes()

            code, result = run_json(
                VERIFY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--plan",
                expected_codes={3},
            )

            self.assertEqual(code, 3, result)
            self.assertEqual(result["checks"], [])
            self.assertTrue(
                any(
                    "Binding de implementación inexistente: BIND-999" in item
                    for item in result["blockers"]
                ),
                result,
            )
            self.assertEqual(manifest_path.read_bytes(), original_manifest)


class HandoffContractDocumentationTests(unittest.TestCase):
    def test_readiness_prepare_and_verify_boundaries_are_documented(self) -> None:
        readiness = (
            PLUGIN_ROOT
            / "skills/lks-sdd-assess-readiness/references/readiness-rubric.md"
        ).read_text(encoding="utf-8")
        implementation = (
            PLUGIN_ROOT
            / "skills/lks-sdd-implement/references/implementation-contract.md"
        ).read_text(encoding="utf-8")
        verification = (
            PLUGIN_ROOT
            / "skills/lks-sdd-verify/references/verification-contract.md"
        ).read_text(encoding="utf-8")

        self.assertIn("puede no existir", implementation)
        self.assertIn("idéntico byte a byte", readiness)
        self.assertIn("copia byte a byte", implementation)
        self.assertIn("checkpoint durable", implementation)
        self.assertIn("lista no vacía de checks", verification)
        self.assertIn("todos ellos en `passed`", verification)
        self.assertIn("Ausencia, `{}`, edición o enlace", verification)
        self.assertIn("implementation.status=completed", verification)


if __name__ == "__main__":
    unittest.main()
