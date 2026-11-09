# Judge bench — quatre juges sur les mêmes 268 épisodes (écran final seul)

**Question.** Un juge plus fort que Holo-3.1-4B distingue-t-il les faux succès des vrais, sur exactement le corpus
gelé de verif-study (66 faux succès, 202 vrais succès faisables, 90 tâches OSWorld, réponse finale `answer`) ?

**Réponse, avec ces prompts et sur l'écran final seul :**
- **Holo4-27B** fait mieux que Holo-3.1-4B surtout en rejetant moins de vrais succès (31 % au lieu de 48 %), mais ne
  détecte pas plus de faux succès (47 % contre 53 %). Son écart (+16 pts) n'est pas distinguable de zéro au niveau
  tâche (IC [-3, +33]), ni distinguable de celui de Holo-3.1-4B (IC de la différence appariée [-8, +28]).
- **Claude (vérificateur gelé de Feci Guard)** détecte 68 % des faux succès en ne rejetant à tort que 10 % des vrais :
  écart +58 pts, IC bootstrap par tâche [+41, +74], nettement au-dessus de Holo-3.1-4B (différence appariée
  +53 pts, IC [+26, +79]). Aucune erreur ni timeout sur 268 appels.
- **V2c, pour lever la confusion modèle/prompt** : Holo4-27B derrière le vérificateur Feci Guard gelé (même prompt,
  même schéma JSON, même règle que Claude). Le prompt Feci aide Holo4 surtout en baissant ses faux rejets (31 % → 24 %) ;
  la détection reste à 47 % (31/66). Écart +23 pts, IC [+5, +40] : au-dessus de zéro, mais pas distinguable de
  Holo-3.1-4B (différence appariée +18, IC [-5, +40]). **Claude reste nettement devant à prompt égal** : différence
  appariée Holo4-Feci − Claude = −35 pts, IC [−59, −10]. L'essentiel de l'avantage de Claude vient donc du modèle,
  pas du prompt.
- 23 sorties de V2c n'ont pas de verdict (16 timeouts à 55 s, le délai gelé de `verify` ; 7 JSON hors schéma) et
  comptent comme « passe ». En ne gardant que les verdicts valides, Holo4-Feci donnerait 31/58 (53 %) contre 49/187
  (26 %), écart ≈ +27 pts : toujours loin de Claude (+58, zéro erreur).

## Table

| | Holo-3.1-4B | Holo4-27B | Claude (Feci Guard verifier) | Holo4-27B (Feci Guard verifier) |
|---|---|---|---|---|
| Faux succès détectés (INCOMPLETE / 66), IC Wilson | 53 % (35/66) [41–65] | 47 % (31/66) [35–59] | 68 % (45/66) [56–78] | 47 % (31/66) [35–59] |
| Vrais succès rejetés à tort (INCOMPLETE / 202), IC Wilson | 48 % (97/202) [41–55] | 31 % (63/202) [25–38] | 10 % (21/202) [7–15] | 24 % (49/202) [19–31] |
| Écart détection − faux rejet | +5.0 pts | +15.8 pts | +57.8 pts | +22.7 pts |
| IC 95 % de l'écart (bootstrap par tâche, 90 tâches) | [-13, +23] pts | [-3, +33] pts | [+41, +74] pts | [+5, +40] pts |
| Erreurs/sorties invalides (comptées « passe »), faux / vrais | 3 / 3 | 1 / 4 | 0 / 0 | 8 / 15 |
| Part de « cannot tell » parmi les exigences listées, faux / vrais | 16 % / 20 % | 12 % / 11 % | 20 % / 28 % | 18 % / 12 % |
| Épisodes avec ≥ 1 « cannot tell », faux / vrais | 13/66 / 52/202 | 8/66 / 19/202 | 31/66 / 118/202 | 16/66 / 39/202 |

- Holo4-27B − Holo-3.1-4B : +10.8 pts d'écart, IC 95 % [-8, +28] pts (mêmes tâches rééchantillonnées pour les deux juges)
- Claude (Feci Guard verifier) − Holo-3.1-4B : +52.8 pts d'écart, IC 95 % [+26, +79] pts (mêmes tâches rééchantillonnées pour les deux juges)
- Holo4-27B (Feci Guard verifier) − Holo-3.1-4B : +17.7 pts d'écart, IC 95 % [-5, +40] pts (mêmes tâches rééchantillonnées pour les deux juges)
- Holo4-27B − Claude : -42.0 pts d'écart, IC 95 % [-69, -14] pts (mêmes tâches rééchantillonnées pour les deux juges)
- Holo4-27B (Feci Guard verifier) − Claude : -35.1 pts d'écart, IC 95 % [-59, -10] pts (mêmes tâches rééchantillonnées pour les deux juges)
Règle de décision identique pour les trois : INCOMPLETE = détection ; COMPLETE = passe ; erreur / timeout / sortie
tronquée ou sans verdict lisible = passe, compté à part (ligne « Erreurs »). Les IC des taux sont de Wilson ; l'IC de
l'écart est un bootstrap percentile qui rééchantillonne les 90 tâches (domaine, task_id) avec les deux labels
ensemble, 10 000 tirages, graine 20261108 (fonction `cluster_ci` de verif-study, importée telle quelle). La colonne
Holo-3.1-4B est recalculée depuis `verif_study/responses.jsonl` (réplique T=0) et redonne exactement les chiffres de
verif-study (35/66, 97/202, IC [-13, +23]).

## Protocole

| | V1 Holo-3.1-4B | V2a Holo4-27B | V2b Claude |
|---|---|---|---|
| Corpus | manifest verif-study (sha `67cc43166d6b1309…`) | idem | idem |
| Image | capture finale de verif-study, sha256 vérifié à chaque appel | idem | idem |
| Prompt | prompt V1 de verif-study | **même prompt, importé de `run_verifier.py`** | prompt propre de Feci Guard (sortie JSON à schéma) |
| Réglages | T=0, max_tokens 4096, réflexion activée | T=0, top_p 1, max_tokens 4096, réflexion activée (`enable_thinking: true`) | `verify(instruction, image_path)` avec ses défauts : `claude -p`, modèle `sonnet`, timeout 55 s, mode passif |
| Service | vLLM local (pod) | endpoint Modal `holo-judge-serve`, 12 requêtes parallèles | CLI Claude Code 2.1.319, 4 appels parallèles |
| Code | `verif_study/run_verifier.py` | `judge_bench/run_holo4.py` | `judge_bench/run_claude.py` ; `feci_guard/verifier.py` non modifié, sha256 `0af76fdbacc72317…` |

Holo4-27B : 268/268 réponses `finish_reason=stop`, 0 erreur de transport, 0 troncature (max 753 tokens de complétion
visibles) — la réflexion a donc été gardée, pas besoin de `enable_thinking: false`. Run 08:07–08:12 UTC (~5 min de serveur).
Claude : 268/268 verdicts valides, latence médiane 6 s (max 12 s), coût affiché par la CLI 7.60 $.
Les deux runs pilotes d'un épisode (même épisode, mêmes réglages) ne sont pas comptés.

V2c (Holo4-27B + Feci Guard) : `run_holo4_feci.sh` → `run_claude.py` (même lanceur que V2b) avec
`GUARD_BACKEND=openai`, `GUARD_BASE_URL` = endpoint Modal, `GUARD_MODEL=Holo4-27B`, `GUARD_API_KEY_ENV` = une variable
remplie depuis `~/.holo_modal_key` dans le shell (jamais écrite) ; `verify_openai` avec ses défauts : T=0, max_tokens
4096, timeout 55 s, sans retry, réglage de réflexion par défaut du serveur (pas de `chat_template_kwargs`), image avant
le texte, schéma JSON ajouté au prompt. 12 requêtes parallèles, 08:28–08:35 UTC, latence médiane 14 s. Le
vérificateur ne garde pas le texte brut d'une réponse hors schéma : les 7 cas ne sont pas diagnostiquables.

## Limites (à lire avant de citer ces chiffres)

1. **Prompt confondu pour Claude (levé en partie par V2c).** Le vérificateur Feci Guard demande un JSON et ne déclare INCOMPLETE que si une
   exigence est visiblement « no » ; un « cannot_tell » ne suffit pas. Le prompt V1 laisse le modèle trancher librement.
   V2c met Holo4 dans les mêmes conditions que Claude : l'écart Claude − Holo4 passe de +42 à
   +35 pts, il reste donc surtout l'effet du modèle. Les 16 timeouts de V2c pénalisent Holo4 (servi plus lentement que
   Claude) ; même sans eux, l'écart reste d'environ 30 pts. Les 21 faux rejets de Claude ont tous au moins une exigence « no » ; les
   INCOMPLETE des modèles Holo ont souvent zéro « no » analysable (texte libre, extraction des exigences imparfaite).
2. **Écran final seul.** Beaucoup d'exigences ne sont pas visibles (fichier enregistré, réglage) : Claude répond
   « cannot_tell » sur au moins une exigence dans 31/66 faux et 118/202 vrais épisodes. Les 21 faux succès que Claude
   laisse passer sont en partie de ce type ; la détection ne peut pas atteindre 100 % sur une seule capture.
3. **Population.** 268 épisodes d'un seul agent (Holo-3.1-4B), 90 tâches seulement : l'IC par tâche est l'incertitude à
   retenir, pas l'IC de Wilson par épisode. Ce n'est pas OSWorld complet.
4. **Une seule passe T=0 par juge** pour V2a et V2b (V1 avait aussi 3 répliques T=0.8, non utilisées ici).
5. **Modèle Claude.** L'alias `sonnet` de la CLI ; la version exacte servie n'est pas consignée par `verify()`.
   Claude peut connaître des tâches OSWorld publiques ; on ne peut pas l'exclure.
6. Sur la boucle réelle, un rejet ne vaut que si l'agent sait ensuite réparer : ces chiffres mesurent le juge, pas le
   gain de score (voir l'étude de réparation de Feci Guard).

## Fichiers

`run_holo4.py`, `run_claude.py` (lanceurs), `holo4_responses.jsonl`, `claude_responses.jsonl` (sorties brutes),
`analyze.py` → `RESULT.json` + `per_episode.json`, `write_report.py` → `REPORT_TABLE.md`, `holo4_run.log`,
`claude_run.log`. Recalcul indépendant : voir la section suivante.

## Recalcul indépendant

Un sous-agent vérificateur (lecture seule, sans importer le code de ce dossier) a réécrit l'analyse de zéro
(`independent_recompute.py`, copie de son script) : parsing des verdicts, Wilson, bootstrap par tâche (graine 1).
**MATCH sur tous les chiffres** : comptes identiques (35/66, 97/202 ; 31/66, 63/202 ; 45/66, 21/202), sorties
invalides identiques (3/3, 1/4, 0/0), écarts identiques ; bornes bootstrap à 0,6 pt au plus des nôtres
(Holo-3.1-4B [-13, +23], Holo4-27B [-2, +34], Claude [+41, +74]). Intégrité : 268 épisodes, 90 tâches, chaque
épisode présent exactement une fois pour chaque juge. V2c recalculé de même (`independent_recompute_v2c.py`, graine 7) :
MATCH — 31/66, 49/202, 8/15 invalides, écart +22,7 [+5, +40] ; appariés D − Holo-3.1 +17,7 [−6, +40] et D − Claude
−35,1 [−59, −10] ; bornes à 0,7 pt au plus des nôtres.
