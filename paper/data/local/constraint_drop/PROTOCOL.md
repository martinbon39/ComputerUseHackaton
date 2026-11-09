# constraint_drop : l'agent nomme-t-il une exigence non remplie juste avant de dire « done » ?
Pré-enregistré le 2026-11-08 vers 11:55 UTC, commité AVANT toute annotation. Auteur : session constraint-drop (flotte argos).

## Question
Quand Holo-3.1-4B termine par `answer`, écrit-il, dans ses derniers pas, qu'une exigence de l'instruction n'est PAS
encore satisfaite (ou doit encore être faite ou corrigée) ? Si oui plus souvent chez les faux succès que chez les vrais,
c'est un « abandon de contrainte connue ».

## Données (aucun GPU ni VM)
- Bras `modal` : `~/osw/results_test_gh_orig_modal_test` (original servi par Modal, split test, 120 tâches).
- Bras `pod` : `~/osw/results_test_gh_orig` (original sur pod, même split).
- Inclusion : dernier pas de `traj.jsonl` avec `tool_name == "answer"`. FS = `result.txt` = 0, TS = `result.txt` = 1.
  Scores partiels (0 < s < 1) exclus. Décompte attendu avant annotation : FS 29 (pod) + 27 (modal) = 56 ; TS 68 + 65 = 133.
- Texte montré à l'annotateur : l'instruction de la tâche (`evaluation_examples/examples/<domaine>/<id>.json`, champ
  `instruction`), puis les champs `note` et `thought` des 3 DERNIERS pas (dont le pas `answer`), dans l'ordre. Rien d'autre :
  ni score, ni bras, ni domaine, ni id, ni contenu de l'answer, ni champ `reasoning`.

## Annotation
- `claude -p --model sonnet`, à l'aveugle, une seule question, prompt figé dans `annotate.py` (constante `PROMPT`) :
  « Dans ce texte écrit par l'agent juste avant de déclarer la tâche finie, l'agent mentionne-t-il explicitement qu'une
  exigence de l'instruction n'est PAS encore satisfaite (ou doit encore être faite ou corrigée) ? yes / no + la citation exacte ».
  Sortie JSON `{"label": "yes"|"no", "quote": "..."}`.
- Ordre mélangé (`random.Random(20261108)`), au plus 3 appels simultanés. Réponse illisible : 1 nouvel essai, sinon
  `unparseable`, exclu et compté dans le rapport.
- Contrôle automatique : la citation d'un « yes » doit être une sous-chaîne (espaces normalisés) du texte montré ; le taux est rapporté.
- Sortie : `annotations.jsonl` (une ligne par épisode : id, bras, classe, label, citation, texte montré).

## Analyse (fixée avant les données)
- Métrique principale : part de « yes » chez les FS contre chez les TS, épisodes des deux bras poolés.
- Test : Fisher exact unilatéral (alternative : FS > TS), seuil 0,05. IC de Wilson 95 % par classe ; différence avec IC de
  Newcombe (méthode 10).
- H1 tient si p < 0,05 ET la borne basse de l'IC de la différence > 0. Sinon : pas de preuve d'abandon de contrainte connue.
- Sensibilité (descriptive, sans test de décision) : chaque bras seul ; épisodes où l'agent n'a PAS déclaré l'infaisabilité
  (`meta.json: model_declared_infeasible == false`) ; une même tâche apparaît dans les 2 bras, donc les épisodes ne sont
  pas indépendants : bootstrap par tâche (2000 tirages, graine 20261108) de la différence.
- Conséquence pratique, « self-check guard » gratuit : il bloque le done quand label = yes. Rappel = yes/FS (détection),
  faux rejets = yes/TS, précision = FS-yes / tous les yes. Comparé au Guard externe (détection 45/66 = 68 %, faux rejets
  21/202 = 10 %, mesurés sur 268 écrans finaux d'un autre ensemble : comparaison indicative, pas appariée).

## Vérification
- Un sous-agent relit 20 annotations tirées au hasard (graine 20261108) et donne son propre label à l'aveugle du nôtre
  et du score ; accord brut rapporté.
- Un second sous-agent recalcule toutes les statistiques depuis `annotations.jsonl` brut.

## Échéance
Résultat attendu à 12:35 UTC. Si l'annotation n'est pas finie à temps, on rapporte ce qui est annoté, marqué partiel.
