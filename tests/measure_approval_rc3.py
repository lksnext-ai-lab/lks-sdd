"""Sequential three-revision measurements and exact-package full CLI accounting.

No profiles or tests may overlap this coordinator. Reports live outside the
distribution so the measured package can remain byte-for-byte immutable.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import statistics
import stat
import subprocess
import sys
import tempfile
import time

from approval_performance_support import ROOT, stable_generation
from profile_approval_performance import revision

MODULES = ('v3_contract.py','v3_scope.py','v3_approval.py','v3_migration.py','v3_workflow.py','v3_inventories.py',
           'v3_evaluation.py','v2_contract.py','path_utils.py','runtime_doctor.py')
TOOLS = ('approval_performance_support.py','measure_approval_performance.py','measure_approval_rc3.py',
         'profile_approval_performance.py','approval_cli_support.py','approval_command_worker.py',
         'performance_command.py','performance_isolation.py','check_approval_cli_hosts.py')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def binding(package):
    paths = [ROOT/'scripts'/n for n in MODULES] + [ROOT/'tests'/n for n in TOOLS]
    paths += list((ROOT/'tests/fixtures/approval-reference').glob('*'))
    paths += [ROOT/'tests/reports/lks-sdd-3.4.3-rc.2.manifest.json',
              ROOT/'tests/reports/lks-sdd-3.4.3-rc.2-development/lks-sdd-plugin-v3.4.3-rc.2.zip']
    return {'files':{p.relative_to(ROOT).as_posix():sha(p) for p in paths if p.is_file()},
            'package':str(package),'package_sha256':sha(package)}


def semantic(value):
    # Only the diagnostic usage envelope is excluded from business-state equality.
    if isinstance(value,dict): return {k:semantic(v) for k,v in value.items() if k != 'usage'}
    if isinstance(value,list): return [semantic(v) for v in value]
    return value


def written_paths(paths):
    # Physical CAS/history addresses bind each runtime/preview independently.
    # Keep their category and multiplicity, and every canonical element path.
    return sorted(re.sub(r'(?<=objects/sha256/)[0-9a-f]{64}|(?<=history/states/)[0-9a-f]{64}',
                         '<content-address>',p) for p in paths)


def remove_workspace(workspace, parent):
    assert workspace.resolve().parent == parent.resolve()
    def readonly(function, path, error):
        target = Path(path)
        if not target.resolve().is_relative_to(workspace.resolve()): raise error
        target.chmod(stat.S_IWRITE | stat.S_IREAD)
        function(path)
    shutil.rmtree(workspace,onexc=readonly)


def worker(args):
    import measure_approval_performance as measures
    # Identical synthetic fixture construction is outside CLI timings. Only the
    # selected immutable package executes the measured commands.
    with revision('candidate' if args.worker == 'cli' else args.revision):
        stable_generation()
        names = iter('approval%09d'%i for i in range(1000000))
        tempfile.tempdir = str(args.workspace)
        tempfile._get_candidate_names = lambda:names
        args.original = args.revision == 'base'
        measures.PROGRESS = args.progress
        if args.worker == 'cli':
            from approval_cli_support import core_files, setup, journey
            from performance_command import run
            fixture = setup(args.size,args.technologies,core_files(args.revision,args.package if args.revision == 'candidate' else None),args.workspace)
            rows = []
            def invoke(label, arguments):
                value,row = run(arguments,args.workspace,label,timeout=args.timeout)
                row.update(operation=label,result=value)
                rows.append(row)
                with args.progress.open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps({k:row[k] for k in ('operation','seconds','cpu_seconds','job_cpu_seconds')})+'\n')
                return value
            final = journey(fixture,args.workspace,invoke)
            # All raw previews, envelopes and application receipts are retained.
            # Apply validates each packet's own hash and fresh physical sources.
            # Runtime identity, packet hashes and elapsed usage intentionally differ.
            contract = {'final_status':semantic(final['final_status']),
                        'readiness':semantic(next(r['result'] for r in rows if r['operation']=='readiness')),
                        'actions':[(o['action'],o['status']) for o in final['operations']],
                        'command_statuses':[(r['operation'],r['result'].get('status')) for r in rows],
                        'write_paths':[(r['operation'],written_paths(r['result'].get('writes',[]))) for r in rows if r['operation'].endswith(':apply')]}
            result = {'rows':rows,'journey':final,'business_contract':contract,
                      'business_digest':hashlib.sha256(json.dumps(contract,sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
        else:
            result = {'calculations':measures.calculation_worker,'workflow':measures.workflow_worker,
                      'shared-inventories':measures.shared_inventory_worker}[args.worker](args)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def summaries(samples):
    result = []
    for size,phase,rev in sorted({(s['size'],s['phase'],s['revision']) for s in samples}):
        selected = [s for s in samples if (s['size'],s['phase'],s['revision'])==(size,phase,rev)]
        for op in sorted({r['operation'] for s in selected for r in s['rows']}|{'TOTAL'}):
            values = []
            for s in selected:
                rows = s['rows'] if op=='TOTAL' else [r for r in s['rows'] if r['operation']==op]
                if phase == 'cli':
                    item = {'cpu_seconds':sum(r['cpu_seconds'] for r in rows),
                            'job_cpu_seconds':sum(r['job_cpu_seconds'] for r in rows),
                            'seconds':sum(r['seconds'] for r in rows),
                            'job_peak_commit_bytes':max(r['job_peak_commit_bytes'] for r in rows),
                            'observed_main_peak_working_set_bytes':max(r['observed_main_peak_working_set_bytes'] for r in rows)}
                else:
                    item = {'cpu_seconds':sum(r['cpu_seconds'] for r in rows),'seconds':sum(r['seconds'] for r in rows),
                            'process_peak_bytes':max(r['memory_after']['process_peak_bytes'] for r in rows),
                            'sampled_peak_working_set_bytes':max(r['sampled_peak_working_set_bytes'] for r in rows)}
                values.append(item)
            result.append({'size':size,'phase':phase,'revision':rev,'operation':op,'samples':len(values),
                           'metrics':{k:{'median':statistics.median(v[k] for v in values),'min':min(v[k] for v in values),
                                         'max':max(v[k] for v in values)} for k in values[0]}})
    return result


def main(args):
    from performance_isolation import Audit, ConcurrentRunner, Watch
    if sys.platform != 'win32': raise RuntimeError('Native Windows measurements required')
    audit = Audit(); initial = binding(args.package)
    samples, comparisons, excluded, inflight = [], [], [], []
    args.output.parent.mkdir(parents=True,exist_ok=True)
    progress = args.output.with_suffix('.progress.jsonl')
    orders = [('base','rc2','candidate'),('candidate','rc2','base'),('candidate','base','rc2'),('rc2','base','candidate')]
    cases = [(s,t,p) for s,t in ((100,5),(500,15),(1500,35)) for p in ('calculations','workflow')]
    cases += [(1500,35,'shared-inventories'),(1500,35,'cli')]
    if args.smoke: cases = [(40,2,'cli')]; orders = [('rc2','candidate')]
    config={'cases':[list(c) for c in cases],'orders':[list(o) for o in orders],'cooldown':args.cooldown,'timeout':args.timeout}
    if args.resume:
        previous=json.loads(args.output.read_bytes())
        if previous['binding']!=initial or previous['config']!=config: raise RuntimeError('Resume inputs/configuration differ')
        samples,comparisons=previous['samples'],previous['comparisons']
        excluded=previous['excluded_attempts']
        if previous['inflight']:
            excluded.append({'reason':'interrupted-inflight-group','samples':previous['inflight']})
    else:
        if args.output.exists(): raise RuntimeError('Output exists; use --resume with identical inputs')
        progress.write_text('',encoding='utf-8')
    def save():
        payload={'method':'fresh sequential workers; cooldown; no profiling; before/after audits and native 500ms monitor; whole-group retry on isolation failure',
            'binding':initial,'binding_unchanged':binding(args.package)==initial,'config':config,'orders':orders,
            'samples':samples,'comparisons':comparisons,'excluded_attempts':excluded,'inflight':inflight,'summaries':summaries(samples),
            'audit_classifications':audit.classifications,'published':False,'installed':False}
        temporary=args.output.with_suffix('.new')
        temporary.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        for attempt in range(20):
            try: temporary.replace(args.output);break
            except PermissionError:
                if attempt==19:raise
                time.sleep(.1)
    def clean_window(context):
        previous_reason=None
        while True:
            try:return audit.check()
            except (RuntimeError,OSError,subprocess.TimeoutExpired) as error:
                if str(error)!=previous_reason:
                    print(json.dumps({'state':'waiting-for-isolation',**context,'reason':str(error)}),flush=True)
                    previous_reason=str(error)
                time.sleep(10)
    save()
    for size,tech,phase in cases:
        for rep,order in enumerate(orders):
            if any((c['size'],c['phase'],c['repetition'])==(size,phase,rep) for c in comparisons):continue
            selected = tuple(r for r in order if phase!='cli' or r!='base')
            attempt=0
            while True:
                attempt+=1; inflight=[]; contaminated=False
                with tempfile.TemporaryDirectory(prefix='approval-rc3-pair-') as temp:
                    parent=Path(temp).resolve()
                    for rev in selected:
                        context={'size':size,'phase':phase,'repetition':rep,'revision':rev,'attempt':attempt}
                        clean_window(context);time.sleep(args.cooldown)
                        before=clean_window(context)
                        workspace=parent/'workspace';workspace.mkdir();output=parent/'sample.json'
                        command=[sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--worker',phase,
                                 '--revision',rev,'--workspace',str(workspace),'--size',str(size),'--technologies',str(tech),
                                 '--output',str(output),'--package',str(args.package),'--progress',str(progress),'--timeout',str(args.timeout)]
                        started=time.perf_counter()
                        child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',
                                               env={**os.environ,'PYTHONHASHSEED':'0'})
                        watcher=Watch(audit,child.pid);watcher.start()
                        try:stdout,stderr=child.communicate(timeout=args.timeout)
                        except subprocess.TimeoutExpired:
                            child.kill();child.wait();raise
                        finally:observations=watcher.close()
                        elapsed=time.perf_counter()-started
                        if child.returncode:raise RuntimeError(stdout[-1000:]+stderr[-12000:])
                        result=json.loads(output.read_bytes())
                        try:after=audit.check()
                        except (RuntimeError,OSError,subprocess.TimeoutExpired) as error:after={'isolation_failure':str(error)}
                        contaminated=bool(observations['unowned_new_identities'] or observations['errors'] or after.get('isolation_failure'))
                        sample={**context,'technologies':tech,'worker_seconds':elapsed,
                                'isolation':{'before':before,'after':after,'during':observations},**result}
                        inflight.append(sample)
                        save();remove_workspace(workspace,parent)
                        print(json.dumps({**context,'worker_seconds':elapsed,'isolated':not contaminated}),flush=True)
                        if contaminated:break
                if contaminated:
                    excluded.append({'reason':'isolation-failure; repeat entire ordered group','samples':inflight})
                    inflight=[];save();continue
                candidate=next(s for s in inflight if s['revision']=='candidate')
                checked=[]
                for ref in (s for s in inflight if s['revision']!='candidate'):
                    equal=ref['business_digest']==candidate['business_digest'] if phase=='cli' else (
                        [(r['operation'],r['semantic_digest']) for r in ref['rows']]==[(r['operation'],r['semantic_digest']) for r in candidate['rows']])
                    checked.append({'size':size,'phase':phase,'repetition':rep,'reference':ref['revision'],'equivalent':equal,
                                    'scope':'business state/readiness/actions/statuses/write paths; own runtime-bound packets validated' if phase=='cli' else 'exact complete semantic digests'})
                if not all(c['equivalent'] for c in checked):
                    save()
                    raise AssertionError('Semantic comparison failed; complete raw samples preserved')
                samples.extend(inflight);comparisons.extend(checked);inflight=[];save();break
    assert binding(args.package)==initial, 'Measured inputs changed'
    save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',choices=['calculations','workflow','shared-inventories','cli'])
    parser.add_argument('--revision',choices=['base','rc2','candidate'])
    parser.add_argument('--workspace',type=Path)
    parser.add_argument('--size',type=int,default=1500)
    parser.add_argument('--technologies',type=int,default=35)
    parser.add_argument('--progress',type=Path)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cooldown',type=int,default=10)
    parser.add_argument('--timeout',type=int,default=3600)
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--resume',action='store_true')
    args = parser.parse_args()
    if args.worker: worker(args)
    else: main(args)
