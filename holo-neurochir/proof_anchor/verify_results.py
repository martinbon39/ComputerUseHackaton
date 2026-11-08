import os

os.environ.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2')

import argparse
import hashlib
import json
import math
import re
import shlex
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu, norm


SEED = 1729
N_BOOT = 10000
LAYERS = [8, 12, 16, 20, 24, 28]
POSITIONS = ['prompt_end', 'reflection_end', 'note_onset']
MODELS = ['logistic_l2', 'knn3_cosine', 'knn5_cosine', 'mlp64_l2']
CORE_SHA = '80ab8c7ec4b031ea82c339f53294752d84351a3c82673f62c6d7d127023f4398'
REVISION = '8c88265a5a159bfd1492db9243733dd2e6e04a6e'


class Audit:
    def __init__(self, root):
        self.root = root
        self.checks = 0
        self.groups = {}

    def require(self, condition, label):
        self.checks += 1
        if not condition:
            raise AssertionError(label)

    def close(self, actual, expected, label, tolerance=1e-11):
        a, e = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
        self.require(a.shape == e.shape and np.isfinite(a).all() and np.isfinite(e).all()
                     and np.allclose(a, e, rtol=0, atol=tolerance), label)

    def json(self, name):
        return json.loads((self.root / name).read_text())

    def sha(self, name):
        return hashlib.sha256((self.root / name).read_bytes()).hexdigest()

    def hash_references(self, refs):
        for name, digest in refs.items():
            self.require(self.sha(name) == digest, 'hash reference: ' + name)

    def group(self, name, **evidence):
        self.groups[name] = dict(passed=True, **evidence)
        print(json.dumps({'verified': name, 'checks': self.checks}), flush=True)


def bounds(values):
    return np.percentile(values, [2.5, 97.5])


def two_u(labels, scores):
    positives = scores[labels == 1]
    negatives = scores[labels == 0]
    return int(sum(2 * np.count_nonzero(v > negatives) + np.count_nonzero(v == negatives)
                   for v in positives))


def bootstrap_auc(labels, scores, counts):
    pos, neg = scores[labels == 1], scores[labels == 0]
    pairs = 2 * (pos[:, None] > neg) + (pos[:, None] == neg)
    numerators = np.einsum('bi,ij,bj->b', counts[1], pairs.astype(np.int64), counts[0], optimize=True)
    return numerators / (2 * len(pos) * len(neg))


def verify(root, expected_result, expected_report):
    a = Audit(root)
    before = {name: a.sha(name) for name in ['RESULT.json', 'RESULT_CORE.json', 'REPORT.md']}
    if expected_result:
        a.require(before['RESULT.json'] == expected_result, 'frozen result SHA')
    if expected_report:
        a.require(before['REPORT.md'] == expected_report, 'frozen report SHA')
    a.require(before['RESULT_CORE.json'] == CORE_SHA, 'immutable original result')
    result, core = a.json('RESULT.json'), a.json('RESULT_CORE.json')
    for key, value in core.items():
        if key == 'artifact_hashes':
            a.require(all(result[key].get(k) == v for k, v in value.items()), 'original artifact references preserved')
        else:
            a.require(result[key] == value, 'original result field preserved: ' + key)
    a.hash_references(result['artifact_hashes'])
    a.require(result['manifest_sha256'] == a.sha('manifest.json'), 'manifest hash')
    a.require(a.json('SOURCE_AUDIT.json')['manifest_sha256'] == result['manifest_sha256'], 'source audit manifest')
    a.require(a.json('MODEL_AUDIT.json')['revision'] == REVISION, 'model audit revision')
    a.require(result['model']['revision'] == REVISION, 'reported model revision')
    a.require(a.json('VERIFY_CAPTURE_FINAL.json')['verdict'] == 'RAN/PASSED/CORRECT', 'capture checker verdict')
    a.require(a.json('VERIFY_REPLAY.json')['verdict'] == 'PASS', 'replay checker verdict')
    a.require(a.json('VERIFY_METHODS.json')['analyze_sha256'] == a.sha('analyze.py'), 'reviewed analysis version')
    a.group('provenance_and_immutable_core', referenced_artifacts=len(result['artifact_hashes']), core_sha256=CORE_SHA)

    preflight = a.json('PREFLIGHT.json')
    metadata = [row['metadata'] for row in preflight['records']]
    ids = [row['context_id'] for row in metadata]
    labels = np.array([row['label'] == 'fs+' for row in metadata], dtype=int)
    a.require(len(ids) == len(set(ids)) == len({row['task_id'] for row in metadata}) == 39, '39 unique tasks and contexts')
    a.require(set(row['label'] for row in metadata) == {'fs+', 'fs-'} and labels.sum() == 19, '19/20 labels')
    rows = [json.loads(line) for line in (root / 'forwards.jsonl').read_text().splitlines()]
    by_key = {(row['context_id'], row['condition']): row for row in rows}
    a.require(len(rows) == len(by_key) == 156, '156 distinct forwards')
    a.require(set(by_key) == {(cid, c) for cid in ids for c in 'abcd'}, 'complete condition coverage')
    residuals = []
    margins = []
    for meta in metadata:
        cid = meta['context_id']
        values = []
        for condition in 'abcd':
            row = by_key[cid, condition]
            a.require(row['task_id'] == meta['task_id'] and row['label'] == meta['label'], 'forward identity ' + cid)
            logits = row['tool_logits']
            margin = logits['answer'] - max(value for name, value in logits.items() if name != 'answer')
            a.close(row['answer_margin'], margin, 'raw tool margin ' + cid + condition, tolerance=0)
            values.append(margin)
        margins.append(values)
        capture = 'captures/' + cid + '.npz'
        a.require(a.sha(capture) == by_key[cid, 'a']['capture_sha256'], 'capture SHA ' + cid)
        with np.load(root / capture) as saved:
            a.require(saved['layers'].tolist() == LAYERS, 'capture layer convention')
            residuals.append(saved['residual'].astype(np.float64))
    margins = np.array(margins)
    residuals = np.stack(residuals)
    a.require(residuals.shape == (39, 6, 3, 2560) and np.isfinite(residuals).all(), 'residual shape and finiteness')
    a.group('raw_cohort', forwards=156, tasks=39, labels={'false_finish': 19, 'true_finish': 20}, capture_hashes=39)

    rng = np.random.default_rng(SEED)
    counts = {v: rng.multinomial(int((labels == v).sum()), np.full(int((labels == v).sum()), 1 / (labels == v).sum()), size=N_BOOT)
              for v in [0, 1]}
    delta = margins[:, 0] - margins[:, 1]
    anchor = result['anchoring']
    per_task = {row['context_id']: row for row in anchor['per_task']}
    for i, cid in enumerate(ids):
        a.close([per_task[cid]['margins'][c] for c in 'abcd'], margins[i], 'per-task margins')
        for j, name in enumerate(['a_minus_b', 'a_minus_c', 'a_minus_d'], 1):
            a.close(per_task[cid]['deltas'][name], margins[i, 0] - margins[i, j], 'per-task contrast')
    for title, v in [('false_finish', 1), ('true_finish', 0)]:
        selected = labels == v
        w, n = counts[v], int(selected.sum())
        data = margins[selected]
        recorded = anchor['strata'][title]
        a.require(recorded['n_tasks'] == n, 'stratum task count')
        for j, condition in enumerate('abcd'):
            estimates = np.einsum('bi,i->b', w, data[:, j]) / n
            a.close(recorded['conditions'][condition]['mean'], data[:, j].mean(), 'condition mean')
            a.close(recorded['conditions'][condition]['ci95'], bounds(estimates), 'condition interval')
            a.require(recorded['conditions'][condition]['positive_margin_count'] == int((data[:, j] > 0).sum()), 'positive margins')
        for j, name in enumerate(['a_minus_b', 'a_minus_c', 'a_minus_d'], 1):
            difference = data[:, 0] - data[:, j]
            a.close(recorded['deltas'][name]['mean'], difference.mean(), 'contrast mean')
            a.close(recorded['deltas'][name]['ci95'], bounds(np.einsum('bi,i->b', w, difference) / n), 'contrast interval')
        base, change = data[:, 0], delta[selected]
        ratios = recorded['fraction_note_and_thought']
        a.require(ratios['zero_baseline_count'] == int((base == 0).sum()), 'zero margin count')
        a.require(ratios['abs_baseline_below_one_count'] == int((abs(base) < 1).sum()), 'near-zero margin count')
        a.require((base != 0).all(), 'actual cohort ratio denominators nonzero')
        a.close(ratios['per_task_values'], change / base, 'individual ratios')
        a.close(ratios['mean_of_ratios']['mean'], np.mean(change / base), 'mean of ratios')
        a.close(ratios['mean_of_ratios']['ci95'], bounds(w @ (change / base) / n), 'mean of ratios interval')
        den = w @ base
        a.close(ratios['ratio_of_means']['value'], change.sum() / base.sum(), 'ratio of means')
        a.close(ratios['ratio_of_means']['ci95'], bounds((w @ change) / den), 'ratio of means interval')
        a.require(ratios['ratio_of_means']['finite_bootstrap_replicates'] == N_BOOT, 'finite ratio replicates')
        a.require(ratios['ratio_of_means']['zero_bootstrap_denominator_count'] == int((den == 0).sum()), 'zero bootstrap denominators')
        a.require(ratios['ratio_of_means']['nonpositive_bootstrap_denominator_count'] == int((den <= 0).sum()), 'nonpositive denominators')
    observed = delta[labels == 1].mean() - delta[labels == 0].mean()
    a.close(anchor['interaction']['false_minus_true_delta'], observed, 'interaction estimate')
    a.close(anchor['interaction']['ci95'], bounds(counts[1] @ delta[labels == 1] / 19 - counts[0] @ delta[labels == 0] / 20), 'interaction interval')
    rng = np.random.default_rng(SEED + 1)
    null = []
    for _ in range(N_BOOT):
        yp = rng.permutation(labels)
        null.append(delta[yp == 1].mean() - delta[yp == 0].mean())
    a.close(anchor['interaction']['p_two_sided'], (1 + np.count_nonzero(np.abs(null) >= abs(observed))) / (N_BOOT + 1), 'interaction permutation p')
    kept = np.array([not row['note_is_null'] for row in metadata])
    a.require(kept.sum() == 38 and anchor['null_note_contexts'] == [ids[i] for i in range(39) if not kept[i]], 'null note sensitivity coverage')
    for title, v in [('false_finish', 1), ('true_finish', 0)]:
        values = delta[(labels == v) & kept]
        draw = np.random.default_rng(SEED + 2 + v).multinomial(len(values), np.full(len(values), 1 / len(values)), size=N_BOOT)
        rec = anchor['nonnull_note_sensitivity_a_minus_b'][title]
        a.close(rec['mean'], values.mean(), 'nonnull sensitivity mean')
        a.close(rec['ci95'], bounds(draw @ values / len(values)), 'nonnull sensitivity interval')
        a.require(rec['n_tasks'] == len(values), 'nonnull sensitivity count')
    a.group('anchoring', paired_bootstraps=10000, interaction_label_permutations=10000, ratios_recomputed=True, nonnull_tasks=38)

    oof = np.load(root / 'oof_scores.npz')
    a.require(oof['context_ids'].tolist() == ids and np.array_equal(oof['y'], labels), 'OOF ordering')
    probes = {row['key']: row for row in result['probes']}
    expected_keys = {f'L{layer}_{position}_{model}' for layer in LAYERS for position in POSITIONS for model in MODELS}
    a.require(len(probes) == 72 and set(probes) == expected_keys, '72 complete probe configurations')
    auc_cache = {}

    def score_check(record, scores, name):
        a.require(scores.shape == (39,) and np.isfinite(scores).all(), 'score vector ' + name)
        statistic = two_u(labels, scores)
        a.require(record['statistic_2u'] == statistic, 'integer statistic ' + name)
        a.close(record['auroc'], statistic / 760, 'AUROC ' + name)
        draws = bootstrap_auc(labels, scores, counts)
        a.close(record['ci95'], bounds(draws), 'AUROC interval ' + name)
        return draws

    baseline_scores = {}
    fields = {'step': 'step', 'prompt_length': 'n_in', 'reasoning_length': 'reasoning_tokens'}
    for rec in result['baselines']:
        name = rec['name']
        if name.endswith('_raw_increasing'):
            base = name.removesuffix('_raw_increasing')
            scores = np.array([m[fields[base]] for m in metadata])
        elif name == 'train_prevalence_only':
            scores = (labels.sum() - labels) / 38
        else:
            scores = oof['baseline_' + name]
        baseline_scores[name] = scores
        auc_cache[name] = score_check(rec, scores, name)
    a.require(len(baseline_scores) == 8, 'eight baseline summaries')
    for key, rec in probes.items():
        scores = oof[key]
        a.require(((scores >= 0) & (scores <= 1)).all(), 'OOF probabilities ' + key)
        auc_cache[key] = score_check(rec, scores, key)
        for base, compared in rec['versus_baselines'].items():
            a.close(compared['difference'], (two_u(labels, scores) - two_u(labels, baseline_scores[base])) / 760, 'paired baseline difference')
            a.close(compared['ci95'], bounds(auc_cache[key] - auc_cache[base]), 'paired baseline interval')
    winner = max(result['probes'], key=lambda row: row['statistic_2u'])
    a.require(result['best_probe']['key'] == winner['key'], 'selected original winner')
    a.require(sum(row['convergence_warnings'] for row in probes.values()) == 702, 'original warning total')
    a.require(all(row['convergence_warnings'] == (39 if row['model'] == 'mlp64_l2' else 0) for row in probes.values()), 'original warnings by model')
    for base, rec in result['best_probe_vs_raw_metadata'].items():
        a.close(rec['difference'], (two_u(labels, oof[winner['key']]) - two_u(labels, baseline_scores[base])) / 760, 'raw metadata difference')
        a.close(rec['ci95'], bounds(auc_cache[winner['key']] - auc_cache[base]), 'raw metadata difference interval')
    a.group('original_probe_statistics', configurations=72, baseline_summaries=8, paired_baseline_comparisons=291, original_mlp_warning_count=702)

    neighbor_cache = {}
    for li, layer in enumerate(LAYERS):
        for pi, position in enumerate(POSITIONS):
            vectors = residuals[:, li, pi]
            unit = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
            similarity = unit @ unit.T
            np.fill_diagonal(similarity, -np.inf)
            neighbors = np.argsort(-similarity, axis=1, kind='stable')[:, :5]
            a.require(all(i not in neighbors[i] for i in range(39)), 'held-out exclusion in cosine neighbors')
            neighbor_cache[layer, position] = neighbors
            for k in [3, 5]:
                a.close(oof[f'L{layer}_{position}_knn{k}_cosine'], labels[neighbors[:, :k]].mean(axis=1), 'kNN scores from raw residuals', tolerance=0)
    a.require(winner['model'] == 'knn3_cosine', 'audited primary permutation model is cosine kNN3')
    neighbors = neighbor_cache[winner['layer'], winner['position']][:, :3]
    permutations = [json.loads(line) for line in (root / 'permutations.jsonl').read_text().splitlines()]
    a.require(len(permutations) == 1000, '1000 complete label permutations')
    rng = np.random.default_rng(SEED + 4)
    statistics = []
    for i, row in enumerate(permutations):
        yp = rng.permutation(labels)
        a.require(row['index'] == i and row['best_key'] == winner['key'], 'permutation identity')
        a.require(np.array_equal(row['labels'], yp) and yp.sum() == 19, 'permutation label replay')
        score = yp[neighbors].mean(axis=1)
        statistic = two_u(yp, score)
        a.require(row['statistic_2u'] == statistic, 'permutation statistic reconstructed from residuals')
        a.close(row['auroc'], statistic / 760, 'permutation AUROC')
        statistics.append(statistic)
    statistics = np.array(statistics)
    exceedances = int((statistics >= winner['statistic_2u']).sum())
    pvalue = (1 + exceedances) / 1001
    perm = result['permutation']
    a.close(perm['p_unadjusted'], pvalue, 'primary permutation p')
    a.close(perm['p_bonferroni_72'], min(1, 72 * pvalue), 'Bonferroni p')
    a.close(perm['minimum_possible_adjusted_p'], 72 / 1001, 'permutation resolution')
    a.close(perm['null_mean'], (statistics / 760).mean(), 'permutation null mean')
    a.close(perm['null_ci95'], bounds(statistics / 760), 'permutation null quantiles')
    a.group('cosine_and_permutations', raw_residual_knn_vectors=36, complete_permutations=1000, tail_count_including_ties=exceedances, unadjusted_p=pvalue)

    power = result['power']

    def exact_upper(u):
        positive = np.arange(1, 20)
        remaining = u
        for i in range(18, -1, -1):
            shift = min(20, remaining)
            positive[i] += shift
            remaining -= shift
        negative = np.array([v for v in range(1, 40) if v not in positive])
        test = mannwhitneyu(positive, negative, alternative='greater', method='exact')
        a.require(test.statistic == u, 'independent exact U construction')
        return test.pvalue

    levels = {'one_sided_05': 0.05, 'two_sided_05': 0.025, 'familywise_72': 0.05 / 72}
    for name, alpha in levels.items():
        critical = power['critical_U'][name]
        tail = exact_upper(critical)
        a.require(tail <= alpha < exact_upper(critical - 1), 'minimal exact rejection threshold')
        a.close(power['actual_null_rejection_probability'][name], tail * (2 if name == 'two_sided_05' else 1), 'exact null rejection size')
    a.require(power['simulations_per_effect'] == 20000 and len(power['curve']) == 91, 'power grid coverage')
    rng = np.random.default_rng(SEED + 3)
    positives = rng.normal(size=(20000, 19, 1))
    negatives = rng.normal(size=(20000, 1, 20))
    for row, population_auc in zip(power['curve'], np.round(np.linspace(0.5, 0.95, 91), 3)):
        a.close(row['population_auroc'], population_auc, 'power grid value')
        shift = math.sqrt(2) * norm.ppf(population_auc)
        u = (positives + shift > negatives).sum(axis=(1, 2))
        for name, critical in power['critical_U'].items():
            rejection = (u >= critical) | (u <= 380 - critical) if name == 'two_sided_05' else u >= critical
            a.close(row[name], rejection.mean(), 'power simulation replay', tolerance=0)
    for name in levels:
        crossing = next(row['population_auroc'] for row in power['curve'] if row[name] >= 0.8)
        a.close(power['minimum_auroc_for_80_percent_power'][name], crossing, '80 percent power crossing')
    a.close(power['mc_se_at_power_80'], math.sqrt(0.8 * 0.2 / 20000), 'power Monte Carlo error')
    a.require(power['actual_1000_permutation_bonferroni_power_at_05'] == 0 and 72 / 1001 > 0.05, 'actual corrected power zero')
    a.group('oracle_power', independently_checked_exact_thresholds=power['critical_U'], replayed_effects=91, simulations_per_effect=20000)

    sensitivity = a.json('MLP_SENSITIVITY.json')
    a.require(result['mlp_optimization_sensitivity'] == sensitivity, 'reported supplemental result copy')
    a.require(sensitivity['status'] == 'complete' and sensitivity['post_result_optimization_sensitivity'], 'supplement completion and disclosure')
    a.hash_references(sensitivity['source_hashes'])
    supplemental = np.load(root / 'mlp_sensitivity_oof.npz')
    a.require(np.array_equal(supplemental['y'], labels), 'supplemental label order')
    a.require(len(sensitivity['results']) == 18 and len(sensitivity['folds']) == sensitivity['n_fits'] == 702, 'supplemental coverage')
    expected_mlp = {key for key in expected_keys if key.endswith('mlp64_l2')}
    a.require({row['key'] for row in sensitivity['results']} == expected_mlp, '18 supplemental configurations')
    a.require({(row['key'], row['fold']) for row in sensitivity['folds']} == {(key, i) for key in expected_mlp for i in range(39)}, '702 unique supplemental folds')
    warnings_count = 0
    for row in sensitivity['folds']:
        i, key = row['fold'], row['key']
        a.require(row['heldout_context'] == ids[i] and row['train_count'] == 38, 'supplemental held-out task identity')
        a.require(0 < row['n_iter'] <= 3000 and np.isfinite(row['loss']), 'supplemental optimizer diagnostic')
        a.close(row['score'], supplemental[key][i], 'supplemental stored score', tolerance=0)
        a.close(row['old_score'], oof[key][i], 'supplemental original score', tolerance=0)
        a.require(isinstance(row['convergence_warnings'], list), 'supplemental warning log')
        warnings_count += bool(row['convergence_warnings'])
    for rec in sensitivity['results']:
        key = rec['key']
        draws = score_check(rec, supplemental[key], key + '_3000')
        a.close(rec['original_auroc'], probes[key]['auroc'], 'supplemental original AUROC')
        a.close(rec['delta_auroc_ci95'], bounds(draws - auc_cache[key]), 'supplemental paired change interval')
        change = np.abs(supplemental[key] - oof[key])
        a.close(rec['max_absolute_score_change'], change.max(), 'supplemental maximum score change')
        a.close(rec['mean_absolute_score_change'], change.mean(), 'supplemental mean score change')
        warning_folds = sum(bool(row['convergence_warnings']) for row in sensitivity['folds'] if row['key'] == key)
        a.require(rec['warning_folds'] == warning_folds, 'supplemental cell warning count')
    a.require(sensitivity['warning_folds'] == warnings_count, 'supplemental warning total')
    a.require(sensitivity['best_descriptive'] == max(sensitivity['results'], key=lambda row: row['statistic_2u']), 'supplemental descriptive maximum')
    a.require(sensitivity['seconds'] <= 1200, 'supplemental declared time bound')
    a.require('not performed' in sensitivity['permutation_test'], 'no supplemental inference inherited')
    a.group('mlp_sensitivity', score_vectors=18, fold_diagnostics=702, warning_folds=warnings_count, no_model_refit=True)

    report = (root / 'REPORT.md').read_text()
    table_numbers = 0

    def check_ci(cell, rec, name, key='mean'):
        nonlocal table_numbers
        actual = re.fullmatch(r'(-?[0-9.]+) \[(-?[0-9.]+) ; (-?[0-9.]+)\]', cell)
        a.require(actual is not None, 'report interval formatting ' + name)
        a.close([float(v) for v in actual.groups()], [rec[key], *rec['ci95']], 'report interval ' + name, tolerance=0.000500001)
        table_numbers += 3

    main_cells = supplemental_cells = 0
    for line in report.splitlines():
        if not re.match(r'^\| (8|12|16|20|24|28) \| (prompt_end|reflection_end|note_onset) \|', line):
            continue
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        layer, position = int(cells[0]), cells[1]
        if len(cells) == 6:
            for model, cell in zip(MODELS, cells[2:]):
                key = f'L{layer}_{position}_{model}'
                check_ci(cell, probes[key], key, key='auroc')
                main_cells += 1
        else:
            a.require(len(cells) == 5, 'supplement report table shape')
            rec = next(row for row in sensitivity['results'] if row['layer'] == layer and row['position'] == position)
            a.close(float(cells[2]), rec['original_auroc'], 'report supplemental original AUROC', tolerance=0.000500001)
            check_ci(cells[3], rec, rec['key'] + '_3000', key='auroc')
            a.require(int(cells[4]) == rec['warning_folds'], 'report supplemental warning count')
            table_numbers += 2
            supplemental_cells += 1
    a.require(main_cells == 72 and supplemental_cells == 18, 'report complete primary and supplemental tables')

    def rows_in(start, end):
        section = report.split(start, 1)[1].split(end, 1)[0]
        return [[v.strip() for v in line.strip('|').split('|')] for line in section.splitlines() if line.startswith('| ')]

    baseline_rows = rows_in('### Baselines', '### Toutes les sondes')
    for rec in result['baselines']:
        row = next(row for row in baseline_rows if row[0] == rec['name'])
        check_ci(row[1], rec, 'baseline ' + rec['name'], key='auroc')
    comparison_rows = rows_in('| Meilleure sonde moins baseline', '### Vérification supplémentaire')
    for name, rec in {**result['best_probe']['versus_baselines'], **result['best_probe_vs_raw_metadata']}.items():
        row = next(row for row in comparison_rows if row[0] == name)
        check_ci(row[1], rec, 'comparison ' + name, key='difference')
    table_rows = [[v.strip() for v in line.strip('|').split('|')] for line in report.splitlines() if line.startswith('| ')]
    strata = [anchor['strata'][name] for name in ['false_finish', 'true_finish']]
    for condition in 'abcd':
        row = next(row for row in table_rows if row[0].startswith(condition + ' —'))
        for j, stratum in enumerate(strata, 1):
            check_ci(row[j], stratum['conditions'][condition], 'anchor condition')
        row = next(row for row in table_rows if row[0] == condition)
        for j, stratum in enumerate(strata, 1):
            a.require(row[j] == str(stratum['conditions'][condition]['positive_margin_count']) + '/' + str(stratum['n_tasks']), 'report positive-margin count')
            table_numbers += 1
    for key in ['a_minus_b', 'a_minus_c', 'a_minus_d']:
        row = next(row for row in table_rows if row[0] == key.replace('_minus_', ' − '))
        for j, stratum in enumerate(strata, 1):
            check_ci(row[j], stratum['deltas'][key], 'anchor contrast')
    for name, label, key in [('mean_of_ratios', 'Moyenne de (a−b)/a par tâche', 'mean'), ('ratio_of_means', '(moyenne a − moyenne b) / moyenne a', 'value')]:
        row = next(row for row in table_rows if row[0] == label)
        for j, stratum in enumerate(strata, 1):
            check_ci(row[j], stratum['fraction_note_and_thought'][name], name, key=key)
    for name, label in [('one_sided_05', 'Unilatéral α=0,05'), ('two_sided_05', 'Bilatéral α=0,05'), ('familywise_72', 'Unilatéral α=0,05/72, résolution idéale')]:
        row = next(row for row in table_rows if row[0] == label)
        a.close(float(row[1]), power['minimum_auroc_for_80_percent_power'][name], 'report oracle power', tolerance=0.000500001)
        table_numbers += 1
    for phrase in ['pas sur une équivalence', 'Le p brut du gagnant n’est pas confirmatoire', 'puissance nulle',
                   'ne garantissent pas une couverture de 95 %', 'aucun score n’a été inversé',
                   'Aucun test de permutation n’est réalisé pour cette famille supplémentaire',
                   'absence de preuve', 'preuve d’absence', 'n’est pas un échantillon aléatoire']:
        a.require(phrase in report, 'reported interpretation limit: ' + phrase)
    a.require(str(warnings_count) + ' conservent un avertissement de convergence' in report, 'report supplemental warning total')
    a.require(f"p unilatéral brut = {pvalue:.4f}" in report, 'report primary p-value')
    a.group('report', checked_table_numbers=table_numbers, primary_probe_cells=72, supplemental_cells=18, interpretation_limits_present=True)
    for name, digest in before.items():
        a.require(a.sha(name) == digest, 'input remained frozen: ' + name)
    return a, before


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--expect-result-sha')
    parser.add_argument('--expect-report-sha')
    args = parser.parse_args()
    started = time.monotonic()
    command = shlex.join([sys.executable, *sys.argv])
    try:
        audit, hashes = verify(args.root, args.expect_result_sha, args.expect_report_sha)
        status, error, code = 'RAN/PASSED/CORRECT', None, 0
        groups, count = audit.groups, audit.checks
    except Exception:
        status, error, code = 'RAN/FAILED/NOT_CORRECT', traceback.format_exc(), 1
        groups, count = {}, None
        hashes = {name: hashlib.sha256((args.root / name).read_bytes()).hexdigest()
                  for name in ['RESULT.json', 'RESULT_CORE.json', 'REPORT.md'] if (args.root / name).exists()}
    not_run = ['No model or GPU execution; no source or weight mutation.',
               'No fresh logistic or MLP cohort fits; their statistics were recomputed from stored OOF scores.',
               'No supplemental MLP permutation test, as declared in the amendment.',
               'Source, evaluator, replay, and weight audit contents were linked by hashes; their external original files were not re-read here.',
               'No claim of future-performance confidence coverage, absence of a discriminator, or behavioral improvement.']
    output = {'verdict': status, 'checker': '/root/stats_check', 'verified_at_utc': datetime.now(timezone.utc).isoformat(),
              'command': command, 'exit_code': code, 'elapsed_seconds': time.monotonic() - started,
              'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'input_hashes': hashes, 'checks_passed': count, 'groups': groups, 'not_run': not_run, 'error': error}
    (args.root / 'VERIFY_FINAL.json').write_text(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    lines = ['# Independent final statistical verification', '', '**' + status + '**', '',
             'Command: `' + command + '`', '', 'Exit code: ' + str(code) + '.', '',
             'The checker independently reconstructs margins, paired bootstrap summaries, exact rank statistics, cosine neighbors, label permutations, oracle power and supplemental score diagnostics. It does not import the maker’s analysis functions.', '']
    if code == 0:
        lines += ['- **RAN:** All requested numerical groups and report tables.',
                  '- **PASSED:** ' + str(count) + ' checks; all groups passed.',
                  '- **CORRECT:** The frozen results and report agree with the stored evidence within the declared exploratory scope.', '']
        lines += ['- ' + name + ': ' + json.dumps(value, ensure_ascii=False) for name, value in groups.items()]
    else:
        lines += ['The final audit failed. This report is not a passing verdict.', '', '```', error, '```']
    lines += ['', '**NOT RUN / limits:**', ''] + ['- ' + value for value in not_run]
    lines += ['', '**Verified versions:**', ''] + ['- `' + name + '`: `' + digest + '`' for name, digest in hashes.items()]
    lines += ['- `verify_results.py`: `' + output['checker_sha256'] + '`', '',
              'The original 72-probe family and the 18-cell post-result optimization sensitivity remain distinct. Fixed-OOF bootstrap intervals are descriptive; the corrected 1,000-permutation primary test cannot reject at 5%.', '']
    (args.root / 'VERIFY_FINAL.md').write_text('\n'.join(lines))
    print(json.dumps({'verdict': status, 'exit_code': code, 'checks': count, 'seconds': output['elapsed_seconds']}), flush=True)
    if error:
        print(error, file=sys.stderr)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
