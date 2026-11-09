import os
os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
import torch
torch.set_num_threads(2)
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path('/workspace/astra/moon-leak')
r=json.loads((root/'attribution_summary.json').read_text())
layers=list(range(3,32,4))
a=np.zeros((8,16));b=a.copy()
for h in r['heads']:
    a[layers.index(h['layer']),h['head']]=h['mean_fs_drop']
    b[layers.index(h['layer']),h['head']]=h['mean_true_drop']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
fig=plt.figure(figsize=(12,9),layout='constrained')
gs=fig.add_gridspec(3,2,height_ratios=[1,1,0.14])
v=max(np.abs(a).max(),np.abs(b).max())
for j,(data,title) in enumerate([(a,'Feasible false finishes · 19 tasks'),(b,'True finishes · 20 tasks')]):
    ax=fig.add_subplot(gs[0,j]);im=ax.imshow(data,cmap='RdBu_r',vmin=-v,vmax=v,aspect='auto')
    ax.set_title(title,loc='left',fontweight='bold');ax.set_xticks(range(16));ax.set_yticks(range(8),layers);ax.set_xlabel('Query head (zero-based)');ax.set_ylabel('Full-attention layer')
    for l,h in r['specs']['head4_s05']['heads']:ax.scatter(h,layers.index(l),s=100,facecolors='none',edgecolors='black',linewidths=1)
fig.colorbar(im,ax=fig.axes[:2],shrink=.85,label='Mean answer-margin loss (logits)')
ax=fig.add_subplot(gs[1,:]);d=sorted(r['delta'],key=lambda x:x['layer']);x=np.arange(len(d));width=.38
ax.bar(x-width/2,[v['mean_fs_drop'] for v in d],width,color='#c35b35',label='False finishes')
ax.bar(x+width/2,[v['mean_true_drop'] for v in d],width,color='#276a91',label='True finishes')
ax.axhline(0,color='black',linewidth=.6);ax.set_xticks(x,[v['layer'] for v in d]);ax.set_xlabel('DeltaNet layer (zero-based)');ax.set_ylabel('Mean answer-margin loss (logits)');ax.set_title('Final mixer-output patch from a same-length neutral note/thought context',loc='left',fontweight='bold');ax.legend(frameon=False)
ax=fig.add_subplot(gs[2,:]);ax.axis('off');ax.text(0,.65,'Whole note/thought neutralization: false +7.55 logits lost; true +8.18. Difference −0.64 [95% task bootstrap −2.13, +0.80].',fontsize=10)
ax.text(0,.05,'Black circles: selective top4. Positive loss means less preference for answer. Teacher-forced diagnosis; exploratory cohort, no online claim.',fontsize=9,color='#555555')
fig.suptitle('moon-leak · Direct final-query head effects are small and not selectively decisive',fontsize=15,fontweight='bold',x=.02,ha='left')
fig.savefig(root/'attribution.png',dpi=180);fig.savefig(root/'attribution.svg')
print('wrote attribution.png and attribution.svg')
