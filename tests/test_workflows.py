from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from eval_support import (
    INIT_SCRIPT,
    READINESS_SCRIPT,
    VALIDATE_SCRIPT,
    _append_row,
    _replace_row,
    initialize,
    materialize_ready_increment,
    run_alternative_stack,
    run_help,
    run_insufficient_information,
    run_json,
    run_new_project,
    tree_digest,
)


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
            (root / "package.json").write_text('{"name":"existing-fixture"}\n', encoding="utf-8")
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
            self.assertFalse(result["next_skill_available"])
            self.assertEqual(before, tree_digest(root))

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
            brief.write_text(brief.read_text(encoding="utf-8") + "\nEdición humana conservada.\n", encoding="utf-8")
            before = brief.read_bytes()
            result = initialize(root, "human-edits")
            self.assertFalse(result["would_change"])
            self.assertEqual(before, brief.read_bytes())

    def test_operational_index_does_not_duplicate_proposals_or_blocker_text(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "index-only")
            manifest = json.loads((root / ".lks-sdd" / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(
                set(manifest["technology"]),
                {"preferred_stack_assessed", "selected_profile", "selection_decision"},
            )
            self.assertEqual(manifest["open_blockers"], ["OPEN-001"])
            self.assertTrue(all(isinstance(item, str) for item in manifest["open_blockers"]))
            self.assertEqual(set(manifest["readiness"]), {"status", "assessed_increment", "assessed_at"})

    def test_validator_enforces_exact_core_mapping_and_table_contract(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "strict-core")
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            status = next(item for item in manifest["artifacts"] if item["id"] == "ART-STATUS")
            status["path"] = "docs/lks-sdd/00-control/scope-register.md"
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            code, result = run_json(VALIDATE_SCRIPT, str(root), expected_codes={2})
            self.assertEqual(code, 2)
            self.assertTrue(any("ruta canónica" in error for error in result["errors"]))

        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "strict-table")
            increments = root / "docs" / "lks-sdd" / "04-delivery" / "increments.md"
            text = increments.read_text(encoding="utf-8").replace("| ID | State | In scope |", "| ID | Status | In scope |")
            increments.write_text(text, encoding="utf-8")
            code, result = run_json(VALIDATE_SCRIPT, str(root), expected_codes={2})
            self.assertEqual(code, 2)
            self.assertTrue(any("tabla contractual" in error for error in result["errors"]))

    def test_unrelated_blocker_does_not_block_active_increment(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "scoped-blocker")
            materialize_ready_increment(root)
            _append_row(
                root / "docs" / "lks-sdd" / "04-delivery" / "increments.md",
                "| ID | State | In scope",
                "| INC-002 | open | Trabajo futuro independiente | INC-001 | not-applicable | not-applicable | not-applicable | not-applicable: pending definition | not-applicable: pending definition | not-applicable: pending definition | not-applicable |",
            )
            open_points = root / "docs" / "lks-sdd" / "00-control" / "open-points.md"
            _append_row(
                open_points,
                "| ID | State | Question",
                "| OPEN-002 | blocked | Falta una decisión de otro incremento | No afecta a INC-001 | INC-002 | true |",
            )
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["open_blockers"] = ["OPEN-002"]
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            before = tree_digest(root)
            code, result = run_json(READINESS_SCRIPT, str(root), "--increment", "INC-001")
            self.assertEqual(code, 0)
            self.assertEqual(result["status"], "ready-with-non-blocking-pending")
            self.assertFalse(result["implementation_authorized"])
            self.assertEqual(before, tree_digest(root))

    def test_selected_profile_requires_confirmed_markdown_decision(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "profile-index")
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["technology"]["selected_profile"] = "STACK-REFERENCE"
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            code, result = run_json(VALIDATE_SCRIPT, str(root), expected_codes={2})
            self.assertEqual(code, 2)
            self.assertTrue(any("selection_decision" in error for error in result["errors"]))

    def test_readiness_requires_reason_for_domain_non_applicability(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "domain-applicability")
            materialize_ready_increment(root)
            _replace_row(
                root / "docs" / "lks-sdd" / "04-delivery" / "increments.md",
                "INC-001",
                "| INC-001 | confirmed | Submit and acknowledge one request | Reporting and administration | FR-001 | AC-001 | ADR-001 | not-applicable | not-applicable: synthetic fixture has no accounts | not-applicable: no external systems | TEST-001 |",
            )
            before = tree_digest(root)
            code, result = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                "INC-001",
                expected_codes={3},
            )
            self.assertEqual(code, 3)
            self.assertTrue(any("no aplicabilidad de datos requiere un motivo" in item for item in result["blockers"]))
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
            brief.write_text(brief.read_text(encoding="utf-8") + "\nDato sintético exclusivo de client-one.\n", encoding="utf-8")
            _, validation = run_json(VALIDATE_SCRIPT, str(second))
            self.assertTrue(validation["valid"])
            self.assertEqual(second_before, tree_digest(second))
            self.assertNotIn(
                "client-one",
                (second / "docs" / "lks-sdd" / "01-context" / "product-brief.md").read_text(encoding="utf-8"),
            )

    def test_incompatible_schema_version_is_blocked_without_migration(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-test-") as directory:
            root = Path(directory)
            initialize(root, "old-schema")
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["schema_version"] = "0.9"
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            before = tree_digest(root)
            code, result = run_json(VALIDATE_SCRIPT, str(root), expected_codes={2})
            self.assertEqual(code, 2)
            self.assertTrue(any("schema_version" in error for error in result["errors"]))
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
                {"id": "ART-DATA", "path": "docs/lks-sdd/03-solution/data.md", "required": True}
            )
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            _, result = run_json(VALIDATE_SCRIPT, str(root))
            self.assertTrue(result["valid"])
            self.assertIn("docs/lks-sdd/03-solution/data.md", result["checked_files"])


if __name__ == "__main__":
    unittest.main()
