"""Synthetic histories and inventories exercise public transitions and recovery."""
from __future__ import annotations

import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from eval_support import authorize_implementation, materialize_ready_project
from content_store import OBJECTS, inventory, object_path, prepare_inventory, read_object
from v2_authoring import author, catalog, edit_elements, historical, history_changes
from v2_contract import ContractError, DOCS, HISTORY, READER, canonical, fingerprint, load, make_element, read_bytes, render_document, sha
from v2_controls import correction
from v2_history import export_history, read_manifest, restore_changes
from v2_lifecycle import checkpoint, diff_guard, report_problem, resume, start
from v2_storage import PENDING, apply, preview, recover, write_one


def persist(root, changes, sources=None, operation="synthetic-fixture", **kwargs):
    plan = preview(root, changes, sources=sources or {}, operation=operation)
    return apply(root, changes, plan, plan["preview_hash"], **kwargs)


def transition(root, function, *args, **kwargs):
    plan = function(load(root), *args, **kwargs)
    return function(load(root), *args, authorized_hash=plan["preview_hash"], **kwargs)


class DocumentStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lks-document-storage-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        materialize_ready_project(self.root, "storage-synthetic")

    def test_exact_states_with_changes_moves_retirement_and_legacy_links(self):
        root = self.root
        feature = DOCS + "/02-specification/features/stable.md"
        asset = DOCS + "/02-specification/features/assets/image.bin"
        entry = make_element("FTR-002", "feature", "Stable", "Preserve this literal contract.", state="confirmed")
        write_one(root, asset, b"stable-image" * 2048)
        request = {"documents": [{"path": feature, "text": render_document("feature", "Stable", [entry], preamble="![image](assets/image.bin)").decode()}]}
        plan, changes = author(load(root), request)
        apply(root, changes, plan, plan["preview_hash"])
        states = []
        for i in range(3):
            model = load(root); model.require_valid()
            expected = {p: read_bytes(root, p, limit=16*1024*1024) for p in model.hashes}
            revision = model.snapshot()
            states.append((revision, expected))
            item = model.elements["FTR-002"]
            meta = dict(item.meta, revision=item.meta["revision"] + 1, state="retired" if i == 2 else "confirmed")
            revised = edit_elements(model, {item.id: meta}, {item.id: "Literal contract revision " + str(i)})
            destination = feature.replace("stable.md", "moved.md") if i == 1 else item.path
            request = {"documents": [{"path": destination, "text": revised[item.path].decode()}]}
            if i == 1: request["moves"] = [{"from": item.path, "to": destination}]
            plan, changes = author(model, request)
            apply(root, changes, plan, plan["preview_hash"])
        for revision, expected in states:
            self.assertEqual(expected, restore_changes(root, revision))
            self.assertEqual(set(expected), {d["source"] for d in historical(root, revision)["documents"]})
            with tempfile.TemporaryDirectory(prefix="lks-history-export-") as parent:
                output = Path(parent) / "exact-state"
                export_history(root, revision, output)
                self.assertEqual(expected, {p.relative_to(output).as_posix(): p.read_bytes() for p in output.rglob("*") if p.is_file()})
                load(output).require_valid()
                with self.assertRaises(ContractError): export_history(root, revision, output)
        self.assertFalse((root / feature).exists())  # supported move deletes the old path
        self.assertEqual(load(root).elements["FTR-002"].meta["uid"], entry["meta"]["uid"])
        self.assertEqual(load(root).elements["FTR-002"].meta["state"], "retired")
        image_copies = [p for p in root.rglob("*") if p.is_file() and p.read_bytes() == read_bytes(root, asset)]
        self.assertEqual(len(image_copies), 1)  # active resource; shared CAS bytes are now packed
        ref = read_manifest(root, states[0][0])["sources"][asset]["object"]
        self.assertEqual(read_bytes(root, asset), read_object(root, ref))
        revision, expected = states[0]
        virtual = HISTORY + "/" + revision[:16] + "/tree/" + feature
        self.assertEqual(read_bytes(root, virtual), expected[feature])
        link_path = DOCS + "/01-context/history-link.md"
        import posixpath
        link = posixpath.relpath(virtual, posixpath.dirname(link_path)) + "#ftr-002"
        request = {"documents": [{"path": link_path, "text": render_document("context", "History", [], preamble="[FTR-002](<" + link + ">)").decode()}]}
        plan, changes = author(load(root), request)
        apply(root, changes, plan, plan["preview_hash"], validator=lambda: load(root).require_valid())
        definitions = catalog(load(root))["features"]
        self.assertGreaterEqual(len(next(f for f in definitions if f["id"] == "FTR-002")["definitions"]), 3)

    def test_legacy_history_coexists_without_rewriting_it(self):
        model = load(self.root)
        revision = model.snapshot()
        prefix = HISTORY + "/" + revision[:16]
        mapping, changes = {}, {}
        for name, digest in model.hashes.items():
            archive = prefix + "/tree/" + name
            changes[archive] = read_bytes(self.root, name)
            mapping[name] = {"path": archive, "sha256": digest}
        manifest = canonical({"schema_version": "2.0", "snapshot": revision, "state": "historical", "sources": mapping})
        changes[prefix + "/snapshot.json"] = manifest
        persist(self.root, changes)
        self.assertEqual(restore_changes(self.root, revision), {p: read_bytes(self.root, p) for p in model.hashes})
        self.assertEqual(history_changes(model), (revision, {}))
        self.assertEqual(read_bytes(self.root, prefix + "/snapshot.json"), manifest)
        write_one(self.root, mapping[next(iter(mapping))]["path"], b"altered")
        with self.assertRaises(ContractError): historical(self.root, revision)

    def test_interrupted_legacy_tree_recovers_before_its_manifest_is_written(self):
        model = load(self.root)
        revision = model.snapshot()
        prefix = HISTORY + "/" + revision[:16]
        changes, mapping = {}, {}
        expected = {p: read_bytes(self.root, p) for p in model.hashes}
        for name, raw in expected.items():
            archive = prefix + "/tree/" + name
            changes[archive] = raw
            mapping[name] = {"path": archive, "sha256": sha(raw)}
        changes[prefix + "/snapshot.json"] = canonical({"schema_version": "2.0", "snapshot": revision,
                                                        "state": "historical", "sources": mapping})
        plan = preview(self.root, changes, sources=model.hashes, operation="legacy-tree-interrupted")
        journal = {"schema_version": "2.0", "preview": plan, "state": "applying",
                   "before": {p: None for p in changes},
                   "after": {p: base64.b64encode(raw).decode() for p, raw in changes.items()}}
        write_one(self.root, PENDING, canonical(journal))
        first = next(iter(changes)); write_one(self.root, first, changes[first])
        result = recover(self.root, plan["preview_hash"])
        self.assertEqual(restore_changes(self.root, revision), expected)
        recover(self.root, plan["preview_hash"], rollback=True, receipt=result["receipt"])
        self.assertTrue(all(not (self.root/p).exists() for p in changes))
        self.assertEqual({p: read_bytes(self.root, p) for p in model.hashes}, expected)

    def test_cas_links_cannot_be_shadowed_by_physical_files(self):
        revision, changes = history_changes(load(self.root))
        persist(self.root, changes)
        source = DOCS + "/01-context/project.md"
        manifest = read_manifest(self.root, revision)
        virtual = manifest["sources"][source]["path"]
        original = read_bytes(self.root, virtual)
        # An export/cache/foreign writer must not replace the manifest's authority.
        write_one(self.root, virtual, b"foreign historical content")
        with self.assertRaises(ContractError): read_bytes(self.root, virtual)
        write_one(self.root, virtual, original)
        ref = manifest["sources"][source]["object"]
        write_one(self.root, object_path(ref), b"altered object behind an intact copy")
        with self.assertRaises(ContractError): read_bytes(self.root, virtual)

    def test_export_preserves_referenced_history_and_protects_its_manifest(self):
        root = self.root
        revision, changes = history_changes(load(root))
        persist(root, changes)
        source = DOCS + "/01-context/project.md"
        manifest = read_manifest(root, revision)
        virtual = manifest["sources"][source]["path"]
        import posixpath
        link_path = DOCS + "/01-context/antecedent.md"
        link = posixpath.relpath(virtual, posixpath.dirname(link_path))
        request = {"documents": [{"path": link_path, "text": render_document("context", "Antecedent", [], preamble="[Earlier context](<" + link + ">)").decode()}]}
        plan, changes = author(load(root), request)
        apply(root, changes, plan, plan["preview_hash"], validator=lambda: load(root).require_valid())
        model = load(root); model.require_valid()
        linked_revision, changes = history_changes(model)
        persist(root, changes, model.hashes)
        with tempfile.TemporaryDirectory(prefix="lks-linked-export-") as parent:
            output = Path(parent) / "state"
            export_history(root, linked_revision, output)
            load(output).require_valid()
            self.assertEqual(read_bytes(output, virtual), read_bytes(root, virtual))
            (output / virtual).unlink()  # the independent manifest/object still resolves it
            self.assertEqual(read_bytes(output, virtual), read_bytes(root, virtual))
            load(output).require_valid()
        manifest_path = HISTORY + "/" + revision[:16] + "/snapshot.json"
        self.assertIn(manifest_path, model.hashes)
        write_one(root, manifest_path, b"altered after preview")
        with self.assertRaises(ContractError): model.revalidate()

    def test_export_preserves_a_destination_created_during_reconstruction(self):
        import v2_history
        revision, changes = history_changes(load(self.root)); persist(self.root, changes)
        publish = v2_history._publish_directory
        with tempfile.TemporaryDirectory(prefix="lks-export-race-") as parent:
            destination = Path(parent)/"competing-output"
            def competing_destination(stage, target):
                target.mkdir()
                return publish(stage, target)
            with patch("v2_history._publish_directory", competing_destination):
                with self.assertRaises(FileExistsError): export_history(self.root, revision, destination)
            self.assertTrue(destination.is_dir())
            self.assertEqual(list(destination.iterdir()), [])
            self.assertEqual(list(Path(parent).glob(".lks-history-export-*")), [])

    def test_export_refuses_unsupported_exclusive_rename_without_overwriting(self):
        import errno
        import os
        from types import SimpleNamespace
        from unittest.mock import Mock
        from v2_history import _publish_directory
        safe_os = SimpleNamespace(name="posix", fsencode=os.fsencode, strerror=os.strerror,
                                  rename=Mock(side_effect=AssertionError("unsafe POSIX fallback")))
        for platform, symbol in (("linux", "renameat2"), ("darwin", "renamex_np")):
            with self.subTest(platform=platform), patch("v2_history.os", safe_os), patch("v2_history.sys.platform", platform):
                library = SimpleNamespace(**{symbol: Mock(return_value=-1)})
                with patch("v2_history.ctypes.CDLL", return_value=library), patch("v2_history.ctypes.get_errno", return_value=errno.EEXIST):
                    with self.assertRaises(FileExistsError): _publish_directory(self.root/"stage", self.root/"destination")
                with patch("v2_history.ctypes.CDLL", return_value=SimpleNamespace()):
                    with self.assertRaises(ContractError): _publish_directory(self.root/"stage", self.root/"destination")

    def test_inventory_budget_is_checked_before_reading_another_object(self):
        changes = {}
        ref = prepare_inventory(self.root, {"src/a": "1"*64}, changes)
        # Budget exhaustion must not parse the next object before rejecting it.
        cache = {("already-loaded", 32 * 1024 * 1024): {}}
        with patch("content_store.read_object", side_effect=AssertionError("over-budget read")):
            with self.assertRaisesRegex(ContractError, "byte budget exceeded"):
                inventory(self.root, {"files_ref": ref}, "files", cache=cache)

    def test_read_remains_bounded_if_the_file_grows_after_stat(self):
        name, budget = "assets/growing.bin", 4
        write_one(self.root, name, b"abcd")
        original_open = Path.open
        class GrowingReader:
            def __init__(self, stream): self.stream = stream
            def __enter__(self): return self
            def __exit__(self, *args): self.stream.close()
            def fileno(self): return self.stream.fileno()
            def read(self, amount=-1):
                if not 0 < amount <= budget + 1: raise AssertionError("unbounded read after growth")
                return self.stream.read(amount)
        def growing_open(path, *args, **kwargs):
            if path == self.root/name and (args[0] if args else kwargs.get("mode")) == "rb":
                with original_open(path, "ab") as writer: writer.write(b"grew after stat")
                return GrowingReader(original_open(path, *args, **kwargs))
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", growing_open):
            with self.assertRaises(ContractError): read_bytes(self.root, name, limit=budget)

    def test_object_publication_does_not_overwrite_an_existing_raced_object(self):
        from content_store import prepare_object
        root = self.root
        target, before, after = "src/publication.txt", b"before", b"new bytes to publish"
        write_one(root, target, before)
        changes = {target: after}
        plan = preview(root, changes, sources={}, operation="publication-race")
        object_name = OBJECTS + sha(after)
        from path_utils import publish_new_file
        def raced_publish(path, raw, **options):
            if options.get("prefix") == ".lks-pack-":
                write_one(root, object_name, b"foreign damaged object")
            return publish_new_file(path, raw, **options)
        with patch("path_utils.publish_new_file", raced_publish):
            with self.assertRaises(ContractError): apply(root, changes, plan, plan["preview_hash"])
        self.assertEqual(read_bytes(root, target), before)
        self.assertEqual((root / object_name).read_bytes(), b"foreign damaged object")
        self.assertFalse((root / PENDING).exists())

    def test_object_publication_verifies_the_winner_of_an_atomic_creation_race(self):
        from content_store import publish_object
        import os
        root, raw = self.root, b"concurrent identical content"
        name = OBJECTS + sha(raw)
        primitive = "rename" if os.name == "nt" else "link"
        real_publish = getattr(os, primitive)
        def competing_publish(temporary, target):
            write_one(root, name, raw)  # another publisher wins after the existence check
            return real_publish(temporary, target)
        with patch("path_utils.os." + primitive, competing_publish):
            publish_object(root, name, raw)
        self.assertEqual(read_bytes(root, name), raw)
        self.assertEqual(list((root / OBJECTS).glob(".lks-object-*")), [])
        write_one(root, name, b"damaged winner")
        with self.assertRaises(ContractError): publish_object(root, name, raw)
        self.assertEqual((root / name).read_bytes(), b"damaged winner")

    def test_tampered_objects_manifests_and_source_races_fail(self):
        model = load(self.root)
        revision, changes = history_changes(model)
        persist(self.root, changes)
        manifest = read_manifest(self.root, revision)
        source = next(iter(manifest["sources"]))
        ref = manifest["sources"][source]["object"]
        raw = read_object(self.root, ref)
        write_one(self.root, object_path(ref), b"altered")
        with self.assertRaises(ContractError): historical(self.root, revision)
        write_one(self.root, object_path(ref), raw)
        name = HISTORY + "/" + revision[:16] + "/snapshot.json"
        damaged = dict(manifest, sources={k: v for k, v in manifest["sources"].items() if k != source})
        write_one(self.root, name, canonical(damaged))
        with self.assertRaises(ContractError): historical(self.root, revision)
        write_one(self.root, name, canonical(manifest))
        write_one(self.root, DOCS + "/01-context/project.md", b"raced")
        with self.assertRaises(ContractError): history_changes(model)

    def test_inventories_reused_across_execution_checkpoints_correction_and_replan(self):
        root = self.root
        for i in range(24): write_one(root, f"src/file-{i}.txt", (str(i) + "\n").encode())
        authorize_implementation(root)
        auth_bytes = read_bytes(root, DOCS + "/00-control/authorizations/AUTH-001.md")
        transition(root, start, ["TASK-001"], "test", actor="fixture-owner", at="2026-01-02T00:00:00+00:00",
                   technology=lambda *_: {"status": "documented"})
        execution = load(root).by_kind("execution")[0]
        ref = execution.meta["baseline_files_ref"]
        for i in range(4):
            transition(root, checkpoint, tasks=["TASK-001"], state="paused", actor="fixture-owner",
                       at=f"2026-01-02T00:00:0{i}+00:00", summary=f"Literal checkpoint {i}", next_action="Resume scoped work")
        model = load(root); model.require_valid()
        self.assertTrue(all(e.meta["files_ref"] == ref for e in model.by_kind("checkpoint")))
        self.assertEqual(read_bytes(root, DOCS + "/00-control/authorizations/AUTH-001.md"), auth_bytes)
        self.assertEqual(diff_guard(model)["changed"], [])
        self.assertEqual(resume(model, ["TASK-001"])["reasons"], [])
        transition(root, report_problem, ["TASK-001"], description="Literal observed problem", actor="fixture-owner", at="2026-01-02T00:00:10+00:00")
        transition(root, correction, ["TASK-001"], actor="fixture-owner", reason="Correct observed problem", at="2026-01-02T00:00:11+00:00")
        model = load(root)
        revision = model.snapshot()
        expected = {p: read_bytes(root, p, limit=16*1024*1024) for p in model.hashes}
        transition(root, correction, ["TASK-001"], actor="fixture-owner", reason="Explicit replan", at="2026-01-02T00:00:12+00:00", replan=True)
        self.assertEqual(restore_changes(root, revision), expected)
        model = load(root); model.require_valid()
        self.assertEqual(model.elements["AUTH-001"].meta["state"], "revoked")
        self.assertEqual(model.elements[execution.id].meta["uid"], execution.meta["uid"])
        self.assertEqual(model.elements["PROB-001"].body.strip().splitlines()[-1], "Literal observed problem")
        # Both old inline maps and references are resolved with identical semantics.
        self.assertEqual(inventory(root, {"files": inventory(root, {"files_ref": ref}, "files")}, "files"), inventory(root, {"files_ref": ref}, "files"))
        raw = read_object(root, ref)
        write_one(root, object_path(ref), b"tampered inventory")
        self.assertFalse(load(root).valid)
        write_one(root, object_path(ref), raw)
        load(root).require_valid()

    def test_interrupted_history_recover_rollback_and_legacy_journal(self):
        root = self.root
        model = load(root)
        revision, archive = history_changes(model)
        path = DOCS + "/01-context/addition.md"
        changes = {**archive, path: render_document("context", "Addition", [], preamble="Literal addition")}
        plan = preview(root, changes, sources=model.hashes, operation="synthetic-history")
        with self.assertRaises(InterruptedError): apply(root, changes, plan, plan["preview_hash"], interrupt_after=2)
        self.assertEqual(json.loads(read_bytes(root, PENDING))["schema_version"], "2.1")
        recover(root, plan["preview_hash"])
        self.assertTrue((root/path).exists())
        self.assertEqual(historical(root, revision)["status"], "available")
        load(root).require_valid()
        # Legacy base64 receipts still roll back exactly, including deletions.
        target = "src/legacy.txt"
        write_one(root, target, b"before")
        old = preview(root, {target: b"after"}, sources={}, operation="legacy")
        journal = {"schema_version": "2.0", "preview": old, "state": "applying",
                   "before": {target: base64.b64encode(b"before").decode()}, "after": {target: base64.b64encode(b"after").decode()}}
        write_one(root, PENDING, canonical(journal)); write_one(root, target, b"after")
        recover(root, old["preview_hash"], rollback=True)
        self.assertEqual(read_bytes(root, target), b"before")
        plan = preview(root, {target: None}, sources={}, operation="delete-fixture")
        with self.assertRaises(InterruptedError): apply(root, {target: None}, plan, plan["preview_hash"], interrupt_after=1)
        recover(root, plan["preview_hash"], rollback=True)
        self.assertEqual(read_bytes(root, target), b"before")

    def test_resources_bounds_and_ambiguous_refs_remain_enforced(self):
        changes = {}
        ref = prepare_inventory(self.root, {"src/a": "1"*64}, changes)
        for p, raw in changes.items(): write_one(self.root, p, raw)
        for meta in ({"files_ref": dict(ref, format="future")}, {"files_ref": ref, "files": {}},
                     {"files_ref": dict(ref, sha256="../escape")}, {"files": {"../escape": "1"*64}},
                     {"files": {"src/invalid\0name": "1"*64}}):
            with self.assertRaises(ContractError): inventory(self.root, meta, "files")
        for i in range(9):
            write_one(self.root, DOCS + f"/01-context/large-{i}.md", render_document("context", "Large", [], preamble="x" * (3900*1024)))
        with self.assertRaisesRegex(ContractError, "Document byte budget exceeded"): load(self.root)

    def test_repeated_inventory_that_exceeds_active_budget_fits_as_exact_references(self):
        files = {"src/" + "stable-component-"*4 + f"{i:05}.txt": sha(str(i).encode()) for i in range(5000)}
        inline, entries = 0, []
        for i in range(60):
            entry = make_element(f"CKPT-{i+100:03}", "checkpoint", "Observed checkpoint", "Literal observed continuity, actor and evidence retained.",
                                 state="active", nature="fact", actor="synthetic-human", files=files, evidence_ids=["EVID-synthetic"])
            path = DOCS + f"/04-delivery/checkpoints/{entry['meta']['id']}.md"
            raw = render_document("checkpoint", "Checkpoint", [entry])
            inline += len(raw); write_one(self.root, path, raw); entries.append((path, entry))
        self.assertGreater(inline, 32 * 1024 * 1024)
        with self.assertRaisesRegex(ContractError, "Document byte budget exceeded"): load(self.root)
        objects = {}
        ref = prepare_inventory(self.root, files, objects)
        for path, raw in objects.items(): write_one(self.root, path, raw)
        referenced = 0
        for path, entry in entries:
            del entry["meta"]["files"]; entry["meta"]["files_ref"] = ref
            raw = render_document("checkpoint", "Checkpoint", [entry])
            referenced += len(raw); write_one(self.root, path, raw)
        model = load(self.root); model.require_valid()
        self.assertLess(referenced, inline // 100)
        cache = {}
        for _, entry in entries:
            actual = model.elements[entry["meta"]["id"]]
            self.assertEqual(actual.meta["uid"], entry["meta"]["uid"])
            self.assertEqual(actual.meta["evidence_ids"], ["EVID-synthetic"])
            self.assertEqual(inventory(self.root, actual.meta, "files", cache=cache), files)

    def test_history_and_recovery_preserve_external_assets_evidence_and_later_work(self):
        root = self.root
        resource = "assets/synthetic-image.png"
        api = "contracts/openapi.json"
        original_image = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aIskAAAAASUVORK5CYII=")
        original_api = canonical({"openapi": "3.1.0", "info": {"title": "Synthetic contract", "version": "1.0.0"}, "paths": {"/example": {"get": {"responses": {"200": {"description": "Literal response"}}}}}})
        evidence = DOCS + "/evidence/EVID-synthetic.json"
        write_one(root, resource, original_image)
        write_one(root, api, original_api)
        write_one(root, evidence, canonical({"evidence_id": "EVID-synthetic", "actor": "synthetic-human", "subject": sha(b"test"), "checks": [{"outcome": "passed"}]}))
        model = load(root)
        path = model.elements["TASK-001"].path
        request = {"documents": [{"path": path, "text": model.documents[path] + "\n\n![asset](../../../assets/synthetic-image.png)\n\n[API](../../../contracts/openapi.json)\n\n[Evidence](../evidence/EVID-synthetic.json)\n"}]}
        plan, changes = author(load(root), request); apply(root, changes, plan, plan["preview_hash"])
        model = load(root)
        self.assertEqual(model.normative({"TASK-001"})["text_attachments"][api], original_api.decode())
        revision, archive = history_changes(model)
        persist(root, archive, model.hashes)
        write_one(root, resource, b"modified binary")
        write_one(root, api, canonical({"openapi": "3.1.0", "info": {"version": "2.0.0"}}))
        self.assertEqual(restore_changes(root, revision)[resource], original_image)
        self.assertEqual(restore_changes(root, revision)[api], original_api)
        self.assertEqual(restore_changes(root, revision)[evidence], read_bytes(root, evidence))
        code = "src/interrupted.txt"
        write_one(root, code, b"before")
        plan = preview(root, {code: b"after"}, sources=load(root).hashes, operation="interrupt-conflict")
        with self.assertRaises(InterruptedError): apply(root, {code: b"after"}, plan, plan["preview_hash"], interrupt_after=1)
        write_one(root, code, b"later human work")
        with self.assertRaisesRegex(ContractError, "later work preserved"): recover(root, plan["preview_hash"], rollback=True)
        self.assertEqual(read_bytes(root, code), b"later human work")

    def test_failure_before_journal_leaves_only_unreferenced_immutable_objects(self):
        from path_utils import publish_new_file
        model = load(self.root)
        original = {p: read_bytes(self.root, p) for p in model.hashes}
        revision, changes = history_changes(model)
        plan = preview(self.root, changes, sources=model.hashes, operation="synthetic-pre-journal")
        def interrupted_write(path, raw, **options):
            publish_new_file(path, raw, **options)
            if options.get("prefix") == ".lks-pack-":
                raise InterruptedError("Synthetic failure after immutable publication, before journal")
        with patch("path_utils.publish_new_file", interrupted_write):
            with self.assertRaises(InterruptedError): apply(self.root, changes, plan, plan["preview_hash"])
        self.assertFalse((self.root/PENDING).exists())
        self.assertEqual(original, {p: read_bytes(self.root, p) for p in model.hashes})
        load(self.root).require_valid()
        revision, changes = history_changes(load(self.root))
        persist(self.root, changes, load(self.root).hashes)
        self.assertEqual(restore_changes(self.root, revision), original)

    def test_failed_journal_sync_exposes_no_partial_pending_record(self):
        target, before, after = "src/journal-sync.txt", b"before", b"after"
        write_one(self.root, target, before)
        changes = {target: after}
        plan = preview(self.root, changes, sources={}, operation="journal-sync-failure")
        syncing_journal = False
        def journal_bytes(value):
            nonlocal syncing_journal
            if isinstance(value, dict) and value.get("state") == "applying": syncing_journal = True
            return canonical(value)
        import os
        real_sync = os.fsync
        def interrupted_sync(descriptor):
            if syncing_journal: raise InterruptedError("interrupted pending journal sync")
            return real_sync(descriptor)
        with patch("v2_storage.canonical", journal_bytes), patch("path_utils.os.fsync", interrupted_sync):
            with self.assertRaises(InterruptedError): apply(self.root, changes, plan, plan["preview_hash"])
        self.assertFalse((self.root/PENDING).exists())
        self.assertEqual(list((self.root/".lks-sdd").glob(".lks-transaction-*")), [])
        self.assertEqual(read_bytes(self.root, target), before)
        persist(self.root, changes)
        self.assertEqual(read_bytes(self.root, target), after)

    def test_late_source_change_before_first_write_is_not_rolled_back(self):
        from path_utils import publish_new_file
        target, before, after = "src/late-writer.txt", b"before", b"after"
        write_one(self.root, target, before)
        changes = {target: after}
        plan = preview(self.root, changes, sources={target: sha(before)}, operation="late-writer")
        def later_writer(path, raw, **kwargs):
            # A competing transaction/editor completed while our objects were prepared.
            # Its bytes happen to match our target; they still do not belong to our write.
            write_one(self.root, target, after)
            return publish_new_file(path, raw, **kwargs)
        with patch("v2_storage.publish_new_file", later_writer):
            with self.assertRaises(ContractError): apply(self.root, changes, plan, plan["preview_hash"])
        self.assertEqual(read_bytes(self.root, target), after)
        self.assertFalse((self.root/PENDING).exists())

    def test_document_added_before_journal_ownership_invalidates_the_preview(self):
        from path_utils import publish_new_file
        target = "src/pending.txt"
        write_one(self.root, target, b"before")
        changes = {target: b"after"}
        plan = preview(self.root, changes, sources=load(self.root).hashes, operation="late-document")
        document = DOCS + "/01-context/later-human-input.md"
        literal = render_document("context", "New human input", [], preamble="Literal later human decision.")
        def later_writer(path, raw, **kwargs):
            write_one(self.root, document, literal)
            return publish_new_file(path, raw, **kwargs)
        with patch("v2_storage.publish_new_file", later_writer):
            with self.assertRaises(ContractError): apply(self.root, changes, plan, plan["preview_hash"])
        self.assertEqual(read_bytes(self.root, target), b"before")
        self.assertEqual(read_bytes(self.root, document), literal)
        self.assertFalse((self.root/PENDING).exists())

    def test_past_inventory_remains_readable_but_current_code_boundaries_block_work(self):
        root = self.root
        write_one(root, "src/module/a.txt", b"baseline")
        authorize_implementation(root)
        transition(root, start, ["TASK-001"], "test", actor="synthetic-human", at="2026-01-02T00:00:00+00:00",
                   technology=lambda *_: {"status": "documented"})
        previous = load(root)
        execution = previous.by_kind("execution")[0]
        baseline = inventory(root, execution.meta, "baseline_files")
        # Baseline keys describe a past state; loading their object must not read
        # these paths from a newly introduced nested repository.
        (root/"src/module/.git").write_text("gitdir: synthetic-nested-repository\n", encoding="utf-8")
        model = load(root); model.require_valid()
        self.assertEqual(inventory(root, model.elements[execution.id].meta, "baseline_files"), baseline)
        with self.assertRaisesRegex(ContractError, "Nested repository"):
            diff_guard(model)

    def test_cas_history_does_not_depend_on_the_present_original_source_location(self):
        root = self.root
        resource = "assets/module/image.bin"
        write_one(root, resource, b"historical exact image")
        path = DOCS + "/01-context/past-image.md"
        request = {"documents": [{"path": path, "text": render_document("context", "Resource", [], preamble="![Image](../../../assets/module/image.bin)").decode()}]}
        plan, changes = author(load(root), request); apply(root, changes, plan, plan["preview_hash"])
        model = load(root); revision, changes = history_changes(model); persist(root, changes, model.hashes)
        (root/"assets/module/.git").write_text("gitdir: synthetic-nested-repository\n", encoding="utf-8")
        self.assertEqual(restore_changes(root, revision)[resource], b"historical exact image")
        with tempfile.TemporaryDirectory(prefix="lks-past-source-export-") as parent:
            destination = Path(parent)/"past"
            export_history(root, revision, destination)
            load(destination).require_valid()
            self.assertEqual(read_bytes(destination, resource), b"historical exact image")


if __name__ == "__main__": unittest.main()
