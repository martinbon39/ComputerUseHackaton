# Backend Modal du service Holo (identique sur les deux comptes)

Source : `osworld/modal_vllm.py`. Les options effectives viennent de la ligne `non-default args` du log vLLM (clé masquée).

| Élément | Valeur |
|---|---|
| GPU | 1 × NVIDIA H100 80 GB (Modal `gpu="H100"`), un seul conteneur par compte |
| Image | `nvidia/cuda:12.8.1-devel-ubuntu24.04` + Python 3.12 (Modal `add_python`) ; nvcc 12.8 pour le JIT, comme le pod |
| Paquets | vllm 0.23.0, torch 2.11.0+cu130, torchvision 0.26.0, transformers 4.57.6, flashinfer-python et flashinfer-cubin 0.6.12, triton 3.6.0, xgrammar 0.2.5.post1, les mêmes versions que `/workspace/vllm-venv` du pod |
| Poids de base | `Hcompany/Holo-3.1-4B`, snapshot `8c88265a5a159bfd1492db9243733dd2e6e04a6e` (identique au pod), Volume `holo-models:/hf` |
| Checkpoints édités | `holo-models:/ckpt/<nom>`, envoyés depuis le pod par `modal_put_ckpt.sh` |
| Entrée | `python -m vllm.entrypoints.openai.api_server` |
| Options effectives | `--model <HF id ou /models/ckpt/<nom>> --served-model-name <nom> --dtype bfloat16 --max-model-len 32768 --max-num-seqs 64 --gpu-memory-utilization 0.40 --kv-cache-memory-bytes 30G --limit-mm-per-prompt '{"image": 5}' --reasoning-parser qwen3 --enable-prefix-caching --api-key *** --host 0.0.0.0 --port 8000` |
| Différences avec le pod | GPU H100 au lieu de H200 ; autre build du conteneur (même versions) ; `--api-key` ajouté ; accès par l'URL HTTPS Modal au lieu d'un tunnel SSH |
| Caches | torch.compile, flashinfer et triton dans le Volume `holo-vllm-cache` (`/cache`) |
| Garde-fous | `max_containers=1`, `min_containers=0`, `scaledown_window=300 s`, 900 s max par requête, au plus 64 requêtes concurrentes par conteneur |

Comparaison équitable avec une édition : servir l'original sur le même compte et le même backend (`HOLO_NAME=Holo-3.1-4B-modal-orig modal deploy osworld/modal_vllm.py`, sans `HOLO_CKPT`).
