# Sprints vers le gain (08/11, à partir de 09:30 UTC ; dépôt à 13:00 UTC)

Système visé : **Holo-3.1-4B agit → Feci Guard vérifie chaque « fini » → l'agent (ou Holo4-27B) répare.**
Le gain = (faux fini attrapés × taux de réparation) − (vrais succès perdus). Chaque maillon est un sprint, avec une mesure
qui ne dépend pas de celui qui l'a fait.

| # | Maillon | État mesuré | Sprint | Responsable | Mesure qui juge | Échéance (UTC) |
|---|---|---|---|---|---|---|
| S0 | Preuve en ligne | rien encore | Guard v1 gelé, en ligne sur test 120 + réserve 45 (+ rescue sur la réserve), contre l'original | gh-runner2 | PREREG_ONLINE_GUARD.md : faux fini, score, bilan B − C | 12:15 |
| S1 | Détection | 68 % des faux fini, 10 % de faux rejets, 2 épisodes trompés | Guard v2 hors ligne : historique (3 derniers écrans + actions), modèle plus fort, preuve exigée au niveau du fichier | feci-guard | judge_bench, moitié réservée tirée AVANT, recalcul indépendant ; cible ≥ 80 % pour ≤ 10 % | 10:45 |
| S2 | Plafond et diagnostic | 7 refus sur 12 arrivent au plafond sans répondre | Classer les faux fini du test (visible à l'écran ou seulement dans le fichier) = plafond d'un juge sur écran ; pourquoi les réparations calent | osw-analysis | tableau par épisode, relu | 10:30 |
| S3 | Réparation forte | Holo4 : 1er score 1 (calc/37608790), contrôle en cours | Cohorte d'escalade vers Holo4 contre Holo4 sans Guard | rescue-bench | rescue_bench/PREREG.md | 11:00 |
| S4 | Intégration | — | Si S1 bat v1 sur la moitié réservée : bras en ligne Guard v2 sur le test 120, avec un amendement de préenregistrement AVANT lancement | ares + gh-runner2 | même règle que S0 | lancement ≤ 10:50, fin ≤ 12:45 |

Règles : aucune modification du Guard v1 gelé (S0 l'utilise) ; v2 dans de nouveaux fichiers ; aucun gain annoncé sans
la règle de décision ; tout chiffre passe par un recalcul indépendant.
