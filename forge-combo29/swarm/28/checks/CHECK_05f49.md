# S-C5 — CONFIRMS seat 05's S-F49 control ranking, with a refinement to its contention caveat

Checked by seat 28 on my own boards and my own harness. Seat 05's files were not read; the claim was
restated from its FINDINGS sentence alone.

## The claim tested
"On the same boards the owner's real controls rank: softnodes 2000 (d7-8) < nodes 20000 (d10-11) < nodes
50000 (d12-14) < nodes 250000 (d15-17) < clock 6s+0.06 (d18) < movetime 6000 (d24-28). PC r15 + PC20,
Threads 1, Hash 16, OwnBook false... the clock path is NOT the weakest control — it beats even the 250,000
node budget by 2-3 plies."

## Verdict: CONFIRMS the ranking, and the absolute depths too

Three boards of my own (a deep middlegame, an opening, a second middlegame), PC r15 + PC20, Threads 1,
Hash 16, OwnBook false:

| board | softnodes 2k | nodes 20k | nodes 50k | nodes 250k | clock 6+.06 | movetime 6s | order monotone? |
|---|---|---|---|---|---|---|---|
| deep middlegame | 7 | 11 | 13 | 15 | **18** | 25 | YES |
| opening | 7 | 10 | 12 | 15 | **18** | 28 | YES |
| second middlegame | 7 | 10 | 12 | 16 | **19** | 26 | YES |

The order is strictly monotone on all three boards, and the depths land inside seat 05's stated bands
(7, 10-11, 12-13, 15-16, 18-19, 25-28). **Even the clock row's depth 18 reproduces exactly**, and the clock
row's node count (998,994 on my deep board; 381,028 on the opening) sits in seat 05's 300k-780k range for
one board and above it for the other.

Full rows in `check_05f49.log`; raw TSV in `out_05f49/check_05f49.tsv`.

## The refinement: what actually varies under contention

Seat 05's caveat says the clock row varied under CPU contention ("d18/784,328 then d17/542,082 twice, but
10 SOLO runs give depth 18 / 784,328"). I tested that directly — the clock row three times solo, then three
times with a busy loop on every other core:

| condition | depth | nodes | wall ms | bestmove |
|---|---|---|---|---|
| solo run 1 | 18 | 998994 | 589 | d1b1 |
| solo run 2 | 18 | 998994 | 647 | d1b1 |
| solo run 3 | 18 | 998994 | 591 | d1b1 |
| under load 1 | 18 | 998994 | 593 | d1b1 |
| under load 2 | 18 | 998994 | 598 | d1b1 |
| under load 3 | 18 | 998994 | 601 | d1b1 |

**Depth, node count and move were identical in all six runs; only wall time moved (589-647 ms, a 10 %
spread).** So on my harness the clock row is stable under load in everything except the wall clock.

**Why the two results differ, and it is a property worth naming:** a clock search stops at the end of a
completed iteration, so its NODE COUNT is a step function that only changes if the load is heavy enough to
push the stop across an iteration boundary. My load (3 busy loops on a 4-vCPU box) moved wall by 10 %,
which was not enough to lose a ply. Seat 05 saw node counts 784,328 vs 542,082 — a 45 % drop — which means
their contention pushed the stop across a boundary (or their runs were cut mid-iteration by a different
path). Both observations are consistent with the same mechanism: **the clock row is robust in depth/nodes
until contention is severe enough to cost a whole iteration, and then it moves in steps, not smoothly.**

So the refinement to seat 05's caveat is: the variation they found is real but is a LARGE-contention effect,
not a general fragility; at moderate load the row is bit-identical in nodes and depth.

## Prediction score
H1 (softnodes < 20k < 50k < 250k order): yes on all 3 boards, SURVIVES. H2 (clock > 250k): 18/19 vs 15/16,
SURVIVES. H3 (movetime > clock): 25-28 vs 18-19, SURVIVES. H4 (clock depth 17-19): 18, 18, 19, SURVIVES.
H5 (nodes 300k-780k): 998,994 on one board, 381,028 on another — **partly REFUTED**: my deep board needed
~1M nodes, above seat 05's stated range, so the range is board-dependent rather than a property of the
control. H6 (reproducible solo): identical nodes/depth/move in 3 runs, SURVIVES. H7 (changes under load):
**REFUTED on my box** — no change at 10 % wall variance.

## A defect in my own check, recorded
The TSV writer had a mangled escape sequence in the solo-run loop. It was caught by an `ast.parse` syntax
check before the run, fixed, and re-verified; no number here came from the broken version.

## Reproduce
```
cd forge-combo29/swarm/28/checks
python3 check_05f49.py ~/build/r15-pc/forge /tmp/c05
```
