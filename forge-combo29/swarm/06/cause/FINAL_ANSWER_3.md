# THE BISECTION — OUTCOME B. The asymmetry is ordering, all the way down. Thread closed.

Seat 06. Base tree, Threads 1, Hash 16. Instrumented build: variant L (logs every visited node with its
position, ply, static evaluation and in-check flag; adds info lines only).

## The question

At depth 4 the scores diverge (self cp -2038, mirror cp -1852). Is that because a position present on both
sides is evaluated differently — a genuine evaluation asymmetry — or because only the *set* of visited
positions differs, so ordering triggered a path divergence that merely looks like one?

## The answer: OUTCOME B, at depth 4 and at depth 3

Each position was folded through the colour mirror to a canonical id, so "the same position on both sides"
is decidable (a node on one side corresponds to its mirrored node on the other).

**Depth 4** (`bisect_depth4.txt`):

| | count |
|---|---|
| nodes logged | self 138, mirror 129 |
| distinct canonical positions | self 85, mirror 86 |
| **visited on BOTH sides** | **14** |
| visited on self only | **71** |
| visited on mirror only | **72** |
| **common positions whose static eval differs** | **0 of 14** |

Every position the two searches both reach has a **bit-identical static evaluation**:

```
1r6/5K2/8/5p2/5k2/8/7p/8 w  -1978 / -1978
1r6/6K1/8/5p2/5k2/8/8/7b w  -1402 / -1402
1r6/6K1/8/5p2/5k2/8/8/7n w  -1447 / -1447
1r6/6K1/8/5p2/5k2/8/8/7q w  -1852 / -1852
1r6/6K1/8/5p2/5k2/8/8/7r w  -1772 / -1772
   ... all 14 rows: equal, to the centipawn
```

Meanwhile **143 of the 171 distinct positions are visited on only one side** (71 self-only, 72 mirror-only).
That is the path divergence, and it is the only thing that differs.

**Depth 3, the control** (`bisect_depth3.txt`): 10 common positions, **0 of 10** differ in static eval;
57 self-only and 32 mirror-only. Same conclusion at the depth where the *scores* still agreed.

## So the two-outcome question is settled

**B. Every position common to both sides scores identically, and only the visited set differs. Ordering
triggered a path divergence that only looks like an evaluation asymmetry.**

There is **no evaluation asymmetry below the root**. The static evaluation is colour-symmetric (S-F1/S-F24/S-F30,
0 differences in 11,000+ position pairs) and this confirms it again at the nodes the search actually visits.

## The complete causal chain, now with every link measured

1. At the root, every picker score is 0 (or tied: 20 of 22 at one node), so `std::sort`'s
   `a.score > b.score` is false for every equal pair and the order collapses to the input order —
   the move generator's emission order, which differs under a colour mirror.
   *(S-F43, S-F44, `rootmove_trace.txt`)*
2. The two searches therefore walk the same moves in different sequences, and alpha-beta's cutoffs
   depend on that sequence, so they visit **mostly different sets of positions** (143 of 171 at depth 4).
   *(this report)*
3. Their node counts differ from depth 1 onward (8 vs 9, from one qsearch node on one move).
   *(S-F43, `rootmove_trace.txt`)*
4. Where both reach the same position they evaluate it identically, so the *score* divergence at depth ≥ 4
   is a consequence of *having reached different positions*, not of scoring one differently.
   *(this report, 0 of 14 and 0 of 10)*

My earlier statement that "ordering explains depths 1–3 and stops explaining depth 4+" is now **resolved in
favour of ordering throughout**: the depth-4 score divergence is not a second mechanism, it is the same
mechanism once the visited sets have diverged enough for the best-scoring leaf to differ.

## Does it need a further step?

**No.** The thread is closed. The cause is an arbitrary, colour-dependent tie order in move selection,
propagated through alpha-beta. Nothing is misevaluated; nothing is stored wrongly; the hash keys differ only
because a mirrored position is a different position.

If a future worker wants to *remove* it, the lever is now precisely known and no longer guessed: give equal
scores a canonical, mirror-invariant order. Variant H tried that at the generator's emission order and it
merely swapped which side paid (S-F44), which is consistent with this report — the fix has to make the
*complete* comparison key mirror-invariant, including the qsearch ordering, not just the root's input order.

## Honesty

- Variant L adds info lines only. It was built for tracing; its pins are not claimed as measured here.
- All tables are pasted output of `bisect_d4.py`, committed as `bisect_depth4.txt` and `bisect_depth3.txt`.
- The canonical-id scheme folds `fen <= mirror(fen)`. If two genuinely different positions in one search
  happened to collapse to one id the comparison would be *conservative* (it would more easily report "equal"),
  so it cannot manufacture outcome B.

---

# CLOSING MEASUREMENT — the two independent negatives (and why the search score is not a third)

`three_negatives.txt`. On the **14 positions visited by both sides** at depth 4, each probed in a **fresh
process with an empty TT** so the result is a function of the position alone:

| # | comparison | result |
|---|---|---|
| NEGATIVE 1 | **static evaluation** | **0 of 14 differ** (S-F47, `bisect_depth4.txt`) |
| NEGATIVE 2 | **picker score vectors** (history / threat / continuation tables) | **0 of 14 differ** |
| OBSERVED | depth-4 *search* score | 11 of 14 differ |
| OBSERVED | node counts | 14 of 14 differ |

**Both negatives hold.** Every `info string rootpicker` vector is identical between a position and its
mirror on every one of the 14 shared positions — typically all-zero vectors, and where non-zero, identical
term by term.

### Why the third line is NOT a third defect

The depth-4 search score on a shared position differs, and it would be wrong to report that as a third
colour-dependent quantity. **A search score is the OUTPUT of the ordering, not a stored or computed
per-position quantity.** With the static evaluation and the picker vectors both provably identical, order is
the only variable left, so a differing search score on corresponding positions is a *direct confirmation* of
the ordering mechanism rather than evidence against it. (It also explains why a single position can score
differently at depth 4 in two separate fresh processes: the ordering difference is inside each search, not
between them.)

### What this closes

**Nothing stored or computed per position is colour-dependent.** Three independent negatives now stand on
the same board:

1. static evaluation — symmetry-exact (S-F1/S-F24/S-F30/S-F47: 0 differences in 11,000+ pairs, and 0 of 14 and
   0 of 10 on the nodes the searches actually share);
2. picker score vectors — identical on all 14 shared positions;
3. hash keys — differ only because a mirrored position genuinely is a different position (S-F45).

The asymmetry is **ordering, everywhere**: tied scores collapse to a mirror-varying emission order, alpha-beta
follows different paths, and every observable difference grows from that single seed.

### Honest limits of this closing measurement

- The 14 shared positions are the ones the two searches both reached at depth 4 on THIS board. They are a
  sample of one pair, not a population.
- The picker vectors compare the values the picker would sort on; they do not enumerate the raw table contents
  cell by cell. A table could in principle differ in a cell that neither search reads here, and this
  measurement would not see it.
- Positions reachable on one side only (143 of 171) cannot be compared this way at all; for those the claim
  rests on the chain argument, not on a direct comparison.

---

# POPULATION CHECK — the same probe on THREE mismatching pairs (67 shared positions, 0 of 67)

The honest limit of the closing measurement was that 14 shared positions is **one board pair**. Rerun on two
further mismatching pairs, chosen as the smallest from the mismatching set and with different piece counts,
side to move and move counts:

| pair | board | shared positions | NEG-1: static eval differ | NEG-2: picker vectors differ |
|---|---|---|---|---|
| 1 | `1r6/8/4K3/5p2/5k2/7p/8/8 w` | 14 | **0 of 14** | **0 of 14** |
| 2 | `8/8/7k/7P/7r/4K3/8/8 w` | 40 | **0 of 40** | **0 of 40** |
| 3 | `3b4/8/8/7p/5k1P/8/4K3/8 b` | 13 | **0 of 13** | **0 of 13** |
| **TOTAL** | | **67** | **0 of 67** | **0 of 67** |

**Nothing colour-dependent appears anywhere in 67 shared positions — 134 independent comparisons, all
identical.** Raw: `bisect_depth4.txt`, `three_negatives.txt`, `three_negatives_p2.txt`,
`three_negatives_p3.txt`, `population_summary.txt`, `shared14.fens`, `shared_p2.fens`, `shared_p3.fens`.

Pair 3 is the most informative of the three for the *ordering* claim in the other direction: its depth-4
search score differed on only **4 of 13** shared positions while its node counts differed on **13 of 13**. A pair
where the verdict nearly always survives despite the search always costing a different number of nodes is
exactly what an ordering effect predicts, and the opposite of what a misevaluation would produce.

This upgrades the conclusion from a single-board observation to a **population statement across three
independent mismatching pairs**.
