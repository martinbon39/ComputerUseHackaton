# Astra-power — cohorte élargie de faux succès faisables

Mesures terminées le 8 novembre 2026 : **880 tirages, 55 tâches distinctes**, soit **19 faux succès faisables, 20 vrais finis complets et 16 contextes sains**, quatre graines appariées par contexte et par bras. Le verdict indépendant et ses preuves sont dans [VERIFY_FINAL.md](VERIFY_FINAL.md) et `VERIFY_FINAL.json` (not in the repository).

**Résultat principal.** C réduit la fréquence d'`answer` sur les faux succès faisables de **-17,1 [-28,9 ; -6,6] points**, IC95 par tâche. La variation sur les vrais finis vaut **-8,8 [-18,8 ; +0,0] points**. La sélectivité, définie comme Δfs − Δvrais, vaut **-8,4 [-22,6 ; +5,9] points** : son intervalle recouvre zéro. Une absence de sélectivité n'est donc pas établie ; une amélioration sélective reste elle aussi à démontrer. B donne une baisse estimée de **-10,5 [-25,0 ; +0,0] points** sur les faux succès, dont la borne supérieure vaut zéro.

**Contrôle D.** Son effet sur les faux succès est **+15,8 [+5,3 ; +27,6] points**. L'IC de D est entièrement positif : le contrôle augmente ici la fréquence d'answer. Le contraste direct C−D vaut **-32,9 [-47,4 ; -19,7] points**. L'IC du contraste C−D est entièrement négatif.

## Différences appariées et sélectivité

Toutes les valeurs sont des points de pourcentage, candidat moins référence, avec IC95 bootstrap par tâche. Une sélectivité négative indique davantage de suppression sur les faux succès que sur les vrais finis. Les intervalles sont individuels, sans correction de multiplicité.

| Contraste | Δ faux succès faisables | Δ vrais finis | Sélectivité Δfs − Δvrais |
|---|---:|---:|---:|
| B-A | -10,5 [-25,0 ; +0,0] | -11,3 [-22,5 ; -2,5] | +0,7 [-16,1 ; +16,3] |
| C-A | -17,1 [-28,9 ; -6,6] | -8,8 [-18,8 ; +0,0] | -8,4 [-22,6 ; +5,9] |
| D-A | +15,8 [+5,3 ; +27,6] | +0,0 [-3,8 ; +3,8] | +15,8 [+5,3 ; +27,7] |
| C-D | -32,9 [-47,4 ; -19,7] | -8,8 [-18,8 ; +0,0] | -24,1 [-41,1 ; -7,2] |

!Effets et intervalles par tâche (`effects.png`, not in the repository)

L'effet ne repose plus sur un seul contexte : C fait baisser la fréquence d'`answer` dans neuf des 19 tâches fs, la laisse identique dans neuf, et l'augmente dans une. Les comparaisons par tâche sont conservées intégralement dans RESULT.json.

| Bras vs A | Tâches fs : baisse / égalité / hausse | Tâches vrais finis : baisse / égalité / hausse |
|---|---:|---:|
| B | 4 / 14 / 1 | 5 / 15 / 0 |
| C | 9 / 9 / 1 | 5 / 14 / 1 |
| D | 0 / 12 / 7 | 1 / 18 / 1 |

## Taux d'answer par strate

Chaque cellule donne le compte, le taux et l'IC95 de Wilson. **Ces Wilson sont descriptifs** : ils traitent les quatre tirages d'un même contexte comme indépendants. L'inférence principale repose sur les intervalles par tâche du tableau précédent. Les IC bootstrap des taux eux-mêmes sont aussi disponibles dans RESULT.json ; un intervalle empirique dégénéré sur des observations toutes identiques ne constitue pas une certitude sur la population.

| Bras | Faux succès faisables | Vrais finis | Contextes sains |
|---|---:|---:|---:|
| A | 55/76 · 72,4% [61,4 ; 81,2] | 75/80 · 93,8% [86,2 ; 97,3] | 5/64 · 7,8% [3,4 ; 17,0] |
| B | 47/76 · 61,8% [50,6 ; 71,9] | 66/80 · 82,5% [72,7 ; 89,3] | 0/64 · 0,0% [0,0 ; 5,7] |
| C | 42/76 · 55,3% [44,1 ; 65,9] | 68/80 · 85,0% [75,6 ; 91,2] | 2/64 · 3,1% [0,9 ; 10,7] |
| D | 67/76 · 88,2% [79,0 ; 93,6] | 75/80 · 93,8% [86,2 ; 97,3] | 8/64 · 12,5% [6,5 ; 22,8] |

L'original rééchantillonné répond `answer` dans 55/76 tirages fs, alors que les actions historiques avaient toutes été sélectionnées comme des `answer` en échec. La référence correcte est cette nouvelle baseline appariée. Les contextes sains sont des pas intermédiaires non répétitifs dans des épisodes finalement réussis ; leur taux d'`answer` mesure ici une terminaison prématurée potentielle.

## Sensibilité sans données de construction/préservation de C

La cohorte entière contient une tâche de construction C et deux tâches de préservation C. Leur retrait laisse **18 fs, 19 vrais finis, 15 sains**, tous disjoints, avec les mêmes exclusions appliquées aux quatre bras. Ce sous-ensemble est disjoint des tâches déclarées pour construire/préserver C ; il ne constitue pas le split_test d'OSWorld.

| Contraste | Δ faux succès faisables | Δ vrais finis | Sélectivité Δfs − Δvrais |
|---|---:|---:|---:|
| B-A | -11,1 [-26,4 ; +0,0] | -11,8 [-23,7 ; -2,6] | +0,7 [-17,0 ; +17,1] |
| C-A | -16,7 [-29,2 ; -5,6] | -7,9 [-18,4 ; +0,0] | -8,8 [-23,8 ; +6,2] |
| D-A | +16,7 [+5,6 ; +29,2] | +0,0 [-3,9 ; +3,9] | +16,7 [+5,6 ; +29,2] |
| C-D | -33,3 [-48,6 ; -19,4] | -7,9 [-18,4 ; +1,3] | -25,4 [-43,2 ; -7,7] |

Les trois tâches retirées sont chrome/47543840-672a-467d-80df-8f7c3b9788c9 (construction, fs), chrome/0d8b7de3-e8de-4d86-b9fd-dd2dce58a217 (préservation, vrai fini), chrome/7b6c7e24-c58a-49fc-a5bb-d57b80e5b4c3 (préservation, sain). La baisse C sur les fs persiste dans cette sensibilité : **-16,7 [-29,2 ; -5,6] points**.

## Cohorte et protocole

Le pool gelé RegMean annoncé à19 fs contenait cinq tâches dont evaluator.func était `infeasible`. Après leur retrait, les deux nouvelles passes DIAG apportent cinq tâches fs distinctes supplémentaires : **19 est le maximum admissible dans les sources demandées**, une tâche sous la cible de20. Les 136 épisodes des deux passes sur les68 tâches admissibles ont été contrôlés. Les autres données DIAG anciennes identifiées séparément n'ont pas été ajoutées. Aucun épisode de réserve45 ni split_test n'a été consulté ou mesuré.

Une première version de cohorte contenait un crédit partiel0,612459 classé positif par la taxonomie canonique score>0. Il a été remplacé, **avant tout tirage**, par une tâche distincte notée1. Le contrôle strict échoue sur l'ancienne version et passe sur la version finale. Labels : fs = answer terminal, score0 et évaluateur faisable ; vrai fini = answer terminal, score1 ; sain = pas loop− dans épisode faisable à score1. Ces labels sont mécaniques et ne constituent pas une annotation sémantique exhaustive des affirmations textuelles de succès.

Manifeste cohorte v2 SHA256 : `2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0`. FROZEN.json : `9bf07af1f630ffbee0f628347270dff9c3abe068aa9fb76c9c8c747e47585839`. Les preuves de sélection, évaluateurs, scores, captures et exclusions se trouvent dans cohort/. La sélection a été figée avant les générations ; aucune tâche n'a été remplacée après observation d'un bras.

A = Original Holo-3.1-4B, révision8c88265a5a159bfd1492db9243733dd2e6e04a6e ; B = Fusion CUA β=0,5 ; C = AlphaEdit broad_residual_p100 ; D = Contrôle broad_residual_random100. Les poids servis ont été audités indépendamment :67/67 contrôles, C/D24 formules BF16 exactes et700 autres tenseurs inchangés chacun. D randomise les facteurs gauches et conserve les facteurs droits de C. Sa norme réalisée totale vaut1,00007756 fois celle de C ; l'écart maximal par tenseur est0,02963%, sous le contrat historique0,1%. Il s'agit d'un contrôle dans cette famille de facteurs, pas d'un bruit isotrope sur tout le modèle.

H200 partagé, vLLM0.23.0, BF16, contexte32768, max_num_seqs32, KV8GiB, gpu_memory_utilization0,20. Ordre B,A,C,D, serveur dédié8024 ; le serveur de production8000 est resté inchangé. Une première tentative de démarrage D avec caches de compilation dans /dev/shm a échoué avant toute génération : ce montage est noexec et empêchait le chargement d'un .so Triton. L'unique reprise utilise les caches par défaut, identiques à A/B/C. Un contrôle bloque désormais ce cas avant chargement ; sa reproduction sort avec le code64 attendu. Les logs rejetés sont conservés (CACHE_LOCATION_D.json, server_D_FAILED_ATTEMPT1.log). Les fichiers de modèles et les paramètres numériques sont identiques au protocole.

Reconstruction canonique holo.osw_replay, messages gelés et hachés, budget trois captures :52 contextes en ont3, deux en ont2, un en a1 faute d'historique plus long. Schéma exact holo_agent, réflexion activée, reasoning_effort medium, T0,8, top_p0,9, top_k20, max_tokens3072 ; graines17000,17001,17002,17003 identiques entre bras. Huit requêtes clientes simultanées, zéro retry silencieux. Les quatre tirages pilotes de B sont conservés dans ses220, avec continuation après un contrôle technique indépendant sans sélection comportementale.

Estimateur : moyenne des quatre indicateurs answer par contexte, différences sur les mêmes tâches/graines. Bootstrap stratifié par tâche,100000 réplications, PCG64 seed20261108, percentiles2,5 et97,5. Ces IC décrivent la variation entre tâches avec les quatre graines fixées. Les mêmes indices de tâches sont appliqués à tous les bras ; les deux strates terminales sont rééchantillonnées indépendamment pour la sélectivité. Les erreurs restent au dénominateur comme invalides/nonanswers. Troncature = finish_reason length ; les catégories invalides et erreurs transport peuvent se chevaucher.

| Bras | Tirages | Invalides | Erreurs transport | Troncatures |
|---|---:|---:|---:|---:|
| A | 220 | 0 | 0 | 0 |
| B | 220 | 0 | 0 | 0 |
| C | 220 | 0 | 0 | 0 |
| D | 220 | 0 | 0 | 0 |

## Portée et audit

Cette expérience mesure la prochaine décision sur des contextes enregistrés. Les actions générées n'ont pas été exécutées : elle ne mesure donc ni une amélioration du score OSWorld ni l'utilité effective des continuations. L'échantillon est conditionné par des échecs et succès DIAG historiques, pas représentatif de l'ensemble OSWorld. Le rejeu hérite des limites de traçabilité documentées dans holo.osw_replay (messages manquants après erreurs historiques env.step/parsing). Les IC restent larges pour les effets modestes et la sélectivité ; ces données ne permettent pas de conclure à une impossibilité générale de correction par édition de poids.

Audit indépendant : VERIFY_PROBE.md pour la mécanique, VERIFY_CHECKPOINTS.md/json pour les identités et normes, VERIFY_FINAL.md/json pour les55 sources/payloads, les880 réponses brutes et le recalcul des statistiques. Les erreurs de préflight et de première version du checker de checkpoints sont archivées ; aucune correction n'a changé les poids ni relâché une exigence de formule bit exacte.

Résultat machine : RESULT.json. Bruts : runs/{A,B,C,D}/generations.jsonl et receipts de début/fin. Calcul : analyze.py ; recalcul indépendant : verifier_recompute.py --phase final ; figure : plot_effects.py, effects.png et effects.svg. PROTOCOL.md contient le plan enregistré avant les mesures. Copie canonique sur le pod : /workspace/astra/astra-power/ ; miroir orbit : experiments/weight_edits/power_cohort/.
