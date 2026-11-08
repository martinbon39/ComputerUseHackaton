# Signal textuel et cohérence d'échantillonnage contre le faux succès (Holo-3.1-4B, OSWorld)
08/11/2026, analyse CPU. Scripts : collect.py et analyze.py. Chiffres complets dans RESULT.json.

## En bref
- **(A) Le texte de l'agent ne bat pas l'index du pas.** Le meilleur détecteur textuel (features simples, surtout la longueur) atteint une AUROC de 0,66 [0,55-0,76], et TF-IDF 0,59 à 0,60. L'index du pas final fait 0,72 [0,61-0,82], et la longueur totale de la réflexion 0,74 [0,64-0,84].
- **Le signal textuel porte sur le type de tâche, pas sur l'épisode.** Dans les 18 tâches mixtes, tous les détecteurs sont au hasard (0,47 à 0,54). Le test de permutation intra-tâche donne p = 0,44.
- **(B) Bras A d'astra-power, k = 4.** Le taux d'answer est de 0,72 sur les fs+ et de 0,94 sur les vrais fini. L'AUROC de (1 − taux) vaut 0,66 [0,53-0,80]. La règle « au moins un tirage ne répond pas answer » donne un TPR de 42 % pour un FPR de 10 %.

## Données
- **(A)** 66 faux succès et 202 vrais succès faisables, sur 90 tâches (dont 18 mixtes). Validation groupée par tâche (leave-one-task-out). IC par bootstrap sur les tâches.
- **(B)** Le fichier runs/A/generations.jsonl d'astra-power : 19 fs+ et 20 vrais fini.

## Réserves
- Les n sont petits.
- Le meilleur des 7 modèles textuels a été choisi après coup, donc il est biaisé vers le haut.
- Il y a un fort confondant domaine/tâche.
- Le résultat de 2606.09863 (des détecteurs TF-IDF qui battent les juges) ne se transpose pas : les notes de Holo sont uniformément affirmatives.
- (B) coûte 4 générations par décision. Ses 39 tâches font aussi partie du corpus de (A).
