"""Proposed input-integrity guard, isolated study code; not plugin implementation.

Checks structural contradictions before selection. Does not prove semantic scopes
correct or detect source files that an untrusted inventory silently omits.
"""
import copy,json
from pathlib import Path
S=Path(__file__).resolve().parents[1]
SOFT={'informative','supersedes','references','example','history','navigation'}
INACTIVE={'historical','superseded','inactive','cancelled','rejected','obsolete','retired'}

def validate(case):
    errors=[];nodes={}
    for f in case['fragments']:
        if f['id'] in nodes:errors.append('duplicate-id:'+f['id'])
        nodes[f['id']]=f
    required=set(case['root_ids']);todo=list(required);seen=set()
    while todo:
        i=todo.pop()
        if i in seen:continue
        seen.add(i)
        if i not in nodes:errors.append('missing-required:'+i);continue
        f=nodes[i]
        if f['state'] in INACTIVE:errors.append('inactive-required:'+i)
        if f['kind'] in {'memory','history','example','proposal'}:errors.append('non-authoritative-required:'+i)
        for e in f['links']:
            if e['type'] not in SOFT:todo.append(e['target'])
    return errors

if __name__=='__main__':
    base={'id':'guard-only','task':'synthetic','affected_scopes':['domain.operation'],'root_ids':['T'],
        'fragments':[{'id':'T','kind':'task','state':'active','scope':'domain.operation','text':'Task','links':[{'target':'R','type':'requires'}]},
                     {'id':'R','kind':'requirement','state':'active','scope':'domain.operation','text':'Required rule','links':[]}]}
    tests=[]
    def check(name,c,expected):
        errors=validate(c);ok=bool(errors)==expected
        tests.append({'name':name,'errors':errors,'passed':ok});assert ok,(name,errors)
    check('valid',copy.deepcopy(base),False)
    c=copy.deepcopy(base);c['fragments'][0]['state']='historical';check('inactive-root',c,True)
    c=copy.deepcopy(base);c['fragments'][1]['state']='superseded';check('inactive-required-edge',c,True)
    c=copy.deepcopy(base);c['fragments'][0]['kind']='memory';check('memory-root',c,True)
    c=copy.deepcopy(base);c['fragments'].append(copy.deepcopy(c['fragments'][1]));check('duplicate-id',c,True)
    c=copy.deepcopy(base);c['fragments'].pop();check('missing-required',c,True)
    c=copy.deepcopy(base);c['fragments'][1]['links']=[{'target':'T','type':'requires'}];check('cycle-terminates',c,False)
    c=copy.deepcopy(base);c['fragments'][1]['links']=[{'target':'OLD','type':'supersedes'}];check('history-reference-not-required',c,False)
    (S/'selection-experiment'/'integrity-guard-tests.json').write_text(json.dumps({'status':'prototype-study-only','tests':tests},indent=2),encoding='utf-8')
    print(json.dumps({'passed':sum(t['passed'] for t in tests),'total':len(tests)}))
