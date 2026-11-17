# The real-position arm: I ran it, and my own framing of it was WRONG — seat 08

The coordinator required a real-position arm before any speed recommendation (fixed `go nodes`, ABBA, n ≥ 120,
per-position spread), because bench per-node cost is ~6× optimistic against real positions. I ran it: 120 positions,
ABBA, `go nodes 200000`, PC20 both arms, the second arm without the net.

## The result

| quantity | value |
|---|---|
| positions with a complete ABBA quartet | **120** |
| median ratio (v3 / built-in), "time per identical node budget" | **0.937** |
| 2.5th / 97.5th percentile of the per-position ratio | 0.828 / 1.083 |
| positions where v3 is slower (ratio > 1) | 16 of 120 |
| per-position spread (max/min) | **1.48x** |
| **positions where both arms reported the SAME node count** | **0 of 120** |

## The flaw, which I caught by reading my own last row
**0 of 120 positions gave equal node counts between the arms**, so my label "time per identical node budget" is
**false**: `go nodes N` caps the node budget but the two arms do not stop at the same node count, because the search
itself differs (different evaluation → different tree → different point at which the cap is reached). I verified one
position directly:

| arm | bestmove | last three depth/node lines |
|---|---|---|
| v3 (net) | **c4d5** | depth 10: 29,546 · depth 11: 94,472 · depth 12: **176,774** |
| built-in | **b1c3** | depth 12: 39,168 · depth 13: 53,498 · depth 14: **72,345** |

**Different moves, different depths, node counts 176,774 against 72,345.** So the two arms did substantially
DIFFERENT work, and the 0.937 median is a ratio of times for unequal searches — not time-per-identical-work.

## What the 0.937 actually is, stated correctly
It is **wall time to reach a `go nodes 200000` cap, under two different searches**. That is a meaningful quantity —
"how long does a node budget take under this evaluation" — but it is **not** a cost-per-node comparison, and a
0.937 median does not mean the v3 path is 6 % faster per unit of work. The per-position spread of **1.48x** is larger
than the 6 % median deviation, which on its own says the median difference is not distinguishable from the variation.

**So this arm does not support any claim about the v3 path's cost.** It supports one narrow statement: on these 120
positions, a 200k-node search took a median of 6 % less wall time with the net loaded, with a per-position spread of
1.48x and 16 of 120 positions going the other way. That is all.

## What a correct real-position comparison would need
For a **cost** comparison the work must be identical, which means comparing arms that make the SAME moves — i.e. a
speed patch against its own base (Step 2's design: identical node rows), not two different evaluations. **So the
coordinator's real-position requirement is properly satisfied by measuring a PATCH against its base with identical
node rows, not by comparing two evaluation paths.** My arm measured the wrong pairing for the question I asked.

That is worth stating plainly because it changes what Step 2 would have to do: a real-position check of a v3 patch is
easy (the patch must produce identical nodes, so the ABBA ratio is clean); a cost comparison between two evaluation
paths is not, and I should not have framed it as one.

## What I keep from this arm
- **The harness works**: 120 ABBA quartets, no hangs, no timeouts, no missing cells.
- **The spread figure (1.48x) is real and useful**: it sets the floor for what a v3 patch claim would have to beat on
  real positions — a patch claiming less than that on this sample size would not be measurable.
- **The finding is the flaw, not the ratio.** I would rather hand Opus "this measurement does not support the claim I
  framed it for" than a 0.937 that invites a wrong conclusion.

## Show it again

    cd forge-combo29/swarm/08/v3 && python3 realpos_v3.py /tmp/rp.txt
    # the row that exposes the flaw is the last one: "positions where both arms reported the SAME node count"
