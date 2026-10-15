"""Diagnostic profiles, separate from final unprofiled performance readings."""
import argparse
from collections import Counter
from contextlib import contextmanager
import cProfile
import gc
import hashlib
import json
from pathlib import Path
import pstats
import sys
import tempfile
import time
import tracemalloc
import zipfile

from approval_performance_support import ROOT, runtime, synthetic, stable_generation


@contextmanager
def revision(name):
    if name != 'rc2':
        with runtime(name == 'base'): yield
        return
    archive = ROOT / 'tests/fixtures/approval-reference/rc2-original.zip'
    manifest = json.loads(archive.with_suffix('.json').read_bytes())
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['archive_sha256']
    with tempfile.TemporaryDirectory(prefix='approval-rc2-reference-') as temp:
        target = Path(temp).resolve()
        with zipfile.ZipFile(archive) as source:
            assert set(source.namelist()) == set(manifest['files'])
            for name, digest in manifest['files'].items():
                raw = source.read(name); assert hashlib.sha256(raw).hexdigest() == digest
                path = target / name; assert path.resolve().is_relative_to(target)
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        sys.path[:0] = [str(target / 'scripts'), str(ROOT / 'tests')]
        try: yield
        finally: sys.path.remove(str(target / 'scripts')); sys.path.remove(str(ROOT / 'tests'))


def main(args):
    with revision(args.revision), tempfile.TemporaryDirectory(prefix='approval-diagnostic-') as temp:
        stable_generation()
        import v3_contract as contract
        model, _, _, _ = synthetic(Path(temp), args.size, args.technologies)
        root = model.root
        documents = [(p.relative_to(root).as_posix(), p.read_bytes()) for p in sorted((root / 'docs/lks-sdd').rglob('*.md'))]
        del model
        def parse():
            result = contract.Model(root)
            for path, raw in documents:
                elements, prose = contract.parse(raw, path)
                if prose: result.prose[path] = prose
                for e in elements: result.elements[e.uid] = e
            result.index()
            return result
        callback = parse if args.phase == 'parse' else lambda: contract.load(root).require_valid()
        profile = cProfile.Profile(); gc.collect()
        start, cpu = time.perf_counter(), time.process_time()
        profile.enable()
        for _ in range(args.repetitions): callback()
        profile.disable()
        elapsed, cpu = time.perf_counter() - start, time.process_time() - cpu
        stats = pstats.Stats(profile)
        calls = sorted([{'file': Path(key[0]).name, 'line': key[1], 'function': key[2],
                         'calls': value[1], 'self_seconds': value[2], 'cumulative_seconds': value[3]}
                        for key, value in stats.stats.items()], key=lambda r: r['cumulative_seconds'], reverse=True)
        gc.collect(); tracemalloc.start(1)
        value = callback()
        current, peak = tracemalloc.get_traced_memory()
        allocations = [{'location': str(s.traceback[0]), 'bytes': s.size, 'count': s.count}
                       for s in tracemalloc.take_snapshot().statistics('lineno')[:18]]
        objects = Counter(type(o).__name__ for o in gc.get_objects() if type(o).__module__ == 'v3_contract')
        del value; gc.collect()
        released = tracemalloc.get_traced_memory()[0]; tracemalloc.stop()
        result = {'revision': args.revision, 'phase': args.phase, 'size': args.size, 'repetitions': args.repetitions,
                  'profiled_wall_seconds': elapsed, 'profiled_cpu_seconds': cpu,
                  'traced_live_bytes': current, 'traced_peak_bytes': peak, 'traced_after_release_bytes': released,
                  'live_model_object_counts': dict(objects), 'allocations': allocations, 'calls': calls[:35],
                  'method': 'cProfile timing then separate one-model tracemalloc reading; diagnostic only'}
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({k: result[k] for k in ('revision','phase','profiled_cpu_seconds','traced_live_bytes','traced_peak_bytes','traced_after_release_bytes')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', choices=['base','rc2','candidate'], required=True)
    parser.add_argument('--phase', choices=['parse','load'], default='parse')
    parser.add_argument('--size', type=int, default=1500)
    parser.add_argument('--technologies', type=int, default=35)
    parser.add_argument('--repetitions', type=int, default=5)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args())
