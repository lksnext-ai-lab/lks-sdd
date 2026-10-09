"""Bounded diagnosis on a disposable fixture, using an unchanged installed runtime."""
import argparse
import cProfile
import json
from pathlib import Path
import pstats
import sys
import time


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--label', default='installed 3.2.0')
    args = p.parse_args()
    repo = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(args.runtime.resolve() / 'scripts'))
    import v3_contract
    assert Path(v3_contract.__file__).resolve().parent == args.runtime.resolve() / 'scripts'
    sys.path.insert(0, str(repo / 'tests'))
    from test_v31_review import IntegralTests
    from v3_cli import execute
    from v3_contract import load, element, render, location
    from v3_decision_presentation import decision_view
    from v3_guidance import readiness

    report = {'scope': 'Bounded library-dispatch diagnostics, not host observation or full public runtime boundary',
              'runtime': args.label, 'model_calls': 0, 'consumer_writes': [],
              'timing_note': 'One instrumented observation per query, not a stable latency benchmark',
              'cases': [], 'run_status': 'running'}

    def save():
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def inspect(name, fn):
        before = load(fixture.root).require_valid().snapshot()
        profile = cProfile.Profile()
        started = time.perf_counter()
        result = profile.runcall(fn)
        seconds = time.perf_counter() - started
        stats = pstats.Stats(profile)
        tracked = []
        for (file, line, function), values in stats.stats.items():
            if (Path(file).name, function) in {('v3_contract.py', 'load'), ('v3_contract.py', '_load'), ('v3_contract.py', 'parse'),
                    ('v3_workflow.py', 'request_facts'), ('v31_guidance.py', 'interventions'),
                    ('v3_context.py', 'select'), ('v2_contract.py', 'read_bytes')}:
                tracked.append({'file': Path(file).name, 'function': function, 'calls': values[1]})
        row = {'query': name, 'instrumented_seconds': seconds, 'tracked': tracked,
               'json_characters': len(json.dumps(result, ensure_ascii=False, indent=2)),
               'result_status': result.get('status'),
               'query_preserved_snapshot': before == load(fixture.root).require_valid().snapshot()}
        for field in ['sources', 'attachments', 'elements']:
            if field in result: row[field] = len(result[field])
        if 'sources' in result:
            row['checkpoint_sources'] = sum(v.get('meta', {}).get('kind') == 'checkpoint' for v in result['sources'])
        if 'markdown' in result: row['markdown_characters'] = len(result['markdown'])
        report['cases'].append(row)
        save()
        print(json.dumps(row, ensure_ascii=False), flush=True)

    fixture = IntegralTests('test_individual_three_decisions_and_no_role_duplicates')
    try:
        started = time.perf_counter()
        fixture.setUp(); fixture.close_proposal(); fixture.create_plan()
        report['setup_seconds'] = time.perf_counter() - started
        save()
        print('Synthetic authorized task prepared', flush=True)
        inspect('catalog-limit-1', lambda: execute('catalog', fixture.root, {'limit': 1}))
        inspect('catalog-limit-50', lambda: execute('catalog', fixture.root, {'limit': 50}))
        inspect('status-selected-request', lambda: execute('status', fixture.root, {'request': fixture.req}))
        inspect('review-dispatch', lambda: execute('review', fixture.root, {'request': fixture.req}))
        inspect('readiness-dispatch-unpinned-fixture', lambda: execute('readiness', fixture.root,
                {'task': fixture.task, 'actor': fixture.actor, 'action': 'start'}))
        inspect('readiness-start-library', lambda: readiness(fixture.root, fixture.task, fixture.actor, 'start'))
        data = {'request': fixture.req}
        inspect('review-before-extra-progress', lambda: decision_view(fixture.root, 'review', data))
        # Synthetic history inputs only: do not claim these were produced by an actual session.
        for i in range(10):
            event = element('checkpoint', f'Synthetic earlier progress {i}',
                            'Earlier observation for the same task. ' * 20,
                            task=fixture.task, request=fixture.req, classification='progress',
                            pending=[], recorded_at=f'2026-01-01T00:00:{i:02d}Z')
            event['meta'].update(state='observed', nature='fact')
            (fixture.root / location(event)).write_bytes(render(event, '3.1'))
        load(fixture.root).require_valid()
        inspect('review-after-10-extra-progress', lambda: decision_view(fixture.root, 'review', data))
        report['run_status'] = 'completed'
        save()
    except Exception as exc:
        report['run_status'] = 'incomplete'
        report['error'] = type(exc).__name__ + ': ' + str(exc)
        save()
        raise
    finally:
        fixture.doCleanups()


if __name__ == '__main__':
    main()
