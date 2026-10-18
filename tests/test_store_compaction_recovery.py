"""One small fault chain, transport checks and pin compatibility; no volume replay."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
import store_compaction as core
import store_maintenance_batches as planner
import test_store_compaction as support
from content_store import reference, read_object
from v2_contract import ContractError, canonical
from v2_storage import PENDING


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        support.CompactionTests.setUp(self)

    def preview(self):
        return support.CompactionTests.preview(self)

    def finish(self, plan):
        return support.CompactionTests.finish(self, plan)

    def cli(self, action, *arguments):
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/v3_cli.py"),
                                 action, str(self.root), *map(str, arguments)], capture_output=True, timeout=45)
        return result.returncode, json.loads(result.stdout)

    def test_three_batch_fault_chain_reuses_one_operation_at_all_durable_boundaries(self):
        boundaries = ["after-own", "before-revalidation", "revalidated", "after-backup", "after-publish",
                      "during-restore", "batch-verified-before-checkpoint", "batch-prepared",
                      "restore-published-before-checkpoint", "awaiting-removal", "removal-authorized",
                      "during-remove", "batch-removed", "before-receipt", "after-receipt"]
        with patch.object(planner, "BATCH_OBJECTS", 1):
            plan = self.preview()
            key = plan["preview_hash"]
            self.assertEqual(3, len(plan["manifest"]["batches"]))
            first = True
            for boundary in boundaries:
                with self.subTest(boundary=boundary):
                    def fail(phase):
                        if phase == boundary:
                            raise InterruptedError(boundary)
                    with patch.object(core, "_checkpoint", side_effect=fail):
                        with self.assertRaises(InterruptedError):
                            if first:
                                first = False
                                core.apply(self.root, plan, key)
                            else:
                                core.recover(self.root, key, remove_authorized=key if boundary == "removal-authorized" else None)
                    self.assertTrue((self.root / PENDING).exists())
                    for raw in self.bodies:
                        self.assertEqual(raw, read_object(self.root, reference(raw)))
            result = core.recover(self.root, key)
            self.assertEqual("compacted", result["status"])
            self.assertEqual(3, len(list((self.base / "backup-dir").glob("batch-*.zip"))))
            self.assertEqual(3, len(list((self.root / core.codec.PACKS).iterdir())))
            self.assertFalse((self.root / PENDING).exists())
            self.assertFalse(core._temporary_directory(self.root, key).exists())

    def test_real_process_death_after_checkpoint_and_exclusive_second_recoverer(self):
        plan = self.preview()
        packet = self.base / "input.json"
        packet.write_bytes(canonical(plan))
        program = ("import json,os,sys;sys.path.insert(0,sys.argv[1]);import store_compaction as c;"
                   "c._checkpoint=lambda p:os._exit(73) if p=='batch-prepared' else None;"
                   "v=json.load(open(sys.argv[3],encoding='utf-8'));c.apply(sys.argv[2],v,v['preview_hash'])")
        result = subprocess.run([sys.executable, "-B", "-c", program, str(ROOT / "scripts"), str(self.root), str(packet)],
                                capture_output=True, timeout=45)
        self.assertEqual(73, result.returncode, result.stderr.decode(errors="replace"))
        self.assertTrue((self.root / PENDING).exists())
        with core.legacy._exclusive(self.root):
            command = "import sys;sys.path.insert(0,sys.argv[1]);from store_compaction import recover;recover(sys.argv[2],sys.argv[3])"
            result = subprocess.run([sys.executable, "-B", "-c", command, str(ROOT / "scripts"), str(self.root), plan["preview_hash"]],
                                    capture_output=True, timeout=20)
        self.assertNotEqual(0, result.returncode)
        self.assertIn(b"Another recovery owns", result.stderr)
        self.assertEqual("awaiting-removal-authorization", core.recover(self.root, plan["preview_hash"])["status"])
        self.finish(plan)

    def test_initial_and_update_temporaries_resume_and_uncommitted_removal_is_not_authority(self):
        plan = self.preview()
        key = plan["preview_hash"]
        def initial(phase):
            if phase == "temporary-fsynced":
                raise InterruptedError("initial temporary")
        with patch.object(core, "_checkpoint", side_effect=initial):
            with self.assertRaises(InterruptedError):
                core.apply(self.root, plan, key)
        self.assertFalse((self.root / PENDING).exists())
        core.apply(self.root, plan, key)
        def authorization(phase):
            if phase == "temporary-fsynced" and (core._temporary_directory(self.root, key) / "transaction.json.tmp").exists():
                raise InterruptedError("uncommitted authorization")
        with patch.object(core, "_checkpoint", side_effect=authorization):
            with self.assertRaises(InterruptedError):
                self.finish(plan)
        self.assertFalse(core.status(self.root, key)["removal_authorized"])
        self.assertEqual("awaiting-removal-authorization", core.recover(self.root, key)["status"])
        self.assertEqual(3, len(list((self.root / core.codec.OBJECTS).iterdir())))
        result = core.recover(self.root, key, finalize_without_removal=True)
        self.assertEqual("retained-originals", result["status"])
        self.assertEqual(3, len(list((self.root / core.codec.OBJECTS).iterdir())))

    def test_deadline_pauses_at_durable_boundary_and_real_io_failure_preserves_owner(self):
        plan = self.preview()
        clock = [0]
        def expire(phase):
            if phase == "batch-prepared":
                clock[0] = 601
        with patch.object(core.time, "monotonic", side_effect=lambda: clock[0]), patch.object(core, "_checkpoint", side_effect=expire):
            result = core.apply(self.root, plan, plan["preview_hash"])
        self.assertEqual("paused", result["status"])
        self.assertTrue((self.root / PENDING).exists())
        with patch.object(core.shutil, "disk_usage", return_value=shutil._ntuple_diskusage(1, 1, 0)):
            with self.assertRaises(ContractError):
                core.recover(self.root, plan["preview_hash"])
        core.recover(self.root, plan["preview_hash"])
        self.finish(plan)

    def test_cli_v2_export_authority_status_and_partial_transport_failure(self):
        source = self.base / "request.json"
        source.write_bytes(canonical({"backup_dir": str(self.base / "backup-dir"), "restore": str(self.base / "restore-v2")}))
        output = self.base / "preview.json"
        code, shown = self.cli("store-preview", "--input", source, "--output", output, "--view", "operational", "--json")
        self.assertEqual(0, code, shown)
        self.assertLessEqual(len(canonical(shown)), 8192)
        plan = json.loads(output.read_bytes())
        self.assertEqual(core.FORMAT, plan["manifest"]["format"])
        key = plan["preview_hash"]
        code, result = self.cli("store-compact", "--input", output, "--authorize", key, "--json")
        self.assertEqual(0, code, result)
        self.assertEqual("awaiting-removal-authorization", result["status"])
        before = (self.root / PENDING).read_bytes()
        code, result = self.cli("store-recover", "--authorize", key, "--status", "--json")
        self.assertEqual(0, code, result)
        self.assertEqual(before, (self.root / PENDING).read_bytes())
        # Inject a real export OSError after execution, without weakening path
        # preflight (an invalid parent would correctly fail before any effects).
        import v3_cli
        displayed = io.StringIO()
        with patch('v3_cli_presentation.write_export', side_effect=OSError("export failed")), redirect_stdout(displayed):
            code = v3_cli.main(["store-recover", str(self.root), "--authorize", key, "--authorize-removal", key,
                                "--output", str(self.base / "result.json"), "--view", "operational", "--json"])
        result = json.loads(displayed.getvalue())
        self.assertEqual(2, code, result)
        self.assertEqual("compacted", result["effects"]["status"])
        self.assertFalse((self.root / PENDING).exists())
        self.assertIn("store-recover", result["next"])

    def test_cli_legacy_and_destination_transport_validation(self):
        source = self.base / "request.json"
        source.write_bytes(canonical({"backup": str(self.base / "backup.zip"), "restore": str(self.base / "restore-old")}))
        code, plan = self.cli("store-preview", "--input", source, "--json")
        self.assertEqual(0, code, plan)
        self.assertEqual(core.legacy.FORMAT, plan["format"])
        packet = self.base / "legacy-plan.json"
        packet.write_bytes(canonical(plan))
        code, result = self.cli("store-compact", "--input", packet, "--authorize", plan["preview_hash"], "--json")
        self.assertEqual(0, code, result)
        code, result = self.cli("store-recover", "--authorize", plan["preview_hash"], "--authorize-removal", plan["preview_hash"], "--json")
        self.assertEqual(0, code, result)
        for value in ({"backup": "a", "backup_dir": "b", "restore": "c"}, {"restore": "c"}):
            source.write_bytes(canonical(value))
            code, result = self.cli("store-preview", "--input", source, "--json")
            self.assertEqual(2, code, result)
        request = {"backup_dir": str(self.base / "new-backup"), "restore": str(self.base / "new-restore")}
        source.write_bytes(canonical(request))
        code, result = self.cli("store-preview", "--input", source, "--output", self.base / "new-backup/preview.json", "--json")
        self.assertEqual(2, code, result)
        self.assertFalse((self.base / "new-backup").exists())

    def test_pending_pin_change_rejected_by_installer_and_doctor(self):
        spec = importlib.util.spec_from_file_location("v401_installer", ROOT / "distribution/install.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        pin = self.root / core.legacy.PIN
        metadata = json.loads(pin.read_bytes())
        metadata.update(schema_version="1.0", project_schema="3.1")
        pin.write_bytes(canonical(metadata))
        plan = self.preview()
        key = plan["preview_hash"]
        core.apply(self.root, plan, key)
        current = pin.read_bytes()
        older = json.loads(current)
        older["storage_formats"].remove(core.FORMAT)
        incoming = canonical(older)
        with self.assertRaisesRegex(ValueError, "exact current pin"):
            installer.check_storage_reader(self.root, incoming)
        with self.assertRaises(ValueError):
            installer.check_storage_reader(self.root, None)
        installer.check_storage_reader(self.root, current)
        from runtime_doctor import check
        pin.write_bytes(incoming)
        diagnostic = check(self.root)
        self.assertEqual("blocked", diagnostic["status"])
        self.assertIn("pending maintenance", " ".join(diagnostic["errors"]))
        pin.write_bytes(current)
        self.finish(plan)
        installer.check_storage_reader(self.root, incoming)

    def test_restoration_uses_only_external_backup_and_missing_backup_has_no_fallback(self):
        import time
        plan = self.preview()
        core.apply(self.root, plan, plan["preview_hash"])
        backup = self.base / "backup-dir"
        destination = self.base / "independent-small-restore"
        with patch.object(core.codec, "read_logical", side_effect=AssertionError("consumer fallback forbidden")), \
                patch.object(planner, "_read_object", side_effect=AssertionError("consumer fallback forbidden")):
            bodies = core._backup_bodies(backup, 0, plan["manifest"])
            core._restore_batch(destination, bodies, time.monotonic() + 30)
            for digest, raw in bodies.items():
                self.assertEqual(raw, (destination / digest).read_bytes())
            with self.assertRaises((ContractError, OSError)):
                core._backup_bodies(self.base / "absent", 0, plan["manifest"])
        self.finish(plan)


if __name__ == "__main__":
    unittest.main()
