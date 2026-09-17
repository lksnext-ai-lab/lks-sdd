"""Measure supplied visible payloads with two reference encodings."""
import json,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1]
paths=[]
for p in sorted((S/'code-experiment').glob('prompt-*.md')):
    paths.append({'id':p.stem,'path':str(p.relative_to(S))})
for p in sorted((S/'repo-probe'/'corpora').rglob('*')):
    if p.is_file() and p.suffix in {'.md','.txt'}:
        paths.append({'id':'repo:'+str(p.relative_to(S/'repo-probe'/'corpora')),'path':str(p.relative_to(S))})
for p in sorted((S/'code-experiment').glob('candidate-*.py')):
    paths.append({'id':p.stem,'path':str(p.relative_to(S))})
r=subprocess.run(['node',str(S/'tools'/'count_tokens.cjs')],input=json.dumps(paths),text=True,encoding='utf-8',capture_output=True,check=True)
out=json.loads(r.stdout)
(S/'evidence'/'corpus-tokens.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
