# PITCH — Neurochirurgie de Holo (3 min, jury H Company × 42AI)

> Écrit le 2026-11-07 vers 19:10 UTC par la session `pitch`. Chiffres tirés de `JOURNAL.md` et `team_dash/status.json` uniquement.
> Les cases `[À REMPLIR]` attendent un résultat qui n'est pas encore mesuré. On ne les remplit qu'avec un chiffre écrit dans JOURNAL.md.
> Deck publié : https://argos.martinbonan.com/artifacts/holo-pitch-deck.html?t=mxdng2xy.fTgitZHpq6TudQD8NPuFyMYMlfrJ2G4f · source `pitch/deck.html` (touche **B** pour basculer entre les versions A et B des résultats, **N** pour afficher ce texte en notes).

## Contraintes du jour (source : page Luma de l'événement, relevée dans `research_notes/Problèmes frontier de H/h_stated_problems.md`)

- Dimanche 8 nov. : **14:00** dépôt, **14:30** premier tour de jury, **15:45** pitchs finaux, **17:45** résultats (heure de Paris).
- Livrable demandé : une démo qui montre « the problem, the actions your agent takes, and the result ». Aucun critère de jugement publié.
- Prix spécifiques : Best Use of Gladia 1 000 €, Best Use of Devin 1 000 €. Une intégration partenaire visible peut donc rapporter un prix à part.
- **Budget GPU** : le pod coûte 5,29 $/h depuis 14:37 UTC samedi, plafond 90 $ (≈ 17 h). À ce rythme, le plafond tombe vers **07:40 UTC dimanche**. Une démo live qui fait tourner le 4B à 15:45 demande de garder ou relancer le pod 1 h autour du pitch (≈ 5 $). **Décision pour ares / Martin.**

## Le fil rouge en une phrase

Holo-3.1-4B échoue surtout parce qu'il croit avoir réussi. On cherche dans ses activations la direction qui porte ce « c'est fait » mensonger, pour la retirer de ses poids sans entraînement (version A : ça marche ; version B : on prouve où ça s'arrête), avec un protocole qui vérifie chaque étape avant de crier victoire. Notre phrase de fin, quelle que soit la version : **« Nous, on a vérifié avant de dire c'est fait. »**

## Pitch minute par minute (~430 mots parlés, ≈ 150 mots/min)

| Temps | Bloc | Slide | Ce qu'on dit (texte à dire, à adapter à l'oral) |
|---|---|---|---|
| 0:00-0:20 | **Accroche** | 1 | « Hier après-midi, on a demandé à Holo-4B d'installer Spotify. Il a lancé l'installation, il est tombé sur le mot de passe, et il a répondu : *installation lancée avec succès*. Score : zéro. Holo ne s'est pas trompé de bouton. Il s'est trompé sur lui-même. » |
| 0:20-0:45 | **Le problème que H connaît** | 2 | « Chez H, vous l'écrivez vous-mêmes : *validation is harder than policy making*. On a mesuré l'ampleur du problème. Sur 119 tâches OSWorld, dans de vraies VMs Ubuntu, Holo-3.1-4B réussit 55,5 %. Et sur 112 tâches, 98 % de ses échecs sont de deux types : il annonce *c'est fini* alors que non, ou il s'enlise jusqu'à la limite de 50 pas. C'est le profil où la méthode du MIT a gagné gros : des obstacles à retirer, pas un trou de compétence. » |
| 0:45-1:05 | **Notre idée** | 3 | « Le 2 novembre, le MIT a montré qu'on peut réparer un modèle en éditant directement ses poids, sans gradient. Tout le monde l'a fait sur des maths. Nous, sur un agent qui utilise un ordinateur. Trois gestes : lire ses activations à chaque pas, trouver la direction qui précède le faux *c'est fait*, et la retirer de quelques colonnes de ses poids. » |
| 1:05-2:05 | **Démo** | 4 → 5 → dashboard | 10 s sur le banc (slide 4, pour la crédibilité), puis 50 s de démo (voir « Plan de démo »). Fil : « À gauche, l'original. Regardez la jauge sous l'écran : c'est la projection de son état interne sur la direction défaut, couche par couche. Elle monte… et il répond *c'est fait*. » Version A : « À droite, le même Holo opéré, même tâche. La jauge reste plate, il continue, il réussit. » Version B : « Sur le 0,8B, une direction de ses activations repère l'enlisement : on sait le lire. La question était : peut-on le couper ? » (ce que montre la jauge du 4B : **[À REMPLIR]** ; les courbes de la slide 5 sont un schéma) |
| 2:05-2:35 | **Résultats** | 6A ou 6B | Voir les deux versions ci-dessous. |
| 2:35-2:50 | **Ce qu'on a appris** | 7 | « Trois leçons. Détecter n'est pas causer : on teste toujours le comportement avant d'éditer. Le modèle qu'on analyse doit être celui qui joue : on a attrapé un “4B” qui était en fait un 0,8B. Et le harness compte autant que les poids : sur le 0,8B et MiniWoB, recadrer l'écran a fait passer le grounding de 8 % à 100 %. » |
| 2:50-3:00 | **La suite / fin** | 8 → 9 | « Tout est réutilisable : le skill *weight-surgery*, la taxonomie d'échecs, l'outil de rejeu exact, sur n'importe quel modèle à poids ouverts. Holo nous a appris une chose : il ne faut pas dire *c'est fait* trop tôt. Nous, on a vérifié avant. Merci. » |

### Résultats, version A : la chirurgie donne un gain OSWorld (slide 6A)

À dire seulement si JOURNAL.md contient le résultat sur `split_test` avec IC.

> « Sur 120 tâches de test qu'on n'avait jamais regardées, Holo-4B original fait **[À REMPLIR] %**, opéré **[À REMPLIR] %**, IC 95 % **[À REMPLIR]**. Les faux succès passent de **[À REMPLIR]** à **[À REMPLIR]**. On a modifié **[À REMPLIR] poids, [À REMPLIR] % du modèle**. Les contrôles : le prompt correctif fait **[À REMPLIR]**, une direction aléatoire de même taille fait **[À REMPLIR]**, et les tâches faciles ne perdent pas plus de **[À REMPLIR]** points. »

Règles pour la version A :
- Toujours dire l'IC. Si l'IC de la différence appariée contient 0, **on passe en version B** (le brief §11 l'interdit : « ne pas présenter un gain dans le bruit comme un résultat »).
- Ne jamais comparer à 75,8 % (chiffre interne de H, autre harness). Seule la comparaison dans notre harness compte (brief §11). On peut dire « même harness, mêmes tâches, mêmes VMs ».
- Si le prompt correctif fait aussi bien que le patch : le dire, c'est le contrôle le plus attendu par un jury technique.

### Résultats, version B : résultat négatif honnête (slide 6B)

> « Le défaut est réel : 98 % des échecs, de type retirable. On sait le lire : sur le 0,8B, une seule direction détecte l'enlisement avec une AUROC de 0,89, contre 0,72 pour un indice trivial. Mais l'effacer ne guérit pas. Quand GPT-6 Astra la retire des poids, les bonnes actions sont abîmées quatre fois plus que les mauvaises. Même avec le meilleur réglage pendant la génération (une direction par couche), il répète encore 81 % du temps au lieu de 96, et ses pas sains tombent de 75 à 58 %. Et sur le 4B, quand on régénère sa réflexion, il redit *answer* 8 fois sur 8 sur ses faux « fini », exactement comme sur ses vrais. C'est un thermomètre, pas un interrupteur. On l'a prouvé proprement, avec un split figé avant le moindre patch, donc personne n'aura à refaire ce chemin à l'aveugle. »

Pourquoi la version B reste forte (à garder en tête, pas forcément à dire) :
- **Science** : le MIT annonce un gain ; on montre où la méthode s'arrête sur un agent GUI, avec des contrôles (direction aléatoire, baselines de position, test comportemental). Un jury technique respecte un négatif bien instrumenté plus qu'un positif fragile. Les critères de type Apart Research (avancer le domaine, code reproductible) récompensent exactement ça.
- **Outillage** : OSWorld monté sur un VPS en Docker+KVM, rejeu exact des activations (mêmes tokens que vLLM sur 12/12 pas), taxonomie d'échecs mécanique, split figé avec sha1. C'est ce qui manque à quiconque veut faire de l'interprétabilité sur un agent computer use.
- **Skill réutilisable** : `weight-surgery` encode la procédure et chaque leçon mesurée aujourd'hui (« détecter n'est pas causer », baselines triviales, test causal avant édition). Un autre agent peut le rejouer sur Holo4 ou n'importe quel modèle ouvert.
- **Ouverture produit** (à dire seulement si mesuré) : la jauge comme **détecteur** temps réel, qui déclenche une vérification avant `answer`. Le brief le prévoit en plan B (§10). Gain mesuré : **[À REMPLIR]**, sinon ne pas le présenter comme un résultat.
- Chiffre 4B à ajouter dès qu'il existe : **AUROC de la direction faux succès sur le 4B [À REMPLIR]**, et le verdict des 6 pistes Astra du 4B **[À REMPLIR]**.

### Questions probables du jury (réponses courtes)

- *« 55,5 %, c'est loin de vos 75,8 %. Votre harness est cassé ? »* : harness de RealtimeGUI (harness officiel de H, vLLM 0.23), 50 pas max au lieu de 100. RealtimeGUI trouve ≈ 45,5 % à 100 pas. On ne compare que dans notre harness.
- *« Comment savez-vous que c'est un faux succès et pas un évaluateur cassé ? »* : labels fixés avant toute AUROC (sha1 noté dans JOURNAL). On a vu un cas limite (refus en clair de GIMP non reconnu par la regex) : exclu des labels, score officiel laissé à 0 pour rester comparable.
- *« Les activations viennent-elles bien du modèle qui joue ? »* : rejeu dans transformers, nombre de tokens identique à vLLM sur 12/12 pas, messages identiques à la vraie boucle d'agent sur 7/7 pas.
- *« Fuite entre diagnostic et test ? »* : 120 tâches diag / 120 test, disjointes par construction (tri sha1 par domaine), figées avant tout patch. Le test n'est lu qu'au run final.
- *« Pourquoi pas juste un prompt "vérifie avant de répondre" ? »* : c'est le bras 2 de l'évaluation. Résultat : **[À REMPLIR]**.

## Plan de démo

### Ce qu'on montre (60 s, ordre fixe)

1. **Banc (10 s, slide 4)** : une phrase sur l'infra, pour que le jury croie aux chiffres.
2. **Le mensonge, enregistré (20 s)** : extrait de `recording.mp4` d'un faux succès court, accéléré ×2. Candidats déjà enregistrés par le harness :
   - `os/94d95f96` (pilote 1, hors des deux splits, 12 pas) : le cas Spotify de l'accroche. **Premier choix** : il boucle avec l'accroche et n'est dans aucun split.
   - `chrome/480bcfea` (split diag, 4 pas, tâche officiellement infaisable) : il « désactive la nouvelle UI Chrome 2023 » en changeant un thème et répond succès. Très court, très lisible.
   - Chemin : `~/osw/results_*/pyautogui/screenshot/Holo-3.1-4B/<domaine>/<id>/recording.mp4` (chaque dossier contient aussi `report.html` et les captures `step_*.png`).
3. **L'IRM (30 s)** : le dashboard `dashboard/` en mode replay, deux panneaux (original / opéré), jauge ⟨h_l, u⟩ par pas avec seuil rouge, carte des couches opérées, tableau des 4 bras en bas.

### Ce qui est vraiment live, et le filet

- **Live sûr** : le dashboard IRM tourne en local et rejoue un épisode précalculé (WebSocket, pas de GPU). Il ne peut pas « rater » devant le jury. Lancement : `devcap python -m uvicorn dashboard.server:app --port 8000` depuis `holo-neurochir/`, puis `http://127.0.0.1:8000`.
- **Live optionnel** (seulement si le pod et les VMs tournent à 15:45, voir budget GPU plus haut) : lancer à 0:00 du pitch une tâche OSWorld courte sur le 4B dans une VM, et montrer son issue à 2:00. T=0,8 : le même faux succès peut ne pas se reproduire. On le présente comme « un essai en direct », jamais comme la preuve.
- **Filet** : si le dashboard casse, on passe sur la vidéo enregistrée du dashboard (même fenêtre, même durée). Si le projecteur ou le réseau tombe, le deck est un fichier HTML autonome : en garder une copie locale sur le portable qui présente (le lien argos demande le réseau).

### Manque à combler avant la démo (hors de mon périmètre, pour ares)

- **Le dashboard ne sait rejouer que des épisodes MiniWoB.** `holo/demo_record.py` produit `demo/<nom>.json` à partir de `holo.agent.run_episode` (MiniWoB) ; aucun `demo/*.json` n'existe encore. Pour OSWorld, il faut un convertisseur `traj.jsonl` + captures `step_*.png` + `acts.npz` (activations rejouées, sur le pod) + direction `.npz` → le format `{name, task, seed, goal, threshold, spec, n_layers, original:{steps, outcome}, patched:{steps, outcome}}`, avec pour chaque pas `{arm, t, img (PNG base64), action, text, gauge:{couche: valeur}, reward}`. Estimation : 1 à 2 h. Bonne tâche pour Devin (voir Partenaires).
- Version B : le panneau « opéré » peut montrer le même épisode rejoué avec le patch candidat (ce qu'il fait : **[À REMPLIR]**), ou être remplacé par le banc de neurochirurgie `demo_banc/banc.html` (figure interactive des neurones de la couche 15, touches 1-4). Attention : `banc.html` affiche des chiffres exploratoires (fold 0) qui ne sont pas dans JOURNAL ; à ne citer à l'oral qu'une fois écrits dans le journal.

### Quoi enregistrer, et quand

| Quand | Quoi | Qui |
|---|---|---|
| Ce soir, dès qu'un convertisseur OSWorld → demo JSON existe | 3 replays du dashboard (brief §8.2) : (1) Spotify `os/94d95f96`, (2) `chrome/480bcfea`, (3) un épisode réussi ou opéré **[À REMPLIR]**. Capture vidéo 1080p de la fenêtre du dashboard, 30-40 s chacun. | ares / worker démo |
| Ce soir | Garder les `recording.mp4` des deux faux succès ci-dessus dans un dossier démo local (ne pas dépendre de `~/osw` le jour J). | worker démo |
| Dimanche, dès le résultat final (avant 12:00) | Choisir A ou B, remplir les `[À REMPLIR]` du deck, réenregistrer le replay n°3 avec le vrai patch. | ares + pitch |
| Dimanche 12:00-13:30 | **Répétition chronométrée ×3** avec bascule vers la vidéo à 1:10 au moins une fois. Couper tout ce qui dépasse 3:00. | l'équipe |
| Dimanche avant 14:00 | Dépôt : repo + lien du deck + vidéo de démo. Copie locale du deck et des vidéos sur le portable du pitch. | Martin |

Outil d'enregistrement : OBS, ou une vidéo Playwright de la page du dashboard (le MCP navigateur sait enregistrer). Pas de `next dev` ni de serveur nu : `devcap` pour tout serveur.

## Partenaires : 2 intégrations légères qui servent la démo

Aucune clé partenaire n'est présente sur orbit (variables d'environnement vérifiées par nom uniquement). **Aucune intégration n'est donc faisable en moins d'une heure sans demander une clé.** Rien ci-dessous ne touche au pod GPU ni aux VMs OSWorld.

### 1. Gladia : le jury dicte la tâche, en français (recommandé, prix Best Use of Gladia 1 000 €)

- **Ce que ça fait** : un bouton « micro » dans le dashboard. Un juré dit la tâche (« ouvre les paramètres de Chrome et désactive le mode sombre »). Gladia la transcrit en direct, le texte s'affiche comme objectif de l'agent.
- **Pourquoi c'est crédible** : ça fait participer le jury, et la démo « montre le problème » à partir d'une demande réelle. En mode replay, on affiche la transcription et on enchaîne sur l'épisode enregistré le plus proche, annoncé comme tel (« voici le même type de tâche, enregistré ») ; en mode live (pod allumé), la transcription devient l'instruction de l'épisode.
- **Comment** : API live v2. Le serveur Python fait `POST https://api.gladia.io/v2/live` (en-tête `x-gladia-key`, `model: solaria-1`, PCM 16 kHz mono, `language_config: {languages: ["fr"]}`, transcriptions partielles activées) et renvoie seulement l'URL WebSocket au navigateur, qui envoie le micro et affiche les messages `transcript`. La clé reste côté serveur.
- **Effort** : ≈ 45 min à 1 h (un endpoint FastAPI + un AudioWorklet de rééchantillonnage + un champ texte). Un fichier dans `dashboard/`, donc à faire par ares ou un worker démo, pas par moi.
- **Clé nécessaire** : `GLADIA_API_KEY` (compte gratuit : 50 € de crédits à l'inscription selon leur page tarifs, soit des dizaines d'heures de temps réel ; à demander aussi sur place).

### 2. Devin : écrire le convertisseur OSWorld → IRM (prix Best Use of Devin 1 000 €)

- **Ce que ça fait** : on confie à une session Devin la tâche qui manque à la démo (le convertisseur décrit plus haut), avec un test : « le JSON produit est rejoué par `dashboard.server` sans erreur ».
- **Pourquoi c'est crédible** : c'est un vrai besoin, pas une décoration, et ça se raconte en une phrase dans le pitch (« le dashboard que vous voyez rejoue des épisodes convertis par Devin »). Le brief prévoyait Devin pour générer des mini-applis de test ; ce rôle a disparu avec le passage à OSWorld, celui-ci le remplace.
- **Comment** : API Devin v3, `POST https://api.devin.ai/v3/organizations/{org_id}/sessions`, corps `{"prompt": "…"}`, en-tête `Authorization: Bearer cog_…`. Devin a besoin d'accéder au code (dépôt GitHub) et à un exemple d'épisode.
- **Effort** : 30 à 60 min de supervision. Risque : le résultat arrive de façon asynchrone ; à lancer ce soir, pas pendant le pitch.
- **Clés nécessaires** : clé de service Devin (`cog_…`) et `org_id` ; plan à confirmer auprès de Cognition sur place (co-organisateur). L'accès du repo à Devin est une décision de Martin.

### Écartés

- **Linkup** (recherche web) : le brief l'imaginait pour chercher les modes d'échec connus avant le diagnostic. Ça n'apporte rien de visible à la démo, et pour vérifier un faux succès il ne voit pas l'état local de la VM (ce que testent la plupart des tâches OSWorld). Utilisable seulement comme panneau secondaire sur les tâches Chrome qui affirment un fait web (ex. « The monthly forecast for Manchester… »). Clé : `LINKUP_API_KEY`. Effort ≈ 30 min. Pas recommandé.
- **Stripe** : aucun usage honnête dans une démo de recherche.

## Méthode et sources de ce pitch

Pratiques appliquées : démo avant la 1:10 et ≈ 60 s de démo ; une seule idée par slide, texte ≥ 30 pt, fond sombre pour une salle peu éclairée ; plan B enregistré et répété ; limites dites franchement plutôt que surclamées ; pour un négatif, protocole et code reproductibles mis en avant.
- Reskilll, « Hackathon demo presentation tips », 21 août 2026 : https://blogs.reskilll.com/hackathon-demo-presentation-tips-pitch-3-minutes-win-2026/ (découpage 3 min, démo de secours, ce que les jurys pénalisent).
- JetBrains, « How to win a hackathon: notes from the judging table », juin 2026 : https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/ (« a strong project with a confusing demo loses… »).
- Apart Research (Esben Kran) sur LessWrong, 15 nov. 2024 : https://www.lesswrong.com/posts/snoXK5yhG4uaCjjmA/college-technical-ai-safety-hackathon-retrospective-georgia (critères : faire avancer le domaine, code reproductible).
- H Company : « validation is harder than policy making » (Surfer-H / Holo1, arXiv 2506.02865, 2025) ; page Luma du hackathon https://luma.com/hz9db5u9 ; Holo3.1 https://huggingface.co/blog/Hcompany/holo31 (2026-06-02).
- Partenaires : docs Gladia live v2 (https://docs.gladia.io/api-reference/v2/live/init.md), docs Devin API (https://docs.devin.ai/api-reference/overview.md), lues le 2026-11-07.
