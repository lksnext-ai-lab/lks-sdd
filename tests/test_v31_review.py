"""Real repository journeys, not simulations of the decision predicates."""
import copy
import json
from pathlib import Path
import shutil
import tempfile

from test_v3_workflow import ProjectFixture, commit_packet, git
from v3_contract import ContractError, element, load
from v3_authoring import author, approve, approve_and_authorize
from v3_workflow import transition
from v3_verification import evidence, integrate, accept
from v31_review import configure, execute, task_reviewed
from v31_guidance import interventions
from v31_corrections import reject, define, resolve, delivery


class IntegralTests(ProjectFixture):
    def setUp(self):
        super().setUp()
        self.configuration = {"proposal_review_required": True, "task_review_required": True,
                              "defaults": {"responsible": self.actor, "integration_validator": self.actor,
                                           "functional_validator": self.actor, "reviewers": [
                                               {"member": self.actor, "required": True, "domains": ["Backend"]},
                                               {"member": self.actor, "required": True, "domains": ["BBDD"]}]}}
        commit_packet(self.root, configure(self.root, self.actor, self.configuration, "Activo el recorrido integral explícitamente"))
        request = element("request", "Saludo integral", "Conservar la interfaz y concretar un saludo verificable.")
        proposal = element("proposal", "Solución conjunta", "Se modifica la función de saludo, conservando la interfaz y comprobando el valor devuelto.",
                           request=request["meta"]["uid"], part="joint", objective="Saludo", included=["app.py"], excluded=[],
                           behavior="Devuelve Hola", solution="Función Python", impact="Módulo acotado", acceptance=["Hola"])
        request["meta"]["relations"]["proposal"] = [proposal["meta"]["uid"]]
        commit_packet(self.root, author(self.root, self.actor, [request, proposal]))
        self.req, self.prop = request["meta"]["uid"], proposal["meta"]["uid"]

    def close_proposal(self):
        commit_packet(self.root, execute("close-proposal", self.root, {
            "actor": self.actor, "request": self.req, "statement": "Reviso y cierro esta propuesta integral", "review": True}))

    def create_plan(self, *, review_tasks=True):
        task = element("task", "Saludo", "Implementar exactamente el saludo y probar su resultado.", request=self.req,
                       owner=self.actor, scope=["app.py"], acceptance=["Hola"], tests=["greeting"])
        plan = element("plan", "Plan concreto", "Implementar, probar y verificar el saludo sin modificar la interfaz.", request=self.req)
        plan["meta"]["relations"]["tasks"] = [task["meta"]["uid"]]
        commit_packet(self.root, author(self.root, self.actor, [task, plan]))
        self.task, self.plan_id = task["meta"]["uid"], plan["meta"]["uid"]
        commit_packet(self.root, approve_and_authorize(self.root, self.actor, self.plan_id,
            "Apruebo y autorizo el plan; reviso el encargo detallado de mi tarea", review_tasks=[self.task] if review_tasks else []))

    def proof(self):
        path = self.root/"docs/lks-sdd/evidence/test-input.txt"
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text("greeting: passed, expected Hola")
        commit_packet(self.root, evidence(self.root, self.actor, self.task, ["greeting"], "passed", "automated",
                                         path.relative_to(self.root).as_posix(), "Prueba del resultado exacto"))

    def test_individual_three_decisions_and_no_role_duplicates(self):
        first = interventions(load(self.root), self.req)
        self.assertEqual(1, len(first["interventions"]))
        self.assertEqual(["review-proposal", "close-proposal"], first["interventions"][0]["actions"])
        self.close_proposal(); self.create_plan()
        model = load(self.root).require_valid()
        self.assertTrue(task_reviewed(model, model.get(self.task), self.actor))
        self.assertFalse(interventions(model, self.req)["interventions"])
        with tempfile.TemporaryDirectory() as temp:
            trusted = Path(temp)/"trusted"; shutil.copytree(self.root, trusted)
            git(trusted, "symbolic-ref", "HEAD", "refs/heads/main")
            self.advance("start"); (self.root/"app.py").write_text("def greeting(): return 'Hola'\n")
            self.advance("implement"); self.proof(); self.advance("verify"); self.advance("close")
            last = interventions(load(self.root), self.req)["interventions"]
            self.assertEqual([["integrate", "accept"]], [r["actions"] for r in last])
            commit_packet(self.root, integrate(self.root, self.actor, self.req, trusted,
                "Compruebo la integración y acepto el resultado funcional concreto", accept_result=True))
            commit_packet(self.root, delivery(self.root, self.actor, self.req, "Preparar la entrega ya aceptada"))
            result = interventions(load(self.root), self.req)
            self.assertTrue(all(h["state"] == "completed" for h in result["milestones"]))
            self.assertFalse(result["interventions"])
            self.assertEqual("3.1", json.loads((self.root/".lks-sdd/project.json").read_text())["schema_version"])

    def test_task_owner_cannot_skip_review_and_stale_definition_requires_review(self):
        self.close_proposal(); self.create_plan(review_tasks=False)
        with self.assertRaisesRegex(ContractError, "task-reviewed"): self.advance("start")
        commit_packet(self.root, transition(self.root, self.actor, self.task, "start", "Reviso el encargo y empiezo", review=True))
        task = copy.deepcopy(load(self.root).get(self.task).item()); task["meta"]["revision"] += 1
        task["body"] += " Incluir también el caso vacío."
        commit_packet(self.root, author(self.root, self.actor, [task]))
        self.assertFalse(task_reviewed(load(self.root), load(self.root).get(self.task), self.actor))
        with self.assertRaises(ContractError): self.advance("implement")

    def test_integral_close_cannot_bypass_objection_or_generic_approval(self):
        with self.assertRaises(ContractError): approve(self.root, self.actor, [self.prop], "proposal", "Intento aprobar sin revisión")
        packet = execute("review-comment", self.root, {"actor": self.actor, "request": self.req, "target": self.prop,
                         "statement": "Falta aclarar la interfaz", "blocking": True})
        commit_packet(self.root, packet)
        comment = next(e for e in load(self.root).by_kind("problem") if e.data.get("purpose") == "review-comment")
        with self.assertRaises(ContractError): self.close_proposal()
        commit_packet(self.root, execute("resolve-comment", self.root, {"actor": self.actor, "request": self.req,
            "comment": comment.uid, "statement": "Se conserva la interfaz descrita y se confirma su alcance", "treatment": "dismissed"}))
        self.close_proposal()
        changed = copy.deepcopy(load(self.root).get(self.prop).item()); changed["meta"]["revision"] += 1
        changed["body"] += " La interfaz ahora acepta un parámetro adicional."
        commit_packet(self.root, author(self.root, self.actor, [changed]))
        self.assertTrue(interventions(load(self.root), self.req)["interventions"])

    def test_rejection_records_correction_and_blocks_old_acceptance(self):
        self.close_proposal(); self.create_plan()
        trusted_temp = tempfile.TemporaryDirectory(); self.addCleanup(trusted_temp.cleanup)
        trusted = Path(trusted_temp.name)/"trusted"; shutil.copytree(self.root, trusted)
        git(trusted, "symbolic-ref", "HEAD", "refs/heads/main")
        self.advance("start"); (self.root/"app.py").write_text("def greeting(): return 'Hola'\n")
        self.advance("implement"); self.proof(); self.advance("verify"); self.advance("close")
        commit_packet(self.root, integrate(self.root, self.actor, self.req, trusted, "Integro y acepto el candidato anterior", accept_result=True))
        from v3_workflow import request_facts
        self.assertTrue(request_facts(load(self.root), load(self.root).get(self.req))["accepted"])
        path = self.root/"docs/lks-sdd/evidence/failure.txt"; path.write_text("Revisión manual: escenario pendiente")
        packet = reject(self.root, self.actor, self.req, "Rechazo el candidato por incumplimiento", phase="acceptance",
                        tasks=[self.task], expected="Hola", observed="Escenario pendiente", artifact=path.relative_to(self.root).as_posix())
        problem, correction = packet["summary"]["problem"], packet["summary"]["correction"]
        commit_packet(self.root, packet)
        with self.assertRaises(ContractError): accept(self.root, self.actor, self.req, "No omitir correcciones")
        with self.assertRaises(ContractError): resolve(self.root, self.actor, problem, "Todavía no se ha definido la corrección")
        commit_packet(self.root, define(self.root, self.actor, correction, "defect", "Corregir el incumplimiento ya definido", "Prueba de Hola"))
        with self.assertRaisesRegex(ContractError, "posteriores"):
            resolve(self.root, self.actor, problem, "No reutilizar la evidencia anterior al fallo")
        self.advance("reopen"); self.proof()
        commit_packet(self.root, resolve(self.root, self.actor, problem, "Compruebo la corrección mediante la evidencia del escenario"))
        self.assertFalse(request_facts(load(self.root), load(self.root).get(self.req))["accepted"])
        with self.assertRaises(ContractError): delivery(self.root, self.actor, self.req, "Sigue faltando integrar y aceptar")

    def test_two_people_distinct_authority_and_partial_handoff(self):
        from v3_authoring import governance
        from v3_team import handoff
        from v31_review import review_status
        member = element("member", "Operador de prueba", "Otra persona con igual nombre visible.", roles=["developer", "reviewer"], active=True)
        other = member["meta"]["uid"]
        commit_packet(self.root, governance(self.root, self.actor, [member], "Incorporo al especialista", "Participará en revisión y ejecución"))
        cfg = copy.deepcopy(self.configuration)
        cfg["defaults"]["reviewers"] += [{"member": other, "required": True, "domains": ["Frontend", "Backend"]}]
        commit_packet(self.root, configure(self.root, self.actor, cfg, "Ambas personas revisan la solución integral", requests=[self.req]))
        rows = interventions(load(self.root), self.req)["interventions"]
        self.assertEqual(2, len(rows)); self.assertEqual({self.actor, other}, {r["actor"] for r in rows})
        with self.assertRaises(ContractError): self.close_proposal()
        commit_packet(self.root, execute("review-proposal", self.root, {"actor": other, "request": self.req, "statement": "Reviso todo el paquete desde ambas especialidades"}))
        self.close_proposal(); self.create_plan(); self.advance("start"); self.advance("pause")
        with self.assertRaises(ContractError): execute("close-proposal", self.root, {"actor": other, "request": self.req, "statement": "No soy el responsable"})
        commit_packet(self.root, handoff(self.root, self.actor, self.task, other, ["app.py"], "Ayuda acotada"))
        offer = next(e.uid for e in load(self.root).by_kind("handoff"))
        commit_packet(self.root, transition(self.root, other, self.task, "resume", "Acepto la porción, reviso el encargo y continúo", offer=offer, review=True))
        self.assertTrue(task_reviewed(load(self.root), load(self.root).get(self.task), other))

    def test_event_disguise_and_stale_preview_are_rejected(self):
        from v31_review import proposal_basis
        model = load(self.root)
        fake = element("change", "Falsa revisión", "Una entidad normativa no acredita una decisión de revisión.",
                       purpose="proposal-review", request=self.req, actor={"member": self.actor}, recorded_at="2026-01-01T00:00:00Z",
                       basis=proposal_basis(model, model.get(self.req)), outcome="approved")
        with self.assertRaises(ContractError): author(self.root, self.actor, [fake])
        data = {"actor": self.actor, "request": self.req, "statement": "Conforme con este paquete integral"}
        first = execute("review-proposal", self.root, data)
        second = execute("review-proposal", self.root, data)
        commit_packet(self.root, first)
        with self.assertRaises(ContractError): commit_packet(self.root, second)

    def test_independent_review_is_not_removed_for_same_person(self):
        from v3_authoring import governance
        member = element("member", "Revisora", "Persona independiente habilitada.", roles=["reviewer"], active=True)
        other = member["meta"]["uid"]
        model = load(self.root)
        policy = copy.deepcopy(model.get(model.project.data["policy"]).item()); policy["meta"]["revision"] += 1
        policy["meta"]["data"]["independent_review"] = True
        commit_packet(self.root, governance(self.root, self.actor, [member, policy], "Exijo revisión independiente", "Regla de este proyecto", requests=[self.req]))
        self.close_proposal(); self.create_plan(); self.advance("start")
        (self.root/"app.py").write_text("def greeting(): return 'Hola'\n")
        self.advance("implement")
        path = self.root/"docs/lks-sdd/evidence/independent.txt"; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("greeting: passed")
        commit_packet(self.root, evidence(self.root, other, self.task, ["greeting"], "passed", "human-observation",
                                         path.relative_to(self.root).as_posix(), "Compruebo el resultado como revisora independiente"))
        with self.assertRaisesRegex(ContractError, "independiente"): self.advance("verify")
        commit_packet(self.root, transition(self.root, other, self.task, "verify", "Revisión independiente acreditada"))

    def test_new_format_adoption_is_recoverable_and_does_not_approve_history(self):
        from v3_storage import recover
        from v31_review import closure_valid
        self.assertFalse(closure_valid(load(self.root), load(self.root).get(self.req)))
        cfg = copy.deepcopy(self.configuration); cfg["task_review_required"] = False
        packet = configure(self.root, self.actor, cfg, "Cambio de política solo para nuevas peticiones")
        result = commit_packet(self.root, packet)
        from v3_policy import policy_for
        self.assertTrue(policy_for(load(self.root), load(self.root).get(self.req)).data["collaboration"]["task_review_required"])
        recover(self.root, packet["preview"]["preview_hash"], rollback=True, receipt=result["receipt"])
        self.assertTrue(policy_for(load(self.root)).data["collaboration"]["task_review_required"])


    def test_guidance_matches_queries_and_shows_review_reservations(self):
        from unittest.mock import patch
        from v3_cli import execute as cli
        from v3_guidance import status
        from v31_review import closure_valid
        from datetime import datetime, timedelta, timezone
        initial = load(self.root).snapshot()
        direct = interventions(load(self.root), self.req, actor=self.actor)
        self.assertEqual(direct, cli("interventions", self.root, {"request": self.req, "actor": self.actor}))
        self.assertEqual(direct, cli("readiness", self.root, {"request": self.req, "actor": self.actor, "action": "close-proposal"})["journey"])
        self.assertEqual(interventions(load(self.root), self.req), status(self.root, request_id=self.req)["requests"][0]["journey"])
        self.assertEqual(initial, load(self.root).snapshot())
        expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        commit_packet(self.root, execute("review-exception", self.root, {
            "actor": self.actor, "request": self.req, "statement": "Dispensa temporal documentada de revisión", "rule": "integral-review",
            "action": "close-proposal", "effect": "Cerrar con reserva sin atribuir conformidad ausente", "expires_at": expiry}))
        commit_packet(self.root, execute("close-proposal", self.root, {
            "actor": self.actor, "request": self.req, "statement": "Cierro bajo la dispensa vigente"}))
        journey = interventions(load(self.root), self.req)
        self.assertEqual("completed-with-reservations", journey["milestones"][1]["state"])
        self.assertEqual([self.actor], journey["milestones"][1]["missing_conformities"])
        with patch("v31_review.active_period", return_value=False):
            self.assertFalse(closure_valid(load(self.root), load(self.root).get(self.req)))
        self.assertEqual("already-recorded", execute("close-proposal", self.root, {
            "actor": self.actor, "request": self.req, "statement": "Reintento el mismo cierre"})["status"])

    def test_disabled_task_review_and_read_only_pagination(self):
        from v3_guidance import status
        cfg = copy.deepcopy(self.configuration); cfg["task_review_required"] = False
        commit_packet(self.root, configure(self.root, self.actor, cfg, "No exigir revisión separada del encargo", requests=[self.req]))
        self.close_proposal(); self.create_plan(review_tasks=False)
        self.assertEqual("not-required", interventions(load(self.root), self.req)["milestones"][3]["state"])
        self.advance("start")
        snapshot = load(self.root).snapshot()
        page = status(self.root, request_id=self.req, task_offset=1, task_limit=1)
        self.assertEqual([], page["requests"][0]["tasks"])
        self.assertEqual(1, page["requests"][0]["task_total"])
        self.assertEqual(snapshot, load(self.root).snapshot())


    def test_grouped_result_respects_acceptance_before_integration(self):
        from v3_authoring import governance
        model = load(self.root)
        policy = copy.deepcopy(model.get(model.project.data["policy"]).item()); policy["meta"]["revision"] += 1
        data = policy["meta"]["data"]; data["acceptance_order"] = "before-integration"
        for step in data["steps"]:
            if step["id"] == "acceptance": step.update(requires=["verification"], conditions=["verified"])
            if step["id"] == "integration": step.update(requires=["acceptance"], conditions=["accepted"])
        commit_packet(self.root, governance(self.root, self.actor, [policy], "Aceptación antes de integración", "Recorrido configurado", requests=[self.req]))
        self.test_individual_three_decisions_and_no_role_duplicates()
        model = load(self.root)
        final = [e for e in model.elements.values() if e.data.get("purpose") in {"integration", "acceptance"}]
        self.assertEqual(2, len(final))
        self.assertEqual(1, len({e.data["intervention"] for e in final}))
