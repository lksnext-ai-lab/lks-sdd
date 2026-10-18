"""Small container/transaction checks, not additional functional journeys."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import stat
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
from content_store import OBJECTS, object_path, read_object, reference, prepare_object, publish_object
from object_zip import Publisher, PACKS, evaluation, encode
from v2_contract import ContractError, read_bytes, sha
from v2_storage import apply, preview, recover, write_one, PENDING, exists_hash


class StoreFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="oz-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def files(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}

    def publish(self, bodies):
        with evaluation():
            publisher = Publisher(self.root)
            refs = [publisher.add(body) for body in bodies]
            publisher.flush()
        return refs


class ObjectZipPrototypeTests(StoreFixture):
    def test_mixed_logical_reads_no_loose_fragments_and_idempotence(self):
        raw = [b"packed first", b"packed second", b"packed third"]
        refs = self.publish(raw)
        self.assertEqual(1, len(self.files()))
        self.assertTrue(all(name.startswith(PACKS) for name in self.files()))
        before = self.files()
        with evaluation():
            for ref, body in zip(refs, raw):
                self.assertEqual(body, read_object(self.root, ref))
                self.assertEqual(body, read_bytes(self.root, object_path(ref)))
                self.assertEqual(ref["sha256"], exists_hash(self.root, object_path(ref)))
                changes = {}; self.assertEqual(ref, prepare_object(self.root, body, changes))
                self.assertEqual({}, changes)
        self.publish(raw)
        self.assertEqual(before, self.files())
        old = b"legacy loose"; publish_object(self.root, object_path(reference(old)), old)
        self.assertEqual(old, read_object(self.root, reference(old)))
        self.assertEqual(raw[0], read_object(self.root, refs[0]))

    def test_journal_21_recovers_with_packed_payloads_and_preserves_later_work(self):
        target = "docs/lks-sdd/evidence/test.txt"
        write_one(self.root, target, b"before")
        refs = self.publish([b"guarded source", b"second source"])
        changes = {target: b"after"}; sources = {object_path(refs[0]): refs[0]["sha256"]}
        plan = preview(self.root, changes, sources=sources, operation="zip-component")
        with self.assertRaises(InterruptedError):
            apply(self.root, changes, plan, plan["preview_hash"], interrupt_after=1)
        journal = json.loads((self.root / PENDING).read_bytes())
        self.assertEqual("2.1", journal["schema_version"])
        self.assertFalse((self.root / object_path(journal["preview_ref"])).exists())
        write_one(self.root, "src/independent.txt", b"later work")
        recover(self.root, plan["preview_hash"], rollback=True)
        self.assertEqual(b"before", read_bytes(self.root, target))
        self.assertEqual(b"later work", read_bytes(self.root, "src/independent.txt"))
        self.assertFalse((self.root / PENDING).exists())

    def test_packed_subject_tamper_invalidates_prepared_apply(self):
        refs = self.publish([b"guarded source", b"other source"])
        plan = preview(self.root, {"output.txt": b"new"},
                       sources={object_path(refs[0]): refs[0]["sha256"]}, operation="zip-guard")
        pack = next((self.root / PACKS).glob("*.zip"))
        body = pack.read_bytes().replace(b"guarded source", b"damaged source")
        pack.write_bytes(body)
        with self.assertRaises(ContractError):
            apply(self.root, {"output.txt": b"new"}, plan, plan["preview_hash"])
        self.assertFalse((self.root / "output.txt").exists())
        self.assertFalse((self.root / PENDING).exists())

    def test_grouped_growth_and_deterministic_pack_bytes(self):
        bodies = [f"synthetic fragment {i}".encode() for i in range(407)]
        self.assertEqual(encode({sha(b): b for b in bodies}), encode({sha(b): b for b in reversed(bodies)}))
        self.publish(bodies)
        self.assertLessEqual(len(self.files()), 81)
        self.assertEqual([], list((self.root / OBJECTS).glob("*")))

    def test_v3_staging_and_native_partial_plan_with_packed_sources(self):
        from test_v3_workflow import ProjectFixture
        from v3_contract import load
        case = ProjectFixture("runTest"); case.setUp()
        self.addCleanup(case.doCleanups)
        case.plan()
        self.assertEqual([], load(case.root).errors)
        self.assertTrue(list((case.root / PACKS).glob("*.zip")))
        from presentation_test_support import present
        from v3_workflow import transition
        from v3_storage import apply as native_apply
        packet = present(transition, case.root, case.actor, case.task, "start", "Scoped idempotent retry check")
        native_apply(case.root, packet, packet["preview"]["preview_hash"])
        def snapshot():
            return {p.relative_to(case.root).as_posix():p.read_bytes() for p in case.root.rglob("*") if p.is_file()}
        before = snapshot()
        result = native_apply(case.root, packet, packet["preview"]["preview_hash"])
        self.assertEqual("previously-applied", result["status"])
        self.assertEqual(before, snapshot())


class ObjectZipContainerTests(StoreFixture):
    def container(self, entries, *, compression=zipfile.ZIP_STORED, mode=stat.S_IFREG):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=compression) as archive:
            for name, body in entries:
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.create_system = 3; info.external_attr = (mode | 0o600) << 16
                info.compress_type = compression
                archive.writestr(info, body)
        raw = output.getvalue(); path = self.root / PACKS / (sha(raw) + ".zip")
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        return path

    def test_unsafe_names_modes_and_compression_are_rejected(self):
        body = b"data"; digest = sha(body)
        cases = [("../"+digest, zipfile.ZIP_STORED, stat.S_IFREG),
                 ("/"+digest, zipfile.ZIP_STORED, stat.S_IFREG),
                 (digest+"/", zipfile.ZIP_STORED, stat.S_IFDIR),
                 (digest, zipfile.ZIP_STORED, stat.S_IFLNK),
                 (digest, zipfile.ZIP_DEFLATED, stat.S_IFREG)]
        for name, compression, mode in cases:
            with self.subTest(name=name, compression=compression, mode=mode):
                path = self.container([(name, body)], compression=compression, mode=mode)
                try:
                    with self.assertRaises(ContractError): read_object(self.root, reference(body))
                finally: path.unlink()

    def test_duplicate_members_and_conflicting_locations_are_rejected(self):
        import warnings
        body = b"data"; digest = sha(body)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            path = self.container([(digest, body), (digest, body)])
        with self.assertRaises(ContractError): read_object(self.root, reference(body))
        path.unlink()
        self.container([(digest, body)])
        self.container([(digest, body+b"different length")])
        with self.assertRaises(ContractError): read_object(self.root, reference(body))

    def test_body_and_local_header_corruption_are_rejected(self):
        body = b"known payload"; digest = sha(body)
        for offset in (6, 30, 94):
            with self.subTest(offset=offset):
                path = self.container([(digest, body)])
                raw = bytearray(path.read_bytes()); raw[offset] ^= 1; path.write_bytes(raw)
                try:
                    with self.assertRaises(ContractError): read_object(self.root, reference(body))
                finally: path.unlink()

    def test_index_and_entry_quotas_reject_before_directory_allocation(self):
        raw = [b"one", b"two"]
        self.container([(sha(b), b) for b in raw])
        import object_zip
        for name in ("MAX_INDEX", "MAX_ENTRIES"):
            with self.subTest(name=name), patch.object(object_zip, name, 1), \
                 patch("object_zip.zipfile.ZipFile", side_effect=AssertionError("over-budget parse")):
                with self.assertRaises(ContractError): read_object(self.root, reference(raw[0]))

    def test_accumulated_index_budget_is_enforced(self):
        for body in (b"one", b"two"): self.container([(sha(body), body)])
        with patch("object_zip.MAX_INDEX_TOTAL", 150), evaluation(), self.assertRaises(ContractError):
            read_object(self.root, reference(b"one"))

    def test_valid_loose_copy_does_not_hide_corrupt_packed_copy(self):
        body = b"known payload"; ref = reference(body)
        publish_object(self.root, object_path(ref), body)
        self.container([(ref["sha256"], b"bad payload!!")])
        with self.assertRaises(ContractError): read_object(self.root, ref)

    def test_index_reused_only_in_scope_and_subject_bytes_stay_fresh(self):
        import object_zip
        body = b"known payload"; ref = reference(body)
        path = self.container([(ref["sha256"], body)])
        with patch("object_zip._index", wraps=object_zip._index) as index:
            with evaluation():
                read_object(self.root, ref); read_object(self.root, ref)
                self.assertEqual(1, index.call_count)
                data = bytearray(path.read_bytes()); data[94] ^= 1; path.write_bytes(data)
                with self.assertRaises(ContractError): read_object(self.root, ref)
            with self.assertRaises(ContractError): read_object(self.root, ref)
            self.assertEqual(2, index.call_count)

    def test_child_thread_does_not_share_locator_ownership(self):
        import object_zip
        from concurrent.futures import ThreadPoolExecutor
        body = b"known payload"; self.container([(sha(body), body)])
        with patch("object_zip._index", wraps=object_zip._index) as index, evaluation():
            read_object(self.root, reference(body))
            with ThreadPoolExecutor(max_workers=1) as pool:
                self.assertEqual(body, pool.submit(read_object, self.root, reference(body)).result())
            self.assertEqual(2, index.call_count)

    def test_publication_race_verifies_winner_and_preserves_corruption(self):
        from path_utils import publish_new_file
        for corrupt in (False, True):
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory(prefix="oz-race-") as directory:
                root = Path(directory)
                def race(path, raw, **options):
                    path.write_bytes(b"corrupt winner" if corrupt else raw)
                    return publish_new_file(path, raw, **options)
                with patch("path_utils.publish_new_file", side_effect=race), evaluation():
                    publisher = Publisher(root); publisher.add(b"first"); publisher.add(b"second")
                    if corrupt:
                        with self.assertRaises(ContractError): publisher.flush()
                    else: publisher.flush()
                self.assertEqual([], list((root / PACKS).glob(".lks-pack-*")))
                if corrupt:
                    self.assertEqual(b"corrupt winner", next((root / PACKS).glob("*.zip")).read_bytes())
                else: self.assertEqual(b"first", read_object(root, reference(b"first")))

    def test_batch_splitting_and_large_object_fallback(self):
        with patch("object_zip.TARGET", 512):
            refs = self.publish([b"first", b"second", b"third", b"x" * 513])
        self.assertEqual(1, len(list((self.root / PACKS).glob("*.zip"))))
        self.assertEqual(2, len(list((self.root / OBJECTS).glob("*"))))
        for ref in refs: self.assertEqual(ref["bytes"], len(read_object(self.root, ref)))

    def test_concurrent_packed_copy_cannot_invalidate_recovery_before_commit(self):
        from path_utils import publish_new_file
        target = "src/pending.txt"
        write_one(self.root, target, b"before")
        changes = {target: b"after"}
        plan = preview(self.root, changes, sources={}, operation="packed-backup-race")
        competitor = []
        def race(path, raw, **options):
            result = publish_new_file(path, raw, **options)
            if options.get("prefix") == ".lks-pack-":
                competitor.append(self.container([(sha(b"before"), b"BEFORE")]))
            return result
        with patch("path_utils.publish_new_file", side_effect=race):
            with self.assertRaises(ContractError):
                apply(self.root, changes, plan, plan["preview_hash"])
        self.assertEqual(b"before", (self.root / target).read_bytes())
        self.assertFalse((self.root / PENDING).exists())
        self.assertEqual(1, len(competitor))
        self.assertTrue(competitor[0].exists())

    def test_central_name_with_hidden_suffix_is_rejected(self):
        body = b"strict flat hash name"
        raw = bytearray(encode({sha(body): body}))
        central = raw.index(b"PK\x01\x02")
        suffix = b"\0../hidden"
        raw[central + 46 + 64:central + 46 + 64] = suffix
        struct.pack_into("<H", raw, central + 28, 64 + len(suffix))
        struct.pack_into("<L", raw, len(raw) - 22 + 12, 110 + len(suffix))
        write_one(self.root, PACKS + sha(raw) + ".zip", bytes(raw))
        with self.assertRaises(ContractError): read_object(self.root, reference(body))

    def pin_reader(self):
        distribution = (ROOT / "distribution/dual.json").read_bytes()
        runtime = ".lks-sdd/runtime/synthetic-zip-reader"
        files = {}
        for module in ("object_zip.py", "v2_contract.py", "content_store.py", "v2_storage.py"):
            name = "scripts/" + module; raw = (ROOT / name).read_bytes()
            write_one(self.root, runtime + "/" + name, raw); files[name] = sha(raw)
        write_one(self.root, runtime + "/distribution/dual.json", distribution)
        write_one(self.root, ".lks-sdd/distribution-lock.json", json.dumps(
            {"storage_formats": json.loads(distribution)["storage_formats"],
             "runtime": runtime, "runtime_files": files}).encode())
        return runtime

    def test_reader_capability_is_fresh_at_publication(self):
        runtime = self.pin_reader()
        for changed in (".lks-sdd/distribution-lock.json", runtime + "/scripts/v2_contract.py"):
            with self.subTest(changed=changed):
                self.pin_reader()
                publisher = Publisher(self.root)
                publisher.add(b"first " + changed.encode()); publisher.add(b"second " + changed.encode())
                replacement = (b'{"storage_formats":["lks-sdd-object/1"]}'
                               if changed.endswith("distribution-lock.json") else b"altered reader")
                write_one(self.root, changed, replacement)
                before = self.files()
                with self.assertRaises(ContractError): publisher.flush()
                self.assertEqual(before, self.files())

    def test_reader_change_during_publication_aborts_before_journal(self):
        from path_utils import publish_new_file
        self.pin_reader()
        target = "src/pending.txt"
        write_one(self.root, target, b"before")
        changes = {target: b"after"}
        plan = preview(self.root, changes, sources={}, operation="reader-publication-race")
        def race(path, raw, **options):
            result = publish_new_file(path, raw, **options)
            if options.get("prefix") == ".lks-pack-":
                write_one(self.root, ".lks-sdd/distribution-lock.json", b'{"storage_formats":[]}')
            return result
        with patch("path_utils.publish_new_file", side_effect=race):
            with self.assertRaises(ContractError): apply(self.root, changes, plan, plan["preview_hash"])
        self.assertEqual(b"before", (self.root / target).read_bytes())
        self.assertFalse((self.root / PENDING).exists())

    def test_short_footer_read_is_a_contract_error(self):
        from contextlib import contextmanager
        import object_zip
        @contextmanager
        def truncated(*args): yield io.BytesIO(b""), 22, None
        with patch("object_zip._opened", truncated), self.assertRaises(ContractError):
            object_zip._index(self.root, PACKS + "0" * 64 + ".zip", 1024)

    def test_pack_changed_after_full_hash_cannot_commit(self):
        import object_zip
        target = "src/pending.txt"
        write_one(self.root, target, b"before")
        changes = {target: b"after"}
        plan = preview(self.root, changes, sources={}, operation="pack-hash-index-race")
        original = object_zip._index
        def changed(root, name, budget):
            path = root / name
            raw = bytearray(path.read_bytes()); raw[94] ^= 1; path.write_bytes(raw)
            return original(root, name, budget)
        with patch("object_zip._index", side_effect=changed):
            with self.assertRaises(ContractError): apply(self.root, changes, plan, plan["preview_hash"])
        self.assertEqual(b"before", (self.root / target).read_bytes())
        self.assertFalse((self.root / PENDING).exists())

    def test_old_pin_keeps_loose_publication_and_forged_capability_blocks(self):
        from object_zip import FORMAT
        lock = self.root / ".lks-sdd/distribution-lock.json"; lock.parent.mkdir()
        lock.write_text(json.dumps({"storage_formats": ["lks-sdd-object/1"]}), encoding="utf-8")
        self.publish([b"legacy first", b"legacy second"])
        self.assertFalse((self.root / PACKS).exists())
        self.container([(sha(b"third"), b"third")])
        before = self.files()
        with self.assertRaisesRegex(ContractError, "lacks ZIP capability"): Publisher(self.root)
        self.assertEqual(before, self.files())
        lock.write_text(json.dumps({"storage_formats": [FORMAT]}), encoding="utf-8")
        before = self.files()
        with self.assertRaises(ContractError): Publisher(self.root)
        self.assertEqual(before, self.files())

    def test_declared_pinned_reader_must_match_its_inventory(self):
        runtime = self.pin_reader()
        with evaluation():
            publisher = Publisher(self.root)
            self.assertTrue(publisher.enabled)
            publisher.add(b"first"); publisher.add(b"second"); publisher.flush()
        write_one(self.root, runtime+"/scripts/v2_contract.py", b"changed reader")
        before = self.files()
        with self.assertRaisesRegex(ContractError, "reader integrity"): Publisher(self.root)
        self.assertEqual(before, self.files())

    def test_business_apply_cannot_change_zip_containers(self):
        for name, body in [(PACKS.rstrip("/"), b"bad"), (PACKS+"0"*64+".zip", b"bad"),
                           (PACKS.upper()+"0"*64+".zip", b"bad")]:
            plan = preview(self.root, {name: body}, sources={}, operation="invalid-container-write")
            before = self.files()
            with self.assertRaises(ContractError): apply(self.root, {name: body}, plan, plan["preview_hash"])
            self.assertEqual(before, self.files())

    @unittest.skipUnless(sys.platform == "win32", "Windows short paths")
    def test_windows_short_alias_does_not_bypass_container_guard(self):
        from path_utils import short_existing_path
        from v2_storage import _pack_path
        (self.root / PACKS).mkdir(parents=True)
        short = short_existing_path(self.root / ".lks-sdd")
        alias = short.name + "/objects/packs/" + "0" * 64 + ".zip"
        self.assertTrue(_pack_path(self.root, alias))
        changes = {alias: b"bad"}
        plan = preview(self.root, changes, sources={}, operation="short-pack-alias")
        before = self.files()
        with self.assertRaises(ContractError): apply(self.root, changes, plan, plan["preview_hash"])
        self.assertEqual(before, self.files())

    @unittest.skipUnless(sys.platform == "win32", "Windows long paths")
    def test_long_windows_object_and_journal_paths(self):
        import shutil
        from path_utils import filesystem_root, same_filesystem_path
        target = self.root / ("deep-"+"a"*75) / ("deep-"+"b"*75) / ("deep-"+"c"*75) / "consumidor ñ con espacios"
        self.assertTrue(target.absolute().is_relative_to(self.root.absolute()))
        long = filesystem_root(target, force_extended=True)
        def cleanup():
            owned = filesystem_root(self.root, force_extended=True)
            self.assertTrue(same_filesystem_path(owned, Path(self.temp.name)))
            if owned.exists(): shutil.rmtree(owned)
        self.addCleanup(cleanup)
        long.mkdir(parents=True)
        changes = {"docs/lks-sdd/evidence/long.txt": b"after"}
        plan = preview(long, changes, sources={}, operation="long-storage-component")
        with self.assertRaises(InterruptedError):
            apply(long, changes, plan, plan["preview_hash"], interrupt_after=1)
        recover(long, plan["preview_hash"], rollback=True)
        self.assertFalse((long / PENDING).exists())
        self.assertTrue(list((long / PACKS).glob("*.zip")))

    def test_grouped_content_in_referenced_packet_and_native_staging(self):
        from v3_packet import Spool, finish, read, Payload
        from v3_storage import staged_write
        from object_zip import stage_writer
        packet_dir = self.root / "packet"
        spool = Spool(packet_dir)
        bodies = [b"packet first", b"packet second"]
        for body in bodies: prepare_object(self.root, body, spool)
        packet = finish({"summary": {}}, spool)
        loaded = read(packet_dir / "packet.json"); payload = Payload(loaded)
        target = self.root / "stage"; target.mkdir()
        with evaluation():
            write, flush = stage_writer(target, staged_write)
            for name, raw in payload.items(): write(name, raw)
            flush()
            for body in bodies: self.assertEqual(body, read_object(target, reference(body)))
        self.assertEqual([], list((target / OBJECTS).glob("*")))
        self.assertEqual(1, len(list((target / PACKS).glob("*.zip"))))


if __name__ == "__main__": unittest.main()
