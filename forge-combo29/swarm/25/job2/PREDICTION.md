# PREDICTION — seat 25, area 5, job 2 (draw scores)

Written before the first measuring command of this job. Never edited afterwards.

## What I am about to measure
The score the engine reports at depth 10 (S14, Threads 1, Hash 16) for five groups of positions:
  A  20 positions K v K            (bare kings, random legal squares, not adjacent)
  B  20 positions KN v K           (insufficient material)
  C  20 positions KB v K           (insufficient material)
  D  20 positions KNN v K          (NOT insufficient material: mate is possible)
  E  20 positions with a threefold repetition on the board, reached by a real move list
  F  20 positions with the fifty-move counter at 99
All generated with SEED 2501, written to files before use.

## Predictions, each with the range that kills it
P1  Group A (K v K): score exactly cp 0 in 20 of 20.        KILLED if any A score is not 0.
P2  Group B (KN v K): score exactly cp 0 in 20 of 20.       KILLED if any B score is not 0.
P3  Group C (KB v K): score exactly cp 0 in 20 of 20.       KILLED if any C score is not 0.
P4  Group D (KNN v K): NOT all zero — the engine should see a win (KNN v K is mate-able), so I predict
    at least 15 of 20 have |score| >= 100 cp, and none claims a mate score.  KILLED if 15 or more are 0.
P5  Group E (threefold on the board): score exactly cp 0 in 20 of 20.  KILLED if any E score is not 0.
P6  Group F (halfmove clock 99): the engine does not answer 0 — it should play on. I predict at most 5 of 20
    are exactly 0, the rest are non-zero. KILLED if 6 or more are exactly 0.
P7  Control for "0 is a real answer": a K v K position planted as NON-draw (K v K with a queen added to one side)
    must NOT score 0 — a harness that reports 0 for everything is caught. KILLED if the control scores 0.

## Notes
- "Score" means the last `info depth 10 ... score` value, and I also record whether a `bestmove 0000` was played
  (which would mean the engine thinks the position is terminal).
- A threefold position is built by playing a real move list, so the repetition is in the history the engine is
  given via `position startpos moves ...` — the FEN alone cannot express it.
