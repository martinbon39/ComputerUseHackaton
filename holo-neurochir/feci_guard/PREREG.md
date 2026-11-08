# Feci Guard — pre-registration (written 2026-11-08 07:36 UTC, before opening any blind packet or running the reserve)

Frozen verifier: `verifier.py` sha256 e46c7ed34fd4ae46… (prompt, schema, model `sonnet`, 90 s timeout).
Decision rule: refuse an answer iff the verifier returns INCOMPLETE (= at least one requirement visibly "no");
COMPLETE, timeout, CLI error or invalid JSON -> the answer passes. Infeasibility answers are never checked.
Max 2 refusals per episode; the 3rd answer passes unchecked.
Tuning: only the 2 hand-test captures from `~/osw/results_diag` (vlc/386dbd0e false success, vlc/9195653c true success)
were used; both came back COMPLETE (settings not visible on the final screen -> "cannot_tell"). No change after that.

(a) Offline: one verdict per packet item, all 60 written to `offline/verdicts.jsonl` before KEY.json is opened.
    Detection = INCOMPLETE among false successes; false rejection = INCOMPLETE among true successes; Wilson 95 % CI.
    A verifier call with no verdict counts as "passes" (it lets the answer through, as online).
(b) Online: Holo original + Guard on the 45 reserve tasks, same server (orbit :8000), same run_osw arguments
    (max_steps 50, T 0.8, v2, image budget 3). Paired comparison per task against results_confirm_gh_orig_confirm and
    results_val_orig_eager_m40; paired bootstrap 95 % CI (10 000 resamples over tasks). Cost = refusals on tasks the
    original solved.

Addendum 07:38 UTC (still before any packet exists): secondary rule, reported but NOT used online:
"strict" = refuse iff at least one requirement is not "yes" (no or cannot_tell), computed from the same 60 outputs.
The primary (online) rule stays the one above. Note: vlc/9195653c, one of the two hand-test captures, is a reserve
task; no setting was changed after the hand test, so nothing was fitted on it.

Update 07:41 UTC: verifier.py refactored (sha256 d23c7feed1827f3b…): pluggable backend added (GUARD_BACKEND=openai); the claude path keeps the same prompt, schema, flags, model and decision rule; parsing now shares _json_text/_validate with the openai path (same accepted inputs). Frozen v1 copy kept in git history. The 60-item blind packet was cancelled by ares; verif-study measures this verifier on its 268 episodes instead.

Update 07:44 UTC, after the independent code review: verifier.py sha256 0af76fdbacc72317…
(feci_guard.VERIFIER_SHA, also written to meta.json "feci_guard"). Passive prompt, schema, CLI flags and model are
unchanged. Changes: timeout 90 -> 55 s (the duel needs < 60 s; observed latency 7-14 s); the accept/reject rule moved to
feci_guard.check, which now also ENFORCES the registered rule (an INCOMPLETE with no "no" requirement is
"inconsistent" -> accept); the guard checks a FRESH capture from the VM controller (it was checking the cached
post-action frame); new opt-in "active" mode (NEED_CHECK -> the agent is asked for a read-only check action), never
the default.
