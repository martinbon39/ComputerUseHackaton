# CHECKLIST JOUR J + réponses Q&R — duel live Holo × Feci Guard

> demo-director, 2026-11-08. Passages : 1er tour de jury 13:30 UTC (14:30 Paris), finales 14:45 UTC (15:45 Paris), à confirmer.
> Commandes à lancer sur orbit depuis `holo-neurochir/`, sauf indication contraire.

## T−60 min : ressources (fait par la flotte, vérifié par ares)
- [ ] **Gel des VMs** : aucun autre agent n'a de VM OSWorld de T−15 à T+30 min. `docker ps` (via `~/osw/osh "docker ps"`) : pas de conteneur OSWorld qui reste.
- [ ] **RAM** : `free -g` → colonne *available* **≥ 15 Go** (garde du duel : `duel_server.py`, `MIN_AVAIL_GB = 15`). En dessous, le bouton LANCER refuse.
- [ ] **Agent servi par Modal** (compte 1, `Holo-3.1-4B-modal-orig`) : le pod (port 8000) ne répond plus depuis ~10:40 UTC, donc le live passe par le preset **`modal_guard`**. Ce serveur redescend à zéro après 2 min sans requête, et son démarrage à froid prend ~70 s (mesuré à 10:46 : 69 s). Le duel refuse de démarrer si le modèle n'est pas listé (`served()`, délai de 20 s). **À T−3 min, Martin lance depuis orbit** (la clé est lue dans le fichier, jamais sur la ligne de commande) :
  `curl -s -m 180 -H @<(printf 'Authorization: Bearer %s\n' "$(cat ~/.holo_modal_key)") https://emilejouannet--holo-vllm-serve.us-east.modal.run/v1/models | grep -o '"id":"Holo-3.1-4B-modal-orig"' || echo 'PAS PRÊT'`
  → affiche `"id":"Holo-3.1-4B-modal-orig"` (jusqu'à ~70 s). Puis lancer le duel dans les 2 min. Un duel de chauffe garde aussi le serveur réveillé.
- [ ] **Juge du Guard** : le Guard appelle `claude -p` (alias `sonnet`, `feci_guard/verifier.py`) avec la connexion Claude Code d'orbit. Test, sur orbit et avec le même binaire : `timeout 60 /home/orbit/.local/bin/claude -p "Réponds juste OK" --model sonnet --strict-mcp-config --setting-sources ""` → `OK` en moins de 15 s. **Risque relevé à 09:10 UTC** : le CLI prévient que *« this sign-in can end at any time from now until 2026-11-10 »*. Martin seul peut le sécuriser : `claude setup-token` (jeton pour les tâches sans surveillance) dans un terminal orbit avant le pitch, puis refaire ce test. Sans connexion valide, le Guard **laisse passer** (timeout 55 s) : la démo perd son refus.
- [ ] **Serveur du duel** : `curl -s -m5 http://127.0.0.1:8765/api/config | head -c 80` répond. Sinon : `bash osworld/duel/duel.sh serve modal_guard` (tmux `duel_server`, devcap 1G). Ne pas le redémarrer pendant un duel.
- [ ] **Aucun duel en cours** : `bash osworld/duel/duel.sh list | head -3` ; si un duel traîne : `bash osworld/duel/duel.sh stop`.
- [ ] **Répétition générale** : un duel complet sur calc/1de60575 entre T−60 et T−30 (avec réservation ares), puis `duel.sh list` pour son verdict et la mise à jour du replay du plan B dans le cockpit.

## T−30 min : le portable de Martin
- [ ] **Tunnel** : `ssh -N -L 8765:127.0.0.1:8765 orbit` dans un terminal qui reste ouvert (ajouter `-o ServerAliveInterval=15`). Test : http://127.0.0.1:8765/ s'ouvre.
- [ ] **Réseau de secours** : partage de connexion du téléphone prêt ; tester le tunnel dessus une fois.
- [ ] **Copies locales (plan C)** : `holo-demo-video.mp4`, `holo-pitch-system.html`, `holo-demo-faux-fini.html`, `holo-paper.pdf` téléchargés dans un dossier du bureau. Ouvrir la vidéo une fois en local.
- [ ] **Onglets, dans l'ordre** (ou tout depuis le cockpit) : 1. Cockpit (minuteur) · 2. **Duel live** · 3. **Replay R1, OUVERT dès le début, juste à côté du live** : `http://127.0.0.1:8765/?replay=20261108-110023_libreoffice_calc_1de60575-bb6e-4c3d-9e6a`, vitesse ×2, prêt à sauter à +130 s · 4. Slides · 4 bis. Replay R3 en réserve (`?replay=20261108-111313_libreoffice_calc_1de60575-bb6e-4c3d-9e6a`) · 5. Vidéo · 6. Papier · 7. Tableau de bord d'équipe.
- [ ] **Page du duel préparée** : preset **« Feci Guard, Modal »** (`modal_guard`), tâche **`libreoffice_calc/1de60575…`** (n°1, en tête de liste ; n°2 : `libreoffice_impress/550ce7e7…`), case **Feci Guard à droite** cochée, pas max 50. **Ne pas lancer.**
- [ ] Zoom du navigateur pour le projecteur (le texte du refus doit se lire du fond de la salle) ; mode « Ne pas déranger » ; batterie branchée.
- [ ] **Minuteur** : cockpit, Espace pour démarrer à 0:00 en même temps que LANCER.

## Fenêtre de la sonde jury (optionnelle, décision de ares)
- Elle sert au Q&R sur la **chirurgie** : elle rejoue un contexte enregistré sur l'original et sur la fusion, et renvoie l'action et la probabilité du premier token de l'outil (`osworld/modal_jury_probe.py`). Hors fenêtre : 503 « porte fermée ».
- Ouverture : **par l'agent `modal-serve` sur ordre de ares**, avec `bash osworld/modal_jury_window.sh check <min>` puis `up <min> --go` (10-180 min). Il faut que `modal_budget_guard.sh` tourne. Le script refuse si un compte dépasserait 24 $. **Attention** : le compte 2 est déjà à 17,32 $ (`osworld/MODAL_COST.md`) ; 90 min le projetterait à ~24,5 $, donc **refus**. Viser ≤ 75 min, et lancer `check` dès maintenant. Démarrage à froid de 3 à 8 min selon `MODAL_COST.md` : **ouvrir à T−25 min**. Fermeture automatique (`down`).
- Coût : une H100 par compte, ~4,1 $/h × (min+15)/60 **par compte** : ~6,2 $ par compte pour 75 min, ~12 $ au total.
- Test pendant la fenêtre : `curl -s https://martinbon39--holo-jury-probe-web.us-east.modal.run/contexts`.

## Après le passage
- [ ] STOP global sur la page (`duel.sh stop`), vérifier qu'aucun conteneur ne reste.
- [ ] Rendre les VMs à la flotte (prévenir ares). Rien d'autre à couper : le serveur du duel reste pour les finales.

---

## Q&R : réponses courtes (chiffres sourcés)

**« Pourquoi la chirurgie des poids échoue-t-elle ? »**
Le modèle ne sépare pas un faux « fini » d'un vrai, ni dans ses activations ni dans son texte. La meilleure direction donne une AUROC de 0,760, contre 0,724 pour le simple numéro du pas (`paper/generated/tab_fs_auc.tex`). Les éditions déplacent bien la décision, mais sans sélectivité : AlphaEdit fait passer `answer` sur les faux succès de 15/16 à 8/16, et sur les vrais « fini » de 15/16 à 3/16. Un contrôle aléatoire de même norme ne change rien (16/16). On abîme donc les vraies réussites autant que les fausses. En ligne : +1,9 point, IC95 [−4,3 ; +8,0], sur 165 tâches appariées, 18 gains pour 14 pertes. Le seuil de décision (gain seulement si la borne basse de l'IC95 est > 0) était figé avant le verdict, et c'est un **négatif**. Honnêteté : le choix de la référence (l'original servi par Modal) a été fait après avoir vu les premiers runs servis par le pod. Contre l'original servi par le pod, la fusion fait −1,3 point (`jury_kit/RESULTS.md` §1). Les chiffres AlphaEdit viennent d'un petit échantillon (16 tirages, 2 contextes).

**« Pourquoi Claude comme juge ? Vous n'êtes pas indépendants de H. »**
Sur les 268 mêmes épisodes et avec le même prompt Feci Guard : Claude 68 % / 10 % (+58), Holo4-27B 47 % / 24 % (+23 [+5 ; +40]). Holo-3.1-4B, avec un autre prompt (V1), fait 53 % / 48 % (+5, au hasard) ; Holo4 avec ce prompt V1 fait 47 % / 31 %. À prompt égal, l'écart Claude − Holo4 est de 35 points [10 ; 59], dont environ 31 si l'on ne garde que les verdicts valides (Holo4 a 23 non-verdicts comptés « passe »). Le Guard est **agnostique au juge** : Holo4 sépare déjà significativement, c'est une piste 100 % H, mais il bloque encore 24 % des vrais succès. Limites : la version exacte de Claude servie n'est pas journalisée (alias `sonnet` du CLI), et Claude a pu voir des tâches publiques d'OSWorld.

**« Coût et latence du Guard ? »**
Une vérification ne se fait qu'au « fini », pas à chaque pas. **~6 à 7 s** : médiane de 6 s sur le banc (4 à 12 s, 268 appels) ; en ligne, médiane de 7,2 s et 0 timeout sur 104 verdicts (bilan de gh-runner2, pas encore écrit dans un fichier) ; **~0,03 $** par vérification (7,60 $ pour 268, `judge_bench/claude_responses.jsonl`). Au plus 2 refus par épisode. Un timeout (55 s) ou une erreur **laisse passer** : le Guard ne bloque jamais l'agent. Holo4-27B : médiane 14 s, 16 timeouts sur 268.

**« Ça marche en ligne, ou seulement hors ligne ? »**
En ligne, sur les 120 tâches du split de test (`report/ONLINE_GUARD_RESULT.md`, règle préenregistrée dans `PREREG_ONLINE_GUARD.md`). Comparaison avec l'original, même déploiement Modal : **taux de faux « fini » de 22,5 % (27/120) à 10,8 % (13/120)**, soit −11,7 points, IC95 [−19,2 ; −4,2], **significatif**. **Score OSWorld : 58,6 → 60,2, soit +1,6 [−4,4 ; +7,7], non significatif : aucun gain de score n'est revendiqué.** 8 tâches réparées, 4 vraies réussites perdues. Ces 4 pertes restent dans le bruit de l'original contre lui-même (9 bascules de 1 à 0). Avec l'original servi par le pod comme comparateur : −13,3 points [−20,8 ; −5,8] sur le faux « fini », score +0,1. Le juge a rendu 104 verdicts sans erreur.

**« Le Guard améliore-t-il le score OSWorld ? »**
**Pas de gain prouvé.** Détecter n'est pas réparer. Première mesure, dans le papier : 0 réparation sur 10 branches dans les deux bras, en 15 pas (`paper/generated/num_guard.tex`). Mesure suivante, relue et validée (`rescue_bench/HOLO31_REFERENCE.json`) : 5 branches sur 18 finissent avec un score officiel de 1 avec le Guard, contre 2 sur 18 sans, soit +16,7 points, IC95 [0 ; +44] (recalcul indépendant : [0 ; +39]) : **non significatif à ce stade**. Mais 2 de ces 5 succès, et les 2 succès sans le Guard, sont des épisodes (8979838c) notés 1 **sans aucune action nouvelle**. **Les vraies réparations sont donc 3 contre 0.** La première mesure, 0/10, était un instantané partiel. Exemple réel de réparation : calc/1de60575 (page `holo-guard-repair`). L'escalade vers Holo4 est en test. Sa valeur aujourd'hui : l'utilisateur sait **quand ne pas faire confiance**, avec la preuve.

**« Comment H pourrait-il l'intégrer ? »**
Un crochet sur l'appel terminal `answer` : `feci_guard.check(task, screenshot)`. `run_holo_guard.py` reprend notre harness avec ce seul crochet. Ce harness est la reproduction tierce RealtimeGUI, pas le dépôt de H (`paper/sec/setting.tex`). Trois usages : (1) produit, avec un vérificateur avant de rendre la main à l'utilisateur ; (2) données, avec des faux succès étiquetés et leur exigence ✗, pour une récompense d'entraînement qui pénalise le faux « fini » ; (3) juge maison, puisque Holo4 avec ce prompt fait déjà +23.

**« Vos 57 % de faux succès, c'est solide ? »**
29 échecs sur 51, sur 120 tâches de diagnostic (119 notées), dont 9 sur des tâches infaisables et 20 sur des tâches faisables (`paper/generated/num_osw_diag.tex`). Notre harness tourne à 50 pas : on ne compare jamais aux chiffres internes de H.

**« Comment je vérifie tout ça moi-même ? »**
Kit jury (`jury_kit/`). Niveau 1 : `python verify_results.py`, quelques secondes, bibliothèque standard seule ; il doit afficher +1,94 (165), +0,18 (test), +6,64 (réserve). Niveau 2 : `python rebuild_merge.py --build OUT` (CPU, ~40 Go de disque), comparé au sha256 attendu. Niveau 3 : `probe_decision.py`, ou le notebook sur une T4 Colab. Pendant la fenêtre : la sonde en ligne. **Honnêteté** : la fusion a été reproduite au bit près sur une autre machine, mais avec notre script `merge_v2.py`. Le script du kit, `rebuild_merge.py`, n'a été vérifié que sur 2 tenseurs : son `--build` complet et le niveau 3 GPU n'ont pas été rejoués.

**« Et ce duel de 11:59 dans la liste, à score 0 ? »**
Panne d'infrastructure, exclue : le serveur de captures de la VM de droite est tombé (« too many consecutive errors; ending episode early » dans `side.log`), à cause d'une cadence de capture à 1 s, revenue depuis à 2 s. Juste avant, le Guard avait refusé normalement. Sur les duels valides de cette tâche, l'arc complet s'est produit 2 fois sur 3.

**« Le live est-il truqué ou choisi ? »**
La tâche est choisie : sur 550ce7e7 (split diagnostic), l'original a dit « fini » à tort dans 4 runs sur 4 ; sur b8adbc24 (split de test), dans 5 duels sur 5. L'exécution, elle, est réelle et aléatoire (T=0,8). Chaque duel est enregistré (`~/osw/duels/`) et se rejoue sur la même page.

**« Combien ça a coûté ? »**
Modal : 16,80 $ + 17,32 $ sur deux comptes (`osworld/MODAL_COST.md`). Juge Claude du banc : 7,60 $. Il faut y ajouter la H200 RunPod partagée.

**« Qui a fait quoi : vous ou les agents ? »**
Un orchestrateur (ares) et environ 25 agents (chercheurs Astra, infrastructure, relecteurs adversariaux), coordonnés sur le canvas argos. Martin fixe les objectifs et les règles d'arrêt, et c'est lui qui tranche. Les relectures adversariales ont attrapé des erreurs : sans elles, le papier annonçait un effet (exemples sur la page système : confusion entre les serveurs pod et Modal, formule RegMean, serveur vLLM figé).
