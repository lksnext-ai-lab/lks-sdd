"""Additional real policy and provenance guards for the composed writers."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
import test_work_operations as support
from test_v3_workflow import commit_packet
from test_v4_cli_presentation import snapshot
from presentation_test_support import present
from v3_authoring import governance, approve_and_authorize
from v3_contract import element, load
from v3_workflow import transition, state
from v3_verification import evidence
from v4_work_operations import run, _tag, request


class WorkOperationGuardTests(unittest.TestCase):
    setUpClass = classmethod(support.WorkOperationsTests.setUpClass.__func__)
    setUp = support.WorkOperationsTests.setUp
    basis = support.WorkOperationsTests.basis
    data = support.WorkOperationsTests.data
    start = support.WorkOperationsTests.start
    proof = support.WorkOperationsTests.proof
    records = support.WorkOperationsTests.records
    cli = support.WorkOperationsTests.cli

    def policy(self, **changes):
        model = load(self.root); item = copy.deepcopy(model.get(model.project.data['policy']).item())
        item['meta']['revision'] += 1; item['meta']['data'].update(changes)
        return item

    def renew_policy_authority(self):
        # Adopting a new policy invalidates the earlier approval descriptor.
        # Explicit fixture decisions renew it; the operation must not do so.
        from v31_review import execute
        commit_packet(self.root, present(execute, 'close-proposal', self.root, {
            'actor': self.actor, 'request': self.req, 'statement': 'Reviso la propuesta bajo las reglas nuevas', 'review': True}))
        model = load(self.root); plan = next(p for p in model.by_kind('plan') if self.task in p.relations.get('tasks', []))
        commit_packet(self.root, present(approve_and_authorize, self.root, self.actor, plan.uid,
            'Apruebo y autorizo el plan bajo las reglas nuevas', review_tasks=[self.task]))

    def test_independent_review_stays_with_another_person(self):
        self.start(); proof = self.proof()
        commit_packet(self.root, transition(self.root, self.actor, self.task, 'implement', 'Implementado'))
        reviewer = element('member', 'Revisora sintética', 'Identidad independiente de prueba.', roles=['reviewer'], active=True)
        other = reviewer['meta']['uid']
        commit_packet(self.root, present(governance, self.root, self.actor,
            [self.policy(independent_review=True), reviewer], 'Exijo revisión independiente', 'Control de prueba', requests=[self.req]))
        self.renew_policy_authority()
        commit_packet(self.root, evidence(self.root, other, self.task, proof['tests'], 'passed', 'human-observation', proof['artifact'], 'Compruebo este resultado de forma independiente'))
        value = run(self.root, 'work-record-results', self.data('work-record-results'), apply=True)
        self.assertEqual('blocked', value['status'], value); self.assertIn('independiente', value['cause'])
        data = self.data('work-record-results'); data['actor'] = other
        value = run(self.root, 'work-record-results', data, apply=True)
        self.assertEqual('completed', value['status'], value)

    def test_pending_offer_is_not_received_on_behalf_of_recipient(self):
        from v3_team import assign
        member = element('member', 'Destinatario sintético', 'Necesita aceptar su encargo.', roles=['developer', 'reviewer'], active=True)
        other = member['meta']['uid']
        commit_packet(self.root, present(governance, self.root, self.actor, [self.policy(assignment_acceptance=True), member],
            'Recepción expresa', 'Control de prueba', requests=[self.req]))
        commit_packet(self.root, present(assign, self.root, self.actor, self.task, other, 'Oferta explícita'))
        before = snapshot(self.root); data = self.data(); data['actor'] = other
        value = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('blocked', value['status'], value); self.assertEqual(before, snapshot(self.root))
        self.assertFalse([e for e in load(self.root).by_kind('assignment') if e.data['status'] == 'accepted'])

    def test_required_quality_without_applicable_terminal_result_stops_verify(self):
        self.start(); proof = self.proof()
        control = {'mode': 'required', 'reason': 'Control obligatorio sintético', 'executor': 'existing-report',
                   'scope': ['app.py'], 'timeout_seconds': 30, 'max_retries': 0,
                   'availability': {'state': 'available', 'source': 'synthetic existing report', 'phase': 'implementation'}}
        controls = copy.deepcopy(load(self.root).get(load(self.root).project.data['policy']).data['controls']); controls['sonar'] = control
        commit_packet(self.root, present(governance, self.root, self.actor, [self.policy(controls=controls)],
            'Sonar obligatorio', 'Control de prueba', requests=[self.req]))
        self.renew_policy_authority()
        value = run(self.root, 'work-record-results', self.data('work-record-results', evidence=[proof]), apply=True)
        self.assertEqual('partial', value['status'], value)
        self.assertEqual(['implement', 'evidence:0'], [e['stage'] for e in value['effects']])
        self.assertIn('quality', value['cause'])

    def test_same_tag_with_another_transition_reason_is_not_a_receipt_for_this_intent(self):
        data = self.data(); chosen = request(self.root, 'work-continue', data)
        different = transition(self.root, self.actor, self.task, 'start', 'Otra intención real')
        packet = _tag(different, 'start', chosen['operation_id'], 0, load(self.root).hashes)
        commit_packet(self.root, packet)
        before = snapshot(self.root); value = run(self.root, 'work-continue', data, apply=True)
        self.assertNotEqual('completed', value['status'], value)
        self.assertIn('different', str(value).lower().replace('another', 'different'))
        self.assertEqual(before, snapshot(self.root))

    def test_real_pinned_runtime_public_launcher_supports_preview_and_apply(self):
        import subprocess
        data = self.data(); source = self.out / 'public-input.json'; source.write_text(json.dumps(data), encoding='utf-8')
        lock = json.loads((self.root / '.lks-sdd/distribution-lock.json').read_bytes())
        launcher = self.root / lock['runtime'] / 'scripts/lks_sdd.py'
        output = self.out / 'public-result.json'
        command = [sys.executable, '-B', '-X', 'utf8', str(launcher), 'v3', 'work-continue', str(self.root),
                   '--input', str(source), '--output', str(output), '--apply', '--view', 'operational']
        completed = subprocess.run(command, capture_output=True, timeout=120)
        self.assertEqual(0, completed.returncode, completed.stdout.decode(errors='replace')[:2000] + completed.stderr.decode(errors='replace'))
        self.assertEqual('completed', json.loads(output.read_bytes())['status'])
        self.assertEqual('in-progress', state(load(self.root), load(self.root).get(self.task)))


if __name__ == '__main__': unittest.main()
