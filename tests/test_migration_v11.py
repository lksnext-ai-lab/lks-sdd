from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "tests"))

import migrate_project as migration  # noqa: E402
from eval_support import (  # noqa: E402
    READINESS_SCRIPT,
    initialize,
    materialize_ready_increment,
    run_json,
)


def _frontmatter(artifact_id: str, artifact_type: str, status: str = "draft") -> str:
    return f"""---
artifact_id: {artifact_id}
artifact_type: {artifact_type}
schema_version: "1.0"
method_version: "1.0.0"
created_with_plugin_version: "0.6.1"
project_id: "legacy-project"
baseline_id: "BL-0001"
status: {status}
classification: internal
audience:
  - delivery-team
owners:
  - pending-assignment
source_of_truth: true
last_updated: "2026-08-20"
---
"""


def _write_project(root: Path) -> dict[str, Path]:
    documents = {
        "increments.md": _frontmatter("ART-INCREMENTS", "increments")
        + """
# Incrementos

| ID | State | In scope | Out of scope | Requirements | Acceptance | Decisions | Data | Identity | Integrations | Tests |
|---|---|---|---|---|---|---|---|---|---|---|
| INC-001 | decision | Alcance | Fuera | FR-001 a FR-003 | AC-001 | ADR-001 | DATA-001 a DATA-003 | SEC-001, PRIV-001 | INT-001 | TEST-001 |

## Aplicabilidad de interfaz y contrato visual

| Increment | Interface applicability | UX contract | Visual mode | Visual prototype | Reason |
|---|---|---|---|---|---|
""",
        "constraints.md": _frontmatter("ART-CONSTRAINTS", "constraints", "fact")
        + """
# Restricciones

| ID | State | Type | Statement | Source | Impact |
|---|---|---|---|---|---|
| CON-001 | requirement | legal | Revisar | source | high |
| CON-002 | assumption | technical | Validar | source | medium |
| CON-003 | not-applicable | scope | Reencuadrar | source | low |
""",
        "architecture.md": _frontmatter("ART-ARCH", "architecture")
        + """
# Arquitectura

| Reference | State | Component | Responsibility | Interfaces | Requirements |
|---|---|---|---|---|---|
| Web | proposal | UI | Mostrar | API | FR-001 a FR-003 |
""",
        "test-strategy.md": _frontmatter("ART-TEST-STRATEGY", "test-strategy")
        + """
# Estrategia de pruebas

| ID | State | Level or type | Scope | Acceptance | Environment | Evidence |
|---|---|---|---|---|---|---|
| TEST-001 | planned | unit | INC-001 | AC-001 | local | EVID-001 |
""",
    }
    paths: dict[str, Path] = {}
    for name, content in documents.items():
        path = root / "docs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        paths[name] = path.resolve()
    manifest = {
        "project_id": "legacy-project",
        "method_version": "1.0.0",
        "schema_version": "1.0",
        "plugin_version": "0.6.1",
        "open_blockers": ["OPEN-001"],
        "readiness": {"status": "blocked"},
        "artifacts": [
            {"id": f"ART-{index}", "path": f"docs/{name}", "required": True}
            for index, name in enumerate(documents, 1)
        ],
    }
    manifest_path = root / ".lks-sdd" / "project.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    paths["project.json"] = manifest_path.resolve()
    return paths


def _write_review_free_project(root: Path) -> dict[str, Path]:
    initialize(root, "migration-positive")
    materialize_ready_increment(root)

    manifest_path = root / ".lks-sdd" / "project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "method_version": "1.0.0",
            "schema_version": "1.0",
            "plugin_version": "0.6.1",
            "open_blockers": [],
            "readiness": {
                "status": "ready",
                "assessed_increment": "INC-001",
                "assessed_at": "2026-08-20",
            },
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    paths = {"project.json": manifest_path.resolve()}
    for artifact in manifest["artifacts"]:
        relative = artifact["path"]
        path = root / relative
        content = path.read_text(encoding="utf-8")
        content = content.replace('schema_version: "1.1"', 'schema_version: "1.0"')
        content = content.replace('method_version: "1.1.0"', 'method_version: "1.0.0"')
        content = content.replace(
            'created_with_plugin_version: "0.7.0"',
            'created_with_plugin_version: "0.6.1"',
        )
        if artifact["id"] == "ART-INCREMENTS":
            current_main = """| ID | State | In scope | Out of scope | Requirements | Acceptance | Decisions | Tests |
|---|---|---|---|---|---|---|---|
| INC-001 | confirmed | Submit and acknowledge one request | Reporting and administration | FR-001 | AC-001 | ADR-001 | TEST-001 |
"""
            legacy_main = """| ID | State | In scope | Out of scope | Requirements | Acceptance | Decisions | Data | Identity | Integrations | Tests |
|---|---|---|---|---|---|---|---|---|---|---|
| INC-001 | confirmed | Submit and acknowledge one request | Reporting and administration | FR-001 | AC-001 | ADR-001 | not-applicable: no domain data | pending: aggregate identity, security and privacy scope | not-applicable: no external system | TEST-001 |
"""
            if current_main not in content:
                raise AssertionError("The initialized increment table changed unexpectedly.")
            content = content.replace(current_main, legacy_main, 1)
            domain_start = content.index("## Aplicabilidad por dominio")
            interface_start = content.index(
                "## Aplicabilidad de interfaz y contrato visual", domain_start
            )
            content = content[:domain_start] + content[interface_start:]
        path.write_text(content, encoding="utf-8", newline="\n")
        paths[artifact["id"]] = path.resolve()
    return paths


class Schema11MigrationTests(unittest.TestCase):
    def test_plan_converts_contract_without_inventing_confirmations(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-migration-11-") as directory:
            root = Path(directory)
            paths = _write_project(root)
            root = migration._safe_root(root)

            plan = migration._plan(root, "1.1")
            preview = migration._preview(root, plan)

            self.assertEqual(plan.source_schema, "1.0")
            self.assertEqual(plan.target_schema, "1.1")
            self.assertRegex(preview["preview_hash"], r"^[a-f0-9]{64}$")
            self.assertEqual(
                preview["preview_hash"], migration._preview(root, plan)["preview_hash"]
            )
            migrated_manifest = json.loads(
                next(
                    change.after
                    for change in plan.changes
                    if change.path == paths["project.json"]
                )
            )
            self.assertEqual(migrated_manifest["schema_version"], "1.1")
            self.assertEqual(migrated_manifest["method_version"], "1.1.0")
            self.assertEqual(migrated_manifest["plugin_version"], "0.7.0")
            self.assertNotIn("open_blockers", migrated_manifest)
            self.assertNotIn("readiness", migrated_manifest)

            increments = next(
                change.after.decode("utf-8")
                for change in plan.changes
                if change.path == paths["increments.md"]
            )
            self.assertIn(
                "| ID | State | In scope | Out of scope | Requirements | Acceptance | Decisions | Tests |",
                increments,
            )
            self.assertIn(
                "| INC-001 | confirmed | Alcance | Fuera | FR-001..FR-003", increments
            )
            self.assertIn(
                "| INC-001 | data | applicable | DATA-001..DATA-003 |", increments
            )
            for domain in ("identity", "security", "privacy"):
                self.assertIn(f"| INC-001 | {domain} | pending |  |", increments)
            self.assertEqual(increments.count("valor anterior: SEC-001, PRIV-001."), 3)
            self.assertIn(
                "| INC-001 | integrations | applicable | INT-001 |", increments
            )

            constraints = next(
                change.after.decode("utf-8")
                for change in plan.changes
                if change.path == paths["constraints.md"]
            )
            self.assertIn('status: "draft"', constraints)
            self.assertIn("| CON-001 | draft |", constraints)
            self.assertTrue(
                any(item["original"] == "fact" for item in plan.human_review_required)
            )
            self.assertTrue(
                any(
                    item["original"] == "requirement"
                    for item in plan.human_review_required
                )
            )
            self.assertTrue(
                any(
                    item["original"] == "assumption"
                    for item in plan.human_review_required
                )
            )
            self.assertTrue(
                any(
                    item["original"] == "not-applicable"
                    for item in plan.human_review_required
                )
            )
            self.assertFalse(
                any(
                    "domains identity/security/privacy" in item["location"]
                    for item in plan.human_review_required
                )
            )
            self.assertNotIn("| INC-001 | fact |", increments)
            self.assertNotIn("| INC-001 | requirement |", increments)

            architecture = next(
                change.after.decode("utf-8")
                for change in plan.changes
                if change.path == paths["architecture.md"]
            )
            self.assertIn("| Label | State |", architecture)
            self.assertIn("| Web | proposed |", architecture)
            self.assertIn("FR-001..FR-003", architecture)
            tests = next(
                change.after.decode("utf-8")
                for change in plan.changes
                if change.path == paths["test-strategy.md"]
            )
            self.assertIn("| Test | Level or type |", tests)
            self.assertIn(
                "| TEST-001 | unit | INC-001 | AC-001 | local | EVID-001 |", tests
            )
            self.assertNotIn("| TEST-001 | planned |", tests)

    def test_apply_has_external_backup_and_rollback_requires_its_own_preview_hash(self):
        with tempfile.TemporaryDirectory(
            prefix="lks-sdd-migration-apply-"
        ) as directory:
            container = Path(directory)
            root = container / "project"
            root.mkdir()
            paths = _write_review_free_project(root)
            root = migration._safe_root(root)
            original = {name: path.read_bytes() for name, path in paths.items()}
            source_validation, _, _ = migration.validate_project(root)
            self.assertTrue(source_validation.valid, source_validation.errors)
            plan = migration._plan(root, "1.1")
            self.assertEqual(plan.human_review_required, [])
            preview_hash = migration._preview(root, plan)["preview_hash"]
            backup = container / "external-backup"
            applied = migration._apply(
                root,
                plan,
                backup,
                preview_hash,
            )

            self.assertEqual(applied["status"], "migrated")
            self.assertTrue(applied["validated"])
            migrated_validation, _, _ = migration.validate_project(root)
            self.assertTrue(migrated_validation.valid, migrated_validation.errors)
            readiness_code, readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                expected_codes={3},
            )
            self.assertEqual(readiness_code, 3)
            self.assertEqual(readiness["status"], "blocked")
            self.assertTrue(
                any("pending" in blocker.casefold() for blocker in readiness["blockers"])
            )
            self.assertTrue((backup / migration.RECORD_NAME).is_file())
            self.assertEqual(
                json.loads(
                    (backup / migration.RECORD_NAME).read_text(encoding="utf-8")
                )["human_review_required"],
                [],
            )
            self.assertEqual(
                json.loads(paths["project.json"].read_text(encoding="utf-8"))[
                    "schema_version"
                ],
                "1.1",
            )

            rollback_plan, record_path, record = migration._plan_rollback(root, backup)
            rollback_preview = migration._preview(root, rollback_plan)
            self.assertEqual(rollback_preview["status"], "rollback-required")
            self.assertRegex(rollback_preview["preview_hash"], r"^[a-f0-9]{64}$")
            rolled_back = migration._apply_rollback(
                root, rollback_plan, record_path, record
            )
            self.assertEqual(rolled_back["status"], "rolled-back")
            for name, path in paths.items():
                self.assertEqual(path.read_bytes(), original[name])

    def test_apply_rejects_unresolved_human_review_before_any_write(self):
        with tempfile.TemporaryDirectory(
            prefix="lks-sdd-migration-review-"
        ) as directory:
            container = Path(directory)
            root = container / "project"
            root.mkdir()
            paths = _write_project(root)
            root = migration._safe_root(root)
            original = {name: path.read_bytes() for name, path in paths.items()}
            plan = migration._plan(root, "1.1")
            preview_hash = migration._preview(root, plan)["preview_hash"]
            backup = container / "must-not-exist"

            self.assertTrue(plan.human_review_required)
            with mock.patch.object(migration, "validate_project") as validation:
                with self.assertRaisesRegex(
                    migration.MigrationError, "human_review_required"
                ):
                    migration._apply(root, plan, backup, preview_hash)
                validation.assert_not_called()

            self.assertFalse(backup.exists())
            for name, path in paths.items():
                self.assertEqual(path.read_bytes(), original[name])

    def test_09_to_10_remains_explicitly_supported(self):
        legacy = (
            _frontmatter("ART-BRIEF", "product-brief").replace(
                'schema_version: "1.0"', 'schema_version: "0.9"'
            )
            + "\n# Brief\n\nHuman body marker.\n"
        )
        migrated, reviews, operations = migration._migrate_markdown_09_to_10(
            legacy.encode("utf-8"), "docs/product-brief.md"
        )
        text = migrated.decode("utf-8")
        self.assertIn('schema_version: "1.0"', text)
        self.assertIn("Human body marker.", text)
        self.assertEqual(reviews, [])
        self.assertEqual(operations, ["frontmatter-schema-version"])


if __name__ == "__main__":
    unittest.main()
