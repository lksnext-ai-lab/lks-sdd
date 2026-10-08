"""Current public entrypoints, exact storage and portable migration on synthetic projects."""
from presentation_test_support import present, technical_solution
import base64
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from v2_contract import canonical, sha, ContractError
from v3_contract import element, load, DOCS
from v3_storage import apply, prepare, recover
from v3_cli import execute
from v3_packet import read as read_packet, save as save_packet, Spool


def configuration(owner="$owner", reviewer=None):
    return {"proposal_review_required": reviewer is not None, "task_review_required": reviewer is not None,
            "defaults": {"responsible": owner, "integration_validator": owner, "functional_validator": owner,
                         "reviewers": [{"member": reviewer, "required": True, "domains": ["functional", "technical"]}] if reviewer else []}}


class EfficiencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from build_dual_distribution import collect_development
        from dual_distribution import artifacts
        cls.bundle_temp = tempfile.TemporaryDirectory(prefix="v31-fixture-bundle-")
        cls.bundle = Path(cls.bundle_temp.name)
        packages = artifacts(collect_development(ROOT), "synthetic-development-fixture", "development-unreleased")
        raw = next(v for k, v in packages.items() if k.startswith("lks-sdd-setup-"))
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for entry in archive.infolist():
                target = cls.bundle/entry.filename
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(entry))

    @classmethod
    def tearDownClass(cls): cls.bundle_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v31-efficiency-"); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/"project"; self.root.mkdir()
        subprocess.run(["git", "-C", str(self.root), "init", "-b", "codex/fixture"], check=True, capture_output=True)
        self.controls = {key: {"mode": "not-used", "reason": "Explicit synthetic fixture decision"} for key in ("sonar", "dependency-check")}

    def init(self, profile="individual-brief", reviewer=None):
        data = {"name": "Synthetic", "actor_name": "Declared fixture actor", "profile": profile,
                "controls": self.controls, "statement": "Explicit synthetic configuration", "target": "main",
                "collaboration": configuration(reviewer=reviewer), "runtime_bundle": str(self.bundle)}
        if reviewer: data["members"] = [{"key": reviewer, "name": "Declared separate reviewer", "roles": ["reviewer"]}]
        packet = present(execute, "init", self.root, data)
        apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        return packet["summary"]["member"]

    def old(self, version="2.3.1"):
        import v2_authoring, v2_storage
        _, changes = v2_authoring.initialize(self.root, "Synthetic v2")
        index = json.loads(changes[".lks-sdd/project.json"]); index["plugin_version"] = version
        changes[".lks-sdd/project.json"] = canonical(index)
        packet = v2_storage.preview(self.root, changes, sources={}, operation="synthetic-v2")
        v2_storage.apply(self.root, changes, packet, packet["preview_hash"])

    def migration(self, **extra):
        return present(execute, "migration-preview", self.root, {"actor_name": "Declared current actor", "profile": "individual-brief",
                       "controls": self.controls, "statement": "Explicit conversion and runtime", "target": "main",
                       "collaboration": configuration(), "runtime_bundle": str(self.bundle), **extra})

    def test_native31_and_profiles_are_explicit_and_pinned(self):
        from runtime_doctor import check
        with self.assertRaises(ContractError): present(execute, "init", self.root, {"name": "X", "actor_name": "X", "profile": "individual-brief",
                                      "controls": self.controls, "statement": "X", "target": "main"})
        self.assertFalse((self.root/DOCS).exists())
        actor = self.init("independent-review", "$reviewer")
        self.assertEqual("3.1.0", load(self.root).require_valid().project.data["method_version"])
        self.assertEqual("valid", check(self.root)["status"])
        declared = element("requirement", "Literal", "Full literal requirement", files_ref={"business_locator": "api-contract"}, subject="Declared business subject")
        packet = present(execute, "author", self.root, {"actor": actor, "items": [declared]})
        apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        saved = load(self.root).require_valid().get(declared["meta"]["uid"])
        self.assertEqual(declared["meta"]["data"], saved.data)

    def test_existing30_without_lock_migrates_and_legacy_writes_are_blocked(self):
        from v3_authoring import initialize
        from runtime_doctor import check
        packet = present(initialize, self.root, "Old 3.0", "Existing declared actor", "individual-brief", self.controls,
                            "Explicit old fixture", target="main")
        actor = packet["summary"]["member"]
        apply(self.root, packet, packet["preview"]["preview_hash"])
        with self.assertRaisesRegex(ContractError, "needs-migration"):
            present(execute, "author", self.root, {"actor": actor, "items": []})
        readiness = present(execute, "readiness", self.root, {"actor": actor})
        self.assertEqual("blocked", readiness["status"])
        self.assertIn("needs-migration", readiness["causes"][0])
        packet = present(execute, "migration-preview", self.root, {"actor": actor, "collaboration": configuration(owner=actor),
                         "statement": "Confirm current configuration and pinned runtime", "runtime_bundle": str(self.bundle)})
        apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        self.assertEqual(actor, load(self.root).get(actor).uid)
        self.assertEqual("valid", check(self.root)["status"])
        self.assertEqual("current", present(execute, "migration-diagnose", self.root, {})["status"])

    def test_v2_compatibility_distributed_by31_migrates_without_claiming_a_verified_runtime(self):
        from v3_migration import diagnose
        from document_state import linked, PREFIX
        self.old(version="3.1.0")
        original = (self.root/".lks-sdd/project.json").read_bytes()
        diagnostic = diagnose(self.root)
        self.assertEqual("compatible", diagnostic["status"])
        self.assertEqual({"version": "3.1.0", "assurance": "declared-in-index"}, diagnostic["runtime"])
        packet = self.migration()
        apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        model = load(self.root).require_valid()
        self.assertEqual("3.1.0", model.project.data["method_version"])
        migration = model.by_kind("migration")[0]
        self.assertEqual(diagnostic["runtime"], migration.data["source"]["runtime"])
        self.assertEqual(original, linked(self.root, PREFIX+migration.data["original_state"]+"/tree/.lks-sdd/project.json", 64*1024*1024))

    def test_small_origin_parity_and_global_collision_are_not_bypassed(self):
        import v2_contract
        from v3_migration import source_model
        self.old()
        standard, normalized = source_model(self.root), source_model(self.root, normalize=True)
        self.assertEqual(set(standard.elements), set(normalized.elements))
        self.assertEqual({k: e.body for k, e in standard.elements.items()}, {k: e.body for k, e in normalized.elements.items()})
        raw = (self.root/standard.elements["PRJ-001"].path).read_bytes()
        (self.root/DOCS/"duplicate.md").write_bytes(raw)
        for mode in (False, True):
            with self.assertRaisesRegex(ContractError, "collision"): source_model(self.root, normalize=mode)

    def test_existing31_old_pinned_runtime_updates_and_rolls_back_capabilities(self):
        import importlib.util
        from v3_authoring import initialize
        from v31_review import configure
        from build_candidate_package import _package_integrity_bytes
        from dual_distribution import artifacts
        from runtime_doctor import check
        packet = present(initialize, self.root, "Previous", "Declared actor", "individual-brief", self.controls, "Previous configuration", target="main")
        actor = packet["summary"]["member"]; apply(self.root, packet, packet["preview"]["preview_hash"])
        packet = present(configure, self.root, actor, configuration(owner=actor), "Previous 3.1 configuration")
        apply(self.root, packet, packet["preview"]["preview_hash"])
        archive = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=zip", "v3.1.0"], capture_output=True, check=True)
        with zipfile.ZipFile(io.BytesIO(archive.stdout)) as opened:
            core = {e.filename: opened.read(e) for e in opened.infolist() if not e.is_dir()}
        core["package-integrity.json"] = _package_integrity_bytes(list(core.items()), "3.1.0", "published-fixture")
        packages = artifacts(core, "published-fixture", "regression")
        bundle = Path(self.temp.name)/"old-bundle"; bundle.mkdir()
        with zipfile.ZipFile(io.BytesIO(next(v for k, v in packages.items() if k.startswith("lks-sdd-setup-")))) as opened:
            for e in opened.infolist():
                target = bundle/e.filename; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(opened.read(e))
        spec = importlib.util.spec_from_file_location("fixture_install", ROOT/"distribution/install.py")
        installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
        installation = installer.plan(bundle, self.root, "copilot", contract_transition=("3.1", "3.1"))
        installer.apply(installation, installation["preview_hash"])
        self.assertEqual("valid", check(self.root)["status"])
        with self.assertRaisesRegex(ContractError, "needs-runtime-update"):
            present(execute, "author", self.root, {"actor": actor, "items": []})
        unchanged = load(self.root).snapshot()
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT/"scripts/lks_sdd.py"), "v3", "author", str(self.root), "--json"], capture_output=True, text=True)
        self.assertEqual(2, result.returncode, result.stderr)
        blocked = json.loads(result.stdout)
        self.assertIn("needs-runtime-update", blocked["error"])
        self.assertIn("read_only_cli", blocked)
        self.assertEqual([], blocked["writes"])
        self.assertEqual(unchanged, load(self.root).snapshot())
        packet = present(execute, "migration-preview", self.root, {"actor": actor, "collaboration": configuration(owner=actor),
                         "statement": "Update the pinned runtime capabilities", "runtime_bundle": str(self.bundle)})
        apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        self.assertEqual("current", present(execute, "migration-diagnose", self.root, {})["status"])
        self.assertEqual(actor, load(self.root).get(actor).uid)
        recover(self.root, packet["preview"]["preview_hash"], rollback=True, receipt=".lks-sdd/transactions.json")
        self.assertEqual("valid", check(self.root)["status"])
        with self.assertRaisesRegex(ContractError, "needs-runtime-update"):
            present(execute, "author", self.root, {"actor": actor, "items": []})

    def test_public_native31_complete_authorized_execution(self):
        actor = self.init()
        req = element("request", "Current request", "A full current governed request")
        prop = element("proposal", "Current proposal", "Literal full functional and technical proposal", request=req["meta"]["uid"],
                       part="joint", objective="Hello", included=["app.py"], excluded=[], behavior="Hello", solution=technical_solution(),
                       impact="One module", acceptance=["Hello"])
        req["meta"]["relations"]["proposal"] = [prop["meta"]["uid"]]
        def commit(action, data):
            packet = present(execute, action, self.root, {"actor": actor, **data})
            apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        commit("author", {"items": [req, prop]})
        commit("close-proposal", {"request": req["meta"]["uid"], "statement": "I validate this exact full proposal"})
        task = element("task", "Current task", "Implement and test the exact Hello result", request=req["meta"]["uid"], owner=actor,
                       scope=["app.py"], acceptance=["Hello"], tests=["hello"])
        plan = element("plan", "Current plan", "Implement and test this one task", request=req["meta"]["uid"])
        plan["meta"]["relations"]["tasks"] = [task["meta"]["uid"]]
        commit("author", {"items": [task, plan]})
        commit("authorize-plan", {"plan": plan["meta"]["uid"], "statement": "I approve and authorize this exact plan"})
        commit("start", {"task": task["meta"]["uid"], "reason": "Start explicitly authorized task"})
        (self.root/"app.py").write_bytes(b"def hello(): return 'Hello'\n")
        commit("implement", {"task": task["meta"]["uid"], "reason": "Exact implementation completed"})
        artifact = DOCS+"/evidence/test.txt"
        (self.root/artifact).parent.mkdir(parents=True, exist_ok=True); (self.root/artifact).write_bytes(b"hello passed")
        commit("evidence", {"task": task["meta"]["uid"], "tests": ["hello"], "outcome": "passed", "source": "automated",
                            "artifact": artifact, "explanation": "Recoverable synthetic test result"})
        commit("verify", {"task": task["meta"]["uid"], "reason": "Exact tested result"})
        commit("close", {"task": task["meta"]["uid"], "reason": "Verified current authorized task"})
        from v3_workflow import state
        model = load(self.root).require_valid()
        self.assertEqual("closed", state(model, model.get(task["meta"]["uid"])))

    def test_public_apply_checks_selected_request_and_allows_independent_new_scope(self):
        from v3_authoring import initialize, author
        packet = present(initialize, self.root, "Old scope", "Declared actor", "individual-brief", self.controls, "Old explicit configuration", target="main")
        actor = packet["summary"]["member"]; apply(self.root, packet, packet["preview"]["preview_hash"])
        old = element("request", "Old pending request", "Retain its old policy until explicitly adopted")
        shared = element("requirement", "Read-only old contract", "Preserve and read this existing normative dependency", request=old["meta"]["uid"])
        packet = author(self.root, actor, [old, shared]); apply(self.root, packet, packet["preview"]["preview_hash"])
        packet = present(execute, "configure-collaboration", self.root, {"actor": actor, "collaboration": configuration(owner=actor),
                         "statement": "Configure new work; preserve pending old scope", "runtime_bundle": str(self.bundle)})
        apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        item = element("receipt", "Existing scope", "Observed fact still requires its current request configuration", request=old["meta"]["uid"])
        packet = prepare(self.root, [item], "synthetic-old-request")
        with self.assertRaisesRegex(ContractError, "request configuration pending"):
            apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        self.assertNotIn(item["meta"]["uid"], load(self.root).elements)
        new = element("request", "Independent current scope", "Explicitly configure and preserve new work")
        packet = present(execute, "author", self.root, {"actor": actor, "items": [new]})
        apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        self.assertIn(new["meta"]["uid"], load(self.root).require_valid().elements)
        feature = element("feature", "Independent implementation contract", "Read the unchanged old dependency without operating its pending scope", request=new["meta"]["uid"])
        feature["meta"]["relations"]["requirements"] = [shared["meta"]["uid"]]
        packet = present(execute, "author", self.root, {"actor": actor, "items": [feature]})
        apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        self.assertEqual(shared["body"], load(self.root).require_valid().get(shared["meta"]["uid"]).body)

    def test_v2_direct31_recovery_originals_and_history_membership(self):
        import v2_contract
        from document_state import PREFIX, linked
        self.old()
        old = v2_contract.load(self.root); old.require_valid()
        original = {p: v2_contract.read_bytes(self.root, p) for p in old.hashes}
        packet = self.migration(packet_directory=str(Path(self.temp.name)/"portable"))
        self.assertEqual("2.0", json.loads((self.root/".lks-sdd/project.json").read_bytes())["schema_version"])
        newcomer = self.root/DOCS/"00-control/history/unexpected.txt"
        newcomer.parent.mkdir(parents=True, exist_ok=True); newcomer.write_bytes(b"later history")
        with self.assertRaisesRegex(ContractError, "membership"): apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        newcomer.unlink()
        with self.assertRaises(InterruptedError): apply(self.root, packet, packet["preview"]["preview_hash"], interrupt_after=3, current=True)
        self.assertTrue(load(self.root).errors)
        recover(self.root, packet["preview"]["preview_hash"])
        model = load(self.root).require_valid()
        self.assertEqual("3.1.0", model.project.data["method_version"])
        self.assertTrue({e.meta["uid"] for e in old.elements.values()} <= set(model.elements))
        state = model.by_kind("migration")[0].data["original_state"]
        for path, raw in original.items(): self.assertEqual(raw, linked(self.root, PREFIX+state+"/tree/"+path, 64*1024*1024))
        self.assertEqual("valid", present(execute, "validate", self.root, {})["status"])
        recover(self.root, packet["preview"]["preview_hash"], rollback=True, receipt=".lks-sdd/transactions.json")
        self.assertEqual("2.0", json.loads((self.root/".lks-sdd/project.json").read_bytes())["schema_version"])
        v2_contract.load(self.root).require_valid()

    def test_documentary_state_excludes_verification_only_code_but_keeps_evidence_and_guards(self):
        from document_state import manifest, export
        self.init()
        code = "unrelated.py"; proof = "reports/current.json"; asset = DOCS + "/assets/retained.bin"
        for path, raw in ((code, b"Verification-only code"), (proof, b"Exact explicit evidence"), (asset, b"Exact documentary resource")):
            destination = self.root/path; destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(raw)
        model = load(self.root).require_valid()
        event = element("receipt", "Observed state", "Keep the complete documentary state and verification inputs.")
        packet = prepare(self.root, [event], "synthetic-verification-inputs", sources={code: sha((self.root/code).read_bytes()), proof: sha((self.root/proof).read_bytes())},
                         state_sources={*model.hashes, proof})
        identity = packet["summary"]["previous_state"]
        self.assertIn(code, packet["preview"]["sources"])
        (self.root/code).write_bytes(b"Changed after exact preview")
        with self.assertRaises(ContractError): apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        self.assertNotIn(event["meta"]["uid"], load(self.root).require_valid().elements)
        (self.root/code).write_bytes(b"Verification-only code")
        apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        files = manifest(self.root, identity)["files"]
        self.assertNotIn(code, files)
        self.assertIn(proof, files); self.assertIn(asset, files)
        output = Path(self.temp.name)/"documentary-export"
        export(self.root, identity, output)
        self.assertEqual(b"Exact explicit evidence", (output/proof).read_bytes())
        self.assertEqual(b"Exact documentary resource", (output/asset).read_bytes())
        self.assertFalse((output/code).exists())

    def test_operational_subjects_share_exact_inventory_and_normative_hashes(self):
        from v3_git import subject
        from content_store import object_path
        actor = self.init()
        (self.root/"stable.py").write_bytes(b"literal code")
        observed = subject(self.root, ["stable.py"])
        events = [element("checkpoint", "Observed", "Distinct human observation " + str(i), actor={"member": actor},
                          subject=observed, dependencies={"synthetic": {"artifact": observed, "basis": "kept"}}) for i in range(6)]
        packet = prepare(self.root, events, "synthetic-observations")
        apply(self.root, packet, packet["preview"]["preview_hash"], current=True)
        model = load(self.root).require_valid()
        values = model.by_kind("checkpoint")
        refs = {v.meta["data"]["subject"]["files_ref"]["sha256"] for v in values}
        self.assertEqual(1, len(refs))
        for event in values:
            self.assertEqual(observed, event.data["subject"])
            self.assertEqual(observed, event.data["dependencies"]["synthetic"]["artifact"])
            self.assertNotIn("files", event.meta["data"]["subject"])
            self.assertEqual(event.digest(), sha(canonical(event.normative())))
        ref = values[0].meta["data"]["subject"]["files_ref"]
        (self.root/object_path(ref)).write_bytes(b"altered")
        with self.assertRaises(ContractError): load(self.root).require_valid()

    def test_portable_packet_over_old_input_limit_exact_states_moves_and_deletions(self):
        from document_state import export, manifest
        self.init()
        folder = Path(self.temp.name)/"prepared"
        changes = Spool(folder)
        raw = b"binary fixture\x00" * (1300000)  # three payload entries exceed 64 MiB in legacy base64
        for i in range(3): changes[DOCS+f"/assets/resource-{i}.bin"] = raw
        packet = prepare(self.root, [], "synthetic-resources", changes=changes)
        self.assertGreater(sum(len(base64.b64encode(changes[p])) for p in changes if p.endswith(".bin")), 64*1024*1024)
        output = Path(self.temp.name)/"relocated.json"
        save_packet(packet, output)
        shutil.rmtree(folder)  # fixture-owned staging; the portable copy must be sufficient
        restored = read_packet(output)
        apply(self.root, restored, restored["preview"]["preview_hash"])
        old_state = prepare(self.root, [element("receipt", "Before move", "Exact observation")], "synthetic-before-move")
        identity = old_state["summary"]["previous_state"]
        apply(self.root, old_state, old_state["preview"]["preview_hash"])
        move = {DOCS+"/assets/resource-0.bin": None, DOCS+"/assets/moved.bin": raw,
                DOCS+"/assets/resource-1.bin": b"modified", DOCS+"/assets/resource-2.bin": None}
        changed = prepare(self.root, [element("receipt", "Move", "Modified, moved and deleted resources")], "synthetic-move", changes=move)
        apply(self.root, changed, changed["preview"]["preview_hash"])
        destination = Path(self.temp.name)/"exported"
        export(self.root, identity, destination)
        for path, ref in manifest(self.root, identity)["files"].items():
            self.assertEqual(ref["sha256"], sha((destination/path).read_bytes()))
        self.assertFalse((destination/DOCS/"assets/moved.bin").exists())
        self.assertEqual(1, len([p for p in (self.root/".lks-sdd/objects/sha256").iterdir() if p.stat().st_size == len(raw)]))

    def test_large_v2_source_uses_same_validator_and_retains_old_history(self):
        import v2_contract
        from v3_migration import source_model
        from content_store import inventory
        self.old()
        files = {"src/" + "stable-component-"*4 + f"{i:05}.txt": sha(str(i).encode()) for i in range(5000)}
        originals = {}
        for i in range(60):
            value = v2_contract.make_element(f"CKPT-{i+100:03}", "checkpoint", "Observed", "Literal actor, authorization and evidence",
                                            state="active", nature="fact", actor="historical-human", authorization="historical-authorization", evidence_ids=["evidence-kept"], files=files)
            path = DOCS+f"/04-delivery/checkpoints/{i}.md"
            raw = v2_contract.render_document("checkpoint", "Observed", [value])
            (self.root/path).parent.mkdir(parents=True, exist_ok=True); (self.root/path).write_bytes(raw)
            originals[value["meta"]["uid"]] = (path, raw)
        with self.assertRaisesRegex(ContractError, "byte budget"): v2_contract.load(self.root)
        for i in range(10005):
            path = self.root/DOCS/f"00-control/history/old/{i}.txt"
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b"preserved old history")
        normalized = source_model(self.root, normalize=True); normalized.require_valid()
        self.assertEqual(60, len(normalized.by_kind("checkpoint")))
        packet = self.migration(packet_directory=str(Path(self.temp.name)/"migration"))
        self.assertLess((packet.base/"packet.json").stat().st_size, 64*1024*1024)
        self.assertFalse(any("/history/old/" in p for p in packet["payload"]))
        apply(self.root, packet, packet["preview"]["preview_hash"])
        model = load(self.root).require_valid()
        self.assertLess(sum((self.root/p).stat().st_size for p in __import__("v3_contract").document_paths(self.root)), 1024*1024)
        for event in model.by_kind("checkpoint"):
            self.assertEqual(files, inventory(self.root, event.data, "files"))
            self.assertEqual("historical-human", event.data["actor"])
            self.assertEqual("historical-authorization", event.data["authorization"])
            self.assertEqual(["evidence-kept"], event.data["evidence_ids"])
            self.assertEqual(originals[event.uid][1], v2_contract.read_bytes(self.root, event.data["legacy"]["original"], limit=4*1024*1024))
        self.assertEqual(10005, len(list((self.root/DOCS/"00-control/history/old").iterdir())))


class StorageBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v31-boundary-"); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/"project"; self.root.mkdir()

    def test_migration_normalization_keeps_irreducible_markdown_budget(self):
        import v2_authoring, v2_contract
        from v3_migration import source_model
        _, changes = v2_authoring.initialize(self.root, "Synthetic irreducible source")
        for name, raw in changes.items():
            path = self.root/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        with self.assertRaisesRegex(ContractError, "needs-migration"):
            execute("author", self.root, {"actor": "unconfirmed", "items": []})
        for i in range(9):
            path = self.root/DOCS/f"01-context/large-{i}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(v2_contract.render_document("context", "Literal source", [], preamble="x"*(3900*1024)))
        before = {p.relative_to(self.root).as_posix(): sha(p.read_bytes()) for p in self.root.rglob("*") if p.is_file()}
        for normalize in (False, True):
            with self.assertRaisesRegex(ContractError, "Document byte budget exceeded"):
                source_model(self.root, normalize=normalize)
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): sha(p.read_bytes()) for p in self.root.rglob("*") if p.is_file()})

    def test_format_detection_without_index_reads_only_the_header(self):
        from v3_cli import is_v3
        path = self.root/DOCS/"source.md"; path.parent.mkdir(parents=True)
        path.write_bytes(b'schema_version: "3.1"\n' + b"x"*4096)
        class Header(io.BytesIO):
            def read(stream, amount=-1):
                self.assertEqual(256, amount)
                return super().read(amount)
        raw = path.read_bytes()
        with patch.object(Path, "read_bytes", side_effect=FileNotFoundError), patch.object(Path, "open", return_value=Header(raw)):
            self.assertTrue(is_v3(self.root))

    def test_migration_catalog_rejects_non_object_values_before_accepting_sources(self):
        from content_store import prepare_object
        from v2_storage import write_one
        from v3_contract import Model, Element
        from v3_inventories import resolve
        for raw in (b"[]", b'{"format":"lks-sdd-migration-inventory/1","entries":"invalid"}'):
            changes = {}; ref = prepare_object(self.root, raw, changes)
            for path, data in changes.items(): write_one(self.root, path, data)
            item = element("migration", "Synthetic malformed catalog", "Invalid technical data grants no authority.", inventory_ref=ref, source={"snapshot": sha(b"empty")})
            model = Model(self.root)
            with self.assertRaises(ContractError): resolve(model, Element(item["meta"], item["body"], DOCS+"/invalid.md"), {})
            self.assertEqual({}, model.hashes)

    def test_exact_state_parts_share_stable_metadata_and_detect_tampering(self):
        import document_state
        from content_store import object_path
        from v2_storage import write_one
        paths = [DOCS+f"/assets/stable-{i}.txt" for i in range(130)]
        for name in paths: write_one(self.root, name, ("Literal " + name).encode())
        def preserve():
            changes = {}
            identity = document_state.prepare(self.root, {p: sha((self.root/p).read_bytes()) for p in paths}, changes)
            for name, raw in changes.items(): write_one(self.root, name, raw)
            return identity, document_state.manifest(self.root, identity)
        first, before = preserve()
        write_one(self.root, paths[0], b"Literal changed resource")
        second, after = preserve()
        self.assertNotEqual(first, second)
        changed = [key for key in before["parts"] if before["parts"][key] != after["parts"][key]]
        self.assertEqual([document_state.bucket(paths[0])], changed)
        self.assertEqual(("Literal " + paths[0]).encode(), document_state.linked(self.root, document_state.PREFIX+first+"/tree/"+paths[0], 1000))
        part = before["parts"][document_state.bucket(paths[0])]
        (self.root/object_path(part)).write_bytes(b"corrupt part")
        with self.assertRaises(ContractError): document_state.manifest(self.root, first)
        with self.assertRaises(ContractError): document_state.export(self.root, first, Path(self.temp.name)/"export")
        self.assertFalse((Path(self.temp.name)/"export").exists())

    def test_state_manifest_rejects_malformed_schema_and_preserves_inline_compatibility(self):
        import document_state
        from content_store import prepare_object
        from v2_storage import write_one
        from v2_contract import fingerprint
        source = DOCS + "/assets/original.txt"
        changes = {}
        ref = prepare_object(self.root, b"Exact original", changes)
        for name, raw in changes.items(): write_one(self.root, name, raw)
        entries = {source: ref}; identity = fingerprint(entries)
        target = document_state.name(identity)
        value = {"format": document_state.FORMAT, "identity": identity, "files": entries}
        write_one(self.root, target, canonical(value))
        self.assertEqual(entries, document_state.manifest(self.root, identity)["files"])
        self.assertEqual(b"Exact original", document_state.linked(self.root, document_state.PREFIX + identity + "/tree/" + source, 100))
        for raw in (b"[]", b"{", canonical({**value, "parts": {}}), canonical({**value, "unknown": "unbound"}), canonical({**value, "files": []})):
            with self.subTest(raw=raw):
                write_one(self.root, target, raw)
                with self.assertRaises(ContractError): document_state.manifest(self.root, identity)

    def test_portable_payload_rejects_alteration_and_aggregate_budget_before_read(self):
        from content_store import reference
        from v3_packet import Packet, Payload, FORMAT, MAX_BYTES, LIMIT
        folder = Path(self.temp.name)/"packet"; values = Spool(folder)
        values[DOCS+"/assets/one.bin"] = b"complete literal bytes"
        packet = Packet({"format": FORMAT, "object_directory": "objects", "payload": values.refs}, folder)
        ref = values.refs[DOCS+"/assets/one.bin"]
        (folder/"objects"/ref["sha256"]).write_bytes(b"other literal bytes")
        with self.assertRaises(ContractError): Payload(packet)[DOCS+"/assets/one.bin"]
        packet["payload"] = {f"asset-{i}.bin": {"format": "lks-sdd-object/1", "sha256": sha(str(i).encode()), "bytes": LIMIT}
                             for i in range(MAX_BYTES//LIMIT+1)}
        with patch("v3_packet.payload_bytes", side_effect=AssertionError("must not read beyond budget")):
            with self.assertRaisesRegex(ContractError, "budget"): Payload(packet)

    def test_fresh_inventory_rejects_replaced_source(self):
        from source_inventory import documents, read
        from v2_storage import write_one
        name = DOCS+"/stable.txt"
        write_one(self.root, name, b"same bytes")
        observed = documents(self.root)[name]
        (self.root/name).unlink(); write_one(self.root, name, b"same bytes")
        with self.assertRaises(ContractError): read(observed)
        self.assertEqual(b"same bytes", read(documents(self.root)[name]))

    def test_legacy_public_initialization_cannot_create_old_workflow(self):
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT/"skills/lks-sdd-define/scripts/init_project.py"),
                                 str(self.root), "--project-id", "synthetic", "--json"], capture_output=True, text=True)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("blocked", json.loads(result.stdout)["status"])
        self.assertEqual([], list(self.root.iterdir()))
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT/"scripts/v2_cli.py"),
                                 "catalog", str(self.root), "--export", "--json"], capture_output=True, text=True)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("blocked", json.loads(result.stdout)["status"])
        self.assertEqual([], list(self.root.iterdir()))

    def test_legacy_action_root_aliases_cannot_dispatch_into_v3(self):
        index = self.root/".lks-sdd/project.json"
        index.parent.mkdir()
        for schema in ("3.0", "3.1"):
            original = canonical({"schema_version": schema})
            index.write_bytes(original)
            for command in ("planning", "tracking", "continuity", "tasks", "work"):
                for arguments in (["start", str(self.root)], [str(self.root), "start"]):
                    with self.subTest(schema=schema, command=command, arguments=arguments):
                        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT/"scripts/lks_sdd.py"), command, *arguments, "--json"], capture_output=True, text=True)
                        self.assertEqual(2, result.returncode, result.stderr)
                        self.assertEqual([], json.loads(result.stdout)["writes"])
                        self.assertIn("v3", json.loads(result.stdout)["error"])
                        self.assertEqual(original, index.read_bytes())
                        self.assertEqual([index], [p for p in self.root.rglob("*") if p.is_file()])

    def test_global_approval_checks_all_content_without_quadratic_digest_work(self):
        from v3_contract import Model, Element, fingerprint
        from v3_approval import descriptor, approved
        model = Model(self.root)
        for i in range(180):
            item = element("requirement", str(i), "Complete global requirement " + str(i))
            entry = Element(item["meta"], item["body"], DOCS+f"/global-{i}.md")
            model.elements[entry.uid] = entry
        expected = {e.uid: e.digest() for e in model.elements.values()}
        self.assertEqual({"units": expected, "digest": fingerprint(expected)}, descriptor(model, list(expected)))
        item = element("decision", "Exact approval", "Human statement kept", purpose="plan", outcome="approved",
                       descriptor={"units": expected, "digest": fingerprint(expected)})
        decision = Element(item["meta"], item["body"], DOCS+"/approval.md")
        model.elements[decision.uid] = decision
        original = Element.digest
        calls = []
        def measured(entry): calls.append(entry.uid); return original(entry)
        with patch.object(Element, "digest", measured): result = approved(model, list(expected), "plan")
        self.assertTrue(result["valid"])
        self.assertEqual(set(expected), set(result["covered"]))
        self.assertLess(len(calls), len(expected)*5)
        model.elements[next(iter(expected))].body += " Changed obligation."
        self.assertFalse(approved(model, list(expected), "plan")["valid"])


if __name__ == "__main__": unittest.main()
