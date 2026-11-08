# Holo-3.1-4B sur Modal (H100, vLLM 0.23.0)

App `holo-vllm` (`osworld/modal_vllm.py`), déployée sur deux comptes Modal. Même vLLM (0.23.0), même snapshot HF
(`8c88265a…`, identique au pod) et mêmes flags que le pod (`serve_vllm.sh`). Une seule H100 par compte
(`max_containers=1`, `min_containers=0`), arrêt après 5 min sans requête (`scaledown_window=300`), 900 s max par requête.
Démarrage à froid : voir les mesures plus bas. Le cache JIT (flashinfer, triton, torch.compile) est conservé dans le
Volume `holo-vllm-cache`, donc seul le premier démarrage de chaque compte le recompile.

| Compte | Profil Modal | Usage prévu (ares) | URL de base OpenAI |
|---|---|---|---|
| 1 | `emilejouannet` (actif par défaut) | candidat `lmscale16`, bras GitHub du test | `https://emilejouannet--holo-vllm-serve.us-east.modal.run/v1` |
| 2 | `martinbon39` (`MODAL_PROFILE=martinbon39`) | éditions statiques d'astra-free (H2, H3) | `https://martinbon39--holo-vllm-serve.us-east.modal.run/v1` |

## Auth

L'endpoint est public : vLLM tourne avec `--api-key`, donc chaque requête `/v1/*` doit porter `Authorization: Bearer <clé>`.
- La clé (la même sur les deux comptes) se trouve sur orbit dans `~/.holo_modal_key` (600). Dans les conteneurs, c'est la variable
  `VLLM_API_KEY`, qui vient du Secret Modal `holo-vllm-key` de chaque compte. Ne l'affiche jamais.
- Côté client : `OpenAI(base_url=URL, api_key=open(os.path.expanduser("~/.holo_modal_key")).read().strip())`, ou
  `export OPENAI_API_KEY="$(cat ~/.holo_modal_key)"` pour le harness.
- Seuls `/health` et `/metrics` répondent sans clé (ils ne servent pas de modèle).

```bash
U=https://emilejouannet--holo-vllm-serve.us-east.modal.run
curl -sL $U/v1/chat/completions -H "Authorization: Bearer $(cat ~/.holo_modal_key)" -H 'Content-Type: application/json' \
  -d '{"model":"Holo-3.1-4B","messages":[{"role":"user","content":"hi"}],"max_tokens":32}'
# 3 requêtes chronométrées (dont 1 au format du harness OSWorld, avec image) :
PYTHONPATH=. ~/osw/venv/bin/python osworld/modal_probe.py $U/v1 <task_dir> [--model <nom servi>]
```
La première requête d'un conteneur à zéro paie le démarrage à froid. Au-delà de 150 s, Modal répond par une redirection 303 :
il faut `curl -L`, et le client OpenAI la suit lui-même.

## Servir un checkpoint modifié

1. Sur le pod, envoie le dossier HF complet (les `.safetensors` et tous les fichiers non-poids du snapshot de base) :
   `bash /workspace/modal_put_ckpt.sh <dir> <nom> [1|2]` (compte 2 par défaut). Le jeton est lu dans `/root/.modal_env` ou
   `/root/.modal_env2`. Débit mesuré : 38 Mo/s, donc environ 4 min pour 9 Go.
2. Sur orbit : `bash osworld/modal_deploy.sh <1|2> <nom servi> [<nom du ckpt>]` (sans ckpt, c'est l'original). Le script déploie
   et écrit `osworld/modal_deploys/<utc>_acct<n>_<nom>.json` (checkpoint, nom servi, commit de `modal_vllm.py`, options vLLM,
   GPU, compte, heure), qu'online-eval joint à ses mesures. Il refuse de déployer si `modal_vllm.py` n'est pas commité.
   Un déploiement remplace le modèle servi : un seul checkpoint par compte à la fois, et une requête en vol est coupée.

## Arrêt

`modal app stop holo-vllm -y` et `MODAL_PROFILE=martinbon39 modal app stop holo-vllm -y`. Il faut redéployer pour relancer.
Les coûts sont tenus dans `MODAL_COST.md` (`modal billing report --for today --show-resources`).

## Mesures
(à compléter après le test)
