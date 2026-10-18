"""Reconstruct continuity from the current consumer, without chat state."""
import json,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
from v3_contract import ContractError,canonical,load
from v4_work_prepare import prepare
from v3_workflow import transition
from presentation_test_support import present
from test_v3_workflow import commit_packet
from test_v4_cli_presentation import snapshot
import test_work_prepare as fixture


class WorkContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): fixture.WorkPrepareTests.setUpClass.__func__(cls)
    setUp=fixture.WorkPrepareTests.setUp
    data=fixture.WorkPrepareTests.data

    def test_current_view_is_read_only_and_points_to_literal_sources(self):
        before=snapshot(self.root);value=prepare(self.root,self.data());view=value['continuity']
        self.assertEqual('current',view['status'],value)
        self.assertFalse(view['authority_granted']);self.assertFalse(view['identity_inherited'])
        self.assertEqual(value['basis']['source_snapshot'],view['basis']['source_snapshot'])
        self.assertEqual(self.task,view['tasks'][0]['uid'])
        self.assertEqual(self.task,view['tasks'][0]['source']['uid'])
        self.assertTrue(value['contract']['sources']);self.assertFalse(view['required_reading']['summaries_replace_contract'])
        self.assertEqual(before,snapshot(self.root))

    def test_owner_is_never_silently_used_as_the_current_actor(self):
        value=prepare(self.root,self.data(actor=None));view=value['continuity']
        self.assertIsNone(view['actor']);self.assertTrue(view['tasks'][0]['owner'])
        self.assertFalse(view['authority_granted']);self.assertEqual([],value['portion']['ready'])
        self.assertTrue(any(r['rule']=='actor-identified' for r in view['stops']))

    def test_a_new_preparation_reconstructs_the_changed_code_basis(self):
        first=prepare(self.root,self.data())['continuity']
        (self.root/'app.py').write_text("def greeting(): return 'Hola'\n",encoding='utf-8')
        second=prepare(self.root,self.data())['continuity']
        self.assertNotEqual(first['basis']['code_inventory_digest'],second['basis']['code_inventory_digest'])
        self.assertEqual(first['tasks'][0]['state'],second['tasks'][0]['state'])

    def test_failed_physical_freshness_cannot_publish_a_current_view(self):
        with patch('v4_work_prepare._fresh',side_effect=ContractError('source changed')):
            value=prepare(self.root,self.data())
        self.assertEqual('blocked',value['status'])
        self.assertEqual('unavailable',value['continuity']['status'])
        self.assertIsNone(value['continuity']['basis']);self.assertEqual([],value['continuity']['tasks'])
        self.assertTrue(value['continuity']['stops'])

    def test_unknown_actor_does_not_reconstruct_authority(self):
        value=prepare(self.root,self.data(actor='missing-current-person'))
        self.assertNotEqual('ready',value['status']);self.assertFalse(value['continuity']['authority_granted'])
        self.assertEqual('missing-current-person',value['continuity']['actor'])

    def test_cold_public_process_reconstructs_without_a_prior_chat(self):
        source=self.out/'request.json';source.write_bytes(canonical(self.data()))
        lock=json.loads((self.root/'.lks-sdd/distribution-lock.json').read_bytes())
        result=subprocess.run([sys.executable,'-B','-X','utf8',str(self.root/lock['runtime']/'scripts/lks_sdd.py'),
            'v3','work-prepare',str(self.root),'--json','--view','operational','--input',str(source)],capture_output=True,timeout=120)
        self.assertEqual(0,result.returncode,result.stderr)
        view=json.loads(result.stdout)['continuity']
        self.assertEqual(self.actor,view['actor']);self.assertFalse(view['identity_inherited'])
        self.assertEqual(self.task,view['tasks'][0]['uid'])

    def test_paused_state_and_resume_are_recovered_from_durable_facts(self):
        for action in ('start','pause'):
            packet=present(transition,self.root,self.actor,self.task,action,'Explicit synthetic '+action)
            commit_packet(self.root,packet)
        before=snapshot(self.root)
        value=prepare(self.root,self.data(parameters={'action':'resume'}));view=value['continuity']
        self.assertEqual('paused',view['tasks'][0]['state'])
        self.assertEqual('resume',view['next']['action'])
        self.assertEqual(before,snapshot(self.root))
