"""Run an existing diagnostic with a study-local temp directory and retained output."""
import json, os, subprocess, sys, time
from pathlib import Path
STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[2]
label, *command = sys.argv[1:]
temp = STUDY / '.tmp' / label
temp.mkdir(parents=True, exist_ok=True)
evidence = STUDY / 'evidence'
evidence.mkdir(exist_ok=True)
env = dict(os.environ, TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
start = time.monotonic()
with (evidence/f'{label}.stdout').open('w',encoding='utf-8') as out, (evidence/f'{label}.stderr').open('w',encoding='utf-8') as err:
    result = subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=540)
summary = {'command':command,'exit_code':result.returncode,'seconds':round(time.monotonic()-start,3),'temp_directory':str(temp)}
(evidence/f'{label}.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
raise SystemExit(result.returncode)
