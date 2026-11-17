# How many distinct searches a budget range buys (S-F129)

Seat 19's prediction closed with the right question: if a large share of positions get the identical search at two
budgets, then *"the practical question is NOT '2000 vs 3000' but 'how many distinct searches do these budgets buy'"*.
This page answers it by sweeping a budget range and counting distinct searches, rather than testing one pair.

## The sweeps

`go softnodes N` for 12 budgets from 250 to 15,000, on three positions of contrasting character, `Threads 1`,
`Hash 16`, fresh process per row, read to `bestmove` before `quit`. PC20.

### `startpos` — 12 budgets, **8 distinct searches**

| budget | result | rung |
|---|---|---|
| 250 | d2d4 d4 n412 | 1 |
| 500 | d2d4 d5 n971 | 2 |
| 1000 | c2c4 d6 n1740 | 3 |
| 1500 | c2c4 d6 n1740 | 3 |
| 2000 | d2d4 d7 **n4121** | 4 |
| 2500 | d2d4 d7 n4121 | 4 |
| 3000 | d2d4 d7 n4121 | 4 |
| 4000 | d2d4 d7 n4121 | 4 |
| 5000 | d2d4 d8 n6170 | 5 |
| 7000 | d2d4 d9 n7131 | 6 |
| 10000 | d2d4 d11 n13604 | 7 |
| 15000 | d2d4 d12 n21600 | 8 |

**Four consecutive budgets (2,000–4,000) buy the identical search.** Note also the search at 2,000 spends **4,121**
nodes — more than twice the request.

### `italian` — 12 budgets, **6 distinct**

Rungs: 250 / 500 / {1000, 1500, 2000} / {2500, 3000, 4000, 5000} / 7000 / {10000, 15000}. The 2,500–5,000 gap spans
**four** budgets.

### `rookend` — 12 budgets, **7 distinct**

Rungs: 250 / 500 / 1000 / {1500, 2000} / {2500, 3000, 4000, 5000, 7000} / 10000 / 15000. The 2,500–7,000 gap spans
**five** budgets.

## The collision rate, counted rather than derived

| position | budgets | distinct | **identical budget PAIRS** |
|---|---|---|---|
| startpos | 12 | 8 | **7 of 66 = 11 %** |
| italian | 12 | 6 | **10 of 66 = 15 %** |
| rookend | 12 | 7 | **11 of 66 = 17 %** |

**I got this wrong first, in exactly the way S-F126 describes.** My initial formula was `1 − (distinct−1)/(n−1)`,
which printed **36 / 55 / 45 %**. The true rate — the fraction of budget *pairs* returning the identical search — is
**11 / 15 / 17 %**, obtained by enumerating the pairs. The formula was a plausible guess at a quantity I had not
defined: a rung holding four budgets contributes six colliding pairs out of 66, not a third of them. **Deriving a
rate from a count is guessing unless you check what the count counts.**

## Cross-check against the pairwise test

The `softnodes 2000` vs `3000` result for italian, from the earlier pair test and from this sweep, independently:

| source | 2000 | 3000 | identical? |
|---|---|---|---|
| pair test (`softnodes_pc20.txt`) | f1b5 d7 n2261 | f1c4 d8 n5993 | no |
| this sweep | f1b5 d7 n2261 (rung 3) | f1c4 d8 n5993 (rung 4) | no |

Same two readings, same conclusion, from two scripts written at different times. That is the check that the sweep is
measuring the same thing the pair test measured.

## What this is for

A pair test reports a collision *rate*. A sweep shows **where the rungs are**, which is what a person choosing budgets
actually needs:

* two budgets inside one gap buy the **identical** search, so an experiment comparing them measures nothing — not a
  small effect, zero;
* the fix is to pick budgets that **straddle a rung**, and the sweep says where the rungs sit for these positions;
* the gaps are wide (2,000–4,000 on `startpos`, 2,500–7,000 on the endgame), so a plausible-looking pair like
  `2000` vs `3000` is a no-op on some positions and not others — which is why a rate across positions is the honest
  summary and a single pair is not.

## What I am not claiming

* **Not a general law about rung width.** Three positions, one configuration. The ladder depends on how large the
  iteration spanning N is, so it moves with settings — the PC20-vs-plain difference in `SOFTNODES_GRANULARITY.md`
  (50 % vs 17 % identical) is the same dependence seen through a different measurement.
* Not that `softnodes` is defective: it does what `search.cpp:2932` says, stopping at the first iteration boundary at
  or above N.
* Not that every budget pair is a no-op — 11–17 % is a minority of pairs. The claim is that the minority is
  **structurally determined** (same rung) rather than random, so it can be avoided by choice.
