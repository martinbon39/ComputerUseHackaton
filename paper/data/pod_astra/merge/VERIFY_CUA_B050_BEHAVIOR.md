# Independent behavior audit: CUA beta 0.50

**Verdict: the reported counts are correct.** The files have identical evaluation keys and no errors, truncations, or parse failures. The observed regression is real in these outputs, but it cannot yet be cleanly attributed to the merge because original and candidate ran on different backends (H200 versus H100).

| Label | Candidate answer | Candidate valid action | Original answer | Original valid action |
|---|---:|---:|---:|---:|
| fs+ | 11/16 | 5/16 | 16/16 | 0/16 |
| fs- | 2/16 | 14/16 | 16/16 | 0/16 |
| healthy | 0/16 | 16/16 | 0/16 | 16/16 |

Both files contain 51 rows: 48 screenshot cases and three text prompts. The screenshot design matches exactly: two tasks per label and seeds 0–7 for each task. Every row in both files ended with `finish_reason=stop`; all screenshot outputs parsed; none reported an error or truncation.

The five fs+ non-answers are all well-formed scroll actions on one car-sort task. Each response explicitly recognizes that sorting succeeded and the largest vehicles are already visible, then scrolls to obtain a “complete view.” This is unnecessary continued exploration after adequate completion evidence, not malformed tool use.

The fourteen fs- non-answers are also coherent post-completion verification actions:

- Seven open Files to confirm that `contacts.csv` and `contacts.xlsx` exist after the window title already confirms the conversion.
- Seven select slide 2 to re-check picture placement and underlining after stating that the presentation was completed and saved.

Thus fs- shows a strong “verify once more” tendency. The actions are executable and schema-valid, but conflict with this benchmark's answer-now target. The two fs- answers are seed 5 for the contacts task and seed 7 for the slides task.

All sixteen healthy cases remain valid actions: eight writes and eight scrolls. The three text-only outputs are coherent and on-topic. The candidate's file-renaming answer is shorter than the original but includes an explicit `ls` verification step; its completion-policy answer is generic but adequate; its sky explanation is concise and correct.

Machine-readable evidence is in `VERIFY_CUA_B050_BEHAVIOR.json`. A same-backend rerun is required before making a clean causal claim about the weight merge.
