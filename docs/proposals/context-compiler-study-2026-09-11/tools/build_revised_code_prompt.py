"""Revision after observed schema ambiguity; preserve task/interface text verbatim.

No original prompt, candidate or oracle is altered. This is an informed revision,
not a fourth independent randomized arm.
"""
import hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parents[1];P=S/'code-experiment'
cases=json.loads((P/'contracts.json').read_text(encoding='utf-8'))
prefix=(P/'prompt-full.md').read_text(encoding='utf-8').split('\n\n## ')[0]
revised=[prefix];literal=[prefix]
for c in cases:
    header=f"## {c['id']} — {c['signature']}\n"
    revised.append(header+'Contrato de entrada/salida y encargo (literal): '+c['task']+'\nReglas: '+c['compact'])
    literal.append(header+c['task']+'\n'+c['details'])
(P/'prompt-contract_preserved.md').write_text('\n\n'.join(revised)+'\n',encoding='utf-8')
(P/'prompt-literal_selected.md').write_text('\n\n'.join(literal)+'\n',encoding='utf-8')
receipt={'revision':'preserve full source task/input/output text; no changes to normative oracle',
 'trigger':'Before tests, the compact agent reported absent output container and dependency-field schema. Tests then found seven output-contract failures.',
 'not_independent_arm':True,'oracle_sha256':hashlib.sha256((P/'evaluate.py').read_bytes()).hexdigest(),
 'prompts':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'prompt-contract_preserved.md',P/'prompt-literal_selected.md']}}
(P/'revision-design.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))
