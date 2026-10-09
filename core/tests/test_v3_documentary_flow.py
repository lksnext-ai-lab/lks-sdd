"""Task-wide documentary efficiency with literal obligations and fresh guards."""
import contextlib
import copy
import io
import json
from unittest.mock import patch

from test_v3_workflow import ProjectFixture, commit_packet
from presentation_test_support import present, technical_solution
from v3_contract import load, element, render, sha, DOCS
from v3_authoring import author, governance


class DocumentaryFlowTests(ProjectFixture):
    def two_proposals(self):
        rows = []
        self.requests, self.proposals, self.requirements = [], [], []
        for number in range(2):
            req = element("request", f"Petición {number}", f"Objetivo independiente {number}")
            rule = element("requirement", f"Condición {number}", f"Obligación literal independiente {number}")
            prop = element("proposal", f"Propuesta {number}", f"Comportamiento acordado {number}",
                           request=req["meta"]["uid"], part="joint", objective="Corregir", included=["módulo"],
                           excluded=["otras peticiones"], behavior="Conservar contrato", solution=technical_solution(),
                           impact="Local", acceptance=["Resultado verificable"], unresolved=[])
            prop["meta"]["relations"]["requirements"] = [rule["meta"]["uid"]]
            req["meta"]["relations"]["proposal"] = [prop["meta"]["uid"]]
            rows += [req, prop, rule]
            self.requests.append(req["meta"]["uid"])
            self.proposals.append(prop["meta"]["uid"])
            self.requirements.append(rule["meta"]["uid"])
        commit_packet(self.root, author(self.root, self.actor, rows))

    def test_before_plan_scope_excludes_independent_units_and_keeps_incoming_globals(self):
        from v3_context import context
        self.two_proposals()
        global_rule = element("rule", "Regla global", "Nunca exceder 30 operaciones", **{"global": True})
        incoming = element("interface", "Contrato entrante", "Conservar API del consumidor", request=self.requests[1])
        incoming["meta"]["relations"]["contributes_to"] = [self.requirements[0]]
        cyclic_api = element("interface", "API compartida", "El callback debe conservar su contrato global", **{"global": True})
        cyclic_limit = element("constraint", "Límite del callback", "Nunca exceder 30 solicitudes del callback", request=self.requests[1])
        cyclic_api["meta"]["relations"]["depends_on"] = [cyclic_limit["meta"]["uid"]]
        cyclic_limit["meta"]["relations"]["depends_on"] = [cyclic_api["meta"]["uid"]]
        other = copy.deepcopy(load(self.root).get(self.proposals[1]).item())
        other["meta"]["revision"] += 1
        other["meta"]["relations"]["constraints"] = [cyclic_limit["meta"]["uid"]]
        commit_packet(self.root, author(self.root, self.actor, [global_rule, incoming, cyclic_api, cyclic_limit, other]))
        scoped = context(self.root, [self.requests[0]])
        keys = {s["key"] for s in scoped["sources"]}
        self.assertIn(self.requirements[0], keys)
        self.assertNotIn(self.requirements[1], keys)
        self.assertIn(global_rule["meta"]["uid"], keys)
        self.assertIn(incoming["meta"]["uid"], keys)
        self.assertIn(cyclic_api["meta"]["uid"], keys)
        self.assertIn(cyclic_limit["meta"]["uid"], keys)
        self.assertIn("Nunca exceder 30 solicitudes del callback", [s["text"] for s in scoped["sources"]])
        self.assertEqual("applicable-literal", scoped["selector_mode"])
        reference = context(self.root, [self.requests[0]], reference=True)
        self.assertIn(self.requirements[1], {s["key"] for s in reference["sources"]})
        # Request annotations cannot override its canonical proposal relationships.
        model = load(self.root); request = copy.deepcopy(model.get(self.requests[0]).item())
        request["meta"]["revision"] += 1
        request["meta"]["data"]["proposal_units"] = [self.proposals[1]]
        commit_packet(self.root, author(self.root, self.actor, [request]))
        self.assertIn(self.requirements[0], {s["key"] for s in context(self.root, [self.requests[0]])["sources"]})

    def test_shared_and_conflicting_memberships_preserve_literal_conditions(self):
        from v3_context import select
        self.two_proposals()
        model = load(self.root)
        shared = model.get(self.proposals[1]).item()
        shared["meta"]["revision"] += 1
        shared["meta"]["relations"]["requirements"].append(self.requirements[0])
        conflict = model.get(self.requirements[1]).item()
        conflict["meta"]["revision"] += 1
        conflict["meta"]["data"]["request"] = self.requests[0]
        commit_packet(self.root, author(self.root, self.actor, [shared, conflict]))
        packet = select(load(self.root), [self.requests[0]])
        self.assertIn(self.requirements[1], {s["key"] for s in packet["sources"]})
        self.assertTrue(any(r["uid"] == self.requirements[1] for r in packet["widened"]))
        from v3_decision_presentation import decision_view
        view = decision_view(self.root, "approve", {"actor": self.actor, "units": [self.proposals[0]], "purpose": "proposal"})
        self.assertFalse(view["complete"])
        self.assertTrue(any("discrepancia" in issue for issue in view["issues"]))

    def test_prose_declaration_needs_exact_governance_and_content_then_goes_stale(self):
        from v3_context import select
        self.two_proposals()
        path = DOCS + "/unrelated.md"
        prose = "Never change the unrelated limits. [Original log](evidence/old.log)"
        (self.root/path).write_text('---\nschema_version: "3.1"\n---\n\n'+prose+'\n', encoding="utf-8")
        log = self.root/DOCS/"evidence/old.log"
        log.parent.mkdir(exist_ok=True)
        log.write_text("Literal unrelated log", encoding="utf-8")
        model = load(self.root).require_valid()
        project = copy.deepcopy(model.project.item())
        project["meta"]["revision"] += 1
        project["meta"]["data"]["context_scopes"] = {"version": "lks-sdd-prose-scope/1", "sources": [
            {"path": path, "sha256": sha(model.prose[path].encode()), "units": [self.requests[1]],
             "global": False, "reason": "Contenido exclusivo de la segunda petición; sin restricciones compartidas"}]}
        # A manually entered assertion without the governing decision cannot exclude anything.
        (self.root/model.project.path).write_bytes(render(project, "3.1"))
        self.assertIn("prose:"+path, {s["key"] for s in select(load(self.root), [self.requests[0]])["sources"]})
        (self.root/model.project.path).write_bytes(render(model.project.item(), "3.1"))
        commit_packet(self.root, present(governance, self.root, self.actor, [project], "Confirmo este alcance exacto", "Aislar contenido independiente"))
        scoped = select(load(self.root), [self.requests[0]])
        self.assertNotIn("prose:"+path, {s["key"] for s in scoped["sources"]})
        self.assertEqual([], scoped["attachments"])
        self.assertTrue(scoped["scope_provenance"])
        # A legacy receipt did not present this extension's source scope choices.
        governed = load(self.root)
        proof = governed.get(scoped["scope_provenance"][1]["uid"])
        original = (self.root/proof.path).read_bytes()
        legacy_receipt = {**proof.data["presentation"], "version": "lks-sdd-presentation/1"}
        for unsupported in [legacy_receipt, None, ["unsupported"]]:
            legacy = copy.deepcopy(proof.item())
            legacy["meta"]["data"]["presentation"] = unsupported
            (self.root/proof.path).write_bytes(render(legacy, "3.1"))
            self.assertIn("prose:"+path, {s["key"] for s in select(load(self.root), [self.requests[0]])["sources"]})
        (self.root/proof.path).write_bytes(original)
        from v3_decision_presentation import decision_view
        # Scope proof can itself share a file with an independent canonical unit.
        model = load(self.root)
        project_path = self.root/model.project.path
        other = model.get(self.requirements[1])
        block = b"<!-- lks-sdd: " + render(other.item(), "3.1").split(b"<!-- lks-sdd: ", 1)[1]
        project_path.write_bytes(project_path.read_bytes()+b"\n"+block)
        (self.root/other.path).unlink()
        approve_data = {"actor": self.actor, "units": [self.proposals[0]], "purpose": "proposal"}
        prior_receipt = decision_view(self.root, "approve", approve_data)["receipt"]
        project_path.write_bytes(project_path.read_bytes().replace(b"Obligaci\xc3\xb3n literal independiente 1", b"Changed independent obligation"))
        self.assertEqual(prior_receipt, decision_view(self.root, "approve", approve_data)["receipt"])
        revised = copy.deepcopy(load(self.root).project.item())
        revised["meta"]["revision"] += 1
        revised["meta"]["data"]["context_scopes"]["sources"][0]["units"] = [self.requests[0]]
        query = {"actor": self.actor, "items": [revised], "statement": "Cambiar el alcance", "reason": "Reconciliación explícita"}
        changed_scope = decision_view(self.root, "governance", query)
        self.assertIn("Never change the unrelated limits", changed_scope["markdown"])
        self.assertIn("Literal unrelated log", changed_scope["markdown"])
        self.assertIn("Contenido exclusivo de la segunda petición", changed_scope["markdown"])
        self.assertIn("Aplica a", changed_scope["markdown"])
        self.assertIn("Petición 0", changed_scope["markdown"])
        revised["meta"]["data"]["context_scopes"]["sources"][0]["sha256"] = "0"*64
        self.assertFalse(decision_view(self.root, "governance", query)["complete"])
        relevant = select(load(self.root), [self.requests[1]])
        self.assertIn("Literal unrelated log", relevant["attachments"][0]["text"])
        self.assertFalse(relevant["attachments"][0].get("requires_observation", False))
        (self.root/path).write_text((self.root/path).read_text(encoding="utf-8")+"\nNew shared obligation.\n", encoding="utf-8")
        stale = select(load(self.root), [self.requests[0]])
        self.assertIn("prose:"+path, {s["key"] for s in stale["sources"]})
        self.assertEqual([], stale["excluded_prose"])

    def test_cli_review_has_one_body_and_explicit_details_with_same_receipt(self):
        from v3_cli import main
        self.plan()
        payload = self.root / "query.json"
        payload.write_text(json.dumps({"request": self.req}), encoding="utf-8")
        def run(*extra):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                result = main(["review", str(self.root), "--input", str(payload), "--json", *extra])
            self.assertEqual(0, result)
            return json.loads(stream.getvalue())
        brief, full = run("--compact"), run("--details")
        self.assertEqual(full, run())
        self.assertEqual(full["presentation"]["receipt"], brief["presentation"]["receipt"])
        self.assertEqual(full["presentation"]["markdown"], brief["presentation"]["markdown"])
        self.assertNotIn("sources", brief["presentation"])
        self.assertNotIn("description", brief["units"][0])
        self.assertIn("sources", full["presentation"])
        self.assertIn("description", full["units"][0])
        self.assertLess(len(json.dumps(brief)), len(json.dumps(full)))
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory(prefix="lks-review-export-") as directory:
            destination = Path(directory)/"full-review.json"
            shown = run("--compact", "--output", str(destination))
            self.assertEqual(brief, shown)
            self.assertEqual(full, json.loads(destination.read_text(encoding="utf-8")))

    def test_independent_prose_image_needs_observation_for_governance_and_global_scope(self):
        from v3_cli import execute
        from v3_context import select
        from v3_decision_presentation import decision_view
        # This case exercises the public mutation boundary with an actual pinned
        # current runtime, unlike the deliberately unpinned library fixtures.
        from test_v3_efficiency import EfficiencyTests
        EfficiencyTests.setUpClass()
        self.addCleanup(EfficiencyTests.tearDownClass)
        native = EfficiencyTests("test_native31_and_profiles_are_explicit_and_pinned")
        native.setUp(); self.addCleanup(native.doCleanups)
        self.root, self.actor = native.root, native.init()
        self.two_proposals()
        path, picture = DOCS + "/independent-visual.md", DOCS + "/evidence/visual.png"
        (self.root/path).write_text('---\nschema_version: "3.1"\n---\n\nIndependent visual contract. ![Reference](evidence/visual.png)\n', encoding="utf-8")
        asset = self.root/picture; asset.parent.mkdir(exist_ok=True)
        import base64
        raw = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aA1sAAAAASUVORK5CYII=")
        asset.write_bytes(raw)
        model = load(self.root).require_valid()
        project = copy.deepcopy(model.project.item()); project["meta"]["revision"] += 1
        project["meta"]["data"]["context_scopes"] = {"version": "lks-sdd-prose-scope/1", "sources": [
            {"path": path, "sha256": sha(model.prose[path].encode("utf-8")), "units": [self.requests[1]],
             "global": False, "reason": "The fixture visual contract applies exclusively to the second request"}]}
        query = {"actor": self.actor, "items": [project], "statement": "Accredit the literal visual scope", "reason": "Independent contract"}
        self.assertFalse(decision_view(self.root, "governance", query)["complete"])
        query["observed_assets"] = {picture: sha(raw)}
        commit_packet(self.root, present(execute, "governance", self.root, query))
        self.assertEqual([], select(load(self.root), [self.requests[0]])["attachments"])
        revised = copy.deepcopy(load(self.root).project.item()); revised["meta"]["revision"] += 1
        revised["meta"]["data"]["context_scopes"]["sources"][0]["global"] = True
        query["items"] = [revised]
        commit_packet(self.root, present(execute, "governance", self.root, query))
        view = decision_view(self.root, "approve", {"actor": self.actor, "units": [self.proposals[0]], "purpose": "proposal"})
        self.assertFalse(view["complete"])
        self.assertTrue(any(a["path"] == picture and a["requires_observation"] for a in view["attachments"]))

    def test_query_reuses_one_model_but_next_operation_reloads_changed_sources(self):
        from v3_cli import execute
        import v3_contract
        self.plan()
        original = v3_contract._load
        with patch("v3_contract._load", wraps=original) as loads:
            first = execute("review", self.root, {"request": self.req})
            self.assertEqual(1, loads.call_count)
            path = self.root / load(self.root).get(self.prop).path
            path.write_bytes(path.read_bytes() + b"\nNew global obligation after first query.\n")
            second = execute("review", self.root, {"request": self.req})
        self.assertNotEqual(first["presentation"]["receipt"], second["presentation"]["receipt"])
        self.assertIn("New global obligation", second["presentation"]["markdown"])

    def test_direct_review_reuses_its_validated_model(self):
        from v3_lifecycle import review
        self.plan()
        with patch("v3_decision_presentation.load", side_effect=AssertionError("duplicate model load")):
            value = review(self.root, self.req)
        self.assertTrue(value["presentation"]["complete"], value["presentation"]["issues"])

    def test_continuity_omits_old_simple_checkpoints_but_retains_pending_and_history(self):
        from v3_decision_presentation import collect, decision_view
        from v3_guidance import trace
        from v3_storage import prepare
        self.plan()
        rows = [element("checkpoint", f"Paso {i}", f"Avance previo {i}", task=self.task,
                        classification="progress", pending=["Reserva sin resolver"] if i == 0 else [], recorded_at=f"2026-10-09T00:00:{i:02d}+00:00") for i in range(10)]
        for row in rows: row["meta"].update(nature="fact", state="observed")
        rows[1]["meta"]["data"]["critical"] = True
        rows[2]["meta"]["data"].pop("classification")
        rows[3]["meta"]["data"]["outcome"] = "failed"
        commit_packet(self.root, prepare(self.root, rows, "synthetic-continuity-fixture"))
        packet = collect(load(self.root), [self.task], ["continuity"])
        checkpoints = [s for s in packet["sources"] if s.get("meta", {}).get("kind") == "checkpoint"]
        self.assertEqual(5, len(checkpoints))
        self.assertEqual(5, packet["history"]["omitted_checkpoints"])
        self.assertIn("Reserva sin resolver", decision_view(self.root, "pause", {"task": self.task})["markdown"])
        self.assertIn("Fallida", decision_view(self.root, "pause", {"task": self.task})["markdown"])
        self.assertEqual(10, len([e for e in trace(self.root, self.task, limit=100)["events"] if e["type"] == "checkpoint"]))
        explicit = collect(load(self.root), [rows[4]["meta"]["uid"]], ["continuity"])
        self.assertIn(rows[4]["meta"]["uid"], {s["key"] for s in explicit["sources"]})

    def test_checkpoint_retry_key_preserves_distinct_observations_and_rejects_reuse(self):
        from v3_lifecycle import checkpoint
        from v3_contract import ContractError
        self.plan()
        commit_packet(self.root, checkpoint(self.root, self.actor, self.task, "Observación", [], operation_id="attempt-1"))
        retry = checkpoint(self.root, self.actor, self.task, "Observación", [], operation_id="attempt-1")
        self.assertEqual("already-recorded", retry["status"])
        self.assertEqual([], retry["writes"])
        with self.assertRaisesRegex(ContractError, "otro hecho"):
            checkpoint(self.root, self.actor, self.task, "Observación diferente", [], operation_id="attempt-1")
        commit_packet(self.root, checkpoint(self.root, self.actor, self.task, "Observación", [], operation_id="attempt-2"))
        self.assertEqual(2, len(load(self.root).by_kind("checkpoint")))

    def test_independent_unit_in_same_file_keeps_receipt_but_applicable_change_invalidates_it(self):
        from v3_decision_presentation import decision_view
        self.two_proposals()
        model = load(self.root)
        own, other = [model.get(key) for key in self.requirements]
        first = render(own.item(), "3.1")
        second = b"<!-- lks-sdd: " + render(other.item(), "3.1").split(b"<!-- lks-sdd: ", 1)[1]
        path = self.root/own.path
        path.write_bytes(first + b"\n" + second)
        (self.root/other.path).unlink()
        data = {"actor": self.actor, "units": [self.proposals[0]], "purpose": "proposal"}
        before = decision_view(self.root, "approve", data)
        path.write_bytes(path.read_bytes().replace(b"Obligaci\xc3\xb3n literal independiente 1", b"Different independent obligation"))
        independent = decision_view(self.root, "approve", data)
        self.assertEqual(before["receipt"], independent["receipt"])
        self.assertNotEqual(before["basis"]["source_files"], independent["basis"]["source_files"])
        path.write_bytes(path.read_bytes().replace(b"Obligaci\xc3\xb3n literal independiente 0", b"Changed applicable obligation"))
        self.assertNotEqual(independent["receipt"], decision_view(self.root, "approve", data)["receipt"])
