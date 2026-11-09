# BRIEF : Neurochirurgie de Holo, VERSION LOCALE (hackathon H Company × 42AI)

> **Pour le Claude Code qui lit ce document.** Ce fichier est ta mission complète. Lis-le en entier avant d'agir. Lance-le comme un `/goal` :
>
> `/goal Exécute la mission décrite dans BRIEF_neurochirurgie_holo_LOCAL.md, phase par phase, en respectant les points de décision (GO / NO-GO), et livre les artefacts de la section 9.`
>
> **Version locale** : tout tourne sur le PC de l'utilisateur, avec un petit modèle. Pas de serveur distant, pas de DGX Spark. La section 2 dit comment détecter la machine et choisir la taille du modèle.
>
> Travaille de façon autonome. Ne t'arrête que sur les points de décision marqués **STOP** ou si une action est irréversible. Tiens un journal `JOURNAL.md` à la racine du projet (ce que tu as fait, les chiffres obtenus, les problèmes rencontrés), parce que l'équipe le lira pour le pitch.

---

## 0. TL;DR

- **Le projet** : on prend un petit modèle computer use de H Company (**Holo3.1-0.8B**, ou 4B si la machine le permet, poids ouverts Apache 2.0), on observe comment il échoue sur des tâches d'ordinateur, on trouve dans ses activations la « direction » responsable de son principal défaut (boucles d'actions répétées ou faux succès), et on la **retire de ses poids, sans aucun entraînement**. On mesure ensuite le gain sur des tâches jamais vues.
- **L'inspiration** : « Sparks of Weight-Space Programming » (MIT CSAIL, 2 nov. 2026). GPT-6 Astra a trouvé une direction liée aux boucles dans Qwen3.5-0.8B et l'a projetée hors de 64 colonnes `down_proj` dans les couches 15 et 19 (W' = W − u(uᵀW), soit 131 072 poids, 0,016 %). MATH-500 est passé de 7,9 % à 48,1 %. **Personne ne l'a encore appliqué à un agent GUI.** C'est notre contribution.
- **La démo** : deux Holo côte à côte sur la même tâche. L'original échoue, le patché réussit. Entre les deux, une « IRM » en temps réel montre la courbe d'activation de la direction défaut qui monte chez l'original et reste plate chez le patché.
- **Le matériel** : le PC de l'utilisateur (GPU NVIDIA, Mac Apple Silicon ou, en dernier recours, CPU). Un modèle de 0,8B est exactement la taille sur laquelle le MIT a fait sa démonstration : c'est un atout pour l'histoire, pas un compromis.

---

## 1. Contexte pour comprendre

- **Le hackathon** : H Company × 42AI, Paris, 7-8 novembre 2026. Il est jugé sur une démo live. Il faut utiliser H plus des partenaires (Gladia, Linkup, Devin, Stripe). H compte comme partenaire, Morning non. Le cœur du projet est H. Les partenaires sont secondaires, voir section 8.
- **H Company** : un lab parisien d'agents computer use, avec les modèles Holo (Holo4, Holo3.1, Holo3). Les modèles Holo sont des fine-tunes de la famille Qwen (Holo4-35B-A3B vient de Qwen3.6-35B-A3B, Holo3-35B-A3B de Qwen3.5-35B-A3B). Holo3.1 sort en 0.8B, 4B, 9B et 35B-A3B, tous en Apache 2.0.
- **Le problème que H reconnaît** : les agents échouent sur les tâches longues (sur OSWorld 2.0, Holo4-35B-A3B fait 30,9 % de crédit partiel et 12,3 % de succès strict, chiffres de H) et annoncent souvent un faux succès (« done » alors que c'est faux). LegacyWorld (arXiv 2608.14131) mesure que les faux succès et les échecs « non atomiques » sont fréquents chez tous les modèles.
- **L'avertissement du MIT** : leur gain venait du **retrait d'un obstacle** (les boucles), pas d'un ajout de compétence. Sur Gemma 3 270M, qui boucle rarement, ils n'ont rien gagné. **Il faut donc d'abord prouver que Holo a un défaut dominant et retirable.** C'est la phase 2, avec un point de décision.

---

## 2. Accès et infrastructure

### 2.1 Détecter la machine (première action)
- Lance un script de diagnostic et écris le résultat dans `JOURNAL.md` : OS, CPU, RAM, GPU (`nvidia-smi` si NVIDIA ; `system_profiler SPHardwareDataType` sur Mac pour la puce et la mémoire unifiée), VRAM libre, espace disque (il faut environ 20 Go libres), version de Python.
- Crée un environnement virtuel dédié (`python -m venv .venv` ou `uv`). N'installe rien globalement.
- Installe PyTorch avec le bon backend : CUDA si GPU NVIDIA, MPS sur Mac Apple Silicon, CPU sinon. Vérifie avec `torch.cuda.is_available()` ou `torch.backends.mps.is_available()`.

### 2.2 Choisir la taille du modèle selon la machine

| Machine | Modèle | Remarque |
|---|---|---|
| GPU NVIDIA 12 Go de VRAM ou plus | Holo3.1-4B en BF16 | Le plus solide pour les résultats |
| GPU NVIDIA 6 à 12 Go | Holo3.1-0.8B en BF16 (ou 4B en 8-bit via bitsandbytes) | 0,8B recommandé |
| Mac Apple Silicon 16 Go ou plus | Holo3.1-0.8B en BF16/FP16 sur MPS (4B possible à partir de 32 Go) | Pas de vLLM sur Mac : tout passe par transformers |
| Mac 8 Go, ou CPU seulement | Holo3.1-0.8B | Lent : réduis le nombre de rollouts (section 2.5) |

- **Par défaut, commence avec Holo3.1-0.8B**, même si la machine permet le 4B. Il est plus rapide pour itérer, c'est la taille de l'expérience du MIT, et un petit modèle a plus de chances d'avoir un défaut net (boucles). Passe au 4B seulement en bonus, pour montrer que la méthode tient à plus grande taille.
- Vérifie les noms exacts des repos sur `https://huggingface.co/Hcompany` (probablement `Hcompany/Holo-3.1-0.8B` et `Hcompany/Holo-3.1-4B` ou proches, **non vérifié**). Lis entièrement la model card : format du prompt, format des actions, normalisation des coordonnées (0-1000 ou pixels, **non vérifié**), code d'exemple, version de transformers requise.
- **Pas de Holo4-35B-A3B en local** sauf si l'utilisateur a une très grosse machine (au moins 24 Go de VRAM pour une version 4-bit). Ne le propose qu'en toute fin, et demande d'abord.

### 2.3 Format de Holo
- Le harness de référence de H est `github.com/hcompai/hai-agents-python` et `github.com/hcompai/holo-desktop-cli`. **Lis leur code pour reproduire exactement le format de prompt et d'actions de Holo.** Un mauvais format fait chuter les scores : un utilisateur a rapporté 23 % en self-host contre 77,8 % annoncés, probablement à cause du parser ou du template.
- Le template de chat et les parsers utilisés par H côté serveur (vLLM) sont : `--chat-template-content-format openai`, `--tool-call-parser qwen3_coder`, `--reasoning-parser qwen3`, au maximum 5 images par requête. En local avec transformers, reproduis l'équivalent : le chat template du tokenizer, et un parsing du raisonnement et de l'appel d'outil identique à hai-agents-python.
- Échantillonnage : utilise les défauts de la model card. Si rien n'est indiqué, prends les défauts « thinking » de Qwen (T=0.8, top-p 0.95, top-k 20, **non vérifié pour Holo**) et garde seulement les 3 dernières captures dans le contexte.

### 2.4 Un seul chemin d'inférence : transformers (important)
- En local, **tout passe par transformers (HF) en Python** : les rollouts, la capture des activations (hooks sur le residual stream et les sorties MLP de chaque couche) et l'édition des poids. C'est plus simple, et ça garantit que le modèle qu'on analyse est exactement celui qui joue.
- vLLM est optionnel, seulement sur Linux avec GPU NVIDIA, si les rollouts sont trop lents. Ne l'installe pas sur Mac ou Windows.
- **Le patch peut être appliqué en mémoire** : on charge le modèle original, on modifie les tenseurs en place, et on obtient le modèle patché sans le retélécharger. Sauvegarde quand même le modèle patché en safetensors pour la démo et la reproductibilité.
- Le même process peut garder les deux modèles en mémoire pour la démo côte à côte (0,8B × 2 tient sans problème). Pour le 4B, recharge-les à tour de rôle si la VRAM est juste.

### 2.5 Budget de calcul en local
- Mesure le temps d'un pas (prefill + génération) dès que le harness marche, et écris-le dans `JOURNAL.md`.
- Adapte les volumes à cette mesure. Ordres de grandeur visés :
  - GPU NVIDIA : environ 150 à 300 rollouts pour le diagnostic, comme prévu.
  - Mac : environ 80 à 150 rollouts.
  - CPU : environ 40 à 60 rollouts, sur des tâches courtes seulement.
- Limite la génération (nombre maximal de tokens par pas, par ex. 512) et la résolution des captures (par ex. 1280 de large au maximum) pour garder des pas rapides. Note ces réglages : ils doivent être identiques pour tous les bras de l'évaluation.
- Lance les rollouts en arrière-plan avec reprise sur erreur (un rollout planté ne doit pas tout arrêter), et sauvegarde au fil de l'eau.

---

## 3. Plan d'ensemble et points de décision

| Phase | Objectif | Durée cible | Point de décision |
|---|---|---|---|
| 1 | Infra : Holo3.1-0.8B chargé en local, environnement de tâches, harness d'agent fonctionnel | 3 h | Le harness résout au moins quelques tâches faciles |
| 2 | Diagnostic : 150 à 300 rollouts, taxonomie des échecs | 3 h | **STOP/GO** : un défaut dominant et détectable existe-t-il ? |
| 3 | Localisation : trouver la direction défaut (couche, vecteur) | 4 h | La direction prédit le défaut (AUROC au moins 0,75) |
| 4 | Chirurgie : retirer la direction des poids, balayer les variantes | 4 h | Le patch réduit le défaut sans casser les tâches normales |
| 5 | Évaluation finale sur des tâches jamais vues, 4 bras | 4 h | Chiffres avec intervalles de confiance |
| 6 | Démo : dashboard « IRM », side-by-side, replay de secours | 4 h | Démo jouable en 3 min, avec plan B enregistré |

Garde au moins 6 h de marge. La phase 2 peut tuer l'idée : c'est voulu, c'est de la recherche.

---

## 4. Phase 1 : infrastructure

### 4.1 L'environnement de tâches : MiniWoB++ via BrowserGym (recommandé)
- **Pourquoi** : 100+ tâches web courtes, avec une **récompense programmatique** (pas de LLM-juge, pas de triche possible). Ça tourne dans Chromium headless, sur Linux, Mac et Windows, c'est rapide et ça se réinitialise instantanément. C'est parfait pour des centaines de rollouts.
- Installation : `pip install browsergym-miniwob` (plus Playwright Chromium). Suis la doc BrowserGym pour héberger les fichiers HTML de MiniWoB++ (une variable d'environnement `MINIWOB_URL` qui pointe vers un serveur local).
- **Actions** : Holo agit par coordonnées. Utilise l'espace d'actions coordonnées de BrowserGym (`mouse_click(x, y)`, `keyboard_type`, `keyboard_press`, `scroll`, etc.) et écris un **adaptateur** entre le format d'action de Holo (trouvé dans la model card ou dans hai-agents-python) et ces actions. Gère la conversion des coordonnées si Holo les normalise.
- **Observation** : uniquement la capture d'écran, plus l'instruction et l'historique texte des actions précédentes. Pas d'arbre d'accessibilité, pour rester fidèle à Holo.
- **Choix des tâches** : privilégie les tâches **multi-étapes** (5 pas ou plus), là où boucles et faux succès apparaissent : formulaires, `book-flight`, `email-inbox-*`, `search-engine`, `click-tab-2-hard`, `use-autocomplete`, `social-media-*`, `login-user-popup`, etc. Liste-les, puis garde celles où le modèle choisi a un taux de succès entre 10 % et 80 % : ni triviales, ni impossibles. Avec un 0,8B, il faudra peut-être descendre vers des tâches un peu plus simples : c'est normal.
- **Tâches impossibles** (pour mesurer le faux succès) : crée une variante de 10 à 20 tâches rendues infaisables, par exemple un bouton cible supprimé du DOM ou un champ désactivé. La bonne réponse de l'agent est alors d'abandonner ou de dire « impossible ».

**Alternative si MiniWoB++ pose problème** : demande à l'humain s'il préfère des mini-applis web générées (par Devin, un des partenaires) avec un état vérifiable en base de données. Ne bascule pas sans demander.

### 4.2 Le harness d'agent
- Une boucle : capture → prompt Holo (format officiel) → parsing de l'action → exécution dans BrowserGym → répéter, jusqu'à la fin de la tâche, l'action « terminé » ou un budget de pas (par ex. 2× le nombre de pas humain, au maximum 30).
- **Enregistre tout** pour chaque rollout, dans `runs/<run_id>/` : instruction, seed, chaque capture (PNG), le texte complet généré (y compris le raisonnement), l'action parsée, la récompense finale, si l'agent a annoncé un succès, le nombre de pas et les temps.
- Parallélisme : un seul modèle en mémoire, et un batch de plusieurs environnements si la VRAM le permet (par ex. 4 navigateurs dont les requêtes sont regroupées). Sinon, en séquentiel, c'est acceptable.
- **Test d'acceptation** : sur 10 tâches faciles (`click-button`, `click-link`, `enter-text`), le harness obtient un taux de succès cohérent avec un modèle compétent (plus de 70 %). Sinon, le problème vient de l'adaptateur (format, coordonnées). Corrige avant de continuer.

---

## 5. Phase 2 : diagnostic (le point de décision clé)

1. **Rollouts** : environ 20 tâches × 8 seeds (au moins 150 rollouts), plus les tâches impossibles.
2. **Taxonomie automatique des échecs**, par rollout et par pas :
   - **Boucle** : la même action (ou presque, par ex. un clic à moins de 15 px du même point, ou le même texte tapé) répétée 3 fois ou plus, sans changement significatif de l'écran (diff de pixels faible).
   - **Faux succès** : l'agent annonce « terminé » alors que la récompense vaut 0, ou annonce un succès sur une tâche impossible.
   - **Mauvais grounding** : un clic à côté de la cible (vérifiable via le DOM de BrowserGym).
   - **Abandon / budget épuisé** sans boucle.
   - **Autre.**
3. **Livrable** : `diagnostic.md` avec le tableau des échecs par catégorie, des exemples (captures) et le taux de succès global.

### STOP / GO
- **GO** si une catégorie retirable (boucle **ou** faux succès) représente au moins 25 % des échecs et qu'on a au moins 40 exemples positifs pour l'analyse. Choisis cette catégorie comme cible.
- **Si aucune ne domine** : essaie l'autre taille (le 4B si tu étais sur le 0,8B, si la machine le permet), ou d'autres tâches plus longues, et refais la phase 2 plus vite. Si ça ne marche toujours pas, **STOP** : écris le résumé, propose les options à l'humain et attends.

---

## 6. Phases 3 et 4 : localisation et chirurgie

### 6.1 Capture des activations (transformers + hooks)
- Pour chaque pas des rollouts enregistrés, rejoue exactement le contexte d'entrée (images et texte) dans le modèle HF, et capture le **residual stream** à la **dernière position du prefill** (juste avant que le modèle génère son action), pour **chaque couche**. Capture aussi la sortie des MLP (`down_proj`) si possible.
- Labels :
  - Cible **boucle** : positif = les pas où l'agent émet une action répétée (à partir de la 2e répétition) ; négatif = les pas normaux qui font progresser l'écran.
  - Cible **faux succès** : positif = le pas où l'agent annonce « terminé » à tort ; négatif = les « terminé » corrects.
- Stocke en `.npy` ou `.safetensors` par couche. Pour un 4B, c'est léger.

### 6.2 Trouver la direction
1. **Diff of means** par couche : u_l = moyenne(positifs) − moyenne(négatifs), normalisée.
2. **Score** par couche : AUROC de la projection ⟨h, u_l⟩ pour séparer positifs et négatifs, sur un split held-out **par tâche** (pas par pas, sinon il y a des fuites). Compare avec une sonde logistique linéaire.
3. Trace la courbe AUROC en fonction de la couche. On s'attend à un pic dans les couches du milieu. Retiens les 1 à 3 meilleures couches.
4. **Critère** : AUROC d'au moins 0,75 sur le held-out. Sinon, note-le, essaie une autre position de token (fin des tokens visuels, ou premier token généré), puis passe en mode « sonde seulement » (voir section 10, plan B).

### 6.3 La chirurgie (édition des poids, sans gradient)
- **Méthode principale** (comme le MIT) : pour une couche l et la direction unitaire u, orthogonaliser la matrice qui **écrit** dans le residual stream : `W_down' = W_down − u (uᵀ W_down)` (u est dans l'espace du modèle). Version ciblée : seulement les colonnes (neurones) de `down_proj` qui contribuent le plus à u, comme le MIT avec 64 colonnes.
- **Variantes à balayer** :
  - couches : 1, 2 ou 3 meilleures ;
  - toutes les colonnes ou top-k colonnes (k = 32, 64, 128, 256) ;
  - coefficient α (W' = W − α·u(uᵀW)), avec α dans {0,5 ; 1 ; 1,5}.
- **Contrôle de sanité pour chaque variante** : un petit lot de **tâches normales faciles** ne doit pas perdre plus de 2 points. Un patch qui « guérit » en cassant tout ne compte pas.
- **Comparateur obligatoire** : le **steering à l'inférence** (soustraire α·u du residual stream via un hook, sans toucher aux poids). Si le steering marche et pas l'édition, c'est aussi un résultat.
- Sélectionne le meilleur patch sur un **set de validation**, jamais sur le set de test final.
- **Optionnel, dans l'esprit du MIT** : tu peux toi-même (Claude) jouer le rôle d'« éditeur » à la Astra : inspecter les poids et les activations en Python, formuler des hypothèses, tester avec un budget limité de forward passes, et itérer. Documente chaque hypothèse dans `JOURNAL.md`, parce que c'est une belle histoire pour le pitch (« Claude a opéré Holo »).

### 6.4 Sauvegarde
- Sauvegarde le modèle patché (`holo31-4b-patched/`) en safetensors, avec la même config et le même tokenizer. Écris `patch_spec.json` : couches, colonnes, α, norme du changement, nombre de poids modifiés (et le pourcentage).
- Pour l'évaluation et la démo, recharge-le avec transformers depuis ce dossier, ou applique le patch en mémoire sur le modèle original (section 2.4).

---

## 7. Phase 5 : évaluation finale

- **Split propre** :
  - les tâches (ou les seeds) de test ne doivent jamais avoir servi au diagnostic, à la direction ni à la sélection du patch ;
  - idéalement, des **tâches jamais vues** (d'autres familles MiniWoB++), plus de nouvelles seeds sur les tâches vues.
- **4 bras**, même harness et mêmes seeds :
  1. Holo original (0,8B ou 4B selon la section 2.2).
  2. Holo + **prompt correctif** (par ex. « si ton action précédente n'a rien changé à l'écran, essaie autre chose » ou « vérifie avant de dire terminé »). C'est ce qu'un ingénieur ferait en premier, et c'est indispensable pour que le résultat soit crédible.
  3. Holo + **steering** à l'inférence.
  4. Holo **patché** (édition des poids).
  - Bonus : un modèle plus gros comme plafond de référence (Holo3.1-9B, ou Holo4-35B-A3B si le temps le permet).
- **Métriques** :
  - taux de succès (récompense MiniWoB) avec un IC à 95 % (bootstrap par tâche) ;
  - taux du défaut ciblé (boucles par rollout, ou faux succès) ;
  - nombre moyen de pas ;
  - régression sur les tâches faciles ;
  - temps par tâche ;
  - nombre et pourcentage de poids modifiés.
- **Livrable** : `results.md` (tableau + graphiques PNG) et `results.json`. Sois honnête sur la taille d'échantillon et les intervalles de confiance.

---

## 8. Phase 6 : démo et pitch

### 8.1 Dashboard « IRM » (une appli web locale, sur localhost)
- **Panneau gauche** : Holo original en live sur une tâche choisie (capture courante, action, raisonnement abrégé).
- **Panneau droit** : Holo patché sur la **même tâche, même seed**.
- **Sous chaque panneau** : la courbe en temps réel de ⟨h_l, u⟩ par pas (la « jauge de défaut »), avec un seuil rouge. Chez l'original, elle doit monter avant ou pendant la boucle.
- **Au centre** : une carte des couches du modèle (barres verticales) avec la ou les couches opérées en surbrillance, et le nombre de poids modifiés (par ex. « 0,01 % des poids »).
- **En bas** : le tableau final des 4 bras.
- Stack simple : un backend Python (FastAPI) qui pilote les deux agents et diffuse les événements en WebSocket, et un frontend HTML/JS d'une seule page. Pas de framework lourd.
- Pour la jauge en live : soit le chemin B (HF) sert aussi la démo, soit on rejoue les activations précalculées pour les tâches de démo. **Recommandé : précalculer**, c'est plus fiable.

### 8.2 Replay de secours
- Enregistre 3 tâches de démo complètes (vidéo de l'écran du dashboard et fichiers JSON rejouables). Si le live casse, on lance le replay.

### 8.3 Partenaires (secondaire, à faire seulement si tout le reste marche)
- **H** : c'est le cœur, avec les modèles Holo.
- **Devin** : générer des mini-applis de test supplémentaires à état vérifiable.
- **Linkup** : le « mécanicien » cherche les modes d'échec connus du modèle (model cards, issues GitHub) avant le diagnostic, comme le MIT avec l'avertissement sur les boucles dans la model card de Qwen.
- **Gladia** : le jury dicte la tâche de démo à la voix.
- Ne sacrifie jamais la phase 5 pour un partenaire.

### 8.4 Le pitch (pour info, c'est l'humain qui le fera)
> « Il y a 5 jours, le MIT a montré qu'un LLM peut réparer un modèle en modifiant ses poids, sans entraînement. Tout le monde l'a fait sur des maths. On l'a fait sur un agent qui utilise un ordinateur. On a trouvé dans le cerveau de Holo la direction qui le fait [boucler / mentir sur son succès], on l'a retirée en modifiant X % de ses poids, et sur des tâches jamais vues il passe de A % à B %. Voici ce qui se passe dans sa tête quand il échoue. »

---

## 9. Artefacts à livrer (checklist)

- [ ] `JOURNAL.md` : journal chronologique, avec décisions et chiffres
- [ ] `diagnostic.md` + taxonomie des échecs + exemples
- [ ] `direction_analysis.md` + graphique AUROC par couche (PNG)
- [ ] `patch_spec.json` + modèle patché sauvegardé
- [ ] `results.md` / `results.json` + graphiques (4 bras, IC 95 %)
- [ ] Dashboard « IRM » fonctionnel sur localhost (donne l'URL et la commande de lancement)
- [ ] 3 replays de secours enregistrés
- [ ] `README.md` : comment tout relancer, en 10 commandes maximum
- [ ] Une slide-ready summary : 5 chiffres clés et 2 phrases, dans `PITCH_NUMBERS.md`

---

## 10. Risques et plans B

| Risque | Signe | Plan B |
|---|---|---|
| Format de prompt ou d'action de Holo mal reproduit | Succès très faible même sur les tâches faciles | Recopier exactement hai-agents-python ; tester l'échantillonnage de la model card |
| Pas de défaut dominant (comme Gemma au MIT) | Phase 2 : aucune catégorie à 25 % ou plus | Essayer l'autre taille ou des tâches plus longues ; sinon STOP et demander à l'humain |
| La direction ne prédit rien | AUROC inférieure à 0,75 | Autre position de token ; sonde non linéaire légère ; puis plan « sonde seulement » : un **détecteur** temps réel du défaut (la jauge) + un arrêt ou une relance quand elle passe le seuil. La démo IRM reste possible |
| Le patch casse les tâches normales | Régression de plus de 2 points | Réduire α, moins de colonnes, une seule couche ; sinon garder le steering à l'inférence |
| Le prompt correctif fait aussi bien que le patch | Bras 2 ≈ bras 4 | C'est un résultat honnête à présenter. On combine (prompt + patch) et on mesure |
| Mémoire insuffisante ou rollouts trop lents | OOM, plus de 30 s par pas | Passer au 0,8B, réduire la résolution des captures et le nombre de tokens générés, réduire les volumes (section 2.5) |
| Problème MPS sur Mac (opération non supportée) | Erreur PyTorch MPS | `PYTORCH_ENABLE_MPS_FALLBACK=1`, ou FP16 au lieu de BF16, ou CPU pour la capture d'activations seulement |
| Pas assez de temps | Phase 5 en retard | Réduire le set de test, mais garder les 4 bras et les IC |

---

## 11. Ce qu'il ne faut PAS faire

- Pas de RL multi-tour, pas de fine-tuning complet : hors scope, et ce n'est pas l'histoire.
- Ne pas évaluer sur les tâches qui ont servi à trouver la direction ou à choisir le patch.
- Ne pas comparer nos chiffres aux scores publiés par H (harness différent). Seules les comparaisons dans notre harness comptent.
- Ne pas utiliser de LLM-juge pour le succès : la récompense MiniWoB suffit.
- Ne pas présenter un gain dans le bruit comme un résultat : toujours afficher les IC.
- Ne pas supprimer de fichiers sur le PC de l'utilisateur, et ne rien installer en dehors de l'environnement virtuel du projet, sans demander.

---

## 12. Références

- MIT CSAIL, « Sparks of Weight-Space Programming » (Takehi, Teoh, Zhang, Khattab), 2 nov. 2026. Blog : rikiyat.github.io ; logs sur GitHub ; modèle édité sur HF.
- Visual Token Routing (CMU, arXiv 2611.06854) : code github.com/Pranjal2041/vtr, modèle HF l3lab/VTR-2B (inspiration pour la phase bonus « ce que Holo regarde »).
- « Why Generate a Click? Plug-in Decision Heads for Web Agents » (arXiv 2610.20107) : les décisions se lisent dans les états cachés du prefill. Ça confirme que lire l'activation au dernier token du prefill est le bon endroit.
- LegacyWorld (arXiv 2608.14131) : faux succès et atomicité chez les agents GUI.
- H Company : huggingface.co/Hcompany, hub.hcompany.ai (local-inference docs), github.com/hcompai/hai-agents-python, github.com/hcompai/holo-desktop-cli.
- BrowserGym / MiniWoB++ : github.com/ServiceNow/BrowserGym.

*Note : plusieurs détails (noms exacts des repos Holo3.1-0.8B et 4B, format des coordonnées, échantillonnage officiel) n'ont pas pu être vérifiés depuis la recherche. Vérifie-les à la source avant de t'appuyer dessus.*
