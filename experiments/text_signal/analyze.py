"""Text-signal detector of false success (A) and sampling-consistency detector (B)."""
import json
import os
import re
import sys

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut, StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(20261108)
N_BOOT = 2000
N_PERM = 500

HEDGE = ["appears", "appear", "seems", "seem", "should", "likely", "verify", "however",
         "might", "may", "probably", "assume", "but", "although", "not sure", "cannot",
         "can't", "unable", "instead", "alternative"]
DONE = ["saved", "completed", "complete", "successfully", "done", "finished", "accomplished",
        "now shows", "has been", "have been"]

data = json.load(open(f"{HERE}/episodes.json"))
E = data["episodes"]
y = np.array([e["y_fs"] for e in E])
groups = np.array([e["task"] for e in E])
domains = np.array([[e["domain"]] for e in E])
final_text = [e["final_note"] + " " + e["final_thought"] for e in E]
last3_text = [e["last3_notes"] for e in E]
reason_text = [e["final_reasoning"] for e in E]
all_text = [a + " " + b for a, b in zip(final_text, reason_text)]


def count(t, words):
    t = t.lower()
    return sum(len(re.findall(r"\b" + re.escape(w) + r"\b", t)) for w in words)


def hand(texts):
    rows = []
    for t in texts:
        nw = max(len(t.split()), 1)
        h, d = count(t, HEDGE), count(t, DONE)
        rows.append([len(t), nw, h, d, h / nw, d / nw])
    return np.array(rows, float)


HAND_NAMES = ["chars", "words", "hedge_n", "done_n", "hedge_rate", "done_rate"]
X_hand = hand(final_text)
X_hand_r = hand(all_text)


def num(v):
    return np.array(v, float).reshape(-1, 1)


feat = {
    "baseline_final_step": num([e["final_step"] for e in E]),
    "baseline_n_steps": num([e["n_steps"] for e in E]),
    "baseline_final_reasoning_chars": num([len(e["final_reasoning"]) for e in E]),
    "baseline_total_reasoning_chars": num([e["total_reasoning_chars"] for e in E]),
}

LR = dict(C=1.0, max_iter=2000, class_weight="balanced")


def tfidf_model():
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                                         lowercase=True), LogisticRegression(**LR))


def dense_model():
    return make_pipeline(StandardScaler(), LogisticRegression(**LR))


def domain_model():
    return make_pipeline(OneHotEncoder(handle_unknown="ignore"), LogisticRegression(**LR))


MODELS = {
    "tfidf_final_note_thought": (tfidf_model, final_text),
    "tfidf_last3_notes": (tfidf_model, last3_text),
    "tfidf_final_reasoning": (tfidf_model, reason_text),
    "tfidf_final_all(note+thought+reasoning)": (tfidf_model, all_text),
    "hand_final_note_thought": (dense_model, X_hand),
    "hand_final_all": (dense_model, X_hand_r),
    "domain_onehot": (domain_model, domains),
}
for k, v in feat.items():
    MODELS[k] = (dense_model, v)


def index(X, idx):
    return [X[i] for i in idx] if isinstance(X, list) else X[idx]


def oof(make, X, yy, splits):
    p = np.full(len(yy), np.nan)
    for tr, te in splits:
        if len(set(yy[tr])) < 2:
            p[te] = 0.5
            continue
        m = make().fit(index(X, tr), yy[tr])
        p[te] = m.predict_proba(index(X, te))[:, 1]
    return p


def boot_ci(yy, s, g):
    ug = np.unique(g)
    rows = {u: np.where(g == u)[0] for u in ug}
    out = []
    for _ in range(N_BOOT):
        idx = np.concatenate([rows[u] for u in RNG.choice(ug, len(ug))])
        if len(set(yy[idx])) == 2:
            out.append(roc_auc_score(yy[idx], s[idx]))
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


def boot_diff(yy, s1, s2, g):
    ug = np.unique(g)
    rows = {u: np.where(g == u)[0] for u in ug}
    out = []
    for _ in range(N_BOOT):
        idx = np.concatenate([rows[u] for u in RNG.choice(ug, len(ug))])
        if len(set(yy[idx])) == 2:
            out.append(roc_auc_score(yy[idx], s1[idx]) - roc_auc_score(yy[idx], s2[idx]))
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


logo = list(LeaveOneGroupOut().split(final_text, y, groups))
res = {"n_episodes": int(len(y)), "n_fs": int(y.sum()), "n_true": int((1 - y).sum()),
       "n_tasks": int(len(set(groups))), "collection_audit": data["audit"], "models": {}}
mixed = {t for t in set(groups) if len(set(y[groups == t])) == 2}
res["n_mixed_tasks"] = len(mixed)

raw_auc = {k: float(roc_auc_score(y, v[:, 0])) for k, v in feat.items()}
scores = {}
for name, (make, X) in MODELS.items():
    s = oof(make, X, y, logo)
    scores[name] = s
    auc = float(roc_auc_score(y, s))
    rep = []
    for seed in range(5):
        sp = list(StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(final_text, y, groups))
        rep.append(float(roc_auc_score(y, oof(make, X, y, sp))))
    res["models"][name] = {"auroc_logo": auc, "ci95_task_boot": boot_ci(y, s, groups),
                           "auroc_5fold_grouped_mean_5rep": float(np.mean(rep)),
                           "auroc_5fold_grouped_range": [min(rep), max(rep)]}
    if name in raw_auc:
        res["models"][name]["auroc_raw_feature_no_fit"] = raw_auc[name]
    print(name, res["models"][name], file=sys.stderr)

# within-mixed-task AUROC (domain/task identity cannot help there)
mm = np.isin(groups, list(mixed))
res["within_mixed_tasks"] = {"n_episodes": int(mm.sum()), "n_fs": int(y[mm].sum())}
for name in MODELS:
    res["within_mixed_tasks"][name] = float(roc_auc_score(y[mm], scores[name][mm]))

text_models = [k for k in MODELS if k.startswith(("tfidf", "hand"))]
best = max(text_models, key=lambda k: res["models"][k]["auroc_logo"])
res["best_text_model"] = best
res["best_minus_final_step_ci95"] = boot_diff(y, scores[best], scores["baseline_final_step"], groups)
res["best_minus_domain_ci95"] = boot_diff(y, scores[best], scores["domain_onehot"], groups)

# permutation tests for the best text model
make, X = MODELS[best]
obs = res["models"][best]["auroc_logo"]
gidx = {t: np.where(groups == t)[0] for t in set(groups)}
null_within, null_global = [], []
for i in range(N_PERM):
    yp = y.copy()
    for t, ix in gidx.items():
        yp[ix] = RNG.permutation(y[ix])
    null_within.append(roc_auc_score(yp, oof(make, X, yp, logo)))
    yg = RNG.permutation(y)
    null_global.append(roc_auc_score(yg, oof(make, X, yg, logo)))
res["permutation"] = {
    "model": best, "observed_auroc": obs, "n_perm": N_PERM,
    "within_task_p": float((1 + sum(v >= obs for v in null_within)) / (N_PERM + 1)),
    "within_task_null_mean": float(np.mean(null_within)),
    "within_task_null_95pct": float(np.percentile(null_within, 95)),
    "global_p": float((1 + sum(v >= obs for v in null_global)) / (N_PERM + 1)),
    "global_null_mean": float(np.mean(null_global)),
    "note": "within-task permutation only shuffles labels inside the mixed tasks; pure tasks keep labels, "
            "so its null keeps task/domain signal and tests only the extra within-task signal",
}

# top n-grams on the full data for each tfidf model
res["top_ngrams"] = {}
for name in [k for k in MODELS if k.startswith("tfidf")]:
    make, X = MODELS[name]
    m = make().fit(X, y)
    vocab = np.array(m[0].get_feature_names_out())
    c = m[1].coef_[0]
    o = np.argsort(c)
    res["top_ngrams"][name] = {
        "false_success": [[vocab[i], round(float(c[i]), 3)] for i in o[::-1][:15]],
        "true_success": [[vocab[i], round(float(c[i]), 3)] for i in o[:15]],
    }

# handcrafted feature means per class
res["hand_feature_means"] = {
    n: {"fs": float(X_hand[y == 1, j].mean()), "true": float(X_hand[y == 0, j].mean()),
        "auroc_raw": float(roc_auc_score(y, X_hand[:, j]))}
    for j, n in enumerate(HAND_NAMES)}
res["domain_counts"] = {}
for e in E:
    d = res["domain_counts"].setdefault(e["domain"], {"fs": 0, "true": 0})
    d["fs" if e["y_fs"] else "true"] += 1

# (B) sampling consistency from astra-power arm A
gen_path = f"{HERE}/astra_copy/A_generations.jsonl"
B = {"source": "astra-power runs/A/generations.jsonl (RESULT.json absent; arm A COMPLETE 220/220 "
               "per RESULT_ABC_PRELIMINARY.json)"}
if os.path.exists(gen_path):
    rates = {}
    for l in open(gen_path):
        g = json.loads(l)
        r = g["row"]
        if r["label"] not in ("fs+", "fs-"):
            continue
        key = (r["context_id"], r["task_id"], r["label"])
        rates.setdefault(key, []).append(bool(g["answer"]))
    ks = sorted(rates)
    yb = np.array([1 if k[2] == "fs+" else 0 for k in ks])
    rate = np.array([np.mean(rates[k]) for k in ks])
    gb = np.array([k[1] for k in ks])
    det = 1 - rate
    B.update({
        "n_contexts_fs": int(yb.sum()), "n_contexts_true": int((1 - yb).sum()),
        "n_samples_per_context": sorted({len(v) for v in rates.values()}),
        "n_distinct_tasks": int(len(set(gb))),
        "mean_answer_rate_fs": float(rate[yb == 1].mean()),
        "mean_answer_rate_true": float(rate[yb == 0].mean()),
        "rate_hist_fs": {str(v): int(((rate == v) & (yb == 1)).sum()) for v in (0, .25, .5, .75, 1)},
        "rate_hist_true": {str(v): int(((rate == v) & (yb == 0)).sum()) for v in (0, .25, .5, .75, 1)},
        "auroc_1_minus_rate": float(roc_auc_score(yb, det)),
        "ci95_task_boot": boot_ci(yb, det, gb),
        "flag_if_rate_lt_1": {"tpr_fs": float((rate[yb == 1] < 1).mean()),
                              "fpr_true": float((rate[yb == 0] < 1).mean())},
        "per_context": [{"context_id": k[0], "task": k[1], "label": k[2], "answer_rate": float(np.mean(rates[k]))}
                        for k in ks],
    })
    overlap = set(gb) & set(groups)
    B["tasks_also_in_text_set"] = len(overlap)
res["B_sampling_consistency"] = B

json.dump(res, open(f"{HERE}/RESULT.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if k not in ("top_ngrams",)}, indent=1)[:6000])
