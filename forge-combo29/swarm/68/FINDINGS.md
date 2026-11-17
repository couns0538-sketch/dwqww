# FINDINGS — label-quality screen for mate scores

Every number below comes from a command in `SCREEN.md`. Denominators are printed
as literals. Where a number is not yet measured it says so.

## 1. The verifier, and whether it can fail

`tools/mateverify.cpp` is an independent C++ program: its own board
representation, own move generation, own search, no engine header, no engine
link. It reports an exact distance-to-mate (DTM) for a FEN and grades a claimed
`mate N` against it.

### Move generation is validated

`python3 tools/perft_check.py` → **27/27** agree with python-chess.

| check | result |
|---|---|
| 7 published perft positions | 7/7 |
| 20 hand-picked + random endgames vs python-chess | 20/20 |

Two genuine bugs surfaced here and were fixed:

1. **Unmake restored the promoted piece instead of the pawn.** After `d7c8=Q`,
   unmake left a queen on `d7`. This corrupted every later position in the
   subtree; perft caught it at 2/7.
2. A hardcoded expectation of `89879` for perft position 6 was **my own
   mistake**, not the code's: the verifier returns `89890` and python-chess
   agrees. Recorded because an expectation typed from memory is a fixture that
   can be wrong, and a fixture cannot outrank a second implementation.

### Ground truth: exact DTM for every KQvK and KRvK state

`python3 tools/retrograde.py all` builds both tables by backward induction and
asserts the published bounds:

| class | legal states | resolved | unresolved draws | max DTM (winner) |
|---|---|---|---|---|
| KQvK | 368,452 | 345,404 | 22,176 | **19 plies = 10 moves** |
| KRvK | 399,112 | 376,868 | 22,176 | **31 plies = 16 moves** |

**The brief's bounds mix units.** KQvK is 10 **moves** (19 plies); KRvK is 31
**plies** (16 moves). Both are asserted explicitly rather than as a single
number, precisely so this cannot pass unnoticed.

The assertion earned its place. A first version of the retrograde script dropped
states where the strong piece could be captured, which deletes the weak king's
best defence (take the undefended queen → KvK draw). It reported KQvK max DTM of
**6 moves** with **zero** unresolved positions — both impossible. The bound
assertion failed loudly instead of producing a plausible wrong table.

### The verifier reproduces that ground truth

| sample | agreement |
|---|---|
| KQvK, `\|DTM\| ≤ 11`, random 50 (seed 11) | **50/50** |
| KQvK, `\|DTM\| ≤ 11`, random 25 (seed 99, final binary) | **25/25** |
| KRvK, `\|DTM\| ≤ 15`, random 20 | **17/20 CORRECT, 3 INCONCLUSIVE, 0 wrong** |

The three KRvK non-CORRECT results are `INCONCLUSIVE` from the node cap at
27–29 plies (e.g. `3K1R2/8/1k6/8/8/8/8/8` at 430M nodes). They are reported as
inconclusive rather than guessed, which is the correct behaviour and is counted
as such.

### It is shown to fail on a planted error

`python3 tools/dtm_validate.py` runs three claims separately:

- fed the **true** distance → must say `CORRECT`;
- fed a **wrong** distance ±1 and ±2 → must say `WRONG` **and name the
  direction** (`over` when the label is larger, `under` when smaller);
- a **negative control**: a checker that assumes the side to move is always the
  attacker misreports the negative-score cases, proving the real verifier's
  agreement on losses is doing work rather than being structurally guaranteed.

Measured on the graded corpus: 42 labels at MultiPV 1, |N| ≤ 5 →
**26 CORRECT / 16 WRONG**, every WRONG labelled `over`, and every verdict
carries `attacker` resolved from the **sign** of the exact score with
`attacker_from: sign_of_exact_score` printed.

### The bug that made it wrong, and how it was caught

The verifier initially reported distances **2–6 plies too large**. Cause: a mate
score cached in the transposition table is stored node-relative and is correct,
but **its distance can exceed the depth the current caller has left** — the
entry may have been proven at the same position on a shallower path with more
remaining depth. Returning it claims a mate deeper than the horizon searched.
Concretely, `8/5k1Q/8/3K4/8/8/8/8 b` reported `mate 12` at **horizon 9**.

Two changes fixed it: clear the table between horizons, and accept a cached mate
only when `cachedDistance <= depth`. Agreement with the retrograde table went
from 28/40 to 50/50.

**This is the single most important warning in this document for anyone reusing
a mate verifier: a TT that looks correct for cp scores is not correct for mate
scores unless the ply adjustment accounts for remaining depth, not only for the
ply offset.**

## 2. Wrong-mate rate at a real match budget

Engine: `forge-combo29` built from `6b98f217`, **Threads 1**, Hash 16, depth 12.
Corpus: 400 positions, all built to be sparse and materially lopsided
(`tools/build_corpus.py`), all accepted by the engine (**0 refused / 400**, 0
timeouts).

| MultiPV | positions | mate labels | PV-length filter | labels with \|N\| ≤ 5 |
|---|---|---|---|---|
| 1 | 400 | 75 | 54/75 pass | 42 |
| 2 | 400 | 135 | 105/135 pass | 84 |
| 3 | 400 | 183 | 145/183 pass | 114 |

Note that the length filter's pass rate rises with MultiPV (72% → 78% → 79%),
so **more lines makes the filter look better while, per the section below,
making the wrong-mate rate worse**.

### Direction and size

240 labels with |N| ≤ 5 across all three MultiPV settings, all graded:

| | count |
|---|---|
| CORRECT | **143/240** |
| WRONG | **89/240** = **37.1%** |
| INCONCLUSIVE | 8/240 (node cap; not counted as wrong) |

By MultiPV (wrong / decidable, with inconclusives excluded from the denominator):

| MultiPV | wrong | rate | of which graded |
|---|---|---|---|
| 1 | 16 | **38.1%** | 42, 0 inconclusive |
| 2 | 28 | **34.6%** | 84, 3 inconclusive |
| 3 | 45 | **41.3%** | 114, 5 inconclusive |

**The sign of the error is not one-directional, but it is dominated by one
direction**: 85 of 89 wrong labels are `over` (label larger than truth) and only
4 are `under`. Overstatement mean **1.33 moves**; understatement is exactly
−1 move in all four cases.

| error | count |
|---|---|
| +1 move | 58 |
| +2 moves | 26 |
| +3 moves | 1 |
| −1 move | 4 |

The four `under` cases are the interesting ones for the class the brief
describes, because they are the opposite direction to everything else:
`8/8/1k6/2p5/2q5/8/1K6/8 w` is labelled `mate −4` by MultiPV 2 and `mate −4` by
MultiPV 3 while the exact distance is 10 plies (5 moves) — the engine
**understates** the distance to its own loss.

An earlier 42-label MultiPV-1 sample showed 16/16 `over` and I wrote "it was
never observed to understate it". **That sentence was wrong** once the sample
grew: it was a sample size too small to see a 4-in-240 direction, not a property
of the engine.

### The PV-length filter is blind on this entire sample

This is the central result. On all 240 graded labels:

| PV-length filter | verifier CORRECT | verifier WRONG |
|---|---|---|
| **pass** | 143 | **97** |
| fail | 0 | 0 |

**Every one of the 240 labels has a PV of exactly the length the score implies
(`2|N|−1` for a win, `2|N|` for a loss), and 97 of them are still wrong about
the distance.**

The filter's accepted set is the whole sample, so its selectivity here is zero:
it passes 240/240 and would have admitted 97 wrong labels into a training set.
Its rejection side never fires on this corpus at all.

That is stronger than "the filter cannot catch every case". On this corpus the
filter is not a filter: every label it sees has the right shape, because at
depth 12 the engine **completes its PV before it completes its distance**. The
PV is a real line that ends in a real checkmate; the number attached to it is
simply not the shortest such mate. The one thing the length rule checks is
precisely the thing that is not wrong.

Direction of the 89 wrong labels: **85 over, 4 under** — so the two known boards
are not the only instances of the class, and both directions occur.

Two candidate explanations for the wrong labels were tested and neither survives:

- **Not a PV-length artefact.** See the table above: length is right on all 240.
- **Not a fixture artefact.** Every FEN was validated with python-chess before
  sending, both streams were scanned for `invalid FEN`, and **0/400** positions
  were refused. The scores are genuinely for the board named.

A third check independently confirmed the direction on a specific case: the
verifier and a plain python negamax both put `8/7k/8/7K/4q3/8/8/8 w` at mate in
6 plies while the engine's label implied 12.

### The caveat that must travel with this number

Depth 12 is a **shallow search on 12-piece positions**, and the engine converges:
on `8/8/8/8/8/k7/8/KQ6 w`, the label is `mate 6` at depth 12, `mate 6` at 16,
and `mate 5` at 20–24 — where the exact answer is 5. So **most of this
wrong-mate rate is a depth artefact, not a persistent defect**: the engine's mate
distance converges to the truth from above as depth grows. What the screen
detects is that **a mate label collected at a fixed shallow depth is not safe to
train on**, which is exactly the corpus risk the brief describes.

## 3. The two known boards

Both FENs were recovered from the store rather than guessed:

- R5 board 222: `2r1k1n1/4p1bQ/1P2B1pp/2pp1pN1/pn3PPP/1RPPP3/1B6/1N2KR2 b - - 0 1`
  (27 pieces, 26 legal moves)
- R6 board 121: `1nbk2r1/2rp1pb1/Bp1n1q2/1Pp3Pp/5pP1/P3P3/2PP1K2/RNB3NR b - - 0 1`
  (28 pieces, 37 legal moves)

**Status: NOT confirmed and NOT refuted. No verdict is claimed.**

Both are populated middlegames with pawns, and the exhaustive verifier does not
finish them. This is measured, not assumed. On board 121, per-depth cost with
check-first ordering and a fresh table per horizon:

| depth | nodes | time | result |
|---|---|---|---|
| 1 | 38 | 0 ms | no mate |
| 2 | 970 | 8 ms | no mate |
| 3 | 36,869 | 239 ms | no mate |
| 4 | 577,419 | 5.2 s | no mate |
| 5 | 7,557,120 | 50 s | aborted at cap |

The claimed `mate 4` needs 8 plies to grade (2×4 for a loss), and depth 5 alone
already cost 7.6M nodes and 50 s. Branching is 37, so 8 plies is on the order of
1e11 nodes at full width. It did not finish in a 15-minute budget.

Note the last row is itself informative and is NOT a verdict: no mate at 4 plies
does not refute `mate 4`, because a loss needs 8 plies. It only shows the cost
curve.

**What this costs the assignment:** sub-task 3 is not delivered. The class those
boards were cited for *is* demonstrated elsewhere in this document, on 89 corpus
labels including 4 in the `under` direction — but the two named boards themselves
are unverified here, and anyone relying on this document for those boards should
treat them as open.

**What would close it:** a retrograde/DTM table for the position class (as done
for KQvK/KRvK here), or a dedicated mate solver with proof-number search.
Neither is built.

## 4. Is the screen cheap enough for a whole self-play corpus?

**No, not as built.** Measured throughput: **0.553 labels/s** single-core
(42 labels in 76.0 s), **~1.2 labels/s** on 4 cores (240 labels in 420 s with 4
shards).

A corpus of 2,000 games yields up to 2,000 mate labels, which is
`2000 / 0.553 = 3,617 s ≈ 1.0 hour` of pure verification single-core, or about
**28 minutes on 4 cores** — and that is with `|N| ≤ 5` labels only. Labels at
`mate 12`–`mate 24`, of which the corpus has several, cost minutes each and
usually return `INCONCLUSIVE`. Sizing on the observed distribution the realistic
figure is **several hours per 2,000 labels on one core**.

It is parallel by construction (`--batch` reads a TSV and is stateless per line),
so wall time divides by cores. That makes it a runnable batch job for a sample,
not an inline transform.

**A per-label budget of 120M nodes / 45 s is required in practice.** Without it
a single deep label can stall a corpus pass indefinitely: one shard sat on
`8/8/5k2/3P1p1P/Q7/BN6/R3K2P/7B w` for over 10 minutes before the bound was
added. The bound converts a stall into an `INCONCLUSIVE`, which is the honest
outcome and is counted separately.

## 5. Can a cp score near a mate horizon be detected cheaply?

**No.** A cp score carries no mate distance, so no cheap transform of it can
prove or disprove a mate label — the two are different quantities.

What the data does support is a weaker, useful statement about **corpus
selection**: mate labels appear almost exclusively in positions that are both
**sparse** and **materially lopsided**. `tools/build_corpus.py` uses exactly
that filter (material difference ≥ 5, ≤ 12 pieces) and produced 400 positions
of which 75 carried a MultiPV-1 mate label at depth 12 — a 19% hit rate, versus
0/73 full-material middlegame positions in the prior measurement.

So sparsity plus imbalance is a **corpus filter**, and that is worth having
because it cuts the verifier's work by removing positions that can never
produce a mate label. It is not a label screen and is not claimed as one.

## What would change each of these conclusions

- Board 222/121 verdicts: need a faster exact solver for populated middlegames.
- A true persistent wrong-mate rate (rather than a depth artefact): grade labels
  at depth 20+ as well as 12, and compare the rate at each depth.
- A cheaper screen: the measured 0.553 labels/s is single-core; parallelism is
  the only lever demonstrated here.
