from common import *
from safetensors import safe_open


def load_weight(root, name):
    index = json.loads((root / "model.safetensors.index.json").read_text())["weight_map"]
    with safe_open(root / index[name], framework="pt", device="cpu") as f:
        return f.get_tensor(name)


def key_blocks(pack, rows, name, excluded_fold=None, only_fold=None, include_text=True):
    blocks = []
    for label in ["fs+", "fs-", "healthy"]:
        selected = [r for r in rows if r["label"] == label
                    and (excluded_fold is None or r["fold"] != excluded_fold)
                    and (only_fold is None or r["fold"] == only_fold)]
        values = [pack["captures"][r["id"]][name].T.double() for r in selected]
        if label == "healthy" and include_text:
            values += [a[name].T.double() for k, a in pack["captures"].items() if k.startswith("text_")]
        assert values, (label, excluded_fold, only_fold)
        raw = torch.cat(values, 1)
        blocks.append(raw / raw.shape[1] ** 0.5)
    return blocks


def solve_right(f, t, g, alpha):
    x = torch.cat([f, t, g], 1)
    gram = x.T @ x
    epsilon = float(alpha * gram.trace() / x.shape[0])
    assert epsilon > 0
    eye = torch.eye(gram.shape[0], dtype=gram.dtype)
    target = eye[:, :f.shape[1]]
    chol = torch.linalg.cholesky(gram + epsilon * eye)
    coefficients = torch.cholesky_solve(target, chol)
    y = x @ coefficients
    residual = x @ (x.T @ y) + epsilon * y - f
    relative_residual = float(residual.norm() / f.norm())
    assert relative_residual < 1e-7, relative_residual
    return y.T, dict(epsilon=epsilon, alpha=alpha, normal_equation_relative_residual=relative_residual,
                     gram_condition=float(torch.linalg.cond(gram + epsilon * eye)), columns=x.shape[1], dimension=x.shape[0])


def errors(delta, left, right, blocks):
    values = {}
    for label, x in zip(["fs+", "fs-", "healthy"], blocks):
        pred = left @ (right @ x)
        target = delta @ x
        denominator = float(target.square().sum())
        assert denominator > 0
        values[label] = float(((pred - target) if label == "fs+" else pred).square().sum()) / denominator
    values["objective"] = sum(values.values())
    return values


@torch.inference_mode()
def main():
    m = read_frozen()
    pack = torch.load(ROOT / "captures.pt", weights_only=True, map_location="cpu")
    assert pack["complete"] and pack["manifest_sha256"] == sha(ROOT / "manifest.json")
    assert sha(ROOT / "captures.pt") == (ROOT / "captures.sha256").read_text().strip()
    alphas = m["parameters"]["ridge_trace_over_d"]
    folds = sorted({r["fold"] for r in m["rows"]})
    factors = {alpha: {} for alpha in alphas}
    stats = []
    for name in writer_names():
        base = load_weight(HOLO, name)
        qwen = load_weight(QWEN, name)
        cua = load_weight(CUA, name)
        assert base.shape == qwen.shape == cua.shape
        assert all(torch.isfinite(w).all() for w in [base, qwen, cua])
        delta = (0.5 * (cua.float() - qwen.float())).double()
        full = key_blocks(pack, m["rows"], name)
        assert full[0].shape[0] == base.shape[1]
        for alpha in alphas:
            fold_metrics = []
            for fold in folds:
                train = key_blocks(pack, m["rows"], name, excluded_fold=fold)
                heldout = key_blocks(pack, m["rows"], name, only_fold=fold, include_text=False)
                right, info = solve_right(*train, alpha)
                left = delta @ train[0]
                fold_metrics.append(dict(fold=fold, **errors(delta, left, right, heldout)))
            right, info = solve_right(*full, alpha)
            left = delta @ full[0]
            factors[alpha][name] = dict(left=left, right=right)
            stats.append(dict(writer=name, folds=fold_metrics, fit=errors(delta, left, right, full), **info))
        print(json.dumps(dict(writer=name, done=len(stats) // len(alphas))), flush=True)
        del base, qwen, cua, delta
    scores = {alpha: sum(f["objective"] for r in stats if r["alpha"] == alpha for f in r["folds"]) / (len(writer_names()) * len(folds)) for alpha in alphas}
    chosen = min(alphas, key=lambda alpha: (scores[alpha], -alpha))
    selected = dict(learned=factors[chosen], metadata=dict(alpha=chosen, scores=scores, stats=[r for r in stats if r["alpha"] == chosen],
                    formula="WH + .5*(WCUA-WQwen)*F*F.T*(F*F.T+T*T.T+G*G.T+epsilon*I)^-1",
                    normalization="Each class block divided by sqrt(number of columns); healthy block includes three text prefill keys",
                    positions=["prefill", "endthink_before_note"], selection="minimum mean held-out task-fold relative donor-fit plus true and healthy actuation; ties choose stronger ridge",
                    original_objective=1.0, construction_cv_improves_original=scores[chosen] < 1,
                    manifest_sha256=sha(ROOT / "manifest.json"), captures_sha256=sha(ROOT / "captures.pt")))
    assert not (ROOT / "candidate_factors.pt").exists()
    torch.save(selected, ROOT / "candidate_factors.pt")
    write_json(ROOT / "derive.json", dict(chosen_alpha=chosen, scores=scores, stats=stats, factors_sha256=sha(ROOT / "candidate_factors.pt")))
    print(json.dumps(dict(chosen_alpha=chosen, scores=scores)), flush=True)


if __name__ == "__main__":
    main()
