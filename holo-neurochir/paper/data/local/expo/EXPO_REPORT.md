# ExPO et vecteur Qwen sur Holo-3.1-4B — rapport du worker expo (2026-11-07, 22:10 → 23:30 UTC)

**Verdict.** Aucune des 7 éditions testées ne réduit le faux succès dans ce test hors ligne. Ce sont des éditions de poids sans gradient ni données : ExPO à 4 valeurs de λ, ExPO par module (attention seule, MLP seuls) et ajout du vecteur de post-entraînement de Qwen. Sur les deux étapes fs+, l'original répond answer 16/16. Les éditions donnent 16/16, sauf MLP seuls à λ 1,5 : 15/16, avec un seul scroll. Le premier dégât de génération apparaît à λ 1,5 sur tout le langage : 1 sortie sur 32 boucle dans le JSON jusqu'à 3072 tokens. λ 1,25 est sain (0/32 invalide, texte juste) ; ares l'a mis en test EN LIGNE sur la réserve, parce que seul OSWorld mesure la qualité des actions. Ce test ne la mesure pas.

## 1. Méthode
- ExPO (Zheng et al. 2024, arXiv 2404.16792) : W(λ) = W_base + λ·(W_holo − W_base), calcul en float64, écriture en bf16 (le type de Holo). `scripts/make_expo_ckpt.py`.
- Vecteur Qwen (dans l'esprit de « Reasoning Vectors », arXiv 2509.01363) : W = W_holo + β·(W_Qwen3.5-4B − W_Qwen3.5-4B-Base), option `--rv` du même script.
- Ne sont édités que les tenseurs présents dans toutes les sources avec une forme identique, et seulement dans la portée choisie :
  - `lang` : `model.language_model.layers.*` et la norme finale, soit 425 tenseurs ;
  - `attn` : `self_attn` et `linear_attn` des couches, sans les normes de couche, soit 264 tenseurs ;
  - `mlp` : 96 tenseurs.
- Tout le reste est l'octet près celui de Holo : la vision, `embed_tokens`, `lm_head` (lié) et les fichiers config, tokenizer et processor.
- Contrôle d'identité intégré : λ=1 (ExPO), et β=0 (vecteur), donnent 0 tenseur différent de Holo, pour chaque checkpoint construit.
- Vérification indépendante par un sous-agent vérificateur, sur λ 1,25 et 1,5 : PASSED.
  - 724 clés, formes et types identiques à Holo.
  - Les 425 tenseurs dans la portée sont égaux à bf16(b + λ(h − b)) (`torch.equal`).
  - Les 299 tenseurs hors portée sont identiques à Holo.
  - λ=1 redonne Holo, et les fichiers non-poids sont identiques (`cmp`).
- Les checkpoints `rv05`, `attn15` et `mlp15` n'ont eu que le contrôle intégré. Ils ont été supprimés après leur sanity.
- Disque : le quota de /workspace était à 89 Go sur 100. La base est donc copiée dans `/root/expo/base` (Qwen3.5-4B) et `/root/expo/base_pt` (Qwen3.5-4B-Base), et les checkpoints sont écrits dans `/dev/shm/expo_ckpt/`. Ils sont perdus au redémarrage du pod et se reconstruisent en ~2 min.

## 2. Filiation et compatibilité
- Variantes officielles sur HF (auteur Qwen, « Qwen3.5-4B ») : **Qwen/Qwen3.5-4B** (post-entraîné, réflexion hybride) et **Qwen/Qwen3.5-4B-Base**, rien d'autre. Il n'y a ni Instruct, ni Thinking, ni Coder, ni Math séparé. La famille 3.5 est nativement VL.
- La model card de Holo cite `Qwen/Qwen3.5-4B` (révision téléchargée 851bf6e8).
- Holo vs Qwen3.5-4B :
  - 723 tenseurs communs, tous de même forme ;
  - présents dans la base seule : 15 tenseurs MTP (`mtp.*`) ;
  - présent chez Holo seul : `lm_head.weight`, égal à `embed_tokens` (tête liée dans les deux) ;
  - 48 tenseurs sont en F32 dans la base et en BF16 chez Holo.
- Écart relatif par groupe (‖Δ‖/‖W_base‖, médiane / max) :

  | Groupe | Médiane | Max | Tenseurs identiques |
  |---|---|---|---|
  | Langage | 4,0 % | 17 % | 14/320 |
  | Normes | 0,2 % | 0,8 % | — |
  | Vision | 0,07 % | 21 % | 19/297 |

  Le max de la vision vient de certains MLP de blocs.
- `embed_tokens` a été réentraîné par H : norme × 2,1, cosinus de ligne de médiane 0,93, mais inférieur à 0,16 sur 10 % des lignes. Il est donc **exclu** de l'extrapolation, puisque la tête est liée.
- Filiation, mesurée sur les 424 tenseurs des couches de langage (normes relatives à ‖Holo‖) :

  | Écart | Norme relative |
  |---|---|
  | ‖Holo − Q4B‖ | **4,7 %** |
  | ‖Holo − Q4B-Base‖ | **7,8 %** |
  | ‖Q4B − Q4B-Base‖ | **6,4 %** |

  Cosinus(Holo − Q4B, Q4B − Q4B-Base) = **−0,02**. On a donc 7,8² ≈ 4,7² + 6,4² : Holo = Qwen3.5-4B + un delta quasi orthogonal au post-entraînement de Qwen. Holo descend de Qwen3.5-4B, qui est déjà le modèle « raisonnement ». Un vecteur « raisonnement − base de Holo » est donc nul. Le seul vecteur disponible est le post-entraînement Qwen entier (Q4B − Q4B-Base), où le RL de raisonnement est inséparable du SFT.

## 3. Sanity hors ligne
**Protocole.**
- vLLM 0.23 sur le port pod 8013, mêmes flags qu'online-eval (`serve_patched.sh` : `--gpu-memory-utilization 0.15`, `--kv-cache-memory-bytes 6G`). Un serveur à la fois, coupé après chaque bras.
- L'original est resservi sur 8013 comme référence, car la prod 8000 varie sous charge.
- Appel exact du harness (`osworld/probe_expo.py`, issu de `probe_answer_rate.py`) : schéma `holo_agent` en structured outputs, réflexion activée, T=0,8, top_p 0,9, 3072 tokens max, 8 tirages par étape.
- Étapes finales answer de `results_diag`, hors des 8 contextes de calibration lm40 et hors des 45 tâches confirm :
  - fs+ (score 0) : chrome/47543840, impress/550ce7e7 ;
  - fs− (score 1) : multi_apps/c867c42d, impress/ed43c15f.
- Les fs− sont ceux qu'online-eval a utilisés pour lm40.

| Bras | fs+ chrome/47543840 | fs+ impress/550ce7e7 | fs− multi_apps/c867c42d | fs− impress/ed43c15f | JSON invalide | tronqué | tokens moyens | autres actions |
|---|---|---|---|---|---|---|---|---|
| original (resservi sur 8013) | 8/8 | 8/8 | 7/8 | 7/8 | 0/32 | 0 | 363 | click 2 |
| ExPO λ 1,1 (langage) | 8/8 | 8/8 | 8/8 | 7/8 | 0/32 | 0 | 385 | click 1 |
| ExPO λ 1,2 (langage) | 8/8 | 8/8 | 8/8 | 5/8 | 0/32 | 0 | 394 | click 3 |
| ExPO λ 1,25 (langage) | 8/8 | 8/8 | 7/8 | 6/8 | 0/32 | 0 | 379 | click 2, hotkey 1 |
| ExPO λ 1,5 (langage) | 8/8 | 8/8 | 8/8 | 5/8 | 1/32 | 1 | 491 | sortie illisible 1, click 2 |
| ExPO λ 1,5 attention seule | 8/8 | 8/8 | 7/8 | 8/8 | 0/32 | 0 | 377 | hotkey 1 |
| ExPO λ 1,5 MLP seuls | 7/8 | 8/8 | 7/8 | 3/8 | 0/32 | 0 | 372 | click 6, scroll 1 |
| Holo + 0,5·(Q4B − Q4B-Base) | 8/8 | 8/8 | 8/8 | 8/8 | 0/32 | 0 | 387 | — |

**Lecture des résultats.**
- Écart relatif à Holo des poids édités (médiane / max) :
  - ExPO langage : 0,33 / 1,7 % (λ 1,1), 0,66 / 3,4 % (1,2), 0,82 / 4,2 % (1,25), 1,6 / 8,5 % (1,5) ;
  - attention λ 1,5 : 1,5 / 8,5 % ;
  - MLP λ 1,5 : 2,5 / 3,2 % ;
  - vecteur Qwen β 0,5 : 2,3 / 4,8 %.
- Texte à T=0 sur 3 prompts (ciel bleu, renommer un fichier, 7 stylos à 3 €), sans réflexion, 200 tokens : lisible et juste dans tous les bras, 21 € partout. Le λ 1,5 « langage » écrit « \boxed{21} ».
- La sortie tronquée de λ 1,5 (fs− impress/ed43c15f) a duré 3072 tokens, avec 38 706 caractères de JSON qui boucle. C'est le symptôme attendu d'un λ trop grand.
- La longueur des sorties augmente avec λ : 363 → 385 → 394 tokens, et 408 à λ 1,5 sans la sortie tronquée.
- MLP seuls λ 1,5 : la seule baisse de fs+ (1 tirage) s'accompagne de la plus forte baisse de fs− (10/16 contre 14/16 pour l'original). Elle va dans le mauvais sens : le modèle perd des vrais « fini », pas des faux.
- Avec 8 tirages par étape, les écarts fs− de 5 à 8 sur 8 restent dans le bruit. Ces résultats sont EXPLORATOIRES (2 fs+), loin des 40 fs+ du critère commun.

## 4. Ce qui reste
- λ 1,25 en ligne sur la réserve de 45 tâches : piloté par ares et online-eval. Le checkpoint `/dev/shm/expo_ckpt/expo_l1.25` est conservé, ainsi qu'`expo_l1.5`.
- Non fait, sur ordre d'ares : λ 0,8 / 0,9 / 1,05 / 1,3, et β 0,3 / 0,6.

## Fichiers
- Code : `scripts/make_expo_ckpt.py`, `osworld/probe_expo.py`.
- Bruts : orbit `~/osw/expo/probe_{orig13,expo11,expo12,expo125,expo150,attn15,mlp15,rv05}.json`.
- Manifestes : `expo_manifest.json` dans chaque checkpoint.
- Pod : `/workspace/expo/` (`compare.json` = écarts tenseur par tenseur Holo vs base).
