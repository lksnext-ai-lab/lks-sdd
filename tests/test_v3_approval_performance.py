"""Differential correctness, invalidation, bounded lifetimes and isolation."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from approval_performance_support import ROOT, synthetic, key
sys.path.insert(0, str(ROOT / "scripts"))
from v3_contract import ContractError, Model, Element, element, location
from v3_approval import approved, descriptor
from v3_evaluation import evaluation, current, MAX_ENTRIES, MAX_UNITS, MAX_SOURCE_BYTES


class ApprovalPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="approval-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_differential_original_results_errors_sources_and_decisions(self):
        results = []
        for original in (True, False):
            output = self.root / ("old.json" if original else "new.json")
            command = [sys.executable, "-B", "-X", "utf8", str(ROOT / "tests/approval_probe.py"), "--output", str(output)]
            if original: command.append("--original")
            done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=120,
                                  env={**os.environ, "PYTHONHASHSEED": "0"})
            self.assertEqual(0, done.returncode, done.stderr)
            results.append(json.loads(output.read_bytes()))
        self.assertEqual(results[0], results[1])

    def test_all_identity_mutators_rebuild_and_do_not_retain_missing_results(self):
        model, tech, _, _ = synthetic(self.root, 40, 2)
        entry = tech[0]
        for change in (lambda: entry.meta.update(id="changed"),
                       lambda: entry.meta.__setitem__("id", "changed"),
                       lambda: setattr(entry, "meta", {**entry.meta, "id": "changed"})):
            entry.meta["id"] = "previous"; self.assertIs(entry, model.get("previous"))
            with self.assertRaises(ContractError): model.get("changed")
            change(); self.assertIs(entry, model.get("changed"))
            with self.assertRaises(ContractError): model.get("previous")
        draft = element("rule", "Added", "New model member", identifier=key("new"))
        new = Element(draft["meta"], draft["body"], location(draft))
        for mutate in (lambda: model.elements.__setitem__(new.uid, new),
                       lambda: model.elements.update({new.uid: new}),
                       lambda: model.elements.setdefault(new.uid, new),
                       lambda: model.elements.__ior__({new.uid: new}),
                       lambda: setattr(model, "elements", {**model.elements, new.uid: new})):
            model.elements.pop(new.uid, None)
            with self.assertRaises(ContractError): model.get(new.uid)
            mutate(); self.assertIs(new, model.get(new.uid))
        original_uid = entry.uid
        entry.meta["uid"] = key("new-identity")
        self.assertIs(entry, model.get(entry.uid))
        with self.assertRaises(ContractError): model.get(original_uid)
        entry.meta["kind"] = "requirement"
        self.assertIn(entry, model.by_kind("requirement"))
        self.assertNotIn(entry, model.by_kind("technology"))
        model.elements.popitem()
        model.elements.clear()
        with self.assertRaises(ContractError): model.get(entry.uid)

    def test_reinitializing_attached_element_preserves_observers_and_guards(self):
        model, technologies, _, _ = synthetic(self.root, 40, 2)
        entry = technologies[0]
        previous = entry.id
        replacement = copy.deepcopy(entry.meta)
        replacement["id"] = "reinitialized"
        model.get(previous)
        entry.__init__(replacement, entry.body, entry.path)
        self.assertIs(entry, model.get("reinitialized"))
        with self.assertRaises(ContractError): model.get(previous)
        entry.meta["id"] = "edited-after-reinitialization"
        self.assertIs(entry, model.get("edited-after-reinitialization"))
        unchanged = copy.deepcopy(entry.item())
        with self.assertRaisesRegex(ContractError, "modelo cambió"):
            with evaluation(model):
                try: entry.__init__(replacement, "rejected", entry.path)
                except ContractError: pass
        self.assertEqual(unchanged, entry.item())

    def test_single_reconstruction_and_original_parse_per_physical_path(self):
        import v3_approval, v3_scope, v3_migration
        model, tech, _, _ = synthetic(self.root, 150, 8, historical=True)
        with patch.object(v3_approval, "_Descriptors", wraps=v3_approval._Descriptors) as readers, \
             patch.object(v3_scope, "_memberships", wraps=v3_scope._memberships) as classifications, \
             patch.object(v3_migration, "read_bytes", wraps=v3_migration.read_bytes) as reads, \
             patch.object(v3_migration.v2, "parse_document", wraps=v3_migration.v2.parse_document) as parses:
            with evaluation(model):
                for e in tech:
                    self.assertTrue(approved(model, [e.uid], "technology")["valid"])
                    descriptor(model, [e.uid])
            self.assertEqual(1, readers.call_count)
            self.assertEqual(1, classifications.call_count)
            self.assertEqual(2, reads.call_count)
            self.assertEqual(2, parses.call_count)
        # An identical hash never substitutes one physical route for another.
        receipt = model.by_kind("migration")[0]
        path = receipt.data["content_confirmations"][tech[0].uid]["original"]
        (self.root / path).unlink()
        self.assertFalse(approved(model, [tech[0].uid], "technology")["valid"])

    def test_mixed_technology_mechanisms_remain_individual(self):
        model, tech, _, _ = synthetic(self.root, 65, 4)
        with evaluation(model):
            specific = [approved(model, [e.uid], "technology")["valid"] for e in tech]
            proposal = [approved(model, [e.uid])["valid"] for e in tech]
            self.assertEqual([True, False, True, False], specific)
            self.assertEqual([False, True, False, True], proposal)
            self.assertTrue(all(a or b for a, b in zip(specific, proposal)))

    def test_development_distribution_includes_and_imports_the_new_runtime_module(self):
        from build_dual_distribution import collect_development
        files = collect_development(ROOT)
        self.assertEqual((ROOT / "scripts/v3_evaluation.py").read_bytes(), files["scripts/v3_evaluation.py"])
        runtime_root = self.root / "packaged-runtime"
        for name, raw in files.items():
            if name.startswith("scripts/") and name.endswith(".py"):
                path = runtime_root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        code = """import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import v3_contract as c, v3_approval as a, v3_evaluation as e
model=c.Model(Path(sys.argv[1]).parent)
item=c.element('rule','Packaged rule','Complete synthetic obligation')
unit=c.Element(item['meta'],item['body'],'synthetic.md')
model.elements[unit.uid]=unit
print(json.dumps({'units':len(a.descriptor(model,[unit.uid])['units']),'module':e.__file__}))
"""
        done = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", "-c", code, str(runtime_root / "scripts")],
                              capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(0, done.returncode, done.stderr)
        value = json.loads(done.stdout)
        self.assertEqual(1, value["units"])
        self.assertTrue(Path(value["module"]).is_relative_to(runtime_root))

    def test_originals_changed_after_shared_read_are_rejected_before_materializing(self):
        from v3_storage import prepare
        model, tech, _, _ = synthetic(self.root, 40, 2, historical=True)
        with evaluation(model):
            self.assertTrue(approved(model, [tech[0].uid], "technology")["valid"])
        sources = dict(model.hashes)
        proof = model.by_kind("migration")[0].data["content_confirmations"][tech[0].uid]
        path = self.root / proof["original"]
        path.write_bytes(path.read_bytes() + b"\nconcurrent change")
        with self.assertRaisesRegex(ContractError, "fuente cambió"):
            prepare(self.root, [element("receipt", "Observed", "Synthetic result")], "synthetic", sources=sources)

    def test_revision_changes_invalidate_only_at_immutable_evaluation_boundaries(self):
        model, tech, _, _ = synthetic(self.root, 40, 2)
        self.assertTrue(approved(model, [tech[0].uid], "technology")["valid"])
        with self.assertRaisesRegex(ContractError, "modelo cambió"):
            with evaluation(model):
                approved(model, [tech[0].uid], "technology")
                tech[0].body += " New revision."
        self.assertTrue(approved(model, [tech[0].uid], "technology")["valid"])
        tech[0].body += " New revision."
        self.assertFalse(approved(model, [tech[0].uid], "technology")["valid"])
        for change in (lambda: tech[0].relations.setdefault("uses", []).append(tech[1].uid),
                       lambda: tech[0].meta["data"].update(global_rule="new"),
                       lambda: setattr(tech[0], "resolved_data", {"new": True})):
            with self.assertRaises(ContractError):
                with evaluation(model): change()
        self.assertIsNone(current(model))

    def test_deepcopy_rebuilds_cold_and_warm_identity_observers(self):
        for warm in (False, True):
            model, tech, _, _ = synthetic(self.root, 40, 2)
            if warm: model.get(tech[0].id)
            clone = copy.deepcopy(model)
            entry = clone.get(tech[0].uid)
            previous = entry.id
            entry.meta["id"] = "NEW-ALIAS"
            self.assertIs(entry, clone.get("NEW-ALIAS"))
            with self.assertRaises(ContractError): clone.get(previous)
            old_uid = entry.uid
            entry.meta["uid"] = key("copied-uid")
            self.assertIs(entry, clone.get(entry.uid))
            with self.assertRaises(ContractError): clone.get(old_uid)
            entry.meta["kind"] = "requirement"
            self.assertIn(entry, clone.by_kind("requirement"))
            self.assertNotIn(entry, clone.by_kind("technology"))
            item = element("rule", "Copy addition", "New independent rule")
            clone.elements[item["meta"]["uid"]] = Element(item["meta"], item["body"], location(item))
            self.assertEqual(item["meta"]["uid"], clone.get(item["meta"]["uid"]).uid)
            self.assertIs(tech[0], model.get(previous))
            self.assertEqual("technology", model.get(old_uid).kind)

    def test_caught_mutation_cannot_restore_or_continue_a_cached_evaluation(self):
        model, tech, _, _ = synthetic(self.root, 40, 2)
        original = tech[0].body
        expected = descriptor(model, [tech[0].uid])
        with self.assertRaisesRegex(ContractError, "modelo cambió"):
            with evaluation(model):
                descriptor(model, [tech[0].uid])
                with self.assertRaises(ContractError): tech[0].body += " Temporary revision."
                self.assertEqual(original, tech[0].body)
                with self.assertRaises(ContractError): descriptor(model, [tech[0].uid])
        self.assertEqual(expected, descriptor(model, [tech[0].uid]))
        self.assertEqual(0, model._evaluations)

    def test_all_nested_mutators_and_root_fields_are_guarded_before_edit(self):
        model, tech, _, _ = synthetic(self.root, 40, 2)
        tech[0].data["nested"] = {"rows": [{"values": [1, 2]}]}
        values = tech[0].data["nested"]["rows"][0]["values"]
        edits = [lambda: values.append(3), lambda: values.extend([3]), lambda: values.insert(0, 3),
                 lambda: values.pop(), lambda: values.remove(1), lambda: values.clear(),
                 lambda: values.reverse(), lambda: values.sort(), lambda: values.__iadd__([3]),
                 lambda: values.__imul__(2), lambda: values.__setitem__(slice(None), [3]),
                 lambda: values.__delitem__(0), lambda: values.__setitem__(0, 3),
                 lambda: tech[0].data.update(new=True), lambda: tech[0].data.pop("nested"),
                 lambda: tech[0].data.popitem(), lambda: tech[0].data.clear(),
                 lambda: tech[0].data.setdefault("new", True), lambda: tech[0].data.__ior__({"new": True}),
                 lambda: tech[0].data.__delitem__("nested"), lambda: tech[0].meta.update(id="new"),
                 lambda: setattr(tech[0], "meta", dict(tech[0].meta)),
                 lambda: setattr(tech[0], "path", "different.md"), lambda: setattr(tech[0], "line", 99),
                 lambda: setattr(tech[0], "resolved_data", {"changed": True}),
                 lambda: model.elements.clear(), lambda: setattr(model, "elements", {}),
                 lambda: model.prose.update({"new.md": "changed"}), lambda: model.errors.append("changed"),
                 lambda: model.warnings.append("changed"), lambda: setattr(model, "root", self.root / "other"),
                 lambda: delattr(tech[0], "body"), lambda: delattr(tech[0], "meta"),
                 lambda: delattr(model, "elements"), lambda: delattr(model, "prose")]
        before = json.dumps([e.item() for e in model.elements.values()], sort_keys=True)
        for edit in edits:
            with self.assertRaises(ContractError):
                with evaluation(model): edit()
            self.assertEqual(before, json.dumps([e.item() for e in model.elements.values()], sort_keys=True))
            self.assertEqual([1, 2], values)
            self.assertEqual(0, model._evaluations)
        values.append(3)
        self.assertEqual([1, 2, 3], values)

    def test_shared_resolved_inventory_remains_one_observable_map_in_copies(self):
        from approval_performance_support import shared_inventory_history
        from v3_contract import load
        model, _, _, _ = synthetic(self.root, 40, 2)
        shared_inventory_history(model, events=3, files=50)
        model = load(self.root).require_valid()
        clone = copy.deepcopy(model)
        for current_model in (model, clone):
            events = current_model.by_kind("execution")
            files = events[0].data["subject"]["files"]
            self.assertTrue(all(e.data["subject"]["files"] is files for e in events))
            with self.assertRaises(ContractError):
                with evaluation(current_model): files["src/new.py"] = "0" * 64
            self.assertNotIn("src/new.py", files)
            files["src/new.py"] = "0" * 64
            self.assertIn("src/new.py", events[1].data["subject"]["files"])
        self.assertIsNot(model.by_kind("execution")[0].data["subject"]["files"],
                         clone.by_kind("execution")[0].data["subject"]["files"])

    def test_detached_drafts_do_not_invalidate_the_current_model(self):
        model, tech, _, _ = synthetic(self.root, 40, 2)
        previous_meta = tech[0].meta
        previous_roles = model.by_kind("member")[0].data["roles"]
        model.by_kind("member")[0].data["roles"] = ["owner"]
        tech[0].meta = copy.deepcopy(dict(tech[0].meta))
        removed = model.elements.pop(tech[1].uid)
        with evaluation(model):
            previous_meta["id"] = "DETACHED"
            previous_roles.clear()
            removed.body += " Independent draft."
        self.assertNotEqual("DETACHED", tech[0].id)
        self.assertEqual(["owner"], model.by_kind("member")[0].data["roles"])
        meta_copy = copy.copy(tech[0].meta)
        meta_copy["id"] = "Independent top-level draft"
        self.assertNotEqual(meta_copy["id"], tech[0].id)
        with self.assertRaises(ContractError):
            with evaluation(model): tech[0].meta["id"] = "Must still be guarded"

    def test_mutation_from_another_thread_is_rejected_for_an_active_model(self):
        model, tech, _, _ = synthetic(self.root, 40, 2)
        previous = tech[0].body
        with self.assertRaises(ContractError):
            with evaluation(model):
                with ThreadPoolExecutor(max_workers=1) as pool:
                    with self.assertRaises(ContractError):
                        pool.submit(setattr, tech[0], "body", "Changed concurrently").result()
        self.assertEqual(previous, tech[0].body)
        self.assertEqual(0, model._evaluations)

    def test_shallow_model_copy_guards_shared_roots_and_later_additions(self):
        model, tech, _, _ = synthetic(self.root, 40, 2)
        model.get(tech[0].id)
        clone = copy.copy(model)
        self.assertIs(model.elements, clone.elements)
        for mutate in (lambda: setattr(tech[0], "body", "Changed shared element"),
                       lambda: model.prose.update({"shared.md": "Changed"}),
                       lambda: model.elements.clear()):
            with self.assertRaises(ContractError):
                with evaluation(clone): mutate()
        item = element("rule", "Later shared addition", "Shared canonical data")
        new = Element(item["meta"], item["body"], location(item))
        model.elements[new.uid] = new
        self.assertIs(new, clone.get(new.uid))
        model.elements |= {}
        self.assertIs(model.elements, clone.elements)
        linked = Model(self.root, elements=model.elements)
        self.assertIs(model.elements, linked.elements)
        with self.assertRaises(ContractError):
            with evaluation(clone): new.meta["id"] = "Must be guarded"
        new.meta["id"] = "SHARED-ALIAS"
        self.assertIs(new, clone.get("SHARED-ALIAS"))
        self.assertIs(new, model.get("SHARED-ALIAS"))

    def test_shallow_element_copy_guards_shared_metadata_with_its_new_owner(self):
        model, tech, _, _ = synthetic(self.root, 40, 2)
        copied = copy.copy(tech[0])
        second = Model(self.root)
        second.elements[copied.uid] = copied
        self.assertIs(copied.meta, tech[0].meta)
        with self.assertRaises(ContractError):
            with evaluation(second): copied.meta["id"] = "Must be guarded"
        copied.body += " Independent shallow body."
        self.assertNotEqual(copied.body, tech[0].body)
        copied.meta["id"] = "SHARED-ELEMENT-ALIAS"
        self.assertIs(tech[0], model.get(copied.id))
        self.assertIs(copied, second.get(copied.id))

    def test_caught_shared_mutation_invalidates_every_active_alias_owner(self):
        model, tech, _, _ = synthetic(self.root, 40, 2)
        clone = copy.copy(model)
        original = tech[0].id
        with self.assertRaises(ContractError):
            with evaluation(model):
                with self.assertRaises(ContractError):
                    with evaluation(clone):
                        with self.assertRaises(ContractError): tech[0].meta["id"] = "Blocked"
                        with self.assertRaises(ContractError): descriptor(clone, [tech[0].uid])
                with self.assertRaises(ContractError): descriptor(model, [tech[0].uid])
        self.assertEqual(original, tech[0].id)
        self.assertEqual(0, model._evaluations)
        self.assertEqual(0, clone._evaluations)

    def test_cached_results_cannot_be_poisoned_and_memory_is_released(self):
        model, tech, _, _ = synthetic(self.root, 40, 2)
        with evaluation(model) as scope:
            from v3_scope import memberships
            members = memberships(model)
            memberships(model).clear()
            self.assertEqual(members, memberships(model))
            expected = descriptor(model, [tech[0].uid])
            descriptor(model, [tech[0].uid])["units"].clear()
            self.assertEqual(expected, descriptor(model, [tech[0].uid]))
            approved(model, [tech[0].uid], "technology")["descriptor"].clear()
            self.assertTrue(approved(model, [tech[0].uid], "technology")["valid"])
            for i in range(MAX_ENTRIES * 2): scope.memo(("test", i), lambda: {}, lambda _: (MAX_UNITS // 4, MAX_SOURCE_BYTES // 4))
            self.assertLessEqual(len(scope.cache), MAX_ENTRIES)
            self.assertLessEqual(scope.units, MAX_UNITS)
            self.assertLessEqual(scope.source_bytes, MAX_SOURCE_BYTES)
        self.assertEqual(0, len(scope.cache))
        self.assertIsNone(scope.model)
        with self.assertRaisesRegex(RuntimeError, "explicit failure"):
            with evaluation(model) as scope:
                descriptor(model, [tech[0].uid]); raise RuntimeError("explicit failure")
        self.assertFalse(scope.cache)
        self.assertIsNone(current(model))

    def test_projects_revisions_threads_and_inherited_async_contexts_are_isolated(self):
        first, tech, _, _ = synthetic(self.root / "first", 40, 2)
        second, tech2, _, _ = synthetic(self.root / "second", 40, 2, project="two")
        changed, tech3, _, _ = synthetic(self.root / "revision", 40, 2)
        tech3[0].body += " Different revision with identical UID."
        def run(model, entry):
            with evaluation(model) as scope:
                return approved(model, [entry.uid], "technology")["valid"], id(scope)
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda pair: run(*pair), [(first, tech[0]), (second, tech2[0]), (changed, tech3[0])]))
        self.assertEqual([True, True, False], [r[0] for r in results])
        async def main():
            with evaluation(first) as outer:
                async def child():
                    with evaluation(first) as inner:
                        await asyncio.sleep(0)
                        self.assertIsNot(inner, outer)
                        return approved(first, [tech[0].uid], "technology")["valid"]
                self.assertEqual([True, True], await asyncio.gather(child(), child()))
        asyncio.run(main())


if __name__ == "__main__": unittest.main()
