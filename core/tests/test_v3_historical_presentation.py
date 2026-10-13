"""Migrated antecedents never acquire current team authority through a view."""
import copy
import unittest
from unittest.mock import patch

from test_v3_workflow import ProjectFixture, commit_packet
from presentation_test_support import present
import v2_contract as v2
from v3_contract import ContractError, element, fingerprint, load, read_bytes, sha
from v3_decision_presentation import decision_view, safe
from v3_storage import prepare
from v3_verification import accept, evidence


class HistoricalPresentationTests(ProjectFixture):
    def history(self, *, state="completed", owner="Former synthetic maintainer", scope=None,
                external_inventory=False, virtual_original=False, critical=False):
        """Create recoverable v2 bytes and the same lineage fields as the migrator."""
        source_path = "docs/lks-sdd/04-delivery/history-task.md"
        body = "Original historical body. Keep the unresolved audit observation."
        data = {"owner": owner, "tests": ["legacy_test"], "acceptance": ["Original criterion"],
                "pending": ["Original pending observation"], "members": ["Second original maintainer"],
                "basis": {"original": "Exact old basis"}, "receipt": "Original result receipt"}
        if scope is not None: data["scope"] = scope
        if critical: data.update(critical=True, unresolved=["Original unresolved critical observation"])
        old = v2.make_element("TASK-HISTORY-001", "task", "Migrated synthetic task", body, state=state, **data)
        raw = v2.render_document("task", "Original task", [old])
        original_body = v2.parse_document(raw.decode("utf-8"), source_path)[0][0].body
        migration = element("migration", "Synthetic migration", "Original migration statement.",
                            source={"format": "2.0", "method": "2.1.0", "snapshot": fingerprint({source_path: sha(raw)})},
                            mapping={old["meta"]["id"]: old["meta"]["uid"]})
        original = "docs/lks-sdd/00-control/migrations/" + migration["meta"]["uid"] + "/tree/" + source_path
        changes = {}
        if virtual_original:
            from document_state import prepare as preserve, PREFIX
            source_file = self.root / source_path
            source_file.parent.mkdir(parents=True, exist_ok=True); source_file.write_bytes(raw)
            original = PREFIX + preserve(self.root, {source_path: sha(raw)}, changes) + "/tree/" + source_path
            source_file.unlink()
        else: changes[original] = raw
        inventory = [{"path": source_path, "sha256": sha(raw), "original": original,
                      "disposition": "converted-with-original"}]
        if external_inventory:
            from content_store import prepare_object
            migration["meta"]["data"]["inventory_ref"] = prepare_object(
                self.root, v2.canonical({"format": "lks-sdd-migration-inventory/1", "entries": inventory}), changes)
        else: migration["meta"]["data"]["inventory"] = inventory
        continuation = "historical" if state in {"done", "completed", "cancelled", "done-with-reservations"} else "reconciliation-required"
        task = element("task", old["meta"]["title"], original_body, identifier=old["meta"]["uid"],
                       **data, dependencies=[], continuation=continuation,
                       legacy={"schema": "2.0", "method": "2.1.0", "id": old["meta"]["id"],
                               "path": source_path, "state": state, "source_sha256": sha(raw),
                               "original": original, "migration": migration["meta"]["uid"]})
        task["meta"].update(id=old["meta"]["id"], state=state)
        commit_packet(self.root, prepare(self.root, [migration, task], "synthetic-migrated-history", changes=changes))
        return task["meta"]["uid"], migration["meta"]["uid"], original

    def related(self, history):
        task = copy.deepcopy(load(self.root).get(self.task).item())
        task["meta"]["revision"] += 1
        task["meta"]["relations"]["depends_on"] = [history]
        commit_packet(self.root, prepare(self.root, [task], "synthetic-history-link"))

    def completed_result(self):
        from v3_authoring import approve_and_authorize
        commit_packet(self.root, present(approve_and_authorize, self.root, self.actor, self.plan_id,
                                          "Confirm the current plan with its historical background."))
        self.advance("start")
        (self.root / "app.py").write_text("def greeting(): return 'Hola'\n")
        self.advance("implement")
        report_path = "docs/lks-sdd/evidence/current-result.txt"
        report = self.root / report_path; report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("Current test observed Hola; no data was written.")
        commit_packet(self.root, evidence(self.root, self.actor, self.task, ["test_saludo"], "passed",
                                          "automated", report_path, "Synthetic current result."))
        self.advance("verify"); self.advance("close")

    def acceptance_policy(self):
        # A real supported policy, allowing direct functional acceptance of the candidate.
        from v3_authoring import governance
        policy = copy.deepcopy(load(self.root).get(load(self.root).project.data["policy"]).item())
        policy["meta"]["revision"] += 1
        policy["meta"]["data"]["acceptance_order"] = "before-integration"
        for step in policy["meta"]["data"]["steps"]:
            if step["id"] == "acceptance": step.update(requires=["verification"], conditions=["closed"])
        commit_packet(self.root, present(governance, self.root, self.actor, [policy],
                                          "Configure candidate acceptance.", "Synthetic lifecycle decision."))

    def test_related_history_preserves_all_data_in_result_profiles(self):
        self.plan()
        histories = [self.history(state=s, scope=["obsolete/path"] if s == "completed" else None)
                     for s in ("completed", "in-progress")]
        task = copy.deepcopy(load(self.root).get(self.task).item())
        task["meta"]["revision"] += 1
        task["meta"]["relations"]["depends_on"] = [h[0] for h in histories]
        commit_packet(self.root, prepare(self.root, [task], "synthetic-history-links"))
        for event in ("verify", "integrate", "accept"):
            with self.subTest(event=event), patch("v3_team.owners", wraps=__import__("v3_team").owners) as owners:
                view = decision_view(self.root, event, {"actor": self.actor, "request": self.req})
                self.assertEqual({self.task}, {call.args[1].uid for call in owners.call_args_list})
                for key, migration, original in histories:
                    self.assertIn(key, {s["key"] for s in view["sources"]})
                    self.assertIn(migration, {s["key"] for s in view["sources"]})
                    self.assertIn(original, {a["path"] for a in view["attachments"]})
                    self.assertEqual(sha(read_bytes(self.root, original)),
                                     next(a["sha256"] for a in view["attachments"] if a["path"] == original))
                for literal in ("Original historical body", "Former synthetic maintainer", "Second original maintainer",
                                "Original pending observation", "Exact old basis", "Original result receipt", "obsolete/path"):
                    self.assertIn(literal, view["markdown"])
                self.assertIn("no confiere autoridad actual", view["markdown"])
                self.assertEqual(["app.py"], view["basis"]["subject"]["scope"])

    def test_direct_history_queries_include_literal_owners_and_pending(self):
        for state in ("completed", "in-progress", "cancelled"):
            with self.subTest(state=state):
                key, _, _ = self.history(state=state, owner=self.actor)
                with patch("v3_team.owners", side_effect=AssertionError("History must not resolve current owners")):
                    view = decision_view(self.root, "trace", {"task": key})
                self.assertIn(safe(self.actor), view["markdown"])
                self.assertIn("Original pending observation", view["markdown"])
                self.assertIn("Original historical body", view["markdown"])
                self.assertTrue(view["complete"], view["issues"])

    def test_current_owners_remain_strict_with_historical_background(self):
        self.plan(); key, _, _ = self.history(); self.related(key)
        current = copy.deepcopy(load(self.root).get(self.task).item())
        for owner, active, roles in (("Missing current owner", True, ["developer"]),
                                     (self.actor, False, ["owner"]), (self.actor, True, ["reviewer"])):
            with self.subTest(owner=owner, active=active, roles=roles):
                current["meta"]["revision"] += 1; current["meta"]["data"]["owner"] = owner
                person = copy.deepcopy(load(self.root).get(self.actor).item()); person["meta"]["revision"] += 1
                person["meta"]["data"].update(active=active, roles=roles)
                commit_packet(self.root, prepare(self.root, [current, person], "synthetic-invalid-current-owner"))
                with self.assertRaises(ContractError): decision_view(self.root, "verify", {"task": self.task})

    def test_forged_migration_provenance_blocks(self):
        key, _, _ = self.history()
        original = copy.deepcopy(load(self.root).get(key).item())
        for field, value in (("migration", self.actor), ("source_sha256", "0" * 64),
                             ("id", "TASK-OTHER-001"), ("state", "in-progress"), ("original", "missing.md"),
                             ("method", "1.5.0")):
            with self.subTest(field=field):
                task = copy.deepcopy(original); task["meta"]["revision"] = load(self.root).get(key).meta["revision"] + 1
                task["meta"]["data"]["legacy"][field] = value
                commit_packet(self.root, prepare(self.root, [task], "synthetic-forged-provenance"))
                with self.assertRaisesRegex(ContractError, "[Pp]rocedencia"):
                    decision_view(self.root, "trace", {"task": key})

    def test_continuation_alone_never_bypasses_current_ownership(self):
        self.plan()
        task = copy.deepcopy(load(self.root).get(self.task).item())
        task["meta"]["revision"] += 1; task["meta"]["data"].update(continuation="historical", owner="Missing owner")
        commit_packet(self.root, prepare(self.root, [task], "synthetic-false-history"))
        with self.assertRaises(ContractError): decision_view(self.root, "verify", {"task": self.task})

    def test_reconciled_tasks_return_to_current_owner_validation(self):
        self.plan(); key, _, _ = self.history(state="in-progress")
        task = copy.deepcopy(load(self.root).get(key).item()); task["meta"]["revision"] += 1
        task["meta"]["data"].update(continuation="reconciled-content-needs-current-authorization",
                                     request=self.req, scope=["app.py"])
        commit_packet(self.root, prepare(self.root, [task], "synthetic-reconciliation"))
        with self.assertRaises(ContractError): decision_view(self.root, "verify", {"task": key})

    def test_external_inventory_and_virtual_original_are_bound_to_view(self):
        key, migration, original = self.history(external_inventory=True, virtual_original=True)
        view = decision_view(self.root, "trace", {"task": key})
        from content_store import object_path
        inventory = load(self.root).get(migration).data["inventory_ref"]
        self.assertEqual(inventory["sha256"], view["basis"]["source_files"][object_path(inventory)])
        from document_state import dependencies
        for path, digest in dependencies(self.root, original).items():
            self.assertEqual(digest, view["basis"]["source_files"][path])
        self.assertIn(original, {a["path"] for a in view["attachments"]})

    def test_pending_reconciliation_result_cannot_be_accepted(self):
        self.acceptance_policy(); self.plan(); self.completed_result()
        key, _, _ = self.history(state="in-progress")
        task = copy.deepcopy(load(self.root).get(key).item()); task["meta"]["revision"] += 1
        task["meta"]["data"]["request"] = self.req
        commit_packet(self.root, prepare(self.root, [task], "synthetic-pending-result"))
        view = decision_view(self.root, "accept", {"actor": self.actor, "request": self.req})
        self.assertFalse(view["complete"])
        self.assertIn("reconciliación", " ".join(view["issues"]))
        with self.assertRaises(ContractError): accept(self.root, self.actor, self.req, "Approve pending result.", presented=view["receipt"])

    def test_current_acceptance_with_history_and_stale_receipts(self):
        from v3_authoring import approve_and_authorize
        from v3_approval import task_authority
        from v3_workflow import plan_for
        self.acceptance_policy(); self.plan()
        key, migration, original = self.history(state="in-progress"); self.related(key)
        self.completed_result()
        history = copy.deepcopy(load(self.root).get(key).item()); history["meta"]["revision"] += 1
        history["meta"]["data"].update(critical=True, unresolved=["Original unresolved critical observation"])
        commit_packet(self.root, prepare(self.root, [history], "synthetic-historical-pending-note"))
        commit_packet(self.root, present(approve_and_authorize, self.root, self.actor, self.plan_id,
                                          "Confirm the current plan with the complete pending background."))
        data = {"actor": self.actor, "request": self.req, "statement": "Accept this candidate."}
        view = decision_view(self.root, "accept", data)
        self.assertTrue(view["complete"], view["issues"])
        history = copy.deepcopy(load(self.root).get(key).item()); history["meta"]["revision"] += 1
        history["body"] += " Another historical pending detail."
        commit_packet(self.root, prepare(self.root, [history], "synthetic-updated-background"))
        with self.assertRaisesRegex(ContractError, "receipt"):
            accept(self.root, self.actor, self.req, data["statement"], presented=view["receipt"])
        model = load(self.root)
        self.assertFalse(task_authority(model, model.get(self.task), plan_for(model, model.get(self.task)), "execution")["valid"])
        commit_packet(self.root, present(approve_and_authorize, self.root, self.actor, self.plan_id,
                                          "Review and authorize the updated normative reference."))
        fresh = decision_view(self.root, "accept", data)
        self.assertNotEqual(view["receipt"], fresh["receipt"])
        packet = accept(self.root, self.actor, self.req, data["statement"], presented=fresh["receipt"])
        self.assertIn(original, packet["preview"]["sources"])
        self.assertIn(load(self.root).get(migration).path, packet["preview"]["sources"])
        self.assertTrue(packet["guards"]["subject"])
        original_file = self.root / original; original_file.write_bytes(original_file.read_bytes() + b"\nChanged concurrently\n")
        with self.assertRaises(ContractError): commit_packet(self.root, packet)

    def test_original_bytes_and_migration_mapping_are_rechecked(self):
        key, migration, original = self.history()
        view = decision_view(self.root, "trace", {"task": key})
        original_file = self.root / original; raw = original_file.read_bytes()
        original_file.write_bytes(raw + b"\nAltered original\n")
        with self.assertRaisesRegex(ContractError, "[Pp]rocedencia"): decision_view(self.root, "trace", {"task": key})
        original_file.write_bytes(raw)
        receipt = copy.deepcopy(load(self.root).get(migration).item()); receipt["meta"]["revision"] += 1
        receipt["meta"]["data"]["mapping"]["TASK-HISTORY-001"] = self.actor
        commit_packet(self.root, prepare(self.root, [receipt], "synthetic-altered-mapping"))
        with self.assertRaisesRegex(ContractError, "[Pp]rocedencia"): decision_view(self.root, "trace", {"task": key})

    def test_historical_attachment_keeps_observation_and_freshness(self):
        import base64
        key, _, _ = self.history(state="cancelled")
        task = copy.deepcopy(load(self.root).get(key).item()); task["meta"]["revision"] += 1
        task["body"] += "\n[Historical screen](../evidence/historical.png)\n"
        path = "docs/lks-sdd/evidence/historical.png"
        raw = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")
        commit_packet(self.root, prepare(self.root, [task], "synthetic-history-attachment", changes={path: raw}))
        pending = decision_view(self.root, "trace", {"task": key})
        self.assertFalse(pending["complete"])
        self.assertTrue(next(a for a in pending["attachments"] if a["path"] == path)["requires_observation"])
        data = {"task": key, "observed_assets": {path: sha(raw)}}
        observed = decision_view(self.root, "trace", data)
        self.assertTrue(observed["complete"], observed["issues"])
        (self.root / path).write_bytes(raw + b"changed")
        changed = decision_view(self.root, "trace", data)
        self.assertFalse(changed["complete"])
        self.assertNotEqual(observed["receipt"], changed["receipt"])

    def test_actual_migrator_lineage_is_readable(self):
        from test_v3_migration import MigrationTests
        from eval_support import materialize_ready_increment
        fixture = MigrationTests("test_conversion_preserves_identity_originals_and_code")
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        materialize_ready_increment(fixture.root)
        packet = fixture.packet(); commit_packet(fixture.root, packet)
        key = packet["summary"]["mapping"]["TASK-001"]
        view = decision_view(fixture.root, "trace", {"task": key})
        self.assertIn("no confiere autoridad actual", view["markdown"])
        self.assertIn("reconciliation-required", view["markdown"])
        original = load(fixture.root).get(key).data["legacy"]["original"]
        self.assertIn(original, {a["path"] for a in view["attachments"]})

    def test_cancelled_historical_root_keeps_related_contract_and_evidence(self):
        self.plan()
        key, _, _ = self.history(state="cancelled")
        requirement = element("requirement", "Scoped historical condition", "Keep the condition of the cancelled task.", request=self.req)
        history = copy.deepcopy(load(self.root).get(key).item()); history["meta"]["revision"] += 1
        history["meta"]["relations"]["requirements"] = [requirement["meta"]["uid"]]
        record = element("checkpoint", "Historical pending evidence", "Keep this pending evidence of the cancelled task.",
                         task=key, pending=["Review original observation"])
        commit_packet(self.root, prepare(self.root, [requirement, history, record], "synthetic-cancelled-task-context"))
        view = decision_view(self.root, "trace", {"task": key})
        for uid in (key, requirement["meta"]["uid"], record["meta"]["uid"]):
            self.assertIn(uid, {s["key"] for s in view["sources"]})
        self.assertIn(requirement["body"], view["markdown"])
        self.assertIn(record["body"], view["markdown"])
        self.assertTrue(view["complete"], view["issues"])


if __name__ == "__main__": unittest.main()
