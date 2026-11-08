import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
import torch
torch.set_num_threads(2)
import json
from pathlib import Path
import build_vision as builder

work = Path('/workspace/astra/moon-vision')
h, q, cua = [builder.Weights(p) for p in [builder.HOLO, builder.QWEN, builder.CUA]]
builder.compatible([h, q, cua])
sources = json.loads((work / 'source_provenance.json').read_text())
for model in [h, q, cua]:
    assert model.provenance() == sources[str(model.path)]
result = builder.build(h, q, h, 0.25, Path('/dev/shm/moon-vision/holo_g025'), sources)
for model in [h, q, cua]:
    assert model.provenance() == sources[str(model.path)]
record = json.loads((work / 'CHECKPOINTS.json').read_text())
record['outputs'].append(result)
record['ares_amendment'] = {'message_id': 6520, 'formula': 'Holo_vis + 0.25*(Holo_vis-Qwen_vis)', 'cap': 3}
builder.write_json(work / 'CHECKPOINTS.json', record)
print('COMPLETE EXTRAPOLATION', flush=True)
