"""Behavioral acceptance scenarios and adversarial conversion/distribution checks."""
from __future__ import annotations
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import v5_core as core
import v5_migration as migration
import v5_distribution as distribution
from v5_legacy import Reader
from v5_results import import_result, wait_file
from test_v5_core import fixture, put, update, meta, FACTS

ROOT = Path(__file__).resolve().parents[1]


def source(root, version="3.1"):
    def element(uid, ident, kind, body, **extra):
        value = {"uid": uid, "id": ident, "kind": kind, "state": "ready", "data": {}, **extra}
        return "<!-- lks-sdd: " + json.dumps(value) + " -->\n" + body + "\n<!-- /lks-sdd -->\n"
    put(root, "docs/lks-sdd/02-specification/features/acceso/specification.md",
        '---\nschema_version: "' + version + '"\n---\n\n' + element("u-1", "FR-1", "requirement", "El permiso limita la consulta."))
    put(root, "docs/lks-sdd/task.md", '---\nschema_version: "' + version + '"\n---\n\n' +
        element("t-1", "TASK-1", "task", "Conservar aislamiento por empresa.",
            relations={"requirements": ["u-1"]}, data={"owner": "test", "health": "needs-reverification"}))
    put(root, ".lks-sdd/project.json", json.dumps({"schema_version": version}))
    put(root, ".lks-sdd/runtime/old/unneeded.py", "raise RuntimeError('old runtime must not execute')")
    put(root, "AGENTS.md", "Keep application policy.\n<!-- LKS-SDD:BEGIN -->\nOld managed instructions\n<!-- LKS-SDD:END -->\n")
    put(root, "app.py", "value = 1\n")


class ScenarioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lks-v5-scenario-")
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        if os.name == "nt" and self.root.exists():
            import shutil
            # Exactly the TemporaryDirectory owned by this test, with the Windows
            # extended prefix needed to reach its intentionally long descendants.
            target = Path("\\\\?\\" + str(self.root))
            if not str(self.root).startswith(str(Path(tempfile.gettempdir()).resolve())):
                raise ValueError("Unexpected test cleanup boundary")
            shutil.rmtree(target)
        self.temp.cleanup()

    def edit(self, name, fn):
        data, body, _ = core.current(self.root, name)
        fn(data)
        put(self.root, name, core.document(data, body))

    def test_small_change_and_lot_have_one_plan_each(self):
        fixture(self.root)
        for task in ("T-001", "T-002", "T-003"):
            if task != "T-001": fixture(self.root, task)
            core.check_task(self.root, task, "C1")
            core.close(self.root, task, {}, FACTS)
            self.assertEqual(len(list((self.root / "docs/sdd/tareas" / task).glob("*"))), 2)
        self.assertEqual(core.validate(self.root)["status"], "passed")

    def test_complex_task_waits_for_children(self):
        fixture(self.root, "parent")
        core.prepare(self.root, "child", "Part", "Do part", ["observable"], ["acceso"], "test", parent="parent")
        core.authorize(self.root, "parent", "test", "whole lot", ["implement", "consolidate"])
        core.authorize(self.root, "child", "test", "whole lot", ["implement", "consolidate"])
        self.edit(core.task_path("child", "plan"), lambda p: p.update(no_checks_reason="Documentary clarification"))
        core.check_task(self.root, "parent", "C1")
        with self.assertRaisesRegex(ValueError, "Subtask"):
            core.close(self.root, "parent", {}, FACTS)
        core.close(self.root, "child", {}, FACTS)
        core.close(self.root, "parent", {}, FACTS)

    def test_shared_permission_change_invalidates_declared_check(self):
        fixture(self.root)
        self.edit(core.task_path("T-001", "plan"), lambda p: p["checks"]["C1"]["inputs"].append("docs/sdd/especificaciones/*.md"))
        core.check_task(self.root, "T-001", "C1")
        put(self.root, core.unit_path("acceso"), update(self.root)["acceso"])
        self.assertEqual(core.check_task(self.root, "T-001", "C1")["status"], "passed")

    def test_recovery_distinguishes_own_consolidation_from_changed_test_input(self):
        fixture(self.root)
        self.edit(core.task_path("T-001", "plan"), lambda p: p["checks"]["C1"]["inputs"].append("docs/sdd/especificaciones/*.md"))
        core.check_task(self.root, "T-001", "C1")
        with self.assertRaises(InterruptedError): core.close(self.root, "T-001", update(self.root), FACTS, interrupt_after=1)
        self.assertEqual(core.resume(self.root)["status"], "applied")

    def test_outage_is_localized_and_wait_is_bounded(self):
        fixture(self.root)
        self.edit(core.task_path("T-001", "plan"), lambda p: p["checks"]["C1"].update(
            argv=[sys.executable, "-c", "import time;time.sleep(1)"], timeout=0.01))
        self.assertEqual(core.check_task(self.root, "T-001", "C1")["status"], "blocked")
        self.assertEqual(core.status(self.root, "T-001")["state"], "en-curso")
        self.assertEqual(wait_file(self.root, "not-arrived.xml", timeout=0.01, interval=0.1)["status"], "blocked")

    def test_deployment_uses_policy_without_running_application_suite(self):
        fixture(self.root)
        core.check_task(self.root, "T-001", "C1")
        result_before = core.current(self.root, core.task_path("T-001", "plan"))[0]["results"]
        core.delivery(self.root, "T-001", {"deployment": "not-run"})
        self.assertEqual(core.current(self.root, core.task_path("T-001", "plan"))[0]["results"], result_before)
        put(self.root, core.unit_path("proyecto"), core.document(meta("unit", "proyecto", policy={"deployment_checks": ["security"]}), "Policy"))
        with self.assertRaisesRegex(ValueError, "deployment check"):
            core.delivery(self.root, "T-001", {"deployment": "observed environment"})

    def external(self):
        fixture(self.root)
        self.edit(core.task_path("T-001", "plan"), lambda p: p.update(checks={"ci": {
            "provider": "fixture-ci", "tool_version": "1", "environment": "isolated", "inputs": ["product.py"],
            "result_format": "junit"}}))
        task = core.current(self.root, core.task_path("T-001", "tarea"))[0]
        check = core.current(self.root, core.task_path("T-001", "plan"))[0]["checks"]["ci"]
        return core.input_fingerprint(self.root, core.task_path("T-001", "tarea"), task, check)

    def test_native_external_results_require_inputs_and_provenance(self):
        fingerprint = self.external()
        put(self.root, "report.xml", '<testsuite><testcase name="C1"/></testsuite>')
        with self.assertRaises(core.Conflict):
            import_result(self.root, "T-001", "ci", "report.xml", inputs="wrong", provider="fixture-ci", run_id="1")
        import_result(self.root, "T-001", "ci", "report.xml", inputs=fingerprint, provider="fixture-ci", run_id="1")
        core.close(self.root, "T-001", {}, FACTS)

    def test_empty_skipped_and_failed_reports_are_not_success(self):
        fingerprint = self.external()
        put(self.root, "report.xml", "<testsuite/>")
        with self.assertRaises(ValueError):
            import_result(self.root, "T-001", "ci", "report.xml", inputs=fingerprint, provider="fixture-ci", run_id="1")
        for element, expected in (("skipped", "blocked"), ("failure", "failed")):
            put(self.root, "report.xml", f'<testsuite><testcase name="C1"><{element}/></testcase></testsuite>')
            import_result(self.root, "T-001", "ci", "report.xml", inputs=fingerprint, provider="fixture-ci", run_id="1")
            self.assertEqual(core.current(self.root, core.task_path("T-001", "plan"))[0]["results"]["ci"]["status"], expected)

    def test_full_conversion_removes_legacy_runtime_and_preserves_policy(self):
        source(self.root)
        preview = migration.preview(self.root)
        migration.run(self.root, preview["preview_sha256"])
        self.assertFalse((self.root / "docs/lks-sdd").exists())
        self.assertFalse((self.root / ".lks-sdd/runtime/old").exists())
        self.assertIn("Keep application policy.", (self.root / "AGENTS.md").read_text())
        self.assertEqual((self.root / "app.py").read_text(), "value = 1\n")
        self.assertEqual(core.status(self.root, "task-1")["state"], "preparado")
        self.assertEqual(distribution.doctor(self.root)["status"], "passed")
        lock = json.loads((self.root / ".lks-sdd/distribution-lock.json").read_bytes())
        cli = self.root / lock["runtime"] / "scripts/lks_sdd.py"
        run = subprocess.run([sys.executable, "-B", str(cli), "validate", "--root", str(self.root)], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_conversion_interruption_resumes_and_removes_all_staging(self):
        source(self.root)
        preview = migration.preview(self.root)
        self.assertFalse(preview["reversible"])
        self.assertFalse((self.root / migration.WORK / "recovery.zip").exists())
        with self.assertRaises(InterruptedError):
            migration.run(self.root, preview["preview_sha256"], interrupt_after=2)
        with self.assertRaises(core.Conflict): migration.discard_preview(self.root)
        self.assertEqual(migration.run(self.root, resume=True)["status"], "passed")
        self.assertFalse((self.root / migration.WORK).exists())
        self.assertFalse((self.root / migration.JOURNAL).exists())
        self.assertFalse((self.root / "docs/lks-sdd").exists())
        self.assertEqual(migration.run(self.root, resume=True)["status"], "unchanged")

    def test_irreversible_migration_has_no_rollback_entrypoint(self):
        import inspect
        self.assertNotIn("rollback", inspect.signature(migration.run).parameters)
        run = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/lks_sdd.py"), "--help"], capture_output=True)
        self.assertNotIn(b"migration-rollback", run.stdout)

    def test_changed_source_new_source_and_modified_preview_block_cutover(self):
        source(self.root)
        preview = migration.preview(self.root)
        put(self.root, "docs/lks-sdd/new.md", "foreign")
        with self.assertRaises(core.Conflict): migration.run(self.root, preview["preview_sha256"])
        (self.root / "docs/lks-sdd/new.md").unlink()
        put(self.root, "docs/lks-sdd/task.md", "foreign edit")
        with self.assertRaises(core.Conflict): migration.run(self.root, preview["preview_sha256"])
        self.assertEqual(core.read(self.root, "docs/lks-sdd/task.md"), b"foreign edit")

    def test_staged_output_changed_blocks_before_write(self):
        source(self.root)
        preview = migration.preview(self.root)
        payload = migration.load_preview(self.root)
        staged = next(item["staged"] for item in payload["entries"].values() if item["staged"])
        put(self.root, migration.WORK + "/" + staged, "changed")
        with self.assertRaises(core.Conflict): migration.run(self.root, preview["preview_sha256"])
        self.assertTrue((self.root / "docs/lks-sdd/task.md").exists())

    def test_unknown_format_and_duplicate_identity_block_conversion(self):
        source(self.root, "9.0")
        with self.assertRaises(ValueError): Reader(self.root)
        source(self.root)
        put(self.root, "docs/lks-sdd/copy.md", core.read(self.root, "docs/lks-sdd/task.md"))
        with self.assertRaisesRegex(ValueError, "Duplicate"): Reader(self.root)

    def test_short_root_inventory_includes_deep_history_and_preserves_new_file(self):
        source(self.root)
        name = "docs/lks-sdd/00-control/history/" + "/".join(["deep-" + "x" * 35] * 5) + "/source.bin"
        put(self.root, name, b"deep source")
        preview = migration.preview(self.root)
        payload = migration.load_preview(self.root)
        self.assertIn(name, payload["source_inventory"])
        put(self.root, "docs/lks-sdd/new-foreign.md", "keep concurrent addition")
        with self.assertRaises(core.Conflict): migration.run(self.root, preview["preview_sha256"])
        self.assertEqual(core.read(self.root, name), b"deep source")
        self.assertEqual(core.read(self.root, "docs/lks-sdd/new-foreign.md"), b"keep concurrent addition")
        (self.root / "docs/lks-sdd/new-foreign.md").unlink()
        migration.run(self.root, preview["preview_sha256"])
        self.assertIsNone(core.read(self.root, name))

    def test_reserved_windows_device_paths_rejected(self):
        for name in ("NUL", "docs/CON.md", ".sdd-work/tmp/COM1.log"):
            with self.assertRaises(ValueError): core.path_at(self.root, name)

    def test_unknown_local_metadata_is_not_silently_removed(self):
        source(self.root)
        put(self.root, ".lks-sdd/user-notes.txt", "owned by a person")
        with self.assertRaisesRegex(ValueError, "ownership"):
            migration.preview(self.root)
        self.assertEqual(core.read(self.root, ".lks-sdd/user-notes.txt"), b"owned by a person")

    def test_published_v2_native_fixture_direct_reader(self):
        with zipfile.ZipFile(ROOT / "tests/fixtures/v3-migration/v2.0.0.zip") as archive:
            for name in archive.namelist():
                if not name.endswith("/"): put(self.root, name, archive.read(name))
        reader = Reader(self.root)
        output, _, counts = migration.convert(reader)
        self.assertTrue(output)
        self.assertIn("2.0", reader.schemas)

    def test_native_15_calculator_tables_and_active_task_are_converted_directly(self):
        case = json.loads((ROOT / "tests/fixtures/calculator-handoff-1.5.json").read_bytes())
        documents = {}
        for table in case["tables"]:
            documents.setdefault(table["path"], []).append(table["header"] + "\n" +
                "|" + "|".join("---" for _ in table["rows"][0]) + "|\n" +
                "\n".join("| " + " | ".join(row) + " |" for row in table["rows"]) + "\n\n")
        for name, parts in documents.items(): put(self.root, "docs/lks-sdd/" + name, "\n".join(parts))
        put(self.root, "docs/lks-sdd/tasks.md", "| ID | State | Owner | Requirement | Scope |\n|---|---|---|---|---|\n| TASK-001 | ready | team | FR-001 | Preserve amounts |\n")
        reader = Reader(self.root)
        output, _, counts = migration.convert(reader)
        self.assertGreater(counts["source_elements"], 20)
        self.assertIn(core.task_path("task-001", "tarea"), output)
        task = core.parse(output[core.task_path("task-001", "tarea")])[0]
        self.assertEqual(task["owner"], "team")
        self.assertTrue(task["units"])

    def test_direct_15_prose_and_30_structured_readers(self):
        source(self.root, "3.0")
        self.assertIn("3.0", Reader(self.root).schemas)
        (self.root / ".lks-sdd/project.json").unlink()
        for p in (self.root / "docs/lks-sdd").rglob("*.md"): p.unlink()
        put(self.root, "docs/lks-sdd/business.md", "# Existing system\n| TASK-1 | pending approval |\nKeep authorization explicit.")
        output, _, _ = migration.convert(Reader(self.root))
        self.assertTrue(any(b"Keep authorization explicit" in raw for raw in output.values()))

    def test_content_store_integrity_and_hostile_pack(self):
        source(self.root)
        reader = Reader(self.root)
        raw = b'{"value":1}'
        ident = core.digest(raw)
        put(self.root, ".lks-sdd/objects/sha256/" + ident, raw)
        reference = {"format": "lks-sdd-object/1", "sha256": ident, "bytes": len(raw)}
        self.assertEqual(reader.payload(reference), raw)
        put(self.root, ".lks-sdd/objects/sha256/" + ident, b"corrupt")
        with self.assertRaises(ValueError): reader.payload(reference)
        (self.root / (".lks-sdd/objects/sha256/" + ident)).unlink()
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive: archive.writestr("../outside", raw)
        put(self.root, ".lks-sdd/objects/packs/bad.zip", stream.getvalue())
        with self.assertRaises(ValueError): Reader(self.root).payload(reference)

    def test_discard_unapplied_preview_preserves_sources(self):
        source(self.root)
        original = core.read(self.root, "docs/lks-sdd/task.md")
        migration.preview(self.root)
        migration.discard_preview(self.root)
        self.assertFalse((self.root / migration.WORK).exists())
        self.assertEqual(core.read(self.root, "docs/lks-sdd/task.md"), original)

    def test_both_host_bundles_reproducible_and_no_legacy_imports(self):
        core_files = distribution.core_files(ROOT)
        a = distribution.artifacts(core_files, "fixture", "candidate")
        self.assertEqual(a, distribution.artifacts(core_files, "fixture", "candidate"))
        for name in ("lks-sdd-plugin-v5.0.0.zip", "lks-sdd-copilot-plugin-v5.0.0.zip"):
            with zipfile.ZipFile(io.BytesIO(a[name])) as archive:
                names = archive.namelist()
                self.assertEqual(len([n for n in names if n.startswith("lks-sdd/skills/") and n.endswith("SKILL.md")]), 6)
                self.assertFalse(any("/scripts/v3" in n for n in names))
                for entry in names: put(self.root, entry, archive.read(entry))
            cli = self.root / ("lks-sdd/core/scripts/lks_sdd.py" if "copilot-plugin" in name else "lks-sdd/scripts/lks_sdd.py")
            run = subprocess.run([sys.executable, "-B", str(cli), "--help"], capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
        from validate_copilot_package import validate
        from validate_release_artifacts import _validate_bundle
        self.assertEqual(validate(a["lks-sdd-copilot-plugin-v5.0.0.zip"])["status"], "valid")
        _validate_bundle(a["lks-sdd-plugin-v5.0.0.zip"], "plugin")
        _validate_bundle(a["lks-sdd-marketplace-v5.0.0.zip"], "marketplace")
        # A native Git distribution must retain the ZIP's exact integrity bytes
        # even when the consuming Windows checkout enables CRLF conversion.
        from validate_copilot_package import unpack
        native = {n[len("lks-sdd/"):]: raw for n, raw in
                  unpack(a["lks-sdd-copilot-plugin-v5.0.0.zip"]).items()}
        with tempfile.TemporaryDirectory(prefix="lks-v5-native-") as native_temporary:
            native_root = Path(native_temporary).resolve()
            repository, clone = native_root / "source", native_root / "clone"
            for name, raw in native.items(): put(repository, name, raw)
            def git(*args, cwd=repository):
                return subprocess.run(["git", *args], cwd=cwd, check=True,
                                      capture_output=True, timeout=30).stdout
            git("init")
            git("-c", "core.autocrlf=false", "add", ".")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "-m", "Native fixture")
            git("clone", "--local", "--config", "core.autocrlf=true",
                str(repository), str(clone))
            cloned = {name: (clone / name).read_bytes() for name in native}
            self.assertEqual({n: core.digest(b) for n, b in cloned.items()},
                             {n: core.digest(b) for n, b in native.items()})
            self.assertEqual(validate(distribution.zip_bytes(
                {"lks-sdd/" + name: raw for name, raw in cloned.items()}))["status"], "valid")

    def test_runtime_integrity_detects_foreign_edit(self):
        files = distribution.consumer_files(distribution.core_files(ROOT))
        for name, raw in files.items(): put(self.root, name, raw)
        distribution.doctor(self.root)
        name = next(n for n in files if n.endswith("v5_core.py"))
        put(self.root, name, files[name] + b"\n# foreign\n")
        with self.assertRaises(ValueError): distribution.doctor(self.root)

    def test_installed_cli_cannot_silently_replace_pinned_core(self):
        for name, raw in distribution.consumer_files(distribution.core_files(ROOT)).items(): put(self.root, name, raw)
        run = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/lks_sdd.py"),
            "validate", "--root", str(self.root)], capture_output=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn(b"exact pinned CLI", run.stdout)

    def test_native_bundle_rejects_unrequested_hook_even_with_consistent_inventory(self):
        from validate_copilot_package import unpack, validate
        bundle = distribution.artifacts(distribution.core_files(ROOT), "test", "local-preparation")["lks-sdd-copilot-plugin-v5.0.0.zip"]
        files = unpack(bundle)
        files["lks-sdd/hooks/hook.py"] = b"print('unrequested')"
        manifest = json.loads(files["lks-sdd/native-integrity.json"])
        manifest["files"]["hooks/hook.py"] = core.digest(files["lks-sdd/hooks/hook.py"])
        files["lks-sdd/native-integrity.json"] = core.encode(manifest).encode()
        with self.assertRaisesRegex(ValueError, "Unrequested"):
            validate(distribution.zip_bytes(files))

    @unittest.skipUnless(os.name == "nt", "Actual Windows long-path regression")
    def test_windows_long_paths_execute_full_migration(self):
        long = self.root.joinpath(*[("segment-" + str(i) + "-" + "x" * 35) for i in range(6)])
        long = core.filesystem_root(long)
        long.mkdir(parents=True)
        self.assertGreater(len(str(long)), 260)
        source(long)
        preview = migration.preview(long)
        migration.run(long, preview["preview_sha256"])
        self.assertEqual(distribution.doctor(long)["status"], "passed")
        lock = json.loads((long / ".lks-sdd/distribution-lock.json").read_bytes())
        run = subprocess.run([sys.executable, "-B", str(long / lock["runtime"] / "scripts/lks_sdd.py"),
                              "context", "--root", str(long), "--task", "task-1"], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__": unittest.main(verbosity=2)
