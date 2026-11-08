"""Hcompany/Holo4-27B served by vLLM 0.23.0 on one Modal H100 (account 2) as 'Holo4-27B', OpenAI-compatible over HTTPS,
as the JUDGE of verif-study / judge-bench, then as the rescue AGENT of rescue-bench (harness format: up to 5
images + JSON schema). Same image, Volumes and Bearer key (Modal Secret
'holo-vllm-key') as modal_vllm.py; its own app so it never replaces the holo-vllm server of the jury window.
54.7 GB of bf16 weights on 80 GB: the 4B's memory flags do not fit, hence gpu-memory-utilization 0.92 and 16 sequences.

  MODAL_PROFILE=martinbon39 modal run    osworld/modal_judge.py::download   # once: HF -> Volume holo-models (CPU)
  MODAL_PROFILE=martinbon39 modal deploy osworld/modal_judge.py
  MODAL_PROFILE=martinbon39 modal app stop holo-judge                       # as soon as verif-study is done
"""
import os
import subprocess

import modal

HF_ID = "Hcompany/Holo4-27B"
HF_REV = "4de03cfeee1d930b616bfd4817570293f29ad8b9"
NAME = "Holo4-27B"
VLLM_ARGS = ["--dtype", "bfloat16", "--max-model-len", "32768", "--max-num-seqs", "16",
             "--gpu-memory-utilization", "0.92", "--limit-mm-per-prompt", '{"image": 5}',
             "--reasoning-parser", "qwen3", "--enable-prefix-caching"]

models = modal.Volume.from_name("holo-models", create_if_missing=True)
cache = modal.Volume.from_name("holo-vllm-cache", create_if_missing=True)
image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu24.04", add_python="3.12")
    .uv_pip_install("vllm==0.23.0", "torch==2.11.0", "torchvision==0.26.0", "transformers==4.57.6",
                    "flashinfer-python==0.6.12", "flashinfer-cubin==0.6.12", "triton==3.6.0", "xgrammar==0.2.5.post1",
                    "huggingface_hub[hf_transfer]")
    .env({"HF_HOME": "/models/hf", "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)
app = modal.App("holo-judge", image=image)


@app.function(volumes={"/models": models}, timeout=3600, cpu=4)
def download():
    from huggingface_hub import snapshot_download

    print(snapshot_download(HF_ID, revision=HF_REV))
    models.commit()


@app.function(
    gpu="H100", max_containers=1, min_containers=0, scaledown_window=600, timeout=900,
    volumes={"/models": models, "/cache": cache}, secrets=[modal.Secret.from_name("holo-vllm-key")],
    env={"HF_HUB_OFFLINE": "1", "XDG_CACHE_HOME": "/cache", "FLASHINFER_WORKSPACE_BASE": "/cache",
         "TRITON_CACHE_DIR": "/cache/triton"},
)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=8000, startup_timeout=1800)
def serve():
    subprocess.Popen(["python", "-m", "vllm.entrypoints.openai.api_server", "--model", HF_ID, "--revision", HF_REV,
                      "--served-model-name", NAME, *VLLM_ARGS, "--api-key", os.environ["VLLM_API_KEY"],
                      "--host", "0.0.0.0", "--port", "8000"])
