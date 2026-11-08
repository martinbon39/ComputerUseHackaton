import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def ci(value, key='mean', digits=3):
    number=value.get(key)
    bounds=value.get('ci95')
    if number is None or bounds is None:
        return 'indéfini'
    return f'{number:.{digits}f} [{bounds[0]:.{digits}f} ; {bounds[1]:.{digits}f}]'


def main():
    r=json.loads((ROOT/'RESULT.json').read_text())
    a=r['anchoring']
    fs=a['strata']['false_finish']
    true=a['strata']['true_finish']
    best=r['best_probe']
    perm=r['permutation']
    power=r['power']
    baselines={row['name']:row for row in r['baselines']}
    receipt=json.loads((ROOT/'capture_receipt_156.json').read_text())
    lines=[
        '# Proof-anchor — ancrage et décodage sur 39 tâches faisables',
        '',
        'Original Holo-3.1-4B, révision `8c88265a5a159bfd1492db9243733dd2e6e04a6e`. Résultats du 8 novembre 2026. '
        'Rejeu HF en teacher forcing, logits seulement, sans génération ni modification des poids.',
        '',
        f'**L’ablation conjointe de la note et de la pensée change la marge « answer » de {ci(fs["deltas"]["a_minus_b"])} logits '
        f'chez les faux « fini » et de {ci(true["deltas"]["a_minus_b"])} chez les vrais.** '
        'Cela mesure une dépendance causale au texte fourni avant le nom de l’outil. '
        'Cela ne démontre ni une copie littérale de la conclusion, ni l’absence de jugement interne. '
        f'Après neutralisation b, answer reste favori parmi les outils dans '
        f'{fs["conditions"]["b"]["positive_margin_count"]+true["conditions"]["b"]["positive_margin_count"]}/39 cas : '
        'une forte atténuation de marge ne signifie pas un changement de décision dans la même proportion.',
        '',
        f'**La meilleure des 72 sondes exploratoires atteint une AUROC de {ci(best,"auroc")}.** '
        f'Son test de permutation donne p={perm["p_unadjusted"]:.4f} brut et p={perm["p_bonferroni_72"]:.4f} après correction conservatrice pour les 72 comparaisons. '
        f'Le numéro du pas brut atteint {baselines["step_raw_increasing"]["auroc"]:.3f} et la longueur du prompt '
        f'{baselines["prompt_length_raw_increasing"]["auroc"]:.3f} sur ces mêmes tâches. '
        'Ni la sélection du meilleur résultat ni les intervalles descriptifs ne permettent de conclure que l’information est absente.',
        '',
        '## Cohorte, fidélité et bornes',
        '',
        '- Manifeste astra-power : `2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0`.',
        '- 19 faux « fini » (`fs+`, score officiel 0), 20 vrais (`fs-`, score 1), une observation par tâche. '
        'Les 39 fonctions d’évaluation et leurs hashes ont été vérifiés : aucune tâche officiellement infaisable. '
        'Les 16 états sains du manifeste ne font pas partie des deux analyses demandées. '
        'Cette cohorte sélectionnée n’est pas un échantillon aléatoire des tâches OSWorld; les intervalles ne corrigent pas son biais de sélection.',
        '- Les 39 prompts sont les messages figés d’astra-power, construits par `osw_replay`. '
        'Hashes des trajectoires et des payloads, historique textuel, schémas et égalité pixel des images retenues vérifiés. '
        'Le processor HF exact est celui de la révision demandée. Les deux shards ont été hashés indépendamment : `MODEL_AUDIT.md`.',
        f'- {receipt["completed"]}/156 forwards distincts achevés, {receipt["started"]} commencés, BF16, `use_cache=False`, `logits_to_keep=1`. '
        f'Pic alloué CUDA : {receipt["max_memory_allocated"]/1e9:.2f} Go. GPU via `gpu_slot.sh`; caches sous `/workspace/astra/proof-anchor/compile_cache`.',
        '- Les longueurs totales en tokens, le prompt multimodal et la frontière avant le premier token du nom d’outil sont identiques entre conditions. '
        'Les textes effectivement utilisés, positions et hashes sont dans `PREFLIGHT.json`.',
        '- `power_032` a une note JSON `null` : celle-ci reste `null`; les conditions b/c modifient sa pensée seule. '
        'Ce cas reste inclus, et une analyse de sensibilité à 38 tâches est donnée ci-dessous.',
        '- Deux erreurs de préparation ont été conservées dans les journaux : frontière de tokenisation lors du préflight CPU, '
        'puis comparaison tuple/liste après sérialisation JSON. La première tentative GPU s’est arrêtée avant tout forward. '
        'Aucun résultat n’a été supprimé ou remplacé.',
        '',
        '## 1. Ancrage à l’échelle',
        '',
        'La marge vaut `logit(answer) − max(logit(autres outils))`. Pour un outil dont le nom contient plusieurs tokens, '
        'on compare son **premier token**, conformément au code d’ancrage réutilisé. '
        'Il ne s’agit ni d’une probabilité de terminer, ni de la vraisemblance du nom complet.',
        '',
        '| Condition | Faux fini, n=19 : marge [IC95] | Vrai fini, n=20 : marge [IC95] |',
        '|---|---:|---:|',
    ]
    names={'a':'a — réflexion, note et pensée originales','b':'b — note et pensée neutres',
           'c':'c — note et pensée contrefactuelles','d':'d — réflexion neutre, note et pensée originales'}
    for c,name in names.items():
        lines.append(f'| {name} | {ci(fs["conditions"][c])} | {ci(true["conditions"][c])} |')
    lines += ['', 'Les phrases neutres répètent « Observing the current screen. »; les contrefactuels répètent '
              '« The task is not complete yet; I still need to inspect the screen. ». '
              'Une terminaison tronquée ou une ponctuation finale ajuste exactement la longueur. '
              'La réflexion enregistrée est identique en a/b/c; seule d la neutralise.', '',
              '| Contraste apparié, positif = texte supprimé favorable à answer | Faux fini [IC95] | Vrai fini [IC95] |',
              '|---|---:|---:|']
    for key in ['a_minus_b','a_minus_c','a_minus_d']:
        lines.append(f'| {key.replace("_minus_"," − ")} | {ci(fs["deltas"][key])} | {ci(true["deltas"][key])} |')
    lines += ['', 'IC par bootstrap de tâches stratifié, 10 000 réplications, même tirage pour les conditions d’une tâche. '
              'Une tâche correspond ici à un contexte.', '',
              '| Ratio demandé | Faux fini [IC95] | Vrai fini [IC95] |','|---|---:|---:|']
    for key,title,mean_key in [('mean_of_ratios','Moyenne de (a−b)/a par tâche','mean'),
                              ('ratio_of_means','(moyenne a − moyenne b) / moyenne a','value')]:
        lines.append(f'| {title} | {ci(fs["fraction_note_and_thought"][key],mean_key)} | {ci(true["fraction_note_and_thought"][key],mean_key)} |')
    lines += ['', '**Le ratio porte sur la note et la pensée ensemble.** Il peut dépasser 1 ou être négatif; '
              'ce n’est pas une part de variance, une part de probabilité, ni une décomposition causale additive. '
              f'Dénominateurs initiaux nuls : {fs["fraction_note_and_thought"]["zero_baseline_count"]} faux et '
              f'{true["fraction_note_and_thought"]["zero_baseline_count"]} vrais. '
              f'Dénominateurs initiaux de valeur absolue <1 : {fs["fraction_note_and_thought"]["abs_baseline_below_one_count"]} et '
              f'{true["fraction_note_and_thought"]["abs_baseline_below_one_count"]}.', '']
    inter=a['interaction']
    lines += [f'Interaction entre strates : `(a−b) faux − (a−b) vrais` = '
              f'{inter["false_minus_true_delta"]:.3f} [{inter["ci95"][0]:.3f} ; {inter["ci95"][1]:.3f}] logits; '
              f'p bilatéral par 10 000 permutations de labels de tâches = {inter["p_two_sided"]:.4f}. '
              '**Ce test porte sur une différence, pas sur une équivalence.** Une interaction compatible avec zéro '
              'serait cohérente avec une influence commune de la conclusion écrite, sans prouver l’absence de discriminateur.', '',
              'Sensibilité sans la note null : a−b = '
              f'{ci(a["nonnull_note_sensitivity_a_minus_b"]["false_finish"])} chez les faux (n=19) et '
              f'{ci(a["nonnull_note_sensitivity_a_minus_b"]["true_finish"])} chez les vrais (n=19).', '',
              '| Condition | Marges answer positives, faux | Marges answer positives, vrais |','|---|---:|---:|']
    for c in 'abcd':
        lines.append(f'| {c} | {fs["conditions"][c]["positive_margin_count"]}/19 | {true["conditions"][c]["positive_margin_count"]}/20 |')
    lines += ['', 'L’ablation remplace toute la note et toute la pensée : elle ne sépare pas le rôle de la conclusion '
              'de celui des détails descriptifs qu’elles contiennent. Les contrefactuels et les répétitions sont des entrées artificielles. '
              'Leur effet conditionnel sur les logits ne mesure pas la réaction du modèle en génération libre, '
              'sa capacité à réparer une tâche, ni un gain OSWorld.', '', '## 2. Information décodable dans les résiduels', '',
              'Sorties résiduelles après les blocs de decoder **indices zéro-based** 8, 12, 16, 20, 24 et 28 '
              '(9e, 13e, 17e, 21e, 25e et 29e blocs). Positions : dernier token du prompt; '
              'dernier token de réflexion avec son délimiteur de fermeture; dernier token avant le contenu de note '
              '(avant `null` pour le cas correspondant). Aucun contenu de la note courante n’est accessible à la position début de note.', '',
              'Validation leave-one-task-out : 39 folds, label positif = faux fini. Hyperparamètres fixes : '
              'logistique L2 C=0,1; kNN cosinus k=3 ou 5, vote uniforme; MLP ReLU 64 unités, alpha L2=10, '
              'optimiseur L-BFGS, 300 itérations maximum, seed 1729. Centrage-réduction appris uniquement sur les 38 tâches d’entraînement '
              'pour logistique/MLP; kNN sur les résiduels bruts. Une SVD du seul entraînement conserve tout son sous-espace non nul '
              '(seuil numérique relatif 1e−10), sans sélection supervisée de dimensions. Les directions du test orthogonales à cet espace sont écartées. '
              'Le MLP est initialisé dans cette base. Les 72 modèles sont exploratoires.', '',
              '### Baselines sur le même découpage', '', '| Baseline | AUROC [intervalle descriptif 95 %] |','|---|---:|']
    for b in r['baselines']:
        lines.append(f'| {b["name"]} | {ci(b,"auroc")} |')
    lines += ['', '**Piège du leave-one-out :** un prédicteur constant égal à la prévalence d’entraînement '
              'donne 18/38 à chaque faux fini tenu à l’écart et 19/38 à chaque vrai, donc AUROC=0 sans aucun signal. '
              'Une sonde régularisée peut subir ce biais de calibration. Les permutations avec réajustement le reproduisent; '
              'une AUROC faible n’est pas une preuve d’absence d’information, et aucun score n’a été inversé après résultat.', '',
              '### Toutes les sondes', '', '| Couche (index) | Position | Logistique L2 | kNN3 | kNN5 | MLP64 |',
              '|---:|---|---:|---:|---:|---:|']
    for layer in r['layer_indices_zero_based']:
        for position in ['prompt_end','reflection_end','note_onset']:
            rows=[next(p for p in r['probes'] if p['layer']==layer and p['position']==position and p['model']==m)
                  for m in ['logistic_l2','knn3_cosine','knn5_cosine','mlp64_l2']]
            lines.append(f'| {layer} | {position} | '+' | '.join(ci(p,'auroc') for p in rows)+' |')
    lines += ['', 'Chaque cellule donne AUROC [intervalle descriptif 95 %]. Les intervalles rééchantillonnent les scores '
              'OOF déjà ajustés, par tâches et par classe (10 000 tirages). Ils ne refont ni l’apprentissage ni la sélection '
              'du gagnant et ne garantissent pas une couverture de 95 % pour la performance future; les folds ont des entraînements largement communs.', '',
              f'Meilleure sonde observée : `{best["key"]}`, {ci(best,"auroc")}. '
              f'Avertissements de convergence : {sum(p["convergence_warnings"] for p in r["probes"])} sur 2 808 ajustements initiaux. '
              '**Les 702 fits MLP ont atteint le plafond préspécifié de 300 itérations.** '
              'Leurs résultats sont donc limités par l’optimisation et ne peuvent pas exclure une information non linéaire.', '',
              '| Meilleure sonde moins baseline | Δ AUROC [intervalle descriptif 95 %] |','|---|---:|']
    for name,stat in best['versus_baselines'].items():
        lines.append(f'| {name} | {ci(stat,"difference")} |')
    for name,stat in r.get('best_probe_vs_raw_metadata',{}).items():
        lines.append(f'| {name} | {ci(stat,"difference")} |')
    if 'mlp_optimization_sensitivity' in r:
        sensitivity=r['mlp_optimization_sensitivity']
        winner=sensitivity['best_descriptive']
        lines += ['', '### Vérification supplémentaire de l’optimisation du MLP', '',
                  'Après observation des 702 avertissements initiaux, une passe supplémentaire a été déclarée dans '
                  '`MLP_OPTIMIZATION_AMENDMENT.md` : mêmes 18 configurations, données, seed, architecture et régularisation; '
                  'seul le plafond d’itérations passe de 300 à 3 000. Les résultats primaires restent inchangés dans '
                  '`RESULT_CORE.json`. Cette analyse supplémentaire ne réutilise pas le p du gagnant primaire.', '',
                  f'{sensitivity["n_fits"]} fits supplémentaires achevés en {sensitivity["seconds"]:.1f} s; '
                  f'{sensitivity["warning_folds"]} conservent un avertissement de convergence. '
                  'Un arrêt sans avertissement peut dépendre de la variation de l’objectif, sans garantir un petit gradient '
                  '(voir le pilote indépendant). La capacité du MLP reste imparfaitement évaluée.', '',
                  f'Maximum descriptif supplémentaire : `{winner["key"]}`, AUROC {ci(winner,"auroc")}. '
                  'Aucun test de permutation n’est réalisé pour cette famille supplémentaire; '
                  'elle ne doit pas être fusionnée aux 72 configurations initiales tout en conservant leur correction.', '',
                  '| Couche | Position | MLP à 300 itérations | MLP à 3 000 [intervalle descriptif 95 %] | Folds avec avertissement /39 |',
                  '|---:|---|---:|---:|---:|']
        for value in sensitivity['results']:
            lines.append(f'| {value["layer"]} | {value["position"]} | {value["original_auroc"]:.3f} | '
                         f'{ci(value,"auroc")} | {value["warning_folds"]} |')
    lines += ['', 'Les écarts avec les baselines utilisent les mêmes tirages bootstrap. Ils restent exploratoires et favorisés par la sélection '
              'du meilleur parmi 72. Les comparaisons à quelques métadonnées n’éliminent pas les autres facteurs de confusion : '
              'applications, instructions, contenu des écrans ou trajectoires. La cohorte contient notamment des applications '
              'présentes seulement parmi les vrais finis.', '', '### Permutations et puissance', '',
              f'1 000 permutations des labels entre tâches, 19 positifs et 20 négatifs conservés, avec réajustement des 39 folds de '
              f'la configuration gagnante. Comparaison exacte de la statistique entière `2U` pour inclure les égalités. '
              f'AUROC nulle moyenne : {perm["null_mean"]:.3f}, quantiles 2,5–97,5 % : '
              f'[{perm["null_ci95"][0]:.3f} ; {perm["null_ci95"][1]:.3f}]. '
              f'p unilatéral brut = {perm["p_unadjusted"]:.4f}; Bonferroni 72 = {perm["p_bonferroni_72"]:.4f}.', '',
              '**Avec 1 000 permutations, le plus petit p corrigé possible vaut 72/1001 = 0,07193.** '
              'Le test familial à 5 % a donc une puissance nulle quelle que soit la qualité du score. '
              'Le p brut du gagnant n’est pas confirmatoire; sa distribution permutée est celle de cette configuration, '
              'pas celle du maximum de 72 sondes.', '',
              'Pour quantifier la faiblesse de n=39 séparément de cette résolution, une simulation de scores continus '
              'binormaux indépendants utilise 19 positifs et 20 négatifs, 20 000 réplications par AUROC, '
              'écart de moyenne `sqrt(2) × Phi^-1(AUROC)`, seuil de rejet exact de Mann–Whitney. '
              'Les 380 comparaisons de paires ne sont pas traitées comme indépendantes.', '',
              '| Test théorique d’un score oracle fixé à l’avance | AUROC minimale pour 80 % de puissance |',
              '|---|---:|']
    for key,title in [('one_sided_05','Unilatéral α=0,05'),('two_sided_05','Bilatéral α=0,05'),('familywise_72','Unilatéral α=0,05/72, résolution idéale')]:
        lines.append(f'| {title} | {power["minimum_auroc_for_80_percent_power"][key]:.3f} |')
    lines += ['', f'Grille AUROC : 0,005; erreur Monte-Carlo à 80 % ≈ {power["mc_se_at_power_80"]:.4f} '
              'en probabilité. Ces seuils sont **optimistes** pour une sonde apprise sur 38 tâches : '
              'ils supposent un score oracle déjà connu. Ils ne démontrent pas que les sondes employées avaient cette sensibilité.', '',
              '## Conclusion utilisable dans le papier', '',
              '> Sur 39 contextes de tâches faisables, les substitutions de la note et de la pensée quantifient '
              'l’influence du texte précédant le choix d’outil sur la marge conditionnelle de terminaison. '
              'Les sondes linéaires et non linéaires, leurs baselines et leurs limites de puissance sont rapportées '
              'sur les mêmes tâches. Ces expériences ne permettent pas de transformer une absence de preuve '
              'de décodage en preuve d’absence d’information dans le modèle.', '',
              '## Vérification et fichiers', '',
              'Les vérifications indépendantes sont consignées dans `MODEL_AUDIT.md`, `VERIFY_REPLAY.md`, '
              '`VERIFY_CAPTURE_FINAL.md`, `VERIFY_METHODS.md` et `VERIFY_FINAL.md`. Le verdict final fait autorité sur le statut de vérification; '
              'le présent texte ne remplace pas ces contrôles.', '',
              '- Résultats complets : `RESULT.json`; scores individuels OOF : `oof_scores.npz`.',
              '- 156 mesures : `forwards.jsonl`; captures : `captures/power_*.npz`; permutations : `permutations.jsonl`.',
              '- Protocole : `PROTOCOL.md`; sources : `SOURCE_AUDIT.json`, `manifest.json`; préflight : `PREFLIGHT.json`.',
              '- Reproduction : `run_capture.py` (GPU), `analyze.py` (CPU), `render_report.py`.',
              '- Source canonique : `/workspace/astra/proof-anchor/`; copie orbit : `holo-neurochir/proof_anchor/`.',
              '', '![Ancrage et sondes exploratoires](FIGURE.png)',
              '', 'Aucun résultat de génération, de réparation ou de gain OSWorld n’est revendiqué.']
    (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    main()
