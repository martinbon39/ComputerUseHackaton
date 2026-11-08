# astra-value — exploration valeur et engagement

Mise à jour UTC : 2026-11-07T20:37:54.015447+00:00

Statut : EXPLORATOIRE. Aucun poids édité, aucun résultat de test consulté. Le pilote comprend seulement deux contextes fs+, deux fs− et deux sains (cinq tâches). Ces cinq tâches et la réserve commune de 45 tâches sont exclues de la construction. Aucun résultat de ce pilote ne peut suffire à admettre un candidat.

## Diagnostic commun fourni

Contexte établi par la mission, non refait ici : 119 tâches notées, 55,5 % de succès; échecs dominés par les faux succès (~59%) et la limite de 50 pas (~39%). La décision de répondre se forme pendant la réflexion. Ces nombres sont les faits fournis au lancement, pas une nouvelle mesure de cette session.

## Protocole et provenance

Lots réservés : 5/20. Échecs et interruptions restent comptés. Un seul processus GPU propre, cap allocateur 13 Go et contrôle mémoire processus <15 Go, STOP partagé, cooldown 20 s. Échantillonnage identique : k=4, T=0.8, top_p=0.9, top_k=20, max=3072, thinking puis schéma JSON.

Source : copie en lecture seule de l’outillage 4b. Référence originale réutilisée (24 générations) : fs+ answer 8/8, fs− answer 8/8, sain non-answer valide 8/8, invalides 0/24. Pilotage au dernier token de prefill, puis éventuellement pendant la réflexion. Les résultats ci-dessous viennent de générations libres, jamais de log-prob teacher-forced.

Construction : 68 tâches, 702 pas. Valeur = succès moins échec; engagement = answer moins continuation. Quatre classes de stade relatif (support commun dans les quatre pour valeur; uniquement le dernier quartile pour engagement), moyenne par tâche et classe dans chaque classe de position, moyenne des contrastes avec support commun. Norme = norme résiduelle moyenne par tâche du train. Aucun label fs dans la fonction de construction. Les fs servent seulement à évaluer la séparation. L’axe valeur est un proxy construit par issue d’épisode, pas une mesure validée de valeur subjective attendue.

## Lecture exploratoire en CV par tâche

AUROC fs+ de la direction positive (succès/answer), moyenne intra-fold pondérée par nombre de paires. Une valeur <0.5 signifie que le score est plus élevé chez les vrais fini. Pas de sélection des couches par ces valeurs.

| Axe | L18 | L24 | L28 |
|---|---:|---:|---:|
| value | 0.1756 | 0.2000 | 0.1512 |
| commitment | 0.4683 | 0.4683 | 0.4293 |

Baselines intra-fold pondérées comme les axes : {"t": 0.8512195121951219, "rel": 0.5, "n_in": 0.8439024390243902, "n_steps": 0.8512195121951219}. Les AUROC brutes regroupées des axes sont conservées dans analysis.json, mais secondaires car les projections de folds différents n’ont pas la même origine. Le stade relatif ne sépare pas les pas terminaux. La direction positive de succès projette davantage les vrais fini; ce résultat ne soutient donc pas directement une valeur subjective plus haute chez les faux fini. La forte prédictivité de la longueur de trajectoire/contexte limite toute interprétation mécanistique de cette lecture. La réserve commune impose un ensemble de construction déjà exposé par 4b, composé ici d’épisodes terminant par answer; cette sélection limite le transfert aux échecs par limite de pas. Deux scores fractionnels sont exclus de la définition stricte succès=1/échec=0.

## Pilotage généré

| Lot | Réglage | fs+ answer | fs− answer | Sain valide non-answer | Invalides | Nouvelles / reprises | État |
|---|---|---|---|---|---|---|---|
| 1 | r1_value_L24_a05_prefill | 8/8 | 8/8 | 8/8 | 0/24 | 24 / 0 | complet |
| 2 | r1_commitment_L24_a05_prefill | 8/8 | 8/8 | 8/8 | 0/24 | 24 / 0 | complet |
| 3 | r1_value_L18_a05_prefill | 8/8 | 8/8 | 8/8 | 0/24 | 24 / 0 | complet |
| 4 | r1_commitment_L18_a05_prefill | 8/8 | 8/8 | 8/8 | 0/24 | 24 / 0 | complet |
| 5 | r1_value_L28_a05_prefill | 8/8 | 0/0 | 0/0 | 0/8 | 8 / 0 | préempté |

Les dénominateurs affichés sont les sorties réellement terminées. Une reprise réutilise les sorties préemptées sans les régénérer; les colonnes nouvelles/reprises évitent de les compter comme de nouveaux tirages. Chaque redémarrage GPU consomme un lot supplémentaire. Une interruption ou un rejet précoce ne vaut pas estimation complète d’un bras. Les bornes de rejet utilisent les 24 sorties prévues, avec 8 sorties par strate. Un seul échec fs− ou sain, ou une sortie invalide dans une strate, rend le seuil de 5 points inaccessible sur ce pilote. Les critères définitifs utilisent causal_metrics.compare de 4b, dont le plafond d’invalides s’applique par strate et au total.

## Réflexions et contrôle aléatoire

Lecture indépendante de référence : aucune action de re-vérification stricte (0/8 dans chaque strate); une intention explicite de réévaluation parmi les 8 fs+, 0/8 fs− et 0/8 sains. Annotations et citations par sortie : BASELINE_VERIFICATION_ANNOTATIONS.json. Lot 1 valeur L24 α=0.5 : aucune action stricte (0/8 par strate); intention de réévaluation 3/8 fs+, 1/8 fs−, 0/8 sains. Codage qualitatif par un lecteur indépendant du code, non aveugle au bras, descriptif; ce changement de texte ne suffit pas à une amélioration comportementale. Preuves : LOT1_VERIFICATION_ANNOTATIONS.json et LOT1_VERIFY.md. Lot 2 engagement L24 α=0.5 : action stricte 0/8 dans chaque strate; réévaluation verbale 3/8 fs+, 1/8 fs−, 0/8 sains, sans changement de décision. Audit indépendant : LOT2_VERIFY.md et LOT2_VERIFICATION_ANNOTATIONS.json. Lot 3 valeur L18 α=0.5 : action stricte 0/8 par strate; réévaluation verbale 2/8 fs+, 1/8 fs−, 0/8 sains (LOT3_VERIFY.md). Lot 4 engagement L18 α=0.5 : action stricte 0/8 par strate; réévaluation verbale 3/8 fs+, 1/8 fs−, 0/8 sains (LOT4_VERIFY.md). Lot 5 préempté après les huit fs+ : 8/8 answer, 0 invalide, action stricte 0/8, réévaluation verbale 2/8; les seize contrôles manquent (LOT5_PARTIAL_VERIFY.md). Aucun verdict complet sur ce bras. Un texte qui dit « vérifier » ne démontre pas une vérification effective de l’environnement. Le vecteur aléatoire unitaire est préparé avec la graine 701117, pour le même site et la même norme d’ajout. À la préemption, aucun bras aléatoire généré, aucune injection pendant la réflexion et aucune dose supérieure à 0.5 n’ont été exécutés.

## Préemption et reprise exacte

Ares a terminé le processus du lot 5 par SIGTERM et retiré astra-value de PRIORITY. Le processus est confirmé arrêté. Les huit fs+ terminés sont conservés; les seize contrôles fs−/sains manquaient lors de la préemption. resume_plan.json décrit la continuation, qui vérifiera les paramètres, hashes, ordre des contextes et graines avant de reprendre uniquement les sorties manquantes. Aucun redémarrage tant que le nom reste exclu de PRIORITY. Le moniteur contrôle désormais la présence réelle du processus pour éviter un état GENERATING périmé. Vérification indépendante CPU : VERIFY_CPU_PASS, CONTROLLER_VERIFY_PASS, PREEMPTION_RESUME_VERIFY_PASS et REAL_RUN_RESUME_PASS. Le corps réel de run() a été exécuté avec une génération simulée : huit sorties conservées identiques, seize appels seulement, aucun build_inputs pour les deux contextes déjà complets, vingt-quatre enregistrements finaux. La reprise sur modèle reste NON EXÉCUTÉE. Détails et limites : PREEMPTION_RESUME_VERIFY.md.

## Compilation en poids

NON EFFECTUÉE. Une addition restreinte au dernier token de prefill dépend de la position; un biais constant ou rang 1 statique appliqué à tous les tokens ne lui est pas exactement équivalent. Une éventuelle compilation devra démontrer sa propre équivalence comportementale et conserver les critères. Aucun checkpoint ne sera produit avant le passage du seuil causal et du seuil de données. Validation en ligne OSWorld NON EFFECTUÉE : les générations rejouées mesurent le choix de l’outil, pas la réussite d’une nouvelle trajectoire. Le split de test est resté fermé.

## Sources scientifiques

[Jiang, Kauvar et Lindsey, The Value Axis](https://arxiv.org/abs/2606.17056) motive la direction vers une valeur basse. [Kumaran, Reported Confidence in LLMs Tracks Commitment More Than Correctness](https://arxiv.org/abs/2606.29490) motive la comparaison avec un axe de décision. Leur transfert à cet agent reste une hypothèse.

## Pilotage des ressources et amendement de dose

DOSE_AMENDMENT.md remplace la grille thinking initiale : doses croissantes 1, 2, 4, 8, 16, dans la limite de 20 lots et avec contrôle apparié; arrêt d’un axe au premier échec protection. Les doses au-delà du budget restent non testées. À partir du lot 5, un créneau commun est acquis par with_gpu_slot.py, avec verrous partagés ouverts en lecture seule, priorité/STOP, affinité CPU et limites de threads. Les lots 1–4 précèdent cette réception de consigne.

## Artefacts

PROTOCOL.md; split.json; source_preparation_summary.json; sources.json; rows.json; activations.npy; value.npz; commitment.npz; random.npz; analysis.json; baseline.jsonl; budget.jsonl; sorties JSONL par lot; VERIFY_CPU.md. Les tableaux par instance sont dans summary.json.
