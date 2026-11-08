# Astra-perceive — étude de la complétude perçue

État au 2026-11-07 à 22:04 UTC : tous les lots et audits indépendants sont terminés. Aucun candidat admissible et aucun poids modifié. Tous les résultats sont exploratoires.

## Question et protocole

L’hypothèse est qu’un faux succès ressemble, pour le modèle, à une tâche effectivement terminée. Le contraste est construit à l’intérieur d’épisodes réussis : résidu du dernier token de préremplissage au vrai `answer` final, moins celui du pas valide non-answer immédiatement précédent. Les plis de validation regroupent chaque tâche et toutes ses passes. Aucun gradient ni entraînement.

La réserve canonique de 45 tâches est exclue de toute construction et de ce pilote ; le split de test et ses résultats n’ont pas été ouverts. Parmi les 75 tâches restantes du diagnostic, un hash déterministe réserve 21 tâches au screening et en affecte 54 à la construction. Le contraste exploite 58 paires réussies de 40 tâches de construction. Une archive propre contient les activations nécessaires à sa reproduction, sans dépendre des données partagées qui continuent d’évoluer.

La génération réutilise la copie du moteur astra-4b-x : réflexion activée, température 0,8, top-p 0,9, top-k 20, 3 072 tokens maximum, quatre graines appariées 4000–4003. Le pilote figé comprend deux contextes fs+, deux fs− et deux sains, choisis par longueur d’entrée puis identifiant de tâche. Il couvre quatre tâches distinctes, dont seulement deux fs+. Les quatre tirages d’un contexte ne constituent pas quatre tâches indépendantes. Les contextes, labels, historiques, empreintes de tokens et longueurs de préremplissage ont été vérifiés.

Le seuil commun exige une baisse de `answer` fs+ d’au moins 25 points et 50 % relatif ; la perte fs− et la perte de sorties saines valides non-answer doivent rester à 5 points au plus, et la hausse d’invalides/troncatures à 5 points au plus. Une autre action doit aussi être pertinente. Moins de 40 fs+ admissibles reste exploratoire. La règle stricte fs− est conservée malgré la formulation plus permissive en fin de mandat.

## Contraste de complétude : prédictif, non identifié comme perception

| Mesure | Résultat |
|---|---:|
| Couche choisie sur la construction | indice zéro 15, soit le 16e bloc |
| AUROC groupée, prédictions hors pli | 0,9096 |
| AUROC moyenne des plis | 0,888 |
| Concordance au sein des 58 paires | 0,9828 |
| AUROC de l’indice du pas / longueur d’entrée | 0,5522 / 0,5547 |
| Norme du contraste L15 / norme résiduelle moyenne | 1,3988 / 8,1988 |
| AUROC sur 25 paires de 18 tâches de screening | 0,952 |

Les deux variables de position ont néanmoins une concordance intra-paire de 1 par construction : le dernier pas suit immédiatement son prédécesseur. Ce protocole réduit la confusion due aux différences de longueur entre tâches ; il ne distingue pas complètement perception, avancement et engagement vers `answer`. Le choix de la couche sur ces mêmes plis est exploratoire.

Sur 14 paires fs+/fs− appariées en position et longueur d’entrée à 10 %, une analyse descriptive exclut la tâche examinée et toutes ses passes de la direction. Le saut de projection depuis le pas précédent est positif dans 14/14 cas pour les deux classes : +1,1094 z pour fs+, +1,5353 z pour fs−. L’écart terminal fs+ moins fs− est −0,1446 z ; fs+ est supérieur dans 6/14 paires. Les faux et vrais « fini » portent donc tous deux ce signal de complétude. Ce résultat ne prouve ni une erreur visuelle ni un mécanisme causal.

L’audit de coordonnées confirme que la capture et l’intervention ciblent exactement la sortie du bloc 15, après les deux additions résiduelles, avant la normalisation du bloc suivant. L’intervention applique h′[−1] = h[−1] − αδ₁₅ au dernier token du préremplissage uniquement ; elle ne pilote pas les tokens de réflexion suivants. α multiplie le contraste brut, sans normalisation à la norme résiduelle moyenne : à α=4, le déplacement vaut environ 5,595, contre une norme résiduelle moyenne de 8,199. La littérature fournie a guidé le choix d’un contrôle de même norme et d’un balayage ; ce n’est pas une reproduction des articles. Aucune attribution patching ni décomposition multidirectionnelle n’a été effectuée. La note verify/LITERATURE_SCOPE.md précise ces limites et indique que les articles cités n’ont pas été consultés directement.

## Attention aux preuves visuelles

Deux paires de construction, même tâche et passes distinctes, ont été fixées avant les cartes : Calc C20 annoncé vert alors que le texte ne l’est pas, et dates de location annoncées correctes alors que novembre est affiché au lieu de décembre. La paire Calc est décalée en position (16 contre 24) ; la paire Chrome est au pas 13 dans les deux passes. Les dates peuvent aussi refléter une erreur de suivi temporel de l’instruction.

Holo étant hybride, seules les couches d’attention complète 15, 19, 23, 27 et 31 donnent les cartes softmax demandées dans l’intervalle 12–31. Cent cartes ont été capturées : quatre contextes, cinq couches, dernière requête de préremplissage puis quatre premières requêtes générées ; 80 têtes sont comparées. Le backend d’origine reste inchangé. Les régions de preuve, le choix de la dernière image et la règle de sélection étaient figés avant capture.

**Aucune tête sur 80 ne passe la règle.** Elle exige un enrichissement de la région de preuve plus élevé lors de la réussite dans les deux tâches, et supérieur à l’attention uniforme sur l’image lors des deux réussites. La meilleure tête rejetée, L15/H11, donne 0,5703→0,7157 sur Chrome et 0,8396→1,2236 sur Calc : Chrome échoue au seuil 1. Les requêtes générées restent descriptives et ne servent pas à remplacer ce sélecteur après observation.

Il n’y a donc ni amplification de tête, ni combinaison, ni contrôle de têtes aléatoires applicable. Ce petit échantillon négatif n’établit pas l’absence de têtes lisant les preuves. La figure `attention_analysis/L15_H11_prefill.png` montre une tête rejetée, pas un candidat.

## Génération causale

Les fractions portent sur les mêmes huit tirages par strate (deux contextes × quatre graines), et 24 au total. Les taux portent sur les sorties générées, pas sur la vraisemblance teacher-forced d’une action enregistrée.

| Intervention L15, dernier token de préremplissage | fs+ answer | fs− answer | Sains valides non-answer | Invalides/tronquées | Seuils échoués |
|---|---:|---:|---:|---:|---|
| Référence | 6/8 | 8/8 | 6/8 | 0/24 | — |
| Soustraction α=0,5 | 5/8 | 8/8 | 7/8 | 0/24 | fs+ absolu et relatif |
| Soustraction α=1 | 4/8 | 8/8 | 5/8 | 0/24 | fs+ relatif et préservation des sains |
| Soustraction α=2 | 5/8 | 8/8 | 7/8 | 0/24 | fs+ absolu et relatif |
| Soustraction α=4 | 5/8 | 8/8 | 5/8 | 0/24 | fs+ absolu et relatif, préservation des sains |
| Direction aléatoire, norme appariée à α=4 | 7/8 | 8/8 | 6/8 | 0/24 | fs+ absolu et relatif |

À α=0,5, l’unique bascule fs+ est une écriture vide. À α=1, Chrome passe de 4/4 à 3/4 answer et Writer de 2/4 à 1/4 : la baisse totale de 25 points reste inférieure à 50 % relatif (33,3 %). Le nouveau clic Chrome ferme l’onglet pour examiner l’interface, mais la justification confond toujours thème Classic et interface Chrome 2023 ; la nouvelle écriture Writer utilise une adresse fictive. Un pas sain Writer devient aussi answer, faisant perdre 12,5 points sur la strate saine. À α=2 et α=4, Chrome reste à 4/4 answer et Writer passe à 1/4 ; l’alternative nouvelle est encore une adresse fictive. α=4 fait également perdre une sortie saine valide. Aucun de ces lots ne passe le seuil comportemental complet.

La référence, α=0,5, α=1/2 et les cartes d’attention sont audités indépendamment. La réutilisation du modèle entre α=1 et α=2 est confirmée par les sources, les tests protégés, le registre et une capture du processus ; le cooldown mesuré est de 20,0659 secondes. Le retrait des hooks est vérifié par le code et les tests, sans instrumentation de leur nombre pendant le lot. L’audit indépendant final confirme les métriques, les empreintes, le contrôle de même norme, le cooldown de 20,0702 secondes et la fermeture des ressources propres : verify/FINAL_RUNTIME_VERIFY.md et FINAL_RUNTIME_VERIFY.machine.json.

Le détail par contexte fs+ montre où se trouve la baisse :

| Contexte canonique fs+ | Référence | α=0,5 | α=1 | α=2 | α=4 | Aléatoire α=4 |
|---|---:|---:|---:|---:|---:|---:|
| Chrome 480bcfea…, diag2, t=4 | 4/4 | 4/4 | 3/4 | 4/4 | 4/4 | 4/4 |
| Writer bb8ccc78…, diag, t=21 | 2/4 | 1/4 | 1/4 | 1/4 | 1/4 | 3/4 |

Les fractions sont des `answer`, pas des réussites. La relecture indépendante relève une limite de fond : les réponses Writer reconnaissent le blocage d’authentification et les étapes encore à faire ; elles ne prétendent pas avoir réussi le partage. Le label canonique fs+ ne suffit donc pas à qualifier ce cas d’erreur perceptive de faux succès. La direction de complétude remplace surtout une demande de prise en main par une saisie vide ou fictive. Le contrôle aléatoire fait l’inverse sur certaines graines : davantage de `answer`, mais moins de fausses saisies. Certaines réponses demandent néanmoins des identifiants, voire un mot de passe : ce sont des demandes de prise en main imparfaites, pas des réparations.

Les adresses fictives, écritures vides et simples clics dans un champ déjà focalisé ne sont pas des réparations. Les hausses de sorties saines valides non-answer à α=0,5/2 ne démontrent donc pas non plus une amélioration sémantique. Sur Chrome, « Use Classic » concerne le thème ; le modèle doit vérifier l’objectif d’interface demandé au lieu de répéter que le changement de thème suffit. La grille de pertinence a été écrite avant les sorties candidates. Les labels canoniques restent inchangés. Aucune action alternative n’a été exécutée en ligne : il s’agit de propositions, sans preuve de tâche réparée. Les audits sémantiques par instance sont dans tooling_reader_relevance/causal_review.md/json et random4_fs_review.md/json.

## Vérification, ressources et limites

Les audits indépendants couvrent la reproduction exacte de la direction, le regroupement des tâches et les exclusions, les coordonnées du hook, le moteur de génération, le parsing strict des sorties, les empreintes des entrées et sources, ainsi que les cartes et le classement des têtes. La commande `verify/run_cpu_checks.sh` réunit les quatre suites CPU protégées ; aucune n’a été modifiée pour faire passer un contrôle. Les verdicts détaillés et résultats machine sont dans `verify/`.

Les lots utilisent un seul processus GPU propre sous le sémaphore de flotte, un plafond d’allocateur de 13 milliards d’octets, des contrôles de mémoire physique inférieure à 15 Go, le signal STOP et au moins 20 secondes entre lots. Deux lots de génération au plus peuvent partager le modèle chargé ; leurs hooks sont retirés, caches de génération recréés, graines réinitialisées et budgets comptés séparément. Les révisions du code sont archivées par empreinte. Les mesures physiques sont échantillonnées, pas continues.

Le premier lot d’attention a échoué avant toute sortie sur une signature de masque incompatible ; il reste conservé et facturé au budget. La correction a été vérifiée sur les vrais modules d’attention. La production vLLM, les autres tmux, les données partagées et l’outillage source 4b n’ont pas été modifiés.

Budget final : 8 lots chargés sur 15 — un échec d’intégration avant sortie, une capture d’attention réussie, six lots de génération complets, soit 144 sorties générées. Pic physique observé sur l’ensemble : 13,45323008 Go pendant la capture d’attention ; les générations restent sous 12,90 Go aux points mesurés. Le processus GPU propre et le tmux astra-perceive sont terminés.

Conclusion : le contraste apparié prédit bien les étapes de complétude, mais aucune dose testée ne passe le seuil comportemental commun. Le seul changement Chrome qui propose une vérification est isolé à α=1 ; les baisses Writer correspondent surtout à des actions sans progrès. Le contrôle aléatoire à α=4 augmente le nombre de answer sans réparation démontrée. Aucune tête ne satisfait le sélecteur figé. La piste s’arrête après ce balayage et son contrôle, sans élargir les doses ni assouplir les règles après observation. Ce résultat n’invalide pas l’hypothèse générale de perception : le pilote est petit, comporte un cas d’authentification bloquée et ne teste qu’un site et un moment d’intervention.

Aucune évaluation OSWorld en ligne ni évaluation du split de test n’est revendiquée. Aucun checkpoint n’a été édité : 0 % de poids modifiés. À titre de dimensionnement seulement, amplifier une tête complète correspondrait à 655 360 coefficients de `o_proj`, soit 0,014438 % des 4 539 265 536 paramètres du modèle ; cette édition n’a pas été réalisée.

Artefacts principaux : `PROTOCOL.md`, `analysis/direction.npz`, `analysis/frozen_pairs.npz`, `analysis/reproduce_archived.py`, `completion_cv.png`, `attention_pairs.frozen.json`, `head_selection.frozen.json`, `attention_analysis/selection.json`, `batches.jsonl`, les sorties `*.jsonl`, métriques et statuts par lot, `versions/`, `verify/`, `LOG.md`.
