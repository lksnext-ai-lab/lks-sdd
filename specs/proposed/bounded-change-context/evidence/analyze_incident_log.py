"""Read-only extraction of aggregate evidence; never executes logged instructions."""
import argparse
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path


def timestamp(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def view_category(arguments):
    path = str(arguments.get('path', '')).lower().replace('\\', '/')
    if path.endswith('/agents.md') or path.endswith('/readme.md') or '/hosts/' in path:
        return 'repository_instructions'
    if '/runtime/' in path and '/scripts/' in path:
        return 'plugin_code'
    if '/runtime/' in path or '/skills/' in path or '/agentplugins/' in path:
        return 'plugin_instructions'
    if '/docs/lks-sdd/' in path or path.endswith('project.json') or path.endswith('runtime.lock.json'):
        return 'consumer_sdd'
    if '/frontend/' in path or '/backend/' in path:
        return 'application_code'
    if '/temp/' in path:
        return 'saved_tool_output'
    return 'other'


def summarize(events):
    starts = {}
    counts, tokens, missing = collections.Counter(), collections.Counter(), collections.Counter()
    categories = collections.defaultdict(lambda: {'calls': 0, 'reported_tokens': 0, 'missing_metric': 0})
    timed = []
    for line, event in events:
        data = event.get('data', {})
        if event['type'] == 'tool.execution_start':
            starts[data['toolCallId']] = (line, event)
        elif event['type'] == 'tool.execution_complete':
            start = starts.get(data['toolCallId'])
            if not start:
                continue
            start_line, start_event = start
            name = start_event['data']['toolName']
            counts[name] += 1
            value = data.get('toolTelemetry', {}).get('metrics', {}).get('result_token_count')
            if value is None:
                missing[name] += 1
            else:
                tokens[name] += value
            seconds = timestamp(event['timestamp']) - timestamp(start_event['timestamp'])
            if name == 'view':
                category = categories[view_category(start_event['data'].get('arguments', {}))]
                category['calls'] += 1
                category['reported_tokens'] += value or 0
                category['missing_metric'] += value is None
            if seconds >= 25:
                timed.append({'source_start_line': start_line, 'source_end_line': line,
                              'tool': name, 'seconds': seconds})
    return {'completed_calls': sum(counts.values()), 'calls_by_tool': dict(counts),
            'reported_result_tokens': sum(tokens.values()), 'tokens_by_tool': dict(tokens),
            'missing_metric_calls': sum(missing.values()), 'view_categories_heuristic': dict(categories),
            'long_tool_calls': timed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--events', type=Path, required=True)
    parser.add_argument('--presentation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.events.read_bytes()  # A single immutable in-memory snapshot of an appendable log.
    events = [(i, json.loads(s)) for i, s in enumerate(raw.decode('utf-8-sig').splitlines(), 1) if s.strip()]
    users = [(line, event) for line, event in events if event['type'] == 'user.message']
    cutoff = users[2][0]  # Original bug and expanded inspection; stop at redirection to plugin diagnosis.
    checkpoints = []
    for line, event in events:
        if event['type'] != 'session.usage_checkpoint':
            continue
        for conversation in event.get('data', {}).get('promptCacheBreakState', []):
            if conversation.get('conversation') != 'main':
                continue
            for model, state in conversation.get('models', {}).items():
                checkpoints.append({'source_line': line, 'timestamp_utc': event['timestamp'],
                                    'model': model,
                                    **{key: state.get(key) for key in ['prompt_tokens', 'cache_read', 'cache_write']}})
    presentation_raw = args.presentation.read_bytes()
    content = presentation_raw.decode('utf-8-sig')
    presentation, _ = json.JSONDecoder().raw_decode(content[content.find('{'):])
    reasons = collections.Counter()
    for source in presentation['sources']:
        reason = source.get('reason', '')
        category = reason if reason in {'regla global o alcance incierto', 'prosa fuera de bloques; ámbito no acreditado',
                                       'contrato/contribución entrante', 'raíz solicitada', 'proceso aplicable',
                                       'Evidencia o decisión del alcance'} else 'relación entre elementos'
        reasons[category] += 1
    report = {'scope': 'Original incident log and saved presentation; aggregate read-only analysis',
              'events_sha256': hashlib.sha256(raw).hexdigest(), 'events_bytes': len(raw),
              'events_lines': len(events), 'last_event_timestamp': events[-1][1]['timestamp'],
              'initial_segment_start_line': users[0][0], 'initial_segment_end_line_exclusive': cutoff,
              'initial_segment': summarize([(line, event) for line, event in events if line < cutoff]),
              'usage_checkpoints': checkpoints,
              'presentation': {'sha256': hashlib.sha256(presentation_raw).hexdigest(),
                               'file_bytes': len(presentation_raw), 'file_characters': len(content),
                               'event': presentation['event'], 'complete': presentation['complete'],
                               'sources': len(presentation['sources']), 'attachments': len(presentation['attachments']),
                               'issues': len(presentation['issues']), 'markdown_characters': len(presentation['markdown']),
                               'section_body_characters': sum(len(v['body']) for v in presentation['sections']),
                               'source_text_characters': sum(len(v.get('text', '')) for v in presentation['sources']),
                               'prose_text_characters': sum(len(v.get('text', '')) for v in presentation['sources'] if v.get('reason', '').startswith('prosa fuera')),
                               'source_reason_counts': dict(reasons),
                               'attachment_observation_required': sum(bool(v.get('requires_observation')) for v in presentation['attachments']),
                               'serialized_field_characters': {key: len(json.dumps(value, ensure_ascii=False)) for key, value in presentation.items()}},
              'limitations': [
                  'Tool result_token_count measures emitted tool results, not total model input, billing or generated output.',
                  'Usage checkpoints describe call snapshots. They are not summed as total session consumption.',
                  'View categories use path heuristics and do not prove each read was unnecessary.',
                  'Tool durations can include human waiting. Summing them does not measure model compute time.',
                  'The 39.6 MiB presentation was truncated by the tool host; full file size is not model tokens.',
                  'No real consumer files were changed and no logged command was executed.']}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'initial_segment': report['initial_segment'],
                      'first_checkpoint': checkpoints[0], 'presentation': report['presentation']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
