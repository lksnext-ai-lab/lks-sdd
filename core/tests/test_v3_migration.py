import json
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import v2_authoring
import v2_contract
import v2_storage
import v3_migration
import v3_storage
from v3_contract import load, read_bytes, sha, ContractError


class MigrationTests(unittest.TestCase):
    def test_open_plan_reuses_exact_content_and_requires_current_execution_authority(self):
        from eval_support import materialize_ready_increment, authorize_implementation
        from v3_authoring import author, approve_and_authorize
        from v3_lifecycle import reconcile_migrated
        from v3_approval import approved, task_authority
        from v3_contract import element
        from v3_workflow import transition
        materialize_ready_increment(self.root); authorize_implementation(self.root)
        old = v2_contract.load(self.root); feature = old.elements["FTR-001"].meta["uid"]
        task_id, plan_id = old.elements["TASK-001"].meta["uid"], old.elements["PLAN-001"].meta["uid"]
        original_body = old.elements["FTR-001"].body
        packet = self.packet(); v3_storage.apply(self.root, packet, packet["preview"]["preview_hash"])
        actor = packet["summary"]["member"]
        model = load(self.root)
        self.assertEqual(original_body, model.get(feature).body.strip())
        self.assertTrue(approved(model, [feature])["valid"])
        request = element("request", "Continuar encargo heredado", "Continuar exclusivamente el alcance previamente confirmado.")
        request["meta"]["relations"] = {"proposal": [feature]}
        pending = author(self.root, actor, [request]); v3_storage.apply(self.root, pending, pending["preview"]["preview_hash"])
        model = load(self.root); task = copy.deepcopy(model.get(task_id).item()); plan = copy.deepcopy(model.get(plan_id).item())
        for item in (task, plan):
            item["meta"]["revision"] += 1
            item["meta"]["data"].update(request=request["meta"]["uid"], proposal_units=[feature])
        task["meta"]["data"].update(owner=actor, scope=["src"], acceptance=["Acknowledgement"], tests=["TST-001"])
        task["meta"]["relations"]["covers"] = task["meta"]["relations"]["requirements"] + task["meta"]["relations"]["acceptance"]
        pending = reconcile_migrated(self.root, actor, [task, plan], "Conservo negocio y plan; asigno responsabilidad y rutas vigentes")
        v3_storage.apply(self.root, pending, pending["preview"]["preview_hash"])
        model = load(self.root)
        self.assertTrue(approved(model, [feature])["valid"])
        self.assertFalse(task_authority(model, model.get(task_id), model.get(plan_id), "execution")["valid"])
        with self.assertRaises(ContractError): transition(self.root, actor, task_id, "start", "No hay autorización vigente")
        pending = approve_and_authorize(self.root, actor, plan_id, "Autorizo continuar bajo el nuevo método")
        v3_storage.apply(self.root, pending, pending["preview"]["preview_hash"])
        pending = transition(self.root, actor, task_id, "start", "Continúo el trabajo existente")
        v3_storage.apply(self.root, pending, pending["preview"]["preview_hash"])
        self.assertEqual(task_id, load(self.root).get(task_id).uid)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v3-migration-"); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "-C", str(self.root), "init", "-b", "codex/migration"], check=True, capture_output=True)
        p, c = v2_authoring.initialize(self.root, "Proyecto anterior")
        index = json.loads(c[".lks-sdd/project.json"]); index["plugin_version"] = "2.3.1"
        c[".lks-sdd/project.json"] = v2_contract.canonical(index)
        p = v2_storage.preview(self.root, c, sources={}, operation="fixture-v2")
        v2_storage.apply(self.root, c, p, p["preview_hash"])
        self.controls = {key: {"mode": "not-used", "reason": "Proyecto de documentación"} for key in ("sonar", "dependency-check")}

    def packet(self):
        return v3_migration.preview(self.root, "Responsable", "individual-brief", self.controls,
                                    "Confirmo configuración y conversión de esta revisión", target="main")

    def test_conversion_preserves_identity_originals_and_code(self):
        (self.root / "business.txt").write_bytes(b"unchanged application")
        old = v2_contract.load(self.root); expected = {e.meta["uid"] for e in old.elements.values()}
        packet = self.packet()
        self.assertEqual("2.0", json.loads(read_bytes(self.root, ".lks-sdd/project.json"))["schema_version"])
        v3_storage.apply(self.root, packet, packet["preview"]["preview_hash"])
        model = load(self.root).require_valid()
        self.assertTrue(expected <= set(model.elements))
        for entry in model.by_kind("migration")[0].data["inventory"]:
            self.assertEqual(entry["sha256"], sha(read_bytes(self.root, entry["original"])))
        self.assertEqual(b"unchanged application", (self.root / "business.txt").read_bytes())
        with self.assertRaises(ContractError): v2_contract.load(self.root)

    def test_unknown_method_is_diagnosed_without_writes(self):
        index = json.loads(read_bytes(self.root, ".lks-sdd/project.json")); index["method_version"] = "2.9.0"
        (self.root / ".lks-sdd/project.json").write_bytes(v2_contract.canonical(index))
        self.assertEqual("unsupported", v3_migration.diagnose(self.root)["status"])
        with self.assertRaises(ContractError): self.packet()

    def test_interruption_and_later_edit_are_protected(self):
        packet = self.packet()
        original = read_bytes(self.root, ".lks-sdd/project.json")
        with self.assertRaises(Exception):
            v3_storage.apply(self.root, packet, packet["preview"]["preview_hash"], interrupt_after=3)
        self.assertEqual(original, read_bytes(self.root, ".lks-sdd/project.json"))
        v3_storage.recover(self.root, packet["preview"]["preview_hash"], rollback=True)
        v2_contract.load(self.root).require_valid()

    def test_published_native_initializers_preserve_their_formats(self):
        fixtures = Path(__file__).parent/"fixtures/v3-migration"
        origins = json.loads((fixtures/"origins.json").read_bytes())["origins"]
        for origin in origins:
            with self.subTest(tag=origin["tag"]), tempfile.TemporaryDirectory(prefix="v3-published-") as temp:
                root = Path(temp)
                archive = fixtures/origin["fixture"]
                self.assertEqual(origin["fixture_sha256"], sha(archive.read_bytes()))
                with zipfile.ZipFile(archive) as z:
                    for name in z.namelist():
                        path = v2_contract.path_at(root, name, missing=True)
                        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(z.read(name))
                subprocess.run(["git", "-C", str(root), "init", "-b", "codex/migration"], check=True, capture_output=True)
                diagnostic = v3_migration.diagnose(root)
                self.assertEqual("compatible", diagnostic["status"], diagnostic)
                self.assertEqual(origin["method"], diagnostic["method"])
                packet = v3_migration.preview(root, "Responsable", "individual-brief", self.controls, "Valido la conversión concreta", target="main")
                v3_storage.apply(root, packet, packet["preview"]["preview_hash"])
                model = load(root).require_valid()
                self.assertEqual("3.0.0", model.project.data["method_version"])
                before = model.snapshot()
                self.assertEqual("previously-applied", v3_storage.apply(root, packet, packet["preview"]["preview_hash"])["status"])
                self.assertEqual(before, load(root).snapshot())


if __name__ == "__main__": unittest.main()
