# REPORT_job2 — AREA 8 (THE CLOCK), seat 28

## What was asked
AREA 8 job 2: very little time. `go wtime 100 / 30 / 10 / 1 / 0` (and the same with `winc 0` and
`winc 10`): overruns and losses on time.

## The answer
**No overrun and no time loss in 400 low-time searches**: every one returned a legal bestmove, none
used more than the wtime it was given (largest 21.66 ms on a 100 ms clock), and `wtime 0` still
answers instantly. Below `Move Overhead` (wtime 0, 1, 10) the engine returns in 0.2 ms through the
`reserve_empty` path without searching. Two real faults fell out of the increment cases:
**(1)** at `wtime <= 10` (the default Move Overhead) the engine ignores the increment completely — with
`winc 1000` and `wtime 5` it still plays instantly instead of using 1005 ms; **(2)** above that
threshold the increment is used, but the hard limit is capped at `0.6 × (wtime − 10)` and does not
include the increment, so a full clock and a small clock plus the same increment buy very different
search times (0.15x at a 2600 ms total).

## How sure
Very high on the low-time results — 40 searches per cell, 400 in total, every bestmove judged legal by
python-chess, every cell's `.meta` stamped with exe sha256 and the exact `go` line. The two zeros in
this job were checked with Opus's Rule 1 (FABLE_TO_swarm_2): the SAME harness, unchanged, was run
against a planted fake engine, and it counted the fault —

| plant | what the harness measured | count | the zero it must break | caught |
|---|---|---|---|---|
| illegal bestmove (fake answers a1a8) | bestmove_legal == False | 400/400 | 400/400 legal | YES |
| time overrun (fake sleeps 300 ms) | wall_ms > wtime | 400/400 | 0 over wtime | YES |
| REAL engine, same harness | bestmove_legal False | 0/400 | - | - |
| REAL engine, same harness | wall_ms > wtime | 0/400 | - | - |

(pasted output of `python3 plant_verdict.py .`; plants under `out_plant/illegal/`, `out_plant/overrun/`,
fake engine `fake_engine.py`, driver `plant_test.py`.)

High on both increment faults: each was measured twice, once as a sweep and once as a paired
comparison, and both follow exactly the line of code that causes them
(`include/forge/clock_plan.hpp:32` and `:41`). Medium on the *practical* severity — I did not run games,
so I cannot say how many games a 15 % vs 100 % use of a 2600 ms clock costs in Elo.

## Honesty numbers
Same exe as job 1, `~/build/base-release/forge`, sha256 `e06310ec…16a83`, `id name Chess Engine Forge
6.4.24 candidate`; all four honesty numbers matched (see `../HONESTY.txt`). No sanitizer in this job.

## Table — pasted output of `python3 lowtime_table.py out` (`lowtime_table_out.txt`)

| run | wtime | winc | n | median ms | p99 ms | largest ms | over wtime | engine time > wtime | legal bestmove | answered |
|---|---|---|---|---|---|---|---|---|---|---|
| w0_i0 | 0 | 0 | 40 | 0.16 | 0.73 | 0.86 | 40 | 0 | 40/40 | 40/40 |
| w0_i10 | 0 | 10 | 40 | 0.18 | 0.67 | 0.81 | 40 | 0 | 40/40 | 40/40 |
| w100_i0 | 100 | 0 | 40 | 4.70 | 10.70 | 11.11 | 0 | 0 | 40/40 | 40/40 |
| w100_i10 | 100 | 10 | 40 | 10.05 | 21.29 | 21.66 | 0 | 0 | 40/40 | 40/40 |
| w10_i0 | 10 | 0 | 40 | 0.16 | 0.51 | 0.59 | 0 | 0 | 40/40 | 40/40 |
| w10_i10 | 10 | 10 | 40 | 0.20 | 0.68 | 0.77 | 0 | 0 | 40/40 | 40/40 |
| w1_i0 | 1 | 0 | 40 | 0.20 | 0.64 | 0.67 | 0 | 0 | 40/40 | 40/40 |
| w1_i10 | 1 | 10 | 40 | 0.20 | 0.67 | 0.74 | 0 | 0 | 40/40 | 40/40 |
| w30_i0 | 30 | 0 | 40 | 1.09 | 1.62 | 1.65 | 0 | 0 | 40/40 | 40/40 |
| w30_i10 | 30 | 10 | 40 | 6.81 | 12.24 | 12.26 | 0 | 0 | 40/40 | 40/40 |

The `over wtime` count of 40 in the `w0_*` rows means every search took longer than 0 ms of wall time,
which is trivially true; the meaningful column is `engine time > wtime`, which is 0 everywhere. Read
the w0 rows as "answered at once", not as 40 time losses.

## The step table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction alone, before measuring | done | `prediction.txt` (commit "swarm 28 job2: prediction committed alone") | 10/13 survived |
| wtime 100/30/10/1/0 x winc 0/10, 40 searches each | done | `out/w*_i*.tsv` (10 files) | table above |
| overruns and losses on time | done | `lowtime_table_out.txt` | 0 overruns, 0 losses |
| Opus Rule 1: planted fault counted by the SAME harness | done | `plant_verdict_out.txt`, `out_plant/` | 400/400 caught, real run 0/400 |
| legal bestmove per search | done | `bestmove_legal` column, python-chess judged | 400/400 |
| increment behaviour at the overhead boundary | done (extra) | `increment_edge_out.txt` | cliff at wtime 11 |
| increment vs clock, paired | done (extra) | `increment_compare_out.txt` | 0.15x at 2600 ms |
| hard limit vs increment, sweep | done (extra) | `increment_cap_out.txt` | hard limit capped without winc |

## Findings

**S-F5 — below the Move Overhead (wtime <= 10 ms) the engine ignores a Fischer increment entirely.**
With `wtime 5 btime 5 winc 1000 binc 1000` a GUI gives 1005 ms for the move, but the engine plays in
0.29 ms with a depth-1, 98-node answer, the same as `winc 0`; at `wtime 11` with the same increment it
suddenly searches 2,048 nodes to depth 6.
Shows again: `python3 increment_cliff.py ~/build/base-release/forge` (`increment_cliff_out.txt`) —
rows `5 / 1000` vs `11 / 1000`. Code: `include/forge/clock_plan.hpp:32`
`if (time <= overhead) return ClockPlan{0, 0, true};` returns before
`soft = available / divisor + increment * increment_percent / 100` on line 41 is reached.

**S-F6 — the hard limit does not include the increment, so a clock + increment pair searches far less
than the same total time held outright.**
`go wtime 1600 winc 1000` (a GUI gives 2600 ms) searches a median 604 ms; `go wtime 2600 winc 0` (the
same 2600 ms) searches a median 92 ms. Across 1100..2600 ms the ratio B/A falls 0.94x → 0.15x.
Shows again: `python3 increment_compare.py ~/build/base-release/forge` (`increment_compare_out.txt`),
`python3 increment_cap.py ~/build/base-release/forge`. Code: `include/forge/clock_plan.hpp:41`
`hard = min(available * hard_percent / 100, soft * hard_soft_multiple)` with `available = time -
overhead` — no term for the increment, while `soft` on line 40 does add it.

**S-F7 — `wtime 0` is answered instantly with a legal move, not with an error or a hang**, which is
the correct behaviour for a fallen flag and is worth recording as the control for S-F5: 40/40 legal,
median 0.16 ms. Evidence: `out/w0_i0.tsv`.

## Suspicions, not proven
- In the `w0_i0` rows the engine answers `a2a3`-type moves (`bestmove a2a3` on the position
  `r1bqk2r/... w KQkq - 2 8`, whose first legal move by python-chess is `d4a7`). The move is legal but
  is not the engine's first root candidate order, so I cannot say which list it comes from. Not a claim.
- The 2,000-node emergency cap (`src/search.cpp:2308`) is what produces the 2,048-node answers just
  above the threshold; the extra 48 nodes are probably the pre-search setup. Unverified.

## What I did NOT do
- No games were played, so no Elo number for S-F5/S-F6 is claimed.
- Did not test `movestogo` (that is job 3) or `wtime` above 100 ms in the low-time grid.
- Did not run these under a sanitizer.

## What I am NOT sure about
- Whether `time <= overhead` returning early is deliberate for sudden death (it is right there) and the
  increment case was simply not considered. S-F5 states the behaviour; the intent is the owner's call.
- Whether a GUI adds the increment before or after sending `go`; I measured the engine, assuming the
  GUI's clock for the move is `wtime + winc`, which is the standard Fischer rule.

## Prediction score (pasted, `prediction_check_job2_out.txt`)

| id | measurement | predicted | measured | kill range | verdict |
|---|---|---|---|---|---|
| P1 | wtime 10 winc 0 median | 1.5 ms | 0.16 ms | 0.5..20 | **KILLED** |
| P2 | wtime 1 winc 0 median | 1.5 ms | 0.2 ms | 0.5..20 | **KILLED** |
| P3 | wtime 0 winc 0 median | 1.5 ms | 0.16 ms | 0.5..20 | **KILLED** |
| P4 | wtime 10 winc 0 over 10 ms | 0 n | 0 n | 0..10 | SURVIVES |
| P5 | wtime 30 winc 0 median | 2.0 ms | 1.09 ms | 0.5..30 | SURVIVES |
| P6 | wtime 30 winc 0 largest | 20 ms | 1.65 ms | 2..200 | **KILLED** |
| P7 | wtime 100 winc 0 median | 4.0 ms | 4.7 ms | 1..60 | SURVIVES |
| P8 | wtime 100 winc 0 over 100 ms | 0 n | 0 n | 0..10 | SURVIVES |
| P9 | wtime 100 winc 10 median | 7.0 ms | 10.05 ms | 1..60 | SURVIVES |
| P10 | wtime 30 winc 10 median | 3.5 ms | 6.81 ms | 0.5..40 | SURVIVES |
| P11 | legal bestmove, all cells (%) | 100.0 % | 100.0 % | 100.0..100.0 | SURVIVES |
| P12 | answered, all cells (%) | 100.0 % | 100.0 % | 100.0..100.0 | SURVIVES |
| P13 | wtime 0 answered (yes=1) | 1 | 1 | 1..1 | SURVIVES |

The three killed predictions are all the same mistake: I predicted ~1.5 ms of handshake cost for the
instant-return path, and the engine returns in 0.2 ms because it answers from the first legal move
without even waiting for a clock poll. The fourth kill (P6) is the same mistake in the other
direction: I expected a ragged iteration near the 30 ms clock; the engine's plan there is so small
(soft 1 ms) that nothing ragged happens.

## Times: see `stamps.txt`. Last command output: `last_command.txt`.
