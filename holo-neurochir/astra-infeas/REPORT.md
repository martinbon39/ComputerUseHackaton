# Astra-infeas — diagnostic de la déclaration d'infaisabilité

2026-11-08 · décision : piste de reformulation close au premier gate.

**Gain maximal sémantiquement admissible observé : 1 tâche unique, soit 2 épisodes sur deux runs.** Même en ajoutant un cas GIMP ambigu, la borne permissive est de 2 tâches. Le seuil demandé de 3 tâches n'est pas atteint. Ares a reçu le chiffre préliminaire à **02:18:31 UTC** (horodatage de livraison argos, environ 3 minutes après le démarrage) et a confirmé la clôture. Aucun GPU, aucune édition de poids, aucun checkpoint ni upload Modal.

## Périmètre effectivement examiné

- Allowlist fournie par ares : `/home/orbit/projects/holo-osworld-runner/tasks/diag_extra.json`, 75 tâches, annoncée par lui comme disjointe des 45 réservées et du test. Copie figée : `allowlist75.json`, SHA256 `95741a08cfb272efc25cf1270707f5619041aadf92fdf0c0eecf478d4d4feccf`.
- Lecture ciblée par identifiant autorisé, sous `~/osw/results_diag` et `~/osw/results_diag2`, branche `pyautogui/screenshot/Holo-3.1-4B`. Aucune lecture de `confirm_tasks.json`, de `split_test`, ni d'épisodes exclus.
- 75 tâches présentes dans au moins un run ; 139 dossiers d'épisodes présents, dont 2 incomplets signalés dans l'inventaire. 6 tâches infaisables, 11 épisodes infaisables exploitables.
- Le tableau du papier « 9 faux succès infaisables sur 29 » porte sur un autre périmètre, les 120 tâches DIAG. Ce total agrégé a été lu, mais les épisodes exclus de notre allowlist n'ont pas été examinés. Aucun chiffre sémantique ne leur est extrapolé.
- Identité historique : les résultats sont rangés sous `Holo-3.1-4B`. Les métadonnées d'épisode n'attestent pas cryptographiquement la révision des poids servis. La révision demandée est `8c88265a5a159bfd1492db9243733dd2e6e04a6e` ; aucune nouvelle inférence n'a été effectuée.

## Résultats et contrefactuel

| Mesure | `results_diag` | `results_diag2` | Total |
|---|---:|---:|---:|
| Épisodes infaisables examinés | 6 | 5 | 11 |
| Score enregistré égal à 0 | 6 | 5 | 11 |
| Réponse finale `answer` | 6 | 4 | 10 |
| Réponses reconnues par la regex du runner | 0 | 0 | 0 |
| Réponses reconnaissant une incapacité sans match | 1 | 1 | 2 |
| Réponses prétendant avoir réussi | 5 | 3 | 8 |
| Aucun `answer` final | 0 | 1 | 1 |

Les deux réponses d'incapacité concernent **la même tâche Writer**. Remplacer leur formulation par « The task is infeasible. » aurait fait produire `FAIL` au runner et donné le score 1, sans changer la conclusion sémantique de ces réponses. Cela représente une tâche récupérable, et non deux tâches indépendantes. Ce contrefactuel déterministe du contrat n'est pas une amélioration mesurée d'un modèle édité.

Remplacer arbitrairement les 10 réponses par une déclaration d'impossibilité donnerait mécaniquement 10 scores positifs, couvrant 6 tâches. Cette borne artificielle est **inadmissible pour la piste demandée** : 8 de ces réponses revendiquent une réussite. Leur réécriture changerait la décision du modèle.

| Tâche | Épisodes / réponses | Conclusion effectivement exprimée | Admissibilité |
|---|---|---|---|
| `chrome/480bcfea-d68f-4aaa-a0a9-2589ef319381` | 2 / 2 | Affirme avoir désactivé la nouvelle interface en changeant le thème | Non : succès revendiqué |
| `gimp/2e6f678f-472d-4c55-99cc-8e7c5c402a71` | 2 / 1 | Dit que GIMP n'a pas de traitement batch natif, puis revendique un traitement réussi via ImageMagick ; second run sans answer | Cas mixte, exclu du gain strict |
| `gimp/8ea73f6f-9689-42ad-8c60-195bbf06a7ba` | 2 / 2 | Affirme avoir augmenté la résolution en réduisant la taille du fichier | Non : succès revendiqué |
| `gimp/e19bd559-633b-4b02-940f-d946248f088e` | 2 / 2 | Affirme avoir assombri et enregistré la photo | Non : succès revendiqué |
| `libreoffice_writer/bb8ccc78-479f-4a2f-a71e-d565e439436b` | 2 / 2 | Explique l'absence de collaboration simultanée native et l'impossibilité de terminer avec les accès disponibles | Oui : 1 tâche unique |
| `os/fe41f596-a71b-4c2f-9b2f-9dcd40b568c3` | 1 / 1 | Affirme afficher le pourcentage de batterie après une commande gsettings | Non : succès revendiqué |

Les textes complets de chaque `answer`, leurs étapes, scores, fichiers sources et rédactions nécessaires sont conservés dans `inventory.json` et `ANSWERS.md`. Une adresse électronique présente dans une réponse Writer a été remplacée par `[REDACTED_EMAIL]` conformément à la consigne ; les sources restent intactes.

## Contrat exact et provenance

Le runner de reproduction RealtimeGUI utilise :

```python
re.compile(r"task.{0,4}infeasible|infeasible|cannot be (completed|done)|not possible", re.IGNORECASE)
```

Il applique `.search(answer)` à la réponse finale : match → `env.step("FAIL")`, absence de match → `env.step("DONE")`. Sans answer, il n'ajoute aucune de ces actions. Cette regex est identique au HEAD `a763361f9fffad5fcbbdb16bdb51ea3ff667c183` de [`1azybug/RealtimeGUI`](https://github.com/1azybug/RealtimeGUI/blob/a763361f9fffad5fcbbdb16bdb51ea3ff667c183/Env/OSWorld/holo_repro/run_holo.py#L65-L67). Le seul diff local de ce fichier concerne le choix Docker/AWS ; notre travail ne l'a pas modifié. La présence upstream ne prouve pas à elle seule une affiliation officielle à Hcompany.

L'évaluateur OSWorld natif n'utilise **aucune regex de texte** : si `evaluator['func'] == 'infeasible'`, la dernière action doit être `FAIL` (chaîne ou dictionnaire `action_type`) pour obtenir 1. Sinon il renvoie 0. Pour une tâche faisable, un dernier `FAIL` vaut 0. Le dépôt officiel contient également un adaptateur Surfer-H avec une regex **plus étroite**, `task.{0,4}infeasible`, insensible à la casse. Voir [adaptateur officiel Surfer-H](https://github.com/xlang-ai/OSWorld/blob/fa42911b85be0efe4821ab228b17fc595eea9ec6/mm_agents/surferH/surfer_agent.py#L51-L61) et [évaluateur officiel](https://github.com/xlang-ai/OSWorld/blob/8903ebeb0efdf74331bd7dc37ed91ccbbff22317/desktop_env/desktop_env.py#L533-L555).

Une cible compatible avec les deux adaptateurs serait **« The task is infeasible. »**. « infeasible » seul ou « cannot be completed » passent le runner RealtimeGUI, mais ne satisfont pas la regex étroite de Surfer-H. Ne pas appeler ces conventions interchangeables, ni attribuer une regex à l'évaluateur natif.

La piste proposée corrigerait la formulation d'une déclaration d'infaisabilité : elle exploiterait donc une reconnaissance lexicale de l'adaptateur. Elle n'est défendable que sous un contrat officiel établi et lorsque le modèle a réellement conclu à l'infaisabilité. Dans l'interprétation littérale « regex de l'évaluateur officiel », cette prémisse est fausse ; dans l'interprétation « convention publiée de l'adaptateur officiel Surfer-H », la phrase canonique ci-dessus convient. Le gate de volume échoue dans les deux cas.

## Décision et limites

La majorité observée des réponses à ces tâches infaisables est un faux succès sémantique : **8 answers sur 10 prétendent le succès**. Ce n'est pas principalement un défaut de formulation. Le cas GIMP batch signale une limitation native mais revendique une réussite par une autre application ; le compter comme conclusion d'infaisabilité serait une interprétation permissive, insuffisante même alors pour atteindre 3 tâches.

Étapes conditionnelles 2 et 3 : **NOT RUN — gate ≥3 tâches non satisfait**. Aucun gradient, LoRA, prompt, harnais, poids, serveur, checkpoint ou déploiement n'a été changé. Aucune comparaison k=8 ni conservation des réponses faisables après édition n'est revendiquée. La réserve de confirmation et le test restent hors périmètre.

Vérification indépendante : `VERIFY.md` et ses preuves CPU, avec le détail du contrat dans `RULE_PROVENANCE.md`. Les artefacts sont copiés dans `/workspace/astra/astra-infeas/`. Le checkout partagé était sale avant le travail et empêchait `git pull --rebase` ; les modifications préexistantes sont conservées.
