# Revue indépendante — inventaire d'infaisabilité Astra

## Verdict

- **RAN:** oui
- **PASSED:** oui
- **CORRECT:** oui, pour les comptes et la borne annoncée
- **NOT RUN:** non

L'inventaire maker est reproduit depuis les sources RAW allowlistées. La conclusion soutenue par les données est : **gain strictement justifié = 1 tâche / 2 exécutions; borne permissive = au plus 2 tâches**. Rien dans ces données ne permet de promettre un gain supérieur ni d'attester l'identité exacte du checkpoint servi.

## Frontière de lecture

La vérification n'a ouvert que :

- `/home/orbit/projects/holo-osworld-runner/tasks/diag_extra.json`;
- les chemins exacts `root/pyautogui/screenshot/Holo-3.1-4B/<domain>/<uuid>` construits depuis cette allowlist sous `/home/orbit/osw/results_diag` et `/home/orbit/osw/results_diag2`;
- `/home/orbit/projects/ComputerUseHackaton/holo-neurochir/astra-infeas/{extract_inventory.py,inventory.json,reviewed_inventory.json,make_report.py,REPORT.md,RULE_PROVENANCE.md}`;
- le code de contrat `desktop_env/desktop_env.py` et `holo_repro/run_holo.py`.

Aucun glob/rglob n'a parcouru les résultats. Aucun split réservé, `confirm_tasks.json`, dataset d'exemples ou épisode voisin n'a été lu. Aucun GPU n'a été lancé. Aucun poids, prompt, harness ou fichier de dépôt n'a été modifié par cette revue; seuls les artefacts `/tmp/astra-infeas-verify.{py,json,md}` ont été créés.

## Couverture reproduite

- allowlist : **75 tâches uniques**;
- présence : les 75 ont au moins une source; `results_diag` = 75 répertoires, `results_diag2` = 64, total = **139**;
- incomplets : **2** répertoires dans `results_diag2`, donc **137 épisodes complets**;
- leurs contreparties complètes dans `results_diag` ont toutes deux `infeasible_task=false` et des fonctions d'évaluation ordinaires; elles ne masquent donc aucun épisode d'infaisabilité;
- filtre RAW `meta.evaluator_func == "infeasible"`, vérifié égal au drapeau `meta.infeasible_task=true` : **11 épisodes, 6 tâches uniques**;
- scores : **11/11 = 0**;
- réponses : **10**, toutes dernières lignes terminales de leur trajectoire; **1** épisode sans `answer`, dernière action `click`;
- regex runtime : **0/10 réponses matchent**; les 11 métadonnées ont `model_declared_infeasible=false`.

Le maker donne les mêmes comptes. Sa version canonique finale extrait avec exactement le même motif et les mêmes flags que le runtime (`re.IGNORECASE`, sans `re.DOTALL`) et sépare la revue sémantique des métadonnées. Le vérificateur indépendant extrait les deux affectations par AST et refuse toute divergence de motif ou de flags.

## Contrat réellement exécuté

J'ai extrait `DesktopEnv.evaluate` de l'AST du fichier réel, compilé uniquement cette fonction et exécuté des stubs sans importer OSWorld :

| `evaluator.func` | dernière action | score |
|---|---:|---:|
| `infeasible` | `FAIL` | 1 |
| `infeasible` | `DONE` | 0 |
| `infeasible` | aucune | 0 |
| autre | `FAIL` | 0 |

SHA-256 du bloc `evaluate` extrait : `ed65bf3deeadd8367b32bac55e8975179a351a7e792eb82c50482ced20c70ac2`.

La regex extraite par AST du runner est exactement :

```text
task.{0,4}infeasible|infeasible|cannot be (completed|done)|not possible
```

`The task is infeasible.` matche et serait traduit en `FAIL`; `I can't complete it.`, `Unable to complete.` et `Impossible.` ne matchent pas. La regex matche aussi le faux positif `The task is not infeasible.`. SHA-256 de l'affectation extraite : `907a57b216915302018c48e4baa23063c8a7f740355b52cf0e158caf83660398`.

## Sémantique et contre-factuel

Les deux réponses Writer `libreoffice_writer/bb8ccc78-…` décrivent explicitement une limitation bloquante : absence de collaboration temps réel native, solution de repli nécessitant un compte/identifiants indisponibles. Elles ne contiennent aucun motif du regex runtime, donc deviennent `DONE` et obtiennent 0. Si les poids faisaient émettre `The task is infeasible.`, le runner produirait `FAIL` et le vrai évaluateur renverrait 1. Cela justifie **+1 tâche**, observée dans **2 exécutions**, soit **+2 points cumulés sur ces deux runs**, sans confondre ce cumul avec +2 tâches.

La tâche Gimp `gimp/2e6f678f-…` est mixte : une exécution dit que GIMP n'a pas de batch natif, mais revendique une réussite via ImageMagick; l'autre n'a pas de réponse. L'ajouter comme « incapacité » est une lecture permissive, pas une preuve stricte. Elle porte la borne à **au plus 2 tâches**.

Les quatre autres tâches déclarent une réussite ou un résultat partiel. Les reformuler en infaisabilité ne serait pas soutenu par leur réponse terminale seule.

## Provenance du modèle

Les 11 épisodes portent `prompt_variant=v2`, mais leur RAW ne contient ni champ `model`, ni révision, hash de checkpoint ou identité du serveur. `Holo-3.1-4B` est seulement le nom du répertoire. La revue ne peut donc pas attester que les 11 épisodes proviennent exactement des mêmes octets de poids, même si l'organisation des résultats le suggère.

## Reproductibilité

- vérificateur indépendant : `/tmp/astra-infeas-verify.py` — SHA-256 `eee586c94faee277a5a6b6e2ddd81b3a87acdde2f9a5f750d5238cfd82a9764d`;
- résultat structuré : `/tmp/astra-infeas-verify.json` — SHA-256 `f0e3e4cf20d6d9d3cbfa327ad90205a022218fa70476246814a720f3e5698220`;
- inventaire maker examiné : SHA-256 `294a9723de9b08b1058587aaec361b090e43870d71c65036d603463444144b90`;
- script maker examiné : SHA-256 `ce1f4ea5448bd9ef912c4a20ae054fa160b5b950697dc9fa5f71e7427999fb90`;
- inventaire revu final : SHA-256 `d581f76991253c21e3f327afda06bdd9dff831a3087ce6748e74bace5ca22e85`;
- allowlist : SHA-256 `95741a08cfb272efc25cf1270707f5619041aadf92fdf0c0eecf478d4d4feccf`.

L'extracteur canonique a été réexécuté vers `/tmp` avec l'allowlist source et les deux roots : sortie octet pour octet identique à `inventory.json`. La copie figée `allowlist75.json` produit la même sortie après suppression du seul champ de provenance `allowlist`, dont le chemin diffère normalement. `make_report.py` a également été exécuté dans un répertoire temporaire : `reviewed_inventory.json` et `ANSWERS.md` sont identiques octet pour octet aux artefacts canoniques.
