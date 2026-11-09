import json
import shutil
from pathlib import Path
import numpy as np
from analyze import SEED, N_BOOT, auc_2u, auc_draws, interval, sha, write_json

ROOT=Path(__file__).resolve().parent
core=ROOT/'RESULT_CORE.json'
if not core.exists():
    shutil.copyfile(ROOT/'RESULT.json',core)
r=json.loads(core.read_text())
oof=np.load(ROOT/'oof_scores.npz')
y=oof['y']
metadata=[row['metadata'] for row in json.loads((ROOT/'PREFLIGHT.json').read_text())['records']]
assert oof['context_ids'].tolist()==[row['context_id'] for row in metadata]
rng=np.random.default_rng(SEED)
weights={v:rng.multinomial(int((y==v).sum()),np.ones(int((y==v).sum()))/(y==v).sum(),size=N_BOOT) for v in [0,1]}
best=oof[r['best_probe']['key']]
best_draws=auc_draws(y,best,weights)
comparisons={}
for name,field in [('step_raw_increasing','step'),('prompt_length_raw_increasing','n_in'),('reasoning_length_raw_increasing','reasoning_tokens')]:
    score=np.array([row[field] for row in metadata])
    comparisons[name]={'difference':(auc_2u(y,best)-auc_2u(y,score))/760,
                       'ci95':interval(best_draws-auc_draws(y,score,weights))}
r['best_probe_vs_raw_metadata']=comparisons
r['model']={'name':'Hcompany/Holo-3.1-4B','revision':'8c88265a5a159bfd1492db9243733dd2e6e04a6e',
            'weights':'original','mode':'HF teacher forcing, logits only, no generation'}
r['execution']=json.loads((ROOT/'capture_receipt_156.json').read_text())
r['environment']=json.loads((ROOT/'ENVIRONMENT.json').read_text())
r['limitations']=[
    'All 702 MLP folds reached the pre-specified 300-iteration cap; the MLP findings are optimization-limited.',
    '39 unique tasks; observational labels can be confounded by application, step and context content.',
    'OOF bootstrap intervals are descriptive and do not refit models or correct selection.',
    'LOO pooled AUROC can suffer label-dependent fold-prevalence calibration; the prior-only baseline has AUROC zero.',
    'The 1000-permutation Bonferroni-adjusted test cannot reach .05, even with an arbitrarily strong signal.',
    'The anchoring ratio is a joint note+thought intervention and is not a probability share.',
    'Replacing all note/thought content does not isolate conclusion wording from descriptive details; repeated controls are artificial inputs.',
    'A null interaction is not an equivalence test or a proof that no discriminator exists.',
]
r['artifact_hashes'].update({name:sha(ROOT/name) for name in ['RESULT_CORE.json','finalize.py','ENVIRONMENT.json','MODEL_AUDIT.json','VERIFY_CAPTURE_FINAL.json','VERIFY_METHODS.json']})
if (ROOT/'MLP_SENSITIVITY.json').exists():
    r['mlp_optimization_sensitivity']=json.loads((ROOT/'MLP_SENSITIVITY.json').read_text())
    r['artifact_hashes']['MLP_SENSITIVITY.json']=sha(ROOT/'MLP_SENSITIVITY.json')
write_json(ROOT/'RESULT.json',r)
