# Selective RegMean — work in progress

Started 2026-11-08 02:19 UTC. Holo snapshot 8c88265a5a159bfd1492db9243733dd2e6e04a6e.

Only static checkpoint weights may change. No gradients, adapters, prompts or production harness changes. The user-prescribed gates supersede the earlier stricter fleet gate: fs+ answer reduction >=25 percentage points; true-finish answer reduction <=30 points; zero invalid outputs; healthy text. Online success remains a separate outcome.

First finding: broad's cached construction contains two fs+ tasks, one of which is the explicitly excluded chrome/480bcfea@4. One positive task cannot support grouped cross-validation. Additional DIAG construction contexts are therefore needed before a separability claim. Broad's six evaluation tasks stay outside all construction. Reserved IDs are filtered using broad's existing exclusion manifest; neither the reserve file nor test split is opened.

Capture positions: last input token and end of recorded thinking, both before the JSON note. Tool-name-prefix activations are excluded from fitting because note and thought already verbalize the decision. End-of-thinking activations can nevertheless encode a decision already reached during reasoning; results must distinguish both positions.

Budget and stop: first overlap report before 03:04 UTC; first complete checkpoint target before 03:49 UTC. At most 64 new capture forwards, one capture recovery, two learned candidate mechanisms and one matched random control for any admitted mechanism. No parameter search on the six evaluation contexts. Stop after two candidate mechanisms without meeting the gate, two consecutive intervals without measurable progress, fleet STOP, or the 90-minute checkpoint deadline. Log all failures and incomplete calls. Evaluate original and candidate with common seeds 7100–7107, vLLM 0.23, T=.8, top_p=.9, top_k=20, thinking and exact schema, plus three deterministic text controls.

Infrastructure: initial pull was blocked by pre-existing shared modifications; fetch verified HEAD equals origin/main. Other agents' files remain read-only. Every numerical process uses two CPU threads. GPU jobs use the fleet semaphore and bounded timeouts.

Verification pending: source identities, replay fidelity, task separation, overlap/CV, mathematical solve, exhaustive tensors, and independent behavioral audit.
