# astra-think — rapport exploratoire

Mise à jour : 2026-11-07T20:42:24.758784+00:00

Modèle : Hcompany/Holo-3.1-4B. Aucun gradient, entraînement ou poids modifié. Split de test jamais lu.

Budget : **5/20 lots réservés**, échecs et interruptions compris.

État opérationnel : **suspendu, aucun processus GPU propre actif**. La priorité de flotte du 7 novembre à 20:26 UTC ne contient plus astra-think. Le lot 5 est interrompu, sans verdict causal; les deux projections préenregistrées restent non exécutées. Ce rapport ne décrit pas une étude à quatre bras achevée.

## Protocole et provenance

Direction recherchée dans les résidus des tokens réellement générés pendant la réflexion, toutes les 32 couches. Préfill enregistré séparément; état j après consommation du token généré j; EOS final non consommé. Pilotage prévu sur toutes les positions de décodage uniquement, 1 à 4 couches.

Quatre tâches de construction en deux paires domaine/stade; aucune paire fs+/fs− de même tâche disponible. Six contextes de screening appartenant à cinq autres tâches. Les quatre tâches de construction appartiennent aux 70 tâches de développement initiales; les cinq tâches de screening sont exactement le pilote initial. Réserve diagnostique commune de 45 tâches non exposée par cette expérience (shared_reserve_proof.json).

Empreinte manifeste : `8114f5cf9e92d2c950b5fc24c1e4e2aa9e0c97c472c91b637c3717d6ac60c7ab`. Protocole effectivement implémenté : `f1efd4c8d2521bbe63e50765dd5744ad9719d9cf7b7abf7143909110875e9aac`.

**Incident de concurrence :** le lot 1 a enregistré l’empreinte d’un PROTOCOL.md remplacé par une autre session. Code de génération et manifeste intacts; journal conservé sans réécriture. Voir COLLISION.md et la copie du protocole concurrent. Propriétaire actif : thread01a1b765-94f9-72f0-8252-510a3d94f647. Les scripts think_run.py/fit_think.py/train.sh du doublon ne sont pas utilisés.

## Génération de référence et collecte

Sampling identique à la référence : T=0,8, top_p=0,9, top_k=20, thinking actif, plafond3072 tokens, schéma xgrammar seulement après </think>, seeds4000–4003. Reconstruction des messages/images enregistrés et égalité du nombre de tokens de prefill.

Baseline de screening réutilisée : fs+ answer8/8; fs− answer8/8; sains non-answer valides8/8; invalides/tronqués0/24.

| Collection | Sorties conservées | État |
|---|---:|---|
| collect_pair1 | 8/8 | complète |
| collect_pair2 | 8/8 | complète |

Le lot2 a échoué au chargement par manque de VRAM globale, zéro sortie. Il reste compté; ce n’est pas un rejet causal. Le lanceur attend maintenant au moins16Go libres et STOP absent avant reprise. Cooldown minimum20s, un seul processus propre sous verrou, allocateur13Go, arrêt si processus observé≥15Go.

Comptages de construction (ne sont pas une évaluation causale) : `{"fs+": {"n": 8, "tasks": 2, "answer": 6, "valid_nonanswer": 2, "invalid": 0}, "fs-": {"n": 8, "tasks": 2, "answer": 8, "valid_nonanswer": 0, "invalid": 0}}`.
Mémoire processus maximale enregistrée dans les sorties : 12.641632 Go; les sondages ne garantissent pas l’absence de pic entre observations.

Premiers marqueurs de conclusion dans les 16 réflexions de construction : index de token 4 : 14/16, index de token 5 : 2/16. Indices à partir de zéro, dans les tokens générés; il ne s’agit pas de numéros de mots. Ces marqueurs localisent une affirmation explicite, pas le moment causal où la décision interne se forme.

## Localisation exploratoire

AUROC CV par paire : `[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]`. Classement des couches : `[31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]`.
Baselines : `{"t": {"fold_auc": [0.5, 0.5], "mean_auc": 0.5}, "n_in": {"fold_auc": [1.0, 1.0], "mean_auc": 1.0}}`.
Tâches avec marqueur de vérification avant la première conclusion : 0/4. Direction vérification non construite faute de couverture suffisante.
Deux paires seulement; l’AUROC de longueur de contexte vaut déjà1.0. Aucun argument causal ne repose sur cette séparation. Fenêtres lexicales et domaines de construction sont des facteurs de confusion.

Diagnostic lexical ajouté après la construction, sans modifier la direction ni sélectionner un bras : proportion de premiers marqueurs `successfully` par tâche; AUROC CV=1.0. Ce simple indicateur sépare aussi les deux paires. Voir lexical_baseline.json. Il renforce la limite de confusion lexicale, sans fournir de résultat causal.

## Tests causaux

| Bras | Sorties | fs+ answer | fs− answer | Sains non-answer valides | Invalides | État |
|---|---:|---:|---:|---:|---:|---|
| Référence | 24/24 | 8/8 | 8/8 | 8/8 | 0/24 | référence réutilisée |
| screen_add_half | 24/24 | 8/8 | 8/8 | 8/8 | 0/24 | complet — rejeté |
| screen_add | 6/24 | non mesuré | non mesuré | 6/6 | 0/6 | interrompu — aucun verdict causal |
| screen_project_half | 0/24 | non mesuré | non mesuré | non mesuré | non mesuré | non exécuté — aucun verdict |
| screen_project | 0/24 | non mesuré | non mesuré | non mesuré | non mesuré | non exécuté — aucun verdict |

Comptages screen_add_half : `{"fs+": {"n": 8, "tasks": 2, "answer": 8, "valid_nonanswer": 0, "invalid": 0}, "fs-": {"n": 8, "tasks": 2, "answer": 8, "valid_nonanswer": 0, "invalid": 0}, "healthy": {"n": 8, "tasks": 2, "answer": 0, "valid_nonanswer": 8, "invalid": 0}}`.


Comptages screen_add : `{"healthy": {"n": 6, "tasks": 2, "answer": 0, "valid_nonanswer": 6, "invalid": 0}}`.


Critère fixé : baisse fs+≥25points et≥50%relatif; baisse fs−≤5points; baisse sains non-answer valides≤5points; hausse invalides/tronqués≤5points sur l’ensemble des24sorties. Les sous-strates invalides sont aussi reportées à titre diagnostique. Une sortie manquante ne compte jamais comme réussite. Tous les résultats restent exploratoires avant40fs+ admissibles; le screening sur deux tâches fs+ ne suffit jamais à prouver une amélioration OSWorld.

Grille historique AMENDMENT_PRE_CAUSAL.md, écrite avant tout screening : deux forces par famille (ajout−0.5/−1 sur une couche, projection0.5/1 sur quatre couches). Sa règle d’arrêt après deux familles sans progrès est remplacée prospectivement par AMENDMENT_RESIDUAL_DOSE.md, à la demande d’ares. Les seuils d’admission, les tâches et le plafond total de 20 lots restent inchangés.

Incident lot 5 : préemption par ares, confirmée dans OWNER.md et ORDERS_FROM_ARES.md. Le SIGTERM du lanceur a laissé son enfant GPU continuer avec PPID=1; le coordinateur a terminé ce seul enfant après vérification de son identité. Six sorties saines valides sont conservées; la septième réflexion n’a pas de sortie finale enregistrée et ne compte ni comme valide ni comme tronquée. Les contrôles fs− et fs+ n’ont pas été atteints. Voir lot5_orphan_termination.json et screen_add.aborted.json. Pic observé avant disparition du moniteur : 11,446256 Go; aucun pic maximal certain ne peut être donné pour l’intervalle sans moniteur. Correctif : signal de mort du parent imposé par Linux et propagation SIGTERM/SIGHUP dans launch.py; ancienne source conservée dans launch_pre_orphan.py. VERIFY_PARENT_DEATH.md : 9 tests CPU avec vrais processus, reproduction de l’orphelin avant correction, absence d’orphelin après correction.

## Vérification et limites

VERIFY_CAPTURE.md : 11/11 contrôles CPU; VERIFY_ANALYSIS.md : 14/14; VERIFY_FROZEN.md : 11/11. VERIFY_LOT1.md :8/8 captures réelles auditées indépendamment sur CPU (hashes, IDs exacts, dimensions, EOS, texte, parsing, mémoire observée).

VERIFY_DIRECTION.md : reconstruction indépendante des directions, échelles, fenêtres et séparation des tâches. VERIFY_SCREEN_ADD_HALF.md : 24/24 sorties auditées, aucun effet confirmé; pic processus observé 13,339984 Go. VERIFY_COMMON_CRITERION.md : 22/22 contrôles CPU sur les cinq seuils, le traitement des invalides et le refus des résultats partiels.

Contrôle aléatoire : non exécuté à ce stade. Confirmation diagnostique disjointe, compilation en poids, test OSWorld réservé, gain en taux de réussite : NON EXÉCUTÉS. Un hook limité au décodage ne se compile pas automatiquement en une édition statique équivalente des poids.

Portée mécanistique : le premier token provient du prefill intact. Le hook agit ensuite jusqu’à la fin du JSON d’action, y compris après </think>. Un effet sélectif ne localiserait donc pas son origine à la réflexion seule; il pourrait aussi agir directement sur la sélection de l’outil. La projection n’est pas centrée et n’est pas équivalente à l’ajout négatif.

Les quatre seeds par contexte ne sont pas quatre nouvelles tâches. Un non-answer peut simplement retarder la clôture : deux sorties fs+ de construction cliquent pour fermer une fenêtre après avoir déjà affirmé la réussite. Aucun gain OSWorld ne peut être inféré de ce seul changement. Un échec de tous les bras signifierait uniquement qu’aucun levier sélectif n’a été trouvé avec cette direction, ces couches, ces doses et ces contextes.

Aucun candidat admis et aucun checkpoint modifié. Les fichiers *.jsonl, captures/*.npz, budget.jsonl et les marqueurs de fin/échec constituent les preuves primaires.

## Reprise préparée sur CPU, non exécutée

Norme résiduelle moyenne à L31 : 50.02117301. Les ajouts historiques représentaient 0.245038 et 0.490076 fois cette norme. Calcul sur les seules 16 captures originales et fenêtres figées, avec poids égal des quatre tâches; aucune activation du pilote ne contribue.

L’addendum est écrit après le résultat négatif à demi-force et la préemption à pleine force : il ne s’agit pas du protocole initial. Il prévoit les doses calibrées 0,5 / 1 / 2 / 4 / 8 / 16 à L31, chacune avec un vecteur aléatoire unitaire fixé (PCG64, seed 271828), de même amplitude d × norme résiduelle. Tous les fichiers sont préparés et hashés; aucune de ces douze conditions n’a tourné.

La reprise exacte de l’ajout interrompu préserve six sorties et en demande dix-huit, aux mêmes seeds. Puis restent les deux projections historiques et les douze conditions de dose : 5 + 1 + 2 + 12 = 20 lots au maximum. Toute nouvelle interruption ou confirmation consomme ce même plafond et réduit la couverture restante. L’escalade s’arrête au premier échec de protection, après le contrôle aléatoire correspondant; un screening sélectif suspend l’escalade pour confirmation. Aucun lancement autonome n’est laissé en attente.

Fichiers de reprise : resume_plan.json, screen_add_resume_job.json, dose_plan.json et AMENDMENT_RESIDUAL_DOSE.md. Une reprise exige la réadmission dans PRIORITY, STOP absent, le sémaphore partagé, le cooldown, les plafonds mémoire et CPU, puis une agrégation vérifiée des fragments avant tout verdict. Les projections restent en unités fractionnelles : leur alpha ne se compare pas directement à une dose d × norme résiduelle.

Audit indépendant final — VERIFY_DOSE_PLAN.md : norme R31 recalculée exactement depuis les 16 captures; vecteur aléatoire reproduit bit à bit; 19 configurations autorisées validées, dont les 12 doses; 82 mutations rejetées sans réservation; fragment de reprise et plafond de 20 lots vérifiés. Le registre interdit aussi le contournement par renommage. PAUSED_VERIFIED.json constate aucun PID GPU propre et aucun tmux astra-think restant. Les décisions d’arrêt entre lots restent manuelles; aucun contrôleur autonome n’a été lancé.
