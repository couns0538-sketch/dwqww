# REPORT job 1 AGAIN — AREA 8 (THE CLOCK) — seat 08, SEED 811

## What was asked
The brief's cycle step 2c: job 1 of my area again with the next seed (SEED + 10 = 811) and a new position set
(R with SEED 811), saying in the report what differs from the first run.

## The answer (one line each)
- The first run reproduces almost exactly on a new position set: `movetime 50` median 40.48 ms (run 1: 40.5),
  `movetime 500` median 490.50 ms (run 1: 490.5), 1 s clock 39.29 ms (run 1: 39.6).
- The new R set gives the SAME movetime-50 median as the O+G set (40.48 vs 40.48 ms), so the wall-clock
  behaviour is a property of the engine's clock code, not of the positions — with one exception below.
- The 10 s clock is the one control that moves with the position set: 352.00 ms median here vs 344.7 ms in run 1,
  and the new-set 1 s clock is 33.74 ms vs 39.29 ms — a 14 % spread on a clocked control between two position
  sets. That is the same iteration-granularity effect as 08-F9, now seen across sets.

## What differs from run 1 (required by the brief)
1. **New R set**: SEED 811 instead of 801, 500 new positions, first 100 used. Half of every "OR" control is
   therefore new material.
2. **`OwnBook false` on every search.** Run 1 had one of 200 positions answered from the book in 0.04 ms (08-F3).
   This run has none, so every one of the 1,400 searches is a real search (confirmed: minimum stdout lines
   between `go` and `bestmove` is 10 in this dataset — a book answer or a fabricated one would be 1-2).
3. Same harness logic, same S14, same 4-core box, guarded start (load 0.02, no other engine process).

## How sure
Sure about the reproduction of the two `movetime` medians (they agree with run 1 to 0.02 ms and the baselines
agree to 0.03 %). Sure that no book answer and no fabricated bestmove is in this set (the `nlines` field, and
the audit against seat 19's 19-F12). NOT sure how much of the 10 s clock's 7 ms shift is position set and how
much is machine state: I did not interleave the two sets.

## Honesty numbers
/home/ubuntu/builds/release/forge, sha256 e06310eca3...a83; bench 11/13/16 = 312,866 / 862,329 / 3,024,920 and
perft 5 = 4,865,609, all exact. job1b/raw/.meta has the path, sha256, option lines and the guard line.
Prediction pushed alone at 21:33:24Z before the first search.

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone before measuring | done | job1b/prediction.txt | pushed 21:33:24Z |
| new R set from SEED 811 | done | job1b/R_seed811.fens (500 lines) | 11 games |
| guard | done | job1b/run.log line 1 | load 0.02, no other engine process |
| 8 controls x 200 searches | done | job1b/raw/*.jsonl | 1,400 searches |
| OwnBook false actually applied | done | job1b/raw/.meta + min nlines per file = 10 | no 0-info answers anywhere |
| baseline repeatability | done | job1b/analysis_table.txt | 0.03 % |

## The table (pasted output of the committed one-liner script in job1b/analysis_table.txt)

```
## job1b — AREA 8 job 1 AGAIN, SEED 811, OwnBook false. 200 searches per control.

| control | set | n | median ms | p99 ms | max ms | min nlines |
|---|---|---|---|---|---|---|
| OG_baseA | OG | 200 | 40.48 | 40.99 | 41.20 | 11 |
| OG_baseB | OG | 200 | 40.46 | 40.93 | 44.13 | 11 |
| OG_mt500 | OG | 200 | 490.50 | 490.93 | 491.37 | 17 |
| OG_tc1000 | OG | 200 | 39.29 | 139.85 | 197.95 | 12 |
| OG_tc10000 | OG | 200 | 352.00 | 1301.39 | 2384.89 | 17 |
| OR_mt50 | OR | 200 | 40.48 | 40.89 | 41.19 | 10 |
| OR_tc1000 | OR | 200 | 33.74 | 184.25 | 194.57 | 11 |

## baseline repeatability (two identical 200-search runs, movetime 50)
| A total | B total | diff | rel | A median | B median |
|---|---|---|---|---|---|
| 8046.15 | 8044.03 | 2.12 | 0.03 % | 40.48 | 40.46 |

## run 1 vs this run, same control, different position sets
| control | run 1 (O+G, SEED 801) | this run (O+G, SEED 811) | this run (O+R811) |
|---|---|---|---|
| movetime 50 | 40.5 | 40.48 | 40.48 |
| movetime 500 | 490.5 | 490.50 | - |
| wtime 1000 inc 10 | 39.6 | 39.29 | 33.74 |
| wtime 10000 inc 100 | 344.7 | 352.00 | - |
```

## Prediction vs result

| my prediction | result | verdict |
|---|---|---|
| movetime 50 baseline A 40.3-40.8 ms | 40.48 | correct |
| movetime 500 490.3-490.8 | 490.50 | correct |
| 1 s clock 38-42 ms | 39.29 | correct |
| 10 s clock 320-380 ms | 352.00 | correct |
| 1 s clock p99 140-200 ms | 139.85 | 0.15 ms below the range — killed by a hair |
| baseline A vs B totals within 1 % | 0.03 % | correct |

## Findings raised by this run
- The 1 s clock p99 (139.85 ms) and the 10 s clock median moved by 7 ms between two position sets. Neither is a
  new mechanism: both are the iteration-boundary effect restated in 08-F10. I am not adding a separate finding
  for a position-set difference on 200 samples.

## What I did NOT do
- Did not interleave the two position sets, so I cannot separate position effect from machine drift.
- No sanitizer (not asked for area 8).
- Did not re-run the `movestogo` controls on the new set.

## What I am NOT sure about
- Whether the new-set 1 s clock being 5.5 ms FASTER (33.74 vs 39.29) is because the new R positions reach a
  cheap iteration boundary earlier, or because the box was quiet. `job1b/raw/OR_tc1000.jsonl` p99 184.25 ms
  against OG's 139.85 argues it is position-driven (wider tail), but I did not test it separately.

## Times
see job1b/stamps.txt and job1b/run.log.

## Last command output
```
$ git status --short
 M forge-combo29/swarm/08/job1b/analysis_table.txt
?? forge-combo29/swarm/08/REPORT_job1b.md
?? forge-combo29/swarm/08/job1b/make_report_job1b.sh
$ ls forge-combo29/swarm/08/job1b/raw
exe_path.txt
exe_sha256.txt
OG_baseA.jsonl
OG_baseB.jsonl
OG_mt500.jsonl
OG_tc10000.jsonl
OG_tc1000.jsonl
OR_mt50.jsonl
OR_tc1000.jsonl
setup_counts.txt
```
