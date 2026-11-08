import os
os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
import torch
torch.set_num_threads(2)
import json
from pathlib import Path
from evaluate import TEXT_PROMPTS,make_client,server_info,validate_server,call

ROOT=Path('/workspace/astra/moon-leak')
SOURCE='/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e'
model='moon_leak_Atext';url='http://127.0.0.1:8030/v1'
client=make_client(url)
info=server_info(url,client);validate_server(info,model,SOURCE)
path=ROOT/'baseline_A/text_controls.jsonl'
assert not path.exists()
with path.open('w') as f:
    for item in TEXT_PROMPTS:
        result=call(client,model,[dict(role='user',content=item['prompt'])],0)
        f.write(json.dumps(dict(model=model,server=info,prompt_id=item['id'],prompt=item['prompt'],seed=0,**result))+'\n');f.flush()
        print(json.dumps(dict(prompt_id=item['id'],**result)),flush=True)
