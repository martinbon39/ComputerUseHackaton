# Feci Guard — results

## Verifier, hand tests (2026-11-08)
| capture | truth | passive (Claude Sonnet) | active (Claude Sonnet) |
|---|---|---|---|
| vlc/386dbd0e final screen (global hotkey) | false success | COMPLETE (setting not visible: cannot_tell) | NEED_CHECK: open Tools > Preferences > Hotkeys |
| vlc/9195653c final screen (max volume 200 %) | true success | COMPLETE | not run |
Latency 6.5-10.6 s, about $0.04 per check. A single final screen cannot show a saved setting, which is why the
active mode exists.

## End-to-end, 1 task on an orbit VM (guard on, passive, Claude Sonnet)
`libreoffice_impress/550ce7e7` (strike through lines 1 and 2). The original recorded a false success on this task in
results_diag. Journal: `smoke/impress_550ce7e7_guard.md`.
- Step 29: the agent answered "done". The guard REFUSED it: "the strike-through stops at 'Requ'; 'ests.' is plain
  text". The evidence was correct, as the screenshot shows.
- Steps 30-33: the agent followed the feedback (Home/Shift+End, strike-through, Ctrl+S).
- Step 34: answered again. COMPLETE, so the answer passed.
- The official evaluator still scored **0**. It compares the saved .pptx with a reference file, and the remaining
  difference is not visible on screen (the final screenshot shows both lines fully struck through). This is the
  limit of a screen-only verifier: the guard fixed what can be seen, and the evaluator checks what cannot.

## Offline (Claude vs Holo as judge on the same 268 episodes)
Measured by verif-study with `feci_guard.check` (frozen verifier, see PREREG.md). Pending.

## Repair (replayed feasible false successes, without vs with guard feedback)
With online-eval. Pending.
