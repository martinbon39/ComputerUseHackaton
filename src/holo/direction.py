"""Phase 3: find the defect direction.
For each layer: diff-of-means u_l = mean(pos) - mean(neg) (normalised); AUROC of <h, u_l> on a held-out split
BY TASK (leave-tasks-out CV, no step leakage); compared with a linear logistic probe.
Usage: python -m holo.direction --tag diag --target fs|loop [--site resid|mlp]
"""
import holo.settings as S
import argparse, json
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from holo.taxonomy import scan


def collect(tags, target, site, min_t=0):
    X, y, g, meta = [], [], [], []
    for tag in tags:
        for d, s, steps, c in scan(tag):
            if not (d / "acts.npz").exists():
                continue
            A = np.load(d / "acts.npz")[site].astype(np.float32)  # [steps, L, D]
            labs = c["fs_labels"] if target == "fs" else c["labels"]
            pos, neg = ("fs+", "fs-") if target == "fs" else ("loop+", "loop-")
            for i, lab in enumerate(labs[: len(A)]):
                if lab in (pos, neg) and i >= min_t:
                    X.append(A[i]); y.append(int(lab == pos)); g.append(s["task"])
                    meta.append({"run": d.name, "t": i, "n_in": steps[i]["n_in"]})
    return np.stack(X), np.array(y), np.array(g), meta


def layer_scores(X, y, g, n_splits=5):
    L = X.shape[1]
    n_groups = len(set(g))
    gkf = GroupKFold(n_splits=min(n_splits, n_groups))
    dom_pred = np.zeros((L, len(y))); lr_pred = np.zeros((L, len(y)))
    for tr, te in gkf.split(X, y, g):
        if len(set(y[tr])) < 2:
            continue
        for l in range(L):
            Xtr, Xte = X[tr, l], X[te, l]
            u = Xtr[y[tr] == 1].mean(0) - Xtr[y[tr] == 0].mean(0)
            u /= np.linalg.norm(u) + 1e-8
            dom_pred[l, te] = Xte @ u
            sc = StandardScaler().fit(Xtr)
            clf = LogisticRegression(C=0.01, max_iter=2000, class_weight="balanced").fit(sc.transform(Xtr), y[tr])
            lr_pred[l, te] = clf.decision_function(sc.transform(Xte))
    auc_dom = [roc_auc_score(y, dom_pred[l]) for l in range(L)]
    auc_lr = [roc_auc_score(y, lr_pred[l]) for l in range(L)]
    return np.array(auc_dom), np.array(auc_lr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", default="diag")
    ap.add_argument("--target", default="fs")
    ap.add_argument("--site", default="resid")
    ap.add_argument("--out", default="directions")
    ap.add_argument("--min_t", type=int, default=0, help="only keep steps with index >= min_t (position control)")
    a = ap.parse_args()
    X, y, g, meta = collect(a.tags.split(","), a.target, a.site, a.min_t)
    print(f"target={a.target} site={a.site} n={len(y)} pos={y.sum()} neg={(1 - y).sum()} tasks={len(set(g))}")
    auc_dom, auc_lr = layer_scores(X, y, g)
    base_t = roc_auc_score(y, [m["t"] for m in meta]); base_nin = roc_auc_score(y, [m["n_in"] for m in meta])
    print(f"baseline AUROC  step_index={base_t:.3f}  context_len={base_nin:.3f}")
    # final directions from all data
    U = np.stack([X[y == 1, l].mean(0) - X[y == 0, l].mean(0) for l in range(X.shape[1])])
    norms = np.linalg.norm(U, axis=1, keepdims=True); U = U / norms
    proj = np.einsum("nld,ld->nl", X, U)
    stats = {"pos_mean": proj[y == 1].mean(0).tolist(), "neg_mean": proj[y == 0].mean(0).tolist(),
             "pos_std": proj[y == 1].std(0).tolist(), "neg_std": proj[y == 0].std(0).tolist()}
    np.savez(S.ROOT / f"{a.out}_{a.target}_{a.site}.npz", U=U, raw_norm=norms[:, 0], auc_dom=auc_dom, auc_lr=auc_lr,
             **{k: np.array(v) for k, v in stats.items()})
    res = {"target": a.target, "site": a.site, "n": int(len(y)), "pos": int(y.sum()), "neg": int((1 - y).sum()),
           "tasks": sorted(set(g.tolist())), "auc_dom": np.round(auc_dom, 3).tolist(), "auc_lr": np.round(auc_lr, 3).tolist(),
           "best_layers_dom": np.argsort(-auc_dom)[:3].tolist(), "min_t": a.min_t,
           "baseline_auc_step_index": round(base_t, 3), "baseline_auc_context_len": round(base_nin, 3)}
    (S.ROOT / f"{a.out}_{a.target}_{a.site}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for l in range(len(auc_dom)):
        print(f"L{l:02d} dom={auc_dom[l]:.3f} lr={auc_lr[l]:.3f}")
    print("best", res["best_layers_dom"])


if __name__ == "__main__":
    main()
