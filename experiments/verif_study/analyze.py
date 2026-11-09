import hashlib
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPLICATES = ['t0', 't08_r1', 't08_r2', 't08_r3']


def wilson(k, n):
    if not n:
        return {'numerator': k, 'denominator': n, 'rate': None, 'ci95': None}
    z = 1.959963984540054
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return {'numerator': k, 'denominator': n, 'rate': p, 'ci95': [center - half, center + half]}


def parse_response(response):
    if response is None:
        return {'verdict': 'MISSING', 'requirement_decisions': [], 'reasoning_tokens_present': False}
    if response['status'] != 'ok':
        return {'verdict': 'ERROR', 'requirement_decisions': [], 'reasoning_tokens_present': False}
    choice = response['response']['choices'][0]
    message = choice['message']
    content = message.get('content') or ''
    plain = re.sub(r'[*`_]', '', content)
    matches = re.finditer(r'''\bVERDICT\s*["']?\s*:\s*["']?\s*(COMPLETE|INCOMPLETE)\b''', plain, re.I)
    unique = {match[1].upper() for match in matches
              if not re.match(r'\s+or\s+(COMPLETE|INCOMPLETE)\b', plain[match.end():], re.I)}
    valid = choice.get('finish_reason') == 'stop' and len(unique) == 1
    if valid:
        verdict = next(iter(unique))
    elif choice.get('finish_reason') == 'length':
        verdict = 'TRUNCATED'
    elif choice.get('finish_reason') != 'stop':
        verdict = 'INVALID_FINISH'
    elif len(unique) > 1:
        verdict = 'CONFLICTING_VERDICTS'
    elif re.search(r'\bVERDICT\b', plain, re.I):
        verdict = 'MALFORMED_VERDICT'
    else:
        verdict = 'MISSING_VERDICT'
    decisions = []
    before_verdict = re.split(r'''\bVERDICT\s*["']?\s*:''', plain, flags=re.I)[0]
    for line_number, line in enumerate(before_verdict.splitlines(), 1):
        stripped = re.sub(r'^\s*(?:\d+[.)]|[-•])\s*', '', line).strip()
        match = re.search(r'(?:^|\s[-–—:]\s*|:\s*|\|\s*)(yes|no|cannot tell)\b', stripped, re.I)
        if not match:
            match = re.search(r'\(\s*(yes|no|cannot tell)\s*\)\s*[.!]?$', stripped, re.I)
        if match:
            decisions.append({'decision': match[1].lower(), 'line_number': line_number, 'text': line.strip()})
    return {
        'verdict': verdict, 'requirement_decisions': decisions,
        'requirement_counts': dict(Counter(row['decision'] for row in decisions)),
        'content': content, 'reasoning_tokens_present': bool(message.get('reasoning') or message.get('reasoning_content')),
        'finish_reason': choice.get('finish_reason'),
    }


def group_metrics(rows, verdict_key='verdict'):
    result = {}
    for label in ['false_success', 'true_success']:
        selected = [row for row in rows if row['label'] == label]
        counts = Counter(row[verdict_key] for row in selected)
        valid = counts['COMPLETE'] + counts['INCOMPLETE']
        result[label] = {
            'verdict_counts': dict(counts),
            'incomplete_rate': wilson(counts['INCOMPLETE'], len(selected)),
            'valid_only_incomplete_rate': wilson(counts['INCOMPLETE'], valid),
        }
    return result


def apply_requirement_review(parsed, raw_index):
    review = json.loads((ROOT / 'audit/requirement_review.json').read_text())
    t0_lines = [line for line in (ROOT / 'responses.jsonl').read_bytes().splitlines(keepends=True)
                if json.loads(line)['request_id'].endswith('__t0')]
    assert hashlib.sha256(b''.join(t0_lines)).hexdigest() == review['source']['selected_t0_raw_lines_sha256']
    by_request = {row['request_id']: row for row in parsed}
    for correction in review['corrections']:
        row = by_request[correction['request_id']]
        decisions = row['requirement_decisions']
        counts = Counter(item['decision'] for item in decisions)
        assert all(counts[key] == value for key, value in correction['parser_counts'].items())
        row['automated_requirement_decisions'] = [dict(item) for item in decisions]
        raw_content = raw_index[row['request_id']]['response']['choices'][0]['message']['content']
        content_lines = raw_content.splitlines()
        for operation in correction['operations']:
            line = operation['content_line']
            assert content_lines[line - 1].strip() == operation['text'].strip()
            if operation['op'] in ['remove', 'change', 'split_compound_line']:
                old = operation.get('from', operation.get('decision'))
                matched = [i for i, item in enumerate(decisions) if item['line_number'] == line and item['decision'] == old]
                assert len(matched) == 1
                decisions.pop(matched[0])
            if operation['op'] in ['add', 'change', 'split_compound_line']:
                label = operation.get('to', operation.get('decision'))
                count = operation.get('audited_count', 1)
                for ordinal in range(count):
                    decisions.append({'decision': label, 'line_number': line, 'text': operation['text'],
                                      'origin': 'independent_semantic_requirement_audit', 'within_line_ordinal': ordinal + 1})
        counts = Counter(item['decision'] for item in decisions)
        assert all(counts[key] == value for key, value in correction['audited_counts'].items())
        row['requirement_counts'] = dict(counts)
        row['requirement_semantically_reviewed'] = True
    totals = Counter(item['decision'] for row in parsed if row['replicate'] == 't0' for item in row['requirement_decisions'])
    expected = review['counts']['strict_audited_distinct_model_listed_requirements']
    assert all(totals[key] == expected[key] for key in ['yes', 'no', 'cannot tell'])
    return review['counts']


def cluster_ci(rows, seed=20261108, draws=10000):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['domain'], row['task_id'])].append(row)
    keys = sorted(groups)
    rng = random.Random(seed)
    distributions = defaultdict(list)
    for _ in range(draws):
        samples = [row for key in rng.choices(keys, k=len(keys)) for row in groups[key]]
        sample_rates = {}
        for label in ['false_success', 'true_success']:
            selected = [row for row in samples if row['label'] == label]
            if selected:
                sample_rates[label] = sum(row['verdict'] == 'INCOMPLETE' for row in selected) / len(selected)
                distributions[label].append(sample_rates[label])
        if len(sample_rates) == 2:
            distributions['detection_minus_false_rejection'].append(sample_rates['false_success'] - sample_rates['true_success'])
    result = {}
    for label, values in distributions.items():
        values.sort()
        result[label] = [values[int(.025 * len(values))], values[min(len(values) - 1, int(.975 * len(values)))]]
    return {'method': f'task-cluster percentile bootstrap; resample {len(keys)} task groups jointly across labels',
            'seed': seed, 'draws': draws, 'ci95': result}


def simulation(primary):
    n = len(primary)
    true_total = sum(r['label'] == 'true_success' for r in primary)
    detected = sum(r['label'] == 'false_success' and r['verdict'] == 'INCOMPLETE' for r in primary)
    rejected = sum(r['label'] == 'true_success' and r['verdict'] == 'INCOMPLETE' for r in primary)
    inventory = json.loads((ROOT / 'inventory.json').read_text())
    scored_feasible = [r for r in inventory if isinstance(r.get('score'), (float, int))
                       and not r.get('infeasible') and 0 <= r['score'] <= 1]
    reference_n = len(scored_feasible)
    reference_score_sum = sum(r['score'] for r in scored_feasible)
    scenarios = {}
    for name, repaired, trials in [('no_repair', 0, 0), ('feasible_valid_branch_observed', 0, 2),
                                   ('all_valid_branch_naive_transfer', 1, 4)]:
        repair_rate = repaired / trials if trials else 0
        expected_repairs = repair_rate * detected
        scenarios[name] = {
            'repair_rate': repair_rate, 'branch_wilson': wilson(repaired, trials) if trials else None,
            'expected_repairs_not_observed': expected_repairs,
            'gain_pp_if_true_successes_preserved': 100 * expected_repairs / n,
            'gain_pp_if_all_false_rejects_lost': 100 * (expected_repairs - rejected) / n,
            'success_rate_if_true_successes_preserved': (true_total + expected_repairs) / n,
            'success_rate_if_all_false_rejects_lost': (true_total + expected_repairs - rejected) / n,
            'reference_315_gain_pp_if_preserved': 100 * expected_repairs / reference_n,
            'reference_315_gain_pp_if_false_rejects_lost': 100 * (expected_repairs - rejected) / reference_n,
        }
    return {
        'population': '268 selected binary-score feasible answer episodes, not full OSWorld',
        'n': n, 'baseline_successes': true_total, 'baseline_success_rate': true_total / n,
        'false_successes_blocked': detected, 'true_successes_blocked': rejected,
        'gate_rule': 'block answer only for a valid INCOMPLETE verdict at T=0; invalid outputs do not trigger this simulated gate',
        'precision_of_block': wilson(detected, detected + rejected), 'scenarios': scenarios,
        'reference_all_scored_feasible_episodes': {
            'n': reference_n, 'official_score_sum': reference_score_sum,
            'official_score_mean': reference_score_sum / reference_n,
            'interpretation': 'Descriptive denominator sensitivity across all scored feasible recorded episodes, including partial scores and non-answer endings. Only the 268 screened episodes are hypothetically gated; every other episode is held unchanged. These incomplete repeated diagnostic passes are not the full OSWorld benchmark.',
        },
        'critical_limit': 'The sole repair in the fidelity-valid 1/4 branch rate was an officially infeasible GIMP task. The feasible valid subset is 0/2 continuations from one Writer episode. Neither rate establishes transfer to this corpus; k=2 continuations are dependent. No new rollout or causal gain is measured.',
    }


def main():
    episodes = json.loads((ROOT / 'manifest.json').read_text())
    raw = [json.loads(line) for line in (ROOT / 'responses.jsonl').read_text().splitlines() if line.strip()]
    index = {row['request_id']: row for row in raw}
    if len(index) != len(raw):
        raise ValueError('Duplicate logical request IDs in responses.jsonl')
    parsed = []
    for episode in episodes:
        for replicate in REPLICATES:
            key = f'{episode["episode_id"]}__{replicate}'
            row = {k: episode[k] for k in ['episode_id', 'pass_id', 'domain', 'task_id', 'label', 'score']}
            row.update({'request_id': key, 'replicate': replicate})
            row.update(parse_response(index.get(key)))
            parsed.append(row)
    requirement_review_counts = apply_requirement_review(parsed, index)
    (ROOT / 'parsed_responses.json').write_text(json.dumps(parsed, indent=2, ensure_ascii=False) + '\n')
    metrics = {replicate: group_metrics([r for r in parsed if r['replicate'] == replicate]) for replicate in REPLICATES}
    per_episode = []
    for episode in episodes:
        rows = [r for r in parsed if r['episode_id'] == episode['episode_id']]
        by_rep = {r['replicate']: r for r in rows}
        sampled = [by_rep[rep]['verdict'] for rep in REPLICATES[1:]]
        counts = Counter(sampled)
        majority = ('INCOMPLETE' if counts['INCOMPLETE'] >= 2 else
                    'COMPLETE' if counts['COMPLETE'] >= 2 else 'INVALID')
        all_valid = all(value in ['COMPLETE', 'INCOMPLETE'] for value in sampled)
        valid_pairs = [(sampled[a], sampled[b]) for a, b in [(0, 1), (0, 2), (1, 2)]
                       if sampled[a] in ['COMPLETE', 'INCOMPLETE'] and sampled[b] in ['COMPLETE', 'INCOMPLETE']]
        row = {k: episode[k] for k in ['episode_id', 'domain', 'task_id', 'label']}
        row.update({'verdict': majority, 'sampled_verdicts': sampled,
                    't0_verdict': by_rep['t0']['verdict'],
                    'all_three_valid': all_valid,
                    'unanimous': all_valid and len(counts) == 1,
                    'pair_disagreements': sum(a != b for a, b in valid_pairs),
                    'pair_comparisons': len(valid_pairs),
                    'majority_matches_t0': majority == by_rep['t0']['verdict'] if majority in ['COMPLETE', 'INCOMPLETE'] and by_rep['t0']['verdict'] in ['COMPLETE', 'INCOMPLETE'] else None})
        per_episode.append(row)
    stability = {'majority_metrics': group_metrics(per_episode)}
    for label in ['all', 'false_success', 'true_success']:
        rows = [r for r in per_episode if label == 'all' or r['label'] == label]
        valid = [r for r in rows if r['all_three_valid']]
        comparable = [r for r in rows if r['majority_matches_t0'] is not None]
        stability[label] = {
            'episodes': len(rows), 'all_three_valid': len(valid),
            'unanimous': wilson(sum(r['unanimous'] for r in valid), len(valid)),
            'at_least_one_sample_incomplete': wilson(sum('INCOMPLETE' in r['sampled_verdicts'] for r in rows), len(rows)),
            'all_three_incomplete': wilson(sum(r['sampled_verdicts'] == ['INCOMPLETE'] * 3 for r in rows), len(rows)),
            'pair_disagreement_count': sum(r['pair_disagreements'] for r in rows),
            'pair_comparisons': sum(r['pair_comparisons'] for r in rows),
            'majority_agreement_t0': wilson(sum(r['majority_matches_t0'] for r in comparable), len(comparable)),
        }
    primary = [r for r in parsed if r['replicate'] == 't0']
    declined = {r['episode_id'] for r in json.loads((ROOT / 'answer_metadata_sensitivity.json').read_text())['flagged_episodes']}
    requirements = {}
    for label in ['all', 'false_success', 'true_success']:
        rows = [r for r in primary if label == 'all' or r['label'] == label]
        counts = Counter(d['decision'] for r in rows for d in r['requirement_decisions'])
        requirements[label] = {
            'explicit_decisions': dict(counts), 'total_explicit_decisions': sum(counts.values()),
            'episodes_with_no': sum(any(d['decision'] == 'no' for d in r['requirement_decisions']) for r in rows),
            'episodes_with_cannot_tell': sum(any(d['decision'] == 'cannot tell' for d in r['requirement_decisions']) for r in rows),
            'episodes_with_no_parsed_decision': sum(not r['requirement_decisions'] for r in rows),
        }
    result = {
        'study': 'Original Holo-3.1-4B final-screen verification; no new rollouts',
        'study_status': 'COMPLETE' if len(raw) == 4 * len(episodes) else 'IN_PROGRESS',
        'corpus': json.loads((ROOT / 'corpus_summary.json').read_text()),
        'unique_tasks_by_label': {label: len({(r['domain'], r['task_id']) for r in episodes if r['label'] == label}) for label in ['false_success', 'true_success']},
        'response_count': len(raw), 'planned_response_count': 4 * len(episodes),
        'response_statuses': dict(Counter(r['status'] for r in raw)),
        'parsed_verdict_counts': dict(Counter(r['verdict'] for r in parsed)),
        'nonempty_reasoning_count': sum(r['reasoning_tokens_present'] for r in parsed),
        'runtime': {
            'first_request_at': min(r['started_at'] for r in raw),
            'last_response_at': max(r['finished_at'] for r in raw),
            'latency_seconds_median': statistics.median(r['elapsed_seconds'] for r in raw),
            'latency_seconds_max': max(r['elapsed_seconds'] for r in raw),
            'completion_tokens': sum(r.get('response', {}).get('usage', {}).get('completion_tokens', 0) for r in raw),
            'prompt_tokens': sum(r.get('response', {}).get('usage', {}).get('prompt_tokens', 0) for r in raw),
            'infrastructure_text_probes_separate_from_study': 4,
        },
        'metrics': metrics, 'primary_task_cluster_bootstrap': cluster_ci(primary),
        'sensitivity_excluding_metadata_declared_infeasible': {
            'excluded_episodes': sorted(declined),
            'metrics_t0': group_metrics([r for r in primary if r['episode_id'] not in declined]),
            'note': 'Primary labels follow the requested final-answer and official-score rule. Two feasible-task score-0 answers were metadata-tagged as explicit refusals; this sensitivity does not alter the primary cohort.',
        },
        'stability': stability, 'requirements_t0': requirements,
        'requirement_extraction_audit': requirement_review_counts,
        'simulation': simulation(primary),
        'directory_inventory_supplement': json.loads((ROOT / 'corpus_probe.json').read_text())['corpus_counts'],
        'by_domain_t0': {domain: group_metrics([r for r in primary if r['domain'] == domain]) for domain in sorted({r['domain'] for r in primary})},
        'by_source_t0': {source: group_metrics([r for r in primary if r['pass_id'] == source]) for source in sorted({r['pass_id'] for r in primary})},
        'v2': {'status': 'NOT RUN', 'reason': 'No stronger independent VLM cached; only Holo 0.8B/4B and edited 4B checkpoints found.'},
        'artifacts_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in [
            'manifest.json', 'responses.jsonl', 'PROTOCOL.md', 'prepare.py', 'run_verifier.py',
            'analyze.py', 'test_parser.py', 'error_cases.json', 'answer_metadata_sensitivity.json',
            'branch_source_REPORT.md', 'infrastructure_probe.json', 'corpus_probe.json', 'audit/requirement_review.json']},
    }
    (ROOT / 'stability_by_episode.json').write_text(json.dumps(per_episode, indent=2) + '\n')
    (ROOT / 'RESULT.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'responses': len(raw), 'primary': metrics['t0'], 'stability': stability['all']}, indent=2))


if __name__ == '__main__':
    main()
