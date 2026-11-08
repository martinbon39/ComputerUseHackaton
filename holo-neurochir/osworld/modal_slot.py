"""Modal research slot: run one job (python <script> <job.json> ...) on one H100 with the pod's research venv
(/workspace/venv frozen in modal_slot_requirements.txt: torch 2.11.0+cu128, transformers 5.22.2, fla, causal_conv1d).
Volume holo-slot: /code/holo (copy of the pod's /workspace/projet/holo, refreshed by every job), /jobs/<id>/in (the job
dir as uploaded), /jobs/<id>/out ($OUT_DIR, fetched back by the caller). Weights: Volume holo-models (HF_HOME=/models/hf,
same snapshot as the pod; edited checkpoints under /models/ckpt/<name>). One container at a time, 1 h max, scales to zero.

  modal deploy osworld/modal_slot.py          # once per account (MODAL_PROFILE=martinbon39 for account 2)
  pod: bash /workspace/modal_run_job.sh <job_dir> "<command>" [1|2]
"""
import os
import subprocess
from pathlib import Path

import modal

HERE = Path(__file__).parent
slot = modal.Volume.from_name("holo-slot", create_if_missing=True)
models = modal.Volume.from_name("holo-models", create_if_missing=True)

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu24.04", add_python="3.12")
    .apt_install("git")
    .pip_install_from_requirements(str(HERE / "modal_slot_requirements.txt"),
                                   extra_index_url="https://download.pytorch.org/whl/cu128")
    .add_local_dir(str(HERE / "modal_slot_wheels"), "/usr/local/lib/python3.12/site-packages", copy=True)
    .env({"HF_HOME": "/models/hf", "HF_HUB_OFFLINE": "1", "PYTHONUNBUFFERED": "1"})
)

app = modal.App("holo-slot", image=image)


@app.function(gpu="H100", max_containers=1, min_containers=0, scaledown_window=60, timeout=3600,
              volumes={"/slot": slot, "/models": models})
def run_job(job_id: str, command: str) -> int:
    job = Path("/slot/jobs") / job_id
    out = job / "out"
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OUT_DIR=str(out), JOB_DIR=str(job / "in"), PYTHONPATH=f"/slot/code:{job / 'in'}",
               TRITON_CACHE_DIR="/slot/cache/triton", TORCHINDUCTOR_CACHE_DIR="/slot/cache/inductor")
    with open(out / "modal_log.txt", "w") as log:
        rc = subprocess.run(["bash", "-c", command], cwd=job / "in", env=env, stdout=log,
                            stderr=subprocess.STDOUT).returncode
    (out / "modal_exit_code").write_text(f"{rc}\n")
    slot.commit()
    return rc
