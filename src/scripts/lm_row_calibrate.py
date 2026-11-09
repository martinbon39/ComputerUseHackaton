"""Calibrate an lm_head row edit for 'answer' (id 8944): delta_row = -c * u_hat, u_hat = mean(h)/|mean(h)| over h =
the lm_head input (after the final norm) at the tool-name position of final answer steps of in-sample diag
trajectories (fs+ and fs-; never confirm_tasks, never split_test). h does not depend on the lm_head row, so the logit
change at a position with input h is exactly -c * (h . u_hat): c = target / mean(h . u_hat).
Controls: drop on the calibration positions (mean, std); drop at every position of the 3 probe prompts (incl. the
largest increase, where h . u_hat < 0). Writes <name>.json (kind lm_head) + <name>_delta.npz per target.
Usage (pod, GPU): PYTHONPATH=. HOLO_MODEL=Hcompany/Holo-3.1-4B python scripts/lm_row_calibrate.py <results_diag>
       <confirm_tasks.json> <acts_dir> <out_dir> <image.png> [--n 4] [--targets 20,40] [--prefix eager_lm]
"""
import holo.settings as S
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from holo.model import Holo
from holo.osw_taxonomy import classify, find_tasks, load_task

sys.path.insert(0, str(Path(__file__).resolve().parent))
from answer_logit_check import ANSWER, context, stacked  # noqa: E402
from check_ckpt_equiv import conversations  # noqa: E402


def pick(results_dir, confirm, acts_dir, n):
    """n fs+ and n fs- final answer steps, deterministic sha1 order, outside confirm, already replayed."""
    pools = {"fs+": [], "fs-": []}
    for d in find_tasks(results_dir):
        key = f"{d.parent.name}/{d.name}"
        if key in confirm or not any((acts_dir / key / f).exists() for f in ("acts.npz", "acts_tail.npz")):
            continue
        meta, score, steps = load_task(d)
        if not steps or score is None:
            continue
        lab = classify(meta, score, steps, [None] * len(steps), max_steps=50)["fs_labels"][-1]
        if lab in pools:
            pools[lab].append((hashlib.sha1(key.encode()).hexdigest(), d))
    return {lab: [d for _, d in sorted(v)[:n]] for lab, v in pools.items()}


def lm_input(holo):
    store = {}
    h = holo.model.lm_head.register_forward_pre_hook(lambda m, a: store.__setitem__("x", a[0].detach().float()))
    return store, h


def main():
    ap = argparse.ArgumentParser()
    for a in ("results_dir", "confirm", "acts_dir", "out_dir", "image"):
        ap.add_argument(a)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--targets", default="20,40")
    ap.add_argument("--prefix", default="eager_lm")
    a = ap.parse_args()
    confirm = {f"{dom}/{e}" for dom, ids in json.loads(Path(a.confirm).read_text())["tasks"].items() for e in ids}
    chosen = pick(Path(a.results_dir), confirm, Path(a.acts_dir), a.n)
    assert all(len(v) == a.n for v in chosen.values()), {k: len(v) for k, v in chosen.items()}

    holo = Holo()
    store, _ = lm_input(holo)
    H, rows = [], []
    with torch.no_grad():
        for lab, dirs in chosen.items():
            for d in dirs:
                inputs, r_ids, h_ids, info = context(holo, d, false_success=(lab == "fs+"))
                full, kw = stacked(inputs, r_ids, h_ids)
                logit = holo.model(input_ids=full, attention_mask=torch.ones_like(full), logits_to_keep=1,
                                   **kw).logits[0, -1, ANSWER].float()
                H.append(store["x"][0, -1].cpu()); rows.append({"label": lab, **info, "logit_answer": float(logit)})
        H = torch.stack(H)
        m = H.mean(0); u = m / m.norm()
        proj = H @ u
        probe = []
        for conv in conversations(Image.open(a.image).convert("RGB")):
            inp = holo.processor.apply_chat_template(conv, add_generation_prompt=True, tokenize=True, return_dict=True,
                                                     return_tensors="pt", enable_thinking=False).to(holo.device)
            holo.model(**inp, logits_to_keep=0)
            probe.append(store["x"][0].cpu() @ u)
    report = {"contexts": rows, "u_norm_mean_h": float(m.norm()), "proj_calib": proj.tolist(), "variants": {}}
    out = Path(a.out_dir)
    for target in [float(t) for t in a.targets.split(",")]:
        c = target / float(proj.mean())
        drop_cal = c * proj; drop_probe = [c * p for p in probe]
        allp = torch.cat(drop_probe)
        name = f"{a.prefix}{int(target)}"
        np.savez(out / f"{name}_delta.npz", delta=(-c * u).numpy().astype(np.float32))
        spec = {"kind": "lm_head", "token_ids": [ANSWER], "delta_file": str(out / f"{name}_delta.npz"), "alpha": 1.0,
                "source": f"online-eval lm_row_calibrate: -c*u_hat, u_hat = mean lm_head input at the tool-name "
                          f"position over {len(rows)} in-sample diag answer steps (fs+ {a.n}, fs- {a.n}), c={c:.3f}",
                "target_mean_drop_answer_8944": target, "n_weights_modified": int(u.numel())}
        (out / f"{name}.json").write_text(json.dumps(spec, indent=1))
        report["variants"][name] = {
            "c": c, "delta_norm": c, "calib_drop_mean": float(drop_cal.mean()), "calib_drop_std": float(drop_cal.std()),
            "calib_drop_min": float(drop_cal.min()), "calib_drop_max": float(drop_cal.max()),
            "probe_drop_mean": [float(x.mean()) for x in drop_probe], "probe_drop_min": [float(x.min()) for x in drop_probe],
            "probe_drop_max": [float(x.max()) for x in drop_probe],
            "probe_max_increase": float(max(0.0, -float(allp.min()))), "probe_frac_increase": float((allp < 0).float().mean())}
    (out / f"{a.prefix}_calibration.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                      for k, v in report["variants"].items()}))
    print("contexts:", [(r["label"], r["task"], round(r["logit_answer"], 2)) for r in rows])


if __name__ == "__main__":
    main()
