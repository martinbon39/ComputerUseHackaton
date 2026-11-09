# Independent check — dose-zero control contrasts

Reviewed `/workspace/astra/moon-leak/control_contrasts.json` read-only after its `PASS` completion. No server, GPU, or generation request was used.

**Pairing and signs are correct.** The ranked pair is `head4_s0` edited versus `random4_s0` control. The raw pair is `raw4_s0` edited versus `random_raw4_s0` control. Every reported contrast is `control − edited`; therefore a positive fs+ answer contrast means the targeted edit suppresses false-success answers more than its random control. Differential selectivity is the fs+ contrast minus the true-finish contrast, so a positive value favors targeted fs+-specific suppression after subtracting the effect on true finishes.

- Ranked: fs+ contrast **−5.26 pp**, 95% task-bootstrap CI **[−15.79, +2.63]**; true-finish contrast **+1.25 pp** **[−5.00, +7.50]**; differential selectivity **−6.51 pp** **[−18.42, +3.88]**. This does not show an advantage for the targeted ranked heads.
- Raw: fs+ contrast **+10.53 pp**, 95% CI **[−3.95, +25.00]**; true-finish contrast **+7.50 pp** **[+1.25, +15.00]**; differential selectivity **+3.03 pp** **[−12.63, +18.75]**. The fs+ point estimate favors the targeted raw edit, but the fs+ and differential-selectivity intervals include zero; the data do not establish a selective advantage over control.

The healthy valid-nonanswer contrast is **−1.56 pp** for ranked and **0.00 pp** for raw, matching the stated sign convention. The file uses 19/20/16 tasks, four seeds averaged within task, 10,000 task-bootstrap replicates, seed 261029609, and records hashes for both scripts, the frozen inputs, all four generation files, audits, run specs, and build specs.

**Verdict:** pairings, arithmetic, sign interpretation, and source binding are correct. The control contrasts provide no statistically resolved targeted fs+-selectivity advantage in either family.
