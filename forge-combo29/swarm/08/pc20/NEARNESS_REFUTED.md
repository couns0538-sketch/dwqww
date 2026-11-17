# Testing my own guess: does nearness-to-mate explain the 37 % vs 10 % gap? — seat 08

**Verdict: NO — my guess was wrong, and the data says so plainly.** I guessed that the first sparse sample had more
mate-appearing targets because its boards were nearer to mate. Nearness, measured independently, does not predict
which boards produce the error. Refuted, and reported as refuted rather than softened.

## How it was measured

For every board in **both** sparse samples (the exact boards already measured), an independent deep search
`go depth 18` from the same position, BEFORE any clocked search. "Near mate" = that deep search reports `mate N`.
Then cross-tabulated against whether that board's **clocked** target had a mate appear at depth D+4.

PC r15, PC20, Threads 1, Hash 16.

## The result

| sample | boards | deep search finds a mate | of those, mate-appearing targets | no mate at depth 18 | of those, mate-appearing |
|---|---|---|---|---|---|
| seed 801 | 27 | **14** | **2** | 13 | **8** |
| seed 902 | 29 | **4** | **1** | 25 | **2** |

| group | mate-appearing targets | boards | rate |
|---|---|---|---|
| boards **near mate** (depth 18 finds a mate) | **3** | **18** | 17 % |
| boards **not near mate** | **10** | **38** | **26 %** |

**The error is MORE common among boards that are not near mate (26 %) than among near-mate boards (17 %).** My
hypothesis predicted the opposite direction. So:

- **Nearness to mate does NOT explain the discrepancy.** Refuted.
- The mate-appearing cases are not "positions already on the edge of mate" — they are ordinary sparse positions
  where four extra plies happen to find a mate that the clocked depth did not. The intuitive story (near-mate boards
  are the dangerous ones) is not what the measurement shows.

## A separate fact: the two samples differ in COMPOSITION (not in cause)

| sample | share of boards where a deep search finds a mate at all |
|---|---|
| seed 801 | **14 of 27 = 52 %** |
| seed 902 | **4 of 29 = 14 %** |

**COMPOSITION, stated as composition:** my hand-selected sparse set was 52 % mate-bearing; the independent
random-game set was 14 %. The two samples are built from different material and differ by nearly a factor of four in
how often a mate exists at all. That is a property OF THE SAMPLES, and it is worth recording because anyone comparing
their rate with mine needs to know the sets are not alike.

It is NOT offered as the cause of the 37 % vs 10 % error gap, and the measurement above rules that reading out:
within each sample the error is not concentrated on the mate-bearing boards (3 of 18 near-mate boards errored, 10 of
38 others did). So: **composition difference is real; my causal story attached to it is wrong; the two are separate
statements and I am not joining them.**

## What this leaves open, stated as open

The 37 % vs 10 % gap is **not explained by nearness to mate**. What it IS explained by is now unmeasured. Plausible
remaining candidates, named but untested:
- the two samples differ in how much a *four-ply* extension can change the verdict in their kind of position, which
  is a property of the position's tactical density, not of whether it is already mate;
- sample size: 27 and 29 boards with rates this variable give intervals that overlap, and the "3.6x" gap could be
  substantially sample noise even though I am not entitled to call it that without more boards;
- the hand-built boards of seed 801 came partly from the 08-F28 shape classes (chosen for few pieces AND few moves),
  while seed 902's came from random games with ≤12 pieces only — a filter difference not captured by "near mate".

**What I will not do:** invent a mechanism that fits after the fact. The honest state is: the rate is not
established (already recorded in 08-F31 and `PRECOMMIT_seed902_rule.md`), and the one explanation I proposed for the
gap has now been tested and failed.

## How sure
Sure of the refutation: the near-mate group produced 3 of 18 errors and the not-near group 10 of 38, both measured
with a deep search independent of the clocked one. Sure of the composition difference (52 % vs 14 % near-mate
boards). NOT sure of any explanation for the error rate itself — none is established.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 nearness_test.py /tmp/nt.txt
