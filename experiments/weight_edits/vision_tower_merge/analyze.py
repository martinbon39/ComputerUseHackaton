import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
import torch
torch.set_num_threads(2)
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np
import jsonschema

ROOT = Path(__file__).resolve().parent


def read_arm(arm, frozen, schema):
    path = ROOT / 'runs' / arm / 'generations.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    expected = {(c['row']['task_id'], s): c for c in frozen['contexts'] for s in frozen['seeds']}
    actual = {(r['row']['task_id'], r['seed']): r for r in rows}
    assert len(rows) == len(actual) == len(expected) == 220
    assert set(actual) == set(expected)
    for key, row in actual.items():
        assert row['row'] == expected[key]['row']
        assert row['payload_sha256'] == expected[key]['payload_sha256']
        parsed = row.get('parsed')
        valid = False
        if parsed is not None:
            try:
                jsonschema.validate(parsed, schema)
                valid = True
            except jsonschema.ValidationError:
                pass
        assert row['schema_valid'] == valid
        assert row['answer'] == (valid and parsed['tool_call']['tool_name'] == 'answer')
        assert row['valid_nonanswer'] == (valid and parsed['tool_call']['tool_name'] != 'answer')
    summary = {}
    for label in ['fs+', 'fs-', 'healthy', 'all']:
        group = [r for r in rows if label == 'all' or r['row']['label'] == label]
        summary[label] = {'n': len(group), 'answer': sum(r['answer'] for r in group), 'valid_nonanswer': sum(r['valid_nonanswer'] for r in group), 'invalid': sum(not r['schema_valid'] for r in group), 'error': sum(bool(r.get('error')) for r in group), 'truncated': sum(bool(r.get('truncated')) for r in group), 'tools': dict(Counter(r.get('tool') for r in group))}
    return actual, summary, hashlib.sha256(path.read_bytes()).hexdigest()


def paired(base, candidate, label, metric):
    tasks = sorted({key[0] for key, row in base.items() if row['row']['label'] == label})
    deltas = np.array([np.mean([float(candidate[(task, s)][metric]) - float(base[(task, s)][metric]) for s in [17000,17001,17002,17003]]) for task in tasks])
    rng = np.random.default_rng(20261108)
    boot = rng.choice(deltas, size=(20000, len(deltas)), replace=True).mean(axis=1)
    return {'delta_pp': float(deltas.mean() * 100), 'ci95_pp': list(np.quantile(boot, [.025, .975]) * 100), 'bootstrap_unit': 'task', 'n_tasks': len(tasks)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('arms', nargs='+')
    args = p.parse_args()
    f = json.loads((ROOT/'FROZEN.json').read_text())
    schema = json.loads((ROOT/'schema.json').read_text())
    base, base_summary, base_sha = read_arm('A', f, schema)
    report = {'baseline': base_summary, 'baseline_sha256': base_sha, 'arms': {}}
    for arm in args.arms:
        data, summary, sha = read_arm(arm, f, schema)
        compare = {label: paired(base, data, label, 'valid_nonanswer' if label == 'healthy' else 'answer') for label in ['fs+', 'fs-', 'healthy']}
        disagreements = [{'task_id': key[0], 'seed': key[1], 'label': row['row']['label'], 'original': base[key], 'candidate': row} for key, row in data.items() if (row.get('parsed') or {}).get('tool_call') != (base[key].get('parsed') or {}).get('tool_call')]
        texts_path = ROOT/'runs'/arm/'texts.json'
        assert texts_path.exists(), 'Three text controls required'
        texts = json.loads(texts_path.read_text())
        assert len(texts['results']) == 3
        report['arms'][arm] = {'summary': summary, 'sha256': sha, 'comparison': compare, 'json_gate': summary['all']['invalid'] <= 11, 'numerical_fs_gate': compare['fs+']['delta_pp'] <= -15, 'healthy_structural_gate_diagnostic': compare['healthy']['delta_pp'] >= -2, 'semantic_health': 'PENDING independent review if candidate has fs+ signal', 'text_results': json.loads(texts_path.read_text()) if texts_path.exists() else None, 'disagreements_count': len(disagreements)}
        (ROOT/f'disagreements_{arm}.json').write_text(json.dumps(disagreements,indent=2))
    (ROOT/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({a:{'summary':r['summary'],'comparison':r['comparison'],'json_gate':r['json_gate'],'numerical_fs_gate':r['numerical_fs_gate']} for a,r in report['arms'].items()},indent=2))


if __name__ == '__main__':
    main()
