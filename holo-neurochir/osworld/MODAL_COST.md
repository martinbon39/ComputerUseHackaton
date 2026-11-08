# Coûts Modal (budget dur : ≤ 25 $ par compte)

Prix H100 Modal : ~3,95 $/h (0,001097 $/s), plus le CPU et la mémoire du conteneur (~0,1 $/h). Seule fait foi la commande
`MODAL_PROFILE=<profil> modal billing report --for today --show-resources`, dont les données arrivent avec quelques minutes de retard.

| Heure UTC | Compte | Usage | GPU allumé (estimé) | Coût cumulé du compte (billing report) |
|---|---|---|---|---|
| 2026-11-08 00:14 | 1 emilejouannet | téléchargement des poids (CPU), construction des images | 0 | 0,02 $ |
| 00:16-00:28 | 1 | démarrages ratés : volume sur un chemin non vide, puis pas de nvcc pour le JIT flashinfer | ~8 min | |
| 00:32-00:41 | 1 | démarrage à froid du modèle de base (torch.compile 200 s, JIT), remplacé par free_h3_l05 | ~9 min | 1,19 $ à 00:45 |
| 00:38-00:47 | 2 martinbon39 | poids, image, démarrage à froid de free_h2 (512 s), test de 3 requêtes | ~9 min | |
| 00:41-00:49 | 1 | démarrage à froid de free_h3_l05, test de 3 requêtes | ~8 min | |
| 00:43, 00:45 | 1 | 2 jobs de test du créneau `holo-slot` (2e GPU du compte, FORCE) | ~3 min | |
| 00:49 | 1 | point de situation | | **2,08 $** (H100 1,91 $) |
| 00:49 | 2 | point de situation | | **0,80 $** (H100 0,67 $) |
| 00:55 | 1 et 2 | mesures en pause (ares) : zéro conteneur sur les deux comptes | 0 | 2,12 $ et 0,83 $ (à 00:50) |

Rythme : une H100 allumée en continu coûte ~4 $/h, soit une alerte à ~20 $ par compte environ 4 h 30 après le point de 00:49.
| 01:05-03:14 | 1 et 2 | file de déploiements (`modal_serve_when_ready.sh`) : modal-orig ×2, free_h3_l1, free_h5_l05, free_h6_s05, free_h6_s025, free_h8_flat, free_h9_a020, free_h2_l2, merge_cua_b050 (test GitHub ~1 h 30), merge_cua_b025, merge_fara_b050, merge_cua_b100, broad_residual_p100 (test GitHub), merge_cua_mid_b050, merge_cua_top_b050, merge_cua_low_b050 | à la demande | |
| 03:14 | 1 et 2 | les deux comptes en ATTENTE sur ordre d'ares (verrous `~/modal_queue/busy_acct*` maintenus), redescente à zéro | 0 | 9,52 $ et 8,05 $ (à 03:10) |
