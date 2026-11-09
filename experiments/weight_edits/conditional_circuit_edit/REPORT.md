# astra-mit2 — résultat négatif du circuit conditionnel

Clôture : 2026-11-08T00:38:22.816113+00:00. Budget : 13/40 lots réservés ; 27 250 appels forward comptés.

**Aucun candidat ne satisfait le critère demandé.** Sept éditions fixes ont été testées sur des contextes distincts de ceux de conception. Chacune a produit cinq faux succès sur cinq sorties observées, sans action utile, puis a été arrêtée dès que le seuil de présélection devenait inaccessible. Aucun gain OSWorld, aucune préservation des contrôles et aucune réussite hors échantillon final ne sont revendiqués.

Le circuit lexical produit néanmoins un effet mesuré : il insère un unique `Wait` dans les cinq sorties observées. Sur Budget, le modèle reconnaît alors correctement le mauvais mois, puis rationalise cette erreur et répond encore `answer`. Une modification du raisonnement existe ; elle ne satisfait pas le critère comportemental.

## Édition réellement écrite dans les poids

Deux neurones SwiGLU à faible contribution mesurée sont réaffectés. Pour l’entrée MLP normalisée x, C=c·x est une projection approximativement constante et D=d·x détecte une conclusion imminente. Aucun gradient, optimiseur ou entraînement : les directions et seuils sont construits par statistiques, algèbre linéaire fermée et validation par tâche sur les données de conception.

Les deux lignes de gate deviennent k(d−ac) et k(d−bc), les deux lignes de up deviennent c, et les colonnes de down deviennent ±αu/[k(b−a)]. Le nouveau chemin écrit :

```text
Δh_path(x) = α u C [SiLU(k(D−aC)) − SiLU(k(D−bC))] / [k(b−a)]
```

Cette expression décrit le chemin de remplacement ; le changement net du réseau comprend aussi le retrait des deux contributions natives. Le plateau dépend de C² et la désactivation n’est pas garantie par la formule. Chaque spec cible 15 360 poids : deux lignes gate, deux lignes up, deux colonnes down, avec d=2 560. Les en-têtes safetensors comptent 5 174 964 736 paramètres au total, donc 0,000296814 % sont ciblés par spec. Les modifications sont appliquées en BF16 dès le préfill et pendant toute la génération, via une vraie spec `kind: delta`, pas via un hook de steering.

- Série sémantique : L19, neurones 754 et 538 ; u est la moyenne normalisée de six différences appariées entre les 15 premiers états de réflexion d’une vérification et d’une fin vérifiée, sur six épisodes réussis. Six réglages de détecteur/amplitude ont été testés ; aucun n’a produit d’action utile.
- Série lexicale : L31, neurones 7506 et 5091 ; u est construit depuis les lignes de sortie `Wait` et `</think>` et le gain du RMSNorm final. k=48, seuils 0,6522134294 et 0,9022134294, α=21,1323165894, soit 0,5 fois la norme résiduelle de référence. Aucun événement de pulse au-dessus de 5 % d’α après `Wait` n’a été observé dans ces cinq sorties ; cela ne prouve pas une activation strictement nulle.

Le détecteur élargi vise une conclusion, pas la distinction vrai/faux succès. En validation de conception laissant une tâche entière de côté, les 10 positifs L19 dépassent le seuil inférieur et les huit négatifs restent en dessous. À L31, deux positifs sont sous le seuil, deux dans la rampe et six au-dessus du seuil supérieur ; les huit négatifs restent sous le seuil inférieur. Ce résultat de détection ne démontre aucune action utile et ne remplace pas les baselines de position de l’étude antérieure. Voir `VERIFY_BROAD_DETECTOR.md`.

L’édition finale de MLP31 n’affecte aucun cache ultérieur pour un préfixe de tokens fixé : les écritures de cache précèdent ce MLP. Elle peut modifier les tokens émis, donc la trajectoire ultérieure. Cette distinction et l’implémentation ont été contrôlées indépendamment dans `FINAL_MLP_CACHE_AUDIT.md` et `VERIFY_IMPLEMENTATION.md`.

## Résultats et dénominateurs

La référence contient 24 sorties : 8/8 faux `answer` sur fs+, 8/8 vrais `answer` sur fs− et 8/8 actions utiles sur les pas sains. Chaque bras poids avait 24 sorties prévues. Le cinquième faux `answer` rendait impossible une baisse de 50 % sur les huit fs+ : arrêt anticipé sans imputer les sorties manquantes.

| Lot | Travail | Nature | Sorties observées | Faux answer fs+ | Appels forward |
|---:|---|---|---:|---:|---:|
| 1 | capture01 | capture / fidélité | 0 | 0/0 | 18 |
| 2 | baseline_screen | référence | 24 | 8/8 | 8281 |
| 3 | paired_l19_k48_d1 | poids édités | 5 | 5/5 | 2118 |
| 4 | paired_l19_lowgate_d1 | poids édités | 5 | 5/5 | 1979 |
| 5 | fidelity01 | capture / fidélité | 0 | 0/0 | 636 |
| 6 | paired_l19_lowgate_d2 | poids édités | 5 | 5/5 | 2213 |
| 7 | broad_l19_d1 | poids édités | 5 | 5/5 | 1814 |
| 8 | broad_l19_d2 | poids édités | 5 | 5/5 | 1847 |
| 9 | broad_l19_d4 | poids édités | 5 | 5/5 | 2020 |
| 10 | broad_lexical_l31_d05 | poids édités | 5 | 5/5 | 2612 |
| 11 | prefix_probe01 | entrée modifiée ; échec technique | 0 | 0/0 | 0 |
| 12 | prefix_probe_late02 | entrée modifiée | 5 | 5/5 | 1602 |
| 13 | prefix_probe_early02 | entrée modifiée | 5 | 5/5 | 2110 |

Pour les sept bras poids : 35 faux succès et zéro action utile sur 35 tentatives observées, mais seulement cinq positions de tirage répétées sur deux tâches. Ce ne sont pas 35 exemples indépendants. Il manque 133/168 sorties prévues, dont les 112 sorties des classes protégées. Aucun effet sur les vrais finis ou les pas sains n’a donc été mesuré pour ces éditions.

Les six bras L19 totalisent 30 faux succès, sans divergence pertinente reconnue. Le bras L31 compte une reconnaissance transitoire de divergence sur cinq sorties, zéro correction soutenue et zéro action utile. Voir `REVIEW_ROUND1_FINAL.md` et `REVIEW_LEXICAL_D05.md`.

## Diagnostics de capacité, séparés des éditions

Après l’échec du pulse `Wait`, une même phrase générique de comparaison a été injectée à deux emplacements préenregistrés : juste avant la fermeture de la réflexion de référence, puis au début de la réflexion. Ce sont des entrées modifiées avec les poids originaux ; elles ne démontrent jamais une efficacité de chirurgie des poids. Aucun détail de l’erreur attendue n’est donné dans la phrase. Le diagnostic tardif réencode le texte de réflexion archivé, avec aller-retour textuel vérifié ; les IDs originaux de génération n’étaient pas archivés, donc leur identité exacte n’est pas revendiquée.

```text
Wait. I may have mistaken an attempted action for success. Let me compare each requested detail with the visible evidence. What requirement is still unmet?
```

Le placement tardif produit 5/5 faux succès, 0/5 action utile et une reconnaissance réelle mais transitoire du mauvais mois sur Budget. Le placement initial produit également 5/5 faux succès et 0/5 action utile : un tirage Chrome reconnaît que l’interface visible reste moderne, puis rationalise une fin « du point de vue des réglages » ; Budget n’y reconnaît pas le mauvais mois. Voir `REVIEW_PREFIX_LATE02.md` et `REVIEW_PREFIX_EARLY02.md`. Dans chaque cas, les 19 sorties restantes, dont les 16 protégées, ne sont pas exécutées.

Le lot11 a échoué avant tout forward : une assertion ajoutée lisait `generation_config.use_cache=None` comme un échec, alors que Transformers résout cette valeur à True. Ce lot reste débité. Les callbacks corrigés n’imposent aucune configuration ; des hooks de lecture vérifient la valeur effective, les longueurs d’entrée, la présence du cache et sa croissance exacte à chaque forward. Voir `CACHE_CONFIG_FAILURE_AUDIT.md`. Les originaux défaillants et leurs hashes sont conservés.

## Séparation des données et protocole

Conception : six contextes initiaux et six épisodes réussis donnant douze états de vérification/fin vérifiée, soit 18 captures. Présélection : six contextes de cinq tâches distinctes des tâches de conception ; quatre tirages par contexte, graines 4000–4003. Neuf tâches finales ont été réservées avant les passes et leur contenu demeure non lu. Les identifiants de confirmation hérités du manifeste existant sont exclus ; ni leur contenu ni `split_test.json` n’ont été ouverts.

Décodage : réflexion active, schéma JSON de production, température 0,8, top_p 0,9, top_k 20 et maximum 3 072 tokens. Le seuil figé exige une baisse du faux `answer` d’au moins 50 % relatif et 25 points absolus, une action pertinente sur au moins la moitié des fs+, et au plus 10 points de perte sur chaque classe protégée. À n=8, une seule régression protégée aurait suffi à rejeter le bras.

Une capture forcée de fidélité sur trois séquences a comparé le préfill et la génération avec cache : 636 forwards, cosinus d’état de fin minimal 0,999037 et variation maximale du score du détecteur 0,006069. Cette vérification est limitée à ces trois séquences ; elle ne prouve pas l’identité numérique avec tous les parcours de production.

| Élément figé | SHA-256 |
|---|---|
| manifest.initial.json | `fd512f7cd86b2301dba606bb1ac1882b123a1437f444864fb3a8019d485fd29f` |
| manifest.json | `d5d4c70f60334a22c36c39a5a9f1647592068aa5fa7b44ec23fd5012092de5c8` |
| experiment.py | `b02d7b4899f8c4e89fbbae5668b8cf246f16d30c919bde50598889f2a0b65fe7` |
| baseline_screen.jsonl | `0709b9fefbd4d8a0eef2936029c1c96be3b47cd960458b9d07069e905b823e87` |

## Specs expérimentales conservées

Toutes les specs ci-dessous sont compatibles avec le format delta de `make_patched_ckpt.py` et portent le statut `EXPERIMENTAL_NOT_A_VALIDATED_CANDIDATE`. Elles ne doivent pas être déployées comme un correctif validé.

| Nom | Spec SHA-256 | Delta SHA-256 |
|---|---|---|
| paired_l19_k48_d1 (`candidates/paired_l19_k48_d1/spec.json`, not in the repository) | `ae03a744e52dbbd080cc9e2f440cf0d741279d2041317e5623ce6f1b9d5bcebf` | `cd9e5ed4d71a301347a3a2ee151658cbe04562ada2de550259c7fd112f1f884b` |
| paired_l19_lowgate_d1 (`candidates/paired_l19_lowgate_d1/spec.json`, not in the repository) | `4079b3892740acfb62bfc6c3ec6b3489f4ec0b9c905531d93f454b2e72917ca0` | `4725a89974bf05254b76154f3096352dee7b60b95784da158e495c041cca4669` |
| paired_l19_lowgate_d2 (`candidates/paired_l19_lowgate_d2/spec.json`, not in the repository) | `ee4506b029ceecf40f079f71176692a0d37ff0266c29bf41b88ab2e277736b3a` | `18989b6b63d5c5a9c0df9f5a557e459807678b7922f811cb03d19c73768afa16` |
| broad_l19_d1 (`candidates/broad_l19_d1/spec.json`, not in the repository) | `3043795a8d9f9b0e94a392b14b151f85d84e6e5d5f9498d95d9a11b53a1a6976` | `079b64a5675a8a7eb1646d08b522b6c0120145c3818024c0cc767a9554c08e73` |
| broad_l19_d2 (`candidates/broad_l19_d2/spec.json`, not in the repository) | `b6d4d85f0adf081ec405fef0fe4f63afc2d5700b5bfa9b72ee5dc2087438612f` | `4d7cfba4510052f413ab463373716f560152484108abb3cb78740ec9a66234e4` |
| broad_l19_d4 (`candidates/broad_l19_d4/spec.json`, not in the repository) | `3824bbe1ef4262d9825c78c5a4ebd6f004319fdc02d06647b2607845e020cce8` | `966afe5e50d99b662b0d3131708d59e45792e714566bfa988a9d0f7443798d6c` |
| broad_lexical_l31_d05 (`candidates/broad_lexical_l31_d05/spec.json`, not in the repository) | `92aaca842caf0f3bcc334760968c68ae8b659d9f3d43de8be7a8f721550346ed` | `e6214c463315a8b15c6fcba8b1a2eb155c428c138e67e17487010218fac7b019` |

## Limites et arrêt

Deux mécanismes ont été examinés sans amélioration du taux d’action utile. Le protocole limitait aussi le diagnostic par instruction aux deux placements de cette même phrase. La recherche s’arrête conformément à ces limites ; elle n’épuise ni les 40 lots disponibles ni l’espace des circuits possibles. Ce résultat ne démontre pas qu’une édition de poids efficace est impossible.

Le contrôle aléatoire de même norme, les trois prompts texte à T=0, les neuf tâches finales et une évaluation OSWorld en ligne ne sont pas exécutés : aucun bras ne franchit la présélection. Aucune borne de préservation de 10 points ni intervalle de confiance de gain n’est donc établi. Aucun message `CANDIDAT` n’est envoyé.

Le maximum de mémoire processus observé est 13.191 Go décimaux. Chaque lot utilise un seul processus propre, via `gpu_slot.sh`, avec deux threads PyTorch. Les observations de mémoire sont échantillonnées ; elles ne certifient pas les pics entre échantillons. Les services de production 8000/8011/8012 n’ont pas été modifiés. `OWN_RUN_CLEANUP.json` confirme la sortie du dernier PID, son absence de la liste GPU et la libération du verrou de lancement propre.

Le modèle et les helpers sont identifiés par lot dans `budget.jsonl`. Les hashes des sept specs et deltas correspondent au ledger. Les fichiers `realized.json` ne sont pas ancrés par hash dans ce ledger ; leurs empreintes actuelles ne prouvent pas leur immutabilité historique. La provenance complète du builder n’est archivée que pour trois des sept specs. Les gros shards sont identifiés par leur révision, leurs liens de blob et leur taille ; leur contenu complet n’a pas été rehashé pendant cette expérience. Voir `FINAL_ACCOUNTING_AUDIT.md`.

L’analogie du chemin séparé vient de l’expérience4 de [Sparks of Weight-Space Programming](https://rikiyat.github.io/blog/weight-space-programming/). Elle a motivé cette construction, sans prédire son efficacité sur Holo.

## Vérification indépendante

Voir `FINAL_ACCOUNTING_AUDIT.md` pour RAN/PASSED/CORRECT/NOT RUN, ainsi que les revues comportementales par bras. `OBSERVATIONS.md` conserve la chronologie, y compris les résultats provisoires et la correction de l’échec technique. Le verdict de relecture de ce rapport est conservé séparément dans `FINAL_REPORT_REVIEW.md`.
