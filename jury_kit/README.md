# Jury kit: check it yourself / Vérifiez vous-même

H Company × 42AI hackathon. Model studied: `Hcompany/Holo-3.1-4B` (computer-use agent). The statistics can be recomputed from this folder in seconds (level 1). The model-side checks (levels 2 and 3) need downloads and a GPU and were not run end to end by the author (see below). The online OSWorld episodes themselves are not in this folder, only their per-task scores.

## EN

**Question.** Holo sometimes calls `answer` ("task done") when the task is not done (*false success*). Can we reduce that by editing the weights directly, without training?

**What we did.** We looked for the stopping decision inside the weights and edited it two independent ways: a weight-space merge with a public CUA model (`θ = θ_Holo + 0.5·(θ_CUA − θ_Qwen)`, language tower only), and a closed-form AlphaEdit-style edit of 24 writer matrices. We then measured the effect offline on frozen contexts and online on OSWorld (165 held-out tasks, same serving backend for both arms).

**Primary verdict: no detectable score gain.** Merge vs original, 165 paired tasks: **+1.9 points, CI95 [−4.3 ; +8.0]** (18 wins, 14 losses). The rule "claim a gain only if the lower bound is > 0", with Modal-served original as reference, was fixed before reading the Modal-vs-Modal results (after the first pod-served runs were seen). Against the pod-served original on the test split the merge is at −1.3 pt (CI [−8.9 ; +6.4]); `verify_results.py` prints it. We claim no gain.

**Three key results** (details and caveats in [RESULTS.md](RESULTS.md)):
1. **A causal lever on stopping exists in the weights.** AlphaEdit on 24 writers lowers `answer` on false-success contexts (15/16 → 8/16) while a random edit of the same norm does nothing (16/16). Caveats: small n (16 samples), and the whole drop comes from one context. One direction (rank 1) is enough to move the margin, but it moves the true-finish margin too.
2. **It is not selective.** The same edits lower `answer` on true finishes at least as much (15/16 → 3/16). A plausible explanation (correlational, metric-dependent): internal states separate false successes from true finishes no better than the step number does (AUROC 0.63–0.70 vs 0.85).
3. **A lever that moves a decision offline did not move the score online.** AlphaEdit (45-task reserve only, minimum detectable effect about 17 pt): Δ −2.2 to +2.2 pt depending on the reference, all CIs contain 0; merge: see the primary verdict.

Paper (signed links, valid 30 days): [arXiv version](https://argos.martinbonan.com/artifacts/holo-paper.pdf?t=mxelge4c.LSxzU-Tqzjg0MDDGnHwrg8eo4oGhcaw3) · [NeurIPS version](https://argos.martinbonan.com/artifacts/holo-paper-neurips.pdf?t=mxelge6y.lVLDjfho3bzWPbIK8QFE1kCyYYhTum3V) · [Demo: the original's false "done" vs the merged agent, one illustrative episode, not evidence of a score gain](https://argos.martinbonan.com/artifacts/holo-demo-faux-fini.html?t=mxec08h4.ypUQurEtCFn45XOw47vn5eHhOEl5Gyfd)

Embeddings and output head: `embed_tokens` is merged, and since Holo has `tie_word_embeddings=true` the effective output head, tied to it at load time, changes too.

### 3 ways to verify

| Level | What | Needs | Time |
|---|---|---|---|
| 1 | `python verify_results.py` recomputes every paired comparison from the per-task scores in `results/scores.csv` (660 rows, 8 arm×split runs) with a fixed-seed bootstrap. Must print +1.94 (165), +0.18 (test), +6.64 (reserve). | Python stdlib (the split called "reserve" here is `confirm` in the CSV) | seconds |
| 2 | `python rebuild_merge.py --build OUT` rebuilds the merged checkpoint from three public models at pinned commits and compares the sha256 of the safetensors with ours (`expected_sha256.json`). `--check 2 --merged DIR` compares 2 tensors only. | ~40 GB disk, CPU. Equal tensors with a different file sha256 (library versions) would not be a failure: use `--check` | minutes |
| 3 | `probe_decision.py` / `probe_decision.ipynb` (Colab T4, fp16) replays 4 recorded contexts (`contexts/`) and prints P(answer) vs the other tools, original vs merged. | GPU 16 GB, `pip install pillow` for `--dry-run`; use `--sample 4` for an informative number | minutes |

Pinned inputs for level 2: `Hcompany/Holo-3.1-4B@8c88265a5a159bfd1492db9243733dd2e6e04a6e`, `Qwen/Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, `OnAnOrange/CUA-Lite-Qwen3.5-4B-ScaleCUA-gpt5_5-epoch3-public@df6eba93efb2df3ed9adc810e0f7f4e038959c74`.

What was and was not tested before release: level 1 run in full; level 2: the full merged checkpoint was rebuilt on an independent machine with our merge script (`merge_v2.py`, same formula) and **reproduced bit-for-bit** the sha256 of both safetensors shards (`b7acdd12…`, `6f88c913…`); `rebuild_merge.py` itself was checked on 2 tensors only, its full `--build` was not run; level 3 message construction checked identical to our harness and tokenisation checked, the model forward pass was not run on a GPU by the author. Read the caveats in RESULTS.md.

Harness caveat: our OSWorld harness (RealtimeGUI @ a763361) is more permissive than the official Holo adapter on infeasible tasks, so absolute scores are not comparable with H's published ones. Only the paired comparisons are meaningful.

## FR

**Question.** Holo appelle parfois `answer` (« tâche finie ») alors que la tâche n'est pas finie (*faux succès*). Peut-on le réduire en éditant les poids, sans entraînement ?

**Ce qu'on a fait.** On a cherché la décision d'arrêt dans les poids et on l'a éditée de deux façons indépendantes : une fusion avec un modèle CUA public (`θ = θ_Holo + 0,5·(θ_CUA − θ_Qwen)`, tour langage seulement) et une édition en forme close de type AlphaEdit sur 24 matrices d'écriture. Mesure hors ligne sur contextes figés, puis en ligne sur OSWorld (165 tâches, même serveur pour les deux bras).

**Verdict primaire : pas de gain de score détectable.** Fusion contre original, 165 tâches appariées : **+1,9 point, IC95 [−4,3 ; +8,0]** (18 gains, 14 pertes). La règle « on ne revendique un gain que si la borne basse est > 0 » a été fixée avant de lire les résultats. Nous ne revendiquons aucun gain.

**Trois résultats clés** (détails et réserves dans [RESULTS.md](RESULTS.md)) :
1. **Il existe un levier causal sur l'arrêt dans les poids.** AlphaEdit sur 24 écrivains baisse `answer` sur les faux succès (15/16 → 8/16), un contrôle aléatoire de même norme ne fait rien (16/16). Une seule direction (rang 1) suffit à déplacer la marge.
2. **Il n'est pas sélectif.** Les mêmes éditions baissent `answer` sur les vrais « fini » au moins autant (15/16 → 3/16). Explication plausible (corrélationnelle, dépend de la métrique) : les états internes ne séparent pas mieux faux succès et vrais « fini » que le numéro du pas (AUROC 0,63–0,70 contre 0,85).
3. **Un levier qui déplace une décision hors ligne n'a pas déplacé le score en ligne.** AlphaEdit : Δ de −2,2 à +2,2 points selon la référence, tous les IC contiennent 0 ; fusion : voir le verdict primaire.

Papier (liens signés, valables 30 jours) : [version arXiv](https://argos.martinbonan.com/artifacts/holo-paper.pdf?t=mxelge4c.LSxzU-Tqzjg0MDDGnHwrg8eo4oGhcaw3) · [version NeurIPS](https://argos.martinbonan.com/artifacts/holo-paper-neurips.pdf?t=mxelge6y.lVLDjfho3bzWPbIK8QFE1kCyYYhTum3V) · [Démo : le faux « fini » de l'original contre l'agent fusionné](https://argos.martinbonan.com/artifacts/holo-demo-faux-fini.html?t=mxec08h4.ypUQurEtCFn45XOw47vn5eHhOEl5Gyfd)

Embeddings et tête de sortie : `embed_tokens` est fusionné, et comme Holo a `tie_word_embeddings=true`, la tête de sortie effective, liée à cet embedding au chargement, change aussi.

### 3 façons de vérifier

1. **Niveau 1, `python verify_results.py`** (bibliothèque standard seulement) : recalcule les comparaisons appariées depuis `results/scores.csv`, bootstrap à graine fixe. Doit afficher +1,94 (165), +0,18 (test), +6,64 (réserve).
2. **Niveau 2, `python rebuild_merge.py --build SORTIE`** : reconstruit le checkpoint fusionné depuis trois modèles publics à révisions épinglées et compare les sha256 des safetensors aux nôtres (`expected_sha256.json`). `--check 2 --merged DOSSIER` ne compare que 2 tenseurs.
3. **Niveau 3, `probe_decision.py` ou `probe_decision.ipynb`** (Colab T4, fp16) : rejoue 4 contextes enregistrés (`contexts/`) et affiche P(answer) contre les autres outils, original contre fusionné.

Testé avant publication : niveau 1 en entier ; niveau 2 : checkpoint fusionné complet reconstruit sur une machine indépendante avec notre script (`merge_v2.py`, même formule), sha256 des deux shards **reproduits bit à bit** (`b7acdd12…`, `6f88c913…`) ; `rebuild_merge.py` lui-même vérifié sur 2 tenseurs seulement, son `--build` complet non lancé ; niveau 3 : construction des messages identique à notre harnais et tokenisation vérifiée, passe avant du modèle non exécutée sur GPU par l'auteur.

Réserve de harnais : notre harnais OSWorld (RealtimeGUI @ a763361) est plus permissif que l'adaptateur officiel de Holo sur les tâches infaisables ; les scores absolus ne sont pas comparables à ceux publiés par H. Seules les comparaisons appariées ont un sens.

## Live probe

Endpoint: `https://martinbon39--holo-jury-probe-web.us-east.modal.run` (routes: `GET /contexts`, `GET /probe/<id>`). The server is open only during the judging window; outside it, it answers 503 "door closed".
Sonde en ligne : `https://martinbon39--holo-jury-probe-web.us-east.modal.run` (routes : `GET /contexts`, `GET /probe/<id>`). Le serveur n'est ouvert que pendant la fenêtre de jugement ; en dehors, il répond 503 « porte fermée ».

## Merged checkpoint on Hugging Face

The merged weights are to be published under `HF_REPO_ID` (placeholder, final name to come). Until then, rebuild them with level 2.

## Layout

```
verify_results.py   level 1          results/scores.csv   per-task scores
rebuild_merge.py    level 2          expected_sha256.json  our checkpoint fingerprints
probe_decision.py / .ipynb  level 3  contexts/             4 frozen contexts (3 screenshots each, full resolution)
RESULTS.md  honest results table     tools/  scripts used to export the data (maintainers)
```
License: Apache-2.0 (code and data of this folder). Models keep their own licenses.
