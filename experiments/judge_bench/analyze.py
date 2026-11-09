"""Judge bench: Holo-3.1-4B (V1, recomputed from verif_study t0) vs Holo4-27B (V2a) vs Claude/Feci Guard (V2b).
Decision rule for every judge: INCOMPLETE = detection (blocks the answer); COMPLETE = pass; any other outcome
(error, timeout, truncated, unparsable) = pass, counted separately."""
import hashlib
import json
import random
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / 'verif_study'
sys.path.insert(0, str(STUDY))
from analyze import cluster_ci, parse_response, wilson  # noqa: E402

LABELS = ['false_success', 'true_success']


def jsonl(path):
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def holo_rows(episodes, responses):
    by_ep = {r['episode_id']: r for r in responses if r['request_id'].endswith('__t0')}
    rows = []
    for e in episodes:
        p = parse_response(by_ep.get(e['episode_id']))
        counts = Counter(d['decision'] for d in p['requirement_decisions'])
        rows.append({'episode_id': e['episode_id'], 'domain': e['domain'], 'task_id': e['task_id'],
                     'label': e['label'], 'verdict': p['verdict'],
                     'req_yes': counts['yes'], 'req_no': counts['no'], 'req_cannot_tell': counts['cannot tell']})
    return rows


def claude_rows(episodes, responses):
    by_ep = {r['episode_id']: r['result'] for r in responses}
    rows = []
    for e in episodes:
        v = by_ep.get(e['episode_id'])
        if v is None:
            verdict, counts = 'MISSING', Counter()
        else:
            verdict = v['verdict'] if v['ok'] else 'ERROR'
            counts = Counter(r.get('status') if isinstance(r, dict) else 'not_an_object' for r in v.get('requirements', []))
        rows.append({'episode_id': e['episode_id'], 'domain': e['domain'], 'task_id': e['task_id'],
                     'label': e['label'], 'verdict': verdict,
                     'req_yes': counts['yes'], 'req_no': counts['no'], 'req_cannot_tell': counts['cannot_tell'],
                     'error': None if v is None else v.get('error'),
                     'latency_s': None if v is None else v.get('latency_s'),
                     'cost_usd': None if v is None else v.get('cost_usd')})
    return rows


def summary(rows):
    out = {}
    for label in LABELS:
        sel = [r for r in rows if r['label'] == label]
        verdicts = Counter(r['verdict'] for r in sel)
        other = len(sel) - verdicts['COMPLETE'] - verdicts['INCOMPLETE']
        decisions = sum(r['req_yes'] + r['req_no'] + r['req_cannot_tell'] for r in sel)
        ct = sum(r['req_cannot_tell'] for r in sel)
        out[label] = {
            'n': len(sel), 'verdict_counts': dict(verdicts),
            'incomplete_rate': wilson(verdicts['INCOMPLETE'], len(sel)),
            'error_or_invalid': wilson(other, len(sel)),
            'cannot_tell_share_of_requirement_decisions': wilson(ct, decisions),
            'episodes_with_any_cannot_tell': wilson(sum(r['req_cannot_tell'] > 0 for r in sel), len(sel)),
        }
    fs, ts = out['false_success']['incomplete_rate']['rate'], out['true_success']['incomplete_rate']['rate']
    out['gap_detection_minus_false_rejection'] = fs - ts
    out['task_cluster_bootstrap'] = cluster_ci(rows)
    return out


def paired_gap_diff(a, b, seed=20261108, draws=10000):
    """Task-cluster bootstrap of gap(b) - gap(a), same resampled tasks for both judges."""
    groups = defaultdict(list)
    for ra, rb in zip(a, b):
        assert ra['episode_id'] == rb['episode_id']
        groups[(ra['domain'], ra['task_id'])].append((ra, rb))
    keys = sorted(groups)
    rng = random.Random(seed)

    def gap(pairs, i):
        rates = []
        for label in LABELS:
            sel = [p[i] for p in pairs if p[i]['label'] == label]
            rates.append(sum(r['verdict'] == 'INCOMPLETE' for r in sel) / len(sel) if sel else None)
        return None if None in rates else rates[0] - rates[1]

    values = []
    for _ in range(draws):
        pairs = [p for k in rng.choices(keys, k=len(keys)) for p in groups[k]]
        ga, gb = gap(pairs, 0), gap(pairs, 1)
        if ga is not None and gb is not None:
            values.append(gb - ga)
    values.sort()
    point = gap([p for k in keys for p in groups[k]], 1) - gap([p for k in keys for p in groups[k]], 0)
    return {'point': point, 'ci95': [values[int(.025 * len(values))], values[int(.975 * len(values)) - 1]],
            'draws_used': len(values), 'seed': seed}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    episodes = json.loads((STUDY / 'manifest.json').read_text())
    judges = {'Holo-3.1-4B': holo_rows(episodes, jsonl(STUDY / 'responses.jsonl'))}
    if (HERE / 'holo4_responses.jsonl').exists():
        judges['Holo4-27B'] = holo_rows(episodes, jsonl(HERE / 'holo4_responses.jsonl'))
    if (HERE / 'claude_responses.jsonl').exists():
        judges['Claude (Feci Guard verifier)'] = claude_rows(episodes, jsonl(HERE / 'claude_responses.jsonl'))
    if (HERE / 'holo4_feci_responses.jsonl').exists():
        judges['Holo4-27B (Feci Guard verifier)'] = claude_rows(episodes, jsonl(HERE / 'holo4_feci_responses.jsonl'))
    result = {'corpus': {'manifest_sha256': sha(STUDY / 'manifest.json'), 'episodes': len(episodes),
                         'labels': dict(Counter(e['label'] for e in episodes))},
              'decision_rule': 'INCOMPLETE = detection; COMPLETE = pass; error/timeout/truncated/unparsable = pass, '
                               'counted separately (error_or_invalid)',
              'judges': {name: summary(rows) for name, rows in judges.items()},
              'paired_gap_difference_vs_Holo-3.1-4B': {
                  name: paired_gap_diff(judges['Holo-3.1-4B'], rows) for name, rows in judges.items()
                  if name != 'Holo-3.1-4B'},
              'paired_gap_difference_vs_Claude': {
                  name: paired_gap_diff(judges['Claude (Feci Guard verifier)'], rows) for name, rows in judges.items()
                  if name.startswith('Holo4-27B')}}
    v1 = result['judges']['Holo-3.1-4B']
    assert v1['false_success']['verdict_counts'].get('INCOMPLETE') == 35
    assert v1['true_success']['verdict_counts'].get('INCOMPLETE') == 97
    for name, rows in judges.items():
        missing = sum(r['verdict'] == 'MISSING' for r in rows)
        result['judges'][name]['missing_responses'] = missing
    for name in ('Claude (Feci Guard verifier)', 'Holo4-27B (Feci Guard verifier)'):
        rows = judges.get(name)
        if rows:
            result['judges'][name]['cost_usd_total'] = sum(r['cost_usd'] or 0 for r in rows)
            result['judges'][name]['error_messages'] = dict(Counter(
                (r['error'] or '')[:60] for r in rows if r['verdict'] not in ('COMPLETE', 'INCOMPLETE')))
    (HERE / 'per_episode.json').write_text(json.dumps(judges, indent=1, ensure_ascii=False) + '\n')
    result['artifacts_sha256'] = {p.name: sha(p) for p in sorted(HERE.glob('*')) if p.is_file()
                                  and p.name not in ('RESULT.json', 'REPORT.md')}
    result['artifacts_sha256']['feci_guard/verifier.py'] = sha(HERE.parent / 'feci_guard' / 'verifier.py')
    (HERE / 'RESULT.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    for name, s in result['judges'].items():
        f, t = s['false_success'], s['true_success']
        print(f"{name:32s} det {f['incomplete_rate']['numerator']}/{f['n']}  falserej "
              f"{t['incomplete_rate']['numerator']}/{t['n']}  gap {s['gap_detection_minus_false_rejection']:+.3f} "
              f"{s['task_cluster_bootstrap']['ci95'].get('detection_minus_false_rejection')}  "
              f"err {f['error_or_invalid']['numerator']}+{t['error_or_invalid']['numerator']}  missing {s['missing_responses']}")


if __name__ == '__main__':
    main()
