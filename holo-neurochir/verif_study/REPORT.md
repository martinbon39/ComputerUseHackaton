# Vérifier explicitement les faux succès avec Holo-3.1-4B

Statut : **COMPLETE**. Étude rétrospective du 8 novembre 2026, sans nouveau rollout, sans modification des poids ou du serveur partagé.

À température 0, Holo détecte **35 des 66 faux succès (53.0 %)**, mais rejette aussi **97 des 202 vrais succès (48.0 %)**. Les verdicts reposent uniquement sur la consigne et la capture finale. Ce résultat mesure une capacité de détection et son coût en faux rejets ; il ne démontre aucune réparation ni amélioration du score OSWorld.

## Corpus et protocole

353 dossiers ont été recensés dans les quatre sources autorisées : 352 contiennent une trajectoire, et un dossier ne contient ni trajectoire ni score. Parmi les 352 trajectoires : 268 épisodes retenus, 28 réponses sur tâches infaisables, 47 terminaisons autres que `answer`, six réponses avec score partiel, et trois trajectoires sans score officiel. Les sept scores partiels au total comprennent les six réponses exclues et une terminaison non-answer. Les 28 réponses infaisables comprennent 24 scores 0 et quatre scores 1 ; elles ne sont pas vérifiées par V1.

| Passe source | Faux succès : score 0 | Vrais succès : score 1 | Réponses faisables à score partiel |
|---|---:|---:|---:|
| diag1 | 20 | 63 | 2 |
| diag2 | 18 | 43 | 1 |
| extra1 | 14 | 47 | 1 |
| extra2 | 14 | 49 | 2 |
| **Total retenu** | **66** | **202** | **6 exclues** |

Définition opérationnelle demandée : dernier outil `answer` et score officiel `result.txt` égal à 0 ou 1. Un épisode par `(tâche, passe)` ; aucun doublon dans ces clés. Les 268 épisodes couvrent **90 tâches distinctes** : 34 tâches contribuent aux faux succès et 74 aux vrais succès, avec 18 tâches présentes dans les deux catégories selon la passe. Les sources sont `results_diag`, `results_diag2`, `results_diag_extra_gh/pass1` et `pass2` ; les deux dernières sont des passes distinctes, et non des copies des premières. Les fichiers sources restent intacts.

L’instruction et la faisabilité proviennent des JSON OSWorld. Toute fonction d’évaluation contenant `infeasible` entraîne l’exclusion. Pour chacun des 268 épisodes, la capture référencée par la dernière ligne `answer` existe et constitue aussi la dernière capture disponible. Le code du runner confirme que cette image est l’observation après la dernière action graphique ; `answer` ne modifie pas l’écran. Aucun repli vers une autre image n’a été nécessaire. Instructions, chemins et SHA256 sont conservés dans `manifest.json`.

V1 est l’original `Hcompany/Holo-3.1-4B`, snapshot `8c88265a5a159bfd1492db9243733dd2e6e04a6e`, servi sur le port 8000 du pod. Une image PNG originale et un message utilisateur, sans schéma JSON d’agent, sans outils, sans historique, sans score ni réponse précédente. Réflexion activée par `enable_thinking=true`, `top_p=1`, `top_k=-1`, limite de sortie 4096 tokens. Un tirage T=0 et trois tirages T=0,8 avec graines distinctes enregistrées. Maximum quatre requêtes simultanées. Le prompt reste exactement :

> Task: <instruction>. Here is the final screen. List every requirement of the task, then for each say whether the screen shows it is satisfied (yes / no / cannot tell). Finally answer VERDICT: COMPLETE or INCOMPLETE.

**V2 non exécuté** : l’inventaire local ne trouve que Holo-3.1-0.8B, Holo-3.1-4B et des variantes de poids du 4B. Aucun VLM indépendant plus fort n’est disponible dans les caches inspectés. Aucun modèle téléchargé, aucun autre serveur sollicité ou modifié. Voir `infrastructure_probe.json`.

## Résultats : IC à 95 % de Wilson

| Vérification | Détection : INCOMPLETE sur faux succès | Faux rejet : INCOMPLETE sur vrais succès |
|---|---:|---:|
| T=0, principal | 35/66 = **53.0 %** [41.2 ; 64.6] | 97/202 = **48.0 %** [41.2 ; 54.9] |
| T=0,8 — tirage 1 | 37/66 = **56.1 %** [44.1 ; 67.4] | 100/202 = **49.5 %** [42.7 ; 56.3] |
| T=0,8 — tirage 2 | 44/66 = **66.7 %** [54.7 ; 76.8] | 102/202 = **50.5 %** [43.7 ; 57.3] |
| T=0,8 — tirage 3 | 38/66 = **57.6 %** [45.6 ; 68.8] | 89/202 = **44.1 %** [37.4 ; 51.0] |
| Majorité des trois tirages T=0,8 | 40/66 = **60.6 %** [48.5 ; 71.5] | 98/202 = **48.5 %** [41.7 ; 55.4] |

Répartition T=0 : faux succès `{'COMPLETE': 28, 'INCOMPLETE': 35, 'MISSING_VERDICT': 1, 'TRUNCATED': 2}` ; vrais succès `{'COMPLETE': 102, 'INCOMPLETE': 97, 'TRUNCATED': 2, 'MISSING_VERDICT': 1}`. Les dénominateurs principaux restent 66 et 202. Les sorties tronquées, absentes, conflictuelles ou mal formées sont distinguées et ne deviennent pas artificiellement COMPLETE. La mise en forme Markdown et les guillemets d’un champ JSON VERDICT sont normalisés de la même façon pour tous les tirages ; un verdict cité reste admissible même si le reste du JSON est mal formé, à condition que sa valeur soit unique et la génération terminée normalement. La règle de blocage simulée ne se déclenche que sur un INCOMPLETE valide. Les taux sur verdicts valides seuls figurent aussi dans `RESULT.json`.

Sur les verdicts valides seuls à T=0 : détection 35/63 = **55.6 %** [43.3 ; 67.2] ; faux rejet 97/199 = **48.7 %** [41.9 ; 55.6].

Les IC de Wilson sont calculés par épisode et ne corrigent pas les répétitions d’une même tâche. En sensibilité, un bootstrap par tâche (10 000 tirages, graine 20261108, toutes les passes d’une tâche rééchantillonnées ensemble) donne :

- Détection : IC 95 % [37.0 ; 68.8] %.
- Faux rejet : IC 95 % [36.9 ; 59.4] %.
- Détection moins faux rejet : IC 95 % [-13.2 ; 22.7] points de pourcentage.

Deux des 66 échecs faisables sont des réponses où l’agent déclarait lui-même la tâche impossible, à cause d’un refus d’accès du site Delta. Ils restent inclus conformément à la définition demandée (`answer` + score 0). Les exclure donne une détection de 33/64 = **51.6 %** [39.6 ; 63.4] ; ce contrôle secondaire ne modifie pas le corpus principal.

Décomposition descriptive T=0 par domaine ; les petites cellules ne permettent pas une comparaison fiable entre applications :

| Domaine | Faux succès détectés | Vrais succès rejetés |
|---|---:|---:|
| chrome | 6/11 | 15/37 |
| gimp | — | 12/12 |
| libreoffice_calc | 6/14 | 13/36 |
| libreoffice_impress | 10/14 | 15/34 |
| libreoffice_writer | 1/1 | 10/20 |
| multi_apps | 10/22 | 19/39 |
| os | 0/1 | 8/12 |
| thunderbird | — | 2/5 |
| vlc | 2/3 | 2/2 |
| vs_code | — | 1/5 |

## Stabilité des trois tirages à T=0,8

258/268 épisodes ont trois verdicts valides. Parmi eux, unanimité : 178/258 = **69.0 %** [63.1 ; 74.3]. Désaccord entre deux tirages valides : 162/784 paires ; les paires d’un même épisode ne sont pas indépendantes. Accord entre la majorité T=0,8 et T=0 : 227/260 = **87.3 %** [82.7 ; 90.8].

| Politique sur les trois tirages | Faux succès bloqués | Vrais succès bloqués |
|---|---:|---:|
| Au moins un INCOMPLETE | 53/66 = **80.3 %** [69.2 ; 88.1] | 126/202 = **62.4 %** [55.5 ; 68.8] |
| Trois INCOMPLETE | 26/66 = **39.4 %** [28.5 ; 51.5] | 67/202 = **33.2 %** [27.0 ; 39.9] |

Ces politiques sont des résumés descriptifs des mêmes tirages ; aucun seuil n’a été choisi ou réévalué sur de nouveaux épisodes.

## Décisions déclarées par exigence

Comptage conservateur des décisions explicitement produites dans la réponse finale T=0, avant le verdict. Un lecteur indépendant a contrôlé le texte et corrigé 27 extractions : étiquettes après une flèche, cases cochées dans un bloc d’évaluation (✓ = yes), tableaux JSON alignés avec les exigences, plusieurs exigences sur une même ligne et répétitions. Les négations dans une exigence, comme « no variations », et les justifications libres sans note catégorielle sont exclues. Les exigences énumérées par le modèle ne constituent pas une annotation indépendante des exigences réelles.

| Population | yes | no | cannot tell | Épisodes avec ≥1 no | Épisodes sans décision catégorielle extraite |
|---|---:|---:|---:|---:|---:|
| Faux succès | 124 | 47 | 28 | 20 | 13 |
| Vrais succès | 369 | 48 | 98 | 30 | 51 |
| Total | 493 | 95 | 126 | 50 | 64 |

Il s’agit de détections déclarées, pas d’un rappel ou d’une précision par exigence : le modèle peut omettre, inventer ou relâcher une exigence. Les 714 décisions retenues comprennent également celles lisibles dans les sorties sans verdict valide ; cela ne réhabilite pas leur verdict global. Les lignes exactes sont conservées dans `parsed_responses.json`, et chaque correction, son texte source et l’empreinte du sous-ensemble T=0 figurent dans `audit/requirement_review.json`. Le décompte automatique avant revue (438 yes, 86 no, 120 cannot tell) est aussi conservé pour transparence.

## Erreurs inspectées

Exemples qualitatifs choisis pour montrer des mécanismes distincts, sans prétention de fréquence. Captures finales inspectées manuellement ; la vérité de référence reste le score officiel.

- **explicit_requirement_relaxed** — `diag1__libreoffice_calc__1de60575-bb6e-4c3d-9e6a-2fa699f9f197` : score 0, verdict COMPLETE. La tâche exige une nouvelle feuille nommée Sheet2. La capture montre Pivot Table_Sheet1_1. Le vérificateur voit ce nom mais considère qu'il peut servir de Sheet2 : il relâche une exigence explicite. Le score officiel est 0 ; cette observation n'identifie pas à elle seule toutes les causes de cet échec.
- **visible_evidence_missed** — `diag1__libreoffice_calc__1273e544-688f-496b-8d89-3e0f40aa0606` : score 1, verdict INCOMPLETE. La capture affiche la feuille sélectionnée Sheet2, l'en-tête Revenue et les valeurs copiées. Le vérificateur affirme ne pas pouvoir confirmer la copie vers Sheet2. L'état visible soutient donc davantage l'exigence qu'il ne le reconnaît ; l'évaluateur officiel donne 1.
- **visible_artifact_missed** — `diag1__chrome__35253b65-1c19-4304-8aa4-6884b8218fc0` : score 1, verdict INCOMPLETE. La fenêtre Desktop montre le fichier chrome-Play_Puzzle_Game_2048.desktop sélectionné. Le vérificateur affirme que la création du raccourci n'a pas commencé. Le fichier visible contredit cette affirmation, sans permettre à l'image seule de prouver tout le contenu du raccourci ; l'évaluateur officiel donne 1.
- **hidden_persistent_state** — `diag1__libreoffice_impress__2cd43775-7085-45d8-89fa-9e35c0a915cf` : score 1, verdict INCOMPLETE. La tâche demande l'enregistrement automatique toutes les trois minutes. Le vérificateur indique cannot tell pour l'activation et l'intervalle, puis INCOMPLETE. La capture finale sans le panneau de réglage ne suffit pas à confirmer ce paramètre persistant ; le score officiel est pourtant 1.
- **unsupported_before_after_inference** — `diag1__gimp__7a4deb26-d57d-4ea9-9a73-630f66a7b568` : score 1, verdict INCOMPLETE. Pour réduire la luminosité, le vérificateur dit que l'image est identique à l'original alors qu'il n'a reçu qu'une capture finale, sans référence avant modification. Le score officiel est 1. Cette critique vise l'inférence de comparaison, pas une mesure humaine de luminosité.

## Simulation de blocage de answer

Population simulée : les **268 épisodes sélectionnés**, avec 202 succès initiaux (75.4 %). Ce n’est pas le score global d’OSWorld. Le filtre T=0 bloquerait 35 faux succès et 97 vrais succès. Parmi les blocages, proportion de faux succès : 35/132 = **26.5 %** [19.7 ; 34.6].

Un blocage ne répare rien par lui-même. La borne sans réparation est **0 gain brut** si les vrais succès sont préservés ; une perte est possible si le blocage dégrade ou empêche de valider ceux-ci. Pour un taux de réparation hypothétique r, le gain attendu sur ce corpus vaut `(r × faux succès bloqués − vrais succès perdus) / 268`.

| Hypothèse de réparation | Réparations attendues, non observées | Gain si tous les vrais succès sont préservés | Gain si tous les vrais succès bloqués sont perdus |
|---|---:|---:|---:|
| r=0 : blocage seul | 0.00 | +0.00 pp | -36.19 pp |
| r=0/2 : branchement faisable et fidèle | 0.00 | +0.00 pp | -36.19 pp |
| r=1/4 : extrapolation naïve du pilote mixte | 8.75 | +3.26 pp | -32.93 pp |

Sensibilité au dénominateur : les quatre sources contiennent **315 épisodes faisables avec score officiel**, y compris les scores partiels et les terminaisons non-answer. Leur score moyen descriptif est 66.7 %. En gardant inchangés tous les épisodes hors des 268 vérifiés, la borne à r=0 reste 0 gain brut, et le scénario favorable r=25 % devient **+2.78 pp** ; si tous les vrais succès bloqués sont perdus, il donne -28.02 pp. Ces passes diagnostiques incomplètes et répétées ne sont toujours pas le benchmark complet.

**Pourquoi le scénario à 25 % ne valide pas un gain :** `~/osw/branch_pilot/REPORT.md` rapporte 5/10 succès pour l’original et 4/10 pour le candidat, mais cela inclut quatre continuations de succès déjà acquis par bras. Parmi les échecs enregistrés : original 1/6, candidat 0/6 ; après le filtre de fidélité du replay : 1/4 et 0/4. L’unique réparation concerne GIMP `fbb548ca…`, une tâche officiellement infaisable. En appliquant notre exclusion des tâches infaisables, il ne reste qu’une tâche Writer faisable et fidèle, avec **0/2 réparations par bras**. Le Chrome dynamique est exclu pour divergence du replay. Les continuations K=2 d’une même tâche ne sont pas indépendantes.

À titre descriptif seulement, Wilson : 1/4 = **25.0 %** [4.6 ; 69.9] ; 0/2 = **0.0 %** [0.0 ; 65.8]. Ces larges intervalles et la différence de population interdisent de traiter le taux du petit pilote comme une probabilité de réparation validée pour cette étude. La borne positive simulée est conditionnelle au transfert du taux et à l’absence de dommage sur les vrais succès ; aucune continuation n’a été exécutée ici.

## Portée du résultat

Cette expérience teste une vérification explicite par le **même modèle**, depuis un écran final. Elle ne compare pas une chirurgie des poids à un vérificateur indépendant plus fort. Elle ne suffit donc pas à affirmer que « le faux succès se corrige par un vérificateur externe ». Elle chiffre le compromis de ce V1 et identifie deux limites : des preuves visuelles parfois mal lues, et des exigences portant sur un état persistant ou passé que la capture finale ne permet pas de vérifier. Un contrôle fiable de chaque exigence pourrait nécessiter l’accès aux fichiers, aux réglages ou à une preuve d’exécution ; cet accès supplémentaire n’est pas évalué ici.

Les tâches proviennent d’épisodes diagnostiques déjà enregistrés, avec répétitions par tâche et sélection des terminaisons answer à score binaire. Les taux ne sont pas des estimations représentatives du benchmark complet. Aucune donnée de test supplémentaire, aucun nouveau rollout, aucune clé secrète affichée.

## Reproduction, coût et audit

1072/1072 réponses conservées ; statuts HTTP/transport `{'ok': 1072}` ; verdicts parsés `{'COMPLETE': 514, 'INCOMPLETE': 542, 'TRUNCATED': 5, 'MISSING_VERDICT': 9, 'MALFORMED_VERDICT': 2}`. Réflexion non vide : 1072/1072. Début : 2026-11-08T07:22:40.794222+00:00 ; dernière réponse : 2026-11-08T07:49:08.229708+00:00. Tokens générés : 458,906. Quatre minuscules sondes textuelles d’infrastructure, séparées du corpus, ont précédé l’étude. Aucun nouveau serveur n’a été lancé.

- `PROTOCOL.md` : protocole fixé avant les inférences ; `manifest.json`, `inventory.json` et `corpus_probe.json` : population et provenance.
- `responses.jsonl` et `attempts.jsonl` : réponses intégrales, paramètres, graines, hashes de requêtes, raisonnement et raisons d’arrêt.
- `analyze.py` : recalcul CPU ; `parsed_responses.json` et `stability_by_episode.json` : résultats élémentaires.
- `RESULT.json` : chiffres non arrondis, IC, domaines, passes, sensibilité par tâche et simulation.
- `error_cases.json`, `images/`, `tasks/` : cas qualitatifs et pièces permettant de les contrôler.
- `branch_source_REPORT.md` et `branch_source_provenance.json` : source exacte du scénario de branchement.

Recalcul local : `python3 analyze.py && python3 write_report.py`. Audit indépendant : `python3 audit/audit_verif.py` ; voir `audit/FINAL_AUDIT.md` et `audit/AUDIT_RESULT.json` pour les vérifications réellement exécutées et leurs limites.

Livraison : `/workspace/astra/verif-study/` sur le pod et `holo-neurochir/verif_study/` sur orbit. Les SHA256 des données utilisées sont enregistrés dans `RESULT.json` et dans l’audit indépendant.
