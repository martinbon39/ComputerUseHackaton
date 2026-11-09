#!/usr/bin/env python3
"""Level 2: run Feci Guard for real (a fresh Claude call) on one recorded OSWorld final screen, and compare the live
verdict with the one recorded on 2026-11-08. Uses the frozen `feci_guard.check`, unchanged.

Two backends, pick one:
  * Claude Code CLI (`claude` logged in):      python reproduce/guard_live.py
  * Anthropic API key (needs `pip install openai`, Anthropic's OpenAI-compatible endpoint):
        ANTHROPIC_API_KEY=... python reproduce/guard_live.py --api
Options: --episode <episode_id> (default: a false success the recorded verdict rejected), --list, --model.
About $0.03 and 5-15 s per call. A live verdict can differ from the recorded one: the model is sampled.
"""
import argparse, json, os, pathlib, shutil, sys
sys.dont_write_bytecode = True  # keep a judge's clone clean

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default=None)
    ap.add_argument("--list", action="store_true", help="list episode ids with their label and recorded verdict")
    ap.add_argument("--api", action="store_true", help="use ANTHROPIC_API_KEY instead of the claude CLI")
    ap.add_argument("--model", default=None, help="CLI default: sonnet; API default: claude-sonnet-5-5")
    a = ap.parse_args()

    manifest = {e["episode_id"]: e for e in json.loads((ROOT / "experiments" / "verif_study" / "manifest.json").read_text())}
    recorded = {}
    for line in (ROOT / "experiments" / "judge_bench" / "claude_responses.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            recorded[r["episode_id"]] = r["result"]
    if a.list:
        for k, e in manifest.items():
            print(f"{k}  {e['label']:<13}  recorded={recorded[k].get('verdict')}")
        return 0
    ep = a.episode or next(k for k, e in manifest.items() if e["label"] == "false_success"
                           and recorded[k].get("verdict") == "INCOMPLETE")
    if ep not in manifest:
        sys.exit(f"unknown episode {ep!r}: run with --list to see the 268 ids")
    e = manifest[ep]

    if a.api:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY is not set")
        os.environ.update(GUARD_BACKEND="openai", GUARD_BASE_URL="https://api.anthropic.com/v1/",
                          GUARD_API_KEY_ENV="ANTHROPIC_API_KEY")
        os.environ.setdefault("GUARD_MODEL", a.model or "claude-sonnet-5-5")
    else:
        cli = os.environ.get("FECI_CLAUDE") or shutil.which("claude")
        if not cli:
            sys.exit("claude CLI not found: install Claude Code, or use --api with ANTHROPIC_API_KEY")
        os.environ.update(GUARD_BACKEND="claude", FECI_CLAUDE=cli)
        if a.model:
            os.environ["GUARD_MODEL"] = a.model
    sys.path.insert(0, str(ROOT / "src" / "feci_guard"))
    import feci_guard  # imported after the env is set: verifier reads FECI_CLAUDE / GUARD_MODEL at import

    png = (ROOT / "experiments" / "verif_study" / "images" / pathlib.Path(e["image_path"]).name).read_bytes()
    print(f"episode  : {ep}\nlabel    : {e['label']} (official OSWorld evaluator)\nTASK     : {e['instruction']}")
    out = feci_guard.check(e["instruction"], png)
    d = out["detail"]
    print(f"live     : {out['verdict'].upper()} ({out['kind']})  [{d.get('backend')}:{d.get('model')}, "
          f"{d.get('latency_s')} s, error={d.get('error')}]")
    for q in out["requirements"]:
        print(f"  [{ {'yes': 'v', 'no': 'x'}.get(q['status'], '?') }] {q['text']}: {q['evidence']}")
    if out["feedback"]:
        print(f"feedback : {out['feedback']}")
    rec = recorded[ep].get("verdict")
    print(f"recorded : {rec} -> {'reject' if rec == 'INCOMPLETE' else 'accept'}   "
          f"same decision: {(rec == 'INCOMPLETE') == (out['verdict'] == 'reject')}")
    return 0 if d.get("error") is None else 2


if __name__ == "__main__":
    sys.exit(main())
