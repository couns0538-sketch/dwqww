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
