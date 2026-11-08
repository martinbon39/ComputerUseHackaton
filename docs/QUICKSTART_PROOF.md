# Quickstart proof

Every command of the README quickstart, run on 2026-11-08 at 11:07 UTC in a **fresh clone** of `main` at commit `37b00e0`,
with a **fresh virtual environment** (nothing installed), Python 3.14.4, Linux x86-64, CPU only. Every command exited 0, and
`git status` in the clone was still clean afterwards. The same quickstart runs in GitHub Actions with the runner's
preinstalled Python 3, whenever the jury kit, the Guard code or its data change:
[.github/workflows/quickstart.yml](../.github/workflows/quickstart.yml).

```bash
git clone https://github.com/martinbon39/ComputerUseHackaton && cd ComputerUseHackaton
python3 -m venv venv && . venv/bin/activate
```

## (a) `python3 jury_kit/verify_results.py`, exit 0
The columns "92.5 vs 89.3" are sums of per-task scores over the n tasks.
```
== PRIMARY VERDICT (rule fixed before reading results): merge vs Modal-served original, Modal vs Modal ==
merge_cua_b050 vs orig_modal, reserve + test               n=165    92.5 vs   89.3  delta +1.94 pt  CI95 [ -4.3 ;  +8.0]  18 wins / 14 losses
  test only (120)                                          n=120    70.5 vs   70.3  delta +0.18 pt  CI95 [ -6.5 ;  +7.5]  11 wins / 10 losses
  reserve only (45)                                        n=45     22.0 vs   19.0  delta +6.64 pt  CI95 [ -6.7 ; +22.1]  7 wins / 4 losses

== Other arms and noise references ==
AlphaEdit broad_residual_p100 vs orig_modal, reserve       n=45     20.0 vs   19.0  delta +2.22 pt  CI95 [-13.3 ; +17.8]  7 wins / 6 losses
ExPO lambda=1.25 vs orig_pod, test                         n=120    70.3 vs   72.1  delta -1.50 pt  CI95 [ -8.9 ;  +5.7]  11 wins / 12 losses
merge_cua_b050 vs orig_pod, test                           n=120    70.5 vs   72.1  delta -1.33 pt  CI95 [ -8.9 ;  +6.4]  12 wins / 13 losses
-- noise: the same original model served by two backends --
orig_pod vs orig_modal, test                               n=120    72.1 vs   70.3  delta +1.51 pt  CI95 [ -4.5 ;  +7.6]  9 wins / 8 losses
orig_pod vs orig_modal, reserve                            n=45     21.0 vs   19.0  delta +4.44 pt  CI95 [ -6.7 ; +17.8]  5 wins / 3 losses

checks against the published values:
  OK  merge_cua_b050 vs orig_modal, reserve + test: +1.94 (expected +1.94, n=165)
  OK    test only (120): +0.18 (expected +0.18, n=120)
  OK    reserve only (45): +6.64 (expected +6.64, n=45)

Verdict rule: a gain is claimed only if the CI95 lower bound is > 0. Lower bound = -4.3 pt -> NO DETECTABLE GAIN
```

## (b) `python3 jury_kit/replay_guard.py --show 2`, exit 0
```
--- refusal 1: chrome/47543840
TASK: On the current website, show me the cars available for pickup at Boston Logan Intl Airport from the 10th to the 11th of next month, sorted by the number of seats to find the largest capacity.
  [v] Pickup location is Boston Logan Intl Airport: Pick-Up shows Boston Logan Intl Airport, BOS.
  [x] Dates are the 10th to 11th of next month (December, since today is Nov 8): Pick-up Tue, Nov 10 and return Wed, Nov 11 are shown. These are in the current month, not December.
  [v] Results sorted by number of seats, largest first: Sort by: Number of Seats (High to Low). The 12-Passenger Van is listed first, then the 7-seat Minivan.
  [v] Car list is displayed: Vehicle list with 21 vehicles is shown.
FEEDBACK TO THE AGENT: Verifier: requirement 'Rental dates must be the 10th to 11th of next month (December), not November.' is not satisfied on screen: The screen shows Pick-Up Tue, Nov 10, 12:00 PM and Return Wed, Nov 11, 12:00 PM. The current date is Nov 8, so next month is December. Click Modify Rental Details, set pick-up to Dec 10 and return to Dec 11 at Boston Logan, search again, and keep the sort on Number of Seats (High to Low). Continue the task.

--- refusal 2: chrome/9f3f70fc
TASK: Browse the list of women's Nike jerseys over $60.
  [v] Viewing Nike women's jerseys list: Nike FR search 'maillot femme (1115)' results page.
  [x] Price filter over $60 applied (or list limited to items > 60): URL has only q=maillot femme, no price filter; visible prices include 42,99 € (below 60); no price filter visible.
  [x] Results visible to browse: Page scrolled to footer; product grid is mostly empty/not visible.
FEEDBACK TO THE AGENT: Verifier: requirement 'Filter the women's jerseys to prices over $60 (about 60 €+)' is not satisfied on screen: URL is only q=maillot femme with no price filter, and a 42,99 € item is shown; the view is scrolled to the footer. Scroll up, open the Prix filter in the sidebar, select the over-60 range (or sort by price), and show the filtered product list. Continue the task.

Feci Guard replay: frozen feci_guard.check on 268 recorded final screens, recorded Claude Sonnet verdicts
  verifier sha 0af76fdb   decision kinds: {'complete': 202, 'incomplete': 66}
  false successes rejected (detection) : 45/66 = 68 %  Wilson95 [56-78]
  true successes rejected (false alarm): 21/202 = 10 %  Wilson95 [7-15]
  gap detection - false alarm         : +58 pts  task-bootstrap95 [+41, +74]
  OK  detected: 45 (expected 45)
  OK  false_success: 66 (expected 66)
  OK  wrongly_rejected: 21 (expected 21)
  OK  true_success: 202 (expected 202)
  OK  verifier_sha: 0af76fdb (expected 0af76fdb)
Matches the published judge-bench numbers.
```

## (b2) `python3 jury_kit/recount_judges.py`, exit 0
```
manifest 268 268 90
A t0 lines 268 unique 268 in manifest 268
B lines 268 268 True
C lines 268 268 True
A FS 35 66 0.5303 [0.4116, 0.6457] TS 97 202 0.4802 [0.4123, 0.5488] invalid 3 3 gap 0.0501
  groups 90 boot CI -0.1341 0.2288
B FS 31 66 0.4697 [0.3543, 0.5884] TS 63 202 0.3119 [0.252, 0.3788] invalid 1 4 gap 0.1578
  groups 90 boot CI -0.0191 0.3388
C FS 45 66 0.6818 [0.5621, 0.7815] TS 21 202 0.104 [0.069, 0.1537] invalid 0 0 gap 0.5779
  groups 90 boot CI 0.4067 0.7366

judge                         detected      wrongly rejected   gap CI95 (task bootstrap, pts)
OK  Holo-3.1-4B (self-judge)    35/66         97/202             [-13, +23]  published [-13, +23]
OK  Holo4-27B                   31/66         63/202             [-2, +34]  published [-3, +33]
OK  Claude Sonnet (Feci Guard)  45/66         21/202             [+41, +74]  published [+41, +74]
268 episodes from 90 tasks; the bootstrap resamples tasks. Counts must match exactly; the CI bounds within 2 pts
(this recount uses its own seed, the published CIs come from judge_bench/analyze.py).
```

## (b3) `python3 jury_kit/verify_online_guard.py`, exit 0
```
Online Feci Guard test, OSWorld test split, paired by task (bootstrap 10,000, seed 0)
  tasks: 120, excluded: 0
  false 'done' rate : original 22.5 % -> Guard 10.8 %   diff -11.7 pts CI95 [-19.2, -4.2]
  OSWorld score     : original 58.6 -> Guard 60.2   diff +1.6 pts CI95 [-4.4, +7.7]
  repaired B=8  true successes lost C=4  net=+4  false done avoided E=19
  criterion 1 (false done down): True   criterion 2 (score gain): False -> NO SCORE GAIN CLAIMED   rule 5 useful: True
Matches ONLINE_GUARD_RESULT.json exactly.
```

## Links: `python3 jury_kit/check_links.py`, exit 0
```
109 relative links checked in 6 documents, 0 broken
```

## All of it: `bash jury_kit/quickstart.sh`, exit 0
```
== (a) OSWorld paired comparisons, recomputed from per-task scores ==
== PRIMARY VERDICT (rule fixed before reading results): merge vs Modal-served original, Modal vs Modal ==
merge_cua_b050 vs orig_modal, reserve + test               n=165    92.5 vs   89.3  delta +1.94 pt  CI95 [ -4.3 ;  +8.0]  18 wins / 14 losses
  test only (120)                                          n=120    70.5 vs   70.3  delta +0.18 pt  CI95 [ -6.5 ;  +7.5]  11 wins / 10 losses
  reserve only (45)                                        n=45     22.0 vs   19.0  delta +6.64 pt  CI95 [ -6.7 ; +22.1]  7 wins / 4 losses

== Other arms and noise references ==
AlphaEdit broad_residual_p100 vs orig_modal, reserve       n=45     20.0 vs   19.0  delta +2.22 pt  CI95 [-13.3 ; +17.8]  7 wins / 6 losses
ExPO lambda=1.25 vs orig_pod, test                         n=120    70.3 vs   72.1  delta -1.50 pt  CI95 [ -8.9 ;  +5.7]  11 wins / 12 losses
merge_cua_b050 vs orig_pod, test                           n=120    70.5 vs   72.1  delta -1.33 pt  CI95 [ -8.9 ;  +6.4]  12 wins / 13 losses
-- noise: the same original model served by two backends --
orig_pod vs orig_modal, test                               n=120    72.1 vs   70.3  delta +1.51 pt  CI95 [ -4.5 ;  +7.6]  9 wins / 8 losses
orig_pod vs orig_modal, reserve                            n=45     21.0 vs   19.0  delta +4.44 pt  CI95 [ -6.7 ; +17.8]  5 wins / 3 losses

checks against the published values:
  OK  merge_cua_b050 vs orig_modal, reserve + test: +1.94 (expected +1.94, n=165)
  OK    test only (120): +0.18 (expected +0.18, n=120)
  OK    reserve only (45): +6.64 (expected +6.64, n=45)

Verdict rule: a gain is claimed only if the CI95 lower bound is > 0. Lower bound = -4.3 pt -> NO DETECTABLE GAIN

== (b) Feci Guard replayed on 268 recorded episodes (frozen decision code, recorded verdicts) ==
--- refusal 1: chrome/47543840
TASK: On the current website, show me the cars available for pickup at Boston Logan Intl Airport from the 10th to the 11th of next month, sorted by the number of seats to find the largest capacity.
  [v] Pickup location is Boston Logan Intl Airport: Pick-Up shows Boston Logan Intl Airport, BOS.
  [x] Dates are the 10th to 11th of next month (December, since today is Nov 8): Pick-up Tue, Nov 10 and return Wed, Nov 11 are shown. These are in the current month, not December.
  [v] Results sorted by number of seats, largest first: Sort by: Number of Seats (High to Low). The 12-Passenger Van is listed first, then the 7-seat Minivan.
  [v] Car list is displayed: Vehicle list with 21 vehicles is shown.
FEEDBACK TO THE AGENT: Verifier: requirement 'Rental dates must be the 10th to 11th of next month (December), not November.' is not satisfied on screen: The screen shows Pick-Up Tue, Nov 10, 12:00 PM and Return Wed, Nov 11, 12:00 PM. The current date is Nov 8, so next month is December. Click Modify Rental Details, set pick-up to Dec 10 and return to Dec 11 at Boston Logan, search again, and keep the sort on Number of Seats (High to Low). Continue the task.

Feci Guard replay: frozen feci_guard.check on 268 recorded final screens, recorded Claude Sonnet verdicts
  verifier sha 0af76fdb   decision kinds: {'complete': 202, 'incomplete': 66}
  false successes rejected (detection) : 45/66 = 68 %  Wilson95 [56-78]
  true successes rejected (false alarm): 21/202 = 10 %  Wilson95 [7-15]
  gap detection - false alarm         : +58 pts  task-bootstrap95 [+41, +74]
  OK  detected: 45 (expected 45)
  OK  false_success: 66 (expected 66)
  OK  wrongly_rejected: 21 (expected 21)
  OK  true_success: 202 (expected 202)
  OK  verifier_sha: 0af76fdb (expected 0af76fdb)
Matches the published judge-bench numbers.

== (b2) the three judges recounted from their raw responses (README rows 2 and 7) ==
judge                         detected      wrongly rejected   gap CI95 (task bootstrap, pts)
OK  Holo-3.1-4B (self-judge)    35/66         97/202             [-13, +23]  published [-13, +23]
OK  Holo4-27B                   31/66         63/202             [-2, +34]  published [-3, +33]
OK  Claude Sonnet (Feci Guard)  45/66         21/202             [+41, +74]  published [+41, +74]
268 episodes from 90 tasks; the bootstrap resamples tasks. Counts must match exactly; the CI bounds within 2 pts
(this recount uses its own seed, the published CIs come from judge_bench/analyze.py).

== (b3) online Feci Guard test, 120 OSWorld tasks (README row 10) ==
Online Feci Guard test, OSWorld test split, paired by task (bootstrap 10,000, seed 0)
  tasks: 120, excluded: 0
  false 'done' rate : original 22.5 % -> Guard 10.8 %   diff -11.7 pts CI95 [-19.2, -4.2]
  OSWorld score     : original 58.6 -> Guard 60.2   diff +1.6 pts CI95 [-4.4, +7.7]
  repaired B=8  true successes lost C=4  net=+4  false done avoided E=19
  criterion 1 (false done down): True   criterion 2 (score gain): False -> NO SCORE GAIN CLAIMED   rule 5 useful: True
Matches ONLINE_GUARD_RESULT.json exactly.

== (c) demo replay pages ==
holo-neurochir/demo_live/repair_calc.html: 1.0 MB, 8 embedded screenshots, 0 external scripts: Feci Guard refuses a false done, the agent repairs
holo-neurochir/demo_faux_fini/demo_faux_fini.html: 3.1 MB, 47 embedded screenshots, 0 external scripts: one task, the original's false done next to the merged agent

QUICKSTART OK: (a) and (b) match the published numbers, (c) the two demo pages are ready to open in a browser.
```

## Level 2
Earlier fresh clone, commit `6bb899f`, about 10:05 UTC.
`python3 jury_kit/guard_live.py` uses the `claude` CLI (Claude Code, logged in) for fresh verifier calls. Both live
decisions matched the recorded ones. The `--api` path (Anthropic key through the OpenAI-compatible endpoint) was
**not run**, because no key was on the machine.

Default episode (a false success), exit 0:
```
episode  : diag1__chrome__47543840-672a-467d-80df-8f7c3b9788c9
label    : false_success (official OSWorld evaluator)
TASK     : On the current website, show me the cars available for pickup at Boston Logan Intl Airport from the 10th to the 11th of next month, sorted by the number of seats to find the largest capacity.
live     : REJECT (incomplete)  [claude:sonnet, 7.6 s, error=None]
  [v] Pickup location is Boston Logan Intl Airport: Pick-Up shows Boston Logan Intl Airport, BOS.
  [x] Dates are the 10th to the 11th of NEXT month (today is Nov 8, so Dec 10 to Dec 11): The page shows Tue, Nov 10, 12:00 PM to Wed, Nov 11, 12:00 PM. That is the current month, not next month.
  [v] Results sorted by number of seats, largest first: Sort by: Number of Seats (High to Low). The 12-Passenger Van is listed first.
  [v] Car list is displayed: The list shows All Vehicles (21), starting with the 12-Passenger Van and the Minivan.
feedback : Verifier: requirement 'The rental dates must be the 10th to the 11th of next month (Dec 10 to Dec 11), not Nov 10 to Nov 11.' is not satisfied on screen: The pick-up is Tue, Nov 10 and the return is Wed, Nov 11. Today is Nov 8, so these dates fall in the current month. Click Modify Rental Details, set pickup to Dec 10 and return to Dec 11 at Boston Logan, then search again. Keep the sort on Number of Seats (High to Low). Continue the task.
recorded : INCOMPLETE -> reject   same decision: True
```

`--episode diag1__chrome__0d8b7de3-e8de-4d86-b9fd-dd2dce58a217` (a true success), exit 0:
```
episode  : diag1__chrome__0d8b7de3-e8de-4d86-b9fd-dd2dce58a217
label    : true_success (official OSWorld evaluator)
TASK     : Browse the natural products database.
live     : ACCEPT (complete)  [claude:sonnet, 4.7 s, error=None]
  [v] Browser shows a natural products database: Chrome is on drugs.com/npc/ with the heading 'Natural Product Information (Consumer)'.
  [v] Browsing content (A-Z listing) is visible: The 'Browse A-Z' letter links and the product listings (5-Hydroxytryptophan, Acai, Aortic Extract) are visible.
recorded : COMPLETE -> accept   same decision: True
```

## Oldest supported Python
Fresh clone at `6bb899f`, Python 3.9.25 (`uv run --python 3.9 --no-project python ...`): `verify_results.py` exited 0,
`replay_guard.py` exited 0, and `guard_live.py --list` printed 268 episodes.
