# astra-short — promotion globale de </think>

Recherche terminée sans candidat admissible. Budget débité : 13/25 lots. Un lot = une intensité figée × un panel × quatre graines, plus trois contrôles texte prévus. Les arrêts anticipés restent débités. Deadline : 2026-11-08 08:00 UTC.

Le meilleur réglage complet préservant les contrôles est phase12 : réflexion moyenne 109,80 → 102,10 tokens (−7,02%), 112/112 JSON valides, aucune variation des scores sémantiques et trois textes finaux identiques. Il manque le seuil prospectif de −25%, sans amélioration des faux succès. Les doses qui raccourcissent fortement échouent sur JSON ou texte. Aucun CANDIDAT transmis, aucune évaluation en ligne revendiquée ; réserve de neuf contextes inutilisée. Ce résultat négatif porte sur cette grille, pas sur toute édition possible.

## Résultats de génération

| Lot | Réglage | Statut | Sorties | Réflexion moyenne | JSON invalide/tronqué | answer fs+ | answer fs− |
|---|---|---|---:|---:|---:|---:|---:|
| 1 | lot01_original_pilot | complet | 12/12 | 127.00 | 0 | 4/4 | 4/4 |
| 2 | lot02_endthink8_pilot | complet | 12/12 | 127.00 | 0 | 4/4 | 4/4 |
| 3 | lot03_original | complet | 112/112 | 109.80 | 0 | 13/20 | 18/20 |
| 4 | lot04_endthink12 | complet | 112/112 | 109.80 | 0 | 13/20 | 18/20 |
| 5 | lot05_endthink16 | rejeté, arrêté | 20/112 | 116.25 | 2 | 8/8 | 8/8 |
| 6 | lot06_endthink20_sentinel | rejeté, arrêté | 4/12 | 1.50 | 2 | 0/0 | 0/0 |
| 7 | lot07_scale2_pilot | complet | 12/12 | 127.00 | 0 | 4/4 | 4/4 |
| 8 | lot08_scale2 | complet | 112/112 | 109.80 | 0 | 13/20 | 18/20 |
| 9 | lot09_phase12_pilot | complet | 12/12 | 73.08 | 0 | 4/4 | 4/4 |
| 10 | lot10_phase12 | complet | 112/112 | 102.10 | 0 | 13/20 | 18/20 |
| 11 | lot11_scale3_pilot | complet, rejeté texte | 12/12 | 8.08 | 0 | 4/4 | 4/4 |
| 12 | lot12_phase16_pilot | complet | 12/12 | 14.58 | 0 | 4/4 | 4/4 |
| 13 | lot13_phase16 | rejeté, arrêté | 16/112 | 0.00 | 2 | 8/8 | 6/8 |

Les pilotes utilisent trois contextes et sont exclus de la comparaison principale sur 28 contextes. Les taux answer ne sont pas des taux de faux succès : une réponse de refus honnête peut être correcte. La pertinence sémantique a été jugée indépendamment, à partir des captures et des actions, bras masqués.

## Méthode et données

Modèle original : Hcompany/Holo-3.1-4B, snapshot 8c88265a5a159bfd1492db9243733dd2e6e04a6e. Édition pure poids : sortie lm_head explicitement déliée, seule ligne248069, 2560 valeurs sélectionnées. delta = dose × mu/(mu·mu), mu moyenne de356 états finaux originaux déjà capturés. Aucun gradient, entraînement, biais API, règle de troncature ou token Wait ajouté. Les356 états comprennent les débuts de6 contextes et206 positions supplémentaires de2 continuations saines ; ce mélange ne constitue pas un biais constant exact.

Panel construction figé avant comportement : 28 contextes, 6 domaines, fs+5/fs−5/intermédiaires18. Ces18 incluent13 pas ajoutés au milieu de tâches réussies ou ratées. Certains comportements enregistrés sont mauvais : ils restent au dénominateur. Réserve locale :9 contextes sur tâches disjointes, aucune utilisation pour choisir le vecteur ou la dose. Ni split_test.json ni confirm_tasks.json ouverts. Allowlist TRAIN héritée et vérifiée antérieurement par mit1 ; aucune nouvelle tâche hors de cette allowlist sélectionnée.

Sampling : k4, graines4000–4003, T0.8, top_p0.9, top_k20, réflexion activée, max3072, XGrammar JSON identique au harness. Contrôles texte T0 : Say hi /2+2/capitale de la France.

## Pré-enregistrement et contrôles

PROTOCOL.md, DOSE_AMENDMENT.md et audit/SCORE_RULES.md fixent les seuils et limites. Grille initiale2/4/8/12 ; pilote8 sans effet. Avant tout résultat du panel complet, les marges CPU des clés existantes justifient une grille12/16/20/24. Aucun critère de qualité assoupli. Arrêt après2 intensités complètes sans raccourcissement mesurable, budget25, deadline08:00 ; une seule interpolation bornée si cible encadrée.

Admission pour exploration en ligne : réflexion moyenne réduite>=25%, perte de pertinence sur les72 sorties intermédiaires<=5points, vrais finis<=10points, validité JSON inchangée et3 textes équivalents. Cela ne prouve pas la réparation des faux succès : il faut ensuite des continuations utiles sur tâches disjointes. Contrôle aléatoire de norme égale requis avant une interprétation mécaniste forte.

Audit indépendant du runner : audit/RUNNER_REVIEW.md, PASSED pour pilote. Rejeu CPU28/28 ;15 longueurs héritées exactes ;13 nouvelles longueurs figées. Incompatibilité initiale des messages string avec le processeur corrigée avant toute passe modèle, contrôlée par expected_nin.json strict. Audit prospectif des28 captures : healthy_rubric.json et terminal_rubric.json ; trois cas fs+ sont des limites/infaisabilités et deux requièrent une correction précise (Budget Dec10–11 ; Calc Sheet2).

Un seul processus GPU astra-short, via gpu_slot.sh ; threads torch2 ; pic réservé mesuré12.222GB dans les pilotes, occupation NVML observée sous13GB. Serveurs8000/8011/8012 intouchés. Les ressources partagées rendent les temps muraux non comparables.

## Provenance

Sources copiées en lecture seule, hashes dans source_manifest.json et budget.jsonl ; spécifications endthink_*.json compatibles make_patched_ckpt.py. Construction algébrique : construction.json, global_endthink_direction.npz, bf16_rows.json, calibration_dose_margins.json. Journal complet, papier et tous rapports préalables demandés lus par deux lecteurs indépendants. Aucun essai rejeté reproduit.

Motivation externe : Cuadron et al.2025, https://arxiv.org/abs/2502.08235 (SWE-bench ; pas une preuve directe sur Holo/OSWorld).

## Variantes après les échecs JSON

Amplification originale : W_end_nouveau = s × W_end_original, s dans{2,3}. Les spécifications endthink_scale_*.json ont delta égal à la ligne originale et alpha=s−1. Cette variante amplifie les logits positifs et rend les négatifs plus négatifs. Le facteur4 a été préparé puis retiré avant exécution.

Projection de phase : mu_T moyenne de150 états précoces de réflexion ; J contient96 états qui prédisent des tokens JSON originaux après </think>, sur une continuation saine de construction. On projette mu_T hors de la portée des lignes de J puis on normalise pour une promotion moyenne de1. Édition : delta = dose × direction_projetée − direction_moyenne_originale, doses12 et16. La soustraction protège les96 états JSON après arrondi BF16. Cela ne garantit pas la validité des nouvelles continuations. source_phase_alignment.json et phase_execution_construction.json documentent alignement et calcul. Les propositions20/28 ont été retirées sur marges CPU avant toute génération de phase ; elles ne sont pas des essais.

SCALING_PROTOCOL.md borne la suite à quatre réglages, en deux tours : gain2 et phase12, puis gain3 et phase16. Chaque pilote valide doit encore passer le panel complet28 ; chaque erreur JSON arrête le réglage, qui reste compté au budget. Deux tours sans raccourcissement sûr mesurable terminent la recherche. Aucun réglage partiel ne peut être admis.

Les lots arrêtés après échec JSON restent au budget. Leurs moyennes partielles ne doivent pas être comparées à celles du panel complet. Les sorties invalides ne sont ni réparées ni retirées. PHASE_AMENDMENT.md décrit les arrêts et le test sentinelle.

## Extension conditionnelle déclarée avant le panel phase16

PROGRESS_EXTENSION.md autorise une seule dose supplémentaire20, déjà construite, uniquement si le panel phase16 préserve tous les critères de qualité et réduit la réflexion de10% à moins de25%. Maximum deux lots supplémentaires, puis arrêt. Cela étend explicitement la grille initiale de quatre à cinq réglages possibles ; les seuils de qualité et le budget25 restent inchangés.

Condition non satisfaite : phase16 a échoué sur JSON au quatrième contexte, après16 sorties persistées, dont2 invalides. Aucun pas intermédiaire du panel complet ni contrôle texte de ce lot n’a été produit. Les résultats favorables de son pilote ne suffisent pas. La dose phase20 reste NON EXÉCUTÉE ; recherche close. Le gain3 a également été arrêté au pilote pour échec texte, sans panel complet.

## Rejets sur les contrôles texte

- lot11_scale3_pilot.rejected: Hard text-preservation gate failed in pilot; full28 panel not launched.
  - Say hi. : 512 tokens, 256 fermetures, tronqué=True.
  - What is 2 + 2? : 78 tokens, 1 fermetures, tronqué=False.
  - What is the capital of France? : 61 tokens, 1 fermetures, tronqué=False.

## Variante temporelle, analyse CPU uniquement

Les contrastes de position N=8/12/16 ont été évalués sur les états de construction existants. Aucun candidat temporel produit et aucune passe modèle supplémentaire. Le meilleur agrégat descriptif est N=8, AUROC moyen0.8542 mais minimum0.4926. Un pli réutilise les états JSON du contexte laissé de côté : cet agrégat ne constitue donc pas une validation stricte hors contexte. Cette limite et les cinq autres plis sont détaillés dans audit/POSITION_FEASIBILITY.md. Aucun ajustement supplémentaire sur cette analyse.

## Audit des actions, bras masqués

| Bras | Groupe | Actions utiles | Faux achèvements | Réponses finales honnêtes |
|---|---|---:|---:|---:|
| lot03_original | fs+ | 3/20 | 13/20 | 0/20 |
| lot03_original | fs- | 18/20 | 2/20 | 16/20 |
| lot03_original | healthy | 55/72 | 0/72 | 0/72 |
| lot04_endthink12 | fs+ | 3/20 | 13/20 | 0/20 |
| lot04_endthink12 | fs- | 18/20 | 2/20 | 16/20 |
| lot04_endthink12 | healthy | 55/72 | 0/72 | 0/72 |
| lot08_scale2 | fs+ | 3/20 | 13/20 | 0/20 |
| lot08_scale2 | fs- | 18/20 | 2/20 | 16/20 |
| lot08_scale2 | healthy | 55/72 | 0/72 | 0/72 |
| lot10_phase12 | fs+ | 3/20 | 13/20 | 0/20 |
| lot10_phase12 | fs- | 18/20 | 2/20 | 16/20 |
| lot10_phase12 | healthy | 55/72 | 0/72 | 0/72 |
| lot13_phase16 | fs+ | 0/8 | 8/8 | 0/8 |
| lot13_phase16 | fs- | 4/8 | 2/8 | 4/8 |

Une réponse finale honnête exige answer=true, useful=true et false_completion=false. Sur fs−, sa baisse doit rester<=10points, en plus du contrôle mécanique du taux answer. Jugements et déblindage conservés dans audit/.

Attention : lot13_phase16 est PARTIEL (quatre contextes,16 sorties), contrairement aux quatre bras complets de112 sorties. Ses deux sorties invalides fs− sont non utiles et leur statut de faux achèvement est indéterminé ; elles restent au dénominateur. Aucune extrapolation au panel complet. Les72 sorties saines de phase12 sont toutes identiques en tokens à l’original ; les102/112 sorties totales identiques expliquent le faible changement comportemental.

## Clôture et vérification finale

Clôture : 2026-11-08T01:45:24.140747+00:00. 13 lots débités, 560 sorties d’action et 30 contrôles texte persistés. 795 requêtes étaient prévues dans les réservations ; ce total inclut les requêtes annulées par les arrêts. Le nombre exact d’exécutions non persistées du lot05 interrompu est inconnu. Ces nombres ne comptent pas les passes token par token.

Revue indépendante finale : audit/FINAL_REVIEW.md. Les critères d’admission sont faux pour tous les bras complets ; les autres bras échouent aux contrôles bloquants. Aucun FROZEN_CANDIDATE, aucun test de la réserve, aucun contrôle aléatoire ni score OSWorld en ligne. Ares reçoit le résultat négatif et les chemins du rapport. Les spécifications conservées sont des artefacts expérimentaux rejetés, pas des candidats validés.
