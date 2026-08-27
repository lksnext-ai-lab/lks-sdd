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

    paths = {"project.json": manifest_path.resolve()}
    for artifact in manifest["artifacts"]:
        relative = artifact["path"]
        path = root / relative
        content = path.read_text(encoding="utf-8")
        content = content.replace('schema_version: "1.5"', 'schema_version: "1.0"')
        content = content.replace('method_version: "1.5.0"', 'method_version: "1.0.0"')
        content = content.replace(
            'created_with_plugin_version: "0.14.0"',
            'created_with_plugin_version: "0.6.1"',
        )
        content = content.replace(
            "PLAN-001 y REL-001 son propuestas iniciales",
            "El horizonte y la release son propuestas iniciales",
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
        if artifact["id"] == "ART-SOLUTION":
            content = "\n".join(
                line for line in content.splitlines() if "| ADR-002 |" not in line
            ) + "\n"
            content = content.replace(
                "Select API-FASTAPI-STATELESS-OCI for UNIT-001.",
                "Select API-FASTAPI-STATELESS-OCI for the increment.",
            ).replace(
                "Limited to INC-001 and BIND-001",
                "Limited to INC-001",
            )
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
            self.assertEqual(readiness["status"], "specification-blocked")
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

    def test_10_rejects_states_introduced_only_for_tracking_14(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-compat-10-") as directory:
            root = Path(directory)
            _write_review_free_project(root)
            requirements = (
                root / "docs/lks-sdd/02-requirements/functional-requirements.md"
            )
            text = requirements.read_text(encoding="utf-8")
            self.assertIn("| FR-001 | confirmed |", text)
            requirements.write_text(
                text.replace("| FR-001 | confirmed |", "| FR-001 | synced |", 1),
                encoding="utf-8",
                newline="\n",
            )
            report, _, _ = migration.validate_project(root)
            self.assertFalse(report.valid)
            self.assertTrue(
                any("estado de elemento no admitido 'synced'" in item for item in report.errors),
                report.errors,
            )

    def test_11_to_12_creates_governance_and_rolls_back_created_artifacts(self):
        with tempfile.TemporaryDirectory(
            prefix="lks-sdd-migration-12-"
        ) as directory:
            container = Path(directory)
            root = container / "project"
            root.mkdir()
            _write_review_free_project(root)
            safe_root = migration._safe_root(root)

            plan_11 = migration._plan(safe_root, "1.1")
            self.assertEqual(plan_11.human_review_required, [])
            backup_11 = container / "backup-11"
            migration._apply(
                safe_root,
                plan_11,
                backup_11,
                migration._preview(safe_root, plan_11)["preview_hash"],
            )
            manifest_11 = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest_11["schema_version"], "1.1")

            # The helper starts from a current initializer. Remove the unindexed
            # 1.2/1.3 files so this source accurately represents a real 1.1 project.
            for _, relative in (
                *migration.V12_ARTIFACTS,
                *migration.V13_ARTIFACTS,
                *migration.V14_ARTIFACTS,
            ):
                candidate = root / relative
                if candidate.exists():
                    candidate.unlink()
            task_directory = root / "docs/lks-sdd/04-delivery/tasks"
            if task_directory.is_dir():
                for task in task_directory.glob("TASK-*.md"):
                    task.unlink()
                task_directory.rmdir()
            snapshot = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }

            plan_12 = migration._plan(safe_root, "1.2")
            preview_12 = migration._preview(safe_root, plan_12)
            self.assertEqual(plan_12.source_schema, "1.1")
            self.assertEqual(plan_12.target_schema, "1.2")
            self.assertEqual(plan_12.human_review_required, [])
            created = [change for change in plan_12.changes if change.created]
            self.assertEqual(len(created), len(migration.V12_ARTIFACTS))
            backup_12 = container / "backup-12"
            applied = migration._apply(
                safe_root,
                plan_12,
                backup_12,
                preview_12["preview_hash"],
            )
            self.assertTrue(applied["validated"])
            migrated = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(migrated["schema_version"], "1.2")
            self.assertEqual(migrated["method_version"], "1.2.0")
            self.assertEqual(migrated["plugin_version"], "0.8.0")
            self.assertEqual(migrated["delivery_governance"]["state"], "proposed")
            self.assertEqual(migrated["technology"]["profile_bindings"], [])
            self.assertNotIn("implementation", migrated)
            self.assertNotIn("verification", migrated)

            rollback_plan, record_path, record = migration._plan_rollback(
                safe_root, backup_12
            )
            rolled_back = migration._apply_rollback(
                safe_root, rollback_plan, record_path, record
            )
            self.assertEqual(rolled_back["status"], "rolled-back")
            restored = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(restored, snapshot)

    def test_12_to_13_and_13_to_14_are_conservative_and_reversible(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-migration-13-") as directory:
            container = Path(directory)
            root = container / "project"
            root.mkdir()
            _write_review_free_project(root)
            safe_root = migration._safe_root(root)

            plan_11 = migration._plan(safe_root, "1.1")
            migration._apply(
                safe_root,
                plan_11,
                container / "backup-11",
                migration._preview(safe_root, plan_11)["preview_hash"],
            )
            for _, relative in (
                *migration.V12_ARTIFACTS,
                *migration.V13_ARTIFACTS,
                *migration.V14_ARTIFACTS,
            ):
                candidate = root / relative
                if candidate.exists():
                    candidate.unlink()
            task_directory = root / "docs/lks-sdd/04-delivery/tasks"
            if task_directory.is_dir():
                for task in task_directory.glob("TASK-*.md"):
                    task.unlink()
                task_directory.rmdir()

            plan_12 = migration._plan(safe_root, "1.2")
            migration._apply(
                safe_root,
                plan_12,
                container / "backup-12",
                migration._preview(safe_root, plan_12)["preview_hash"],
            )
            source_validation, _, _ = migration.validate_project(safe_root)
            self.assertTrue(source_validation.valid, source_validation.errors)
            snapshot = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }

            plan_13 = migration._plan(safe_root, "1.3")
            preview_13 = migration._preview(safe_root, plan_13)
            self.assertEqual(plan_13.source_schema, "1.2")
            self.assertEqual(plan_13.target_schema, "1.3")
            self.assertEqual(plan_13.human_review_required, [])
            created = [change for change in plan_13.changes if change.created]
            self.assertEqual(
                [change.path.relative_to(safe_root).as_posix() for change in created],
                ["docs/lks-sdd/04-delivery/planning-coverage.md"],
            )

            backup_13 = container / "backup-13"
            applied = migration._apply(
                safe_root,
                plan_13,
                backup_13,
                preview_13["preview_hash"],
            )
            self.assertTrue(applied["validated"])
            migrated = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(migrated["schema_version"], "1.3")
            self.assertEqual(migrated["method_version"], "1.3.0")
            self.assertEqual(migrated["plugin_version"], "0.9.1")
            self.assertEqual(migrated["active_tasks"], [])
            self.assertIsNone(migrated["planning"]["target_id"])
            self.assertEqual(migrated["authorizations"], [])
            self.assertEqual(migrated["executions"], [])
            planning_text = (
                root / "docs/lks-sdd/04-delivery/planning-coverage.md"
            ).read_text(encoding="utf-8")
            self.assertNotIn("| REL-001 | release | proposed |", planning_text)

            readiness_code, readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                expected_codes={3},
            )
            self.assertEqual(readiness_code, 3)
            self.assertFalse(readiness["implementation_authorized"])
            self.assertNotEqual(readiness["status"], "ready-to-implement")

            snapshot_13 = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            planning_before_14 = migrated["planning"]
            authorizations_before_14 = migrated["authorizations"]
            executions_before_14 = migrated["executions"]

            blocked_manifest = json.loads(json.dumps(migrated))
            blocked_manifest["executions"] = [
                {"execution_id": "EXEC-777", "status": "paused"}
            ]
            (root / ".lks-sdd/project.json").write_text(
                json.dumps(blocked_manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            with self.assertRaisesRegex(
                migration.MigrationError, "ejecución reanudable activa"
            ):
                migration._plan(safe_root, "1.4")
            (root / ".lks-sdd/project.json").write_text(
                json.dumps(migrated, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )

            historical_checkpoint = (
                root / "docs/lks-sdd/04-delivery/checkpoints/CKPT-999.md"
            )
            historical_checkpoint.parent.mkdir(parents=True, exist_ok=True)
            historical_bytes = (
                b'---\nartifact_id: "ART-CKPT-999"\n'
                b'artifact_type: "implementation-checkpoint"\n'
                b'schema_version: "1.3"\n---\n# historical checkpoint\n'
            )
            historical_checkpoint.write_bytes(historical_bytes)
            snapshot_13[
                historical_checkpoint.relative_to(root).as_posix()
            ] = historical_bytes
            plan_14 = migration._plan(safe_root, "1.4")
            preview_14 = migration._preview(safe_root, plan_14)
            self.assertEqual(plan_14.source_schema, "1.3")
            self.assertEqual(plan_14.target_schema, "1.4")
            self.assertEqual(plan_14.human_review_required, [])
            created_14 = [change for change in plan_14.changes if change.created]
            self.assertEqual(
                [
                    change.path.relative_to(safe_root).as_posix()
                    for change in created_14
                ],
                ["docs/lks-sdd/04-delivery/task-tracking.md"],
            )

            backup_14 = container / "backup-14"
            applied_14 = migration._apply(
                safe_root,
                plan_14,
                backup_14,
                preview_14["preview_hash"],
            )
            self.assertTrue(applied_14["validated"])
            migrated_14 = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(migrated_14["schema_version"], "1.4")
            self.assertEqual(migrated_14["method_version"], "1.4.0")
            self.assertEqual(migrated_14["plugin_version"], "0.10.0")
            self.assertEqual(migrated_14["planning"], planning_before_14)
            self.assertEqual(
                migrated_14["authorizations"], authorizations_before_14
            )
            self.assertEqual(migrated_14["executions"], executions_before_14)
            self.assertEqual(
                migrated_14["task_tracking"],
                {
                    "source": "docs/lks-sdd/04-delivery/task-tracking.md",
                    "binding_id": "TRK-001",
                    "state": "proposed",
                    "mode": "repository-only",
                    "provider": None,
                    "decision": None,
                    "site": None,
                    "project_key": None,
                    "issue_type": None,
                    "sync_policy": "not-required",
                    "write_policy": "local-only",
                    "projection_fingerprint": None,
                    "sync_status": "not-required",
                    "last_sync_on": None,
                },
            )
            self.assertEqual(historical_checkpoint.read_bytes(), historical_bytes)
            tracking_text = (
                root / "docs/lks-sdd/04-delivery/task-tracking.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "| TRK-001 | proposed | repository-only | none | ", tracking_text
            )
            self.assertIn(
                "| pending: migration-preserved from schema 1.3 |", tracking_text
            )

            snapshot_14 = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            plan_15 = migration._plan(safe_root, "1.5")
            preview_15 = migration._preview(safe_root, plan_15)
            self.assertEqual(plan_15.source_schema, "1.4")
            self.assertEqual(plan_15.target_schema, "1.5")
            self.assertEqual(plan_15.human_review_required, [])
            backup_15 = container / "backup-15"
            applied_15 = migration._apply(
                safe_root,
                plan_15,
                backup_15,
                preview_15["preview_hash"],
            )
            self.assertTrue(applied_15["validated"])
            migrated_15 = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(migrated_15["schema_version"], "1.5")
            self.assertEqual(migrated_15["method_version"], "1.5.0")
            self.assertEqual(migrated_15["plugin_version"], "0.14.0")
            self.assertEqual(
                migrated_15["task_tracking"]["reporting_scope"],
                "not-applicable",
            )
            self.assertEqual(
                migrated_15["task_tracking"]["reporting_status"],
                "not-required",
            )
            self.assertEqual(historical_checkpoint.read_bytes(), historical_bytes)
            tracking_15 = (
                root / "docs/lks-sdd/04-delivery/task-tracking.md"
            ).read_text(encoding="utf-8")
            self.assertIn("## Reporting policy", tracking_15)
            self.assertIn("| RPT-001 | confirmed | not-applicable |", tracking_15)
            self.assertIn("## Milestone operations", tracking_15)

            rollback_15, record_path_15, record_15 = migration._plan_rollback(
                safe_root, backup_15
            )
            migration._apply_rollback(
                safe_root, rollback_15, record_path_15, record_15
            )
            restored_14 = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(restored_14, snapshot_14)

            rollback_14, record_path_14, record_14 = migration._plan_rollback(
                safe_root, backup_14
            )
            migration._apply_rollback(
                safe_root, rollback_14, record_path_14, record_14
            )
            restored_13 = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(restored_13, snapshot_13)
            historical_checkpoint.unlink()
            historical_checkpoint.parent.rmdir()

            rollback_plan, record_path, record = migration._plan_rollback(
                safe_root, backup_13
            )
            migration._apply_rollback(
                safe_root, rollback_plan, record_path, record
            )
            restored = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(restored, snapshot)

    def test_13_treats_v14_tracking_ids_as_plain_text_in_applicability_reasons(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-compat-13-") as directory:
            root = Path(directory)
            initialize(root, "tracking-identifiers-are-v14-only")
            materialize_ready_increment(root, confirm_plan=False)
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update(
                {
                    "schema_version": "1.3",
                    "method_version": "1.3.0",
                    "plugin_version": "0.9.1",
                }
            )
            manifest.pop("task_tracking", None)
            manifest["artifacts"] = [
                item
                for item in manifest["artifacts"]
                if item["id"] != "ART-TRACKING"
            ]
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            (root / "docs/lks-sdd/04-delivery/task-tracking.md").unlink()
            for markdown in (root / "docs/lks-sdd").rglob("*.md"):
                text = markdown.read_text(encoding="utf-8")
                markdown.write_text(
                    text.replace('schema_version: "1.5"', 'schema_version: "1.3"')
                    .replace('method_version: "1.5.0"', 'method_version: "1.3.0"')
                    .replace(
                        'created_with_plugin_version: "0.14.0"',
                        'created_with_plugin_version: "0.9.1"',
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
            baseline, _, _ = migration.validate_project(root)
            self.assertTrue(baseline.valid, baseline.errors)

            tasks_path = root / "docs/lks-sdd/04-delivery/tasks.md"
            tasks_text = tasks_path.read_text(encoding="utf-8")
            tasks_path.write_text(
                tasks_text.replace(
                    "not-applicable: no prerequisite task",
                    "not-applicable: external Jira labels TRK-999 and SYNC-999",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            compatibility, _, _ = migration.validate_project(root)
            self.assertTrue(compatibility.valid, compatibility.errors)
            self.assertFalse(
                any(
                    token in error
                    for error in compatibility.errors
                    for token in ("TRK-999", "SYNC-999")
                )
            )


if __name__ == "__main__":
    unittest.main()
