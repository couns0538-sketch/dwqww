# REPORT_job1 — AREA 8 (THE CLOCK), seat 28

## What was asked
AREA 8 job 1: 200 searches (first 100 of O and of G) at `go wtime 1000 btime 1000 winc 10 binc 10`,
`go wtime 10000 btime 10000 winc 100 binc 100`, `go movetime 50`, `go movetime 500`; wall time from
sending `go` to reading `bestmove` on a monotonic clock; table with median, 99th percentile, largest,
searches over the limit; the movetime-50 base run twice first (how much two equal runs differ); say how
many cores the machine has.

## The answer
The engine never exceeded its own planned hard limit in 1,000 timed searches, and the two movetime-50
runs differ by 0.05 ms. But the limit it plans is not the limit the GUI asks for:
`go movetime M` is turned into a **hard limit of M − Move Overhead** with a default of 10 ms, so every
movetime search finishes ~9.5 ms early (40.5 ms for a 50 ms budget, 490.6 ms for 500 ms). Clock
searches are the opposite way round: the median is below `wtime/30 + winc` but 41 % of the 1 s searches
and 27 % of the 10 s searches run past it, with a largest of 1,270 ms on a 10 s clock. On a 1 s clock
that is 4.6 % of the total clock in one move, but no search went over the engine's own hard limit
(260 ms at wtime 1000, 2,645 ms at wtime 10000) in this run.


## Process state for every search in this report (seat 10's rule)

Every search reported here ran in **one long-lived engine process per configuration**, with
`ucinewgame` + `isready` sent and read before EACH `go` — never `Clear Hash`, and not a fresh process per
search. Seat 10 reports that warm state changes results and that `ucinewgame` restores cold while
`Clear Hash` does not. I tested that directly on my own build (`job4/state_check.py`,
`job4/state_check_out.txt`): one process with `ucinewgame` gives **bit-identical** node counts and last
depths to a fresh process per search (112,623 nodes and depth 14 on all five searches in both regimes),
while a process with nothing between searches climbs 14,15,16,17,17. So the design of every harness in
this report is sound for the quantity reported, and `ucinewgame` — not `Clear Hash` — is what makes it so.

## How sure
High on the measurements (raw per-search files, one engine process per config, 200 searches each,
two independent movetime-50 runs agreeing to 0.05 ms), and the Move Overhead mechanism was confirmed
by direct experiment at three overhead values. The two zeros in this job were checked with Opus's
Rule 1 (FABLE_TO_swarm_2): the SAME harness, unchanged, caught both planted faults —

| plant | harness column | plant count | real count | the zero it must break | caught |
|---|---|---|---|---|---|
| no answer (fake never prints bestmove) | status == NORESP | 8/8 | 0/200 | 0 NORESP | YES |
| overrun (fake sleeps 300 ms) | wall_ms > 50 | 8/8 | 0/200 | 0 over movetime 50 | YES |

(pasted output of `python3 ../job2/plant_verdict_job1.py .`; plant raw files in
`job2/out_plant_job1/{noanswer,overrun}/`.)

Medium on the interpretation of the clock outliers:
201 ms and 1,270 ms are within the engine's own hard limit, so they are legal use of the budget, not
a fault — unless Fable/Opus consider `wtime/30+winc` a promise, which the engine does not make.

## Honesty numbers
From `../HONESTY.txt` (Release build, GCC 13.3.0, commit 6b98f217): bench 11 = 312,866; bench 13 =
862,329; bench 16 = 3,024,920; perft 5 = 4,865,609 — all four match. All four timed runs used
`~/build/base-release/forge`, sha256 `e06310ec…16a83`, `id name Chess Engine Forge 6.4.24 candidate`
(stamped in every `.meta`).

## Machine
`nproc` = 4 (Intel Xeon). 15 GiB RAM. Each timed run was one process, `Threads 1`, `Hash 16`, S14 sent
as setoption lines before the run.

## Table — pasted output of `python3 table1.py .` (see `table1_out.txt`)

| run | n | median | p99 | largest | limit ms | over limit |
|---|---|---|---|---|---|---|
| A1_mt50 | 200 | 40.5 | 40.9 | 41.6 | 50.0 | 0 |
| B1_mt50 | 200 | 40.5 | 40.9 | 41.0 | 50.0 | 0 |
| A_mt500 | 200 | 490.6 | 491.0 | 491.2 | 500.0 | 0 |
| A_wt1000 | 200 | 38.2 | 130.2 | 201.0 | 43.3 | 82 |
| A_wt10000 | 200 | 322.5 | 1082.6 | 1269.9 | 433.3 | 54 |

two movetime-50 runs: median A 40.54, median B 40.49, difference 0.05 ms

The "limit" column here is the budget as asked (`movetime`, or `wtime/30 + winc`). "Over limit" counts
searches above it. The next table uses the limit the ENGINE plans for itself.

## Table — pasted output of `python3 plan_limit.py outA mt50 mt500 wt1000 wt10000` (`plan_limit_out.txt`)

| config | soft ms | hard ms | n | median | max | over soft | over HARD |
|---|---|---|---|---|---|---|---|
| mt50 | 40 | 40 | 200 | 40.5 | 41.6 | 2 | 2 |
| mt500 | 490 | 490 | 200 | 490.6 | 491.2 | 4 | 4 |
| wt1000 | 52 | 260 | 200 | 38.5 | 201.0 | 53 | 0 |
| wt10000 | 529 | 2645 | 200 | 322.5 | 1269.9 | 33 | 0 |

Soft/hard are recomputed from `include/forge/clock_plan.hpp` + the defaults in `src/search.cpp:79-82`
and the 10 ms `Move Overhead` default in `src/uci.cpp:152`. No clock search overran its hard limit;
the movetime cases are "over" only by 0.5-1.6 ms of process/pipe latency.

## The step table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction alone, before measuring | done | `prediction.txt` (commit "swarm 28 job1: prediction committed alone before measuring") | 15 predictions, 6 killed |
| movetime 50 base run twice | done | `outA/mt50.txt`, `outB/mt50.txt` | 40.54 vs 40.49 ms median, differ 0.05 ms |
| movetime 500 | done | `outA/mt500.txt` | median 490.6, max 491.2 |
| wtime 1000 winc 10 | done | `outA/wt1000.txt` | median 38.2, p99 130.2, max 201.0 |
| wtime 10000 winc 100 | done | `outA/wt10000.txt` | median 322.5, p99 1082.6, max 1269.9 |
| median/p99/largest/over-limit table | done | `table1_out.txt`, `plan_limit_out.txt` | above |
| 200 searches per config = first 100 O + first 100 G | done | every `.txt` has 200 data rows | yes |
| say how many cores | done | this report, "Machine" | 4 |
| Move Overhead causality experiment | done (extra) | `outA/mo_{0,10,40}.tsv` | shortfall = overhead exactly |
| Opus Rule 1: planted fault counted by the SAME harness | done (extra) | `plant_verdict_job1_out.txt` | 8/8 caught, real run 0/200 |
| `timing.py` now takes npos + watchdog as argv 4/5 (added for the plant; the 200-position results above used the 200/60 s defaults) | done | `timing.py` | no effect on the reported numbers |

## Findings

**S-F1 — `go movetime M` searches stop at M − 10 ms; the default `Move Overhead 10` is subtracted from
the movetime limit, so every fixed-time search finishes 9.5 ms early.**
Shows again:
```
cd forge-combo29/swarm/28/job1
python3 mo_test.py ~/build/base-release/forge /tmp/mo.tsv 0    # median 50.6 / 500.5
python3 mo_test.py ~/build/base-release/forge /tmp/mo.tsv 10   # median 40.5 / 490.5
python3 mo_test.py ~/build/base-release/forge /tmp/mo.tsv 40   # median 10.5 / 460.6
```
Code: `src/search.cpp:2192` `hard_limit_ms_ = max(1, limits.movetime_ms - overhead)` with
`overhead` from `limits.move_overhead_ms` (`src/uci.cpp:518`), default 10 at `src/uci.cpp:152`.
Beyond what FABLE_TO_swarm_1 lists (it says nothing about movetime). Consequence, measured on a
non-book position (`tiny_movetime_out.txt`, pasted output of `python3 tiny_movetime.py
~/build/base-release/forge "r1bqk2r/p1ppbppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"`):

| movetime | Move Overhead | wall ms | engine `time` | hard limit the code computes |
|---|---|---|---|---|
| 50 | 10 | 40.58 | 22 | 40 |
| 11 | 10 | 1.54 | 1 | 1 |
| 10 | 10 | 1.16 | 1 | 1 |
| 5 | 10 | 1.52 | 0 | 1 |
| 1 | 10 | 1.31 | 1 | 1 |
| 0 | 10 | 1.16 | 1 | 1 |
| 50 | 40 | 10.54 | 7 | 10 |
| 50 | 0 | 50.24 | 22 | 50 |

So `go movetime 10` (the default overhead of 10 ms) does not search for 10 ms — it searches for 1 ms,
and `go movetime 5` with `Move Overhead 40` also gets the 1 ms floor. The startpos answers above are
all identical because the opening book answers startpos without searching; the table above is on a
position outside the book.

**S-F2 — 41 % of the `wtime 1000 winc 10` searches run past `wtime/30 + winc`; largest 201 ms
(4.6 ms early is not the behaviour, over-spending is).**
Shows again: `python3 table1.py .` (row A_wt1000) and
`awk -F'\t' 'NR>1 && $3>43.3' outA/wt1000.txt | wc -l` → 82.
The engine's own soft limit is 52 ms and 53 searches exceed it, so the planner is not the cause; the
search spends past `soft_limit_ms_` (normal for an iteration that is still improving) up to the hard
limit of 260 ms. Whether that is intended is a question for the owner, not a bug claim.

**S-F3 — movetime-50 timing is stable to 0.05 ms between runs on this machine**, so any later
movetime change of more than ~1 % is measurable without repetition. Evidence: `outA/mt50.txt` vs
`outB/mt50.txt`.

## Suspicions, not proven
- The `wt10000` largest of 1,269.9 ms happens on the 100th and 99th G positions; I did not check
  whether those are positions where the search's "unstable" heuristic inflates the budget. Not a claim.
- `engine_time_ms` in the TSVs is the `time` of the LAST COMPLETED `info` line, not the final elapsed
  time, so `wall_ms − engine_time_ms` (see `harness_overhead_out.txt`) is not pure harness latency for
  the movetime configs; do not read the 8.56 ms and 97.60 ms medians there as pipe cost.

## What I did NOT do
- No `movestogo` case (that is job 3), no sub-50 ms budgets (job 2), no multi-thread timing (area 4).
- No clock search under a sanitizer — the timed runs are Release only.
- Did not test with `Threads > 1`; a 4-core box with one process is the S14 condition.

## What I am NOT sure about
- Whether the owner wants `movetime` to mean "search up to M ms" (then S-F1 is a defect for short M) or
  "use M ms of the GUI's budget minus network overhead" (then it is by design). S-F1 states the
  behaviour, not a verdict.
- The 95 % figures are for wall time as measured through a pipe and a Python driver; a GUI's own
  handshake adds its own latency on top.

## Prediction score (pasted, `prediction_check_out.txt`)

| id | measurement | predicted | measured | kill range | verdict |
|---|---|---|---|---|---|
| P1 | movetime 50 run A median | 51.5 ms | 40.54 ms | 45..70 | **KILLED** |
| P2 | movetime 50 run B median | 51.5 ms | 40.49 ms | 45..70 | **KILLED** |
| P3 | A vs B median difference | 0.4 ms | 0.05 ms | 0..3 | SURVIVES |
| P4 | movetime 50 largest (both runs) | 56 ms | 41.64 ms | 50..110 | **KILLED** |
| P5 | movetime 50 over limit of 400 | 3 n | 0 n | 0..40 | SURVIVES |
| P6 | movetime 500 median | 502 ms | 490.59 ms | 460..570 | SURVIVES |
| P7 | movetime 500 largest | 512 ms | 491.22 ms | 500..700 | **KILLED** |
| P8 | movetime 500 over limit | 0 n | 0 n | 0..20 | SURVIVES |
| P9 | wt1000 median | 45 ms | 38.22 ms | 25..90 | SURVIVES |
| P10 | wt1000 largest | 55 ms | 200.99 ms | 40..150 | **KILLED** |
| P11 | wt1000 over wtime/30+winc(43.3) | 0 n | 82 n | 0..25 | **KILLED** |
| P12 | wt10000 median | 350 ms | 322.51 ms | 150..600 | SURVIVES |
| P13 | wt10000 largest | 380 ms | 1269.91 ms | 250..900 | **KILLED** |
| P14 | wt10000 over 433.3 | 0 n | 54 n | 0..25 | **KILLED** |
| P15 | median grows with budget | true | true | true | SURVIVES |

9 of 15 survived, 6 killed. The six killed ones all fail in the SAME direction: I predicted the engine
follows the budget it is given, and it does not — it shaves overhead off movetime and spends past
`wtime/30+winc` on a real clock. That is the finding, and it was written down before the numbers.

## Harness bug (reported in full, `README_HARNESS_BUG.md`)
The first version of `timing.py` used a buffered `TextIOWrapper` under `select()`, which fakes hangs;
it produced three 60 s "timeouts" that a replay in a fresh process disproved. Fixed to read the raw fd
with `os.read()`; the discarded run is deleted and no result uses it.

## Times: see `stamps.txt`
Last command output is in `last_command.txt`.
