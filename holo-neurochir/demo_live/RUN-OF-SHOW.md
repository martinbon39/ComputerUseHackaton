# RUN-OF-SHOW — pitch Holo × Feci Guard, avec duel LIVE (jury H Company × 42AI)

> demo-director, 2026-11-08 ~09:45 UTC. Chiffres : `judge_bench/REPORT.md`, `paper/generated/*.tex`, `jury_kit/RESULTS.md`,
> `~/osw/duels/`. Aucun gain OSWorld n'est affirmé : le Guard **détecte**, il ne **répare** pas encore.
> Résultat en ligne (`report/ONLINE_GUARD_RESULT.md`) : faux « fini » de 22,5 % à 10,8 % (significatif), score +1,6 (non significatif).
> Heures (page Luma, `pitch/PITCH.md`) : dépôt 14:00, 1er tour de jury 14:30, finales 15:45 (Paris) = **13:00 / 13:30 / 14:45 UTC**.
> Heure exacte de passage : **à confirmer par Martin**.

## L'idée en une phrase
« Les agents computer-use disent *c'est fini* alors que non. On a tenté de l'enlever de leurs poids : ça ne marche pas, et on
sait pourquoi. Alors on a construit un vérificateur externe qui l'attrape, et vous allez le voir faire en direct. »

## Le moment LIVE (le cœur, 25 % Computer Use + 10 % UX/contrôle)
Page du duel `http://127.0.0.1:8765/` (via le tunnel), preset **« Feci Guard, Modal »** (`modal_guard` ; le pod ne sert plus depuis
~10:40 UTC), case **Feci Guard à droite** cochée. Agent Modal **réveillé à T−3 min** (commande dans la checklist).
- **Tâche n°1 : `libreoffice_calc/1de60575`** (split **diagnostic**) : « résumer le chiffre d'affaires par type de promotion dans une
  nouvelle feuille (**Sheet2**) avec un tableau croisé ». Répétition R1 (11:00 UTC, `20261108-110023…`), chronologie **mesurée** :
  - +139 s : la gauche dit « fini » → +165 s : verdict officiel **0**, bandeau **FAUX SUCCÈS** ;
  - +144 s : la droite dit « fini » → le Guard **REFUSE** : ✗ « la feuille doit s'appeler Sheet2 », ✗ « les noms de promotions en
    en-têtes de colonnes » ;
  - la droite répare, puis +215 s : le Guard **accepte** → +242 s : verdict officiel **1**.
  T=0,8 : rien ne garantit la même issue (voir les répétitions suivantes et les plans B/C).
- **Tâche n°2 : `libreoffice_impress/550ce7e7`** (barré, split diagnostic) : l'original y a dit « fini » à tort 4 fois sur 4, et le Guard
  refuse avec une preuve visible (« le barré s'arrête à “Requ” »). En revanche, la réparation n'y réussit pas (l'écart est dans le fichier) :
  on montre le refus, puis **STOP**.
- **Fiabilité mesurée : 2 arcs complets sur 3 duels valides** (R1, R3 ; en R2, la gauche réussit vraiment ; R4 est exclu pour panne d'infra), avec un calendrier régulier quand ça marche : refus à droite
  entre +144 et +172 s, FAUX SUCCÈS à gauche entre +165 et +206 s, Guard qui accepte à ~+216 s, **score 1 à ~+243 s**. En R2, la gauche
  a vraiment réussi et la droite a erré 50 pas sans répondre.
- **Stratégie retenue (hybride)** : le duel est lancé à 0:00 et montré à 2:15. Le jury voit deux vrais bureaux en action, ce qui
  prouve que c'est réel. **Décision à 3:30** (= +210 s) :
  - FAUX SUCCÈS à gauche **et** refus à droite déjà affichés → on **reste en live** jusqu'au score de droite (~4:05) ;
  - sinon → une phrase honnête : *« l'agent est stochastique, aujourd'hui il a fait autre chose ; voici ce que le Guard fait quand
    il ment, enregistré ce matin, même tâche, même page »* → replay de R1 (`20261108-110023…`, ×2, sauter à +130 s : ~60 s jusqu'au
    score 1). Le duel live continue en arrière-plan, et on y revient en Q&R s'il a fini.
  - Le replay de R1 est **ouvert à l'avance** dans l'onglet voisin du live.
  - Second replay de secours : R3 `20261108-111313_libreoffice_calc_1de60575-bb6e-4c3d-9e6a` (11:13 UTC, même arc, score 1 à +243 s).
  - Pourquoi 3:30 et pas 3:00 : en R3, le FAUX SUCCÈS de gauche n'est apparu qu'à +206 s (3:26). Une bascule à 3:00 aurait abandonné un live réussi.
- **Contrôle humain** : le bouton **■ STOP** reste sous la main de Martin. Il s'en sert si la droite dérive : pas de nouvelle réponse
  ~90 s après un refus, ou un 2e refus. « Le Guard me dit pourquoi ce n'est pas fini ; c'est moi qui décide d'arrêter. »
- Ne jamais promettre le ✓ à droite : « s'il répare, tant mieux ; ce que le Guard garantit, c'est qu'on ne vous ment pas ».

## Déroulé minute par minute (cible 6:10, plafond 7:00, puis Q&R)
> Durée du créneau **non confirmée** (le brief dit 5 à 7 min ; `pitch/PITCH.md` prévoyait 3 min). En version 3 min : garder 0:00 LANCER, le problème (20 s), la chirurgie (30 s), le duel (75 s), les chiffres du Guard (30 s), la fin (10 s).
Le minuteur est dans le cockpit (`demo_live/cockpit.html`, touche Espace).

| Temps | Écran | Ce que fait / dit Martin | Critère coché |
|---|---|---|---|
| **−2:00** (avant d'être appelé) | Duel | Page du duel ouverte, preset et tâche choisis, case Guard cochée, **ne pas lancer**. RAM ≥ 15 Go vérifiée par `free -g` (la page n'affiche pas la RAM ; elle refuse seulement au lancement). Onglets prêts (voir checklist). | — |
| **0:00-0:15** | Duel | **Appuie sur ▶ LANCER.** « Je lance tout de suite deux agents sur deux vrais bureaux Ubuntu, dans des VMs sur notre serveur. Même modèle, celui de H, Holo-3.1-4B, même tâche. Une seule différence : à droite, notre vérificateur, avec Claude pour juge. On y revient dans deux minutes. » | Computer Use |
| **0:15-0:45** | Slides : le problème | « Quand Holo échoue sur OSWorld, **57 % de ses échecs sont des faux “fini”** : 29 sur 51, sur 120 tâches de diagnostic. Il ne se trompe pas de bouton, il se trompe sur lui-même. Et l'utilisateur, lui, le croit. » | Utilité |
| **0:45-1:45** | Slides : la chirurgie (négatif) | « Notre première idée : retirer ce défaut directement des poids, sans entraînement. Une nuit, un labo autonome d'agents IA, seuil de décision figé avant le verdict (gain seulement si la borne basse de l'IC95 est > 0), relecteurs adversariaux. Résultat honnête : **+1,9 point, IC95 [−4,3 ; +8,0] sur 165 tâches : pas de gain détectable.** Et on sait pourquoi : à l'intérieur, le modèle ne distingue pas un faux “fini” d'un vrai, pas mieux que le simple numéro du pas. On ne peut pas couper un signal qui n'existe pas. Il faut une information **extérieure**. » | Originalité, exécution technique |
| **1:45** | Coup d'œil au duel | Point de décision n° 1 (voir « Plans B/C ») : les deux côtés affichent des pas ? Sinon (erreur, pas de VM), replay de R1 directement. | — |
| **1:45-2:15** | Slides : Feci Guard | « Feci Guard regarde l'écran au moment où l'agent dit “fini”, liste chaque exigence de la tâche, la marque ✓ ou ✗ avec sa preuve visuelle, et refuse le “fini” si une exigence est visiblement fausse. Il ne change rien au modèle de H, il se branche sur le dernier appel. » | Utilité, UX |
| **2:15-4:15** | **DUEL (plein écran)** | **Le moment live.** ~2:20 gauche : « Il dit : *tâche terminée*. » → ~2:45 bandeau officiel **FAUX SUCCÈS**. ~2:25 droite : « Même phrase, mais le Guard vérifie… **refus** : <lire l'exigence ✗ affichée, par exemple “la feuille ne s'appelle pas Sheet2” ou “les promotions ne sont pas en en-têtes de colonnes”>, voilà la preuve. » L'agent reçoit la raison et corrige, sous nos yeux. ~3:35 : le Guard accepte → ~4:00 : verdict officiel **✓ 1**. « Même modèle, même tâche : à gauche, un mensonge à 0 ; à droite, un succès à 1. » Si la droite dérive : **STOP** (« c'est moi qui décide »). Pendant l'attente (2:50-3:35) : parler de la mesure en ligne (ligne 4:15). | **Computer Use, UX et contrôle** |
| *(plan B seulement)* | Séquence enregistrée « l'agent répare » (`repair_calc.html`) | À montrer **uniquement** si la réparation n'a pas eu lieu en live : « voici le même scénario, enregistré : refus, 5 pas, score officiel 1 ». Dire que c'est **enregistré** et **choisi**. Chiffre agrégé (`rescue_bench/HOLO31_REFERENCE.json`) : 5/18 branches à score 1 avec le Guard contre 2/18 sans, IC95 [0 ; +44], **non significatif à ce stade** ; dont **3 vraies réparations contre 0** (les autres sont notées 1 sans aucune action nouvelle). | Utilité |
| **4:15-5:00** | Slides : les chiffres du Guard | « Ce n'est pas un cas choisi. **En ligne, sur les 120 tâches de test tenues à part, le Guard divise par deux les faux “fini” : de 22,5 % à 10,8 %**, écart significatif (−11,7 points, IC [−19,2 ; −4,2]). Le score, lui, ne bouge pas de façon mesurable (+1,6, IC [−4,4 ; +7,7]) : on ne revendique **aucun gain de score**. Hors ligne, sur 268 épisodes : Claude attrape 68 % des faux succès pour 10 % de faux rejets ; Holo-3.1 qui juge son propre travail est au hasard ; Holo4-27B avec le même prompt fait déjà +23 points. Coût : ~6 s et ~0,03 $ par vérification. » | Utilité, exécution technique |
| **5:00-5:40** | Slides : le système | « Tout ça a été fait par un labo d'agents d'environ 25 agents, avec des protocoles préenregistrés et des relecteurs adversariaux. Ces relectures ont attrapé des erreurs qui, sans elles, nous auraient fait annoncer un effet. Plus d'un millier d'épisodes OSWorld ont été notés. Un humain supervise sur le canvas, avec des règles d'arrêt automatiques. Et tout est vérifiable : le kit jury, la fusion reproduite au bit près sur une autre machine, la sonde en ligne. » | Originalité, exécution, UX |
| **5:40-6:10** | Slide de fin | « Pour H : une retouche de poids à bas coût ne suffit pas, la correction passe par un **vérificateur externe** ou par l'**entraînement**. La prochaine étape, c'est de mesurer la réparation à grande échelle : vous en avez vu un cas, la mesure est en cours. Nous, on a vérifié avant de dire *c'est fait*. Merci. » | Utilité, clarté |
| **6:10-** | Q&R | Fiche `CHECKLIST_JOUR_J.md` § Q&R. Garder le duel ouvert : on peut **rejouer** le refus (bouton replay, ×2). | Clarté et Q&R |

Règles d'oral : ne jamais dire « le Guard améliore le score » (+1,6, non significatif) ; dire « divise par deux les faux “fini” » (significatif, en ligne) ; dire « détecte », « refuse », « attrape ». Le chiffre de
réparation (rescue-bench : 5/18 branches à score 1 avec le Guard contre 2/18 sans, +16,7 points, IC95 [0 ; +44] ; recalcul indépendant [0 ; +39]) est **relu et validé**. À dire exactement : « 3 vraies réparations contre 0 » (2 des 5 succès avec le Guard et les 2 succès sans le Guard sont notés 1 sans aucune action nouvelle, sur 8979838c)
(audit rescue-bench, `rescue_bench/HOLO31_REFERENCE.json`) : on le cite toujours avec son IC, qui touche 0, et la mention « non
significatif à ce stade ». Page de la séquence : https://argos.martinbonan.com/artifacts/holo-guard-repair.html?t=mxehqaqs.SsRdAM7BfXxBtWZEUzqCHbXqFzQApOsO

## Choix des tâches pour le live
Sources : `~/osw/feci_demo/calc_1de60575/`, `verif_study/manifest.json` (268 épisodes), `judge_bench/claude_responses.jsonl`, `feci_guard/smoke/impress_550ce7e7_guard.md`,
`~/osw/duels/*/events.jsonl`. **Splits** : 1de60575, 550ce7e7 et 8979838c viennent du split **diagnostic** ; b8adbc24, 9f935cce et bedcedc4 viennent
du split de **test** (le dire si on le demande : ce sont les tâches de démo choisies hier, où l'original a fait un faux « fini »).

| Rang | Tâche | Faux succès de l'original | Durée jusqu'au faux « fini » | Refus du Guard (texte réel) | Risques |
|---|---|---|---|---|---|
| **1 (live)** | `libreoffice_calc/1de60575-bb6e-4c3d-9e6a-2fa699f9f197` : tableau croisé dans une nouvelle feuille « Sheet2 » | 1/1 enregistré (results_diag, score 0) ; R1 en live : faux « fini », score 0 | 12 pas ; faux « fini » à +139 s en R1 | ✗ « Pivot table is on a sheet named Sheet2 », ✗ « Promotion names are the column headers » (R1). **Réparation** : score 1 en R1 et dans 2/2 branches rejouées ; 0/2 sans le Guard | Une seule répétition live à ce stade ; T=0,8. |
| **2** | `libreoffice_impress/550ce7e7-747b-495f-b122-acdc4d0b8e54` : barrer les lignes 1 et 2 | **4/4** passages | 7 pas, 20-67 s d'agent → ~1:45-2:45 après START (**estimé**) | Claude refuse 4/4 hors ligne ; en vrai (smoke) : ✗ « 2e ligne barrée entièrement » — *« la sélection et le barré s'arrêtent à “Requ”, “ests.” n'est pas barré »* | Même réparé à vue, l'évaluateur officiel a mis 0 (smoke) : à droite, ne pas promettre de ✓. Jamais lancée en duel ; un seul run Guard (smoke), 1re réponse au pas 29. |
| **3** | `libreoffice_impress/b8adbc24-cef2-4b15-99d5-ecbe7ff445eb` : titre « Online Shopping » comme le précédent | **5/5** duels | 6-9 pas ; faux « fini » mesuré à 104-159 s après START (5 duels) | Duel 074039 : ✗ « position du titre identique » — *« sur la diapo 1 le titre est centré, sur la diapo 2 il est aligné à gauche »* (2 refus, pas 7 et 11) | Split de **test**. Preuve moins visible (vignettes) ; à droite, l'agent dérive ensuite jusqu'à 50 pas : STOP indispensable. Duel Guard 074039 fait avec le vérificateur d'avant 07:43. |
| 4 | `libreoffice_impress/8979838c` : fond violet + titre dans les notes | 3/4 | 10 pas | ✗ faute de frappe « Sohuld » dans les notes | Visible seulement dans le panneau des notes ; jamais passé sous le Guard en vrai. |
| — écartées | `chrome/9f935cce`, `os/bedcedc4` | 3/4 ; 1/1 | 5-13 pas | pas de run Guard | 9f935cce : l'original réussit parfois ; bedcedc4 : tâche probablement infaisable, histoire confuse. |

**Répétitions (fenêtre online-eval 11:00-11:30 UTC, réservée par ares)** : (1) 550ce7e7, (2) b8adbc24, (3) 550ce7e7 si le temps le
permet. Résultats ci-dessous, à remplir **uniquement** avec les verdicts enregistrés (`bash osworld/duel/duel.sh list`).

| Répétition | Duel id | Gauche : faux « fini » à (s) / verdict | Droite : refus à (s) / exigence ✗ lisible ? | Verdict |
|---|---|---|---|---|
| R1 **calc/1de60575** (tâche choisie par online-eval) | `20261108-110023_libreoffice_calc_1de60575-bb6e-4c3d-9e6a` | faux « fini » à +139 s, verdict officiel **0** (FAUX SUCCÈS) à +165 s, 12 pas | **REFUS à +144 s** : ✗ « Pivot table is on a sheet named Sheet2 », ✗ « Promotion names are the column headers » ; réparation, puis **accepté à +215 s**, **score officiel 1** à +242 s | **Arc complet en live en 4:02 → devient la tâche live n°1** |
| R2 **calc/1de60575** | `20261108-110716_libreoffice_calc_1de60575-bb6e-4c3d-9e6a` | « fini » à +145 s, mais **vraie réussite** : score **1** à +171 s, 14 pas | **jamais de réponse** : 50 pas, score 0 à +329 s ; le Guard n'a rien eu à vérifier | **Image inversée** : le live est un pari (1 bonne issue sur 2) → règles de bascule ci-dessous |
| R3 **calc/1de60575** | `20261108-111313_libreoffice_calc_1de60575-bb6e-4c3d-9e6a` | « fini » à +180 s, verdict **0** (FAUX SUCCÈS) à +206 s, 21 pas | **REFUS à +172 s** (✗ « Promotion names appear as column headers ») ; accepté à +217 s ; **score 1** à +243 s | **Arc complet en 4:03** |
| R4 **calc/1de60575** (bench-wall, 11:59) | `20261108-115902_libreoffice_calc_1de60575-bb6e-4c3d-9e6a` | vraie réussite à gauche | 1 refus du Guard, puis **panne d'infra** : le serveur de captures de la VM tombe (`side.log` : « screenshot failed… too many consecutive errors; ending episode early »), score 0 | **Exclu (infra failure)**, à cause de la cadence de capture à 1 s, revenue depuis à 2 s. Bilan : **2 arcs sur 3 duels valides** |

Le **meilleur** duel répété devient le replay du plan B (son id va dans le cockpit).

## Plans B et C (décider vite, le dire franchement)
- **Point de décision 1 (1:45)** : un côté en `error`, pas de VM, ou refus « RAM » au lancement → **plan B immédiatement**.
- **Point de décision 2 (2:15-3:45)** :
  - Gauche **réussit vraiment** (T=0,8, ça arrive) → le dire : « cette fois il a réussi, c'est aléatoire » → replay de R1 (`20261108-110023…`), ×2, sauter au refus.
  - Droite **n'a pas encore répondu** quand la gauche a fini (même aléa) → montrer d'abord le FAUX SUCCÈS de gauche, continuer les
    slides, revenir à droite à 5:00 ; pas de refus à 5:30 → replay du refus.
  - Droite : le Guard **accepte** un faux « fini » (il en laisse passer ~1 sur 3) → le dire tel quel (« 68 %, pas 100 % ») → replay.
  - Rien à 3:45 → continuer les slides, revenir au duel à 5:00 ; toujours rien → replay.
- **Plan B — replay** : même page, `http://127.0.0.1:8765/?replay=<id>` (lien dans le cockpit), vitesse ×2. Annoncer ce qui est vrai :
  « l'enregistrement de notre répétition de ce matin, à <heure>, sur <tâche>, même page, même code ». Après les répétitions, l'id du
  meilleur duel remplace celui du cockpit. **Replay par défaut : R1 `20261108-110023_libreoffice_calc_1de60575-bb6e-4c3d-9e6a`** (11:00 UTC, arc complet, vérificateur actuel). Ancienne réserve : `20261108-074039_libreoffice_impress_b8adbc24-cef2-4b15-9`
  (enregistré à 07:40 UTC, tâche b8adbc24 du split de test ; faux « fini » à gauche à 155 s, refus à droite à 141 s et 204 s ;
  vérificateur d'avant la correction de 07:43, à dire si on le demande).
- **Plan C — vidéo** (réseau ou tunnel morts) : `holo-demo-video.mp4`, **copie locale sur le portable**, plus la démo pas à pas
  `holo-demo-faux-fini.html` téléchargée. Annoncer : « une vidéo enregistrée cette nuit ».
- Ne jamais présenter un replay ou la vidéo comme du live.

## Ce qui reste hors de mon périmètre (pour ares)
- **Slides** : la page système (`holo-pitch-system.html`, 07:08 UTC) ne parle pas encore de Feci Guard. Il faut 2 slides : « Feci
  Guard : comment » et « 268 épisodes : 68 % / 10 %, Holo-3.1 au hasard, Holo4 +23 ».
- **Gel des ressources pendant les passages** : le duel exige ≥ 15 Go de RAM libres et l'agent servi par Modal (compte 1), réveillé à T−3 min (commande dans la checklist). Aucune VM d'autres
  agents de 13:15 à 14:00 UTC, ni de 14:30 à 15:15 UTC (finales).
- **Dépôt GitHub privé** : un lien `jury_kit/` sur GitHub ne s'ouvre pas pour le jury. À décider par Martin : rendre public, ou
  partager le kit autrement.
