import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from v2_fixture import element, project, write
from v2_contract import ContractError, DOCS, canonical, execution_context, load, render_document
from v2_authoring import author, commit, catalog, edit_elements, historical, initialize
from v2_storage import apply, recover


class V2DocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.feature = project(self.root)

    def test_hybrid_literal_obligations_and_sources(self):
        model = load(self.root)
        self.assertTrue(model.valid, model.errors)
        context = execution_context(model, ["TASK-001"])
        self.assertEqual(context["status"], "sufficient")
        self.assertIn("Nunca incluir datos privados", json.dumps(context, ensure_ascii=False))
        self.assertEqual(context["writes"], [])
        self.assertTrue(all(e["source"]["line"] > 1 for e in context["elements"]))

    def test_parent_is_navigation_not_inherited_scope_or_approval(self):
        model = load(self.root)
        feature = model.elements["FTR-001"]
        for name, data in edit_elements(model, {feature.id: dict(feature.meta, relations={**feature.relations, "parent": ["FTR-900"]})}).items():
            write(self.root, name, data)
        write(self.root, DOCS + "/02-specification/features/FTR-900-parent/specification.md", render_document("feature", "Parent",
            [element("FTR-900", "feature", state="draft", relations={"requirements": ["FR-900"]}),
             element("FR-900", "requirement", "Unrelated parent draft requirement", state="draft")]))
        context = execution_context(load(self.root), ["TASK-001"])
        self.assertEqual(context["status"], "sufficient", context["blockers"])
        self.assertNotIn("FR-900", {e["meta"]["id"] for e in context["elements"]})
        self.assertEqual(context["organizational_parents"][0]["id"], "FTR-900")
        self.assertFalse(context["organizational_parents"][0]["approval_inherited"])

    def test_external_text_attachment_is_literal_and_change_invalidates_context(self):
        write(self.root, "design/constraints.txt", "Nunca borrar el histórico, incluso al cancelar.")
        path = self.root / self.feature
        path.write_text(path.read_text(encoding="utf-8") + "\n[Restricción externa](../../../../../design/constraints.txt)\n", encoding="utf-8")
        model = load(self.root)
        context = execution_context(model, ["TASK-001"])
        self.assertIn("Nunca borrar", json.dumps(context, ensure_ascii=False))
        write(self.root, "design/constraints.txt", "Cambio no revisado.")
        with self.assertRaisesRegex(ContractError, "attachment changed"):
            model.normative({"FTR-001"})
        self.assertNotEqual(context["fingerprint"], execution_context(load(self.root), ["TASK-001"])["fingerprint"])

    def test_invalid_author_preview_is_read_only_and_staged(self):
        before = (self.root / self.feature).read_bytes()
        with self.assertRaises(ContractError):
            author(load(self.root), {"documents": [{"path": DOCS + "/02-specification/bad.md",
                "text": render_document("feature", "Broken", [element("FTR-002", "feature", relations={"uses": ["FTR-999"]})]).decode()}]})
        self.assertEqual((self.root / self.feature).read_bytes(), before)
        self.assertFalse((self.root / DOCS / "02-specification/bad.md").exists())

    def test_prose_changes_fingerprint_even_outside_blocks(self):
        before = execution_context(load(self.root), ["TASK-001"])["fingerprint"]
        path = self.root / self.feature
        path.write_text(path.read_text(encoding="utf-8") + "\nNo imprimir domingos.\n", encoding="utf-8")
        self.assertNotEqual(before, execution_context(load(self.root), ["TASK-001"])["fingerprint"])

    def test_derived_catalog_does_not_change_execution_fingerprint(self):
        before = execution_context(load(self.root), ["TASK-001"])["fingerprint"]
        write(self.root, DOCS + "/02-specification/catalog.md", '---\nschema_version: "2.0"\nartifact_type: "derived"\n---\n\n# Vista\n')
        self.assertEqual(before, execution_context(load(self.root), ["TASK-001"])["fingerprint"])

    def test_task_state_is_not_a_normative_change(self):
        model = load(self.root)
        before = execution_context(model, ["TASK-001"])["fingerprint"]
        changed = dict(model.elements["TASK-001"].meta, state="in-progress")
        for path, value in edit_elements(model, {"TASK-001": changed}).items():
            write(self.root, path, value)
        self.assertEqual(before, execution_context(load(self.root), ["TASK-001"])["fingerprint"])

    def test_shared_unknown_critical_obligation_blocks(self):
        write(self.root, DOCS + "/02-specification/shared/rules.md", render_document("rules", "Privacidad", [
            element("RULE-001", "rule", "No exportar datos médicos.", scope="unknown", critical=True)]))
        context = execution_context(load(self.root), ["TASK-001"])
        self.assertEqual(context["status"], "blocked")
        self.assertIn("No exportar datos médicos", str(context))

    def test_contributor_task_and_consumer_included(self):
        write(self.root, DOCS + "/04-delivery/tasks/TASK-002.md", render_document("task", "Auditoría", [
            element("TASK-002", "task", "Registrar auditoría.", relations={"contributes_to": ["FTR-001"]})]))
        context = execution_context(load(self.root), ["TASK-001"])
        self.assertIn("TASK-002", [e["meta"]["id"] for e in context["elements"]])

    def test_duplicate_id_and_uid_rejected(self):
        for duplicate in (element("FR-001", "requirement"),
                          element("FR-002", "requirement", uid=load(self.root).elements["FR-001"].meta["uid"])):
            write(self.root, DOCS + "/02-specification/shared/duplicate.md", render_document("rule", "Duplicado", [duplicate]))
            self.assertFalse(load(self.root).valid)

    def test_orphan_and_cycle_rejected(self):
        value = element("FTR-002", "feature", relations={"depends_on": ["FTR-002"], "uses": ["FTR-999"]})
        write(self.root, DOCS + "/02-specification/features/FTR-002/specification.md", render_document("feature", "Ciclo", [value]))
        errors = load(self.root).errors
        self.assertTrue(any("Cycle" in e for e in errors))
        self.assertTrue(any("Orphan" in e for e in errors))

    def test_partial_replacement_requires_residual_and_effectivity(self):
        value = element("FTR-002", "feature", replacement={"mode": "partial", "state": "approved"})
        write(self.root, DOCS + "/02-specification/features/FTR-002/specification.md", render_document("feature", "Cambio", [value]))
        self.assertFalse(load(self.root).valid)

    def test_total_replacement_split_merge_and_cancel_preserve_old_identity(self):
        for relation in ("replaces", "splits", "merges"):
            with self.subTest(relation=relation):
                value = element("FTR-002", "feature", state="cancelled", relations={relation: ["FTR-001"]},
                    replacement={"mode": "total", "state": "proposed", "effective": {"version": "2.0", "environment": "test"}})
                write(self.root, DOCS + "/02-specification/features/FTR-002/specification.md", render_document("feature", "Cancelled future", [value]))
                model = load(self.root)
                self.assertTrue(model.valid, model.errors)
                result = catalog(model)
                self.assertEqual(result["features"][0]["definition_state"], "confirmed")
                self.assertEqual(result["features"][0]["successors"][0]["definition_state"], "cancelled")

    def test_future_replacement_does_not_retire_current(self):
        value = element("FTR-002", "feature", state="approved", relations={"replaces": ["FTR-001"]},
                        replacement={"mode": "partial", "state": "approved", "effective": {"version": "3.0", "environment": "preproduction"}, "residual_scope": "Consulta de pedidos"})
        write(self.root, DOCS + "/02-specification/features/FTR-002/specification.md", render_document("feature", "Cambio", [value]))
        result = catalog(load(self.root))
        self.assertEqual(result["features"][0]["definition_state"], "confirmed")
        self.assertEqual(result["features"][0]["deployment"], [])

    def test_catalog_keeps_previous_definition_when_future_revision_is_approved(self):
        model = load(self.root)
        feature = model.elements["FTR-001"]
        meta = dict(feature.meta, revision=2, state="approved",
                    maintained_versions=[{"version": "1.x", "environment": "production", "status": "maintained"},
                                         {"version": "2.0", "environment": "preproduction", "status": "planned"}])
        changes = edit_elements(model, {feature.id: meta})
        request = {"documents": [{"path": p, "text": b.decode()} for p, b in changes.items()]}
        proposed, _ = author(model, request)
        commit(model, request, proposed["preview_hash"])
        versions = catalog(load(self.root))["features"][0]["definitions"]
        self.assertEqual({d["revision"] for d in versions}, {1, 2})
        old = next(d for d in versions if d["revision"] == 1)
        self.assertIn("/history/", old["source"]["path"])
        self.assertTrue((self.root / old["source"]["path"]).is_file())
        self.assertTrue(all(d["verification"] == "not-inferred" for d in versions))

    def test_link_target_id_and_anchor_must_match(self):
        path = self.root / self.feature
        original = path.read_text(encoding="utf-8")
        path.write_text(original + '\n[FR-001 · regla](#fr-001)\n', encoding="utf-8")
        self.assertTrue(load(self.root).valid)
        path.write_text(original + '\n[FR-001 · regla](#ac-001)\n', encoding="utf-8")
        self.assertFalse(load(self.root).valid)

    def test_links_cannot_escape_or_read_secrets(self):
        path = self.root / self.feature
        path.write_text(path.read_text(encoding="utf-8") + '\n[secreto](../../../../../.env)\n', encoding="utf-8")
        self.assertFalse(load(self.root).valid)

    def test_package_templates_do_not_enable_secret_reads_in_queries(self):
        from v2_contract import read_bytes, path_at
        write(self.root, "scaffold/.env.example", "EXAMPLE=placeholder\n")
        with self.assertRaises(ContractError):
            read_bytes(self.root, "scaffold/.env.example")
        self.assertEqual(read_bytes(self.root, "scaffold/.env.example", package_data=True), b"EXAMPLE=placeholder\n")
        for forbidden in (".env", "private.key", "scaffold/.env.local", ".git/config", "secrets/.env.example"):
            with self.assertRaises(ContractError):
                path_at(self.root, forbidden, missing=True, package_data=True)

    def test_no_process_or_writes_while_reading(self):
        with patch("subprocess.run", side_effect=AssertionError("process")), patch.object(Path, "write_bytes", side_effect=AssertionError("write")):
            execution_context(load(self.root), ["TASK-001"])

    def test_cancelled_or_empty_execution_root_rejected(self):
        model = load(self.root)
        with self.assertRaises(ContractError):
            execution_context(model, [])
        model.elements["TASK-001"].meta["state"] = "cancelled"
        with self.assertRaises(ContractError):
            execution_context(model, ["TASK-001"])

    def test_snapshot_available_after_authoring(self):
        model = load(self.root)
        snapshot = model.snapshot()
        old = model.documents[self.feature]
        new = old.replace('"revision":1', '"revision":2').replace("Nunca incluir", "Jamás incluir")
        request = {"documents": [{"path": self.feature, "text": new}]}
        plan, _ = author(model, request)
        commit(model, request, plan["preview_hash"])
        history = historical(self.root, snapshot)
        self.assertIn(old, [d["text"] for d in history["documents"]])
        self.assertIn("Jamás incluir", (self.root / self.feature).read_text(encoding="utf-8"))

    def test_author_requires_revision_and_preserves_identity(self):
        model = load(self.root)
        text = model.documents[self.feature].replace("Nunca incluir", "Incluir")
        with self.assertRaises(ContractError):
            author(model, {"documents": [{"path": self.feature, "text": text}]})

    def test_stale_author_preview_rejected(self):
        model = load(self.root)
        text = model.documents[self.feature].replace('"revision":1', '"revision":2')
        request = {"documents": [{"path": self.feature, "text": text}]}
        plan, changes = author(model, request)
        write(self.root, self.feature, model.documents[self.feature] + "\nCambio externo.\n")
        with self.assertRaises(ContractError):
            apply(self.root, changes, plan, plan["preview_hash"])

    def test_interruption_recovers_and_rollback_refuses_later_work(self):
        model = load(self.root)
        text = model.documents[self.feature].replace('"revision":1', '"revision":2')
        plan, changes = author(model, {"documents": [{"path": self.feature, "text": text}]})
        with self.assertRaises(InterruptedError):
            apply(self.root, changes, plan, plan["preview_hash"], interrupt_after=1)
        receipt = recover(self.root, plan["preview_hash"])["receipt"]
        write(self.root, self.feature, text + "\nTrabajo posterior.\n")
        with self.assertRaises(ContractError):
            recover(self.root, plan["preview_hash"], rollback=True, receipt=receipt)
        self.assertIn("Trabajo posterior", (self.root / self.feature).read_text(encoding="utf-8"))

    def test_initialization_no_empty_feature_or_fictional_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, changes = initialize(root, "Proyecto nuevo")
            apply(root, changes, plan, plan["preview_hash"])
            model = load(root)
            self.assertTrue(model.valid)
            self.assertEqual(model.by_kind("feature"), [])
            self.assertEqual(model.by_kind("authorization"), [])
            self.assertEqual(len(model.by_kind("applicability")), 8)

    def test_new_visual_metadata_asset_is_checked_in_authoring_stage(self):
        from v2_contract import sha
        asset = DOCS + "/02-specification/features/FTR-001-pedidos/assets/approved.png"
        write(self.root, asset, b"synthetic-asset-not-a-render")
        value = element("VIS-001", "visual", baseline_assets=[asset])
        path = DOCS + "/02-specification/features/FTR-001-pedidos/visual.md"
        request = {"documents": [{"path": path, "text": render_document("visual", "Baseline", [value]).decode()}]}
        proposed, _ = author(load(self.root), request)
        self.assertEqual(proposed["sources"][asset], sha(b"synthetic-asset-not-a-render"))
        write(self.root, asset, b"changed")
        with self.assertRaises(ContractError):
            commit(load(self.root), request, proposed["preview_hash"])

    def test_approved_traceability_inventory_has_real_code_and_test_references(self):
        from v2_audit import audit
        result = audit()
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["counts"], {"requirements": 67, "tasks": 48, "scenario_families": 60})


if __name__ == "__main__":
    unittest.main()
