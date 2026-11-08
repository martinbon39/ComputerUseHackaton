# CUA beta.25 static behavior audit

PASS for the bounded static audit. No inference, forward call, deployment, reserve episode, or test data was read.

The full artifact contains 51 rows: 48 structured generations and three text health prompts. It uses the exact frozen six-context cohort, seeds 0 through 7, T=.8, top-p=.9, top-k=20, reflection, structured `holo_agent` JSON, and max 3072 tokens. Text uses T=0, thinking disabled, max 256. Identity is Modal account 1, model `Holo-3.1-4B-merge_cua_b025`, root `/models/ckpt/merge_cua_b025`, vLLM 0.23.0. The smoke artifact independently has 3 text + 1 healthy row with zero errors/truncations.

All 51 full rows have zero errors and zero truncations. Counts are fs+ 15/16 `answer` and 1 non-answer; fs− 11/16 `answer` and 5 non-answer; healthy 0/16 `answer` and 16/16 valid non-answer. The observed non-answers are concrete actions: one `scroll` on the car-results fs+ context; `click` actions in two fs− contexts; and `write`/`scroll` actions in the two healthy contexts. The healthy actions remain on the expected file-manager search and font-dropdown interactions.

All three text responses are non-empty, stop normally, and coherent for completion verification, Linux `mv` renaming, and atmospheric scattering.

The static result is not an OSWorld score estimate: only two fs+ and two fs− contexts are sampled, and no VM replay was run. It establishes behavior on the frozen screening contexts only.
