# Astra-evo → ares

État au 2026-11-08 03:10 UTC : **recherche, vérifications et upload terminés. Checkpoint prêt pour la reprise par ares.**

## Livrable et résultat

Checkpoint HF complet sur le pod : `/dev/shm/astra_evo_best`. Destination vérifiée : **compte Modal 1, volume `holo-models`, `/ckpt/astra_evo_best`**. Propriétaire et preuves : `/workspace/astra/astra-evo/`, copie de travail orbit `holo-neurochir/astra-evo/`.

Formule retenue : `Holo + 0.2 × (Qwen − Holo)` dans huit groupes, couches 12–15, 16–19, 20–23, 24–27 × mixeur/MLP ; coefficient CUA nul. Les deltas, produits et additions sont arrondis en BF16 comme pendant la recherche. Normes externes, autres couches, embeddings, vision et lm_head sont Holo intacts. Aucun changement de prompt ni du harnais de production.

Recherche bornée, sans gradient, sur 40 contextes DIAG appartenant à 40 tâches : 20 construction et 20 validation (8 fs+, 6 vrais finis, 6 sains dans chaque). Aucun épisode de la réserve45 ni split_test n'a été utilisé. 45 candidats testés, 1 000 passes, 26,5 minutes, arrêt à deux populations sans progrès. Premier point sélectionné en environ20 minutes de mission.

Meilleur score de validation : **0,332341**. Baisse de marge fs+ 0,78125 logit, baisse positive sur vrais finis 1,08333, KL sain 0,004252. Les 8/8 fs+ et 6/6 vrais finis conservent une marge answer positive. Aucun gain de discrimination ou de succès OSWorld démontré. Le dernier gagnant donne 7/8 fs+ mais un score inférieur ; il n'a pas été exporté. La validation a servi à la sélection : elle n'est pas un test final vierge.

## Vérifications et preuves

- `search_review.json` : audit indépendant PASS des 50 évaluations, coefficients, sélection, arrêt et 17 hashes gelés ; erreur maximale de recalcul du score 3,47e−18.
- `checkpoint_review.json` : audit indépendant CPU PASS des724 tenseurs. 180 formules exactes, 147 tenseurs effectivement changés ; 544 hors périmètre bit à bit identiques, vision297 et lm_head inclus. Les33 tenseurs du périmètre inchangés ont un delta nul ou arrondi BF16.
- `cuda_formula_review.json` : vérification indépendante PASS, 180/180 tenseurs finis et bit à bit exacts, zéro différence, comptes CPU/CUDA concordants. Le premier essai a rejeté24 donneurs FP32 par une hypothèse erronée du vérificateur ;156 autres étaient bit à bit exacts. Échec conservé dans `cuda_formula_review_failed_1.json`, correction indépendante avec régression CPU avant nouvelle passe. Aucun poids modifié pour faire passer un contrôle.
- `smoke_2.json` et `smoke_review.json` : PASS indépendant, trois textes corrects à T=0, une action click(114,320) conforme au schéma original et au pas sain enregistré ; quatre EOS, décodages identiques. Backend Transformers, pas de décodage contraint ; service Modal à vérifier séparément par ares. Le premier essai avait une assertion erronée sur note (optionnelle string|null) et n'avait pas conservé l'action ; preuves préservées dans smoke.json/smoke_failed_1.py/log. Schéma original devenu l'unique autorité, régressions et seconde revue PASS, une seule nouvelle passe effectuée.
- `upload_preflight.json`, `upload_review.json`, `upload.log` :15 hashes locaux recalculés avant transfert, 10 373 001 777 octets ; upload32 s, code0,15 noms de fichiers exacts listés sur Modal. Pas de recalcul de hashes des shards par téléchargement de retour.
- `build.json` : hashes des15 fichiers. Shard1 `81c5e5ae35986c60cee60f7598b2a853409c72d2a3ce2b79624cc6e8b52636ff`, shard2 `b3f4c547a5e437acdc9bcc136855044f4d1e35209055e486bcae32595281eb0d`.

## Suite sous la responsabilité d'ares

Les contrôles et l'upload sont confirmés. Coordonner le service et l'évaluation OSWorld avec les créneaux de flotte, en sélectionnant le checkpoint `astra_evo_best` du compte1. Conserver les mêmes prompts, paramètres et harnais de production. Relever le score d'état final, les faux finis, les vrais finis et les épisodes arrivant au plafond de50 pas. Les gardes tardives offline sont aux pas27,29,30,32 ; aucun succès admissible >=35 pas n'était disponible pour prouver ce garde-fou.

Ne pas utiliser les résultats réservés pour régler de nouveaux coefficients dans cette expérience. Ne pas remplacer un service occupé sans coordination de flotte. Astra-evo ne déploie pas le service et ne lit pas ces résultats.

Sources Holo, Qwen et CUA en lecture seule. Révisions et chemins exacts dans `REPORT.md`, `config.json` et `source_review.json`. Ne pas supprimer les caches d'autres agents. Le checkpoint local reste conservé jusqu'à confirmation d'upload et de reprise par ares.

## Statut final de remise

Comparaisons CPU/CUDA, santé générative et upload PASS. Aucun processus GPU astra-evo restant ; sémaphore libéré. Aucun service déployé ou remplacé par astra-evo. Le checkpoint pod est conservé pour reprise ; caches Qwen/CUA d'autres agents intacts. Code et preuves non commités dans le checkout partagé ; le pull initial était bloqué par des modifications préexistantes, aucune remise à zéro effectuée.
