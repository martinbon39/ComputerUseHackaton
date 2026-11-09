import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
import json
import signal
import sys
import time
from pathlib import Path
import psutil

arm = sys.argv[1]
assert arm in {'V05', 'V10', 'E025'}
state = Path('/workspace/astra/moon-vision')
pid = int((state / f'server_{arm}.pid').read_text())
process = psutil.Process(pid)
cmd = process.cmdline()
assert 'vllm.entrypoints.openai.api_server' in cmd
assert f'moon_vision_{arm}' in cmd and '8028' in cmd
owned = [(p.pid, p.create_time()) for p in [process] + process.children(recursive=True)]
process.send_signal(signal.SIGTERM)
deadline = time.monotonic() + 25
alive = []
while time.monotonic() < deadline:
    alive = []
    for child_pid, started in owned:
        try:
            p = psutil.Process(child_pid)
            if p.create_time() == started and p.status() != psutil.STATUS_ZOMBIE:
                alive.append(p)
        except psutil.NoSuchProcess:
            pass
    if not alive:
        break
    time.sleep(1)
for p in alive:
    p.kill()
print(json.dumps({'arm': arm, 'owned_pids': [p for p,_ in owned], 'forced_pids': [p.pid for p in alive]}))
