"""Verify one frozen memory variant; profiles and tests never overlap timings."""
import argparse
from collections import Counter
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tracemalloc
import unittest

from approval_memory_variants import VARIANTS, runtime, files
from approval_performance_support import stable_generation, synthetic, semantic


def main(args):
    with runtime(args.variant), tempfile.TemporaryDirectory(prefix='approval-layout-check-') as temp:
        stable_generation()
        root = Path(temp)
        if args.mode == 'verify':
            from approval_probe import probe
            result = {'variant':args.variant, 'probe':semantic(probe(root), [(root,'<root>')])}
            suites = [unittest.defaultTestLoader.loadTestsFromName(n) for n in
                      ('test_approval_memory_layout','test_v3_approval_performance')]
            test = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(suites))
            result.update(passed=test.wasSuccessful(), tests=test.testsRun, skipped=len(test.skipped),
                          failures=[(t.id(),e) for t,e in test.failures+test.errors])
        else:
            import v3_contract as c
            model, _, _, _ = synthetic(root, args.size, args.technologies)
            documents = [(p.relative_to(root).as_posix(), p.read_bytes()) for p in sorted((root/'docs/lks-sdd').rglob('*.md'))]
            del model
            # Warm imports/schema caches, then trace only one fresh retained model.
            for name, raw in documents: c.parse(raw,name)
            gc.collect(); tracemalloc.start(1)
            value = c.Model(root)
            for name, raw in documents:
                elements, prose = c.parse(raw,name)
                if prose: value.prose[name] = prose
                for e in elements: value.elements[e.uid] = e
            del elements, e
            value.index()
            live, peak = tracemalloc.get_traced_memory()
            counts = Counter(type(o).__name__ for o in gc.get_objects() if type(o).__module__ == 'v3_contract')
            allocations = [{'location':str(s.traceback[0]), 'bytes':s.size, 'count':s.count}
                           for s in tracemalloc.take_snapshot().statistics('lineno')[:20]]
            ref = __import__('weakref').ref(value)
            del value; gc.collect()
            after = tracemalloc.get_traced_memory()[0]; tracemalloc.stop()
            result = {'variant':args.variant,'size':args.size,'traced_live_bytes':live,'traced_peak_bytes':peak,
                      'traced_after_release_bytes':after,'model_released':ref() is None,
                      'counts':dict(counts),'allocations':allocations,'method':'separate tracemalloc; no CPU claims'}
        result['contract_sha256'] = hashlib.sha256(files(args.variant)['scripts/v3_contract.py']).hexdigest()
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k not in ('probe','allocations','failures')}))
        if result.get('passed') is False: raise SystemExit(1)


if __name__ == '__main__':
    # Integration comparisons traverse sets. Fix the interpreter hash seed before
    # imports; setting os.environ in this interpreter would not fix that order.
    if os.environ.get('PYTHONHASHSEED') != '0':
        raise SystemExit(subprocess.call([sys.executable,'-B','-X','utf8',*sys.argv],
                                        env={**os.environ,'PYTHONHASHSEED':'0'}))
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant',choices=VARIANTS,required=True)
    parser.add_argument('--mode',choices=['verify','memory'],required=True)
    parser.add_argument('--size',type=int,default=1500)
    parser.add_argument('--technologies',type=int,default=35)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args())
