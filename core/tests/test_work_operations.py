"""Real transaction composition, retry correlation and material failure boundaries."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
from v3_contract import canonical, load, sha, fingerprint, element, render, ContractError
from v3_git import observe, code_inventory, subject
from v3_workflow import state, transition
from v3_storage import apply as apply_packet, recover
from v3_cli import main
from v4_work_operations import run, REQUEST
import test_work_prepare as prepare_fixture
from test_v3_workflow import commit_packet
from presentation_test_support import present
from test_v4_cli_presentation import snapshot


class WorkOperationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prepare_fixture.WorkPrepareTests.setUpClass.__func__(cls)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='work-operations-'); self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name); self.root = self.out / 'consumer'
        shutil.copytree(self.case.root, self.root)

    def basis(self):
        model = load(self.root).require_valid(); task = model.get(self.task)
        git = observe(self.root)
        return {'source_snapshot': model.snapshot(), 'subject': subject(self.root, task.data['scope']),
                'git': {k: git[k] for k in ('branch', 'head')}, 'code_inventory_digest': fingerprint(code_inventory(self.root)),
                'state': state(model, task)}

    def data(self, operation='work-continue', **params):
        parameters = {'reason': 'Resultado técnico sintético acreditado', **({'action': 'start'} if operation == 'work-continue' else {'target': 'closed'}), **params}
        return {'format': REQUEST, 'version': 1, 'operation_id': 'auto', 'task': self.task, 'actor': self.actor,
                'basis': self.basis(), 'parameters': parameters}

    def cli(self, operation, data, *flags):
        source = self.out / 'input.json'; source.write_bytes(canonical(data)); output = io.StringIO()
        with contextlib.redirect_stdout(output): code = main([operation, str(self.root), '--input', str(source), *map(str, flags)])
        return code, json.loads(output.getvalue())

    def start(self):
        value = run(self.root, 'work-continue', self.data(), apply=True)
        self.assertEqual('completed', value['status'], value)

    def proof(self):
        (self.root / 'app.py').write_text("def greeting(): return 'Hola'\n", encoding='utf-8')
        code = "import runpy,inspect; f=runpy.run_path('app.py')['greeting']; assert f()=='Hola'; assert not inspect.signature(f).parameters; print('greeting: passed')"
        completed = subprocess.run([sys.executable, '-B', '-c', code], cwd=self.root, capture_output=True)
        self.assertEqual(0, completed.returncode, completed.stderr)
        artifact = 'docs/lks-sdd/evidence/observed.txt'; path = self.root / artifact
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(completed.stdout)
        return {'tests': ['greeting'], 'outcome': 'passed', 'source': 'automated', 'artifact': artifact,
                'artifact_sha256': sha(path.read_bytes()), 'subject': self.basis()['subject'],
                'explanation': 'Prueba Python realmente ejecutada del valor y de la firma, sobre este sujeto.'}

    def records(self, **params):
        self.start(); proof = self.proof()
        return self.data('work-record-results', evidence=[proof], **params)

    def test_preview_is_read_only_and_retains_literal_contract(self):
        before = snapshot(self.root); data = self.data(); value = run(self.root, 'work-continue', data)
        self.assertEqual('ready', value['status'], value); self.assertEqual([], value['effects'])
        self.assertTrue(value['contract']['sources']); self.assertIn('packet', value)
        self.assertEqual(before, snapshot(self.root))

    def test_start_exact_retry_uses_journal_without_duplicate_execution(self):
        data = self.data(); first = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('completed', first['status'], first)
        after = snapshot(self.root); again = run(self.root, 'work-continue', {**data, 'operation_id': first['operation_id']}, apply=True)
        self.assertEqual('completed', again['status'], again); self.assertEqual(first['effects'], again['effects'])
        self.assertEqual([], again['writes']); self.assertEqual(after, snapshot(self.root))
        self.assertEqual(1, len(load(self.root).by_kind('execution')))

    def test_resume_uses_existing_pause_without_new_human_decision(self):
        self.start(); commit_packet(self.root, present(transition, self.root, self.actor, self.task, 'pause', 'Pausa explícita sintética'))
        value = run(self.root, 'work-continue', self.data(action='resume'), apply=True)
        self.assertEqual('completed', value['status'], value)
        self.assertEqual('in-progress', state(load(self.root), load(self.root).get(self.task)))

    def test_complete_results_record_separate_facts_and_keep_acceptance_separate(self):
        data = self.records(); value = run(self.root, 'work-record-results', data, apply=True)
        self.assertEqual('completed', value['status'], value)
        self.assertEqual(['implement', 'evidence:0', 'verify', 'close'], [e['stage'] for e in value['effects']])
        model = load(self.root).require_valid(); self.assertEqual('closed', state(model, model.get(self.task)))
        self.assertCountEqual(['start', 'implement', 'verify', 'close'], [e.data['action'] for e in model.by_kind('execution')])
        self.assertEqual(1, len(model.by_kind('evidence')))
        self.assertFalse([e for e in model.by_kind('receipt') if e.data.get('purpose') == 'integration'])
        self.assertFalse([e for e in model.by_kind('decision') if e.data.get('purpose') == 'acceptance'])
        after = snapshot(self.root); again = run(self.root, 'work-record-results', data, apply=True)
        self.assertEqual('completed', again['status'], again); self.assertEqual(after, snapshot(self.root))

    def test_failed_and_not_run_evidence_are_recorded_but_do_not_verify_or_close(self):
        for outcome in ('failed', 'not-run'):
            with self.subTest(outcome=outcome):
                with tempfile.TemporaryDirectory() as temp:
                    original = self.root; self.root = Path(temp) / 'c'; shutil.copytree(self.case.root, self.root)
                    try:
                        data = self.records(); data['parameters']['evidence'][0]['outcome'] = outcome
                        value = run(self.root, 'work-record-results', data, apply=True)
                        self.assertEqual('partial', value['status'], value)
                        self.assertEqual(['implement', 'evidence:0'], [e['stage'] for e in value['effects']])
                        self.assertEqual('implemented', state(load(self.root), load(self.root).get(self.task)))
                    finally: self.root = original

    def test_old_subject_and_changed_report_cannot_certify_new_result(self):
        data = self.records(); before = snapshot(self.root)
        data['parameters']['evidence'][0]['subject']['digest'] = '0' * 64
        with self.assertRaises(ContractError): run(self.root, 'work-record-results', data, apply=True)
        self.assertEqual(before, snapshot(self.root))
        data = self.data('work-record-results', evidence=[self.proof()])
        (self.root / data['parameters']['evidence'][0]['artifact']).write_text('otro reporte')
        value = run(self.root, 'work-record-results', data, apply=True)
        self.assertEqual('partial', value['status'], value); self.assertEqual(1, len(value['effects']))
        self.assertIn('artifact', value['cause'])

    def test_unknown_keys_types_and_forbidden_actions_have_no_effect(self):
        data = self.data(); before = snapshot(self.root)
        variants = [{**data, 'version': True}, {**data, 'actor': None}, {**data, 'unexpected': True},
                    {**data, 'parameters': {**data['parameters'], 'review': True}},
                    {**data, 'parameters': {'action': 'reopen', 'reason': 'not allowed'}}]
        for bad in variants:
            with self.subTest(bad=bad): self.assertEqual(2, self.cli('work-continue', bad, '--apply')[0])
        self.assertEqual(before, snapshot(self.root))
        self.assertEqual(2, self.cli('work-record-results', self.data('work-record-results', target='accept'), '--apply')[0])

    def test_changed_intent_cannot_reuse_operation_id(self):
        data = self.data(); prepared = run(self.root, 'work-continue', data)
        data['operation_id'] = prepared['operation_id']; data['parameters']['reason'] += ' distinto'
        self.assertEqual(2, self.cli('work-continue', data, '--apply')[0])

    def test_goals_do_not_reopen_closed_work_or_record_beyond_requested_limit(self):
        data = self.records(); beyond = copy.deepcopy(data); beyond['parameters']['target'] = 'implemented'
        self.assertEqual(2, self.cli('work-record-results', beyond, '--apply')[0])
        missing = self.data('work-record-results', target='evidence')
        self.assertEqual(2, self.cli('work-record-results', missing, '--apply')[0])
        value = run(self.root, 'work-record-results', data, apply=True)
        self.assertEqual('completed', value['status'], value)
        self.assertEqual(2, self.cli('work-record-results', self.data('work-record-results'), '--apply')[0])

    def test_stale_documents_authority_and_code_block_before_first_effect(self):
        from v3_authoring import author
        data = self.data(); note = element('constraint', 'Nueva condición', 'Conservar esta condición nueva.')
        commit_packet(self.root, author(self.root, self.actor, [note]))
        value = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('blocked', value['status'], value); self.assertEqual([], value['effects'])
        data = self.data(); (self.root / 'app.py').write_text('changed = True\n')
        self.assertEqual('blocked', run(self.root, 'work-continue', data, apply=True)['status'])

    def test_changed_git_or_pinned_runtime_prevents_writes(self):
        from test_v3_workflow import git
        data = self.data(); branch = observe(self.root)['branch']
        git(self.root, 'checkout', '-b', 'codex/another-synthetic-branch')
        before = snapshot(self.root)
        value = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('blocked', value['status'], value); self.assertEqual([], value['effects'])
        self.assertEqual(before, snapshot(self.root))
        # These fixtures can use an unborn branch: select its symbolic HEAD
        # without pretending a branch commit already exists.
        git(self.root, 'symbolic-ref', 'HEAD', 'refs/heads/' + branch)
        lock = json.loads((self.root / '.lks-sdd/distribution-lock.json').read_bytes())
        path = self.root / lock['runtime'] / 'scripts/v4_work_operations.py'; original = path.read_bytes()
        try:
            path.write_bytes(original + b'\n# synthetic altered runtime\n'); before = snapshot(self.root)
            value = run(self.root, 'work-continue', self.data(), apply=True)
            self.assertEqual('blocked', value['status'], value); self.assertEqual([], value['effects'])
            self.assertEqual(before, snapshot(self.root))
        finally:
            path.write_bytes(original)

    def test_change_during_stage_preparation_stops_before_first_effect(self):
        import v4_work_operations as operations
        from v3_usage import observe as observe_usage, record
        for mutation in ('code', 'diagnostic-document'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                original = self.root; self.root = Path(temp) / 'c'; shutil.copytree(self.case.root, self.root)
                try:
                    data = self.data(); prepare = operations._prepare
                    def concurrent(root, chosen, step):
                        if mutation == 'code':
                            (root / 'later.py').write_text('later = True\n', encoding='utf-8')
                        else:
                            row = observe_usage('status', {}, {'status': 'synthetic-observation'}, root=root)
                            commit_packet(root, record(root, {'actor': self.actor, 'observations': [row]}))
                        return prepare(root, chosen, step)
                    with patch('v4_work_operations._prepare', side_effect=concurrent):
                        value = run(self.root, 'work-continue', data, apply=True)
                    self.assertEqual([], value['effects'], value)
                    self.assertEqual('blocked', value['status'], value)
                    model = load(self.root).require_valid()
                    self.assertFalse(model.by_kind('execution'))
                    if mutation == 'code': self.assertTrue((self.root / 'later.py').exists())
                    else: self.assertTrue([e for e in model.by_kind('receipt') if e.data.get('purpose') == 'usage-observation'])
                finally:
                    self.root = original

    def test_git_change_inside_preparation_is_rechecked_outside_cache(self):
        import v3_git
        data = self.data(); original = v3_git.git; changed = False
        def concurrent(root, *args, **kwargs):
            nonlocal changed
            value = original(root, *args, **kwargs)
            if not changed and v3_git._OBSERVATION.get() is not None and args == ('symbolic-ref', '--short', 'HEAD'):
                subprocess.run(['git', '-C', str(root), 'symbolic-ref', 'HEAD', 'refs/heads/concurrent'], check=True, capture_output=True)
                changed = True
            return value
        with patch('v3_git.git', side_effect=concurrent):
            value = run(self.root, 'work-continue', data, apply=True)
        self.assertTrue(changed)
        self.assertEqual('blocked', value['status'], value)
        self.assertEqual([], value['effects'], value)
        self.assertIsNone(v3_git._OBSERVATION.get())
        self.assertFalse(load(self.root).by_kind('execution'))

    def test_scope_widening_is_rejected_by_the_original_core(self):
        self.start(); self.proof(); (self.root / 'outside.py').write_text('not covered = True\n')
        value = run(self.root, 'work-record-results', self.data('work-record-results'), apply=True)
        self.assertEqual('blocked', value['status'], value); self.assertIn('alcance', value['cause'])

    def test_missing_review_or_recipient_is_not_accepted_by_composition(self):
        from v3_contract import render
        model = load(self.root)
        review = next(e for e in model.by_kind('decision') if e.data.get('purpose') == 'task-review')
        (self.root / review.path).unlink()
        value = run(self.root, 'work-continue', self.data(), apply=True)
        self.assertEqual('blocked', value['status'], value); self.assertIn('task-reviewed', value['cause'])

    def test_revoked_permission_is_not_reused_from_preview(self):
        from v3_lifecycle import revoke
        data = self.data(); run(self.root, 'work-continue', data)
        authorization = next(e for e in load(self.root).by_kind('authorization') if e.data.get('purpose') == 'execution')
        commit_packet(self.root, present(revoke, self.root, self.actor, authorization.uid, 'Revocación de prueba'))
        value = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('blocked', value['status'], value); self.assertEqual([], value['effects'])
        self.assertEqual('blocked', run(self.root, 'work-continue', self.data(), apply=True)['status'])

    def test_fault_after_every_committed_stage_recovers_receipts_without_duplicate(self):
        for boundary in range(1, 5):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as temp:
                original = self.root; self.root = Path(temp) / 'c'; shutil.copytree(self.case.root, self.root)
                try:
                    data = self.records(); calls = 0
                    def fault(*args, **kwargs):
                        nonlocal calls
                        result = apply_packet(*args, **kwargs); calls += 1
                        if calls == boundary: raise OSError('injected after committed stage')
                        return result
                    with patch('v3_storage.apply', side_effect=fault): value = run(self.root, 'work-record-results', data, apply=True)
                    self.assertEqual('partial', value['status'], value); self.assertEqual(boundary, len(value['effects']))
                    again = run(self.root, 'work-record-results', data, apply=True)
                    self.assertEqual('completed', again['status'], again)
                    self.assertEqual(4, len(load(self.root).by_kind('execution')))
                    self.assertEqual(1, len(load(self.root).by_kind('evidence')))
                finally: self.root = original

    def test_interrupted_material_write_requires_explicit_native_recovery(self):
        data = self.data()
        def fault(root, packet, key, **kwargs):return apply_packet(root, packet, key, interrupt_after=1, **kwargs)
        with patch('v3_storage.apply', side_effect=fault): value = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('partial', value['status'], value); self.assertIn('recovery', value)
        self.assertEqual('partial', run(self.root, 'work-continue', data, apply=True)['status'])
        recover(self.root, value['recovery']['preview_hash'])
        again = run(self.root, 'work-continue', data, apply=True)
        self.assertEqual('completed', again['status'], again)
        self.assertEqual(1, len(load(self.root).by_kind('execution')))

    def test_later_documents_are_preserved_between_stages_and_on_retry(self):
        from v3_authoring import author
        data = self.records(); count = 0
        def concurrent(*args, **kwargs):
            nonlocal count
            result = apply_packet(*args, **kwargs); count += 1
            if count == 1:
                note = element('constraint', 'Trabajo posterior', 'No sobrescribir este trabajo posterior.')
                commit_packet(self.root, author(self.root, self.actor, [note]))
            return result
        with patch('v3_storage.apply', side_effect=concurrent): value = run(self.root, 'work-record-results', data, apply=True)
        self.assertEqual('partial', value['status'], value); self.assertEqual(1, len(value['effects']))
        before = snapshot(self.root); again = run(self.root, 'work-record-results', data, apply=True)
        self.assertEqual('partial', again['status'], again); self.assertEqual(before, snapshot(self.root))

    def test_cli_preview_export_and_completed_status(self):
        data = self.data(); code, value = self.cli('work-continue', data, '--view', 'operational', '--json')
        self.assertEqual(0, code, value); self.assertNotIn('packet', value)
        output = self.out / 'preview.json'
        code, value = self.cli('work-continue', data, '--output', output)
        self.assertEqual(0, code, value); exported = json.loads(output.read_bytes()); self.assertIn('packet', exported)
        code, value = self.cli('work-continue', data, '--apply', '--view', 'operational')
        self.assertEqual(0, code, value); self.assertEqual('completed', value['status'])

    def test_output_failure_preserves_committed_receipts_and_retry(self):
        data = self.data(); output = self.out / 'undelivered.json'
        with patch('v3_cli_presentation.write_export', side_effect=OSError('injected output failure')):
            code, failed = self.cli('work-continue', data, '--apply', '--output', output, '--view', 'operational')
        self.assertEqual(3, code, failed); self.assertEqual('partial', failed['status'])
        self.assertEqual('completed', failed['operation_status']); self.assertEqual(1, len(failed['effects']))
        code, again = self.cli('work-continue', data, '--apply')
        self.assertEqual(0, code, again); self.assertEqual(failed['effects'], again['effects'])
        self.assertEqual([], again['writes']); self.assertEqual(1, len(load(self.root).by_kind('execution')))

    def test_cli_diagnostics_distinguish_preparation_from_partial_applied_effects(self):
        data = self.data(); code, preview = self.cli('work-continue', data, '--json')
        self.assertEqual(0, code, preview)
        self.assertEqual('prepared', preview['usage']['observations'][0]['stage'])
        code, applied = self.cli('work-continue', data, '--apply', '--json')
        self.assertEqual(0, code, applied)
        self.assertEqual('applied', applied['usage']['observations'][0]['stage'])
        proof = self.proof(); proof['outcome'] = 'failed'
        code, partial = self.cli('work-record-results', self.data('work-record-results', evidence=[proof]), '--apply', '--json')
        self.assertEqual(3, code, partial); self.assertEqual(2, len(partial['effects']))
        observation = partial['usage']['observations'][0]
        self.assertEqual('applied', observation['stage'])
        self.assertEqual('partial', observation['application']['status'])

    def test_output_failure_preserves_partial_effects_and_remaining_work(self):
        data = self.records(); output = self.out / 'partial-undelivered.json'
        def fault(*args, **kwargs):
            result = apply_packet(*args, **kwargs)
            raise OSError('injected after committed first result stage')
        with patch('v3_storage.apply', side_effect=fault), patch('v3_cli_presentation.write_export', side_effect=OSError('injected output failure')):
            code, failed = self.cli('work-record-results', data, '--apply', '--output', output)
        self.assertEqual(3, code, failed); self.assertEqual('partial', failed['operation_status'])
        self.assertEqual(['implement'], [r['stage'] for r in failed['effects']])
        code, again = self.cli('work-record-results', data, '--apply')
        self.assertEqual(0, code, again); self.assertEqual(4, len(again['effects']))
        self.assertEqual(4, len(load(self.root).by_kind('execution')))


if __name__ == '__main__': unittest.main()
