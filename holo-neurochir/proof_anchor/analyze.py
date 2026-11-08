import os
os.environ.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2')

import argparse
import hashlib
import json
import math
import time
import warnings
from pathlib import Path

import numpy as np
from scipy.linalg import svd
from scipy.stats import norm
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
SEED = 1729
N_BOOT = 10000
LAYERS = [8,12,16,20,24,28]
POSITIONS = ['prompt_end','reflection_end','note_onset']
MODELS = ['logistic_l2','knn3_cosine','knn5_cosine','mlp64_l2']


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interval(values):
    return np.quantile(values, [.025,.975]).tolist()


def summary(values, weights):
    values = np.asarray(values)
    estimates = weights @ values / len(values)
    return {'mean': float(values.mean()), 'ci95': interval(estimates), 'n_tasks': len(values)}


def auc_draws(y, scores, weights):
    p, n = scores[y == 1], scores[y == 0]
    pair = (p[:,None] > n[None,:]).astype(float) + .5 * (p[:,None] == n[None,:])
    return ((weights[1] @ pair) * weights[0]).sum(axis=1) / (len(p)*len(n))


def auc_2u(y,scores):
    p,n=scores[y==1],scores[y==0]
    return int(2*np.sum(p[:,None]>n[None,:])+np.sum(p[:,None]==n[None,:]))


def auc_summary(y, scores, weights):
    statistic=auc_2u(y,scores)
    return {'auroc': statistic/(2*int((y==1).sum())*int((y==0).sum())),
            'statistic_2u':statistic,'ci95': interval(auc_draws(y,scores,weights))}


def load():
    pre = json.loads((ROOT / 'PREFLIGHT.json').read_text())
    metadata = [r['metadata'] for r in pre['records']]
    ids = [r['context_id'] for r in metadata]
    assert len(ids) == 39 and len(set(r['task_id'] for r in metadata)) == 39
    records = [json.loads(line) for line in (ROOT / 'forwards.jsonl').read_text().splitlines()]
    assert len(records) == 156
    by_key = {(r['context_id'],r['condition']): r for r in records}
    assert len(by_key) == 156
    acts = []
    for id in ids:
        path = ROOT / 'captures' / f'{id}.npz'
        assert sha(path) == by_key[id,'a']['capture_sha256']
        value = np.load(path)
        assert value['layers'].tolist() == LAYERS
        acts.append(value['residual'])
    x = np.stack(acts).astype(np.float64)
    assert x.shape[:3] == (39,6,3) and np.isfinite(x).all()
    y = np.array([r['label'] == 'fs+' for r in metadata],dtype=int)
    margins = np.array([[by_key[id,c]['answer_margin'] for c in 'abcd'] for id in ids])
    for id in ids:
        for c in 'abcd':
            r=by_key[id,c]
            assert r['answer_margin'] == r['tool_logits']['answer'] - max(v for k,v in r['tool_logits'].items() if k!='answer')
    return metadata, x, y, margins


def anchoring(metadata, y, margins, weights):
    out = {'strata': {}, 'null_note_contexts': [r['context_id'] for r in metadata if r['note_is_null']]}
    contrasts = {'a_minus_b': margins[:,0]-margins[:,1], 'a_minus_c': margins[:,0]-margins[:,2],
                 'a_minus_d': margins[:,0]-margins[:,3]}
    for label, value in [('false_finish',1),('true_finish',0)]:
        take=y==value
        v=margins[take]
        w=weights[value]
        result={'n_tasks':int(take.sum()),'conditions':{},'deltas':{}}
        for i,c in enumerate('abcd'):
            result['conditions'][c]=summary(v[:,i],w)
            result['conditions'][c]['positive_margin_count']=int((v[:,i]>0).sum())
        for name,values in contrasts.items():
            result['deltas'][name]=summary(values[take],w)
        base=v[:,0]
        delta=contrasts['a_minus_b'][take]
        good=base!=0
        result['fraction_note_and_thought']={
            'zero_baseline_count':int((base==0).sum()), 'abs_baseline_below_one_count':int((abs(base)<1).sum()),
            'per_task_values':[float(d/b) if b!=0 else None for d,b in zip(delta,base)],
            'definition':'joint note+thought ablation; unbounded ratio, not a variance share'}
        if good.all():
            result['fraction_note_and_thought']['mean_of_ratios']=summary(delta/base,w)
        boot_base=w@base
        ratio_boot=np.full(len(boot_base),np.nan)
        np.divide(w@delta,boot_base,out=ratio_boot,where=boot_base!=0)
        finite=np.isfinite(ratio_boot)
        baseline_mean=float(base.mean())
        result['fraction_note_and_thought']['ratio_of_means']={
            'value':float(delta.mean()/baseline_mean) if baseline_mean!=0 else None,
            'ci95':interval(ratio_boot[finite]) if finite.any() else None,
            'status':'undefined' if baseline_mean==0 else 'unstable' if min(boot_base)<=0<=max(boot_base) else 'defined',
            'finite_bootstrap_replicates':int(finite.sum()),
            'zero_bootstrap_denominator_count':int((boot_base==0).sum()),
            'nonpositive_bootstrap_denominator_count':int((boot_base<=0).sum())}
        out['strata'][label]=result
    delta=contrasts['a_minus_b']
    observed=float(delta[y==1].mean()-delta[y==0].mean())
    boot=weights[1]@delta[y==1]/19-weights[0]@delta[y==0]/20
    rng=np.random.default_rng(SEED+1)
    null=[]
    for _ in range(N_BOOT):
        yp=rng.permutation(y)
        null.append(delta[yp==1].mean()-delta[yp==0].mean())
    out['interaction']={'false_minus_true_delta':observed,'ci95':interval(boot),
        'permutations':N_BOOT,'p_two_sided':float((1+np.sum(np.abs(null)>=abs(observed)))/(N_BOOT+1)),
        'interpretation':'test of difference, not equivalence or absence of a discriminator'}
    keep=np.array([not r['note_is_null'] for r in metadata])
    sens={}
    for label,value in [('false_finish',1),('true_finish',0)]:
        vals=delta[(y==value)&keep]
        rng=np.random.default_rng(SEED+2+value)
        w=rng.multinomial(len(vals),np.ones(len(vals))/len(vals),size=N_BOOT)
        sens[label]=summary(vals,w)
    out['nonnull_note_sensitivity_a_minus_b']=sens
    out['per_task']=[dict(context_id=r['context_id'],task_id=r['task_id'],label=r['label'],
                         margins=dict(zip('abcd',margins[i].tolist())),
                         deltas={k:float(v[i]) for k,v in contrasts.items()}) for i,r in enumerate(metadata)]
    return out


def prepare_folds(x,cosine=True):
    folds=[]
    for i in range(len(x)):
        train=np.flatnonzero(np.arange(len(x))!=i)
        scaler=StandardScaler().fit(x[train])
        xt=scaler.transform(x[train])
        xv=scaler.transform(x[i:i+1])
        if xt.shape[1] > len(train):
            _,s,vt=svd(xt,full_matrices=False,check_finite=True)
            rank=int((s>s[0]*1e-10).sum())
            basis=vt[:rank].T
            xt=xt@basis
            xv=xv@basis
        folds.append((train,xt,xv))
    if not cosine:
        return folds,None
    norms=np.linalg.norm(x,axis=1)
    assert (norms>0).all()
    z=x/norms[:,None]
    distance=1-z@z.T
    np.fill_diagonal(distance,np.inf)
    neighbors=np.argsort(distance,axis=1,kind='stable')[:,:5]
    assert all(i not in neighbors[i] for i in range(len(x)))
    return folds,neighbors


def estimator(name):
    if name=='logistic_l2':
        return LogisticRegression(C=.1,penalty='l2',solver='lbfgs',max_iter=1000,tol=1e-7,random_state=SEED)
    assert name=='mlp64_l2'
    return MLPClassifier(hidden_layer_sizes=(64,),activation='relu',alpha=10,solver='lbfgs',
                         max_iter=300,max_fun=15000,tol=1e-5,random_state=SEED)


def predict(y,name,folds,neighbors):
    if name.startswith('knn'):
        k=int(name[3])
        return y[neighbors[:,:k]].mean(axis=1),0
    scores=np.empty(len(y))
    n_warn=0
    for i,(train,xt,xv) in enumerate(folds):
        assert i not in train
        model=estimator(name)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always',ConvergenceWarning)
            model.fit(xt,y[train])
        n_warn+=sum(issubclass(w.category,ConvergenceWarning) for w in caught)
        scores[i]=model.predict_proba(xv)[0,list(model.classes_).index(1)]
    assert np.isfinite(scores).all()
    return scores,n_warn


def power():
    n,m=19,20
    max_rank_sum=(n+m)*(n+m+1)//2
    counts=np.zeros((n+1,max_rank_sum+1),dtype=np.int64)
    counts[0,0]=1
    for r in range(1,n+m+1):
        for k in range(min(r,n),0,-1):
            counts[k,r:]+=counts[k-1,:-r]
    distribution=counts[n,n*(n+1)//2:n*(n+1)//2+n*m+1]/math.comb(n+m,n)
    assert np.isclose(distribution.sum(),1)
    tail=distribution[::-1].cumsum()[::-1]
    levels={'one_sided_05':.05,'two_sided_05':.025,'familywise_72':.05/72}
    critical={k:int(np.flatnonzero(tail<=a)[0]) for k,a in levels.items()}
    rng=np.random.default_rng(SEED+3)
    n_sim=20000
    pn=rng.normal(size=(n_sim,n,1))
    nn=rng.normal(size=(n_sim,1,m))
    curve=[]
    for auc in np.round(np.arange(.5,.951,.005),3):
        shift=math.sqrt(2)*norm.ppf(auc)
        u=((pn+shift)>nn).sum(axis=(1,2))
        curve.append({'population_auroc':float(auc), **{
            k:float(((u>=c) | (u<=n*m-c)).mean()) if k=='two_sided_05' else float((u>=c).mean())
            for k,c in critical.items()}})
    mde={k:next((r['population_auroc'] for r in curve if r[k]>=.8),None) for k in levels}
    return {'model':'independent binormal oracle scores, equal variance, population AUC=Phi(delta/sqrt(2))',
            'n_positive':n,'n_negative':m,'simulations_per_effect':n_sim,'grid_step':.005,
            'alpha_positive_tail':levels,'critical_U':critical,
            'actual_null_rejection_probability':{k:float(tail[c])*(2 if k=='two_sided_05' else 1) for k,c in critical.items()},
            'minimum_auroc_for_80_percent_power':mde,'mc_se_at_power_80':math.sqrt(.8*.2/n_sim),
            'curve':curve,'limitation':'optimistic sensitivity of a pre-specified oracle score, not the learned probes',
            'actual_1000_permutation_bonferroni_power_at_05':0.0}


def run():
    tic=time.monotonic()
    metadata,x,y,margins=load()
    rng=np.random.default_rng(SEED)
    weights={value:rng.multinomial(int((y==value).sum()),np.ones(int((y==value).sum()))/(y==value).sum(),size=N_BOOT) for value in [0,1]}
    result={'manifest_sha256':sha(ROOT/'manifest.json'),'n_contexts':39,'n_tasks':39,
            'counts':{'false_finish':19,'true_finish':20},'bootstrap_replicates':N_BOOT,
            'positive_label':'false_finish','folds':'leave_one_task_out','layer_indices_zero_based':LAYERS,
            'anchoring':anchoring(metadata,y,margins,weights),'probes':[],'baselines':[]}
    oof={}
    cache={}
    meta_features={
        'step':np.array([[r['step']] for r in metadata]),
        'prompt_length':np.array([[r['n_in']] for r in metadata]),
        'reasoning_length':np.array([[r['reasoning_tokens']] for r in metadata]),
        'step_prompt_reasoning':np.array([[r['step'],r['n_in'],r['reasoning_tokens']] for r in metadata])}
    base_draws={}
    for name,features in meta_features.items():
        folds,_=prepare_folds(features,cosine=False)
        scores,nwarn=predict(y,'logistic_l2',folds,None)
        key='baseline_'+name
        oof[key]=scores
        base_draws[name]=auc_draws(y,scores,weights)
        result['baselines'].append({'name':name,'method':'L2 logistic C=.1',**auc_summary(y,scores,weights),'convergence_warnings':nwarn})
        if features.shape[1]==1:
            result['baselines'].append({'name':name+'_raw_increasing','method':'fixed metadata rank',
                                       **auc_summary(y,features[:,0],weights)})
    prior=(y.sum()-y)/(len(y)-1)
    result['baselines'].append({'name':'train_prevalence_only','method':'intercept-only LOO',**auc_summary(y,prior,weights)})
    result['baselines_warning']='LOO class prevalence differs with held-out label. Shrunk predictors can have AUROC below .5 solely from fold calibration; do not reverse their scores.'
    for li,layer in enumerate(LAYERS):
        for pi,position in enumerate(POSITIONS):
            folds,neighbors=prepare_folds(x[:,li,pi])
            cache[(layer,position)]=(folds,neighbors)
            for model in MODELS:
                start=time.monotonic()
                scores,nwarn=predict(y,model,folds,neighbors)
                key=f'L{layer}_{position}_{model}'
                oof[key]=scores
                stats=auc_summary(y,scores,weights)
                compared={}
                draws=auc_draws(y,scores,weights)
                for name in meta_features:
                    base=oof['baseline_'+name]
                    compared[name]={'difference':stats['auroc']-float(roc_auc_score(y,base)),
                                    'ci95':interval(draws-base_draws[name])}
                row=dict(key=key,layer=layer,position=position,model=model,**stats,
                         versus_baselines=compared,convergence_warnings=nwarn,fit_seconds=time.monotonic()-start)
                result['probes'].append(row)
                print(json.dumps({k:row[k] for k in ['key','auroc','ci95','convergence_warnings','fit_seconds']}),flush=True)
            write_json(ROOT/'ANALYSIS_PROGRESS.json',result)
    assert len(result['probes'])==72
    best=max(result['probes'],key=lambda r:r['statistic_2u'])
    result['best_probe']=dict(best,selection='highest observed OOF AUC among 72; exploratory, winner-biased')
    result['power']=power()
    result['analysis_seconds_before_permutation']=time.monotonic()-tic
    np.savez_compressed(ROOT/'oof_scores.npz',y=y,context_ids=np.array([r['context_id'] for r in metadata]),**oof)
    write_json(ROOT/'ANALYSIS_PREPERM.json',result)
    permutation(best,result,y,cache[(best['layer'],best['position'])])


def permutation(best,result,y,prepared):
    folds,neighbors=prepared
    path=ROOT/'permutations.jsonl'
    prior=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    assert all(r['index']==i and r['best_key']==best['key'] for i,r in enumerate(prior))
    rng=np.random.default_rng(SEED+4)
    for i in range(1000):
        yp=rng.permutation(y)
        if i<len(prior):
            assert prior[i]['labels']==yp.tolist()
            continue
        scores,nwarn=predict(yp,best['model'],folds,neighbors)
        statistic=auc_2u(yp,scores)
        row={'index':i,'best_key':best['key'],'auroc':statistic/760,'statistic_2u':statistic,
             'labels':yp.tolist(),'convergence_warnings':nwarn}
        with path.open('a') as stream:
            stream.write(json.dumps(row)+'\n')
            stream.flush()
        prior.append(row)
        if (i+1)%25==0:
            print(json.dumps({'permutations':i+1,'best':best['key']}),flush=True)
    null=np.array([r['auroc'] for r in prior])
    null_statistics=np.array([r['statistic_2u'] for r in prior])
    p=float((1+(null_statistics>=best['statistic_2u']).sum())/1001)
    result['permutation']={'selected_probe':best['key'],'n_permutations':1000,
         'refitted_in_every_permutation':True,'unit':'task','tail':'one-sided positive discrimination',
         'p_unadjusted':p,'p_bonferroni_72':min(1.,p*72),'minimum_possible_adjusted_p':72/1001,
         'null_mean':float(null.mean()),'null_ci95':interval(null),'observed_auroc':best['auroc'],
         'selection_warning':'Selected winner p is exploratory; Bonferroni is conservative and cannot reach .05 with 1000 permutations.'}
    result['artifact_hashes']={name:sha(ROOT/name) for name in ['PROTOCOL.md','run_capture.py','analyze.py','PREFLIGHT.json',
                                   'SOURCE_AUDIT.json','forwards.jsonl','oof_scores.npz','permutations.jsonl']}
    write_json(ROOT/'RESULT.json',result)
    print(json.dumps({'done':True,'best':best['key'],'auc':best['auroc'],'p':p}),flush=True)


def resume():
    result=json.loads((ROOT/'ANALYSIS_PREPERM.json').read_text())
    metadata,x,y,margins=load()
    best=result['best_probe']
    li=LAYERS.index(best['layer'])
    pi=POSITIONS.index(best['position'])
    permutation(best,result,y,prepare_folds(x[:,li,pi]))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--resume-permutation',action='store_true')
    args=parser.parse_args()
    resume() if args.resume_permutation else run()
