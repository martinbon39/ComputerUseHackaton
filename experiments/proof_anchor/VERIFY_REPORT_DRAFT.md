# Independent review of draft report

**RAN / PASSED / CORRECT:** Read-only review found no numerical or statistical interpretation blocker. All 216 numbers in the 72-probe table agree with `RESULT.json` at the displayed precision.

`RESULT_CORE.json` remains unchanged. The current result preserves every original analysis field, with additional raw-metadata comparisons and provenance. Source review confirms the raw comparisons regenerate the same stratified bootstrap draws.

The draft correctly limits the fixed-OOF intervals, selected-winner inference, pooled LOO AUROC, nonconverged MLP fits, oracle power, and causal interpretation of artificial text interventions. Its cohort-confounding statement is supported: writer, OS, and GIMP tasks occur only among true finishes in this sample.

**NOT RUN:** Validation of the ongoing MLP sensitivity; final independent numerical reconstruction of scores and permutation statistics; any refit, optimizer work, or GPU execution.

One publication requirement remains: the draft references `VERIFY_FINAL.md` as existing, but that verdict was not yet present. It must be created and reviewed before this report is treated as final.

Reviewed report SHA256: `472deca721bc725b1321496a49309d420c16f056d53da1d117a0673c3a7ca8e2`.

Reviewed result SHA256: `f1f4e961aa56a533f3d32b8147c8f2b65950efb4f6b2e4f79d4e0c49c9d0ca68`.

Original core SHA256: `80ab8c7ec4b031ea82c339f53294752d84351a3c82673f62c6d7d127023f4398`.

Detailed scope and evidence are in `VERIFY_REPORT_DRAFT.json`. This draft review does not replace the final audit.
