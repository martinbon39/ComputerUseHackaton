import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def pct(value):
    return f'{100 * value:.1f} %'


def rate(row):
    if row['rate'] is None:
        return 'non estimable'
    lo, hi = row['ci95']
    return f"{row['numerator']}/{row['denominator']} = **{pct(row['rate'])}** [{100 * lo:.1f} ; {100 * hi:.1f}]"


def main():
    result = json.loads((ROOT / 'RESULT.json').read_text())
    if result['study_status'] != 'COMPLETE':
        raise SystemExit('Final report requires all 1072 planned responses; study is still in progress.')
    primary = result['metrics']['t0']
    f = primary['false_success']['incomplete_rate']
    t = primary['true_success']['incomplete_rate']
    stable = result['stability']['all']
    corpus = result['corpus']
    sim = result['simulation']
    lines = [
        '# Vérifier explicitement les faux succès avec Holo-3.1-4B',
        '',
        f"Statut : **{result['study_status']}**. Étude rétrospective du 8 novembre 2026, sans nouveau rollout, sans modification des poids ou du serveur partagé.",
        '',
        f"À température 0, Holo détecte **{f['numerator']} des {f['denominator']} faux succès ({pct(f['rate'])})**, mais rejette aussi **{t['numerator']} des {t['denominator']} vrais succès ({pct(t['rate'])})**. Les verdicts reposent uniquement sur la consigne et la capture finale. Ce résultat mesure une capacité de détection et son coût en faux rejets ; il ne démontre aucune réparation ni amélioration du score OSWorld.",
        '',
        '## Corpus et protocole',
        '',
        '353 dossiers ont été recensés dans les quatre sources autorisées : 352 contiennent une trajectoire, et un dossier ne contient ni trajectoire ni score. Parmi les 352 trajectoires : 268 épisodes retenus, 28 réponses sur tâches infaisables, 47 terminaisons autres que `answer`, six réponses avec score partiel, et trois trajectoires sans score officiel. Les sept scores partiels au total comprennent les six réponses exclues et une terminaison non-answer. Les 28 réponses infaisables comprennent 24 scores 0 et quatre scores 1 ; elles ne sont pas vérifiées par V1.',
        '',
        '| Passe source | Faux succès : score 0 | Vrais succès : score 1 | Réponses faisables à score partiel |',
        '|---|---:|---:|---:|',
    ]
    for name, counts in corpus['by_source'].items():
        lines.append(f"| {name} | {counts.get('false_success', 0)} | {counts.get('true_success', 0)} | {counts.get('partial_score', 0)} |")
    lines += [
        '| **Total retenu** | **66** | **202** | **6 exclues** |',
        '',
        'Définition opérationnelle demandée : dernier outil `answer` et score officiel `result.txt` égal à 0 ou 1. Un épisode par `(tâche, passe)` ; aucun doublon dans ces clés. Les 268 épisodes couvrent **90 tâches distinctes** : 34 tâches contribuent aux faux succès et 74 aux vrais succès, avec 18 tâches présentes dans les deux catégories selon la passe. Les sources sont `results_diag`, `results_diag2`, `results_diag_extra_gh/pass1` et `pass2` ; les deux dernières sont des passes distinctes, et non des copies des premières. Les fichiers sources restent intacts.',
        '',
        'L’instruction et la faisabilité proviennent des JSON OSWorld. Toute fonction d’évaluation contenant `infeasible` entraîne l’exclusion. Pour chacun des 268 épisodes, la capture référencée par la dernière ligne `answer` existe et constitue aussi la dernière capture disponible. Le code du runner confirme que cette image est l’observation après la dernière action graphique ; `answer` ne modifie pas l’écran. Aucun repli vers une autre image n’a été nécessaire. Instructions, chemins et SHA256 sont conservés dans `manifest.json`.',
        '',
        'V1 est l’original `Hcompany/Holo-3.1-4B`, snapshot `8c88265a5a159bfd1492db9243733dd2e6e04a6e`, servi sur le port 8000 du pod. Une image PNG originale et un message utilisateur, sans schéma JSON d’agent, sans outils, sans historique, sans score ni réponse précédente. Réflexion activée par `enable_thinking=true`, `top_p=1`, `top_k=-1`, limite de sortie 4096 tokens. Un tirage T=0 et trois tirages T=0,8 avec graines distinctes enregistrées. Maximum quatre requêtes simultanées. Le prompt reste exactement :',
        '',
        '> Task: <instruction>. Here is the final screen. List every requirement of the task, then for each say whether the screen shows it is satisfied (yes / no / cannot tell). Finally answer VERDICT: COMPLETE or INCOMPLETE.',
        '',
        f"**V2 non exécuté** : l’inventaire local ne trouve que Holo-3.1-0.8B, Holo-3.1-4B et des variantes de poids du 4B. Aucun VLM indépendant plus fort n’est disponible dans les caches inspectés. Aucun modèle téléchargé, aucun autre serveur sollicité ou modifié. Voir `infrastructure_probe.json`.",
        '',
        '## Résultats : IC à 95 % de Wilson',
        '',
        '| Vérification | Détection : INCOMPLETE sur faux succès | Faux rejet : INCOMPLETE sur vrais succès |',
        '|---|---:|---:|',
    ]
    for rep, label in [('t0', 'T=0, principal'), ('t08_r1', 'T=0,8 — tirage 1'), ('t08_r2', 'T=0,8 — tirage 2'), ('t08_r3', 'T=0,8 — tirage 3')]:
        metrics = result['metrics'][rep]
        lines.append(f"| {label} | {rate(metrics['false_success']['incomplete_rate'])} | {rate(metrics['true_success']['incomplete_rate'])} |")
    majority = result['stability']['majority_metrics']
    lines.append(f"| Majorité des trois tirages T=0,8 | {rate(majority['false_success']['incomplete_rate'])} | {rate(majority['true_success']['incomplete_rate'])} |")
    lines += [
        '',
        f"Répartition T=0 : faux succès `{primary['false_success']['verdict_counts']}` ; vrais succès `{primary['true_success']['verdict_counts']}`. Les dénominateurs principaux restent 66 et 202. Les sorties tronquées, absentes, conflictuelles ou mal formées sont distinguées et ne deviennent pas artificiellement COMPLETE. La mise en forme Markdown et les guillemets d’un champ JSON VERDICT sont normalisés de la même façon pour tous les tirages ; un verdict cité reste admissible même si le reste du JSON est mal formé, à condition que sa valeur soit unique et la génération terminée normalement. La règle de blocage simulée ne se déclenche que sur un INCOMPLETE valide. Les taux sur verdicts valides seuls figurent aussi dans `RESULT.json`.",
        '',
        f"Sur les verdicts valides seuls à T=0 : détection {rate(primary['false_success']['valid_only_incomplete_rate'])} ; faux rejet {rate(primary['true_success']['valid_only_incomplete_rate'])}.",
        '',
        'Les IC de Wilson sont calculés par épisode et ne corrigent pas les répétitions d’une même tâche. En sensibilité, un bootstrap par tâche (10 000 tirages, graine 20261108, toutes les passes d’une tâche rééchantillonnées ensemble) donne :',
        '',
    ]
    cluster = result['primary_task_cluster_bootstrap']['ci95']
    for key, label in [('false_success', 'Détection'), ('true_success', 'Faux rejet'), ('detection_minus_false_rejection', 'Détection moins faux rejet')]:
        lo, hi = cluster[key]
        unit = 'points de pourcentage' if key == 'detection_minus_false_rejection' else '%'
        lines.append(f'- {label} : IC 95 % [{100 * lo:.1f} ; {100 * hi:.1f}] {unit}.')
    sensitivity = result['sensitivity_excluding_metadata_declared_infeasible']['metrics_t0']['false_success']['incomplete_rate']
    lines += [
        '',
        f"Deux des 66 échecs faisables sont des réponses où l’agent déclarait lui-même la tâche impossible, à cause d’un refus d’accès du site Delta. Ils restent inclus conformément à la définition demandée (`answer` + score 0). Les exclure donne une détection de {rate(sensitivity)} ; ce contrôle secondaire ne modifie pas le corpus principal.",
        '',
        'Décomposition descriptive T=0 par domaine ; les petites cellules ne permettent pas une comparaison fiable entre applications :',
        '',
        '| Domaine | Faux succès détectés | Vrais succès rejetés |',
        '|---|---:|---:|',
    ]
    for domain, metrics in result['by_domain_t0'].items():
        a = metrics['false_success']['incomplete_rate']
        b = metrics['true_success']['incomplete_rate']
        a_text = f"{a['numerator']}/{a['denominator']}" if a['denominator'] else '—'
        b_text = f"{b['numerator']}/{b['denominator']}" if b['denominator'] else '—'
        lines.append(f"| {domain} | {a_text} | {b_text} |")
    lines += [
        '',
        '## Stabilité des trois tirages à T=0,8',
        '',
        f"{stable['all_three_valid']}/{stable['episodes']} épisodes ont trois verdicts valides. Parmi eux, unanimité : {rate(stable['unanimous'])}. Désaccord entre deux tirages valides : {stable['pair_disagreement_count']}/{stable['pair_comparisons']} paires ; les paires d’un même épisode ne sont pas indépendantes. Accord entre la majorité T=0,8 et T=0 : {rate(stable['majority_agreement_t0'])}.",
        '',
        '| Politique sur les trois tirages | Faux succès bloqués | Vrais succès bloqués |',
        '|---|---:|---:|',
        f"| Au moins un INCOMPLETE | {rate(result['stability']['false_success']['at_least_one_sample_incomplete'])} | {rate(result['stability']['true_success']['at_least_one_sample_incomplete'])} |",
        f"| Trois INCOMPLETE | {rate(result['stability']['false_success']['all_three_incomplete'])} | {rate(result['stability']['true_success']['all_three_incomplete'])} |",
        '',
        'Ces politiques sont des résumés descriptifs des mêmes tirages ; aucun seuil n’a été choisi ou réévalué sur de nouveaux épisodes.',
        '',
        '## Décisions déclarées par exigence',
        '',
        'Comptage conservateur des décisions explicitement produites dans la réponse finale T=0, avant le verdict. Un lecteur indépendant a contrôlé le texte et corrigé 27 extractions : étiquettes après une flèche, cases cochées dans un bloc d’évaluation (✓ = yes), tableaux JSON alignés avec les exigences, plusieurs exigences sur une même ligne et répétitions. Les négations dans une exigence, comme « no variations », et les justifications libres sans note catégorielle sont exclues. Les exigences énumérées par le modèle ne constituent pas une annotation indépendante des exigences réelles.',
        '',
        '| Population | yes | no | cannot tell | Épisodes avec ≥1 no | Épisodes sans décision catégorielle extraite |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for key, label in [('false_success', 'Faux succès'), ('true_success', 'Vrais succès'), ('all', 'Total')]:
        row = result['requirements_t0'][key]
        counts = row['explicit_decisions']
        lines.append(f"| {label} | {counts.get('yes', 0)} | {counts.get('no', 0)} | {counts.get('cannot tell', 0)} | {row['episodes_with_no']} | {row['episodes_with_no_parsed_decision']} |")
    lines += [
        '',
        'Il s’agit de détections déclarées, pas d’un rappel ou d’une précision par exigence : le modèle peut omettre, inventer ou relâcher une exigence. Les 714 décisions retenues comprennent également celles lisibles dans les sorties sans verdict valide ; cela ne réhabilite pas leur verdict global. Les lignes exactes sont conservées dans `parsed_responses.json`, et chaque correction, son texte source et l’empreinte du sous-ensemble T=0 figurent dans `audit/requirement_review.json`. Le décompte automatique avant revue (438 yes, 86 no, 120 cannot tell) est aussi conservé pour transparence.',
        '',
        '## Erreurs inspectées',
        '',
        'Exemples qualitatifs choisis pour montrer des mécanismes distincts, sans prétention de fréquence. Captures finales inspectées manuellement ; la vérité de référence reste le score officiel.',
        '',
    ]
    for case in json.loads((ROOT / 'error_cases.json').read_text()):
        lines.append(f"- **{case['kind']}** — `{case['episode_id']}` : score {case['official_score']}, verdict {case['verifier_verdict']}. {case['assessment']}")
    lines += [
        '',
        '## Simulation de blocage de answer',
        '',
        f"Population simulée : les **{sim['n']} épisodes sélectionnés**, avec {sim['baseline_successes']} succès initiaux ({pct(sim['baseline_success_rate'])}). Ce n’est pas le score global d’OSWorld. Le filtre T=0 bloquerait {sim['false_successes_blocked']} faux succès et {sim['true_successes_blocked']} vrais succès. Parmi les blocages, proportion de faux succès : {rate(sim['precision_of_block'])}.",
        '',
        'Un blocage ne répare rien par lui-même. La borne sans réparation est **0 gain brut** si les vrais succès sont préservés ; une perte est possible si le blocage dégrade ou empêche de valider ceux-ci. Pour un taux de réparation hypothétique r, le gain attendu sur ce corpus vaut `(r × faux succès bloqués − vrais succès perdus) / 268`.',
        '',
        '| Hypothèse de réparation | Réparations attendues, non observées | Gain si tous les vrais succès sont préservés | Gain si tous les vrais succès bloqués sont perdus |',
        '|---|---:|---:|---:|',
    ]
    for key, label in [('no_repair', 'r=0 : blocage seul'), ('feasible_valid_branch_observed', 'r=0/2 : branchement faisable et fidèle'), ('all_valid_branch_naive_transfer', 'r=1/4 : extrapolation naïve du pilote mixte')]:
        row = sim['scenarios'][key]
        lines.append(f"| {label} | {row['expected_repairs_not_observed']:.2f} | {row['gain_pp_if_true_successes_preserved']:+.2f} pp | {row['gain_pp_if_all_false_rejects_lost']:+.2f} pp |")
    reference = sim['reference_all_scored_feasible_episodes']
    reference_optimistic = sim['scenarios']['all_valid_branch_naive_transfer']
    lines += [
        '',
        f"Sensibilité au dénominateur : les quatre sources contiennent **{reference['n']} épisodes faisables avec score officiel**, y compris les scores partiels et les terminaisons non-answer. Leur score moyen descriptif est {pct(reference['official_score_mean'])}. En gardant inchangés tous les épisodes hors des 268 vérifiés, la borne à r=0 reste 0 gain brut, et le scénario favorable r=25 % devient **+{reference_optimistic['reference_315_gain_pp_if_preserved']:.2f} pp** ; si tous les vrais succès bloqués sont perdus, il donne {reference_optimistic['reference_315_gain_pp_if_false_rejects_lost']:+.2f} pp. Ces passes diagnostiques incomplètes et répétées ne sont toujours pas le benchmark complet.",
        '',
        '**Pourquoi le scénario à 25 % ne valide pas un gain :** `~/osw/branch_pilot/REPORT.md` rapporte 5/10 succès pour l’original et 4/10 pour le candidat, mais cela inclut quatre continuations de succès déjà acquis par bras. Parmi les échecs enregistrés : original 1/6, candidat 0/6 ; après le filtre de fidélité du replay : 1/4 et 0/4. L’unique réparation concerne GIMP `fbb548ca…`, une tâche officiellement infaisable. En appliquant notre exclusion des tâches infaisables, il ne reste qu’une tâche Writer faisable et fidèle, avec **0/2 réparations par bras**. Le Chrome dynamique est exclu pour divergence du replay. Les continuations K=2 d’une même tâche ne sont pas indépendantes.',
        '',
        f"À titre descriptif seulement, Wilson : {rate(sim['scenarios']['all_valid_branch_naive_transfer']['branch_wilson'])} ; {rate(sim['scenarios']['feasible_valid_branch_observed']['branch_wilson'])}. Ces larges intervalles et la différence de population interdisent de traiter le taux du petit pilote comme une probabilité de réparation validée pour cette étude. La borne positive simulée est conditionnelle au transfert du taux et à l’absence de dommage sur les vrais succès ; aucune continuation n’a été exécutée ici.",
        '',
        '## Portée du résultat',
        '',
        'Cette expérience teste une vérification explicite par le **même modèle**, depuis un écran final. Elle ne compare pas une chirurgie des poids à un vérificateur indépendant plus fort. Elle ne suffit donc pas à affirmer que « le faux succès se corrige par un vérificateur externe ». Elle chiffre le compromis de ce V1 et identifie deux limites : des preuves visuelles parfois mal lues, et des exigences portant sur un état persistant ou passé que la capture finale ne permet pas de vérifier. Un contrôle fiable de chaque exigence pourrait nécessiter l’accès aux fichiers, aux réglages ou à une preuve d’exécution ; cet accès supplémentaire n’est pas évalué ici.',
        '',
        'Les tâches proviennent d’épisodes diagnostiques déjà enregistrés, avec répétitions par tâche et sélection des terminaisons answer à score binaire. Les taux ne sont pas des estimations représentatives du benchmark complet. Aucune donnée de test supplémentaire, aucun nouveau rollout, aucune clé secrète affichée.',
        '',
        '## Reproduction, coût et audit',
        '',
        f"{result['response_count']}/{result['planned_response_count']} réponses conservées ; statuts HTTP/transport `{result['response_statuses']}` ; verdicts parsés `{result['parsed_verdict_counts']}`. Réflexion non vide : {result['nonempty_reasoning_count']}/{result['response_count']}. Début : {result['runtime']['first_request_at']} ; dernière réponse : {result['runtime']['last_response_at']}. Tokens générés : {result['runtime']['completion_tokens']:,}. Quatre minuscules sondes textuelles d’infrastructure, séparées du corpus, ont précédé l’étude. Aucun nouveau serveur n’a été lancé.",
        '',
        '- `PROTOCOL.md` : protocole fixé avant les inférences ; `manifest.json`, `inventory.json` et `corpus_probe.json` : population et provenance.',
        '- `responses.jsonl` et `attempts.jsonl` : réponses intégrales, paramètres, graines, hashes de requêtes, raisonnement et raisons d’arrêt.',
        '- `analyze.py` : recalcul CPU ; `parsed_responses.json` et `stability_by_episode.json` : résultats élémentaires.',
        '- `RESULT.json` : chiffres non arrondis, IC, domaines, passes, sensibilité par tâche et simulation.',
        '- `error_cases.json`, `images/`, `tasks/` : cas qualitatifs et pièces permettant de les contrôler.',
        '- `branch_source_REPORT.md` et `branch_source_provenance.json` : source exacte du scénario de branchement.',
        '',
        'Recalcul local : `python3 analyze.py && python3 write_report.py`. Audit indépendant : `python3 audit/audit_verif.py` ; voir `audit/FINAL_AUDIT.md` et `audit/AUDIT_RESULT.json` pour les vérifications réellement exécutées et leurs limites.',
        '',
        'Livraison : `/workspace/astra/verif-study/` sur le pod et `experiments/verif_study/` sur orbit. Les SHA256 des données utilisées sont enregistrés dans `RESULT.json` et dans l’audit indépendant.',
    ]
    (ROOT / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    print(ROOT / 'REPORT.md')


if __name__ == '__main__':
    main()
