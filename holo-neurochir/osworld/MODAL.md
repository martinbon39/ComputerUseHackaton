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

## Mesures (2026-11-08, `osworld/modal_probe.py`, tâche chrome `fc6d8143…`, dernier pas)

| Compte, modèle servi | Démarrage à froid | Texte T=0 | Texte avec réflexion | Pas OSWorld (11 024 tokens de prompt + capture, schéma, réflexion) |
|---|---|---|---|---|
| 2, `Holo-3.1-4B-free_h2` | 512 s (premier, JIT compris) | 2,2 s | 1,6 s (307 tokens) | 4,7 s, JSON valide |
| 1, `Holo-3.1-4B-free_h3_l05` | ~17 min (premier, JIT compris, après 2 essais ratés) | 3,2 s | 2,3 s (447 tokens) | 5,4 s, JSON valide |

Sans la clé, `/v1/models` répond 401. Les démarrages suivants profitent du cache du Volume `holo-vllm-cache` (torch.compile et JIT).

## Créneau de recherche (app `holo-slot`, `osworld/modal_slot.py`)

Ce créneau exécute un job de recherche quelconque (transformers, hooks, activations) sur une H100 Modal. Le venv est le même que
celui du pod (`/workspace/venv`, figé dans `modal_slot_requirements.txt` : torch 2.11.0+cu128, transformers 5.22.2, fla 0.6.0,
causal_conv1d 1.7.0, dont le build est copié du pod). La fonction `run_job` tourne dans un seul conteneur à la fois par compte,
1 h au plus, et redescend à zéro 60 s après la fin.

Sur le pod :
```bash
bash /workspace/modal_run_job.sh <dossier_job> "python <script> <job.json>" [1|2]   # compte 2 par défaut
```
1. Le script envoie `/workspace/projet/holo` (`/slot/code/holo`, à chaque job) et `<dossier_job>` (`/slot/jobs/<id>/in`) dans le
   Volume `holo-slot` du compte.
2. Il lance la commande avec `bash -c`, `cwd` = la copie du dossier, `PYTHONPATH=/slot/code:<dossier>`, `HF_HOME=/models/hf`
   (Holo-3.1-4B en cache, hors ligne) et `OUT_DIR=/slot/jobs/<id>/out`. Les checkpoints édités sont lisibles sous
   `/models/ckpt/<nom>`.
3. Il rapatrie `OUT_DIR` dans `<dossier_job>/modal_out/` (avec `modal_log.txt`, la sortie standard et les erreurs du job, et
   `modal_exit_code`) et rend le code de retour du job.

Règles pour le job : chemins relatifs au dossier du job (rien sous `/workspace`) ; écrire les résultats dans `$OUT_DIR` ; ne pas
dépasser quelques Go (le débit d'upload est d'environ 40 Mo/s). Le script refuse de lancer un job si le même compte sert
`holo-vllm` sur sa GPU (une H100 par compte, budget), sauf avec `MODAL_SLOT_FORCE=1`.

Exemple testé : `/workspace/osw_shared/modal_slot_example` (`gen.py` : une génération gloutonne avec `holo.model.Holo`).
Mesures du 2026-11-08 sur le compte 1 : 75 à 89 s de bout en bout, dont chargement des poids 10 à 15 s et génération de 48 tokens
48 à 52 s, qui comprennent le JIT et l'autotune des noyaux fla au premier appel ; envoi 7 à 9 s. Sortie : torch 2.11.0+cu128,
transformers 5.22.2, NVIDIA H100 80GB HBM3.
