import copy
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from v2_fixture import element, project, write
from variant_fixture import IMAGE, OBSERVER
from v2_contract import ContractError, DOCS, load, render_document
from v2_authoring import edit_elements
from v2_lifecycle import authorize, start, checkpoint
from v2_verification import verification_plan, verify, close, evidence
from project_variants import markdown, approval_preview, apply_approval, VariantError

AT = "2026-09-18T00:00:00+00:00"


def materialize(root):
    project(root)
    model = load(root)
    task = model.elements["TASK-001"]
    values = dict(task.meta, relations={**task.relations, "bindings": ["BIND-001"]},
                  paths=["component/service.py"], gates=["GATE-API-TEST", "GATE-API-OPENAPI"])
    for path, data in edit_elements(model, {task.id: values}).items():
        write(root, path, data)
    write(root, DOCS + "/03-solution/bindings.md", render_document("binding", "Referencia tecnológica", [
        element("BIND-001", "binding", profile_id="API-FASTAPI-STATELESS-OCI", unit_path="component"),
        element("ENV-001", "environment", role="development")]))
    write(root, "component/service.py", 'def acknowledge(request):\n    return {"accepted": request["value"]} if request["value"] else {"error": "required"}\ncontract = {"request": ["value"], "response": ["accepted", "error"]}\n')
    write(root, "component/requirements.txt", "fastapi==0.140.0\nattrs==25.3.0\n")
    write(root, "component/requirements.lock", "fastapi==0.140.0\nattrs==25.3.0\n")
    write(root, "component/.python-version", "3.13.12\n")
    write(root, "observer.py", OBSERVER)
    config = {"schema_version": "1.0", "policy": {"mode": "approved-project-variants", "allow_task_closure": True,
              "allowed_stages": ["development", "integration"], "approver_roles": ["synthetic-owner"],
              "max_age_days": 30, "cache_max_age_hours": 24}, "variants": [{
              "id": "VAR-001", "profile_id": "API-FASTAPI-STATELESS-OCI", "increment": "INC-001", "release": "REL-001",
              "task_ids": ["TASK-001"], "environment": "ENV-001", "technology_roots": ["component"],
              "inputs": ["component", "observer.py"], "composition": {"layout": "component"},
              "gates": [{"id": gate, "source": "approved-consumer", "stage": stage, "scopes": ["component"], "interfaces": [],
                         "deterministic": True, "timeout_seconds": 20, "image": IMAGE,
                         "observer": {"path": "observer.py", "sha256": hashlib.sha256(OBSERVER.encode()).hexdigest(),
                                      "command": ["/usr/local/bin/python", "-I", "-B", "/input/observer.py"]}}
                        for gate, stage in [("GATE-API-TEST", "development"), ("GATE-API-OPENAPI", "integration")]]}]}
    write(root, DOCS + "/03-solution/technology-variants.md", markdown(config, "Variante sintética"))
    return config


def fake_observer(root, entry):
    gate = entry["gate"]
    raw = b'{"synthetic_test_observation":true}'
    digest = hashlib.sha256(raw).hexdigest()
    return {"gate_id": gate["id"], "status": "passed", "evidence_scopes": gate["scopes"], "interface_ids": [],
            "observations": {"synthetic": True}, "artifacts": [{"path": "result.json", "sha256": digest}]}, {digest: raw}


class V2VariantTests(unittest.TestCase):
    def test_engine_identity_covers_transitive_guard_and_observation_contract(self):
        from v2_verification import engine_hash
        original = Path.read_bytes
        expected = engine_hash()
        for changed in ("v2_features.py", "v2_storage.py", "v2_controls.py", "consumer-observation.schema.json", "requirements-runtime.txt"):
            def read(path, *, target=changed):
                raw = original(path)
                return raw + b"\nsynthetic-change" if path.name == target else raw
            with self.subTest(changed=changed), patch.object(Path, "read_bytes", read):
                self.assertNotEqual(engine_hash(), expected)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = materialize(self.root)
        self.clock = patch("v2_lifecycle.now", return_value=AT)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        verification_clock = patch("v2_verification.now", return_value=AT)
        verification_clock.start()
        self.addCleanup(verification_clock.stop)
        self.args = dict(actor="synthetic-owner", role="delivery-owner", environment="ENV-001", approved_at=AT,
                         expires_at="2026-10-18T00:00:00+00:00", reason="Caso sintético confirmado.")
        result = authorize(load(self.root), ["TASK-001"], **self.args)
        authorize(load(self.root), ["TASK-001"], **self.args, authorized_hash=result["preview_hash"])

    def approve(self, stage):
        result = approval_preview(self.root, "VAR-001", "ENV-001", stage, actor="synthetic-owner", reason="Diferencias revisadas.",
                                  risks="Riesgo acotado a la prueba.", expires=(date.today() + timedelta(days=7)).isoformat())
        apply_approval(self.root, result, result["preview_hash"])

    def handoff(self):
        self.approve("development")
        self.approve("integration")
        args = dict(actor="synthetic-dev", at=AT)
        model = load(self.root)
        result = start(model, ["TASK-001"], "ENV-001", **args)
        start(model, ["TASK-001"], "ENV-001", **args, authorized_hash=result["preview_hash"])
        model = load(self.root)
        ckargs = dict(state="in-review", actor="synthetic-dev", at=AT, summary="Preparado para prueba sintética.", next_action="Verificar.")
        result = checkpoint(model, **ckargs)
        checkpoint(model, **ckargs, authorized_hash=result["preview_hash"])

    def test_missing_technology_approval_blocks_start(self):
        with self.assertRaises((VariantError, ContractError)):
            start(load(self.root), ["TASK-001"], "ENV-001", actor="synthetic", at=AT)

    def test_full_synthetic_verification_records_and_closes_reserved_only(self):
        self.handoff()
        result = verify(load(self.root), ["TASK-001"], "ENV-001", "integration", evidence_id="EVID-001", execute=True, runner=fake_observer)
        self.assertEqual(result["status"], "verified-with-reservations")
        model = load(self.root)
        self.assertTrue(model.valid, model.errors)
        args = dict(actor="synthetic-owner", at=AT)
        plan = close(model, ["TASK-001"], "EVID-001", **args)
        close(model, ["TASK-001"], "EVID-001", **args, authorized_hash=plan["preview_hash"])
        self.assertEqual(load(self.root).elements["TASK-001"].meta["state"], "done")
        self.assertEqual(evidence(load(self.root), "EVID-001")["delivery"], "not-assessed")

    def test_cache_reuses_without_refreshing_observation_age(self):
        self.handoff()
        verify(load(self.root), ["TASK-001"], "ENV-001", "integration", evidence_id="EVID-001", execute=True, runner=fake_observer)
        old = evidence(load(self.root), "EVID-001")
        with patch("consumer_observer.execute", side_effect=AssertionError("cache should not execute")):
            result = verify(load(self.root), ["TASK-001"], "ENV-001", "integration", evidence_id="EVID-002", execute=True)
        self.assertEqual(result["processes_executed"], 0)
        new = evidence(load(self.root), "EVID-002")
        self.assertEqual(old["build_id"], new["build_id"])
        self.assertEqual([c["observed_at"] for c in old["checks"]], [c["observed_at"] for c in new["checks"]])
        self.assertTrue(all(c["disposition"] == "reused" for c in new["checks"]))

    def test_development_omission_never_closes_critical_gate(self):
        self.handoff()
        result = verify(load(self.root), ["TASK-001"], "ENV-001", "development", evidence_id="EVID-001", execute=True, runner=fake_observer)
        self.assertEqual(result["status"], "not-verified")
        with self.assertRaises(ContractError):
            close(load(self.root), ["TASK-001"], "EVID-001", actor="synthetic-owner", at=AT)

    def test_observer_changed_or_artifact_tampered_invalidates_reuse(self):
        self.handoff()
        verify(load(self.root), ["TASK-001"], "ENV-001", "integration", evidence_id="EVID-001", execute=True, runner=fake_observer)
        stored = evidence(load(self.root), "EVID-001")
        artifact = stored["checks"][0]["artifacts"][0]["evidence_path"]
        write(self.root, artifact, b"tampered")
        with self.assertRaises(ContractError):
            verification_plan(load(self.root), ["TASK-001"], "ENV-001", "integration")

    def test_failed_gate_never_passes_or_enters_cache(self):
        self.handoff()
        def failure(root, entry):
            value, blobs = fake_observer(root, entry)
            value["status"] = "failed"
            return value, blobs
        result = verify(load(self.root), ["TASK-001"], "ENV-001", "integration", evidence_id="EVID-001", execute=True, runner=failure)
        self.assertEqual(result["status"], "not-verified")
        plan = verification_plan(load(self.root), ["TASK-001"], "ENV-001", "integration")
        self.assertTrue(all(c["disposition"] == "execute" for c in plan["checks"]))


if __name__ == "__main__":
    unittest.main()
