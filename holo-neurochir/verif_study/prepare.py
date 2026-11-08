import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OSW = Path('/home/orbit/osw')
SOURCES = {
    'diag1': OSW / 'results_diag',
    'diag2': OSW / 'results_diag2',
    'extra1': OSW / 'results_diag_extra_gh/pass1',
    'extra2': OSW / 'results_diag_extra_gh/pass2',
}
TASKS = OSW / 'rtg/Env/OSWorld/evaluation_examples/examples'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def final_tool(row):
    value = row.get('tool_name')
    call = row.get('tool_call')
    if not value and isinstance(call, dict):
        value = call.get('tool_name')
    return value


def screen_key(path):
    match = re.match(r'step_(\d+)_(.*)\.png$', path.name)
    return (int(match[1]), match[2]) if match else (-1, path.name)


def main():
    if (ROOT / 'responses.jsonl').exists():
        raise SystemExit('Refusing to reselect corpus after inference began')
    (ROOT / 'images').mkdir(exist_ok=True)
    (ROOT / 'tasks').mkdir(exist_ok=True)
    inventory, selected, seen = [], [], set()
    for pass_id, source in SOURCES.items():
        for trajectory in sorted(source.rglob('traj.jsonl')):
            directory = trajectory.parent
            task_id, domain = directory.name, directory.parent.name
            row = {
                'episode_id': f'{pass_id}__{domain}__{task_id}',
                'pass_id': pass_id, 'domain': domain, 'task_id': task_id,
                'source_dir': str(directory), 'trajectory_sha256': sha(trajectory),
            }
            key = (pass_id, domain, task_id)
            if key in seen:
                row['exclusion'] = 'duplicate_task_pass'
                inventory.append(row)
                continue
            seen.add(key)
            try:
                records = [json.loads(line) for line in trajectory.read_text().splitlines() if line.strip()]
                last = records[-1]
                task_file = TASKS / domain / f'{task_id}.json'
                task = json.loads(task_file.read_text())
                score_file = directory / 'result.txt'
                score = float(score_file.read_text().strip())
                row.update({
                    'score': score, 'score_sha256': sha(score_file),
                    'final_tool': final_tool(last), 'last_step': last.get('step_num'),
                    'task_source': str(task_file), 'task_sha256': sha(task_file),
                    'instruction': task['instruction'],
                    'evaluator_func': task.get('evaluator', {}).get('func'),
                })
                row['infeasible'] = 'infeasible' in json.dumps(row['evaluator_func']).lower()
                row['partial'] = 0 < score < 1
                if row['final_tool'] != 'answer':
                    row['exclusion'] = 'last_tool_not_answer'
                elif row['infeasible']:
                    row['exclusion'] = 'infeasible'
                elif row['partial']:
                    row['exclusion'] = 'partial_score'
                elif score not in (0, 1):
                    row['exclusion'] = 'score_out_of_range'
                else:
                    screens = sorted(directory.glob('step_*.png'), key=screen_key)
                    referenced = directory / last.get('screenshot_file', '__missing__')
                    latest = screens[-1] if screens else None
                    if latest and (not referenced.is_file() or screen_key(latest) > screen_key(referenced)):
                        screenshot = latest
                        rule = 'latest_available_step'
                    elif referenced.is_file():
                        screenshot = referenced
                        rule = 'final_trajectory_screenshot'
                    else:
                        raise FileNotFoundError('No final screenshot')
                    relative = f'images/{row["episode_id"]}.png'
                    shutil.copyfile(screenshot, ROOT / relative)
                    task_relative = f'tasks/{domain}__{task_id}.json'
                    shutil.copyfile(task_file, ROOT / task_relative)
                    row.update({
                        'label': 'false_success' if score == 0 else 'true_success',
                        'screenshot_source': str(screenshot), 'screenshot_rule': rule,
                        'screenshot_sha256': sha(screenshot), 'image_path': relative,
                        'task_path': task_relative, 'exclusion': None,
                    })
                    selected.append(row)
            except (OSError, ValueError, KeyError, IndexError) as error:
                row['exclusion'] = 'invalid_or_missing_evidence'
                row['error'] = f'{type(error).__name__}: {error}'
            inventory.append(row)
    (ROOT / 'inventory.json').write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + '\n')
    (ROOT / 'manifest.json').write_text(json.dumps(selected, indent=2, ensure_ascii=False) + '\n')
    summary = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'source_episodes': len(inventory), 'selected_episodes': len(selected),
        'unique_selected_tasks': len({(r['domain'], r['task_id']) for r in selected}),
        'labels': dict(Counter(r['label'] for r in selected)),
        'exclusions': dict(Counter(r['exclusion'] for r in inventory if r['exclusion'])),
        'all_partial_scores': sum(r.get('partial', False) for r in inventory),
        'all_infeasible': sum(r.get('infeasible', False) for r in inventory),
        'answer_partial_scores': sum(r.get('partial', False) and r.get('final_tool') == 'answer' for r in inventory),
        'by_source': {key: dict(Counter(r.get('label') or r['exclusion'] for r in inventory if r['pass_id'] == key)) for key in SOURCES},
        'planned_completions': 4 * len(selected),
        'manifest_sha256': sha(ROOT / 'manifest.json'),
    }
    (ROOT / 'corpus_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
