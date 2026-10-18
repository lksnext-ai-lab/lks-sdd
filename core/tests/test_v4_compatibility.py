"""Explicit 3.4.3 cutover on disposable consumers, with real journal recovery."""
import importlib.util
import base64
import io
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tests')]
from build_dual_distribution import collect_development
from build_candidate_package import _package_integrity_bytes
from dual_distribution import artifacts
from presentation_test_support import present
from runtime_doctor import check
import test_v31_review as fixture
from test_v4_cli_presentation import snapshot
from v3_contract import ContractError, load
from v3_current import upgrade
from v3_storage import apply, recover
from v3_workflow import state


class CompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='v4-compat-bundles-')
        cls.addClassCleanup(cls.temp.cleanup)
        spec = importlib.util.spec_from_file_location('compat_installer', ROOT/'distribution/install.py')
        cls.installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.installer)
        archived = subprocess.run(['git', 'archive', '--format=zip', 'v3.4.3'], cwd=ROOT,
                                  capture_output=True, check=True).stdout
        with zipfile.ZipFile(io.BytesIO(archived)) as source:
            old = {i.filename: source.read(i) for i in source.infolist() if not i.is_dir()}
        assert json.loads(old['.codex-plugin/plugin.json'])['version'] == '3.4.3'
        old['package-integrity.json'] = _package_integrity_bytes(list(old.items()), '3.4.3', 'published-v3.4.3-fixture')
        cls.bundles = {}
        cls.source_bindings = {}
        for label, core in [('old', old), ('candidate', collect_development(ROOT))]:
            import hashlib
            cls.source_bindings[label] = {name:hashlib.sha256(raw).hexdigest() for name,raw in core.items()}
            bundle = Path(cls.temp.name)/label; bundle.mkdir()
            packages = artifacts(core, 'v4-compat-'+label, 'development-unreleased')
            setup = next(raw for name, raw in packages.items() if name.startswith('lks-sdd-setup-'))
            with zipfile.ZipFile(io.BytesIO(setup)) as archive:
                for item in archive.infolist():
                    target = cls.installer.safe(bundle, item.filename)
                    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(item))
            cls.bundles[label] = bundle

    def setUp(self):
        self.case = fixture.IntegralTests(methodName='runTest')
        self.addCleanup(self.case.doCleanups)
        # Construct the pre-cutover fixture in its real legacy physical format.
        # Current bootstrap writes ZIP by default; that is not a 3.4.3 baseline.
        # Capability checks during upgrade/recovery are never patched.
        with patch('object_zip.supported', return_value=False): self.case.setUp()
        self.root, self.actor = self.case.root, self.case.actor
        # Seed a disposable fixture including its ownership receipt. No active
        # plugin, marketplace registration or real consumer is installed.
        prepared = self.installer.plan(self.bundles['old'], self.root, 'copilot')
        for entry in prepared['changes']:
            path = self.root/entry['path']
            if entry['content'] is None: path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(bytes.fromhex(entry['content']))
        self.case.close_proposal(); self.case.create_plan()
        (self.root/'app.py').write_text("def greeting(): return 'Adios'\n", encoding='utf-8')
        self.old_lock = json.loads((self.root/'.lks-sdd/distribution-lock.json').read_bytes())
        self.assertEqual('valid', check(self.root)['status'])

    def packet(self, bundle=True):
        return present(upgrade, self.root, {'actor': self.actor,
            'collaboration': self.case.configuration,
            'statement': 'Confirmo el cambio de runtime sin renovar la ejecución ni las decisiones previas',
            **({'runtime_bundle': str(self.bundles['candidate'])} if bundle else {})})

    def test_explicit_upgrade_preserves_open_work_history_and_exact_rollback(self):
        before = snapshot(self.root)
        model = load(self.root).require_valid()
        prior = {item.uid: item.digest() for item in model.elements.values() if item.kind in {'decision', 'execution', 'task', 'proposal', 'plan'}}
        task_state = state(model, model.get(self.case.task))
        code = (self.root/'app.py').read_bytes()
        old_cli = self.root/self.old_lock['runtime']/'scripts/lks_sdd.py'
        old_validation = subprocess.run([sys.executable,'-B',str(old_cli),'v3','validate',str(self.root)],
                                        capture_output=True,timeout=90)
        self.assertEqual(0,old_validation.returncode,old_validation.stderr)
        self.assertEqual('valid',json.loads(old_validation.stdout)['status'])
        packet = self.packet()
        self.assertEqual(before, snapshot(self.root), 'Preview must not cut over the consumer')
        receipt = apply(self.root, packet, packet['preview']['preview_hash'])
        lock = json.loads((self.root/'.lks-sdd/distribution-lock.json').read_bytes())
        self.assertNotEqual(self.old_lock['runtime_digest'], lock['runtime_digest'])
        self.assertEqual('3.1', lock['project_schema']); self.assertEqual('valid', check(self.root)['status'])
        updated = load(self.root).require_valid()
        for uid, digest in prior.items(): self.assertEqual(digest, updated.get(uid).digest(), uid)
        self.assertEqual(task_state, state(updated, updated.get(self.case.task)))
        self.assertEqual(code, (self.root/'app.py').read_bytes())
        cli = self.root/lock['runtime']/'scripts/lks_sdd.py'
        completed = subprocess.run([sys.executable, '-B', str(cli), 'v3', 'validate', str(self.root)],
                                   capture_output=True, timeout=90)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual('valid', json.loads(completed.stdout)['status'])
        recover(self.root, packet['preview']['preview_hash'], rollback=True, receipt=receipt['receipt'])
        after = snapshot(self.root)
        for path, raw in before.items():
            if path != '.lks-sdd/transactions.json': self.assertEqual(raw, after[path], path)
        old_journal = json.loads(before['.lks-sdd/transactions.json'])
        new_journal = json.loads(after['.lks-sdd/transactions.json'])
        for key, value in old_journal['transactions'].items():
            self.assertEqual(value, new_journal['transactions'][key], key)
        self.assertEqual('rolled-back', new_journal['transactions'][packet['preview']['preview_hash']]['state'])
        self.assertEqual(self.old_lock, json.loads((self.root/'.lks-sdd/distribution-lock.json').read_bytes()))
        self.assertEqual('valid', check(self.root)['status'])

    def test_interrupted_cutover_recovers_and_rejects_rollback_over_later_work(self):
        packet = self.packet(); key = packet['preview']['preview_hash']
        with self.assertRaises(InterruptedError): apply(self.root, packet, key, interrupt_after=1)
        self.assertTrue((self.root/'.lks-sdd/transaction.json').exists())
        note = self.root/'later-independent.txt'; note.write_bytes(b'keep independent work')
        result = recover(self.root, key)
        self.assertEqual('valid', check(self.root)['status'])
        self.assertEqual(b'keep independent work', note.read_bytes())
        lock_path = self.root/'.lks-sdd/distribution-lock.json'
        lock_path.write_bytes(lock_path.read_bytes()+b'\n')
        before = snapshot(self.root)
        with self.assertRaises(ContractError):
            recover(self.root, key, rollback=True, receipt=result['receipt'])
        self.assertEqual(before, snapshot(self.root), 'Rejected rollback must preserve later work')

    def test_missing_bundle_and_changed_pin_never_grant_cutover(self):
        before = snapshot(self.root)
        with self.assertRaises(ContractError): self.packet(bundle=False)
        self.assertEqual(before, snapshot(self.root))
        packet = self.packet(); cli = self.root/self.old_lock['runtime']/'scripts/lks_sdd.py'
        cli.write_bytes(cli.read_bytes()+b'\n# local runtime modification\n')
        before = snapshot(self.root)
        with self.assertRaises(ContractError): apply(self.root, packet, packet['preview']['preview_hash'])
        self.assertEqual(before, snapshot(self.root))

    def test_grouped_journal_blocks_pin_only_rollback_and_backup_restores_old_reader(self):
        from content_store import OBJECTS, read_object, reference
        from object_zip import PACKS, FORMAT
        from v2_storage import preview, apply as journal_apply, recover as journal_recover
        from v2_contract import sha
        backup = snapshot(self.root)
        model = load(self.root).require_valid()
        prior = {item.uid:item.digest() for item in model.elements.values()
                 if item.kind in {'decision','execution','task','proposal','plan'}}
        task_state = state(model, model.get(self.case.task))
        code = (self.root/'app.py').read_bytes()
        old_cli = self.root/self.old_lock['runtime']/'scripts/lks_sdd.py'
        old_validation = subprocess.run([sys.executable,'-B',str(old_cli),'v3','validate',str(self.root)],
                                        capture_output=True,timeout=90)
        self.assertEqual(0,old_validation.returncode,old_validation.stderr)
        with self.assertRaises(ContractError): self.packet(bundle=False)
        self.assertEqual(backup,snapshot(self.root))
        packet = self.packet(); key = packet['preview']['preview_hash']
        self.assertEqual(backup,snapshot(self.root))
        original = old_cli.read_bytes()
        old_cli.write_bytes(original+b'\n# synthetic later runtime edit\n')
        try:
            before = snapshot(self.root)
            with self.assertRaises(ContractError): apply(self.root,packet,key)
            self.assertEqual(before,snapshot(self.root))
        finally: old_cli.write_bytes(original)
        with self.assertRaises(InterruptedError): apply(self.root,packet,key,interrupt_after=1)
        self.assertTrue((self.root/'.lks-sdd/transaction.json').exists())
        note = self.root/'later-independent.txt'; note.write_bytes(b'keep independent later work')
        receipt = recover(self.root,key)
        self.assertFalse((self.root/'.lks-sdd/transaction.json').exists())
        self.assertEqual(b'keep independent later work',note.read_bytes())
        lock = json.loads((self.root/StorageReaderCompatibilityTests.pin).read_bytes())
        self.assertIn(FORMAT, lock['storage_formats'])
        self.assertEqual('valid',check(self.root)['status'])
        updated = load(self.root).require_valid()
        for uid,digest in prior.items(): self.assertEqual(digest,updated.get(uid).digest(),uid)
        self.assertEqual(task_state,state(updated,updated.get(self.case.task)))
        self.assertEqual(code,(self.root/'app.py').read_bytes())
        pin = self.root/StorageReaderCompatibilityTests.pin
        original = pin.read_bytes(); pin.write_bytes(original+b'\n')
        try:
            before = snapshot(self.root)
            with self.assertRaises(ContractError): recover(self.root,key,rollback=True,receipt=receipt['receipt'])
            self.assertEqual(before,snapshot(self.root))
        finally: pin.write_bytes(original)
        # Fork the same verified cutover state: one pre-ZIP rollback, one post-ZIP
        # refusal. There is only one expensive runtime upgrade in this probe.
        pre_temp = tempfile.TemporaryDirectory(prefix='v4-pre-'); self.addCleanup(pre_temp.cleanup)
        pre = Path(pre_temp.name)
        shutil.copytree(self.root,pre,dirs_exist_ok=True)
        self.assertEqual(snapshot(self.root),snapshot(pre))
        recover(pre,key,rollback=True,receipt=receipt['receipt'])
        restored_before = snapshot(pre)
        for name,raw in backup.items():
            if name != '.lks-sdd/transactions.json': self.assertEqual(raw,restored_before[name],name)
        self.assertEqual('valid',check(pre)['status'])
        self.assertFalse((pre/PACKS).exists())
        self.assertEqual(b'keep independent later work',(pre/'later-independent.txt').read_bytes())
        bodies = [b'first post-cutover body', b'second post-cutover body']
        changes = {OBJECTS+sha(raw):raw for raw in bodies}
        plan = preview(self.root, changes, sources={}, operation='synthetic-storage-journal')
        grouped_receipt = journal_apply(self.root, changes, plan, plan['preview_hash'])
        self.assertTrue(list((self.root/PACKS).glob('*.zip')))
        before = snapshot(self.root)
        with self.assertRaisesRegex(ContractError, 'Incompatible ZIP reader'):
            recover(self.root, key, rollback=True, receipt=receipt['receipt'])
        self.assertEqual(before, snapshot(self.root))
        self.assertEqual('valid', check(self.root)['status'])
        with self.assertRaisesRegex(ValueError, 'Incompatible ZIP reader'):
            self.installer.plan(self.bundles['old'], self.root, 'copilot')
        self.assertEqual(before, snapshot(self.root))
        # Exercise the new grouped receipt with the actual compatible reader.
        journal_recover(self.root, plan['preview_hash'], rollback=True, receipt=grouped_receipt['receipt'])
        for body in bodies: self.assertEqual(body, read_object(self.root, reference(body)))
        load(self.root).require_valid()
        current = snapshot(self.root)
        pin = self.root/StorageReaderCompatibilityTests.pin
        pin.write_bytes(json.dumps(self.old_lock).encode())
        try:
            diagnosis = check(self.root)
            self.assertEqual('blocked', diagnosis['status'])
            self.assertTrue(any('Incompatible ZIP reader' in error for error in diagnosis['errors']))
        finally: pin.write_bytes(current[StorageReaderCompatibilityTests.pin])
        self.assertEqual(current, snapshot(self.root))
        # Restore the whole pre-cutover backup to a separate owned consumer;
        # never replace the current consumer's later records or immutable bodies.
        restored_temp = tempfile.TemporaryDirectory(prefix='v4-old-'); self.addCleanup(restored_temp.cleanup)
        restored = Path(restored_temp.name)
        for name,raw in backup.items():
            path = restored/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)
        self.assertEqual(backup, snapshot(restored))
        self.assertFalse((restored/PACKS).exists())
        self.assertEqual('valid', check(restored)['status'])
        cli = restored/self.old_lock['runtime']/'scripts/lks_sdd.py'
        completed = subprocess.run([sys.executable,'-B',str(cli),'v3','validate',str(restored)],
                                   capture_output=True,timeout=90)
        self.assertEqual(0,completed.returncode,completed.stderr)
        self.assertEqual('valid',json.loads(completed.stdout)['status'])
        self.assertEqual(current,snapshot(self.root))


class StorageReaderCompatibilityTests(unittest.TestCase):
    """Small boundary probes; no complete functional journey or installation."""
    old = b'{"storage_formats":["lks-sdd-object/1"]}'
    new = b'{"storage_formats":["lks-sdd-object/1","lks-sdd-object-zip/1"]}'
    pin = ".lks-sdd/distribution-lock.json"

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('storage_compat_installer', ROOT/'distribution/install.py')
        cls.installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.installer)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='v4-reader-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def grouped(self, root=None):
        from object_zip import encode, PACKS
        from v2_contract import sha
        from v2_storage import write_one
        raw = encode({sha(b'first'):b'first', sha(b'second'):b'second'})
        write_one(root or self.root, PACKS + sha(raw) + '.zip', raw)

    def test_business_apply_rejects_old_reader_over_grouped_data(self):
        from v2_storage import preview, apply as journal_apply
        self.grouped()
        changes = {self.pin:self.old}
        plan = preview(self.root, changes, sources={}, operation='reader-cutover-probe')
        before = snapshot(self.root)
        with self.assertRaisesRegex(ContractError, 'ZIP|compatible'):
            journal_apply(self.root, changes, plan, plan['preview_hash'])
        self.assertEqual(before, snapshot(self.root))

    def test_old_reader_cutover_before_zip_keeps_compatible_loose_backups(self):
        from object_zip import PACKS
        from v2_storage import preview, apply as journal_apply, recover as journal_recover
        changes = {self.pin:self.old}
        plan = preview(self.root, changes, sources={}, operation='compatible-old-reader')
        receipt = journal_apply(self.root, changes, plan, plan['preview_hash'])
        self.assertFalse((self.root/PACKS).exists())
        journal_recover(self.root, plan['preview_hash'], rollback=True, receipt=receipt['receipt'])
        self.assertFalse((self.root/self.pin).exists())

    def test_pending_maintenance_is_preserved_and_blocks_business_mutation(self):
        from v2_storage import preview, apply as journal_apply, recover as journal_recover, write_one, PENDING
        plan = preview(self.root, {'test.txt':b'after'}, sources={}, operation='pending-owner')
        write_one(self.root, PENDING, b'{"schema_version":"lks-sdd-store-maintenance/1"}')
        before = snapshot(self.root)
        with self.assertRaises(ContractError): journal_apply(self.root, {'test.txt':b'after'}, plan, plan['preview_hash'])
        with self.assertRaises(ContractError): journal_recover(self.root, plan['preview_hash'])
        self.assertEqual(before, snapshot(self.root))

    def test_development_package_rejects_a_declared_but_missing_zip_reader(self):
        from types import SimpleNamespace
        (self.root/'.codex-plugin').mkdir(); (self.root/'distribution').mkdir()
        (self.root/'.codex-plugin/plugin.json').write_text('{"version":"3.4.3"}',encoding='utf-8')
        (self.root/'distribution/dual.json').write_text(
            '{"storage_formats":["lks-sdd-object-zip/1"],"additional_files":[]}',encoding='utf-8')
        tracked = b'.codex-plugin/plugin.json\0distribution/dual.json\0'
        with patch('build_dual_distribution.subprocess.run',return_value=SimpleNamespace(stdout=tracked)):
            with self.assertRaisesRegex(ValueError,'ZIP reader is missing'): collect_development(self.root)

    def test_runtime_diagnosis_does_not_import_project_transaction_engine(self):
        import builtins
        from v2_storage import write_one
        self.grouped()
        write_one(self.root,self.pin,b'{"schema_version":"1.0","project_schema":"3.1","storage_formats":[]}')
        original = builtins.__import__
        def safe_import(name,*args,**kwargs):
            if name == 'v2_storage': raise ImportError('Project runtime must not be imported by its integrity diagnostic')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=safe_import): result=check(self.root)
        self.assertEqual('blocked',result['status'])
        self.assertTrue(any('Incompatible ZIP reader' in error for error in result['errors']))

    def test_both_business_journals_reject_incompatible_rollback_without_writes(self):
        from v2_contract import canonical
        from v2_storage import preview, apply as journal_apply, recover as journal_recover, write_one, PENDING, TRANSACTION_STORE
        for version in ('2.0','2.1'):
            with self.subTest(version=version):
                root = self.root/version; root.mkdir()
                write_one(root, self.pin, self.old)
                changes = {self.pin:self.new}
                plan = preview(root, changes, sources={}, operation='reader-rollback-probe')
                receipt = None
                if version == '2.1':
                    receipt = journal_apply(root, changes, plan, plan['preview_hash'])['receipt']
                else:
                    journal = {'schema_version':'2.0','preview':plan,'state':'applying',
                               'before':{self.pin:base64.b64encode(self.old).decode()},
                               'after':{self.pin:base64.b64encode(self.new).decode()}}
                    write_one(root, PENDING, canonical(journal)); write_one(root, self.pin, self.new)
                self.grouped(root)
                before = snapshot(root)
                with self.assertRaisesRegex(ContractError, 'ZIP|compatible'):
                    journal_recover(root, plan['preview_hash'], rollback=True, receipt=receipt)
                self.assertEqual(before, snapshot(root))

    def test_installer_apply_and_recovery_recheck_store_before_writes(self):
        from v2_contract import sha
        from v2_storage import write_one
        metadata = {'version':'3.4.3','channel':'synthetic','runtime_digest':'0'*64}
        with patch.object(self.installer,'load_payload',return_value=(metadata,{self.pin:self.old})):
            plan = self.installer.plan(self.root,self.root,'copilot')
            self.grouped()
            with self.assertRaisesRegex(ValueError,'Incompatible ZIP reader'):
                self.installer.plan(self.root,self.root,'copilot')
        before = snapshot(self.root)
        with self.assertRaisesRegex(ValueError, 'ZIP|compatible'):
            self.installer.apply(plan, plan['preview_hash'])
        self.assertEqual(before, snapshot(self.root))
        write_one(self.root, self.pin, self.new)
        journal = {'schema_version':'1.0','changes':[{'path':self.pin,'before':sha(self.old),
                   'after':sha(self.new),'original':self.old.hex(),'content':self.new.hex()}]}
        write_one(self.root, self.installer.JOURNAL, json.dumps(journal).encode())
        before = snapshot(self.root)
        with self.assertRaisesRegex(ValueError, 'ZIP|compatible'): self.installer.recover(self.root)
        self.assertEqual(before, snapshot(self.root))


if __name__ == '__main__': unittest.main()
