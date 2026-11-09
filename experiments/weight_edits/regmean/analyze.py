from common import *
import numpy as np
from sklearn.metrics import roc_auc_score


def basis(x, center=False):
    if center:
        x = x - x.mean(1, keepdim=True)
    u, s, _ = torch.linalg.svd(x, full_matrices=False)
    rank = int((s > s.max() * max(x.shape) * torch.finfo(torch.float32).eps).sum())
    return u[:, :rank], rank


def geometry(f, t, center=False):
    if center:
        f = f - f.mean(1, keepdim=True)
        t = t - t.mean(1, keepdim=True)
    qf, rf = basis(f)
    qt, rt = basis(t)
    cosine = torch.linalg.svdvals(qf.T @ qt).clamp(0, 1)
    angles = torch.rad2deg(torch.acos(cosine))
    assert rf > 0 and rt > 0 and f.square().sum() > 0 and t.square().sum() > 0
    return dict(rank_f=rf, rank_t=rt, relative_rank_threshold=max(f.shape[0], f.shape[1], t.shape[1]) * torch.finfo(torch.float32).eps,
                angles_degrees=angles.tolist(),
                min_angle=float(angles.min()), median_angle=float(angles.median()), max_angle=float(angles.max()),
                mean_cos_squared=float(cosine.square().mean()),
                f_energy_in_t=float((qt.T @ f).square().sum() / f.square().sum()),
                t_energy_in_f=float((qf.T @ t).square().sum() / t.square().sum()))


def auc(y, score):
    positive = score[y == 1, None]
    negative = score[None, y == 0]
    return float(((positive > negative) + .5 * (positive == negative)).mean())


def cv_probe(features, labels, groups, folds, normalize=True):
    x = torch.as_tensor(features, dtype=torch.float64)
    y = torch.as_tensor(labels, dtype=torch.float64)
    if normalize:
        x = x / x.norm(dim=1, keepdim=True).clamp_min(1e-12)
    predictions = {"ridge": np.zeros(len(y)), "centroid": np.zeros(len(y))}
    fold_scores = []
    permutation_labels = np.tile(np.asarray(labels), (199, 1))
    rng = np.random.default_rng(180926)
    for fold in sorted(set(folds)):
        indices = np.flatnonzero(np.asarray(folds) == fold)
        for p in range(len(permutation_labels)):
            permutation_labels[p, indices] = rng.permutation(np.asarray(labels)[indices])
    permutation_scores = {"ridge": np.zeros(199), "centroid": np.zeros(199)}
    total_pairs = 0
    for fold in sorted(set(folds)):
        test = torch.tensor([f == fold for f in folds])
        train = ~test
        assert not {groups[i] for i in torch.where(train)[0]} & {groups[i] for i in torch.where(test)[0]}
        assert len(set(y[train].tolist())) == len(set(y[test].tolist())) == 2
        z, v = x[train], x[test]
        if not normalize:
            scale = z.std(0).clamp_min(1e-8)
            z, v = z / scale, v / scale
        mean = z.mean(0)
        z, v = z - mean, v - mean
        gram = z @ z.T
        ridge = max(float(gram.trace() / len(z)) * 0.1, 1e-12)
        target = 2 * y[train] - 1
        cross = v @ z.T
        influence = torch.linalg.solve(gram + ridge * torch.eye(len(z)), cross.T).T
        pred_ridge = influence @ (target - target.mean()) + target.mean()
        n_positive = int(y[train].sum())
        n_negative = int(train.sum()) - n_positive
        pred_centroid = cross @ (y[train] / n_positive - (1 - y[train]) / n_negative)
        n_pairs = int(y[test].sum()) * (int(test.sum()) - int(y[test].sum()))
        total_pairs += n_pairs
        perm_train = torch.as_tensor(permutation_labels[:, train.numpy()].T, dtype=torch.float64)
        perm_ridge = influence @ (2 * perm_train - 1 - target.mean()) + target.mean()
        perm_centroid = cross @ (perm_train / n_positive - (1 - perm_train) / n_negative)
        for name, perm in [("ridge", perm_ridge), ("centroid", perm_centroid)]:
            for p in range(199):
                permutation_scores[name][p] += n_pairs * auc(permutation_labels[p, test.numpy()], perm[:, p].numpy())
        scores = {}
        for name, pred in [("ridge", pred_ridge), ("centroid", pred_centroid)]:
            predictions[name][test.numpy()] = pred.numpy()
            scores[name] = float(roc_auc_score(y[test].numpy(), pred.numpy()))
        fold_scores.append(dict(fold=fold, n_train=int(train.sum()), n_test=int(test.sum()), n_positive=int(y[test].sum()), n_negative=int(test.sum()-y[test].sum()), pairs=n_pairs, auc=scores))
    weighted_auc = {name: sum(f["auc"][name] * f["pairs"] for f in fold_scores) / total_pairs for name in predictions}
    permutation = {}
    for name in predictions:
        null = permutation_scores[name] / total_pairs
        permutation[name] = dict(p_value=float((1 + (null >= weighted_auc[name]).sum()) / 200), null_median=float(np.median(null)), null_95=float(np.quantile(null, .95)))
    return dict(oof_auc={name: float(roc_auc_score(labels, pred)) for name, pred in predictions.items()},
                pair_weighted_fold_auc=weighted_auc, within_fold_task_permutation=permutation,
                mean_fold_auc={name: float(np.mean([f["auc"][name] for f in fold_scores])) for name in predictions},
                folds=fold_scores, predictions={name: pred.tolist() for name, pred in predictions.items()})


def main():
    m = read_frozen()
    pack = torch.load(ROOT / "captures.pt", weights_only=True, map_location="cpu")
    assert pack["complete"] and pack["manifest_sha256"] == sha(ROOT / "manifest.json")
    assert sha(ROOT / "captures.pt") == (ROOT / "captures.sha256").read_text().strip()
    rows = [r for r in m["rows"] if r["label"] in ["fs+", "fs-"]]
    labels = [int(r["label"] == "fs+") for r in rows]
    groups = [r["task_id"] for r in rows]
    folds = [r["fold"] for r in rows]
    assert len(set(groups)) == len(rows)
    records = []
    for name in writer_names():
        for pos in [0, 1]:
            x = torch.stack([pack["captures"][r["id"]][name][pos] for r in rows]).double()
            f, t = x[np.array(labels) == 1].T, x[np.array(labels) == 0].T
            g = torch.stack([pack["captures"][r["id"]][name][pos] for r in m["rows"] if r["label"] == "healthy"]).double().T
            records.append(dict(writer=name, position=m["positions"][pos],
                                raw=geometry(f, t), centered=geometry(f, t, True),
                                false_healthy=geometry(f, g), true_healthy=geometry(t, g),
                                cv=cv_probe(x, labels, groups, folds),
                                activation_norm_baseline=cv_probe(x.norm(dim=1)[:, None], labels, groups, folds, normalize=False)))
    baseline = {name: cv_probe([[r[name]] for r in rows], labels, groups, folds, normalize=False)
                for name in ["t", "n_in"]}
    baseline["step_and_length"] = cv_probe([[r["t"], r["n_in"]] for r in rows], labels, groups, folds, normalize=False)
    result = dict(n_fs_positive=sum(labels), n_true_finish=len(labels) - sum(labels), task_ids=groups, labels=labels,
                  records=records, baselines=baseline, capture_sha256=sha(ROOT / "captures.pt"),
                  caveat="Finite-sample angles and fixed linear probes do not establish an information-theoretic bound. Endthink includes recorded reasoning. Length/step confounding reported. Primary AUC uses within-fold positive-negative pairs; pooled OOF is secondary and uncalibrated. Permutations shuffle whole task labels within fixed folds, preserving class counts. One inherited fold has a single true finish. Multiple-writer p-values are descriptive and uncorrected.")
    write_json(ROOT / "overlap.json", result)
    summary = {}
    for pos in m["positions"]:
        rs = [r for r in records if r["position"] == pos]
        summary[pos] = dict(auroc_ridge_median=float(np.median([r["cv"]["pair_weighted_fold_auc"]["ridge"] for r in rs])),
                            auroc_ridge_range=[min(r["cv"]["pair_weighted_fold_auc"]["ridge"] for r in rs), max(r["cv"]["pair_weighted_fold_auc"]["ridge"] for r in rs)],
                            median_principal_angle=float(np.median([r["raw"]["median_angle"] for r in rs])),
                            mean_cos_squared=float(np.mean([r["raw"]["mean_cos_squared"] for r in rs])),
                            f_energy_in_t=float(np.mean([r["raw"]["f_energy_in_t"] for r in rs])))
    summary["baselines"] = {k: v["pair_weighted_fold_auc"] for k, v in baseline.items()}
    summary["total_empirical_overlap"] = all(r["raw"]["max_angle"] < 5 and r["raw"]["f_energy_in_t"] > .99 and r["raw"]["t_energy_in_f"] > .99 for r in records)
    write_json(ROOT / "overlap_summary.json", summary)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
