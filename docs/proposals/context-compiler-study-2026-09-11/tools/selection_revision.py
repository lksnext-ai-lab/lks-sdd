"""Dev-informed conservative revision. No oracle access; preserves v1 verbatim.

Changes: expand impacts across consumers and domain scopes; reinclude rules in
newly discovered scopes; separate stale derived memory from normative state;
unknown/incomplete authoritative state blocks execution. Broad domain expansion
is deliberately conservative and NOT a production-quality applicability engine.
"""
import collections,hashlib,json,math,re,subprocess
from pathlib import Path
from selection_experiment import S,E,INFO,INACTIVE,SOFT_LINKS

SKIP=INACTIVE|{'retired'}
NON_AUTH={'memory','history','example','proposal'}
OK={'active','confirmed','approved','verified','untrusted'}

def render(c,chosen):
    return str(c['task'])+'\n\n'+'\n\n'.join(f"[{f['id']}; {f.get('kind','unknown')}; {f.get('state','unknown')}]\n{f['text']}" for f in c['fragments'] if f['id'] in chosen)

def select(c):
    nodes={f['id']:f for f in c['fragments']};chosen=set();missing=set();scopes=set(c['affected_scopes'])
    def eligible(f):return f['state'] not in SKIP and f['kind'] not in NON_AUTH and f['kind'] not in INFO
    def expand(ids):
        q=collections.deque(ids)
        while q:
            i=q.popleft()
            if i in chosen:continue
            if i not in nodes:missing.add(i);continue
            f=nodes[i]
            if not eligible(f):continue
            chosen.add(i);scopes.add(f['scope'])
            for edge in f['links']:
                if edge['type'] not in SOFT_LINKS|{'supersedes'}:q.append(edge['target'])
    expand(c['root_ids'])
    while True:
        before=(len(chosen),len(scopes))
        domains={s.split('.')[0] for s in scopes if s not in {'global','*','project'}}
        seeds=[]
        for f in c['fragments']:
            if not eligible(f):continue
            direct=f['scope'] in scopes|{'global','*','project'}
            family=f['scope'].split('.')[0] in domains
            reverse=any(e['target'] in chosen and e['type'] not in SOFT_LINKS|{'supersedes'} for e in f['links'])
            if direct or family or reverse:seeds.append(f['id'])
        expand(seeds)
        if before==(len(chosen),len(scopes)):break
    problems=['missing-reference:'+i for i in sorted(missing)]
    for i in sorted(chosen):
        f=nodes[i]
        if f['state'] not in OK and f['kind']!='untrusted_evidence':problems.append('uncertain-authoritative-state:'+i)
    return dict(case=c['id'],strategy='proposal_v2',selected_ids=sorted(chosen),missing_references=sorted(missing),status='needs_context' if problems else 'ready',problems=problems,text=render(c,chosen))

def terms(t):return re.findall(r'[\w]+',t.casefold())

def lexical(c):
    docs=[terms(f['text']) for f in c['fragments']];N=len(docs);av=sum(map(len,docs))/N
    df=collections.Counter(t for d in docs for t in set(d));query=set(terms(c['task']))
    ranked=[]
    for f,d in zip(c['fragments'],docs):
        tf=collections.Counter(d);score=0
        for t in query:
            freq=tf[t]
            score+=math.log(1+(N-df[t]+.5)/(df[t]+.5))*freq*2.5/(freq+1.5*(.25+.75*len(d)/av)) if freq else 0
        ranked.append((score,f['id']))
    chosen=set(c['root_ids'])|{i for _,i in sorted(ranked,reverse=True)[:4]}
    return dict(case=c['id'],strategy='bm25_top4',selected_ids=sorted(chosen),missing_references=[],status='ready',problems=[],text=render(c,chosen))

cases=json.loads((S/'cases'/'inputs.json').read_text(encoding='utf-8'))
outputs=[f(c) for c in cases for f in (select,lexical)]
(E/'selections-v2.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2),encoding='utf-8')
receipt={'selector_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'inputs_sha256':hashlib.sha256((S/'cases'/'inputs.json').read_bytes()).hexdigest(),
 'development_inputs_examined':['CC-014','CC-016','CC-017','CC-019','CC-034','CC-035'],
 'holdout_caveat':'V1 aggregate holdout metrics and metadata enum counts were visible; no holdout case contents or oracle details were inspected for this revision. Not an independently sealed benchmark.',
 'states_require_external_classification':True}
(E/'freeze-v2.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
counts=json.loads(subprocess.run(['node',str(S/'tools'/'count_tokens.cjs')],input=json.dumps([{'id':f"{o['case']}:{o['strategy']}",'text':o['text']} for o in outputs]),capture_output=True,text=True,encoding='utf-8',check=True).stdout)
(E/'token-counts-v2.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
print(json.dumps(receipt))
