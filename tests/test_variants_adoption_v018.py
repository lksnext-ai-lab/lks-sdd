"""Exact catalog diagnosis and safe adoption regressions, synthetic only."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from adoption_preparation import adoption_preview, adoption_resources
from evidence_safety import sanitize, evidence_safety_errors
from profile_impact import impact
from profile_registry import load_profile_bundle
from technology_resolution import inspect_dependencies, diagnose
from composition_contract import resolve_compositions
from observation_contract import persistence_errors
from profile_materialization import materialize_profile
from validate_reference_profile import validate_consumer_profile_lock

_spec = importlib.util.spec_from_file_location("variant_verification_test", ROOT / "skills/lks-sdd-verify/scripts/run_verification.py")
verification = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = verification
_spec.loader.exec_module(verification)


class VariantsAdoptionV018Tests(unittest.TestCase):
    def test_system_variant_cannot_be_bound_to_a_fictitious_unit(self):
        with tempfile.TemporaryDirectory() as directory:
            errors, _ = validate_consumer_profile_lock(Path(directory), profile_id="WEB-FASTAPI-REACT-LOCAL-AUTH-PG-PY313-TS59", binding_id="BIND-001", required=False)
            self.assertTrue(any("INT.Exact composition" in error for error in errors))

    def test_declared_resolved_and_verified_runtime_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"dependencies": {"react": "^19.0.0"}}))
            (root / "package-lock.json").write_text(json.dumps({"packages": {"node_modules/react": {"version": "19.2.7"}}}))
            result = inspect_dependencies(root)
            self.assertEqual(result["declared"]["npm:react"], "^19.0.0")
            self.assertEqual(result["resolved"]["npm:react"], "19.2.7")
            self.assertEqual(result["runtime_verified"], {})

    def test_dependency_changes_are_seen_without_changing_profile_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text('{"dependencies":{"react":"19.2.7"}}')
            before = inspect_dependencies(root)
            (root / "package.json").write_text('{"dependencies":{"react":"17.0.2"}}')
            after = diagnose(root, "WEB-REACT-VITE-LOCAL-AUTH-STATIC-TS59", snapshot=before)
            self.assertTrue(after["dependency_drift"])
            self.assertFalse(after["certified"])

    def test_react_16_and_17_are_not_certified(self):
        for version in ["16.14.0", "17.0.2"]:
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "package.json").write_text(json.dumps({"dependencies": {"react": version}}))
                (root / "package-lock.json").write_text(json.dumps({"packages": {"node_modules/react": {"version": version}}}))
                result = diagnose(root, "WEB-REACT-VITE-LOCAL-AUTH-STATIC-TS59")
                self.assertFalse(result["certified"])
                self.assertIn(result["compatibility"], {"not-evaluated", "insufficient-information"})

    def test_adoption_of_both_layouts_preserves_every_consumer_byte(self):
        for layout, prefix in [("flat", Path(".")), ("apps", Path("apps"))]:
            with self.subTest(layout=layout), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture = json.loads((ROOT / f"tests/fixtures/adoption-{layout}-v018.json").read_text())
                self.assertFalse(fixture["contains_consumer_data"])
                for relative, content in fixture["files"].items():
                    path = root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
                before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
                profile = "API-FASTAPI-LOCAL-AUTH-PG-OCI-PY313"
                binding = {"binding_id": "BIND-001", "unit_path": (prefix / "backend").as_posix(), "profile_id": profile}
                driver = load_profile_bundle(profile).driver
                preview = adoption_preview(root, binding, driver)
                self.assertEqual(preview["adapter"], layout)
                for path, content in adoption_resources(root, binding, driver):
                    self.assertTrue(path.relative_to(root).as_posix().startswith(".lks-sdd/verification/"))
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)
                self.assertTrue(all((root / path).read_bytes() == content for path, content in before.items()))
                self.assertEqual(preview["functional_files_written"], [])
                self.assertFalse(preview["commands_from_metadata"])

    def test_legacy_copy_driver_cannot_overwrite_adopted_application(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "no se copiará"):
                adoption_preview(Path(directory), {"unit_path": "."}, {"prepare": {"strategy": "copy", "sources": []}})

    def test_sanitization_precedes_output_without_rewriting_original(self):
        original = {"headers": {"Authorization": "Bearer synthetic-sensitive-token", "Cookie": "refresh=synthetic"},
                    "log": "password=synthetic-credential"}
        before = copy.deepcopy(original)
        cleaned, locations = sanitize(original)
        self.assertTrue(locations)
        self.assertEqual(original, before)
        self.assertNotIn("synthetic-credential", json.dumps(cleaned))
        self.assertTrue(evidence_safety_errors(original))

    def test_uncertain_impact_expands_scope_and_never_waives_certification(self):
        report = impact(["unknown-input.bin"])
        self.assertTrue(report["uncertainty"])
        self.assertFalse(report["recertification_waived"])
        self.assertGreaterEqual(len(report["affected"]), 23)
        self.assertTrue(all(item["reasons"] for item in report["affected"]))

    def test_composition_requires_exact_participants_without_system_unit(self):
        profile = "WEB-FASTAPI-REACT-LOCAL-AUTH-PG-PY313-TS59"
        participants = load_profile_bundle(profile).driver["variant"]["participants"]
        bindings = {f"BIND-{i:03}": {"binding_id": f"BIND-{i:03}", "unit_id": f"UNIT-{i:03}", "unit_path": role,
                    "profile_id": exact.partition("@")[0], "state": "confirmed", "lock_path": f".lks-sdd/profiles/BIND-{i:03}.lock.json"}
                    for i, (role, exact) in enumerate(participants.items(), 1)}
        row = {"State": "confirmed", "Verification task": "TASK-001", "Exact composition": profile + "@1.0.0",
               "Protocol": "HTTPS", "Required evidence": "contract,composition,user-flow,persistence", "Operations": "read,write",
               "Consumer unit": "UNIT-001", "Producer unit": "UNIT-002", "Profile bindings": ",".join(bindings)}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); delivery = {"bindings": bindings, "interfaces": {"INT-001": row}}
            resolved, errors = resolve_compositions(root, delivery, ["TASK-001"], require_certified=False)
            self.assertEqual(errors, [])
            self.assertEqual(len(resolved[0]["material"]["participants"]), 4)
            self.assertEqual(len(bindings), 4)
            row["Profile bindings"] = "BIND-001,BIND-002,BIND-003"
            self.assertTrue(resolve_compositions(root, delivery, ["TASK-001"], require_certified=False)[1])
            row["Profile bindings"] = ",".join(bindings); row["Consumer unit"] = "UNIT-999"
            self.assertTrue(resolve_compositions(root, delivery, ["TASK-001"], require_certified=False)[1])

    def test_simulated_or_foreign_database_read_is_rejected(self):
        baseline = {"mutation": {"record_id": "synthetic-001"}, "read_back": {"observer": "postgresql-psql", "record_id": "synthetic-001", "resource": "records", "matches": True}, "persistence": True}
        self.assertEqual(persistence_errors(baseline), [])
        for replacement in [True, {**baseline["read_back"], "record_id": "foreign"}, {**baseline["read_back"], "observer": "mock"}]:
            self.assertTrue(persistence_errors({**baseline, "read_back": replacement}))

    def test_consumer_cannot_replace_the_packaged_verification_adapter(self):
        profile = "API-FASTAPI-LOCAL-AUTH-PG-OCI-PY313"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); materialize_profile(profile, root)
            (root / "verification/gate.py").write_text("raise RuntimeError('consumer-controlled adapter')\n")
            bundle = load_profile_bundle(profile)
            check = next(c for c in bundle.driver["verify"]["checks"] if c["id"] == "GATE-API-TEST")
            result = verification._profile_command(root, {"binding_id": "BIND-001", "profile_id": profile, "unit_path": "."}, check)
            self.assertEqual(Path(result["command"][1]), ROOT / "profiles/_shared/local-auth/verification/gate.py")
            config = root / "profile-runtime.json"; content = json.loads(config.read_text()); content["images"]["postgresql"] = "untrusted:18@sha256:" + "a" * 64
            config.write_text(json.dumps(content))
            with self.assertRaisesRegex(verification.VerificationError, "diverge"):
                verification._profile_command(root, {"binding_id": "BIND-001", "profile_id": profile, "unit_path": "."}, check)


if __name__ == "__main__": unittest.main()
