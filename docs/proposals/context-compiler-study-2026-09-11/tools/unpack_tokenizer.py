"""Extract only portable runtime modules/license; no install or package registration."""
import base64, hashlib, json, tarfile
from pathlib import Path
STUDY=Path(__file__).resolve().parents[1]
archive=STUDY/'gpt-tokenizer-3.4.0.tgz'
expected='wxFLnhIXTDjYebd9A9pGl3e31ZpSypbpIJSOswbgop5jLte/AsZVDvjlbEuVFlsqZixVKqbcoNmRlFDf6pz/UQ=='
assert base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()==expected
dest=STUDY/'.vendor'/'gpt-tokenizer'
dest.mkdir(parents=True,exist_ok=True)
count=0
with tarfile.open(archive) as tf:
    for member in tf.getmembers():
        rel=Path(member.name).relative_to('package')
        if not member.isfile() or not (str(rel).replace('\\','/').startswith('cjs/') or str(rel) in ('LICENSE','package.json','README.md')):
            continue
        target=(dest/rel).resolve()
        assert target.is_relative_to(dest.resolve())
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(tf.extractfile(member).read())
        count+=1
receipt={'name':'gpt-tokenizer','version':'3.4.0','tarball':'https://registry.npmjs.org/gpt-tokenizer/-/gpt-tokenizer-3.4.0.tgz','sha512_base64':expected,'extracted_files':count,'installed':False,'encodings_are_reference_not_host_billing':True}
(STUDY/'evidence'/'tokenizer-provenance.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))
