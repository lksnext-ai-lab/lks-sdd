"""Transparent selection simulation; not a language-model coding benchmark.

Selectors receive INPUTS ONLY. Oracles are read after all selections are written.
The synthetic metadata is an assumption, not a demonstrated prose classifier.
"""
import hashlib,json,re,subprocess
from collections import deque
from pathlib import Path
S=Path(__file__).resolve().parents[1]
E=S/'selection-experiment'
E.mkdir(exist_ok=True)
INFO={'informative','informational','example','background','history','historical','reference','navigation'}
INACTIVE={'historical','superseded','inactive','cancelled','rejected','obsolete'}
PENDING={'pending','unresolved','conflicting','ambiguous','missing','stale','unverified'}
SOFT_LINKS={'mentions','reference','informative','example','history','navigation','related','background'}

def relevant(f,scopes):
    s=f.get('scope','global')
    ss=set(s) if isinstance(s,list) else {s}
    return bool(ss & (set(scopes)|{'global','*','project'}))

def selected_context(case,strategy):
    nodes={f['id']:f for f in case['fragments']}
    roots=set(case['root_ids']);scopes=case.get('affected_scopes',[])
    chosen=set();missing=set()
    def visit(seeds,typed=False):
        q=deque(seeds)
        while q:
            ident=q.popleft()
            if ident in chosen:continue
            if ident not in nodes:missing.add(ident);continue
            f=nodes[ident]
            if typed and f.get('state') in INACTIVE:continue
            chosen.add(ident)
            for edge in f.get('links',[]):
                if not typed or edge.get('type','requires') not in SOFT_LINKS:
                    q.append(edge['target'])
    if strategy=='full':
        chosen=set(nodes)
    elif strategy=='roots_only':
        chosen=roots & set(nodes);missing=roots-set(nodes)
    elif strategy=='explicit_graph':
        visit(roots)
    elif strategy in {'proposal_v1','proposal_v2'}:
        seeds=roots|{f['id'] for f in nodes.values() if relevant(f,scopes) and f.get('kind','unknown') not in INFO and f.get('state') not in INACTIVE}
        visit(seeds,typed=True)
        # Reverse mandatory dependencies/detail rows; informational inbound links do not expand.
        while True:
            reverse={f['id'] for f in nodes.values() if relevant(f,scopes) and f.get('state') not in INACTIVE and any(e['target'] in chosen and e.get('type','requires') not in SOFT_LINKS for e in f.get('links',[]))}
            before=len(chosen);visit(reverse,typed=True)
            if len(chosen)==before:break
    else:raise ValueError(strategy)
    problems=[]
    if strategy in {'proposal_v1','proposal_v2'}:
        problems += ['missing-reference:'+x for x in sorted(missing)]
        problems += ['uncertain-state:'+x for x in sorted(chosen) if nodes[x].get('state') in PENDING]
    # V2 policy initially unimplemented: experiment will register improvements on dev cases.
    text='\n\n'.join(f"[{f['id']}; {f.get('kind','unknown')}; {f.get('state','unknown')}]\n{f['text']}" for f in case['fragments'] if f['id'] in chosen)
    return {'case':case['id'],'strategy':strategy,'selected_ids':sorted(chosen),'missing_references':sorted(missing),'status':'needs_context' if problems else 'ready','problems':problems,'text':str(case['task'])+'\n\n'+text}

def run():
    payload=json.loads((S/'cases'/'inputs.json').read_text(encoding='utf-8'))
    cases=payload if isinstance(payload,list) else payload['cases']
    strategies=['full','roots_only','explicit_graph','proposal_v1']
    outputs=[selected_context(c,s) for c in cases for s in strategies]
    # Freeze pre-oracle artifact. Later scoring cannot change selections.
    (E/'selections-v1.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2),encoding='utf-8')
    receipt={'selector_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'inputs_sha256':hashlib.sha256((S/'cases'/'inputs.json').read_bytes()).hexdigest(),
        'split_rule':'case numeric suffix divisible by 3 is held-out; others development; declared before reading oracle',
        'strategies':strategies,'case_count':len(cases)}
    (E/'freeze-v1.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    counts=json.loads(subprocess.run(['node',str(S/'tools'/'count_tokens.cjs')],input=json.dumps([{'id':f"{o['case']}:{o['strategy']}",'text':o['text']} for o in outputs]),capture_output=True,text=True,encoding='utf-8',check=True).stdout)
    (E/'token-counts-v1.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
    print(json.dumps(receipt))

if __name__=='__main__':run()
