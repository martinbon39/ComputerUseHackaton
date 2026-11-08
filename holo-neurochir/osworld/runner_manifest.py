"""Effective runner manifest of a Modal-served measurement: the deployed source (osworld/modal_vllm.py: git commit,
sha256, image spec, GPU and container options, vLLM command line) plus what the live server reports (vLLM /version,
served model id and root). Written next to the measurement as runner_manifest.json.
Usage: PYTHONPATH=. ~/osw/venv/bin/python osworld/runner_manifest.py <base_url ending /v1> <served name> <out.json>
       [ENVVAR with the auth header lines]
"""
import hashlib, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from astra_cohort_probe import server_info  # noqa: E402

SRC = Path(__file__).resolve().parent / "modal_vllm.py"


def source_manifest():
    text = SRC.read_text()
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(SRC)], capture_output=True, text=True,
                            cwd=SRC.parent).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", str(SRC)], capture_output=True, text=True,
                                cwd=SRC.parent).stdout.strip())
    image = text[text.index("image = ("): text.index("app = modal.App")].strip()
    function_opts = {k: v for k, v in re.findall(r"^\s*(gpu|max_containers|min_containers|scaledown_window|timeout)"
                                                 r"\s*=\s*([^,\n]+)", text, re.M)}
    cmd = text[text.index('"python", "-m", "vllm.entrypoints.openai.api_server"'):]
    cmd = cmd[: cmd.index("]", cmd.index('"--port"'))]  # the list ends after the port, past os.environ[...] lookups
    return {"file": "holo-neurochir/osworld/modal_vllm.py", "git_commit": commit or None,
            "uncommitted_changes": dirty, "tracked": bool(commit),
            "sha256": hashlib.sha256(text.encode()).hexdigest(), "image": image, "function_options": function_opts,
            "vllm_command": re.sub(r'os\.environ\["VLLM_API_KEY"\]', '"<VLLM_API_KEY secret>"', cmd)}


def main():
    url, name, out = sys.argv[1:4]
    auth = sys.argv[4] if len(sys.argv) > 4 else None
    m = {"written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "runner": "Modal app holo-vllm",
         "served": server_info(url, name, auth), "source": source_manifest()}
    Path(out).write_text(json.dumps(m, indent=1))
    print(json.dumps({"vllm": m["served"].get("vllm_version"), "models": m["served"].get("models"),
                      "gpu": m["source"]["function_options"].get("gpu"), "commit": (m["source"]["git_commit"] or "untracked")[:10],
                      "dirty": m["source"]["uncommitted_changes"]}))


if __name__ == "__main__":
    main()
