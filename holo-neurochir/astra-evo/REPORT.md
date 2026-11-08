# Astra-evo — évolution de coefficients de fusion

2026-11-08, propriétaire astra-evo, thread `01a1b8ed-ef85-73f0-8c1a-4c4d8d8fe39b`.

Mission : modifier seulement les poids de Holo-3.1-4B, sans gradient, adaptation, changement de prompt ou du harnais de production. Recherche en espace des paramètres inspirée de [Sakana, 2024](https://arxiv.org/abs/2403.13187), avec une recherche gaussienne adaptative bornée, pas une reproduction de leur méthode complète.

**Livraison finale, 03:10 UTC :** checkpoint complet vérifié et uploadé sur **Modal compte1, `holo-models:/ckpt/astra_evo_best`**. 45 candidats, 26,5 minutes de recherche, arrêt à deux populations sans progrès. Meilleur point : a=0,2 et b=0 dans les huit groupes. Trois textes corrects, action JSON conforme, audits indépendants PASS. Aucun gain OSWorld démontré ; service et test en ligne confiés à ares. Passation : `HANDOFF_ARES.md`, contrôles : `VERIFY.md`.

## Protocole gelé avant calcul

- Sources en lecture seule : Holo `8c88265a5a159bfd1492db9243733dd2e6e04a6e`, Qwen3.5-4B `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, CUA demandé `df6eba93efb2df3ed9adc810e0f7f4e038959c74`. Cache Qwen `/root/expo/base`, CUA `/dev/shm/astra_merge_cua`.
- Huit groupes : blocs 12–15,16–19,20–23,24–27, chacun mixeur/MLP. Tous les paramètres internes de ces modules suivent Holo + a(Qwen−Holo) + b(CUA−Qwen). Normes externes, embeddings, vision, couches restantes et lm_head restent Holo.
- Calcul : deltas FP32 arrondis BF16, multiplications et additions BF16 explicites. L'export doit reproduire ces arrondis, plutôt qu'une autre formule en FP32.
- 40 contextes DIAG, 40 tâches distinctes : construction20 et validation20, chacun 8 fs+,6 vrais finis,6 sains. Sélection par hash fixe ; les quatre vrais finis les plus tardifs sont répartis entre les deux panels. Réserve45 exclue par identifiants ; aucun contenu d'épisode réservé ni split_test lu.
- Manifest SHA256 `0dee9300265424202187ba4cd62cdea82c30b16287fd2f030c90a172edcc7512` ; sources, images et trajectoires liées par hash. Taxonomie et fidélité revues indépendamment avant recherche.
- Replay : messages exacts, raisonnement enregistré et préfixe JSON jusqu'au nom d'outil. Une passe par contexte produit les logits de trois positions : fin du prompt, fin du raisonnement enregistré, choix d'outil. Marge = logit answer − maximum des premiers tokens des autres outils autorisés. KL vocabulaire complet aux trois positions, moyenné sur les pas sains.
- Score : baisse moyenne de marge fs+ − 0,4 × baisse positive moyenne sur vrais finis − 2 × KL sain − 0,05 × RMS des coefficients. Une hausse de marge vraie ne donne pas de bonus. Garde-fou : les quatre vrais finis tardifs doivent conserver une marge positive.
- a∈[−0,2;0,8], b∈[−0,25;1,25]. 4 populations×15 points, maximum60. Élite des4 meilleurs scores de construction pour le centre/dispersion suivant. Seul le gagnant construction de chaque population est évalué en validation. Validation employée pour sélection/arrêt, donc elle n'est pas un test final vierge.
- Arrêt : deux populations sans amélioration validation >0,05, ou deux heures à compter du lancement du processus Python. Les points interrompus sont journalisés ; aucune relance automatique.

## Limites fixées à l'avance

La marge conditionnée au raisonnement enregistré n'est qu'un objectif de recherche. Elle ne démontre ni une action utile, ni une amélioration OSWorld. Les trajectoires complètes et le score final seront évalués par ares. Aucun vrai fini non réservé n'atteint35 pas dans ce cache : les contrôles tardifs sont aux pas27,29,30,32. Le risque d'épisodes atteignant50 pas doit donc encore être contrôlé en ligne.

Le donneur peut avoir une contamination de benchmark inconnue ; aucune revendication de généralisation n'en découle. Le checkpoint, s'il est produit, doit passer une vérification indépendante des tenseurs, trois textes gloutons et un JSON d'action valide avant upload Modal. Aucun service existant ne sera remplacé par astra-evo.

## État

02:16 UTC : sélection40 gelée et scripts écrits. Relectures indépendantes en cours. Aucun forward ni checkpoint candidat à cette heure. Deux slots GPU occupés ; astra-evo autorisé dans PRIORITY. `/dev/shm` dispose maintenant de32Go. `git pull --rebase` bloqué par modifications partagées préexistantes ; aucun stash/reset ni staging global.

02:21:38 UTC : recherche lancée via gpu_slot.sh, slot0, PID Python380433 et timeout7200s. Relecture statique GO après contrôles additionnels. Audits indépendants : cohort_review PASS (40 tâches,200 fichiers,677 images,62 égalités HF/vLLM), source_review PASS (4 SHA256 donneurs). Replay final SHA5bee8e8f187f9600a6f516779076b0f5fb9590e220d8629ba804cc166742b90a. Baselines et recherche intégrées pour éviter une seconde charge ; garde-fous baseline assertés avant tout coefficient non nul. Sources Holo liées au snapshot ; absence de SHA externe Holo distinct explicitée dans audit.

02:24 UTC : objectif calculable et pilote indépendant PASS. 40 forwards baseline, marges answer positives pour8/8 fs+ et6/6 vrais finis dans chaque panel ; argmax sain non-answer6/6. Scope exact180tenseurs,1 784 942 848 paramètres ;544tenseurs hors édition. Premier panel validation48,89s, régime suivant23–35s/panel. Aucun gradient.

02:32 UTC : population1/4 terminée,15points,360forwards au total. Premier meilleur point validation : tous groupes a=0,2,b=0 ; score0,33234, baisse fs+0,78125logit, pénalité vrais finis1,08333logit, KL sain0,004252. fs+8/8 et vraisfinis6/6 gardent une margepositive ; gardes tardivesPASS. Ce gain de score pondéré ne constitue pas une sélectivité supérieure ni un gain de génération. Premier meilleur point obtenu en20minutes de mission ; poursuite conforme au protocole.

02:49 UTC : arrêt conforme après 45 candidats (3 populations de 15), deux populations sans progrès de validation. 50 évaluations de panel, 1 000 passes, 1 590,37 s de recherche ; pic mémoire CUDA réservé 26,54 Go. Le plafond de 60 candidats est donc volontairement non atteint. Le processus a terminé avec code 0 et libéré son slot GPU.

| Population | Score construction du gagnant | Score validation | fs+ avec marge positive /8 | Vrais finis avec marge positive /6 |
|---|---:|---:|---:|---:|
| 1 | 0,751382 | **0,332341** | 8 | 6 |
| 2 | 0,713568 | 0,302729 | 8 | 6 |
| 3 | 0,823089 | 0,304355 | 7 | 6 |

Le meilleur point est uniforme dans les huit groupes : **a=0,2, b=0**. Il restaure donc 20 % du delta vers Qwen dans ces modules ; aucun delta CUA n'est retenu. La dernière population donne une inversion fs+ en validation, mais son score pondéré est inférieur ; ses coefficients sont conservés dans le journal, sans second export. Le résultat ne démontre pas une meilleure discrimination entre faux et vrais finis.

02:51–02:53 UTC : checkpoint HF complet créé sous `/dev/shm/astra_evo_best` (15 fichiers, deux shards). Vérification CPU indépendante PASS : 724 tenseurs finis, 180 formules exactes dont 147 tenseurs effectivement modifiés, 1 466 114 226 valeurs changées ; 544 tenseurs hors périmètre identiques bit à bit, dont 297 de vision et lm_head. Les 33 tenseurs du périmètre inchangés résultent de deltas nuls ou de l'arrondi BF16. Assets Holo conservés. Audit indépendant de la recherche PASS : les 50 scores sont recalculés depuis les 1 000 lignes de contexte (erreur maximale 3,47e−18), sélection et arrêt corrects, 17 empreintes de sources gelées intactes.

02:54 UTC : première vérification CUDA bloquée par une hypothèse erronée du vérificateur : 24 tenseurs donneurs sont en FP32 alors qu'il exigeait BF16. Les 156 tenseurs comparés sont tous exacts ; aucune différence arithmétique constatée. Le code de recherche convertit explicitement les donneurs en FP32 avant les deltas BF16, et accepte donc ces sources. L'échec est conservé dans `cuda_formula_review_failed_1.json` ; correction indépendante du vérificateur et nouvelle comparaison exhaustive requises avant upload.

Preuves principales : `search_review.json`, `checkpoint_review.json`, `finished.json`, `build.json`, `evaluations.jsonl`. La recherche est terminée ; santé générative et upload restent à vérifier à ce point du journal.

02:58 UTC : comparaison CUDA exhaustive indépendante PASS et relecture finale PASS. Les 180 tenseurs sont finis, suivent les intermédiaires BF16 attendus et sont identiques bit à bit à l'export ; zéro valeur divergente, maximum absolu0. Les 147 tenseurs et 1 466 114 226 valeurs effectivement changés concordent avec l'audit CPU. Les15 fichiers du checkpoint ont été liés à nouveau aux empreintes de cet audit. Régression active : donneurs FP32 acceptés, mauvais delta CUA−Holo rejeté, Holo/export FP32 rejetés. Le vérificateur corrigé ne modifie ni le modèle ni l'exigence d'égalité. Preuve `cuda_formula_review.json`, SHA256 `9827201578ac193e737fede0679820118de1928867eb7aa2a8b5b7d0c4e6c843`. Générations de santé lancées via le sémaphore de flotte, plafond15 minutes.

03:00 UTC : les trois textes gloutons sont corrects et terminés par EOS : `56`, `Le chat dort sur la chaise.`, puis les primaires de lumière rouge/vert/bleu. Le premier essai d'action échoue après `json.loads` sur une assertion supplémentaire exigeant note/thought de type chaîne. La sortie d'action n'était sauvegardée qu'après les assertions et manque donc dans cette première preuve ; le journal d'échec et les trois textes sont conservés. Comparaison indépendante de l'assertion au schéma original et correction de l'observabilité en cours. Aucun changement de poids ou de prompt, upload suspendu.

03:04 UTC : le schéma original exige thought/tool_call mais autorise note absente, chaîne ou null. L'assertion ajoutée était donc trop stricte ; faute de sortie conservée, cela ne prouve pas rétroactivement la conformité de la première action. Correction au niveau de la conception : `jsonschema.validate` devient l'unique autorité pour les types des champs. La sortie est conservée avant décodage et contrôles, après le filtre de données personnelles. Régressions CPU positives et négatives PASS, puis seconde revue indépendante GO. Une seule nouvelle passe est lancée sous les mêmes poids, messages et paramètres, dans `smoke_2.json`/`smoke_2.log`. Le premier essai est conservé dans `smoke.json` et `smoke_failed_1.log`. Preuve de correction : `smoke_gate_review.json`.

03:06–03:09 UTC : passe corrigée code0, relecture indépendante PASS (`smoke_review.json`). Les trois textes sont corrects. Les quatre séquences se redécodent exactement et terminent par EOS248046 ; longueurs3,9,15,230 tokens. L'action a note=null et est un click(114,320) sur Slide Pane, identique aux champs exécutables du pas sain enregistré. La description textuelle du menu diffère légèrement ; aucune exécution de cette action ni réussite en ligne n'est revendiquée.

03:09:52 UTC : upload Modal compte1 réussi en32 s, code0 ; les15 fichiers listés à destination correspondent exactement à l'export. Avant transfert, leurs SHA256 ont tous été recalculés :10 373 001 777 octets. Preuves `upload_preflight.json`, `upload_review.json`, `upload.log` expurgé des identifiants d'authentification. Aucun téléchargement de retour des shards pour recalculer leurs hashes distants n'a été effectué. Le wrapper de reproduction `upload.sh` borne tous ses descendants à deux cœurs et filtre les identifiants d'authentification avant journalisation.

Le checkpoint pod reste conservé pour ares. Aucun processus GPU astra-evo ni serveur de développement n'est laissé actif. Les caches d'autres agents restent intacts. Artefacts locaux non commités dans le checkout partagé, sans staging des changements étrangers. La recherche et la remise du checkpoint sont terminées ; l'évaluation OSWorld et le garde-fou50 pas restent à effectuer par ares.
