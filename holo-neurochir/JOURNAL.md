# JOURNAL — Neurochirurgie de Holo (version locale)

## 2026-11-07 — Phase 1 : infrastructure

### Diagnostic machine
| Élément | Valeur |
|---|---|
| OS | Windows 11 Famille 10.0.26200 |
| CPU | Intel Core Ultra 7 258V (Lunar Lake), 8 cœurs / 8 threads |
| RAM | 31,5 Go (7,1 Go libres au démarrage) |
| GPU | Intel Arc 140V (iGPU, mémoire partagée annoncée 16 Go) — **pas de NVIDIA** |
| Disque C: | 282 Go libres |
| Python | 3.12.10, uv 0.11.29 |

**Décision** : machine hors tableau 2.2 (ni NVIDIA, ni Mac). Option retenue : PyTorch avec backend Intel XPU dans le `.venv` si fonctionnel, sinon CPU. Modèle : Holo3.1-0.8B (défaut du brief). Volumes de rollouts à calibrer sur le temps mesuré par pas (cible CPU/iGPU : 40–150 rollouts).

### Installation (tout dans le projet)
- `.venv` (uv, CPython 3.12.13) : torch 2.15.0+xpu (Intel XPU OK : 50 matmul 2048² bf16 en 0,37 s), transformers 5.22.2, browsergym-miniwob 0.14.3, playwright 1.44.
- Caches redirigés dans le projet : `HF_HOME=.hf`, `PLAYWRIGHT_BROWSERS_PATH=.pw-browsers` (rien d'installé hors du dossier).
- MiniWoB++ cloné (commit épinglé 7fd85d7), servi par `python -m http.server 8765` → `MINIWOB_URL=http://127.0.0.1:8765/miniwob/`.
- Modèle : `Hcompany/Holo-3.1-0.8B` (vérifié sur HF), `Qwen3_5ForConditionalGeneration`, 24 couches (hybride : 3 linear-attention + 1 full-attention), hidden 1024, MLP 3584 → `down_proj` = 1024×3584. Même architecture que Qwen3.5-0.8B du MIT.

### Format Holo (sources : hub.hcompany.ai, chat_template.jinja)
- Le prompt système exact du desktop agent de H n'est pas public (runtime fermé). Les docs de H disent « plug in your own SYSTEM_PROMPT » → prompt système à nous, court, sans exemples de format.
- Outils au format function-calling de H : `click(element, x, y)` en [0,1000], `answer(content)` (les deux publiés par H) + `type_text`, `press_key`, `scroll` (définis par nous, comme H le recommande).
- Sortie : XML qwen3_coder `<tool_call><function=…><parameter=…>`. Observation : `<observation>` + image ; 3 dernières captures gardées, les anciennes → `[screenshot evicted]`.
- Échantillonnage : T=0,8, top-p 0,95, top-k 20 (docs H : 0,8 pour les boucles d'agent). max_new_tokens=512.
- MiniWoB : BrowserGym efface l'instruction de la page → elle est passée en texte (1er message user), comme dans le format H.

### Bugs trouvés et corrigés
1. **Pas d'EOS** : le repo 0.8B n'a pas de `generation_config.json` → la génération ne s'arrêtait pas à `<|im_end|>` et partait en texte hors sujet (maths, Python…) jusqu'à 512 tokens. Fix : `eos_token_id=[<|im_end|>, <|endoftext|>]`. Pas : ~30 s → ~3-5 s.
2. Le 0.8B omet parfois la balise `<parameter=text>` → parser tolérant pour les outils à un seul argument texte.
- Kernels attention linéaire : fallback PyTorch de référence (pas de `flash-linear-attention` sur XPU/Windows). Acceptable.

### Test d'acceptance (click-button, click-link, enter-text × 4 seeds, 6 pas max)
- Pas de thinking, capture à l'échelle 1× (498×321) : **0/12**. Observation : clics très loin de la cible (ex. « yes » à (60,640) normalisé, clic à (468,546)), et **boucle parfaite** (même clic 6 fois, écran inchangé). Hypothèse : image trop petite / hors distribution pour Holo (entraîné sur écrans pleine taille).
- **Test de grounding isolé** (12 captures click-button, cible connue par le DOM, 1 clic) :
  | Config | Clics corrects |
  |---|---|
  | page entière 1× | 8 % |
  | page entière 2× | 17 % |
  | zone tâche recadrée 2× / 3× / 4× / **5×** | 8 % / 25 % / 75 % / **100 %** |
  | prompt de localisation officiel H, recadré 4× | 58 % |
  → Holo 0.8B a besoin d'éléments de taille « écran réel ». **Observation retenue : zone MiniWoB (`#wrap`) recadrée puis agrandie 5×**, coordonnées remappées avec le décalage. Réglage identique pour tous les bras.
- **Acceptance (crop + 5×, sans thinking)** : **11/12 = 92 %** (click-button 4/4, click-link 4/4, enter-text 3/4) → ✅ critère > 70 %. Temps moyen de génération : **6,4 s/pas** (prefill ~1 200 tokens image par capture, 3 captures en contexte).
- Thinking : désactivé (512 tokens max par pas → le raisonnement serait tronqué et coûterait ~30 s/pas). Noté comme écart au défaut « thinking » de H.
- Budget : ~6-7 s/pas → ~1 min par rollout de 8 pas → cible ~150 rollouts pour le diagnostic (≈ 2,5 h).

**Phase 1 : GO.**

## Phase 2 : diagnostic
- Pilote : 24 tâches multi-étapes × seeds 0-1 pour sélectionner les tâches à 10-80 % de succès.
- Pilote terminé : 48 rollouts en 29 min (~36 s/rollout), 0 plantage. **Succès global 27 %.**
  - 2/2 : click-option, click-tab, email-inbox-delete ; 1/2 : choose-list, click-checkboxes, click-dialog-2, click-menu, click-widget, navigate-tree, use-autocomplete ; 0/2 : les 14 autres.
- Lecture des traces de la catégorie « other » (17/35 échecs) : c'est surtout de la **soumission prématurée**. Exemples : click-collapsible (Submit sans déplier la section), enter-text-2 (Submit sans mettre en majuscules), form-sequence (slider ignoré puis Submit).
  - Sur MiniWoB, cliquer Submit, c'est déclarer « terminé ». C'est donc la forme « action » du faux succès du brief.
- **Définitions révisées (taxonomy.py)**, décidées après lecture des traces, avant le run principal :
  - Boucle : seuil « écran inchangé » relevé de 0,3 % à **1 % de pixels modifiés**. Cocher/décocher la même case 6 fois (diff 0,45 %) n'était pas compté.
  - Faux succès = `answer` « terminé » avec récompense 0 (ou sur tâche impossible), **ou** action finale de type validation (bouton Submit/Login/Search, ou Entrée) qui clôt l'épisode avec récompense 0.
  - Un mauvais clic qui clôt une tâche à action unique (click-dialog-2, click-widget…) n'est **pas** compté comme faux succès → catégorie séparée `wrong_final_action`.
  - Labels au niveau du pas : fs+ = « terminé » à tort, fs- = « terminé » correct (même critère d'action de validation).
- Pilote avec ces définitions : faux succès **40 % des échecs** (14 positifs, dont 12 Submit et 2 answer) ; boucle 20 % (23 pas positifs). **Limite** : seulement 5 négatifs fs- (beaucoup de succès viennent de tâches à un clic).
- Run principal lancé : 24 tâches × seeds 2-7 (144 rollouts) + 10 tâches impossibles × seeds 0-3 (40 rollouts).
- **Split réservé pour la phase 5** : les familles MiniWoB absentes de ces 24 tâches restent jamais vues. Elles ne serviront qu'au test final.

### Préparation des phases 3-4 (pendant le run principal)
- `holo/direction.py` : diff of means par couche, AUROC en CV **par tâche** (GroupKFold), sonde logistique en comparaison, plus des **contrôles de position**. Test sur les données partielles (cible boucle, 23 positifs) :
  - tous négatifs : direction 0,95 (L11), **mais un baseline trivial « indice du pas » fait déjà 0,89** → confound (un pas en boucle arrive forcément tard dans l'épisode) ;
  - négatifs restreints à t ≥ 2 : baseline 0,75, direction 0,88 (L3, L9) → il reste un signal au-delà de la position. Ce contrôle est gardé dans l'analyse officielle.
- `holo/surgery.py` : W' = W − α·u(uᵀW) sur `down_proj`, toutes colonnes ou top-k (option : projection de sortie de l'attention). Test unitaire : |uᵀW| passe de 1,196 à 0,005 (α=1 ; reste = arrondi bf16) et de 1,196 à 0,598 (α=0,5). En top-64, seules 64 colonnes changent (65 536 poids par couche, l'échelle du MIT).
- `holo/replay.py` : reconstruction exacte de l'entrée du modèle à n'importe quel pas enregistré, et score « teacher-forced » d'une action. **Fidélité vérifiée** sur 6 pas : nombre de tokens identique, cosinus = 1,0000 avec les activations enregistrées (L0, 6, 12, 18, 23). Usage prévu : cribler les variantes de patch hors ligne (log-prob de l'action fautive contre celle des actions correctes) avant la validation en ligne.

## Provisioning GPU Runpod (demande de l'utilisateur, 2026-11-07)
- L'utilisateur a choisi de louer un GPU (« le meilleur », budget ~100 €). Configuration via le plugin officiel Runpod pour Claude Code (OAuth : aucune clé API sur disque).
- Lectures (Secure Cloud, pods) : H200 SXM 141 Go **5,29 $/h**, stock MEDIUM (EUR-IS-4 : LOW) ; H100 SXM 3,99 $/h ; B200 7,99 $/h ; B300 8,99 $/h. Le parc est en CUDA 13.2 → plancher `minCudaVersion 12.8`.
- Choix : **H200 SXM** (rang 1 du document de provisioning). B200/B300 écartés : prix ×1,5-1,7 sans gain pour cette mission ; avec ~100 € de crédit, le H200 laisse ~20 h de calcul.
- Créés à 14:37 UTC :
  - volume réseau `8206qbtznz` (« holo-neurochir », 100 Go STANDARD, EUR-IS-4) ;
  - pod `fbup7c0tebnkwf` (« holo-neurochir-h200 »), 1× H200, image `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` (template officiel `runpod-torch-v280`), disque conteneur 50 Go, volume monté sur `/workspace`, ports 22/tcp et 8000/http, `HF_HOME=/workspace/hf`.
  - clé SSH dédiée `~/.ssh/runpod_holo`.
- **Règles de dépense** : un seul pod ; arrêt (stop, jamais delete) dès qu'il ne tourne plus rien ; plafond personnel ~90 $ pour ne jamais vider le crédit ; coût cumulé noté toutes les 2 h.
- Coût à 14:37 UTC : 0 $ (démarrage).

## Migration vers orbit / argos (2026-11-07 ~16:10 Paris)
- 8 shards 4B sur le pod : 25-50 s/pas, charge 19 pour 12 vCPU → shards arrêtés (~13 rollouts 4B faits). Benchmark FLA vs fallback préparé (`scripts/bench_gen.py`), pas encore lancé.
- À la demande de Martin : le projet est copié dans `orbit:~/projects/ComputerUseHackaton/holo-neurochir/`, la clé `runpod_holo` est copiée sur orbit (SSH vers le pod OK depuis orbit), et la suite est confiée à une session Claude Code dans argos (voir `HANDOFF.md`). Le pod reste allumé (choix de Martin).
- Coût pod à ~15:10 UTC : ~0,6 h × 5,29 $ ≈ 3 $ (estimation horaire, pas une lecture de facturation).
