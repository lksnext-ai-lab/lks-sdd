"""Diagnostic only: synthetic projects, original runtime, no consumer mutations.

Run with Python that satisfies the plugin's existing dependencies:
  python -B -X utf8 measure_documentary_cost.py --runtime PLUGIN_ROOT --output REPORT
The source repository's existing fixture helpers are reused, but runtime modules
are loaded exclusively from --runtime. No approval or scope guard is bypassed.
"""
import argparse
import collections
import cProfile
import hashlib
import json
import pstats
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--extended', action='store_true',
                        help='Also run large/scoped fixtures and lifecycle probes; deliberately opt-in.')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[4]
    runtime = args.runtime.resolve()
    sys.path.insert(0, str(runtime / 'scripts'))
    import v3_contract
    assert Path(v3_contract.__file__).resolve().parent == runtime / 'scripts'
    sys.path.insert(0, str(repo / 'tests'))
    from test_v31_review import IntegralTests
    from v3_contract import load, element, render, location
    from v3_context import context, _CACHE
    from v3_decision_presentation import decision_view, compact
    from v3_lifecycle import review, checkpoint
    from v3_guidance import status, readiness
    from v3_packet import persist
    from v31_guidance import interventions

    report = {'runtime_version': json.loads((runtime / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))['version'],
              'runtime_origin': 'installed plugin supplied via --runtime',
              'python_version': sys.version, 'repeats': args.repeats,
              'scope': 'Synthetic library queries and selected fresh CLI processes; no model calls or real consumer',
              'billing_tokens': None, 'host_tokens': None, 'whole_development_latency': None,
              'module_sha256': {name: hashlib.sha256((runtime / 'scripts' / name).read_bytes()).hexdigest()
                                for name in ['v3_context.py', 'v3_contract.py', 'v3_decision_presentation.py', 'v3_lifecycle.py', 'v3_storage.py']},
              'cases': [], 'profiles': [], 'cli': [], 'setup_seconds': None,
              'run_status': 'running', 'extended': args.extended}

    def save():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

    def measure(label, fn, **metadata):
        times = []
        for _ in range(args.repeats):
            started = time.perf_counter()
            result = fn()
            times.append(time.perf_counter() - started)
        started = time.perf_counter()
        serialized = json.dumps(result, ensure_ascii=False, indent=2)
        serialize_time = time.perf_counter() - started
        row = {'operation': label, **metadata, 'seconds': times,
               'median_seconds': statistics.median(times), 'serialization_seconds': serialize_time,
               'json_characters': len(serialized), 'utf8_bytes': len(serialized.encode('utf-8'))}
        if isinstance(result, dict):
            for name in ('complete', 'selector_mode', 'runtime_cache'):
                if name in result: row[name] = result[name]
            for name in ('sources', 'attachments', 'issues'):
                if name in result: row[name] = len(result[name])
            if 'markdown' in result: row['markdown_characters'] = len(result['markdown'])
            if 'sources' in result:
                row['source_reason_counts'] = dict(collections.Counter(s.get('reason') for s in result['sources']))
        report['cases'].append(row)
        print(json.dumps({k: row[k] for k in ('operation', 'phase', 'variant', 'median_seconds', 'json_characters') if k in row}), flush=True)
        save()
        return result

    def profile(label, fn):
        p = cProfile.Profile()
        p.runcall(fn)
        s = pstats.Stats(p)
        tracked = []
        for (filename, line, name), (primitive, total, own, cumulative, callers) in s.stats.items():
            if (Path(filename).name, name) in {
                ('v3_contract.py', 'load'), ('v3_contract.py', 'parse'), ('v3_contract.py', 'get'),
                ('v3_context.py', 'select'), ('v3_policy.py', 'policy_for'),
                ('v3_decision_presentation.py', 'decision_view'), ('subprocess.py', 'run'),
                ('v3_storage.py', 'prepare'), ('v2_contract.py', 'read_bytes')}:
                tracked.append({'file': Path(filename).name, 'line': line, 'function': name,
                                'calls': total, 'self_seconds': own, 'cumulative_seconds': cumulative})
        hottest = sorted(s.stats.items(), key=lambda pair: pair[1][2], reverse=True)[:12]
        report['profiles'].append({'operation': label, 'instrumented_seconds': s.total_tt,
                                   'tracked': tracked,
                                   'top_self': [{'file': Path(k[0]).name, 'line': k[1], 'function': k[2],
                                                 'calls': v[1], 'self_seconds': v[2]} for k, v in hottest]})
        save()

    fixture = IntegralTests('test_integral_close_cannot_bypass_objection_or_generic_approval')
    started = time.perf_counter()
    try:
        fixture.setUp()
        report['setup_seconds'] = time.perf_counter() - started
        root = fixture.root
        synthetic = root / 'docs/lks-sdd/cost-synthetic'
        synthetic.mkdir()
        generated = []
        def clear_generated():
            # All generated paths are explicitly inside this disposable fixture.
            for path in generated:
                assert root.resolve() in path.resolve().parents
                path.unlink()
            generated.clear()

        def add_prose(count):
            for i in range(count):
                path = synthetic / f'note-{i:04d}.md'
                text = '---\nschema_version: "3.1"\n---\n# Antecedente independiente\n\n'
                text += ('Detalle historico sin relacion con el cambio solicitado. ' * 72)
                path.write_text(text, encoding='utf-8', newline='\n')
                generated.append(path)

        def add_structured(count):
            for i in range(count):
                req = element('request', f'Otra peticion {i}', 'Peticion independiente para observar crecimiento.')
                prop = element('requirement', f'Otro requisito {i}', 'Obligacion independiente. ' * 160,
                               request=req['meta']['uid'])
                for item in (req, prop):
                    path = root / location(item)
                    path.write_bytes(render(item, '3.1'))
                    generated.append(path)

        data = {'actor': fixture.actor, 'request': fixture.req, 'review': True}
        variants = [('base', 0, False), ('prose-25', 25, False), ('prose-100', 100, False)]
        if args.extended:
            variants.extend([('prose-500', 500, False), ('structured-100', 100, True)])
        for variant, count, structured in variants:
            clear_generated()
            (add_structured if structured else add_prose)(count)
            before = load(root).require_valid().snapshot()
            meta = {'phase': 'before_plan', 'variant': variant}
            measure('load', lambda: {'elements': len(load(root).require_valid().elements)}, **meta)
            view = measure('decision_view', lambda: decision_view(root, 'close-proposal', data), **meta)
            measure('decision_view_compact_transport', lambda: compact(view), **meta)
            measure('review', lambda: review(root, fixture.req), **meta)
            if variant == 'prose-100' and not args.extended:
                assert before == load(root).snapshot(), 'Query changed canonical documents'
                continue
            _CACHE.clear()
            measure('context_default', lambda: context(root, [fixture.req]), **meta)
            measure('context_comparison', lambda: context(root, [fixture.req], comparison=True), **meta)
            measure('status_selected', lambda: status(root, request_id=fixture.req), **meta)
            measure('interventions', lambda: interventions(load(root).require_valid(), fixture.req, actor=fixture.actor), **meta)
            assert before == load(root).snapshot(), 'Query changed canonical documents'
            if variant in {'base', 'prose-500', 'structured-100'}:
                for name, fn in [('decision_view', lambda: decision_view(root, 'close-proposal', data)),
                                 ('review', lambda: review(root, fixture.req)),
                                 ('context_cached', lambda: context(root, [fixture.req]))]:
                    profile(variant + ':' + name, fn)
            if variant in {'base', 'prose-500'}:
                with tempfile.TemporaryDirectory(prefix='sdd-cost-cli-') as cli_temp:
                    payload = Path(cli_temp) / 'input.json'
                    for name, operation, body, extra in [
                        ('decision-default', 'decision-view', {'event': 'close-proposal', 'data': data}, []),
                        ('decision-json', 'decision-view', {'event': 'close-proposal', 'data': data}, ['--json']),
                        ('review-default', 'review', {'request': fixture.req}, []),
                        ('context-default', 'context', {'roots': [fixture.req]}, [])]:
                        payload.write_text(json.dumps(body), encoding='utf-8')
                        started = time.perf_counter()
                        p = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(runtime / 'scripts/lks_sdd.py'),
                                            'v3', operation, str(root), '--input', str(payload), *extra],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
                        row = {'variant': variant, 'operation': name, 'seconds': time.perf_counter() - started,
                               'stdout_bytes': len(p.stdout), 'returncode': p.returncode}
                        if p.returncode: row['error'] = p.stderr.decode('utf-8', errors='replace')[:500] + p.stdout.decode('utf-8', errors='replace')[:500]
                        report['cli'].append(row)
                        print(json.dumps(row), flush=True)
                        save()
        if not args.extended:
            report['run_status'] = 'completed_bounded_queries'
            report['checks'] = {'synthetic_queries_preserved_snapshots': True,
                                'all_cli_queries_succeeded': all(v['returncode'] == 0 for v in report['cli']),
                                'no_guard_modified': True}
            save()
            return
        clear_generated()
        fixture.close_proposal()
        fixture.create_plan()
        for count in [0, 100, 500]:
            clear_generated(); add_prose(count)
            before = load(root).require_valid().snapshot()
            meta = {'phase': 'authorized_task', 'variant': f'prose-{count}'}
            measure('readiness_start_library', lambda: readiness(root, fixture.task, fixture.actor, 'start'), **meta)
            measure('status_selected', lambda: status(root, request_id=fixture.req), **meta)
            measure('context_task', lambda: context(root, [fixture.task]), **meta)
            if count == 500:
                profile('task:readiness', lambda: readiness(root, fixture.task, fixture.actor, 'start'))
            assert before == load(root).snapshot(), 'Query changed canonical documents'
        clear_generated()
        # Prepare-only checkpoints: no application and no user facts are invented.
        # Two equal messages test packet identity, not elapsed human workflow.
        reports = []
        for i in range(2):
            before = load(root).snapshot()
            started = time.perf_counter()
            packet = checkpoint(root, fixture.actor, fixture.task, 'Synthetic unchanged diagnostic checkpoint', [])
            reports.append({'seconds': time.perf_counter()-started,
                            'preview_hash': packet['preview']['preview_hash'],
                            'prepared_write_paths': len(packet['preview'].get('after', {})),
                            'canonical_snapshot_unchanged': before == load(root).snapshot()})
        report['repeated_checkpoint_previews'] = reports
        report['checks'] = {'synthetic_queries_preserved_snapshots': True,
                            'all_cli_queries_succeeded': all(v['returncode'] == 0 for v in report['cli']),
                            'no_guard_modified': True}
        report['run_status'] = 'completed_extended_queries'
        save()
    except KeyboardInterrupt:
        report['run_status'] = 'interrupted_partial_results'
        save()
        raise
    finally:
        fixture.doCleanups()
    print('REPORT=' + str(args.output.resolve()), flush=True)


if __name__ == '__main__':
    main()
