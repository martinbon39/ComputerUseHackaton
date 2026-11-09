# Tours d'idéation à contexte frais (sous-agents d'ares, Claude, sans accès aux fichiers sauf mention)

Résumés recopiés par ares depuis leurs réponses.

## Tour 1 (08/11, ~02:10-02:45 UTC)
- **Relecteur adversarial (avec accès aux fichiers)** : voir REDTEAM_0305.md.
- **Créatif avec nos résultats** : 10 idées.
  - Lancées : fusion évolutive par blocs (→ astra-evo), RegMean contrastif (→ astra-regmean).
  - Non lancées : neurone de garde greffé, masque TIES discriminant, mémoire DeltaNet « collante », greffe de tête de récupération, transplant de neurones du donneur, fusion de la tour vision, biais de récence RoPE.
- **Profane, sans contexte technique** : 8 idées par analogie (synapse inhibitrice doute → answer, verrou anti-rationalisation, neurone « assert », portefeuille de poids, neuromodulation des têtes…). Ont servi à dédoublonner les autres pistes.
- **Physicien** : la décision vue comme variable lente ; une borne d'information sur la sélectivité. Recettes :
  - R1, projection de faible rang : testée, B d'astra-broad, rang 1 suffit ;
  - R3, mémoire DeltaNet par tête : proposée à astra-free, gardée en réserve ;
  - test d'ancrage : fait par astra-broad.
- **Philosophe** : « akrasie représentationnelle », une contrainte encodée mais supprimée avant la décision. Expériences proposées : chronométrie de la décision, pont rang-1 violation → stop, désarmement du suppresseur. Envoyées à astra-ratio (clos avant exécution) et à astra-tact (chronométrie).

## Tour 2 (~03:30 UTC)
- **Créatif** : 6 directions. Lancées :
  - fusion moins la direction « done » (non exécutée, l'agent avait clos) ;
  - préambule de vérification dans la note (→ astra-preamble, rejeté) ;
  - plan apparié par branchement (→ online-eval, pilote 9/10) ;
  - vérification « sauvegarde avant de finir » (→ osw-analysis, 0/14).
- **Relecteur adversarial n°2 (avec fichiers)** : voir REDTEAM2_0335.md.

## Veille de papiers récents (08/11, ~07:15 UTC, 3 search-workers)
- Arrêt et faux succès : aucune correction par édition de poids dans la littérature. Pertinents :
  - « Who Verifies the Agent's Success Claim? » (2610.29609) : l'auto-déclaration contamine la décision, d'où moon-leak ;
  - « From Confident Closing to Silent Failure » (2606.09863) ;
  - VeriCUA (2610.26469 et 2610.40578) ;
  - Coati (2611.02644) ;
  - « Neural Procedural Memory » (2606.29824 : feature SAE « EarlyStop » sur Qwen3-4B, L17-19).
- Édition et fusion sans entraînement :
  - Selective-RL (2610.08659 : SVD top-k du delta RL), d'où une variante de moon-rl et de moon-combo ;
  - CUSD (2611.04108) ;
  - TFTV (2609.09054) ;
  - Grafting (2610.05872) ;
  - BACAM (2610.04966).
- Agents CUA récents : Mage-VL-Cowork (2610.40747, 4B, 66 % OSWorld-Verified). Ses poids sont publics (microsoft/Mage-VL-Cowork), mais l'architecture est INCOMPATIBLE avec Holo (base Qwen3 de 36 couches, vocabulaire de 151 936, contre Qwen3.5 de 32 couches hybride) : pas de fusion possible.
