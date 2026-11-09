# Independent runner review

Reviewed statically on 2026-11-08. No server, GPU, network request, or model call was used.

## Passed

- `WORKFLOW_FREEZE.json` matches the executing runner SHA-256 `36a4d103a3332c22fecceaea259a2ea2725f3d344a3fec91793f2ffe209ff546`, `FROZEN.json` SHA-256 `9bf07af1f630ffbee0f628347270dff9c3abe068aa9fb76c9c8c747e47585839`, and protocol SHA-256 `a01e43eae0e4ea9292af849f02738e856d92fa8f52a06fa69fb8791cb4a47ac6`.
- `run` and `texts` both invoke `check_runner()` before server access. The runner retains the inherited canonical schema/settings/source checks, four frozen seeds, payload SHA checks, no-retry behavior, schema revalidation, denominator retention for errors/invalids/truncations, duplicate-pair rejection, and flush/fsync per completion.
- Frozen payload inspection found all 55 expected payload files and no digest mismatches. The frozen cohort remains 19 `fs+`, 20 `fs-`, 16 `healthy`, with four seeds and 220 GUI draws per arm.
- The analyzer requires exactly 220 unique GUI task/seed rows and exactly three text results for each candidate. The three text calls use canonical T=0, max_tokens=256, thinking-off settings.
- The E025 arm is present as a third candidate root; protocol amendment messages 6520 and 6532 are recorded, and the protocol forbids serving an own baseline. The amendment is frozen before candidate inference.

## Baseline provenance correction

The provenance artifact is at `/tmp/moon-vision/IMPORTED_A.json` (the protocol root), rather than under `runs/A/`. It exists and records the source directory, `rows: 220`, `copied_verbatim: true`, and hashes for the source receipt files. The copied `runs/A/generations.jsonl` SHA-256 is `c7f309a97947452e47a343bb07f429937f200a5159d0868be2aad8d7fb9ad546`, matching the artifact. `analyze.read_arm` independently enforces 220 unique task/seed rows plus frozen row/payload/schema consistency. The previous absent-artifact finding is retracted; no blocking provenance gap remains.

No blocking runner discrepancy was found in the requested static scope.
