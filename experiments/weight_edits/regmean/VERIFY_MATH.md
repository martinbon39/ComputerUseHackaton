# Independent selective RegMean math audit

**Verdict:** math artifact **PASS**. Behavioral efficacy **NOT RUN**. Checkpoint **NOT BUILT** by this audit. The reviewed output is suitable only as a research candidate pending the separate exhaustive checkpoint verifier and behavioral gates.

Reviewed files:

- `derive.py` — SHA-256 `b899ad2d032e5807d6257df40f12401410a0f8adb8e8ba36f4a36f173dd1f374`
- `build.py` — SHA-256 `3157e231f3c96aaa8aae7cb58cd29af68112fe1ed7039a5aef74855d1aac1824`

The local and pod copies were byte-identical at review time.

## Mathematical result

Let

\[
\Delta=\tfrac12(W_{CUA}-W_{Qwen}),\qquad X=[F,T,G].
\]

The implementation constructs

\[
W^*=W_H+E,
\qquad
E=\Delta FF^T(XX^T+\epsilon I)^{-1}.
\]

This is the centered-ridge solution. It preserves the Holo mapping on the orthogonal complement of the construction activation span in exact arithmetic.

The code uses the exact dual solve

\[
J=[I;0;0],\quad
C=(X^TX+\epsilon I)^{-1}J,\quad
Y=XC,\quad
E=(\Delta F)Y^T,
\]

so it never materializes or inverts a writer-width square matrix. Each activation block is divided by the square root of its column count, making the three covariance terms stratum means. The frozen ridge grid is `0.01, 0.1, 1.0`, with

\[
\epsilon=\alpha\,\mathrm{tr}(X^TX)/d.
\]

## Independent CPU verification

A deterministic float64 toy problem used `d=17`, output width `11`, and block sizes `3/4/2`. Across all three ridge values:

- maximum dual-versus-dense relative error: `1.88e-14`
- maximum normal-equation relative error: `4.11e-16`
- maximum nullspace update norm: `3.56e-16`
- maximum Holo nullspace-preservation relative error: `2.29e-16`
- maximum solver-reported residual: `4.32e-16`

## CV and leakage review

`derive.py` uses only frozen construction rows. The six evaluation contexts are not loaded. Each fold excludes its held-out rows from F/T/G construction. Generic text anchors occur only in the training healthy block and are omitted from held-out healthy scoring.

For false-success rows, the normalized loss is

\[
\|EX-\Delta X\|^2/\|\Delta X\|^2.
\]

For true-finish and healthy rows, it is

\[
\|EX\|^2/\|\Delta X\|^2.
\]

The three terms are summed and averaged equally over the 24 writers and inherited folds. `W_H` has exact objective `1`; the unrestricted donor has exact objective `2`. The lowest-cost alpha is selected, with exact ties choosing the stronger ridge. This is a frozen research ranking, not an admission test and not evidence of behavioral success.

## Build review and limits

The builder edits exactly the 24 declared residual writers in layers 12–23. It adds the requested FP64 update to Holo, casts once to the stored dtype, preserves all other tensors from Holo, and records factor provenance and update diagnostics.

Exact nullspace preservation applies to the requested FP64 update. BF16 rounding can add a small off-subspace component, which the build manifest measures through quantization error. The post-build verifier still needs to check every tensor, retained-tensor identity, factor provenance, file hashes, config and processor loading. Behavioral efficacy and online success remain untested.
