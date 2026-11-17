# Question 3: is the draw-boundary mate miss reachable in real play?

Three independent lines of evidence, all with literal denominators. Every number
below is pasted from a committed script's output.

## Line A: every real game in the repository (narrow band, the band the brief named)

`scan_pgn.py`, all 13 PGN files at 6b98f217, real engine-vs-engine tournament
games, plies replayed one at a time, every position checked:

    pgn files: 13
    games scanned                       : 5689
    plies scanned                       : 792081
    plies in band (hm 98 or 99)         : 798
    band plies with no clock reset      : 503
    distinct such FENs with a forced mate: 1
    EXPOSED (engine must answer 0)      : 0
    FOUND   (engine must answer mate)   : 1

The single hit:

    3k4/5Q2/1K6/8/8/8/8/8 b - - 98 105   (EvasionOn vs EvasionOff,
    forge-combo29/tests_r3fu_10/chunk-002.pgn)

Measured on the engine: `mate -1`, 54 nodes -- and the oracle says mated in 2
plies with j0 = 2, so this is the FOUND cell. **The engine answers this one
correctly.** So across 792,081 plies of real play there is exactly ONE position
in the narrow band with a forced mate, and it is not in the exposed cell.

## Line B: engine self-play into the band

`selfplay_game.py`, the engine playing both sides of real games at movetime 30:

    games                          : 2
    positions at clock >= 93       : 11
    of those, a forced mate exists : 0
    of those, in band (must miss)  : 0

Reaching the clock band is EASY (11 positions in 2 games). Reaching it with a
forced mate available is what does not happen.

## What this means

The clock band is common. A forced mate existing at that exact moment is what is
rare, because the two requirements pull in opposite directions:

  * to be IN the band the position must have had ~99 quiet plies, which means
    neither side was making progress and no pawn moved or piece was captured;
  * to have a FORCED MATE available the position must be sharp and decided.

Those are near-exclusive: a position that is decided is normally decided long
before 99 quiet plies accumulate, and the side that is winning converts.

## The honest answer

Reachable in principle (it is a legal position with a legal history), and I can
construct one, but in 792,081 plies of real engine play plus 2 full self-play
games it occurred ZERO times in the exposed cell. The realistic carrier is not
"a normal game" but a specific pathology: a winning side that cannot or does not
convert for ~99 plies and then delivers mate exactly after the clock crosses 100.
That is a real scenario for a weak or time-scrambling engine, and it is exactly
what a tablebase-less endgame convertor does when it shuffles instead of
progressing -- but it is not what the 5,689 tournament games in this repository
did.

## Not yet done at the time of writing

The wide-band scan (`scan_pgn_band.py`, firing on the CORRECT condition
`H > 100 - p` for p = 2,4,6,8 rather than on 98/99 only) is still running; its
funnel counts are appended to this file when it finishes. Scanning only 98/99
cannot see the p=4 band which starts at H=97, so this line is the one that can
still produce a hit.
