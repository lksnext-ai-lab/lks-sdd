"""Small independent corpus for literal scope and authoring boundaries.

Models and policy objects are real. No runtime package, Git repository, or whole
consumer is created: the few files below are the attachments being observed.
"""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from v3_contract import ContractError, Element, Model, element, sha
from v3_policy import profile


class ContextScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v4-scope-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model = Model(self.root)
        controls = {k: {"mode": "not-used", "reason": "Synthetic corpus"}
                    for k in ("sonar", "dependency-check")}
        self.policy = self.add("policy", "policy", **profile("individual-brief", controls))
        self.project = self.add("project", "project", policy=self.policy.uid)
        self.req = self.add("request", "request-a", policy=self.policy.uid,
                            policy_digest=self.policy.digest())
        self.other = self.add("request", "request-b", policy=self.policy.uid,
                              policy_digest=self.policy.digest())
        self.prop = self.add("proposal", "proposal-a", request=self.req.uid)
        self.foreign = self.add("proposal", "proposal-b", request=self.other.uid)
        self.req.relations["proposal"] = [self.prop.uid]
        self.other.relations["proposal"] = [self.foreign.uid]
        self.rule = self.add("requirement", "requirement-a", "Applicable literal requirement")
        self.remote = self.add("requirement", "requirement-b", "Independent literal requirement")
        self.prop.relations["requirements"] = [self.rule.uid]
        self.foreign.relations["requirements"] = [self.remote.uid]

    def add(self, kind, name, body=None, **data):
        obj = element(kind, name, body or "Literal " + name,
                      identifier=str(uuid.uuid5(uuid.NAMESPACE_URL, "v4-context:" + name)), **data)
        value = Element(obj["meta"], obj["body"], "docs/" + name + ".md")
        self.model.elements[value.uid] = value
        self.model.hashes[value.path] = sha((name + value.body).encode())
        return value

    def prose(self, path, text):
        self.model.prose[path] = text
        self.model.hashes[path] = sha(text.encode())
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return {"path": path, "sha256": sha(text.encode()), "units": [self.foreign.uid],
                "global": False, "reason": "Independent corpus section"}

    def govern(self, rows, assets=None):
        self.project.data["context_scopes"] = {"version": "lks-sdd-prose-scope/1", "sources": rows}
        return self.add("decision", "scope-proof", purpose="governance", outcome="approved",
                        decided_at="2026-10-17T00:00:00Z", descriptor={"units": {self.project.uid: self.project.digest()}},
                        presentation={"version": "lks-sdd-presentation/2", "event": "governance"},
                        **({"scope_assets": assets} if assets is not None else {}))

    def selected(self, roots=None, **kwargs):
        from v3_context import select
        return select(self.model, [self.prop.uid] if roots is None else roots, **kwargs)

    @staticmethod
    def keys(result):
        return {row["key"] for row in result["sources"]}

    def task_and_plans(self, second=None, explicit=None):
        task = element("task", "task", "Task", request=self.req.uid)
        if explicit is not None: task["meta"]["data"]["proposal_units"] = explicit
        plans = []
        for number, units in enumerate(([self.prop.uid], second) if second is not None else ([self.prop.uid],)):
            plan = element("plan", "plan-" + str(number), "Plan", request=self.req.uid, proposal_units=units)
            plan["meta"]["relations"]["tasks"] = [task["meta"]["uid"]]
            plans.append(plan)
        return [task, *plans]

    def test_authoring_inherits_unique_plan_without_mutating_input(self):
        from v3_scope import authoring_scopes
        items = self.task_and_plans()
        before = copy.deepcopy(items)
        result = authoring_scopes(self.model, items)
        self.assertEqual([self.prop.uid], result[0]["meta"]["data"]["proposal_units"])
        self.assertEqual(before, items)

    def test_authoring_same_scope_multiple_plans_is_order_independent(self):
        from v3_scope import authoring_scopes
        items = self.task_and_plans([self.prop.uid])
        a = authoring_scopes(self.model, items)[0]
        b = authoring_scopes(self.model, [items[0], *reversed(items[1:])])[0]
        self.assertEqual(a, b)

    def test_authoring_ambiguous_plan_scope_is_rejected_in_either_order(self):
        from v3_scope import authoring_scopes
        items = self.task_and_plans([self.foreign.uid])
        for ordered in (items, [items[0], *reversed(items[1:])]):
            with self.subTest(order=ordered[1]["meta"]["title"]), self.assertRaises(ContractError):
                authoring_scopes(self.model, ordered)

    def test_authoring_explicit_scope_cannot_contradict_plan(self):
        from v3_scope import authoring_scopes
        with self.assertRaises(ContractError):
            authoring_scopes(self.model, self.task_and_plans(explicit=[self.foreign.uid]))

    def test_preview_is_literal_readonly_and_grants_no_authority(self):
        from v3_scope import scope_preview
        row = self.prose("docs/unknown.md", "Unknown restriction. Never discard the final prohibition.")
        before = (copy.deepcopy(self.project.item()), dict(self.model.hashes))
        result = scope_preview(self.model, [self.prop.uid])
        self.assertFalse(result["authority_granted"])
        self.assertEqual([], result["writes"])
        self.assertIsNone(result["proposed_project"])
        source = next(r for r in result["sources"] if r["path"] == row["path"])
        self.assertEqual(self.model.prose[row["path"]], source["text"])
        self.assertEqual("unclassified", source["scope_status"])
        self.assertEqual(before, (self.project.item(), dict(self.model.hashes)))

    def test_preview_proposes_exact_governed_change_without_accrediting_it(self):
        from v3_scope import scope_preview
        row = self.prose("docs/proposed.md", "Independent rule")
        result = scope_preview(self.model, [self.prop.uid], proposals=[row])
        proposed = result["proposed_project"]
        self.assertEqual(self.project.meta["revision"] + 1, proposed["meta"]["revision"])
        self.assertEqual([row], proposed["meta"]["data"]["context_scopes"]["sources"])
        self.assertNotIn("context_scopes", self.project.data)
        self.assertIn("prose:" + row["path"], self.keys(self.selected()))

    def test_preview_rejects_stale_or_incomplete_scope_declarations(self):
        from v3_scope import scope_preview
        row = self.prose("docs/stale.md", "Current literal")
        for bad in ({**row, "sha256": "0" * 64}, {k: v for k, v in row.items() if k != "reason"}):
            with self.subTest(fields=sorted(bad)), self.assertRaises(ContractError):
                scope_preview(self.model, [self.prop.uid], proposals=[bad])

    def test_preview_bounds_legacy_batch_without_silent_classification(self):
        from v3_scope import scope_preview
        for index in range(105): self.prose(f"docs/legacy-{index:03}.md", "Unclassified " + str(index))
        result = scope_preview(self.model, [self.prop.uid])
        self.assertLessEqual(len(result["sources"]), 100)
        self.assertIsNone(result["proposed_project"])
        self.assertTrue(all(row["scope_status"] == "unclassified" for row in result["sources"]))
        self.assertEqual(105, len([k for k in self.keys(self.selected()) if k.startswith("prose:")]))

    def test_independent_obligation_inventory_keeps_shared_incoming_and_typed_transitive(self):
        # Expected set is declared directly, independently of either selector.
        shared = self.add("constraint", "shared", "Limit applies to both proposals")
        self.prop.relations["constraints"] = [shared.uid]
        self.foreign.relations["constraints"] = [shared.uid]
        incoming = self.add("interface", "incoming", "Consumer must receive a compatible response", request=self.other.uid)
        incoming.relations["contributes_to"] = [self.rule.uid]
        transit = self.add("constraint", "transitive", "Never expose private response fields", request=self.other.uid)
        incoming.relations["depends_on"] = [transit.uid]
        typed = self.add("interface", "typed", "Typed dependency must remain compatible", request=self.other.uid)
        self.prop.data["dependencies"] = [{"uid": typed.uid, "type": "requires"}]
        global_rule = self.add("rule", "global", "Never weaken authentication", **{"global": True})
        unknown = self.add("rule", "unknown", "Unknown applicability must remain visible")
        expected = {self.rule.uid, shared.uid, incoming.uid, transit.uid, typed.uid, global_rule.uid, unknown.uid}
        result = self.selected()
        self.assertTrue(expected <= self.keys(result))
        for value in (shared, incoming, transit, typed, global_rule, unknown):
            self.assertEqual(value.body, next(r["text"] for r in result["sources"] if r["key"] == value.uid))
        self.assertIn("scope_diagnostics", result)

    def test_empty_retired_or_ambiguous_root_never_claims_sufficiency(self):
        from v3_context import select
        with self.assertRaises(ContractError): select(self.model, [])
        self.prop.meta["state"] = "retired"
        with self.assertRaises(ContractError): self.selected()
        self.prop.meta["state"] = "draft"
        self.foreign.meta["id"] = self.prop.id
        with self.assertRaises(ContractError): select(self.model, [self.prop.id])

    def test_foreign_accredited_growth_stays_out_but_unknown_and_global_expand(self):
        from v3_scope import scope_preview
        before = self.keys(self.selected())
        rows = [self.prose(f"docs/foreign-{i}.md", "Unrelated text " + str(i)) for i in range(4)]
        preview = scope_preview(self.model, [self.prop.uid], proposals=rows)
        self.assertFalse(preview["authority_granted"])
        self.assertEqual([], preview["writes"])
        self.assertEqual(rows, preview["proposed_project"]["meta"]["data"]["context_scopes"]["sources"])
        self.assertTrue({"prose:" + row["path"] for row in rows} <= self.keys(self.selected()))
        self.govern(rows)
        result = self.selected()
        self.assertEqual(before, self.keys(result))
        self.assertEqual(4, len(result["excluded_prose"]))
        self.prose("docs/new-unknown.md", "Unknown new prohibition")
        global_rule = self.add("rule", "new-global", "New global prohibition", **{"global": True})
        expanded = self.keys(self.selected())
        self.assertIn("prose:docs/new-unknown.md", expanded)
        self.assertIn(global_rule.uid, expanded)

    def test_changed_prose_revoked_proof_and_changed_governance_restore_literal(self):
        row = self.prose("docs/foreign.md", "Independent scope")
        proof = self.govern([row])
        self.assertNotIn("prose:" + row["path"], self.keys(self.selected()))
        self.model.prose[row["path"]] += "\nNow shared."
        self.assertIn("prose:" + row["path"], self.keys(self.selected()))
        self.model.prose[row["path"]] = "Independent scope"
        revoke = self.add("decision", "revoke-scope", outcome="revoked", revokes=proof.uid)
        self.assertIn("prose:" + row["path"], self.keys(self.selected()))
        del self.model.elements[revoke.uid]
        self.project.data["context_scopes"]["sources"][0]["reason"] = "Changed classification"
        self.assertIn("prose:" + row["path"], self.keys(self.selected()))

    def test_mixed_global_prose_conflicts_and_distinct_negative_rules_are_retained(self):
        row = self.prose("docs/mixed.md", "Foreign feature notes. Global: do not log credentials.")
        self.govern([{**row, "global": True}])
        self.remote.data["request"] = self.req.uid
        negative = self.add("rule", "negative", "May accept retries.\n" + "detail " * 5000 + "\nMust not retry charges.")
        result = self.selected()
        self.assertIn("prose:" + row["path"], self.keys(result))
        self.assertIn(self.remote.uid, self.keys(result))
        self.assertIn(negative.uid, self.keys(result))
        self.assertTrue(next(r["text"] for r in result["sources"] if r["key"] == negative.uid).endswith("Must not retry charges."))
        self.assertTrue(any(r.get("uid") == self.remote.uid for r in result["widened"]))

    def test_changed_attachment_or_missing_manifest_invalidates_exclusion(self):
        row = self.prose("docs/foreign-image.md", "Independent visual contract ![diagram](evidence/diagram.png)")
        picture = self.root / "docs/evidence/diagram.png"
        picture.parent.mkdir(exist_ok=True)
        picture.write_bytes(b"original-image")
        manifest = {row["path"]: [{"path": "docs/evidence/diagram.png", "sha256": sha(picture.read_bytes())}]}
        proof = self.govern([row], manifest)
        self.assertNotIn("prose:" + row["path"], self.keys(self.selected()))
        picture.write_bytes(b"changed-image-with-global-obligation")
        self.assertIn("prose:" + row["path"], self.keys(self.selected()))
        picture.write_bytes(b"original-image")
        proof.data.pop("scope_assets")
        self.assertIn("prose:" + row["path"], self.keys(self.selected()))

    def test_necessary_visual_and_transitive_text_assets_preserve_observation_boundary(self):
        self.prose("docs/visual.md", "See [contract](evidence/contract.txt)")
        folder = self.root / "docs/evidence"
        folder.mkdir(exist_ok=True)
        (folder / "contract.txt").write_text("Do not crop this diagram. ![rule](diagram.png)", encoding="utf-8")
        (folder / "diagram.png").write_bytes(b"visual-bytes")
        result = self.selected()
        assets = {a["path"]: a for a in result["attachments"]}
        self.assertIn("Do not crop", assets["docs/evidence/contract.txt"]["text"])
        self.assertTrue(assets["docs/evidence/diagram.png"]["requires_observation"])
        self.assertEqual("requires-attachment-observation", result["sufficiency"])

    def test_comparison_is_explicit_and_never_claims_semantic_equivalence(self):
        import v3_context
        v3_context._CACHE.clear()
        self.addCleanup(v3_context._CACHE.clear)
        with patch("v3_context.load", return_value=self.model), patch("v3_git.observe", return_value={"branch": "test", "head": "a" * 40}):
            result = v3_context.context(self.root, [self.prop.uid], comparison=True)
        comparison = result["comparison"]
        self.assertEqual("not-established", comparison["semantic_equivalence"])
        self.assertIn(self.remote.uid, comparison["reference_only"])
        self.assertEqual([], comparison["selected_only"])
        self.assertTrue(comparison["shared_literal_equal"])
        self.assertGreaterEqual(comparison["reference_characters"], comparison["selected_characters"])
        self.assertIn("excluded_units", result)

    def test_approval_descriptor_tracks_incoming_and_typed_contract_changes(self):
        from v3_approval import descriptor
        incoming = self.add("interface", "incoming-approval", request=self.other.uid)
        incoming.relations["interfaces"] = [self.rule.uid]
        typed = self.add("constraint", "typed-approval", request=self.other.uid)
        self.prop.data["dependencies"] = [{"uid": typed.uid, "type": "requires"}]
        before = descriptor(self.model, [self.prop.uid])
        self.assertTrue({incoming.uid, typed.uid} <= set(before["units"]))
        incoming.body += "\nA newly introduced prohibition."
        self.assertNotEqual(before["digest"], descriptor(self.model, [self.prop.uid])["digest"])

    def test_approval_descriptor_does_not_turn_incoming_tasks_into_authority(self):
        from v3_approval import descriptor
        task = self.add("task", "incoming-task", request=self.req.uid)
        task.relations["implements"] = [self.prop.uid]
        plan = self.add("plan", "incoming-plan", request=self.req.uid)
        plan.relations["depends_on"] = [self.prop.uid]
        result = descriptor(self.model, [self.prop.uid])
        self.assertNotIn(task.uid, result["units"])
        self.assertNotIn(plan.uid, result["units"])

    def test_incoming_proposal_is_a_dependency_not_an_independent_approval(self):
        from v3_approval import approved, descriptor
        self.foreign.relations["depends_on"] = [self.prop.uid]
        exact = descriptor(self.model, [self.prop.uid])
        self.assertIn(self.foreign.uid, exact["units"])
        self.add("decision", "approve-only-a", purpose="proposal", outcome="approved",
                 descriptor=exact, approval_roots=[self.prop.uid])
        self.assertTrue(approved(self.model, [self.prop.uid])["valid"])
        self.assertFalse(approved(self.model, [self.foreign.uid])["valid"])
        self.assertFalse(approved(self.model, [self.prop.uid, self.foreign.uid])["valid"])
        # An unrelated legacy decision must not make dependency coverage become
        # a fresh approval of B when its own roots have never been approved.
        self.add("decision", "unrelated-legacy", purpose="proposal", outcome="approved",
                 descriptor={"units": {self.rule.uid: self.rule.digest()}})
        self.assertFalse(approved(self.model, [self.foreign.uid])["valid"])
        self.add("decision", "approve-only-b", purpose="proposal", outcome="approved",
                 descriptor=descriptor(self.model, [self.foreign.uid]), approval_roots=[self.foreign.uid])
        self.assertTrue(approved(self.model, [self.prop.uid, self.foreign.uid])["valid"])
        self.rule.body += "\nA changed shared obligation invalidates both exact decisions."
        self.assertFalse(approved(self.model, [self.prop.uid, self.foreign.uid])["valid"])

    def interface_plan(self):
        """A published-style plan names its task/contracts, not their parent proposal."""
        self.prop.body = "Reviewed functional and technical proposal with its exact interface and technology."
        self.prop.data.update(part="joint", objective="Keep contract", included=["app.py"],
            excluded=[], impact="One module", acceptance=["Contract"], behavior="Keep interface",
            solution="Reviewed explicit technical solution")
        interface = self.add("interface", "owned-interface", "Exact contract")
        interface.relations["interfaces"] = [self.rule.uid]
        technology = self.add("technology", "owned-technology", "Exact selected technology")
        self.prop.relations["interfaces"] = [interface.uid]
        self.prop.relations["technology"] = [technology.uid]
        task = self.add("task", "owned-task", request=self.req.uid, scope=["app.py"], proposal_units=[self.prop.uid])
        task.relations["covers"] = [interface.uid]
        plan = self.add("plan", "owned-plan", request=self.req.uid, proposal_units=[self.prop.uid])
        plan.relations["tasks"] = [task.uid]
        # Independent historical expectation: only these four units were agreed
        # in the plan; proposal/technology have their own exact approval boundary.
        units = {e.uid: e.digest() for e in (plan, task, interface, self.rule)}
        return plan, task, interface, technology, units

    def legacy_plan_decision(self, plan, task, units, purpose="plan"):
        from v3_approval import task_basis
        return self.add("authorization" if purpose == "execution" else "decision",
            "legacy-" + purpose, purpose=purpose, outcome="approved",
            descriptor={"units": units}, task_bases={task.uid: task_basis(self.model, task, plan)})

    def test_legacy_plan_retains_authority_without_reapproving_interface_owner(self):
        from v3_approval import approved, descriptor, task_authority
        plan, task, interface, technology, units = self.interface_plan()
        self.legacy_plan_decision(plan, task, units)
        self.legacy_plan_decision(plan, task, units, "execution")
        self.assertEqual(units, descriptor(self.model, [plan.uid])["units"])
        self.assertTrue(approved(self.model, [plan.uid], "plan")["valid"])
        self.assertTrue(approved(self.model, [plan.uid], "execution")["valid"])
        self.assertTrue(task_authority(self.model, task, plan, "execution")["valid"])
        self.assertTrue({self.prop.uid, technology.uid, interface.uid} <= self.keys(self.selected([task.uid])))
        self.prop.body += " A material proposal change."
        self.assertFalse(task_authority(self.model, task, plan, "execution")["valid"])

    def test_interface_membership_does_not_hide_explicit_or_typed_dependencies(self):
        from v3_approval import descriptor
        plan, task, interface, technology, units = self.interface_plan()
        for relation in ("depends_on", "modifies", "implements", "contributes_to"):
            with self.subTest(relation=relation):
                self.prop.relations[relation] = [interface.uid]
                self.assertTrue({self.prop.uid, technology.uid} <= set(descriptor(self.model, [plan.uid])["units"]))
                del self.prop.relations[relation]
        self.prop.data["dependencies"] = [{"uid": interface.uid, "type": "requires"}]
        self.assertTrue({self.prop.uid, technology.uid} <= set(descriptor(self.model, [plan.uid])["units"]))

    def test_legacy_plan_stales_on_contract_and_technology_changes(self):
        from v3_approval import approved, task_authority
        plan, task, interface, technology, units = self.interface_plan()
        self.legacy_plan_decision(plan, task, units)
        self.legacy_plan_decision(plan, task, units, "execution")
        interface.body += " A changed contract prohibition."
        self.assertFalse(approved(self.model, [plan.uid], "plan")["valid"])
        self.assertFalse(task_authority(self.model, task, plan, "execution")["valid"])
        interface.body = "Exact contract"
        self.assertTrue(task_authority(self.model, task, plan, "execution")["valid"])
        technology.body += " A changed technology decision."
        self.assertFalse(task_authority(self.model, task, plan, "execution")["valid"])

    def test_legacy_plan_revocation_and_global_proposal_are_not_ignored(self):
        from v3_approval import approved, descriptor
        plan, task, interface, technology, units = self.interface_plan()
        previous = self.legacy_plan_decision(plan, task, units)
        self.add("decision", "revoke-legacy-plan", purpose="plan", outcome="revoked", revokes=previous.uid)
        self.assertFalse(approved(self.model, [plan.uid], "plan")["valid"])
        self.prop.data["global"] = True
        self.assertTrue({self.prop.uid, technology.uid} <= set(descriptor(self.model, [plan.uid])["units"]))

    def test_legacy_feature_interface_inventory_is_not_an_incoming_obligation(self):
        from v3_approval import descriptor
        plan, task, interface, technology, units = self.interface_plan()
        feature = self.add("feature", "legacy-owner", legacy=True, request=self.req.uid)
        feature.relations["interfaces"] = [interface.uid]
        feature.relations["technology"] = [technology.uid]
        self.assertEqual(units, descriptor(self.model, [plan.uid])["units"])
        feature.relations["depends_on"] = [interface.uid]
        self.assertIn(feature.uid, descriptor(self.model, [plan.uid])["units"])

    def test_retired_plan_does_not_override_current_task_scope(self):
        from v3_scope import authoring_scopes
        items = self.task_and_plans()
        old = self.add("plan", "retired-plan", request=self.req.uid, proposal_units=[self.foreign.uid])
        old.meta["state"] = "retired"
        old.relations["tasks"] = [items[0]["meta"]["uid"]]
        result = authoring_scopes(self.model, items)
        self.assertEqual([self.prop.uid], result[0]["meta"]["data"]["proposal_units"])


if __name__ == "__main__": unittest.main()
