# Wide-band real-play scan, and the H=100 cell that is NOT the defect

`scan_pgn_wide.py` fires on the CORRECT condition (from job3/BAND_TABLE.md:
missed iff `p > 100 - H`) rather than on the 98/99 band the brief named. Corpus:
all 13 PGN files at 6b98f217, 5,689 real engine tournament games.

## Funnel (first run, before the terminal-position fix)

    games scanned                        : 5689
    plies scanned                        : 792081
    clock >= 93                          : 3825
    of those, <= 6 pieces                : 2305
    of those, no clock-resetting move    : 1673
    distinct FENs tested for a mate      : 1220
    with a forced mate (p in 2,4,6)      : 4
    IN BAND (H > 100-p)                  : 1

The four positions with a mate are all the TAIL OF ONE GAME
(EvasionOn vs EvasionOff), the final conversion sequence:

    near H=94 p=6 j0=6  K2k4/5Q2/8/8/8/8/8/8 b - - 94 103
    near H=96 p=4 j0=4  2k5/K4Q2/8/8/8/8/8/8 b - - 96 104
    near H=98 p=2 j0=2  3k4/5Q2/1K6/8/8/8/8/8 b - - 98 105
    "HIT" H=100 p=2 j0=0  2k1Q3/8/1K6/8/8/8/8/8 b - - 100 106

## The H=100 row is not a hit, and I nearly reported it as one

`2k1Q3/8/1K6/8/8/8/8/8 b - - 100 106` has **no legal moves** -- it is already
checkmate. Measured:

    base -> mate 0, 0 nodes, bestmove 0000

`mate 0` at 0 nodes is the terminal-root path, not the fifty-move rule. The scan
was counting it because `mated_within` trivially returns true when every move
loses, and a checkmated board has no moves to iterate.

There are TWO reasons this row cannot count as the defect, and both had to be
fixed in the scan rather than argued away:

1. **It is terminal.** `scan_pgn_wide.py` now returns `None` from
   `mate_distance` when the board has no legal moves.
2. **At H=100 the side to move can claim the draw itself.** The defect needs the
   clock-100 node to appear BELOW the root, i.e. `j0 = 100 - H >= 1`. A root
   whose own clock is already 100 is the root-guard case, where 0 is correct.
   The scan now requires `j0 >= 1`.

So the honest count from this corpus is **0 exposed positions**, and the one
candidate the first run produced was an artefact of two unfixed conditions in my
own filter -- found by measuring the "hit" instead of trusting the label.

The re-run with both conditions applied is `pgn_wide2.log`; its funnel is pasted
into REAL_PLAY.md.
