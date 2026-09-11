from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from eval_support import (
    IMPLEMENT_SCRIPT,
    INIT_SCRIPT,
    READINESS_SCRIPT,
    VALIDATE_SCRIPT,
    VERIFY_SCRIPT,
    _append_row,
    authorize_implementation,
    confirm_planning,
    initialize,
    materialize_ready_project,
    materialize_ready_increment,
    run_alternative_stack,
    run_help,
    run_insufficient_information,
    run_json,
    run_new_project,
    tree_digest,
)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TRACEABILITY_SCRIPT = PLUGIN_ROOT / "scripts" / "check_traceability.py"


class WorkflowTests(unittest.TestCase):
    def _run_in_temp(self, runner):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            return runner(Path(directory))

    def test_new_project(self):
        self.assertTrue(self._run_in_temp(run_new_project)["passed"])

    def test_insufficient_information(self):
        self.assertTrue(self._run_in_temp(run_insufficient_information)["passed"])

    def test_alternative_stack(self):
        self.assertTrue(self._run_in_temp(run_alternative_stack)["passed"])

    def test_help_is_read_only(self):
        self.assertTrue(self._run_in_temp(run_help)["passed"])

    def test_existing_application_routes_without_writing(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            (root / "package.json").write_text(
                '{"name":"existing-fixture"}\n', encoding="utf-8"
            )
            before = tree_digest(root)
            code, result = run_json(
                INIT_SCRIPT,
                str(root),
                "--project-id",
                "existing-fixture",
                expected_codes={3},
            )
            self.assertEqual(code, 3)
            self.assertEqual(result["status"], "adopt-existing-required")
            self.assertTrue(result["next_skill_available"])
            self.assertEqual(before, tree_digest(root))

    def test_implementation_requires_readiness(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "implementation-blocked")
            before = tree_digest(root)
            code, result = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--dry-run",
                expected_codes={3},
            )
            self.assertEqual(code, 3)
            self.assertEqual(result["status"], "blocked")
            self.assertFalse(result["changed"])
            self.assertEqual(before, tree_digest(root))

    def test_implementation_preview_blocks_a_changed_manifest(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "stale-implementation-preview")
            authorize_implementation(root)
            _, preview = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--dry-run",
            )
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["last_verified_revision"] = "f" * 40
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            before = tree_digest(root)
            code, result = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--apply",
                "--authorize",
                "--preview-hash",
                preview["preview_hash"],
                expected_codes={2},
            )
            self.assertEqual(code, 2)
            self.assertEqual(result["status"], "error")
            self.assertEqual(before, tree_digest(root))
            self.assertFalse((root / "apps").exists())

    def test_implementation_preview_apply_and_verification_plan(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "implementation-ready")
            authorize_implementation(root)
            before = tree_digest(root)
            _, preview = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--dry-run",
            )
            self.assertEqual(preview["status"], "dry-run")
            self.assertEqual(before, tree_digest(root))
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
            self.assertTrue(applied["changed"])
            self.assertTrue((root / "pyproject.toml").is_file())
            self.assertTrue((root / "Dockerfile").is_file())
            manifest = json.loads(
                (root / ".lks-sdd" / "project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["implementation"]["status"], "in-progress")
            after_apply = tree_digest(root)
            _, plan = run_json(
                VERIFY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--plan",
            )
            self.assertEqual(plan["classification"], "not-run")
            self.assertEqual(
                plan["transition_summary"]["where_we_are"],
                "verification-not-run",
            )
            self.assertTrue(
                all(check["status"] == "not-run" for check in plan["checks"])
            )
            self.assertFalse(plan["execution_ready"])
            self.assertTrue(
                any("implementation.status=completed" in item for item in plan["limitations"])
            )
            self.assertEqual(after_apply, tree_digest(root))

    def test_document_collision_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            collision = root / "docs" / "lks-sdd" / "00-control" / "project-status.md"
            collision.parent.mkdir(parents=True)
            collision.write_text("human content\n", encoding="utf-8")
            before = tree_digest(root)
            code, result = run_json(
                INIT_SCRIPT,
                str(root),
                "--project-id",
                "collision-fixture",
                expected_codes={2},
            )
            self.assertEqual(code, 2)
            self.assertIn("Colisión documental", result["error"])
            self.assertEqual(before, tree_digest(root))

    def test_short_project_id_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            before = tree_digest(root)
            code, result = run_json(
                INIT_SCRIPT,
                str(root),
                "--project-id",
                "ab",
                expected_codes={2},
            )
            self.assertEqual(code, 2)
            self.assertIn("al menos tres", result["error"])
            self.assertEqual(before, tree_digest(root))

    def test_resume_preserves_human_content(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "human-edits")
            brief = root / "docs" / "lks-sdd" / "01-context" / "product-brief.md"
            brief.write_text(
                brief.read_text(encoding="utf-8") + "\nEdición humana conservada.\n",
                encoding="utf-8",
            )
            before = brief.read_bytes()
            result = initialize(root, "human-edits")
            self.assertFalse(result["would_change"])
            self.assertEqual(before, brief.read_bytes())

    def test_operational_index_does_not_duplicate_proposals_or_blocker_text(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "index-only")
            manifest = json.loads(
                (root / ".lks-sdd" / "project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                set(manifest["technology"]),
                {
                    "preferred_stack_assessed",
                    "selected_profile",
                    "selection_decision",
                    "profile_bindings",
                },
            )
            self.assertNotIn("open_blockers", manifest)
            self.assertNotIn("readiness", manifest)
            open_points = (
                root / "docs" / "lks-sdd" / "00-control" / "open-points.md"
            ).read_text(encoding="utf-8")
            self.assertIn("| OPEN-001 | open |", open_points)

    def test_validator_enforces_exact_core_mapping_and_table_contract(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "strict-core")
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            status = next(
                item for item in manifest["artifacts"] if item["id"] == "ART-STATUS"
            )
            status["path"] = "docs/lks-sdd/00-control/scope-register.md"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            code, result = run_json(VALIDATE_SCRIPT, str(root), expected_codes={2})
            self.assertEqual(code, 2)
            self.assertTrue(any("ruta canónica" in error for error in result["errors"]))

        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "strict-table")
            increments = root / "docs" / "lks-sdd" / "04-delivery" / "increments.md"
            text = increments.read_text(encoding="utf-8").replace(
                "| ID | State | In scope |", "| ID | Status | In scope |"
            )
            increments.write_text(text, encoding="utf-8")
            code, result = run_json(VALIDATE_SCRIPT, str(root), expected_codes={2})
            self.assertEqual(code, 2)
            self.assertTrue(
                any("tabla contractual" in error for error in result["errors"])
            )

    def test_unrelated_blocker_does_not_block_active_increment(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "scoped-blocker")
            _append_row(
                root / "docs" / "lks-sdd" / "04-delivery" / "increments.md",
                "| ID | State | In scope",
                "| INC-002 | draft | Trabajo futuro independiente | INC-001 | pending: definición futura | pending: definición futura | pending: definición futura | pending: definición futura |",
            )
            open_points = root / "docs" / "lks-sdd" / "00-control" / "open-points.md"
            _append_row(
                open_points,
                "| ID | State | Question",
                "| OPEN-002 | blocked | Falta una decisión de otro incremento | No afecta a INC-001 | INC-002 | true |",
            )
            before = tree_digest(root)
            code, result = run_json(
                READINESS_SCRIPT, str(root), "--increment", "INC-001"
            )
            self.assertEqual(code, 0)
            self.assertEqual(
                result["status"], "ready-for-implementation-authorization"
            )
            self.assertFalse(result["implementation_authorized"])
            self.assertEqual(before, tree_digest(root))

    def test_selected_profile_requires_confirmed_markdown_decision(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "profile-index")
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["technology"]["selected_profile"] = "WEB-FASTAPI-REACT-KEYCLOAK-PG"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            code, result = run_json(VALIDATE_SCRIPT, str(root), expected_codes={2})
            self.assertEqual(code, 2)
            self.assertTrue(
                any("selection_decision" in error for error in result["errors"])
            )

    def test_readiness_requires_reason_for_domain_non_applicability(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "domain-applicability")
            increments_path = (
                root / "docs" / "lks-sdd" / "04-delivery" / "increments.md"
            )
            increments = increments_path.read_text(encoding="utf-8")
            increments = increments.replace(
                "| INC-001 | data | not-applicable | none | The fixture does not persist domain data. |",
                "| INC-001 | data | not-applicable | none | |",
                1,
            )
            increments_path.write_text(increments, encoding="utf-8", newline="\n")
            before = tree_digest(root)
            code, result = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                expected_codes={2},
            )
            self.assertEqual(code, 2)
            self.assertTrue(
                any(
                    "LKS-DOMAIN-REASON" in item
                    for item in result["blockers"]
                )
            )
            self.assertEqual(before, tree_digest(root))

    def test_readiness_exposes_structured_diagnostics_on_invalid_contract(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "readiness-diagnostics")
            increments_path = (
                root / "docs" / "lks-sdd" / "04-delivery" / "increments.md"
            )
            increments = increments_path.read_text(encoding="utf-8")
            increments = increments.replace(
                "| INC-001 | confirmed | Submit and acknowledge one request | "
                "Reporting and administration | FR-001 | AC-001 | ADR-001 | TEST-001 |",
                "| INC-001 | confirmed | Submit and acknowledge one request | "
                "Reporting and administration | FR-001 | AC-001 |  | TEST-001 |",
                1,
            )
            increments_path.write_text(increments, encoding="utf-8", newline="\n")

            before = tree_digest(root)
            code, result = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                expected_codes={2},
            )

            self.assertEqual(code, 2, result)
            self.assertTrue(
                any("Contrato inválido:" in item for item in result["blockers"])
            )
            self.assertTrue(
                any(
                    item["code"] == "LKS-REF-REQUIRED"
                    and item["severity"] == "error"
                    and item.get("location", {}).get("column") == "Decisions"
                    for item in result["diagnostics"]
                )
            )
            self.assertEqual(before, tree_digest(root))

    def test_readiness_accepts_business_requirements_in_contract_relations(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            materialize_ready_project(
                root, "business-requirement", confirm_plan=False
            )
            docs = root / "docs" / "lks-sdd"
            for relative in (
                "02-requirements/functional-requirements.md",
                "02-requirements/acceptance-criteria.md",
                "03-solution/solution-overview.md",
                "03-solution/architecture.md",
                "04-delivery/increments.md",
                "04-delivery/planning-coverage.md",
                "04-delivery/tasks/TASK-001.md",
                "05-quality/traceability.md",
                "06-operation/deployment.md",
            ):
                path = docs / relative
                path.write_text(
                    path.read_text(encoding="utf-8").replace("FR-001", "BR-001"),
                    encoding="utf-8",
                    newline="\n",
                )

            confirm_planning(root)

            before = tree_digest(root)
            code, result = run_json(
                READINESS_SCRIPT, str(root), "--increment", "INC-001"
            )

            self.assertEqual(code, 0)
            self.assertEqual(
                result["status"], "ready-for-implementation-authorization"
            )
            self.assertEqual(result["specification_readiness"]["status"], "ready")
            trace_code, traceability = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                "--phase",
                "preimplementation",
            )
            self.assertEqual(trace_code, 0, traceability)
            self.assertTrue(traceability["valid"], traceability["gaps"])
            self.assertEqual(traceability["checked"], ["BR-001"])
            self.assertEqual(before, tree_digest(root))

    def test_projects_are_isolated(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            parent = Path(directory)
            first = parent / "client-one"
            second = parent / "client-two"
            first.mkdir()
            second.mkdir()
            initialize(first, "client-one")
            initialize(second, "client-two")
            second_before = tree_digest(second)
            brief = first / "docs" / "lks-sdd" / "01-context" / "product-brief.md"
            brief.write_text(
                brief.read_text(encoding="utf-8")
                + "\nDato sintético exclusivo de client-one.\n",
                encoding="utf-8",
            )
            _, validation = run_json(VALIDATE_SCRIPT, str(second))
            self.assertTrue(validation["valid"])
            self.assertEqual(second_before, tree_digest(second))
            self.assertNotIn(
                "client-one",
                (
                    second / "docs" / "lks-sdd" / "01-context" / "product-brief.md"
                ).read_text(encoding="utf-8"),
            )

    def test_incompatible_schema_version_is_blocked_without_migration(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "old-schema")
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["schema_version"] = "0.9"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            before = tree_digest(root)
            code, result = run_json(VALIDATE_SCRIPT, str(root), expected_codes={2})
            self.assertEqual(code, 2)
            self.assertTrue(
                any("schema_version" in error for error in result["errors"])
            )
            self.assertEqual(before, tree_digest(root))

    def test_conditional_annex_template_can_be_materialized_and_validated(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "conditional-annex")
            template = (
                Path(__file__).resolve().parents[1]
                / "skills"
                / "lks-sdd-define"
                / "assets"
                / "templates"
                / "03-solution"
                / "data.md"
            )
            content = template.read_text(encoding="utf-8")
            content = content.replace("{{PROJECT_ID}}", "conditional-annex")
            content = content.replace("{{BASELINE_ID}}", "BL-0001")
            content = content.replace("{{DATE}}", "2026-08-19")
            annex = root / "docs" / "lks-sdd" / "03-solution" / "data.md"
            annex.write_text(content, encoding="utf-8")
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"].append(
                {
                    "id": "ART-DATA",
                    "path": "docs/lks-sdd/03-solution/data.md",
                    "required": True,
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            _, result = run_json(VALIDATE_SCRIPT, str(root))
            self.assertTrue(result["valid"])
            self.assertIn("docs/lks-sdd/03-solution/data.md", result["checked_files"])


if __name__ == "__main__":
    unittest.main()
