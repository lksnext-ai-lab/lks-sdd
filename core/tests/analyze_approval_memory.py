"""Summarize paired experiments without pooling different variant baselines."""
import argparse
import json
from pathlib import Path
import statistics


def analyze(report):
    rows=[]
    for variant,size,phase in sorted({(s['variant'],s['size'],s['phase']) for s in report['samples']}):
        selected=[s for s in report['samples'] if (s['variant'],s['size'],s['phase'])==(variant,size,phase)]
        for operation in sorted({r['operation'] for s in selected for r in s['rows']}|{'TOTAL'}):
            for metric in (('job_cpu_seconds','seconds','job_peak_commit_bytes','observed_main_peak_working_set_bytes')
                           if phase=='cli' else ('cpu_seconds','seconds','process_peak_bytes')):
                values={}
                for revision in ('rc3',variant):
                    values[revision]=[]
                    for sample in sorted((s for s in selected if s['revision']==revision),key=lambda s:s['repetition']):
                        parts=sample['rows'] if operation=='TOTAL' else [r for r in sample['rows'] if r['operation']==operation]
                        numbers=[r['memory_after'][metric] if metric=='process_peak_bytes' else r[metric] for r in parts]
                        values[revision].append((max if metric.endswith('bytes') else sum)(numbers))
                a,b=values['rc3'],values[variant]
                delta=100*(statistics.median(b)/statistics.median(a)-1) if statistics.median(a) else None
                rows.append({'variant':variant,'size':size,'phase':phase,'operation':operation,'metric':metric,
                             'baseline':a,'variant_values':b,'median_change_percent':delta,
                             'worse_pairs':sum(y>x for x,y in zip(a,b)),
                             'all_pairs_worse':all(y>x for x,y in zip(a,b))})
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    rows=analyze(json.loads(args.report.read_bytes()))
    if args.output: args.output.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    for row in rows:
        if row['operation'] in ('TOTAL','load','identities'):
            print(json.dumps(row))
