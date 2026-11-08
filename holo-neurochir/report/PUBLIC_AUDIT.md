# Audit avant passage en public : martinbon39/ComputerUseHackaton

Audit du 2026-11-08 (repo-audit, flotte argos), à la demande de ares. Il ne réécrit rien et ne pousse rien : chaque correctif ci-dessous est une recommandation, et c'est Martin qui décide.

## Périmètre et méthode

- **Clone.** Clone complet et non shallow (`git clone --no-local`), fait dans le scratchpad et pas dans la copie partagée.
- **Refs auditées.** Toutes les refs distantes : `main` jusqu'à `e880c66`, `feat/rescue-bench` (`46a38b2`) et la PR #1 (`refs/pull/1/head` = `46a38b2`, `refs/pull/1/merge` = `93aba96`). Cela fait 142 commits et 3 475 blobs uniques.
- **Outils.** gitleaks et trufflehog n'ont pas pu être installés : les releases GitHub répondaient en 504 et l'accès à docker était refusé. Je les ai remplacés par trois choses :
  1. **Scan de chaque blob de l'historique** (`git rev-list --all --objects` puis `cat-file`), y compris les fichiers supprimés depuis, avec ces motifs :
     - clés et jetons : `hf_`, `sk-`/`sk-ant-`/`sk-proj-`, `ghp_`/`gho_`/`github_pat_`, `cog_`, `r8_`, Modal `ak-`/`as-`/`wk-`/`ws-`, `rpa_`, `AKIA`, `AIza`, `xox?-`, jeton de bot Telegram, JWT ;
     - en-têtes `-----BEGIN … PRIVATE KEY`, `Bearer …`, et les affectations `password|secret|token|api_key = "…"` ;
     - URL avec identifiants, e-mails, IPv4, téléphones FR ;
     - motifs internes : martinbonan.com, oopercast/ooper, astry, `/home/orbit`, runpod, tailscale ;
     - motifs de prompts système : `system-reminder`, `You are Claude Code`, `HARNESS MODE`.
  2. **Archives décompressées** et scannées : les 217 fichiers `.gz`/`.npz`.
  3. **detect-secrets 1.5.0** (`--all-files`) sur l'arbre de `ce6e843`. Les 6 commits suivants, jusqu'à `e880c66`, ont été relus à la main sur leur diff.
     - 6 « Secret Keyword » : tous des faux positifs (`api_key="EMPTY"`, un nom de variable d'environnement, des phrases du type « No tokens collected »), plus la clé `hk-` (voir A2).
     - 12 chaînes Base64 : des JPEG de VM OSWorld embarqués dans `paper/data/local/demo/osw_fs1_spotify.json`.
     - 12 668 chaînes hexadécimales : des sha256 et des IDs.
- **Relecture humaine.** Toute la prose a été relue par un lecteur séparé : LOG, JOURNAL, HANDOFF, BRIEF, CONTEXT, MODAL et les README.
- **Vérifications ciblées** sur les points sensibles :
  - provenance de la clé `hk-` ;
  - portée des jetons argos, testée en requête GET ;
  - authentification des endpoints Modal ;
  - corps de la PR #1.
- **Constat structurel.** L'historique est presque identique à HEAD : aucun fichier sensible n'a été ajouté puis supprimé. Seul `holo-neurochir/osworld/val_ok_tasks.json` a disparu de HEAD (ajouté en `706a036`, retiré en `67f8d9c`). D'après son nom, c'est une liste de tâches ; le scan de motifs n'y a rien trouvé. Supprimer un fichier dans HEAD ne le retire donc pas de l'historique, mais rien de sensible ne s'y cache sans être aussi visible dans HEAD.

## Verdict

| Gravité | Nombre | Résumé |
|---|---|---|
| **BLOQUANT** | 1 | Le nom d'un tiers, `emilejouannet` (titulaire du compte Modal 1), apparaît dans 59 fichiers et 21 commits. Il faut son accord, sinon remplacer le nom. |
| **À NETTOYER** | 12 | Liens argos signés encore valides, SSH et IDs de l'ex-pod, ordres d'agents bruts, budgets et dépenses, endpoint jury public, etc. |
| **OK** | 9 | Aucun secret propre à Martin. Les e-mails sont des fixtures OSWorld. Aucun fichier ne dépasse 20 Mo. Le VPS 37.187.252.136 n'apparaît jamais. |

**Aucune clé ni aucun jeton appartenant à Martin ou à l'équipe n'a été trouvé dans l'historique**, ni en clair ni dans les archives. La seule clé présente (`hk-…`) est celle de l'adaptateur officiel public d'OSWorld (voir A2). Si Martin accepte le constat B1, ou s'il remplace le nom dans HEAD, le dépôt peut passer public sans réécriture d'historique.

## Constats

### BLOQUANT

**B1. Nom d'un tiers : `emilejouannet`, compte Modal 1**

- **Où.** 21 commits, à partir de `b4aa504` (2026-11-08). 59 fichiers dans HEAD :
  - prose : `holo-neurochir/osworld/MODAL.md:11,24`, `osworld/MODAL_COST.md:7`, `paper/data/local/MODAL_COST.md:7`, `astra-merge/VERIFY_MODAL_REFERENCE.md:7`, `paper/data/pod_astra/merge/VERIFY_MODAL_REFERENCE.md:7` ;
  - code : `osworld/duel/duel_server.py:26-29`, `osworld/modal_deploy.sh`, `osworld/modal_budget_guard.sh` ;
  - données : plus de 400 lignes dans HEAD contenant `https://emilejouannet--holo-vllm-serve.us-east.modal.run/v1` dans `astra-merge/*`, `astra-regmean/*`, `osworld/modal_deploys/*.json` et les logs.
- **Risque.** Le prénom et le nom d'une personne autre que Martin sont associés à son workspace Modal et à ses dépenses (`MODAL_COST.md`). L'endpoint lui-même est protégé par une clé Bearer (`modal_vllm.py:105 --api-key`), donc le risque n'est pas technique : il s'agit de vie privée et de consentement.
- **Correctif recommandé.**
  - **Option 1, la plus simple :** Émile donne un accord explicite. B1 passe alors en À NETTOYER, rien à faire.
  - **Option 2 :** retirer le nom de HEAD, puis réécrire l'historique pour qu'il ne reste pas lisible dans les anciens commits :
    ```bash
    # HEAD (commit normal)
    git grep -l -I emilejouannet | xargs sed -i 's/emilejouannet/modal-account-1/g'
    # Historique : à faire sur un clone miroir neuf, pas sur la copie partagée
    git clone --mirror git@github.com:martinbon39/ComputerUseHackaton.git cuh-clean && cd cuh-clean
    printf 'emilejouannet==>modal-account-1\n' > ../replacements.txt
    git filter-repo --replace-text ../replacements.txt
    ```
  - **Attention si l'historique est réécrit :**
    - GitHub conserve `refs/pull/1/head` et `refs/pull/1/merge`, qu'un force-push ne peut pas modifier. Les anciens commits restent aussi accessibles par leur SHA.
    - Il vaut donc mieux **publier un nouveau dépôt public** à partir du miroir nettoyé que basculer la visibilité du dépôt actuel. L'autre voie est de demander au support GitHub de purger les refs de la PR.
    - La PR #1 serait à recréer, et les liens `github.com/martinbon39/ComputerUseHackaton` du README et du jury_kit à mettre à jour.
    - Les URL des données ne seront plus des URL réelles. C'est sans conséquence pour la reproduction : l'endpoint demande de toute façon une clé.

### À NETTOYER

**N1. Liens argos signés encore valides**

- **Où.**
  - `holo-neurochir/paper/data/local/reports/CONTEXT_2026-11-07.md:53-57` : tableau de bord d'équipe, papier, deck de pitch, vidéo, capture de démo. Commit `44854e6`.
  - `holo-neurochir/paper/data/local/JOURNAL.md:176` : archive `astra-circuit-report-final-20261107.zip`. Commit `44854e6`.
  - `jury_kit/README.md:18,49` (`052c906`) et `README.md` (`05fdc55`) : papier arXiv et NeurIPS, page de démo.
- **Risque.**
  - J'ai testé la portée : un jeton ne donne accès qu'à **son propre** artifact. Le jeton du papier sur l'URL du tableau de bord renvoie 401, et l'URL sans jeton aussi. Il ne s'agit donc pas d'un jeton maître.
  - Les liens restent valides environ 30 jours (jusqu'à début décembre). J'ai vérifié que quatre liens de `CONTEXT` et de `JOURNAL` répondent 200 : tableau de bord, deck, vidéo et archive zip.
  - Ces pages ne contiennent que du matériel du hackathon. Le tableau de bord d'équipe montre l'état de la mission, des ETA et les chiffres OSWorld.
- **Correctif.**
  - Les liens du README et du jury_kit sont faits pour le jury : on peut les garder.
  - Pour ceux de `CONTEXT_2026-11-07.md` et de `JOURNAL.md:176` :
    - soit on les retire de HEAD ;
    - soit on accepte que ces pages soient publiques pendant 30 jours ;
    - soit on les révoque côté argos, en supprimant ou renommant l'artifact.
  - Une réécriture d'historique n'est pas utile : il suffit de rendre le jeton mort côté serveur.

**N2. Accès SSH et identifiants de l'ex-pod RunPod**

- **Où.**
  - `ssh -i ~/.ssh/runpod_holo -p 15780 root@213.181.111.151` figure dans 4 fichiers de HEAD : `holo-neurochir/HANDOFF.md:17`, `osworld/ONLINE_EVAL.md:3`, `osworld/modal_serve_when_ready.sh:20`, `verif_study/sync.sh:4-5`.
  - `runpod_holo` figure dans 6 fichiers.
  - Les IDs pod `fbup7c0tebnkwf`, volume `8206qbtznz` et datacenter EUR-IS-4 figurent dans `HANDOFF.md:16`, `JOURNAL.md:78-79` et `paper/data/local/JOURNAL.md`.
  - Commits : à partir de `7cb9de0` (2026-11-07) ; 4 commits pour l'IP, 2 pour les IDs.
- **Risque.** Faible.
  - Aucune clé privée n'est dans le dépôt : `runpod_holo` n'est que le nom du fichier, et aucun en-tête `PRIVATE KEY` n'a été trouvé.
  - Le pod est arrêté, et RunPod réattribue l'IP et le port à d'autres clients. L'adresse ne désigne plus une machine de l'équipe.
  - Les IDs RunPod sans clé API ne donnent aucun accès.
- **Correctif.** Vérifier dans la console RunPod que le pod `fbup7c0tebnkwf` est bien terminé. Si le volume réseau `8206qbtznz` ne sert plus, le supprimer. Rédaction facultative dans HEAD. Pas de réécriture.

**N3. Ordres bruts de l'orchestrateur**

- **Où.** `holo-neurochir/moon-vision/ARES_ORDERS.json`, commit `cc671d3`.
- **Contenu.** Les messages de ares à un worker, avec leur IDs de message (6520, 6532, 6579…) et un ID de session argos, `"to_session": "4DOyaufy2j"`.
- **Risque.** Faible. Ni prompt système ni secret, mais c'est une conversation interne entre agents, avec un identifiant de session argos.
- **Correctif.** Le supprimer de HEAD (`git rm`), ou retirer `to_session`. Pas de réécriture.

**N4. Endpoint jury public sans authentification**

- **Où.** `https://martinbon39--holo-jury-probe-web.us-east.modal.run`, dans `jury_kit/README.md`, `osworld/MODAL.md:87` et `osworld/modal_jury_probe.py` (commit `0b61465`).
- **Risque.**
  - C'est un proxy CPU ouvert (CORS `*`). Il transmet à vLLM avec la clé serveur et peut donc réveiller un H100. Ce coût est borné : `max_containers=1`, `scaledown_window=300`, sémaphore et limite par client.
  - Le dépôt public ne fait qu'élargir l'audience d'un endpoint déjà donné au jury.
- **Correctif.** Pas dans le dépôt : il faut stopper l'app (`modal app stop holo-jury-probe`) à la fin de la fenêtre jury (cf. `osworld/modal_jury_window.sh`). On peut aussi garder le budget plafonné par `modal_budget_guard.sh`.

**N5. Budgets, dépenses et galères de comptes cloud**

- **Où.**
  - `osworld/MODAL_COST.md` (`b4aa504`) et `paper/data/local/MODAL_COST.md` (`44854e6`) : budget par compte, montants dépensés, une erreur de déploiement double.
  - `HANDOFF.md:16-18` et `JOURNAL.md:76,81` (`7cb9de0`) : « ~100 € de crédit », « 5,29 $/h ».
  - `osworld/MODAL.md:105-109`.
  - `paper/data/local/reports/CONTEXT_2026-11-07.md:7,12,79` : AWS et GCP bloqués, plafond de 90 $.
- **Risque.** Aucun risque de sécurité. Ce sont des informations financières personnelles, sans gravité.
- **Correctif.** C'est un choix éditorial de Martin : garder (transparence) ou retirer de HEAD.

**N6. Briefs d'agents et mode d'emploi de la flotte**

- **Où.** `holo-neurochir/HANDOFF.md:3-12,60-63` (« Règles de Martin… `argos spawn`… `argos notify` ») et `holo-neurochir/BRIEF_neurochirurgie_holo_LOCAL.md` (« Lance-le comme un /goal », stratégie partenaires du hackathon). Commit `7cb9de0`.
- **Risque.** Ce ne sont ni des prompts système ni le contenu du harnais (aucune occurrence de `CLAUDE.md`, `system-reminder` ou `HARNESS MODE` dans tout l'historique). Ces fichiers décrivent en revanche l'outillage personnel de Martin.
- **Correctif.** Un choix éditorial. Le README public décrit déjà l'équipe d'agents, ce qui rend ces fichiers cohérents avec le récit.

**N7. Estimations et remarques internes**

- **Où.** `paper/data/local/reports/CONTEXT_2026-11-07.md` (`44854e6`) :
  - `:71-72` : « Papier solide qui intéresse H ~85 % », « Victoire au hackathon ~15 % » ;
  - `:14,61-62` : incidents de flotte (« le pkill a tué un agent ») ;
  - `:12` : VNC des VM exposé sur l'IP publique du VPS, puis corrigé en 127.0.0.1. C'est une faille passée décrite en clair.
- **Correctif.** Retirer ce fichier de HEAD, ou au moins les lignes 12 et 66-72 (tableau des probabilités).

**N8. Lien vers un artifact claude.ai**

- **Où.** `LOG.md:27`, commit `67f8d9c` : `https://claude.ai/artifact/4pBuLKr…`, qui contient un « pack de contexte complet », environ 364 k caractères de notes brutes.
- **Risque.** Les artifacts claude.ai sont privés par défaut. Le lien n'expose rien tant que l'artifact n'est pas partagé.
- **Correctif.** Vérifier côté claude.ai que l'artifact n'est pas partagé publiquement.

**N9. Fichiers `.pyc` commités**

- **Où.** 18 fichiers `__pycache__/*.pyc` dans HEAD, par exemple `holo-neurochir/feci_guard/__pycache__/feci_guard.cpython-314.pyc`.
- **Risque.** Aucun secret, mais ils contiennent des chemins absolus. C'est surtout une question d'hygiène.
- **Correctif.** `git rm -r --cached '*/__pycache__'`, puis ajouter `__pycache__/` au `.gitignore`.

**N10. Chemins `/home/orbit` et topologie du VPS**

- **Où.** 80 fichiers dans HEAD (logs, manifests `modal_deploys/*`, scripts), à partir de `b7fda94`.
- **Risque.** Faible. Cela révèle le nom d'utilisateur `orbit` et l'arborescence, sans IP du VPS. Le README public (`05fdc55`) l'assume déjà : « Some scripts contain absolute paths of our server ».
- **Correctif.** Aucun.

**N11. Pseudo `martinbon39` et e-mail des commits**

- **Où.**
  - `martinbon39` figure dans 74 fichiers : URL Modal `martinbon39--holo-*`, `martinbon39/holo-osworld-runner`.
  - 139 commits sur 142 (toutes refs) ont pour auteur `Martin Bonan <bonanmartin@gmail.com>`. Il y a aussi `argos <argos@localhost>` (`8a2a4f5`) et `holo-neurochir <noreply@users.noreply.github.com>`.
- **Risque.**
  - Le pseudo est celui du propriétaire du dépôt public, donc déjà public.
  - L'e-mail personnel deviendra visible dans les métadonnées des commits.
- **Correctif.** Si Martin veut masquer l'e-mail : `git filter-repo --mailmap` vers `…@users.noreply.github.com`, avec la même contrainte de nouveau dépôt qu'en B1. Sinon, rien à faire.

**N12. Matériel du PC de Martin**

- **Où.** `holo-neurochir/JOURNAL.md:9-11` et `paper/data/local/JOURNAL.md:8` (`7cb9de0`) : Windows 11 Famille, Core Ultra 7 258V, Arc 140V, 31,5 Go.
- **Risque.** Négligeable.
- **Correctif.** Aucun.

### OK

- **A1. Aucun secret de l'équipe.** Aucune occurrence, dans les 142 commits et toutes les archives décompressées, de `hf_`, `sk-`, `ghp_`/`github_pat_`, `cog_`, Modal `ak-`/`as-`, `rpa_`, `AKIA`, d'une clé privée ou d'un jeton Bearer en clair.
  - Le jeton Modal mentionné dans `astra-merge/REPORT.md:94`, qu'on avait vu fuiter dans des logs du pod, n'a jamais été commité : aucune occurrence `ak-`/`as-`/`wk-`/`ws-` dans tout l'historique.
  - Les clés vLLM et Modal ne sont référencées que par leur chemin (`~/.holo_modal_key`, `modal.Secret.from_name("holo-vllm-key")`).
- **A2. Clé `hk-f8a86be2…` dans `holo-neurochir/paper/data/local/harness/surfer_agent.py:25`** (commit `44854e6`). C'est une copie verbatim de l'adaptateur officiel `xlang-ai/OSWorld` `mm_agents/surferH/surfer_agent.py`. J'ai vérifié : la même clé est à la ligne 25 du dépôt public upstream. Elle est donc déjà publique, et elle appartient à H Company, pas à Martin. Correctif facultatif : la remplacer dans HEAD par `os.environ["HAI_API_KEY"]`. Pas de réécriture.
- **A3. Le mot de passe `"osworld-public-evaluation"`** (`feci_guard/run_holo_guard.py`, `harness/run_holo.py`) est le mot de passe sudo public des VM OSWorld.
- **A4. Les e-mails sont des fixtures du benchmark OSWorld** :
  - `*@someuniversity.edu`, `anonym-x2024@outlook.com`/`gmail.com`, `xlang2024anonym@gmail.com`, `Test@gmail.com`, `*@example.com` ;
  - les adresses publiques des auteurs d'OSWorld (`taoyu.nlp@gmail.com`, `liuqi@cs.hku.hk`…) présentes dans les tâches ;
  - `garnett@wustl.edu` dans `neurips_2026.sty` (le style officiel) et `noreply@anthropic.com` (trailers Co-Authored-By).

  Aucune adresse de Martin ni d'un tiers réel ne figure dans le contenu des fichiers. Les trois « téléphones » détectés sont des décimales de métriques (`0,0732421875`).
- **A5. VPS 37.187.252.136** : **aucune occurrence** dans tout l'historique. Les IP restantes sont 127.0.0.1, 172.23.0.2 (Docker interne) et quelques faux positifs, des numéros de version. Pour l'IP de l'ex-pod 213.181.111.151, voir N2.
- **A6. Autres projets de Martin** : aucune occurrence de Oopercast, Ooper, Astry, ooper.dev ni de clients, dans tout l'historique.
- **A7. Prompts système et transcriptions d'agents** : aucun `system-reminder`, `You are Claude Code` ou `HARNESS MODE`, et aucun contenu de `CLAUDE.md` ou `AGENTS.md` du harnais.
  - Les « system prompt » trouvés sont ceux du modèle Holo étudié.
  - `judge_bench/claude_responses.jsonl` contient des verdicts du vérificateur, pas des conversations.
  - Les dossiers `.claude/` et `.codex/` ne sont pas suivis par git.
- **A8. Taille** : aucun blob ne dépasse 20 Mo. Les plus gros sont `verif_study/attempts.jsonl` (6,9 Mo), `pod_astra/neurons/selected.json` (5,2 Mo) et `moon-leak/frozen/payloads/*.json.gz` (4,7 Mo au plus). `.git` complet pèse 240 Mo, ce qui est acceptable pour GitHub.
- **A9. Captures d'écran** : les 594 blobs PNG uniques (966 fichiers `.png` dans HEAD) sont des captures de VM OSWorld ou MiniWoB, de figures et du duel. Je n'ai trouvé aucune capture d'un autre projet ou du bureau de Martin. Méthode : j'ai trié les chemins par dossier, puis ouvert les captures qui ne viennent pas d'OSWorld (`duel/shots`, `moon-leak`).
  - Les 14 PDF sont des figures et le papier, avec « Anonymous Authors ».
  - Je n'ai pas ouvert un par un les PNG de `screenshot/`, de `verif_study/images` ni de `diagnostic_examples`. Ce sont des sorties automatiques d'OSWorld.

## Addendum : commit `4c8b1ab` (repo-ready, 10:13 UTC, 50 fichiers de synthèse)

Ajouté à la demande de ares après l'audit principal. J'ai scanné le diff complet (6 302 lignes ajoutées) avec les mêmes motifs.

- **OK : `Bearer cog_…` factices.**
  - Les quatre occurrences sont `holo-neurochir/devin/README.md` (« `Authorization: Bearer cog_…` », « clé `cog_…` dans `~/.devin_key` ») et `holo-neurochir/pitch/PITCH.md` (deux lignes « en-tête `Authorization: Bearer cog_…` », « clé de service Devin (`cog_…`) »).
  - Elles sont toutes littéralement `cog_` suivi d'une ellipsis `…`. Ce sont donc des gabarits de documentation : aucune valeur de clé n'y figure.
  - La seule autre chaîne qui ressemble à une clé, `sk-disjoint-from-construction`, est un libellé de split.
- **OK : aucun autre secret.** Pas de `hf_`, `sk-`, `ghp_`, Modal `ak-`/`as-`, `hk-`, `rpa_` ni clé privée.
- **OK : aucune donnée de vie privée nouvelle.**
  - Aucune occurrence de `emilejouannet`, d'IP de pod ou de VPS, d'e-mail, de téléphone, d'Oopercast/Ooper/Astry ni de `to_session`.
  - Le seul nom propre de personne est Esben Kran (Apart Research), cité avec un lien public LessWrong dans `pitch/PITCH.md:124`.
- **À NETTOYER (rattaché à N1) : deux URL `?t=` signées.**
  - `holo-guard-repair.html?t=mxehqaqs…`, que je n'avais pas encore recensée, se trouve dans un des fichiers de synthèse.
  - `holo-pitch-deck.html?t=mxdng2xy…` est dans `pitch/PITCH.md`. Elle était déjà relevée en N1.
  - Toutes deux sont partageables, et chaque jeton est limité à son propre artifact : on peut les garder ou les révoquer côté argos.
- **À NETTOYER (rattaché à N6 et N10) :**
  - `astra-evo/HANDOFF_ARES.md` est un compte rendu de worker à ares, sans secret.
  - `demo_live/CHECKLIST_JOUR_J.md` contient le tunnel `ssh -N -L 8765:127.0.0.1:8765 orbit` (alias d'hôte, sans IP) et le chemin `/home/orbit/.local/bin/claude`.
  - On trouve aussi des chemins `/home/orbit/…` dans les rapports `astra-*`.
- **Verdict.** `4c8b1ab` n'ajoute aucun BLOQUANT.

## Vérification

Un vérificateur indépendant, qui n'a pas écrit ce rapport, a refait la recherche de secrets sur les 3 475 blobs avec ses propres motifs, archives décompressées comprises. Il n'a trouvé ni secret ni donnée privée manquée. Il a aussi recontrôlé les commits, chemins et comptages cités, et j'ai corrigé les chiffres qu'il a trouvés faux.

## Hors périmètre, à surveiller

La copie de travail partagée sur argos contient des fichiers **non suivis**, absents de l'historique et donc non audités ici :
- `holo-neurochir/report/agent_reports/`, `holo-neurochir/report/CONTEXT_2026-11-07.md`, `REDTEAM*.md` ;
- `holo-neurochir/alerts/` (page d'alerte téléphone) ;
- `.claude/`, `.codex/`, `STATUS.md`, `VERIFY_CPU.md`, `devin/`, etc.

Avant tout `git add` de ces chemins après le passage en public, il faut les relire, en particulier `alerts/` et `agent_reports/`.

## Ordre d'action proposé à Martin

1. **Décider B1.** Soit Émile donne son accord, soit on remplace le nom. Le remplacement suppose une réécriture d'historique sur un miroir neuf et la publication d'un **nouveau** dépôt, à cause de la PR #1.
2. **Dans HEAD, en un seul commit normal :** retirer `moon-vision/ARES_ORDERS.json` (N3), `paper/data/local/reports/CONTEXT_2026-11-07.md` ou ses lignes 12, 53-57 et 66-72 (N1, N7), les `.pyc` (N9) et, au choix, les montants (N5).
3. **Côté services, sans toucher au dépôt :** révoquer les artifacts argos signés hors jury (N1), stopper `holo-jury-probe` après le jury (N4), confirmer la terminaison du pod et du volume RunPod (N2), vérifier que l'artifact claude.ai est privé (N8).
4. Basculer la visibilité, ou publier le dépôt nettoyé.
