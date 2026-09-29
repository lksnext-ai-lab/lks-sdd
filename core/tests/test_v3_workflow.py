"""Behavioral tests against actual temporary Git projects and canonical Markdown."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from v3_contract import ContractError, element, load
from v3_storage import apply
from v3_authoring import initialize, author, approve, approve_and_authorize
from v3_workflow import transition, state
from v3_verification import evidence


def commit_packet(root, packet):
    return apply(root, packet, packet["preview"]["preview_hash"])


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode: raise RuntimeError(result.stderr.decode())


class ProjectFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v3-flow-")
        self.addCleanup(self.temp.cleanup); self.root = Path(self.temp.name)
        git(self.root, "init", "-b", "main")
        git(self.root, "checkout", "-b", "codex/request")
        controls = {key: {"mode": "not-used", "reason": "Decisión explícita de este proyecto de prueba"}
                    for key in ("sonar", "dependency-check")}
        packet = initialize(self.root, "Fixture", "Operador de prueba", "individual-brief", controls,
                            "Confirmo estas reglas y mi responsabilidad", target="main")
        self.actor = packet["summary"]["member"]
        commit_packet(self.root, packet)

    def plan(self):
        req = element("request", "Cambio de saludo", "Cambiar únicamente el saludo del módulo acordado.")
        acceptance = element("acceptance", "Saludo verificable", "El módulo devuelve el saludo acordado.")
        prop = element("proposal", "Propuesta concreta", "Se cambia el saludo del módulo app.py y se conserva su interfaz pública.",
                       part="joint", objective="Saludo", included=["app.py"], excluded=["UI"], behavior="Devuelve Hola",
                       solution="Función Python existente", impact="Módulo aislado", acceptance=["saludo"], request=req["meta"]["uid"])
        prop["meta"]["relations"] = {"acceptance": [acceptance["meta"]["uid"]]}
        req["meta"]["relations"] = {"proposal": [prop["meta"]["uid"]]}
        commit_packet(self.root, author(self.root, self.actor, [req, prop, acceptance]))
        self.req, self.prop = req["meta"]["uid"], prop["meta"]["uid"]
        commit_packet(self.root, approve(self.root, self.actor, [self.prop], "proposal", "Valido exactamente esta propuesta"))
        task = element("task", "Cambiar saludo", "Implementar y comprobar el saludo acordado.", request=self.req,
                       owner=self.actor, scope=["app.py"], acceptance=["saludo"], tests=["test_saludo"])
        task["meta"]["relations"] = {"covers": [acceptance["meta"]["uid"]]}
        plan = element("plan", "Plan de saludo", "Una implementación acotada con comprobación de su resultado.", request=self.req)
        plan["meta"]["relations"] = {"tasks": [task["meta"]["uid"]]}
        commit_packet(self.root, author(self.root, self.actor, [task, plan]))
        self.task, self.plan_id = task["meta"]["uid"], plan["meta"]["uid"]
        commit_packet(self.root, approve_and_authorize(self.root, self.actor, self.plan_id, "Valido y autorizo este plan"))

    def advance(self, action):
        commit_packet(self.root, transition(self.root, self.actor, self.task, action, "Resultado comprobado del escenario"))

class WorkflowTests(ProjectFixture):
    def test_alias_change_preserves_authority_but_latest_failed_evidence_blocks_close(self):
        self.plan()
        item = copy.deepcopy(load(self.root).get(self.task).item())
        item["meta"].update(id="TASK-SALUDO", revision=item["meta"]["revision"]+1)
        commit_packet(self.root, author(self.root, self.actor, [item]))
        self.advance("start"); (self.root/"app.py").write_text("answer = 42\n")
        self.advance("implement")
        report = "docs/lks-sdd/evidence/result.txt"
        (self.root/report).parent.mkdir(parents=True, exist_ok=True)
        (self.root/report).write_text("Synthetic evidence transport")
        for outcome in ("passed", "failed"):
            commit_packet(self.root, evidence(self.root, self.actor, self.task, ["test_saludo"], outcome, "automated", report, "Resultado de fixture"))
            if outcome == "passed": self.advance("verify")
        with self.assertRaises(ContractError): self.advance("close")
        commit_packet(self.root, evidence(self.root, self.actor, self.task, ["test_saludo"], "passed", "automated", report, "Nueva comprobación satisfactoria del mismo sujeto"))
        self.advance("close")

    def test_full_lifecycle_and_stale_code(self):
        self.plan(); self.advance("start")
        (self.root / "app.py").write_text("def saludo(): return 'Hola'\n")
        self.advance("implement")
        with self.assertRaises(ContractError): self.advance("close")
        report = "docs/lks-sdd/evidence/input.txt"
        (self.root / report).parent.mkdir(parents=True, exist_ok=True)
        (self.root / report).write_text("test_saludo: passed; expected Hola, actual Hola")
        commit_packet(self.root, evidence(self.root, self.actor, self.task, ["test_saludo"], "passed", "automated", report, "Resultado de ejecución del escenario de prueba"))
        self.advance("verify"); self.advance("close")
        model = load(self.root).require_valid()
        self.assertEqual("closed", state(model, model.get(self.task)))
        (self.root / "app.py").write_text("def saludo(): return 'Otro'\n")
        model = load(self.root).require_valid()
        self.assertEqual("in-progress", state(model, model.get(self.task)))

    def test_approval_change_invalidates_start(self):
        self.plan()
        model = load(self.root); prop = copy.deepcopy(model.get(self.prop).item())
        prop["meta"]["revision"] += 1; prop["body"] += " Ahora cambia también el formato."
        commit_packet(self.root, author(self.root, self.actor, [prop]))
        with self.assertRaises(ContractError): self.advance("start")

    def test_scope_and_branch_guards(self):
        self.plan(); self.advance("start")
        (self.root / "unrelated.txt").write_text("Cambio ajeno")
        with self.assertRaisesRegex(ContractError, "fuera del alcance"): self.advance("implement")
        git(self.root, "checkout", "-b", "codex/other")
        with self.assertRaisesRegex(ContractError, "otra rama"): self.advance("pause")

    def test_stale_preview_preserves_new_work(self):
        note = element("requirement", "Requisito", "Contenido normativo completo.")
        packet = author(self.root, self.actor, [note])
        another = element("requirement", "Otro", "Trabajo ajeno que debe conservarse.")
        commit_packet(self.root, author(self.root, self.actor, [another]))
        with self.assertRaises(ContractError): commit_packet(self.root, packet)
        self.assertIn(another["meta"]["uid"], load(self.root).elements)


if __name__ == "__main__": unittest.main()
