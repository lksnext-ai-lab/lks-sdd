"""Isolated AB/BA memory experiments, uninstrumented CPU and exact output hashes.

One baseline/variant pair is accepted only if the whole pair is isolated.
Use --phases calculations workflow shared-inventories cli for final coverage.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

from approval_memory_variants import BASELINE, VARIANTS, files, runtime, source_binding
from approval_performance_support import ROOT, stable_generation
from measure_approval_rc3 import remove_workspace, semantic, written_paths, summaries


def sha(raw): return hashlib.sha256(raw).hexdigest()


def binding(args):
    names = ('approval_memory_variants.py','measure_approval_memory.py','measure_approval_performance.py',
             'approval_performance_support.py','measure_approval_rc3.py','approval_cli_support.py',
             'performance_command.py','approval_command_worker.py','performance_isolation.py')
    result = {'variants':source_binding(),'baseline_package':sha(BASELINE.read_bytes()),
              'tools':{n:sha((ROOT/'tests'/n).read_bytes()) for n in names}}
    if args.package: result['candidate_package'] = sha(args.package.read_bytes())
    return result


class PlainMeasurements:
    """No tracing, monkeypatched counters, profiler or memory sampler in timings."""
    def __init__(self): self.rows = []
    def run(self, label, callback):
        from measure_approval_performance import memory
        from v3_contract import canonical
        count = {'identities':100,'classification':20,'dependencies':20}.get(label,1)
        before = memory()
        cpu = time.process_time(); start = time.perf_counter()
        for _ in range(count): value = callback()
        elapsed = time.perf_counter()-start; cpu = time.process_time()-cpu
        raw = canonical(value)
        after = memory()
        self.rows.append({'operation':label,'batch_iterations':count,'cpu_seconds':cpu,'seconds':elapsed,
                          'memory_before':before,'memory_after':after,
                          'sampled_peak_working_set_bytes':max(before['working_set_bytes'],after['working_set_bytes']),
                          'semantic_digest':sha(raw),'serialized_bytes':len(raw)})
        return value


def worker(args):
    import measure_approval_performance as measures
    with runtime(args.revision, args.package):
        stable_generation()
        names = iter('approval%09d'%i for i in range(1000000))
        tempfile.tempdir = str(args.workspace)
        tempfile._get_candidate_names = lambda:names
        args.original = False
        measures.Measurements = PlainMeasurements
        measures.PROGRESS = None
        if args.worker == 'cli':
            from approval_cli_support import setup, journey
            from performance_command import run
            fixture = setup(args.size,args.technologies,files(args.revision,args.package),args.workspace)
            rows = []
            def invoke(label, arguments):
                value, row = run(arguments,args.workspace,label,timeout=args.timeout)
                row.update(operation=label,result=value)
                rows.append(row)
                with args.progress.open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps({'revision':args.revision,'operation':label,'seconds':row['seconds']})+'\n')
                return value
            final = journey(fixture,args.workspace,invoke)
            contract = {'final_status':semantic(final['final_status']),
                        'readiness':semantic(next(r['result'] for r in rows if r['operation']=='readiness')),
                        'actions':[(o['action'],o['status']) for o in final['operations']],
                        'command_statuses':[(r['operation'],r['result'].get('status')) for r in rows],
                        'write_paths':[(r['operation'],written_paths(r['result'].get('writes',[]))) for r in rows if r['operation'].endswith(':apply')]}
            result = {'rows':rows,'journey':final,'business_contract':contract,
                      'business_digest':sha(json.dumps(contract,sort_keys=True,ensure_ascii=False).encode())}
        else:
            result = {'calculations':measures.calculation_worker,'workflow':measures.workflow_worker,
                      'shared-inventories':measures.shared_inventory_worker}[args.worker](args)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main(args):
    from performance_isolation import Audit, Watch
    audit = Audit(); initial = binding(args)
    config = {'variants':args.variants,'sizes':args.sizes,'phases':args.phases,
              'repetitions':args.repetitions,'cooldown':args.cooldown}
    samples, comparisons, excluded, inflight = [], [], [], []
    if args.resume:
        previous = json.loads(args.output.read_bytes())
        assert previous['binding']==initial and previous['config']==config
        samples,comparisons,excluded = previous['samples'],previous['comparisons'],previous['excluded']
        if previous['inflight']: excluded.append({'reason':'interrupted-pair','samples':previous['inflight']})
    else: assert not args.output.exists(), 'Output already exists'
    progress = args.output.with_suffix('.progress.jsonl')
    def save(complete=False):
        assert binding(args)==initial, 'Measured source changed'
        result = {'binding':initial,'config':config,'complete':complete,'samples':samples,'comparisons':comparisons,
                  'excluded':excluded,'inflight':inflight,'summaries':summaries(samples),
                  'method':'fresh sequential AB/BA; no profiling or counters; fixed short-operation batches; native audit 500ms',
                  'memory_note':'library process peaks cumulative; before/after working sets only; allocation profiles separate',
                  'tokens_note':'exact complete library JSON bytes compared; no model calls; actual host billing not observed'}
        temporary = args.output.with_suffix('.new')
        temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        temporary.replace(args.output)
    def clean():
        previous = None
        while True:
            try: return audit.check()
            except (RuntimeError,OSError,subprocess.TimeoutExpired) as error:
                if str(error)!=previous: print(json.dumps({'waiting_for_isolation':str(error)}),flush=True); previous=str(error)
                time.sleep(10)
    save()
    for variant in args.variants:
        for spec in args.sizes:
            size,tech = map(int,spec.split(':'))
            for phase in args.phases:
                for repetition in range(args.repetitions):
                    key = {'variant':variant,'size':size,'phase':phase,'repetition':repetition}
                    if any(all(c[k]==v for k,v in key.items()) for c in comparisons): continue
                    order = ('rc3',variant) if repetition%2==0 else (variant,'rc3')
                    while True:
                        inflight=[]; contaminated=False
                        with tempfile.TemporaryDirectory(prefix='approval-memory-pair-') as temp:
                            parent = Path(temp).resolve()
                            for rev in order:
                                clean();time.sleep(args.cooldown);before=clean()
                                workspace=parent/'workspace';workspace.mkdir();output=parent/'sample.json'
                                command=[sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--worker',phase,
                                         '--revision',rev,'--workspace',str(workspace),'--size',str(size),'--technologies',str(tech),
                                         '--output',str(output),'--progress',str(progress),'--timeout',str(args.timeout)]
                                if args.package: command+=['--package',str(args.package)]
                                started=time.perf_counter()
                                child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',
                                                       env={**os.environ,'PYTHONHASHSEED':'0'})
                                watch=Watch(audit,child.pid);watch.start()
                                try: stdout,stderr=child.communicate(timeout=args.timeout)
                                except subprocess.TimeoutExpired: child.kill();child.wait();raise
                                finally: observations=watch.close()
                                if child.returncode: raise RuntimeError(stdout[-1000:]+stderr[-12000:])
                                result=json.loads(output.read_bytes())
                                try: after=audit.check()
                                except (RuntimeError,OSError,subprocess.TimeoutExpired) as error: after={'isolation_failure':str(error)}
                                contaminated=bool(observations['unowned_new_identities'] or observations['errors'] or after.get('isolation_failure'))
                                inflight.append({**key,'revision':rev,'technologies':tech,'worker_seconds':time.perf_counter()-started,
                                    'isolation':{'before':before,'during':observations,'after':after},**result})
                                save(); remove_workspace(workspace,parent)
                                print(json.dumps({**key,'revision':rev,'worker_seconds':inflight[-1]['worker_seconds'],'isolated':not contaminated}),flush=True)
                                if contaminated: break
                        if contaminated:
                            excluded.append({'reason':'foreign-process; repeat entire pair','samples':inflight});inflight=[];save();continue
                        left,right=inflight
                        equal = left['business_digest']==right['business_digest'] if phase=='cli' else (
                            [(r['operation'],r['semantic_digest'],r['serialized_bytes']) for r in left['rows']]==
                            [(r['operation'],r['semantic_digest'],r['serialized_bytes']) for r in right['rows']])
                        if not equal: save();raise AssertionError('Equivalence failed; raw results retained')
                        comparisons.append({**key,'equivalent':equal,'identical_library_payload_bytes':phase!='cli'})
                        samples.extend(inflight);inflight=[];save();break
    save(complete=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',choices=['calculations','workflow','shared-inventories','cli'])
    parser.add_argument('--revision',choices=[*VARIANTS,'candidate'])
    parser.add_argument('--variants',nargs='+',choices=['slots','uid','combined','candidate'],default=['slots','uid'])
    parser.add_argument('--sizes',nargs='+',default=['1500:35'])
    parser.add_argument('--phases',nargs='+',default=['calculations'])
    parser.add_argument('--repetitions',type=int,default=4)
    parser.add_argument('--cooldown',type=float,default=5)
    parser.add_argument('--timeout',type=int,default=3600)
    parser.add_argument('--package',type=Path)
    parser.add_argument('--workspace',type=Path)
    parser.add_argument('--size',type=int,default=1500)
    parser.add_argument('--technologies',type=int,default=35)
    parser.add_argument('--progress',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.worker: worker(args)
    else: main(args)
