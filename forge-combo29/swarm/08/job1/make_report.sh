#!/usr/bin/env bash
# make_report.sh — assembles REPORT_job1.md. Every table below is the pasted output of a committed
# script (analyse_job1.py, analyse_job1_tail.py, check_legal.py, limits_vs_wall.py) reading the raw files.
set -u
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"
R=../REPORT_job1.md

cat > "$R" <<'HEAD'
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
HEAD
{
  echo
  echo "## How sure"
  echo "Latency numbers: sure — 1,000 searches, each timed with \`time.monotonic()\` from writing the \`go\` line to"
  echo "reading \`bestmove\`, two identical baseline runs disagreeing by 0.11 % of total time."
  echo "The soft/hard limits in the table below are RECOMPUTED from the formula in \`include/forge/clock_plan.hpp\`"
  echo "with the defaults read out of the engine's own \`uci\` answer; they are arithmetic, not measured, and the"
  echo "caveat is that the formula does not implement every escape the search itself may take."
  echo "The attribution of each slow tail to a named source is NOT sure: the tail table reports which positions"
  echo "are slow, not why."
} >> "$R"

cat >> "$R" <<'H1'

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
H1
sed -n '/^## runs on the machine/,$p' raw/analysis_table.txt >> "$R"
cat >> "$R" <<'H2'
```

## Table 2 — the tail and the instant searches (pasted output of `python3 analyse_job1_tail.py raw`)

```
H2
cat raw/analysis_tail.txt >> "$R"
cat >> "$R" <<'H3'
```

## Table 3 — bestmove legality (pasted output of `python3 check_legal.py raw`)

```
H3
cat raw/legal_table.txt >> "$R"
cat >> "$R" <<'H4'
```

## Table 4 — measured wall time against the engine's OWN clock plan (pasted output of `python3 limits_vs_wall.py raw`)

The plan is `plan_clock_budget` in `include/forge/clock_plan.hpp` (lines 27-50) called from
`search.cpp:2113` `clock_plan_for`, with `Move Overhead 10`, `TmSoftDivisor 22`, `TmIncrementPercent 75`,
`TmHardPercent 60`, `TmHardSoftMultiple 5` — the defaults the engine itself printed in its `uci` answer.

```
H4
cat raw/limits_table.txt >> "$R"
cat >> "$R" <<'H5'
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
H5
{
  echo
  echo "## Last command output"
  echo
  echo '```'
  echo '$ git status --short'
  git -C /agent/repos/dwqww status --short | sed -n '1,40p'
  echo '$ ls forge-combo29/swarm/08/job1'
  ls -1 .
  echo '$ ls forge-combo29/swarm/08/job1/raw'
  ls -1 raw
  echo '```'
} >> "$R"
echo "wrote $R"
