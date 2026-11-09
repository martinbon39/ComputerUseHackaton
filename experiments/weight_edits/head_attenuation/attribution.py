import os
os.environ.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', TOKENIZERS_PARALLELISM='false', HF_HOME='/workspace/hf', HF_HUB_OFFLINE='1', CUBLAS_WORKSPACE_CONFIG=':4096:8')
import torch
torch.set_num_threads(2)
torch.set_num_interop_threads(2)
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
torch.use_deterministic_algorithms(True)
import argparse
import base64
import copy
import datetime
import gzip
import hashlib
import io
import json
import re
import sys
import time
from pathlib import Path
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor
from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS

ROOT = Path('/workspace/astra/moon-leak')
POWER = Path('/workspace/astra/astra-power')
MODEL = '/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e'
FULL = list(range(3, 32, 4))
LINEAR = [i for i in range(32) if i not in FULL]
STATE = dict(layer=None, head=None, positions=[], delta_layer=None, donor=None, capture=False, outputs={})
COUNT = 0
START = time.monotonic()
ORIGINAL_SDPA = ALL_ATTENTION_FUNCTIONS['sdpa']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def log(value):
    print(json.dumps(value), flush=True)


def attention(module, query, key, value, attention_mask, **kw):
    if query.shape[-2] != 1 or not hasattr(module, 'layer_idx'):
        return ORIGINAL_SDPA(module, query, key, value, attention_mask, **kw)
    keys = key.repeat_interleave(module.num_key_value_groups, dim=1)
    values = value.repeat_interleave(module.num_key_value_groups, dim=1)
    scores = torch.matmul(query.float(), keys.float().transpose(-2,-1)) * kw['scaling']
    if attention_mask is not None:
        scores = scores + attention_mask
    if module.layer_idx == STATE['layer'] and STATE['head'] is not None:
        scores[:,STATE['head'],:,STATE['positions']] = -torch.inf
    weights = torch.softmax(scores, dim=-1).to(query.dtype)
    output = torch.matmul(weights, values).transpose(1,2).contiguous()
    return output, None


def guarded(model, **inputs):
    global COUNT
    assert COUNT < 6500, 'forward cap'
    assert datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M') < '08:40', 'attribution time cap'
    assert not (ROOT / 'STOP').exists(), 'own stop'
    assert not Path('/workspace/astra/4b/STOP_GPU').exists(), 'fleet stop'
    COUNT += 1
    with torch.inference_mode():
        return model(**inputs, logits_to_keep=1)


def delta_hook(layer):
    def hook(module, args, output):
        if STATE['capture']:
            STATE['outputs'][layer] = output[:, -1:, :].detach().clone()
        if STATE['delta_layer'] == layer:
            assert output.shape[1] == 1
            return STATE['donor'].to(output)
        return output
    return hook


def hf_messages(messages):
    result = copy.deepcopy(messages)
    for message in result:
        if isinstance(message['content'], list):
            for part in message['content']:
                if part['type'] == 'image_url':
                    url = part['image_url']['url']
                    assert url.startswith('data:image/')
                    im = Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGB')
                    part.clear()
                    part.update(type='image', image=im)
    return result


def extend(inputs, ids):
    out = dict(inputs)
    for k, value in inputs.items():
        if torch.is_tensor(value) and value.ndim == 2 and value.shape == inputs['input_ids'].shape:
            extra = ids if k == 'input_ids' else torch.ones_like(ids) if k == 'attention_mask' else torch.zeros_like(ids, dtype=value.dtype)
            out[k] = torch.cat((value, extra), 1)
    return out


def prepare(processor, context):
    row = context['row']
    blob = gzip.decompress((POWER / 'payloads' / (context['payload_sha256'] + '.json.gz')).read_bytes())
    assert sha(blob) == context['payload_sha256']
    messages = json.loads(blob)
    record = json.loads((ROOT/'recorded_steps.json').read_text())[row['context_id']]
    assert record['task_id'] == row['task_id'] and record['t'] == row['t']
    assert record['traj_sha256'] == row['source_hashes']['traj.jsonl']
    step = record['step']
    assert step['tool_name'] == 'answer'
    action = json.dumps({k:step[k] for k in ['note','thought','tool_call']}, ensure_ascii=False, separators=(',', ':'))
    end = re.search(r'"tool_name":"', action).end()
    reason = (step.get('reasoning') or '').strip() + '\n</think>\n\n'
    suffix = reason + action[:end]
    tok = processor.tokenizer
    enc = tok(suffix, add_special_tokens=False, return_offsets_mapping=True, return_tensors='pt')
    spans = []
    for match in re.finditer(r'"(note|thought)":("(?:\\.|[^"\\])*"|null)', action[:end]):
        if match.group(2) != 'null':
            spans.append((len(reason)+match.start(2)+1, len(reason)+match.end(2)-1, match.group(1)))
    assert spans
    offsets = enc['offset_mapping'][0].tolist()
    overlap = [i for i,(a,b) in enumerate(offsets) if any(a < y and b > x for x,y,_ in spans)]
    interior = [i for i,(a,b) in enumerate(offsets) if any(a >= x and b <= y and b > a for x,y,_ in spans)]
    assert interior and overlap
    prompt = processor.apply_chat_template(hf_messages(messages), add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors='pt', enable_thinking=True).to('cuda')
    n = prompt['input_ids'].shape[1]
    ids = enc['input_ids'].to('cuda')
    full = extend(prompt, ids)
    names = ['answer','click','double_click','right_click','write','press_key','hotkey','scroll','drag','wait']
    tokens = {}
    for name in names:
        combined = tok(suffix + name + '"', add_special_tokens=False)['input_ids']
        assert combined[:ids.shape[1]] == ids[0].tolist(), name
        tokens[name] = combined[ids.shape[1]]
    assert len(set(tokens.values())) == len(tokens)
    neutral = dict(full)
    neutral['input_ids'] = full['input_ids'].clone()
    space = tok(' ', add_special_tokens=False)['input_ids']
    assert len(space) == 1
    neutral['input_ids'][0, [n+i for i in interior]] = space[0]
    neutral_text = tok.decode(neutral['input_ids'][0,n:].tolist())
    assert neutral_text[:len(reason)] == reason
    json.loads(neutral_text.split('\n</think>\n\n',1)[1] + 'answer"}}')
    meta = dict(context_id=row['context_id'], task_id=row['task_id'], label=row['label'], t=row['t'], payload_sha256=context['payload_sha256'], input_ids_sha256=sha(full['input_ids'].cpu().numpy().tobytes()), n_in=n, n_full=full['input_ids'].shape[1], note_thought_tokens=len(overlap), neutralized_tokens=len(interior), neutralized_boundary_tokens_excluded=len(set(overlap)-set(interior)), tool_token_ids=tokens)
    return full, neutral, [n+i for i in overlap], meta


def trim_last(inputs):
    out = dict(inputs)
    shape = inputs['input_ids'].shape
    for k,v in inputs.items():
        if torch.is_tensor(v) and v.ndim == 2 and v.shape == shape:
            out[k] = v[:,:-1]
    return out


def score(output, tokens):
    logits = output.logits[0,-1].float()
    precise = STATE['hidden'].float() @ STATE['tool_weight'].T
    vals = {name:float(precise[i]) for i,name in enumerate(tokens)}
    other = max(v for k,v in vals.items() if k != 'answer')
    return dict(answer_margin=vals['answer']-other, tool_logits=vals)


def snapshot(cache):
    out = []
    for layer in cache.layers:
        for key,value in vars(layer).items():
            if torch.is_tensor(value):
                out.append((key, value.shape, float(value.float().sum())))
            elif isinstance(value,dict):
                for kk,v in value.items():
                    if torch.is_tensor(v):
                        out.append((key,str(kk),v.shape,float(v.float().sum())))
    return repr(out)


def last_inputs(full, cache):
    assert bool(full['attention_mask'].all()), 'unpadded single-context replay required'
    return dict(input_ids=full['input_ids'][:,-1:], past_key_values=copy.deepcopy(cache), use_cache=True)


def run_context(model, processor, context, output, pilot):
    began = time.monotonic()
    full, neutral, positions, meta = prepare(processor, context)
    STATE['tool_weight'] = model.lm_head.weight[list(meta['tool_token_ids'].values())].detach().float()
    STATE.update(layer=None, head=None, delta_layer=None, capture=False, outputs={})
    original_full = guarded(model, **full, use_cache=False)
    full_score = score(original_full, meta['tool_token_ids'])
    full_logits = original_full.logits.detach().float().cpu()
    del original_full
    pref = guarded(model, **trim_last(full), use_cache=True)
    cache = pref.past_key_values
    del pref
    base_rope = model.model.rope_deltas.clone()
    before = snapshot(cache)
    base = guarded(model, **last_inputs(full,cache))
    baseline = score(base,meta['tool_token_ids'])
    error = float((base.logits.detach().float().cpu()-full_logits).abs().max())
    margin_error = abs(baseline['answer_margin']-full_score['answer_margin'])
    assert margin_error <= 0.75, ('cached margin fidelity',margin_error)
    assert before == snapshot(cache), 'base cache mutated'
    del base,full_logits
    record = dict(kind='baseline', **meta, **baseline, full_score=full_score, cached_logits_max_abs_diff=error, cached_margin_abs_diff=margin_error)
    output.write(json.dumps(record)+'\n');output.flush()
    log(dict(context=meta['context_id'], phase='baseline', seconds=time.monotonic()-began, **baseline, margin_error=margin_error))
    if pilot:
        baseline_hidden = STATE['hidden'].clone()
        again = guarded(model, **last_inputs(full,cache))
        again_score = score(again,meta['tool_token_ids'])
        log(dict(phase='cache_repeatability',context=meta['context_id'],baseline=baseline,repeat=again_score,hidden_max_abs_diff=float((STATE['hidden'].float()-baseline_hidden.float()).abs().max()),hidden_equal=bool(torch.equal(STATE['hidden'],baseline_hidden))))
        assert again_score == baseline, 'cache clone nonrepeatable'
        del again
    for layer in FULL:
        STATE.update(layer=layer,head=None,positions=positions)
        model.model.rope_deltas = base_rope.clone()
        control_out = guarded(model, **last_inputs(full,cache))
        control = score(control_out,meta['tool_token_ids'])
        del control_out
        output.write(json.dumps(dict(kind='mask_control', context_id=meta['context_id'], label=meta['label'],layer=layer,**control,margin_drop=baseline['answer_margin']-control['answer_margin']))+'\n')
        for head in range(16):
            STATE.update(layer=layer,head=head,positions=positions)
            model.model.rope_deltas = base_rope.clone()
            result = guarded(model, **last_inputs(full,cache))
            value = score(result,meta['tool_token_ids'])
            del result
            output.write(json.dumps(dict(kind='head', context_id=meta['context_id'], label=meta['label'],layer=layer,head=head,**value,margin_drop=control['answer_margin']-value['answer_margin'],unmatched_margin_drop=baseline['answer_margin']-value['answer_margin']))+'\n')
        output.flush()
        log(dict(context=meta['context_id'],phase='head',layer=layer,seconds=time.monotonic()-began,forwards=COUNT))
    STATE.update(layer=None,head=None,capture=False)
    neutral_pref = guarded(model, **trim_last(neutral), use_cache=True)
    assert torch.equal(model.model.rope_deltas, base_rope), 'neutral positions differ'
    neutral_cache = neutral_pref.past_key_values
    del neutral_pref
    STATE.update(capture=True,outputs={})
    neutral_out = guarded(model, **last_inputs(neutral,neutral_cache))
    donors = STATE['outputs']
    neutral_score=score(neutral_out,meta['tool_token_ids'])
    del neutral_out, neutral_cache
    STATE.update(capture=False,outputs={})
    output.write(json.dumps(dict(kind='neutral',context_id=meta['context_id'],label=meta['label'],**neutral_score,margin_drop=baseline['answer_margin']-neutral_score['answer_margin']))+'\n')
    for layer in LINEAR:
        STATE.update(delta_layer=layer,donor=donors[layer])
        model.model.rope_deltas = base_rope.clone()
        result = guarded(model, **last_inputs(full,cache))
        value = score(result,meta['tool_token_ids'])
        del result
        output.write(json.dumps(dict(kind='delta',context_id=meta['context_id'],label=meta['label'],layer=layer,**value,margin_drop=baseline['answer_margin']-value['answer_margin']))+'\n')
    STATE.update(delta_layer=None,donor=None)
    assert before == snapshot(cache), 'base cache mutated after interventions'
    output.write(json.dumps(dict(kind='complete',context_id=meta['context_id'],seconds=time.monotonic()-began,forwards=COUNT))+'\n');output.flush()
    os.fsync(output.fileno())
    log(dict(context=meta['context_id'],phase='complete',seconds=time.monotonic()-began,forwards=COUNT))
    del full,neutral,cache,donors
    torch.cuda.empty_cache()


def main():
    global COUNT
    assert sha((ROOT/'recorded_steps.json').read_bytes()) == '93b32dbd65a93a671b423464fa788783b2f0f9d3c440b00c68a7d7126d430d57'
    ap=argparse.ArgumentParser();ap.add_argument('--pilot',action='store_true');ap.add_argument('--limit',type=int);args=ap.parse_args()
    assert sha((POWER/'cohort/manifest.json').read_bytes()) == '2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0'
    frozen=json.loads((POWER/'FROZEN.json').read_text())
    contexts=[x for x in frozen['contexts'] if x['row']['label'] in ['fs+','fs-']]
    groups=[[x for x in contexts if x['row']['label']==label] for label in ['fs+','fs-']]
    contexts=[x for pair in __import__('itertools').zip_longest(*groups) for x in pair if x is not None]
    if args.pilot: contexts=contexts[:2]
    if args.limit: contexts=contexts[:args.limit]
    target=ROOT/('attribution_pilot.jsonl' if args.pilot else 'attribution.jsonl')
    done=set()
    if target.exists():
        lines=[json.loads(s) for s in target.read_text().splitlines()]
        done={r['context_id'] for r in lines if r['kind']=='complete'}
        assert all(r['context_id'] in done for r in lines), 'partial context: preserve file then use new output'
    if not args.pilot: COUNT = 165*len(done)
    torch.cuda.set_per_process_memory_fraction(24e9/torch.cuda.get_device_properties(0).total_memory)
    processor=AutoProcessor.from_pretrained(MODEL)
    model=AutoModelForImageTextToText.from_pretrained(MODEL,dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda').eval()
    assert model.config.text_config.num_attention_heads==16
    ALL_ATTENTION_FUNCTIONS.register('sdpa',attention)
    layers=model.model.language_model.layers
    handles=[layers[i].linear_attn.register_forward_hook(delta_hook(i)) for i in LINEAR]
    def capture_norm(module, inputs, output):
        STATE['hidden'] = output[0,-1].detach()
    handles.append(model.model.language_model.norm.register_forward_hook(capture_norm))
    versions = {name:p._version for name,p in model.named_parameters()}
    with target.open('a') as out:
        for c in contexts:
            if c['row']['context_id'] not in done: run_context(model,processor,c,out,args.pilot)
    assert versions == {name:p._version for name,p in model.named_parameters()}, 'weights mutated'
    for h in handles:h.remove()
    log(dict(phase='finished',seconds=time.monotonic()-START,forwards=COUNT,output=str(target)))

if __name__=='__main__':main()
