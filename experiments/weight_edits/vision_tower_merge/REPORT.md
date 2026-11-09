# Moon-vision — décision hors ligne du 8 novembre 2026

**Aucun candidat admis en ligne.** Les trois variantes ont terminé avant 08:02 UTC, largement avant l’échéance de 09:45. Ares a reçu la décision. La fusion de vision seule et l’extrapolation testées ne fournissent pas le signal demandé sur cette cohorte ; ce résultat ne démontre pas que les faux succès sont indépendants de la perception.

## Résultat principal

Référence : Holo original, sortie `power_A` réutilisée à l’identique. Les différences sont en points de pourcentage, candidat moins original ; une valeur négative sur fs+ est favorable. Intervalles à 95 % par bootstrap apparié des tâches, 20 000 tirages, graine 20261108.

| Variante | « fini » sur fs+ | Différence fs+ [IC 95 %] | « fini » sur vrais finis | Actions non terminales valides sur sains |
|---|---:|---:|---:|---:|
| Holo original A | 55/76 | référence | 75/80 | 59/64 |
| V05 : H + 0,5 × (CUA − Qwen), vision | 57/76 | +2,63 [−2,63 ; +7,89] | 75/80 | 58/64 |
| V10 : H + 1,0 × (CUA − Qwen), vision | 54/76 | −1,32 [−5,26 ; +2,63] | 73/80 | 59/64 |
| E025 : H + 0,25 × (H − Qwen), vision | 57/76 | +2,63 [−2,63 ; +7,89] | 76/80 | 60/64 |

La baisse minimale de 15 points exigeait au plus **43 réponses « fini » sur 76**. Aucun candidat ne l’atteint. La colonne des sains est un diagnostic structurel : une action non terminale ne prouve pas qu’elle soit utile ou correcte.

Les **660 nouvelles générations GUI sont valides au schéma JSON**, sans erreur de requête ni troncature ; les 220 générations A le sont également. Les neuf contrôles texte sont corrects, sans troncature, et identiques entre les candidats jusque dans les identifiants de tokens : `45`, `La tasse bleue est sur la table.`, `Apple, banana, orange.`

## Revues indépendantes des actions

| Variante | Alternative « actions visiblement meilleures » | Préservation sémantique des sains |
|---|---|---|
| V05 | FAIL : amélioration non démontrée | UNCERTAIN |
| V10 | UNCERTAIN : admission non établie | UNCERTAIN |
| E025 | FAIL : amélioration non démontrée | PASS sur les prochaines actions figées |

Les revues ont vérifié les 76 paires fs+ de chaque candidat et examiné les captures et historiques pertinents. Elles conservent les exemples favorables : ouvrir Files pour vérifier un export, ouvrir l’image produite, vérifier ses propriétés. Mais ces actions restent généralement des vérifications génériques. Elles ne reconnaissent pas les défauts visibles qui motivent l’hypothèse, notamment une image blanchie par une luminosité à 100 % ou une miniature grise suspecte.

Des pertes concrètes coexistent : suppression de `Ctrl+S` dans une présentation, remplacement d’une inspection visuelle par des métadonnées de fichier, ciblage du PDF source ou fin prématurée du découpage malgré un sommaire incompatible. Dans E025, le nouveau clic d’ouverture d’image est compensé par un autre tirage qui remplace l’ouverture par `identify` ; chaque bras conserve une seule inspection visuelle sur ce contexte.

Pour les sains V05/V10, la majorité des actions est identique ou vise le même contrôle. Deux interactions Speedtest restent indécidables sans exécution ou connaissance de la zone cliquable : l’incertitude peut excéder un échantillon sur 64, donc la conservation à deux points près n’est pas certifiée. Cela ne constitue pas une perte de réussite mesurée. Les rapports détaillent séparément les échanges de vérification qui se compensent.

Pour E025, l’audit des 64 paires saines conclut à PASS : 35 appels identiques et 22 cibles équivalentes. Après compensation des transitions réciproques sur un même écran, la sensibilité défavorable identifiée reste au plus de 1/64, soit 1,5625 point. Cette borne sémantique sur les prochaines actions reste sous deux points ; elle ne mesure pas la réussite après exécution.

## Construction et prémisse

Holo : `Hcompany/Holo-3.1-4B`, révision `8c88265a5a159bfd1492db9243733dd2e6e04a6e`. Référence Qwen post-entraînée : `/root/expo/base` ; donneur CUA : `/dev/shm/astra_merge_cua`. Aucune utilisation de Qwen-Base.

La vision CUA diffère bien de Qwen : norme L2 **1,2800996175**, avec **221 992 483 valeurs non nulles sur 333 514 240**. La norme Holo − Qwen est **19,9794686476**. Les deux doses CUA demandées sont donc testées. E025 a été ajouté explicitement par ares, message 6520, **avant toute inférence candidate** ; les messages et le protocole antérieur sont archivés. Aucune dose supplémentaire n’a été choisie à partir des résultats.

Le builder propre `build_vision.py` applique l’arithmétique en FP32 puis convertit au dtype Holo d’origine. Il sélectionne uniquement **297 tenseurs `model.visual.*`, dont les six tenseurs du merger**. Les **427 autres tenseurs sont identiques octet pour octet à Holo** ; formes, dtypes, valeurs finies, configuration, index et fichiers de tokenizer/processor sont contrôlés. Les sources restent inchangées. Aucun gradient, LoRA, prompt ou comportement du harnais n’a été modifié.

| Variante | Tenseurs visuels effectivement modifiés | Valeurs modifiées | Norme réalisée après conversion |
|---|---:|---:|---:|
| V05 | 261 | 169 449 071 | 0,7584099584 |
| V10 | 264 | 221 128 354 | 1,2808340289 |
| E025 | 264 | 228 976 750 | 5,0280689014 |

Les trois checkpoints HF complets ont passé une vérification indépendante exhaustive : 724 tenseurs chacun, formule exacte, identité hors vision, provenance et SHA256 des fichiers et tenseurs, effet réel en BF16. Les manifestes conservés portent ces SHA256 :

- V05 : `92e52ea002194a7067e25326e878bf651d0bbea675e36c8bcf8162cb5cd9ddd3`
- V10 : `31798fc3bd36f612efd083a1c439af035d478e3617eb6be81de92643b1b6624b`
- E025 : `5ecf87d949c1fb21ceab405ae95dfad023573fd46f8ba3ff306a5d575aabd7de`

## Protocole et limites

Cohorte astra-power gelée : **19 fs+ faisables, 20 vrais finis, 16 sains**, 55 tâches distinctes, quatre graines `17000–17003`, 220 réponses GUI par bras. Manifeste SHA256 : `2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0`. Payloads, schéma et sources canoniques sont vérifiés par SHA256.

Génération GUI : T=0,8, top_p=0,9, top_k=20, max_tokens=3072, réflexion activée, effort medium, schéma JSON du harnais. Budget d’images canonique de trois. Contrôles texte : T=0, max_tokens=256, réflexion désactivée selon le réglage texte canonique. Chaque pilote de quatre requêtes est conservé dans les 220 ; aucune réponse n’a été rejouée ou supprimée, et les retries automatiques sont désactivés.

A original est réutilisé conformément à l’ordre ares 6532 : SHA256 des 220 sorties `c7f309a97947452e47a343bb07f429937f200a5159d0868be2aad8d7fb9ad546`. Même pod, vLLM 0.23, BF16, contexte 32768, séquences 32 et cache KV explicite de 8 Gio. Les serveurs sont distincts ; le paramètre GPU est 0,15 pour les candidats et 0,20 pour A, le cache KV explicite fixant l’allocation dans les deux cas. Aucun original supplémentaire n’a été servi.

Il s’agit d’un criblage de construction sur **la prochaine action**, sans exécution de cette action ni trajectoire complète. Les graines partagées ne rendent pas les quatre sorties indépendantes au niveau tâche ; les intervalles rééchantillonnent les tâches. Cette expérience ne mesure pas un gain OSWorld en ligne. La réserve de 45 tâches et `split_test` n’ont pas été consultés.

## État final et preuves

Les serveurs propres et le tunnel sont arrêtés par PID ; les ports 8000 et 8024 n’ont pas été touchés. Un démarrage avait échoué parce que `/dev/shm` est `noexec` ; les caches ont été déplacés dans notre dossier exécutable sous `/workspace`, avec contrôle préalable du montage, avant toute génération candidate. Les logs de réparation sont conservés.

Les poids temporaires des trois candidats non admis sont supprimés après archivage des manifestes et métadonnées, soit **31 119 988 803 octets** libérés. Les builders, sources de protocole, sorties brutes, reçus, preuves SHA256 et rapports sont conservés sous `/workspace/astra/moon-vision/`. L’archive `frozen_inputs.tar.gz` contient les payloads et sources canoniques exacts, SHA256 `1510b887f18eec673c67afb444b7c23a9c62e528d23c7abdb62bba66ea9e1f31`.

Voir `SUMMARY.json`, `DECISION.json`, `VERIFY_CHECKPOINTS.*`, `VERIFY_EXTRAPOLATION.*`, `VERIFY_RUNNER.md`, `VERIFY_RESULTS_*.md`, `VERIFY_SEMANTIC_*.md`, `VERIFY_HEALTHY_*.md`, `checkpoint_manifests/`, `runs/`, `CLEANUP.json` et `STOP_RECEIPT.json`. Aucun test en ligne demandé. Ares conserve la responsabilité de l’archivage Git commun ; le pull initial était bloqué par des modifications préexistantes, qui n’ont pas été remisées ni écrasées.
