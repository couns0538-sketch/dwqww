# 19-C53 — the node saving is real, but only ~2.8 % of it survives into wall time; and my own 19-C35 was measured on the wrong workload

## The question, and why it was worth asking
Three established facts implied something none of them stated:
1. **PC20 searches 12.4 % fewer nodes** at matched depth (I measured 0.9090 on 119 positions; seat 29 had 10.7–11.9 %).
2. **PC20's per-node cost is at most ~1.2 % higher** — my own 19-C35, from `bench 16`, ratio **1.0119**, CI
   [0.9997, 1.0241].
3. **But no wall-time difference was found** — seat 29's 29-F56, n = 40, ratio 1.0255, **CI [0.9085, 1.1647]**.

**1 and 2 predict ≈11 % less wall time. 3 found none.** All three could not be right.

## Power first, per trap 16 (and it changed the design)
From seat 29's CI, the implied sd of ln(paired time ratio) is **0.401**. At 80 % power:
detect 12 % → **n = 87 pairs**; 8 % → 197; 5 % → 504. **So 29-F56's n = 40 could not have detected a 12 %
effect**, and its null was uninformative. I committed to ≥120 pairs before running.

**My prediction (committed alone at `b1ae9433d`): ratio 0.88–0.93, significantly below 1.0, contradicting 29-F56.**
**RESULT: 0.9728 at depth 12, n = 119 — my prediction was WRONG**, though in the direction of PC20 still winning.

## What the measurement shows
Fixed depth 12, Threads 1, Hash 16, ABBA, fresh process per search, 119 usable of 120:

| quantity | result |
|---|---|
| node ratio (PC20/S14) | **0.9090 → 12.39 % fewer nodes** |
| engine-reported time ratio | **0.9728**, CI [0.9014, 1.0497] |
| external wall time (incl. startup) | 1.0070, CI [0.9622, 1.0539] |

**The node saving does NOT transfer proportionally.** PC20 is ~2.8 % faster, not ~12 %.

## Why — measured, not inferred
Two noisy ratios implied a per-node cost of ~1.066, but that is an inference. So I measured it directly at a
**fixed node budget**, where equal nodes make the time ratio *equal* the per-node cost:

**19-C53b — fixed `go nodes 50000`, 180 positions, ABBA:**

| | S14 | PC20 | ratio |
|---|---|---|---|
| node totals | 6,721,052 | 6,591,407 | 0.9807 (budget-matched) |
| ms per 1M nodes | 51.66 | 55.24 | **1.0693** |
| per-position ln-ratio | | | **1.0773, CI [1.0670, 1.0876]** |

**PC20 costs ~7 % MORE per node on real positions.** (My first attempt at this used 4 positions and gave 1.0089 —
pure small-sample noise, and exactly the error this thread has been about. n = 180 settles it.)

**The reconciliation closes exactly:**
**0.9090 (nodes) × 1.0693 (per node) = 0.9720 predicted time ratio** vs **0.9728 observed.** Two independent
measurements, agreeing to 0.1 %.

## This qualifies my own 19-C35 — and I need to say so plainly
**19-C35 measured per-node cost on `bench 16` and reported 1.0119, CI [0.9997, 1.0241], concluding "at most ~1.2 %
slower". That interval does NOT overlap 1.0773 [1.0670, 1.0876].**

**`bench` is not a representative workload for per-node cost.** It replays a fixed position sequence with its own
`Searcher(16)` and a specific move mix; PC20's extra per-node work (`CuckooRep` maintenance, `HistRework` blending,
`TtPruneV2`/`CorrHistV2` probes) is exercised at a different rate there than on real game positions. **So 19-C35's
number was correct for bench and wrong as a general claim about PC20**, and I published it as the latter.

**Corrected statement:** *PC20 costs ~7 % more per node on real positions (1.0693, CI [1.0670, 1.0876], n=180)
while searching ~12 % fewer nodes at fixed depth; the net wall-time gain is ~2.8 %. On `bench` the per-node
penalty is only ~1.2 %, which is why bench-based reasoning overstated the speed win.*

## Also: a fixed-overhead test that pointed the wrong way, kept in the record
I tested whether the excess was a **fixed per-search cost** (which would amortise as the search grew) by measuring
the per-node ratio at budgets 2,000 / 5,000 / 20,000 / 100,000. **The ratio ROSE with budget (1.038 → 1.083), the
opposite of a fixed overhead**, which is consistent with a genuine per-node penalty that compounds. That is the
outcome that led me to the direct fixed-node measurement above. Recorded because the first hypothesis was wrong
and the test is what corrected it.

## For the owner, in one line
**PC20 at fixed depth is about 2.8 % faster in wall time, not the 12 % its node count suggests** — because it pays
~7 % per node. At matched *nodes* (his match condition) that means **an S14-vs-PC20 match at equal nodes is not an
equal-time match: PC20 spends ~7 % more time to reach the same node count.** That is a real, quantified cost of
the switches, and it is the number to weigh against PC20's depth advantage at 8k–20k.
