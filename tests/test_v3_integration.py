import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from test_v3_workflow import ProjectFixture, commit_packet, git
from v3_contract import element, load, ContractError
from v3_authoring import author, approve, approve_and_authorize
from v3_context import context
from v3_guidance import status
from v3_verification import evidence, integrate, accept


class IntegrationTests(ProjectFixture):
    def test_functional_approval_survives_independent_technical_revision(self):
        from v3_approval import approved, proposal_ready
        request = element("request", "Partes separadas", "Propuesta funcional y técnica con revisiones independientes.")
        common = {"request": request["meta"]["uid"], "objective": "Saludo", "included": ["app.py"], "excluded": [], "impact": "Módulo delimitado", "acceptance": ["Saludo acordado"]}
        functional = element("proposal", "Comportamiento", "La aplicación devuelve el saludo documentado conservando el resto del comportamiento.", part="functional", behavior="Devuelve Hola", **common)
        technical = element("proposal", "Solución", "Se modifica la función existente conservando su interfaz pública y las dependencias.", part="technical", solution="Función existente", **common)
        request["meta"]["relations"] = {"proposal": [functional["meta"]["uid"], technical["meta"]["uid"]]}
        commit_packet(self.root, author(self.root, self.actor, [request, functional, technical]))
        commit_packet(self.root, approve(self.root, self.actor, [functional["meta"]["uid"]], "proposal", "Acepto el comportamiento funcional"))
        with self.assertRaises(ContractError): proposal_ready(load(self.root), load(self.root).get(request["meta"]["uid"]), [functional["meta"]["uid"]])
        commit_packet(self.root, approve(self.root, self.actor, [technical["meta"]["uid"]], "proposal", "Acepto la solución técnica"))
        changed = copy.deepcopy(load(self.root).get(technical["meta"]["uid"]).item()); changed["meta"]["revision"] += 1
        changed["body"] += " Se extrae una función auxiliar interna sin alterar la interfaz."
        commit_packet(self.root, author(self.root, self.actor, [changed]))
        self.assertTrue(approved(load(self.root), [functional["meta"]["uid"]])["valid"])
        self.assertFalse(approved(load(self.root), [technical["meta"]["uid"]])["valid"])
        commit_packet(self.root, approve(self.root, self.actor, [technical["meta"]["uid"]], "proposal", "Acepto únicamente la revisión técnica"))
        self.assertTrue(approved(load(self.root), request["meta"]["relations"]["proposal"])["valid"])

    def test_available_dependency_can_continue_while_verified_dependency_waits(self):
        from v3_authoring import governance
        from v3_workflow import dependencies
        from v3_approval import task_authority
        model = load(self.root); policy = copy.deepcopy(model.get(model.project.data["policy"]).item()); policy["meta"]["revision"] += 1
        policy["meta"]["data"]["controls"]["sonar"] = {"mode": "required", "reason": "Resultado terminal pendiente", "executor": "existing-report", "scope": ["app.py"], "timeout_seconds": 30, "max_retries": 1}
        policy["meta"]["data"]["controls"]["sonar"]["availability"] = {"state": "available", "source": "Exportador existente de fixture", "phase": "implementation"}
        commit_packet(self.root, governance(self.root, self.actor, [policy], "Acepto el control durante implementación", "Verificar la independencia de tareas"))
        self.plan()
        model = load(self.root)
        consumer = element("task", "Consumir resultado", "Comprobar el artefacto disponible sin modificar su contrato.", request=self.req,
                           owner=self.actor, scope=["app.py"], acceptance=["artefacto disponible"], tests=["consume"], integration=True,
                           dependencies=[{"uid": self.task, "type": "available", "artifact": "app.py"}])
        strict = copy.deepcopy(consumer); strict["meta"] = element("task", "Consumir verificado", "Esperar resultado verificado.", **consumer["meta"]["data"])["meta"]
        strict["meta"]["data"]["dependencies"] = [{"uid": self.task, "type": "verified", "artifact": "app.py"}]
        plan = copy.deepcopy(model.get(self.plan_id).item()); plan["meta"]["revision"] += 1
        plan["meta"]["relations"]["tasks"].extend([consumer["meta"]["uid"], strict["meta"]["uid"]])
        commit_packet(self.root, author(self.root, self.actor, [consumer, strict, plan]))
        model = load(self.root)
        self.assertTrue(task_authority(model, model.get(self.task), model.get(self.plan_id), "execution")["valid"])
        commit_packet(self.root, approve_and_authorize(self.root, self.actor, self.plan_id, "Autorizo las nuevas tareas del mismo contrato"))
        self.advance("start"); (self.root/"app.py").write_text("answer = 42\n"); self.advance("implement")
        model = load(self.root)
        self.assertFalse(dependencies(model, model.get(consumer["meta"]["uid"])))
        self.assertTrue(dependencies(model, model.get(strict["meta"]["uid"])))
        commit_packet(self.root, __import__("v3_workflow").transition(self.root, self.actor, consumer["meta"]["uid"], "start", "El resultado requerido ya está disponible"))
        with self.assertRaises(ContractError):
            __import__("v3_workflow").transition(self.root, self.actor, strict["meta"]["uid"], "start", "Aún no verificado")

    def test_partial_proposal_and_independent_plan_extension(self):
        self.plan()
        before = context(self.root, [self.task])
        model = load(self.root)
        future = element("proposal", "Porción futura", "Se estudiará otra interfaz, todavía con decisiones pendientes.",
                         request=self.req, part="joint", unresolved=["Diseño futuro"])
        request = copy.deepcopy(model.get(self.req).item()); request["meta"]["revision"] += 1
        request["meta"]["relations"]["proposal"].append(future["meta"]["uid"])
        commit_packet(self.root, author(self.root, self.actor, [future, request]))
        selected = context(self.root, [self.task], comparison=True)
        self.assertNotIn(future["meta"]["uid"], {s["key"] for s in selected["sources"]})
        self.advance("start")
        report = status(self.root)
        self.assertEqual("in-progress", report["requests"][0]["tasks"][0]["state"])
        self.assertFalse(next(s for s in report["requests"][0]["steps"] if s["id"] == "acceptance")["state"] == "completed")

    def test_independent_clones_keep_identity_with_same_alias(self):
        git(self.root, "config", "user.email", "fixture@example.invalid")
        git(self.root, "config", "user.name", "Fixture")
        git(self.root, "add", "."); git(self.root, "commit", "-m", "Shared fixture")
        with tempfile.TemporaryDirectory(prefix="v3-clone-") as temp:
            other = Path(temp)/"other"
            subprocess.run(["git", "clone", str(self.root), str(other)], check=True, capture_output=True)
            a = element("requirement", "Primero", "Obligación de la primera rama."); a["meta"]["id"] = "REQ-SAME"
            b = element("requirement", "Segundo", "Obligación independiente de la segunda rama."); b["meta"]["id"] = "REQ-SAME"
            commit_packet(self.root, author(self.root, self.actor, [a]))
            commit_packet(other, author(other, self.actor, [b]))
            from v3_contract import location
            target = self.root/location(b); target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((other/location(b)).read_bytes())
            model = load(self.root).require_valid()
            self.assertNotEqual(a["meta"]["uid"], b["meta"]["uid"])
            self.assertEqual(b["body"], model.get(b["meta"]["uid"]).body)
            with self.assertRaises(ContractError): model.get("REQ-SAME")

    def test_joint_result_integration_and_acceptance_are_distinct(self):
        self.plan()
        with tempfile.TemporaryDirectory(prefix="v3-trusted-") as temp:
            trusted = Path(temp)/"trusted"; shutil.copytree(self.root, trusted)
            git(trusted, "symbolic-ref", "HEAD", "refs/heads/main")
            self.advance("start"); (self.root/"app.py").write_text("def saludo(): return 'Hola'\n")
            self.advance("implement")
            artifact = self.root/"docs/lks-sdd/evidence/result.txt"; artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("test_saludo passed")
            commit_packet(self.root, evidence(self.root, self.actor, self.task, ["test_saludo"], "passed", "automated", artifact.relative_to(self.root).as_posix(), "Ejecución local del escenario"))
            self.advance("verify"); self.advance("close")
            self.assertFalse([r for r in load(self.root).by_kind("receipt") if r.data.get("purpose") == "integration"])
            commit_packet(self.root, integrate(self.root, self.actor, self.req, trusted, "He revisado el resultado conjunto y su compatibilidad"))
            self.assertFalse([d for d in load(self.root).by_kind("decision") if d.data.get("purpose") == "acceptance"])
            commit_packet(self.root, accept(self.root, self.actor, self.req, "Acepto el resultado funcional concreto"))
            last = status(self.root)["requests"][0]["steps"][-1]
            self.assertEqual("completed", last["state"])


if __name__ == "__main__": unittest.main()
