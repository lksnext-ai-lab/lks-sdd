import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from contract_engine import (  # noqa: E402
    Diagnostic,
    RelationSpec,
    SourceLocation,
    active_contract_fingerprint,
    build_project_model,
    document_fingerprint,
    legacy_messages,
    load_registry,
    parse_reference_cell,
    resolve_active_increment,
)


def _codes(diagnostics):
    return [item.code for item in diagnostics]


def _table(headers, rows):
    header = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    values = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join((header, separator, *values))


def _artifact(artifact_id, artifact_type, tables, schema_version="1.1"):
    frontmatter = (
        "---\n"
        f"artifact_id: {artifact_id}\n"
        f"artifact_type: {artifact_type}\n"
        f"schema_version: {schema_version}\n"
        "---\n\n"
    )
    return frontmatter + "\n\n".join(tables) + "\n"


class ContractRegistryTests(unittest.TestCase):
    def test_registry_selects_schema_specific_contracts(self):
        current = load_registry("1.1")
        legacy = load_registry("1.0")

        constraints = current.artifacts["ART-CONSTRAINTS"].tables[0]
        self.assertEqual(constraints.key_prefixes, frozenset({"CON"}))
        self.assertEqual(current.artifacts["ART-ARCH"].tables[0].headers[0], "Label")
        self.assertEqual(legacy.artifacts["ART-ARCH"].tables[0].headers[0], "Reference")
        self.assertEqual(
            current.artifacts["ART-FR"].tables[0].state_policy,
            "content-lifecycle",
        )
        self.assertEqual(current.catalog_version, "1.1")

    def test_packaged_catalog_and_schema_are_json(self):
        catalog = json.loads(
            (ROOT / "schemas" / "document-contracts.json").read_text(encoding="utf-8")
        )
        schema = json.loads(
            (ROOT / "schemas" / "document-contracts.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(catalog["catalog_version"], "1.1")
        self.assertEqual(
            schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )


class ReferenceParserTests(unittest.TestCase):
    def setUp(self):
        self.relation = RelationSpec(
            column="Requirements",
            targets=frozenset({"FR"}),
            minimum=1,
            maximum=None,
            active_input=True,
        )
        self.known = {f"FR-{number:03d}" for number in range(1, 6)}

    def test_canonical_ranges_and_lists_expand_inclusively(self):
        result = parse_reference_cell(
            "FR-001..FR-003; FR-005", self.relation, self.known
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.references, ("FR-001", "FR-002", "FR-003", "FR-005"))
        self.assertEqual(result.canonical, "FR-001..FR-003, FR-005")

    def test_legacy_range_is_accepted_only_in_compatibility_mode(self):
        strict = parse_reference_cell(
            "FR-001 a FR-003", self.relation, self.known, mode="strict"
        )
        compat = parse_reference_cell(
            "FR-001 a FR-003", self.relation, self.known, mode="compat"
        )

        self.assertFalse(strict.valid)
        self.assertEqual(strict.references, ())
        self.assertTrue(compat.valid)
        self.assertEqual(compat.references, ("FR-001", "FR-002", "FR-003"))
        warnings = [item for item in compat.diagnostics if item.severity == "warning"]
        self.assertEqual([item.code for item in warnings], ["LKS-REF-LEGACY-RANGE"])

    def test_invalid_ranges_are_atomic(self):
        cases = (
            ("FR-003..FR-001", "LKS-REF-RANGE-ORDER", self.known),
            ("FR-001..NFR-003", "LKS-REF-RANGE-PREFIX", self.known),
            ("FR-001..FR-003", "LKS-REF-RANGE-HOLE", {"FR-001", "FR-003"}),
        )
        for value, expected_code, known in cases:
            with self.subTest(value=value):
                result = parse_reference_cell(value, self.relation, known)
                self.assertFalse(result.valid)
                self.assertEqual(result.references, ())
                self.assertIn(expected_code, _codes(result.diagnostics))

    def test_legacy_whitespace_lists_warn_and_normalize(self):
        result = parse_reference_cell(
            "FR-001 FR-002", self.relation, self.known, mode="compat"
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.references, ("FR-001", "FR-002"))
        self.assertIn("LKS-REF-LEGACY-WHITESPACE-LIST", _codes(result.diagnostics))

    def test_optional_cardinality_does_not_override_non_empty_contract(self):
        relation = RelationSpec(
            column="Decisions",
            targets=frozenset({"ADR"}),
            minimum=0,
            maximum=None,
            active_input=True,
            allow_empty=False,
            allow_applicability=frozenset({"not-applicable", "pending"}),
        )

        for empty_value in ("", "none", "n/a"):
            with self.subTest(empty_value=empty_value):
                result = parse_reference_cell(empty_value, relation)
                self.assertFalse(result.valid)
                self.assertIn("LKS-REF-REQUIRED", _codes(result.diagnostics))

        for applicability in (
            "not-applicable: no decision is needed",
            "pending: decision not confirmed",
        ):
            with self.subTest(applicability=applicability):
                result = parse_reference_cell(applicability, relation)
                self.assertTrue(result.valid)
                self.assertEqual(result.syntax, "applicability")


class ProjectModelTests(unittest.TestCase):
    def _write_project(self, root, artifacts, schema_version="1.1"):
        entries = []
        for artifact_id, artifact_type, relative, tables in artifacts:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                _artifact(artifact_id, artifact_type, tables, schema_version),
                encoding="utf-8",
            )
            entries.append({"id": artifact_id, "path": relative, "required": True})
        manifest = {
            "project_id": "contract-engine-tests",
            "method_version": "1.1",
            "schema_version": schema_version,
            "route": "new-build",
            "baseline_id": "BASE-001",
            "technology": {"profile": "test"},
            "artifacts": entries,
        }
        manifest_path = root / ".lks-sdd" / "project.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def test_ids_in_narrative_cells_are_not_treated_as_relations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fr_table = _table(
                (
                    "ID",
                    "State",
                    "Statement",
                    "Source",
                    "Priority",
                    "Acceptance",
                    "Increment",
                ),
                (
                    (
                        "FR-001",
                        "confirmed",
                        "Text mentioning FR-999",
                        "user",
                        "must",
                        "",
                        "",
                    ),
                ),
            )
            self._write_project(
                root,
                (
                    (
                        "ART-FR",
                        "functional-requirements",
                        "docs/lks-sdd/02-requirements/functional-requirements.md",
                        (fr_table,),
                    ),
                ),
            )

            model = build_project_model(root)

        self.assertNotIn("FR-999", model.nodes)
        self.assertFalse(any(edge.target_id == "FR-999" for edge in model.edges))
        self.assertFalse(
            any(
                diagnostic.code == "LKS-REF-UNDEFINED"
                and diagnostic.observed == "FR-999"
                for diagnostic in model.diagnostics
            )
        )

    def test_table_owner_and_state_policy_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fr_table = _table(
                (
                    "ID",
                    "State",
                    "Statement",
                    "Source",
                    "Priority",
                    "Acceptance",
                    "Increment",
                ),
                (("NFR-001", "requirement", "Wrong owner", "user", "must", "", ""),),
            )
            self._write_project(
                root,
                (
                    (
                        "ART-FR",
                        "functional-requirements",
                        "docs/lks-sdd/02-requirements/functional-requirements.md",
                        (fr_table,),
                    ),
                ),
            )

            model = build_project_model(root)

        self.assertIn("LKS-ID-OWNER", _codes(model.diagnostics))
        self.assertIn("LKS-STATE-TABLE", _codes(model.diagnostics))

    def _active_project(self, root, active_visual="VIS-003"):
        asset_dir = root / "docs/lks-sdd/03-solution/ui-prototypes"
        asset_dir.mkdir(parents=True, exist_ok=True)
        rejected = asset_dir / "rejected.png"
        active = asset_dir / "active.png"
        rejected.write_bytes(b"historical visual")
        active.write_bytes(b"active visual")
        rejected_hash = hashlib.sha256(rejected.read_bytes()).hexdigest()
        active_hash = hashlib.sha256(active.read_bytes()).hexdigest()

        fr = _table(
            (
                "ID",
                "State",
                "Statement",
                "Source",
                "Priority",
                "Acceptance",
                "Increment",
            ),
            (
                (
                    "FR-001",
                    "confirmed",
                    "Deliver feature",
                    "user",
                    "must",
                    "AC-001",
                    "INC-001",
                ),
            ),
        )
        ac = _table(
            ("ID", "State", "Condition", "Requirement", "Evidence"),
            (("AC-001", "confirmed", "Feature works", "FR-001", "none"),),
        )
        solution_options = _table(
            ("ID", "State", "Option", "Support", "Fit", "Risks", "Alternative"),
            (),
        )
        solution_decisions = _table(
            ("ID", "State", "Decision", "Requirements", "Impact"),
            (("ADR-001", "confirmed", "Use the selected design", "FR-001", "bounded"),),
        )
        increments = _table(
            (
                "ID",
                "State",
                "In scope",
                "Out of scope",
                "Requirements",
                "Acceptance",
                "Decisions",
                "Tests",
            ),
            (
                (
                    "INC-001",
                    "confirmed",
                    "feature",
                    "none",
                    "FR-001",
                    "AC-001",
                    "ADR-001",
                    "TEST-001",
                ),
            ),
        )
        interface = _table(
            (
                "Increment",
                "Interface applicability",
                "UX contract",
                "Visual mode",
                "Visual prototype",
                "Reason",
            ),
            (
                (
                    "INC-001",
                    "applicable",
                    "UX-001, UX-002, UX-003",
                    "new",
                    active_visual,
                    "user-facing",
                ),
            ),
        )
        domains = _table(
            ("Increment", "Domain", "Applicability", "References", "Reason"),
            tuple(
                ("INC-001", domain, "not-applicable", "", "outside this increment")
                for domain in (
                    "data",
                    "identity",
                    "security",
                    "privacy",
                    "integrations",
                )
            ),
        )
        tests = _table(
            ("ID", "State", "Purpose", "Increment", "Acceptance"),
            (("TEST-001", "planned", "Verify behavior", "INC-001", "AC-001"),),
        )
        trace = _table(
            ("Requirement", "Acceptance", "Decision", "Increment", "Test", "Evidence"),
            (("FR-001", "AC-001", "ADR-001", "INC-001", "TEST-001", "none"),),
        )
        screens = _table(
            (
                "ID",
                "State",
                "Screen",
                "Purpose",
                "Users",
                "Content",
                "Main actions",
                "Requirements",
                "Acceptance",
                "Increment",
            ),
            (
                (
                    "UX-001",
                    "confirmed",
                    "Main",
                    "Deliver",
                    "user",
                    "feature",
                    "act",
                    "FR-001",
                    "AC-001",
                    "INC-001",
                ),
            ),
        )
        screen_detail = _table(
            (
                "Screen",
                "Entry and exit",
                "Information hierarchy",
                "Secondary actions",
                "Permissions and role variants",
                "Responsive and priority devices",
                "Accessibility",
                "Pending content",
            ),
            (
                (
                    "UX-001",
                    "direct",
                    "primary",
                    "none",
                    "user",
                    "responsive",
                    "keyboard",
                    "none",
                ),
            ),
        )
        screen_states = _table(
            (
                "Screen",
                "Loading",
                "Empty",
                "Error",
                "No permission",
                "Confirmation",
                "Recovery",
            ),
            (("UX-001", "spinner", "message", "message", "message", "toast", "retry"),),
        )
        flows = _table(
            (
                "ID",
                "State",
                "Flow or interaction",
                "User",
                "Screens",
                "Entry or trigger",
                "Expected steps or response",
                "Alternate, error or recovery path",
                "Dialog or confirmation",
                "Accessibility",
                "Acceptance",
                "Increment",
            ),
            (
                (
                    "UX-002",
                    "confirmed",
                    "Primary flow",
                    "user",
                    "UX-001",
                    "open",
                    "complete",
                    "retry",
                    "none",
                    "keyboard",
                    "AC-001",
                    "INC-001",
                ),
            ),
        )
        direction = _table(
            (
                "ID",
                "State",
                "Aspect",
                "Proposal",
                "Rationale",
                "Constraints",
                "Human validation",
                "Decision",
                "Increment",
            ),
            (
                (
                    "UX-003",
                    "confirmed",
                    "layout",
                    "simple",
                    "clarity",
                    "none",
                    "approved",
                    "ADR-001",
                    "INC-001",
                ),
            ),
        )
        visuals = _table(
            (
                "ID",
                "State",
                "Asset",
                "Format",
                "Viewport",
                "Screens or flow",
                "Requirements",
                "Source",
                "Generated on",
                "Prompt or brief",
                "SHA-256",
                "Human validation",
                "Confirmation scope",
                "Limitations",
                "Decision",
                "Increment",
            ),
            (
                (
                    "VIS-001",
                    "rejected",
                    "![old](ui-prototypes/rejected.png)",
                    "png",
                    "desktop",
                    "UX-001",
                    "FR-001",
                    "generated",
                    "2026-08-20",
                    "old",
                    rejected_hash,
                    "rejected",
                    "none",
                    "historical",
                    "ADR-001",
                    "INC-001",
                ),
                (
                    "VIS-003",
                    "confirmed",
                    "![active](ui-prototypes/active.png)",
                    "png",
                    "desktop",
                    "UX-001",
                    "FR-001",
                    "generated",
                    "2026-08-20",
                    "active",
                    active_hash,
                    "approved",
                    "increment",
                    "none",
                    "ADR-001",
                    "INC-001",
                ),
            ),
        )
        artifacts = (
            (
                "ART-FR",
                "functional-requirements",
                "docs/lks-sdd/02-requirements/functional-requirements.md",
                (fr,),
            ),
            (
                "ART-AC",
                "acceptance-criteria",
                "docs/lks-sdd/02-requirements/acceptance-criteria.md",
                (ac,),
            ),
            (
                "ART-SOLUTION",
                "solution-overview",
                "docs/lks-sdd/03-solution/solution-overview.md",
                (solution_options, solution_decisions),
            ),
            (
                "ART-UX",
                "ux-accessibility",
                "docs/lks-sdd/03-solution/ux-accessibility.md",
                (screens, screen_detail, screen_states, flows, direction, visuals),
            ),
            (
                "ART-INCREMENTS",
                "increments",
                "docs/lks-sdd/04-delivery/increments.md",
                (increments, interface, domains),
            ),
            (
                "ART-QUALITY",
                "quality-strategy",
                "docs/lks-sdd/05-quality/quality-strategy.md",
                (tests,),
            ),
            (
                "ART-TRACE",
                "traceability",
                "docs/lks-sdd/05-quality/traceability.md",
                (trace,),
            ),
        )
        self._write_project(root, artifacts)
        return rejected, active

    def test_active_fingerprint_excludes_rejected_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rejected, active_asset = self._active_project(root)
            initial_model = build_project_model(root)
            initial_active = resolve_active_increment(initial_model, "INC-001")
            initial_document_hash = document_fingerprint(initial_model)
            initial_active_hash = active_contract_fingerprint(initial_active)

            self.assertEqual(
                [asset.owner_id for asset in initial_active.assets], ["VIS-003"]
            )
            self.assertNotIn("VIS-001", initial_active.node_ids)

            rejected.write_bytes(b"changed historical visual")
            historical_model = build_project_model(root)
            historical_active = resolve_active_increment(historical_model, "INC-001")
            self.assertNotEqual(
                initial_document_hash, document_fingerprint(historical_model)
            )
            self.assertEqual(initial_active_hash, historical_active.fingerprint)

            active_asset.write_bytes(b"changed active visual")
            changed_model = build_project_model(root)
            changed_active = resolve_active_increment(changed_model, "INC-001")
            self.assertNotEqual(initial_active_hash, changed_active.fingerprint)

    def test_active_reference_to_historical_node_has_one_root_diagnostic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._active_project(root, active_visual="VIS-001")
            model = build_project_model(root)
            active = resolve_active_increment(model, "INC-001")

        historical = [
            item
            for item in active.diagnostics
            if item.code == "LKS-ACTIVE-HISTORICAL-REFERENCE"
        ]
        self.assertEqual(len(historical), 1)
        self.assertEqual(historical[0].observed["id"], "VIS-001")
        self.assertEqual(active.assets, ())

    def test_active_contract_excludes_foreign_scoped_trace_and_keeps_ux_details(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._active_project(root)

            increments_path = root / "docs/lks-sdd/04-delivery/increments.md"
            increments_text = increments_path.read_text(encoding="utf-8")
            increments_text = increments_text.replace(
                "| INC-001 | confirmed | feature | none | FR-001 | AC-001 | "
                "ADR-001 | TEST-001 |",
                "| INC-001 | confirmed | feature | none | FR-001 | AC-001 | "
                "ADR-001 | TEST-001 |\n"
                "| INC-002 | confirmed | other | none | FR-001 | AC-002 | "
                "ADR-002 | TEST-002 |",
            )
            increments_path.write_text(increments_text, encoding="utf-8")

            acceptance_path = (
                root / "docs/lks-sdd/02-requirements/acceptance-criteria.md"
            )
            acceptance_text = acceptance_path.read_text(encoding="utf-8").replace(
                "| AC-001 | confirmed | Feature works | FR-001 | none |",
                "| AC-001 | confirmed | Feature works | FR-001 | none |\n"
                "| AC-002 | confirmed | Other feature works | FR-001 | none |",
            )
            acceptance_path.write_text(acceptance_text, encoding="utf-8")

            solution_path = root / "docs/lks-sdd/03-solution/solution-overview.md"
            solution_text = solution_path.read_text(encoding="utf-8").replace(
                "| ADR-001 | confirmed | Use the selected design | FR-001 | bounded |",
                "| ADR-001 | confirmed | Use the selected design | FR-001 | bounded |\n"
                "| ADR-002 | confirmed | Use another design | FR-001 | other |",
            )
            solution_path.write_text(solution_text, encoding="utf-8")

            tests_path = root / "docs/lks-sdd/05-quality/quality-strategy.md"
            tests_text = tests_path.read_text(encoding="utf-8").replace(
                "| TEST-001 | planned | Verify behavior | INC-001 | AC-001 |",
                "| TEST-001 | planned | Verify behavior | INC-001 | AC-001 |\n"
                "| TEST-002 | planned | Verify other behavior | INC-002 | AC-002 |",
            )
            tests_path.write_text(tests_text, encoding="utf-8")

            trace_path = root / "docs/lks-sdd/05-quality/traceability.md"
            trace_text = trace_path.read_text(encoding="utf-8").replace(
                "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | none |",
                "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | none |\n"
                "| FR-001 | AC-002 | ADR-002 | INC-002 | TEST-002 | foreign |",
            )
            trace_path.write_text(trace_text, encoding="utf-8")

            model = build_project_model(root)
            active = resolve_active_increment(model, "INC-001")

        self.assertNotIn("INC-002", active.node_ids)
        self.assertNotIn("AC-002", active.node_ids)
        self.assertNotIn("ADR-002", active.node_ids)
        self.assertNotIn("TEST-002", active.node_ids)
        self.assertFalse(
            any(
                row.table_id == "quality.traceability"
                and row.cells.get("Increment") == "INC-002"
                for row in active.rows
            )
        )
        self.assertTrue(
            {"ux.screen-detail", "ux.screen-states"}.issubset(
                {row.table_id for row in active.rows}
            )
        )

    def test_domain_matrix_is_required_for_each_declared_increment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._active_project(root)
            increments_path = root / "docs/lks-sdd/04-delivery/increments.md"
            text = increments_path.read_text(encoding="utf-8")
            first_row = (
                "| INC-001 | confirmed | feature | none | FR-001 | AC-001 | "
                "ADR-001 | TEST-001 |"
            )
            second_row = (
                "| INC-002 | proposed | follow-up | none | FR-001 | AC-001 | "
                "ADR-001 | TEST-001 |"
            )
            increments_path.write_text(
                text.replace(first_row, f"{first_row}\n{second_row}"),
                encoding="utf-8",
            )

            model = build_project_model(root)

        missing = [
            item
            for item in model.diagnostics
            if item.code == "LKS-DOMAIN-MISSING"
            and item.location.source_id == "INC-002"
        ]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0].severity, "warning")
        self.assertEqual(
            missing[0].observed,
            ["data", "identity", "integrations", "privacy", "security"],
        )


class DiagnosticCompatibilityTests(unittest.TestCase):
    def test_structured_diagnostics_have_deduplicated_legacy_views(self):
        diagnostic = Diagnostic(
            code="LKS-TEST",
            severity="error",
            stage="handoff",
            message="Contract mismatch.",
            location=SourceLocation(
                path="docs/lks-sdd/example.md",
                table_id="example.table",
                row=9,
                column="Requirement",
            ),
        )

        legacy = legacy_messages((diagnostic, diagnostic))

        self.assertEqual(diagnostic.as_dict()["location"]["row"], 9)
        self.assertEqual(len(legacy["errors"]), 1)
        self.assertEqual(legacy["errors"], legacy["blockers"])
        self.assertEqual(legacy["warnings"], [])


if __name__ == "__main__":
    unittest.main()
