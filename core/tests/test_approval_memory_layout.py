"""Behavioral regressions for compact elements and split identity indexes."""
import copy
import gc
from pathlib import Path
import random
import unittest
import weakref

from approval_performance_support import ROOT, key
import sys
sys.path.insert(0, str(ROOT / 'scripts'))
from v3_contract import ContractError, Element, Model, element
from v3_evaluation import evaluation


class MemoryLayoutTests(unittest.TestCase):
    def entry(self, label):
        item = element('rule', label, 'Literal rule ' + label, identifier=key(label))
        return Element(item['meta'], item['body'], 'synthetic.md')

    def assert_lookup(self, model, identifier):
        expected = [e for e in model.elements.values() if identifier in (e.uid, e.id)]
        if len(expected) == 1:
            self.assertIs(expected[0], model.get(identifier))
        else:
            with self.assertRaises(ContractError): model.get(identifier)

    def test_collisions_uid_changes_noncanonical_keys_and_duplicate_members(self):
        for reverse in (False, True):
            a, b = self.entry('a'), self.entry('b')
            entries = [a, b][::(-1 if reverse else 1)]
            model = Model(Path('.'), {e.uid:e for e in entries})
            for alias in (a.uid, b.uid, 'shared'):
                a.meta['id'] = alias
                for other in (a.uid, b.uid, alias): self.assert_lookup(model, other)
                b.meta['id'] = alias
                for other in (a.uid, b.uid, alias): self.assert_lookup(model, other)
            a.meta['uid'] = key('changed')
            for other in (a.uid, b.uid, alias, key('a')): self.assert_lookup(model, other)
            model.elements = {'unrelated-a':a, 'unrelated-b':b}
            for other in (a.uid, b.uid, a.id, b.id, 'unrelated-a'): self.assert_lookup(model, other)
            model.elements['duplicate'] = a
            self.assert_lookup(model, a.uid)
            a.meta['uid'] = b.uid
            self.assert_lookup(model, b.uid)

    def test_lookup_matches_linear_oracle_after_random_mutations(self):
        rng = random.Random(314159)
        entries = [self.entry('random-' + str(i)) for i in range(9)]
        model = Model(Path('.'), {e.uid:e for e in entries})
        for step in range(120):
            chosen = rng.choice(entries)
            operation = step % 6
            if operation == 0: chosen.meta['id'] = rng.choice(entries).uid
            elif operation == 1: chosen.meta['uid'] = rng.choice(entries).uid
            elif operation == 2: model.elements[str(step)] = chosen
            elif operation == 3 and model.elements: model.elements.pop(rng.choice(list(model.elements)))
            elif operation == 4: model.elements = {e.uid:e for e in entries}
            else: chosen.meta['kind'] = rng.choice(['rule', 'feature'])
            for identifier in [e.uid for e in entries] + [e.id for e in entries] + ['absent']:
                self.assert_lookup(model, identifier)
            for kind in ('rule','feature'):
                self.assertEqual([id(e) for e in model.elements.values() if e.kind == kind],
                                 [id(e) for e in model.by_kind(kind)])

    def test_shallow_copy_weakrefs_and_nested_guard_keep_every_owner(self):
        entry = self.entry('original')
        first = Model(Path('.'), {entry.uid:entry})
        clone = copy.copy(entry)
        second = Model(Path('.'), {clone.uid:clone})
        self.assertIs(entry.meta, clone.meta)
        self.assertIs(clone, weakref.ref(clone)())
        for model in (first, second): model.get(entry.id)
        clone.meta['id'] = 'changed'
        self.assertIs(entry, first.get('changed'))
        self.assertIs(clone, second.get('changed'))
        with self.assertRaises(ContractError):
            with evaluation(first):
                try: clone.relations['uses'] = [key('missing')]
                except ContractError: pass
        self.assertNotIn('uses', entry.relations)
        detached = copy.deepcopy(clone)
        detached.meta['id'] = 'independent'
        self.assertEqual('changed', clone.id)
        ref = weakref.ref(detached)
        del detached
        gc.collect()
        self.assertIsNone(ref())


if __name__ == '__main__': unittest.main()
