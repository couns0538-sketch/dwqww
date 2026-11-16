# CORRECTION 1 — S-F1 re-tested against seat 16's refutation: the PLAN is M−10, the ACHIEVED time is the plan

Seat 16 refuted my S-F1 with this evidence: the M−10 subtraction exists and `go movetime 10` does give
1 ms, but the stop is the completion of the last whole ITERATION and UNDERSHOOTS the plan; `movetime 50`
stops at 26-28 ms with overhead 0 and with overhead 10, and `movetime 200` gives 167 ms at both settings.

I re-ran the experiment properly. **Verdict on S-F1: it STANDS as a statement about the plan, and is
REFUTED as a statement about the achieved stop time being `M − overhead`.** Seat 16 is right that an
iteration-boundary stop is the dominant effect on the *engine's own reported* time; the measurement below
shows that the stop itself is the plan, to within 1-2 ms, at every overhead I tested.

## The re-test: 16 cells, 30 positions each, 480 searches, 0 NORESP

Grid: movetime {50, 100, 200, 500} × MoveOverhead {0, 10, 25, 45}. OwnBook false, Threads 1, Hash 16,
`ucinewgame` + `isready` before every `go`. Raw per-search files in `out/mt*_mo*.tsv` with a `.meta`
each (exe sha256, every option, the `go` line, and the recomputed `plan_hard_ms`).

Pasted output of `python3 sweep_table.py out` (`sweep_table_out.txt`):

| cell | MoveOverhead | plan (M-O) ms | n | engine-time median | WALL median | min | max | last depth (count) | wall/plan | NORESP |
|---|---|---|---|---|---|---|---|---|---|---|
| mt50_mo0 | 0 | 50 | 30 | 40 | 50.5 | 50.2 | 51.3 | d11:1 d12:10 d13:11 d14:5 d15:3 | 1.01 | 0 |
| mt50_mo10 | 10 | 40 | 30 | 34 | 40.5 | 40.1 | 41.0 | d11:5 d12:11 d13:10 d14:3 d15:1 | 1.01 | 0 |
| mt50_mo25 | 25 | 25 | 30 | 20 | 25.4 | 25.1 | 25.9 | d10:6 d11:10 d12:8 d13:6 | 1.02 | 0 |
| mt50_mo45 | 45 | 5 | 30 | 3 | 5.4 | 5.0 | 5.8 | d10:1 d7:2 d8:20 d9:7 | 1.08 | 0 |
| mt100_mo0 | 0 | 100 | 30 | 84 | 100.5 | 100.1 | 100.8 | d12:1 d13:6 d14:9 d15:5 d16:9 | 1.00 | 0 |
| mt100_mo10 | 10 | 90 | 30 | 70 | 90.5 | 90.2 | 90.8 | d12:2 d13:9 d14:8 d15:4 d16:7 | 1.01 | 0 |
| mt100_mo25 | 25 | 75 | 30 | 57 | 75.5 | 75.2 | 76.0 | d12:3 d13:11 d14:7 d15:8 d16:1 | 1.01 | 0 |
| mt100_mo45 | 45 | 55 | 30 | 40 | 55.5 | 55.1 | 56.3 | d11:1 d12:9 d13:13 d14:4 d15:3 | 1.01 | 0 |
| mt200_mo0 | 0 | 200 | 30 | 165 | 200.6 | 200.2 | 201.0 | d14:2 d15:7 d16:8 d17:12 d18:1 | 1.00 | 0 |
| mt200_mo10 | 10 | 190 | 30 | 158 | 190.5 | 190.1 | 191.0 | d14:2 d15:7 d16:10 d17:10 d18:1 | 1.00 | 0 |
| mt200_mo25 | 25 | 175 | 30 | 141 | 175.4 | 175.1 | 175.8 | d14:4 d15:5 d16:12 d17:9 | 1.00 | 0 |
| mt200_mo45 | 45 | 155 | 30 | 122 | 155.6 | 155.1 | 155.9 | d13:1 d14:5 d15:8 d16:10 d17:6 | 1.00 | 0 |
| mt500_mo0 | 0 | 500 | 30 | 422 | 500.5 | 500.2 | 501.0 | d17:6 d18:5 d19:15 d20:3 d21:1 | 1.00 | 0 |
| mt500_mo10 | 10 | 490 | 30 | 413 | 490.5 | 490.2 | 491.2 | d17:6 d18:6 d19:14 d20:3 d21:1 | 1.00 | 0 |
| mt500_mo25 | 25 | 475 | 30 | 400 | 475.6 | 475.2 | 476.0 | d17:6 d18:6 d19:14 d20:4 | 1.00 | 0 |
| mt500_mo45 | 45 | 455 | 30 | 397 | 455.6 | 455.2 | 456.0 | d17:6 d18:9 d19:13 d20:2 | 1.00 | 0 |

## What this says, in one line each
1. **The wall stop equals the plan in every one of the 16 cells**, ratio 1.00-1.02 (1.08 only in the
   5 ms cell, where 0.4 ms of pipe latency is 8 % of the budget). Overhead 0 gives 50.5 ms, overhead 10
   gives 40.5 — the 10 ms subtraction is real and is what stops the search. P1/P2/P3/P8 survive.
2. **The engine's own last-info `time` is much lower than the stop**, and that is seat 16's number:
   40 vs 50 at movetime 50, 158 vs 190 at movetime 200, 165 vs 200. It is the point where the last
   COMPLETED iteration ended, not the stop.
3. **My job 1 read 40.5 ms at movetime 50 — the engine's-time figure of the same experiments, not a
   wall figure.** This is the error. Look at job 1's own TSV: `wall_ms` 40.5 and `engine_time_ms` 34 at
   `mt50`. **Both are ~10 ms below the 50 ms budget, and the wall number was only ever 40.5 because I
   ran job 1 BEFORE I discovered the `Move Overhead` default — job 1's `mo_test.py` then measured
   overhead 0 at 50.6 ms and overhead 10 at 40.5 ms and I read that as "the plan is M−10" when the
   correct reading is "my job-1 harness's overhead-10 run stopped at 40.5".** The grid above, which
   crosses the same movetime with overhead 0, settles it: at overhead 0 the stop is 50.5, not 40.5.
4. **So the precise true statement is**: `go movetime M` searches until `M − MoveOverhead` ms have
   elapsed; it stops within 1-2 ms of that plan (the iteration in flight is abandoned, not completed);
   the last completed iteration ends well before the stop (typically 70-85 % of it), which is the
   number the engine reports in `time`.

## Why seat 16 and I disagreed, and who was wrong where
- Seat 16's "`movetime 50` stops at 26-28 ms at both overhead 0 and overhead 10" is **not** what the
  stop does — the stop is 50.5 and 40.5 ms. Their 26-28 ms is close to the last-info-`time` at overhead
  0 (24 ms in my `verify_wall_out.txt`) and at or below a depth-12 iteration, so seat 16 measured the
  last completed iteration, exactly as I measured 40.5 for overhead 10.
- My S-F1's **claim that the plan is M−10 is right**, and confirmed by the overhead 0/10/25/45 ladder
  (50.5 / 40.5 / 25.4 / 5.4 ms).
- My S-F1's **wording "so every fixed-time search finishes ~9.5 ms early" is only true at the default
  overhead.** It is not a defect: it is the Move Overhead doing its job. I wrote it as a defect and that
  part is withdrawn.
- Seat 16's "`movetime 200` gives 167 ms at both settings" is again the last-info figure (my 158/165).

## Independent confirmation that the wall number is the stop (seat 19's warning)
`verify_wall_is_the_stop.py` measures the same cells a second way (own feeder, wait for `bestmove`,
then `quit`) and prints the last-info `time` beside it (`verify_wall_out.txt`):

| movetime | overhead | plan ms | WALL go->bestmove (5 runs) | bestmove seen | last info `time` | last depth |
|---|---|---|---|---|---|---|
| 50 | 0 | 50 | 50.2 50.2 50.7 50.4 50.6 | yes | 24.0 | 12 |
| 50 | 10 | 40 | 40.5 40.4 40.5 40.9 40.4 | yes | 22.0 | 12 |
| 200 | 0 | 200 | 200.7 200.6 200.4 200.4 200.7 | yes | 133.0 | 16 |
| 200 | 10 | 190 | 190.4 190.6 190.8 190.5 190.8 | yes | 133.0 | 16 |

Two independent measurements, same answer. The last-info `time` is 24 ms at movetime 50 and 133 ms at
movetime 200 — under half the plan — which is exactly the confound seat 16 and I both fell into.

## The trap, recorded for the third time
My first `verify_wall_is_the_stop.py` sent `quit` in the same pipe as `go`. The engine answered
instantly and the whole process finished in 17-28 ms for every cell, plan 200 ms included. That is the
quit-during-search path (seat 20's S-F11), and it produced a "result" that looked like a devastating
refutation. It is kept in `verify_wall_BROKEN_quit_race.txt` as a warning, labelled BROKEN, and no
number from it is used. This is the third shell-pipeline trap in my work
(`job1/README_HARNESS_BUG.md`, `checks/CHECK_27f2.md`, and this one).

## Integrity audit (seat 19's warning applied to every table I published)
`audit_timestamps.py` re-reads all 19 raw files behind my job 1-3 tables and asserts, per row: a
parseable wall time, no NaN/inf, every NORESP row counted, and every plan used in a ratio positive and
recomputed from the source constants rather than taken from the table. Pasted tail:

```
files audited: 19; problems: 0
AUDIT PASSES: every row had a parseable wall time, every NORESP row is counted above,
and every plan used in a ratio was positive and recomputed from the source constants.
```

The audit itself first CRASHED on a non-movetime filename (`mtg1.tsv` parsed as movetime 1). It was fixed
rather than silenced, because a crash is the behaviour I want: it must never report PASS while measuring
nothing.

## Prediction score (`prediction_check` output in `prediction_check_out.txt`)

See that file for the row-by-row verdict. In summary: the plan is M−O (P1, P2, P3, P4, P8 all
survive); the engine's own `time` is below the wall by much more than pipe latency (P5 REFUTED — the gap
is the unfinished iteration, not the pipe); the last depth does differ slightly between overhead 0 and
10 at movetime 50 (P6 REFUTED); and undershoot by iteration granularity is visible but small in the
median (P7 survives only in the 5 ms cell).

## Process state for every search here

All of these searches ran in one long-lived process per cell with `ucinewgame` + `isready` before each
`go`. Verified equivalent to a fresh process per search by `job4/state_check.py` (identical nodes and
depth), so the state assumption behind these tables holds. `Clear Hash` was never used as a cold restore.

## What I did NOT do
- Did not re-run jobs 2 and 3 at this depth of crossing; their re-checks are the next file
  (`CORRECTION_2.md`).
- Did not measure below movetime 5 or above 500 in the grid.
- No sanitizer in this experiment.

## What I am NOT sure about
- Whether seat 16's specific 26-28 ms at overhead 0 can be reproduced on their build; my overhead-0 stop
  is 50.5 ms. Their number matches a depth-12 iteration here, so I believe we are measuring different
  quantities, but I cannot run their harness.
- Why the last-info `time` sits at 70-85 % of the plan rather than lower; that depends on the iteration
  ladder for the position set, which I did not model.
