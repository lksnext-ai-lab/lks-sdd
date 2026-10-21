"""Product regressions from the critical review and the final v5 decisions."""
import json
import sys
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import v5_core as c
import v5_migration as migration
from v5_legacy import Reader
from v5_results import import_result
from test_v5_core import fixture, put, meta, FACTS, update


class ImprovementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lks-v5-improvements-')
        self.root = Path(self.temp.name)
        fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def edit(self, name, fn):
        data, body, _ = c.current(self.root, name)
        fn(data)
        put(self.root, name, c.document(data, body))

    def test_authority_reference_update_reuses_technical_result(self):
        c.check_task(self.root, 'T-001', 'C1')
        c.authorize(self.root, 'T-001', 'fixture-owner', 'same scope, new source', ['implement', 'consolidate', 'deliver'])
        self.assertEqual(c.check_task(self.root, 'T-001', 'C1')['status'], 'reused')

    def test_subdivision_preserves_parent_authority_and_result(self):
        c.check_task(self.root, 'T-001', 'C1')
        c.prepare(self.root, 'child', 'Part', 'Within original scope', ['C1'], ['acceso'], 'team', parent='T-001')
        self.assertEqual(c.check_task(self.root, 'T-001', 'C1')['status'], 'reused')
        child = c.current(self.root, c.task_path('child', 'tarea'))[0]
        self.assertNotIn('authority', child)  # Subdivision does not invent delegated permission.

    def test_material_scope_change_still_requires_authority(self):
        name = c.task_path('T-001', 'tarea')
        self.edit(name, lambda task: task.update(criteria={'NEW': 'New permission'}))
        with self.assertRaisesRegex(ValueError, 'scope'):
            c.check_task(self.root, 'T-001', 'C1')

    def test_owner_change_needs_no_new_authorization_or_test(self):
        c.check_task(self.root, 'T-001', 'C1')
        self.edit(c.task_path('T-001', 'tarea'), lambda t: t.update(owner='another responsible colleague'))
        self.assertEqual(c.check_task(self.root, 'T-001', 'C1')['status'], 'reused')
        c.close(self.root, 'T-001', {}, FACTS)

    def test_repeated_failures_keep_one_log_then_success_retires_it(self):
        put(self.root, 'product.py', 'def visible(value):\n    return True\n')
        for _ in range(5):
            self.assertEqual(c.check_task(self.root, 'T-001', 'C1')['status'], 'failed')
            plan = c.current(self.root, c.task_path('T-001', 'plan'))[0]
            self.assertEqual(len(plan['temporaries']), 1)
            self.assertEqual(len(list((self.root / '.sdd-work/tmp').glob('*.log'))), 1)
        put(self.root, 'product.py', 'def visible(value):\n    return bool(value)\n')
        c.check_task(self.root, 'T-001', 'C1')
        self.assertEqual(c.current(self.root, c.task_path('T-001', 'plan'))[0]['temporaries'], {})
        self.assertEqual(list((self.root / '.sdd-work/tmp').glob('*.log')), [])

    def test_retry_preserves_failure_log_edited_by_someone_else(self):
        put(self.root, 'product.py', 'raise RuntimeError("failure")\n')
        c.check_task(self.root, 'T-001', 'C1')
        plan = c.current(self.root, c.task_path('T-001', 'plan'))[0]
        log = plan['results']['C1']['failure_log']
        put(self.root, log, 'Keep human diagnosis')
        with self.assertRaises(c.Conflict): c.check_task(self.root, 'T-001', 'C1')
        self.assertEqual(c.read(self.root, log), b'Keep human diagnosis')

    def test_close_reuses_recorded_delivery_and_leaves_unknowns_honest(self):
        c.check_task(self.root, 'T-001', 'C1')
        c.delivery(self.root, 'T-001', {'implementation': 'Recorded implementation', 'publication': 'not-run'})
        c.close(self.root, 'T-001', {}, {'verification': 'Observed test'})
        plan = c.current(self.root, c.task_path('T-001', 'plan'))[0]
        self.assertEqual(plan['delivery']['implementation'], 'Recorded implementation')
        self.assertEqual(plan['delivery']['verification'], 'Observed test')
        self.assertEqual(plan['delivery']['publication'], 'not-run')
        self.assertEqual(c.close(self.root, 'T-001', {})['status'], 'unchanged')
        c.prepare(self.root, 'doc', 'Docs', 'Clarify docs', ['Readable'], ['acceso'], 'team', paths=['docs/guide.md'])
        c.authorize(self.root, 'doc', 'team', 'documentation change', ['consolidate'])
        self.edit(c.task_path('doc', 'plan'), lambda p: p.update(no_checks_reason='Human review of wording'))
        c.close(self.root, 'doc', {})
        self.assertEqual(set(c.current(self.root, c.task_path('doc', 'plan'))[0]['delivery'].values()), {'unknown'})

    def test_new_project_can_explicitly_have_no_additional_controls(self):
        cli = Path(__file__).resolve().parents[1] / 'scripts/lks_sdd.py'
        result = subprocess.run([sys.executable, '-B', str(cli), 'init', '--root', str(self.root), '--data', '-'],
            input=json.dumps({'project': 'Known project', 'policy': {}}).encode(), capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(c.project_policy(self.root), {})

    def test_concurrent_editor_between_transaction_writes_is_preserved(self):
        c.check_task(self.root, 'T-001', 'C1')
        name = c.task_path('T-001', 'plan')
        atomic = c.atomic_write
        def other_editor(path, raw, **kwargs):
            atomic(path, raw, **kwargs)
            if path.name == 'acceso.md':
                put(self.root, name, c.read(self.root, name) + b'\nForeign decision\n')
        with patch.object(c, 'atomic_write', other_editor), self.assertRaises(c.Conflict):
            c.close(self.root, 'T-001', update(self.root), FACTS)
        self.assertIn(b'Foreign decision', c.read(self.root, name))
        with self.assertRaises(c.Conflict): c.resume(self.root)

    def test_atomic_write_checks_precondition_after_staging(self):
        path = self.root / 'value.md'
        path.write_bytes(b'foreign')
        with self.assertRaises(c.Conflict):
            c.atomic_write(path, b'after', expected=c.digest(b'before'))
        self.assertEqual(path.read_bytes(), b'foreign')

    def parent_and_child(self):
        c.prepare(self.root, 'parent', 'Parent', 'Two criteria', ['Access', 'Permissions'], ['acceso'], 'team')
        c.prepare(self.root, 'child', 'Child', 'Access only', ['Access'], ['acceso'], 'team', parent='parent')
        for task in ('parent', 'child'):
            c.authorize(self.root, task, 'team', 'test decision', ['implement', 'consolidate'])
        checks = c.current(self.root, c.task_path('T-001', 'plan'))[0]['checks']
        self.edit(c.task_path('child', 'plan'), lambda p: p.update(checks=checks))
        c.check_task(self.root, 'child', 'C1')
        c.close(self.root, 'child', {}, FACTS)

    def test_parent_cannot_close_with_uncovered_criteria(self):
        self.parent_and_child()
        with self.assertRaisesRegex(ValueError, 'criteria'):
            c.close(self.root, 'parent', {}, FACTS)

    def test_parent_links_child_evidence_without_copying_results(self):
        self.parent_and_child()
        name = c.task_path('parent', 'plan')
        self.edit(name, lambda p: p.update(criterion_links={'C1': [{'task': 'child', 'criterion': 'C1'}]},
            criterion_dispositions={'C2': 'Explicit review: this change preserves the existing permission contract.'}))
        c.close(self.root, 'parent', {}, FACTS)
        self.assertNotIn('results', c.current(self.root, name)[0])

    def test_parent_rejects_child_with_changed_test_inputs(self):
        self.parent_and_child()
        name = c.task_path('parent', 'plan')
        self.edit(name, lambda p: p.update(criterion_links={'C1': [{'task': 'child', 'criterion': 'C1'}]},
            criterion_dispositions={'C2': 'Reviewed separately'}))
        put(self.root, 'product.py', 'changed')
        with self.assertRaisesRegex(ValueError, 'passing result'):
            c.close(self.root, 'parent', {}, FACTS)

    def test_parent_reuses_required_control_only_with_complete_current_delegation(self):
        put(self.root, c.unit_path('proyecto'), c.document(meta('unit', 'proyecto',
            policy={'required_checks': ['C1']}), 'Required shared quality control'))
        self.parent_and_child()
        name = c.task_path('parent', 'plan')
        self.edit(name, lambda p: p.update(criterion_links={'C1': [{'task': 'child', 'criterion': 'C1'}]},
            criterion_dispositions={'C2': 'Human review of other work'}))
        with self.assertRaisesRegex(ValueError, 'requires checks'):
            c.close(self.root, 'parent', {}, FACTS)
        self.edit(c.task_path('parent', 'tarea'), lambda t: t.update(criteria={'C1': 'Access'}))
        c.authorize(self.root, 'parent', 'team', 'Scope fully delegated', ['consolidate'])
        self.edit(name, lambda p: p.update(criterion_dispositions={}))
        put(self.root, 'product.py', 'def visible(value):\n    return False\n')
        with self.assertRaisesRegex(ValueError, 'passing result'):
            c.close(self.root, 'parent', {}, FACTS)
        put(self.root, 'product.py', 'def visible(value):\n    return bool(value)\n')
        c.close(self.root, 'parent', {}, FACTS)
        self.assertNotIn('results', c.current(self.root, name)[0])

    def test_close_cannot_claim_delivery_without_authority(self):
        c.authorize(self.root, 'T-001', 'team', 'local work only', ['implement', 'consolidate'])
        c.check_task(self.root, 'T-001', 'C1')
        with self.assertRaisesRegex(ValueError, 'deliver'):
            c.close(self.root, 'T-001', {}, {**FACTS, 'deployment': 'deployed'})
        c.close(self.root, 'T-001', {}, FACTS)

    def test_close_and_delivery_require_same_deployment_checks(self):
        put(self.root, c.unit_path('proyecto'), c.document(meta('unit', 'proyecto', depends_on=[],
            policy={'deployment_checks': ['smoke']}), 'Explicit policy'))
        c.check_task(self.root, 'T-001', 'C1')
        with self.assertRaisesRegex(ValueError, 'smoke'):
            c.delivery(self.root, 'T-001', {'deployment': 'deployed'})
        with self.assertRaisesRegex(ValueError, 'smoke'):
            c.close(self.root, 'T-001', {}, {**FACTS, 'deployment': 'deployed'})
        c.close(self.root, 'T-001', {}, FACTS)  # not-run is a valid honest result.

    def external(self, bounded=True):
        check = {'inputs': ['product.py'], 'environment': 'ci', 'provider': 'gitlab', 'tool_version': '18',
                 'result_format': 'gitlab', 'commit': 'abc'}
        if bounded: check['max_age_seconds'] = 60
        self.edit(c.task_path('T-001', 'plan'), lambda p: p.update(checks={'ci': check}))
        name = c.task_path('T-001', 'tarea')
        return check, c.input_fingerprint(self.root, name, c.current(self.root, name)[0], check)

    def test_old_ci_remains_old_after_import_and_reimport(self):
        check, fp = self.external()
        put(self.root, 'ci.json', json.dumps({'id': 42, 'sha': 'abc', 'status': 'success', 'finished_at': '2020-01-01T00:00:00Z'}))
        args = dict(inputs=fp, provider='gitlab', run_id='42')
        import_result(self.root, 'T-001', 'ci', 'ci.json', **args)
        name = c.task_path('T-001', 'plan')
        plan, _, before = c.current(self.root, name)
        self.assertFalse(c.result_current(plan['results']['ci'], fp, check))
        self.assertEqual(import_result(self.root, 'T-001', 'ci', 'ci.json', **args)['status'], 'unchanged')
        self.assertEqual(before, c.current(self.root, name)[2])

    def test_unknown_ci_age_cannot_satisfy_freshness_policy(self):
        _, fp = self.external()
        put(self.root, 'ci.json', json.dumps({'id': 42, 'sha': 'abc', 'status': 'success'}))
        with self.assertRaisesRegex(ValueError, 'original execution time'):
            import_result(self.root, 'T-001', 'ci', 'ci.json', inputs=fp, provider='gitlab', run_id='42')

    def legacy(self, controls=0):
        elements = [
            ({'uid': 'p', 'id': 'PROJECT-1', 'kind': 'project', 'state': 'active',
              'data': {'policy': {'required_checks': ['C1']}}}, 'Product policy'),
            ({'uid': 'r', 'id': 'FR-1', 'kind': 'requirement', 'state': 'active'}, 'Access contract'),
            ({'uid': 't', 'id': 'TASK-1', 'kind': 'task', 'state': 'active', 'relations': {'requirements': ['r']},
              'data': {'owner': 'team', 'criteria': {'C1': 'Nonempty values are visible'},
                       'checks': c.current(self.root, c.task_path('T-001', 'plan'))[0]['checks']}}, 'Implement access')]
        elements += [({'uid': f'ck-{i}', 'id': f'CKPT-{i}', 'kind': 'checkpoint', 'state': 'active'}, 'Method-only tracking ' * 100) for i in range(controls)]
        raw = '---\nschema_version: "3.1"\n---\n\n' + '\n'.join('<!-- lks-sdd: ' + json.dumps(e) + ' -->\n' + body + '\n<!-- /lks-sdd -->' for e, body in elements)
        put(self.root, 'docs/lks-sdd/source.md', raw)

    def test_migrated_task_keeps_executable_criteria_and_policy(self):
        self.legacy()
        output, _, _ = migration.convert(Reader(self.root))
        for name, raw in output.items(): put(self.root, name, raw)
        task = c.current(self.root, c.task_path('task-1', 'tarea'))[0]
        self.assertEqual(task['criteria'], {'C1': 'Nonempty values are visible'})
        self.assertEqual(c.project_policy(self.root)['required_checks'], ['C1'])
        c.authorize(self.root, 'task-1', 'team', 'continue converted task', ['implement', 'consolidate'])
        c.check_task(self.root, 'task-1', 'C1')
        c.close(self.root, 'task-1', {}, FACTS)

    def test_method_history_does_not_grow_total_converted_documents(self):
        totals = []
        for history in (0, 10, 100):
            self.legacy(history)
            output, _, _ = migration.convert(Reader(self.root))
            docs = {k: v for k, v in output.items() if k.startswith('docs/sdd/')}
            totals.append((len(docs), sum(map(len, docs.values()))))
        self.assertEqual(totals[0], totals[1])
        self.assertEqual(totals[0], totals[2])

    def test_migration_does_not_create_configuration_backlog_or_reopen_done(self):
        self.legacy()
        reader = Reader(self.root)
        task = reader.elements['t']
        task.meta['data'] = {'health': 'needs-reverification', 'continuation': 'reconciliation-required',
                             'reconciliation_required': True}
        for source, expected in [('done', 'cerrado'), ('ready', 'preparado'), ('draft', 'definido'),
                                 ('in-review', 'en-curso'), ('reconciliation-required', 'en-curso')]:
            with self.subTest(source=source):
                task.meta['state'] = source
                output, _, _ = migration.convert(reader)
                plan, body = c.parse(output[c.task_path('task-1', 'plan')])
                self.assertEqual(plan['state'], expected)
                self.assertEqual(plan['blockers'], [])
                self.assertEqual(plan['next'], '')
                self.assertNotIn('results', plan)
                self.assertIn('needs-reverification', output[c.task_path('task-1', 'tarea')].decode())

    def test_migration_keeps_actual_blocker_and_close_still_needs_evidence(self):
        self.legacy()
        reader = Reader(self.root)
        task = reader.elements['t']
        task.meta['data'] = {'blockers': ['Missing required business decision']}
        output, _, _ = migration.convert(reader)
        plan, _ = c.parse(output[c.task_path('task-1', 'plan')])
        self.assertEqual(plan['blockers'], ['Missing required business decision'])
        self.assertEqual(plan['state'], 'bloqueado')
        task.meta['data'] = {}
        output, _, _ = migration.convert(reader)
        for name, raw in output.items(): put(self.root, name, raw)
        c.authorize(self.root, 'task-1', 'team', 'resume', ['consolidate'])
        with self.assertRaisesRegex(ValueError, 'requires checks'):
            c.close(self.root, 'task-1', {}, FACTS)
        task.meta['state'] = 'blocked'
        output, _, _ = migration.convert(reader)
        self.assertEqual(c.parse(output[c.task_path('task-1', 'plan')])[0]['state'], 'bloqueado')
        task.meta.update(state='active', data={'health': 'blocked'})
        output, _, _ = migration.convert(reader)
        self.assertTrue(c.parse(output[c.task_path('task-1', 'plan')])[0]['blockers'])

    def test_orphan_requests_preserve_content_without_creating_work(self):
        from v5_legacy import Element
        self.legacy()
        reader = Reader(self.root)
        for kind in ('request', 'proposal', 'change', 'increment', 'release', 'plan'):
            reader.elements[kind] = Element({'uid': kind, 'id': kind, 'kind': kind, 'state': 'draft',
                'data': {'criteria': {'C1': 'Preserve unique ' + kind}}}, 'Historic ' + kind, 'docs/lks-sdd/source.md', '3.1')
        output, _, counts = migration.convert(reader)
        self.assertEqual(counts['tasks'], 1)
        text = b'\n'.join(output.values()).decode()
        for kind in ('request', 'proposal', 'change', 'increment', 'release', 'plan'):
            self.assertIn('Preserve unique ' + kind, text)
            self.assertNotIn(c.task_path(kind, 'tarea'), output)
        for name, data in output.items(): put(self.root, name, data)
        self.assertNotIn(c.unit_path('antecedentes'), c.context(self.root, 'task-1')['documents'])
        self.assertNotIn('Preserve unique request', output[c.unit_path('proyecto')].decode())

    def test_scoped_quality_policy_excludes_only_demonstrably_unrelated_paths(self):
        policy = {'required_checks': ['sonar'], 'check_scopes': {'sonar': ['backend/app', 'frontend/src']}}
        for paths, needed in [(['docs/guide.md'], False), (['backend/app/api.py'], True),
                              (['frontend/*'], True), (['**/*.py'], True), (['.'], True), ([], True),
                              (['backend/app-old/a.py'], False), (['backend/app/../docs'], True)]:
            with self.subTest(paths=paths):
                self.assertEqual(c.required_checks(policy, {'paths': paths}), {'sonar'} if needed else set())
        put(self.root, c.unit_path('proyecto'), c.document(meta('unit', 'proyecto', policy=policy), 'Scoped policy'))
        self.edit(c.task_path('T-001', 'tarea'), lambda t: t.update(paths=['docs/guide.md']))
        c.authorize(self.root, 'T-001', 'team', 'docs scope', ['implement', 'consolidate'])
        c.check_task(self.root, 'T-001', 'C1')
        c.close(self.root, 'T-001', {}, FACTS)
        self.edit(c.task_path('T-001', 'tarea'), lambda t: t.update(paths=['backend/app/api.py']))
        self.edit(c.task_path('T-001', 'plan'), lambda p: p.update(state='en-curso'))
        c.authorize(self.root, 'T-001', 'team', 'code scope', ['consolidate'])
        with self.assertRaisesRegex(ValueError, 'requires checks.*sonar'):
            c.close(self.root, 'T-001', {}, FACTS)

    def test_migration_preserves_control_scope_and_unconditional_precedence(self):
        self.legacy()
        reader = Reader(self.root)
        policy = reader.elements['p'].meta['data']['policy']
        policy['controls'] = {'sonar': {'mode': 'required', 'scope': ['backend/app', 'frontend/src']}}
        output, _, _ = migration.convert(reader)
        converted = c.parse(output[c.unit_path('proyecto')])[0]['policy']
        self.assertEqual(converted['check_scopes']['sonar'], ['backend/app', 'frontend/src'])
        self.assertEqual(converted['required_checks'], ['C1', 'sonar'])
        policy['required_checks'].append('sonar')
        self.assertNotIn('sonar', migration.operational_policy(reader.elements, None).get('check_scopes', {}))

    def test_repeated_operations_do_not_accumulate_control_documents(self):
        c.check_task(self.root, 'T-001', 'C1')
        def snapshot():
            return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in (self.root / 'docs/sdd').rglob('*.md')}
        before = snapshot()
        for _ in range(20):
            c.context(self.root, 'T-001'); c.status(self.root, 'T-001')
            self.assertEqual(c.check_task(self.root, 'T-001', 'C1')['status'], 'reused')
        self.assertEqual(before, snapshot())

    def test_native_cli_stdin_flow_needs_no_argument_or_control_files(self):
        cli = Path(__file__).resolve().parents[1] / 'scripts/lks_sdd.py'
        def call(command, data=None, *extra):
            argv = [sys.executable, '-B', '-X', 'utf8', str(cli), command, '--root', str(self.root), '--task', 'CLI', *extra]
            if data is not None: argv += ['--data', '-']
            result = subprocess.run(argv, input=json.dumps(data).encode() if data is not None else None, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)
        call('prepare', dict(title='Native CLI flow', request='Preserve visibility', criteria=['Visible when nonempty'], units=['acceso'], owner='test'))
        call('authorize', dict(actor='test', source='fixture decision', scope=['implement', 'consolidate']))
        checks = c.current(self.root, c.task_path('T-001', 'plan'))[0]['checks']
        self.edit(c.task_path('CLI', 'plan'), lambda p: p.update(checks=checks))
        self.assertEqual(call('check', None, '--check', 'C1')['status'], 'passed')
        self.assertEqual(call('check', None, '--check', 'C1')['status'], 'reused')
        call('close', dict(documents={'acceso': update(self.root)['acceso'].decode()}, facts=FACTS))
        self.assertEqual(sorted(p.name for p in (self.root / 'docs/sdd/tareas/CLI').iterdir()), ['plan.md', 'tarea.md'])
        self.assertFalse(list(self.root.glob('*.json')))
        self.assertFalse((self.root / '.sdd-work/journal.json').exists())

    def test_migration_preserves_foreign_edit_during_cutover(self):
        from test_v5_scenarios import source
        root = self.root / 'consumer'; root.mkdir(); source(root)
        preview = migration.preview(root)
        atomic = migration.atomic_write
        def editor(path, raw, **kwargs):
            atomic(path, raw, **kwargs)
            if path.name == 'tarea.md':
                put(root, 'docs/lks-sdd/task.md', 'Foreign decision during conversion')
        with patch.object(migration, 'atomic_write', editor), self.assertRaises(c.Conflict):
            migration.run(root, preview['preview_sha256'])
        self.assertEqual(c.read(root, 'docs/lks-sdd/task.md'), b'Foreign decision during conversion')
        self.assertTrue(c.read(root, migration.JOURNAL))

    def test_migration_resumes_interrupted_final_cleanup(self):
        from test_v5_scenarios import source
        root = self.root / 'consumer'; root.mkdir(); source(root)
        preview = migration.preview(root)
        with patch.object(migration, 'clean_staging', side_effect=InterruptedError), self.assertRaises(InterruptedError):
            migration.run(root, preview['preview_sha256'])
        self.assertFalse((root / 'docs/lks-sdd').exists())
        self.assertEqual(migration.run(root, resume=True)['status'], 'passed')
        self.assertFalse((root / migration.WORK).exists())
        self.assertFalse((root / migration.JOURNAL).exists())

    def test_conversion_report_measures_scope_and_is_written_only_after_success(self):
        from test_v5_scenarios import source
        root = self.root / 'consumer'; root.mkdir(); source(root)
        preview = migration.preview(root)
        self.assertIsNone(c.read(root, migration.REPORT))
        payload = migration.load_preview(root)
        before_files = sum(c.path_at(root, n).is_file() for n in payload['entries'])
        before_bytes = sum(c.path_at(root, n).stat().st_size for n in payload['entries'] if c.path_at(root, n).is_file())
        with self.assertRaises(InterruptedError): migration.run(root, preview['preview_sha256'], interrupt_after=1)
        self.assertIsNone(c.read(root, migration.REPORT))
        result = migration.run(root, resume=True)
        report = c.read(root, migration.REPORT)
        after_files = sum(c.path_at(root, n).is_file() for n in payload['entries'])
        after_bytes = sum(c.path_at(root, n).stat().st_size for n in payload['entries'] if c.path_at(root, n).is_file())
        self.assertIn(f'| **{before_files}** | **{after_files}** | **{before_bytes}** | **{after_bytes}** |'.encode(), report)
        self.assertEqual(result['report'], migration.REPORT)
        self.assertIn('Tareas con bloqueos declarados en origen'.encode(), report)
        migration.run(root, resume=True)
        self.assertEqual(report, c.read(root, migration.REPORT))
        self.assertFalse((root / migration.WORK).exists())

    def test_conversion_report_tampering_blocks_before_cutover(self):
        from test_v5_scenarios import source
        root = self.root / 'consumer'; root.mkdir(); source(root)
        preview = migration.preview(root)
        put(root, migration.WORK + '/report.md', 'edited')
        with self.assertRaises(c.Conflict): migration.run(root, preview['preview_sha256'])
        self.assertTrue(c.read(root, 'docs/lks-sdd/task.md'))
        self.assertIsNone(c.read(root, migration.REPORT))

    def test_report_cannot_describe_outputs_edited_after_their_write(self):
        from test_v5_scenarios import source
        root = self.root / 'consumer'; root.mkdir(); source(root)
        preview = migration.preview(root)
        atomic = migration.atomic_write
        edited = []
        def editor(path, raw, **kwargs):
            atomic(path, raw, **kwargs)
            if path.name == 'tarea.md' and not edited:
                unit = next((root / 'docs/sdd/especificaciones').glob('*.md'))
                unit.write_bytes(unit.read_bytes() + b'\nForeign useful decision\n')
                edited.append(unit)
        with patch.object(migration, 'atomic_write', editor), self.assertRaises(c.Conflict):
            migration.run(root, preview['preview_sha256'])
        self.assertIn(b'Foreign useful decision', edited[0].read_bytes())
        self.assertTrue(c.read(root, 'docs/lks-sdd/task.md'))
        self.assertIsNone(c.read(root, migration.REPORT))

    def test_unconverted_criteria_and_check_details_remain_available(self):
        self.legacy()
        name = 'docs/lks-sdd/source.md'
        raw = c.read(self.root, name).decode().replace('"Nonempty values are visible"', '{"expected": "Visible value"}')
        raw = raw.replace('"inputs":', '"manual_inputs":')
        put(self.root, name, raw)
        output, _, _ = migration.convert(Reader(self.root))
        combined = b'\n'.join(output.values())
        self.assertIn(b'Visible value', combined)
        self.assertIn(b'manual_inputs', combined)

    def test_migration_keeps_distinct_task_and_plan_criteria_with_same_identifier(self):
        self.legacy()
        name = 'docs/lks-sdd/source.md'
        raw = c.read(self.root, name).decode().replace('"requirements": ["r"]', '"requirements": ["r"], "plans": ["plan"]')
        plan = {'uid': 'plan', 'id': 'PLAN-1', 'kind': 'plan', 'state': 'active',
                'relations': {'tasks': ['t']}, 'data': {'criteria': {'C1': 'Another distinct obligation'},
                'checks': c.current(self.root, c.task_path('T-001', 'plan'))[0]['checks']}}
        raw += '\n<!-- lks-sdd: ' + json.dumps(plan) + ' -->\nPlan\n<!-- /lks-sdd -->\n'
        put(self.root, name, raw)
        output, _, _ = migration.convert(Reader(self.root))
        task, _ = c.parse(output[c.task_path('task-1', 'tarea')])
        plan, _ = c.parse(output[c.task_path('task-1', 'plan')])
        self.assertEqual(task['criteria'], {'C1': 'Nonempty values are visible', 'PLAN-1-C1': 'Another distinct obligation'})
        self.assertEqual({x for check in plan['checks'].values() for x in check['criteria']}, set(task['criteria']))


if __name__ == '__main__': unittest.main()
