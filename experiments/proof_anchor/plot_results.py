import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'RESULT.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig=plt.figure(figsize=(9,11),layout='constrained')
grid=fig.add_gridspec(2,2,height_ratios=[1,2.4])
ax=fig.add_subplot(grid[0,0])
for label,title,color,offset in [('false_finish','False finish (19)','#ba3d38',-.07),('true_finish','True finish (20)','#176b86',.07)]:
    stats=r['anchoring']['strata'][label]['conditions']
    means=np.array([stats[c]['mean'] for c in 'abcd'])
    bounds=np.array([stats[c]['ci95'] for c in 'abcd'])
    ax.errorbar(np.arange(4)+offset,means,yerr=np.stack([means-bounds[:,0],bounds[:,1]-means]),
                marker='o',capsize=3,color=color,label=title,linewidth=1.3)
ax.axhline(0,color='#888888',linewidth=.8)
ax.set(xticks=range(4),xticklabels=['a: Original','b: Neutral\nN+T','c: Not done\nN+T','d: Neutral\nreflection'],
       ylabel='Answer margin (logits)',title='A. Conditional tool margin')
ax.legend(frameon=False,fontsize=8)
ax=fig.add_subplot(grid[0,1])
rows=r['anchoring']['per_task']
rng=np.random.default_rng(1729)
for j,(label,color) in enumerate([('fs+','#ba3d38'),('fs-','#176b86')]):
    vals=np.array([row['deltas']['a_minus_b'] for row in rows if row['label']==label])
    ax.scatter(j+rng.uniform(-.12,.12,len(vals)),vals,color=color,s=15,alpha=.65)
    summary=r['anchoring']['strata']['false_finish' if j==0 else 'true_finish']['deltas']['a_minus_b']
    mean=summary['mean'];low,high=summary['ci95']
    ax.errorbar(j+.2,mean,yerr=np.array([[mean-low],[high-mean]]),color='black',marker='D',capsize=4,markersize=5)
ax.axhline(0,color='#888888',linewidth=.8)
ax.set(xticks=[0,1],xticklabels=['False finish','True finish'],ylabel='Original − neutral note+thought (logits)',title='B. Paired anchoring effect by task')
ax=fig.add_subplot(grid[1,:])
models=['logistic_l2','knn3_cosine','knn5_cosine','mlp64_l2']
positions=['prompt_end','reflection_end','note_onset']
cells=[(layer,position) for layer in r['layer_indices_zero_based'] for position in positions]
matrix=np.array([[next(p['auroc'] for p in r['probes'] if p['layer']==layer and p['position']==position and p['model']==model)
                  for model in models] for layer,position in cells])
im=ax.imshow(matrix,vmin=0,vmax=1,cmap='RdBu',aspect='auto')
for i in range(len(cells)):
    for j in range(4):
        ax.text(j,i,f'{matrix[i,j]:.3f}',ha='center',va='center',color='white' if abs(matrix[i,j]-.5)>.28 else '#222222')
names={'prompt_end':'Prompt end','reflection_end':'Reflection end','note_onset':'Note onset'}
ax.set(xticks=range(4),xticklabels=['Logistic L2','Cosine kNN3','Cosine kNN5','MLP64 L2'],
       yticks=range(len(cells)),yticklabels=[f'L{layer:02d} · {names[position]}' for layer,position in cells],
       title='C. Exploratory leave-one-task-out AUROC (positive = false finish)')
for y in np.arange(2.5,18,3):
    ax.axhline(y,color='white',linewidth=1.5)
fig.colorbar(im,ax=ax,label='AUROC',shrink=.65)
fig.suptitle('Holo-3.1-4B original · 39 feasible tasks · teacher-forced replay',fontsize=13)
fig.supxlabel('N+T = note and thought. A–B: 95% task-bootstrap intervals. C: 72 exploratory probes.\n'
               'All MLP fits reached the 300-iteration cap; LOO calibration and selection limit inference.\n'
               'Layer indices are zero-based. No generation or OSWorld improvement is measured.',fontsize=8)
fig.savefig(ROOT/'FIGURE.png',dpi=180)
fig.savefig(ROOT/'FIGURE.svg')
