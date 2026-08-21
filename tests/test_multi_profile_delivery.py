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
    initialize,
    materialize_ready_increment,
    run_json,
)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from delivery_engine import load_delivery_evidence  # noqa: E402
from profile_registry import load_catalog, resolve_profile  # noqa: E402


class MultiProfileDeliveryTests(unittest.TestCase):
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
        self.assertEqual(len(active), 6)
        self.assertEqual(len(candidate), 4)

        for profile_id in sorted(active):
            with self.subTest(profile=profile_id):
                support = resolve_profile(profile_id)
                self.assertEqual(support.errors, ())
                self.assertTrue(support.validated_lock)
                self.assertTrue(support.composition_certified)
                self.assertTrue(support.implementable)
                self.assertTrue(support.verifiable)
                self.assertEqual(
                    support.support_level,
                    "H0"
                    if profile_id == "WEB-FASTAPI-REACT-KEYCLOAK-PG"
                    else "H1",
                )

        for profile_id in sorted(candidate):
            with self.subTest(profile=profile_id):
                support = resolve_profile(profile_id)
                self.assertTrue(support.documentable)
                self.assertTrue(support.analyzable)
                self.assertFalse(support.validated_lock)
                self.assertFalse(support.composition_certified)
                self.assertFalse(support.implementable)
                self.assertFalse(support.verifiable)
                self.assertEqual(support.support_level, "H2")

    def test_two_certified_bindings_prepare_one_task_slice_without_collisions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-multiprofile-") as temporary:
            root = Path(temporary)
            initialize(root, "multi-profile")
            materialize_ready_increment(root)
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
            detail_1 = docs / "04-delivery" / "tasks" / "TASK-001.md"
            detail_2 = docs / "04-delivery" / "tasks" / "TASK-002.md"
            task_text = detail_1.read_text(encoding="utf-8")
            task_text = task_text.replace("ART-TASK-001", "ART-TASK-002")
            task_text = task_text.replace("TASK-001", "TASK-002")
            task_text = task_text.replace("UNIT-001", "UNIT-002")
            task_text = task_text.replace("BIND-001", "BIND-002")
            task_text = task_text.replace(
                "Implement synthetic acknowledgement",
                "Implement synthetic web",
            )
            detail_2.write_text(task_text, encoding="utf-8", newline="\n")

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
