import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / 'compile_cache'
for key, sub in {'TRITON_CACHE_DIR': 'triton', 'TORCHINDUCTOR_CACHE_DIR': 'inductor',
                 'CUDA_CACHE_PATH': 'cuda', 'TMPDIR': 'tmp', 'VLLM_CACHE_ROOT': 'vllm'}.items():
    path = CACHE / sub
    path.mkdir(parents=True, exist_ok=True)
    os.environ[key] = str(path)
os.environ.update(HF_HOME='/workspace/hf', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                  OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                  TOKENIZERS_PARALLELISM='false')

import argparse
import base64
import datetime
import gzip
import hashlib
import io
import json
import re
import sys
import time

sys.path.insert(0, '/workspace/astra/astra-broad')
from anchoring import splice
from ceiling import MODEL, extend, sha
from holo.osw_replay import assistant_json, tool_output, EVICTED
import numpy as np
import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor

POWER = Path('/workspace/astra/astra-power')
EXPECTED = '2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0'
LAYERS = [8, 12, 16, 20, 24, 28]
NEUTRAL = 'Observing the current screen.'
COUNTER = 'The task is not complete yet; I still need to inspect the screen.'


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def encode(tok, text):
    return tok(text, add_special_tokens=False)['input_ids']


def prefix_for(step):
    action = assistant_json(step)
    match = re.search(r'"tool_name":"', action)
    assert match and action[match.end():].startswith('answer')
    return action[:match.end()]


def length_matched(tok, original, phrase, measure):
    target = measure(original)
    filler_ids = encode(tok, ' '.join([phrase] * (target + 10)))
    guess = len(encode(tok, original))
    for n in sorted(range(1, target + 20), key=lambda n: abs(n - guess)):
        base = tok.decode(filler_ids[:n], skip_special_tokens=False)
        for ending in ['', '.', ' ', ' screen', ' now']:
            text = base + ending
            if measure(text) == target:
                assert '\ufffd' not in text
                return text
    raise AssertionError(('no exact contextual length', target, phrase))


def note_value_start(prefix, step):
    expected = '{"note":'
    assert prefix.startswith(expected)
    return len(expected) + (1 if isinstance(step['note'], str) else 0)


def make_variants(tok, step):
    reason = (step.get('reasoning') or '').strip() + '\n</think>\n\n'
    original_prefix = prefix_for(step)
    variants = {'a': (reason, original_prefix)}
    for key, phrase in [('b', NEUTRAL), ('c', COUNTER)]:
        changed = dict(step)
        if step['note'] is not None:
            def note_measure(text):
                temp = dict(changed, note=text)
                p = prefix_for(temp).split(',"thought":')[0] + ',"thought":'
                return len(encode(tok, reason + p))
            changed['note'] = length_matched(tok, step['note'], phrase, note_measure)
        def thought_measure(text):
            return len(encode(tok, reason + prefix_for(dict(changed, thought=text))))
        changed['thought'] = length_matched(tok, step['thought'], phrase, thought_measure)
        variants[key] = (reason, prefix_for(changed))
    closing = '\n</think>\n\n'
    body = reason[:-len(closing)]
    changed_reason = length_matched(tok, body, NEUTRAL,
                                   lambda text: len(encode(tok, text + closing + original_prefix))) + closing
    variants['d'] = (changed_reason, original_prefix)
    lengths = {key: len(encode(tok, r + p)) for key, (r, p) in variants.items()}
    assert len(set(lengths.values())) == 1, lengths
    assert len(encode(tok, variants['d'][0])) == len(encode(tok, reason))
    return variants


def load_source(row, context):
    d = ROOT / 'sources' / row['context_id']
    for name, digest in {**row['source_hashes'], **row['screenshot_sha256']}.items():
        assert sha(d / name) == digest
    steps = [json.loads(line) for line in (d / 'traj.jsonl').read_text().splitlines()]
    assert [s['step_num'] for s in steps] == list(range(1, len(steps) + 1))
    assert all(s['tool_name'] != 'answer' for s in steps[:-1])
    assert all(s['tool_call']['tool_name'] == s['tool_name'] for s in steps)
    assert steps[row['t']]['tool_name'] == 'answer'
    blob = gzip.decompress((POWER / 'payloads' / (context['payload_sha256'] + '.json.gz')).read_bytes())
    assert hashlib.sha256(blob).hexdigest() == context['payload_sha256']
    messages = json.loads(blob)
    assert messages[0] == {'role': 'system', 'content': (d / 'system_prompt.txt').read_text()}
    assert len(messages) == 3 * row['t'] + 2
    for i in range(row['t'] + 1):
        obs = messages[1 + 3*i]
        assert obs['role'] == 'user'
        assert obs['content'][0] == {'type': 'text', 'text': '<observation>\n'}
        assert obs['content'][2] == {'type': 'text', 'text': '\n</observation>'}
        chunk = obs['content'][1]
        if i < row['t'] - 2:
            assert chunk == {'type': 'text', 'text': EVICTED}
        else:
            assert chunk['type'] == 'image_url'
            url = chunk['image_url']['url']
            assert url.startswith('data:image/png;base64,')
            img = Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGB')
            orig = Image.open(d / steps[i]['screenshot_file']).convert('RGB')
            assert np.array_equal(np.asarray(img), np.asarray(orig))
            obs['content'][1] = {'type': 'image', 'image': img}
        if i < row['t']:
            assert messages[2 + 3*i] == {'role': 'assistant', 'content': assistant_json(steps[i])}
            assert messages[3 + 3*i] == {'role': 'user', 'content': f'<tool_output tool="{steps[i]["tool_name"]}">\n{tool_output(steps[i])}\n</tool_output>'}
    return steps[row['t']], messages


def tool_tokens(tok, system, suffix):
    schema = json.loads(system.split('<output_format>\n```json\n')[1].split('\n```\n</output_format>')[0])
    names = set()
    def walk(obj):
        if isinstance(obj, dict):
            prop = obj.get('properties', {}).get('tool_name', {})
            if 'const' in prop:
                names.add(prop['const'])
            names.update(prop.get('enum', []))
            for val in obj.values():
                walk(val)
        elif isinstance(obj, list):
            for val in obj:
                walk(val)
    walk(schema)
    assert 'answer' in names and len(names) > 2
    prefix_ids = encode(tok, suffix)
    tokens = {}
    lengths = {}
    for name in sorted(names):
        ids = encode(tok, suffix + name + '"')
        assert ids[:len(prefix_ids)] == prefix_ids
        tokens[name] = ids[len(prefix_ids)]
        lengths[name] = len(encode(tok, name))
    assert tokens['answer'] not in [v for k, v in tokens.items() if k != 'answer']
    return tokens, lengths


def prepare(processor, row, context):
    step, messages = load_source(row, context)
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors='pt', enable_thinking=True)
    tok = processor.tokenizer
    variants = make_variants(tok, step)
    reason, prefix = variants['a']
    tokens, tool_lengths = tool_tokens(tok, messages[0]['content'], reason + prefix)
    extra = tok(reason + prefix, add_special_tokens=False, return_tensors='pt')['input_ids']
    original = extend(prompt, extra)
    n = prompt['input_ids'].shape[1]
    rid = encode(tok, reason)
    offsets = tok(reason + prefix, add_special_tokens=False, return_offsets_mapping=True)['offset_mapping']
    onset_char = len(reason) + note_value_start(prefix, step)
    first_content = next(i for i, (start, end) in enumerate(offsets) if end > onset_char)
    positions = [n-1, n+len(rid)-1, n+first_content-1]
    assert offsets[first_content-1][1] <= onset_char
    assert extra[0, :len(rid)].tolist() == rid
    meta = dict(context_id=row['context_id'], task_id=row['task_id'], label=row['label'], step=row['t'],
                n_in=n, reasoning_tokens=len(rid), original_suffix_tokens=extra.shape[1],
                total_tokens=original['input_ids'].shape[1], positions=positions,
                note_is_null=step['note'] is None, note_value_start_char=onset_char,
                note_onset_token_offset=list(offsets[first_content-1]), tool_token_ids=tokens,
                tool_name_token_lengths=tool_lengths, payload_sha256=context['payload_sha256'],
                input_ids_sha256=hashlib.sha256(original['input_ids'].numpy().tobytes()).hexdigest())
    all_variants = {}
    for key, (r, p) in variants.items():
        full, pos, metadata = splice(processor, original, meta, r, p)
        assert full['input_ids'].shape == original['input_ids'].shape
        assert torch.equal(full['input_ids'][0, :n], original['input_ids'][0, :n])
        if key == 'a':
            assert all(torch.equal(value, full[k]) for k, value in original.items() if torch.is_tensor(value))
        all_variants[key] = dict(reason=r, prefix=p, input_ids_sha256=metadata['input_ids_sha256'],
                                 total_tokens=full['input_ids'].shape[1])
    return original, positions, meta, all_variants


def inputs_and_rows():
    assert sha(ROOT / 'manifest.json') == EXPECTED
    assert sha(POWER / 'cohort/manifest.json') == EXPECTED
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    frozen = json.loads((POWER / 'FROZEN.json').read_text())
    assert frozen['cohort_sha256'] == EXPECTED
    contexts = {c['row']['context_id']: c for c in frozen['contexts']}
    rows = [r for r in manifest['train'] if r['label'] in ('fs+', 'fs-')]
    assert len(rows) == 39 and len({r['task_id'] for r in rows}) == 39
    assert sum(r['label'] == 'fs+' for r in rows) == 19
    for row in rows:
        assert row == contexts[row['context_id']]['row']
        assert row['feasible'] and 'infeasible' not in json.dumps(row['evaluator_func']).lower()
    return rows, contexts


def preflight():
    rows, contexts = inputs_and_rows()
    processor = AutoProcessor.from_pretrained(MODEL)
    records = []
    for row in rows:
        original, positions, meta, variants = prepare(processor, row, contexts[row['context_id']])
        records.append({'metadata': meta, 'variants': variants})
        print(json.dumps({'preflight': row['context_id'], 'tokens': meta['total_tokens'], 'null_note': meta['note_is_null']}), flush=True)
        del original
    write_json(ROOT / 'PREFLIGHT.json', {'records': records, 'manifest_sha256': EXPECTED,
               'source_code_sha256': {str(p): sha(p) for p in [Path(__file__), Path('/workspace/astra/astra-broad/anchoring.py'),
                    Path('/workspace/astra/astra-broad/ceiling.py'), Path('/workspace/projet/holo/osw_replay.py')]}})


def capture(limit):
    rows, contexts = inputs_and_rows()
    preflight = json.loads((ROOT / 'PREFLIGHT.json').read_text())
    expected = {r['metadata']['context_id']: r for r in preflight['records']}
    for p, digest in preflight['source_code_sha256'].items():
        assert sha(p) == digest
    processor = AutoProcessor.from_pretrained(MODEL)
    torch.cuda.set_per_process_memory_fraction(18e9 / torch.cuda.get_device_properties(0).total_memory)
    model = AutoModelForImageTextToText.from_pretrained(MODEL, dtype=torch.bfloat16).to('cuda').eval()
    assert len(model.model.language_model.layers) == 32
    live = {'positions': [], 'capture': False, 'acts': {}}
    def hook(index):
        def call(module, args, output):
            if live['capture']:
                value = output[0] if isinstance(output, tuple) else output
                live['acts'][index] = value[0, live['positions']].float().cpu().numpy()
        return call
    handles = [model.model.language_model.layers[i].register_forward_hook(hook(i)) for i in LAYERS]
    (ROOT / 'captures').mkdir(exist_ok=True)
    results = ROOT / 'forwards.jsonl'
    previous = [json.loads(line) for line in results.read_text().splitlines()] if results.exists() else []
    done = {(r['context_id'], r['condition']) for r in previous}
    assert len(done) == len(previous)
    assert all((ROOT / 'captures' / f'{r["context_id"]}.npz').exists() for r in previous if r['condition'] == 'a')
    started_file = ROOT / 'started.jsonl'
    started = len(started_file.read_text().splitlines()) if started_file.exists() else 0
    count = 0
    for row in rows:
        if all((row['context_id'], c) in done for c in 'abcd'):
            continue
        original, positions, meta, variants = prepare(processor, row, contexts[row['context_id']])
        assert meta == expected[row['context_id']]['metadata']
        assert variants == expected[row['context_id']]['variants']
        original = {k: v.to('cuda') if torch.is_tensor(v) else v for k,v in original.items()}
        for condition in 'abcd':
            if (row['context_id'], condition) in done:
                continue
            assert datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M') < '10:05'
            assert not (ROOT / 'STOP').exists() and not Path('/workspace/astra/4b/STOP_GPU').exists()
            assert started < 160
            v = variants[condition]
            full, _, metadata = splice(processor, original, meta, v['reason'], v['prefix'])
            assert metadata['input_ids_sha256'] == v['input_ids_sha256']
            started += 1
            with started_file.open('a') as stream:
                stream.write(json.dumps({'forward': started, 'context_id': row['context_id'], 'condition': condition,
                             'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            live.update(positions=positions, capture=condition == 'a', acts={})
            tic = time.monotonic()
            with torch.inference_mode():
                output = model(**full, use_cache=False, logits_to_keep=1)
            logits = output.logits[0, -1].float().cpu()
            tools = {name: float(logits[index]) for name,index in meta['tool_token_ids'].items()}
            others = {name: val for name,val in tools.items() if name != 'answer'}
            record = dict(context_id=row['context_id'], task_id=row['task_id'], label=row['label'],
                       condition=condition, forward=started, answer_margin=tools['answer']-max(others.values()),
                       tool_logits=tools, best_other=max(others,key=others.get), input_ids_sha256=v['input_ids_sha256'],
                       total_tokens=meta['total_tokens'], seconds=time.monotonic()-tic)
            assert all(np.isfinite(list(tools.values())))
            if condition == 'a':
                acts = np.stack([live['acts'][i] for i in LAYERS])
                assert acts.shape[:2] == (6,3) and np.isfinite(acts).all()
                path = ROOT / 'captures' / f'{row["context_id"]}.npz'
                assert not path.exists()
                np.savez_compressed(path, residual=acts, positions=np.array(positions), layers=np.array(LAYERS))
                record['capture_sha256'] = sha(path)
            with results.open('a') as stream:
                stream.write(json.dumps(record) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            print(json.dumps({k:record[k] for k in ['context_id','condition','forward','answer_margin','seconds']}), flush=True)
            del full, output, logits
            count += 1
        del original
        if limit and count >= limit * 4:
            break
    for handle in handles:
        handle.remove()
    write_json(ROOT / f'capture_receipt_{len(previous)+count:03d}.json',
               {'completed': len(previous)+count, 'started': started, 'model': MODEL,
                'dtype': str(model.dtype), 'device': str(model.device), 'torch': torch.__version__,
                'max_memory_allocated': torch.cuda.max_memory_allocated(), 'layers_zero_based': LAYERS,
                'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['preflight','capture'])
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()
    preflight() if args.command == 'preflight' else capture(args.limit)
