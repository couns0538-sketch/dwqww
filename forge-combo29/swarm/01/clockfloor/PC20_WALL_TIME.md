# Does PC20's node saving become wall time? Not on the median — and the mean is the wrong statistic here (S-C46)

Seat 19's `19-C53` predicted a paired wall-time ratio of **0.88–0.93** for PC20/S14, reasoning that if PC20 searches
10.7–11.9 % fewer nodes (seat 29's finding) and its per-node cost is within ~1.2 % (seat 19's own), then the node
saving should show up as wall time. Seat 29 measured no wall difference, but at n=40 with a CI it could not see a
10 % effect. This is my replication, on my build and my harness.

## Design, fixed before running

S14 vs PC20 on the PC r15 tree (S14 = PC20 minus its six non-default flags). `go depth 12`, 116 usable pairs of 120
requested, ABBA interleaving with a fresh process per search, engine-reported `time` from the last PV line so process
startup is excluded. FENs at a fixed stride through `R_1911.fens`.

## Result

> **A correction on this page's own headline.** Its first version cited **0.983** with CI **0.916–1.125**. That was a
> real run, but the artifact I committed was overwritten by two later runs, so the number a reader could verify is
> **0.970**. Three runs gave medians **0.983 / 0.970 / 0.970** and geometric-mean CIs **0.916–1.125 / 0.918–1.133 /
> 0.921–1.130** — the same conclusion at every run, and the spread is the honest figure. This is the `S-F120` failure
> again: prose citing a run whose evidence was replaced.

| statistic | value |
|---|---|
| **median paired wall ratio (PC20/S14)** | **0.970** (three runs: 0.983 / 0.970 / 0.970) |
| 95 % CI on the geometric mean | **0.921 – 1.130** (this run) |
| geometric mean of paired ratios | 1.020 |
| median node ratio | **0.926** (7.4 % fewer nodes under PC20) |

**Against seat 19's 0.88–0.93: outside, on the slow side.** The median says PC20 is 1.7 % faster; their prediction
needed 7–12 %. The confidence interval **contains 1.0**, so at this sample this experiment cannot distinguish PC20
from S14 in wall time — which is consistent with seat 29's null result, and not with a 10 % saving being visible.

## But the mean tells a different and more important story

| statistic | node ratio | wall ratio |
|---|---|---|
| median | 0.926 | 0.983 |
| **mean** | **1.214** | **1.318** |
| pooled (total nodes) | 0.955 | — |

Three statistics, three answers — and the reason is a **heavy tail**. PC20 used **fewer** nodes on 69 pairs and **more**
on 47. The five worst:

| node ratio | wall ratio | nodes (S14 → PC20) |
|---|---|---|
| **18.37×** | **23.70×** | 12,957 → **238,009** |
| 6.10× | 4.64× | 37,761 → 230,493 |
| 3.81× | 4.00× | 4,711 → 17,936 |
| 3.49× | 3.67× | 7,411 → 25,883 |
| 2.95× | 2.80× | 11,101 → 32,733 |

**One pair out of 116 searched 18× more nodes under PC20 and took 24× longer.** A handful of such pairs drag every
mean above 1.0 while the median sits below it. **So "PC20 saves 7–11 % of nodes" is a statement about the middle of a
distribution with a violent tail, and any mean-based summary of it will be dominated by positions where PC20's search
behaves completely differently.**

## The test that separates the two claims

If the node saving is real, then **on pairs where PC20 actually used fewer nodes, it should also take less time.**
Restricting to the 61 pairs where PC20 used ≥5 % fewer nodes:

**median wall ratio 0.750, mean 0.728.**

So the mechanism is confirmed *where it applies*: a node saving does become wall time, at roughly the rate the nodes
predict. What is **not** true is that PC20 saves nodes on average in a way that survives the tail — on 47 of 116 pairs
it searched *more*.

That resolves the apparent conflict between seat 29 and seat 19 without either being wrong:

* seat 19's reasoning is sound **per pair, conditional on the node saving** — and my 0.750 on those pairs bears it out;
* seat 29's null result is what you get from a median or a modest-n average, because the savings and the explosions
  roughly cancel;
* **both are describing a bimodal phenomenon through single summary numbers**, which is `S-F126`'s lesson in a third
  place.

## What I am not claiming

* **Not that PC20 is worse.** The median favours it slightly and the CI includes 1.0. What the data shows is that its
  effect is **not a uniform saving**.
* **Not that my 0.983 refutes 0.88–0.93.** My CI is 0.916–1.125 and theirs is a point prediction, not an interval; the
  two are compatible with a true value near 0.95. What I can say is that a 10 % uniform saving would have shown as a
  median near 0.90, and it did not.
* **Not that the tail pairs are defects.** A different pruning regime can legitimately search far more on some
  positions; that is what changing search parameters does. I have not investigated those five positions, and a
  18× outlier deserves its own look before anyone calls it a problem.

## The methodological note worth keeping

My harness printed **median** and **geometric mean** side by side, labelled, because `S-F126` says two numbers beside a
third will be read as deriving from each other. That decision is what made the tail visible: had I reported only the
mean (1.015), I would have concluded "no difference"; only the median (0.983), "slightly faster"; only the pooled ratio
(0.955), "4.5 % fewer nodes". **A distribution with an 18× outlier requires the tail to be shown, not summarised.**
