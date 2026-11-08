import os
os.environ.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

root = Path('/workspace/astra/moon-leak')
arms = ['head4_s05', 'head4_s0', 'random4_s0', 'raw4_s05', 'raw4_s0', 'random_raw4_s0']
labels = ['Selective × 0.5', 'Selective × 0', 'Random selective × 0', 'Raw strength × 0.5', 'Raw strength × 0', 'Random raw × 0']
data = [json.loads((root / f'screen_{arm}.json').read_text()) for arm in arms]
fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), sharey=True)
for ax, field, title in zip(axes, ['fs+', 'fs-', 'healthy'], ['False finishes: answer reduction', 'True finishes: answer reduction', 'Healthy actions: proxy loss']):
    for i, (arm, item) in enumerate(zip(arms, data)):
        metric = item['metrics'][field]
        mean = metric['drop'] * 100
        lo, hi = np.array(metric['drop_ci95']) * 100
        color = '#818b98' if arm.startswith('random') else '#176e99'
        ax.errorbar(mean, i, xerr=[[mean - lo], [hi - mean]], fmt='o', color=color, capsize=3, markersize=6)
    ax.axvline(0, color='#333333', lw=0.8)
    if field == 'fs+':
        ax.axvline(15, color='#ae6620', linestyle='--', lw=1)
    if field == 'healthy':
        ax.axvline(2, color='#ae6620', linestyle='--', lw=1)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel('Original − edited, percentage points')
    ax.grid(axis='x', alpha=0.15)
    ax.spines[['top', 'right']].set_visible(False)
axes[0].set_yticks(range(len(labels)), labels)
axes[0].invert_yaxis()
fig.suptitle('Frozen offline screen: head attenuation and matched random controls', fontsize=15)
fig.text(0.5, 0.02, '55 tasks × 4 paired seeds per arm; 95% task-bootstrap intervals. Exploratory selection and screening on the same cohort.\nHealthy proxy = schema-valid nonanswer; no downstream task success or online effect is measured.', ha='center', fontsize=9)
fig.tight_layout(rect=(0, 0.11, 1, 0.93))
fig.savefig(root / 'screens.png', dpi=180)
fig.savefig(root / 'screens.svg')
