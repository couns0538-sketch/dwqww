# NOTES FOR THE FINAL BLOCK (seat 29, area 9 SPEED)
Draft material for the required `## <time> FINAL` STATUS.md block at the end of the 12-hour window
(2026-11-17T10:18Z). Kept separate so the FINAL block itself can be written quickly and completely.

## CORRECTION APPLIED TO THIS NOTE (29-F39 / 29-N20)
An earlier draft of these notes put "11.1 %" forward as *the* PC figure. **That was wrong to present as a single
number.** A 2x2 sweep on the same instrumented build shows the replacement-scan age/depth rate depends on DEPTH and
HASH together:

| Hash | depth | probes | scans entered | found empty | age/depth rate |
|---|---|---|---|---|---|
| 16 | 10 | 1,372,713 | 888,124 | 831,845 | **6.3 %** |
| 16 | 12 | 4,087,859 | 2,633,613 | 1,453,333 | **44.8 %** |
| 64 | 10 | 1,372,713 | 888,124 | 887,481 | **0.1 %** |
| 64 | 12 | 4,087,859 | 2,633,611 | 2,570,388 | **2.4 %** |

Probe counts are identical across Hash sizes at a given depth, so table size does not change the search at all — it
only changes how often a scan finds an EMPTY slot, i.e. whether the table is saturated.

## The two robust statements the FINAL should carry instead
1. **bench 13 reaches the age/depth replacement comparison 50 times in 861,904 probes (0.006 %)** — reproduced to the
   digit on my own counters, matching seat 19's 19-F18 bench figure.
2. **In real play at a saturated table it is reached far more often, and the exact share must be quoted with its
   depth and hash** (0.1 % to 44.8 % across the four cells above). Seat 19's 19-F18 54.7 % sits within that range:
   it is a different position set and a different saturation, NOT an error — their bench figure matches mine exactly.

## NAMED RULE FOR THE FINAL, to carry forward (29-N23)
**Sweep the second variable before any number reaches a summary.** Twice in one hour a single-cell percentage of mine
was wrong for the same reason: the replacement-scan rate (11.1 % was one cell of a 0.1-44.8 % range across depth and
hash) and the PC20 tree-size effect (19.5 % fewer nodes at depth 12, but **+2.3 % MORE at depth 10** and -14.1 % at
depth 14). Both were caught by varying one more axis before believing the first measurement. Before a figure goes
into a finding, a rule or a summary: measure it at another value of whatever it most plausibly depends on, and if the
answer moves, report the TABLE rather than the number. A single figure may stand only when the sweep shows it is
flat — and then the flatness is the finding. The depth-10 sign flip is the sharpest example: it says the PC20
switches are NOT free at low depth, which no single depth-12 number would ever have revealed.

## Headline results to list
- FIRST RULE (29-N19): a zero must always be a measurement, never a default; NOT FOUND + INCONCLUSIVE, never 0.
- 29-F35 rule: bench is not a representative workload for any slot-sensitive or TT-cost optimisation
  (96.0 % slot-0 hits vs 26/25/25/24 %; 0 vs 16,811 generation writes; 50 of 861,904 vs a high real-play rate).
- 29-F36 recommendation: picker scoring 2.91 % vs selection 0.77 % → reduce history reads per move, not the sort.
- 29-F16: PC r15 patch reproduces exactly; all eight known numbers match in all three regimes.
- 29-F19/F28/N16: my own TT patch REVERSES on the PC build (+0.320 %) and is non-additive (−0.872 % interaction);
  it is code cleanliness, not a speed win. Bench also flatters it ~3.7x (29-N18).
- 29-F22/F23/F24/F29/F30: `go softnodes` and `go nodes` contracts, determinism, overshoot.
- 29-F32: 6s+0.06 clock on the PC build — median 203 ms of a 6000 ms clock, 0 of 60 past soft or hard.
- 29-C6/C7/C8: confirmations of seat 05's S-F23 and of 19-F19 and 19-F18 (bench half to the digit).
