# linkedin_anim: "Not inside." (25 s silent loop for LinkedIn)

A near-wordless animation of Holo-3.1-4B for a LinkedIn post about the paper *Cogito, Ergo Feci*
(DOI 10.5281/zenodo.24061167).

| File | What |
|---|---|
| `not_here_4x5.mp4` | 1080x1350, 30 fps, 25 s, H.264 High yuv420p, faststart, no audio, loops (first and last frame nearly identical) |
| `not_here_1x1.mp4` | 1080x1080 centre crop of the same video (y offset 110) |
| `linkedin_anim.html` | Self-contained page (three.js, font and data inlined). Opens and plays the loop; `?t=12.5` freezes one time |
| `app.js`, `style.css`, `build.py` | Sources. `python3 build.py` writes the HTML |
| `capture.mjs` | Deterministic frame-by-frame render (`render(t)`, `TOTAL`) piped to ffmpeg |
| `frames.mjs` | Stills at chosen timestamps, for checking |
| `vendor/` | three.js 0.185.1 (MIT), Geist Mono Regular (SIL OFL 1.1) |

Rebuild:
```bash
python3 build.py
export CHROME=~/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome
node capture.mjs $PWD/linkedin_anim.html $PWD/not_here_4x5.mp4 30
ffmpeg -i not_here_4x5.mp4 -vf crop=1080:1080:0:110 -c:v libx264 -preset slow -crf 18 -maxrate 12M -bufsize 24M -pix_fmt yuv420p -movflags +faststart not_here_1x1.mp4
```

## What is real and what is illustrative

- **Real data (the coloured dots and trails).** The 14 matched pairs of false and true "done" steps from the
  imminent-completion analysis: `paper/data/pod_astra/perceive/descriptive_v2.json` (`rows[*].fs_plus` = false
  "done", `rows[*].fs_minus` = true "done"). Paper: `paper/sec/interventions.tex`, subsection `sec:perceive`, and
  the macros `pcMatchN`, `pcTermDiff`, `pcFsPosGt` in `paper/generated/`.
  - Height of a dot at layer 15 = its projection on the layer-15 completion direction (z-scored, direction fitted
    without that task). Dots start at the step before "done" (`previous_z[15]`) and rise to the "done" step
    (`terminal_z[15]`). Both colours rise (14/14 and 14/14); at the "done" step false sits 0.14 SD below true on
    average and above it in 6 of 14 pairs. 3 of the 14 false completions are infeasible tasks, and one false-completion
    task (chrome/9f3f70fc) appears in two pairs (paper, `sec:perceive`).
  - The two horizontal lines are the mean "done" height of each colour.
  - Trails: the same 28 "done" steps, height = `terminal_z[l]` at each of the 32 layers.
  - Horizontal position of each dot or trail is a fixed random slot. It carries no meaning.
- **Illustrative.** The 8x8 grey grids and grey links (the model has 2,560 dimensions per layer), the arc layout,
  the travelling pulses, the viewfinder brackets.

## Captions (all text in the video)

1. 0.0-4.6 s: "Where does an AI agent know it's wrong?"
2. 9.6-13.6 s: "true “done” vs false “done”" (colour key)
3. 13.9-17.0 s: "Not inside."
4. 18.8-21.7 s: "It takes an outside check."
5. End card 21.9-24.3 s: "Cogito, Ergo Feci" / "Holo-3.1-4B · doi 10.5281/zenodo.24061167"

Faithfulness: the paper finds no internal signal that separates false from true "done" beyond episode position.
The completion direction shown fires before both (paper, `sec:perceive`). The external verifier (Feci Guard) detects
45/66 false "done" offline where the agent judging itself is at chance (`jury_kit/replay_guard.py`). The video claims
nothing about weight edits and no online score gain.

LinkedIn practice applied: 4:5 1080x1350 H.264 MP4, a frame that can serve as a thumbnail from t=0 (question plus
network), silent-first captions of 46 px or more (about 15 px on a 360 px-wide phone), text kept out of the top 12 %
and the bottom 20 % (captions span y 176-296 and 950-1071 of 1350), 15-30 s length. Sources: contentin.io/blog/linkedin-video-best-practices (2026-09),
quso.ai/blog/linkedin-video-specs (2026-07), linkedin.com/help/linkedin/answer/a565326 (autoplay is muted).
