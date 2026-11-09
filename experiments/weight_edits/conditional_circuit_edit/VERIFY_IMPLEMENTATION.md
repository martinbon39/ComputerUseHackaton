# Independent implementation verification

Date: 2026-11-07 UTC. Scope: `experiment.py`, `build_circuit.py`, and
`screen_supervisor.py`; static review plus CPU-only tensor checks. No model
forward and no GPU use.

## Verdict

**Circuit implementation: PASS. Screening supervisor: BLOCK until the completed
baseline file is frozen and attested.**

The gate/up/down edits implement the intended two-neuron circuit. For neurons
`i,j`, the installed rows/columns are

`gate = [k(d-ac), k(d-bc)]`, `up = [c,c]`, and
`down = [alpha*u/(k(b-a)), -alpha*u/(k(b-a))]`.

Therefore their residual write is

`alpha*u*c(x)*(SiLU(k(d(x)-a*c(x)))-SiLU(k(d(x)-b*c(x))))/(k(b-a))`,

which matches the protocol. The same row/column addition and BF16 cast order is
used by the runtime installer and `make_patched_ckpt.py`.

On the actual `semantic_l19_d1` and `semantic_l19_d2` artifacts, an independent
CPU reconstruction found exact BF16 agreement for all gate and down entries.
Three of 5,120 up entries differ from the directly rounded analytic target by
only `1.907e-6`, due to float32 subtraction/addition cancellation; runtime and
checkpoint compilation still agree exactly with the stored delta semantics.
This difference is immaterial.

`CircuitTrace` selects the two intermediate activations with shape `[tokens,2]`,
projects the corresponding post-edit down columns onto the unit writer, and
computes the selected circuit's scalar residual write correctly. The independent
CPU identity check differed from a direct BF16 down projection by at most
`0.00198` (dose 1) and `0.00397` (dose 2), versus peak writes of `10.71` and
`21.43`. This is BF16 output rounding, not an indexing or algebra error.

The measured realized coefficients also match the intended detector: the four
terminal construction states are `0.789` to `0.984`; all fourteen negative
terminal coefficients have magnitude at most `0.0588`; sampled prefill states
have magnitude at most `0.0256`. The dose-1 and dose-2 candidates use the same
detector and scale only the writer amplitude.

The lexical `Wait` writer's multiplication by `(1 + norm.weight)` is consistent
with the installed `Qwen3_5RMSNorm`, whose forward pass multiplies normalized
states by exactly `(1 + weight)`.

The supervisor's early-rejection arithmetic is correct for an 8/8/8 panel:
observed fs+ answers above the admissible maximum cannot recover; true-finish and
healthy checks compute the best possible final count as eight minus failures
already observed. Semantic usefulness remains a later human audit, as required.

## Blocking issue

`screen_supervisor.py` trusts mutable `baseline_screen.jsonl`. It checks only 24
rows and 8 examples per label; it does not attest the file hash, the complete
`(row_index,sample)` grid, seeds 4000--4003, or the frozen sampling dictionary.
The baseline was still incomplete during this audit, so its final hash could not
yet be fixed. After it completes, freeze its SHA-256 and make the supervisor
verify that digest plus the row/sample/seed/sampling invariants before deriving
any rejection bound. Until then, the mathematical gate is based on a mutable
reference and should not launch a candidate.

Operationally, an early rejection writes the global `STOP` file and no code here
clears it. A later candidate will be refused until the owner deliberately removes
that marker after recording the rejected lot; this does not alter the rejected
result but must be part of the run procedure.
