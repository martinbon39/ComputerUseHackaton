# Astra-verify — ajout de vérification par CAA

Mise à jour UTC : 2026-11-07T21:56:18.759569+00:00. Lots GPU débités : **4/15**. Captures de préfixe : **48/48**.

**Statut : exploratoire. Aucun candidat admis, aucun poids modifié, aucun score OSWorld nouveau.**

## Protocole et provenance

Manifeste figé SHA256 : `b154e4b5785566fe13d7dad180f7837f7b37ad6f06922d737136f47f6453b3a8`. Six contextes de construction issus de six tâches (2 fs+, 2 fs-, 2 sains). Six contextes de screening issus de cinq autres tâches, toutes Chrome. Les 45 tâches de confirmation canoniques sont exclues de la construction et du screening.

Quatre paraphrases « vérifier » et quatre « conclure », comparées sur exactement les mêmes contextes. Capture des résiduels des préfixes et du premier token généré après eux, dans les 32 couches. Sélection de couche du milieu par séparation de préfixes hors contexte, jamais par les réponses de screening. L’axe ne constitue pas une preuve causale avant génération libre.

Échantillonnage de production : T=0,8, top_p=0,9, top_k=20, thinking, 3072 tokens max, k=4, graines 4000–4003. Ajout au dernier token du prefill puis aux 20 premiers tokens décodés. Doses 1, 2, 4, 8 fois la norme résiduelle moyenne ; contrôle gaussien de même norme à chaque dose.

Référence héritée auditée : fs+ answer8/8, fs- answer8/8, sains valides non-answer8/8, invalides/tronqués0/24. Une calibration de la copie du générateur est prévue avant comparaison.

## Vérifications

Voir VERIFY_CPU.md : tests indépendants du calendrier du hook, de la position, de la norme BF16, de la copie exacte du générateur et des splits. Le test a détecté un import json manquant ; corrigé avant tout GPU. Test inchangé passé ensuite. Plafond allocateur 13Go, surveillance processus et arrêt à14,5Go, sémaphore partagé, STOP et cooldown20s.

## Calibration exécutée

Sans intervention : 4/4 answer, 0 invalide/tronqué. Quatre réflexions byte-identiques aux références (vérification dans LOG.md) ; 2/4 textes complets identiques. Les deux autres diffèrent uniquement après </think>, dans la formulation JSON, avec même outil. Cette calibration valide le comportement observé sur ce contexte ; elle ne prouve pas une identité de tous les tirages sur tous les contextes.

## Sémantique de la référence

Revue directe des 8 réflexions fs+ héritées : mentions concrètes de l’écran 8/8 ; écart réel identifié 0/8 ; action non-answer pertinente 0/8. Une liste de vérifications erronées ne démontre pas une vérification réussie. Les générations modifiées seront annotées selon ces mesures séparées, avec la pertinence de l’action comme garde-fou du critère de mission.

## Direction construite

Couche sélectionnée (index zéro) : **L18**. Norme résiduelle moyenne : **10.896365**. Classification de préfixes hors contexte : **0.979167**. Ces mesures concernent les préfixes imposés et ne démontrent pas une amélioration de comportement.

## Générations

| Bras | n / prévu | fs+ answer | fs- answer | sains valides non-answer | invalides/tronqués | État |
|---|---:|---:|---:|---:|---:|---|
| baseline_calibration | 4/4 | 4/4 | 0/0 | 0/0 | 0/4 | complet |
| random_a1 | 24/24 | 8/8 | 8/8 | 8/8 | 0/24 | complet |
| random_a2 | 20/24 | 8/8 | 7/8 | 4/4 | 0/20 | incomplet |
| verify_a1 | 24/24 | 8/8 | 8/8 | 8/8 | 0/24 | complet |
| verify_a2 | 22/24 | 8/8 | 8/8 | 6/6 | 0/22 | incomplet |

## Revue sémantique des fs+ générés

| Bras | Réflexions relues | Éléments écran cités | Écart réel identifié | Incertain | Action non-answer pertinente |
|---|---:|---:|---:|---:|---:|
| random_a1 | 8 | 8 | 0 | 0 | 0 |
| random_a2 | 8 | 8 | 0 | 0 | 0 |
| verify_a1 | 8 | 8 | 0 | 0 | 0 |
| verify_a2 | 8 | 8 | 0 | 1 | 0 |

Ce tableau compte les sorties effectivement relues, pas les sorties manquantes. Chaque annotation est liée au SHA256 du texte dans semantic_reviews.json. Le taux d’actions pertinentes parmi les non-answer ne peut pas être estimé quand aucun non-answer n’est produit. À dose1, le tirage Budget sample3 lit explicitement Nov8 puis affirme que Nov10–11 est le mois prochain : comparaison encore erronée. Le témoin aléatoire à dose2 sample0 montre la même contradiction ; lire la date courante n’est donc pas un effet spécifique établi de la direction.


Un bras arrêté pour qualité n’a pas d’estimation finale : le nombre d’erreurs déjà observées suffit à rendre le seuil impossible sur le panneau prévu (2 invalides/24 ou1 action saine dégradée/8). Les sorties partielles et les bornes restent dans les fichiers .jsonl/.rejected.json. Les comptes par instance sont dans metrics.json.

## Critères et limites

Critère spécifique de mission : réduction relative de P(answer) fs+ ≥50%, au moins la moitié des non-answer pertinentes comme vérification/correction, baisse de validité sur pas sains ≤5points, hausse invalides/tronqués ≤5points ; baisse fs- tolérée. Critère commun plus strict : baisse fs+ ≥25points et≥50% relative, baisse fs- ≤5points, au moins40 fs+ admissibles avant toute conclusion confirmatoire. Dernier état partagé lu au démarrage :32 fs+ admissibles, go_fs=false. Deux tâches fs+ de screening ne sont pas40 exemples indépendants ; les quatre graines par contexte ne sont pas quatre tâches.

Audit du panneau : le premier fs+ est marqué officiellement infaisable dans les métadonnées copiées. Theme:Classic ne prouve pas la désactivation de l’interface2023. Le second a une erreur visible : la barre système affiche Nov8 et la location Nov10–11, alors que le mois prochain implique Dec10–11 (revue visuelle directe par le parent). Le panneau reste figé mais ces limites interdisent une inférence de gain OSWorld à partir de la seule baisse de answer.

La pertinence exige une preuve à l’écran, selon semantic_rubric.md ; compter des mots comme « vérifier » ne suffit pas. Aucun gain online n’est inféré d’une action hors ligne. Aucun accès au split_test ou à ses résultats.

Compilation conditionnelle seulement après causalité : un neurone quasi constant écrirait approximativement le vecteur ; une édition statique sur tous les tokens n’est pas équivalente par construction au hook des20 premiers tokens. Il faudra mesurer P(answer) et vérification à±5points et compter les poids changés.

## Références

- CAA : https://arxiv.org/abs/2312.06681
- Steering des modèles à réflexion : https://arxiv.org/abs/2506.18167
- Skill local weight-surgery et /workspace/osw_shared/LIT.md lus ; constats antérieurs repris sans les refaire.
