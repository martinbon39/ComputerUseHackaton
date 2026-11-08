# Benchmark wall: the 3-minute submission video

A deterministic HTML page (`template.html`, `render(t)`) shows 16 real OSWorld sessions replayed ×20, the Feci Guard
verdict recorded on each final screen, and the measured repairs (Holo-3.1, escalation to Holo4). It then shows the real totals, and
an infra screen, the two-arm conclusion, the paper cover, and the 11:00 UTC online-eval duel (`~/osw/duels/20261108-110023_libreoffice_calc_1de60575-bb6e-4c3d-9e6a`).
The tiles are chosen examples. The numbers in the totals card are the aggregates, each with its source file.

Build (it ran in `/tmp/wall`, a tmpfs; the paths in the scripts point there and at `~/osw`):
1. `prep.py` reads the tile sources and writes `tiles.json` and the 640×360 frames. Detection tiles come from
   `verif_study/manifest.json` + `judge_bench/claude_responses.jsonl`, the repair tile from
   `~/osw/feci_demo/calc_1de60575`, and the escalation tiles from `~/osw/rescue_bench/guard/*_k0`.
2. `prepduel.py <duel id>` builds `duel.json` from a recorded duel.
3. `vo/gen.sh` generates the narration (voix-martin, English). `vo/subs.json` holds the written subtitles.
4. `build.py` writes the timeline from the voice durations and inlines everything into one HTML file (`--audio` embeds the narration).
5. `mix.py` places each line at its time. `capture.mjs page audio out.mp4` takes a 25 fps headless capture and pipes it to ffmpeg (1080p).
