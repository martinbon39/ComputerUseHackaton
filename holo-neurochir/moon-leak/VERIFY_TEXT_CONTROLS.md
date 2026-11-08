# Independent text-control review — final 6/6

Review date: 2026-11-08 UTC. This is a read-only qualitative review of three deterministic, temperature-zero text controls per arm. No server, GPU, generation request, GUI trajectory, or online action was used.

## Coverage

Reviewed original A plus all six completed candidate arms:

| Arm | Text rows | File SHA-256 |
|---|---:|---|
| original A | 3 | `2e4eff640cff84a836242e7e52c04534104944c0dd05e6745895d6715872ca71` |
| `head4_s05` | 3 | `153c45891387300e1843fd5adc433f9c93e462fc59c413871dc102176295af63` |
| `head4_s0` | 3 | `f6972b88571c3bd08f7fa5739c69e3039e2a45b3b4386628c867d1fa4c7bd5c5` |
| `raw4_s05` | 3 | `2148d8b67ffd425a75448bd624555fec7b8e98ca41e65e3ad1eef3b6ed40f3ff` |
| `raw4_s0` | 3 | `8a7eb6dcd397909bc6ebcb3b2279f68bff7502ce5f6af754d6cc7b5ad9aebfdf` |
| `random4_s0` | 3 | `172962604d85fa8f63915ab01ff7e423088eb82349bd7a7d6d5493c7364220eb` |
| `random_raw4_s0` | 3 | `5a8f0ac5096d03ce5c5f1d19ff712d05ac0dc16d9d2d2e34865c190ce09b6558` |

All reviewed records use the exact prompts and seed 0. None contains an API error, truncation, non-empty reasoning leakage, repetition, or malformed output.

## Results

| Arm | French → English | `17 × 19` | Three-step Linux rename |
|---|---|---|---|
| original A | Incorrect: `The file has been successfully opened.` | Correct: `323` | Correct |
| `head4_s05` | Same incorrect output as A | Same correct output as A | Same correct output as A |
| `head4_s0` | Same incorrect output as A | Same correct output as A | Correct three steps using `mv old.txt new.txt`, then `ls` |
| `raw4_s05` | Same incorrect output as A | Same correct output as A | Correct three steps using `mv old.txt new.txt`, then `ls` |
| `raw4_s0` | Incorrect variant: `"The file has been successfully processed."` | Same correct output as A | Correct three steps using `mv old.txt new.txt`, then `ls new.txt` |
| `random4_s0` | Same incorrect variant as `raw4_s0` | Same correct output as A | Correct three steps using `mv old.txt new.txt` |
| `random_raw4_s0` | Same incorrect output as A | Same correct output as A | Correct three steps using `mv old.txt new.txt`, then `ls` |

The expected translation of `Le dossier a été renommé avec succès.` is “The folder was successfully renamed.” Original A already changes both the object and action by producing “file … opened.” The `head4_s05`, `head4_s0`, and `raw4_s05` arms reproduce that baseline error exactly, including token IDs and output length.

`raw4_s0` and `random4_s0` instead produce the same “file … processed” variant. It remains an absolute translation error and does not introduce a new failure category beyond the baseline translation defect. These two arms have different layer distributions and are not an experimental pair.

Within the actual pairs, `head4_s0` produces the baseline “opened” error while `random4_s0` produces “processed”; `raw4_s0` produces “processed” while `random_raw4_s0` produces the baseline “opened” error. These are deterministic output divergences on the translation prompt, but every version is semantically incorrect. This smoke test therefore establishes different wording, not a targeted-versus-control quality advantage.

All six arms return the exact arithmetic answer `323`. Every Linux response follows the requested three-step format, includes the correct `mv old.txt new.txt` command, and remains short and practical. Wording and verification commands vary slightly; none of those variants is a functional defect.

## Final verdict

**RAN:** field-level comparison of prompt, seed, reasoning, content, rendered text, token IDs, output length, finish reason, stop reason, truncation, and error status; manual semantic and format review of all 21 records, including A.

**PASSED:** arithmetic and Linux rename controls for all six candidate arms. No formatting degeneration, reasoning leakage, truncation, request error, repetition, or incoherent response was found.

**CORRECT:** the French translation control fails absolutely in A and every candidate. Four candidate arms preserve A's wrong “opened” answer; two non-paired dose-zero arms share the wrong “processed” answer. Both experimental pairs differ in wording while remaining wrong on both sides, so no text-quality advantage is established by this prompt.

**NOT RUN:** online evaluation, GUI trajectory review, and any broader text benchmark.

These three prompts are a narrow smoke check. They do not establish general language quality, instruction following, reasoning health, or absence of degeneration outside the tested prompts.
