"""V2a: Holo4-27B as judge on the frozen verif_study corpus, same prompt and same final screenshot, T=0."""
import argparse
import base64
import concurrent.futures
import hashlib
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / 'verif_study'
sys.path.insert(0, str(STUDY))
from run_verifier import PROMPT  # noqa: E402  (the frozen V1 prompt, imported, not copied)

ENDPOINT = 'https://martinbon39--holo-judge-serve.us-east.modal.run/v1/chat/completions'
LOCK = threading.Lock()


def now():
    return datetime.now(timezone.utc).isoformat()


def one(episode, args, key, out):
    image = (STUDY / episode['image_path']).read_bytes()
    assert hashlib.sha256(image).hexdigest() == episode['screenshot_sha256']
    prompt = PROMPT.format(instruction=episode['instruction'])
    payload = {
        'model': 'Holo4-27B', 'temperature': 0.0, 'top_p': 1.0, 'max_tokens': args.max_tokens, 'stream': False,
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + base64.b64encode(image).decode()}}]}],
        'chat_template_kwargs': {'enable_thinking': not args.no_thinking},
    }
    body = json.dumps(payload).encode()
    meta = {k: v for k, v in payload.items() if k != 'messages'}
    meta.update(prompt=prompt, image_sha256=episode['screenshot_sha256'])
    item = {'request_id': episode['episode_id'] + '__t0', 'episode_id': episode['episode_id'], 'replicate': 't0',
            'request': meta}
    for attempt in (1, 2):
        start = time.monotonic()
        item.update(attempt=attempt, started_at=now())
        try:
            req = urllib.request.Request(ENDPOINT, body, {'Content-Type': 'application/json',
                                                          'Authorization': 'Bearer ' + key})
            with urllib.request.urlopen(req, timeout=args.timeout) as r:
                item.update(response=json.loads(r.read().decode()), status='ok')
                item.pop('error', None)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
            item.update(status='transport_error', error=str(e)[:500])
            if isinstance(e, urllib.error.HTTPError):
                item['error_body'] = e.read().decode(errors='replace')[:2000]
        item.update(finished_at=now(), elapsed_seconds=time.monotonic() - start)
        if item['status'] == 'ok':
            break
        time.sleep(3)
    with LOCK:
        with out.open('a') as f:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    fr = item.get('response', {}).get('choices', [{}])[0].get('finish_reason')
    print(json.dumps({'id': item['request_id'], 'status': item['status'], 'finish': fr,
                      'elapsed': round(item['elapsed_seconds'], 1)}), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=12)
    ap.add_argument('--max-tokens', type=int, default=4096)
    ap.add_argument('--timeout', type=float, default=300)
    ap.add_argument('--no-thinking', action='store_true')
    ap.add_argument('--limit', type=int)
    ap.add_argument('--out', default='holo4_responses.jsonl')
    args = ap.parse_args()
    assert args.workers <= 12
    key = (Path.home() / '.holo_modal_key').read_text().strip()
    out = HERE / args.out
    episodes = json.loads((STUDY / 'manifest.json').read_text())
    done = set()
    if out.exists():
        done = {json.loads(l)['episode_id'] for l in out.read_text().splitlines() if l.strip()}
    jobs = [e for e in episodes if e['episode_id'] not in done][:args.limit]
    print(json.dumps({'started_at': now(), 'jobs': len(jobs), 'done': len(done)}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        for f in [pool.submit(one, e, args, key, out) for e in jobs]:
            f.result()
    print(json.dumps({'finished_at': now()}), flush=True)


if __name__ == '__main__':
    main()
