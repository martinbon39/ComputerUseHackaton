# Vérification du budget d’attribution

**Verdict budget : conforme, avec une lacune documentaire.** À partir des journaux et JSONL préservés, le total reconstruisible est de **7 426 appels de forward tentés**. Il est inférieur au plafond global amendé de 8 500 de **1 074** appels. Il reste aussi inférieur de 74 à l’ancien budget inclusif de 7 500.

| Exécution | Forwards | Nature de la preuve |
|---|---:|---|
| Pilot attempt 1 | 3 | Inféré fortement : le traceback échoue dans le troisième `guarded(model, ...)`, après le full-prefill et le prefill-cache ; `PROTOCOL.md` dit aussi « failed after3 calls ». Le troisième appel a commencé mais n’a pas retourné. |
| Pilot attempt 2 | 316 | Observé directement dans `attribution_pilot_attempt2.log`, phases `complete` à 158 puis 316 et ligne `finished` à 316. |
| Pilot attempt 3 | 170 | 166 observés à la fin du premier contexte. Le second baseline écrit dans le log/JSONL requiert ensuite trois forwards ; le forward de répétition retourne avant l’assertion `cache clone nonrepeatable`, soit 166 + 3 + 1. Il n’y a pas de compteur final imprimé. |
| Pilot attempt 4 | 170 | Même reconstruction que l’essai 3 : premier contexte complet à 166, trois forwards jusqu’au second baseline, puis répétition calculée et journalisée avant l’assertion. |
| Pilot corrigé final | 332 | Observé directement dans `attribution_pilot.log`, deux contextes complets à 166 puis 332 et ligne `finished` à 332. |
| Attribution principale | 6 435 | Observé directement au dernier `complete` et à `finished` dans `attribution.log`. `attribution_part1.log` couvre les cinq premiers contextes, soit 825 appels, puis s’arrête pendant `prepare` avant le premier forward du sixième. La reprise initialise le compteur à 825 et ajoute 34 × 165 = 5 610 ; les 825 ne doivent donc pas être additionnés une seconde fois. |
| **Total** | **7 426** | 3 + 316 + 170 + 170 + 332 + 6 435. |

Le compteur du script est incrémenté avant l’appel modèle. Avec cette sémantique de plafond, l’appel qui plante à l’intérieur du modèle lors de l’essai 1 compte bien. Le nombre de forwards ayant retourné est 7 425 ; la différence est cet unique appel. Les révisions exactes du script propres aux essais 1–4 ne sont pas archivées ici, donc les comptes 3/170/170 sont des inférences de contrôle de flux corroborées par les tracebacks et les JSONL, pas des compteurs terminaux.

Le plafond par exécution de l’attribution principale est également respecté : 6 435 < 6 500. La ligne 20 de `PROTOCOL.md` énumère `attempt1 + attempt2 + corrected pilot + main` mais omet les essais 3 et 4. Ce parenthétique donne 7 086 appels, et ne constitue donc pas le décompte réel de tous les essais. La ligne 23 relève ensuite le plafond global à 8 500 pour les diagnostics échoués, sans inscrire leur somme. C’est la lacune documentaire ; elle ne change pas la conformité numérique une fois les deux essais ajoutés.

## Garde-fou des deux réparations sans progrès

Entre les essais 3 et 4, il n’y a **pas de progrès mesuré sur l’avancement ou la réussite du pilot** : dans les deux cas, `power_000` se termine à 166, puis `power_019` atteint son baseline et échoue sur la répétition du cache au même point, à 170 forwards reconstruits. L’essai 3 ne journalise pas l’amplitude de l’écart, donc aucune réduction quantitative entre les deux essais ne peut être revendiquée.

L’essai 4 apporte une information diagnostique nouvelle : sur `power_019`, il mesure `hidden_max_abs_diff = 0.125`, `hidden_equal = false`, avec une marge baseline 21.131321 contre 21.180126 à la répétition ; `power_000` reste exactement répétable. Cela localise la non-déterminisme dans l’état caché plutôt que dans la seule projection FP32. C’est un progrès de diagnostic, mais pas une amélioration du comportement exécuté.

La conformité au garde-fou dépend donc de la définition de « repair round », qui n’est ni définie ni enregistrée par le script. Lecture étroite : l’essai 3 découvre le défaut et l’essai 4 est une instrumentation diagnostique, donc ils ne sont pas deux réparations échouées ; la réparation déterministe suivante réussit à 332. Lecture stricte où toute révision de code compte comme une réparation : les essais 3 et 4 sont deux rounds consécutifs sans amélioration d’exécution, et continuer vers le pilot final s’écarte de la règle écrite en ligne 11. Les preuves disponibles ne permettent pas de trancher l’intention après coup ; elles permettent seulement d’affirmer qu’il n’y a pas eu de progrès d’exécution entre 3 et 4.

Périmètre : cette note ne vérifie aucun résultat de génération, statistique textuelle ou contrôle de cohorte, et aucun appel modèle/GPU n’a été lancé.
