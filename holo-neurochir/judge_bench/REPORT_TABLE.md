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
