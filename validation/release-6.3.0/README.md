# Release 6.3.0 strength validation

All matches: fastchess (commit 60d7a7a), `-repeat` colour-swapped pairs,
`-recover`, openings `tools/openings/forge-10000.epd` in random order, one
thread, 4-core Intel Xeon VM, four games at a time for the fixed-node
matches. Both sides of every match were built from this tree with the same
compiler (GCC 13.3, Release, `-mpopcnt`). The 6.2.0 reference ("base") is
commit 86c9162, the head of the 6.2.0 branch.

Fixed-node self-play (`-each nodes=25000`, Hash 16 MB, no adjudication of
any kind) isolates a search or evaluation change from machine load and
from speed: both sides search exactly 25,000 nodes per move (roughly depth
9-10 for this engine), so a positive result means the change makes the
tree, or the evaluation, better per node. Each component was tested on its
own, 1000 games (500 opening pairs), against the tree it was added to, in
the order below; the adopted ones were then kept for the next test.

## Single-thread component results (25,000 nodes per move, 1000 games each)

| Change under test (reference) | W / L / D | Score | Elo | Verdict |
| --- | --- | --- | --- | --- |
| Cutoff-count reductions (vs 6.2.0) | 393 / 357 / 250 | 51.8 % | **+12.5 +/- 14.0** (LOS 96 %) | adopted |
| Quiescence move-count pruning, recaptures exempt only from the count rule (vs cutoff-count) | 391 / 355 / 254 | 51.8 % | **+12.5 +/- 15.1** (LOS 95 %) | adopted |
| Quiescence move-count pruning, Stockfish variant: recaptures also exempt from futility (vs cutoff-count) | 400 / 368 / 232 | 51.6 % | +11.1 +/- 13.7 (LOS 94 %) | not adopted (the other variant was) |
| Deeper / shallower re-search after a reduced move beats alpha (vs the two above) | 380 / 346 / 274 | 51.7 % | **+11.8 +/- 14.5** (LOS 94 %) | adopted |
| Eleven new evaluation terms, fitted alone on 387k match positions (vs the three above) | 398 / 372 / 230 | 51.3 % | **+9.0 +/- 14.5** (LOS 89 %) | adopted |
| Thirteen new evaluation terms incl. space and long-diagonal bishop, fitted on 230k positions (vs the three search changes) | 370 / 359 / 271 | 50.55 % | +3.8 +/- 13.9 (LOS 71 %) | dropped (the two extra terms fitted to about zero and cost 2 % speed) |
| One ply less reduction for killer and counter moves | 367 / 367 / 266 | 50.0 % | 0.0 +/- 13.7 | dropped |

TC_RESULTS_PLACEHOLDER

The W / L / D figures are from the `new` side's point of view. The first
two adopted changes were also measured by an earlier run of this
automation whose branch was never published: +13.6 +/- 13.8 and
+14.6 +/- 13.5 over 1000 games each, so each is confirmed by two
independent 1000-game samples.

## The evaluation fit

The new terms were fitted with `forge_extract` on the UCI-notation PGNs of
the fixed-node matches above (5,000 games, 386,943 quiet positions) and
`forge_texel --first-index 614` (300 epochs, K = 2.85 on this data), which
leaves the 614 existing parameters at their 6.0.0 values and fits only the
new ones. Fitted values (middlegame, endgame): knight per own pawn above
four (0, 6); rook per own pawn above four (1, -1); weak pawn on a half-open
file (6, -9); passed pawn on the a/h, b/g, c/f, d/e files (-9, -15),
(1, -21), (-8, -14), (-4, -14); own rook behind a passer (6, 4); enemy rook
behind a passer (-15, -34); trapped rook (-6, 1) per unit, doubled without
castling rights; king on a pawnless flank (8, -29). The space term and the
long-diagonal bishop term of the first attempt fitted to (0, -1) and
(-4, -4) and were removed. A full refit of all parameters on these
positions was not attempted; the 6.2.0 validation found one neutral.

## Speed

SPEED_PLACEHOLDER

## Sanity

- `ctest`: 4/4 suites (C++ tests, match-tool tests, UCI regression, ponder
  regression) with GCC Release `-Wall -Wextra -Wpedantic -Wconversion -Wshadow
  -Werror`.
- `bench` 13 signatures along the way: 6.2.0 1,234,322; cutoff-count
  reductions 720,188; quiescence move-count pruning 741,614; deeper /
  shallower re-search 670,847; evaluation terms 668,960 (the pawn attack
  span fill and the zero-valued term code left the signature unchanged).
- The generated evaluation table is checked at compile time to have one
  entry per parameter index.
