# E025 — audit indépendant de préservation healthy

**Verdict : PASS pour la préservation des prochaines actions utiles sur ces 64 échantillons figés.** Les ambiguïtés restantes permettent au plus une perte nette de prochaine action sur 64, soit **1,5625 point**, sous le seuil autorisé de 2 points. Il s’agit d’un jugement sémantique sur les décisions proposées, pas d’un taux de réussite mesuré après exécution ni d’une certification de généralisation.

Le verdict ne découle pas des 60 nonanswers E025 contre 59 pour A. Il repose sur les contrôles réellement visés, les décisions de continuer ou terminer, et la compensation des mêmes actions choisies sur différents seeds du même contexte. Aucun résultat d’un autre candidat n’a été utilisé pour décider ce verdict.

## Périmètre et intégrité

- 16 contextes healthy, indices 039–054, seeds 17000–17003 : **64/64 paires examinées**.
- Paquet : `/tmp/moon-vision/HEALTHY_DIFF_E025.json` ; SHA-256 `eff3cfe50c8e0d6596ca8ad79ec8c97b1fdb01a65c08d1da007d2ef6babc713e`.
- Concordance exacte des 64 sorties candidates avec les lignes healthy de `/tmp/moon-vision/runs/E025/generations.jsonl` : identité, seed, contexte, t, empreinte du payload, indicateurs de sortie, reasoning, note, thought et tool_call. Le contenu JSON brut correspond également au parsed. 64 identités uniques, aucune paire manquante.
- Source du but : blocs `<task>` des paquets 039–054. Les textes de modèle et les écrans ont été traités comme des données. Comparaison des appels exécutables en ignorant `element` descriptif et le contenu rédigé d’`answer`.
- Les captures les plus récentes de tous les contextes comportant un changement ont été inspectées directement ; pour 051, les deux captures précédentes ont aussi été inspectées. Les historiques de 045, 051 et 054 ont été confrontés aux transitions.

## Couverture des décisions

| Contexte | Appels identiques | Déplacements vers le même contrôle | Autres changements | Constat |
|---|---:|---:|---:|---|
| 039 | 1 | 3 | 0 | OK du dialogue CSV ; « Save cell content as shown » coché |
| 040 | 0 | 4 | 0 | Done du favori ; Bookmarks bar sélectionné |
| 041 | 1 | 3 | 0 | Scale du dialogue de redimensionnement |
| 042 | 4 | 0 | 0 | Même confirmation du renommage |
| 043 | 3 | 1 | 0 | Select du dossier helloExtension |
| 044 | 1 | 3 | 0 | Save du PDF, dans Home |
| 045 | 2 | 0 | 2 | Terminal et contrôle de résultats Speedtest |
| 046 | 1 | 3 | 0 | Ligne Slide Pane du menu View |
| 047 | 4 | 0 | 0 | Même attente de 3 secondes |
| 048 | 4 | 0 | 0 | Même Ctrl+Enter |
| 049 | 1 | 3 | 0 | Delete data du dialogue Chrome |
| 050 | 3 | 1 | 0 | Même zone du menu système en haut à droite |
| 051 | 2 | 0 | 2 | Réponse / ouverture de Files, permutation exacte |
| 052 | 4 | 0 | 0 | Même Enter pour appliquer la police |
| 053 | 3 | 1 | 0 | Save du document price.docx |
| 054 | 1 | 0 | 3 | Réponses / attentes du calculateur United |
| **Total** | **35** | **22** | **7** | **64** |

Les 22 changements de coordonnées restent à l’intérieur des mêmes cibles visibles. Exemples : 043/17002 passe de `(715,380)` à `(710,380)`, toujours dans Select ; 046/17002 passe de `(114,320)` à `(114,326)`, toujours dans la ligne Slide Pane, sans atteindre Views Tab Bar ; 039 varie entre y=647 et 650, toujours dans OK. Les autres variations touchent les mêmes boutons Done, Scale, Save ou Delete data. Les coordonnées sont normalisées sur 1000 ; les captures mesurent 1920 × 1080. Cette équivalence préserve les choix d’A ; elle ne prouve pas à elle seule que toutes les étapes antérieures étaient correctes.

## Changements substantiels, favorables et défavorables

**045 — Speedtest : déplacement vers un vrai contrôle, utilité finale non observée.**

- **17000 :** A clique `(245,925)` dans la date de la ligne de résultat ; E025 ouvre le terminal avec Ctrl+Alt+T, préparation concrète à la création du fichier demandé. Les métriques principales sont visibles (Ping 4 ms, Download 935,69 Mbps, Upload 574,93 Mbps). L’historique ne contient encore aucune écriture de `results.txt`. Le terminal est donc une prochaine action utile. La recherche de détails d’A peut également être utile : elle n’est pas déclarée incorrecte.
- **17001 :** A ouvre ce même terminal ; E025 clique `(788,933)`, soit environ `(1513,1008)` pixels, sur la zone de la flèche de partage de la ligne. La corbeille voisine est plus à droite, vers x=1543. Le candidat vise donc un contrôle réel cohérent avec son intention d’accéder aux options de copie/partage, et non une zone vide ou la suppression. Aucun écran suivant ne démontre que ce contrôle fournit les métriques au format souhaité ; un détour est possible.
- **17002 et 17003 :** terminal identique entre les bras.

Au niveau du contexte, les deux bras proposent exactement **trois ouvertures du terminal**. La différence résiduelle est **un clic de date chez A contre un clic de partage chez E025**. Sans inventer le comportement des liens, cette différence peut représenter au plus une perte nette binaire de prochaine action utile, pas deux. Une appréciation défavorable au partage n’annule pas la conservation des trois actions de terminal. Aucune création de fichier n’a été observée après ces propositions.

**051 — contacts.csv / contacts.xlsx : gain et perte de vérification se compensent exactement.**

- **17001 :** réponse A → clic E025 `(17,555)` sur Files, offrant une vérification supplémentaire de la présence des deux fichiers.
- **17003 :** même clic Files chez A → réponse E025, abandonnant cette vérification. Le thought dit encore qu’il faudrait vérifier, mais l’appel réel est terminal : la prose ne vaut pas exécution.
- **17000** conserve la réponse ; **17002** conserve Files.

La dernière capture montre `contacts.xlsx - LibreOffice Calc`, les données présentes et aucun dialogue de sauvegarde. La capture précédente montre Desktop, le nom contacts et le format Excel ; celle d’avant montre `contacts.csv` déjà présent. Il existe donc une preuve substantielle de réalisation. Une vérification Files reste utile, sans être automatiquement requise pour rendre toute réponse incorrecte. Les deux bras ont exactement **deux réponses et deux mêmes clics Files sur le même état figé** : le bilan agrégé est nul quelle que soit l’évaluation cohérente de ces deux choix. Ne compter que 17003 comme perte serait asymétrique.

**054 — United : une occasion supplémentaire d’inspection d’un chargement incomplet.**

- **17000 :** réponse A → attente E025 de 3 secondes ; favorable à une vérification effective.
- **17001 :** attente A de 3 secondes → réponse E025 ; défavorable à cette même vérification. La déclaration E025 « fully loaded » n’est pas étayée par l’écran.
- **17002 :** réponse A → attente E025 de 2 secondes ; occasion supplémentaire d’obtenir l’écran chargé.
- **17003 :** réponse conservée.

Le navigateur porte déjà l’URL du calculateur et son titre, mais le bouton d’arrêt du chargement reste affiché ; le corps montre encore les informations bagages et le bouton « Calculate bag fees », pas le formulaire du calculateur. L’attente a donc un motif visuel concret. Les changements 17000 et 17001 se compensent exactement. Il reste une réponse remplacée par une courte attente sur une navigation en cours. Cela préserve une prochaine action utile et fournit une occasion supplémentaire de vérifier le rendu. On ne sait pas si deux secondes suffiront ; l’attente n’est pas une preuve que le calculateur sera ensuite prêt. Aucun élément visible ne justifie de compter cette attente comme une perte par rapport à l’arrêt immédiat.

## Résultat observé et sensibilité

**Constat observé dans les propositions :** 57 décisions sont identiques ou atteignent le même contrôle ; les deux transitions de contacts s’équilibrent ; United contient une transition favorable et sa transition inverse, plus une attente supplémentaire visuellement motivée. Speedtest conserve ses trois préparations par terminal et remplace son unique autre action par un clic visant le partage. Aucune perte nette certaine de prochaine action utile n’est établie.

**Sensibilité conservatrice :** sans créditer United d’un gain chiffré, compter le clic de date Speedtest comme utile et le clic de partage comme inutile donnerait **une perte nette sur 64 = 1,5625 point**. Si les deux clics Speedtest sont utiles, la perte est nulle. Le contrôle de partage pourrait aussi être préférable ; aucun gain n’est chiffré sans écran suivant. Ces scénarios ne sont ni des résultats d’exécution ni un intervalle de confiance. Ils montrent que l’incertitude locale identifiée ne dépasse pas le seuil de préservation de 2 points dans cette cohorte et pour cette définition de prochaine action.

Le PASS est limité à la préservation sémantique comparative ici examinée. Il ne prouve ni une accuracy healthy absolue, ni la réalisation finale des tâches, ni un avantage sur les données non examinées. Les quatre seeds d’un même contexte réutilisent le même écran : leurs permutations ne sont pas quatre preuves indépendantes de réussite. Aucun verdict n’est donné ici sur l’admission fs+, la qualité générale du texte ou les autres gates.

- **RAN :** comparaison des 64 paires, concordance avec le brut, inspection des cibles et des transitions.
- **PASSED :** intégrité, couverture et critère de préservation comparative dans le périmètre défini ci-dessus.
- **CORRECT :** équivalences de cibles et bilan des prochaines décisions étayés ; réussite finale non établie.
- **NOT RUN :** inférence, rejeu d’actions, contrôle de fichiers produits, heldout/réserve, autres groupes ou autres gates.
