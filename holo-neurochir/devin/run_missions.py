#!/usr/bin/env python3
"""Launch the lab's Devin missions in parallel, follow them, write STATUS.json and the live page.

    python run_missions.py --dry-run                         # build inputs, print requests, no key, no network
    python run_missions.py --missions M1                      # live: needs ~/.devin_key or DEVIN_API_KEY
    python run_missions.py --missions M1,M2 --fork-repo martinbon39/OSWorld
    python run_missions.py --follow                           # resume following the sessions in STATUS.json

Inputs go to Devin as attachments built from git (origin/main, never the shared working tree), each with its sha256
written into the prompt so Devin can check integrity. M2 needs --fork-repo (our fork of xlang-ai/OSWorld) that Devin
can push to: Devin's GitHub integration on that repo, or a fine-grained token for that repo only in ~/.devin_gh_token,
passed as a sensitive session secret GH_TOKEN (never written anywhere by this script).
Every follow tick rewrites STATUS.json and republishes the page with `argos artifact` (page reloads itself).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import pathlib
import re
import subprocess
import sys
import tarfile
import time

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parent
REPO = LAB.parent
BUILD = HERE / "build"
STATUS = HERE / "STATUS.json"
PAGE = BUILD / "devin-lab.html"
GH_TOKEN_FILE = pathlib.Path.home() / ".devin_gh_token"
sys.path.insert(0, str(HERE))
from devin_client import FINAL, Devin, DevinError, load_key  # noqa: E402
import render_page  # noqa: E402

MISSIONS = {
    "M1": {"file": "M1_reproduction.md", "title": "M1 · independent reproduction of the jury kit", "max_acu": 10},
    "M2": {"file": "M2_feci_guard_pr.md", "title": "M2 · Feci Guard as a Surfer-H option (PR on our fork)", "max_acu": 20},
    "M3": {"file": "M3_scale_audit.md", "title": "M3 · infrastructure audit, 100-VM OSWorld plan", "max_acu": 6},
    "M4": {"file": "M4_gpu_ctl.md", "title": "M4 · GPU infrastructure controller (gpu_ctl.py)", "max_acu": 6},
}
N_EPISODES_PER_LABEL = 12
SECRET_PATTERNS = [r"\?t=[A-Za-z0-9._-]{20,}", r"\b(hk|sk|cog|apk|apk_user|hf|ghp|gho|github_pat)[-_][A-Za-z0-9_]{16,}",
                   r"\bAKIA[0-9A-Z]{16}\b", r"(?i)(api[_-]?key|token|secret)\s*[=:]\s*['\"][^'\"\s]{12,}['\"]"]


def git(*args: str, binary: bool = False):
    out = subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True)
    return out.stdout if binary else out.stdout.decode().strip()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def redact(text: str) -> tuple[str, int]:
    n = 0
    for p in SECRET_PATTERNS:
        text, k = re.subn(p, "<redacted>", text)
        n += k
    return text, n


def tar_bytes(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz, tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as t:
        for name in sorted(files):
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(files[name]), 0, 0o644
            t.addfile(info, io.BytesIO(files[name]))
    return buf.getvalue()


def at(commit: str, path: str) -> bytes:
    return git("show", f"{commit}:{path}", binary=True)


def bundle_m1(commit: str) -> dict:
    data = git("archive", "--format=tar.gz", commit, "jury_kit", binary=True)
    return {"name": f"jury_kit-{commit[:12]}.tar.gz", "bytes": data,
            "fields": {"JURY_TREE": git("rev-parse", f"{commit}:jury_kit")}}


def bundle_m2(commit: str) -> dict:
    files = {f"feci_guard/{f}": at(commit, f"holo-neurochir/feci_guard/{f}") for f in
             ("feci_guard.py", "verifier.py", "run_holo_guard.py", "README.md", "PREREG.md")}
    src = BUILD / "m2_src"
    src.mkdir(parents=True, exist_ok=True)
    for f in ("feci_guard.py", "verifier.py"):
        (src / f).write_bytes(files[f"feci_guard/{f}"])
    sys.path.insert(0, str(src))
    manifest = {e["episode_id"]: e for e in json.loads(at(commit, "holo-neurochir/verif_study/manifest.json"))}
    labels = {e["episode_id"]: e["label"] for e in
              json.loads(at(commit, "holo-neurochir/judge_bench/per_episode.json"))["Claude (Feci Guard verifier)"]}
    rec = {r["episode_id"]: r["result"] for r in map(json.loads, at(
        commit, "holo-neurochir/judge_bench/claude_responses.jsonl").decode().splitlines()) if r}
    picked = []
    for lab in ("false_success", "true_success"):
        picked += sorted(e for e, l in labels.items() if l == lab and e in rec and e in manifest)[:N_EPISODES_PER_LABEL]
    eps = []
    for e in picked:
        m = manifest[e]
        task = json.loads(at(commit, f"holo-neurochir/verif_study/tasks/{m['domain']}__{m['task_id']}.json"))
        eps.append({"episode_id": e, "domain": m["domain"], "task_id": m["task_id"],
                    "instruction": task["instruction"], "label": labels[e]})
        files[f"episodes/images/{e}.png"] = at(commit, f"holo-neurochir/verif_study/images/{e}.png")
    files["episodes/episodes.json"] = json.dumps(eps, indent=1).encode()
    files["episodes/recorded_verdicts.jsonl"] = "".join(
        json.dumps({"episode_id": e, "result": rec[e]}) + "\n" for e in picked).encode()
    files["episodes/expected_metrics.json"] = json.dumps(expected_metrics(eps, rec), indent=1).encode()
    data = tar_bytes(files)
    return {"name": f"feci_guard-{commit[:12]}.tar.gz", "bytes": data, "fields": {"N_EPISODES": str(len(eps))}}


def expected_metrics(eps: list[dict], rec: dict) -> dict:
    """Run the recorded verifier outputs through the real feci_guard.check rule (verifier.verify stubbed)."""
    import feci_guard
    import verifier
    real = verifier.verify
    out = {"false_success": [0, 0], "true_success": [0, 0]}
    try:
        for e in eps:
            verifier.verify = lambda *a, _r=rec[e["episode_id"]], **k: dict(_r)
            r = feci_guard.check(e["instruction"], b"png")
            out[e["label"]][0] += r["verdict"] == "reject"
            out[e["label"]][1] += 1
    finally:
        verifier.verify = real
    (d, nd), (f, nf) = out["false_success"], out["true_success"]
    return {"rule": "feci_guard.check on recorded verifier outputs (verifier.verify stubbed)",
            "false_success": {"rejected": d, "n": nd}, "true_success": {"rejected": f, "n": nf},
            "detection_rate": round(d / nd, 4), "false_rejection_rate": round(f / nf, 4)}


def bundle_m3(commit: str) -> dict:
    paths = ["holo-neurochir/JOURNAL.md"] + [p for p in git("ls-tree", "-r", "--name-only", commit,
                                                              "holo-neurochir/osworld", "holo-neurochir/scripts").split()
                                             if re.search(r"\.(md|sh|py|json|txt)$", p) and "__pycache__" not in p]
    files, hits = {}, 0
    for p in paths:
        text, n = redact(at(commit, p).decode(errors="replace"))
        files[p.removeprefix("holo-neurochir/")] = text.encode()
        hits += n
    return {"name": f"infra-{commit[:12]}.tar.gz", "bytes": tar_bytes(files), "fields": {"REDACTIONS": str(hits)}}


def bundle_m4(commit: str) -> dict:
    """The Modal apps, deploy manifests and docs at the commit, plus real Modal CLI outputs captured on orbit
    (missions/m4_fixtures/), every file passed through redact()."""
    osw = "holo-neurochir/osworld/"
    paths = [osw + f for f in ("modal_vllm.py", "modal_judge.py", "modal_deploy.sh", "modal_budget_guard.sh",
                               "MODAL_COST.md", "MODAL.md", "MODAL_MANIFEST.md")]
    paths += [p for p in git("ls-tree", "-r", "--name-only", commit, osw + "modal_deploys").split() if p.endswith(".json")]
    files, hits = {}, 0
    for p in paths:
        text, n = redact(at(commit, p).decode())
        files["osworld/" + p.removeprefix(osw)] = text.encode()
        hits += n
    for f in sorted((HERE / "missions" / "m4_fixtures").iterdir()):
        text, n = redact(f.read_text())
        files[f"fixtures/{f.name}"] = text.encode()
        hits += n
    return {"name": f"gpu_ctl_inputs-{commit[:12]}.tar.gz", "bytes": tar_bytes(files), "fields": {"REDACTIONS": str(hits)}}


BUNDLES = {"M1": bundle_m1, "M2": bundle_m2, "M3": bundle_m3, "M4": bundle_m4}


def example_to_schema(x):
    """JSON Schema (draft 7) from the example object in the mission prompt, the single source of the report shape."""
    if isinstance(x, dict):
        return {"type": "object", "properties": {k: example_to_schema(v) for k, v in x.items()}, "required": list(x)}
    if isinstance(x, list):
        return {"type": "array", "items": example_to_schema(x[0]) if x else {}}
    if isinstance(x, bool):
        return {"type": "boolean"}
    if isinstance(x, (int, float)):
        return {"type": "number"}
    return {"type": ["string", "null"]}


def prepare(mid: str, commit: str, fork: str | None) -> dict:
    m = MISSIONS[mid]
    text = (HERE / "missions" / m["file"]).read_text()
    b = BUNDLES[mid](commit)
    BUILD.mkdir(exist_ok=True)
    (BUILD / b["name"]).write_bytes(b["bytes"])
    digest = sha256(b["bytes"])
    fields = {"COMMIT": commit, "ATTACHMENT_LINE": f"the attached file `{b['name']}`", "ARCHIVE_SHA256": digest,
              f"{mid}_ARCHIVE_NAME": b["name"], f"{mid}_ARCHIVE_SHA256": digest, "FORK_REPO": fork or "<fork>",
              **b["fields"]}
    for k, v in fields.items():
        text = text.replace("{" + k + "}", v)
    left = sorted(set(re.findall(r"\{([A-Z][A-Z0-9_]+)\}", text)) - {"instruction", "feedback"})
    if left:
        raise SystemExit(f"{mid}: unfilled placeholders {left}")
    example = json.loads(re.findall(r"```json\n(.*?)\n```", text, re.S)[-1])
    leaks = redact(text)[1]
    if leaks:
        raise SystemExit(f"{mid}: the prompt matches a secret pattern, refusing to send it")
    (BUILD / f"{mid}.prompt.md").write_text(text)
    return {"mission": mid, "title": m["title"], "prompt": text, "schema": example_to_schema(example),
            "max_acu": m["max_acu"], "bundle": {"name": b["name"], "sha256": digest, "bytes": len(b["bytes"]),
                                                "path": str(BUILD / b["name"])}}


def save(status: dict, publish: bool) -> None:
    status["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    STATUS.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n")
    PAGE.parent.mkdir(exist_ok=True)
    PAGE.write_text(render_page.render(status))
    if publish:
        r = subprocess.run(["argos", "artifact", str(PAGE), "--name", "devin-lab.html"], capture_output=True, text=True)
        url = (r.stdout.strip().splitlines() or [""])[-1]
        if r.returncode == 0 and url.startswith("http") and status.get("page_url") != url:
            status["page_url"] = url
            STATUS.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n")


def launch(d: Devin, p: dict, fork: str | None) -> dict:
    url = d.upload(p["bundle"]["path"])
    secrets = None
    if p["mission"] == "M2" and GH_TOKEN_FILE.exists():
        secrets = [{"key": "GH_TOKEN", "value": GH_TOKEN_FILE.read_text().strip(), "sensitive": True}]
        p["prompt"] += (f"\n\nGitHub access: a token restricted to `{fork}` is in the environment variable GH_TOKEN "
                        "(use it with `gh` and git over https). Never print it.")
    s = d.create_session(p["prompt"], title=p["title"], tags=["holo-lab", p["mission"]], schema=p["schema"],
                         attachment_urls=[url], max_acu_limit=p["max_acu"], session_secrets=secrets)
    return {"mission": p["mission"], "title": p["title"], "session_id": s["session_id"], "url": s.get("url"),
            "state": "running", "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "max_acu": p["max_acu"], "bundle": {k: p["bundle"][k] for k in ("name", "sha256", "bytes")}}


def follow(d: Devin, status: dict, poll_s: float, timeout_s: float, publish: bool) -> None:
    t0 = time.time()
    while True:
        for s in status["sessions"]:
            if s.get("final"):
                continue
            try:
                cur = d.summary(s["session_id"])
            except DevinError as e:
                s["last_error"] = str(e)[:300]
                continue
            s.update({k: cur[k] for k in ("url", "state", "status", "status_detail", "acus_consumed",
                                          "pull_requests", "structured_output")})
            s["url"] = s["url"] or cur["url"]
            if cur["state"] != s.get("last_state"):
                status.setdefault("events", []).append({"at": time.strftime("%H:%M:%SZ", time.gmtime()),
                                                        "mission": s["mission"], "state": cur["state"]})
                s["last_state"] = cur["state"]
            if cur["state"] in FINAL:
                s["final"] = True
                s["finished_at"] = s.get("finished_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                try:
                    s["attachments"] = [{"name": a.get("name"), "url": a.get("url")} for a in d.attachments(s["session_id"])
                                        if a.get("source") != "user"]
                except DevinError as e:
                    s["last_error"] = str(e)[:300]
        save(status, publish)
        if all(s.get("final") for s in status["sessions"]) or time.time() - t0 > timeout_s:
            return
        time.sleep(poll_s)


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--missions", default="M4")
    a.add_argument("--fork-repo", help="owner/name of our OSWorld fork (required for M2 live)")
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--follow", action="store_true", help="only follow the sessions already in STATUS.json")
    a.add_argument("--poll", type=float, default=60)
    a.add_argument("--timeout-h", type=float, default=6)
    a.add_argument("--no-publish", action="store_true")
    o = a.parse_args()
    publish = not o.no_publish
    if o.follow:
        status = json.loads(STATUS.read_text())
        follow(Devin(), status, o.poll, o.timeout_h * 3600, publish)
        return
    mids = [m.strip() for m in o.missions.split(",") if m.strip()]
    if "M2" in mids and not o.dry_run and not o.fork_repo:
        raise SystemExit("M2 needs --fork-repo owner/name (a fork of xlang-ai/OSWorld that Devin can push to)")
    commit = git("rev-parse", "origin/main")
    preps = [prepare(m, commit, o.fork_repo) for m in mids]
    if o.dry_run:
        for p in preps:
            with open(BUILD / f"{p['mission']}.dry_run.json", "w") as out:
                live_v1 = (load_key() or "").startswith("apk_")
                d = Devin(key="apk_" if live_v1 else None, dry_run=True, out=out)
                url = d.upload(p["bundle"]["path"])
                d.create_session(p["prompt"], title=p["title"], tags=["holo-lab", p["mission"]], schema=p["schema"],
                                 attachment_urls=[url], max_acu_limit=p["max_acu"])
            print(f"{p['mission']}: prompt {len(p['prompt'])} chars, bundle {p['bundle']['name']} "
                  f"{p['bundle']['bytes'] / 1e6:.1f} MB sha256 {p['bundle']['sha256'][:16]}…, max_acu {p['max_acu']} "
                  f"-> {BUILD / (p['mission'] + '.dry_run.json')}")
        old = json.loads(STATUS.read_text()) if STATUS.exists() else {}
        status = {"mode": "dry_run", "commit": commit, "auth_check": old.get("auth_check"), "page_url": old.get("page_url"),
                  "sessions": [
            {"mission": p["mission"], "title": p["title"], "session_id": None, "url": None, "state": "not_launched",
             "max_acu": p["max_acu"], "bundle": {k: p["bundle"][k] for k in ("name", "sha256", "bytes")}} for p in preps]}
        save(status, publish)
        return
    d = Devin()
    status = {"mode": "live", "api_version": d.version, "commit": commit, "sessions": []}
    if STATUS.exists():
        old = json.loads(STATUS.read_text())
        status["sessions"] = [s for s in old.get("sessions", []) if s.get("session_id") and s["mission"] not in mids]
        status["page_url"] = old.get("page_url")
    for p in preps:
        status["sessions"].append(launch(d, p, o.fork_repo))
        save(status, publish)
        print(f"{p['mission']} launched: {status['sessions'][-1]['url']}", flush=True)
    follow(d, status, o.poll, o.timeout_h * 3600, publish)


if __name__ == "__main__":
    main()
