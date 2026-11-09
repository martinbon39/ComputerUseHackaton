import os
os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
import torch
torch.set_num_threads(2)
import json
import random
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np

ROOT=Path('/workspace/astra/moon-leak')
rows=[json.loads(x) for x in (ROOT/'attribution.jsonl').read_text().splitlines()]
bases={r['context_id']:r for r in rows if r['kind']=='baseline'}
assert len(bases)==39 and Counter(r['label'] for r in bases.values())=={'fs+':19,'fs-':20}
assert {r['context_id'] for r in rows if r['kind']=='complete'}==set(bases)
for cid in bases:
    one=[r for r in rows if r['context_id']==cid]
    assert Counter(r['kind'] for r in one)=={'baseline':1,'mask_control':8,'head':128,'neutral':1,'delta':24,'complete':1}
    assert len({(r['layer'],r['head']) for r in one if r['kind']=='head'})==128


def table(kind):
    groups=defaultdict(lambda:defaultdict(list))
    for r in rows:
        if r['kind']==kind:groups[(r.get('layer'),r.get('head'))][r['label']].append(r['margin_drop'])
    result=[]
    for (layer,head),v in groups.items():
        assert len(v['fs+'])==19 and len(v['fs-'])==20
        p,n=np.array(v['fs+']),np.array(v['fs-'])
        result.append(dict(layer=layer,head=head,mean_fs_drop=float(p.mean()),mean_true_drop=float(n.mean()),selectivity=float(p.mean()-n.mean()),fs_positive=int((p>0).sum()),true_positive=int((n>0).sum()),fs_median=float(np.median(p)),true_median=float(np.median(n))))
    return sorted(result,key=lambda x:(-x['selectivity'],x['layer'] or -1,x['head'] or -1))

heads=table('head');delta=table('delta');neutral=table('neutral');controls=table('mask_control')
selected=[(r['layer'],r['head']) for r in heads if r['mean_fs_drop']>0 and r['selectivity']>0]
assert len(selected)>=6, 'no6 eligible selective heads'
rng=random.Random(261029609)
specs={}
for k in [2,4,6]:
    chosen=selected[:k]
    excluded=set(selected[:6])
    random_heads=[]
    for layer,count in sorted(Counter(l for l,h in chosen).items()):
        candidates=[h for h in range(16) if (layer,h) not in excluded]
        random_heads += [(layer,h) for h in rng.sample(candidates,count)]
    for scale in [0.5,0]:
        for control,hs in [(False,chosen),(True,random_heads)]:
            name=f'{"random" if control else "head"}{k}_s{str(scale).replace(".","")}'
            spec=dict(name=name,heads=hs,scale=scale,control=control,ranking='mean fs+ drop minus mean true-finish drop, matched zero-mask controls',random_seed=261029609)
            (ROOT/f'spec_{name}.json').write_text(json.dumps(spec,indent=2)+'\n');specs[name]=spec
baseline_descriptives={label:{key:float(np.mean([r[key] for r in bases.values() if r['label']==label])) for key in ['n_in','n_full','note_thought_tokens','neutralized_tokens','answer_margin']} for label in ['fs+','fs-']}
assert all(r['margin_drop']==0 for r in rows if r['kind']=='mask_control'), 'zero-mask control differs'
summary=dict(baseline_descriptives=baseline_descriptives,contexts=Counter(r['label'] for r in bases.values()),heads=heads,delta=delta,neutral=neutral,mask_controls=controls,max_cached_margin_error=max(r['cached_margin_abs_diff'] for r in bases.values()),max_cached_logits_error=max(r['cached_logits_max_abs_diff'] for r in bases.values()),specs=specs)
(ROOT/'attribution_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(top_heads=heads[:10],top_delta=delta[:6],neutral=neutral,max_cached_margin_error=summary['max_cached_margin_error']),indent=2))
