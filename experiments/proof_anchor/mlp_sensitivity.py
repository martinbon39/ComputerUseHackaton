import os
os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
import json
import time
import warnings
from pathlib import Path
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from analyze import load, prepare_folds, estimator, auc_summary, auc_draws, interval, write_json, sha, SEED, N_BOOT, LAYERS, POSITIONS

ROOT=Path(__file__).resolve().parent
metadata,x,y,_=load()
old=np.load(ROOT/'oof_scores.npz')
rng=np.random.default_rng(SEED)
weights={v:rng.multinomial(int((y==v).sum()),np.ones(int((y==v).sum()))/(y==v).sum(),size=N_BOOT) for v in [0,1]}
tic=time.monotonic()
results=[]
oof={}
diagnostics=[]
for li,layer in enumerate(LAYERS):
    for pi,position in enumerate(POSITIONS):
        folds,_=prepare_folds(x[:,li,pi],cosine=False)
        scores=[]
        key=f'L{layer}_{position}_mlp64_l2'
        for i,(train,xt,xv) in enumerate(folds):
            assert time.monotonic()-tic<1200,'20-minute sensitivity cap'
            model=estimator('mlp64_l2').set_params(max_iter=3000)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always',ConvergenceWarning)
                model.fit(xt,y[train])
            score=float(model.predict_proba(xv)[0,list(model.classes_).index(1)])
            scores.append(score)
            warn=[str(w.message) for w in caught if issubclass(w.category,ConvergenceWarning)]
            diagnostics.append({'key':key,'fold':i,'heldout_context':metadata[i]['context_id'],
                                'train_count':len(train),'n_iter':model.n_iter_,'loss':float(model.loss_),
                                'score':score,'old_score':float(old[key][i]),'convergence_warnings':warn})
        scores=np.array(scores)
        oof[key]=scores
        result={'key':key,'layer':layer,'position':position,**auc_summary(y,scores,weights),
                'original_auroc':auc_summary(y,old[key],weights)['auroc'],
                'delta_auroc_ci95':interval(auc_draws(y,scores,weights)-auc_draws(y,old[key],weights)),
                'max_absolute_score_change':float(np.max(abs(scores-old[key]))),
                'mean_absolute_score_change':float(np.mean(abs(scores-old[key]))),
                'warning_folds':sum(bool(d['convergence_warnings']) for d in diagnostics if d['key']==key)}
        results.append(result)
        print(json.dumps(result),flush=True)
        write_json(ROOT/'MLP_SENSITIVITY_PROGRESS.json',{'results':results,'folds':diagnostics})
assert len(results)==18 and len(diagnostics)==702
np.savez_compressed(ROOT/'mlp_sensitivity_oof.npz',y=y,**oof)
write_json(ROOT/'MLP_SENSITIVITY.json',{'status':'complete','post_result_optimization_sensitivity':True,
    'change':'max_iter=3000; all other estimator settings and train-only preprocessing unchanged',
    'n_fits':702,'results':results,'warning_folds':sum(bool(d['convergence_warnings']) for d in diagnostics),
    'best_descriptive':max(results,key=lambda r:r['statistic_2u']),
    'seconds':time.monotonic()-tic,'folds':diagnostics,
    'permutation_test':'not performed for this supplementary family; do not reuse the primary winner p-value',
    'source_hashes':{name:sha(ROOT/name) for name in ['mlp_sensitivity.py','analyze.py','MLP_OPTIMIZATION_AMENDMENT.md','mlp_sensitivity_oof.npz']}})
