# ONE POSITION, ALL THE DATA — where the colour-mirror search asymmetry actually lives

Seat 06. Instrumented build: variant F (base 6b98f217 + one `info string rootnodes` print per depth; pins
unchanged at 312866/862329/3024920/4865609). Threads 1, Hash 16, OwnBook false, depth 4 and 6.

## The position

`1r6/8/4K3/5p2/5k2/7p/8/8 w - - 0 1` — 5 pieces, 6 legal moves, one of the 120 the PC build mismatches.
Chosen because it is the CLEAREST of the mismatching set (fewest pieces, fewest moves), so any divergence is
readable rather than buried in a 50-move tree.

## What the data shows, in order

**1. The move generator emits the moves in a DIFFERENT ORDER under a colour mirror.**

```
GENERATION ORDER self   : e6d5 e6d6 e6f6 e6d7 e6e7 e6f7
GENERATION ORDER mirror : e6d7 e6e7 e6f7 e6d6 e6f6 e6d5
```

This is `root_effort_moves_`, copied straight from `board.legal_moves()` before any scoring
(`search.cpp:2203-2207`, `2375-2377`), so it is the generator's own emission order. The mirror reversal is not a
coincidence of this position: on `R3K2R` the generator emits `a1b1 a1c1 … a1a8` on one side and
`a1a8 … a1b1` on the other, and on the start position it is identical because the position is left-right
symmetric. The generator walks squares in a fixed direction, and that direction is not mirror-invariant.

**2. At depth 4 the SCORE and the PV are IDENTICAL, but the per-root-move node counts DIVERGE.**

```
self   PV: score cp -1861 nodes 392   pv e6f6 b8b6 f6g7 h3h2 g7h7
mirror PV: score cp -1861 nodes 224   pv e3f3 b1b3 f3g2 h6h7 g2h2   (maps back to the same line)
```

| root move | self nodes | mirror nodes |
|---|---|---|
| e6d5 | 13 | 13 |
| e6d6 | 5 | 5 |
| **e6f6** | **182** | **154** |
| e6d7 | 12 | 12 |
| e6e7 | 5 | 5 |
| **e6f7** | **170** | **30** |

Four of the six root moves cost exactly the same. Two cost very different amounts — e6f7 by a factor of 5.7.

**3. The two differing subtrees are structurally identical.** After `e6f7` the opponent has 22 legal replies and
**no captures and no check**; after the mirrored move the opponent has 22 legal replies and no captures and no
check. So the divergence is not a different move list below, and not a different terminal condition: the same 22
replies are available on both sides and a different NUMBER of them gets searched.

## This answers the branch question the brief posed

> if the root-move scores differ before any search, it is evaluation or move generation; if they agree and the
> node counts diverge, it is ordering or a table interaction

**The scores agree and the node counts diverge.** It is **ordering or a table interaction** — not the evaluation.
This is independently confirmed by everything already measured: the evaluation is exactly symmetric (S-F1/S-F24/S-F30,
0 differences in 11,000+ pairs), and the tables are ruled out (TT cleared per root move changes nothing, S-F17/G;
the continuation-history colour index changes nothing, S-F20).

## What is left, now stated precisely

The generator's emission order differs under mirroring, so the root walks the same moves in a different sequence;
alpha-beta then prunes a different subset of the 22 replies beneath two of them. That is where the asymmetry is
**created**. What remains unexplained is why the *aggregate* rate did not move when I removed the obvious
tie-break (S-C1): the answer is visible here — the difference is not in the SORT of equal-scored moves, it is in
the SEED ORDER the generator hands to the picker, which my variants never canonicalised (variant B ordered only
the generated *list*, after the generator had already chosen the sequence, and it still failed).

**The next experiment, named but not run**: canonicalise the generator's own emission order (mirror the square
walk), not the sort. That is a different patch from all seven already tried, and this position is the fixture to
test it on.

## What I did NOT do

- I did not build and measure the generator-order patch. That is the one lever this data points at and it is not
  yet tried; it is named above so the next worker does not start from the sort again.
- I did not dump depth 8/10 for this position: at depth 4 the divergence is already complete and readable, and the
  deeper trees only obscure it.
- The `searchmoves`-ordered arms in `order_forced_test.txt` are NOT evidence of the ordering effect: `searchmoves`
  sets `root_restricted_` and changes the search (the same trap my own S-F12 correction records). They are kept in
  the folder as a record of a contaminated measurement, labelled as such.
