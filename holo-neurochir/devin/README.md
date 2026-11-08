# Devin dans le labo

Devin (Cognition) est l'ingénieur indépendant du labo. Notre orchestrateur lui confie, par l'API, des missions
vérifiables ; il rend une sortie structurée (JSON Schema), des fichiers et, pour M2, une PR.

| Fichier | Rôle |
|---|---|
| `devin_client.py` | client de l'API (stdlib) : session, message, attente, sortie structurée, PR, fichiers ; `--dry-run` sans clé |
| `missions/M1_reproduction.md` | reproduction indépendante du kit jury (niveaux 1 et 2), rapport PASS/FAIL |
| `missions/M2_feci_guard_pr.md` | Feci Guard comme option de l'adaptateur Surfer-H d'OSWorld, tests, workflow CI, PR sur notre fork |
| `missions/M3_scale_audit.md` | (optionnelle) audit de l'infra et plan chiffré à 100 VMs, lecture seule |
| `run_missions.py` | construit les archives d'entrée depuis `origin/main`, lance les missions en parallèle, suit, écrit `STATUS.json`, publie la page |
| `render_page.py` | page « Devin dans le labo » (se recharge chaque minute ; republiée à chaque tour de suivi) |
| `test_devin.py` | tests hors ligne contre un faux serveur Devin v3 local (`python3 -m unittest test_devin -v`) |

```
python3 run_missions.py --dry-run --missions M1,M2,M3       # sans clé ni réseau Devin : build/<M>.dry_run.json
python3 run_missions.py --missions M1                         # en vrai
python3 run_missions.py --missions M2 --fork-repo martinbon39/OSWorld
python3 run_missions.py --follow                              # reprend le suivi des sessions de STATUS.json
python3 devin_client.py status <devin_id> | message <devin_id> "…" | messages <devin_id> | terminate <devin_id>
```

## API utilisée (doc lue le 2026-11-08)
- v3, la version courante : `https://api.devin.ai/v3/organizations/{org_id}/…`, `Authorization: Bearer cog_…`
  (clé de service user ou PAT), org_id donné par `GET /v3/self`. Sources : https://docs.devin.ai/api-reference/overview.md,
  https://docs.devin.ai/api-reference/authentication.md, spec https://docs.devin.ai/v3-openapi.yaml.
- `POST /sessions` (`prompt`, `title`, `tags`, `attachment_urls`, `structured_output_schema`, `max_acu_limit`,
  `session_secrets`), `GET /sessions/{devin_id}` (`status` new|claimed|running|exit|error|suspended|resuming,
  `status_detail` working|waiting_for_user|waiting_for_approval|finished|…, `structured_output`, `pull_requests`,
  `acus_consumed`), `POST /sessions/{id}/messages`, `GET /sessions/{id}/messages`, `GET /sessions/{id}/attachments`,
  `POST /attachments` (multipart `file`), `DELETE /sessions/{id}`.
- Une clé legacy `apk_…` passe par la v1 (`/v1/sessions`, `status_enum`, pièces jointes en lignes `ATTACHMENT:"url"`).
- La doc ne dit pas quel statut veut dire « fini » : on prend `exit` ou `status_detail=finished` (fini),
  `error` (échec), `suspended` (en veille, s'arrête de compter les ACU), `waiting_for_*` (attend une réponse).
- La doc ne donne ni limites de débit chiffrées (seulement 429), ni taille du disque ou de la RAM de la VM de Devin
  (agrandissable dans Settings), ni prix de l'ACU sur les offres actuelles (Free, Pro, Max, Teams, Enterprise).
  Devin se met en veille après 5 min d'inactivité et ne consomme rien en veille (https://docs.devin.ai/admin/billing/usage).

## Ce qu'il faut à Martin
1. **La clé** : Settings > Devin API > service user, clé `cog_…` dans `~/.devin_key` (`chmod 600`). Elle n'est jamais
   affichée ni écrite par ces scripts.
2. **M1, accès au dépôt privé** : rien à faire. Le dossier `jury_kit/` part en pièce jointe (`git archive` du commit
   épinglé, sha256 dans le prompt). L'intégration GitHub de Devin (Settings > Connections > GitHub) permettrait en plus
   le clone direct, mais la doc la décrit pour une organisation GitHub dont on est admin
   (https://docs.devin.ai/integrations/gh) ; ne pas rendre le dépôt public pour ça.
3. **M2, un fork d'OSWorld que Devin peut pousser** : `gh repo fork xlang-ai/OSWorld --clone=false` (crée le dépôt
   public `martinbon39/OSWorld`, à décider par Martin), puis soit l'intégration GitHub de Devin limitée à ce dépôt, soit
   un token GitHub fine-grained limité à ce seul dépôt (Contents, Pull requests et Workflows en écriture) dans
   `~/.devin_gh_token` : il est passé à la session comme secret sensible `GH_TOKEN`. La PR vise le fork, jamais xlang-ai.
4. **Coût** : plafonds `max_acu_limit` M1 10, M2 20, M3 6 ACU (dans `run_missions.py`). Aucune autre dépense.
5. **Pour un vrai `--check` au niveau 2** : publier le checkpoint fusionné sur Hugging Face (le kit dit encore
   `HF_REPO_ID`) ; sinon M1 fait le `--build` complet si la VM a ~45 Go de disque, ou un contrôle réduit déclaré comme tel.
