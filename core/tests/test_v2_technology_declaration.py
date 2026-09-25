"""Focused local technology declaration and migration regressions."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "skills/lks-sdd-adopt-existing/scripts"))

from materialize_adoption import _build_manifest
from validate_project import validate_project
from v2_authoring import initialize
from v2_contract import (ContractError, DOCS, TECHNOLOGY_DECLARATION_PATH, load, make_element,
                         render_document, technology_readiness)
from v2_migration import migrate, plan


def _write_changes(root: Path, changes: dict[str, bytes | None]) -> None:
    for relative, data in changes.items():
        path = root / relative
        if data is None:
            if path.exists():
                path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


class V2TechnologyDeclarationTests(unittest.TestCase):
    def test_legacy_initializers_do_not_emit_global_technology_fields(self):
        manifest = _build_manifest(
            "adoption-cleanup",
            "standard",
            "undetermined",
            {
                "baseline": {
                    "git": {"type": "git", "origin": "none", "revision": None},
                    "inventory_fingerprint": "c" * 64,
                }
            },
            {"strategy": "documentation"},
            "a" * 64,
            "b" * 64,
            "2026-09-19",
        )

        self.assertNotIn("technology", manifest)

    def test_initializer_creates_a_mandatory_local_unknown_declaration(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-technology-") as directory:
            root = Path(directory)
            _, changes = initialize(root, "Synthetic project", project_id="synthetic-project")
            _write_changes(root, changes)

            model = load(root)

            self.assertTrue(model.valid, model.errors)
            self.assertIn(TECHNOLOGY_DECLARATION_PATH, model.documents)
            self.assertEqual([item.id for item in model.technology_declarations], ["TECH-001"])
            self.assertEqual(model.technology_declarations[0].meta["state"], "unknown")
            readiness = technology_readiness(model, ["TASK-001"])
            self.assertEqual(readiness["status"], "blocked")
            self.assertIn("TECH-001", readiness["blockers"][0])

    def test_task_scoped_declaration_requires_an_existing_task_element(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-technology-") as directory:
            root = Path(directory)
            _, changes = initialize(root, "Synthetic project", project_id="synthetic-project")
            _write_changes(root, changes)
            declaration_path = root / TECHNOLOGY_DECLARATION_PATH
            declaration_path.write_bytes(
                declaration_path.read_bytes().replace(
                    b'"scope":["global"]', b'"scope":["TASK-999"]'
                )
            )

            model = load(root)

            self.assertFalse(model.valid)
            with self.assertRaisesRegex(
                ContractError,
                "Technology scope must reference an existing TASK element: TASK-999",
            ):
                model.require_valid()

    def test_task_scoped_declaration_rejects_a_non_task_element(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-technology-") as directory:
            root = Path(directory)
            _, changes = initialize(root, "Synthetic project", project_id="synthetic-project")
            _write_changes(root, changes)
            non_task_path = DOCS + "/02-specification/task-looking-requirement.md"
            non_task = make_element(
                "TASK-001", "requirement", "No es una tarea",
                "El identificador coincide con el selector, pero no es un elemento task.",
                uid=str(uuid.uuid4()), state="confirmed", nature="fact", relations={},
            )
            path = root / non_task_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(render_document("requirement", "Requisito", [non_task]))
            declaration_path = root / TECHNOLOGY_DECLARATION_PATH
            declaration_path.write_bytes(
                declaration_path.read_bytes().replace(
                    b'"scope":["global"]', b'"scope":["TASK-001"]'
                )
            )

            model = load(root)

            self.assertFalse(model.valid)
            with self.assertRaisesRegex(
                ContractError,
                "Technology scope must reference an existing TASK element: TASK-001",
            ):
                model.require_valid()

    def test_generic_binding_remains_a_supported_v2_concept(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-binding-") as directory:
            root = Path(directory)
            _, changes = initialize(root, "Synthetic project", project_id="synthetic-binding")
            _write_changes(root, changes)
            binding_path = DOCS + "/03-solution/bindings/BIND-001.md"
            binding = make_element(
                "BIND-001", "binding", "Asignación no tecnológica",
                "Relación local que no declara ni selecciona una tecnología.",
                uid=str(uuid.uuid4()), state="confirmed", nature="fact", relations={},
            )
            path = root / binding_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(render_document("binding", "Binding genérico", [binding]))
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"].append({"id": "BIND-001", "path": binding_path})
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            model = load(root)

            self.assertTrue(model.valid, model.errors)
            self.assertEqual(model.elements["BIND-001"].kind, "binding")

    def test_migration_archives_legacy_profile_concepts_into_local_declaration(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-migration-") as directory:
            root = Path(directory) / "project"
            root.mkdir()
            initialized = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-X",
                    "utf8",
                    str(ROOT / "skills/lks-sdd-define/scripts/init_project.py"),
                    str(root),
                    "--project-id",
                    "technology-migration",
                    "--date",
                    "2026-09-19",
                    "--json",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)

            manifest_path = root / ".lks-sdd/project.json"
            generated_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertNotIn("technology", generated_manifest)
            validation, _, _ = validate_project(root)
            self.assertTrue(validation.valid, validation.errors)

            # A 1.x source may contain these retired fields and paths only as
            # migration provenance. They must be archived, never interpreted as
            # active v2 technology authority.
            manifest = generated_manifest
            manifest["technology"] = {
                "preferred_stack_assessed": True,
                "selected_profile": "HISTORICAL-STACK",
                "profile_bindings": [
                    {
                        "binding_id": "BIND-001",
                        "profile_id": "HISTORICAL-STACK",
                        "lock_path": ".lks-sdd/profiles/BIND-001.lock.json",
                    }
                ],
            }
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
            lock_path = root / ".lks-sdd/profiles/BIND-001.lock.json"
            lock_path.parent.mkdir(parents=True)
            lock_path.write_text('{"components": [{"name": "legacy", "version": "1"}]}\n', encoding="utf-8")
            variant_path = root / "docs/lks-sdd/03-solution/technology-variants.md"
            variant_path.parent.mkdir(parents=True, exist_ok=True)
            variant_path.write_text("Retired technology source.\n", encoding="utf-8")
            approval_path = root / "docs/lks-sdd/00-control/technology-approvals/ADR-001.md"
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            approval_path.write_text("Retired technology source.\n", encoding="utf-8")
            # This retired binding exists only in active Markdown, not in the
            # legacy manifest technology block. It must stay solely in the raw
            # migration archive and must not become a BIND/LEG v2 element.
            architecture_path = root / "docs/lks-sdd/03-solution/architecture.md"
            architecture_path.write_text(
                architecture_path.read_text(encoding="utf-8").replace(
                    "|---|---|---|---|---|---|---|---|---|\n",
                    "|---|---|---|---|---|---|---|---|---|\n"
                    "| UNIT-777 | confirmed | Retired Profile Recipe Variant | "
                    "Historical only | not-applicable | none | none | none | BIND-777 |\n",
                    1,
                ),
                encoding="utf-8",
            )
            manifest["executions"] = [{
                "execution_id": "EXEC-777",
                "bindings": ["BIND-777"],
            }]
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
            validation, _, _ = validate_project(root)
            self.assertFalse(validation.valid)
            self.assertTrue(
                any("fuente histórica de migración" in error for error in validation.errors),
                validation.errors,
            )

            preview, changes = plan(root)

            self.assertIn(TECHNOLOGY_DECLARATION_PATH, changes)
            declaration = changes[TECHNOLOGY_DECLARATION_PATH].decode("utf-8")
            self.assertIn('"kind":"technology"', declaration)
            self.assertNotIn('"kind":"binding"', declaration)
            self.assertNotIn("HISTORICAL-STACK", declaration)
            execution_payload = next(value for path, value in changes.items()
                                     if path.endswith("EXEC-777.md"))
            self.assertNotIn(b"BIND-777", execution_payload)
            architecture_archive = preview["mapping"][
                "docs/lks-sdd/03-solution/architecture.md"
            ]["archive"]
            self.assertIn(b"BIND-777", changes[architecture_archive])
            self.assertIsNone(changes[".lks-sdd/profiles/BIND-001.lock.json"])
            self.assertIsNone(changes["docs/lks-sdd/03-solution/technology-variants.md"])
            self.assertIsNone(changes["docs/lks-sdd/00-control/technology-approvals/ADR-001.md"])

            outcome = migrate(root, preview["preview_hash"])

            self.assertEqual(outcome["status"], "applied")
            model = load(root)
            self.assertTrue(model.valid, model.errors)
            self.assertEqual(technology_readiness(model, ["TASK-001"])["status"], "blocked")
            self.assertNotIn("BIND-777", {
                element.id for element in model.elements.values()
            })
            # Receipt/history retain the original BIND-777 source as migration provenance.
            receipt_path = root / outcome["migration_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            for source in (
                ".lks-sdd/profiles/BIND-001.lock.json",
                "docs/lks-sdd/03-solution/technology-variants.md",
                "docs/lks-sdd/00-control/technology-approvals/ADR-001.md",
            ):
                self.assertEqual(receipt["mapping"][source]["disposition"], "archived")


if __name__ == "__main__":
    unittest.main()
