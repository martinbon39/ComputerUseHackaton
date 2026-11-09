import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[1] / 'experiments/weight_edits/power_cohort'
EXPECTED = '2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = SOURCE / 'cohort/manifest.json'
    assert sha(manifest_path) == EXPECTED
    manifest = json.loads(manifest_path.read_text())
    rows = [r for r in manifest['train'] if r['label'] in ('fs+', 'fs-')]
    assert Counter(r['label'] for r in rows) == {'fs+': 19, 'fs-': 20}
    assert len({r['task_id'] for r in rows}) == 39
    target = ROOT / 'sources'
    target.mkdir(exist_ok=False)
    shutil.copy2(manifest_path, ROOT / 'manifest.json')
    frozen = json.loads((SOURCE / 'FROZEN.json').read_text())
    assert frozen['cohort_sha256'] == EXPECTED
    contexts = {c['row']['context_id']: c for c in frozen['contexts']}
    receipt = []
    for row in rows:
        assert contexts[row['context_id']]['row'] == row
        evaluator = Path(row['evaluator_path'])
        assert sha(evaluator) == row['evaluator_sha256']
        func = json.loads(evaluator.read_text())['evaluator']['func']
        assert func == row['evaluator_func']
        assert 'infeasible' not in json.dumps(func).lower() and row['feasible']
        src = Path(row['task_dir'])
        dest = target / row['context_id']
        dest.mkdir()
        for name, digest in {**row['source_hashes'], **row['screenshot_sha256']}.items():
            assert sha(src / name) == digest, (row['context_id'], name)
            shutil.copy2(src / name, dest / name)
        steps = [json.loads(line) for line in (src / 'traj.jsonl').read_text().splitlines()]
        assert steps[row['t']]['tool_name'] == 'answer'
        assert float((src / 'result.txt').read_text()) == row['score']
        receipt.append({'context_id': row['context_id'], 'task_id': row['task_id'],
                        'evaluator_sha256_verified': sha(evaluator), 'evaluator_func': func,
                        'source_files_verified': len(row['source_hashes']) + len(row['screenshot_sha256'])})
    (ROOT / 'SOURCE_AUDIT.json').write_text(json.dumps({'manifest_sha256': EXPECTED, 'rows': receipt}, indent=2) + '\n')
    print(json.dumps({'contexts': len(rows), 'feasible_evaluators_verified': len(receipt)}))


if __name__ == '__main__':
    main()
