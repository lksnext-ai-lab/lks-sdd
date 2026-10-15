"""Cold CLI process with deterministic generation; all operational guards run."""
import itertools
import os
from pathlib import Path
import runpy
import sys
import uuid

if sys.stdin.readline() != 'run\n': raise SystemExit('Missing job-accounting handshake')
launcher = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(launcher.parent), str(Path(__file__).resolve().parent)]
from approval_performance_support import stable_generation
stable_generation()
sequence = itertools.count()
invocation = os.environ['LKS_PERFORMANCE_INVOCATION']
uuid.uuid4 = lambda: uuid.uuid5(uuid.NAMESPACE_URL, 'lks-cli:'+invocation+':'+str(next(sequence)))
sys.argv = sys.argv[1:]
runpy.run_path(str(launcher), run_name='__main__')
