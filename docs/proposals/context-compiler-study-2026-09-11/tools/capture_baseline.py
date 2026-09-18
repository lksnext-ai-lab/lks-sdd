import hashlib
import json
import subprocess
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[2]
out = STUDY / 'evidence'
out.mkdir(exist_ok=True)
status = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z'], cwd=ROOT)
entries = status.decode('utf-8').split('\0')
files = {}
for entry in entries:
    if not entry or len(entry) < 4:
        continue
    name = entry[3:]
    p = ROOT / name
    if p.is_file() and STUDY not in p.parents:
        files[name] = hashlib.sha256(p.read_bytes()).hexdigest()
payload = {'git_head': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
           'status_porcelain': entries, 'preexisting_changed_file_sha256': files,
           'scope': 'Hashes of preexisting changed files; untracked directories listed, not recursively hashed.'}
(out/'baseline.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'baseline_files':len(files),'path':str(out/'baseline.json')}))
