# REPORT job 1 — AREA 8 (THE CLOCK) — seat 08

## What was asked
Wall-clock latency of 200 searches (first 100 of O + first 100 of G) at four controls —
`go movetime 50`, `go movetime 500`, `go wtime 1000 btime 1000 winc 10 binc 10`,
`go wtime 10000 btime 10000 winc 100 binc 100` — with the two equal `movetime 50` baseline runs FIRST
so their difference can be reported; median / 99th percentile / largest / searches over the limit; and
how many cores the machine has.

## The answer (one line each)
- `movetime` is honoured tightly and lands ~1 % OVER the engine's own limit, which is
  `movetime - Move Overhead`: median 40.5 ms for `movetime 50` and 490.5 ms for `movetime 500`, i.e. over
  40 and 490, never over 50 and 500. Zero of 200 searches passed the number that was asked for.
- Clocked play (`wtime/btime`) is far looser: median 39.6 ms on a 1000 ms clock with a 99th percentile of
  153.2 ms and a worst case of 198.6 ms; on a 10000 ms clock a median of 344.7 ms, a p99 of 1334.9 ms and a
  worst case of 2425.7 ms. Every one of those stays inside the engine's own hard limit (260 ms / 2645 ms);
  63 of 200 and 46 of 200 respectively run past its own soft limit.
- The machine has 4 cores (`nproc` = 4).

## How sure
Latency numbers: sure — 2,000 timed searches on a guarded machine (no other engine process, load < 0.5 at
start), each timed with `time.monotonic()` from writing the `go` line to reading `bestmove`, and two identical
baseline runs disagreeing by 0.20 % of total time.
The soft/hard limits in Table 4 are RECOMPUTED arithmetic from `include/forge/clock_plan.hpp:27-50` with the
defaults the engine itself printed in its `uci` answer — not measured. If some other path adjusts the time,
they differ; I read `uci.cpp:116-123` and saw no adjustment.
WHY anything is slow: NOT sure. The tail tables show which positions are slow, not why.

## A contamination incident in my own first run (reported, not hidden)
My first `run_job1.sh` hung on the `uci`/`readyok` bug described under "what I did NOT do" below; I killed the
harness, fixed it, and re-ran. The FIRST script was still alive and re-ran itself concurrently from 21:16 to
21:19 UTC while job 2 was being measured. I found it by reading `/proc/<pid>/cwd` (it was my own
`job1/tc1000.jsonl` being rewritten) and killed the whole process group. Both the first job-1 set and the job-2
set measured with a competing engine on the same 4 cores.
**Everything in this report is from the clean re-run** (`job1/raw2/`, `job2/raw2/`), started by `run_clean.sh`
which refuses to start unless no other engine process exists and `loadavg < 0.5`. The first run is kept at
`job1/raw/` and `job2/raw/` and the difference is tabulated below: the contamination moved medians by under
1 ms on the movetime runs (the median is robust) and by 15 ms on the 10 s clock run, and it left the 10 s file
with ONE line because it was being overwritten when I killed it. That is why the guard exists.

## Honesty numbers
Build: /home/ubuntu/builds/release/forge, sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83.
bench 11 = 312,866 / bench 13 = 862,329 / bench 16 = 3,024,920 / perft 5 = 4,865,609 — all four exact.
See HONESTY.txt and honesty/out_release/. job1/raw2/.meta records the exe path it started and its sha256.

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| R position set with SEED 801, FENs written before use | done | job1/R_seed801.fens, job1/gen_R.py | 500 positions, 11 random games, one position per 7 plies |
| prediction committed and pushed ALONE before measuring | done | job1/prediction.txt (commit 841f0b9f5, 21:07:32Z) | pushed before the first search |
| guard against a competing engine before re-measuring | done | job1/run_clean.sh, job1/run_clean.log line 1 | "GUARD ok: load 0.39, no other engine process" |
| two equal baseline runs at movetime 50, first | done | job1/raw2/base_a.jsonl, base_b.jsonl | 200 + 200; totals differ by 0.20 % |
| movetime 500, 200 searches | done | job1/raw2/mt500.jsonl | median 490.5 ms, max 491.1 ms |
| wtime/btime 1000 inc 10, 200 searches | done | job1/raw2/tc1000.jsonl | median 39.6 ms, p99 153.2, max 198.6 |
| wtime/btime 10000 inc 100, 200 searches | done | job1/raw2/tc10000.jsonl | median 344.7 ms, p99 1334.9, max 2425.7 |
| every bestmove legal (python-chess) | done | job1/raw2/legal_table.txt | 1000 of 1000 legal, 0 illegal |
| how many cores | done | job1/raw2/analysis_table.txt | nproc = 4 |
| book-answer contamination of the timing set | done | job1/raw/book_count.txt | 1 of 200 positions is answered from the book |
| first (contaminated) run vs clean run | done | job1/raw2/contamination_table.txt | medians moved ≤ 15.1 ms; the 10 s file had 1 line left |

## Table 1 — the four controls (pasted output of `python3 analyse_job1.py raw2`)

```
## runs on the machine (nproc = 4)

| run                        |   n  | median ms | p99 ms  | largest ms | >limit+50ms |
|----------------------------|------|-----------|---------|------------|-------------|
| base A  movetime 50        |  200 |     40.5 |     41.0 |      47.2 |        0 |     0 |
| base B  movetime 50        |  200 |     40.4 |     40.9 |      42.4 |        0 |     0 |
| movetime 500               |  200 |    490.5 |    490.9 |     491.1 |        0 |     0 |
| wtime/btime 1000 inc10     |  200 |     39.6 |    153.2 |     198.6 |       14 |    14 |
| wtime/btime 10000 inc100   |  200 |    344.7 |   1334.9 |    2425.7 |       58 |    58 |

## baseline repeatability (two identical runs of 200 x movetime 50)
| quantity | run A | run B | difference |
|---|---|---|---|
| median wall ms | 40.5 | 40.4 | 0.0 |
| total ms | 8013.03 | 7996.66 | 16.37 |
| mean wall ms | 40.07 | 39.98 | 0.08 |
| largest ms | 47.2 | 42.4 | 4.9 |
| total relative difference | | | 0.20 % |

## distribution detail, wall ms
| run | min | p10 | p50 | p90 | p99 | max | mean | sd |
|---|---|---|---|---|---|---|---|---|
| base A  movetime 50 | 0.4 | 40.2 | 40.5 | 40.8 | 41.0 | 47.2 | 40.1 | 3.9 |
| base B  movetime 50 | 0.4 | 40.2 | 40.4 | 40.7 | 40.9 | 42.4 | 40.0 | 3.9 |
| movetime 500 | 0.4 | 490.3 | 490.5 | 490.7 | 490.9 | 491.1 | 481.0 | 66.5 |
| wtime/btime 1000 inc10 | 0.0 | 24.8 | 39.6 | 78.4 | 153.2 | 198.6 | 47.6 | 27.1 |
| wtime/btime 10000 inc100 | 0.0 | 257.5 | 344.7 | 692.3 | 1334.9 | 2425.7 | 433.1 | 261.1 |

## overruns (wall > budget + 50 ms) and over budget exactly
| run | budget ms | n over budget+50 | n over budget | worst wall ms | worst excess ms |
|---|---|---|---|---|---|
| base A  movetime 50 | 50 | 0 | 0 | 47.2 | -2.8 |
| base B  movetime 50 | 50 | 0 | 0 | 42.4 | -7.6 |
| movetime 500 | 500 | 0 | 0 | 491.1 | -8.9 |
| wtime/btime 1000 inc10 | 41 | 14 | 96 | 198.6 | 157.3 |
| wtime/btime 10000 inc100 | 413 | 58 | 75 | 2425.7 | 2012.4 |
```

## Table 2 — tail and instant searches (pasted output of `python3 analyse_job1_tail.py raw2`)

```
## instant searches (wall < 5 ms) — which ones and why
| run | i | wall ms | bestmove | fen |
|---|---|---|---|---|
| mt500.jsonl | 3 | 0.36 | bestmove e1g1 | r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8 |
| tc1000.jsonl | 3 | 0.02 | bestmove e1g1 | r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8 |
| tc10000.jsonl | 3 | 0.04 | bestmove e1g1 | r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8 |

## the 10 slowest searches of the 10000 ms clock run
| i | wall ms | move-overhead-adjusted budget ms | bestmove | fen |
|---|---|---|---|---|
| 107 | 2425.7 | 413 | bestmove g5h5 | 8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1 |
| 137 | 1514.7 | 413 | bestmove h8h1 | 7r/2k2p2/2p3P1/2Ppn3/PP2p1b1/4P3/4BK2/R6R b - - 0 1 |
| 120 | 1333.1 | 413 | bestmove e6d6 | 8/8/4K1k1/8/4N1P1/8/1b6/8 w - - 0 1 |
| 128 | 1254.5 | 413 | bestmove a4a5 | 8/p7/5pk1/7p/r2NKP2/4P1P1/PR5P/8 b - - 0 1 |
| 141 | 1069.6 | 413 | bestmove d3d2 | 1kr4n/1ppQ4/4p3/p6P/3P4/3q1RP1/6PK/4R3 b - - 0 1 |
| 186 | 1049.8 | 413 | bestmove d8d7 | 3r4/p7/5kp1/1p3n2/1P3R1P/P4N2/2K2P2/8 b - - 0 1 |
| 158 | 1031.4 | 413 | bestmove e3f4 | 8/6kp/8/1p1r1p2/p7/2bBBP1P/P3K3/8 w - - 0 1 |
| 122 | 996.3 | 413 | bestmove g3h4 | 8/7p/6k1/1p1r1p2/pb3P2/3BK1BP/P7/8 w - - 0 1 |
| 135 | 972.6 | 413 | bestmove e3f3 | 8/8/7k/7P/8/4K3/r7/8 w - - 0 1 |
| 79 | 965.8 | 413 | bestmove c8g4 | r1bqkbnr/ppp2ppp/2n5/3p4/8/1P6/PBPPPPPP/RN1QKBNR b KQkq - 2 4 |

## the 10 slowest searches of the 1000 ms clock run
| i | wall ms | bestmove | fen |
|---|---|---|---|
| 99 | 198.6 | bestmove b1c3 | rnbqkbnr/ppp3pp/4p3/3p1p2/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 0 4 |
| 191 | 155.1 | bestmove g2g4 | 8/p3kpp1/1p2p2p/1b1pP3/5K1P/P3P3/1P4P1/2N5 w - - 0 1 |
| 187 | 153.2 | bestmove f4f3 | 8/p4kp1/8/3b2PN/5p2/P6P/7K/4R3 b - - 0 1 |
| 55 | 124.3 | bestmove c2c4 | r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/3P1P2/PPP3PP/RNBQKBNR w KQkq - 1 4 |
| 18 | 122.8 | bestmove f8e7 | rnbqkbnr/pp3ppp/3p4/2pPp3/2P5/2N5/PP2PPPP/R1BQKBNR b KQkq - 1 4 |
| 40 | 118.8 | bestmove b8d7 | rn1qk1nr/pbp2pbp/1p1pp1p1/8/2PPP3/2N2N2/PP2BPPP/R1BQ1RK1 b kq - 1 7 |
| 199 | 115.3 | bestmove b5c5 | 8/6qp/8/1K6/6Pb/7P/8/1k6 w - - 0 1 |
| 122 | 108.1 | bestmove h3h4 | 8/7p/6k1/1p1r1p2/pb3P2/3BK1BP/P7/8 w - - 0 1 |
| 131 | 102.0 | bestmove c6d7 | 2rqr1k1/5pb1/2bpp1np/pp4p1/3PP1P1/P3B3/1PBQNPP1/4RRK1 b - - 0 1 |
| 157 | 100.8 | bestmove g6f6 | 8/8/6k1/Q7/1P4PP/1K3P2/8/8 b - - 0 1 |

## is the slow tail the same positions in both clocked runs? (top 20 by wall time)
| overlap of the two top-20 sets | 6 of 20 |
| indices only in 1000 ms top-20 | [9, 34, 40, 42, 55, 70, 77, 99, 115, 116, 127, 131, 157, 191] |
| indices only in 10000 ms top-20 | [17, 57, 79, 95, 103, 114, 120, 128, 135, 137, 141, 158, 186, 197] |
```

## Table 3 — bestmove legality (pasted output of `python3 check_legal.py raw2`)

```
| file | searches | illegal or missing bestmove |
|---|---|---|
| base_a.jsonl | 200 | 0 |
| base_b.jsonl | 200 | 0 |
| mt500.jsonl | 200 | 0 |
| tc1000.jsonl | 200 | 0 |
| tc10000.jsonl | 200 | 0 |

TOTAL searches 1000, bad 0
```

## Table 4 — measured wall time against the engine's OWN clock plan (`python3 limits_vs_wall.py raw2`)

`plan_clock_budget` in `include/forge/clock_plan.hpp` (lines 27-50), called from `search.cpp:2113`
`clock_plan_for`, with the defaults the engine printed: `Move Overhead 10`, `TmSoftDivisor 22`,
`TmIncrementPercent 75`, `TmHardPercent 60`, `TmHardSoftMultiple 5`. Movetime bypasses the plan:
`search.cpp:2191-2193` sets `hard = max(1, movetime - overhead)`.

```
| run | engine soft ms | engine hard ms | median wall | p99 wall | max wall | n over hard | n over soft |
|---|---|---|---|---|---|---|---|
| movetime 50 | 40 | 40 | 40.5 | 41.0 | 47.2 | 196 | 196 |
| movetime 500 | 490 | 490 | 490.5 | 490.9 | 491.1 | 196 | 196 |
| wtime 1000 inc 10 | 52 | 260 | 39.6 | 153.2 | 198.6 | 0 | 63 |
| wtime 10000 inc 100 | 529 | 2645 | 344.7 | 1334.9 | 2425.7 | 0 | 46 |

## how much of the hard limit is used (movetime runs: hard = movetime - Move Overhead 10)
| movetime 50 | wall/hard median 1.012 | wall/hard max 1.181 |
| movetime 500 | wall/hard median 1.001 | wall/hard max 1.002 |
| wtime 1000 inc 10 | wall/hard median 0.153 | wall/hard max 0.764 |
| wtime 10000 inc 100 | wall/hard median 0.131 | wall/hard max 0.917 |
```

## Table 5 — first (contaminated) run vs the clean re-run (`python3 job1/contamination.py .`)

```
| run | first run n | first median | first p99 | first max | clean n | clean median | clean p99 | clean max | median moved by |
|---|---|---|---|---|---|---|---|---|---|
| movetime 50 baseline A | 200 | 40.4 | 41.0 | 42.6 | 200 | 40.5 | 41.0 | 47.2 | +0.1 ms |
| movetime 500 | 200 | 490.5 | 490.9 | 494.5 | 200 | 490.5 | 490.9 | 491.1 | -0.0 ms |
| wtime 1000 inc 10 | 200 | 38.9 | 128.9 | 155.4 | 200 | 39.6 | 153.2 | 198.6 | +0.8 ms |
| wtime 10000 inc 100 | 1 | 329.6 | 329.6 | 329.6 | 200 | 344.7 | 1334.9 | 2425.7 | +15.1 ms |
```

## Findings

### 08-F1 — on a clock, the tail is ~4x the median and the engine never stops at its own soft limit
10,000 ms clock: plan soft 529 ms / hard 2645 ms. Measured median 344.7 ms, p99 1334.9 ms, largest 2425.7 ms.
46 of 200 searches ran past the soft limit (up to 4.6x it); none passed the hard limit.
1,000 ms clock: plan soft 52 / hard 260; measured median 39.6, p99 153.2, largest 198.6; 63 of 200 past soft.
Show it again:

    cd forge-combo29/swarm/08/job1 && python3 limits_vs_wall.py raw2

Why it matters: one search using 2.4 s of a 10 s clock is a fifth of the clock on one move. In a real game
that repeats. The hard limit did hold in all 400 clocked searches, so this is a tail-quality finding, not a
demonstrated loss on time at these clocks (see REPORT_job2.md for the small-clock end).

### 08-F2 — `go movetime T` searches for T - Move Overhead, so `movetime 50` gives 40 ms of search
200 searches at `go movetime 50`: median 40.5 ms, p99 41.0, max 47.2. 200 at `go movetime 500`: median 490.5,
max 491.1. The engine sets `hard = max(1, movetime - overhead)` with `Move Overhead` defaulting to 10
(`search.cpp:2191-2193`), so both land just OVER 40 and 490 and never over 50 and 500. The overshoot past its
own limit is 1.0 % median at movetime 50 and 0.1 % at movetime 500 — the stop check is on the node path.
Show it again:

    cd forge-combo29/swarm/08/job1 && python3 analyse_job1.py raw2

Consequence: a cross-engine "movetime 50" match gives Forge 20 % less thinking time than a rival that uses
the whole 50 ms. Not a fault; a comparison trap.

### 08-F3 — one of the 200 timing positions is answered from the opening book in 0.04 ms
Index 3 of the O set (`r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8`) is in the built-in
book: the engine prints `info string book move e1g1` and returns in 0.02-0.36 ms in every run. `OwnBook`
defaults to true, so a latency harness that leaves it on mixes book answers into search latency.
Show it again:

    cd forge-combo29/swarm/08/job1 && python3 count_book.py ~/builds/release/forge OG200.fens /tmp/book.txt

    printf 'uci\nisready\nucinewgame\nisready\nposition fen r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8\nisready\ngo movetime 50\nquit\n' | ~/builds/release/forge | grep -E 'book|bestmove'

### 08-F4 — two identical runs of the same 200 searches agree to 0.20 %
Baseline A total 8013.03 ms, baseline B 7996.66 ms, difference 16.37 ms (0.20 %); medians 40.5 vs 40.4 ms.
So on this 4-core box a difference under about 1 % of total time is noise, and a speed claim needs more than
one run per side.
Show it again:

    cd forge-combo29/swarm/08/job1 && python3 analyse_job1.py raw2

## Suspicions, not proven
- The clock tail (08-F1) is probably depth-dependent escalation on sharp positions: the slow set does not
  repeat between the 1 s and the 10 s runs, and the extremes are endgames and imbalanced middlegames. NOT
  shown — I did not instrument the extension logic.
- Some of the p99 may be the 4-core box's own scheduling noise (a cloud VM neighbour). Reduced but not
  eliminated by the guard.

## What I did NOT do
- No sanitizer run: area 8 does not ask for one and a sanitizer build changes timings. No sanitizer claim.
- Did not test `movestogo` here (that is job 3), and did not test Threads > 1.
- Did not measure CPU steal, and did not pin the process to a core.
- Did not re-run job 1 a third time after the clean run.

## What I am NOT sure about
- My prediction said `movetime 50` would give a median of 50-62 ms with a kill at < 40 ms. Measured 40.5 ms:
  inside the kill line by 0.5 ms, and only because of the Move Overhead subtraction I had not accounted for.
  The prediction's mechanism was wrong; its kill range very nearly fired on a correct measurement.
- Table 4's soft/hard numbers are recomputed arithmetic from the quoted formula, not read out of a running
  engine.

## Times
see stamps2.txt (a `date -u` line after every part) and stamps.txt (the first, contaminated run).

## Last command output

```
$ git status --short
 M forge-combo29/swarm/08/REPORT_job1.md
 M forge-combo29/swarm/08/job1/analyse_job1.py
 M forge-combo29/swarm/08/job1/limits_vs_wall.py
 M forge-combo29/swarm/08/job1/make_report.sh
 M forge-combo29/swarm/08/job1/raw/tc1000.jsonl
 M forge-combo29/swarm/08/job1/raw/tc10000.jsonl
 M forge-combo29/swarm/08/job1/run_job1.log
 M forge-combo29/swarm/08/job1/stamps.txt
?? forge-combo29/swarm/08/job1/contamination.py
?? forge-combo29/swarm/08/job1/raw2/
?? forge-combo29/swarm/08/job1/run_clean.log
?? forge-combo29/swarm/08/job1/run_clean.sh
?? forge-combo29/swarm/08/job1/stamps2.txt
?? forge-combo29/swarm/08/job2/OG200.fens
?? forge-combo29/swarm/08/job2/analyse_job2.py
?? forge-combo29/swarm/08/job2/probe_reserve.sh
?? forge-combo29/swarm/08/job2/probe_reserve.txt
?? forge-combo29/swarm/08/job2/raw/
?? forge-combo29/swarm/08/job2/raw2/
?? forge-combo29/swarm/08/job2/run.log
?? forge-combo29/swarm/08/job2/run_job2.sh
?? forge-combo29/swarm/08/job2/stamps.txt
?? forge-combo29/swarm/08/job2/stamps2.txt
$ ls forge-combo29/swarm/08/job1/raw2
analysis_table.txt
analysis_tail.txt
base_a.jsonl
base_b.jsonl
contamination_table.txt
exe_path.txt
exe_sha256.txt
legal_table.txt
limits_table.txt
mt500.jsonl
tc10000.jsonl
tc1000.jsonl
```
