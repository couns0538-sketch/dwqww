# Do the two named repair patches fix it? Measured, not inferred.

Pasted output of `patch_test.py` (18 cells = 6 positions x 3 builds, depth 14).
The harness is proven live by `patch_test.py --plant-fault`, which injects wrong
expectations and is CAUGHT: "mismatches: 9 ... harness CAUGHT the bad expectation".
Exit code 1 on the planted run, 0 on the real one.

## Result

    position                                     build   oracle   verdict  engine    nodes
    6k1/8/5PPP/8/8/8/8/R6K b - - 99 40           base    p=2      MISSED   cp 0       42
    6k1/8/5PPP/8/8/8/8/R6K b - - 99 40           seat12  p=2      MISSED   cp 0       42
    6k1/8/5PPP/8/8/8/8/R6K b - - 99 40           seat27  p=2      MISSED   cp 0       42
    6k1/8/5PPP/8/8/8/8/R6K b - - 98 40           base    p=2      FOUND    mate -1    73
    6k1/8/5PPP/8/8/8/8/R6K b - - 98 40           seat12  p=2      FOUND    mate -1    73
    6k1/8/5PPP/8/8/8/8/R6K b - - 98 40           seat27  p=2      FOUND    mate -1    73
    8/8/8/7Q/8/8/1Q5k/1K6 b - - 99 40            base    p=2      MISSED   cp 0       42
    8/8/8/7Q/8/8/1Q5k/1K6 b - - 99 40            seat12  p=2      MISSED   cp 0       42
    8/8/8/7Q/8/8/1Q5k/1K6 b - - 99 40            seat27  p=2      MISSED   cp 0       42
    8/1R6/8/5R2/3K4/8/8/5k2 b - - 97 40          base    p=4      MISSED   cp 0       1758
    8/1R6/8/5R2/3K4/8/8/5k2 b - - 97 40          seat12  p=4      MISSED   cp 0       1758
    8/1R6/8/5R2/3K4/8/8/5k2 b - - 97 40          seat27  p=4      MISSED   cp 0       1758
    8/1R6/8/5R2/3K4/8/8/5k2 b - - 96 40          base    p=4      FOUND    mate -2    2085
    8/1R6/8/5R2/3K4/8/8/5k2 b - - 96 40          seat12  p=4      FOUND    mate -2    2085
    8/1R6/8/5R2/3K4/8/8/5k2 b - - 96 40          seat27  p=4      FOUND    mate -2    2085

    rows: 18   mismatches: 0

**Neither patch changes a single node count, on any cell, at either mate length.**
That is a stronger statement than "it still returns cp 0": the patched builds are
bit-for-bit indistinguishable from base on this whole instrument, so the repair
cannot be claimed to have touched this rule at all.

## Why, from the source of each patch

seat 12 `two_doors_mate.patch.txt` adds a pre-pass over the root's legal moves
before the root guard at 2251: if any root move mates immediately, it declines
the adjudication. On the reported board no root move mates (Black is the one
being mated), so the pre-pass finds nothing and the guard behaves identically.
Even where it does fire, it only covers a root-side mate in one -- it never
touches the leaf rule at 1302 that produces this 0.

seat 27 `drawn_root_reporting.patch.txt` replaces the loop at 2259 that re-emits
a drawn root's score once per depth with a single emit at depth 1. It changes
how many info lines a drawn root prints and nothing else. On this board the root
guard does not even fire (measured: root_drawn=0 at H=99), so the patch's code
does not execute.

## What a repair has to change

The condition at 1304 asks "is this node checkmate?", when the rule it is
implementing needs "can the side to move deliver mate now?". A root-only patch
cannot reach it, and a reporting patch cannot reach it either. The correct cell
to change is the leaf predicate, and it has to change for every clock H >= 100-p,
not for the one clock in the bug report (see job3/BAND_TABLE.md: the miss starts
at H=97 for a mate in two, not at 99).
