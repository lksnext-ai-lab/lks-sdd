"""Small /2 durability and authority checks; one separate frozen volume journey."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
import object_zip as codec
import store_compaction as core
import test_store_maintenance as old_tests
from content_store import publish_object, reference, read_object
from v2_contract import ContractError, canonical, fingerprint, sha
from v2_storage import PENDING, write_one


def pin_v2(root):
    pin = root / core.legacy.PIN
    lock = json.loads(pin.read_bytes())
    lock["storage_formats"] = list(dict.fromkeys(lock["storage_formats"] + [core.FORMAT]))
    for module in core.MODULES:
        raw = (ROOT / "scripts" / module).read_bytes()
        name = "scripts/" + module
        write_one(root, lock["runtime"] + "/" + name, raw)
        lock["runtime_files"][name] = sha(raw)
    write_one(root, lock["runtime"] + "/distribution/dual.json", canonical({"storage_formats": lock["storage_formats"]}))
    write_one(root, core.legacy.PIN, canonical(lock))


class CompactionTests(unittest.TestCase):
    def setUp(self):
        old_tests.MaintenanceTests.setUp(self)
        pin_v2(self.root)

    def preview(self):
        return core.preview(self.root, self.base / "backup-dir", self.base / "restore-v2")

    def finish(self, plan):
        return core.recover(self.root, plan["preview_hash"], remove_authorized=plan["preview_hash"])

    def assert_logical(self):
        for raw in self.bodies:
            self.assertEqual(raw, read_object(self.root, reference(raw)))
        self.assertEqual(b"Canonical, no mutation", (self.root / "docs/lks-sdd/canonical.md").read_bytes())

    def snapshot(self):
        return {str(path.relative_to(self.root)): sha(path.read_bytes()) for path in self.root.rglob("*") if path.is_file()}

    def test_full_two_authorities_and_historical_receipt_are_idempotent(self):
        before = self.snapshot()
        plan = self.preview()
        self.assertEqual(before, self.snapshot())
        with self.assertRaises(ContractError):
            core.apply(self.root, plan, "0" * 64)
        result = core.apply(self.root, plan, plan["preview_hash"])
        self.assertEqual("awaiting-removal-authorization", result["status"])
        self.assertEqual(3, len(list((self.root / codec.OBJECTS).iterdir())))
        self.assert_logical()
        snapshot = self.snapshot()
        self.assertTrue(core.status(self.root, plan["preview_hash"])["read_only"])
        self.assertEqual(snapshot, self.snapshot())
        with self.assertRaises(ContractError):
            core.recover(self.root, plan["preview_hash"], remove_authorized="0" * 64)
        result = self.finish(plan)
        self.assertEqual("compacted", result["status"])
        self.assertFalse((self.root / PENDING).exists())
        self.assertEqual([], list((self.root / codec.OBJECTS).iterdir()))
        self.assert_logical()
        self.assertTrue(core.recover(self.root, plan["preview_hash"])["previously_completed"])
        self.assertEqual(1, len(list((self.root / codec.PACKS).iterdir())))
        for raw in self.bodies:
            self.assertEqual(raw, (self.base / "restore-v2" / sha(raw)).read_bytes())

    def test_stale_preview_is_rejected_under_owner_without_external_effects(self):
        plan = self.preview()
        publish_object(self.root, codec.OBJECTS + sha(b"later"), b"later")
        result = core.apply(self.root, plan, plan["preview_hash"])
        self.assertEqual("rejected-stale-preview", result["status"])
        self.assertFalse((self.root / PENDING).exists())
        self.assertFalse((self.base / "backup-dir").exists())
        self.assertFalse((self.base / "restore-v2").exists())
        self.assert_logical()

    def test_matching_hash_does_not_make_malformed_structure_authoritative(self):
        plan = self.preview()
        with self.assertRaises(ContractError):
            core.apply(self.root, {**plan, "preview_hash": "0" * 64}, plan["preview_hash"])
        for label, change in {
            "membership": lambda manifest: manifest["batches"][0]["packs"][0]["members"].pop(),
            "range": lambda manifest: manifest["batches"][0].update(first=1),
            "loose type": lambda manifest: manifest["objects"][0].update(loose=1),
            "space": lambda manifest: manifest["space_policy"]["components"].update(consumer=0),
            "destination": lambda manifest: manifest["destinations"].update(backup_dir=str(self.root / "foreign")),
        }.items():
            with self.subTest(label=label):
                value = copy.deepcopy(plan)
                change(value["manifest"])
                key = value["preview_hash"] = fingerprint(value["manifest"])
                with self.assertRaises((ContractError, ValueError)):
                    core.apply(self.root, value, key)
                self.assertFalse((self.root / PENDING).exists())

    def test_business_dispatch_never_authorizes_removal_or_rollback(self):
        from v2_storage import recover as v2_recover
        from v3_storage import recover as v3_recover
        plan = self.preview()
        key = plan["preview_hash"]
        core.apply(self.root, plan, key)
        for recover in (v2_recover, v3_recover):
            self.assertEqual("awaiting-removal-authorization", recover(self.root, key)["status"])
            with self.assertRaises(ContractError):
                recover(self.root, key, rollback=True)
        self.assertEqual(3, len(list((self.root / codec.OBJECTS).iterdir())))
        self.finish(plan)

    def test_active_and_external_corruption_preserve_pending_and_originals(self):
        plan = self.preview()
        core.apply(self.root, plan, plan["preview_hash"])
        pack = plan["manifest"]["batches"][0]["packs"][0]
        paths = [self.base / "backup-dir/batch-0000.zip", self.base / "backup-dir/manifest.json",
                 self.base / "restore-v2" / sha(self.bodies[0]),
                 self.root / (codec.PACKS + pack["sha256"] + ".zip")]
        for path in paths:
            with self.subTest(path=str(path)):
                raw = path.read_bytes()
                path.write_bytes(b"foreign or damaged")
                with self.assertRaises(ContractError):
                    self.finish(plan)
                self.assertEqual(b"foreign or damaged", path.read_bytes())
                self.assertTrue((self.root / PENDING).exists())
                self.assertEqual(3, len(list((self.root / codec.OBJECTS).iterdir())))
                path.write_bytes(raw)
        self.finish(plan)

    def test_finalize_partial_without_removal_preserves_active_objects_and_new_growth(self):
        plan = self.preview()
        def fail(phase):
            if phase == "after-publish":
                raise InterruptedError("partial preparation")
        with patch.object(core, "_checkpoint", side_effect=fail):
            with self.assertRaises(InterruptedError):
                core.apply(self.root, plan, plan["preview_hash"])
        publish_object(self.root, codec.OBJECTS + sha(b"later outside scope"), b"later outside scope")
        (self.base / "backup-dir" / "foreign-external").write_bytes(b"preserve")
        result = core.recover(self.root, plan["preview_hash"], finalize_without_removal=True)
        self.assertEqual("retained-originals", result["status"])
        self.assertIn("unverified", result["backup_status"])
        self.assertFalse((self.root / PENDING).exists())
        self.assertEqual(4, len(list((self.root / codec.OBJECTS).iterdir())))
        self.assert_logical()

    def test_completed_scope_preserves_later_growth_and_does_not_claim_to_compact_it(self):
        plan = self.preview()
        core.apply(self.root, plan, plan["preview_hash"])
        extra = b"later outside scope"
        publish_object(self.root, codec.OBJECTS + sha(extra), extra)
        self.finish(plan)
        self.assertEqual([sha(extra)], [path.name for path in (self.root / codec.OBJECTS).iterdir()])
        self.assertEqual(extra, read_object(self.root, reference(extra)))
        self.assert_logical()

    def test_actual_enospc_error_during_write_preserves_recoverable_owner(self):
        import errno
        plan = self.preview()
        atomic = core._atomic
        def full(path, *args, **kwargs):
            if Path(path).name == "manifest.json":
                raise OSError(errno.ENOSPC, "disk full")
            return atomic(path, *args, **kwargs)
        with patch.object(core, "_atomic", side_effect=full):
            with self.assertRaises(OSError) as raised:
                core.apply(self.root, plan, plan["preview_hash"])
        self.assertEqual(errno.ENOSPC, raised.exception.errno)
        self.assertTrue((self.root / PENDING).exists())
        self.assert_logical()
        core.recover(self.root, plan["preview_hash"])
        self.finish(plan)

    def test_after_first_withdrawal_finalize_refuses_and_persisted_authority_resumes(self):
        plan = self.preview()
        core.apply(self.root, plan, plan["preview_hash"])
        def fail(phase):
            if phase == "during-remove":
                raise InterruptedError("unlink without checkpoint")
        with patch.object(core, "_checkpoint", side_effect=fail):
            with self.assertRaises(InterruptedError):
                self.finish(plan)
        with self.assertRaises(ContractError):
            core.recover(self.root, plan["preview_hash"], finalize_without_removal=True)
        self.assertEqual("compacted", core.recover(self.root, plan["preview_hash"])["status"])
        self.assert_logical()

    def test_pin_and_unknown_staging_conflicts_never_overwrite(self):
        plan = self.preview()
        key = plan["preview_hash"]
        core.apply(self.root, plan, key)
        pin = self.root / core.legacy.PIN
        original = pin.read_bytes()
        pin.write_bytes(original + b" ")
        with self.assertRaises(ContractError):
            self.finish(plan)
        pin.write_bytes(original)
        foreign = self.base / "backup-dir/foreign"
        foreign.write_bytes(b"preserve")
        with self.assertRaises(ContractError):
            self.finish(plan)
        self.assertEqual(b"preserve", foreign.read_bytes())
        foreign.unlink()
        self.finish(plan)

    def test_mid_batch_backup_and_restore_changes_preserve_next_original(self):
        plan = self.preview()
        key = plan["preview_hash"]
        core.apply(self.root, plan, key)
        rows = plan["manifest"]["objects"]
        backup = self.base / "backup-dir/batch-0000.zip"
        initial_backup = backup.read_bytes()
        changed = [False]
        def change_backup(phase):
            if phase == "during-remove" and not changed[0]:
                changed[0] = True
                backup.write_bytes(b"changed during withdrawal")
        with patch.object(core, "_checkpoint", side_effect=change_backup):
            with self.assertRaisesRegex(ContractError, "backup changed"):
                self.finish(plan)
        self.assertEqual(2, len(list((self.root / codec.OBJECTS).iterdir())))
        self.assertTrue((self.root / (codec.OBJECTS + rows[1]["sha256"])).exists())
        backup.write_bytes(initial_backup)
        restored = self.base / "restore-v2" / rows[2]["sha256"]
        original_restore = restored.read_bytes()
        changed[0] = False
        def change_restore(phase):
            if phase == "during-remove" and not changed[0]:
                changed[0] = True
                restored.write_bytes(b"changed during withdrawal")
        with patch.object(core, "_checkpoint", side_effect=change_restore):
            with self.assertRaisesRegex(ContractError, "Restored copy changed"):
                core.recover(self.root, key)
        self.assertTrue((self.root / (codec.OBJECTS + rows[2]["sha256"])).exists())
        restored.write_bytes(original_restore)
        self.assertEqual("compacted", core.recover(self.root, key)["status"])
        self.assert_logical()


if __name__ == "__main__":
    unittest.main()
