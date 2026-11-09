# Relecture adversariale (agent à contexte frais, 08/11 vers 03:00 UTC)

Rapport reçu par ares et recopié ici en version condensée.
- **[V]** : vérifié dans les fichiers par le relecteur.
- **[S]** : soupçon non vérifié.

## Problèmes classés par gravité

**1. La métrique vise parfois la mauvaise action [V].**
- `paper/generated/num_osw_diag.tex` : 9 faux succès sur 29 du diag sont des tâches infaisables.
- Dans le harness, le refus passe par `answer` suivi d'un texte reconnu par une regex.
- Le contexte fs+ `chrome/480bcfea@4` est infaisable (`astra-free/REPORT.md:28`) et figure dans les jeux d'astra-free, d'astra-merge et du pilote 4b. Sur ce contexte, la bonne action EST answer.
- Les contextes « sains » d'astra-free sont au pas 0, alors que le papier dit « mid-episode ».

**2. Le plafond « réparation » n'a jamais été mesuré.**
- Depuis les états fs+, on n'a pas compté combien de tâches réussissent quand answer est interdit.
- Si ce nombre est proche de 0, la cible « faux succès » ne peut rien rapporter.

**3. La marge et l'« attracteur » sont mal interprétés [V].**
- Le schéma suit l'ordre note → thought → tool_call (`holo_agent/tools.py:145-158`).
- La marge est mesurée en teacher forcing au token du nom d'outil, après un thought qui dit déjà « task completed ». C'est la confiance à recopier une décision déjà prise.
- « 2/51 identiques » ne prouve rien sans une perturbation aléatoire de même norme.
- H5 est circulaire : `</think>` est absent des 6 prompts.

**4. Le test de plafond est confondu [V].**
- Donneur = pas précédent : autre écran, autre réflexion, autre thought, autre position.
- Il ne porte que sur 1 contexte.
- Un vrai fini bascule aussi. Le test localise donc la construction de l'identité du prochain token.

**5. Le split TEST a déjà été consommé [V].**
- Lus : orig (120 tâches, 72,1), expo125 (120 tâches, 70,3 ; discordantes 12 contre 11), prompt partiel (38 tâches).
- Nommage piégeux : `results_val_patched_eager_m40` contient en réalité Holo-3.1-4B-expo125 (vu dans meta.json).

**6. La puissance statistique est faible et les comparaisons multiples [V].**
- 2 contextes par strate et k = 8, pour environ 30 bras.
- En ligne : l'original fait 19/44 sur la réserve, contre 55,5 % sur le diag.
- lm40 apparié : 5/14 contre 3/14, non significatif.
- Bras prompt : 6/20 contre 5/20.
- Il faut publier les intervalles de confiance appariés et l'effet minimal détectable (environ 15 points à n = 45).

**7. L'arrondi BF16 dégrade les petites éditions [V/S].**
- 88 tenseurs langage sont inchangés après arrondi dans CUA β = 0,5.
- β = 0,25 et ExPO 1,1 sont probablement plus touchés.
- À vérifier : la norme effective comparée à la norme visée.

**8. Les dénominateurs diffèrent entre bras [V]** : les cohortes et le matériel (H200 contre H100) ne sont pas les mêmes.

**9. Les chiffres sont incohérents [V].**
- Régression vers la moyenne : 42 % contre 50 %.
- Limite de pas : 39 % contre 31 %.

**10. Le papier surinterprète [V]** : « internal state reads a false completion as complete » repose sur 14 paires ; le titre repose sur 8 traces ; « attractor », voir les points 3 et 4.

## Pistes proposées

1. **Faux succès infaisables (9/29)** : édition lexicale de lm_head, conditionnée sur les états « je ne peux pas », pour produire les formulations reconnues par la regex. À signaler comme exploitation de la regex du harness officiel.
2. **Mesurer le plafond de réparation**, puis choisir la cible. La limite de pas (16 échecs) a été peu attaquée.
3. **Juger les fusions et ExPO sur le score** en ligne, sur une grille β/λ, avec un contrôle de contamination de CUA.
4. **Éditer la tour vision ou le merger**, jamais tenté.
5. **Pilotage compilable via la ligne d'embedding** d'un token toujours présent (rôle assistant, `<think>`), en visant les tokens de la réflexion et du thought, là où la décision est verbalisée.
