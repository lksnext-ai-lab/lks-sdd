"""No benchmarks or project fixtures; reject unsafe admission from raw records."""
import copy
import unittest
from performance_control import evaluate
from performance_command import measurement_affinity


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.hashes={'input':'a'*64,'method':'b'*64,'source':'c'*64}
        rows=[{'enabled':e,'seconds':2.01 if e else 2.,'cpu_seconds':2.01 if e else 2.,
               'count':10000,'bytes':67 if e else 0} for e in (False,True,True,False,False,True)]
        self.record={'hashes':self.hashes.copy(),'preregistered':True,'started_epoch':100,'finished_epoch':130,
            'result':{'rows':rows,'affinity':2048,'natural_gc_enabled':True,'controller_affinity_unchanged':True,
                'isolated':True,'audits':[{'errors':[],'unowned_new_identities':[],'snapshots':10}],
                'metrics':{'job_affinity_mask':2048,'job_assigned_before_process_start':True,
                           'job_active_processes_at_exit':0,'exit_code':0}}}

    def check(self,record=None,now=131):
        return evaluate(self.record if record is None else record,expected_hashes=self.hashes,now=now)

    def test_ready_is_only_a_control_precondition(self):
        value=self.check();self.assertTrue(value['control_ready'])
        self.assertFalse(value['authority_granted']);self.assertEqual(0,value['runs_started'])

    def test_saved_pass_cannot_hide_dispersion_or_overhead(self):
        for key in ('seconds','cpu_seconds'):
            record=copy.deepcopy(self.record);record['result']['passed']=True
            record['result']['rows'][1][key]=4
            self.assertFalse(self.check(record)['control_ready'])
            for r in record['result']['rows']:
                if r['enabled']:r[key]=4
            self.assertIn(key+'-overhead',self.check(record)['reasons'])

    def test_stale_future_changed_hashes_or_incomplete_records_are_rejected(self):
        self.assertFalse(self.check(now=431)['control_ready'])
        self.assertFalse(self.check(now=129)['control_ready'])
        for mutation in ('hash','missing','count','nan','order','posthoc'):
            record=copy.deepcopy(self.record)
            if mutation=='hash':record['hashes']['source']='d'*64
            elif mutation=='missing':record['result']['rows'].pop()
            elif mutation=='count':record['result']['rows'][0]['count']=1
            elif mutation=='nan':record['result']['rows'][0]['seconds']=float('nan')
            elif mutation=='posthoc':record['preregistered']=False
            else:record['result']['rows'][0]['enabled']=True
            self.assertFalse(self.check(record)['control_ready'],mutation)

    def test_affinity_descendants_and_isolation_fail_closed(self):
        for key,value in (('job_affinity_mask',1),('job_active_processes_at_exit',1),('job_assigned_before_process_start',False)):
            record=copy.deepcopy(self.record);record['result']['metrics'][key]=value
            self.assertFalse(self.check(record)['control_ready'])
        record=copy.deepcopy(self.record);record['result']['audits'][0]['unowned_new_identities']=[42]
        self.assertFalse(self.check(record)['control_ready'])

    def test_longer_fixed_work_requires_actual_stable_warmup_and_equal_counts(self):
        record=copy.deepcopy(self.record);record['work_units']=30000
        for r in record['result']['rows']:r['count']=30000
        warm=[dict(enabled=False,seconds=2.,cpu_seconds=2.,count=30000,bytes=0) for _ in range(3)]
        record['result']['warmup']=warm
        self.assertTrue(self.check(record)['control_ready'])
        warm[-1]['seconds']=2.2
        self.assertIn('seconds-warmup-unstable',self.check(record)['reasons'])
        warm[-1]['seconds']=2.;record['result']['rows'][1]['count']=10000
        self.assertIn('unequal-work-or-invalid-output',self.check(record)['reasons'])

    def test_owned_execution_policy_must_be_observed_not_just_requested(self):
        record=copy.deepcopy(self.record);record['performance_mode']=True
        self.assertIn('unverified-owned-execution-policy',self.check(record)['reasons'])
        metrics=record['result']['metrics']
        metrics.update(owned_job_performance_mode=True,owned_job_priority=0x8000,
                       worker_power_throttling={'control':1,'state':0})
        self.assertTrue(self.check(record)['control_ready'])
        metrics['worker_power_throttling']['state']=1
        self.assertFalse(self.check(record)['control_ready'])

    def test_failed_warmup_is_explicit_and_never_approves_empty_variant_rows(self):
        record=copy.deepcopy(self.record)
        record['result'].update(rows=[],reason='warmup-never-stabilized-within-30s')
        value=self.check(record)
        self.assertFalse(value['control_ready'])
        self.assertIn('warmup-never-stabilized-no-variants-started',value['reasons'])
        self.assertEqual(0,value['runs_started'])


class TopologyTests(unittest.TestCase):
    def test_hybrid_selection_uses_class_and_physical_core_before_timing(self):
        rows=[dict(group=0,logical=i,core=i//2 if i<4 else i,
                   efficiency_class=1 if i<4 else 0,flags=0) for i in range(12)]
        self.assertEqual(4,measurement_affinity(rows,4095))
        self.assertEqual(4,measurement_affinity(list(reversed(rows)),4095))
        self.assertEqual(8,measurement_affinity(rows,4091))

    def test_parked_reserved_disallowed_and_other_groups_are_not_selected(self):
        rows=[dict(group=0,logical=0,core=0,efficiency_class=1,flags=1),
              dict(group=0,logical=1,core=1,efficiency_class=1,flags=2),
              dict(group=0,logical=2,core=2,efficiency_class=1,flags=6),
              dict(group=1,logical=3,core=3,efficiency_class=2,flags=0)]
        self.assertEqual(4,measurement_affinity(rows,15))
        with self.assertRaises(RuntimeError):measurement_affinity(rows,3)
        with self.assertRaises(RuntimeError):measurement_affinity([],4095)


if __name__=='__main__':unittest.main()
