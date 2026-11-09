"""REPORT.md from RESULT.json (numbers only come from RESULT.json)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.loads((HERE / 'RESULT.json').read_text())
J = R['judges']


def pct(w):
    return f"{100 * w['rate']:.0f} % ({w['numerator']}/{w['denominator']}) [{100 * w['ci95'][0]:.0f}–{100 * w['ci95'][1]:.0f}]"


def ci(c):
    return f"[{100 * c[0]:+.0f}, {100 * c[1]:+.0f}] pts"


names = list(J)
rows = [
    ('Faux succès détectés (INCOMPLETE / 66), IC Wilson', lambda s: pct(s['false_success']['incomplete_rate'])),
    ('Vrais succès rejetés à tort (INCOMPLETE / 202), IC Wilson', lambda s: pct(s['true_success']['incomplete_rate'])),
    ('Écart détection − faux rejet', lambda s: f"{100 * s['gap_detection_minus_false_rejection']:+.1f} pts"),
    ('IC 95 % de l\'écart (bootstrap par tâche, 90 tâches)',
     lambda s: ci(s['task_cluster_bootstrap']['ci95']['detection_minus_false_rejection'])),
    ('Erreurs/sorties invalides (comptées « passe »), faux / vrais',
     lambda s: f"{s['false_success']['error_or_invalid']['numerator']} / {s["true_success"]["error_or_invalid"]['numerator']}"),
    ('Part de « cannot tell » parmi les exigences listées, faux / vrais',
     lambda s: f"{100 * s['false_success']['cannot_tell_share_of_requirement_decisions']['rate']:.0f} % / "
               f"{100 * s['true_success']['cannot_tell_share_of_requirement_decisions']['rate']:.0f} %"),
    ('Épisodes avec ≥ 1 « cannot tell », faux / vrais',
     lambda s: f"{s['false_success']['episodes_with_any_cannot_tell']['numerator']}/66 / "
               f"{s['true_success']['episodes_with_any_cannot_tell']['numerator']}/202"),
]
table = ['| | ' + ' | '.join(names) + ' |', '|---|' + '---|' * len(names)]
table += [f'| {title} | ' + ' | '.join(f(J[n]) for n in names) + ' |' for title, f in rows]
paired_lines = [f"- {n} − {ref} : {100 * p['point']:+.1f} pts d'écart, IC 95 % {ci(p['ci95'])} "
                f"(mêmes tâches rééchantillonnées pour les deux juges)"
                for ref, key in [('Holo-3.1-4B', 'paired_gap_difference_vs_Holo-3.1-4B'),
                                 ('Claude', 'paired_gap_difference_vs_Claude')]
                for n, p in R.get(key, {}).items()]
(HERE / 'REPORT_TABLE.md').write_text('\n'.join(table) + '\n\n' + '\n'.join(paired_lines) + '\n')
print('\n'.join(table)); print(); print('\n'.join(paired_lines))
