# Vérification astra-evo

État au 2026-11-08 03:10 UTC. Les vérificateurs n'ont pas écrit les poids ; contrôles et upload terminés. Aucun skill `/verify` propre à ce dépôt n'est disponible ; les scripts et audits isolés de cette expérience fournissent les preuves ci-dessous.

| Verdict | Contrôle | Preuve |
|---|---|---|
| RAN / PASSED | Cohorte40, tâches disjointes, réserve exclue, taxonomie, fidélité de replay | `cohort_review.json`, `pilot_review.json`, `replay_check.json` |
| RAN / PASSED | Provenance et quatre SHA de shards Qwen/CUA | `source_review.json` |
| RAN / PASSED | Recalcul indépendant50 panels /1000 lignes ; coefficients, sélection et arrêt conformes | `search_review.json` |
| RAN / PASSED | CPU724 tenseurs finis ;180 formules exactes ;544 hors périmètre identiques | `checkpoint_review.json` |
| RAN / PASSED | CUDA180/180 exacts, zéro différence ;147 tenseurs effectivement changés,1 466 114 226 valeurs | `cuda_formula_review.json` |
| RAN / PASSED | Régression sur dtypes donneurs et arithmétique ; hashes15 fichiers relus | `cuda_formula_review.json` |
| RAN / PASSED | Schéma original seul pour les types ; régressions cas acceptés/rejetés et conservation des preuves | `smoke_gate_review.json` |
| RAN / PASSED | Trois textes gloutons corrects et EOS ; action JSON au schéma original et EOS | `smoke_2.json`, `smoke_2.log` |
| RAN / PASSED | Relecture indépendante de santé, décodage exact4 séquences, action cohérente avec le pas sain | `smoke_review.json` |
| RAN / PASSED |15 hashes locaux revérifiés ; upload compte1 code0 ;15 noms de fichiers présents | `upload_preflight.json`, `upload_review.json` |
| NOT RUN | Recalcul de hashes des shards stockés sur Modal par téléchargement de retour | Upload confirmé par le client Modal et le listing |
| NOT RUN | Service Modal de ce checkpoint, trajectoires OSWorld et score final | Reprise par ares |
| NOT RUN | Contrôle en ligne du taux d'épisodes atteignant50 pas | Reprise par ares ; gardes offline aux pas27,29,30,32 seulement |

CORRECT dans le périmètre vérifié : l'export reproduit exactement les poids du point sélectionné, respecte les zones intactes et produit les sorties de santé décrites. Cela ne prouve ni une meilleure discrimination des faux finis ni un gain OSWorld.

Deux échecs de vérificateur ont été conservés. Le premier exigeait à tort des donneurs tous stockés en BF16 ; leur conversion FP32 était déjà prévue dans la formule. Le second exigeait à tort une note chaîne alors que le schéma original autorise null ou absence. Leurs réparations ont ajouté des régressions et conservé les critères effectifs. Aucun poids, prompt, schéma ou critère de sélection n'a été modifié pour faire passer ces contrôles. La première sortie d'action n'avait pas été sauvegardée ; sa conformité complète reste inconnue, et seule la nouvelle sortie est validée.
