"""Adversarial sensitivity of metadata-dependent selection, not production gates.

Mutations deliberately violate assumptions. Some would be caught by upstream
schema validation in a real integration; this harness does not model that gate.
Gold decides mutation targets but is never supplied to the selector.
"""
import copy,json,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];E=S/'selection-experiment'
source=(S/'tools'/'selection_revision.py').read_text(encoding='utf-8')
namespace={'__name__':'stress_import','__file__':str(S/'tools'/'selection_revision.py')}
exec(compile(source.split('\ncases=json.loads')[0],str(S/'tools'/'selection_revision.py'),'exec'),namespace)
select=namespace['select']
cases=json.loads((S/'cases'/'inputs.json').read_text(encoding='utf-8'))
gold={c['id']:c for c in json.loads((S/'cases'/'oracle.json').read_text(encoding='utf-8'))}
rows=[];texts=[]
for original in cases:
    g=gold[original['id']];required=set(g['required_ids'])
    for variant in ['all_states_active','remove_links','wrong_leaf_scope','missing_unindexed_fragment','sibling_scope_noise']:
        c=copy.deepcopy(original);removed=[];target=None;expected=g['expected_status']
        if variant=='all_states_active':
            for f in c['fragments']:f['state']='active'
        elif variant=='remove_links':
            for f in c['fragments']:f['links']=[]
        elif variant in {'wrong_leaf_scope','missing_unindexed_fragment'}:
            candidates=[f for f in c['fragments'] if f['id'] in required and f['id'] not in c['root_ids'] and f['kind'] in {'requirement','interface','consumer_contract','global_constraint','exception'}]
            if not candidates:continue
            target=candidates[-1]['id']
            if variant=='wrong_leaf_scope':candidates[-1]['scope']='unrelated.legacy'
            else:
                c['fragments']=[f for f in c['fragments'] if f['id']!=target]
                removed=[target];expected='needs_context'
        else:
            domain=c['affected_scopes'][0].split('.')[0]
            for i in range(60):
                c['fragments'].append(dict(id=f'NOISE-{i:03}',kind='requirement',scope=f'{domain}.unrelated_feature_{i}',state='active',links=[],text=f'La herramienta auxiliar {i} presenta su índice de documentos por título y permite filtrar por etiqueta {i}. Este ámbito independiente no participa en la tarea objetivo.'))
        result=select(c);selected=set(result['selected_ids']);missing=required-selected
        ident=f"{original['id']}:{variant}"
        rows.append(dict(case=original['id'],variant=variant,target=target,expected_status=expected,status=result['status'],
            complete=not missing,missing_ids=sorted(missing),false_ready=result['status']=='ready' and (bool(missing) or expected=='needs_context'),
            unnecessary_abstention=result['status']=='needs_context' and expected=='ready',selected_fragments=len(selected),total_fragments=len(c['fragments'])))
        texts.append({'id':ident,'text':result['text']})
counts=json.loads(subprocess.run(['node',str(S/'tools'/'count_tokens.cjs')],input=json.dumps(texts),text=True,encoding='utf-8',capture_output=True,check=True).stdout)
countmap={r['id']:r for r in counts}
base={r['id']:r for r in json.loads((E/'token-counts-v2.json').read_text(encoding='utf-8'))}
for r in rows:
    r['o200k_base']=countmap[r['case']+':'+r['variant']]['o200k_base']
    r['growth_vs_v2']=r['o200k_base']/base[r['case']+':proposal_v2']['o200k_base']
summary=[]
for v in sorted({r['variant'] for r in rows}):
    rs=[r for r in rows if r['variant']==v]
    summary.append(dict(variant=v,cases=len(rs),complete=sum(r['complete'] for r in rs),false_ready=sum(r['false_ready'] for r in rs),
        unnecessary_abstention=sum(r['unnecessary_abstention'] for r in rs),max_token_growth=max(r['growth_vs_v2'] for r in rs),
        total_tokens=sum(r['o200k_base'] for r in rs)))
(E/'stress-results.json').write_text(json.dumps({'limitation':__doc__,'summary':summary,'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
