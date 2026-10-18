"""Read-only /2 preparation: real multi-batch data and stale-preview rejection."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
import object_zip as codec
import store_maintenance as legacy
import store_maintenance_batches as batches
from content_store import publish_object, reference
from path_utils import filesystem_root
import test_store_maintenance as legacy_tests
from v2_contract import ContractError, canonical, fingerprint, sha
from v2_storage import PENDING, write_one

MIB = 1024 * 1024


class BatchPreviewTests(unittest.TestCase):
    def setUp(self):
        legacy_tests.MaintenanceTests.setUp(self)

    def preview(self):
        return batches.preview(self.root, self.base / "backup-dir", self.base / "restore-v2")

    def add(self, raw):
        publish_object(self.root, codec.OBJECTS + sha(raw), raw)
        return reference(raw)

    def snapshot(self):
        return {str(path.relative_to(self.root)): (path.stat().st_size, sha(path.read_bytes()))
                for path in self.root.rglob("*") if path.is_file()}

    def pack(self, objects):
        raw = codec.encode(objects)
        name = codec.PACKS + sha(raw) + ".zip"
        write_one(self.root, name, raw)
        return name

    def test_real_store_over_64mib_full_backup_protected_and_cross_batch_references(self):
        references = []
        for ordinal in range(17):
            raw = b"x" * (4 * MIB - 8) + f"{ordinal:08}".encode()
            references.append(self.add(raw))
        protected = self.add(b"p" * (9 * MIB))
        self.add(canonical({"all": references, "protected": protected}))
        del raw
        before = self.snapshot()
        checked = []
        encoder = legacy._backup_bytes

        def checked_backup(bodies):
            raw = encoder(bodies)
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                self.assertEqual(sorted(bodies), archive.namelist())
                for info in archive.infolist():
                    body = archive.read(info)
                    self.assertEqual(info.filename, sha(body))
                    self.assertEqual(bodies[info.filename], body)
                    self.assertEqual(zipfile.ZIP_STORED, info.compress_type)
            checked.append((len(raw), sha(raw)))
            return raw

        with patch.object(legacy, "_backup_bytes", side_effect=checked_backup):
            result = self.preview()
        manifest = result["manifest"]
        rows, planned = manifest["objects"], manifest["batches"]
        self.assertGreater(sum(row["bytes"] for row in rows), 64 * MIB)
        self.assertEqual(22, len(rows))
        self.assertEqual(sorted(row["sha256"] for row in rows), [row["sha256"] for row in rows])
        self.assertGreaterEqual(len(planned), 2)
        covered, packed = [], []
        object_batch = {}
        for number, batch in enumerate(planned):
            self.assertLessEqual(batch["logical_bytes"], 64 * MIB)
            self.assertLessEqual(batch["count"], 4096)
            self.assertLessEqual(batch["backup"]["bytes"], 66 * MIB)
            self.assertEqual(checked[number], (batch["backup"]["bytes"], batch["backup"]["sha256"]))
            indices = list(range(batch["first"], batch["first"] + batch["count"]))
            covered.extend(indices)
            object_batch.update({rows[index]["sha256"]: number for index in indices})
            for pack in batch["packs"]:
                packed.extend(pack["members"])
                self.assertTrue(set(pack["members"]).issubset(indices))
        self.assertEqual(list(range(len(rows))), covered)
        self.assertEqual([i for i, row in enumerate(rows) if row["bytes"] <= codec.TARGET], sorted(packed))
        self.assertEqual(18, manifest["structured_references_checked"])
        self.assertGreater(len({object_batch[ref["sha256"]] for ref in references}), 1)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(fingerprint(manifest), result["preview_hash"])
        self.assertFalse(result["execution_enabled"])
        self.assertEqual([], result["consumer_writes"])
        self.assertFalse((self.base / "backup-dir").exists())
        self.assertFalse((self.base / "restore-v2").exists())
        self.assertFalse(Path(result["restore_stage"]).exists())
        with self.assertRaises(ContractError):
            legacy._validate(result, result["preview_hash"])

    def test_determinism_ignores_enumeration_order_and_observed_free_bytes(self):
        physical = batches._physical

        def reversed_scan(*args):
            return {key: dict(reversed(list(value.items()))) for key, value in physical(*args).items()}

        with patch.object(batches.shutil, "disk_usage", return_value=shutil._ntuple_diskusage(10**15, 0, 10**15)):
            first = self.preview()
        with patch.object(batches, "_physical", side_effect=reversed_scan), patch.object(
                batches.shutil, "disk_usage", return_value=shutil._ntuple_diskusage(10**15, 1, 10**15 - 1)):
            second = self.preview()
        self.assertEqual(first["preview_hash"], second["preview_hash"])
        self.assertEqual(first["manifest"], second["manifest"])
        self.assertNotEqual(first["observed_space"], second["observed_space"])

    def test_late_membership_pin_content_pending_and_destination_changes_reject(self):
        pin = self.root / legacy.PIN
        original_pin = pin.read_bytes()
        original = self.root / (codec.OBJECTS + sha(self.bodies[0]))
        added = self.root / (codec.OBJECTS + sha(b"late"))
        actions = {
            "membership": lambda: added.write_bytes(b"late"),
            "pin": lambda: pin.write_bytes(original_pin + b" "),
            "content": lambda: original.write_bytes(b"later edit"),
            "pending": lambda: write_one(self.root, PENDING, b"{}"),
            "destination": lambda: (self.base / "backup-dir").mkdir(),
        }
        for label, action in actions.items():
            with self.subTest(label=label):
                def change(phase):
                    if phase == "before-final-validation":
                        action()
                with patch.object(batches, "_checkpoint", side_effect=change):
                    with self.assertRaises(ContractError):
                        self.preview()
                pin.write_bytes(original_pin)
                original.write_bytes(self.bodies[0])
                added.unlink(missing_ok=True)
                (self.root / PENDING).unlink(missing_ok=True)
                if (self.base / "backup-dir").exists():
                    (self.base / "backup-dir").rmdir()
                self.assertFalse((self.root / PENDING).exists())

    def test_valid_redundant_copies_are_verified_and_reused(self):
        selected = {sha(body): body for body in self.bodies[:2]}
        name = self.pack(selected)
        other = b"only packed, unreferenced"
        second = self.pack({sha(other): other, sha(self.bodies[0]): self.bodies[0]})
        result = self.preview()
        manifest = result["manifest"]
        self.assertEqual({Path(name).stem, Path(second).stem}, set(manifest["existing_packs"]))
        self.assertEqual(4, len(manifest["objects"]))
        reused = {row["sha256"] for row in manifest["objects"] if row.get("packed")}
        self.assertEqual(set(selected) | {sha(other)}, reused)
        new = {manifest["objects"][i]["sha256"] for batch in manifest["batches"]
               for pack in batch["packs"] for i in pack["members"]}
        self.assertEqual({sha(self.bodies[2])}, new)

    def test_corrupt_redundant_member_cannot_hide_behind_valid_copies(self):
        body = self.bodies[0]
        self.pack({sha(body): body})
        raw = bytearray(codec.encode({sha(body): body, sha(self.bodies[1]): self.bodies[1]}))
        raw[94] ^= 1  # Keep valid headers/index and a correctly named whole ZIP.
        name = codec.PACKS + sha(raw) + ".zip"
        write_one(self.root, name, bytes(raw))
        before = self.snapshot()
        with self.assertRaisesRegex(ContractError, "integrity"):
            self.preview()
        self.assertEqual(before, self.snapshot())

    def test_conflicting_physical_sizes_unknown_files_and_missing_references_reject(self):
        body = self.bodies[0]
        name = self.pack({sha(body): body})
        loose = self.root / (codec.OBJECTS + sha(body))
        loose.write_bytes(b"wrong size")
        with self.assertRaisesRegex(ContractError, "Contradictory"):
            self.preview()
        loose.write_bytes(body)
        unknown = self.root / codec.OBJECTS / "unknown"
        unknown.write_bytes(b"preserve")
        with self.assertRaisesRegex(ContractError, "Unrecognized"):
            self.preview()
        unknown.unlink()
        unknown = self.root / ".lks-sdd/objects/unrecognized"
        unknown.write_bytes(b"preserve")
        with self.assertRaisesRegex(ContractError, "Unrecognized"):
            self.preview()
        unknown.unlink()
        self.add(canonical({"ref": reference(b"missing")}))
        with self.assertRaisesRegex(ContractError, "Unresolved"):
            self.preview()
        self.assertTrue((self.root / name).exists())

    def test_json_budget_is_per_object_not_accumulated_store(self):
        for ordinal in range(3):
            self.add(b"[" + str(ordinal).encode() + b",0" * 350_000 + b"]")
        result = self.preview()
        self.assertGreater(result["structured_nodes_checked"], 1_000_000)

    def test_quotas_deadline_and_space_fail_without_partial_preview(self):
        before = self.snapshot()
        for label, target, value in (("time", "WORK_SECONDS", 0), ("manifest", "MANIFEST_LIMIT", 1),
                                     ("count", "OBJECT_COUNT", 2)):
            with self.subTest(label=label), patch.object(batches, target, value):
                with self.assertRaises(ContractError):
                    self.preview()
        with patch.object(batches.shutil, "disk_usage", return_value=shutil._ntuple_diskusage(1, 1, 0)):
            with self.assertRaisesRegex(ContractError, "Insufficient"):
                self.preview()
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.base / "backup-dir").exists())

    def test_batch_boundaries_include_zero_bytes_and_exact_64mib(self):
        rows = [{"bytes": 0}] * 4097 + [{"bytes": 64 * MIB}, {"bytes": 1}]
        self.assertEqual([(0, 4096), (4096, 2), (4098, 1)], list(batches._ranges(rows)))
        with self.assertRaises(ContractError):
            list(batches._ranges([{"bytes": 64 * MIB + 1}]))

    def test_space_is_aggregated_by_volume_without_double_restore_staging(self):
        original = batches._volume
        def volume(path):
            _, parent = original(path)
            return ("backup-volume" if Path(path).name == "backup-dir" else "consumer-volume"), parent
        with patch.object(batches, "_volume", side_effect=volume):
            result = self.preview()
        space = result["manifest"]["space_policy"]
        volumes = {volume["device"]: volume["required_bytes"] for volume in space["volumes"]}
        self.assertEqual(space["components"]["backup_dir"], volumes["backup-volume"])
        self.assertEqual(space["components"]["consumer"] + space["components"]["restore"], volumes["consumer-volume"])
        self.assertEqual(sum(len(body) for body in self.bodies), space["components"]["restore"])

    def test_overlapping_in_repo_existing_and_non_directory_destinations_reject(self):
        file = self.base / "file"
        file.write_bytes(b"keep")
        for backup, restore in ((self.root / "backup", self.base / "restore"),
                                (self.base / "backup", self.base / "backup" / "restore"),
                                (file, self.base / "restore"),
                                (file / "backup", self.base / "restore")):
            with self.subTest(backup=str(backup)), self.assertRaises(ContractError):
                batches.preview(self.root, backup, restore)
        self.assertEqual(b"keep", file.read_bytes())

    def test_unicode_and_long_paths_use_existing_extended_path_transport(self):
        old = self.root
        area = filesystem_root(self.base / ("ruta-á-" + "x" * 80) / ("y" * 80) / ("z" * 80), force_extended=True)
        self.root = area / "consumidor"
        # Remove the long subtree through its extended path before the generic
        # TemporaryDirectory finalizer walks its ordinary spelling on Windows.
        self.addCleanup(shutil.rmtree, filesystem_root(self.base / ("ruta-á-" + "x" * 80), force_extended=True))
        shutil.copytree(old, self.root)
        result = batches.preview(self.root, area / "respaldo-á", area / "restauración")
        self.assertGreater(len(str(self.root)), 260)
        self.assertEqual(3, len(result["manifest"]["objects"]))
        self.assertFalse((area / "respaldo-á").exists())

    def test_link_and_dangling_destination_are_rejected(self):
        link = self.base / "link"
        if os.name == "nt":
            # A real NTFS junction exercises reparse rejection without requiring
            # symlink/admin privilege or any host configuration change.
            subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.base / "absent")],
                           check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.addCleanup(link.rmdir)
        else:
            os.symlink(self.base / "absent", link, target_is_directory=True)
            self.addCleanup(link.unlink)
        with self.assertRaises(ContractError):
            batches.preview(self.root, link, self.base / "restore-v2")


if __name__ == "__main__":
    unittest.main()
