# HANDOFF — Neurochirurgie de Holo (reprise sur orbit / argos)

Tu reprends une mission en cours. Lis dans cet ordre : ce fichier, `BRIEF_neurochirurgie_holo_LOCAL.md` (la mission complète), puis `JOURNAL.md` (tout ce qui a été fait, avec les chiffres). Tiens `JOURNAL.md` à jour : l'équipe le lira pour le pitch.

## Le but
Livrer les 9 artefacts de la section 9 du brief, vérifiés. Phases : 1 infra ✅ → 2 diagnostic (en cours) → 3 direction → 4 chirurgie → 5 évaluation 4 bras → 6 dashboard + replays.

## Règles de Martin (non négociables)
- **Demande à Martin et attends** : au STOP/GO de la phase 2 (brief §5), avant tout changement d'environnement de tâches (MiniWoB → autre chose), si 2 itérations d'affilée n'apportent aucun progrès mesurable, et avant toute dépense nouvelle (nouveau pod, volume…).
- Ne jamais supprimer le pod ni le volume Runpod. Stop seulement, et seulement quand rien ne tourne.
- **Utilise argos pour paralléliser et pour être visible.** `argos spawn "<brief autonome>" --model sonnet` pour les sous-tâches indépendantes (une session visible par sous-tâche), `argos read/send <nom>` pour les suivre, et `argos notify "…"` pour prévenir Martin (STOP/GO, fin de phase, problème de budget). Les jobs longs tournent dans des tmux visibles (sur le pod), jamais en avant-plan bloquant.
- Martin veut que ça aille **vite**.

## Où sont les choses
- Code : `~/projects/ComputerUseHackaton/holo-neurochir/` (ici). `holo/` = harness + analyse, `dashboard/` = IRM (FastAPI + HTML), `scripts/` = lanceurs pod.
- **GPU Runpod** : pod RunPod (1× H200 141 Go, EUR-IS-4, **5,29 $/h**, allumé depuis 14:37 UTC le 2026-11-07). Volume réseau (100 Go) monté sur `/workspace`.
  - SSH depuis orbit avec une clé dédiée (adresse, port et nom de clé retirés de la version publique ; le pod est terminé). L'adresse change si le pod est stoppé puis redémarré : la relire dans la console Runpod ou via le MCP Runpod.
  - Budget : ~100 € de crédit. **Plafond ~90 $ cumulés** (≈ 17 h de pod). Note le coût cumulé dans `JOURNAL.md` toutes les 2 h.
  - Le MCP Runpod (plugin officiel `runpod@runpod`, OAuth) est configuré sur le PC de Martin, pas forcément sur orbit. Sans lui, Martin stoppe le pod depuis la console.
- Sur le pod : venv `/workspace/venv` (torch 2.11+cu128, transformers 5.22.2, flash-linear-attention, causal-conv1d, browsergym-miniwob 0.14.3), Chromium `/workspace/pw`, modèles dans `/workspace/hf` (Holo-3.1-0.8B et 4B), code dans `/workspace/projet` (copie à resynchroniser depuis ici avec `tar` + `scp`, extraire avec `tar xzf … --no-same-owner`), runs dans `/workspace/runs`, logs dans `/workspace/logs`.
- Le serveur MiniWoB tourne dans le tmux `miniwob` du pod (port 8765). `scripts/pod_rollouts.sh` le relance s'il manque.

## État exact
- **Phase 1 GO** (détails dans JOURNAL). Décisions clés du harness :
  - **l'observation = la zone MiniWoB `#wrap` recadrée puis agrandie 5×** (grounding 8 % → 100 %) ;
  - EOS forcé (le repo 0.8B n'a pas de `generation_config`) ;
  - thinking désactivé, T=0,8, 512 tokens max, 3 captures en contexte.
- Acceptance sur la H200 : **4B 10/12 = 83 %** ✅.
- **Diagnostic 0.8B** (24 tâches × 8 seeds + 10 tâches impossibles × 4) : lancé sur le PC de Martin (iGPU Intel), pas encore fini. Les données partielles sont dans `runs/diag/`. Pilote (48 rollouts) : succès 27 % ; faux succès **40 % des échecs** (14 positifs) ; boucle 20 % (23 pas positifs).
- **Diagnostic 4B** sur le pod (`/workspace/runs/diag4b`, 24 tâches × seeds 0-7) : lancé puis **arrêté volontairement** après ~13 rollouts, parce que les pas prenaient **25 à 50 s** avec 8 processus en parallèle. La charge CPU montait à 19 pour **12 vCPU seulement** sur ce pod, malgré la H200.
  - Hypothèse non vérifiée : le CPU est saturé par 8 × (boucle Python + Chromium) et l'autotune Triton de FLA à chaque nouvelle longueur de séquence.
  - **Prochaine action** : `scripts/bench_gen.py` (déjà sur le pod) compare FLA et le fallback PyTorch sur des contextes réels rejoués :
    `cd /workspace/projet && HF_HOME=/workspace/hf HF_HUB_OFFLINE=1 HOLO_MODEL=Hcompany/Holo-3.1-4B PYTHONPATH=. /workspace/venv/bin/python scripts/bench_gen.py /workspace/runs/diag4b [--no-fla]`
  - Puis relance avec le meilleur réglage et **~4 shards** au lieu de 8. Le lanceur reprend là où il s'est arrêté (il saute les rollouts déjà faits) :
    `bash scripts/pod_rollouts.sh Hcompany/Holo-3.1-4B 4 --tag diag4b --tasks "$(cat runs_pilot_tasks.txt)" --seeds 0-7`
  - Puis les tâches impossibles : la même commande avec `--impossible --tasks "click-button,click-link,enter-text,login-user,enter-password,click-checkboxes,click-option,enter-text-2,enter-date,use-autocomplete" --seeds 0-3`.
- Diagnostic et STOP/GO : `python -m holo.diagnostic diag4b` (avec `HOLO_RUNS=/workspace/runs`) produit `diagnostic.md` et le verdict. **Ensuite : notifie Martin et attends son GO.**

## Définitions déjà fixées (avant le run principal, voir JOURNAL)
- Boucle = ≥ 3 actions identiques (clic à moins de 15 px, ou même texte, ou même touche) avec un écran presque inchangé (< 1 % de pixels).
- Faux succès = `answer` « terminé » avec récompense 0 (ou sur tâche impossible), OU action finale de validation (Submit, Login, Search, Entrée) qui clôt l'épisode avec récompense 0.
- `wrong_final_action` est une catégorie séparée.
- Labels au niveau du pas pour la phase 3 : `fs+` / `fs-` (« terminé » à tort / à raison), `loop+` / `loop-`.

## Code déjà prêt pour les phases 3 à 6 (testé là où c'était possible)
- `holo/direction.py` : diff of means par couche, AUROC en CV **par tâche**, sonde logistique, et **contrôle de position** (`--min_t`, baselines « indice du pas » et « longueur du contexte »).
  - Sur les données 0.8B partielles (boucle), le baseline trivial atteint déjà 0,89 : il faut toujours rapporter la direction contre ce baseline.
- `holo/surgery.py` : W' = W − α·u(uᵀW) sur `down_proj`, toutes colonnes ou top-k. Test unitaire OK.
- `holo/replay.py` : reconstruction exacte des contextes (fidélité vérifiée : cosinus 1,0000). Sert au criblage hors ligne des patchs par log-prob de l'action fautive.
- `holo/splits.py` : **split figé** (validation = seeds 50-51 ; test = 8 familles jamais vues avec seeds 100-104, plus seeds 100-101 sur les tâches vues ; tâches faciles seeds 300-303). Ne pas le modifier.
- `holo/results.py` (IC 95 % par bootstrap sur les tâches, différences appariées), `holo/demo_record.py` et `dashboard/` (mode replay et mode live) : écrits, **pas encore testés de bout en bout** (il faut un vrai patch).
- `holo/rollouts.py --arm original|corrective|steer|patched --patch patch_spec.json --shard i/N`.

## Pièges rencontrés
- `pkill -f holo.rollouts` en SSH tue aussi le shell SSH (sa ligne de commande contient ce motif). Tue plutôt les sessions tmux par nom.
- Playwright 1.44 + Ubuntu 24.04 : `--with-deps` échoue (`libasound2` → `libasound2t64`). Les dépendances sont déjà installées à la main.
- Le volume réseau refuse les chown : utiliser `tar --no-same-owner`.
- Le premier pas de chaque processus prend ~55 s (compilation Triton).

## Suggestion de découpage argos (à toi de juger)
- Toi : tu pilotes le diagnostic 4B et tu prépares la décision STOP/GO.
- `argos spawn` (sonnet) : finir le test de bout en bout du dashboard (mode replay) avec un faux demo JSON, pendant que les rollouts tournent.
- `argos spawn` (sonnet) : surveiller le coût du pod et les shards (temps par pas, plantages), avec `argos notify` en cas d'anomalie.
