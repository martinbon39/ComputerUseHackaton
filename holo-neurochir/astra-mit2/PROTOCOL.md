# astra-mit2 — conditional verification circuit

Owner: astra-mit2. Started 2026-11-07 22:14 UTC. Deadline 2026-11-08 08:00 UTC.

New mechanism: replace a few low-contribution SwiGLU neurons with an analytic input detector and residual writer. The fixed weights act at every token, including prefill. No gradient, optimizer, or training loop. Captures and algebra derive weights; generated behavior decides acceptance.

The first detector targets imminent end-of-reasoning in terminal trajectories. A two-neuron saturated gate uses the existing bias-free architecture: with a measured approximately constant projection c(x), its response is c(x)[SiLU(k(d(x)-a c(x)))-SiLU(k(d(x)-b c(x)))]/[k(b-a)]. Incoming gate rows implement the two thresholds, up rows implement c, and opposite outgoing columns write the chosen verification vector. Off-distribution activation and repeated reactivation are failure modes, not assumed away. Alternative detector can use a conclusion-onset state; no unconditional previous CAA sweep will be repeated.

Writer candidates: actual successful evidence-seeking action states contrasted with terminal states; or a late-layer lexical reinspection branch (Wait/But) derived analytically from the model's own output rows. Neither is claimed to encode verification until complete generated actions are independently reviewed. Stop-word suppression alone is not success.

Splits: manifest.initial.json frozen before model use; original six pilot contexts are screening only, prior six construction contexts are design, nine new task IDs are final heldout and their content stays unread until a patch is frozen. Canonical confirmation task identifiers, inherited from an existing manifest, are excluded from all construction and screening. Never open split_test.json. Additional successful verification examples must exclude every screen, heldout and canonical reserve task.

Budget: at most 40 lots, each reserved durably before model load. A lot is one fixed, bounded capture job (at most 64 sequences) or one fixed generation arm (at most 48 sequences). Every resumption charges a lot. Failed model attempts remain charged. Record actual forward calls and generated tokens separately. No simultaneous owned GPU processes. All runs enter through gpu_slot.sh from the owned directory, torch threads=2, allocator<=13 GB, observed process abort>=14.5 GB, STOP flag honored. Production ports 8000, 8011, 8012 untouched.

Screening uses thinking, production schema, T=.8/top_p=.9/top_k=20/max3072, paired seeds 4000..4003. Baseline regenerated to avoid inherited-engine differences. At most two mechanism rounds, at most six fixed candidates per round. Stop after two complete rounds with no improvement in relevant fs+ action rate under protection, or resource/deadline/budget limit. Do not claim results for incomplete panels.

Admission: false terminal answers must fall by >=50% relative and >=25 points absolute; at least half of all fs+ generations must perform a relevant verification/correction/continuation action. True finishes and healthy useful actions decline by <=10 points relative to paired original; invalid outputs may not increase by >10 points. At n=8, one regression already exceeds 10 points. Semantic usefulness requires a concrete goal-related observation/action, not checking vocabulary or merely a valid non-answer.

After screen admission, freeze exact delta spec/hash, run paired original/patch on the nine heldout tasks (k=4), equal-norm random writer control, and three text prompts at T=0. Only a candidate meeting these gates is sent to ares as CANDIDAT. Small sample uncertainty and online-unverified status must be explicit. A fresh agent audits numerical results, circuit implementation, data separation, and action usefulness before completion. Rejected specs stay marked experimental.

Prior evidence read in full by two bounded readers: JOURNAL.md, paper/main.tex including generated Table2/macros, and all eight named pod reports. Historical negative arms are not repeated. Source for the separate-path analogy: https://rikiyat.github.io/blog/weight-space-programming/ (Experiment4); it does not establish success on Holo.
