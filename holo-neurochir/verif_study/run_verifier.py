import argparse
import base64
import concurrent.futures
import hashlib
import json
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROMPT = ('Task: {instruction}. Here is the final screen. List every requirement of the task, '
          'then for each say whether the screen shows it is satisfied (yes / no / cannot tell). '
          'Finally answer VERDICT: COMPLETE or INCOMPLETE.')
LOCK = threading.Lock()
STOP = threading.Event()
LAST_PROGRESS = time.monotonic()


def now():
    return datetime.now(timezone.utc).isoformat()


def append(path, item):
    with LOCK:
        with path.open('a') as handle:
            handle.write(json.dumps(item, ensure_ascii=False) + '\n')
            handle.flush()


def request_one(episode, replicate, args):
    global LAST_PROGRESS
    key = f'{episode["episode_id"]}__{replicate}'
    image_bytes = (ROOT / episode['image_path']).read_bytes()
    assert hashlib.sha256(image_bytes).hexdigest() == episode['screenshot_sha256']
    prompt = PROMPT.format(instruction=episode['instruction'])
    seed = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % (2**31 - 1)
    payload = {
        'model': 'Holo-3.1-4B',
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {
                'url': 'data:image/png;base64,' + base64.b64encode(image_bytes).decode(),
            }},
        ]}],
        'temperature': 0.0 if replicate == 't0' else 0.8,
        'top_p': 1.0, 'top_k': -1,
        'presence_penalty': 0.0, 'frequency_penalty': 0.0, 'repetition_penalty': 1.0,
        'seed': seed, 'max_tokens': args.max_tokens, 'stream': False,
        'chat_template_kwargs': {'enable_thinking': True},
    }
    encoded = json.dumps(payload, ensure_ascii=False).encode()
    metadata = {k: v for k, v in payload.items() if k != 'messages'}
    metadata.update({'prompt': prompt, 'image_path': episode['image_path'],
                     'image_sha256': episode['screenshot_sha256'],
                     'request_body_sha256': hashlib.sha256(encoded).hexdigest()})
    base = {'request_id': key, 'episode_id': episode['episode_id'],
            'replicate': replicate, 'request': metadata}
    for attempt in range(1, 3):
        if STOP.is_set() or datetime.now(timezone.utc).timestamp() >= args.deadline_ts:
            return
        started = time.monotonic()
        item = dict(base, attempt=attempt, started_at=now())
        try:
            request = urllib.request.Request(args.endpoint + '/v1/chat/completions', encoded,
                                             {'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=240) as response:
                raw = response.read().decode()
            item.update({'response': json.loads(raw), 'response_raw': raw, 'status': 'ok'})
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            item.update({'status': 'transport_error', 'error': str(error)})
            if isinstance(error, urllib.error.HTTPError):
                item['error_body'] = error.read().decode(errors='replace')[:4000]
        item.update({'finished_at': now(), 'elapsed_seconds': time.monotonic() - started})
        append(ROOT / 'attempts.jsonl', item)
        if item['status'] == 'ok' or attempt == 2:
            append(ROOT / 'responses.jsonl', item)
            with LOCK:
                LAST_PROGRESS = time.monotonic()
            print(json.dumps({'request_id': key, 'status': item['status'],
                              'elapsed': round(item['elapsed_seconds'], 2)}), flush=True)
            return
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--endpoint', default='http://127.0.0.1:8000')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--max-tokens', type=int, default=4096)
    parser.add_argument('--pilot', action='store_true')
    parser.add_argument('--deadline', default='2026-11-08T09:45:00+00:00')
    args = parser.parse_args()
    assert 1 <= args.workers <= 4
    args.deadline_ts = datetime.fromisoformat(args.deadline).timestamp()
    episodes = json.loads((ROOT / 'manifest.json').read_text())
    done = set()
    if (ROOT / 'responses.jsonl').exists():
        done = {json.loads(line)['request_id'] for line in (ROOT / 'responses.jsonl').read_text().splitlines() if line.strip()}
    jobs = [(episode, replicate) for replicate in ['t0', 't08_r1', 't08_r2', 't08_r3'] for episode in episodes
            if f'{episode["episode_id"]}__{replicate}' not in done]
    if args.pilot:
        jobs = jobs[:1]
    print(json.dumps({'started_at': now(), 'remaining_jobs': len(jobs), 'already_done': len(done),
                      'workers': args.workers, 'deadline': args.deadline}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = set()
        source = iter(jobs)
        exhausted = False
        while pending or not exhausted:
            if datetime.now(timezone.utc).timestamp() >= args.deadline_ts or time.monotonic() - LAST_PROGRESS >= 1200:
                STOP.set()
            while not exhausted and not STOP.is_set() and len(pending) < args.workers:
                job = next(source, None)
                if job is None:
                    exhausted = True
                else:
                    pending.add(pool.submit(request_one, *job, args))
            if STOP.is_set():
                exhausted = True
            if pending:
                finished, pending = concurrent.futures.wait(pending, timeout=30,
                    return_when=concurrent.futures.FIRST_COMPLETED)
                for future in finished:
                    future.result()
    print(json.dumps({'finished_at': now(), 'stopped_early': STOP.is_set()}), flush=True)


if __name__ == '__main__':
    main()
