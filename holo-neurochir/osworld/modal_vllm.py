"""Holo-3.1-4B (or a weight-edited checkpoint) served by vLLM 0.23.0 on one Modal H100, OpenAI-compatible over HTTPS.
Same vLLM version and flags as the pod (serve_vllm.sh). Protected by vLLM --api-key (Bearer token from the Modal
Secret 'holo-vllm-key', copy on orbit in ~/.holo_modal_key). Budget: 1 GPU max, scales to zero after 5 min idle.

  modal run    osworld/modal_vllm.py::download                      # once: HF weights -> Volume holo-models (CPU only)
  modal run    osworld/modal_vllm.py::toolchain                     # CPU check: nvcc + package versions vs the pod
  modal deploy osworld/modal_vllm.py                                # serve Hcompany/Holo-3.1-4B as 'Holo-3.1-4B'
  HOLO_CKPT=<subdir> HOLO_NAME=Holo-3.1-4B-patched modal deploy osworld/modal_vllm.py
                                                                    # serve /models/ckpt/<subdir> instead
  modal volume put holo-models <local_ckpt_dir> /ckpt/<subdir>      # upload a modified checkpoint (HF layout)
  modal app stop holo-vllm                                          # nothing left running
"""
import os
import subprocess

import modal

HF_ID = "Hcompany/Holo-3.1-4B"
HF_REV = "8c88265a5a159bfd1492db9243733dd2e6e04a6e"
VLLM_ARGS = ["--dtype", "bfloat16", "--max-model-len", "32768", "--max-num-seqs", "64",
             "--gpu-memory-utilization", "0.40", "--kv-cache-memory-bytes", "30G",
             "--limit-mm-per-prompt", '{"image": 5}', "--reasoning-parser", "qwen3", "--enable-prefix-caching"]
CKPT = os.environ.get("HOLO_CKPT", "")
NAME = os.environ.get("HOLO_NAME", "Holo-3.1-4B")

models = modal.Volume.from_name("holo-models", create_if_missing=True)
cache = modal.Volume.from_name("holo-vllm-cache", create_if_missing=True)

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu24.04", add_python="3.12")  # pod: nvcc of /usr/local/cuda 12.8
    .uv_pip_install("vllm==0.23.0", "torch==2.11.0", "torchvision==0.26.0", "transformers==4.57.6",
                    "flashinfer-python==0.6.12", "flashinfer-cubin==0.6.12", "triton==3.6.0", "xgrammar==0.2.5.post1",
                    "huggingface_hub[hf_transfer]")
    .env({"HF_HOME": "/models/hf", "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

app = modal.App("holo-vllm", image=image)


@app.function(volumes={"/models": models}, timeout=1800)
def download():
    from huggingface_hub import snapshot_download

    path = snapshot_download(HF_ID, revision=HF_REV)
    models.commit()
    print(path)


@app.function()
def toolchain():
    subprocess.run("nvcc --version | tail -1; python -c 'import torch, vllm, flashinfer, transformers; "
                   "print(torch.__version__, torch.version.cuda, vllm.__version__, flashinfer.__version__, "
                   "transformers.__version__)'", shell=True, check=True)


@app.function(
    gpu="H100",
    max_containers=1,
    min_containers=0,
    scaledown_window=300,
    timeout=900,
    volumes={"/models": models, "/cache": cache},
    secrets=[modal.Secret.from_name("holo-vllm-key")],
    env={"HOLO_CKPT": CKPT, "HOLO_NAME": NAME, "HF_HUB_OFFLINE": "1", "XDG_CACHE_HOME": "/cache",
         "FLASHINFER_WORKSPACE_BASE": "/cache", "TRITON_CACHE_DIR": "/cache/triton"},
)
@modal.concurrent(max_inputs=64)
@modal.web_server(port=8000, startup_timeout=1800)
def serve():
    ckpt = os.environ["HOLO_CKPT"]
    model = f"/models/ckpt/{ckpt}" if ckpt else HF_ID
    cmd = ["python", "-m", "vllm.entrypoints.openai.api_server", "--model", model,
           "--served-model-name", os.environ["HOLO_NAME"], *VLLM_ARGS,
           "--api-key", os.environ["VLLM_API_KEY"], "--host", "0.0.0.0", "--port", "8000"]
    subprocess.Popen(cmd)
