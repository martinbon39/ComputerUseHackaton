# 2-minute demo (holo-neurochir/video_demo/feci-guard-demo-2min.mp4)

1. `rec.mjs` (live attempt) and `rec2.mjs` (replay fallback) drive the real pages in Playwright and record them: the cockpit, then a click on "Watch the duel", then the duel page.
   The duel key is read from `~/.duel_key` and used only in a separate context that is not recorded. The recorded context
   receives only the cookie.
   - The live duel `20261108-115902` did not make the arc: left (Holo alone) scored 1, right (Guard) scored 0 after 1 refusal.
   - The video therefore shows the recorded 11:00 UTC duel `20261108-110023`, marked REPLAY.
2. `capseg.mjs` re-renders segments of the benchmark wall (`../template.html`) without subtitles.
3. `assemble.py` places the narration (Higgsfield seed_audio, preset voice) and writes `subs.ass` (subtitles + speed markers). It then builds the concat list.
   Final encode: `ffmpeg -f concat -i concat.txt -i vo.wav -vf subtitles=subs.ass …`.
