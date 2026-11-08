import os
os.environ.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
import torch
torch.set_num_threads(2)
import argparse
import hashlib
import json
import shutil
import re
from pathlib import Path
from safetensors import safe_open
from safetensors.torch import save_file

SOURCE=Path('/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e')
ROOT=Path('/workspace/astra/moon-leak')
OUTROOT=Path('/dev/shm/moon-leak')


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(8*1024*1024),b''):h.update(data)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('spec',type=Path);args=ap.parse_args()
    spec=json.loads(args.spec.read_text())
    assert re.fullmatch(r'[a-z0-9_]+',spec['name'])
    assert type(spec['scale']) in [int,float] and spec['scale'] in [0,0.5]
    assert 2<=len(spec['heads'])<=6 and len(set(map(tuple,spec['heads'])))==len(spec['heads'])
    assert all(type(l) is int and type(h) is int and l in range(3,32,4) and h in range(16) for l,h in spec['heads'])
    final=OUTROOT/spec['name'];assert not final.exists(),final
    dest=OUTROOT/(spec['name']+'.building');assert not dest.exists(),dest
    assert shutil.disk_usage('/dev/shm').free>=10_000_000_000
    dest.mkdir(parents=True)
    for path in SOURCE.iterdir():
        if path.is_file() and path.suffix!='.safetensors':shutil.copy2(path,dest/path.name)
    idx=json.loads((SOURCE/'model.safetensors.index.json').read_text())
    targets={f'model.language_model.layers.{l}.self_attn.o_proj.weight':sorted(h for ll,h in spec['heads'] if ll==l) for l,_ in spec['heads']}
    assert all(k in idx['weight_map'] for k in targets)
    changed=[];unchanged=0
    for shard in sorted(set(idx['weight_map'].values())):
        with safe_open(SOURCE/shard,framework='pt',device='cpu') as sf:
            assert set(sf.keys())=={k for k,v in idx['weight_map'].items() if v==shard}, 'source index mismatch'
            metadata=sf.metadata();state={}
            for key in sf.keys():
                tensor=sf.get_tensor(key)
                if key in targets:
                    assert tensor.shape==(2560,4096)
                    patched=tensor.clone()
                    for head in targets[key]:patched[:,head*256:(head+1)*256]*=spec['scale']
                    changed.append(dict(key=key,heads=targets[key],changed_elements=int((patched!=tensor).sum()),dtype=str(tensor.dtype)))
                    tensor=patched
                else:unchanged+=1
                state[key]=tensor
            save_file(state,dest/shard,metadata=metadata)
        del state
    assert len(changed)==len(targets)
    os.rename(dest,final)
    dest=final
    receipt=dict(spec=spec,spec_sha256=digest(args.spec),source=str(SOURCE),output=str(dest),target_matrices=changed,unchanged_tensor_count=unchanged,files={p.name:digest(p) for p in sorted(dest.iterdir()) if p.is_file()})
    (ROOT/f'build_{spec["name"]}.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(output=str(dest),targets=changed,unchanged_tensors=unchanged)),flush=True)

if __name__=='__main__':main()
