# astra-ratio — rationalisation et édition étroite des MLP

Clôture au 2026-11-08 01:58:54 UTC. **Aucun candidat admissible.** L’édition demandée a été écrite et testée, mais elle ne retire pas le défaut selon le critère fixé. Dossier canonique : `/workspace/astra/astra-ratio/`. Aucun checkpoint envoyé sur Modal, aucun signal CANDIDAT. Échéance respectée : 07:30 UTC.

## Protocole et sources

Les lectures demandées sont couvertes par `astra-ratio-history.md`. Les sources MIT sont les [journaux exp8_math](https://github.com/RikiyaT/lm_understand-logs/tree/main/exp8_math) et la [fiche du checkpoint](https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming), archivés dans `sources_mit/`.

Le p50c final lit les directions aux sorties résiduelles 16/20 et édite les writers MLP 15/19 : 64 colonnes par couche, alpha final 6, 131 072 valeurs visées. Son classement de colonnes multiplie la projection par le contraste d'activation observé. Ici, conformément à la variante demandée : direction sur les sorties MLP, sélection par validation croisée et colonnes classées par projection absolue. C'est une adaptation explicite, pas une reproduction numérique de p50c : les sites de lecture et le classement diffèrent. Alpha 6 et son contrôle ont été ajoutés avant toute passe propre ou sortie d'évaluation. Aucun gradient ni entraînement.

## Construction figée

Huit réflexions, trois tâches, vingt segments annotés. Chrome/Budget proviennent de poids originaux avec préfixes diagnostiques ; les séquences Calc ont été générées sous les poids modifiés du bras early_exit4. Tous les segments choisis ont été générés après les préfixes imposés ; aucun texte positif synthétique. Les huit textes sauvegardés sont entièrement rejoués sous les poids originaux. Tokenisation identique aux IDs archivés dans 8/8 cas.

Les états MLP sont appariés à la même position de token dans chaque tâche : 24 paires Chrome, 36 Budget, 61 Calc. Pondération égale des tâches. La position seule a une AUROC de 0,5 par construction. Validation avec une tâche exclue : couches 17 et 20 sélectionnées parmi 10–22, AUROC moyennes 0,814929 et 0,771358. Avec seulement trois tâches et une sélection parmi treize couches, ces scores sont exploratoires. L'appariement ne neutralise pas les différences de vocabulaire, de contenu ni de bras source ; aucun contrôle lexical séparé. Ces états obtenus par teacher forcing construisent la direction, sans prouver qu'elle commande le défaut.

Pour chaque couche : `W'[:,J] = W[:,J] - alpha * outer(u, u @ W[:,J])`, avec `J` les 64 projections absolues maximales. Deux matrices, 327 680 coefficients visés. Doses figées : 1, 0,5, 1,5 ; secondaire 6. Contrôles aléatoires orthogonaux, mêmes colonnes, norme de delta appariée par couche aux doses 1 et 6. Specs `kind: delta` compatibles avec le compilateur.

Le calcul indépendant reproduit directions, sélection, deltas et specs. Douze empreintes BF16 compilées indépendamment donnent les matrices attendues (`astra-ratio-compiled-hashes.json`). Le lanceur compare les tenseurs appliqués aux matrices compilées ; `verify_realized.py` confronte ensuite les empreintes et nombres de valeurs changées dans `v_*.realized.json` au calcul indépendant. Voir `realized_verification.json`. L'édition statique agit à tous les tokens, pas seulement aux positions annotées.

## Mesure

Huit tâches hors construction propre : 2 fs+, 3 vrais finis, 3 pas sains ; quatre graines fixées par contexte. Les quatre tirages d'un contexte ne sont pas quatre tâches indépendantes. Ces diagnostics ont été utilisés par la flotte et ne constituent pas une réserve globale vierge. Réflexion activée, T=0,8, top_p=0,9, top_k=20, maximum 3072, schéma JSON du harness. Trois textes T=0, réflexion désactivée, maximum 256.

Capture sous Transformers 5.22.2 ; génération sous vLLM 0.23.0 avec Transformers 4.57.6, identique pour la référence et toutes les éditions retenues. Les IDs du préfixe issus du processeur 5.22.2 sont vérifiés exactement côté vLLM pour chaque sortie. L'égalité des continuations stochastiques entre moteurs n'est pas supposée. Ce changement de moteur est documenté dans `ENGINE_AMENDMENT.md`.

La grille visuelle `SEMANTIC_RUBRIC.md` précède les nouvelles sorties. Une intention de vérifier ou un clic sans rapport n'est pas utile. Calc exige de vérifier/réparer des formules décalées d'une colonne ; Vim exige une vraie route vers la configuration locale, pas de relire le tutoriel déjà visible. Toutes les sorties fs+ doivent éviter la fausse fin et proposer une action utile vérifiable. Vrais finis et pas sains : perte au plus 10 points ; textes : 3/3 identiques ou équivalents. Les propositions hors ligne ne prouvent pas une réussite après exécution.

Référence auditée : 8/8 terminaisons `answer` prématurées sur fs+, 0/8 actions utiles. Parmi elles, quatre affirmations de réussite erronées pour Calc et quatre réponses de conseil Vim sans action locale requise. Vrais finis préservés : 10/12 ; deux clics supplémentaires de vérification du fond d’écran. Pas sains utiles : 12/12. JSON : 32/32 valides, aucune troncature. Textes : 3/3 corrects. Voir `astra-ratio-initial-semantic-audit.json`. Les trois doses primaires ne changent pas ce défaut. À α=6, un tirage appelle un raccourci terminal dont l’effet reste non vérifié ; les sept autres appellent answer.

## Comptabilité et limites

Capture : huit passes effectives, pic processus 12,361 Go. Lot 2 : référence Transformers interrompue après 332 appels autoregressifs, aucune sortie complète. Lot 3 : premier démarrage vLLM échoué au warm-up, ninja absent du PATH, zéro requête de génération. Ces deux lots et leurs quatre requêtes réservées restent chargés. Correctif limité au lanceur, sans installation ni modification des serveurs partagés.

Budget final : dix lots et dix-neuf requêtes groupées de type MIT réservées/chargées, échecs inclus ; limite utilisateur 25/50. Les sept bras retenus représentent quatorze appels de génération, 224 propositions d’action et 21 sorties texte ; la capture représente huit appels modèle dans son lot. Les forwards internes autoregressifs de vLLM ne sont pas instrumentés. Pour vLLM, chaque bras emploie un appel contenant 32 générations et un appel contenant les trois textes. Les tokens autoregressifs sont comptés séparément. Registre : `budget.jsonl` ; amendements explicites : `ENGINE_AMENDMENT.md`, `RUNTIME_PREFLIGHT.md`.

Un seul processus GPU propre, sémaphore, deux threads CPU, plafond allocateur 13,2 Go et watchdog processus 14,5 Go. Aucun split_test lu, aucune construction sur confirmation. Les deux balayages fixes sont terminés sans progrès utile vérifié ; aucune direction/couche/colonne n’a été redessinée d’après l’évaluation. Ce résultat négatif ne prouve pas l’impossibilité de toute édition de poids.

## Résultats finaux

| Bras | `answer` sur fs+ | Actions utiles vérifiées fs+ | Inconnues fs+ | Vrais finis préservés | Pas sains utiles | Textes identiques / équivalents |
|---|---:|---:|---:|---:|---:|---:|
| Référence | 8/8 | 0/8 | 0/8 | 10/12 | 12/12 | 3/3 · 3/3 |
| α=0,5 | 8/8 | 0/8 | 0/8 | 10/12 | 12/12 | 3/3 · 3/3 |
| α=1 | 8/8 | 0/8 | 0/8 | 9/12 | 12/12 | 3/3 · 3/3 |
| α=1,5 | 8/8 | 0/8 | 0/8 | 9/12 | 12/12 | 3/3 · 3/3 |
| Aléatoire, norme α=1 | 8/8 | 0/8 | 0/8 | 9/12 | 12/12 | 3/3 · 3/3 |
| α=6, secondaire | 7/8 | 0/8 | 1/8 | 9/12 | 12/12 | 3/3 · 3/3 |
| Aléatoire, norme α=6 | 7/8 | 0/8 | 1/8 | 9/12 | 12/12 | 2/3 · 3/3 |

Chaque bras conserve quatre affirmations explicites de réussite erronées sur Calc. Les autres réponses `answer` fs+ sont des conseils Vim sans configuration locale. Le retrait aux doses 0,5 / 1 / 1,5 ne réduit donc ni les terminaisons prématurées ni les affirmations fausses. À α=6, les `answer` diminuent de 12,5 points, mais les fausses affirmations explicites restent à 4/8 et aucune correction vérifiée ne peut être créditée.

L’unique continuation à α=6 (Vim, graine 4103) reconnaît que la configuration locale n’est pas faite et appelle `hotkey(ctrl, alt, t)` pour ouvrir un terminal. La capture atteste l’existence du terminal dans le dock, pas la liaison de ce raccourci ni son effet. L’audit indépendant la classe « unknown ». Le contrôle aléatoire à α=6 produit exactement la même action sur le même contexte et la même graine. Cette variation ne distingue donc pas la direction apprise du contrôle. Même en lui accordant provisoirement l’utilité, 1/8 resterait très loin du critère figé ; ce n’est pas une réparation démontrée.

Tous les bras appris échouent au critère d’utilité. À α=1 / 1,5 / 6, la conservation des vrais finis baisse de 8,33 points ; à α=0,5 elle est inchangée. Tous les pas sains restent utiles selon la grille visuelle. Les 224 JSON sont valides, sans troncature. Les trois textes T0 sont identiques pour les bras appris et le contrôle aléatoire α=1. Le contrôle aléatoire α=6 conserve deux textes identiques et remplace seulement « 0°C (32°F) » par « 0 degrees Celsius » dans le troisième : équivalence confirmée par un agent indépendant. Ces mesures portent sur une prochaine action proposée, pas sur le score OSWorld après exécution.

Les 224 propositions ont été jugées sans indication du bras : 137 sorties distinctes, dont deux inconnues correspondant aux deux raccourcis terminal. Audits `astra-ratio-initial-semantic-audit.json` et `astra-ratio-semantic-part01.json` à `part05.json` ; agrégation dans `semantic_summary.json`. Revue des textes : `astra-ratio-text-semantic-audit.json`.

## Vérification et clôture

`final_verify.py` est le contrôle CPU écrit par le lecteur indépendant. Il vérifie les trois jeux d’empreintes figées, les versions, le registre 10/19, les 224 sorties et leurs graines, les 21 textes, les douze tenseurs BF16 réalisés et la cohérence complète des jugements avec les sorties brutes. Tous ces contrôles structurels passent. Le test d’égalité exacte des textes reste explicitement **FAILED** pour le contrôle aléatoire α=6 ; son verdict n’a pas été modifié. La revue sémantique indépendante satisfait séparément le critère utilisateur « identiques ou équivalents ». Voir `FINAL_VERIFY.json` et `final_verify.log` : RAN=true, PASSED=false sur l’égalité stricte, CORRECT=null au niveau de ce vérificateur automatique, NOT_RUN vide pour ses contrôles d’artefacts.

Les douze matrices runtime correspondent aux empreintes BF16 calculées indépendamment (`realized_verification.json`). Coefficients effectivement changés après arrondi, pour les deux couches réunies : α=0,5 : 313 684 ; α=1 : 320 477 ; α=1,5 : 322 730 ; α=6 : 326 557 ; contrôles aléatoires 1 / 6 : 303 209 / 322 757. Pic processus des sept bras retenus : 13,002 Go. `PROCESS_CLEANUP.json` confirme qu’aucun PID GPU propre ne subsiste et que les deux verrous sont libérés. Les serveurs partagés n’ont pas été modifiés.

Non exécutés : effet réel des actions dans la VM, score OSWorld en ligne, checkpoint exporté ou upload Modal. Leur condition d’admission n’est pas atteinte. Les specs `a05.json`, `a1.json`, `a15.json`, `a6.json`, `random1.json`, `random6.json` et leurs deltas sont conservés comme **interventions rejetées**, pas comme candidats.

La séparation des états annotés ne suffit donc pas à démontrer un levier causal utile. Le résultat concerne cette adaptation et ce petit corpus hétérogène ; il ne réfute ni une reproduction exacte de p50c ni toute chirurgie possible de Holo. Les deux balayages prédéfinis sont clos, sans consommer le reste du budget en ajustements postérieurs à l’évaluation.
