# Préenregistrement : Holo-3.1-4B + Feci Guard en ligne (08/11, écrit à 09:27 UTC, avant tout lancement)

Écrit et commité avant le premier job de ces bras. Aucun résultat en ligne de ces bras n'existe à cette heure.

## Bras
- `orig_guard_claude` : Holo-3.1-4B (pod, port 8000), avec Feci Guard (vérificateur gelé `feci_guard/verifier.py`, prompt passif) jugé par Claude Sonnet via le relais `guard_server.py`. Au plus 2 refus par épisode ; les réponses d'infaisabilité ne sont pas vérifiées ; une erreur du juge laisse passer la réponse.
- `orig_guard_rescue`, réserve seulement : le même, mais après le 1er refus l'agent devient Holo4-27B (Modal), avec l'historique et le feedback.
- Comparateur : l'original servi par le même pod, `results_confirm_gh_orig_confirm` (réserve 45) et `results_test_gh_orig` (test 120), mêmes runners GitHub et même harness.

## Critères (la décision se lit sur le TEST 120, la réserve sert de réplication)
1. **Principal, taux d'erreur « faux fini »** : part des épisodes terminés par `answer` avec un score officiel de 0, sur toutes les tâches. Original test : 0,242 (29/120). Succès si la différence appariée par tâche (Guard − original) a une borne haute IC95 bootstrap < 0.
2. **Secondaire, score OSWorld** : moyenne du score officiel. Gain déclaré seulement si la borne basse IC95 appariée est > 0. Sinon, rapporter l'estimation ponctuelle et son IC, sans parler de gain.
3. Garde-fou : nombre de vrais succès de l'original perdus avec le Guard (tâches 1 → 0), rapporté tel quel.

## Amendement (09:28 UTC, avant tout lancement des bras complets ; seuls deux pilotes d'1 tâche existent)
Demande de Martin : on ne compte pas une baisse des faux fini sans la mettre en regard des vrais fini perdus.
4. **Bilan bénéfice / coût**, sur le test, par tâche appariée :
   - B = tâches réparées : 0 chez l'original → 1 avec le Guard ;
   - C = vrais succès perdus : 1 chez l'original → 0 avec le Guard ;
   - E = faux fini évités : faux fini chez l'original, et pas de faux fini avec le Guard ;
   - on rapporte B, C, E, le gain net B − C (soit l'écart de score) et le ratio E / max(C, 1).
5. **Règle de décision** : le Guard n'est déclaré utile que si (a) le gain net B − C ≥ 0, et (b) le taux de faux fini baisse (critère 1).
   - Une baisse des faux fini accompagnée d'un gain net négatif est rapportée comme un **échec du compromis**, pas comme un succès.
   - Le gain de score n'est déclaré que selon le critère 2.
   - Le bruit attendu pour C est calculé à part : les basculements 1 → 0 de l'original contre lui-même, entre ses deux runs servis par le pod et par Modal sur les mêmes tâches. Il est rapporté à côté.

Bootstrap apparié par tâche, 10 000 tirages, graine 0. Tâches invalides (job mort, 0 pas) exclues des deux bras, avec la liste publiée. Le bruit d'un run à l'autre de l'original (43,2 / 46,7 / 42,2 sur la réserve) est rappelé à côté de chaque écart.

## Amendement 2 (09:40 UTC, AUCUN épisode des bras Guard n'a tourné)
Le pod Runpod est tombé vers 09:30. Les 20 jobs ont échoué au contrôle des modèles, avec 0 tâche jouée.
L'agent sera servi par Modal, avec le même déploiement que les bras `orig_modal`. Le **comparateur principal devient donc l'original servi par Modal** :
- `results_test_gh_orig_modal_test` pour le test ;
- `results_confirm_gh_orig_modal_confirm` pour la réserve.

C'est le même serveur, ce qui évite le confondant pod/Modal. Les comparaisons à l'original servi par le pod restent rapportées en secondaire.

## Amendement 3 (10:44 UTC, AVANT toute comparaison avec l'original)
Les 6 tâches du job run (0) de la relance (run 42468884640) sont mortes pour raison d'infrastructure, avec 0 résultat. Elles seront rejouées une fois, avec les mêmes réglages, pour compléter les 120 tâches prévues.
- L'analyse PRINCIPALE porte sur l'ensemble final.
- Les tâches encore sans résultat après cette relance sont exclues des deux bras, selon la règle d'origine.
- L'analyse sur les 114 tâches disponibles à 10:42 est rapportée en secondaire.
