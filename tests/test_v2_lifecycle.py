import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from v2_fixture import element, project, write
from v2_contract import ContractError, DOCS, load, render_document
from v2_authoring import edit_elements
from v2_lifecycle import (authorize, current_authorization, planning, start, diff_guard,
                          review_diff, checkpoint, resume, semantic_merge)
from v2_verification import verify, close, evidence

AT = "2026-09-18T00:00:00+00:00"
EXPIRY = "2026-09-30T00:00:00+00:00"


def approved(*args):
    return {"status": "exact-certified", "bindings": [], "stage": "development", "environment": "ENV-001"}


class V2LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.feature = project(self.root)
        self.clock = patch("v2_lifecycle.now", return_value=AT)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def auth(self):
        args = dict(actor="synthetic-owner", role="delivery-owner", environment="ENV-001",
                    approved_at=AT, expires_at=EXPIRY, reason="Implementar el caso sintético confirmado.")
        plan = authorize(load(self.root), ["TASK-001"], **args)
        authorize(load(self.root), ["TASK-001"], **args, authorized_hash=plan["preview_hash"])
        return args

    def begin(self):
        self.auth()
        model = load(self.root)
        plan = start(model, ["TASK-001"], "ENV-001", actor="synthetic-dev", at=AT, technology=approved)
        start(model, ["TASK-001"], "ENV-001", actor="synthetic-dev", at=AT, technology=approved, authorized_hash=plan["preview_hash"])

    def test_ready_is_not_authorized(self):
        self.assertEqual(planning(load(self.root), ["TASK-001"])["status"], "ready")
        with self.assertRaises(ContractError):
            current_authorization(load(self.root), ["TASK-001"], "ENV-001")

    def test_feature_membership_does_not_claim_unplanned_requirement_coverage(self):
        from v2_features import decomposition
        model = load(self.root)
        feature = model.elements["FTR-001"]
        plan = model.elements["PLAN-001"]
        for path, raw in edit_elements(model, {
            feature.id: dict(feature.meta, relations={"requirements": ["FR-001", "FR-002"]}),
            plan.id: dict(plan.meta, relations={"requirements": ["FR-001", "FR-002"], "implements": ["TASK-001"]})
        }).items():
            write(self.root, path, raw)
        write(self.root, DOCS + "/02-specification/shared/extra.md", render_document("requirements", "Otra capacidad", [
            element("FR-002", "requirement", relations={"acceptance": ["AC-002"]}),
            element("AC-002", "acceptance")]))
        model = load(self.root)
        self.assertEqual(decomposition(model, "PLAN-001")["missing"], ["FR-002"])
        self.assertIn("Full plan incomplete: FR-002", planning(model, ["TASK-001"])["blockers"])
        # Claiming an acceptance outside the agreed plan is also visible.
        for path, raw in edit_elements(model, {"PLAN-001": dict(model.elements["PLAN-001"].meta,
            relations={"requirements": ["FR-002"], "implements": ["TASK-001"]})}).items():
            write(self.root, path, raw)
        self.assertIn("Tasks add undeclared plan scope: FR-001", planning(load(self.root), ["TASK-001"])["blockers"])

    def test_authorization_reused_and_not_authentication(self):
        args = self.auth()
        result = authorize(load(self.root), ["TASK-001"], **args)
        self.assertEqual(result["status"], "reused")
        self.assertEqual(result["writes"], [])
        self.assertEqual(result["identity_assurance"], "declared-not-authenticated")

    def test_stale_expired_wrong_environment_and_revoked(self):
        self.auth()
        model = load(self.root)
        for environment, at in (("ENV-002", AT), ("ENV-001", "2026-10-01T00:00:00+00:00")):
            with self.assertRaises(ContractError):
                current_authorization(model, ["TASK-001"], environment, at=at)
        auth = model.by_kind("authorization")[0]
        for path, data in edit_elements(model, {auth.id: dict(auth.meta, state="revoked")}).items():
            write(self.root, path, data)
        with self.assertRaises(ContractError):
            current_authorization(load(self.root), ["TASK-001"], "ENV-001")

    def test_normative_edit_invalidates_auth(self):
        self.auth()
        path = self.root / self.feature
        path.write_text(path.read_text(encoding="utf-8") + "\nExcepto los domingos.\n", encoding="utf-8")
        with self.assertRaises(ContractError):
            current_authorization(load(self.root), ["TASK-001"], "ENV-001")

    def test_cancelled_dependency_is_not_done(self):
        model = load(self.root)
        task = model.elements["TASK-001"]
        changed = dict(task.meta, relations={**task.relations, "depends_on": ["TASK-002"]})
        for path, data in edit_elements(model, {task.id: changed}).items():
            write(self.root, path, data)
        write(self.root, DOCS + "/04-delivery/tasks/TASK-002.md", render_document("task", "Cancelada", [element("TASK-002", "task", state="cancelled")]))
        result = planning(load(self.root), ["TASK-001"])
        self.assertIn("Unfinished dependency: TASK-002", result["blockers"])

    def test_start_creates_single_execution_and_checkpoint(self):
        self.begin()
        model = load(self.root)
        self.assertEqual(model.elements["TASK-001"].meta["state"], "in-progress")
        self.assertEqual(len(model.by_kind("execution")), 1)
        self.assertEqual(len(model.by_kind("checkpoint")), 1)
        self.assertEqual(resume(model, ["TASK-001"])["status"], "continue-recommended")
        with self.assertRaises(ContractError):
            start(model, ["TASK-001"], "ENV-001", actor="other", at=AT, technology=approved)

    def test_direct_out_of_scope_change_detected(self):
        self.begin()
        write(self.root, "src/payments.py", "outside = True\n")
        result = diff_guard(load(self.root))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["unauthorized"], ["src/payments.py"])

    def test_test_edits_need_exact_review_and_cannot_hide_new_scope(self):
        self.begin()
        write(self.root, "tests/test_print.py", "def test_print():\n    assert False\n")
        model = load(self.root)
        guard = diff_guard(model)
        self.assertEqual(guard["status"], "blocked")
        args = dict(actor="synthetic-reviewer", reason="Revisión explícita de cobertura negativa.", observed_diff=guard["diff_fingerprint"])
        plan = review_diff(model, **args)
        review_diff(model, **args, authorized_hash=plan["preview_hash"])
        self.assertEqual(diff_guard(load(self.root))["status"], "within-scope")
        write(self.root, "tests/test_print.py", "def test_print():\n    pass\n")
        self.assertEqual(diff_guard(load(self.root))["status"], "blocked")

    def test_pause_and_changed_base_requires_reconciliation(self):
        self.begin()
        args = dict(state="paused", actor="synthetic-dev", at=AT, summary="Código todavía pendiente.", next_action="Continuar impresión.")
        model = load(self.root)
        plan = checkpoint(model, **args)
        checkpoint(model, **args, authorized_hash=plan["preview_hash"])
        self.assertEqual(resume(load(self.root), ["TASK-001"])["status"], "continue-recommended")
        write(self.root, "src/print.py", "changed = True\n")
        self.assertEqual(resume(load(self.root), ["TASK-001"])["status"], "reconcile-recommended")

    def test_block_durable_problem_and_cancel_not_completion(self):
        self.begin()
        args = dict(state="blocked", actor="synthetic-dev", at=AT, summary="Dependencia pendiente.", next_action="Resolver dependencia.")
        model = load(self.root)
        plan = checkpoint(model, **args)
        checkpoint(model, **args, authorized_hash=plan["preview_hash"])
        self.assertEqual(len(load(self.root).by_kind("problem")), 1)
        self.assertEqual(resume(load(self.root), ["TASK-001"])["status"], "reconcile-recommended")

    def test_diagnostic_never_executes(self):
        result = verify(load(self.root), ["TASK-001"], "ENV-001", "diagnostic", evidence_id="EVID-001", execute=True)
        self.assertEqual(result["processes_executed"], 0)
        self.assertEqual(result["writes"], [])

    def test_verification_requires_review_handoff(self):
        self.begin()
        with self.assertRaises(ContractError):
            verify(load(self.root), ["TASK-001"], "ENV-001", "development", evidence_id="EVID-001", execute=True, assessor=approved)

    def test_missing_gates_cannot_be_verified(self):
        self.begin()
        model = load(self.root)
        args = dict(state="in-review", actor="synthetic-dev", at=AT, summary="Código preparado para verificar.", next_action="Ejecutar gates.")
        plan = checkpoint(model, **args)
        checkpoint(model, **args, authorized_hash=plan["preview_hash"])
        result = verify(load(self.root), ["TASK-001"], "ENV-001", "development", evidence_id="EVID-001", execute=True, assessor=approved)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("GATE-UNIT", result["missing_critical_gates"])
        self.assertFalse((self.root / DOCS / "evidence/EVID-001.json").exists())

    def test_clean_text_merge_still_requires_semantic_review(self):
        with tempfile.TemporaryDirectory() as left_dir, tempfile.TemporaryDirectory() as right_dir:
            left, right = Path(left_dir), Path(right_dir)
            project(left)
            project(right)
            base = load(self.root)
            write(left, DOCS + "/02-specification/shared/rules.md", render_document("rule", "Regla transversal", [element("RULE-001", "rule", scope="global")]))
            path = right / self.feature
            path.write_text(path.read_text(encoding="utf-8").replace("Solo se imprime", "Nunca se imprime"), encoding="utf-8")
            result = semantic_merge(base, load(left), load(right))
            self.assertEqual(result["status"], "semantic-review-required")
            self.assertFalse(result["distributed_lock"])


if __name__ == "__main__":
    unittest.main()
