"""Score already-frozen selections; cannot change selection or access model internals."""
import hashlib,json,re,statistics,sys
from pathlib import Path
S=Path(__file__).resolve().parents[1]
E=S/'selection-experiment'
version=sys.argv[1] if len(sys.argv)>1 else 'v1'
raw=json.loads((S/'cases'/'oracle.json').read_text(encoding='utf-8'))
gold={c['id']:c for c in (raw if isinstance(raw,list) else raw['cases'])}
selections=json.loads((E/f'selections-{version}.json').read_text(encoding='utf-8'))
tokens={r['id']:r for r in json.loads((E/f'token-counts-{version}.json').read_text(encoding='utf-8'))}
rows=[]
for s in selections:
    oracle=gold[s['case']];required=set(oracle['required_ids']);selected=set(s['selected_ids'])
    missing=sorted(required-selected)
    split='holdout' if int(re.search(r'(\d+)$',s['case']).group())%3==0 else 'development'
    baseline=tokens.get(s['case']+':full')
    if baseline is None:
        old={r['id']:r for r in json.loads((E/'token-counts-v1.json').read_text(encoding='utf-8'))}
        baseline=old[s['case']+':full']
    row={k:s[k] for k in ['case','strategy','status','problems']}
    row.update(split=split,expected_status=oracle['expected_status'],required=len(required),covered=len(required&selected),missing_ids=missing,
        coverage_complete=not missing,precision=len(required&selected)/max(1,len(selected)),
        false_ready=s['status']=='ready' and (bool(missing) or oracle['expected_status']=='needs_context'),
        unnecessary_abstention=s['status']=='needs_context' and oracle['expected_status']=='ready',
        correctly_executable=s['status']=='ready' and oracle['expected_status']=='ready' and not missing,
        o200k_base=tokens[s['case']+':'+s['strategy']]['o200k_base'],
        saving_vs_full=1-tokens[s['case']+':'+s['strategy']]['o200k_base']/baseline['o200k_base'])
    rows.append(row)
summary=[]
for strat in sorted({r['strategy'] for r in rows}):
    for split in ['all','development','holdout']:
        rs=[r for r in rows if r['strategy']==strat and (split=='all' or r['split']==split)]
        summary.append(dict(strategy=strat,split=split,cases=len(rs),complete=sum(r['coverage_complete'] for r in rs),
            false_ready=sum(r['false_ready'] for r in rs),unnecessary_abstention=sum(r['unnecessary_abstention'] for r in rs),
            correctly_executable=sum(r['correctly_executable'] for r in rs),total_reference_tokens=sum(r['o200k_base'] for r in rs),
            median_saving=statistics.median(r['saving_vs_full'] for r in rs),
            weighted_coverage=sum(r['covered'] for r in rs)/sum(r['required'] for r in rs)))
payload={'version':version,'oracle_sha256':hashlib.sha256((S/'cases'/'oracle.json').read_bytes()).hexdigest(),
 'limitation':'False-ready is a deterministic simulator classification, not an observed LLM implementation error. Human-authored metadata and gold. Full baseline lacks readiness guard by design.',
 'summary':summary,'rows':rows}
(E/f'results-{version}.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
