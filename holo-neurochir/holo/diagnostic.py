"""Builds diagnostic.md (failure taxonomy) from runs/<tag>/ and prints the STOP/GO verdict."""
import holo.settings as S
import json, shutil, sys
from collections import Counter, defaultdict
from holo.taxonomy import scan

tag = sys.argv[1] if len(sys.argv) > 1 else "diag"
rows = scan(tag)
normal = [r for r in rows if not r[1]["impossible"]]
imp = [r for r in rows if r[1]["impossible"]]

per_task = defaultdict(list)
for d, s, steps, c in normal:
    per_task[s["task"]].append(c["success"])
cats = Counter(c["category"] for _, _, _, c in normal)
fails = [r for r in normal if not r[3]["success"]]
n_fail = len(fails)
loop_fail = sum(r[3]["loop"] for r in fails)
fs_fail = sum(r[3]["false_success"] for r in fails)
imp_cats = Counter(c["category"] for _, _, _, c in imp)
imp_fs = sum(c["false_success"] for *_, c in imp)
loop_pos = sum(sum(l == "loop+" for l in c["labels"]) for *_, c in rows)
loop_neg = sum(sum(l == "loop-" for l in c["labels"]) for *_, c in rows)
fs_pos = sum(l == "fs+" for *_, c in rows for l in c["fs_labels"])
done_correct = sum(l == "fs-" for *_, c in rows for l in c["fs_labels"])
fs_ans = sum(c["fs_answer"] for *_, c in rows); fs_sub = sum(c["fs_submit"] for *_, c in rows)

ex_dir = S.ROOT / "diagnostic_examples"; ex_dir.mkdir(exist_ok=True)
L = [f"# Diagnostic — Holo3.1-0.8B sur MiniWoB++ (runs/{tag})", "",
     f"- Rollouts normaux : **{len(normal)}** sur {len(per_task)} tâches ; rollouts impossibles : **{len(imp)}**",
     f"- Taux de succès global (tâches normales) : **{100 * sum(r[3]['success'] for r in normal) / max(1, len(normal)):.1f} %**",
     f"- Échecs (normaux) : {n_fail}", "",
     "## Catégorie principale par rollout (tâches normales)", "",
     "Priorité : faux succès > boucle > mauvais grounding > abandon/budget > autre.", "",
     "| Catégorie | Rollouts | % des échecs |", "|---|---|---|"]
for k in ["false_success", "loop", "grounding", "abandon_or_budget", "wrong_final_action", "other", "error"]:
    L.append(f"| {k} | {cats.get(k, 0)} | {100 * cats.get(k, 0) / max(1, n_fail):.1f} % |")
L += ["", "## Défauts retirables (multi-label, parmi les échecs normaux)", "",
      f"- Rollouts en échec contenant une **boucle** (≥ 3 actions identiques sans changement d'écran) : **{loop_fail}/{n_fail} = {100 * loop_fail / max(1, n_fail):.1f} %**",
      f"- Rollouts en échec avec **faux succès** : **{fs_fail}/{n_fail} = {100 * fs_fail / max(1, n_fail):.1f} %** "
      f"(toutes tâches confondues : {fs_ans} via `answer` « terminé » + {fs_sub} via une soumission qui clôt l'épisode avec récompense 0)",
      f"- Tâches impossibles : {dict(imp_cats)} → faux succès sur impossible : {imp_fs}/{len(imp)}",
      "", "## Exemples positifs disponibles pour l'analyse (phase 3)", "",
      f"- Boucle : **{loop_pos} pas positifs** (2e répétition et au-delà), {loop_neg} pas négatifs (actions qui font progresser l'écran)",
      f"- Faux succès : **{fs_pos} « terminé » à tort**, {done_correct} « terminé » corrects",
      "", "## Taux de succès par tâche", "", "| Tâche | n | succès |", "|---|---|---|"]
for t, v in sorted(per_task.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
    L.append(f"| {t} | {len(v)} | {100 * sum(v) / len(v):.0f} % |")
L += ["", "## Exemples", ""]
shown = Counter()
for d, s, steps, c in rows:
    cat = c["category"]
    if cat in ("success", "error", "correct_abandon") or shown[cat] >= 2:
        continue
    shown[cat] += 1
    L.append(f"### {cat} — {d.name}")
    L.append(f"Objectif : `{s['goal']}` — récompense {s['reward']}, {s['n_steps']} pas")
    L.append("")
    for st, lab in zip(steps, c["labels"]):
        L.append(f"- t={st['t']} `{st['action']}` diff_écran={st['screen_diff']} {'**[boucle]**' if lab == 'loop+' else ''}")
    first = d / "step00.png"; last = d / f"step{max(0, len(steps) - 1):02d}.png"
    for p in (first, last):
        if p.exists():
            dst = ex_dir / f"{d.name}_{p.name}"; shutil.copy(p, dst)
            L.append(f"![{p.name}]({dst.relative_to(S.ROOT).as_posix()})")
    L.append("")

share_loop = loop_fail / max(1, n_fail); share_fs = fs_fail / max(1, n_fail)
verdict = []
if share_loop >= 0.25 and loop_pos >= 40:
    verdict.append(f"GO boucle ({100 * share_loop:.0f} % des échecs, {loop_pos} positifs)")
if share_fs >= 0.25 and fs_pos >= 40:
    verdict.append(f"GO faux succès ({100 * share_fs:.0f} % des échecs, {fs_pos} positifs)")
L += ["## Verdict STOP / GO", "", "- " + ("; ".join(verdict) if verdict else
      f"NO-GO pour l'instant (boucle {100 * share_loop:.0f} % / {loop_pos} pos ; faux succès {100 * share_fs:.0f} % / {fs_pos} pos)")]
(S.ROOT / "diagnostic.md").write_text("\n".join(L), encoding="utf-8")
print(json.dumps({"normal": len(normal), "imp": len(imp), "success": round(sum(r[3]['success'] for r in normal) / max(1, len(normal)), 3),
                  "cats": dict(cats), "loop_fail_share": round(share_loop, 3), "fs_fail_share": round(share_fs, 3),
                  "fs_answer": fs_ans, "fs_submit": fs_sub, "loop_pos": loop_pos, "loop_neg": loop_neg, "fs_pos": fs_pos, "done_correct": done_correct,
                  "imp_cats": dict(imp_cats), "per_task": {t: f"{sum(v)}/{len(v)}" for t, v in per_task.items()},
                  "verdict": verdict}, indent=0))
