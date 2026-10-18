"""Differential preparation, physical freshness and shared public adapters."""
import base64
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import test_v4_cli_presentation as fixture
from v3_contract import ContractError,canonical,element,load,render
from v3_cli import execute,main
from v4_work_prepare import REQUEST,RESULT,prepare
from path_utils import filesystem_root


class WorkPrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.MinimalPresentationTests.setUpClass()
        cls.case=fixture.MinimalPresentationTests(methodName='runTest');cls.case.payload=fixture.MinimalPresentationTests.payload
        cls.case.setUp();cls.addClassCleanup(cls.case.doCleanups)
        cls.case.case.close_proposal();cls.case.case.create_plan()
        cls.actor=cls.case.actor;cls.task=cls.case.case.task;cls.req=cls.case.req
        (cls.case.root/'app.py').write_bytes(b"def greeting(): return 'Adios'\n")

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='work-prepare-');self.addCleanup(self.temp.cleanup)
        self.out=Path(self.temp.name);self.root=self.out/'consumer'
        shutil.copytree(self.case.root,self.root)

    def data(self,**values):
        return {'format':REQUEST,'version':1,'operation_id':'auto','task':self.task,'actor':self.actor,**values}

    def call(self,data=None,flags=()):
        source=self.out/'input.json';source.write_bytes(canonical(data if data is not None else self.data()))
        stdout=io.StringIO()
        with contextlib.redirect_stdout(stdout):code=main(['work-prepare',str(self.root),'--input',str(source),*map(str,flags)])
        return code,json.loads(stdout.getvalue()),stdout.getvalue()

    def edit(self,uid,change):
        item=copy.deepcopy(load(self.root).get(uid).item());change(item)
        path=self.root/load(self.root).get(uid).path
        path.write_bytes(render(item,version='3.1'))

    def test_ready_is_read_only_and_matches_individual_queries(self):
        before=fixture.snapshot(self.root);code,value,_=self.call()
        self.assertEqual(0,code,value);self.assertEqual('ready',value['status']);self.assertEqual([],value['effects'])
        self.assertEqual(before,fixture.snapshot(self.root));self.assertTrue(value['contract']['sources'])
        direct=execute('readiness',self.root,{'task':self.task,'actor':self.actor,'action':'start'})
        self.assertEqual({k:v for k,v in direct.items() if k not in {'usage','journey'}},value['preparation'][0]['readiness'])
        self.assertEqual(direct['journey'],value['interventions'])
        context=execute('context',self.root,{'roots':[self.task],'operation':'start'})
        self.assertEqual(context['sources'],value['contract']['sources']);self.assertEqual(context['attachments'],value['contract']['attachments'])
        state=execute('status',self.root,{'request':self.req,'task':self.task})
        state.pop('usage');state['requests'][0].pop('journey')
        self.assertEqual(state,value['work_state'])

    def test_shared_model_counters_include_internal_work(self):
        value=prepare(self.root,self.data());self.assertEqual('ready',value['status'],value)
        counts=value['evaluation_metrics']['counters']
        self.assertEqual(1,counts['model_loads']);self.assertEqual(1,counts['calculation_scopes'])
        self.assertEqual(1,counts['status_evaluations']);self.assertEqual(1,counts['readiness_evaluations'])
        self.assertEqual(1,counts['intervention_evaluations']);self.assertGreaterEqual(counts['context_selections'],2)
        self.assertGreaterEqual(counts['git_commands'],6);self.assertEqual(1,counts['freshness_boundaries'])

    def test_missing_and_unknown_actor_never_prepare_execution(self):
        for actor in (None,'missing-person'):
            with self.subTest(actor=actor):
                code,value,_=self.call(self.data(actor=actor))
                self.assertEqual(2,code);self.assertEqual('action-required',value['status'])
                self.assertEqual([],value['portion']['ready']);self.assertTrue(value['contract']['sources'])

    def test_invalid_request_types_unknown_keys_and_bound_operation_ids(self):
        variants=[{'version':True},{'version':2},{'task':''},{'task':[]},{'unexpected':True},
                  {'parameters':{'action':'integrate'}},{'parameters':{'reference':'false'}},
                  {'parameters':{'command':'arbitrary'}},{'parameters':{'tasks':['x']*20}},{'actor':42}]
        before=fixture.snapshot(self.root)
        for update in variants:
            with self.subTest(update=update):self.assertEqual(2,self.call(self.data(**update))[0])
        _,value,_=self.call();identifier=value['operation_id']
        self.assertEqual(0,self.call(self.data(operation_id=identifier))[0])
        self.assertEqual(2,self.call(self.data(operation_id=identifier,parameters={'action':'resume'}))[0])
        self.assertEqual(before,fixture.snapshot(self.root))

    def test_unknown_retired_and_ambiguous_tasks_do_not_widen_to_another_task(self):
        for task in ('missing-task',self.req):
            code,value,_=self.call(self.data(task=task));self.assertEqual(2,code);self.assertEqual('blocked',value['status'])
        self.edit(self.task,lambda item:item['meta'].update(state='retired'))
        self.assertEqual('blocked',self.call()[1]['status'])

    def test_missing_authorization_and_task_review_match_core_causes(self):
        # Remove the authorization event; keep the canonical task/plan intact.
        event=next(e for e in load(self.root).by_kind('authorization') if e.data.get('purpose')=='execution')
        (self.root/event.path).unlink()
        direct=execute('readiness',self.root,{'task':self.task,'actor':self.actor})
        code,value,_=self.call();self.assertEqual(2,code)
        self.assertEqual(direct['causes'],value['preparation'][0]['readiness']['causes'])
        self.assertEqual([],value['portion']['ready'])

    def test_ambiguous_alias_is_blocked_without_choosing_another_uid(self):
        alias=load(self.root).get(self.task).id
        other=element('task','Alias duplicado','Otra tarea con alias igual',request=self.req,owner=self.actor,scope=['other.py'],acceptance=['Otro'],tests=['other'])
        other['meta']['id']=alias
        (self.root/'docs/lks-sdd/ambiguous.md').write_bytes(render(other,version='3.1'))
        code,value,_=self.call(self.data(task=alias))
        self.assertEqual(2,code);self.assertEqual('blocked',value['status']);self.assertIn('ambiguo',value['cause'])

    def test_rejected_task_review_is_not_silently_reused(self):
        review=next(e for e in load(self.root).by_kind('decision') if e.data.get('purpose')=='task-review')
        self.edit(review.uid,lambda item:item['meta']['data'].update(outcome='changes-requested'))
        direct=execute('readiness',self.root,{'task':self.task,'actor':self.actor})
        code,value,_=self.call();self.assertEqual(2,code)
        self.assertEqual(direct['causes'],value['preparation'][0]['readiness']['causes'])
        self.assertTrue(any('task-reviewed' in str(cause) for cause in direct['causes']))

    def test_critical_unknown_and_incoming_interface_are_retained(self):
        rule=element('rule','Decisión crítica pendiente','NO ejecutar sin resolver esta obligación.',critical=True,unresolved=True,global_rule=True)
        rule['meta']['state']='unknown';rule['meta']['data']['global']=True
        interface=element('interface','Contrato entrante','Conservar el contrato entrante de la porción.')
        interface['meta']['relations']['contributes_to']=[self.task]
        for name,item in [('critical',rule),('incoming',interface)]:
            (self.root/('docs/lks-sdd/'+name+'.md')).write_bytes(render(item,version='3.1'))
        code,value,_=self.call();self.assertEqual(2,code);self.assertEqual('action-required',value['status'])
        keys={s['key'] for s in value['contract']['sources']}
        self.assertIn(rule['meta']['uid'],keys);self.assertIn(interface['meta']['uid'],keys)
        self.assertEqual([],value['portion']['ready'])

    def test_independent_review_cannot_be_waived_by_preparation(self):
        from presentation_test_support import present
        from test_v3_workflow import commit_packet
        from v3_workflow import transition
        from v3_authoring import governance
        commit_packet(self.root,transition(self.root,self.actor,self.task,'start','Inicio sintético autorizado'))
        (self.root/'app.py').write_text("def greeting(): return 'Hola'\n",encoding='utf-8')
        commit_packet(self.root,transition(self.root,self.actor,self.task,'implement','Resultado sintético'))
        model=load(self.root);policy=copy.deepcopy(model.get(model.project.data['policy']).item())
        policy['meta']['revision']+=1;policy['meta']['data']['independent_review']=True
        commit_packet(self.root,present(governance,self.root,self.actor,[policy,element('member','Revisora sintética','Identidad sintética independiente.',roles=['reviewer'],active=True)],'Exijo revisión independiente','Política sintética',requests=[self.req]))
        direct=execute('readiness',self.root,{'task':self.task,'actor':self.actor,'action':'verify'})
        code,value,_=self.call(self.data(parameters={'action':'verify'}));self.assertEqual(2,code)
        self.assertEqual(direct['causes'],value['preparation'][0]['readiness']['causes'])
        self.assertIn('independiente',str(direct['causes']))

    def test_existing_apply_guards_reject_a_change_after_ready(self):
        from v3_workflow import transition
        from v3_storage import apply
        self.assertEqual('ready',self.call()[1]['status'])
        packet=transition(self.root,self.actor,self.task,'start','Inicio posterior a consulta')
        (self.root/'app.py').write_text('changed after preview',encoding='utf-8')
        before=fixture.snapshot(self.root)
        with self.assertRaises(ContractError):apply(self.root,packet,packet['preview']['preview_hash'],current=True)
        self.assertEqual(before,fixture.snapshot(self.root))

    def test_changed_head_is_detected_without_a_branch_change(self):
        from v3_guidance import readiness
        def altered(*args,**kwargs):
            result=readiness(*args,**kwargs)
            tree=subprocess.run(['git','-C',str(self.root),'hash-object','-t','tree','-w','--stdin'],input=b'',capture_output=True,check=True).stdout.decode().strip()
            commit=subprocess.run(['git','-C',str(self.root),'-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','-c','commit.gpgsign=false','commit-tree',tree,'-m','Synthetic base change'],capture_output=True,check=True).stdout.decode().strip()
            subprocess.run(['git','-C',str(self.root),'update-ref','refs/heads/codex/request',commit],capture_output=True,check=True)
            return result
        with patch('v3_guidance.readiness',side_effect=altered):code,value,_=self.call()
        self.assertEqual(2,code);self.assertIn('Git branch/base changed',value['cause'])

    def test_expiring_authority_during_preparation_is_detected(self):
        from datetime import datetime,timezone,timedelta
        from v3_guidance import readiness
        reference=datetime.now(timezone.utc)
        authorization=next(e for e in load(self.root).by_kind('authorization') if e.data.get('purpose')=='execution')
        self.edit(authorization.uid,lambda item:item['meta']['data'].update(expires_at=(reference+timedelta(seconds=30)).isoformat()))
        class Clock(datetime):
            elapsed=0
            @classmethod
            def now(cls,tz=None):return reference+timedelta(seconds=cls.elapsed)
        def later(*args,**kwargs):
            result=readiness(*args,**kwargs);Clock.elapsed=60;return result
        with patch('v3_policy.datetime',Clock),patch('v3_guidance.readiness',side_effect=later):code,value,_=self.call()
        self.assertEqual(2,code);self.assertIn('period changed',value['cause'])

    def test_literal_globals_uncertainty_incoming_dependencies_and_long_tail_remain(self):
        text='Obligación literal: conservar euskara y no borrar datos.\n'*2000
        (self.root/'docs/lks-sdd/unclassified-extra.md').write_text('---\nschema_version: "3.1"\n---\n\n'+text,encoding='utf-8')
        value=self.call()[1];self.assertTrue(any(s['key'].startswith('prose:') for s in value['contract']['sources']))
        actual='\n'.join(s['text'] for s in value['contract']['sources']).replace('\r\n','\n')
        self.assertIn(text.rstrip(),actual)
        self.assertEqual(execute('context',self.root,{'roots':[self.task],'operation':'start'})['sources'],value['contract']['sources'])

    def test_binary_attachment_is_not_assumed_observed_and_capture_keeps_it(self):
        raw=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==')
        (self.root/'docs/lks-sdd/asset.png').write_bytes(raw)
        (self.root/'docs/lks-sdd/asset-note.md').write_text('---\nschema_version: "3.1"\n---\n\n![Obligación](asset.png)',encoding='utf-8')
        before=fixture.snapshot(self.root);capture=self.out/'capture'
        code,value,stdout=self.call(flags=['--view','operational','--capture-dir',capture])
        self.assertEqual(2,code);self.assertEqual('action-required',value['status']);self.assertEqual([],value['portion']['ready'])
        self.assertEqual('stored',value['diagnostic_ref']['status']);self.assertEqual(before,fixture.snapshot(self.root))
        import diagnostic_capture as dc
        captured=dc.load(capture);entry=captured['entries'][0]
        self.assertIn(raw,[dc.get(captured['root'],ref) for ref in entry['materials'].values()])
        self.assertEqual(stdout.encode(),dc.get(captured['root'],entry['transport']['stdout']))
        self.assertTrue(entry['transport'].get('reproduction_fixture'));self.assertTrue(captured['observations'][0]['fragments'])

    def test_runtime_without_capability_is_blocked_and_does_not_migrate(self):
        path=self.root/'.lks-sdd/distribution-lock.json';lock=json.loads(path.read_bytes())
        runtime=self.root/lock['runtime'];relative='scripts/v4_work_prepare.py'
        (runtime/relative).unlink();lock['runtime_files'].pop(relative)
        from dual_distribution import digest,json_bytes
        lock['runtime_digest']=digest(json_bytes(lock['runtime_files']));path.write_bytes(json_bytes(lock))
        before=fixture.snapshot(self.root);code,value,_=self.call()
        self.assertEqual(2,code);self.assertIn('work-prepare/1',value['cause']);self.assertEqual(before,fixture.snapshot(self.root))

    def test_changed_source_during_preparation_blocks_every_ready_portion(self):
        from v3_guidance import readiness
        original=readiness
        def changed(*args,**kwargs):
            result=original(*args,**kwargs)
            (self.root/'docs/lks-sdd/new-source.md').write_text('---\nschema_version: "3.1"\n---\n\nNueva obligación',encoding='utf-8')
            return result
        with patch('v3_guidance.readiness',side_effect=changed):code,value,_=self.call()
        self.assertEqual(2,code);self.assertEqual('blocked',value['status']);self.assertEqual([],value['portion']['ready'])
        self.assertIn('membership changed',value['cause'])

    def test_changed_role_policy_code_and_branch_are_detected(self):
        from v3_guidance import readiness
        originals=fixture.snapshot(self.root)
        def check(change):
            def altered(*args,**kwargs):
                result=readiness(*args,**kwargs);change();return result
            with patch('v3_guidance.readiness',side_effect=altered):code,value,_=self.call()
            self.assertEqual(2,code);self.assertEqual('blocked',value['status']);self.assertEqual([],value['portion']['ready'])
        check(lambda:(self.root/'app.py').write_text('changed',encoding='utf-8'))
        (self.root/'app.py').write_bytes(originals['app.py'])
        check(lambda:self.edit(self.actor,lambda item:item['meta']['data'].update(roles=[])))
        for name,raw in originals.items():
            if name.startswith('docs/lks-sdd/'):(self.root/name).write_bytes(raw)
        policy=load(self.root).project.data['policy']
        check(lambda:self.edit(policy,lambda item:item.update(body=item['body']+' Regla nueva')))
        for name,raw in originals.items():
            if name.startswith('docs/lks-sdd/'):(self.root/name).write_bytes(raw)
        check(lambda:subprocess.run(['git','-C',str(self.root),'checkout','-b','codex/other'],capture_output=True,check=True))

    def test_partial_selection_retains_blocked_task_and_independent_authorized_task(self):
        from v3_authoring import author
        from test_v3_workflow import commit_packet
        task=element('task','Otra porción','Pendiente de plan y autorización',request=self.req,owner=self.actor,scope=['other.py'],acceptance=['Otro'],tests=['other'])
        commit_packet(self.root,author(self.root,self.actor,[task]))
        code,value,_=self.call(self.data(task=task['meta']['uid'],parameters={'tasks':[self.task]}))
        self.assertEqual(3,code,value);self.assertEqual('partial',value['status'])
        self.assertEqual([self.task],value['portion']['ready']);self.assertEqual([task['meta']['uid']],value['portion']['blocked'])
        self.assertEqual({self.task,task['meta']['uid']},set(value['contract']['roots']))

    def test_empty_contract_never_reports_ready(self):
        with patch('v3_context.context',return_value={'sources':[],'attachments':[]}):
            code,value,_=self.call()
        self.assertEqual(2,code);self.assertIn('Empty literal',value['cause'])

    def test_apply_is_rejected_and_output_is_explicit_outside_consumer(self):
        before=fixture.snapshot(self.root);self.assertEqual(2,self.call(flags=['--apply'])[0])
        destination=self.out/'result.json';code,value,_=self.call(flags=['--view','operational','--output',destination])
        self.assertEqual(0,code);self.assertEqual(RESULT,json.loads(destination.read_bytes())['format'])
        self.assertEqual(before,fixture.snapshot(self.root));self.assertEqual(2,self.call(flags=['--output',self.root/'hidden.json'])[0])

    def test_public_pinned_cli_and_two_distribution_adapters(self):
        from build_dual_distribution import collect_development
        from dual_distribution import artifacts
        core=collect_development(ROOT);packages=artifacts(core,'work-prepare-test','development-unreleased')
        lock=json.loads((self.root/'.lks-sdd/distribution-lock.json').read_bytes())
        command=self.root/lock['runtime']/'scripts/lks_sdd.py'
        source=self.out/'request.json';source.write_bytes(canonical(self.data()))
        for host,prefix in [('codex','lks-sdd-plugin-v'),('copilot','lks-sdd-copilot-v')]:
            with self.subTest(host=host):
                raw=next(raw for name,raw in packages.items() if name.startswith(prefix))
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    name=next(n for n in archive.namelist() if n.endswith('/scripts/v4_work_prepare.py'))
                    base=name.removesuffix('scripts/v4_work_prepare.py')
                    for relative in ('scripts/v4_work_prepare.py','scripts/v3_cli.py','docs/WORK-PREPARE.md'):
                        self.assertEqual(core[relative],archive.read(base+relative))
                        self.assertEqual(archive.read(base+relative),(self.root/lock['runtime']/relative).read_bytes())
                    # Execute bytes extracted from each adapter, with the exact pinned inventory.
                    import hashlib
                    for relative,digest in lock['runtime_files'].items():
                        packaged=archive.read(base+relative)
                        self.assertEqual(digest,hashlib.sha256(packaged).hexdigest())
                        filesystem_root(self.root/lock['runtime']/relative).write_bytes(packaged)
                result=subprocess.run([sys.executable,'-B','-X','utf8',str(command),'v3','work-prepare',str(self.root),'--input',str(source),'--view','operational'],capture_output=True,text=True,encoding='utf-8',timeout=120)
                self.assertEqual(0,result.returncode,result.stdout+result.stderr);self.assertEqual('ready',json.loads(result.stdout)['status'])
        wrong=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'scripts/lks_sdd.py'),'v3','work-prepare',str(self.root),'--input',str(source)],capture_output=True,text=True,encoding='utf-8',timeout=60)
        self.assertEqual(2,wrong.returncode)


    def test_optional_index_large_index_missing_root_and_git_timeout(self):
        index=self.root/'.lks-sdd/project.json';raw=index.read_bytes();index.unlink()
        self.assertEqual('ready',prepare(self.root,self.data())['status'])
        self.assertFalse(index.exists())
        index.write_bytes(raw+b' '*1100000)
        self.assertEqual('ready',prepare(self.root,self.data())['status'])
        self.assertEqual(raw+b' '*1100000,index.read_bytes())
        index.write_bytes(raw)
        from v3_context import context
        def incomplete(*args,**kwargs):
            value=context(*args,**kwargs)
            value['sources']=[s for s in value['sources'] if s['key']!=self.task]
            return value
        with patch('v3_context.context',side_effect=incomplete):value=prepare(self.root,self.data())
        self.assertEqual('blocked',value['status']);self.assertIn('omits',value['cause'])
        before=fixture.snapshot(self.root)
        with patch('v3_git.subprocess.run',side_effect=subprocess.TimeoutExpired('git',60)):
            value=prepare(self.root,self.data())
        self.assertEqual('blocked',value['status']);self.assertIn('60 s',value['cause'])
        self.assertEqual(before,fixture.snapshot(self.root))


    def test_transaction_started_during_query_blocks_ready(self):
        from v3_guidance import readiness
        def concurrent(*args,**kwargs):
            value=readiness(*args,**kwargs)
            (self.root/'.lks-sdd/transaction.json').write_bytes(b'{}')
            return value
        with patch('v3_guidance.readiness',side_effect=concurrent):value=prepare(self.root,self.data())
        self.assertEqual('blocked',value['status']);self.assertEqual([],value['portion']['ready'])
        self.assertIn('transaction',value['cause'].lower())
        self.assertEqual(b'{}',(self.root/'.lks-sdd/transaction.json').read_bytes())

    def test_runtime_declaration_changed_at_initial_and_final_boundary(self):
        from v3_current import require_current
        from runtime_doctor import check
        lock=self.root/'.lks-sdd/distribution-lock.json';raw=lock.read_bytes()
        def change():
            value=json.loads(raw);value['review_marker']='concurrent'
            lock.write_bytes(canonical(value))
        def initial(*args,**kwargs):
            value=require_current(*args,**kwargs);change();return value
        with patch('v3_current.require_current',side_effect=initial):value=prepare(self.root,self.data())
        self.assertEqual('blocked',value['status']);self.assertEqual([],value['portion']['ready'])
        lock.write_bytes(raw);calls=0
        def final(*args,**kwargs):
            nonlocal calls
            calls+=1;value=check(*args,**kwargs)
            if calls==2:change()
            return value
        with patch('runtime_doctor.check',side_effect=final):value=prepare(self.root,self.data())
        self.assertEqual('blocked',value['status']);self.assertIn('declaration changed',value['cause'])

    def test_runtime_declaration_changed_during_final_validation(self):
        from runtime_doctor import check
        lock=self.root/'.lks-sdd/distribution-lock.json';raw=lock.read_bytes();calls=0
        def concurrent(*args,**kwargs):
            nonlocal calls
            calls+=1;value=check(*args,**kwargs)
            if calls==2:
                changed=json.loads(raw);changed['review_marker']='final-concurrent'
                lock.write_bytes(canonical(changed))
            return value
        with patch('runtime_doctor.check',side_effect=concurrent):value=prepare(self.root,self.data())
        self.assertEqual('blocked',value['status']);self.assertEqual([],value['portion']['ready'])
        self.assertIn('declaration changed',value['cause'])

    def test_basis_includes_history_read_during_evaluation(self):
        from v3_contract import HISTORY,Element
        from v3_guidance import status
        old=copy.deepcopy(load(self.root).get(self.task).item())
        old['body']+='\nVersión histórica recuperada para auditar la base.'
        previous=Element(old['meta'],old['body'],'unused').digest()
        path=self.root/HISTORY/old['meta']['uid']/(previous+'.md');path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(render(old,version='3.1'))
        def history(*args,**kwargs):
            value=status(*args,**kwargs);load(self.root).at(old['meta']['uid'],previous);return value
        with patch('v3_guidance.status',side_effect=history):value=prepare(self.root,self.data())
        self.assertEqual('ready',value['status'],value.get('cause'))
        self.assertEqual(value['contract']['snapshot'],value['basis']['source_snapshot'])

    @unittest.skipUnless(os.name=='nt','Windows long path')
    def test_public_prepare_under_long_windows_consumer_path(self):
        target=self.out/('segment-'+ 'a'*70)/('segment-'+ 'b'*70)/('segment-'+ 'c'*70)/'consumer'
        self.assertTrue(target.resolve().is_relative_to(self.out.resolve()))
        extended=filesystem_root(target,force_extended=True)
        cleanup=filesystem_root(self.out/('segment-'+ 'a'*70),force_extended=True)
        self.addCleanup(lambda:shutil.rmtree(cleanup))
        extended.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(self.root,extended)
        self.root=extended
        self.assertGreater(len(str(target)),260)
        source=self.out/'long-request.json';source.write_bytes(canonical(self.data()))
        lock=json.loads((self.root/'.lks-sdd/distribution-lock.json').read_bytes())
        before=fixture.snapshot(self.root)
        result=subprocess.run([sys.executable,'-B','-X','utf8',str(self.root/lock['runtime']/'scripts/lks_sdd.py'),'v3','work-prepare',str(self.root),'--input',str(source),'--view','operational'],capture_output=True,text=True,encoding='utf-8',timeout=120)
        self.assertEqual(before,fixture.snapshot(self.root))
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)
        self.assertEqual('ready',json.loads(result.stdout)['status'])

if __name__=='__main__':unittest.main()
