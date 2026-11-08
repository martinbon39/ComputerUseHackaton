import os
os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
import torch
torch.set_num_threads(2)
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path('/workspace/astra/moon-leak')
POWER=Path('/workspace/astra/astra-power')


def load(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('arm');args=ap.parse_args()
    frozen=json.loads((POWER/'FROZEN.json').read_text())
    baseline=load(ROOT/'baseline_A/generations.jsonl')
    candidate=load(ROOT/'runs'/args.arm/'generations.jsonl')
    contexts={c['row']['task_id']:c for c in frozen['contexts']}
    keys={(tid,s) for tid in contexts for s in frozen['seeds']}
    tables=[]
    for rows in [baseline,candidate]:
        tab={}
        for r in rows:
            key=(r['row']['task_id'],r['seed']);assert key not in tab
            assert r['row']==contexts[key[0]]['row'] and r['payload_sha256']==contexts[key[0]]['payload_sha256']
            tab[key]=r
        assert set(tab)==keys
        tables.append(tab)
    a,b=tables
    rng=np.random.default_rng(261029609)
    metric={};draws={}
    for label in ['fs+','fs-','healthy']:
        tasks=[t for t,c in contexts.items() if c['row']['label']==label]
        field='valid_nonanswer' if label=='healthy' else 'answer'
        av=np.array([[int(a[t,s][field]) for s in frozen['seeds']] for t in tasks]).mean(1)
        bv=np.array([[int(b[t,s][field]) for s in frozen['seeds']] for t in tasks]).mean(1)
        d=av-bv
        boot=d[rng.integers(0,len(tasks),size=(10000,len(tasks)))].mean(1)
        draws[label]=boot
        candidate_invalid=sum(int(b[t,s]['invalid']) for t in tasks for s in frozen['seeds'])
        candidate_nonanswer=sum(int(b[t,s]['valid_nonanswer']) for t in tasks for s in frozen['seeds'])
        metric[label]=dict(candidate_invalid=candidate_invalid,candidate_valid_nonanswer=candidate_nonanswer,tasks=len(tasks),samples=len(tasks)*4,field=field,A=float(av.mean()),candidate=float(bv.mean()),drop=float(d.mean()),drop_ci95=np.quantile(boot,[.025,.975]).tolist())
    selection=metric['fs+']['drop']-metric['fs-']['drop']
    valid=sum(r['schema_valid'] for r in candidate)/220
    result=dict(arm=args.arm,metrics=metric,selectivity=selection,selectivity_ci95=np.quantile(draws['fs+']-draws['fs-'],[.025,.975]).tolist(),json_valid=valid,errors=sum(bool(r.get('error')) for r in candidate),truncated=sum(bool(r.get('truncated')) for r in candidate),gates=dict(json_valid=valid>=.95,healthy_proxy_loss=metric['healthy']['drop']<=.02,fs_reduction=metric['fs+']['drop']>=.15,selectivity=selection>0),text='REQUIRES_INDEPENDENT_REVIEW',online='NOT_RUN',scope='exploratory: heads selected on this cohort; healthy proxy is schema-valid non-answer')
    result['numerical_pass']=all(result['gates'].values())
    result['input_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'baseline_A/generations.jsonl',ROOT/'runs'/args.arm/'generations.jsonl']}
    (ROOT/f'screen_{args.arm}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
