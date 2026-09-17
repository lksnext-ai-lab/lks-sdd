"""Independent executable assertions. Frozen before candidate generation.

These are contract microtests, not a production code-quality certification.
Run each candidate in a separate process via this script. Standard library only.
"""
import copy,hashlib,hmac,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
results=[]

def equal(actual,expected):
    assert actual==expected,f'expected {expected!r}; got {actual!r}'

def raises(exc, fn, *args):
    try: fn(*args)
    except exc: return
    except Exception as e: raise AssertionError(f'expected {exc.__name__}, got {type(e).__name__}')
    raise AssertionError(f'expected {exc.__name__}, no error')

def check(case,name,fn):
    try:
        fn()
        results.append(dict(case=case,test=name,passed=True))
    except Exception as e:
        results.append(dict(case=case,test=name,passed=False,error=f'{type(e).__name__}: {e}'))

def run(m):
    for name,amounts,want in [
        ('empty',[],'0.00'),('ordinary',['1.20','2.30'],'3.50'),
        ('per-line-half',['0.005','0.005'],'0.02'),
        ('negative-half',['-0.005','-0.005'],'-0.02'),
        ('mixed',['100.005','-0.005'],'100.00'),
        ('negative-zero',['-0.001'],'0.00'),
        ('decimal-not-binary',['2.675'],'2.68'),
        ('large-exact',['9007199254740992.01','0.02'],'9007199254740992.03')]:
        check('C01',name,lambda a=amounts,w=want:equal(m.ledger_total(a),w))
    def c01_mutation():
        a=['0.005','1']; b=a.copy(); m.ledger_total(a); equal(a,b)
    check('C01','immutability',c01_mutation)

    events=[{'id':'before','timestamp':'2026-03-28T22:59:59Z'},
            {'id':'start','timestamp':'2026-03-28T23:00:00Z'},
            {'id':'last','timestamp':'2026-03-29T21:59:59Z'},
            {'id':'end','timestamp':'2026-03-29T22:00:00Z'}]
    check('C02','spring-23h',lambda:equal(m.local_day_ids(events,'2026-03-29','Europe/Madrid'),['start','last']))
    autumn=[{'id':'first','timestamp':'2026-10-25T00:30:00Z'},
            {'id':'second','timestamp':'2026-10-25T01:30:00Z'},
            {'id':'last','timestamp':'2026-10-25T22:59:59Z'},
            {'id':'end','timestamp':'2026-10-25T23:00:00Z'}]
    check('C02','autumn-25h',lambda:equal(m.local_day_ids(autumn,'2026-10-25','Europe/Madrid'),['first','second','last']))
    check('C02','empty',lambda:equal(m.local_day_ids([],'2026-01-01','UTC'),[]))
    check('C02','offset',lambda:equal(m.local_day_ids([{'id':1,'timestamp':'2026-01-02T01:00:00+02:00'}],'2026-01-01','UTC'),[1]))
    check('C02','naive-rejected',lambda:raises(ValueError,m.local_day_ids,[{'id':1,'timestamp':'2020-01-01T12:00:00'}],'2026-01-01','UTC'))
    def c02_mutation():
        a=copy.deepcopy(events); m.local_day_ids(a,'2026-03-29','Europe/Madrid');equal(a,events)
    check('C02','immutability',c02_mutation)

    def event(tenant='a',key='k',seq=1,eid='e1',value='v1',deleted=False):
        return dict(tenant=tenant,key=key,seq=seq,event_id=eid,value=value,deleted=deleted)
    old=event(); new=event(seq=2,eid='e2',value='v2'); tomb=event(seq=3,eid='e3',deleted=True)
    for name,events,want in [
        ('empty',[],{}),('single',[old],{('a','k'):'v1'}),
        ('order-independent',[new,old],{('a','k'):'v2'}),
        ('tombstone-no-resurrection',[tomb,old,new],{}),
        ('resurrect-newer',[tomb,event(seq=4,eid='e4',value='v4')],{('a','k'):'v4'}),
        ('duplicate',[old,copy.deepcopy(old)],{('a','k'):'v1'}),
        ('tenant-local-event-id',[old,event(tenant='b',value='other')],{('a','k'):'v1',('b','k'):'other'})]:
        check('C03',name,lambda a=events,w=want:equal(m.fold_events(a),w))
    check('C03','same-id-different-payload',lambda:raises(ValueError,m.fold_events,[old,event(value='changed')]))
    check('C03','same-seq-different-id',lambda:raises(ValueError,m.fold_events,[old,event(eid='e-other')]))
    check('C03','stale-conflict-still-error',lambda:raises(ValueError,m.fold_events,[new,old,event(eid='e-other')]))
    def c03_mutation():
        a=[copy.deepcopy(old),copy.deepcopy(new)]; b=copy.deepcopy(a);m.fold_events(a);equal(a,b)
    check('C03','immutability',c03_mutation)

    user=dict(id='u',tenant='a',roles=[],disabled=False)
    resource=dict(tenant='a',owner_id='x',public=False,denied_user_ids=[])
    access=[('default-deny',{}, {},False),('owner',{}, {'owner_id':'u'},True),
        ('public',{}, {'public':True},True),('admin',{'roles':['admin']},{},True),
        ('disabled-admin',{'disabled':True,'roles':['admin']},{'public':True,'owner_id':'u'},False),
        ('tenant-admin',{'roles':['admin']},{'tenant':'b'},False),
        ('tenant-public',{}, {'tenant':'b','public':True},False),
        ('explicit-deny-admin',{'roles':['admin']},{'denied_user_ids':['u']},False),
        ('explicit-deny-owner',{}, {'owner_id':'u','denied_user_ids':['u']},False),
        ('other-deny',{}, {'owner_id':'u','denied_user_ids':['z']},True)]
    for name,u,r,want in access:
        check('C04',name,lambda u=u,r=r,w=want:equal(m.can_read(user|u,resource|r),w))
    def c04_mutation():
        u=copy.deepcopy(user);r=copy.deepcopy(resource);m.can_read(u,r);equal((u,r),(user,resource))
    check('C04','immutability',c04_mutation)

    patches=[('replace-scalar',{'a':1},3,3),('replace-null',{'a':1},None,None),
        ('delete-key',{'a':1,'b':2},{'a':None},{'b':2}),
        ('recursive',{'a':{'b':1,'c':2}},{'a':{'b':None,'d':3}},{'a':{'c':2,'d':3}}),
        ('arrays-replace',{'a':[1,2]},{'a':[3]},{'a':[3]}),
        ('scalar-to-object',5,{'a':1},{'a':1}),
        ('remove-missing',{}, {'a':None},{}),('replace-list',{},[1,{'a':2}],[1,{'a':2}])]
    for name,doc,patch,want in patches:
        check('C05',name,lambda d=doc,p=patch,w=want:equal(m.merge_patch(d,p),w))
    def c05_alias():
        d={'keep':[{'a':1}],'edit':{'v':1}};p={'edit':{'new':[2]}}
        d0=copy.deepcopy(d);p0=copy.deepcopy(p);o=m.merge_patch(d,p)
        o['keep'][0]['a']=9;o['edit']['new'].append(3)
        equal(d,d0);equal(p,p0)
    check('C05','no-alias-or-mutation',c05_alias)

    rows=[dict(id=3,ts='2026-01-01T00:00:00Z',data=[3]),dict(id=1,ts='2026-01-01T00:00:00Z',data=[1]),dict(id=2,ts='2026-01-01T00:00:00Z',data=[2]),dict(id=4,ts='2026-01-02T00:00:00Z',data=[4])]
    check('C06','stable-tie',lambda:equal([r['id'] for r in m.page_after(rows,('2026-01-01T00:00:00Z',1),10)],[2,3,4]))
    check('C06','limit',lambda:equal([r['id'] for r in m.page_after(rows,None,2)],[1,2]))
    check('C06','zero',lambda:equal(m.page_after(rows,None,0),[]))
    check('C06','negative',lambda:raises(ValueError,m.page_after,rows,None,-1))
    check('C06','after-end',lambda:equal(m.page_after(rows,('2027-01-01T00:00:00Z',0),5),[]))
    def c06_alias():
        a=copy.deepcopy(rows);o=m.page_after(a,None,1);o[0]['data'].append(9);equal(a,rows)
    check('C06','no-alias-or-mutation',c06_alias)

    now=datetime(2026,9,11,12,0,0,500000,tzinfo=timezone.utc)
    retries=[('none',None,100,None),('seconds',' 12 ',100,12),('zero','0',100,0),
       ('cap','999',20,20),('decimal','1.5',100,None),('negative','-2',100,None),
       ('plus','+3',100,None),('non-ascii','٣',100,None),('garbage','later',100,None),
       ('future-ceil','Fri, 11 Sep 2026 12:00:02 GMT',100,2),
       ('past','Fri, 11 Sep 2026 11:00:00 GMT',100,0),
       ('future-cap','Fri, 11 Sep 2026 12:01:00 GMT',10,10),
       ('no-zone','Fri, 11 Sep 2026 12:01:00',100,None),
       ('wrong-zone','Fri, 11 Sep 2026 12:01:00 +0200',100,None)]
    for name,value,cap,want in retries:
        check('C07',name,lambda v=value,c=cap,w=want:equal(m.retry_delay(v,now,c),w))

    cells=[('none',None,''),('int',-12,'-12'),('float',-1.5,'-1.5'),
        ('plain','hello','hello'),('formula','=1+2',"'=1+2"),
        ('leading',' \t=cmd',"' \t=cmd"),('negative-string','-12',"'-12"),
        ('at','\r\n@SUM(A1)',"'\r\n@SUM(A1)"),('plus','+1',"'+1"),
        ('empty','',''),('space-only',' \t',' \t'),('comma','a,b','a,b'),
        ('not-leading','x=1','x=1'),('existing-quote',"'=x","'=x")]
    for name,value,want in cells:
        check('C08',name,lambda v=value,w=want:equal(m.csv_cell(v),w))

    steps=[{'id':'c','depends_on':['a']},{'id':'b','depends_on':[]},{'id':'a','depends_on':[]}]
    check('C09','lex-every-step',lambda:equal(m.migration_order(steps,[]),['a','b','c']))
    check('C09','new-ready-before-old',lambda:equal(m.migration_order([{'id':'z','depends_on':[]},{'id':'b','depends_on':[]},{'id':'a','depends_on':['b']}],[]),['b','a','z']))
    check('C09','external-applied',lambda:equal(m.migration_order([{'id':'b','depends_on':['a']}],['a']),['b']))
    check('C09','ignore-applied-deps',lambda:equal(m.migration_order([{'id':'a','depends_on':['missing']},{'id':'b','depends_on':['a']}],['a']),['b']))
    check('C09','missing',lambda:raises(ValueError,m.migration_order,[{'id':'b','depends_on':['x']}],[]))
    check('C09','duplicate',lambda:raises(ValueError,m.migration_order,[{'id':'a','depends_on':[]},{'id':'a','depends_on':[]}],[]))
    check('C09','cycle',lambda:raises(ValueError,m.migration_order,[{'id':'a','depends_on':['b']},{'id':'b','depends_on':['a']}],[]))
    check('C09','empty',lambda:equal(m.migration_order([],[]),[]))
    def c09_mutation():
        a=copy.deepcopy(steps);m.migration_order(a,[]);equal(a,steps)
    check('C09','immutability',c09_mutation)

    keys=[('ordinary','a','u',['write','read','read'],'["a","u",["read","write"]]'),
          ('unicode','ñ','É',['α'],'["ñ","É",["α"]]'),
          ('separators','a:b','c',['x,y'],'["a:b","c",["x,y"]]'),
          ('empty','','',[],'["","",[]]')]
    for name,t,u,sc,w in keys:
        check('C10',name,lambda t=t,u=u,s=sc,w=w:equal(m.cache_key(t,u,s),w))
    check('C10','scope-order',lambda:equal(m.cache_key('a','u',['b','a','a']),m.cache_key('a','u',['a','b'])))
    def c10_distinct():
        assert m.cache_key('é','u',[])!=m.cache_key('e\u0301','u',[])
        assert m.cache_key('a:b','c',[])!=m.cache_key('a','b:c',[])
        assert m.cache_key('A','u',[])!=m.cache_key('a','u',[])
    check('C10','no-normalization-collisions',c10_distinct)
    def c10_mutation():
        s=['b','a','a'];m.cache_key('a','u',s);equal(s,['b','a','a'])
    check('C10','immutability',c10_mutation)

    record={'id':'i','tenant':'t','version':3,'v':1,'keep':[1]}
    check('C11','increment',lambda:equal(m.update_record(record,3,{'v':2}),record|{'version':4,'v':2}))
    check('C11','same-value-increments',lambda:equal(m.update_record(record,3,{'v':1}),record|{'version':4}))
    check('C11','empty-no-increment',lambda:equal(m.update_record(record,3,{}),record))
    check('C11','empty-stale',lambda:raises(RuntimeError,m.update_record,record,2,{}))
    for field in ['id','tenant','version']:
        check('C11','immutable-'+field,lambda f=field:raises(ValueError,m.update_record,record,3,{f:record[f]}))
    check('C11','version-precedence',lambda:raises(RuntimeError,m.update_record,record,2,{'id':'x'}))
    def c11_alias():
        r=copy.deepcopy(record);c={'v':[2]};o=m.update_record(r,3,c);o['keep'].append(9);o['v'].append(9);equal(r,record);equal(c,{'v':[2]})
    check('C11','no-alias-or-mutation',c11_alias)

    secret=b'synthetic-test-key';body=b'{ "a": 1 }';nowsec=10000
    def sig(ts,payload=body):
        return 'sha256='+hmac.new(secret,ts.encode('ascii')+b'.'+payload,hashlib.sha256).hexdigest()
    for name,delta,want in [('fresh',0,True),('past-limit',-300,True),('past-out',-301,False),('future-limit',30,True),('future-out',31,False)]:
        ts=str(nowsec+delta)
        check('C12',name,lambda ts=ts,w=want:equal(m.verify_signature(body,sig(ts),ts,nowsec,secret),w))
    check('C12','body-byte-exact',lambda:equal(m.verify_signature(b'{"a":1}',sig('10000'),'10000',nowsec,secret),False))
    check('C12','upper-hex',lambda:equal(m.verify_signature(body,sig('10000').upper(),'10000',nowsec,secret),False))
    check('C12','wrong-prefix',lambda:equal(m.verify_signature(body,sig('10000').replace('sha256=','sha1='),'10000',nowsec,secret),False))
    check('C12','wrong-signature',lambda:equal(m.verify_signature(body,'sha256='+'0'*64,'10000',nowsec,secret),False))
    for invalid in ['','+10000','-10000','10000.0',' 10000','١٠٠٠٠']:
        check('C12','invalid-ts-'+repr(invalid),lambda ts=invalid:equal(m.verify_signature(body,'sha256='+'0'*64,ts,nowsec,secret),False))
    check('C12','leading-zero-ts-exact',lambda:equal(m.verify_signature(body,sig('010000'),'010000',nowsec,secret),True))

if __name__=='__main__':
    p=Path(sys.argv[1]).resolve();spec=importlib.util.spec_from_file_location('candidate',p);m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    run(m)
    cases={c:{'passed':sum(r['passed'] for r in results if r['case']==c),'total':sum(r['case']==c for r in results)} for c in sorted({r['case'] for r in results})}
    payload={'candidate':p.name,'candidate_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'oracle_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'passed':sum(r['passed'] for r in results),'total':len(results),'all_cases_passed':sum(v['passed']==v['total'] for v in cases.values()),'cases':cases,'results':results}
    output=HERE/f'results-{p.stem}.json';output.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in payload.items() if k!='results'},ensure_ascii=False))
