# Modal reference audit

PASS. This is a read-only audit of the existing `Holo-3.1-4B_full` original artifact against `merge_cua_b050_full`; no inference or endpoint call was made.

Both artifacts contain exactly 51 rows: 48 structured rows and three text rows. They use the identical six DIAG contexts and seeds 0 through 7, with row identity hash `29ac4a34f41bf52bc4650285bfb73ef12ba1941777bca30c1b0bf7a67d601a39`. Both summaries record T=0.8, top-p=.9, top-k=20, reflection enabled, structured `holo_agent` JSON, max 3072; text health uses T=0, reflection disabled, max 256.

The original is Modal account 1 (`emilejouannet`), vLLM 0.23.0, served as `Holo-3.1-4B-modal-orig`, root `Hcompany/Holo-3.1-4B`. Its 16 fs+ rows are answer 16/16, 16 fs− rows answer 16/16, and 16 healthy rows valid non-answer 16/16. It has zero invalid/truncated outputs. The original revision `8c88265a5a159bfd1492db9243733dd2e6e04a6e` was separately verified by ares/modal-serve.

The candidate is Modal account 2 (`martinbon39`), vLLM 0.23.0, served as `Holo-3.1-4B-merge_cua_b050`, root `/models/ckpt/merge_cua_b050`. Its fs+ result is 11/16 answer and 5/16 valid non-answer; fs− is 2/16 answer and 14/16 valid non-answer; healthy is 16/16 valid non-answer. It also has zero invalid/truncated outputs.

All three text prompts are non-empty and stop normally for both models. Their content is coherent for completion verification, Linux `mv` renaming, and atmospheric scattering.

The backend-class difference is resolved: both are Modal H100/vLLM 0.23.0 routes. They are different accounts/containers, so this establishes backend-class comparability, not exact stochastic determinism.
