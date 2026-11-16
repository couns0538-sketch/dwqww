# REPORT — seat 07, job 43: check of seat 10's 10-F53 / 10-F54 (node budgets change bestmoves)

## What was asked / the answer / how sure

**Asked:** (cycle work) take a contested or unconfirmed finding. Seat 10's **10-F53** is the most
decision-relevant number anyone has produced on the owner's real path — budgets changing the chosen
move — and nobody had independently confirmed it.

**Answer:** **the headline is confirmed and slightly stronger; the operational recommendation built on
it does not hold on my sample.** Budgets disagree on **24/100** positions (seat 10: 19/100), but the
specific claim that `nodes 50000` is the cheapest safe budget is **reversed**: on my disjoint sample
`nodes 50000` disagrees with `nodes 250000` on **22/100** positions where seat 10 measured 8/100.

**How sure:** high for the measurement — determinism control passed, PC r15 under PC20, Threads 1,
Hash 16, fresh process per cell, the exact three budgets the owner uses. The *reason* for the
discrepancy between our two samples is not established (below).

## Why this is an independent check and not a re-run

Seat 10 used **the first 100 positions of G**. I used **the last 100** — disjoint samples from the same
353-position set. So the two measurements cannot share positions, and agreement between them is
evidence about the engine rather than about one slice.

## Results

| measure | this seat (last 100) | seat 10 (first 100) |
|---|---|---|
| all three budgets agree | **76/100 = 76 %** | 81/100 |
| any disagreement | **24/100 = 24 %** | 19/100 |
| `softnodes 20000` vs `nodes 250000` | **18/100** | 17/100 |
| `nodes 50000` vs `nodes 250000` | **22/100** | **8/100** |
| ties among disagreements (≤20 cp at the large budget) | 13 of 24 | seat 10: "not ties" for the worst cases |

The `softnodes 20000` versus `250000` figure matches to within one position — that is the strongest
agreement between two disjoint samples and confirms the core of 10-F53: **the small self-play budget
and the large match budget genuinely pick different moves on about one position in six.**

## Where I disagree: 10-F54's recommendation

Seat 10 concluded that 50000 is "the cheapest safe budget if a single one must be chosen (92/100
agreement with 250000)" and that the disagreement rate is "2.1x higher between 20000 and 250000 than
between 50000 and 250000". On my disjoint sample:

    softnodes 20000 vs nodes 250000 : 18/100 disagree  (82/100 agree)
    nodes 50000     vs nodes 250000 : 22/100 disagree  (78/100 agree)

so **the 50 k budget agrees *less* often than the 20 k budget**, the opposite ordering. Of the 22
`50000` disagreements, 12 are ties at the large budget (so the move difference is harmless) and 10 are
genuinely different.

**This matters operationally**: acting on 10-F54 would mean standardising self-play on 50000 nodes as
the "safe" budget. On my sample that budget is the *least* stable of the three against the match budget,
which would be the wrong direction to standardise.

## What I am NOT claiming

- Not that seat 10 measured wrongly. Their positions are different; both measurements can be correct
  about their own sample, and 100 positions is small enough that the ordering of two rates ~10 pp apart
  can flip between disjoint slices.
- Not a mechanism. I have no account of why 50 k would be worse than 20 k on these positions, and I am
  not inventing one.

**What follows is that 10-F54's recommendation is not safe to act on from 100 positions in either
direction** — a budget-safety claim needs a sample large enough to order the three rates reliably, and
two disjoint 100-position samples already disagree about the ordering.

## Findings

**07-C42** in FINDINGS.md.

## Suspicions, not proven

- That the flip is sample noise: 24 vs 19 disagreements among 100 positions is well within binomial
  noise, and the per-pair counts (18 vs 22) are closer still. A paired design over 353 positions would
  settle it, and I did not run one.

## What I did NOT do

- Did not run seat 10's first 100 to separate build/harness from sample. Their harness is their own and
  my brief is to use mine.
- Did not run all 353 positions; cost.

## What I am NOT sure about

- Whether the 10 genuinely-different `50000` disagreements include a large-damage case like the two
  seat 10 found at 20000. The max gap I saw was 497 cp, which is larger than their 279 cp max, so
  probably yes — but I did not examine those positions individually.

## Times

See job43/stamps.txt.
