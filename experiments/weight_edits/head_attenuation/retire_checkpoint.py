import os
os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
import torch
torch.set_num_threads(2)
import argparse
import datetime
import json
import re
import shutil
from pathlib import Path

ROOT=Path('/workspace/astra/moon-leak');OUT=Path('/dev/shm/moon-leak')
ap=argparse.ArgumentParser();ap.add_argument('name');args=ap.parse_args()
assert re.fullmatch(r'[a-z0-9_]+',args.name)
p=(OUT/args.name).resolve();assert p.parent==OUT.resolve() and p.is_dir()
pidfile=ROOT/f'server_{args.name}.pid'
if pidfile.exists():
    pid=int(pidfile.read_text());cmdpath=Path(f'/proc/{pid}/cmdline')
    if cmdpath.exists():assert b'vllm.entrypoints.openai.api_server' not in cmdpath.read_bytes(), 'server still active'
assert (ROOT/f'verify_{args.name}.json').exists()
assert (ROOT/f'screen_{args.name}.json').exists()
size=sum(q.stat().st_size for q in p.rglob('*') if q.is_file())
shutil.rmtree(p)
with (ROOT/'retired.jsonl').open('a') as f:f.write(json.dumps(dict(name=args.name,bytes=size,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='screened; reproducible spec/build/verification retained'))+'\n')
print(json.dumps(dict(retired=args.name,bytes_freed=size)))
