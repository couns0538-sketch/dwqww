# THE ASYMMETRY, LOCATED — the last experiment, and what it proves

Seat 06, base tree, Threads 1, Hash 16, depth 1 on `1r6/8/4K3/5p2/5k2/7p/8/8 w` and its colour mirror.
Instrumented build: variant J (per-root-move node and qsearch counters; adds info lines only),
and the combined H+J build (J plus variant H's canonical generator order).

## The trace: one move is responsible

| order (self) | move | nodes | qnodes | score | | order (mirror) | move | nodes | qnodes | score |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | e6d5 | 1 | 1 | -2031 | | 1 | e6d7 | 1 | 1 | -2023 |
| 2 | e6d6 | 1 | 1 | -2083 | | 2 | e6e7 | 1 | 1 | -2084 |
| 3 | e6f6 | 2 | 2 | -1726 | | 3 | **e6f7** | **2** | **2** | -1863 |
| 4 | e6d7 | 1 | 1 | -2023 | | 4 | e6d6 | 1 | 1 | -2083 |
| 5 | e6e7 | 1 | 1 | -2084 | | 5 | e6f6 | 2 | 2 | -1726 |
| 6 | **e6f7** | **1** | **1** | -1863 | | 6 | e6d5 | 1 | 1 | -2031 |

**Five of the six root moves cost exactly the same on both sides. One move, `e6f7`, costs 1 node on self
and 2 on the mirror.** That single qsearch node — one node — is the entire 8-vs-9 difference, and it is the
seed from which the whole depth-10 asymmetry grows.

Answering the brief's two-way question exactly: it is **(b) a different qsearch node count on the same move**,
not a move tried on one side and not the other. Both sides try all six moves.

## Where the extra node comes from

`e6f7` is searched **6th on self and 3rd on mirror**, because the root order differs. When it runs, a different
amount of the transposition table has been filled by the earlier moves, so on one side qsearch takes a TT hit
(1 node) and on the other it misses and expands (2 nodes).

The 1-node gap is invariant to Hash size (1 MB, 16 MB and 256 MB all give (1,1) vs (2,2)), which rules out
*saturation*; it is a hit-vs-miss on the same key, not a full-table effect.

## Why the root order differs when every picker score is 0

At the first root visit every picker score is 0 on both sides (`picker_iter1_truth.txt`). `std::sort`'s
comparator is `a.score > b.score`, which returns **false for every pair when all scores are equal**, so the
resulting order is whatever the input order was — and the input order is the move generator's emission order,
which differs under a colour mirror (root-effort order, `search.cpp:2203-2207`, straight from `legal_moves()`).

## The decisive cross-check, and what it does and does not fix

Rebuilding with variant H's canonical generator order (H+J together) makes the emission order mirror-invariant
and **swaps which side pays**:

| build | self total | mirror total | e6f7 (self, mirror) |
|---|---|---|---|
| variant J (base order) | 8 | 9 | (1, 2) |
| H+J (canonical order) | 9 | 8 | (2, 1) |

So the order determines **who** pays the extra node, but not **whether** one is paid. That is why variant H
alone left the depth-10 count at 101 of 353: canonicalising the order relocates the difference rather than
removing it.

## What this establishes, and what it does not

**Established, with the narrowest evidence in the whole thread:** the colour-mirror search asymmetry begins as
**one qsearch node** on **one root move**, caused by a **transposition-table hit landing on one side of a mirror
pair and not the other**, because the root visits the moves in a different order when all picker scores are
tied. Every larger effect measured at depth 10 (101 bestmoves, 334 scores) grows from seeds of this kind.

**Not established:** why a TT hit/miss should differ at all for a position and its mirror when the tree is
otherwise identical. The key must differ, or what is stored must differ. That is a *separate* question and I am
not going to guess at it here — it needs the key and the stored entry for that one node printed, which is the
natural next experiment.

## Honesty

- Variant J and H+J add info lines only; J's pins are unmeasured (it was built for tracing), and H fails the
  pins as any order change does. Both are evidence, not candidates.
- All numbers are pasted engine output, saved in `rootmove_trace.txt`,
  `rootmove_trace_canonical.txt`, `e6f7_qsearch.txt`, `e6f7_tt_test.txt`, `qsearch_entry_diff.txt`.
- The two nodes that get different qsearch counts are structurally identical by every python-chess check I ran
  (same halfmove clock 1, neither in check, 22 legal moves each, no captures, no promotions, no insufficient
  material, no repetition).
