import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_v3_workflow import ProjectFixture, commit_packet, git
from v3_authoring import governance, author
from v3_contract import ContractError, element, load, now, read_bytes, sha
from v3_context import context
from v3_team import handoff, owners
from v3_quality import record, checks, config_digest, normalize, analysis_context
from v3_git import subject
from v3_workflow import transition, exception, evaluate
from v3_policy import policy_for


class GovernanceQualityTests(ProjectFixture):
    def test_deviation_and_conflicting_assignments_remain_visible_without_authority(self):
        from v3_lifecycle import checkpoint
        from v3_guidance import status
        from v3_contract import render, location
        self.plan()
        before = len(load(self.root).by_kind("authorization"))
        commit_packet(self.root, checkpoint(self.root, self.actor, self.task,
                      "Trabajo previo observado antes del inicio autorizado", ["Regularizar la porción actual"], classification="deviation"))
        model = load(self.root)
        self.assertEqual(before, len(model.by_kind("authorization")))
        self.assertEqual("fact", model.by_kind("problem")[0].meta["nature"])
        # Two merged clones can bring competing assignment tips. Status must
        # expose that conflict, and execution must remain blocked.
        for title in ("Clon A", "Clon B"):
            item = element("assignment", title, "Asignación aportada por otro clon.",
                           task=self.task, owner=self.actor, previous=None, status="accepted")
            path = self.root/location(item); path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(render(item))
        view = status(self.root)
        self.assertEqual("conflict", view["requests"][0]["tasks"][0]["state"])
        self.assertTrue(view["issues"])
        with self.assertRaises(ContractError): self.advance("start")

    def test_recipient_acceptance_and_independent_review(self):
        from v3_team import assign
        from v3_verification import evidence
        from v3_guidance import status, readiness, trace
        self.plan(); other = self.add_member()
        self.update_policy(lambda d: d.update(profile="coordinated-team", independent_review=True), requests=[self.req])
        commit_packet(self.root, assign(self.root, self.actor, self.task, other, "Relevo por especialidad"))
        self.assertEqual(self.actor, status(self.root)["requests"][0]["tasks"][0]["owner"])
        offer = load(self.root).by_kind("assignment")[0]
        commit_packet(self.root, assign(self.root, other, self.task, other, "Acepto el trabajo y pendientes", previous=offer.uid, accept=True))
        self.assertEqual(other, status(self.root)["requests"][0]["tasks"][0]["owner"])
        for action in ("start", "implement"):
            if action == "implement": (self.root/"app.py").write_text("answer = 42\n")
            commit_packet(self.root, transition(self.root, other, self.task, action, "Resultado del especialista"))
        self.assertEqual("blocked", readiness(self.root, self.task, other, "verify")["status"])
        report = "docs/lks-sdd/evidence/review.txt"; (self.root/report).parent.mkdir(parents=True, exist_ok=True)
        (self.root/report).write_text("Independent fixture observation")
        commit_packet(self.root, evidence(self.root, self.actor, self.task, ["test_saludo"], "passed", "automated", report, "Revisión separada del ejecutor"))
        self.advance("verify"); self.advance("close")
        entries = trace(self.root, self.task)["events"]
        self.assertIn(other, {e["actor"].get("member") for e in entries})
        self.assertIn(self.actor, {e["actor"].get("member") for e in entries})

    def test_existing_executor_timeout_has_bounded_retry_and_preserved_attempts(self):
        from v3_contract import fingerprint
        from v3_quality import run_existing
        arguments = ["-c", "import time; time.sleep(2)"]
        control = {"mode": "required", "reason": "Exportador existente de prueba", "executor": "existing-command", "scope": ["app.py"],
                   "availability": {"state": "available", "source": "Ejecutable Python de la prueba", "phase": "implementation"},
                   "timeout_seconds": 0.05, "max_retries": 1, "executable_sha256": sha(Path(sys.executable).read_bytes()), "arguments_digest": fingerprint(arguments)}
        self.update_policy(lambda d: d["controls"].update(sonar=control)); self.plan()
        first = run_existing(self.root, self.actor, [self.task], "sonar", sys.executable, arguments)
        commit_packet(self.root, first)
        second = run_existing(self.root, self.actor, [self.task], "sonar", sys.executable, arguments, retry_of=first["summary"]["analysis"])
        commit_packet(self.root, second)
        with self.assertRaisesRegex(ContractError, "reintentos"):
            run_existing(self.root, self.actor, [self.task], "sonar", sys.executable, arguments, retry_of=second["summary"]["analysis"])
        self.assertEqual(2, len(load(self.root).by_kind("analysis")))
        self.assertEqual("error", checks(load(self.root), load(self.root).get(self.task))["sonar"]["status"])

    def test_context_attachment_cache_and_retired_root(self):
        self.plan()
        path = self.root/"docs/lks-sdd/details.txt"; path.write_text("Complete first rule")
        note = element("constraint", "Adjunto global", "Respetar [el detalle](../details.txt).", **{"global": True})
        commit_packet(self.root, author(self.root, self.actor, [note]))
        first = context(self.root, [self.task]); second = context(self.root, [self.task])
        self.assertIn("hit", second["runtime_cache"])
        path.write_text("Complete changed rule")
        third = context(self.root, [self.task])
        self.assertNotEqual(first["attachments"][0]["sha256"], third["attachments"][0]["sha256"])
        self.assertEqual("conservative-reference", third["selector_mode"])
        from v3_authoring import approve
        commit_packet(self.root, approve(self.root, self.actor, [self.prop], "proposal", "Acepto también la nueva restricción global"))
        item = copy.deepcopy(load(self.root).get(self.task).item()); item["meta"].update(state="retired", revision=item["meta"]["revision"]+1)
        commit_packet(self.root, author(self.root, self.actor, [item]))
        with self.assertRaisesRegex(ContractError, "retirada"): context(self.root, [self.task])

    def update_policy(self, edit, requests=()):
        model = load(self.root); policy = copy.deepcopy(model.get(model.project.data["policy"]).item())
        policy["meta"]["revision"] += 1; edit(policy["meta"]["data"])
        commit_packet(self.root, governance(self.root, self.actor, [policy], "Acepto este cambio concreto", "Necesidad del proyecto", requests=requests))

    def add_member(self):
        item = element("member", "Compañero", "Especialista de prueba, identidad declarada.", roles=["developer", "reviewer"], active=True)
        commit_packet(self.root, governance(self.root, self.actor, [item], "Incorporo este especialista", "Trabajo de equipo"))
        return item["meta"]["uid"]

    def test_governance_keeps_prior_policy_and_cannot_self_grant(self):
        self.plan(); before = policy_for(load(self.root), self.req).digest()
        other = self.add_member()
        self.update_policy(lambda d: d.update(lifecycle="maintenance"))
        self.assertEqual(before, policy_for(load(self.root), self.req).digest())
        person = copy.deepcopy(load(self.root).get(other).item()); person["meta"]["revision"] += 1
        person["meta"]["data"]["roles"] = ["owner"]
        with self.assertRaises(ContractError): governance(self.root, other, [person], "Me autorizo", "Acceso")
        self.advance("start")
        self.update_policy(lambda d: d["permissions"].update(implement=["owner"]))
        from v3_policy import operator
        with self.assertRaisesRegex(ContractError, "vigente"):
            operator(load(self.root), other, "implement", policy_for(load(self.root), self.req))

    def test_partial_handoff_needs_recipient_and_preserves_history(self):
        self.plan(); other = self.add_member()
        packet = handoff(self.root, self.actor, self.task, other, ["app.py"], "Ayuda de especialista")
        commit_packet(self.root, packet)
        offer = load(self.root).by_kind("handoff")[0].uid
        with self.assertRaises(ContractError): handoff(self.root, self.actor, self.task, other, ["app.py"], "Acepto", previous=offer, accept=True)
        commit_packet(self.root, handoff(self.root, other, self.task, other, ["app.py"], "Recibido con estos pendientes", previous=offer, accept=True))
        model = load(self.root)
        self.assertEqual(2, len(model.by_kind("handoff")))
        self.assertIn(other, {row["member"] for row in owners(model, model.get(self.task))})

    def test_literal_context_includes_unknown_global_and_new_sources(self):
        self.plan(); first = context(self.root, [self.task])
        rule = element("constraint", "Regla sin enlace", "No debe enviarse información fuera del entorno autorizado.")
        commit_packet(self.root, author(self.root, self.actor, [rule]))
        second = context(self.root, [self.task])
        self.assertNotEqual(first["snapshot"], second["snapshot"])
        self.assertIn(rule["body"], [row["text"] for row in second["sources"]])
        self.assertEqual(len(second["sources"]), len({row["key"] for row in second["sources"]}))
        with self.assertRaises(ContractError): context(self.root, [])
        with self.assertRaises(ContractError): context(self.root, ["not-a-root"])

    def test_quality_cannot_close_on_missing_stale_or_wrong_analysis(self):
        control = {"mode": "required", "reason": "Control acordado", "executor": "existing-report", "scope": ["app.py"],
                   "availability": {"state": "available", "source": "Informe normalizado de fixture", "phase": "implementation"},
                   "timeout_seconds": 60, "max_retries": 1}
        self.update_policy(lambda d: d["controls"].update(sonar=control))
        self.plan(); self.advance("start")
        (self.root/"app.py").write_text("answer = 42\n")
        self.advance("implement")
        with self.assertRaises(ContractError): self.advance("verify")
        report = {"analysis_id": "observed-test-analysis", "gate_analysis_id": "other", "generated_at": now(),
                  "context": analysis_context(load(self.root), [load(self.root).get(self.task)]),
                  "tool_version": "fixture-only", "subject_digest": subject(self.root, ["app.py"])["digest"],
                  "config_digest": config_digest(control), "state": "completed", "projectStatus": {"status": "OK", "conditions": []}}
        with self.assertRaises(ContractError): record(self.root, self.actor, [self.task], "sonar", report)
        report["gate_analysis_id"] = report["analysis_id"]
        commit_packet(self.root, record(self.root, self.actor, [self.task], "sonar", report))
        model = load(self.root)
        self.assertEqual("passed", checks(model, model.get(self.task))["sonar"]["status"])
        self.assertEqual("reused", record(self.root, self.actor, [self.task], "sonar", report)["status"])
        (self.root/"app.py").write_text("answer = 0\n")
        model = load(self.root)
        self.assertEqual("pending", checks(model, model.get(self.task))["sonar"]["status"])

    def test_preview_cannot_apply_after_code_change(self):
        self.plan(); self.advance("start")
        (self.root/"app.py").write_text("x = 1\n")
        packet = transition(self.root, self.actor, self.task, "implement", "Terminado")
        (self.root/"app.py").write_text("x = 2\n")
        with self.assertRaises(ContractError): commit_packet(self.root, packet)
        self.assertEqual("x = 2\n", (self.root/"app.py").read_text())

    def test_dependency_check_stale_data_and_severity(self):
        control = {"fail_cvss": 7, "max_data_age_seconds": 3600}
        report = {"analysis_id": "dep-1", "generated_at": now(), "tool_version": "fixture", "subject_digest": "a", "config_digest": "b",
                  "state": "completed", "data_updated_at": now(), "dependencies": [{"fileName": "lib", "vulnerabilities": [{"name": "CVE-fixture", "cvssv3": {"baseScore": 8}}]}]}
        self.assertEqual("failed", normalize("dependency-check", report, control)[0])
        report["data_updated_at"] = (datetime.now(timezone.utc)-timedelta(days=2)).isoformat()
        with self.assertRaises(ContractError): normalize("dependency-check", report, control)

    def test_exception_never_turns_failure_into_pass(self):
        policy = policy_for(load(self.root)).data
        facts = {"authorized": True, "evidence": True, "scope": True, "verified": True, "quality": False,
                 "branch": True, "proposal-approved": True, "plan-approved": True, "implemented": True}
        result = evaluate("close", "verified", facts, policy, [{"rule": "quality", "action": "close", "uid": "exception"}])
        self.assertEqual("closed-with-reservations", result["state"])
        self.assertEqual("allowed", result["status"])
        self.assertFalse(facts["quality"])
        self.plan()
        with self.assertRaises(ContractError): exception(self.root, self.actor, self.task, "quality", "close", "Motivo", "2020-01-01T00:00:00+00:00")


if __name__ == "__main__": unittest.main()
