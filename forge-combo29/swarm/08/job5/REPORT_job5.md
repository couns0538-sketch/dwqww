# REPORT job 5 — AREA 8 (THE CLOCK) — the tail across clock sizes — seat 08

## What was asked
Is the clock tail (08-F1: p99 ~4x median) a fixed latency or does it scale with the clock? 200 searches at each
of wtime/btime 200, 500, 1000, 3000, 10000, 30000 ms, winc 0, OwnBook false, guarded run.

## The answer (one line each)
- **The tail scales with the clock, almost exactly.** A 10x clock gives a 11.9x p99 and a 8.8x median; a 30x
  clock gives 31.0x p99 and 24.2x median. p99/median stays 3.1-4.8x at every clock size.
- **The median is a near-constant fraction of the planned soft limit**: 100 %, 80 %, 77 %, 75 %, 67 %, 61 % from
  the 200 ms to the 30 s clock — a 1.6x spread over a 150x range of clocks. So 08-F9's "engine spends a
  fraction of soft" holds across clock sizes, and shrinks slowly as the budget grows.
- **No search exceeded its own clock at any size**, and the three "over hard limit" rows are 0.4-0.6 ms over —
  the fixed stop-check latency, not a real overrun.

## How sure
Sure of the scaling: 1,200 searches, six clock sizes, guarded start, OwnBook false so no book answer is in the
set. Sure of the medians and p99 (200 samples per clock).
Not sure that the 200 ms clock's 100 % median/soft is meaningful: soft there is 8 ms and the measurement floor
is ~0.1 ms, so a 1 ms quantisation of the engine's own clock is 12 % of the plan.

## Honesty numbers
/home/ubuntu/builds/release/forge, sha256 e06310eca3...a83; bench 11/13/16 = 312,866 / 862,329 / 3,024,920 and
perft 5 = 4,865,609, all exact. job5/raw/.meta holds the path, sha256, option lines and the guard line. The
prediction was pushed alone at 21:40:58Z before the first search.

## The table (`python3 analyse_job5.py raw`, pasted)

See job5/raw/analysis_table.txt.

## Findings
- **08-F11** (new): the tail scales linearly with the clock; p99/median constant at 3.1-4.8x.
- **08-F9** extended: median/soft is 61-100 % across a 150x clock range, so the "fraction of soft" statement
  generalises and slowly shrinks.

## What I did NOT do
- No increment in this sweep (job 2 covered winc).
- Did not test clocks above 30 s (a 60 s clock would take ~7 minutes for 200 searches at the median).
- No sanitizer.

## What I am NOT sure about
- My prediction said the 30 s clock p99 would be 2500-5000 ms; measured 3710 — inside. It also predicted
  p99/median 3-6x; measured 4.5, inside at every clock. The one prediction that missed is the 200 ms median:
  I said 3-9 ms, measured 8.0 — inside but at the top edge.
