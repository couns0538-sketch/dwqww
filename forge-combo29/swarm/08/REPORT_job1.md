# REPORT job 1 — AREA 8 (THE CLOCK) — seat 08

## What was asked
Wall-clock latency of 200 searches (first 100 of O + first 100 of G) at four controls —
`go movetime 50`, `go movetime 500`, `go wtime 1000 btime 1000 winc 10 binc 10`,
`go wtime 10000 btime 10000 winc 100 binc 100` — with the two equal `movetime 50` baseline runs FIRST
so their difference can be reported; median / 99th percentile / largest / searches over the limit; and
how many cores the machine has.

## The answer (one line each)
- `movetime` is honoured tightly and sits slightly UNDER the number asked, not over: median 40.4 ms for
  `movetime 50` and 490.5 ms for `movetime 500` — the engine subtracts the default `Move Overhead` of 10 ms
  from the movetime before it searches, so it stops at 40 and 490.
- Clocked play (`wtime/btime`) is far looser than the movetime path: median 39.1 ms on a 1000 ms clock but a
  99th percentile of 130 ms and a worst case of 194 ms, and on a 10000 ms clock a median of 345 ms with a
  worst case of 2411 ms. All of it stays inside the engine's OWN hard limit (260 ms and 2645 ms); about a
  quarter to a third of the searches run past its own soft limit (64 of 200 at 1 s, 45 of 200 at 10 s).
- The machine has 4 cores (`nproc` = 4).

## How sure
Latency numbers: sure — 1,000 searches, each timed with `time.monotonic()` from writing the `go` line to
reading `bestmove`, two identical baseline runs disagreeing by 0.11 % of total time.
The soft/hard limits in the table below are RECOMPUTED from the formula in `include/forge/clock_plan.hpp`
with the defaults read out of the engine's own `uci` answer; they are arithmetic, not measured, and the
caveat is that the formula does not implement every escape the search itself may take.
The attribution of each slow tail to a named source is NOT sure: the tail table reports which positions
are slow, not why.

## Honesty numbers
Build: /home/ubuntu/builds/release/forge, sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83.
bench 11 = 312,866 / bench 13 = 862,329 / bench 16 = 3,024,920 / perft 5 = 4,865,609 — all four exact.
See HONESTY.txt and honesty/out_release/. Every search below ran on THAT exe (raw/.meta records the path it
started and its sha256).

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| R position set with SEED 801, FENs written before use | done | job1/R_seed801.fens (500 lines), job1/gen_R.py | 500 positions, 11 random games, one position every 7 plies |
| prediction committed and pushed ALONE before measuring | done | job1/prediction.txt (commit 841f0b9f5) | pushed 2026-11-16T21:07:32Z, before the first search |
| two equal baseline runs at movetime 50, first | done | job1/raw/base_mt50_a.jsonl, base_mt50_b.jsonl | 200 + 200 searches; totals differ by 0.11 % |
| movetime 500, 200 searches | done | job1/raw/mt500.jsonl | median 490.5 ms, max 494.5 ms |
| wtime/btime 1000 inc 10, 200 searches | done | job1/raw/tc1000.jsonl | median 39.1 ms, p99 130.2 ms, max 194.4 ms |
| wtime/btime 10000 inc 100, 200 searches | done | job1/raw/tc10000.jsonl | median 345.5 ms, p99 1306.1 ms, max 2410.7 ms |
| every bestmove legal (python-chess) | done | job1/raw/legal_table.txt | 1000 of 1000 legal, 0 illegal |
| how many cores | done | job1/raw/analysis_table.txt | nproc = 4 |
| book-answer contamination of the timing set | done | job1/raw/book_count.txt | 1 of 200 positions is answered from the book |

## Table 1 — the four controls (pasted output of `python3 analyse_job1.py raw`)

```
## runs on the machine (nproc = 4)

| run                        |   n  | median ms | p99 ms  | largest ms | >limit+50ms |
|----------------------------|------|-----------|---------|------------|-------------|
| base A  movetime 50        |  200 |     40.4 |     41.0 |      42.6 |        0 |     0 |
| base B  movetime 50        |  200 |     40.5 |     40.9 |      41.1 |        0 |     0 |
| movetime 500               |  200 |    490.5 |    490.9 |     494.5 |        0 |     0 |
| wtime/btime 1000 inc10     |  200 |     39.1 |    130.2 |     194.4 |       13 |    13 |
| wtime/btime 10000 inc100   |  200 |    345.5 |   1306.1 |    2410.7 |       61 |    61 |

## baseline repeatability (two identical runs of 200 x movetime 50)
| quantity | run A | run B | difference |
|---|---|---|---|
| median wall ms | 40.4 | 40.5 | 0.1 |
| total ms | 7994.26 | 8003.06 | 8.80 |
| mean wall ms | 39.97 | 40.02 | 0.04 |
| largest ms | 42.6 | 41.1 | 1.5 |
| total relative difference | | | 0.11 % |

## distribution detail, wall ms
| run | min | p10 | p50 | p90 | p99 | max | mean | sd |
|---|---|---|---|---|---|---|---|---|
| base A  movetime 50 | 0.0 | 40.2 | 40.4 | 40.7 | 41.0 | 42.6 | 40.0 | 3.9 |
| base B  movetime 50 | 0.4 | 40.3 | 40.5 | 40.7 | 40.9 | 41.1 | 40.0 | 3.9 |
| movetime 500 | 0.0 | 490.3 | 490.5 | 490.8 | 490.9 | 494.5 | 481.0 | 66.6 |
| wtime/btime 1000 inc10 | 0.4 | 25.5 | 39.1 | 79.0 | 130.2 | 194.4 | 47.2 | 26.1 |
| wtime/btime 10000 inc100 | 0.2 | 254.5 | 345.5 | 724.8 | 1306.1 | 2410.7 | 437.6 | 268.1 |

## overruns (wall > budget + 50 ms) and over budget exactly
| run | budget ms | n over budget+50 | n over budget | worst wall ms | worst excess ms |
|---|---|---|---|---|---|
| base A  movetime 50 | 50 | 0 | 0 | 42.6 | -7.4 |
| base B  movetime 50 | 50 | 0 | 0 | 41.1 | -8.9 |
| movetime 500 | 500 | 0 | 0 | 494.5 | -5.5 |
| wtime/btime 1000 inc10 | 41 | 13 | 93 | 194.4 | 153.1 |
| wtime/btime 10000 inc100 | 413 | 61 | 75 | 2410.7 | 1997.4 |
```

## Table 2 — the tail and the instant searches (pasted output of `python3 analyse_job1_tail.py raw`)

```
## instant searches (wall < 5 ms) — which ones and why
| run | i | wall ms | bestmove | fen |
|---|---|---|---|---|
| base_mt50_a.jsonl | 3 | 0.04 | bestmove e1g1 | r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8 |
| base_mt50_b.jsonl | 3 | 0.37 | bestmove e1g1 | r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8 |
| mt500.jsonl | 3 | 0.04 | bestmove e1g1 | r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8 |
| tc1000.jsonl | 3 | 0.36 | bestmove e1g1 | r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8 |
| tc10000.jsonl | 3 | 0.20 | bestmove e1g1 | r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8 |

## the 10 slowest searches of the 10000 ms clock run
| i | wall ms | move-overhead-adjusted budget ms | bestmove | fen |
|---|---|---|---|---|
| 107 | 2410.7 | 413 | bestmove g5h5 | 8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1 |
| 137 | 1445.2 | 413 | bestmove h8h1 | 7r/2k2p2/2p3P1/2Ppn3/PP2p1b1/4P3/4BK2/R6R b - - 0 1 |
| 120 | 1304.7 | 413 | bestmove e6d6 | 8/8/4K1k1/8/4N1P1/8/1b6/8 w - - 0 1 |
| 128 | 1226.4 | 413 | bestmove a4a5 | 8/p7/5pk1/7p/r2NKP2/4P1P1/PR5P/8 b - - 0 1 |
| 158 | 1166.7 | 413 | bestmove e3f4 | 8/6kp/8/1p1r1p2/p7/2bBBP1P/P3K3/8 w - - 0 1 |
| 186 | 1144.2 | 413 | bestmove d8d7 | 3r4/p7/5kp1/1p3n2/1P3R1P/P4N2/2K2P2/8 b - - 0 1 |
| 141 | 1119.9 | 413 | bestmove d3d2 | 1kr4n/1ppQ4/4p3/p6P/3P4/3q1RP1/6PK/4R3 b - - 0 1 |
| 57 | 1019.1 | 413 | bestmove c5b6 | r1bqk1nr/pppp1pp1/2n4p/2b1p3/2B1P3/2P2N2/PP1P1PPP/RNBQ1RK1 b kq - 0 5 |
| 122 | 1015.1 | 413 | bestmove g3h4 | 8/7p/6k1/1p1r1p2/pb3P2/3BK1BP/P7/8 w - - 0 1 |
| 68 | 978.3 | 413 | bestmove e7e5 | rnbqkb1r/ppp1pppp/5n2/8/8/5Q2/PPPP1PPP/RNB1KBNR b KQkq - 2 4 |

## the 10 slowest searches of the 1000 ms clock run
| i | wall ms | bestmove | fen |
|---|---|---|---|
| 99 | 194.4 | bestmove b1c3 | rnbqkbnr/ppp3pp/4p3/3p1p2/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 0 4 |
| 191 | 158.3 | bestmove g2g4 | 8/p3kpp1/1p2p2p/1b1pP3/5K1P/P3P3/1P4P1/2N5 w - - 0 1 |
| 187 | 129.9 | bestmove f4f3 | 8/p4kp1/8/3b2PN/5p2/P6P/7K/4R3 b - - 0 1 |
| 55 | 124.8 | bestmove c2c4 | r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/3P1P2/PPP3PP/RNBQKBNR w KQkq - 1 4 |
| 40 | 118.2 | bestmove b8d7 | rn1qk1nr/pbp2pbp/1p1pp1p1/8/2PPP3/2N2N2/PP2BPPP/R1BQ1RK1 b kq - 1 7 |
| 199 | 110.9 | bestmove b5c5 | 8/6qp/8/1K6/6Pb/7P/8/1k6 w - - 0 1 |
| 122 | 110.1 | bestmove h3h4 | 8/7p/6k1/1p1r1p2/pb3P2/3BK1BP/P7/8 w - - 0 1 |
| 131 | 102.5 | bestmove c6d7 | 2rqr1k1/5pb1/2bpp1np/pp4p1/3PP1P1/P3B3/1PBQNPP1/4RRK1 b - - 0 1 |
| 157 | 100.8 | bestmove g6f6 | 8/8/6k1/Q7/1P4PP/1K3P2/8/8 b - - 0 1 |
| 116 | 98.9 | bestmove h5h6 | 8/8/4k3/3rp1RR/KP6/P2p4/6PP/2r5 w - - 0 1 |

## is the slow tail the same positions in both clocked runs? (top 20 by wall time)
| overlap of the two top-20 sets | 5 of 20 |
| indices only in 1000 ms top-20 | [9, 34, 40, 42, 55, 70, 80, 99, 106, 115, 116, 127, 131, 157, 191] |
| indices only in 10000 ms top-20 | [17, 18, 57, 68, 79, 110, 114, 120, 128, 135, 137, 141, 158, 186, 197] |
```

## Table 3 — bestmove legality (pasted output of `python3 check_legal.py raw`)

```
| file | searches | illegal or missing bestmove |
|---|---|---|
| base_mt50_a.jsonl | 200 | 0 |
| base_mt50_b.jsonl | 200 | 0 |
| mt500.jsonl | 200 | 0 |
| tc1000.jsonl | 200 | 0 |
| tc10000.jsonl | 200 | 0 |

TOTAL searches 1000, bad 0
```

## Table 4 — measured wall time against the engine's OWN clock plan (pasted output of `python3 limits_vs_wall.py raw`)

The plan is `plan_clock_budget` in `include/forge/clock_plan.hpp` (lines 27-50) called from
`search.cpp:2113` `clock_plan_for`, with `Move Overhead 10`, `TmSoftDivisor 22`, `TmIncrementPercent 75`,
`TmHardPercent 60`, `TmHardSoftMultiple 5` — the defaults the engine itself printed in its `uci` answer.

```
| run | engine soft ms | engine hard ms | median wall | p99 wall | max wall | n over hard | n over soft |
|---|---|---|---|---|---|---|---|
| movetime 50 | 40 | 40 | 40.4 | 41.0 | 42.6 | 196 | 196 |
| movetime 500 | 490 | 490 | 490.5 | 490.9 | 494.5 | 196 | 196 |
| wtime 1000 inc 10 | 52 | 260 | 39.1 | 130.2 | 194.4 | 0 | 64 |
| wtime 10000 inc 100 | 529 | 2645 | 345.5 | 1306.1 | 2410.7 | 0 | 45 |

## how much of the hard limit is used (movetime runs: hard = movetime - Move Overhead 10)
| movetime 50 | wall/hard median 1.010 | wall/hard max 1.065 |
| movetime 500 | wall/hard median 1.001 | wall/hard max 1.009 |
| wtime 1000 inc 10 | wall/hard median 0.150 | wall/hard max 0.748 |
| wtime 10000 inc 100 | wall/hard median 0.131 | wall/hard max 0.911 |
```

## Findings

### 08-F1 — the clock tail is 5x the median, and the engine never stops at its own soft limit
On a 10,000 ms clock the engine's plan is soft 529 ms / hard 2645 ms. Measured: median 345 ms, 99th
percentile 1306 ms, largest 2411 ms — 45 of 200 searches ran past the soft limit by up to 4.6x, and none
passed the hard limit. On a 1,000 ms clock: plan soft 52 / hard 260, measured median 39.1, p99 130.2,
largest 194.4 — 64 of 200 past soft.
Show it again:

    cd forge-combo29/swarm/08/job1 && python3 limits_vs_wall.py raw

Why it matters: a tail of one second on a 10-second clock is one fifth of the clock spent on a single move,
and the search will do that repeatedly; that is where a game is lost on time, not in the median.
(The engine's own hard limit kept every single search inside the clock, so this is a strength-of-tail
finding, not a lost-on-time finding.)

### 08-F2 — the `movetime` path subtracts Move Overhead, so `movetime 50` searches for 40 ms
`go movetime 50` produced a median wall of 40.4 ms (p99 41.0, max 42.6) on 200 searches; `go movetime 500`
produced 490.5 ms (p99 490.9, max 494.5). The engine sets `hard = max(1, movetime - overhead)` with
`overhead = Move Overhead = 10` (`search.cpp:2191-2193`), so both are ~1 % over 40 and 490 rather than over
50 and 500. The overshoot over the engine's own limit is 0.4 ms median at movetime 50 (1.0 %) and 0.5 ms at
movetime 500 (0.1 %): the stop check is on the node path and lands within about one node's time.
Show it again:

    cd forge-combo29/swarm/08/job1 && python3 analyse_job1.py raw

For a fixed-time test this matters: anyone comparing engines at "movetime 50" is giving Forge 40 ms of
search. Not a fault, but it makes cross-engine movetime comparisons unfair by 20 %.

### 08-F3 — one of the 200 timing positions is answered from the opening book, so its "latency" is 0.04 ms
Position index 3 of the O set (`r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8`) is in the
built-in book: the engine prints `info string book move e1g1` and returns in 0.04 ms, in all five runs.
`OwnBook` defaults to true, so any latency harness that does not send `setoption name OwnBook value false`
mixes book latency into search latency.
Show it again:

    cd forge-combo29/swarm/08/job1 && python3 count_book.py ~/builds/release/forge OG200.fens raw/book_count.txt

    printf 'uci\nisready\nucinewgame\nisready\nposition fen r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8\nisready\ngo movetime 50\n' | ~/builds/release/forge | grep -E 'book|bestmove'

### 08-F4 — two identical runs of the same 200 searches agree to 0.11 %
Baseline A total 7994.26 ms, baseline B 8003.06 ms, difference 8.80 ms (0.11 %); medians 40.4 vs 40.5 ms.
So any difference below about 1 % of total time on this machine is noise, and a "speed" claim on this
machine needs more than one run per side.
Show it again:

    cd forge-combo29/swarm/08/job1 && python3 analyse_job1.py raw

## Suspicions, not proven
- The clock tail (08-F1) is probably unstable-score extension: the tail positions are mostly sharp endgames
  and middlegames with material imbalance, and the slow set does not repeat between the 1 s and the 10 s clock
  runs (overlap of the top-20 sets was 5 of 20), which is what a depth-dependent escalation looks like. NOT
  shown: I did not read the extension logic and did not instrument it.
- The tail may also be the time check granularity on a 4-core box under load from my own harness; the box ran
  one engine process at a time and nothing else of mine, but a cloud VM neighbour can steal time. NOT shown.

## What I did NOT do
- I did not run any of this under a sanitizer: area 8 does not ask for it, and a sanitizer build changes the
  timings. No sanitizer claim is made anywhere in this report.
- I did not test `movestogo` (that is job 3) and did not test very small clocks (job 2).
- I did not test multi-threaded timing (`Threads` stayed 1 for every search here).
- I did not measure CPU steal or pin the process to a core.

## What I am NOT sure about
- My own prediction said `movetime 50` would give a median of 50-62 ms and named <40 ms as a kill. The
  measurement is 40.4 ms — just inside the kill line, and the reason is the Move Overhead subtraction I had not
  accounted for. The prediction was wrong in its mechanism even though it did not trip its own kill range.
- The soft/hard limits in Table 4 are recomputed arithmetic from the quoted formula. If `uci.cpp` adjusts
  `limits.time_ms` before the plan is made, the true limits differ; I read `uci.cpp:121-122` and saw no
  adjustment, but I did not trace every path.

## Times
see stamps.txt (a `date -u` line after every part).

## Last command output

```
$ git status --short
 M forge-combo29/swarm/08/HONESTY.txt
?? forge-combo29/swarm/08/REPORT_job1.md
?? forge-combo29/swarm/08/job1/G100.fens
?? forge-combo29/swarm/08/job1/O100.fens
?? forge-combo29/swarm/08/job1/OG200.fens
?? forge-combo29/swarm/08/job1/analyse_job1.py
?? forge-combo29/swarm/08/job1/analyse_job1_tail.py
?? forge-combo29/swarm/08/job1/check_legal.py
?? forge-combo29/swarm/08/job1/clock_latency.py
?? forge-combo29/swarm/08/job1/count_book.py
?? forge-combo29/swarm/08/job1/limits_vs_wall.py
?? forge-combo29/swarm/08/job1/make_report.sh
?? forge-combo29/swarm/08/job1/raw/
?? forge-combo29/swarm/08/job1/run_job1.log
?? forge-combo29/swarm/08/job1/run_job1.sh
?? forge-combo29/swarm/08/job1/stamps.txt
?? forge-combo29/swarm/08/job1/test3.fens
$ ls forge-combo29/swarm/08/job1
analyse_job1.py
analyse_job1_tail.py
check_legal.py
clock_latency.py
count_book.py
first200.fens
G100.fens
gen_R.py
limits_vs_wall.py
make_report.sh
O100.fens
OG200.fens
prediction.txt
raw
R_seed801.fens
run_job1.log
run_job1.sh
set_G.epd
stamps.txt
test3.fens
$ ls forge-combo29/swarm/08/job1/raw
analysis_table.txt
analysis_tail.txt
base_mt50_a.jsonl
base_mt50_b.jsonl
book_count.txt
exe_path.txt
exe_sha256.txt
legal_table.txt
limits_table.txt
mt500.jsonl
setup_counts.txt
tc10000.jsonl
tc1000.jsonl
```
