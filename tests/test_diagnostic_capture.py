"""External capture, publication recovery and programmatic conservation."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import diagnostic_capture as dc
from v3_contract import ContractError,canonical,sha
from v3_usage import observe
from path_utils import filesystem_root
import test_v4_cli_presentation as presentation_fixture


class CaptureTests(unittest.TestCase):
    def test_conflicting_object_lengths_in_different_fields_are_rejected(self):
        self.store();entry=dc.load(self.directory)['entries'][0]
        ref=next(iter(entry['materials'].values()))
        entry['transport']['alias']={**ref,'bytes':ref['bytes']+1}
        for directory in ('entries','pending'):
            (self.directory/directory/(entry['id']+'.json')).write_bytes(canonical(entry))
        with self.assertRaisesRegex(ContractError,'Conflicting capture object reference'):dc.load(self.directory)

    def test_unique_verification_is_local_and_late_corruption_is_rejected(self):
        self.store()
        other=dc.Capture(self.directory,self.root,'synthetic-run')
        value=self.sample();value['usage']['observations'][0]['run_id']=other.run_id
        other.store({'status':'second'},value,argv=[])
        original=dc.get
        with patch.object(dc,'get',wraps=original) as reader:
            loaded=dc.load(self.directory)
        material=next(iter(loaded['materials'].values()))
        self.assertEqual(1,sum(call.args[1]==material for call in reader.call_args_list))
        # No trust result survives another load, even in this same process.
        path=self.directory/'objects'/material['sha256'];path.write_bytes(b'corrupt')
        with self.assertRaises(ContractError):dc.load(self.directory)

    def test_deferred_verification_detects_damage_before_return_and_alias_limits_remain(self):
        self.store();loaded=dc.load(self.directory);ref=next(iter(loaded['materials'].values()))
        original=dc.checked_entry
        def damage(*args,**kwargs):
            value=original(*args,**kwargs)
            (self.directory/'objects'/ref['sha256']).write_bytes(b'damaged')
            return value
        with patch.object(dc,'checked_entry',side_effect=damage),self.assertRaises(ContractError):dc.load(self.directory)

    def test_compact_capture_stdout_is_exact_and_api_contract_stays_complete(self):
        result=self.sample();shown={'status':'completed','effects':[{'stage':'close'}]}
        text=self.cap.store(shown,result,argv=[],compact_output=True)
        self.assertEqual(1,text.count('\n'))
        loaded=dc.load(self.directory);entry=loaded['entries'][0]
        self.assertEqual(text.encode(),dc.get(self.directory,entry['transport']['stdout']))
        self.assertEqual(result,json.loads(dc.get(self.directory,entry['transport']['api_result'])))

    def test_read_allocation_is_bounded_and_growth_shrink_and_budget_still_reject(self):
        path=self.base/'bounded.txt';path.write_bytes(b'small')
        class Stream(io.BytesIO):
            def read(self,size=-1):
                requested.append(size);return super().read(size)
        for raw,valid in ((b'small',True),(b'larger',False),(b'tiny',False)):
            requested=[]
            with patch.object(Path,'open',return_value=Stream(raw)):
                if valid:self.assertEqual(raw,dc.read_file(path))
                else:
                    with self.assertRaisesRegex(ContractError,'changed'):dc.read_file(path)
            self.assertEqual([6],requested)
        with patch.object(Path,'open') as opened:
            with self.assertRaisesRegex(ContractError,'budget'):dc.read_file(path,maximum=4)
            opened.assert_not_called()
        self.assertEqual(b'small',path.read_bytes())

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='diagnostic-capture-')
        self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)
        self.root=self.base/'consumer';self.root.mkdir();self.directory=self.base/'capture'
        self.cap=dc.Capture(self.directory,self.root,'synthetic-run')

    def sample(self,text='Obligación íntegra: no borrar. Ámbito euskara.'):
        result={'sources':[{'key':'source','text':text}]}
        result['usage']={'observations':[observe('context',{},result,context={'run_id':self.cap.run_id})]}
        return result

    def store(self,**kwargs):
        value=self.sample()
        return self.cap.store({'status':'observed','text':value['sources'][0]['text']},value,argv=['context','ROOT'],**kwargs)

    def test_exact_stdout_input_and_full_api_are_recoverable(self):
        raw=b'{ "literal": "input with spaces" }\r\n'
        output=self.store(input_raw=raw)
        loaded=dc.load(self.directory);entry=loaded['entries'][0]
        self.assertEqual(output.encode('utf-8'),dc.get(self.directory,entry['transport']['stdout']))
        self.assertEqual(raw,dc.get(self.directory,entry['transport']['input']))
        self.assertIn('usage',json.loads(dc.get(self.directory,entry['transport']['api_result'])))
        info=dc.inspect(self.directory)
        self.assertEqual(len(output.encode('utf-8')),info['prepared_stdout_bytes'])
        self.assertEqual(len(raw),info['input_file_bytes']);self.assertEqual('unobserved',info['host_received'])
        self.assertEqual([],list(self.root.iterdir()))

    def test_identical_publication_replay_and_collision(self):
        value=self.sample();shown={'status':'observed'}
        first=self.cap.store(shown,value,argv=[])
        before=dc.inspect(self.directory)
        self.assertEqual(first,self.cap.store(shown,value,argv=[]))
        self.assertEqual(before,dc.inspect(self.directory))
        with self.assertRaisesRegex(ContractError,'collision'):self.cap.store({'status':'other'},value,argv=[])
        self.assertEqual(before,dc.inspect(self.directory))

    def test_pending_interruption_recovers_without_reexecuting_operation(self):
        value=self.sample()
        with self.assertRaises(InterruptedError):self.cap.store({'status':'observed'},value,argv=[],interrupt_after='pending')
        self.assertEqual('incomplete',dc.inspect(self.directory)['status'])
        self.assertEqual(0,dc.inspect(self.directory)['observations'])
        recovered=dc.recover(self.directory)
        self.assertEqual('stored',recovered['status']);self.assertEqual(1,len(recovered['writes']))
        self.assertTrue(Path(recovered['writes'][0]).is_file())
        self.assertEqual([],dc.recover(self.directory)['writes'])
        self.assertEqual(1,dc.recover(self.directory)['observations'])
        self.assertEqual([],list(self.root.iterdir()))

    def test_object_stage_interruption_does_not_claim_a_complete_entry(self):
        with self.assertRaises(InterruptedError):self.store(interrupt_after=0)
        self.assertEqual('incomplete',dc.inspect(self.directory)['status'])
        self.assertEqual(0,dc.recover(self.directory)['entries'])

    def test_pending_window_requires_recovery_before_another_invocation(self):
        value=self.sample()
        with self.assertRaises(InterruptedError):self.cap.store({},value,argv=[],interrupt_after='pending')
        before=dc.inspect(self.directory)
        other=dc.Capture(self.directory,self.root,'synthetic-run')
        with self.assertRaisesRegex(ContractError,'Recover pending'):other.store({},self.sample('another'),argv=[])
        self.assertEqual(before,dc.inspect(self.directory))
        self.assertEqual('stored',dc.recover(self.directory)['status'])

    def test_later_interruption_exposes_uncommitted_objects_without_losing_prior_entry(self):
        self.store();other=dc.Capture(self.directory,self.root,'synthetic-run')
        with self.assertRaises(InterruptedError):other.store({},self.sample('new body'),argv=[],interrupt_after=3)
        info=dc.inspect(self.directory)
        self.assertEqual('incomplete',info['status']);self.assertEqual(1,info['entries'])
        self.assertTrue(info['unreferenced_objects'])
        self.assertEqual(info,dc.recover(self.directory))

    def test_corruption_is_rejected_without_repair(self):
        self.store();value=dc.load(self.directory);ref=value['entries'][0]['transport']['stdout']
        path=self.directory/'objects'/ref['sha256'];path.write_bytes(b'corrupted')
        with self.assertRaises(ContractError):dc.inspect(self.directory)
        with self.assertRaises(ContractError):dc.recover(self.directory)
        self.assertEqual(b'corrupted',path.read_bytes())

    def test_shadow_pending_corruption_is_rejected_without_repair(self):
        self.store();entry=dc.load(self.directory)['entries'][0]
        duplicate=self.directory/'pending'/(entry['id']+'.json');duplicate.write_bytes(b'corrupted pending')
        with self.assertRaises(ContractError):dc.inspect(self.directory)
        with self.assertRaises(ContractError):dc.recover(self.directory)
        self.assertEqual(b'corrupted pending',duplicate.read_bytes())

    def test_alias_expansion_is_bounded_before_reading_the_next_batch(self):
        self.store();entry=dc.load(self.directory)['entries'][0]
        entry['batches']*=2;size=entry['batches'][0]['bytes']
        with patch.object(dc,'LIMIT',size),patch.object(dc,'get',wraps=dc.get) as reader:
            with self.assertRaisesRegex(ContractError,'byte budget'):dc.checked_entry(dc.safe_root(self.directory),canonical(entry))
            self.assertEqual(1,reader.call_count)
        with patch.object(dc,'MAX_OBSERVATIONS',1),self.assertRaisesRegex(ContractError,'observation budget'):
            dc.checked_entry(dc.safe_root(self.directory),canonical(entry))

    def test_transport_references_and_duplicate_row_limits_are_validated(self):
        self.store();entry=dc.load(self.directory)['entries'][0];entry['transport']['stdout']='unsupported'
        with self.assertRaises(ContractError):dc.checked_entry(dc.safe_root(self.directory),canonical(entry))
        other=dc.Capture(self.base/'duplicates',self.root,'synthetic-run');value=self.sample()
        value['usage']['observations']*=2
        with patch.object(dc,'MAX_OBSERVATIONS',1),self.assertRaises(ContractError):other.store({},value,argv=[])
        self.assertFalse(other.root.exists())

    def test_empty_capture_cannot_claim_already_conserved(self):
        self.cap.store({'status':'available'},{'status':'available'},argv=[])
        with self.assertRaisesRegex(ContractError,'No committed observations'):
            dc.record(self.root,{'capture_dir':str(self.directory)})

    def test_other_run_unknown_files_and_consumer_destination_are_rejected(self):
        self.store()
        with self.assertRaises(ContractError):dc.Capture(self.directory,self.root,'another-run')
        with self.assertRaises(ContractError):dc.Capture(self.root/'hidden-capture',self.root)
        extra=self.base/'unowned';extra.mkdir();(extra/'keep.txt').write_text('foreign')
        with self.assertRaises(ContractError):dc.Capture(extra,self.root)
        self.assertEqual(['keep.txt'],[p.name for p in extra.iterdir()])

    def test_credential_refusal_does_not_change_normative_result_or_save_values(self):
        stdout=io.StringIO()
        with contextlib.redirect_stdout(stdout):dc.emit({'status':'available'},self.sample(),self.cap,argv=[],input_raw=b'{"access_token":"SYNTHETIC-NON-SECRET"}')
        shown=json.loads(stdout.getvalue());self.assertEqual('available',shown['status'])
        self.assertEqual('failed',shown['diagnostic_capture']['status'])
        self.assertFalse(self.directory.exists());self.assertNotIn('SYNTHETIC',stdout.getvalue())

    def test_file_and_byte_budgets_and_busy_window_preserve_existing_capture(self):
        self.store();before=dc.inspect(self.directory)
        for attribute,limit in [('MAX_FILES',len(dc.load(self.directory)['files'])),('LIMIT',100)]:
            with patch.object(dc,attribute,limit),self.assertRaises(ContractError):
                dc.Capture(self.directory,self.root,'synthetic-run').store({'different':True},self.sample(),argv=[])
        self.assertEqual(before,dc.inspect(self.directory))
        with dc.locked(self.directory):
            with self.assertRaises((ContractError,OSError)):
                dc.Capture(self.directory,self.root,'synthetic-run').store({},self.sample(),argv=[])

    def test_material_gaps_remain_incomplete_and_imports_never_promote(self):
        result=self.sample('Contenido largo.\n'*6000)
        text=self.cap.store({'status':'observed'},result,argv=[])
        self.assertEqual('stored',json.loads(text)['diagnostic_capture']['status'])
        value,rows,materials=dc.imported_window(self.directory)
        self.assertEqual('agent-declared',rows[0]['origin']['kind'])
        self.assertEqual('declared',rows[0]['metrics']['prepared_bytes']['status'])
        self.assertIn(sha(result['sources'][0]['text'].encode()),materials)
        other=dc.Capture(self.base/'missing',self.root,'synthetic-run')
        other.store({'status':'observed'},{'usage':result['usage']},argv=[])
        self.assertEqual('incomplete',dc.inspect(other.root)['status'])

    def test_recovery_refuses_to_exceed_capacity(self):
        with self.assertRaises(InterruptedError):self.store(interrupt_after='pending')
        count=len(dc.load(self.directory)['files'])
        with patch.object(dc,'MAX_FILES',count),self.assertRaises(ContractError):dc.recover(self.directory)
        self.assertTrue(dc.inspect(self.directory)['pending'])

    def test_early_runtime_failure_is_captured_without_weakening_the_block(self):
        from lks_sdd import runtime_failure
        stdout=io.StringIO()
        with contextlib.redirect_stdout(stdout):runtime_failure({'status':'blocked','error':'Wrong pinned runtime','writes':[]},'v3',['context',str(self.root),'--view','operational','--capture-dir',str(self.directory)])
        result=json.loads(stdout.getvalue())
        self.assertEqual('blocked',result['status']);self.assertEqual([],result['writes'])
        self.assertEqual('stored',result['diagnostic_capture']['status'])
        self.assertEqual(1,dc.inspect(self.directory)['observations'])
        self.assertFalse(dc.early_options(['--input','--capture-dir']).get('--capture-dir'))
        inside=self.root/'forbidden'
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            runtime_failure({'status':'blocked','error':'Wrong pinned runtime','writes':[]},'v3',['--view','operational','context',str(self.root),'--capture-dir',str(inside)])
        self.assertEqual('failed',json.loads(stdout.getvalue())['diagnostic_capture']['status'])
        self.assertEqual([],list(self.root.iterdir()))

    def test_invalid_input_bytes_and_run_limits_are_reported_without_consumer_writes(self):
        from v3_cli import main
        source=self.base/'invalid.json';raw=b'{ invalid JSON }\r\n';source.write_bytes(raw)
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            code=main(['context',str(self.root),'--input',str(source),'--view','operational','--capture-dir',str(self.directory)])
        result=json.loads(stdout.getvalue());self.assertEqual(2,code)
        self.assertEqual('blocked',result['status']);self.assertEqual('stored',result['diagnostic_capture']['status'])
        entry=dc.load(self.directory)['entries'][0]
        self.assertEqual(1,dc.inspect(self.directory)['observations'])
        self.assertEqual(raw,dc.get(dc.safe_root(self.directory),entry['transport']['input']))
        with self.assertRaises(ContractError):dc.Capture(self.base/'bad-run',self.root,42)
        other=dc.Capture(self.base/'excess',self.root,'synthetic-run')
        value=self.sample();two=copy.deepcopy(value['usage']['observations'][0]);two['observation_id']='another'
        value['usage']['observations'].append(two)
        with patch.object(dc,'MAX_OBSERVATIONS',1),self.assertRaises(ContractError):other.store({},value,argv=[])
        self.assertFalse(other.root.exists());self.assertEqual([],list(self.root.iterdir()))

    @unittest.skipUnless(os.name=='nt','real Windows long paths')
    def test_long_unicode_capture_paths_and_retry_names_are_bounded(self):
        directory=filesystem_root(self.base/('Ámbito con espacios'+'a'*65)/('b'*70)/('c'*70)/'capture')
        self.addCleanup(lambda:shutil.rmtree(directory.parent) if directory.parent.exists() else None)
        cap=dc.Capture(directory,self.root,'synthetic-run')
        value=self.sample();cap.store({},value,argv=[])
        before=dc.inspect(directory)
        cap.store({},value,argv=[])
        self.assertEqual(before,dc.inspect(directory));self.assertGreater(len(str(directory)),260)
        self.assertTrue(all(len(p.name)<=64 for p in directory.rglob('*') if p.is_file() and not p.name.endswith('.json')))

    @unittest.skipUnless(os.name=='nt','real Windows descendant paths')
    def test_shorter_root_with_descendants_over_260_uses_extended_io(self):
        relative='d'*(210-len(str(self.base)))
        directory=self.base/relative
        cap=dc.Capture(directory,self.root,'synthetic-run');cap.store({},self.sample(),argv=[])
        self.addCleanup(lambda:shutil.rmtree(cap.root) if cap.root.exists() else None)
        self.assertLess(len(str(directory)),248)
        self.assertGreater(max(len(str(p)) for p in cap.root.rglob('*')),260)
        self.assertEqual('stored',dc.inspect(directory)['status'])


class CurrentCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):presentation_fixture.MinimalPresentationTests.setUpClass()
    def setUp(self):
        self.case=presentation_fixture.MinimalPresentationTests(methodName='runTest');self.case.payload=presentation_fixture.MinimalPresentationTests.payload
        self.case.setUp();self.addCleanup(self.case.doCleanups)
        self.root=self.case.root;self.directory=self.case.out/'captured'
    def call(self,action,data=None,flags=()):return self.case.invoke(action,data,flags)

    def test_disabled_capture_and_enabled_capture_keep_contract_and_decision_receipt(self):
        before=presentation_fixture.snapshot(self.root)
        data=self.case.decision()
        a,plain,_=self.call('decision-view',data,['--view','operational'])
        b,captured,raw=self.call('decision-view',data,['--view','operational','--capture-dir',self.directory])
        self.assertEqual((0,0),(a,b));self.assertEqual(plain['receipt'],captured['receipt']);self.assertEqual(plain['markdown'],captured['markdown'])
        self.assertNotIn('diagnostic_capture',plain)
        self.assertEqual('stored',captured['diagnostic_capture']['status'])
        value=dc.load(self.directory)
        self.assertEqual(raw.encode(),dc.get(self.directory,value['entries'][0]['transport']['stdout']))
        self.assertEqual(before,presentation_fixture.snapshot(self.root))

    def test_capture_failure_does_not_hide_core_block_or_change_authority(self):
        before=presentation_fixture.snapshot(self.root)
        code,value,_=self.call('context',{'roots':['missing']},['--view','operational','--capture-dir',self.root/'forbidden'])
        self.assertEqual(2,code);self.assertEqual('blocked',value['status']);self.assertTrue(value['cause'])
        self.assertEqual('failed',value['diagnostic_capture']['status'])
        self.assertEqual(before,presentation_fixture.snapshot(self.root))
        code,value,_=self.call('context',{'roots':[self.case.prop]},['--capture-dir',self.root/'forbidden'])
        self.assertEqual(0,code);self.assertEqual('failed',value['diagnostic_capture']['status'])
        self.assertEqual(before,presentation_fixture.snapshot(self.root))

    def test_programmatic_conservation_after_source_removal_and_independent_export(self):
        import base64
        from v3_cli import execute
        from v3_storage import apply
        from v3_usage import catalog
        from v3_contract import load
        source=self.root/'docs/lks-sdd/capture-note.md';literal='Contenido completo que no puede desaparecer.\n'*2500
        source.write_text('---\nschema_version: "3.1"\n---\n\n'+literal,encoding='utf-8')
        image=self.root/'docs/lks-sdd/capture-asset.png'
        binary=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==')
        image.write_bytes(binary)
        source.write_text(source.read_text(encoding='utf-8')+'\n![Imagen pendiente de observar](capture-asset.png)\n',encoding='utf-8')
        before=presentation_fixture.snapshot(self.root)
        capture_durations=[];original_store=dc.Capture.store
        def measured_store(instance,*args,**kwargs):
            begin=time.monotonic()
            try:return original_store(instance,*args,**kwargs)
            finally:capture_durations.append(time.monotonic()-begin)
        started=time.monotonic()
        with patch.object(dc.Capture,'store',measured_store):
            code,shown,_=self.call('context',{'roots':[self.case.prop]},['--view','operational','--capture-dir',self.directory])
        self.assertEqual(0,code);self.assertEqual('stored',shown['diagnostic_capture']['status'])
        captured=dc.load(self.directory)
        api=json.loads(dc.get(captured['root'],captured['entries'][0]['transport']['api_result']))
        selected=next(s['text'].encode() for s in api['sources'] if s['source']['path']=='docs/lks-sdd/capture-note.md')
        self.assertTrue(literal.rstrip() in selected.decode().replace('\r\n','\n'), 'Selected body must retain the complete literal')
        self.assertEqual(before,presentation_fixture.snapshot(self.root));source.unlink();image.unlink()
        capture_seconds=time.monotonic()-started
        started=time.monotonic();packet=execute('usage-record',self.root,{'actor':self.case.actor,'capture_dir':str(self.directory)})
        apply(self.root,packet,packet['preview']['preview_hash'],current=True)
        conservation_seconds=time.monotonic()-started
        self.assertEqual('already-recorded',execute('usage-record',self.root,{'actor':self.case.actor,'capture_dir':str(self.directory)})['status'])
        rows=catalog(load(self.root).require_valid(),run_id=shown['diagnostic_capture']['run_id'])
        self.assertTrue(rows,{'expected_run':shown['diagnostic_capture']['run_id'],'capture_source':packet.get('capture_source')})
        self.assertTrue(all(r['origin']['kind']=='agent-declared' for r in rows),[r['origin'] for r in rows])
        started=time.monotonic();report=execute('usage-report',self.root,{'capture_dir':str(self.directory)})
        self.assertTrue(report['summary']);report_seconds=time.monotonic()-started
        started=time.monotonic();bundle=execute('usage-export',self.root,{'capture_dir':str(self.directory)})
        self.assertTrue(any(selected==base64.b64decode(v) for v in bundle['files'].values()))
        self.assertTrue(any(binary==base64.b64decode(v) for v in bundle['files'].values()))
        from usage_bundle import export,inspect
        destination=self.case.out/'portable';export(bundle,destination,bundle['export_hash'])
        self.assertEqual('needs-material',inspect(destination)['bundle_status'])
        self.assertEqual(['No substantiated trigger; supply a bounded case and expected behavior'],bundle['manifest']['missing'])
        self.assertTrue(all(p in bundle['manifest']['files'] for p in ['observations.json','REPORT.md']))
        import subprocess
        cold=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'scripts/lks_sdd.py'),'usage-inspect',str(destination),'--reproduce'],capture_output=True,text=True,encoding='utf-8',timeout=60)
        self.assertEqual(0,cold.returncode,cold.stdout+cold.stderr)
        self.assertEqual('reproduced',json.loads(cold.stdout)['reproduction']['status'])
        from usage_bundle import reproduce
        graph=json.loads(base64.b64decode(bundle['files']['reproduction/fixture.json']))
        self.assertEqual(sha(binary),graph['cases'][0]['expected_sources']['docs/lks-sdd/capture-asset.png'])
        graph['cases'][0]['files']['docs/lks-sdd/capture-asset.png']=base64.b64encode(binary+b'changed').decode()
        self.assertEqual('not-reproduced',reproduce({'reproduction/fixture.json':canonical(graph)})['status'])
        export_seconds=time.monotonic()-started
        if os.environ.get('LKS_V4_CAPTURE_EVIDENCE'):
            import zipfile
            artifact=Path(os.environ['LKS_V4_CAPTURE_EVIDENCE']).with_suffix('.case.zip')
            with zipfile.ZipFile(artifact,'w',zipfile.ZIP_DEFLATED) as package:
                for prefix,directory in [('capture',self.directory),('bundle',destination)]:
                    for file in directory.rglob('*'):
                        if file.is_file():package.write(file,prefix+'/'+file.relative_to(directory).as_posix())
                package.writestr('independent-inspection.json',cold.stdout)
        corrupt=next(e for e in load(self.root).by_kind('receipt') if e.data.get('purpose')=='usage-observation').data['observations_ref']
        from content_store import object_path
        damaged=self.root/object_path(corrupt);damaged.write_bytes(b'corrupted')
        code,blocked,_=self.call('context',{'roots':[self.case.prop]},['--view','operational','--capture-dir',self.directory])
        self.assertEqual(2,code);self.assertEqual('blocked',blocked['status']);self.assertEqual(b'corrupted',damaged.read_bytes())
        if os.environ.get('LKS_V4_CAPTURE_EVIDENCE'):
            Path(os.environ['LKS_V4_CAPTURE_EVIDENCE']).write_text(json.dumps({'capture_query_seconds':capture_seconds,'capture_store_seconds':sum(capture_durations),'capture_store_scope':'Nested in query; excludes preflight and initial input read','conservation_prepare_apply_seconds':conservation_seconds,'report_seconds':report_seconds,'export_preview_write_inspect_seconds':export_seconds,'scope':'Synthetic component phases, not whole-task saving; archive retention excluded'},indent=2),encoding='utf-8')

    def test_capture_after_apply_retains_effects_packet_bytes_and_recovery(self):
        from v3_contract import element
        packet_path=self.case.out/'packet.json'
        code,preview,_=self.call('author',{'actor':self.case.actor,'items':[element('request','Captura aplicada','Caso sintético')]},['--output',packet_path])
        self.assertEqual(0,code)
        from v3_cli import main
        stdout=io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code=main(['apply',str(self.root),'--input',str(packet_path),'--authorize',preview['preview_hash'],'--view','operational','--capture-dir',str(self.directory)])
        value=json.loads(stdout.getvalue());self.assertEqual(0,code)
        self.assertEqual('stored',value['diagnostic_capture']['status'])
        entry=dc.load(self.directory)['entries'][0]
        self.assertTrue(entry['transport']['input_packet'])
        self.assertEqual(value['receipt'],json.loads(dc.get(self.directory,entry['transport']['api_result']))['receipt'])
        self.assertEqual('stored',dc.recover(self.directory)['status'])

    def test_multiple_batches_use_one_existing_journal_and_replay_is_idempotent(self):
        from v3_cli import execute
        from v3_storage import apply
        from v3_usage import catalog
        from v3_contract import load
        cap=dc.Capture(self.directory,self.root,'multiple-batches')
        template=observe('synthetic-batch',{'declared_material':'x'*20000},{'status':'observed'},context={'run_id':cap.run_id})
        rows=[]
        for index in range(100):
            row=copy.deepcopy(template);row['observation_id']='synthetic-'+str(index);rows.append(row)
        cap.store({'status':'observed'},{'usage':{'observations':rows}},argv=[])
        self.assertGreater(len(dc.load(self.directory)['entries'][0]['batches']),1)
        packet=execute('usage-record',self.root,{'actor':self.case.actor,'capture_dir':str(self.directory)})
        result=apply(self.root,packet,packet['preview']['preview_hash'],current=True)
        self.assertTrue(result['receipt'])
        self.assertEqual(100,len(catalog(load(self.root),run_id=cap.run_id)))
        self.assertEqual('already-recorded',execute('usage-record',self.root,{'actor':self.case.actor,'capture_dir':str(self.directory)})['status'])

    def test_report_respects_focal_capture_entry_selection(self):
        from v3_cli import execute
        for index in range(2):
            cap=dc.Capture(self.directory,self.root,'report-selection')
            result={'status':'observed'};result['usage']={'observations':[observe('synthetic',{},result,context={'run_id':cap.run_id})]}
            cap.store(result,result,argv=[])
        entry=dc.load(self.directory)['entries'][0]['id']
        data={'capture_dir':str(self.directory),'capture_entries':[entry]}
        self.assertEqual(1,execute('usage-report',self.root,data)['metrics']['observations'])
        self.assertEqual(2,execute('usage-report',self.root,{'capture_dir':str(self.directory)})['metrics']['observations'])

    def test_public_report_preserves_list_summary_and_complete_content(self):
        from v3_cli import execute
        code,shown,_=self.call('context',{'roots':[self.case.prop]},
            ['--view','operational','--capture-dir',self.directory])
        self.assertEqual(0,code)
        data={'capture_dir':str(self.directory)}
        expected=execute('usage-report',self.root,data)
        self.assertIsInstance(expected['summary'],list)
        before=presentation_fixture.snapshot(self.root)
        for flags in (['--json'],['--view','operational','--json'],['--details'],['--compact']):
            code,report,_=self.call('usage-report',data,flags)
            self.assertEqual(0,code,report)
            self.assertEqual(expected['summary'],report['summary'])
            self.assertEqual(expected['markdown'],report['markdown'])
            self.assertEqual(expected['metrics'],report['metrics'])
        exported=self.case.out/'usage-report.json'
        code,reference,_=self.call('usage-report',data,['--view','operational','--output',exported])
        self.assertEqual(0,code,reference)
        full=json.loads(exported.read_bytes())
        self.assertEqual(expected,full)
        self.assertEqual(expected['summary'],reference['summary'])
        self.assertNotIn('markdown',reference)
        self.assertEqual(before,presentation_fixture.snapshot(self.root))

    @unittest.skipUnless(os.name=='nt','real Windows temporary paths')
    def test_documentary_reproduction_uses_long_unicode_temporary_root(self):
        from usage_bundle import fixture,reproduce
        directory=self.case.out/('Ámbito con espacios'+'x'*max(1,210-len(str(self.case.out))-19))
        directory.mkdir();self.assertLess(len(str(directory)),248)
        graph={'reproduction/fixture.json':canonical(fixture(self.root,[self.case.prop]))}
        with patch.object(tempfile,'tempdir',str(directory)):
            self.assertEqual('reproduced',reproduce(graph)['status'])


if __name__=='__main__':unittest.main()
