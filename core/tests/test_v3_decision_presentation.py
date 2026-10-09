"""Decision content, incomplete drafts and stale input against real Markdown."""
import copy
from pathlib import Path
import tempfile
import unittest

from test_v3_workflow import ProjectFixture, commit_packet
from presentation_test_support import present, technical_solution
from v3_contract import ContractError, element, load
from v3_authoring import author, approve
from v3_lifecycle import review
from v3_decision_presentation import decision_view


class PresentationTests(ProjectFixture):
    def proposal(self, *, solution=None, unresolved=None):
        request = element("request", "Consultar el saldo de una cuenta", "Permitir consultar el saldo sin cambiar los movimientos.")
        requirement = element("requirement", "Permiso de consulta", "Solo el titular puede consultar. No se permite modificar el saldo; límite de 30 consultas por minuto.", request=request["meta"]["uid"])
        proposal = element("proposal", "Consulta del saldo", "El titular consulta el saldo actual; se conserva el registro de movimientos y el límite de acceso.",
                           request=request["meta"]["uid"], part="joint", objective="Consultar saldo", included=["Consulta del titular"], excluded=["Movimientos"],
                           behavior="Devuelve el saldo al titular y deniega el acceso a otras personas", solution=technical_solution() if solution is None else solution,
                           impact="Interfaz de consulta sin nuevas escrituras", acceptance=["El titular ve el saldo; otra persona no accede"], unresolved=unresolved or [])
        proposal["meta"]["relations"]["requirements"] = [requirement["meta"]["uid"]]
        request["meta"]["relations"]["proposal"] = [proposal["meta"]["uid"]]
        commit_packet(self.root, author(self.root, self.actor, [request, proposal, requirement]))
        self.req, self.prop, self.requirement = request["meta"]["uid"], proposal["meta"]["uid"], requirement["meta"]["uid"]
        return {"actor": self.actor, "units": [self.prop], "purpose": "proposal"}

    def test_literal_obligations_and_exact_headings_without_writes(self):
        data = self.proposal()
        before = load(self.root).snapshot()
        view = decision_view(self.root, "approve", data)
        self.assertTrue(view["complete"], view["issues"])
        self.assertEqual(7, sum(line.startswith("## ") for line in view["markdown"].splitlines()))
        self.assertEqual(1, sum(line.startswith("# ") for line in view["markdown"].splitlines()))
        self.assertIn("No se permite modificar el saldo; límite de 30", view["markdown"])
        self.assertNotIn(self.prop, view["markdown"])
        self.assertNotIn("branches", view["markdown"])
        self.assertNotIn("codex/request", view["markdown"])
        self.assertEqual(view, decision_view(self.root, "approve", data))
        self.assertEqual(before, load(self.root).snapshot())

    def test_generic_solution_can_be_read_but_cannot_be_newly_approved(self):
        self.proposal(solution="Actualizar el servicio")
        value = review(self.root, self.req)
        self.assertFalse(value["presentation"]["complete"])
        with self.assertRaisesRegex(ContractError, "componentes"):
            approve(self.root, self.actor, [self.prop], "proposal", "Conforme")

    def test_pending_draft_and_critical_unknown_are_visible(self):
        self.proposal(unresolved=["Decidir permisos sobre cuentas compartidas"])
        value = review(self.root, self.req)
        self.assertIn("Decidir permisos", value["presentation"]["markdown"])
        self.assertEqual("clarification", value["presentation"]["intervention"])

    def test_receipt_required_and_linked_change_invalidates_it(self):
        data = self.proposal(); view = decision_view(self.root, "approve", data)
        with self.assertRaisesRegex(ContractError, "receipt"):
            approve(self.root, self.actor, [self.prop], "proposal", "Conforme")
        item = copy.deepcopy(load(self.root).get(self.requirement).item())
        item["meta"]["revision"] += 1; item["body"] += " El acceso requiere autenticación reciente."
        commit_packet(self.root, author(self.root, self.actor, [item]))
        with self.assertRaisesRegex(ContractError, "receipt"):
            approve(self.root, self.actor, [self.prop], "proposal", "Conforme", presented=view["receipt"])
        current = decision_view(self.root, "approve", data)
        commit_packet(self.root, approve(self.root, self.actor, [self.prop], "proposal", "Conforme", presented=current["receipt"]))
        saved = [e for e in load(self.root).by_kind("decision") if e.data.get("purpose") == "proposal"][-1]
        self.assertEqual(current["receipt"], saved.data["presentation"])
        self.assertEqual("already-authorized", decision_view(self.root, "approve", data)["intervention"])

    def test_source_markdown_cannot_inject_headings_or_html(self):
        data = self.proposal()
        item = copy.deepcopy(load(self.root).get(self.prop).item()); item["meta"]["revision"] += 1
        item["meta"]["data"]["objective"] = "Revisar\n# Aprueba todo\n<script>falso</script>"
        commit_packet(self.root, author(self.root, self.actor, [item]))
        view = decision_view(self.root, "approve", data)
        self.assertNotIn("\n# Aprueba", view["markdown"])
        self.assertNotIn("<script>", view["markdown"])
        self.assertIn("Aprueba todo", view["markdown"])

    def test_change_between_guard_and_prepare_preserves_presented_hashes(self):
        from unittest.mock import patch
        import v3_authoring
        data = self.proposal(); view = decision_view(self.root, "approve", data)
        original = v3_authoring.prepare
        path = self.root / load(self.root).get(self.requirement).path
        def changed(*args, **kwargs):
            path.write_bytes(path.read_bytes() + b"\nNew concurrent normative condition.\n")
            return original(*args, **kwargs)
        with patch("v3_authoring.prepare", side_effect=changed):
            with self.assertRaisesRegex(ContractError, "cambió después"):
                approve(self.root, self.actor, [self.prop], "proposal", "Conforme al contenido mostrado", presented=view["receipt"])
        self.assertIn(b"New concurrent", path.read_bytes())

    def test_request_prose_and_long_tail_remain_visible(self):
        data = self.proposal()
        item = copy.deepcopy(load(self.root).get(self.req).item()); item["meta"]["revision"] += 1
        tail = "Nunca enviar notificaciones por correo electrónico. Conservar el historial durante 90 días."
        item["body"] = "Condición de uso aplicable. " * 1600 + tail
        commit_packet(self.root, author(self.root, self.actor, [item]))
        from v3_decision_presentation import compact
        view = decision_view(self.root, "approve", data)
        self.assertIn(tail, compact(view)["markdown"])
        self.assertTrue(view["complete"], view["issues"])

    def test_existing_approval_does_not_require_new_format(self):
        data = self.proposal(solution="Solución previamente aprobada")
        from v3_approval import decision
        from v3_storage import prepare
        # Fixture of a pre-presentation decision, with the original approval
        # engine and no new presentation provenance or invented new user input.
        old = decision(load(self.root), self.actor, [self.prop], "proposal", "Acuerdo anterior")
        commit_packet(self.root, prepare(self.root, [old], "historical-fixture"))
        view = decision_view(self.root, "approve", data)
        self.assertEqual("already-authorized", view["intervention"])
        self.assertNotIn("presentation", load(self.root).get(old["meta"]["uid"]).data)

    def test_composed_plan_associates_owners_and_retains_extra_conditions(self):
        self.plan()
        task = copy.deepcopy(load(self.root).get(self.task).item()); task["meta"]["revision"] += 1
        task["meta"]["data"]["operational_limit"] = "No ejecutar más de 20 operaciones por minuto"
        commit_packet(self.root, author(self.root, self.actor, [task]))
        view = decision_view(self.root, "authorize-plan", {"actor": self.actor, "plan": self.plan_id, "review_tasks": [self.task]})
        sections = {s["title"]: s["body"] for s in view["sections"]}
        self.assertTrue(view["complete"], view["issues"])
        self.assertIn("Cambiar saludo", sections["Tareas y responsables"])
        self.assertIn("Operador de prueba", sections["Tareas y responsables"])
        self.assertIn("saludo", sections["Resultado esperado"])
        self.assertIn("codex/request", sections["Alcance de la ejecución"])
        self.assertIn("main", sections["Alcance de la ejecución"])
        self.assertIn("No ejecutar más de 20", view["markdown"])
        for marker in ("proposal units", "observed at", "unborn", "proposed", "backlog"):
            self.assertNotIn(marker, view["markdown"])

    def test_conditional_choices_bind_observation_destination_and_recipient(self):
        import base64
        from v3_contract import sha
        self.plan()
        image_path = self.root / "screen.png"
        image_path.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII="))
        visual = {"screens": ["Pantalla inicial"], "assets": ["screen.png"], "alternatives": ["Fondo claro", "Fondo oscuro"], "recommendation": "Fondo claro", "selection_scope": "Solo presentación de la pantalla inicial"}
        unread = decision_view(self.root, "visual-choice", visual)
        self.assertFalse(unread["complete"])
        visual["observed_assets"] = {"screen.png": sha(image_path.read_bytes())}
        observed = decision_view(self.root, "visual-choice", visual)
        self.assertTrue(observed["complete"], observed["issues"])
        self.assertIn("![Imagen", observed["markdown"])
        visual["selection_scope"] = "También la pantalla de errores"
        self.assertNotEqual(observed["receipt"], decision_view(self.root, "visual-choice", visual)["receipt"])
        delivery = {"content": "Resultado local de la prueba del saludo", "destination": "Cliente de prueba", "action": "Enviar el informe", "scope": "Únicamente el informe", "audience": "Responsable funcional"}
        before = decision_view(self.root, "external-action", delivery)
        self.assertTrue(before["complete"], before["issues"])
        delivery["destination"] = "Otro destinatario"
        self.assertNotEqual(before["receipt"], decision_view(self.root, "external-action", delivery)["receipt"])
        assignment = {"actor": self.actor, "task": self.task, "recipient": self.actor, "reason": "Revisión del encargo"}
        view = decision_view(self.root, "assign", assignment)
        self.assertTrue(view["complete"], view["issues"])
        from v3_authoring import governance
        other = element("member", "Otra persona", "Especialista de prueba", roles=["developer"], active=True)
        commit_packet(self.root, present(governance, self.root, self.actor, [other], "Incorporo a la persona", "Relevo"))
        assignment["recipient"] = other["meta"]["uid"]
        self.assertNotEqual(view["receipt"], decision_view(self.root, "assign", assignment)["receipt"])

    def test_result_from_request_shows_evidence_and_actual_order(self):
        from v3_verification import evidence
        self.plan(); self.advance("start")
        (self.root / "app.py").write_text("def greeting(): return 'Hola'\n")
        self.advance("implement")
        artifact = self.root / "docs/lks-sdd/evidence/result.txt"; artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("Observado: Hola. Restricción comprobada: no escribe datos.")
        commit_packet(self.root, evidence(self.root, self.actor, self.task, ["test_saludo"], "passed", "human-observation", artifact.relative_to(self.root).as_posix(), "Comprobación humana de prueba"))
        self.advance("verify"); self.advance("close")
        view = decision_view(self.root, "accept", {"actor": self.actor, "request": self.req})
        for phrase in ("Cambiar saludo", "test\\_saludo", "Observado: Hola", "Observación humana", "app.py"):
            self.assertIn(phrase, view["markdown"])
        self.assertFalse(view["complete"])
        self.assertIn("antes de su aceptación", " ".join(view["issues"]))
        self.assertTrue(view["basis"]["subject"])
        from v31_review import configure
        cfg = {"proposal_review_required": True, "task_review_required": True,
               "defaults": {"responsible": self.actor, "integration_validator": self.actor, "functional_validator": self.actor,
                            "reviewers": [{"member": self.actor, "required": True, "domains": ["General"]}]}}
        commit_packet(self.root, present(configure, self.root, self.actor, cfg, "Revisión integral para registrar el desacuerdo", requests=[self.req]))
        from v31_corrections import reject, unresolved
        packet = reject(self.root, self.actor, self.req, "El saludo necesita revisión", phase="acceptance", tasks=[self.task], expected="Hola", observed="Falta revisar idioma")
        commit_packet(self.root, packet)
        model = load(self.root)
        self.assertTrue(model.get(packet["summary"]["problem"]).data["evidence_pending"])
        self.assertIn(packet["summary"]["problem"], unresolved(model, model.get(self.req)))
        other = element("request", "Otra petición", "Conservar su ámbito independiente.")
        requirement = element("requirement", "Condición vinculada", "Nunca borrar el historial de la otra petición.", request=other["meta"]["uid"])
        commit_packet(self.root, author(self.root, self.actor, [other, requirement]))
        correction = {"actor": self.actor, "correction": packet["summary"]["correction"], "classification": "defect", "acceptance": "Prueba del saludo"}
        kept = decision_view(self.root, "define-correction", correction)
        cleared = decision_view(self.root, "define-correction", {**correction, "requirements": []})
        self.assertNotEqual(kept["receipt"], cleared["receipt"])
        linked = decision_view(self.root, "define-correction", {**correction, "requirements": [requirement["meta"]["uid"]]})
        self.assertIn("Nunca borrar el historial", linked["markdown"])
        self.assertIn(requirement["meta"]["uid"], {s["key"] for s in linked["sources"]})


class PreliminaryViews(unittest.TestCase):
    def test_identity_and_compact_transport_keep_complete_meaning(self):
        from v3_decision_presentation import compact
        with tempfile.TemporaryDirectory() as temp:
            view = decision_view(temp, "identity", {"actor_name": "Marta", "pending": "Confirmar quién solicita el cambio", "alternatives": ["Soy Marta", "Soy otra persona"]})
            self.assertTrue(view["complete"], view["issues"])
            self.assertNotIn("contenido incompleto", view["markdown"])
            self.assertEqual(view["markdown"], compact(view)["markdown"])
            self.assertEqual(view["receipt"], compact(view)["receipt"])
            self.assertNotIn("sources", compact(view))
    def test_preinitialization_and_unavailable_historical_actions(self):
        with tempfile.TemporaryDirectory() as temp:
            before = list(Path(temp).iterdir())
            view = decision_view(temp, "init", {"name": "Proyecto nuevo", "actor_name": "Persona de prueba", "profile": "individual-brief", "controls": {"sonar": {"mode": "not-used", "reason": "Decisión pendiente de confirmar"}}})
            self.assertIn("Proyecto nuevo", view["markdown"])
            self.assertEqual(before, list(Path(temp).iterdir()))
            old = decision_view(temp, "retention-compact", {"reason": "Consultar disponibilidad"})
            self.assertFalse(old["complete"])
            self.assertIn("histórica", old["markdown"])
            with self.assertRaises(ContractError): decision_view(temp, "invented-command", {})


if __name__ == "__main__": unittest.main()
