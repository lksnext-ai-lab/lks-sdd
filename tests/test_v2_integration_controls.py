"""Adversarial boundaries for composed, visual, delivery and trusted-review flows."""
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from v2_fixture import element, project, write
from v2_contract import ContractError, DOCS, canonical, execution_context, load, render_document, sha
from v2_authoring import edit_elements
from v2_visual import request, inspect, observe, accept, cancel
from v2_quality import visual_coverage_errors, observation_errors, interface_obligation

AT = "2026-09-18T00:00:00+00:00"


class V2IntegrationControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "consumer"
        self.root.mkdir()
        project(self.root)
        clock = patch("v2_controls.now", return_value=AT)
        clock.start()
        self.addCleanup(clock.stop)

    def mutate(self, function, *args, **kwargs):
        proposed = function(load(self.root), *args, **kwargs)
        function(load(self.root), *args, **kwargs, authorized_hash=proposed["preview_hash"])
        return proposed

    def visual(self):
        asset = DOCS + "/02-specification/features/FTR-001-pedidos/assets/proposal.png"
        raw = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aHkwAAAAASUVORK5CYII=")
        write(self.root, asset, raw)
        write(self.root, DOCS + "/02-specification/visual.md", render_document("visual", "Visual contract", [
            element("VIS-001", "visual", baseline_assets=[asset], viewports=["desktop"], states=["confirmed", "draft"],
                    relations={"requirements": ["FR-001"], "acceptance": ["AC-001"]})]))
        return {"path": asset, "sha256": sha(raw), "description": "Synthetic one-pixel fixture, not a human-approved design",
                "viewport": "desktop", "state": "confirmed"}

    def handoff(self):
        asset = self.visual()
        proposal = self.mutate(request, {"from_host": "copilot", "to_host": "codex", "actor": "synthetic",
                                      "visual_ids": ["VIS-001"], "brief": "Synthetic visual transfer"})
        return proposal["id"], asset

    def test_visual_transfer_is_bound_proposal_not_execution_authority(self):
        identifier, asset = self.handoff()
        self.mutate(observe, identifier, {"host": "codex", "actor": "synthetic", "assets": [asset]})
        self.assertEqual(inspect(load(self.root), identifier)["result"]["acceptance"], "not-granted")
        self.mutate(accept, identifier, {"selected_asset": asset["path"], "actor": "reviewer", "recorded_at": AT, "reason": "Synthetic review"})
        model = load(self.root)
        self.assertEqual(model.by_kind("authorization"), [])
        self.assertEqual(model.by_kind("receipt")[0].meta["implementation_authorization"], "not-granted")

    def test_native_codex_does_not_create_unnecessary_handoff(self):
        self.visual()
        with self.assertRaises(ContractError):
            request(load(self.root), {"from_host": "codex", "to_host": "codex", "actor": "synthetic", "visual_ids": ["VIS-001"], "brief": "Native"})

    def test_visual_asset_or_source_change_rejects_reuse(self):
        identifier, asset = self.handoff()
        self.mutate(observe, identifier, {"host": "codex", "actor": "synthetic", "assets": [asset]})
        write(self.root, asset["path"], b"changed")
        with self.assertRaises(ContractError):
            inspect(load(self.root), identifier)
        # A stale request may still be explicitly cancelled; no old evidence is erased.
        self.mutate(cancel, identifier, {"actor": "owner", "recorded_at": AT, "reason": "Sources changed"})
        with self.assertRaisesRegex(ContractError, "cancelled"):
            inspect(load(self.root), identifier)

    def test_visual_verification_needs_every_state_and_exact_artifacts(self):
        asset = self.visual()
        screenshot = {**asset, "visual_id": "VIS-001", "acceptance_ids": ["AC-001"]}
        observations = [{"status": "passed", "observations": {"screenshots": [screenshot]}, "artifacts": [asset]}]
        errors = visual_coverage_errors(load(self.root), ["TASK-001"], observations)
        self.assertTrue(any("draft" in e for e in errors))
        observations[0]["observations"]["screenshots"].append({**screenshot, "state": "draft"})
        self.assertEqual(visual_coverage_errors(load(self.root), ["TASK-001"], observations), [])
        observations[0]["artifacts"] = []
        self.assertTrue(visual_coverage_errors(load(self.root), ["TASK-001"], observations))

    def composition(self):
        from profile_registry import load_profile_bundle
        profile = "WEB-FASTAPI-REACT-LOCAL-AUTH-PG-PY313-TS59"
        bundle = load_profile_bundle(profile)
        bindings = [element(f"BIND-{i:03}", "binding", profile_id=exact.partition("@")[0], unit_id=f"UNIT-{i:03}", unit_path=role)
                    for i, (role, exact) in enumerate(sorted(bundle.driver["variant"]["participants"].items()), 1)]
        write(self.root, DOCS + "/03-solution/bindings.md", render_document("binding", "Exact participants", bindings))
        ids = [b["meta"]["id"] for b in bindings]
        interface = element("INT-001", "interface", protocol="HTTP", contract="GET /api/v1/items; POST /api/v1/items",
            operations=["read", "write"], exact_composition=profile + "@" + bundle.profile["version"],
            evidence_scopes=["contract", "composition", "user-flow", "persistence"], gates=["GATE-BROWSER-FULLSTACK-E2E"],
            consumer_unit="UNIT-003", producer_unit="UNIT-001", relations={"bindings": ids})
        write(self.root, DOCS + "/03-solution/interfaces.md", render_document("interface", "Business contract", [interface]))
        model = load(self.root)
        task = model.elements["TASK-001"]
        for name, data in edit_elements(model, {task.id: dict(task.meta, relations={**task.relations, "interfaces": ["INT-001"], "bindings": ids})}).items():
            write(self.root, name, data)
        return profile

    def test_exact_composition_uses_certified_participants_and_immutable_locks(self):
        from v2_preparation import reference_locks
        from v2_composition import resolve, command
        from profile_registry import load_profile_bundle
        profile = self.composition()
        model = load(self.root)
        generated = reference_locks(model, ["TASK-001"])
        self.assertTrue(any("/compositions/" in p for p in generated))
        for name, data in generated.items():
            write(self.root, name, data)
        composition = resolve(load(self.root), ["TASK-001"], require_locks=True)[0]
        self.assertEqual(composition["profile_id"], profile)
        gate = next(g for g in load_profile_bundle(profile).driver["verify"]["checks"] if g["id"] == composition["gate_id"])
        invocation = command(self.root, {"composition": composition, "packaged": gate,
                            "interface_obligations": [interface_obligation(model.elements["INT-001"])]})
        self.assertEqual(invocation["interface_ids"], ["INT-001"])
        self.assertTrue(invocation["requires_containers"])
        write(self.root, composition["path"], "{}")
        with self.assertRaises(ContractError):
            resolve(load(self.root), ["TASK-001"], require_locks=True)

    def test_unresolved_composition_participant_does_not_invent_unit(self):
        from v2_composition import resolve
        self.composition()
        model = load(self.root)
        binding = model.elements["BIND-001"]
        meta = dict(binding.meta)
        meta.pop("unit_id")
        for name, data in edit_elements(model, {binding.id: meta}).items():
            write(self.root, name, data)
        with self.assertRaisesRegex(ContractError, "unit identities"):
            resolve(load(self.root), ["TASK-001"])

    def test_adopted_preparation_writes_only_verification_resources(self):
        from v2_lifecycle import authorize
        from v2_preparation import prepare
        from v2_fixture import ROOT
        fixture = json.loads((ROOT / "tests/fixtures/adoption-flat-v018.json").read_text())
        for relative, content in fixture["files"].items():
            write(self.root, relative, content)
        model = load(self.root)
        write(self.root, ".lks-sdd/project.json", canonical({**model.manifest, "route": "adopt-existing"}))
        write(self.root, DOCS + "/03-solution/bindings.md", render_document("binding", "Exact adoption", [
            element("BIND-001", "binding", profile_id="API-FASTAPI-LOCAL-AUTH-PG-OCI-PY313", unit_path="backend")]))
        model = load(self.root)
        task = model.elements["TASK-001"]
        for path, raw in edit_elements(model, {task.id: dict(task.meta, relations={**task.relations, "bindings": ["BIND-001"]})}).items():
            write(self.root, path, raw)
        self.mutate(authorize, ["TASK-001"], actor="owner", role="owner", environment="ENV-001",
            approved_at=AT, expires_at="2026-09-30T00:00:00+00:00", reason="Synthetic bounded adoption")
        before = {p: (self.root / p).read_bytes() for p in fixture["files"]}
        proposed = self.mutate(prepare, ["TASK-001"], "ENV-001")
        self.assertTrue(proposed["writes"])
        self.assertTrue(all(p.startswith((".lks-sdd/verification/", ".lks-sdd/profiles/")) for p in proposed["writes"]))
        self.assertTrue(all((self.root / p).read_bytes() == raw for p, raw in before.items()))
        self.assertEqual(proposed["verification"], "not-run")

    def test_successful_unrelated_http_route_is_not_business_contract_evidence(self):
        self.composition()
        item = load(self.root).elements["INT-001"]
        observation = {"gate_id": "GATE-BROWSER-FULLSTACK-E2E", "status": "passed",
                       "scopes": ["contract", "composition", "user-flow", "persistence"], "interfaces": ["INT-001"],
                       "observations": {"requests": [{"method": "POST", "path": "/login", "status": 200}], "domain_mocks": False},
                       "artifacts": [{"path": "trace.json", "sha256": "a" * 64}]}
        errors = observation_errors(observation, {"gate_id": observation["gate_id"], "interface_obligations": [interface_obligation(item)]})
        self.assertTrue(any("contrato declarado" in e for e in errors))

    def test_trusted_guard_rejects_self_approved_test_weakening(self):
        from v2_integration_guard import assess, review
        candidate = Path(self.temp.name) / "incoming"
        candidate.mkdir()
        project(candidate)
        write(candidate, "tests/test_print.py", "assert True\n")
        result = assess(self.root, candidate, ["TASK-001"])
        self.assertEqual(result["status"], "blocked")
        request = {"actor": "trusted-reviewer", "recorded_at": AT, "reason": "Synthetic exact diff review"}
        proposed = review(self.root, candidate, ["TASK-001"], request)
        review(self.root, candidate, ["TASK-001"], request, authorized_hash=proposed["preview_hash"])
        self.assertEqual(assess(self.root, candidate, ["TASK-001"])["status"], "structurally-within-scope")
        write(candidate, "tests/test_print.py", "pass\n")
        self.assertEqual(assess(self.root, candidate, ["TASK-001"])["status"], "blocked")

    def test_delivery_approval_cannot_be_substituted_by_a_successful_log(self):
        from v2_controls import authorize_delivery
        value = {"actor": "owner", "recorded_at": AT, "expires_at": "2026-09-19T00:00:00+00:00",
                 "environment": "ENV-001", "version": "1.0.0", "artifact_digest": "a" * 64, "evidence_id": "EVID-001",
                 "operation": "deployed", "features": ["FTR-001"], "reason": "Synthetic delivery"}
        with patch("v2_verification.evidence", return_value={"classification": "verified", "artifact_digests": ["a" * 64]}):
            with self.assertRaisesRegex(ContractError, "deployable"):
                authorize_delivery(load(self.root), value)

    def test_delivery_rollback_and_flags_are_separate_exact_observations(self):
        from v2_controls import authorize_delivery, delivery_observation
        write(self.root, DOCS + "/06-operation/environments.md", render_document("environment", "Environment", [
            element("ENV-001", "environment", role="production")]))
        verified = {"classification": "verified", "deliverable_artifact_digests": ["a" * 64],
                    "environment": "ENV-001", "stage": "release", "integrity_sha256": "b" * 64}
        for index, operation in enumerate(("deployed", "rolled-back", "flag-disabled"), 1):
            request = {"actor": "synthetic-owner", "recorded_at": AT, "expires_at": "2026-09-19T00:00:00+00:00",
                "environment": "ENV-001", "version": "1.0.0", "artifact_digest": "a" * 64, "evidence_id": "EVID-001",
                "operation": operation, "features": ["FTR-001"], "reason": "Synthetic observation, no actual deployment"}
            if operation == "flag-disabled":
                request["flags"] = {"orders-print-v2": False}
            with patch("v2_verification.evidence", return_value=verified):
                self.mutate(authorize_delivery, request)
                auth = load(self.root).by_kind("receipt")[-1]
                request["authorization_id"] = auth.id
                with self.assertRaisesRegex(ContractError, "approved evidence"):
                    delivery_observation(load(self.root), {**request, "evidence_id": "EVID-999"})
                with self.assertRaisesRegex(ContractError, "G4"):
                    delivery_observation(load(self.root), request)
                proofs = {}
                for gate in ("smoke", "observability", "recovery"):
                    raw = canonical({"kind": gate, "status": "passed", "observed_at": AT,
                                     "flags": request.get("flags", {}),
                                     **{k: request[k] for k in ("environment", "version", "artifact_digest", "operation")}})
                    path = DOCS + "/evidence/delivery-" + str(index) + "-" + gate + ".json"
                    write(self.root, path, raw)
                    proofs[gate] = {"status": "passed", "path": path, "sha256": sha(raw)}
                request["delivery_evidence"] = proofs
                self.mutate(delivery_observation, request)
                from v2_controls import revoke
                self.mutate(revoke, auth.id, actor="owner", at=AT, reason="Explicit scope revocation after observation")
                with self.assertRaisesRegex(ContractError, "approval"):
                    delivery_observation(load(self.root), request)
        receipts = [r for r in load(self.root).by_kind("receipt") if r.meta["category"] == "delivery-observation"]
        self.assertEqual([r.meta["operation"] for r in receipts], ["deployed", "rolled-back", "flag-disabled"])
        self.assertEqual(load(self.root).elements["TASK-001"].meta["state"], "ready")


if __name__ == "__main__":
    unittest.main()
