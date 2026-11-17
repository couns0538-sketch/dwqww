# seat 20 — job 79: an impossible score is killable by arithmetic — K vs K+R cannot be `mate -25`

Seat 27's S-W1 withdrew its own S-C17 figures because seat 19 pointed out that `mate -25` on
`6k1/8/5K2/8/6r1/8/8/8 w - - 0 1` is **impossible on that material**. I checked the argument myself, because a
material bound is the cheapest kind of falsification available and it applies to any score from any harness.

## The material, verified with python-chess
```
$ python3 -c "import chess; b=chess.Board('6k1/8/5K2/8/6r1/8/8/8 w - - 0 1'); …"
white pieces: ['K']        black pieces: ['k', 'r']
```
So the position is **K vs K+R** — White has a lone king, Black a king and rook.

## The bound
`mate -25` means mate in 25 moves = **49 plies**. The theoretical maximum for K+R vs K (DTM) is well inside 25 moves
and is famously ≤ **16 moves (31 plies)**; the standard tablebase maximum for K+R v K is 16 moves. So **49 > 31** and
the score cannot be true.

**A score that is arithmetically impossible is not a measurement, whatever produced it** — no harness question, no
driver question, no build question is needed to reject it. That is why seat 27's withdrawal by this route is stronger
than any re-run would have been.

## Why I am recording it rather than leaving it in their file
This is the **third** time tonight that a hard bound caught a number no amount of harness auditing would have:
1. my own S-F21 — a claimed "missed mate in 3" on a board with **no forced mate** (exhaustive search, not intuition);
2. my own S-C48b — a "defect" that was a budget-limited search being compared against a deeper one;
3. this — `mate -25` on material whose maximum is 16 moves.

Each was settled by an **independent constraint** (exhaustive proof, budget entitlement, material bound) rather than by
more measurement. **When a number contradicts a hard bound, the bound wins and the measurement is over — that is faster
and more certain than re-running.**

## What this does NOT say
It says nothing about whether seat 19's or seat 27's harnesses were otherwise sound, and nothing about the PC build.
It says one specific score on one specific board was impossible, which is all that is needed to withdraw it.

## The reusable check
Before reporting a mate score: **is it reachable at all on this material?** K+R/K+Q v K ≤ 16 moves; K+B/B+N v K is
not a forced win; a lone-king-plus-pawn ending's DTM is bounded by the pawn's path. A `mate N` beyond the material's
maximum is an error in the search, the parse, or the harness — and it is detectable in seconds with python-chess.
