"""Account for literal prose reconciliation cost on an explicit disposable fixture."""
import copy
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'tests'))
from test_v3_documentary_flow import DocumentaryFlowTests
from test_v3_workflow import commit_packet
from presentation_test_support import present
from v3_authoring import governance
from v3_contract import load, DOCS, sha
from v3_decision_presentation import decision_view, compact


def main():
    output = Path(sys.argv[1])
    fixture = DocumentaryFlowTests('test_prose_declaration_needs_exact_governance_and_content_then_goes_stale')
    report = {'scope': 'Synthetic exact-content governance and ordinary presentation characters; not AI billing or human review',
              'billed_tokens': None, 'human_seconds': None, 'real_consumer_writes': [], 'run_status': 'running'}
    try:
        started = time.perf_counter(); fixture.setUp(); fixture.two_proposals()
        paths = []
        for i in range(25):
            path = f'{DOCS}/independent-note-{i}.md'
            (fixture.root/path).write_text('---\nschema_version: "3.1"\n---\n\n'+
                f'Contract for the second request, note {i}. '+('Keep the independent limits unchanged. '*100)+'\n', encoding='utf-8')
            paths.append(path)
        report['fixture_setup_seconds'] = time.perf_counter()-started
        model = load(fixture.root).require_valid()
        data = {'actor': fixture.actor, 'units': [fixture.proposals[0]], 'purpose': 'proposal'}
        def describe(view):
            return {'ordinary_json_characters': len(json.dumps(compact(view), ensure_ascii=False, indent=2)),
                    'literal_characters': len(view['markdown']), 'sources': len(view['sources']),
                    'attachments': len(view['attachments']), 'complete': view['complete']}
        before = decision_view(fixture.root, 'approve', data)
        project = copy.deepcopy(model.project.item()); project['meta']['revision'] += 1
        project['meta']['data']['context_scopes'] = {'version': 'lks-sdd-prose-scope/1', 'sources': [
            {'path': path, 'sha256': sha(model.prose[path].encode('utf-8')), 'units': [fixture.requests[1]],
             'global': False, 'reason': 'Literal fixture contract exclusive to the second request; no shared limits.'} for path in paths]}
        governance_data = {'actor': fixture.actor, 'items': [project], 'statement': 'Confirm the exact fixture source scopes',
                           'reason': 'Exclude only the independent second-request prose'}
        review = decision_view(fixture.root, 'governance', governance_data)
        assert review['complete'], review['issues']
        assert all(model.prose[path] in review['markdown'] for path in paths)
        started = time.perf_counter()
        commit_packet(fixture.root, present(governance, fixture.root, fixture.actor, [project],
            governance_data['statement'], governance_data['reason']))
        report['governance_prepare_apply_seconds'] = time.perf_counter()-started
        after = decision_view(fixture.root, 'approve', data)
        report['before'] = describe(before); report['classification_review'] = describe(review); report['after'] = describe(after)
        assert before['complete'] and after['complete']
        assert not any(s['key'].startswith('prose:') and s['source']['path'] in paths for s in after['sources'])
        assert all(sha((fixture.root/path).read_bytes()) == model.hashes[path] for path in paths)
        delta = report['before']['ordinary_json_characters']-report['after']['ordinary_json_characters']
        # This counts an extra classification view, not billable input or human effort.
        # It assumes a later operation would otherwise emit the same unrelated text.
        report['literal_sources_read_for_classification'] = len(paths)
        report['source_prose_characters_reviewed'] = sum(len(model.prose[path]) for path in paths)
        report['canonical_declaration_characters_written'] = len(json.dumps(project['meta']['data']['context_scopes'], ensure_ascii=False))
        report['ordinary_characters_saved_per_equivalent_view'] = delta
        report['equivalent_views_to_offset_extra_classification_view_characters'] = math.ceil(report['classification_review']['ordinary_json_characters']/delta) if delta > 0 else None
        report['limitations'] = ['Fixtures define independent prose explicitly; this is not a semantic audit of the original consumer.',
            'Exact governance review itself retains other unclassified prose; its first-use cost may be high in a large consumer.',
            'Offset is a character-only conditional scenario; token caching, model reading, human decisions and elapsed time have no measured break-even.',
            'No corpus-wide conversion is required. The proposed runtime update remains explicit and recoverable.']
        report['run_status'] = 'completed'
    except Exception as exc:
        report['run_status'] = 'incomplete'; report['error'] = type(exc).__name__+': '+str(exc); raise
    finally:
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        fixture.doCleanups()


if __name__ == '__main__': main()
