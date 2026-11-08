# Astra-neurons — neurones MLP tardifs

Aucun candidat admis. Les deux réglages testés (top 16 et top 64, échelle 0) gardent answer 4/4 sur la première tâche fs+ disjointe, comme la baseline sur cette tâche. Chacun dépasse déjà le plafond admissible de 3 réponses sur les 8 prévues. Arrêt après deux réglages successifs sans changement de comportement, conformément au protocole.

Statut : EXPLORATOIRE. Lots réservés : 4/20. Aucun poids persistant modifié.

## Méthode et provenance

Modèle : Hcompany/Holo-3.1-4B. Plan figé : `3f2d31f5c16546a038c17aafb45dcc9650e1f65fe86c8e0a8e759a7baf52cff0`.
Quatre tâches de construction (deux fs+, deux fs-), 16 réflexions réellement générées et conservées par astra-4b-x. Le texte est retokenisé pour l’attribution car les anciens IDs ne sont pas disponibles ; ce rejeu ne mesure aucun effet comportemental. Six tâches de screening disjointes, deux par strate, k=4, graines appariées 4000–4003 entre baseline et interventions ; sampling de production T=0,8, top_p=0,9, top_k=20, réflexion activée, maximum 3072 tokens. Aucun accès au split test.
Attribution additive directe des colonnes L20–31 vers le logit answer moins la moyenne des premiers tokens concurrents, à RMS final figé. Cela ne prédit pas à soi seul un effet causal. Classement uniquement sur les tâches de construction. Hooks de mise à l’échelle appliqués pendant toute la réflexion et la génération.

## Colonnes sélectionnées

Neurones éligibles : 27796. Paramètres distincts du modèle chargé : 4,539,265,536.

| Top-k | Scalaires ciblés | % modèle |
|---:|---:|---:|
| 16 | 40960 | 0.00090235 % |
| 64 | 163840 | 0.00360939 % |

Ces nombres décrivent les colonnes correspondant aux hooks proposés ; zéro scalaire a été modifié dans un checkpoint.

## Générations

| Bras | Complet | fs+ answer | fs- answer | sain non-answer valide | invalide/tronqué |
|---|---|---:|---:|---:|---:|
| lot02_baseline | True | 6/8 | 5/8 | 8/8 | 0/24 |
| candidate_03_k16_s0p0 | False | 4/4 | NON MESURÉ | NON MESURÉ | 0/4 |
| candidate_04_k64_s0p0 | False | 4/4 | NON MESURÉ | NON MESURÉ | 0/4 |

Critères figés : baisse fs+ ≥25 points ET ≥50 % relatif ; baisse fs- ≤5 points ; baisse sain valide non-answer ≤5 points ; hausse invalide/tronqué ≤5 points. Tout résultat sous 40 fs+ admissibles reste exploratoire. Le screening actuel contient seulement deux contextes fs+ ; il ne vaut pas confirmation.

`candidate_03_k16_s0p0` : `{"assessed": true, "numerical_thresholds_pass": false, "admitted": false, "reason": "final criterion mathematically impossible", "bound": {"criterion": "fs_plus", "observed_answers": 4, "maximum_admissible_final_answers": 3.0, "planned_denominator": 8}}`

`candidate_04_k64_s0p0` : `{"assessed": true, "numerical_thresholds_pass": false, "admitted": false, "reason": "final criterion mathematically impossible", "bound": {"criterion": "fs_plus", "observed_answers": 4, "maximum_admissible_final_answers": 3.0, "planned_denominator": 8}}`

## Arrêt et limites

La baseline contient 24 sorties sur 6 tâches disjointes de construction. Les deux interventions ont été arrêtées après 4 sorties chacune, sur une seule tâche fs+ : libreoffice_impress/550ce7e7-747b-495f-b122-acdc4d0b8e54. Ne pas lire 4/4 comme un taux final sur les 8 sorties fs+ planifiées. Même avec zéro answer sur les 4 sorties restantes, le taux final serait au minimum 4/8=50%, contre 6/8=75% en baseline : baisse relative maximale 33,3%, inférieure aux 50% requis. Les strates fs- et saines des interventions n’ont pas été générées. Leur préservation n’est pas démontrée.
Le snapshot partagé de fin contient 32 fs+ admissibles, sous le seuil commun de 40. L’ensemble reste EXPLORATOIRE. Cette absence de progrès n’invalide pas toutes les chirurgies de neurones : elle rejette ces deux réglages issus de ce petit classement. Top 64×0,5, top 256×0 et les projections restent NON EXÉCUTÉS après la condition d’arrêt.

La longueur de contexte a guidé le petit screening pour borner le coût. Les quatre tâches de construction sont toutes Chrome ; leurs pas sont 4 et 13 pour fs+, contre 3 et 3 pour fs-, donc la position est confondue avec le label dans ce petit pilote. Le transfert aux autres applications est évalué mais ne peut être généralisé avec ces effectifs. Le classement DLA ignore la réponse des couches suivantes et de RMSNorm à la suppression. Les contrôles indépendants sont dans VERIFY.md lorsqu’ils sont terminés.
Budget : 4 lots sur 20 (attribution, baseline, deux interventions). Pic de mémoire réservé torch : 11,758731264 Go. Aucun processus Python propre restant après les lots. Les versions exactes du code utilisé sont conservées dans code_snapshots et identifiées dans budget.jsonl. La reproduction du contexte sain déjà présent dans le pilote précédent a donné 3/4 textes identiques ; la quatrième réflexion diffère, avec le même nombre de tokens et la même action. Aucune garantie de déterminisme bit à bit n’est revendiquée.
Aucun checkpoint édité, aucun contrôle aléatoire généré, aucune comparaison finale sur tâches de confirmation, aucun gain OSWorld en ligne prouvé. Ces étapes sont conditionnées par une intervention causalement prometteuse.
