# REPORT — seat 07, job 56: check of 29-F45 (S14-vs-PC20 agreement is flat across depth)

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 29 flags **29-F42 / 29-F44 / 29-F45** as **OPEN and unconfirmed by any second
seat**, and publishes a reproduction recipe. 29-F45 is the highest-value of the three for the owner because
it describes how the two settings he chooses between differ: *agreement is flat across depth (87.5 / 87.5 /
85.0 / 92.5 %), so the disagreements are not horizon noise.*

**Answer:** **confirmed exactly on its own position set — and the generalisation fails on a different one.**
On R_2911 I reproduce all four numbers **to the digit**. On the last 40 positions of G the same measurement
gives 55–78 %, a 22.5-point spread with a +15-point upward trend.

**How sure:** very high for both halves — the exact four-figure reproduction is not something sampling can
produce by accident, and the G sample is 30 points away, far outside the ±5-point error.

## The two measurements (PC r15, S14 vs PC20, Threads 1, Hash 16, fresh process per cell)

| depth | **R_2911 (seat 29's set)** | **last 40 of G** |
|---|---|---|
| 8 | 87.5 % | **55.0 %** |
| 10 | 87.5 % | **60.0 %** |
| 12 | 85.0 % | **77.5 %** |
| 14 | 92.5 % | **70.0 %** |
| spread | **7.5 pts** | **22.5 pts** |
| trend 8→14 | +5.0 pts | **+15.0 pts** |

The left column is seat 29's published table, reproduced exactly by an independent harness on their own 400
FENs. The right column is a different real-game sample.

## How I nearly got this wrong

My G sample came first, and 30 points outside the sampling error looked like a refutation. Their recipe
explicitly says "any set of real-game positions" and invites a REFUTES line if numbers differ materially —
so filing REFUTES would have been procedurally correct and **wrong**. Running **their** set was what
settled it: identical to the digit.

That is the same lesson as the header's scarcity corollary. **A number can be right on its own sample and
wrong as a generalisation**, and the only way to separate those two is to run the original sample before
calling the original wrong.

## What the owner should take from it

- **The mechanism 29-F45 claims is real**: on random-game positions the PC20 switch set reaches a different
  move about one time in eight, at every depth, and that does **not** shrink with depth — so it is a regime
  difference, not shallow-search noise. That is the useful part and it is confirmed.
- **The rate is set-dependent, and strongly so**: on G's late positions the regimes agree only 55–78 % of
  the time and the agreement *does* rise with depth (55 → 77.5 from d8 to d12). So on those positions some
  of the disagreement **is** horizon-related after all. Anyone quoting "one position in eight" as a
  universal property of the switch set would be over-generalising from R_2911.

## Findings

**07-C56** in FINDINGS.md. It gives seat 29 the independent confirmation 29-N28 says F45 needs, with the
scope correction attached.

## Suspicions, not proven

- That G's positions are later/more tactical than R_2911's random games, which would explain why agreement
  is lower there and rises with depth. Consistent with the data, not tested.

## What I did NOT do

- Did not run 29-F42 or 29-F44 (the node-size and move-quality claims). Those need a neutral-regime
  judgement pass per disagreement and are a bigger job than the remaining window should start.
- Did not test more than one G subset, so "55–78 % on late G" is one sample of 40.

## What I am NOT sure about

- Whether the G curve would flatten by depth 16–20; if it does, the horizon component there is shallow-only
  and the two accounts reconcile rather than conflict.

## Times

See job56/stamps.txt.
