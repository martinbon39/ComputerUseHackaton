# Fara beta.5 static behavior audit

PASS for the bounded static audit. No inference, forward call, deployment, reserve episode, or test data was read.

The full artifact contains 51 rows: 48 structured generations and three text health prompts. It uses the exact frozen six-context cohort, seeds 0 through 7, T=.8, top-p=.9, top-k=20, reflection, structured `holo_agent` JSON, and max 3072 tokens. Text uses T=0, thinking disabled, max 256. Identity is Modal account 1, model `Holo-3.1-4B-merge_fara_b050`, root `/models/ckpt/merge_fara_b050`, vLLM 0.23.0. The smoke artifact independently has 3 text + 1 healthy row with zero errors/truncations.

All 51 full rows have zero errors and zero truncations. Counts are fs+ 16/16 `answer`; fs− 14/16 `answer` and 2 `click` non-answers; healthy 0/16 `answer` and 16/16 valid non-answers. The healthy actions are concrete expected interactions: eight `write` actions in the file-manager search field and eight `scroll` actions in the font dropdown. The two fs− non-answers are clicks describing confirmation of the saved `contacts.xlsx` state.

All three text responses are non-empty, stop normally, and coherent for completion verification, Linux `mv` renaming, and atmospheric scattering.

The static result is not an OSWorld score estimate: only two fs+ and two fs− contexts are sampled, and no VM replay was run.

## README audit

No factual CLI or data-policy blocker was found in `/tmp/astra-merge-work/README.md`. The available builder and checker evidence agrees with its claims: `merge.py` and `merge_v1.py` are byte-identical; 723 common tensors plus the explicit Holo `lm_head` account for 724 total; sparse method descriptions match the implementation; and the reserve/test exclusion and static-score caveat match the cohort and reports. README was not edited.
