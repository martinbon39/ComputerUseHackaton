# LOG — <project>

Append-only. Newest at the top. One entry per unit of work (a PR, a campaign phase, a loop run, a decision).
Never edit or delete past entries; if one was wrong, add a new entry that says so.

Entry format (keep it to 3–8 lines):

```
## YYYY-MM-DD · <who> · <feat|fix|decision|loop-run|verify|revert> · <one-line title>
- What: <what changed / what was decided>
- Why: <the reason, in one line>
- Verified: <RAN/PASSED/CORRECT summary, or "not verified — why">
- Result: <kept | discarded | partial> · <link: PR #, commit, evidence path>
```

---

## 2026-11-03 — Recherche + vidéo computer use
- Deep research (5 axes) → reports/Computer use agents état de l art.md
- Vidéo narrée (voix Martin, 7,6 min) → video/computer-use-agents.html, publiée via argos artifact

## 2026-11-03 — Vidéo computer use, voix Andre
- Narration refaite en ElevenLabs v4 Andre via Higgsfield (76 phrases, ~70 crédits), v01 sans « c'est Martin ». narration-andre.json, audio-andre/, computer-use-agents-andre.html. build.py prend la narration en argument.
- 2026-11-04 : page « Toutes les idées » (12 idées du brainstorm + 10 opportunités + primitives H + comment gagner), reports/idees-hackathon.html, publiée par argos artifact.
- 2026-11-04 : ajout de 10 idées « frontier » (F1-F10) en tête de reports/idees-hackathon.html, republiée.
- 2026-11-04 : recherche « Problèmes frontier de H » (4 search-workers : retours utilisateurs, problèmes déclarés par H, mesures tierces, Gladia/Devin) → reports/problemes-frontier-h.html (8 problèmes, reco P1+P2), vérifiée contre les notes par un agent séparé (6 corrections appliquées), publiée.
- 2026-11-07 : pack de contexte complet (synthèse + problèmes frontier + toutes les idées + rapport état de l'art + toutes les notes brutes + script vidéo, ~364 k caractères) → reports/pack/ (build.mjs, pack-contexte.md/.html), publié en artifact claude.ai https://claude.ai/artifact/4pBuLKrCY1GE86siFrjFbh, bouton « Copier tout en Markdown ».

## 2026-11-07 · astra-08b · verify · Weight-space loop surgery pilot
- What: Isolated experiment in pod /workspace/astra, tmux astra; 22 candidate edits, identity and global-direction diagnostic, frozen patch and random controls; REPORT.md and independent VERIFY.md written.
- Why: Test whether a loop-associated residual direction can be removed by direct weight edits, without gradients or training.
- Verified: 27/50 replay batches counted including one failed batch; training-only L10 AUROC 0.904202; independent CPU audit passed hashes, selection, numerical results and replay regression. No candidate met the prespecified efficacy threshold.
- Result: Partial — /workspace/astra/REPORT.md. Final seed 6–7 comparison NOT RUN: no such rollouts present in diag, local copy or the old 0.8B archive. Candidate remains frozen; user asked for their location. Shared pod code/data and other tmux sessions untouched.

## 2026-11-07 — Astra Round 2 (pod, weight-space screening)

- What: 18 additional patch screens, full saved development comparison (415 steps), frozen patch and three-arm seeds 6–7 evaluation (48 rollouts, 142 steps), all under /workspace/astra on the pod.
- Why: test selective suppression of repeated actions without gradients; complete the reserved evaluation.
- Verified: independent CPU artifact audit; budget 50/50; immutable freeze before reserved data; targeted 1,966,080 weights; own GPU process exited. Final log-prob/token means (loop+, healthy): original (-0.07198938, -0.11248348), patch (-0.07429665, -0.12140671), random (-0.07328731, -0.11667309).
- Result: no selective patch validated; screening ratio 4.17 did not generalize (full-dev worst-healthy ratio 0.358, heldout 0.223). Pod REPORT.md Round 2 and VERIFY_ROUND2.md contain evidence. Initial git pull --rebase blocked by existing dirty changes, left intact; no local code changes or commits.

## 2026-11-07 — Astra Round 3 (behavioral causal screening)

- What: Real sampled replay generations (four per context, T=0.8), residual/MLP paired directions and centered PCA, all-layer steering, stronger/negative coefficients, random and identity controls; isolated pod /workspace/astra/r3.
- Why: Test causal suppression of repeated actions before editing weights, replacing teacher-forced log-prob screening.
- Verified: Independent raw-output audit, 1,224 saved generations, 23/40 charged batches. Baseline REPEAT 46/48 and HEALTH 36/48; best complete learned arm REPEAT 39/48 and HEALTH 28/48 fails both criteria. Nine candidates rejected by rigorous HEALTH upper bounds; two degenerate variants interrupted without full scores. Own GPU process exited, peak reserved 6.018 GiB. Final report SHA256 3fa27d1743e2e5e4ada57ceee131deb7d4f9c799d1c28bdec421ef86bbbeffaf.
- Result: No admissible causal intervention found; patch_spec null, zero weights changed. Compilation, heldout6–7 and online50–51 NOT RUN because causal gate failed. Pod REPORT.md Round3 and r3/VERIFY.md finalized. Existing local dirty changes left intact; initial pull blocked, no code commit.

## 2026-11-07 · astra-4b · experiment-preparation · False-success behavioral tooling
- What: Isolated pod /workspace/astra/4b, tmux astra4b, REPORT_4B.md; exact diagnostic replay preparation, sparse activation mapping, structured-thinking generation, conditional tool-token probe and budget ledger. No weights edited and no test split read.
- Why: Require generated behavior before any 4B weight surgery; avoid repeating 0.8B marker-versus-cause mistake.
- Verified: Independent CPU checks on 239 rows/57 tasks (fs+15, fs-42, healthy182), grammar/sampling, sparse mapping and aggregation. Corrected inherited production top_k20 with regression checks; 192-case real trim-function proof reinstates parse-error trajectories. Old synthetic aggregation fixture remains superseded/failing after seed-contract extension; new 8-case shard tests pass, no weakened check.
- Result: Partial, data threshold unmet and latency-limited. Budget4/60 (one wrong-top_k abort, one external latency pause counted). Original first false-success context answer4/4; resumed remaining20 samples, no causal conclusion/AUROC/patch. Production and shared source files untouched; initial pull blocked by pre-existing dirty changes.

## 2026-11-07 · astra-4b-x · resume/verify · Original 4B behavioral reference recovered
- What: Inherited lot4 and finish_report waiter finished naturally; recovered all20 resumed outputs plus4 preserved outputs. Corrected isolated direction preparation and paired metrics; installed checked runner only after both processes exited.
- Why: Establish an auditable behavioral reference before causal weight surgery, retaining top_k20, fixed labels, exact replay proof and production latency guard.
- Verified: Independent raw audit of24 outputs / six contexts / five tasks: fs+ answer8/8, fs- answer8/8, healthy valid non-answer8/8, invalid/truncated0. Preparation/metrics37 checks and runner19 new mocked checks plus existing CPU suite passed; no CUDA initialized by checks. All four reserved jobs' task exposures are covered by the pilot probe.
- Result: Partial mission — reference complete, budget4/60, own GPU idle. Local15/shared16 fs+ remain below40; no official AUROC, causal steering, edited weights or online improvement. Pod REPORT_4B.md and 4b/VERIFY_{RESUME,RUNNER_RESUME,PILOT_RESUME}.md preserve evidence and remaining confirmation/compilation requirements. Initial pull blocked by pre-existing changes; unrelated work left intact.

## 2026-11-07 18:55 UTC — daedalus : slide « banc de neurochirurgie » (skill Anatomy)
- Figure interactive isométrique (skill wheresryan22/anatomy) : baie de 32 tiroirs = couches du Holo-3.1-4B ; tiroir L15 ouvert, 70 aiguilles = vrais neurones de mlp.down_proj (poids lus sur HF par range request), règle = direction, portique = orthogonalisation.
- Données réelles : direction faux succès = exploratoire Astra fold 0 (pod /workspace/astra/4b, lecture seule, aucune AUROC calculée) ; 13/9216 neurones |cos| > 0,1 vs 0 pour une direction aléatoire ; la coupe retire 0,05 % de l'énergie d'écriture. Effet comportemental : « en mesure » (après la coupe : à remplir dans needles.json behaviour.after_cut).
- Fichiers : holo-neurochir/demo_banc/ (build.mjs à lancer depuis examples/banc d'un clone d'anatomy). Pages publiées : argos artifacts banc-neurochirurgie(.html / -clair.html).

## 2026-11-07 · astra-4b-x · provisional C interrupted by production guard
- What: Trained provisional matched directions on20 fs+/50 fs- with all five pilot tasks excluded (14 matched pairs); launched lot5 negative addition atL16. STOP_GPU interrupted the first fs- sample after8 healthy outputs; process exited naturally and released GPU. Raw output and log hashes preserved in the explicit aborted marker.
- Why: Test generated behavior out of task before weights; preserve exact work across external latency pauses without dropping, duplicating or selecting samples.
- Verified: All8 saved outputs valid non-answer,0 invalid/truncated; no complete terminal output. Independent pilot CPU tests17 plus prior19 passed; staged round2 hooks passed48 CPU tests after validation fixes. CPU numerical writer equivalence does not establish behavioral equivalence. Audit resolves all budget manifests and identifies45 diagnostic tasks untouched by either evaluation or direction construction.
- Result: Partial, budget5/60; no efficacy result, no official AUROC, no patch or online gain. STOP flag belongs to ares; no automatic relaunch. Exact resume and generic interruption finalization are staged for independent checks. Unrelated shared edits preserved.

## 2026-11-07 19:30 UTC · online-eval · validation en ligne d'un 4B patché, prête (aucune VM lancée)
- What: scripts/make_patched_ckpt.py (spec surgery ou steering compilé → checkpoint servable : snapshot HF d'origine, seuls les shards édités réécrits), scripts/check_ckpt_equiv.py, osworld/serve_patched.sh (pod :8011, car le :8001 du pod est le nginx Runpod), tmux orbit osw_tunnel2 (orbit 8001 → pod 8011), osworld/make_val_tasks.py → val_fs_tasks.json (33) + val_ok_tasks.json (15), osworld/run_patched_eval.sh, osworld/compare_val.py, osworld/probe_served.py, runbook osworld/ONLINE_EVAL.md.
- Verified: patch nul (alpha=0, 6 tenseurs réécrits) : 0/724 tenseurs différents, 3 prompts × (glouton, seed 0) identiques en HF. Servi par vLLM : 8001 stable et égal à la sortie HF ; la prod 8000 sous charge donne 2 réponses distinctes sur 4 appels identiques à T=0 (non-déterminisme de batch). Contrôle positif (alpha=1, L16, top-256) : exactement 1 tenseur différent. Relecture indépendante (verifier) : statistiques et preflight corrects.
- Result: serveur de test arrêté (demande d'ares). Les listes de tâches sont à régénérer quand results_diag2 aura fini. Les tâches fs sont celles du diag, d'où viennent les directions : la validation est in-sample.
