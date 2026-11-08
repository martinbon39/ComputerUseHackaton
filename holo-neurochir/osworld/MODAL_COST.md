# Coûts Modal (budget dur : ≤ 25 $ par compte)

Prix H100 Modal : ~3,95 $/h (0,001097 $/s), plus le CPU et la mémoire du conteneur (~0,1 $/h). Seule fait foi la commande
`MODAL_PROFILE=<profil> modal billing report --for today --show-resources`, dont les données arrivent avec quelques minutes de retard.

| Heure UTC | Compte | Usage | GPU allumé (estimé) | Coût cumulé du compte (billing report) |
|---|---|---|---|---|
| 2026-11-08 00:14 | 1 emilejouannet | téléchargement des poids (CPU), construction des images | 0 | 0,02 $ |
| 00:16-00:28 | 1 | démarrages ratés : volume sur un chemin non vide, puis pas de nvcc pour le JIT flashinfer | ~8 min | |
| 00:32-00:41 | 1 | démarrage à froid du modèle de base (torch.compile 200 s, JIT), remplacé par free_h3_l05 | ~9 min | 1,19 $ à 00:45 |
| 00:38- | 2 martinbon39 | téléchargement des poids, démarrage à froid de free_h2 | en cours | 0,17 $ à 00:45 |
| 00:41- | 1 | démarrage à froid de free_h3_l05 | en cours | |
