"""Small physical recovery boundaries; no lifecycle journeys or active installs."""
import json
import os
from pathlib import Path
import shutil
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts')]
from v2_contract import ContractError, canonical, sha
from content_store import publish_object, OBJECTS, read_object, reference
from v2_storage import PENDING, write_one, ensure_idle
import store_maintenance as maintenance


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sm-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.root = self.base/'consumer'; self.root.mkdir()
        runtime = '.lks-sdd/runtime/test'
        formats = ['lks-sdd-object/1', 'lks-sdd-object-zip/1', maintenance.FORMAT]
        inventory = {}
        for module in ['object_zip.py','v2_contract.py','content_store.py','v2_storage.py','store_maintenance.py']:
            raw = (ROOT/'scripts'/module).read_bytes()
            write_one(self.root, runtime+'/scripts/'+module, raw)
            inventory['scripts/'+module] = sha(raw)
        write_one(self.root, runtime+'/distribution/dual.json', canonical({'storage_formats':formats}))
        write_one(self.root, '.lks-sdd/distribution-lock.json', canonical({'runtime':runtime,
            'runtime_files':inventory,'storage_formats':formats}))
        self.bodies = [b'alpha',b'beta',b'unreferenced-but-preserved']
        for raw in self.bodies: publish_object(self.root, OBJECTS+sha(raw), raw)
        write_one(self.root, 'docs/lks-sdd/canonical.md', b'Canonical, no mutation')

    def plan(self):
        return maintenance.preview(self.root, self.base/'backup.zip', self.base/'restore')

    def assert_logical(self):
        for raw in self.bodies: self.assertEqual(raw, read_object(self.root, reference(raw)))
        self.assertEqual(b'Canonical, no mutation', (self.root/'docs/lks-sdd/canonical.md').read_bytes())

    def finish(self, plan):
        return maintenance.recover(self.root,plan['preview_hash'],remove_authorized=plan['preview_hash'])

    def test_preview_readonly_exact_auth_and_two_phase_removal(self):
        before = {str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        plan = self.plan(); key = plan['preview_hash']
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertFalse((self.base/'backup.zip').exists())
        with self.assertRaises(ContractError): maintenance.apply(self.root,plan,'0'*64)
        result = maintenance.apply(self.root,plan,key)
        self.assertEqual('awaiting-removal-authorization',result['status'])
        self.assertEqual(3,len(list((self.root/OBJECTS).iterdir())))
        with self.assertRaises(ContractError): ensure_idle(self.root)
        with self.assertRaises(ContractError): maintenance.recover(self.root,key,remove_authorized='0'*64)
        self.assertEqual('compacted',self.finish(plan)['status'])
        self.assertFalse((self.root/PENDING).exists())
        self.assertEqual([],list((self.root/OBJECTS).iterdir()))
        self.assert_logical()
        self.assertEqual({sha(b):b for b in self.bodies},{p.name:p.read_bytes() for p in (self.base/'restore').iterdir()})

    def test_failure_boundaries_resume_without_second_owner(self):
        for boundary in ['before-publish','after-publish','during-restore','before-remove','during-remove','before-receipt','after-receipt']:
            with self.subTest(boundary=boundary):
                # Reuse the small fixture by explicitly restoring its physical originals.
                for raw in self.bodies:
                    path=self.root/(OBJECTS+sha(raw)); path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)
                for p in [self.base/'backup.zip',self.base/'restore']:
                    if p.is_dir(): shutil.rmtree(p)
                    elif p.exists(): p.unlink()
                plan=self.plan(); key=plan['preview_hash']
                def fail(phase):
                    if phase==boundary: raise InterruptedError(boundary)
                with patch.object(maintenance,'_checkpoint',side_effect=fail):
                    with self.assertRaises(InterruptedError):
                        maintenance.apply(self.root,plan,key)
                        self.finish(plan)
                self.assertTrue((self.root/PENDING).exists())
                with self.assertRaises(ContractError): maintenance.apply(self.root,plan,key)
                self.assert_logical()
                self.assertEqual('compacted',self.finish(plan)['status'])
                self.assert_logical()

    def test_changed_original_backup_and_pack_are_never_repaired_or_removed(self):
        plan=self.plan(); key=plan['preview_hash']; maintenance.apply(self.root,plan,key)
        original=self.root/(OBJECTS+sha(self.bodies[0])); original.write_bytes(b'later edit')
        with self.assertRaises(ContractError): self.finish(plan)
        self.assertEqual(b'later edit',original.read_bytes()); original.write_bytes(self.bodies[0])
        backup=self.base/'backup.zip'; old=backup.read_bytes(); backup.write_bytes(b'damaged')
        with self.assertRaises(ContractError): self.finish(plan)
        self.assertTrue(original.exists()); backup.write_bytes(old)
        pack=self.root/plan['packs'][0]['path']; old=pack.read_bytes(); pack.write_bytes(b'damaged')
        with self.assertRaises(ContractError): self.finish(plan)
        self.assertEqual(b'damaged',pack.read_bytes()); self.assertTrue(original.exists())
        pack.write_bytes(old); self.finish(plan); self.assert_logical()

    def test_stale_preview_unknown_files_space_and_reader_block(self):
        plan=self.plan(); publish_object(self.root,OBJECTS+sha(b'later'),b'later')
        with self.assertRaises(ContractError): maintenance.apply(self.root,plan,plan['preview_hash'])
        self.assertFalse((self.root/PENDING).exists())
        unknown=self.root/OBJECTS/'unknown'; unknown.write_bytes(b'keep')
        with self.assertRaises(ContractError): self.plan()
        self.assertEqual(b'keep',unknown.read_bytes()); unknown.unlink()
        with patch.object(maintenance.shutil,'disk_usage',return_value=shutil._ntuple_diskusage(1,1,0)):
            with self.assertRaises(ContractError): self.plan()
        pin=self.root/'.lks-sdd/distribution-lock.json'; raw=pin.read_bytes()
        changed=json.loads(raw); changed['storage_formats'].remove(maintenance.FORMAT); pin.write_bytes(canonical(changed))
        with self.assertRaises(ContractError): self.plan()
        pin.write_bytes(raw)

    def test_shared_business_recovery_dispatch_does_not_authorize_removal(self):
        from v2_storage import recover as business_recover
        from v3_storage import recover as public_recover
        plan=self.plan(); key=plan['preview_hash']; maintenance.apply(self.root,plan,key)
        self.assertEqual('awaiting-removal-authorization',business_recover(self.root,key)['status'])
        self.assertEqual('awaiting-removal-authorization',public_recover(self.root,key)['status'])
        with self.assertRaises(ContractError): public_recover(self.root,key,rollback=True)
        self.assertEqual(3,len(list((self.root/OBJECTS).iterdir())))
        self.finish(plan)

    def test_restore_conflict_preserves_foreign_content(self):
        plan=self.plan(); destination=Path(plan['restore']); destination.mkdir(); (destination/'foreign').write_bytes(b'keep')
        with self.assertRaises(ContractError): maintenance.apply(self.root,plan,plan['preview_hash'])
        self.assertEqual(b'keep',(destination/'foreign').read_bytes())
        self.assertEqual(3,len(list((self.root/OBJECTS).iterdir())))

    def test_separate_process_cannot_recover_the_same_pending_slot(self):
        plan=self.plan(); key=plan['preview_hash']; maintenance.apply(self.root,plan,key)
        program = ('import sys;sys.path.insert(0,sys.argv[1]);from store_maintenance import recover;'
                   'recover(sys.argv[2],sys.argv[3])')
        with maintenance._exclusive(self.root):
            from path_utils import filesystem_root
            spelling=filesystem_root(self.root,force_extended=True) if os.name=='nt' else self.root
            result=subprocess.run([sys.executable,'-B','-c',program,str(ROOT/'scripts'),str(spelling),key],
                                  capture_output=True,timeout=15)
        self.assertNotEqual(0,result.returncode)
        self.assertIn(b'Another recovery owns',result.stderr)
        self.assertEqual(3,len(list((self.root/OBJECTS).iterdir())))
        self.finish(plan)

    def test_reference_resolution_and_large_protected_objects(self):
        ref=reference(b'absent'); body=canonical({'reference':ref})
        publish_object(self.root,OBJECTS+sha(body),body)
        with self.assertRaisesRegex(ContractError,'Unresolved'): self.plan()
        publish_object(self.root,OBJECTS+sha(b'absent'),b'absent')
        raw=b'x'*(maintenance.codec.TARGET+1)
        publish_object(self.root,OBJECTS+sha(raw),raw)
        plan=self.plan(); self.assertIn(sha(raw),plan['protected'])
        self.assertNotIn(sha(raw),plan['originals'])
        maintenance.apply(self.root,plan,plan['preview_hash']); self.finish(plan)
        self.assertEqual(raw,read_object(self.root,reference(raw)))

    def test_pack_mutation_between_full_hash_and_object_read_blocks_removal(self):
        plan=self.plan(); key=plan['preview_hash']; maintenance.apply(self.root,plan,key)
        packed=maintenance.codec._read_packed
        def race(root,digest,location,limit):
            path=self.root/plan['packs'][0]['path']
            body=bytearray(path.read_bytes()); body[0] ^= 1; path.write_bytes(body)
            return packed(root,digest,location,limit)
        with patch.object(maintenance.codec,'_read_packed',side_effect=race):
            with self.assertRaises(ContractError): self.finish(plan)
        self.assertEqual(3,len(list((self.root/OBJECTS).iterdir())))

    def test_business_journals_20_and_21_recover_after_compaction(self):
        import base64
        from v2_storage import preview,apply,recover,_save_transaction,TRANSACTION_STORE
        path='docs/lks-sdd/canonical.md'; before=(self.root/path).read_bytes()
        for version in ['2.0','2.1']:
            with self.subTest(version=version):
                after=('After '+version).encode(); changes={path:after}
                expected=preview(self.root,changes,sources={},operation='business-'+version)
                key=expected['preview_hash']
                if version=='2.0':
                    journal={'schema_version':'2.0','preview':expected,'state':'completed',
                        'before':{path:base64.b64encode(before).decode()},'after':{path:base64.b64encode(after).decode()}}
                    write_one(self.root,path,after);_save_transaction(self.root,key,journal)
                else: apply(self.root,changes,expected,key)
                loose=('unreferenced physical original '+version).encode()
                publish_object(self.root,OBJECTS+sha(loose),loose)
                # Give each explicit maintenance operation new external destinations.
                plan=maintenance.preview(self.root,self.base/('backup-'+version+'.zip'),self.base/('restore-'+version))
                maintenance.apply(self.root,plan,plan['preview_hash']);self.finish(plan)
                result=recover(self.root,key,rollback=True,receipt=TRANSACTION_STORE)
                self.assertEqual('rolled-back',result['status']);self.assertEqual(before,(self.root/path).read_bytes())
                self.assert_logical()

    def test_later_unknown_content_is_preserved_and_never_collected(self):
        plan=self.plan();key=plan['preview_hash'];maintenance.apply(self.root,plan,key)
        later=b'later unreferenced content';publish_object(self.root,OBJECTS+sha(later),later)
        foreign=self.root/'.lks-sdd/objects/unknown-folder';foreign.mkdir();(foreign/'keep').write_bytes(b'keep')
        self.finish(plan)
        self.assertEqual(later,read_object(self.root,reference(later)))
        self.assertTrue((self.root/(OBJECTS+sha(later))).exists())
        self.assertEqual(b'keep',(foreign/'keep').read_bytes());self.assert_logical()

    def test_legacy_pending_larger_than_maintenance_limit_still_recovers(self):
        import base64
        from v2_storage import preview,recover
        path='docs/lks-sdd/canonical.md';before=(self.root/path).read_bytes();after=b'a'*(13*1024*1024)
        expected=preview(self.root,{path:after},sources={},operation='legacy-large')
        journal={'schema_version':'2.0','preview':expected,'state':'applying',
                 'before':{path:base64.b64encode(before).decode()},'after':{path:base64.b64encode(after).decode()}}
        raw=canonical(journal);self.assertGreater(len(raw),maintenance.JOURNAL_LIMIT)
        write_one(self.root,path,after);write_one(self.root,PENDING,raw)
        result=recover(self.root,expected['preview_hash'],rollback=True)
        self.assertEqual('rolled-back',result['status']);self.assertEqual(before,(self.root/path).read_bytes())


if __name__ == '__main__': unittest.main()
