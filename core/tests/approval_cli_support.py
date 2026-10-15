"""Full public CLI journeys in owned temporary consumers; no host installation."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from approval_performance_support import ROOT, key


def core_files(revision, package=None):
    import io, zipfile
    if package is not None:
        with zipfile.ZipFile(package) as archive:
            names = archive.namelist()
            launcher = next(n for n in names if n.endswith('scripts/lks_sdd.py'))
            prefix = launcher.removesuffix('scripts/lks_sdd.py')
            return {n.removeprefix(prefix):archive.read(n) for n in names if n.startswith(prefix) and not n.endswith('/')}
    if revision == 'rc2':
        manifest = json.loads((ROOT / 'tests/reports/lks-sdd-3.4.3-rc.2.manifest.json').read_bytes())
        path = ROOT / 'tests/reports/lks-sdd-3.4.3-rc.2-development/lks-sdd-plugin-v3.4.3-rc.2.zip'
        import hashlib
        assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['reproducible_artifacts'][path.name]
        with zipfile.ZipFile(path) as archive:
            return {n.removeprefix('lks-sdd/'): archive.read(n) for n in archive.namelist()}
    if revision == 'base':
        done = subprocess.run(['git','archive','--format=zip','a657bf7b07461c8b03516f9adbb00bb7a6b9ed7c'],cwd=ROOT,capture_output=True,check=True)
        with zipfile.ZipFile(io.BytesIO(done.stdout)) as archive:
            files = {n:archive.read(n) for n in archive.namelist() if not n.endswith('/')}
        from build_candidate_package import _package_integrity_bytes
        files['package-integrity.json'] = _package_integrity_bytes(list(files.items()),'3.4.2','frozen-base')
        return files
    from build_dual_distribution import collect_development
    return collect_development(ROOT)


def setup(size, technologies, core, workspace):
    from test_v31_review import IntegralTests
    from test_v3_workflow import git
    from v3_contract import element, load, render, location, BLOCK
    from dual_distribution import project_files
    fixture = IntegralTests(methodName='runTest'); fixture.setUp()
    try:
        model = load(fixture.root).require_valid()
        proposal = copy.deepcopy(model.get(fixture.prop).item())
        tech = [element('technology',f'CLI technology {i}',f'Literal technology {i}',
                        identifier=key(f'cli-technology-{i}'),request=fixture.req) for i in range(technologies)]
        extras = tech + [element('rule',f'Global {i}',f'Complete global rule {i}',identifier=key(f'cli-rule-{i}'),
                               **{'global':True}) for i in range(min(24,size//20))]
        extras += [element('feature',f'Feature {i}',f'Literal feature {i}',identifier=key(f'cli-feature-{i}'),request=fixture.req)
                   for i in range(max(0,size-len(model.elements)-len(extras)))]
        proposal['meta']['revision'] += 1
        proposal['meta']['relations']['technology'] = [e['meta']['uid'] for e in tech]
        raw = b'---\nschema_version: "3.1"\nartifact_type: "specification"\n---\n\n'
        raw += b'\n'.join(BLOCK.search(render(item,'3.1').decode())[0].encode() for item in extras)
        (fixture.root/'docs/lks-sdd/cli-volume.md').write_bytes(raw)
        (fixture.root/location(proposal)).write_bytes(render(proposal,'3.1'))
        fixture.close_proposal(); fixture.create_plan()
        consumer = workspace/'consumer'
        shutil.copytree(fixture.root,consumer)
        # This is an owned test fixture assembled from distribution bytes. No
        # plugin registration, product cache or existing consumer is changed.
        payload = project_files(core,'performance-fixture','development-unreleased',plugin_entrypoints=True)
        for name, raw in payload.items():
            target = consumer/name
            if not target.resolve().is_relative_to(consumer.resolve()): raise ValueError('Unsafe fixture path')
            target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
        git(consumer,'add','-A'); git(consumer,'-c','user.name=Synthetic CLI fixture','-c','user.email=fixture@example.invalid','commit','-m','Synthetic pinned fixture')
        trusted = workspace/'trusted'; shutil.copytree(consumer,trusted)
        git(trusted,'symbolic-ref','HEAD','refs/heads/main')
        lock = json.loads((consumer/'.lks-sdd/distribution-lock.json').read_bytes())
        return {'root':consumer,'trusted':trusted,'runtime':consumer/lock['runtime'],'actor':fixture.actor,
                'request':fixture.req,'task':fixture.task,'lock':lock}
    finally: fixture.doCleanups()


def journey(fixture, workspace, invoke):
    """invoke(label, argv) returns the complete parsed CLI envelope."""
    root, runtime = fixture['root'], fixture['runtime']
    launcher = runtime/'scripts/lks_sdd.py'
    step = 0
    def command(label, action, data=None, **options):
        nonlocal step
        step += 1
        arguments = [sys.executable,'-B','-X','utf8',str(launcher),'v3',action,str(root),'--json']
        if data is not None:
            source = workspace/(str(step)+'-input.json'); source.write_text(json.dumps(data)+'\n',encoding='utf-8')
            arguments += ['--input',str(source)]
        for name,value in options.items():
            arguments += ['--'+name.replace('_','-')]
            if value is not True: arguments.append(str(value))
        return invoke(label,arguments)
    doctor = invoke('runtime-doctor',[sys.executable,'-B','-X','utf8',str(launcher),'runtime-doctor',str(root),'--json'])
    if doctor['status'] != 'valid': raise RuntimeError(doctor)
    command('validate','validate')
    command('readiness','readiness',{'actor':fixture['actor'],'task':fixture['task'],'action':'start'})
    operations = []
    for action in ('start','implement','evidence','verify','close','integrate','accept'):
        if action == 'implement': (root/'app.py').write_bytes(b"def greeting(): return 'Hola'\n")
        if action == 'evidence':
            proof = subprocess.run([sys.executable,'-B','-c',"from app import greeting; assert greeting() == 'Hola'; print('greeting: passed')"],cwd=root,capture_output=True,check=True)
            artifact = root/'docs/lks-sdd/evidence/cli-test.txt'; artifact.parent.mkdir(parents=True,exist_ok=True); artifact.write_bytes(proof.stdout)
            data = {'actor':fixture['actor'],'task':fixture['task'],'tests':['greeting'],'outcome':'passed',
                    'source':'automated','artifact':artifact.relative_to(root).as_posix(),'explanation':'Observed synthetic greeting test'}
        elif action in ('integrate','accept'):
            data = {'actor':fixture['actor'],'request':fixture['request'],'statement':'Explicit synthetic '+action}
            if action == 'integrate': data['trusted_root'] = str(fixture['trusted'])
        else:
            data = {'actor':fixture['actor'],'task':fixture['task'],'reason':'Observed synthetic '+action}
        from v3_presentation_guard import required
        if required(action,data):
            view = command(action+':presentation','decision-view',{'event':action,'data':data},compact=True)
            data['presented'] = view['receipt']
        packet_path = workspace/(action+'-packet.json')
        preview = command(action+':prepare',action,data,output=packet_path)
        if not preview.get('preview_hash'): raise RuntimeError(preview)
        applied = command(action+':apply','apply',json.loads(packet_path.read_bytes()),authorize=preview['preview_hash'])
        if applied.get('status') not in ('applied','completed'): raise RuntimeError(applied)
        operations.append({'action':action,'preview_hash':preview['preview_hash'],'status':applied['status']})
    final = command('final-status','status',{'task':fixture['task']})
    command('final-validate','validate')
    return {'operations':operations,'final_status':final,'runtime_files':len(fixture['lock']['runtime_files']),
            'runtime_version':fixture['lock']['version'],'runtime_digest':fixture['lock']['runtime_digest']}
