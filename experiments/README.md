# Experiments

One folder per study. Each holds its protocol or pre-registration (when one was written), its code, its report and
the result files it produced. The status and source-of-truth file of every folder are in
[`docs/REPO_MAP.md`](../docs/REPO_MAP.md). Many reports are in French, the working language of the project.

| Folder | Question | Paper |
|---|---|---|
| [`miniwob_pilot/`](miniwob_pilot/) | How does Holo-3.1-0.8B fail on MiniWoB++? (pilot, loops) | §5, §8, appendix |
| [`verif_study/`](verif_study/) | Can Holo-3.1-4B judge its own final screen? 268 labelled episodes | §7 |
| [`judge_bench/`](judge_bench/) | Three judges on the same 268 screens | §7 |
| [`constraint_drop/`](constraint_drop/) | Does the agent name an unmet requirement before answering? (pre-registered) | §9 |
| [`text_signal/`](text_signal/) | Do text or sampling signals detect a false success better than the step number? | §6 |
| [`proof_anchor/`](proof_anchor/) | How much of the tool call rests on the note and thought written before it? | §6 |
| [`rescue_bench/`](rescue_bench/) | Guard refusal then escalation to Holo4-27B, in replay (pre-registered) | §7 |
| [`online_guard/`](online_guard/) | The guarded agent online on the 120-task test split (pre-registered) | §7 |
| [`weight_edits/`](weight_edits/) | Seventeen weight and activation edit families | §6, appendix on edits |
