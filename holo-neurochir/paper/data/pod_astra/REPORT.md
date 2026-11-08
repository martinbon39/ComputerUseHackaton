# Astra-08b — chirurgie des poids et boucles MiniWoB

> **État actuel — Round 3, 2026-11-07 : aucun pilotage causal admissible trouvé ; 23/40 lots, 1 224 générations sauvegardées. Aucun poids modifié (patch_spec null), compilation et validation online non exécutées faute de succès causal. Voir Round 3 en fin de rapport et r3/VERIFY.md. Rounds 1–2 conservés comme historique.**

Date UTC : 2026-11-07T16:15:30.308154+00:00

## Verdict

**Contrôle final incomplet : les résultats requis ne sont pas disponibles. Aucun succès hors ligne ni correction des boucles ne peut être déclaré.**

La direction détecte les contextes de boucle, mais sa détectabilité n’établit pas qu’elle cause la répétition. Le fichier `patch_spec.json` livre le meilleur compromis de criblage sous les limites de préservation ; il ne certifie ni un patch efficace ni une édition minimale parmi toutes les éditions possibles. Aucun candidat de développement n’a atteint le seuil d’efficacité préfixé. Aucun rollout sous poids patchés n’a été évalué ici.

## Périmètre, séparation des données et budget

Modèle : `Hcompany/Holo-3.1-0.8B`, révision cache `72da4c53b351eb60e10a7022279019633c479292`. Chargement BF16, `eval()`, gradients désactivés globalement, aucune rétropropagation, aucun optimiseur, aucun entraînement. 852,985,920 paramètres uniques au total, vision comprise ; embeddings et tête de sortie partagent leurs poids. Toutes les couches sont indexées à partir de zéro.

Développement figé : 152 rollouts, seeds {0: 34, 1: 34, 2: 32, 3: 24, 4: 23, 5: 5}, 52 réussis. Fit sur 228 pas t≥2 : 72 loop+ et 156 loop−. L’ancienne direction fournie n’a pas été utilisée : `train_direction.npz` a été recalculé exclusivement sur ce développement.

Criblage : 40 contextes fixes (16 loop+, 20 loop−, 14 de rollouts réussis), catégories chevauchantes. Attribution par entrées des writers : 16 positifs et 13 négatifs t≥2 dans ce lot. Ces nombres sont faibles et les tâches ne sont pas appariées entre classes.

Contrôle final disponible : 0 rollouts terminés, distribution seeds {}. Seuls les fichiers terminés présents au gel ont été pris ; ce n’est pas une affirmation que toutes les tâches × seeds 6–7 étaient disponibles. `freeze.json` a été écrit avant la première lecture de leurs contenus. Les paramètres et contrôles ont ensuite été conservés sans ajustement. Aucune donnée seeds 50+, 100+ ou 300+ n’a été ouverte.

Budget : **27/50 lots** inscrits avant exécution dans `budget.log`, dont un lot échoué avant le premier score (incompatibilité de replay), les baselines, le patch identité, le diagnostic global ; aucun bras final exécuté. Une passe est un lot de contextes rejoués, conformément à la définition demandée ; ce n’est pas un unique exemple. 1080 contextes prévus dans les lots (le lot échoué n’a pas été entièrement exécuté). Trois rondes adaptatives au maximum, arrêt à ce plafond ; les deux comparaisons mécanistiques de la dernière ronde sont exclues de la sélection. Un seul processus GPU propre à cette expérience à la fois, verrouillé par `flock`, dans tmux `astra`. Les autres sessions et `/workspace/projet/holo`, `/workspace/runs/diag*` n’ont pas été modifiés.

Seuils inscrits avant criblage : baisse loop+ d’au moins 0,10 nat/token ; baisse loop− et succès d’au plus 0,02 nat/token. Sélection : parmi les candidats satisfaisants, minimum de poids ciblés ; faute de candidat satisfaisant, plus forte baisse loop+ parmi ceux qui respectent les deux limites de préservation. Un résultat inférieur au seuil n’a pas été requalifié en succès. Le verdict final demande aussi une baisse loop+ supérieure à chacun des deux contrôles aléatoires.

## Hypothèse et preuves sur les activations et les poids

Hypothèse testée : une composante du résiduel, écrite par certains MLP et projections de sortie d’attention, entretient les actions répétées ; la retirer de leurs vecteurs d’écriture devrait réduire sélectivement la probabilité de ces actions.

Pour chaque couche, `u_l = normalize(mean(h_l | loop+) − mean(h_l | loop−))`. CV en cinq plis groupés par tâche, t≥2 : AUROC de L10 **0.904202**, contre **0.686075** pour l’indice du pas et **0.707131** pour la longueur du contexte. L10 est aussi le meilleur de ce nouveau calcul propre. Son choix initial était néanmoins informé par le résultat historique fourni, dont le split exact n’était pas garanti : le contrôle final n’est pas une réplication entièrement sans connaissance préalable de la couche.

Tous les incréments suivants sont projetés sur le même u10, pour éviter de comparer des axes différents. Unité : différence de moyenne de projection loop+ moins loop−, sur les 228 pas de fit.

| Couche | Écart résiduel en sortie | Contribution MLP | Contribution attention estimée |
|---|---:|---:|---:|
| 8 | 0.024431 | 0.003590 | 0.005064 |
| 9 | 0.055692 | 0.016452 | 0.014809 |
| 10 | 0.172288 | 0.053856 | 0.062740 |
| 11 | 0.114522 | -0.043441 | -0.014325 |
| 12 | 0.105386 | -0.035749 | 0.026613 |
| 13 | 0.145268 | -0.002625 | 0.042506 |
| 15 | 0.175311 | 0.000400 | 0.045242 |
| 19 | 0.225740 | -0.007135 | 0.016322 |
| 23 | 0.184744 | 0.039899 | -0.069099 |

Attention estimée = résidu après couche − résidu avant couche − sortie du MLP, donc inclut l’erreur numérique du résiduel BF16. L9–L10 font émerger une grande partie de la séparation ; les MLP L11–L12 s’y opposent, et des couches ultérieures la réécrivent. Il s’agit d’une cartographie de contributions associées au label, pas d’une preuve de circuit causal complet.

Pour une colonne j de W, capacité d’écriture `c_j = u10ᵀ W[:,j]`, contribution effective `c_j z_j`, où z est l’entrée de la projection capturée au dernier token du prefill. Classement par `|c_j (mean(z_j|+) − mean(z_j|−))|`. Cela distingue capacité du poids et activité réelle. Les sorties de MLP sont 1024×3584 ; les projections d’attention examinées sont 1024×2048.

**10.mlp.down_proj** : écart effectif 0.052623 dans le replay. Les 64 colonnes les plus contributrices portent 20.3 % de la somme des contributions absolues. La sélection native par |uᵀW|, différente, porte 15.5 % de l’énergie des coefficients et un écart signé 0.013520. Colonnes dominantes par attribution : 383, 1275, 2360, 206, 2685, 767, 380, 1205, 1986, 3155, 434, 435, 112, 2192, 2480, 116.

| Colonne | uᵀW_j | Δ activation | Contribution à l’écart |
|---|---:|---:|---:|
| 383 | -0.043756 | -0.108830 | 0.004762 |
| 1275 | -0.030396 | -0.054365 | 0.001653 |
| 2360 | -0.028894 | -0.044890 | 0.001297 |
| 206 | 0.018631 | 0.054869 | 0.001022 |

**10.linear_attn.out_proj** : écart effectif 0.059982 dans le replay. Les 64 colonnes les plus contributrices portent 33.8 % de la somme des contributions absolues. La sélection native par |uᵀW|, différente, porte 22.1 % de l’énergie des coefficients et un écart signé 0.019584. Colonnes dominantes par attribution : 1041, 1412, 1504, 703, 1460, 1418, 747, 1409, 1461, 1434, 668, 1364, 1513, 602, 713, 1383.

| Colonne | uᵀW_j | Δ activation | Contribution à l’écart |
|---|---:|---:|---:|
| 1041 | 0.041164 | 0.061630 | 0.002537 |
| 1412 | -0.025019 | -0.084538 | 0.002115 |
| 1504 | -0.047427 | -0.040500 | 0.001921 |
| 703 | -0.029921 | -0.058681 | 0.001756 |

Les 48 writers sont documentés dans `writers.json`. Les colonnes d’attention sont des canaux de sortie, pas des neurones MLP. Aucune preuve ne permet d’appeler les 64 premières colonnes « les 64 neurones responsables des boucles ».

Embeddings/lm_head : inspection de leurs produits scalaires/cosinus avec u10, poids partagés. Parmi les tokens les plus alignés : ' themselves', ' asleep', ' engulf', ' erupted', ' radical', ' remains', ' región', ' lze'. Pas de groupe évident de commandes d’action dans ces premiers résultats. Cette projection ignore la RMSNorm finale et les transformations intermédiaires : ce n’est pas un effet causal sur les logits, ni la preuve d’absence de mécanisme lexical. Aucun embedding/lm_head n’a été modifié.

### Contrôle mécanistique : effacement global du même u10

Toutes les colonnes de tous les writers des 24 couches ont leur composante u10 retirée (α=1), sans changer les embeddings. Cette intervention volontairement large est un diagnostic, exclu du choix du patch minimal.

| Mesure | Original | Effacement global |
|---|---:|---:|
| Écart de projection u10, L0 | 0.000156 | -0.000064 |
| Écart de projection u10, L10 | 0.165270 | -0.000080 |
| Écart de projection u10, L23 | 0.226719 | 0.000793 |
| Log-prob/token, loop+ | -0.095409 | -0.108825 |
| Log-prob/token, loop− | -0.091205 | -0.099515 |
| Log-prob/token, succès | -0.137698 | -0.151030 |

Le contraste u10 à L10 passe de 0,165270 à −0,000080 : le marqueur est pratiquement effacé. Pourtant la log-prob des boucles ne baisse que de 0,013416 nat/token, et celle des actions de rollouts réussis baisse de 0,013331. Dans ce test, effacer le marqueur ne produit donc pas une réduction sélective nette des réponses en boucle. Cela affaiblit l’hypothèse naïve d’un unique axe causal retirable ; cela ne prouve pas qu’aucun autre circuit de répétition existe.

## Édition livrée et taille

Format natif, directement lu par `holo.surgery.apply_patch_inplace` ; aucun nouveau format nécessaire :

```json
{
  "direction_file": "/workspace/astra/train_direction.npz",
  "layers": [
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23
  ],
  "alpha": 4.0,
  "topk": 64,
  "writers": [
    "mlp",
    "attn"
  ]
}
```

Pour les top-k colonnes par |u_lᵀW| de chaque writer : `W[:,J] ← BF16(W[:,J] − α u_l (u_lᵀ W[:,J]))`. Chaque variante repart des poids originaux exacts ; aucun cumul d’éditions. Avec α=4, ce n’est pas une simple orthogonalisation : le coefficient sélectionné devient théoriquement −3 fois sa valeur initiale. Ce dépassement fait partie de l’expérience et ne doit pas être dissimulé sous le terme « suppression ».

15 couches × 2 writers × 64 colonnes × 1024 = **1,966,080 entrées ciblées**, soit **0.230494 %** du modèle entier. **1,957,093 valeurs réellement différentes après arrondi BF16**, soit **0.229440 %**. Norme Frobenius effective du delta : **6.185231**. La cardinalité ciblée et le nombre réellement changé ne sont pas interchangeables.

Les statistiques de poids ci-dessus proviennent du bras de criblage choisi ; aucun bras final n’a été exécuté faute de rollouts réservés.

Les indices complets sont dans `patch_columns.json`. `patch_columns.npz` contient une reconstruction CPU de référence ; `patch_weights_actual.npz`, lorsqu’un bras final patché a été exécuté, contient les colonnes avant/après réellement appliquées sur GPU. Le patch est reproductible avec le modèle original et le NPZ de direction. Il n’est pas recommandé comme correctif validé.

## Tous les candidats de criblage

Différences patch−original, en nat/token (négatif = action enregistrée moins probable). Les contrôles d’identité/global sont séparés. L’ensemble des scores par pas est conservé dans les fichiers JSON des candidats.

| Candidat | Entrées ciblées | Δ loop+ | Δ loop− | Δ succès | Seuil complet atteint |
|---|---:|---:|---:|---:|---|
| r1_L10_attn_64 | 65,536 | -0.000828 | 0.000667 | 0.001568 | non |
| r1_L10_attn_None | 2,097,152 | -0.001768 | 0.000377 | 0.002297 | non |
| r1_L10_mlp_64 | 65,536 | -0.000533 | 0.000534 | 0.001139 | non |
| r1_L10_mlp_None | 3,670,016 | -0.000341 | -0.000140 | 0.000710 | non |
| r1_L10_mlp_attn_64 | 131,072 | -0.000841 | -0.000036 | 0.001265 | non |
| r1_L10_mlp_attn_None | 5,767,168 | -0.002106 | -0.000735 | 0.001221 | non |
| r2_distributed_64 | 1,966,080 | -0.001995 | 0.003238 | 0.008601 | non |
| r2_distributed_None | 86,507,520 | -0.004465 | -0.001886 | -0.000255 | non |
| r2_early_64 | 262,144 | -0.000296 | 0.000596 | 0.002788 | non |
| r2_early_None | 11,534,336 | -0.002772 | -0.000321 | 0.001454 | non |
| r2_late_attn_64 | 458,752 | -0.001372 | 0.002337 | 0.005108 | non |
| r2_late_attn_None | 14,680,064 | -0.001890 | 0.002319 | 0.006168 | non |
| r2_mit_layers_64 | 131,072 | -0.000529 | -0.000053 | 0.000545 | non |
| r2_mit_layers_None | 7,340,032 | -0.000627 | -0.000529 | 0.000112 | non |
| r3_L10_a16 | 131,072 | -0.027338 | -0.031665 | -0.043465 | non |
| r3_L10_a4 | 131,072 | -0.003284 | -0.000655 | -0.001697 | non |
| r3_distributed_a16 | 1,966,080 | -0.262659 | -0.259443 | -0.342088 | non |
| r3_distributed_a4 | 1,966,080 | -0.013955 | -0.008612 | -0.003290 | non |
| r3_early_a16 | 1,048,576 | -0.206201 | -0.197138 | -0.284703 | non |
| r3_early_a4 | 1,048,576 | -0.008113 | -0.008681 | -0.017657 | non |
| r3_mit_layers_a16 | 131,072 | -0.006526 | 0.001035 | -0.002854 | non |
| r3_mit_layers_a4 | 131,072 | -0.001384 | 0.001084 | 0.001820 | non |

## Contrôle final seeds 6–7

Cible : réponse brute enregistrée + EOS, scorée par `holo.replay.score(rebuild_messages(...))`. Deux métriques sont rapportées : moyenne, sur les pas, de la log-prob moyenne par token ; et moyenne de la somme des log-probs de toute la réponse. Les réponses ont des longueurs différentes. La seconde mesure est la log-prob de la réponse complète, pas une probabilité agrégée sur toutes les formulations possibles de la même action.

**Non disponible : voir `freeze.log` et `heldout_manifest.json`. Aucun chiffre de développement n’est présenté comme une mesure hors ligne finale.**

## Vérification, limites et reproduction

Le premier replay a échoué car les `mm_token_type_ids` du préfixe n’étaient pas étendus à la réponse teacher-forced dans la version installée de Transformers. Correction uniquement dans `code/holo/replay.py` : ajouter des types texte (zéros) pour les tokens cibles. `regression_before.log` montre l’AssertionError ; `regression_after.log` montre PASS. Le calcul MRoPE a aussi été relu indépendamment contre la version installée. Les indices de capture sont `n_in−1`, jamais le dernier token de la réponse ; le nombre de tokens du contexte est vérifié pour chaque exemple.

| Couche de fidélité | Cosinus minimum avec résidu enregistré | Erreur relative maximale |
|---|---:|---:|
| 0 | 0.99995184 | 0.010422 |
| 10 | 0.99950761 | 0.031437 |
| 23 | 0.99693567 | 0.078709 |

Le replay n’est donc pas bit à bit identique aux captures enregistrées. Des différences de moteur/matériel/arithmétique BF16 entre collecte et replay sont possibles ; leur cause exacte n’a pas été isolée. En revanche, le patch identité α=0 reproduit exactement les scores baseline sur les 40 contextes, ce qui vérifie la comparaison inter-variantes de ce harness.

Limites : labels automatiques (clics proches, seuil écran de 1 %, incluant parfois des changements réels très petits) ; corpus partiel et tâches sélectionnées ; tâches impossibles dans le développement ; pas de test sur tâches nouvelles ; capture des neurones à une seule position alors que le patch agit sur tous les tokens ; `raw` inclut syntaxe, noms, coordonnées et EOS, donc une baisse peut être une dégradation de format ; teacher forcing imposant toute l’histoire, sans mesure d’une meilleure action alternative ni du taux de boucles en génération libre. La séparation par seed est une séparation de rollouts, pas par familles de tâches. Aucune nouvelle capacité n’a été démontrée.

Artefacts : `PROTOCOL.md`, `budget.log`, `train_manifest.json`, `heldout_manifest.json`, `freeze.json`, `train_analysis.json`, `writers.json`, `lexical.json`, `fidelity.json`, `selection.json`, les JSON de résultats par pas, `offline_summary.json` (NON PRODUIT si contrôle final absent), `patch_spec.json`, `train_direction.npz`, les deux specs aléatoires, et les scripts Python. Les hashes du gel protègent les directions, spécifications et code du replay. Une revue indépendante est consignée séparément dans `VERIFY.md` lorsqu’elle est terminée.

Application du patch sur le modèle original, avec le code et le cache indiqués :

```python
from holo.model import Holo
from holo.surgery import load_spec, apply_patch_inplace
h = Holo(model_path="Hcompany/Holo-3.1-0.8B", device="cuda")
stats = apply_patch_inplace(h.model, load_spec("/workspace/astra/patch_spec.json"))
```

Le lanceur d’expérience refuse d’écraser un résultat existant. Une répétition doit utiliser un nouveau répertoire/noms de résultats et un budget explicite ; aucune passe supplémentaire n’est implicite.

Référence méthodologique : [Sparks of Weight-Space Programming, expérience 8, MIT CSAIL, 2 novembre 2026](https://rikiyat.github.io/blog/weight-space-programming/). Cette expérience porte sur Qwen et des boucles de raisonnement, avec une intervention différente ; ses résultats ne sont pas transférés à Holo/MiniWoB et ne constituent pas une preuve pour le présent patch.

## Round 2 — recherche de sélectivité et contrôle seeds 6–7

Rapport établi le 2026-11-07T16:54:01.232983+00:00. Les sections précédentes décrivent Round 1 et ses anciens seuils ; cette section décrit la reprise et remplace son verdict pour le patch canonique actuel.

**Aucune édition sélective validée : le candidat figé échoue au critère sur le développement complet.** Critère complet : développement=False, réservé=False. La baisse loop+ du patch est supérieure au contrôle aléatoire : True. Aucune génération libre sous patch ; aucune correction comportementale des boucles démontrée.

### Protocole, sélection et séparation

Baisse D = moyenne(log-prob originale − log-prob éditée), positive si la réponse devient moins probable. Métrique primaire : nats/token de la réponse brute contenant l’action répétée + EOS, teacher-forced avec le même contexte. Ce score inclut format et arguments ; il ne mesure pas la probabilité marginale de toutes les formulations d’une action. Les sommes de log-probs de la réponse entière sont également rapportées.

« Sains » = union dédupliquée des pas loop− et des pas de rollouts réussis. Succès qualifie le rollout, pas une action individuellement. Le critère demandé est appliqué de façon conservatrice : D_loop+ > 0 et D_loop+ ≥ 3 × max(0, D_sains, D_loop−, D_succès). Une hausse des scores sains donne une dégradation nulle pour ce test ; elle ne produit pas un ratio infini présenté comme preuve.

18 nouveaux candidats, en trois séries de six, sur les mêmes 40 contextes de développement. Les anciens candidats restent comparables sous le nouveau critère. Sélection prédéfinie : plus grande baisse loop+ parmi les candidats admissibles, puis moins de poids ciblés en cas d’égalité. Gagnant : `a2_r3_a3`. Gel horodaté **2026-11-07T16:34:11Z**, dans `a2_freeze.json`, avant toute lecture nouvelle des contenus seeds 6–7. Patch, direction aléatoire, code de scoring, protocole et fichiers de sélection sont hashés. Le manifeste réservé vide de Round 1 avait été lu à la reprise.

Après le gel : deux passes sur tous les 415 pas éligibles du développement sauvegardé (seeds 0–5), sans sélection supplémentaire ni retouche du patch. Cela élargit l’échantillon ; ce n’est pas un test indépendant, car les directions et le criblage proviennent de ce même développement. Les données du développement restent le snapshot partiel de Round 1, notamment seed 5 peu représentée.

Les nouvelles directions MLP utilisent les sorties MLP déjà enregistrées. Les directions contrastées calculent les différences loop+ − loop− séparément à chaque t=2…13, puis les moyennent avec la fréquence des positifs par t. Elles ne contrôlent ni tâche ni longueur de contexte et ne comprennent pas tous les succès non étiquetés loop−. Aucun gradient, entraînement ou optimiseur.

### Patch figé et contrôle

```json
{
  "direction_file": "/workspace/astra/train_direction.npz",
  "layers": [
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23
  ],
  "alpha": 3.0,
  "topk": 64,
  "writers": [
    "mlp",
    "attn"
  ]
}
```

Le patch sélectionne les colonnes par |u_lᵀW[:,j]| et applique W[:,J] ← BF16(W[:,J] − α u_l(u_lᵀW[:,J])). À α=3 la composante devient théoriquement −2 fois sa valeur initiale : inversion amplifiée, pas simple projection orthogonale. Chaque bras repart des poids originaux.

Contrôle aléatoire : directions gaussiennes unitaires, seed 2026110702, mêmes couches/writers/alpha/top-k. Le top-k est recalculé dans sa propre direction : même nombre nominal de poids ciblés, mais pas les mêmes colonnes ni nécessairement le même nombre de valeurs BF16 réellement changées. Norme du delta non appariée ; ce contrôle ne sépare donc pas tous les effets de taille de perturbation.

| Bras final | Poids ciblés | Valeurs BF16 changées | Norme Frobenius réelle du delta |
|---|---:|---:|---:|
| patch | 1,966,080 | 1,953,863 | 4.639009 |
| random | 1,966,080 | 1,950,843 | 3.768563 |

### Développement complet seeds 0–5

Moyennes par pas de log-prob/token (plus négatif = réponse moins probable).

| Groupe | N | Original | Patché | Aléatoire | Baisse patch | IC95 % baisse patch |
|---|---:|---:|---:|---:|---:|---|
| loop+ | 72 | -0.09087929 | -0.09476926 | NA | 0.00388997 | [0.00131713, 0.00641304] |
| healthy | 344 | -0.11602996 | -0.12599836 | NA | 0.00996840 | [0.00662334, 0.01369342] |
| loop- | 287 | -0.10613141 | -0.11528785 | NA | 0.00915644 | [0.00651375, 0.01162669] |
| success | 119 | -0.13639902 | -0.14725647 | NA | 0.01085745 | [0.00398668, 0.02057570] |

Intersection loop+ / sains : **1 pas**, conservée et explicitée. IC descriptifs par bootstrap de tâches (2000 réplications, seed 8102), sans correction de sélection multiple.

Moyenne de la somme des log-probs de toute la réponse :

| Groupe | Original | Patché | Aléatoire |
|---|---:|---:|---:|
| loop+ | -5.49001752 | -5.72497558 | NA |
| healthy | -7.97976918 | -8.71042802 | NA |
| loop- | -7.45879207 | -8.14744149 | NA |
| success | -9.68164697 | -10.55795249 | NA |

### Contrôle final seeds 6–7

Moyennes par pas de log-prob/token (plus négatif = réponse moins probable).

| Groupe | N | Original | Patché | Aléatoire | Baisse patch | IC95 % baisse patch |
|---|---:|---:|---:|---:|---:|---|
| loop+ | 23 | -0.07198938 | -0.07429665 | -0.07328731 | 0.00230726 | [-0.00066730, 0.00761980] |
| healthy | 119 | -0.11248348 | -0.12140671 | -0.11667309 | 0.00892323 | [0.00507477, 0.01402740] |
| loop- | 90 | -0.10961683 | -0.11994450 | -0.11381599 | 0.01032767 | [0.00672641, 0.01481105] |
| success | 54 | -0.13051701 | -0.13993563 | -0.13584591 | 0.00941862 | [0.00267603, 0.01939179] |

Intersection loop+ / sains : **0 pas**, conservée et explicitée. IC descriptifs par bootstrap de tâches (2000 réplications, seed 8102), sans correction de sélection multiple.

Moyenne de la somme des log-probs de toute la réponse :

| Groupe | Original | Patché | Aléatoire |
|---|---:|---:|---:|
| loop+ | -4.48545201 | -4.63987674 | -4.56805657 |
| healthy | -9.78170019 | -10.70535926 | -10.05718434 |
| loop- | -9.53147429 | -10.50681515 | -9.80129230 |
| success | -12.57505809 | -13.71256263 | -12.93058704 |

Réservé : 48 rollouts terminés dans le snapshot, seeds {6: 24, 7: 24}. Horodatage du snapshot : 2026-11-07T16:48:28.739510+00:00. Voir `a2_collection_status.json` pour la complétude observée des producteurs.

Les 40 contextes du criblage, rejoués dans le développement complet, reproduisent exactement les scores originaux et patchés (écarts maximaux 0). Analyse descriptive après gel : baisse saine de 0,01458061 nat/token à t<2 et 0,00535619 à t≥2 ; même à t≥2, elle dépasse la baisse loop+ de 0,00388997. Hors criblage : 56 loop+ baissent de 0,00234281 et 320 sains de 0,01079605. Exclure le pas loop+ du groupe sain donne encore une baisse de 0,00992463. Le petit criblage et sa sélection adaptative étaient donc insuffisants ; aucune retouche postérieure.

### Nouveaux candidats

Deltas positifs = baisse de log-prob/token.

| Candidat | D loop+ | D sains | D loop− | D succès | Admissible criblage |
|---|---:|---:|---:|---:|---|
| a2_r1_matched_mlp_attn | 0.00112814 | -0.00029880 | -0.00051873 | -0.00053252 | True |
| a2_r1_matched_mlp_mlp | 0.00017664 | -0.00072362 | -0.00002671 | -0.00131791 | True |
| a2_r1_matched_resid_attn | 0.00102243 | -0.00000336 | 0.00033094 | -0.00045436 | True |
| a2_r1_matched_resid_mlp | 0.00052239 | -0.00040962 | 0.00020931 | -0.00134851 | False |
| a2_r1_mlp_attn | 0.00067888 | 0.00098845 | 0.00071135 | 0.00107825 | False |
| a2_r1_mlp_mlp | 0.00042847 | -0.00080227 | -0.00064098 | -0.00145681 | True |
| a2_r2_distributed128 | 0.00137807 | -0.00361455 | -0.00323067 | -0.00562316 | True |
| a2_r2_distributed_a2 | 0.00471908 | -0.00371256 | -0.00125880 | -0.00813566 | True |
| a2_r2_matched_attn128 | 0.00051568 | 0.00003195 | -0.00048863 | -0.00019454 | True |
| a2_r2_matched_attn16 | 0.00062852 | -0.00044418 | -0.00029313 | -0.00130287 | True |
| a2_r2_matched_early | 0.00084229 | -0.00011643 | -0.00088703 | -0.00023261 | True |
| a2_r2_matched_late | 0.00076031 | -0.00000935 | 0.00013151 | -0.00044586 | True |
| a2_r3_a25 | 0.00707916 | -0.00274009 | 0.00018050 | -0.00761810 | True |
| a2_r3_a3 | 0.00930505 | -0.00106696 | 0.00223047 | -0.00632112 | True |
| a2_r3_attn | 0.00207294 | -0.00284539 | -0.00216168 | -0.00449410 | True |
| a2_r3_k16 | 0.00187835 | -0.00350293 | -0.00293183 | -0.00591593 | True |
| a2_r3_k32 | 0.00248800 | -0.00358598 | -0.00242412 | -0.00674999 | True |
| a2_r3_mlp | 0.00340162 | -0.00202784 | 0.00054752 | -0.00524771 | True |

### Budget, ressources, vérification

Budget final : **50/50 lots**, dont 27 hérités et 23 nouveaux. Chaque lot ajouté avant son scoring. Plafond de recherche atteint : 18 nouveaux candidats ; pas de poursuite après gel. Un seul processus GPU propre à l’expérience à la fois, dans tmux `astra2`, verrou `gpu.lock`. Allocateur plafonné à 24 GiB ; pic réservé PyTorch mesuré **23.340 GiB** (distinct du total du GPU partagé). Les relevés nvidia-smi du processus complètent ce chiffre.

Les données de `/workspace/runs/diag` sont uniquement lues et copiées sous `/workspace/astra/data`; aucun fichier de `/workspace/runs*` ni `/workspace/projet/holo` modifié par cette reprise. Aucune autre session tmux pilotée. Le git pull local a échoué à cause de modifications préexistantes, laissées intactes ; aucun code de ce checkout utilisé pour l’édition.

Verification indépendante : `VERIFY_ROUND2.md` (RAN/PASSED/CORRECT/NOT RUN). Artefacts : `a2_ranking.json`, `a2_freeze.json`, `patch_spec.json`, `patch_columns.json`, `patch_columns.npz` (reconstruction CPU), `a2_patch_weights_actual.npz` (colonnes GPU réellement appliquées), `a2_dev_summary.json`, `a2_final_summary.json`, résultats par pas, manifeste réservé et specs/directions aléatoires. Les anciens patch_columns/spec sont préservés avec préfixe `round1_`.

Limites : faible corpus, sélection adaptative sur 40 pas, labels automatiques, replay BF16 non bit-identique à la collecte initiale, tâches partagées entre seeds, absence de nouvelles tâches ou de rollouts patchés. Le résultat ne doit pas être présenté comme une réplication comportementale de [Sparks of Weight-Space Programming, exp. 8](https://rikiyat.github.io/blog/weight-space-programming/), qui évaluait des générations et réussites de benchmarks.

Vérification finale Round 2 : les moyennes, sommes et intervalles ont été recalculés indépendamment ; 14 hashes de gel inchangés, budget 50/50. L’export GPU du patch est la référence : ses colonnes et poids avant édition correspondent exactement à la reconstruction CPU ; 223 entrées après édition diffèrent entre CPU et GPU (écart absolu maximal 0,0001220703125), par différences numériques du calcul avant arrondi BF16. Le nombre GPU de valeurs changées, 1 953 863, est confirmé. Verdict de vérification : artefacts et conclusion négative conformes ; critère expérimental échoué.

## Round 3 — test causal comportemental avant édition

Rapport UTC : 2026-11-07T17:57:57.824476+00:00

**Aucun pilotage admissible trouvé dans cette recherche ; aucun poids Holo édité.** Le seuil était une réduction relative de REPEAT ≥50 %, avec une perte de HEALTH ≤5 points. Les étapes de compilation et de validation online sont restées conditionnées à ce succès causal, conformément au protocole. Ce résultat ne prouve pas qu’aucune autre direction ne puisse fonctionner.

### A. Mesure comportementale

Générations libres sur les messages de `holo.replay.rebuild_messages`, aucune log-prob teacher-forced utilisée. T=0,8, top_p=0,95, top_k=20, max_new_tokens=512, thinking désactivé. Quatre tirages par contexte, groupés via `num_return_sequences=4`, seeds SHA256 fixes par contexte et identiques entre bras. Modèle original Hcompany/Holo-3.1-0.8B en BF16, eval, sans gradients ni entraînement.

Échantillon de développement fixe : 24 contextes uniques, 12 loop+ et 12 sains, soit 48 tirages par métrique. Original : REPEAT **95.83 % (46/48)** ; HEALTH **75.00 % (36/48)** ; parsing/adaptation **96/96**. Il fallait au plus 23 répétitions et au moins 34 succès HEALTH.

REPEAT réutilise `taxonomy.same_action` face à l’action précédente ; les coordonnées sont reconverties dans le screenshot non agrandi avec les offsets crop_box. HEALTH : union dédupliquée loop−/rollout réussi, parse+adaptation et même outil que l’action enregistrée ; clic strictement à moins de 15 pixels. Le pool sain inclut les succès également loop+, mais cet échantillon n’en sélectionne aucun. HEALTH est une proximité à une action enregistrée, pas une preuve de réussite de tâche.

Deux pilotes (un scalaire, un vectorisé) de 2 contextes ont chacun donné REPEAT 4/4 et HEALTH 3/4 ; ils n’ont pas servi à la sélection. Le premier essai CPU a échoué avant la première génération, sur un noyau CUDA-only ; ce lot reste compté. Un second démarrage CPU a été interrompu avant de commencer un lot.

### B. Interventions à l’inférence

Les directions historiques utilisent seulement le snapshot seeds0–5. Les nouveaux contrastes appariés ont parcouru les 839 pas sauvegardés de 152 rollouts : 97 paires valides, même tâche et même pas, avec action changée chez le témoin. Audit : 24 paires croisaient normal/impossible ; une seconde famille stricte apparie aussi cette propriété (73 paires, mêmes 10 tâches). Directions résiduelles et MLP, différences de moyennes et première PCA centrée ; moyenne des directions de couches également testée. Les PCA non centrées préparées initialement n’ont pas été évaluées.

Table : résultats complets sauf mention explicite. Les intervalles « ≤ » sont des bornes de rejet, pas des scores finaux inventés. Après l’essai dégénéré alpha=−1, les nouveaux bras évaluent les pas sains d’abord et s’arrêtent seulement si même tous les tirages sains restants réussis ne pourraient atteindre 70 % ; 15 échecs rendent le seuil impossible. Le seed de chaque contexte ne dépend pas de sa position.

| Bras | REPEAT | HEALTH | Tirages enregistrés | État |
|---|---:|---:|---:|---|
| baseline | 95.83 % | 75.00 % | 96 | complet |
| u10_L10 | 93.75 % | 66.67 % | 96 | complet |
| u10_L9_13 | 89.58 % | 60.42 % | 96 | complet |
| u10_all | 93.75 % | 64.58 % | 96 | complet |
| native_all | 81.25 % | 58.33 % | 96 | complet |
| identity | 95.83 % | 72.92 % | 96 | complet |
| u10_all_a2 | 93.75 % | 56.25 % | 96 | complet |
| u10_all_am1 | non mesuré | non mesuré | 4 | interrompu, non sélectionnable |
| u10_add025 | non mesuré | non mesuré | 4 | interrompu, non sélectionnable |
| paired_all | non mesuré | ≤ 66.67 % | 36 | rejet certain par HEALTH |
| paired_pca_all | non mesuré | ≤ 62.50 % | 36 | rejet certain par HEALTH |
| mlp_all | non mesuré | ≤ 66.67 % | 36 | rejet certain par HEALTH |
| mlp_pca_all | non mesuré | ≤ 62.50 % | 40 | rejet certain par HEALTH |
| mean_all | non mesuré | ≤ 64.58 % | 40 | rejet certain par HEALTH |
| random_all | 95.83 % | 72.92 % | 96 | complet |
| baseline_repeat | 95.83 % | 70.83 % | 96 | complet |
| strict_paired | non mesuré | ≤ 62.50 % | 36 | rejet certain par HEALTH |
| strict_paired_pca | non mesuré | ≤ 64.58 % | 40 | rejet certain par HEALTH |
| strict_mlp | non mesuré | ≤ 68.75 % | 36 | rejet certain par HEALTH |
| strict_mlp_pca | non mesuré | ≤ 66.67 % | 36 | rejet certain par HEALTH |

Alpha=−1 est une amplification de la composante existante, pas un ajout négatif constant. Cet essai a été interrompu après les quatre premières sorties enregistrées, toutes invalides (~92 secondes pour le premier contexte), pendant le contexte suivant. Il ne fournit aucun score HEALTH et ne démontre pas un échec mesuré sur tout le lot. L’ajout négatif distinct h ← h −0,25u a lui aussi été interrompu après quatre sorties invalides : premier contexte ~279,5 secondes de génération. Il ne fournit ni HEALTH complet ni REPEAT ; son effet causal reste non évalué au-delà de ce pilote dégénéré.

Contrôle aléatoire : directions gaussiennes unitaires, seed2026110703, projection sur les 24 couches à alpha1. C’est un contrôle de pilotage, pas un contrôle de poids modifiés : aucune compilation n’a été autorisée par le critère causal.

Arrêt : deux familles de recherche sans amélioration admissible observée sous la contrainte HEALTH, avec deux variantes interrompues pour dégénérescence/coût de génération ; le plafond de40 lots est un maximum, pas une obligation de poursuivre une recherche sans progrès.

### C. Compilation : non exécutée

**patch_spec final : `null`. Poids réellement modifiés : 0, soit 0 %.** Les anciennes spécifications à la racine de /workspace/astra concernent les rounds précédents et ne sont pas un patch validé par Round3. `r3/selection.json` porte le statut courant.

Point vérifié indépendamment : le hook Holo projette en sortie de bloc ; orthogonaliser les writers modifie aussi l’entrée du MLP après l’attention. Même sur toutes les couches, les deux interventions ne sont donc pas automatiquement identiques. Le pont prévu devait tester des hooks sur tous les writers (embedding, attention, MLP, merger visuel+biais), puis les poids correspondants, avec séparation du head lié pour conserver le readout.

La routine `r3/compile.py`, non appliquée aux poids Holo, a été vérifiée sur un modèle synthétique : six writers, poids/biais/embedding corrects, head délié sans changement de valeurs ; erreur hooks/poids max2,38e−7 FP32 et 0,0078125 BF16. Ces tests ne valent pas validation comportementale d’un patch Holo. Aucun test top-k ni export de modèle patché.

### D. Validation online : non exécutée

| Bras prévu | Rollouts | Succès | Taux de boucle |
|---|---:|---:|---:|
| astra3_val_orig / original | 0 | NA | NA |
| astra3_val_patch / patched | 0 | NA | NA |

Sans pilotage causal validé, pas de patch figé : ni contrôle Round3 seeds6–7, ni consommation online seeds50–51. Les données historiques Round2 seeds6–7 figurant plus haut ne sont pas des résultats Round3. Le lanceur isolé `r3/scripts/pod_rollouts.sh` est préparé avec garde de gel/validation, modèle0.8B, au plus2 shards et uniquement tmux astra3 ; il n’a pas été exécuté. `holo.diagnostic` online n’a donc aucun résultat nouveau.

### Reproductibilité, budget et limites

Budget : **23/40 lots** dans `/workspace/astra/budget_r3.log`, inscrits avant génération, dont le lot CPU échoué et les deux variantes interrompues. Au total, 1 224 générations brutes ont été sauvegardées, pilotes et variantes interrompues compris. Les rejets précoces restent des lots entiers au budget. Données brutes, scripts, manifeste des essais et vérification indépendante sont dans `/workspace/astra/r3/`.

Le contrôle alpha0 donne 92/96 textes identiques à l’original, REPEAT inchangé46/48, HEALTH35/48 contre36/48 : variation de2,083 points. La cause exacte n’est pas isolée ; une reproduction bit à bit n’est pas démontrée. Le second original sans hook, avec ordre sain-d’abord, donne HEALTH34/48 : écart de4,167 points avec le premier original, REPEAT toujours46/48. La mesure HEALTH sur seulement12 contextes est donc particulièrement bruitée. Cette variation n’a pas servi à assouplir le seuil.

Petit échantillon de12 contextes par groupe ; les quatre tirages d’un contexte ne sont pas des observations de tâches indépendantes. Recherche adaptative, labels automatiques, santé mesurée par proximité, contexte historique forcé mais réponse générée librement. Aucune réussite online, aucun gain de capacité et aucune équivalence empirique pilotage/poids ne sont revendiqués.

Un seul processus GPU expérimental à la fois, allocateur plafonné à24Gio (pic réservé mesuré parmi les résultats terminés : 6,02 Gio), session astra3 uniquement ; les autres sessions, notamment vllm_8000, n’ont été ni pilotées ni arrêtées. Aucun fichier de /workspace/projet/holo ou /workspace/runs/diag* modifié. Les latences de production n’ont pas été instrumentées pour démontrer une absence absolue de contention. Le pull local a été refusé à cause de modifications préexistantes, laissées intactes.
