"""V2b: the frozen Feci Guard verifier (Claude via `claude -p`) on the frozen verif_study corpus, final screenshot."""
import argparse
import concurrent.futures
import hashlib
import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / 'verif_study'
sys.path.insert(0, str(HERE.parent / 'feci_guard'))
import verifier  # noqa: E402  (frozen; called with its defaults)

LOCK = threading.Lock()


def one(episode, out):
    image = STUDY / episode['image_path']
    assert hashlib.sha256(image.read_bytes()).hexdigest() == episode['screenshot_sha256']
    started = datetime.now(timezone.utc).isoformat()
    v = verifier.verify(episode['instruction'], str(image))
    item = {'episode_id': episode['episode_id'], 'started_at': started, 'result': v}
    with LOCK:
        with out.open('a') as f:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(json.dumps({'id': episode['episode_id'], 'ok': v['ok'], 'verdict': v['verdict'], 'error': v['error'],
                      'latency': v.get('latency_s')}), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--out', default='claude_responses.jsonl')
    args = ap.parse_args()
    assert args.workers <= 4
    out = HERE / args.out
    episodes = json.loads((STUDY / 'manifest.json').read_text())
    done = set()
    if out.exists():
        done = {json.loads(l)['episode_id'] for l in out.read_text().splitlines() if l.strip()}
    jobs = [e for e in episodes if e['episode_id'] not in done][:args.limit]
    print(json.dumps({'jobs': len(jobs), 'done': len(done), 'model': verifier.DEFAULT_MODEL,
                      'timeout': verifier.TIMEOUT_S}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        for f in [pool.submit(one, e, out) for e in jobs]:
            f.result()


if __name__ == '__main__':
    main()
