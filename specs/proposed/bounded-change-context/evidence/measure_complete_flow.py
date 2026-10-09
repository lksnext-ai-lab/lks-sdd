"""Compare a complete disposable library journey; no model or real consumer calls."""
import argparse
import cProfile
import json
from pathlib import Path
import pstats
import shutil
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(args.runtime.resolve() / 'scripts'))
    import v3_contract
    assert Path(v3_contract.__file__).resolve().parent == args.runtime.resolve() / 'scripts'
    sys.path.insert(0, str(repo / 'tests'))
    from test_v31_review import IntegralTests
    from test_v3_workflow import commit_packet, git
    from presentation_test_support import present, technical_solution
    from v3_authoring import author
    from v3_contract import element, load, DOCS
    from v3_cli import execute
    import v3_cli
    import v3_decision_presentation as presentation
    from v3_lifecycle import checkpoint
    from v3_verification import integrate
    from v31_corrections import delivery
    from v31_guidance import interventions

    report = {'runtime': args.label, 'scope': 'Complete synthetic library journey with real Git/Markdown/guards; not host acceptance',
              'model_calls': 0, 'real_consumer_writes': [], 'billed_tokens': None, 'human_seconds': None,
              'timing_note': 'Instrumented single run under concurrent storage regression; latency comparison is not accredited',
              'transport': 'ordinary decision-view/review presentation; full library results remain available',
              'preparation': [], 'operations': [], 'presentations': [], 'run_status': 'running'}

    def save():
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    original_view = presentation.decision_view
    def measured_view(*a, **kw):
        result = original_view(*a, **kw)
        caller = sys._getframe(1)
        # Only presentations requested by the synthetic reviewer are transport.
        # Fresh guard recomputations remain in the operation's CPU/call counts.
        if Path(caller.f_code.co_filename).name == 'presentation_test_support.py':
            brief = presentation.compact(result)
            report['presentations'].append({'event': result['event'], 'complete': result['complete'],
                'sources': len(result['sources']), 'checkpoint_sources': sum(s.get('meta', {}).get('kind') == 'checkpoint' for s in result['sources']),
                'literal_characters': len(result['markdown']), 'ordinary_json_characters': len(json.dumps(brief, ensure_ascii=False, indent=2)),
                'full_json_characters': len(json.dumps(result, ensure_ascii=False, indent=2)),
                'global_obligation_present': 'GLOBAL-OBLIGATION-KEEP' in result['markdown'] if fixture_ready else None})
        return result
    presentation.decision_view = measured_view
    fixture_ready = False

    def measure(name, fn, *, preparation=False, query=False):
        before = load(fixture.root).require_valid().snapshot() if query else None
        profiler = cProfile.Profile(); started = time.perf_counter()
        result = profiler.runcall(fn)
        row = {'operation': name, 'instrumented_seconds': time.perf_counter()-started}
        tracked = []
        for (file, line, function), values in pstats.Stats(profiler).stats.items():
            if (Path(file).name, function) in {('v3_contract.py', 'load'), ('v3_contract.py', '_load'), ('v3_contract.py', 'parse'),
                    ('v3_workflow.py', 'request_facts'), ('v3_context.py', 'select'), ('v2_contract.py', 'read_bytes')}:
                tracked.append({'file': Path(file).name, 'function': function, 'calls': values[1]})
        row['tracked'] = tracked
        if query:
            row['query_preserved_snapshot'] = before == load(fixture.root).require_valid().snapshot()
            shown = v3_cli.presentation_output('review', result) if name == 'review' and hasattr(v3_cli, 'presentation_output') else result
            row['ordinary_json_characters'] = len(json.dumps(shown, ensure_ascii=False, indent=2))
            row['full_json_characters'] = len(json.dumps(result, ensure_ascii=False, indent=2))
        report['preparation' if preparation else 'operations'].append(row)
        save(); print(name+' completed', flush=True)
        return result

    fixture = IntegralTests('test_individual_three_decisions_and_no_role_duplicates')
    try:
        measure('initialize-and-draft-proposal', fixture.setUp, preparation=True)
        def add_independent_contract():
            rows = []
            for i in range(5):
                request = element('request', f'Independent request {i}', 'Independent objective')
                rule = element('requirement', f'Independent obligation {i}', ('Unrelated literal condition. '*100))
                proposal = element('proposal', f'Independent proposal {i}', 'Independent behavior', request=request['meta']['uid'],
                    part='joint', objective='Independent', included=['other.py'], excluded=['app.py'], behavior='Independent',
                    solution=technical_solution(), impact='Independent', acceptance=['Independent'])
                proposal['meta']['relations']['requirements'] = [rule['meta']['uid']]
                request['meta']['relations']['proposal'] = [proposal['meta']['uid']]
                rows += [request, proposal, rule]
            rows.append(element('rule', 'Global obligation', 'GLOBAL-OBLIGATION-KEEP: preserve the public interface.', **{'global': True}))
            commit_packet(fixture.root, author(fixture.root, fixture.actor, rows))
        measure('prepare-five-independent-units-and-global-contract', add_independent_contract, preparation=True)
        fixture_ready = True
        measure('review', lambda: execute('review', fixture.root, {'request': fixture.req}), query=True)
        measure('close-proposal', fixture.close_proposal)
        measure('create-and-authorize-plan', fixture.create_plan)
        with tempfile.TemporaryDirectory(prefix='lks-flow-integration-') as temp:
            trusted = Path(temp)/'trusted'; shutil.copytree(fixture.root, trusted)
            git(trusted, 'symbolic-ref', 'HEAD', 'refs/heads/main')
            measure('start', lambda: fixture.advance('start'))
            for i in range(10):
                measure(f'checkpoint-{i}', lambda i=i: commit_packet(fixture.root,
                    checkpoint(fixture.root, fixture.actor, fixture.task, f'Observed progress {i}: '+('literal progress '*20), [])))
            measure('pause', lambda: fixture.advance('pause'))
            measure('resume', lambda: fixture.advance('resume'))
            measure('status', lambda: execute('status', fixture.root, {'request': fixture.req}), query=True)
            measure('review', lambda: execute('review', fixture.root, {'request': fixture.req}), query=True)
            # Execute a real deterministic fixture test before recording its report.
            (fixture.root/'app.py').write_text("def greeting(): return 'Hola'\n", encoding='utf-8')
            namespace = {}; exec((fixture.root/'app.py').read_text(encoding='utf-8'), namespace)
            assert namespace['greeting']() == 'Hola'
            measure('implement', lambda: fixture.advance('implement'))
            measure('record-passing-evidence', fixture.proof)
            measure('verify', lambda: fixture.advance('verify'))
            measure('close', lambda: fixture.advance('close'))
            measure('integrate-and-accept', lambda: commit_packet(fixture.root, present(integrate,
                fixture.root, fixture.actor, fixture.req, trusted, 'Accept the exact verified greeting', accept_result=True)))
            measure('prepare-delivery', lambda: commit_packet(fixture.root,
                delivery(fixture.root, fixture.actor, fixture.req, 'Prepare the accepted fixture delivery')))
        final = interventions(load(fixture.root).require_valid(), fixture.req)
        assert all(h['state'] == 'completed' for h in final['milestones'])
        assert not final['interventions']
        assert all(r['query_preserved_snapshot'] for r in report['operations'] if 'query_preserved_snapshot' in r)
        assert all(r['global_obligation_present'] for r in report['presentations'] if r['global_obligation_present'] is not None)
        report['result'] = {'all_milestones': 'completed', 'open_interventions': 0, 'greeting': 'Hola',
                            'historical_checkpoints_preserved': len(load(fixture.root).by_kind('checkpoint')),
                            'canonical_schema': json.loads((fixture.root/'.lks-sdd/project.json').read_text())['schema_version']}
        report['total_instrumented_seconds'] = sum(r['instrumented_seconds'] for r in report['preparation']+report['operations'])
        report['ordinary_presentation_characters'] = sum(r['ordinary_json_characters'] for r in report['presentations']) + sum(r.get('ordinary_json_characters', 0) for r in report['operations'])
        report['run_status'] = 'completed'; save()
    except Exception as exc:
        report['run_status'] = 'incomplete'; report['error'] = type(exc).__name__+': '+str(exc); save(); raise
    finally:
        fixture.doCleanups()


if __name__ == '__main__': main()
