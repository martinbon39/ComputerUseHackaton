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

Bootstrap apparié par tâche, 10 000 tirages, graine 0. Tâches invalides (job mort, 0 pas) exclues des deux bras, avec la liste publiée. Le bruit d'un run à l'autre de l'original (43,2 / 46,7 / 42,2 sur la réserve) est rappelé à côté de chaque écart.
