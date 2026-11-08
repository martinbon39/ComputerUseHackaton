# Live duel: original Holo-3.1-4B vs the merged model, same OSWorld task, same time

A local page on orbit with two OSWorld VMs side by side. On the left is the original Holo-3.1-4B; on the right is the
merged model (merge_cua_b050). Both play the same task at the same time with the exact `run_holo` harness: v2 prompt,
T=0.8, top_p 0.9, image budget 3, a 60 s settle, the final answer sent as DONE/FAIL, then the official evaluator.

The page shows, for each side:
- a live screenshot of the VM, every 2 s;
- the step number and the clock;
- the model's note, reasoning and action at each step;
- at the end, the official verdict, set against what the agent claimed. A claimed "done" that the evaluator scores 0
  is labelled FAUX SUCCÈS.

There is one STOP button per agent and a global STOP. A stop ends the episode at once and closes the VM. Every duel
is recorded in `~/osw/duels/<id>/{meta.json,left,right}`: `events.jsonl` plus the JPEG frames. The same page replays
any recorded duel at real speed (×2, ×4 and ×8 are also available).

```
bash duel.sh serve [pod|modal]   # tmux duel_server, devcap 1G -> http://127.0.0.1:8765/
bash duel.sh list                # recorded duels and verdicts
bash duel.sh replay <id|last>    # -> http://127.0.0.1:8765/?replay=<id>
bash duel.sh stop                # STOP all
```

Public access: `bash duel.sh tunnel` (cloudflared quick tunnel, tmux `duel_tunnel`) prints an https URL. Everyone gets
the page, the replays and the live state, read-only. Starting or stopping VMs needs the key in `~/.duel_key` (umask
077): open the page once with `?k=<key>`. The server stores it as an HttpOnly SameSite=Strict cookie and redirects to
drop it from the address bar. Any POST without it, or from another site, gets 403. Still one duel at a time.

## Server presets
- `pod` uses H200 on the pod. The original is served on pod 8000 (orbit 8000); the merged model is served on pod 8011
  (orbit 8001), from `/dev/shm/release_merge_cua_b050` via `serve_patched.sh`.
- `modal` uses H100s. The original is `Holo-3.1-4B-modal-orig` on account 1; the merged model is
  `Holo-3.1-4B-merge_cua_b050` on account 2. The Modal key is read from `~/.holo_modal_key` inside the VM login, and
  never appears on a command line.

## Guards
- A duel starts only if at least 15 GB of RAM is available (two 5 GB VMs plus the 5 GB VPS floor), and only one duel
  runs at a time.
- The live thread and the agent take turns on the VM's `/screenshot`. Concurrent calls return broken PNGs: both sides
  of the first test crashed that way.

## Demo tasks
These are tasks where, in recorded runs, the original claimed a false "done" and the merged model succeeded:
`libreoffice_impress/b8adbc24`, `chrome/9f935cce`, `os/bedcedc4`. Results vary from run to run because sampling
uses T=0.8; the page says so.
