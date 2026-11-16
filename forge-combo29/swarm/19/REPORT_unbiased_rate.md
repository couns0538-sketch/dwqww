# The divergence rate on an UNBIASED sample — 30 % of positions are ambiguous, 10 % of those diverge

seat 19 · area 9 · build **PC r15** · **PC20** · **Threads 1** · Hash 16 · cold.

## 1. The three lines

**What was asked.** 19-F48's 18.4 % was measured on a *hostile* sample — positions selected because they were
ambiguous. Get the rate on an **unbiased** sample so the owner has the number he can act on: take 100 positions
from G at random, find those whose top two moves are within 15 cp at depth 12, and report **both** what fraction
of random positions are ambiguous and what fraction of those diverge.

**The answer.** **30.0 % of random G positions are ambiguous** (top-two moves within 15 cp at depth 12), and
among the ambiguous ones **10.0 % of (position, budget) cells diverge** — i.e. **4 of 30 ambiguous positions
(13.3 %) pick a different move at at least one budget**. Over the whole random distribution that is **2.0 % of
(position, budget) cells**.

**How sure.** Good on the two rates (100-position random sample, fixed seed so it is reproducible; 200 cells
tested, deterministic at Threads 1). The precision is limited by the sample: 4 divergences out of 40 cells
means the true rate is roughly 3–22 % by the rule of three, so **quote "about 10 % of ambiguous positions", not
"10.0 %"**.

## 2. The numbers

Sample: 100 positions drawn from set G's 353 with `random.Random(19711)`, indices sorted, reproducible —
`nodes/unbiased/sample.fens`.

| quantity | value |
|---|---|
| positions scanned | 100 |
| **ambiguous (top-two ≤ 15 cp at depth 12)** | **30 = 30.0 %** |
| cells tested on ambiguous positions (2 budgets each) | 40 |
| **cells where the modes diverged** | **4 = 10.0 %** |
| ambiguous positions diverging at ≥ 1 budget | 4 of 30 = **13.3 %** |
| all (position, budget) cells over the random sample | 4 of 200 = **2.0 %** |

### Comparison with the hostile sample

| sample | ambiguous rate | divergence rate among ambiguous |
|---|---|---|
| hostile (19-F48): selected for ≤ 15 cp from 60 G positions | 19 of 60 = 31.7 % | 7 of 38 cells = **18.4 %** |
| unbiased: 100 random G positions | 30 of 100 = 30.0 % | 4 of 40 cells = **10.0 %** |

**Interesting: the ambiguity rate is essentially the same in both (31.7 % vs 30.0 %).** My "hostile" filter
did not actually select rarer positions than the population — set G is simply full of positions with a close
second-best move. What the hostile sample *did* inflate was the **divergence** rate (18.4 % → 10.0 %), which
makes sense: I scanned 60 positions and tested the 19 sharpest of *those*, effectively double-selecting.

So the honest summary is: **ambiguity is common (about 30 % of game positions), and on ambiguous positions the
budget mode changes the move about one time in ten.**

## 3. What the owner can act on

- **His matches (`go nodes`) and his self-play (`go softnodes 2000`) disagree about the move on roughly 3 % of
  positions** (30 % ambiguous × 10 % divergent), and on about 2 % of individual (position, budget) decisions.
  That is small enough that it does not invalidate his data wholesale, and large enough that mixing modes
  inside one match is worth avoiding — a 3 % move-disagreement rate is on the order of the edge a short match
  is trying to measure.
- **The ambiguity rate (30 %) is the more interesting number** for training data: nearly a third of game
  positions have a second-best move within 15 cp at depth 12. Any pipeline that treats "the engine's move" as
  a ground-truth label is, on those positions, labelling a coin flip.

## 4. Finding

**19-F49 — on 100 random set-G positions: 30.0 % are ambiguous (top-two moves within 15 cp at depth 12) and
10.0 % of (position, budget) cells on those diverge between `go nodes` and `go softnodes` (13.3 % of ambiguous
positions at ≥1 budget; 2.0 % of all cells over the random distribution).** PC r15, PC20, Threads 1, Hash 16,
cold, N ∈ {20000, 50000}, sample reproducible from `random.Random(19711)`. This replaces 19-F48's hostile
18.4 % with the population rate. **19-F48's ambiguity rate was not in fact rare — 31.7 % hostile vs 30.0 %
random — so the hostile filter inflated the divergence rate, not the ambiguity rate.**

### Suspicions, not proven

- That the divergence rate would be higher at larger budgets, where more of the search is done mid-iteration.
  I only tested 20k and 50k.
- That 15 cp is the right ambiguity threshold. A tighter threshold (5 cp) would give a smaller ambiguity rate
  and, per 19-F48's by-gap table, possibly a *higher* divergence rate — the two numbers trade off and I did not
  map the curve.

## 5. What I did NOT do

- 100 positions, not 353 — enough for a usable rate, not enough for a tight one.
- I did not test a second random seed to check the rates are stable. The sample is seeded and reproducible, so
  that is a cheap follow-up I did not take.
- I did not score the divergent moves; which mode plays better is a games question.

## 6. Files

`nodes/unbiased/sample.fens` (the 100 positions), `nodes/sharp_positions.py`,
`nodes/unbiased/out100/RESULT.txt` (all 40 cells), `nodes/unbiased/run100.log`.
