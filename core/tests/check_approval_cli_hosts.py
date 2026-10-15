"""Technical packaged-host checks in owned consumers, without product activation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from approval_performance_support import ROOT, stable_generation
from approval_cli_support import core_files, setup, journey


def execute(arguments, cwd):
    done = subprocess.run(arguments,cwd=cwd,capture_output=True,text=True,encoding='utf-8',timeout=600)
    try: value = json.loads(done.stdout)
    except ValueError: value = {'stdout':done.stdout,'stderr':done.stderr}
    return done.returncode, value


def snapshot(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}


def check(package, host):
    stable_generation()
    with tempfile.TemporaryDirectory(prefix='approval-host-check-') as temp:
        workspace = Path(temp); fixture = setup(40,2,core_files('candidate',package),workspace)
        root, runtime = fixture['root'], fixture['runtime']
        launcher = runtime/'scripts/lks_sdd.py'
        command = lambda *args: [sys.executable,'-B','-X','utf8',str(launcher),*args]
        rows, negatives = [], []
        def invoke(label, arguments):
            code, value = execute(arguments,workspace)
            rows.append({'label':label,'exit_code':code,'result':value})
            if code: raise RuntimeError(rows[-1])
            return value
        # Both generated adapters must select this exact immutable runtime.
        for name in ('AGENTS.md','.github/lks-sdd-host.md'):
            assert fixture['lock']['runtime'] in (root/name).read_text(encoding='utf-8'), name
        assert len(list((runtime/'skills').glob('*/SKILL.md'))) == 6
        target = runtime/'docs/V3-COMMON.md'; original = target.read_bytes()
        for kind in ('tampered','missing','extra'):
            if kind == 'tampered': target.write_bytes(original+b'\nchanged\n')
            elif kind == 'missing': target.unlink()
            else: (runtime/'unexpected.txt').write_text('unexpected',encoding='utf-8')
            before = snapshot(root)
            code,value = execute(command('runtime-doctor',str(root),'--json'),workspace)
            assert value.get('status') != 'valid' and value.get('errors'), (kind,value)
            assert before == snapshot(root), kind
            negatives.append({'case':kind,'exit_code':code,'result':value,'no_writes':True})
            target.write_bytes(original)
            (runtime/'unexpected.txt').unlink(missing_ok=True)
        # A global/source launcher cannot bypass the consumer's runtime pin.
        before = snapshot(root)
        code,value = execute([sys.executable,'-B',str(ROOT/'scripts/lks_sdd.py'),'v3','validate',str(root),'--json'],workspace)
        assert code != 0 and before == snapshot(root), value
        negatives.append({'case':'wrong-launcher','exit_code':code,'result':value,'no_writes':True})
        data = workspace/'stale.json'; packet = workspace/'stale-packet.json'
        data.write_text(json.dumps({'actor':fixture['actor'],'task':fixture['task'],'reason':'Synthetic stale preview'}),encoding='utf-8')
        code,preview = execute(command('v3','start',str(root),'--input',str(data),'--output',str(packet),'--json'),workspace)
        assert code == 0 and preview.get('preview_hash'), preview
        app = root/'app.py'; previous = app.read_bytes() if app.exists() else None
        app.write_bytes((previous or b'')+b'\n# changed after preview\n')
        before = snapshot(root)
        code,value = execute(command('v3','apply',str(root),'--input',str(packet),'--authorize',preview['preview_hash'],'--json'),workspace)
        assert code != 0 and before == snapshot(root), value
        negatives.append({'case':'stale-source-apply','exit_code':code,'result':value,'no_writes':True})
        if previous is None: app.unlink()
        else: app.write_bytes(previous)
        result = journey(fixture,workspace,invoke)
        return {'host':host,'package':str(package),'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
                'technical_cycle':result,'commands':rows,'negative_cases':negatives,
                'conversational_activation':'not-run','installed':False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--host',choices=['codex','copilot'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    # Import current source only in this separate functional-check process.
    sys.path.insert(0,str(ROOT/'scripts'))
    result = check(args.package,args.host)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'host':args.host,'commands':len(result['commands']),'negative_cases':len(result['negative_cases']),'passed':True}))
