# Independent CPU verification: broad terminal detector

Date: 2026-11-07 UTC. Scope: `derive_broad.py`, `detector_broad.json`, `detector_broad.npz`, `capture01` metadata/captures, and the `build_circuit.py --bundle` path. No GPU/model execution, screen or heldout access, new examples, or change to `experiment.py`.

## Verdict and blocking issues

No blocking construction or artifact-identity error was found. Independent recomputation reproduces the stored P, N, B, c, d, a, and b arrays at layers 19 and 31. The leave-one-task-out masks remove every P, N, and B row for the held task, including both members of each verification/verified-done pair.

One result must remain explicit: layer 31 leave-one-task-out has **2 of 10 positives below a**, 2 between a and b, and 6 above b. This differs from any initial summary implying that every held-positive clears the threshold. The two below-threshold cases are:

- `libreoffice_writer/ecc2413d-8a48-416e-a3a2-d30106ca36cb`: ratio 0.560899 versus a 0.567368;
- `os/13584542-872b-42d8-b299-866967b5c3ef`: ratio 0.623413 versus a 0.642605.

Layer 19 leave-one-task-out has 0 below a, 4 between a and b, and 6 above b.

## Populations and alignment

The 18 existing captures contain exactly:

| Population | Labels | Count | Distinct tasks |
|---|---|---:|---:|
| P, terminal conclusions | 2 `fs+`, 2 `fs-`, 6 `verified_done` | 10 | 10 |
| N, non-conclusions | 2 `healthy`, 6 `verification` | 8 | 8 |
| Union | all above | 18 | 12 |

For every capture, `tail_state_offset == 1`, `len(X) == len(ids) + 1`, and there is exactly one `</think>` token. The metadata alignment is `X[j] predicts ids[j]; X[j+1] is the state after ids[j]`. Accordingly, `derive_broad.py:136-149` selects `X[end]`, the state **predicting** `</think>`. It is an imminent-termination state, not the post-`</think>` state `X[end+1]`. This agrees with the stored `terminal_index` description and the circuit’s intended trigger point.

At each target layer, B contains 637 states: up to 20 evenly spaced tail/reflection states per capture excluding distance <=3 from `end`, plus every fourth state from the 64-state prefill sample. The extracted arrays exactly equal the NPZ arrays:

- P shape `(10, 2560)`;
- N shape `(8, 2560)`;
- B shape `(637, 2560)`.

## Leave-one-task-out exclusions

`derive_broad.py:175-245` forms folds from the union of P-task and N-task IDs. For each held task it independently applies `task != held_task` to P, N, and B before fitting c/d or thresholds. Independent reconstruction reproduced every stored training count, held count, a, b, held-positive ratio, and held-negative ratio in all 12 folds at both layers.

Six tasks contain a paired `verification` N state and `verified_done` P state. In every corresponding fold, held counts are exactly P=1 and N=1, and all B states from both captures disappear as well:

| Held paired task | Held B rows |
|---|---:|
| `multi_apps/2373b66a-092d-44cb-bfd7-82e86e7a3b4d` | 70 |
| `multi_apps/26660ad1-6ebb-4f59-8cba-a8432dfe8d38` | 71 |
| `multi_apps/2c9fc0de-3ee7-45e1-a5df-c86206ad78b5` | 70 |
| `multi_apps/8df7e444-8e06-4f93-8a1a-c5c974269d82` | 71 |
| `multi_apps/d68204bf-11c1-4b13-b48b-d303c73d4bf6` | 71 |
| `os/13584542-872b-42d8-b299-866967b5c3ef` | 71 |

Thus the paired end state cannot leak through N or B when its verification episode is held out.

## Detector algebra

`inverse_moment(B, v)` is the Woodbury form of a ridge-regularized inverse second moment applied to v. The constant direction c is normalized so `mean(B) @ c = 1`. Measured constant-coordinate ranges are:

| Layer | P: x·c | N: x·c | B: x·c |
|---:|---|---|---|
| 19 | 0.8893–0.9674 | 0.8239–0.9452 | 0.9822–1.0110 |
| 31 | 0.7648–0.8791 | 0.7100–0.8146 | 0.9859–1.0134 |

The d direction is the ridge inverse centered-background moment applied to `mean(P)-mean(N)`, scaled by the raw P/N projection difference, then shifted by a multiple of c. For every x with nonzero x·c, the last subtraction shifts the ratio `(x·d)/(x·c)` by the same scalar. It does not make the final raw means `mean(N)·d=0` and `mean(P)·d=1` unless mean x·c is exactly one in those populations; the stored artifact does not claim otherwise. The actual final raw projection means are -0.0446/0.9754 at layer 19 and -0.1108/0.9113 at layer 31, while the mean ratios are -0.0502/1.0340 and -0.1491/1.1109 respectively.

Threshold construction is exactly:

`a = max(max(N ratio) + 0.1, quantile_0.999(B ratio) + 0.1)` and `b = a + 0.25`.

Independent values match the NPZ and JSON exactly:

| Layer | a | b |
|---:|---:|---:|
| 19 | 0.6217787870805422 | 0.8717787870805422 |
| 31 | 0.6522134293714460 | 0.9022134293714460 |

## Meaning of `window_between_a_b`

The two-neuron SwiGLU circuit uses gate rows `k(d-a c)` and `k(d-b c)`, identical up rows c, and opposite down columns `+/- alpha*u/[k(b-a)]`. Its normalized writer coefficient is

`g(x) = (x·c) [SiLU(k(x·d-a x·c)) - SiLU(k(x·d-b x·c))] / [k(b-a)]`.

Writing `r=(x·d)/(x·c)`, the interval a <= r <= b is the transition region. For r>b, both SiLU inputs enter their linear regime and their difference approaches `k(b-a)(x·c)`, so `g(x)` approaches `(x·c)^2`: the active plateau. Therefore a positive above b is **saturated/active, not missed**. The `positive_inside` statistic counts transition-window examples only; it is not recall.

Exact positive categories are:

| Layer/evaluation | Below a | Between a,b | Above b |
|---|---:|---:|---:|
| 19, full fit | 0 | 2 | 8 |
| 19, leave-one-task-out | 0 | 4 | 6 |
| 31, full fit | 0 | 1 | 9 |
| 31, leave-one-task-out | 2 | 2 | 6 |

For the actual k=48 BF16-built candidates, full-fit examples above b have writer coefficients 0.828–0.938 at layer 19 and 0.583–0.785 at layer 31, consistent with the `(x·c)^2` plateau. The only full-fit transition examples have coefficients 0.757–0.797 at layer 19 and 0.298 at layer 31. No full-fit positive is below a. The two layer-31 failures described above occur only under leave-one-task-out refits and should not be hidden by the window statistic.

## Hashes and artifact identity

Every hash recorded in `detector_broad.json.capture01_sha256` matches the current file in `capture01`, including all 18 NPZ captures, metadata, token map, and weights. Key current hashes are:

- `derive_broad.py`: `d076636aed177c3615a358ebc0640854be0fe7abc444c3af512177f555d8f174`;
- `detector_broad.json`: `892031e2937fe7c7435eb9529d1a9d9f3021ba6825e71985c23169b841677848`;
- `detector_broad.npz`: `1102c997c6e7f32211d5c9a525e10aa68411a9b3178b04f165e141e9d3df3dc4`;
- `build_circuit.py`: `c75cf703d93b96785248f3feef988ab045b53765c944d65677b82c8786659610`;
- `capture01/metadata.json`: `aa8caa3b0b9a5b596b47795491d7e60307d0b853d29b9840e6d15cb638decacf`;
- `capture01/token_map.json`: `01662067e01731b5641fd8122420f1572fec81faa31dad8de50dd25b58866fc3`.

The JSON does not embed the derive-script hash or NPZ hash. Their coupling is nevertheless independently established here by exact recomputation of all NPZ arrays and JSON counts/statistics from the hash-attested captures.

## Builder `--bundle` path

`build_circuit.py:23-38` accepts an alternate bundle, retrieves `detector__{c,d,P,N,B}`, and recomputes a/b with the same threshold rule. It then constructs the two rows/columns at lines 42-43 and 71. It does not alter `experiment.py`.

For the two already-built broad candidates, the c/d arrays stored in `delta.npz` are exact float32 copies of the corresponding `detector_broad.npz` arrays, and spec thresholds exactly match the broad bundle:

- `broad_l19_d1`: spec SHA `3043795a8d9f9b0e94a392b14b151f85d84e6e5d5f9498d95d9a11b53a1a6976`; delta SHA `079b64a5675a8a7eb1646d08b522b6c0120145c3818024c0cc767a9554c08e73`;
- `broad_lexical_l31_d025`: spec SHA `53d9ff0f50f4aebada666600969ebc0f5005a36d9fd94b046ee7449e37bc4c6b`; delta SHA `a988f3d5206ecc076cab58ca9cfcd7dba29926ea0e476f3185f7dacfba9461a6`.

Those hashes agree with each candidate’s `algebra.json`, so the frozen existing artifacts have no detector-identity ambiguity. The CLI bundle path is intentionally not inserted into the already-hashed spec. The current builder now writes a separate `provenance.json` for every future candidate (`build_circuit.py:112-117`) containing all CLI arguments, resolved detector-bundle path and SHA-256, builder SHA-256, and capture metadata/weights hashes. The two existing broad candidates predate that addition and have no sidecar; their exact embedded c/d, thresholds, and artifact hashes provide the identity evidence above without changing their frozen specs or deltas.

This audit validates construction and stored numerical evidence only. It does not establish behavior under generation; no GPU diagnostic or behavioral output was inspected.
