# Infrastructure recovery and ares order

Original stage 0 retained 10 complete records before /workspace reached its disk quota. The process exited; at least one further forward may have run without a persisted record. Preserve the original run and never infer missing observations. Recovery is a separate run, capped at 12 forwards, with repeated controls, a second fs+ pair and a true finish. Ares cleared 12 GB of his own closed checkpoints. Large tensors/checkpoints now live under /dev/shm/astra-broad; keep a local durable copy.

Ares message 6015 redirects the first candidate family from MLP layers 12–31 to both residual writers on layers 12–23: down_proj plus full-attention o_proj or DeltaNet out_proj. Capture writer inputs and assert their outputs equal the mixer outputs. Uniformly distribute the donor final-residual displacement over the 24 writers. This is a simultaneous local linear approximation, not a guarantee of final-residual equality after nonlinear propagation.

Ares initially requests two or three additional fs+ ceiling contexts and one true finish. Message 6037 narrows the immediate prerequisite to the second fs+ and one true finish. Both are complete, so keep the original two-pair construction manifest frozen. A third pair remains an optional future diagnostic, not part of this first candidate.

The source data had passed current disjointness in independent review, but construction code omitted some general checks. Enforce canonical reserve membership equality, unique evaluation tasks, per-label counts, donor bounds and recorded-tool equality in code. No test/reserve episode is opened by these checks.

Per ares message 6006, the rationalization direction is a possible conditioning key. Do not assume that direction is causal; use it only if its train-only provenance and selectivity can be checked. The first closed-form pilot uses only the frozen fs+ keys and explicit preserved-key projection.
