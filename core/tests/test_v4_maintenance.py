"""Bounded parity of maintenance guarantees against the published 3.4.3 core."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('LKS_SDD_TEST_SOURCE', str(ROOT))).resolve()
sys.path[:0] = [str(SOURCE/'scripts'), str(SOURCE/'tests')]
import test_v31_review as fixture
from presentation_test_support import present, technical_solution
from v3_contract import ContractError, element, load, render
from v3_authoring import author, approve_and_authorize
from v3_approval import task_authority
from v3_workflow import plan_for, state
from v3_guidance import readiness
from v3_verification import evidence
from v3_lifecycle import revoke
from v31_corrections import reject, define, resolve


class MaintenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = fixture.IntegralTests('runTest')
        cls.template.setUp()
        cls.addClassCleanup(cls.template.doCleanups)
        cls.template.close_proposal()
        cls.template.create_plan()

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='v4-maint-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)/'consumer'
        shutil.copytree(self.template.root, self.root)
        self.case = fixture.IntegralTests('runTest')
        for name in ('actor', 'req', 'prop', 'task', 'plan_id'):
            setattr(self.case, name, getattr(self.template, name))
        self.case.root = self.root
        self.actions = []

    def apply(self, name, packet):
        result = fixture.commit_packet(self.root, packet)
        self.actions.append(name)
        return result

    def advance(self, action):
        self.case.advance(action)
        self.actions.append(action)

    def record(self, **facts):
        for name, module in tuple(sys.modules.items()):
            if name.startswith(('v3_', 'v31_', 'v2_', 'v4_')) and getattr(module, '__file__', None):
                self.assertTrue(Path(module.__file__).resolve().is_relative_to(SOURCE/'scripts'), (name, module.__file__))
        target = os.environ.get('LKS_SDD_MAINTENANCE_RESULTS')
        if target:
            Path(target).mkdir(parents=True, exist_ok=True)
            (Path(target)/(self._testMethodName+'.json')).write_text(json.dumps({
                'case':self._testMethodName, 'source':str(SOURCE), 'actions':self.actions,
                'facts':facts, 'billed_tokens':None}, ensure_ascii=False, indent=2), encoding='utf-8')

    def test_covered_defect_reuses_agreements_and_checks_real_result(self):
        model = load(self.root)
        definitions = {key:model.get(key).digest() for key in (self.case.req,self.case.prop,self.case.task,self.case.plan_id)}
        original_authority = task_authority(model, model.get(self.case.task), plan_for(model, model.get(self.case.task)), 'execution')['decisions']
        self.advance('start')
        app = self.root/'app.py'
        app.write_text("def greeting(): return 'Adios'\n", encoding='utf-8')
        command = [sys.executable, '-B', '-X', 'utf8', '-c', "from app import greeting; assert greeting() == 'Hola'"]
        failed = subprocess.run(command, cwd=self.root, capture_output=True)
        self.assertNotEqual(0, failed.returncode)
        failure = self.root/'docs/lks-sdd/evidence/initial-failure.txt'
        failure.parent.mkdir(exist_ok=True)
        failure.write_bytes(failed.stderr)
        app.write_text("def greeting(): return 'Hola'\n", encoding='utf-8')
        passed = subprocess.run(command, cwd=self.root, capture_output=True)
        self.assertEqual(0, passed.returncode, passed.stderr)
        report = self.root/'docs/lks-sdd/evidence/correction.txt'
        report.write_text('Executed assertion: greeting() == Hola; exit=0', encoding='utf-8')
        self.advance('implement')
        self.apply('evidence', evidence(self.root,self.case.actor,self.case.task,['greeting'],'passed','automated',
                    report.relative_to(self.root).as_posix(),'Resultado real de la prueba afectada'))
        self.advance('verify'); self.advance('close')
        model = load(self.root)
        self.assertEqual('closed', state(model, model.get(self.case.task)))
        self.assertEqual(definitions,{key:model.get(key).digest() for key in definitions})
        self.assertEqual(original_authority,task_authority(model,model.get(self.case.task),plan_for(model,model.get(self.case.task)),'execution')['decisions'])
        self.advance('reopen')
        self.apply('revoke',present(revoke,self.root,self.case.actor,original_authority[0],'Retiro expresamente el permiso de ejecución'))
        self.assertEqual('blocked',readiness(self.root,self.case.task,self.case.actor,'implement')['status'])
        self.assertTrue(failure.exists())
        self.record(definitions_reused=True,authorization_reused_before_revocation=True,
                    initial_test='failed',corrected_test='passed',closed_then_reopened=True,revoked_permission_blocks=True)

    def test_agreement_change_needs_proposal_before_plan_and_critical_unknown_blocks(self):
        model = load(self.root)
        proposal = copy.deepcopy(model.get(self.case.prop).item())
        proposal['meta']['revision'] += 1
        proposal['body'] += ' Solo usuarios administradores pueden consultar el saludo.'
        task = copy.deepcopy(model.get(self.case.task).item())
        task['meta']['revision'] += 1
        task['body'] += ' Comprobar además permisos de consulta.'
        before = model.snapshot()
        with self.assertRaises(ContractError): author(self.root,self.case.actor,[proposal,task])
        self.assertEqual(before,load(self.root).snapshot())
        self.apply('author-proposal',author(self.root,self.case.actor,[proposal]))
        self.assertEqual('blocked',readiness(self.root,self.case.task,self.case.actor,'start')['status'])
        with self.assertRaises(ContractError): present(approve_and_authorize,self.root,self.case.actor,self.case.plan_id,'No fusionar el cambio de acuerdo y el plan')
        self.case.close_proposal(); self.actions.append('close-proposal')
        self.apply('author-task',author(self.root,self.case.actor,[task]))
        model = load(self.root)
        self.assertFalse(task_authority(model,model.get(self.case.task),plan_for(model,model.get(self.case.task)),'execution')['valid'])
        self.apply('authorize-plan',present(approve_and_authorize,self.root,self.case.actor,self.case.plan_id,
                   'Valido el plan posterior a la propuesta revisada',review_tasks=[self.case.task]))
        self.assertEqual('allowed',readiness(self.root,self.case.task,self.case.actor,'start')['status'])
        unknown = element('rule','Permiso sin decidir','Falta decidir el acceso de usuarios externos.',critical=True,unresolved=['acceso externo'])
        unknown['meta']['state'] = 'unknown'
        self.apply('author-critical-unknown',author(self.root,self.case.actor,[unknown]))
        self.assertEqual('blocked',readiness(self.root,self.case.task,self.case.actor,'start')['status'])
        self.record(atomic_proposal_and_task_rejected=True,old_authority_stale=True,
                    proposal_before_plan=True,small_permission_change_requires_decision=True,critical_unknown_blocks=True)

    def test_new_capability_requires_separate_coverage_and_rejection_is_preserved(self):
        packet = reject(self.root,self.case.actor,self.case.req,'Falta una capacidad nueva',phase='integration',tasks=[self.case.task],
                        expected='Saludo con idioma configurable',observed='El acuerdo vigente solo cubre Hola')
        problem, correction = packet['summary']['problem'],packet['summary']['correction']
        self.apply('reject-result',packet)
        self.apply('define-correction',present(define,self.root,self.case.actor,correction,'new-request',
                        'Es una capacidad distinta del saludo acordado','Idioma configurable'))
        with self.assertRaises(ContractError):
            present(resolve,self.root,self.case.actor,problem,'La clasificación no amplía el permiso anterior')
        request = element('request','Idioma configurable','Añadir selección de idioma mediante un acuerdo independiente.')
        prop = element('proposal','Contrato de idioma','El saludo acepta un idioma explícito y conserva su valor por defecto.',
                       request=request['meta']['uid'],part='joint',objective='Configurar idioma',included=['app.py'],excluded=[],
                       behavior='Idioma explícito',solution=technical_solution(),impact='Interfaz pública',acceptance=['Idioma configurable'])
        request['meta']['relations']['proposal'] = [prop['meta']['uid']]
        task = element('task','Implementar idioma','Añadir y comprobar la interfaz de idioma.',request=request['meta']['uid'],
                       owner=self.case.actor,scope=['app.py'],acceptance=['Idioma configurable'],tests=['language'])
        before = load(self.root).snapshot()
        with self.assertRaises(ContractError): author(self.root,self.case.actor,[request,prop,task])
        self.assertEqual(before,load(self.root).snapshot())
        self.apply('author-new-request-proposal',author(self.root,self.case.actor,[request,prop]))
        self.case.req,self.case.prop = request['meta']['uid'],prop['meta']['uid']
        self.case.close_proposal(); self.actions.append('close-new-proposal')
        plan = element('plan','Plan de idioma','Implementar y probar el nuevo contrato de idioma.',request=self.case.req)
        plan['meta']['relations']['tasks'] = [task['meta']['uid']]
        self.apply('author-new-plan',author(self.root,self.case.actor,[task,plan]))
        model = load(self.root)
        self.assertFalse(task_authority(model,model.get(task['meta']['uid']),model.get(plan['meta']['uid']),'execution')['valid'])
        self.assertEqual('blocked',readiness(self.root,task['meta']['uid'],self.case.actor,'start')['status'])
        self.assertEqual('open',model.get(problem).meta['state'])
        self.assertTrue(model.get(problem).data['evidence_pending'])
        self.record(separate_request=True,proposal_before_executable_tasks=True,old_permission_not_reused=True,
                    original_rejection_retained=True,missing_evidence_not_fabricated=True)

    def test_expired_member_permission_blocks_covered_task(self):
        model = load(self.root)
        actor = model.get(self.case.actor)
        changed = copy.deepcopy(actor.item())
        changed['meta']['revision'] += 1
        changed['meta']['data']['expires_at'] = '2000-01-01T00:00:00+00:00'
        # A changed canonical identity is reloaded; earlier task authority cannot
        # preserve the operator's expired permission.
        (self.root/actor.path).write_bytes(render(changed))
        self.assertEqual('blocked',readiness(self.root,self.case.task,self.case.actor,'start')['status'])
        self.record(expired_operator_permission_blocks=True,task_not_started=True)


if __name__ == '__main__': unittest.main()
