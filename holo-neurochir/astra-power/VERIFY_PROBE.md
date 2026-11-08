# Independent probe verification

Verifier: `/root/probe_audit`, 2026-11-08 06:59 UTC. Read-only review of the runner; this verification record is the only file written. No real cohort or generation records were read, no GPU was used, and no network/API request was made.

Verified final `probe.py` SHA-256: `bdc74083eb51eb9983d82733cf223167e66a06921eb7616c6a7bc738956c4409`.

## Verdict

- **RAN:** CPU compilation/import with the existing `/home/orbit/osw/venv/bin/python`, thread-limit and retry checks, mock canonical-call inspection, an entirely in-memory four-seed execution, and final-version identity/resume-guard inspection.
- **PASSED:** All executed assertions. No blocking runner defect remains for the planned dedicated `power_A` server and the expected B/C/D roots.
- **CORRECT:** The wrapper preserves the canonical generation settings, uses frozen content-addressed payloads across arms, pairs the same four seeds, validates the exact schema, records truncations and transport failures, and saves each completed response with flush/fsync. This verdict covers runner mechanics only.
- **NOT RUN:** Live endpoint/model identity checks, checkpoint hashes, cohort eligibility/labels/split exclusions, actual payload preparation from trajectories, inference, completeness of measured arms, or statistical analysis. Those require separate evidence.

## Checks and evidence

The imported canonical call was exercised against a mock completion client. Observed request settings were temperature 0.8, top_p 0.9, top_k 20, max_tokens 3072, reasoning_effort medium, enable_thinking true, exact imported SCHEMA, and the supplied seed. The real client was instantiated without an HTTP call and had max_retries=0. Torch and all three BLAS/OpenMP thread limits were 2.

The in-memory run used four synthetic seeds and returned one valid answer, one schema-invalid answer-shaped object, one length-truncated unparseable response, and one transport error. It wrote four records, called fsync four times, preserved the payload digest and seed identity, rejected the invalid answer as an answer, retained truncation/error evidence, and made zero additional calls on resume. A modified decompressed payload was rejected by the SHA-256 check. All file operations in this simulation used memory-backed objects.

The simulation ran on initial runner hash `e262e9d2a0279b9bf0e87783151dfaf228a003128b16e252247af02f443983f2`. The maker then added exact model-root checks and validation of old records before resume. The final version was compiled/imported again, and its new assertions were independently checked: arm/model, valid seed, complete row equality, payload digest, and exact server root. These changes do not alter the simulated generation or output-classification path.

Static inspection confirms prepare() requires four distinct seeds and distinct task IDs, reconstructs contexts with image_budget=3, checks the resulting image count, freezes the schema and source hashes, and stores each compressed payload under its uncompressed SHA-256. run() rechecks schema/source/payload hashes and uses the same frozen messages for every arm. Source or schema changes after freezing abort rather than silently changing a comparison.

The original port-8000 alias is `Holo-3.1-4B`, whereas this runner requires `power_A`. The maker confirmed A will be served as a dedicated `power_A` copy using the same serving flags as the other arms; that resolves the alias mismatch. The final original root is pinned to revision `8c88265a5a159bfd1492db9243733dd2e6e04a6e`.

Transport errors also have invalid=true because they contain no schema-valid action. Downstream reporting must describe these categories as overlapping or compute a separate nontransport-invalid count. Truncation is an independent flag. The primary answer denominator should retain all planned/measured draws and must not silently drop errors or invalids.
