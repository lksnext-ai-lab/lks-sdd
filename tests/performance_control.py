"""Fail-closed local control check; never starts or authorizes a journey."""
import math
import statistics


def evaluate(record, *, expected_hashes, now, max_age=300):
    """Caller supplies fresh file hashes and UTC epoch time, not saved pass flags.

    A certificate binds raw samples to the input, method and measured source.
    Readiness is only a measurement precondition: funding, candidate identity,
    business guarantees and host acceptance have separate checks.
    """
    reasons=[]; details={}
    try:
        if record['preregistered'] is not True:
            reasons.append('control-not-preregistered')
        if not expected_hashes or record['hashes']!=expected_hashes:
            reasons.append('input-method-source-mismatch')
        started,finished=record['started_epoch'],record['finished_epoch']
        if not all(type(v) in (int,float) and math.isfinite(v) for v in (started,finished,now)):
            raise ValueError('invalid timestamps')
        if not 0<=finished-started<=90 or not 0<=now-finished<=max_age:
            reasons.append('stale-or-invalid-window')
        result=record['result']; rows=result['rows']
        if result.get('reason')=='warmup-never-stabilized-within-30s':
            reasons.append('warmup-never-stabilized-no-variants-started')
        units=record.get('work_units',10000)
        if type(units) is not int or units not in (10000,30000):
            raise ValueError('unrecognized fixed-work method')
        order=[False,True,True,False,False,True]
        if len(rows)!=6 or any(type(r['enabled']) is not bool or r['enabled']!=e for r,e in zip(rows,order)):
            raise ValueError('incomplete or reordered control')
        if any(type(r['count']) is not int or r['count']!=units or type(r['bytes']) is not int or
               not 0<=r['bytes']<=16384 or (not r['enabled'] and r['bytes']!=0) for r in rows):
            reasons.append('unequal-work-or-invalid-output')
        mask=result['affinity']; metrics=result['metrics']; audits=result['audits']
        if (type(mask) is not int or mask<=0 or mask&(mask-1) or metrics['job_affinity_mask']!=mask or
                metrics['job_assigned_before_process_start'] is not True or metrics['job_active_processes_at_exit']!=0 or
                metrics['exit_code']!=0 or result['controller_affinity_unchanged'] is not True or
                result['isolated'] is not True or not audits or
                any(a['errors'] or a['unowned_new_identities'] or a['snapshots']<1 for a in audits)):
            reasons.append('unverified-isolation-or-affinity')
        if result['natural_gc_enabled'] is not True:
            reasons.append('changed-work-method')
        if record.get('performance_mode',False):
            power=metrics.get('worker_power_throttling') or {}
            if (metrics.get('owned_job_performance_mode') is not True or
                    metrics.get('owned_job_priority')!=0x8000 or
                    power.get('control')!=1 or power.get('state')!=0):
                reasons.append('unverified-owned-execution-policy')
        if units==30000:
            warm=result['warmup']
            if len(warm)<3:raise ValueError('missing steady-work warmup')
            for key in ('seconds','cpu_seconds'):
                values=[r[key] for r in warm[-3:]]
                if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in values):
                    raise ValueError('invalid warmup')
                if (max(values)-min(values))/statistics.median(values)>.05:
                    reasons.append(key+'-warmup-unstable')
            if any(r['enabled'] is not False or r['count']!=units or r['bytes']!=0 for r in warm):
                reasons.append('unequal-warmup-work')
        for key in ('seconds','cpu_seconds'):
            if any(type(r[key]) not in (int,float) or not math.isfinite(r[key]) or r[key]<=0 for r in rows):
                raise ValueError('invalid raw measurement')
            off=[r[key] for r in rows if not r['enabled']]; on=[r[key] for r in rows if r['enabled']]
            baseline=statistics.median(off); delta=statistics.median(on)-baseline
            spread={name:(max(values)-min(values))/statistics.median(values) for name,values in (('off',off),('on',on))}
            limit=max(.10,.05*baseline)
            details[key]={'delta':delta,'limit':limit,'spread':spread}
            if delta>limit:reasons.append(key+'-overhead')
            if any(v>.05 for v in spread.values()):reasons.append(key+'-unstable')
    except (KeyError,TypeError,ValueError,ZeroDivisionError,OverflowError):
        reasons.append('incomplete-or-invalid-control')
    return {'control_ready':not reasons,'reasons':reasons,'recomputed':details,
            'authority_granted':False,'runs_started':0}
