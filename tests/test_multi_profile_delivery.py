from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from eval_support import (
    IMPLEMENT_SCRIPT,
    _append_row,
    _replace_row,
    authorize_implementation,
    confirm_planning,
    initialize,
    materialize_ready_project,
    materialize_ready_increment,
    run_json,
)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from delivery_engine import load_delivery_evidence  # noqa: E402
from profile_registry import load_catalog, resolve_profile  # noqa: E402
from automation_coverage import describe_profile_coverage  # noqa: E402
from run_reference_profile_gate import _dockerized  # noqa: E402


class MultiProfileDeliveryTests(unittest.TestCase):
    def test_fullstack_host_readiness_checks_retry_transient_port_publication(self) -> None:
        driver = json.loads(
            (
                PLUGIN_ROOT
                / "profiles/WEB-FASTAPI-REACT-KEYCLOAK-PG/profile-driver.json"
            ).read_text(encoding="utf-8")
        )
        checks = {
            item["id"]: item for item in driver["verify"]["checks"]
        }

        for gate_id in ("GATE-OIDC-INTEGRATION", "GATE-DATA-INTEGRATION"):
            with self.subTest(gate=gate_id):
                check = checks[gate_id]
                self.assertEqual(check["execution_context"], "host")
                self.assertIn("for _ in range(30)", check["command"][2])
                self.assertGreaterEqual(check["timeout_seconds"], 90)

    def test_node_gate_uses_a_linux_dependency_volume(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-node-volume-") as temporary:
            work = Path(temporary)
            frontend = work / "apps" / "frontend"
            frontend.mkdir(parents=True)
            command = _dockerized(
                ["npx", "--yes", "pnpm@10.34.5", "test"],
                work,
                frontend,
                "frontend-tests",
                dependency_volume="lkssdd-test-node-modules",
            )

        self.assertIn(
            "lkssdd-test-node-modules:/work/apps/frontend/node_modules",
            command,
        )
        self.assertIn("node:24.19.0-bookworm-slim@", " ".join(command))

    def test_python_gate_uses_a_linux_virtualenv_volume(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-python-volume-") as temporary:
            work = Path(temporary)
            backend = work / "apps" / "backend"
            backend.mkdir(parents=True)
            command = _dockerized(
                ["uv", "run", "mypy"],
                work,
                backend,
                "backend-typecheck",
                dependency_volume="lkssdd-test-python-venv",
            )

        self.assertIn(
            "lkssdd-test-python-venv:/work/apps/backend/.venv",
            command,
        )
        self.assertIn("python:3.14.7-slim@", " ".join(command))
        self.assertIn("pip install", " ".join(command))

    def test_plain_python_gate_does_not_install_uv(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-python-command-") as temporary:
            work = Path(temporary)
            command = _dockerized(
                ["python", "-c", "print('ok')"],
                work,
                work,
                "scaffold-integrity",
            )

        self.assertNotIn("pip install", " ".join(command))

    def test_only_exactly_certified_active_profiles_are_supported(self) -> None:
        catalog, catalog_errors = load_catalog()
        self.assertEqual(catalog_errors, [])
        active = {
            item["id"]
            for item in catalog["profiles"]
            if item["lifecycle"] == "active"
        }
        candidate = {
            item["id"]
            for item in catalog["profiles"]
            if item["lifecycle"] == "candidate"
        }
        self.assertEqual(len(active), 17)
        self.assertIn("WEB-FASTAPI-REACT-KEYCLOAK-PG", active)
        self.assertEqual(len(candidate), 6)

        for profile_id in sorted(active):
            with self.subTest(profile=profile_id):
                support = resolve_profile(profile_id)
                self.assertEqual(support.errors, ())
                self.assertTrue(support.validated_lock)
                self.assertTrue(support.composition_certified)
                self.assertTrue(support.implementable)
                self.assertTrue(support.verifiable)
                self.assertEqual(support.support_level, "H1")

        for profile_id in sorted(candidate):
            with self.subTest(profile=profile_id):
                support = resolve_profile(profile_id)
                self.assertTrue(support.documentable)
                self.assertTrue(support.analyzable)
                self.assertFalse(support.validated_lock)
                self.assertFalse(support.composition_certified)
                self.assertFalse(support.implementable)
                self.assertFalse(support.verifiable)
                expected_level = "H1" if "ENTRA" in profile_id else "H2"
                self.assertEqual(support.support_level, expected_level)

    def test_candidate_coverage_is_granular_but_never_supported(self) -> None:
        coverage = describe_profile_coverage("API-FASTAPI-ENTRA-PG-OCI")
        self.assertEqual(coverage["catalog_fit"], "candidate")
        self.assertEqual(coverage["preparation"], "available")
        self.assertEqual(coverage["implementation"], "candidate-not-certified")
        self.assertEqual(coverage["local_verification"], "defined-not-certified")
        self.assertEqual(coverage["external_interoperability"], "not-run")
        self.assertEqual(coverage["delivery_evidence"], "not-run")
        self.assertIn("CAP-ENTRA-CLAIMS", coverage["capabilities"]["declared"])
        self.assertFalse(resolve_profile("API-FASTAPI-ENTRA-PG-OCI").implementable)

    def test_simulated_oidc_profiles_are_exactly_supported_but_non_productive(self) -> None:
        for profile_id in (
            "API-FASTAPI-SIMULATED-OIDC-PG-OCI",
            "WEB-REACT-VITE-SIMULATED-OIDC-STATIC",
        ):
            with self.subTest(profile=profile_id):
                support = resolve_profile(profile_id)
                coverage = describe_profile_coverage(profile_id)
                self.assertTrue(support.implementable)
                self.assertTrue(support.verifiable)
                self.assertEqual(coverage["catalog_fit"], "exact")
                self.assertEqual(coverage["external_interoperability"], "not-applicable")
                self.assertIn(
                    "CAP-IDENTITY-OIDC-SIMULATED",
                    coverage["capabilities"]["declared"],
                )

    def test_uncatalogued_profile_has_no_automation_coverage(self) -> None:
        coverage = describe_profile_coverage("API-FASTAPI-UNKNOWN")
        self.assertEqual(coverage["catalog_fit"], "not-catalogued")
        self.assertEqual(coverage["preparation"], "not-available")
        self.assertEqual(coverage["implementation"], "not-available")

    def test_two_certified_bindings_prepare_one_task_slice_without_collisions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-multiprofile-") as temporary:
            root = Path(temporary)
            materialize_ready_project(root, "multi-profile", confirm_plan=False)
            docs = root / "docs" / "lks-sdd"
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["active_task"] = None
            manifest["technology"]["selected_profile"] = None
            manifest["technology"]["selection_decision"] = None
            manifest["technology"]["profile_bindings"].append(
                {
                    "binding_id": "BIND-002",
                    "unit_id": "UNIT-002",
                    "unit_path": "web",
                    "profile_id": "WEB-REACT-VITE-STATIC",
                    "profile_scope": "deployable",
                    "selection_decision": "ADR-003",
                    "lock_path": ".lks-sdd/profiles/BIND-002.lock.json",
                    "state": "confirmed",
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )

            _append_row(
                docs / "03-solution" / "solution-overview.md",
                "| ID | State | Decision",
                "| ADR-003 | confirmed | Select WEB-REACT-VITE-STATIC for UNIT-002 and BIND-002. | FR-001 | Limited to the static web deployable |",
            )
            _append_row(
                docs / "03-solution" / "architecture.md",
                "| Unit | State | Component",
                "| UNIT-002 | confirmed | Static React web | Present the synthetic acknowledgement | Static browser deployable | HTTP to UNIT-001 | none: client state only | FR-001 | BIND-002 |",
            )
            _append_row(
                docs / "04-delivery" / "tasks.md",
                "| ID | Plan | Title",
                "| TASK-002 | PLAN-001 | Implement synthetic web | REL-001 | INC-001 | UNIT-002 | BIND-002 | ready | on-track | 0 | not-applicable: no prerequisite task | none | fixture-owner | ./tasks/TASK-002.md | 2026-08-19 |",
            )
            _replace_row(
                docs / "04-delivery" / "plans.md",
                "REL-001",
                "| REL-001 | active | 0.1.0 | PLAN-001 | 2026-08-19 | continuous stream | ENV-001 | TASK-001, TASK-002 | pending | pending | pending: G3/G4 not executed |",
            )
            planning_path = docs / "04-delivery" / "planning-coverage.md"
            planning_path.write_text(
                planning_path.read_text(encoding="utf-8").replace(
                    "| REL-001 | INC-001 | FR-001, AC-001, ADR-001, TEST-001 | TASK-001 | not-applicable: single-task release | Implement and jointly verify the complete synthetic increment | All active items are owned by the only executable task |",
                    "| REL-001 | INC-001 | FR-001, AC-001, ADR-001, TEST-001 | TASK-001 | TASK-002 | Coordinate the API ownership with the web contribution | TASK-001 keeps primary ownership and TASK-002 provides the bound frontend contribution |",
                ),
                encoding="utf-8",
                newline="\n",
            )
            detail_1 = docs / "04-delivery" / "tasks" / "TASK-001.md"
            detail_2 = docs / "04-delivery" / "tasks" / "TASK-002.md"
            task_text = detail_1.read_text(encoding="utf-8")
            task_text = task_text.replace("ART-TASK-001", "ART-TASK-002")
            task_text = task_text.replace("TASK-001", "TASK-002")
            task_text = task_text.replace("UNIT-001", "UNIT-002")
            task_text = task_text.replace("BIND-001", "BIND-002")
            task_text = task_text.replace(
                "CAP-API-CONTRACT, CAP-OCI-RUNTIME",
                "CAP-FRONTEND-QUALITY, CAP-STATIC-BUNDLE",
            )
            task_text = task_text.replace(
                "GATE-API-TEST, GATE-API-OPENAPI, GATE-OCI-BUILD",
                "GATE-FRONTEND-TEST, GATE-FRONTEND-BUILD, GATE-BROWSER-SMOKE",
            )
            task_text = task_text.replace(
                "Implement synthetic acknowledgement",
                "Implement synthetic web",
            )
            detail_2.write_text(task_text, encoding="utf-8", newline="\n")

            confirm_planning(root)
            authorize_implementation(
                root, task_ids=("TASK-001", "TASK-002")
            )

            _, preview = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-001",
                "--task",
                "TASK-002",
                "--dry-run",
            )
            self.assertEqual(preview["profile_bindings"], ["BIND-001", "BIND-002"])
            self.assertEqual(
                preview["profiles"],
                ["API-FASTAPI-STATELESS-OCI", "WEB-REACT-VITE-STATIC"],
            )
            self.assertIn("web/package.json", preview["created"])
            self.assertIn(".lks-sdd/profiles/BIND-001.lock.json", preview["created"])
            self.assertIn(".lks-sdd/profiles/BIND-002.lock.json", preview["created"])

            _, applied = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--task",
                "TASK-001",
                "--task",
                "TASK-002",
                "--apply",
                "--authorize",
                "--preview-hash",
                preview["preview_hash"],
            )
            self.assertTrue(applied["changed"])
            after = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                after["implementation"]["profile_bindings"],
                ["BIND-001", "BIND-002"],
            )
            self.assertEqual(len(after["implementation"]["locks"]), 2)
            self.assertTrue((root / "web" / "package.json").is_file())

    def test_delivery_evidence_rejects_unverifiable_revision_tree_build_or_artifact(self) -> None:
        valid = {
            "schema_version": "1.0",
            "release": "REL-001",
            "environment": "ENV-001",
            "revision": "workspace-sha256:" + "a" * 64,
            "tree_id": "workspace:" + "b" * 64,
            "build_id": "build-sha256:" + "c" * 64,
            "artifact_digests": ["sha256:" + "d" * 64],
            "promotion": {
                "status": "passed",
                "recorded_at": "2026-08-21T10:00:00Z",
                "reference": "promotion-log-001",
            },
            "smoke": {
                "status": "passed",
                "recorded_at": "2026-08-21T10:01:00Z",
                "reference": "smoke-log-001",
            },
            "observability": {
                "status": "passed",
                "recorded_at": "2026-08-21T10:02:00Z",
                "reference": "dashboard-check-001",
            },
            "recovery": {
                "status": "passed",
                "recorded_at": "2026-08-21T10:03:00Z",
                "reference": "rollback-check-001",
            },
            "authorization": {
                "status": "passed",
                "recorded_at": "2026-08-21T09:59:00Z",
                "reference": "approval-001",
                "authority": "release-manager",
            },
        }
        with tempfile.TemporaryDirectory(prefix="lks-sdd-delivery-evidence-") as temporary:
            path = Path(temporary) / "delivery.json"
            path.write_text(
                json.dumps(valid, indent=2) + "\n", encoding="utf-8", newline="\n"
            )
            _, errors = load_delivery_evidence(path)
            self.assertEqual(errors, [])

            invalid_values = {
                "revision": "main",
                "tree_id": "latest",
                "build_id": "build-42",
                "artifact_digests": ["latest"],
            }
            for field, value in invalid_values.items():
                with self.subTest(field=field):
                    payload = json.loads(json.dumps(valid))
                    payload[field] = value
                    path.write_text(
                        json.dumps(payload, indent=2) + "\n",
                        encoding="utf-8",
                        newline="\n",
                    )
                    _, errors = load_delivery_evidence(path)
                    self.assertTrue(errors)

            payload = json.loads(json.dumps(valid))
            payload["authorization"].pop("authority")
            path.write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            _, errors = load_delivery_evidence(path)
            self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
