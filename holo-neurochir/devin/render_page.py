"""Render STATUS.json as the self-contained page "Devin dans le labo" (reloads itself every 60 s)."""
from __future__ import annotations

import html
import json

STATE_FR = {"not_launched": "non lancée", "running": "en cours", "needs_input": "attend une réponse",
            "finished": "terminée", "failed": "échec", "suspended": "en veille"}
DELIVERABLE = {"M1": "rapport PASS/FAIL du kit jury", "M2": "PR sur notre fork d'OSWorld + CI", "M3": "plan chiffré 100 VMs", "M4": "contrôleur GPU gpu_ctl.py + tests"}

CSS = """
:root{--bg:#f7f7f5;--fg:#16181d;--mute:#5d6470;--line:#dcdde0;--card:#fff;--ok:#1d7a46;--warn:#9a6700;--bad:#b42318;--run:#2457c5}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#111317;--fg:#e8e9ec;--mute:#9aa1ad;--line:#2a2e36;--card:#181b21;--ok:#4cc38a;--warn:#e3b341;--bad:#f97066;--run:#7aa2ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 16px 48px}h1{font-size:24px;margin:0 0 4px}.sub{color:var(--mute);margin:0 0 24px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;min-width:0}
.card h2{font-size:15px;margin:0 0 8px}.pill{display:inline-block;border-radius:99px;padding:1px 10px;font-size:13px;border:1px solid currentColor}
.running{color:var(--run)}.finished{color:var(--ok)}.failed{color:var(--bad)}.needs_input,.suspended{color:var(--warn)}.not_launched{color:var(--mute)}
dl{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:12px 0 0;font-size:13.5px}dt{color:var(--mute)}dd{margin:0;overflow-wrap:anywhere}
a{color:var(--run)}code{font-size:12.5px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:8px;max-height:260px;overflow:auto}
.checks{margin:10px 0 0;padding:0;list-style:none;font-size:13.5px}.checks li{margin:2px 0}
footer{color:var(--mute);font-size:12.5px;margin-top:24px}
"""


def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def link(url, text=None) -> str:
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(text or url)}</a>' if url else "—"


def card(s: dict) -> str:
    st = s.get("state") or "not_launched"
    so = s.get("structured_output") or {}
    rows = [("Session", link(s.get("url"), s.get("session_id")) if s.get("session_id") else "—"),
            ("Livrable", esc(DELIVERABLE.get(s["mission"], ""))),
            ("Statut API", esc(" / ".join(x for x in (s.get("status"), s.get("status_detail")) if x)) or "—"),
            ("ACU", f"{esc(s.get('acus_consumed') if s.get('acus_consumed') is not None else '—')} / plafond {esc(s.get('max_acu'))}"),
            ("Entrée", f"<code>{esc(s['bundle']['name'])}</code> sha256 <code>{esc(s['bundle']['sha256'][:12])}…</code>")]
    prs = s.get("pull_requests") or ([so["pr_url"]] if so.get("pr_url") else [])
    if prs:
        rows.append(("PR", "<br>".join(link(u) for u in prs)))
    for a in s.get("attachments") or []:
        rows.append(("Fichier", link(a.get("url"), a.get("name"))))
    checks = ""
    if so.get("checks"):
        checks = '<ul class="checks">' + "".join(
            f'<li><b class="{ "finished" if c.get("status") == "PASS" else "failed" if c.get("status") == "FAIL" else "suspended"}">'
            f'{esc(c.get("status"))}</b> {esc(c.get("id"))} · {esc(c.get("summary"))}</li>' for c in so["checks"]) + "</ul>"
    verdict = so.get("overall") or (so.get("ci") or {}).get("status")
    head = f' · résultat <b>{esc(verdict)}</b>' if verdict else ""
    raw = f"<details><summary>Sortie structurée</summary><pre>{esc(json.dumps(so, indent=1, ensure_ascii=False))}</pre></details>" if so else ""
    return (f'<section class="card"><h2>{esc(s["title"])}</h2><span class="pill {st}">{esc(STATE_FR.get(st, st))}</span>{head}'
            f'<dl>{"".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)}</dl>{checks}{raw}</section>')


def render(status: dict) -> str:
    mode = "Aucune session Devin n'a été lancée pendant le hackathon, pour préserver les crédits (0 ACU)" if status.get("mode") == "dry_run" else f"API Devin {esc(status.get('api_version'))}"
    ac = status.get("auth_check") or {}
    auth = (f" et authentifié (appel en lecture seule, API {esc(ac.get('api_version'))}, {esc(ac.get('at'))} UTC, aucune session créée)"
            if ac.get("authenticated") else ", pas encore authentifié")
    events = "".join(f"<li>{esc(e['at'])} · {esc(e['mission'])} → {esc(STATE_FR.get(e['state'], e['state']))}</li>"
                     for e in status.get("events", [])[-12:])
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="60"><title>Devin dans le labo</title><style>{CSS}</style></head><body><main>
<h1>Devin dans le labo</h1>
<p class="sub">Intégration de l'API Devin (Cognition) : le client est installé{auth}. La mission ci-dessous est écrite et testée à blanc. {mode}. Commit d'entrée <code>{esc((status.get('commit') or '')[:12])}</code>.</p>
<div class="grid">{''.join(card(s) for s in status.get('sessions', []))}</div>
{f'<h2 style="font-size:15px;margin-top:24px">Événements</h2><ul class="checks">{events}</ul>' if events else ''}
<footer>Mis à jour {esc(status.get('updated_at'))} UTC · la page se recharge toute seule chaque minute · source : holo-neurochir/devin/STATUS.json</footer>
</main></body></html>"""
