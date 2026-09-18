"""Independent counterexamples for human authoring, continuity, quality and remote receipts."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from v2_fixture import project, element, write
from v2_contract import ContractError, DOCS, load, render_document
from v2_authoring import author, commit, edit_elements
from v2_features import create, decomposition, rename_aliases, SECTIONS
from v2_lifecycle import authorize, start, checkpoint, planning, report_problem
from v2_controls import correction, revoke
from v2_storage import preview, apply, recover
from v2_quality import obligations, observation_errors
from v2_tracking import (authorize_projection, record_result, projection, readiness, milestone)

AT = "2026-09-18T00:00:00+00:00"


class V2ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.feature = project(self.root)
        for module in ("v2_lifecycle", "v2_controls"):
            clock = patch(module + ".now", return_value=AT)
            clock.start()
            self.addCleanup(clock.stop)

    def mutate(self, function, *args, **kwargs):
        result = function(load(self.root), *args, **kwargs)
        function(load(self.root), *args, **kwargs, authorized_hash=result["preview_hash"])
        return result

    def authorize(self):
        self.mutate(authorize, ["TASK-001"], actor="synthetic-owner", role="owner", environment="test",
                    approved_at=AT, expires_at="2026-10-01T00:00:00+00:00", reason="Controlled test.")

    def start(self):
        self.authorize()
        self.mutate(start, ["TASK-001"], "test", actor="synthetic-developer", at=AT,
                    technology=lambda *args: {"status": "exact-certified"})

    def test_feature_draft_has_sections_folder_links_no_implicit_subfolders(self):
        request = {"id": "FTR-002", "title": "Reimprimir pedido", "slug": "reimpresion",
                   "sections": {s: "Contenido solicitado: " + s for s in SECTIONS}, "relations": {"parent": ["FTR-001"]}}
        self.mutate(create, request)
        model = load(self.root)
        self.assertTrue(model.valid, model.errors)
        feature = model.elements["FTR-002"]
        self.assertEqual(feature.meta["state"], "draft")
        self.assertIn("/02-specification/features/FTR-002-reimpresion/specification.md", feature.path)
        self.assertIn("../FTR-001-pedidos/specification.md#ftr-001", feature.body)
        self.assertFalse((self.root / Path(feature.path).parent / "details").exists())
        self.assertEqual(model.elements["FTR-001"].meta["state"], "confirmed")

    def test_feature_requires_full_human_definition(self):
        with self.assertRaises(ContractError):
            create(load(self.root), {"id": "FTR-002", "title": "x", "slug": "x", "sections": {}})

    def test_two_clones_same_alias_different_creation_intents_have_distinct_uids(self):
        from v2_features import feature_request
        from v2_contract import parse_document
        first = {"id": "FTR-002", "title": "Printing", "slug": "printing", "sections": {s: "Printing scope" for s in SECTIONS}}
        second = {**first, "title": "Delivery", "slug": "delivery"}
        a = parse_document(feature_request(load(self.root), first)["documents"][0]["text"], "a.md")[0][0]
        b = parse_document(feature_request(load(self.root), second)["documents"][0]["text"], "b.md")[0][0]
        self.assertEqual(a.id, b.id)
        self.assertNotEqual(a.meta["uid"], b.meta["uid"])

    def test_author_cannot_forge_done_or_authority(self):
        model = load(self.root)
        task = model.elements["TASK-001"]
        text = render_document("task", "Fraudulent done", [element("TASK-001", "task", uid=task.meta["uid"], revision=2, state="done")]).decode()
        with self.assertRaisesRegex(ContractError, "fabricate"):
            author(model, {"documents": [{"path": task.path, "text": text}]})
        forged = render_document("authorization", "Autoapproval", [element("AUTH-900", "authorization", state="active")]).decode()
        with self.assertRaisesRegex(ContractError, "dedicated"):
            author(model, {"documents": [{"path": DOCS + "/00-control/forged.md", "text": forged}]})

    def test_decomposition_requires_primary_and_checks_both_directions(self):
        result = decomposition(load(self.root), "PLAN-001")
        self.assertEqual(result["status"], "covered")
        model = load(self.root)
        task = model.elements["TASK-001"]
        meta = dict(task.meta, relations={**task.relations, "implements": [], "requirements": ["FR-001"]})
        for path, data in edit_elements(model, {task.id: meta}).items():
            write(self.root, path, data)
        self.assertEqual(decomposition(load(self.root), "PLAN-001")["status"], "incomplete")

    def test_explicit_alias_collision_repair_preserves_uid_and_history(self):
        self.authorize()
        original = load(self.root).elements["FTR-001"].meta["uid"]
        self.mutate(rename_aliases, {"mapping": {"FTR-001": "FTR-901"}, "reason": "Synthetic incoming-clone collision", "actor": "reviewer"})
        model = load(self.root)
        self.assertTrue(model.valid, model.errors)
        self.assertEqual(model.elements["FTR-901"].meta["uid"], original)
        self.assertEqual(model.elements["FTR-901"].meta["aliases"][0]["id"], "FTR-001")
        self.assertIn("FTR-901", model.elements["TASK-001"].targets("implements"))
        self.assertEqual(model.elements["AUTH-001"].meta["state"], "revoked")
        self.assertTrue(list((self.root / DOCS / "00-control/history").glob("*/snapshot.json")))

    def test_revoke_blocks_existing_authority(self):
        self.authorize()
        self.mutate(revoke, "AUTH-001", actor="owner", reason="Scope withdrawn", at=AT)
        from v2_lifecycle import current_authorization
        with self.assertRaises(ContractError):
            current_authorization(load(self.root), ["TASK-001"], "test")

    def test_corrective_handoff_keeps_problem_open_until_new_evidence(self):
        self.start()
        self.mutate(checkpoint, state="blocked", actor="developer", at=AT, summary="Observed defect", next_action="Correct defect")
        self.mutate(correction, ["TASK-001"], actor="owner", reason="Correct same approved behavior", at=AT)
        self.mutate(checkpoint, state="in-review", actor="developer", at=AT, summary="Correction ready", next_action="Reverify")
        model = load(self.root)
        self.assertEqual(model.elements["TASK-001"].meta["state"], "in-review")
        self.assertEqual(model.elements["PROB-001"].meta["state"], "open")

    def test_replan_preserves_code_cancels_execution_and_revokes_auth(self):
        self.start()
        before = (self.root / "src/print.py").read_bytes()
        self.mutate(correction, ["TASK-001"], actor="owner", reason="Replan scope", at=AT, replan=True)
        model = load(self.root)
        self.assertEqual(model.elements["EXEC-001"].meta["state"], "cancelled")
        self.assertEqual(model.elements["AUTH-001"].meta["state"], "revoked")
        self.assertEqual((self.root / "src/print.py").read_bytes(), before)

    def test_partial_transaction_is_not_read_as_a_valid_contract(self):
        model = load(self.root)
        changes = {self.feature: (self.root / self.feature).read_bytes() + b"\n", DOCS + "/other.md": b"pending"}
        proposal = preview(self.root, changes, sources=model.hashes, operation="synthetic-interrupt")
        with self.assertRaises(InterruptedError):
            apply(self.root, changes, proposal, proposal["preview_hash"], interrupt_after=1)
        with self.assertRaisesRegex(ContractError, "Interrupted transaction"):
            load(self.root)
        recover(self.root, proposal["preview_hash"], rollback=True)
        self.assertTrue(load(self.root).valid)

    def test_rollback_preserves_new_documents_not_in_the_original_write_set(self):
        model = load(self.root)
        changes = {self.feature: (self.root / self.feature).read_bytes() + b"\n"}
        proposal = preview(self.root, changes, sources=model.hashes, operation="synthetic-rollback")
        result = apply(self.root, changes, proposal, proposal["preview_hash"])
        write(self.root, DOCS + "/later.md", render_document("feature", "Later work", [element("FTR-002", "feature")]))
        with self.assertRaisesRegex(ContractError, "new documents"):
            recover(self.root, proposal["preview_hash"], rollback=True, receipt=result["receipt"])
        self.assertTrue((self.root / DOCS / "later.md").exists())

    def test_rollback_preserves_new_evidence_not_in_the_original_write_set(self):
        model = load(self.root)
        changes = {self.feature: (self.root / self.feature).read_bytes() + b"\n"}
        proposed = preview(self.root, changes, sources=model.hashes, operation="synthetic-evidence-rollback")
        result = apply(self.root, changes, proposed, proposed["preview_hash"])
        write(self.root, DOCS + "/evidence/EVID-999.json", '{"later":"evidence"}')
        with self.assertRaisesRegex(ContractError, "new documents"):
            recover(self.root, proposed["preview_hash"], rollback=True, receipt=result["receipt"])

    def test_interface_cannot_hide_composition_or_persistence_obligations(self):
        model = load(self.root)
        task = model.elements["TASK-001"]
        for path, data in edit_elements(model, {task.id: dict(task.meta, relations={**task.relations, "interfaces": ["INT-001"]})}).items():
            write(self.root, path, data)
        write(self.root, DOCS + "/03-solution/interfaces.md", render_document("interface", "Write contract", [
            element("INT-001", "interface", persistent_mutation=True)]))
        assessed = obligations(load(self.root), ["TASK-001"])
        self.assertTrue({"contract", "composition", "persistence"} <= set(assessed["scopes"]))
        self.assertTrue(assessed["blockers"])
        self.assertEqual(planning(load(self.root), ["TASK-001"])["status"], "blocked")

    def test_persistence_labels_and_mocked_integration_do_not_pass(self):
        observation = {"gate_id": "GATE-X", "status": "passed", "scopes": ["persistence"], "observations": {"persistence": True}, "artifacts": [{"sha256": "a" * 64}]}
        errors = observation_errors(observation, {"gate_id": "GATE-X"})
        self.assertTrue(any("independent" in e for e in errors))
        self.assertTrue(any("mocks" in e for e in errors))

    def tracking(self):
        write(self.root, DOCS + "/04-delivery/tracking-policy.md", render_document("decision", "Tracking", [
            element("TRK-001", "decision", category="tracking", mode="jira-hybrid", site="https://synthetic.invalid",
                    project_key="DEMO", reporting_scope="milestone-reporting", coordination_gate="advisory",
                    transitions={"review-requested": "review"})]))

    def test_uncertain_remote_attempt_must_reconcile_and_history_is_append_only(self):
        self.tracking()
        self.mutate(authorize_projection, "TASK-001", actor="owner", at=AT, duplicate_check="no-match")
        original = (self.root / DOCS / "04-delivery/tracking/SYNC-001.md").read_bytes()
        self.mutate(record_result, "SYNC-001", {"result": "uncertain"})
        self.assertEqual((self.root / DOCS / "04-delivery/tracking/SYNC-001.md").read_bytes(), original)
        with self.assertRaises(ContractError):
            authorize_projection(load(self.root), "TASK-001", actor="owner", at=AT, duplicate_check="no-match")
        value = projection(load(self.root), "TASK-001")
        observed = {"result": "succeeded", "observed_marker": value["marker"], "observed_projection_fingerprint": value["fingerprint"],
                    "external_id": "42", "external_key": "DEMO-42", "site": "https://synthetic.invalid", "project_key": "DEMO"}
        self.mutate(record_result, "SYNC-002", observed, reconcile=True)
        self.assertEqual(readiness(load(self.root), ["TASK-001"])["status"], "synchronized")
        with self.assertRaises(ContractError):
            record_result(load(self.root), "SYNC-001", observed)

    def test_mismatched_remote_binding_cannot_be_recorded_as_success(self):
        self.tracking()
        self.mutate(authorize_projection, "TASK-001", actor="owner", at=AT, duplicate_check="no-match")
        value = projection(load(self.root), "TASK-001")
        with self.assertRaises(ContractError):
            record_result(load(self.root), "SYNC-001", {"result": "succeeded", "observed_marker": value["marker"],
                          "observed_projection_fingerprint": value["fingerprint"], "external_id": "42", "external_key": "OTHER-42"})

    def test_remote_receipts_block_silent_rebind(self):
        self.tracking()
        self.mutate(authorize_projection, "TASK-001", actor="owner", at=AT, duplicate_check="no-match")
        path = self.root / DOCS / "04-delivery/tracking-policy.md"
        path.write_text(path.read_text().replace("https://synthetic.invalid", "https://other.invalid"), encoding="utf-8")
        self.assertEqual(readiness(load(self.root), ["TASK-001"])["status"], "blocked")

    def test_high_risk_requires_result_review_and_primary_feature_is_mandatory(self):
        model = load(self.root)
        task = model.elements["TASK-001"]
        for name, data in edit_elements(model, {task.id: dict(task.meta, risk="critical")}).items():
            write(self.root, name, data)
        self.assertTrue(obligations(load(self.root), ["TASK-001"])["human_review_required"])
        model = load(self.root)
        task = model.elements["TASK-001"]
        for name, data in edit_elements(model, {task.id: dict(task.meta, relations={**task.relations, "implements": []})}).items():
            write(self.root, name, data)
        self.assertTrue(any("primary feature" in b for b in planning(load(self.root), ["TASK-001"])["blockers"]))


if __name__ == "__main__":
    unittest.main()
