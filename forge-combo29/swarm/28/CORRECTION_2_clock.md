# CORRECTION 2 — S-F2, S-F6, S-F9 re-checked for the iteration-granularity confound

**One line of this file is itself withdrawn.** Its S-F9 paragraph claimed 2 of 40 `movestogo 1`
searches exceeded the engine's hard plan, and called that "the only place the engine breaks a bound it
set itself". `REPORT_job4.md` (S-F14) re-measured 300 clock searches and shows the engine's own `time`
never exceeds hard: the wall excess is <=1.2 ms of pipe latency. The paragraph below is corrected in
place, and the finding line in FINDINGS.md carries the withdrawal.

Seat 16's confound, applied to the three remaining clock findings. The rule from Correction 1: **the
stop is the plan; the engine's reported `time` is the last completed iteration, which sits below it.**
So every claim must name which quantity it measures, and every plan must be the ENGINE's, not my own.

Summary of what survives:

| finding | what I claimed | what is true after the re-check | status |
|---|---|---|---|
| S-F2 | 41 % of 1 s-clock searches run past `wtime/30+winc` (43.3 ms), largest 201 ms | The engine exceeded **my invented** 43.3 ms in 82/200 searches but its own soft plan (52 ms) in 54/200, and its own HARD plan (260 ms) in **0/200**. "Over budget" was about my yardstick, not the engine's. | **restated, narrower** |
| S-F6 | `wtime 1600 winc 1000` → 604 ms vs `wtime 2600 winc 0` → 92 ms (0.15x) | Reproduces and is **stronger** than I said: 556 vs 101 ms (0.18x) at total 2600, and the gap is a PLAN difference (soft 822 vs 117 ms), not an iteration artefact. Both sides' achieved times track their plans. | **STANDS, and is about the plan** |
| S-F9 | at `movestogo 1` the engine uses 32 % of the clock = 65 % of its own soft plan | Achieved 323 ms, plan soft 495 ms — but the achieved/last-info gap is only 1 ms (323 vs 322), so here the search genuinely stops early instead of at its plan. That is **different from the movetime case**, where achieved = plan. | **STANDS, with a corrected mechanism** |

## S-F2 — restated, because 43.3 ms was my number, not the engine's
`sf2_recount.py`, pasted (`sf2_recount_out.txt`), same raw files:

| case | n | median wall | over my wtime/30+winc | over engine SOFT | over engine HARD | median vs soft | median vs hard |
|---|---|---|---|---|---|---|---|
| wtime 1000 winc 10 (job1/outA/wt1000.txt) | 200 | 38.2 | 82 | 54 | 0 | 0.74 | 0.15 |
| wtime 10000 winc 100 (job1/outA/wt10000.txt) | 200 | 322.5 | 54 | 33 | 0 | 0.61 | 0.12 |
| wtime 100 winc 10 (job2/out/w100_i10.tsv) | 40 | 10.1 | 10 | 15 | 0 | 0.91 | 0.19 |

So my original "41 % run past the budget, largest 201 ms" was measuring the engine against a rule I
invented. Against the engine's OWN plan, it exceeded its soft limit 54 times and its hard limit **never**,
and its median sat at 74 % of soft. In all three configurations the median is BELOW soft, so the engine
is not over-spending on average; it is completing an iteration that crosses soft, which is ordinary
iterative deepening.

## S-F6 — stands, and the confound is not its cause
`sf6_recheck.py`, pasted (`sf6_recheck_out.txt`), 24 positions per cell, both sides measured the same way:

| total clock | side | wtime | winc | plan soft | plan hard | achieved median | last-info median | attained/plan | last depth (mode) |
|---|---|---|---|---|---|---|---|---|---|
| 1200 | A inc | 200 | 1000 | 114 | 114 | 92.4 | 81 | 0.81 | d13 |
| 1200 | B clock | 1200 | 0 | 54 | 270 | 56.5 | 54 | 1.05 | d12 |
| 1800 | A inc | 800 | 1000 | 474 | 474 | 353.9 | 318 | 0.75 | d16 |
| 1800 | B clock | 1800 | 0 | 81 | 405 | 79.3 | 72 | 0.98 | d13 |
| 2600 | A inc | 1600 | 1000 | 822 | 954 | 556.4 | 526 | 0.68 | d18 |
| 2600 | B clock | 2600 | 0 | 117 | 585 | 101.3 | 94 | 0.87 | d13 |

At the same total 2600 ms the increment side gets 556 ms and the clock side 101 ms — **0.18x**, the same
direction and similar size to my original 0.15x. Crucially the PLANS differ (soft 822 vs 117 ms) in
exactly the same direction, so this is a planning difference, not an iteration artefact. Both sides
attain 0.68-1.05 of their own plan, i.e. the achieved times track the plans as they should.
**S-F6 is a claim about the PLAN, and the plan is what is wrong: the hard limit never includes the
increment (`clock_plan.hpp:41`, `available = time - overhead`).**

A bug in my own tool, found and fixed while doing this: my first `plan()` in `sf6_recheck.py` omitted the
`if (soft > hard) soft = hard` clamp on `clock_plan.hpp:47` and printed "soft 190 / hard 114" for
`wtime 200 winc 1000` — soft above hard, a plan the engine never computes. The cell table in
`sf6_recheck_out.txt` is from the CORRECTED function. That clamp is itself part of S-F6: with a large
increment and a small clock the engine lowers soft to the time-only hard limit, which is the mechanism.

## S-F9 — stands, but the mechanism I implied was wrong
`clock_with_plan.py`, pasted (`clock_with_plan_out.txt`), from the existing job 3 raw files:

| cell | n | plan soft | plan hard | achieved (wall) median | last-info median | last depth (mode) | over SOFT | over HARD |
|---|---|---|---|---|---|---|---|---|
| mtg1 | 40 | 495 | 792 | 323.0 | 322 | d- | 6 | 2 |
| mtg2 | 40 | 330 | 792 | 234.8 | 241 | d- | 11 | 0 |
| mtg40 | 40 | 24 | 96 | 20.4 | 20 | d- | 16 | 0 |
| mtg50 | 40 | 19 | 76 | 16.3 | 16 | d- | 17 | 0 |
| mtg51 | 40 | 19 | 76 | 16.4 | 16 | d- | 17 | 0 |

At `movestogo 1` the MEDIANS of achieved and reported time are 1 ms apart (323.0 vs 322.0), unlike the
movetime cells where they were 10-70 ms apart. **Per search they are not 1 ms apart:** 38 of 40 rows have
a 0-1 ms gap, but two rows have a 379 ms gap (wall 792.7 with reported `time` 413, and wall 792.7 with
reported 414). The median agreement is therefore a statement about the TYPICAL search, and those two tail
searches are the movetime pattern showing through: the last completed iteration ended at 413 ms and the
search ran on to the 792 ms hard stop without finishing another one. The honest form is: **typically the
mtg1 search stops near its soft plan and reports the same number; on 2 of 40 it ran on to the hard stop and
reported an iteration 379 ms earlier.** My "achieved equals reported within 1 ms" was true only of the
median, and is corrected here. S-F9's numbers stand, and "stopping at 65 % of its own soft plan" is a
target undershoot rather than an iteration artefact: 6 of 40 searches exceeded soft.

**Beyond my original:** 2 of 40 `movestogo 1` searches appeared to exceed the engine's HARD plan
(792 ms). **This part of Correction 2 is WITHDRAWN — see `REPORT_job4.md` and S-F14.** A 300-search
re-measurement across five clock configurations shows the engine's own reported `time` never exceeds its
hard plan (max engine-time minus hard = 0 in every cell); what exceeded hard was my WALL measurement, by
+0.8 ms at `movestogo 1` and +1.2 ms at `movetime 500`, i.e. pipe latency. So the honest statement is:
**the engine does not break the hard bound it sets itself.** The "over wtime" count I originally reported
was 0 for the boring reason that the 1000 ms clock was never reached.

## Note on the last-depth column
`clock_with_plan.py` prints `d-` for the job 2 and job 3 files because those harnesses did not record the
last completed depth (job 1 and the correction sweep do). That is a gap in my raw data, not a zero: it
means for jobs 2 and 3 I can compare ACHIEVED against PLAN but not the attained depth. Stated rather
than papered over.

## Prediction score (`prediction_check2_out.txt`)

| id | measurement | measured | expected | verdict |
|---|---|---|---|---|
| Q1 | S-F2 median below engine soft 52 | 38.2 | <52 | SURVIVES |
| Q2 | S-F2 count over engine soft 52 (< 40) | 54 | <40 | **REFUTED** |
| Q3 | S-F2 largest below hard 260 | 201.0 | <=260 | SURVIVES |
| Q6 | S-F9 mtg1 median below soft 495 and above 200 | 323.0 | 200..495 | SURVIVES |
| Q7 | S-F9 achieved/plan in 0.4..1.0 | 0.65 | 0.4..1.0 | SURVIVES |

Q2 was refuted: I predicted fewer than 40 searches over the engine's 52 ms soft limit and 54 exceeded it.
That is the honest core of S-F2 after the correction — the engine crosses its soft target 27 % of the
time, which is normal for iterative deepening, and my original "41 % over budget" counted the wrong
threshold. Q4/Q5/Q8 also survived (arithmetic shown in the script's own output).

## Process state for every search here

All of these searches ran in one long-lived process per cell with `ucinewgame` + `isready` before each
`go`. Verified equivalent to a fresh process per search by `job4/state_check.py` (identical nodes and
depth), so the state assumption behind these tables holds. `Clear Hash` was never used as a cold restore.

## What I did NOT do
- Did not record last completed depth for job 2 or job 3; that data does not exist in those raw files.
- Did not re-run job 3; the re-check used the committed raw files and a recomputed plan.
- No sanitizer.

## What I am NOT sure about
- Whether the 2 wall-clock reads just over hard at `movestogo 1` are pure pipe latency or include a tiny
  real overshoot. Job 4 settles the question for the engine's own `time` (never over hard) and shows the
  wall excess is ≤1.2 ms, so the remaining uncertainty is sub-millisecond and does not affect any claim.
- Why clock searches stop near their soft plan while movetime searches stop at their hard plan (ratio
  1.00). The difference is consistent across every cell I have, so it is real; the code path behind it is
  not something I traced.
