"""Historical support is reusable only inside an unchanged model evaluation."""
from pathlib import Path
import hashlib
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from v3_contract import ContractError
from v3_contract import fingerprint
from v3_evaluation import evaluation
from v3_migration import inherited_confirmations


class MigrationEvaluationReuseTests(unittest.TestCase):
    def setUp(self):
        self.model = SimpleNamespace(_revision=0, _evaluations=0)

    def test_repeated_support_is_computed_once_and_results_are_independent(self):
        with patch('v3_migration._inherited_confirmations', return_value={'task': 'receipt'}) as raw:
            with evaluation(self.model):
                first = inherited_confirmations(self.model, {'task': 'digest'})
                first['task'] = 'another-current-decision'
                self.assertEqual({'task': 'receipt'}, inherited_confirmations(self.model, {'task': 'digest'}))
            self.assertEqual(1, raw.call_count)

    def test_different_expected_content_does_not_reuse_support(self):
        with patch('v3_migration._inherited_confirmations', return_value={}) as raw:
            with evaluation(self.model):
                inherited_confirmations(self.model, {'task': 'old'})
                inherited_confirmations(self.model, {'task': 'new'})
            self.assertEqual(2, raw.call_count)

    def test_scope_exit_and_uncached_calls_recompute(self):
        with patch('v3_migration._inherited_confirmations', return_value={}) as raw:
            for _ in range(2):
                with evaluation(self.model): inherited_confirmations(self.model, {'task': 'digest'})
            inherited_confirmations(self.model, {'task': 'digest'})
            inherited_confirmations(self.model, {'task': 'digest'})
            self.assertEqual(4, raw.call_count)

    def test_model_revision_change_stops_instead_of_reusing_authority(self):
        with patch('v3_migration._inherited_confirmations', return_value={}):
            with self.assertRaises(ContractError):
                with evaluation(self.model):
                    inherited_confirmations(self.model, {'task': 'digest'})
                    self.model._revision += 1
                    inherited_confirmations(self.model, {'task': 'digest'})

    def test_failure_is_not_cached(self):
        with patch('v3_migration._inherited_confirmations', side_effect=[ContractError('missing original'), {}]) as raw:
            with evaluation(self.model):
                with self.assertRaises(ContractError): inherited_confirmations(self.model, {'task': 'digest'})
                self.assertEqual({}, inherited_confirmations(self.model, {'task': 'digest'}))
            self.assertEqual(2, raw.call_count)

    def test_shared_unit_reuse_keeps_exact_original_and_dependency_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / 'original.md'
            original.write_bytes(b'unchanged historical decisions')
            shared = {'global': 'g', **{'global-'+str(i): 'digest-'+str(i) for i in range(300)}}
            units = {**shared, 'technology-a': 'a', 'technology-b': 'b'}
            mapping = {key: {'target_digest': digest, 'original': 'original.md',
                            'original_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
                            'source_id': key, 'source_normative': fingerprint({'key': key})}
                       for key, digest in units.items()}
            receipt = SimpleNamespace(uid='receipt', data={'content_confirmations': mapping})
            self.model.root = Path(folder); self.model.hashes = {}
            self.model.by_kind = lambda kind: [receipt]
            old = [SimpleNamespace(id=key, meta={'nature': 'decision', 'state': 'approved'},
                                   normative=lambda key=key: {'key': key}) for key in units]
            with patch('v3_migration.v2.parse_document', return_value=(old, None)), \
                 patch('v3_approval.descriptor', side_effect=lambda model, keys: {'units': {k: units[k] for k in {'global', *keys}}}) as descriptor:
                with evaluation(self.model):
                    self.assertEqual({*shared, 'technology-a'}, set(inherited_confirmations(self.model, {**shared, 'technology-a': 'a'})))
                    self.assertEqual({*shared, 'technology-b'}, set(inherited_confirmations(self.model, {**shared, 'technology-b': 'b'})))
                self.assertEqual(len(units), descriptor.call_count)  # Also above the 256-entry cache boundary.
                original.write_bytes(b'changed after the immutable phase')
                self.model.hashes['original.md'] = hashlib.sha256(original.read_bytes()).hexdigest()
                with evaluation(self.model):
                    self.assertEqual({}, inherited_confirmations(self.model, units))
                original.unlink()
                self.model.hashes.pop('original.md', None)
                with evaluation(self.model):
                    self.assertEqual({}, inherited_confirmations(self.model, units))

    def test_dependency_digest_mismatch_is_not_a_confirmation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'original.md').write_bytes(b'old')
            proof = {'target_digest': 'task-digest', 'original': 'original.md',
                     'original_sha256': hashlib.sha256(b'old').hexdigest(),
                     'source_id': 'old-task', 'source_normative': fingerprint({'old': 'task'})}
            self.model.root=root; self.model.hashes={}
            self.model.by_kind=lambda kind: [SimpleNamespace(uid='migration', data={'content_confirmations': {'task': proof}})]
            old=SimpleNamespace(id='old-task', meta={'nature':'decision','state':'approved'}, normative=lambda:{'old':'task'})
            with patch('v3_migration.v2.parse_document', return_value=([old],None)), \
                 patch('v3_approval.descriptor', return_value={'units':{'task':'task-digest','required-dependency':'missing-digest'}}):
                with evaluation(self.model):
                    self.assertEqual({}, inherited_confirmations(self.model, {'task':'task-digest'}))

    def test_changed_observed_source_hash_stops_even_without_a_model_revision_change(self):
        self.model.hashes={'original.md':'old'}
        with patch('v3_migration._inherited_confirmations',return_value={'task':'receipt'}):
            with self.assertRaises(ContractError):
                with evaluation(self.model):
                    inherited_confirmations(self.model,{'task':'digest'})
                    self.model.hashes['original.md']='changed'
                    inherited_confirmations(self.model,{'task':'digest'})

    def test_new_source_is_observed_but_cannot_change_after_a_cached_calculation(self):
        self.model.hashes={}
        def first(model,expected):
            model.hashes['original.md']='first';return {'task':'receipt'}
        with patch('v3_migration._inherited_confirmations',side_effect=first):
            with self.assertRaises(ContractError):
                with evaluation(self.model):
                    inherited_confirmations(self.model,{'task':'digest'})
                    self.model.hashes['original.md']='later'

    def test_unchanged_sources_and_footprint_expansion_are_allowed(self):
        self.model.hashes={'original.md':'same'}
        with evaluation(self.model):
            with patch('v3_migration._inherited_confirmations',return_value={}):
                inherited_confirmations(self.model,{'task':'digest'})
                self.model.hashes.update({'original.md':'same','another.md':'newly-observed'})
                inherited_confirmations(self.model,{'task':'digest'})
