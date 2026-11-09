# Deuxième relecture adversariale (contexte frais, 08/11, 03:35 UTC)

Condensé recopié par ares. Script de recalcul : `report/redteam2_recompute.py`. [V] = vérifié dans les fichiers, [S] = soupçon.

1. **[V] Le papier cite toujours l'audit retiré de broad p100** : `sec/interventions.tex:85` et `neurips/body.tex:76` (« non-destructive… e-mail recipient »). L'audit corrigé de 02:37 dit autre chose : les destinataires étaient déjà complets, et les 3 continuations « write » sont potentiellement régressives.

2. **[V] Les comparaisons en ligne se recalculent à l'identique** (orig_confirm 21/45 ; fusion 21,99 ; AlphaEdit 20 ; +2,2 avec 6 gains et 5 pertes ; −2,2 avec 3 et 4 ; mêmes 45 clés ; bons modèles servis ; aucun épisode à 0 pas), mais elles restent fragiles :
   - L'original contre lui-même (orbit contre GH, 44 tâches) donne −2,3, avec 7 discordantes.
   - Confondant de SERVEUR : orig_confirm passe par le pod (127.0.0.1:8000), les bras modifiés par Modal.
   - **[S]** calc 2bd59342 et impress bf4e9888 valent 0 sur les 3 runs servis par le pod et 1 sur les 2 bras Modal. Sans ces deux tâches : fusion −2,2, AlphaEdit −6,7.
   - Effet de VM : os 23393935 et 5812b315 valent 0 sur orbit et 1 sur GH. Le « pooled » est donc à rejeter.
   - La fusion a 6 échecs de parse, contre 0 pour l'original (signal de dégradation du format). Shard 4 : 19 erreurs pyautogui sur 69acbb55, notée 0 partout.

3. **[V] Le résumé surestime.**
   - « consistent with an information bound » contredit le corps du papier.
   - « requires swapping many writers of 12–31 » est faux : le bloc 12-23 seul donne −3,5, le bloc 24-31 seul −10,0, et le rang 1 ramène à +1,4.

4. **[V] L'ancrage ne repose que sur 1 contexte faisable.**
   - fs_0 est infaisable.
   - Le donneur, le pas précédent, avait cliqué. Le test montre donc que le nom d'outil suit l'intention écrite, ce qui est presque tautologique.
   - Pas de contrôle fs−, ni de texte neutre.
   - Environ 10 logits viennent de l'écran et de l'historique (−7,4 contre −17,1 pour le donneur).

5. **[V] « Non additif » n'est pas soutenu** : 1 contexte et k = 8 (3/8 [9 ; 76 %] contre 7/8 [47 ; 100 %], Fisher p = 0,12). Les arrondis BF16 diffèrent d'une fusion partielle à l'autre.

6. **[V] La discriminabilité dépend de la métrique.**
   - Seulement 71 paires intra-fold sur 361.
   - Médiane 0,704 sur [0,61 ; 0,90].
   - En AUROC poolée hors fold : position 0,644, sonde 0,596.
   - Le 95e centile du null est autour de 0,67-0,71.
   - Écrire « pas mieux que la position ».

7. **[V] Incohérences internes.**
   - `limits.tex:7` « used once » contre « three online runs ».
   - « three online » alors qu'il y a 5 bras.
   - `\tofill` restants.
   - Les PDF datent d'avant 03:27.

**À faire.**
- Servir l'original sur Modal (même endpoint que les bras) et le passer sur la réserve et sur le test, avec une règle de décision fixée AVANT de lire les résultats.
- Contrôles par logits seulement :
  - ancrage sur 2 vrais fini, avec un texte neutre ;
  - localisation avec k ≥ 32, ou avec plus de contextes faisables.
