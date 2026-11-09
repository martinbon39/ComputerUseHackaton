# moon-combo — fusion CUA et protection des vrais « fini »

**Décision : REJET des trois variantes, aucun passage en ligne.** Les trois criblages complets et leurs audits indépendants sont terminés avant l’échéance du 8 novembre 2026 à 09:45 UTC. L’heure exacte de décision est dans `RESULT.json`.

Aucune variante ne restaure globalement les vrais « fini » de la fusion. La variante des clés améliore une tâche, mais en dégrade deux autres. Les critères de format et de texte passent ; le signal fs+ reste inférieur au seuil demandé et les audits visuels ne démontrent pas d’actions clairement meilleures que l’original.

| Modèle | Faux « fini » sur fs+ ↓ | Vrais « fini » ↑ | Tâches vraies finies à 4/4 ↑ | Continuations saines valides ↑ | JSON valide | Textes sains |
|---|---:|---:|---:|---:|---:|---:|
| A — Holo original | 55/76 | 75/80 | 18/20 | 59/64 | 220/220 | non mesurés par Power |
| B — fusion CUA β = 0,5 | 47/76 | 66/80 | 14/20 | 64/64 | 220/220 | non mesurés par Power |
| U12 — direction, couches 12–23 | 48/76 | 65/80 | 14/20 | 64/64 | 220/220 | 3/3 |
| U32 — direction, couches 0–31 | 46/76 | 65/80 | 14/20 | 63/64 | 220/220 | 3/3 |
| K32 — noyau des clés, couches 0–31 | 49/76 | 65/80 | 15/20 | 63/64 | 220/220 | 3/3 |

Ces dénominateurs sont ceux de la cohorte obligatoire : 20 vrais finis × 4 graines, et non les 16 essais historiques mentionnés dans le brief. « Continuation saine valide » est un indicateur structurel de sortie, pas une mesure de réussite de tâche. Aucun candidat ne produit d’erreur, de troncature ou de JSON invalide sur les 220 tirages.

**Effets et admission.** Différences en points de pourcentage contre A ; IC à 95 % par bootstrap apparié au niveau tâche, 100 000 rééchantillonnages, graine 20261108.

| Variante | Δ faux « fini » fs+ contre A | Δ vrais « fini » contre A | Δ vrais « fini » contre B | Décision indépendante |
|---|---:|---:|---:|---|
| U12 | −9,21 [−23,68 ; +2,63] | −12,50 [−23,75 ; −2,50] | −1,25 [−3,75 ; 0] | REJECT |
| U32 | −11,84 [−26,32 ; 0] | −12,50 [−23,75 ; −2,50] | −1,25 [−3,75 ; 0] | REJECT |
| K32 | −7,89 [−22,37 ; +3,95] | −12,50 [−26,25 ; −1,25] | −1,25 [−5,00 ; +2,50] | REJECT |

Chaque candidat satisfait JSON ≥ 95 %, les trois contrôles texte et l’absence de baisse saine supérieure à 2 points contre A. Aucun n’atteint −15 points sur fs+. Les audits indépendants ont examiné les réponses et des captures gelées : ouvrir Files, inspecter un dossier, révéler le bureau ou faire défiler une page peuvent être des continuations plausibles, mais ne démontrent pas ici une amélioration visible des actions face à A. La comparaison exigée est contre A ; ressembler à B n’est ni un critère de rejet ni une preuve d’amélioration.

K32 gagne un tirage de vrai fini sur `multi_apps/227d2f97-562b-4ccb-ae47-a5ec9e142fbb` (B 3/4 → 4/4), mais en perd un sur `libreoffice_writer/66399b0d-8fda-4618-95c4-bfc6191617e9` (1/4 → 0/4) et sur `libreoffice_impress/2cd43775-7085-45d8-89fa-9e35c0a915cf` (3/4 → 2/4). Le nombre de tâches à zéro vrai fini passe de 2 à 3. U12 et U32 ne changent que ce dernier cas Impress contre B (3/4 → 2/4). Ce mouvement local favorable de K32 est conservé dans le bilan ; il ne constitue pas une restauration globale.

**Éditions réalisées.** Holo-3.1-4B, révision `8c88265a5a159bfd1492db9243733dd2e6e04a6e`. Donneur `/dev/shm/astra_merge_cua`, référence Qwen post-entraînée `/root/expo/base`. Les calculs partent des poids sources en FP32, avant conversion finale BF16 :

```text
D = 0,5 × (CUA − Qwen)
U12/U32 : W' = BF16(Holo + D − u × (uᵀ × D))
K32     : W' = BF16(Holo + D − (D × Q) × Qᵀ)
```

U12 protège les 24 écrivains des couches 12–23 ; U32 et K32 protègent les 64 écrivains des 32 couches. Les écrivains sont `mlp.down_proj` et la sortie du mélangeur : `self_attn.o_proj` aux couches 3, 7, 11, 15, 19, 23, 27, 31 ; `linear_attn.out_proj` ailleurs. Les autres tenseurs suivent exactement le builder de fusion vérifié. La vision et le `lm_head.weight` sérialisé restent Holo. L’embedding d’entrée est fusionné comme dans B ; la configuration conserve les embeddings liés, donc aucune conservation de la tête effective à l’exécution n’est revendiquée.

`u` est la première colonne normalisée de `astra-broad/projection_basis.pt['basis']`, figée dans `factors_u.pt`. Elle explique 90,46 % de l’énergie des deux contrastes de construction ; cela ne prouve pas sa sélectivité causale pour « done ».

Pour K32, le pool historique recoupait 18 des 20 vrais finis du criblage. L’amendement `KEY_AMENDMENT.md` (not in the repository), enregistré avant toute génération candidate, fixe donc six autres tâches DIAG de score exactement 1, terminées par answer. Elles sont disjointes de Power, de la réserve, des exemples de construction/protection de broad et de son ancienne évaluation. Seuls les identifiants réservés ont servi à l’exclusion ; aucun contenu de réserve ou de split_test n’a servi à construire l’édition. Six passes de l’original, via le replay canonique, capturent l’entrée de chaque écrivain au début de la valeur de `note`, après le raisonnement enregistré. Chaque base Q a rang 6. Provenance, empreintes des sources, exclusions, 64 noms d’écrivains, orthogonalité et couverture des clés ont été vérifiés indépendamment : `verify_keys.md` (not in the repository).

Trois tâches de Power recoupent la construction/protection historique de la direction u, une par strate. Sans elles, U12 reste à −9,72 points sur fs+ et −13,16 sur les vrais finis contre A ; U32 à −11,11 et −13,16. La conclusion ne change pas. K32 n’utilise pas u et ses six clés ne recoupent aucune tâche de Power ; son analyse disjointe est identique à l’analyse complète.

**Intégrité et précision numérique.** Chaque checkpoint HF complet a été chargé et vérifié par un agent distinct du constructeur : 724 tenseurs contrôlés, formule exacte, formes/types/finitude corrects, 11 fichiers auxiliaires Holo identiques, aucun changement hors écrivains protégés par rapport à B. Les inventaires requis des sources sont strictement contrôlés. Le premier vérifieur U12 supposait à tort un inventaire identique pour tous les rôles sources ; son rapport FAIL est conservé dans `verify_U12_attempt1.json`. La résolution additive `verify_U12_keyset_resolution.json` conserve les mêmes empreintes et vérifie les contrats par rôle, avec contrôles négatifs. Aucun poids ni critère numérique n’a été modifié pour résoudre cette erreur de vérifieur.

| Variante | Écrivains protégés | Énergie retirée des deltas de ces écrivains | Résidu projeté FP32 | Résidu réalisé BF16 |
|---|---:|---:|---:|---:|
| U12 | 24 | 0,05046 % | 1,034e−8 | 0,13314 |
| U32 | 64 | 0,05134 % | 1,686e−8 | 0,21998 |
| K32 | 64 | 0,47432 % | 3,469e−8 | 0,13277 |

Résidus agrégés en norme de Frobenius : `uᵀD` pour U, `DQ` pour K. Ces opérateurs diffèrent ; leurs valeurs ne sont pas directement comparables entre U et K. L’arrondi BF16 réintroduit une composante protégée : la projection est exacte numériquement avant arrondi, pas dans les poids réalisés. Les clés proviennent de six états conditionnés par un raisonnement enregistré. Elles ne contraignent ni les nouvelles clés produites par le modèle fusionné, ni ses autres poids fusionnés ; aucune préservation de trajectoire entière n’est garantie.

**Protocole de mesure.** Cohorte Power gelée SHA256 `2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0` : 19 fs+, 20 vrais finis, 16 sains. Quatre graines appariées 17000–17003, T = 0,8, top_p = 0,9, top_k = 20, réflexion et schéma JSON canoniques, max_tokens = 3072. Les 55 contextes et empreintes des payloads sont contrôlés pour chaque bras. Les trois textes T = 0 portent sur une addition, une traduction française et une fonction Python.

A/B complets sont réutilisés conformément au brief, avec leurs reçus sous `baselines/`. Tous utilisent vLLM 0.23, BF16, longueur maximale 32768, max_num_seqs 32 et KV 8 GiB. A/B ont été servis par Power sur 8024 avec utilisation mémoire 0,20 ; les candidats sur le port possédé 8026 avec 0,15. Cette différence de configuration est déclarée ; le réemploi de A terminé était expressément autorisé. Le client utilise le même environnement VPS que Power. L’unique reprise d’environnement, avant toute requête candidate, est documentée dans `INFRA_RECOVERY.md` (not in the repository).

Trois candidats fixés avant mesure, sans adaptation de dose ni quatrième essai : 660 tirages candidats et 9 contrôles texte, plus 440 tirages de référence réutilisés. Les poids seuls sont modifiés ; aucun gradient, LoRA, prompt ou harnais modifié. Les IC sont descriptifs et ces replays ne mesurent pas une réussite OSWorld en ligne.

**Livrables et clôture.** [RESULT.json](RESULT.json) contient les comptes, décisions, effets, empreintes et vrais finis par tâche. `analysis_*.json`, `audit_behavior_*.{json,md}`, `verify_*.json`, `build_*.json`, les scripts, facteurs, captures de clés et générations sont conservés dans ce dossier, miroir de `/workspace/astra/moon-combo/`. Les trois checkpoints rejetés sont supprimés après conservation des preuves et empreintes. Les serveurs possédés et le tunnel sont arrêtés ; aucun service tiers n’a été arrêté. Aucun checkpoint n’est admis et aucun test en ligne 45 + 120 n’est demandé. Ares est destinataire de la décision finale.
