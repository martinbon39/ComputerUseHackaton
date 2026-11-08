# RUN-OF-SHOW — pitch Holo × Feci Guard, avec duel LIVE (jury H Company × 42AI)

> demo-director, 2026-11-08 ~09:45 UTC. Chiffres : `judge_bench/REPORT.md`, `paper/generated/*.tex`, `jury_kit/RESULTS.md`,
> `~/osw/duels/`. Aucun gain OSWorld n'est affirmé : le Guard **détecte**, il ne **répare** pas encore.
> Heures (page Luma, `pitch/PITCH.md`) : dépôt 14:00, 1er tour de jury 14:30, finales 15:45 (Paris) = **13:00 / 13:30 / 14:45 UTC**.
> Heure exacte de passage : **à confirmer par Martin**.

## L'idée en une phrase
« Les agents computer-use disent *c'est fini* alors que non. On a tenté de l'enlever de leurs poids : ça ne marche pas, et on
sait pourquoi. Alors on a construit un vérificateur externe qui l'attrape, et vous allez le voir faire en direct. »

## Le moment LIVE (le cœur, 25 % Computer Use + 10 % UX/contrôle)
Page du duel `http://127.0.0.1:8765/` (via le tunnel), preset **« Feci Guard, pod »**, case **Feci Guard à droite** cochée,
tâche **`libreoffice_impress/550ce7e7`** : « barrer la 1re et la 2e ligne » (split **diagnostic**). Elle est dans la liste de la page depuis 09:12 UTC, en tête (online-eval).
- À gauche, **Holo-3.1-4B seul** ; à droite, **le même Holo-3.1-4B + Feci Guard (juge : Claude)**. Même agent, même tâche, deux vraies VMs Ubuntu.
- Chronologie **estimée, jamais mesurée en duel sur 550ce7e7** (les répétitions de 11:00 la mesureront) : VM prête en ~20 s, attente
  de 60 s, puis ~7 pas (20-67 s d'agent dans les 4 runs de l'original). **Le faux « fini » de gauche devrait arriver vers ~1:45-2:45
  après START** ; mesuré sur b8adbc24 : 104-159 s. Verdict officiel ~23 s plus tard (bandeau **FAUX SUCCÈS**). À droite, même modèle
  donc même aléa : sa 1re réponse peut venir bien plus tard (au pas 29 dans l'unique run Guard sur cette tâche). Le Guard vérifie
  en ~6-10 s et affiche **REFUS** avec l'exigence ✗ et sa preuve (texte du run réel : *« la sélection et le barré s'arrêtent à
  “Requ”, “ests.” n'est pas barré »*).
- **Aucun duel Guard n'a encore abouti avec le vérificateur actuel** (074039 : version d'avant 07:43 ; 075133 : bug de code ;
  075423 : arrêté faute de RAM). Les répétitions sont donc la vraie validation.
- Martin appuie sur **■ STOP** du côté droit après le refus : l'humain garde la main. On le dit franchement : *la réparation après un refus
  ne réussit pas toujours (sur cette tâche, même réparé à l'écran, l'évaluateur met 0 : l'écart est dans le fichier), donc je
  l'arrête* ; puis on enchaîne sur la séquence enregistrée où la réparation réussit (calc/1de60575).

## Déroulé minute par minute (cible 6:10, plafond 7:00, puis Q&R)
> Durée du créneau **non confirmée** (le brief dit 5 à 7 min ; `pitch/PITCH.md` prévoyait 3 min). En version 3 min : garder 0:00 LANCER, le problème (20 s), la chirurgie (30 s), le duel (75 s), les chiffres du Guard (30 s), la fin (10 s).
Le minuteur est dans le cockpit (`demo_live/cockpit.html`, touche Espace).

| Temps | Écran | Ce que fait / dit Martin | Critère coché |
|---|---|---|---|
| **−2:00** (avant d'être appelé) | Duel | Page du duel ouverte, preset et tâche choisis, case Guard cochée, **ne pas lancer**. RAM ≥ 15 Go vérifiée par `free -g` (la page n'affiche pas la RAM ; elle refuse seulement au lancement). Onglets prêts (voir checklist). | — |
| **0:00-0:15** | Duel | **Appuie sur ▶ LANCER.** « Je lance tout de suite deux agents sur deux vrais bureaux Ubuntu, dans des VMs sur notre serveur. Même modèle, celui de H, Holo-3.1-4B, même tâche. Une seule différence : à droite, notre vérificateur, avec Claude pour juge. On y revient dans deux minutes. » | Computer Use |
| **0:15-0:45** | Slides : le problème | « Quand Holo échoue sur OSWorld, **57 % de ses échecs sont des faux “fini”** : 29 sur 51, sur 120 tâches de diagnostic. Il ne se trompe pas de bouton, il se trompe sur lui-même. Et l'utilisateur, lui, le croit. » | Utilité |
| **0:45-1:45** | Slides : la chirurgie (négatif) | « Notre première idée : retirer ce défaut directement des poids, sans entraînement. Une nuit, un labo autonome d'agents IA, seuil de décision figé avant le verdict (gain seulement si la borne basse de l'IC95 est > 0), relecteurs adversariaux. Résultat honnête : **+1,9 point, IC95 [−4,3 ; +8,0] sur 165 tâches : pas de gain détectable.** Et on sait pourquoi : à l'intérieur, le modèle ne distingue pas un faux “fini” d'un vrai, pas mieux que le simple numéro du pas. On ne peut pas couper un signal qui n'existe pas. Il faut une information **extérieure**. » | Originalité, exécution technique |
| **1:45** | Coup d'œil au duel | Point de décision n° 1 (voir « Plans B/C ») : les deux côtés affichent des pas ? Sinon, plan B. | — |
| **1:45-2:15** | Slides : Feci Guard | « Feci Guard regarde l'écran au moment où l'agent dit “fini”, liste chaque exigence de la tâche, la marque ✓ ou ✗ avec sa preuve visuelle, et refuse le “fini” si une exigence est visiblement fausse. Il ne change rien au modèle de H, il se branche sur le dernier appel. » | Utilité, UX |
| **2:15-3:45** | **DUEL (plein écran)** | **Le moment live.** Gauche : « Il dit : *tâche terminée*. » → bandeau officiel **FAUX SUCCÈS**. Droite : « Même phrase, mais le Guard vérifie… **refus** : la deuxième ligne n'est pas barrée jusqu'au bout, voilà la preuve. » → **Martin appuie sur STOP à droite.** « C'est moi qui décide. Ce que le Guard garantit ici, c'est qu'on ne vous ment plus : la réparation, elle, ne réussit pas toujours. Je vous en montre une qui réussit. » | **Computer Use, UX et contrôle** |
| **3:45-4:15** | **Séquence enregistrée « l'agent répare »** (`repair_calc.html`, flèches →) | « Et quand l'agent sait corriger ? Épisode réel, enregistré, tâche calc du split diagnostic. Il dit *fini*, le Guard refuse : l'onglet s'appelle *Pivot Table_Sheet1_1*, pas *Sheet2*. L'agent renomme l'onglet en 5 pas, le Guard accepte, **score officiel 1**. Sans le Guard, sur ce même rejeu : 0 deux fois sur deux. » Dire que c'est **enregistré** et **choisi**. Puis le chiffre agrégé, relu et validé (`rescue_bench/HOLO31_REFERENCE.json`) : « sur 18 branches rejouées, 5 réparées avec le Guard contre 2 sans : +17 points, IC95 [0 ; +44], **non significatif à ce stade** ». | Utilité, Computer Use |
| **4:15-5:00** | Slides : les chiffres du Guard | « Ce n'est pas un cas choisi : sur **268 épisodes** réels, le Guard avec Claude attrape **68 %** des faux succès et ne bloque que **10 %** des vrais (écart +58 points, IC [+41 ; +74]). Holo-3.1 qui juge son propre travail est **au hasard** (53 % / 48 %). Et **Holo4-27B, avec le même prompt que Claude, sépare déjà significativement** : 47 % / 24 %, +23 points [+5 ; +40], mais il bloque encore 1 vrai succès sur 4. Coût : ~3 centimes et ~6 s par vérification. » | Utilité, exécution technique |
| **5:00-5:40** | Slides : le système | « Tout ça a été fait par un labo d'agents d'environ 25 agents, avec des protocoles préenregistrés et des relecteurs adversariaux. Ces relectures ont attrapé des erreurs qui, sans elles, nous auraient fait annoncer un effet. Plus d'un millier d'épisodes OSWorld ont été notés. Un humain supervise sur le canvas, avec des règles d'arrêt automatiques. Et tout est vérifiable : le kit jury, la fusion reproduite au bit près sur une autre machine, la sonde en ligne. » | Originalité, exécution, UX |
| **5:40-6:10** | Slide de fin | « Pour H : une retouche de poids à bas coût ne suffit pas, la correction passe par un **vérificateur externe** ou par l'**entraînement**. La prochaine étape, c'est de mesurer la réparation à grande échelle : vous en avez vu un cas, la mesure est en cours. Nous, on a vérifié avant de dire *c'est fait*. Merci. » | Utilité, clarté |
| **6:10-** | Q&R | Fiche `CHECKLIST_JOUR_J.md` § Q&R. Garder le duel ouvert : on peut **rejouer** le refus (bouton replay, ×2). | Clarté et Q&R |

Règles d'oral : ne jamais dire « le Guard améliore le score » (non mesuré) ; dire « détecte », « refuse », « attrape ». Le chiffre de
réparation (rescue-bench / ares : 5/18 avec le Guard contre 2/18 sans, +16,7 points, IC95 [0 ; +44]) est **relu et validé**
(audit rescue-bench, `rescue_bench/HOLO31_REFERENCE.json`) : on le cite toujours avec son IC, qui touche 0, et la mention « non
significatif à ce stade ». Page de la séquence : https://argos.martinbonan.com/artifacts/holo-guard-repair.html?t=mxehqaqs.SsRdAM7BfXxBtWZEUzqCHbXqFzQApOsO

## Choix des tâches pour le live
Sources : `verif_study/manifest.json` (268 épisodes), `judge_bench/claude_responses.jsonl`, `feci_guard/smoke/impress_550ce7e7_guard.md`,
`~/osw/duels/*/events.jsonl`. **Splits** : 550ce7e7 et 8979838c viennent du split **diagnostic** ; b8adbc24, 9f935cce et bedcedc4 viennent
du split de **test** (le dire si on le demande : ce sont les tâches de démo choisies hier, où l'original a fait un faux « fini »).

| Rang | Tâche | Faux succès de l'original | Durée jusqu'au faux « fini » | Refus du Guard (texte réel) | Risques |
|---|---|---|---|---|---|
| **1 (live)** | `libreoffice_impress/550ce7e7-747b-495f-b122-acdc4d0b8e54` : barrer les lignes 1 et 2 | **4/4** passages | 7 pas, 20-67 s d'agent → ~1:45-2:45 après START (**estimé**) | Claude refuse 4/4 hors ligne ; en vrai (smoke) : ✗ « 2e ligne barrée entièrement » — *« la sélection et le barré s'arrêtent à “Requ”, “ests.” n'est pas barré »* | Même réparé à vue, l'évaluateur officiel a mis 0 (smoke) : à droite, ne pas promettre de ✓. Jamais lancée en duel ; un seul run Guard (smoke), 1re réponse au pas 29. |
| **2 (secours)** | `libreoffice_impress/b8adbc24-cef2-4b15-99d5-ecbe7ff445eb` : titre « Online Shopping » comme le précédent | **5/5** duels | 6-9 pas ; faux « fini » mesuré à 104-159 s après START (5 duels) | Duel 074039 : ✗ « position du titre identique » — *« sur la diapo 1 le titre est centré, sur la diapo 2 il est aligné à gauche »* (2 refus, pas 7 et 11) | Split de **test**. Preuve moins visible (vignettes) ; à droite, l'agent dérive ensuite jusqu'à 50 pas : STOP indispensable. Duel Guard 074039 fait avec le vérificateur d'avant 07:43. |
| 3 | `libreoffice_impress/8979838c` : fond violet + titre dans les notes | 3/4 | 10 pas | ✗ faute de frappe « Sohuld » dans les notes | Visible seulement dans le panneau des notes ; jamais passé sous le Guard en vrai. |
| — écartées | `chrome/9f935cce`, `os/bedcedc4` | 3/4 ; 1/1 | 5-13 pas | pas de run Guard | 9f935cce : l'original réussit parfois ; bedcedc4 : tâche probablement infaisable, histoire confuse. |

**Répétitions (fenêtre online-eval 11:00-11:30 UTC, réservée par ares)** : (1) 550ce7e7, (2) b8adbc24, (3) 550ce7e7 si le temps le
permet. Résultats ci-dessous, à remplir **uniquement** avec les verdicts enregistrés (`bash osworld/duel/duel.sh list`).

| Répétition | Duel id | Gauche : faux « fini » à (s) / verdict | Droite : refus à (s) / exigence ✗ lisible ? | Verdict |
|---|---|---|---|---|
| R1 550ce7e7 | _à remplir_ | | | |
| R2 b8adbc24 | _à remplir_ | | | |
| R3 550ce7e7 | _à remplir_ | | | |

Le **meilleur** duel répété devient le replay du plan B (son id va dans le cockpit).

## Plans B et C (décider vite, le dire franchement)
- **Point de décision 1 (1:45)** : un côté en `error`, pas de VM, ou refus « RAM » au lancement → **plan B immédiatement**.
- **Point de décision 2 (2:15-3:45)** :
  - Gauche **réussit vraiment** (T=0,8, ça arrive) → le dire : « cette fois il a réussi, c'est aléatoire ; dans nos 4 runs de cette
    tâche, il avait dit “fini” à tort. Voici un cas enregistré » → replay du plan B, ×2, sauter au refus.
  - Droite **n'a pas encore répondu** quand la gauche a fini (même aléa) → montrer d'abord le FAUX SUCCÈS de gauche, continuer les
    slides, revenir à droite à 5:00 ; pas de refus à 5:30 → replay du refus.
  - Droite : le Guard **accepte** un faux « fini » (il en laisse passer ~1 sur 3) → le dire tel quel (« 68 %, pas 100 % ») → replay.
  - Rien à 3:45 → continuer les slides, revenir au duel à 5:00 ; toujours rien → replay.
- **Plan B — replay** : même page, `http://127.0.0.1:8765/?replay=<id>` (lien dans le cockpit), vitesse ×2. Annoncer ce qui est vrai :
  « l'enregistrement de notre répétition de ce matin, à <heure>, sur <tâche>, même page, même code ». Après les répétitions, l'id du
  meilleur duel remplace celui du cockpit. Réserve d'ici là : `20261108-074039_libreoffice_impress_b8adbc24-cef2-4b15-9`
  (enregistré à 07:40 UTC, tâche b8adbc24 du split de test ; faux « fini » à gauche à 155 s, refus à droite à 141 s et 204 s ;
  vérificateur d'avant la correction de 07:43, à dire si on le demande).
- **Plan C — vidéo** (réseau ou tunnel morts) : `holo-demo-video.mp4`, **copie locale sur le portable**, plus la démo pas à pas
  `holo-demo-faux-fini.html` téléchargée. Annoncer : « une vidéo enregistrée cette nuit ».
- Ne jamais présenter un replay ou la vidéo comme du live.

## Ce qui reste hors de mon périmètre (pour ares)
- **Slides** : la page système (`holo-pitch-system.html`, 07:08 UTC) ne parle pas encore de Feci Guard. Il faut 2 slides : « Feci
  Guard : comment » et « 268 épisodes : 68 % / 10 %, Holo-3.1 au hasard, Holo4 +23 ».
- **Gel des ressources pendant les passages** : le duel exige ≥ 15 Go de RAM libres et le vLLM 8000 du pod. Aucune VM d'autres
  agents de 13:15 à 14:00 UTC, ni de 14:30 à 15:15 UTC (finales).
- **Dépôt GitHub privé** : un lien `jury_kit/` sur GitHub ne s'ouvre pas pour le jury. À décider par Martin : rendre public, ou
  partager le kit autrement.
