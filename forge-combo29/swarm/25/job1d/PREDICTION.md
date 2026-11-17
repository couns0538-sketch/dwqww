# PREDICTION — seat 25, area 5, job 1 FOURTH RUN (seed 2531, set R4)

Written before the first measuring command of this run. Never edited afterwards.

## What differs from runs 1-3
- Seed 2531 (SEED + 30), a fresh R4 set of 250 random-game positions, one every 7 plies.
- Depth 12, S14, Threads 1, Hash 16 unchanged, so the comparison stays like-for-like.
- For the first time I record, per mate score, whether the reported distance ever FELL with depth - the mechanism
  test from S-C32 (a mate should appear as *nothing, then the true distance*). I predict that a depth-12 mate score
  equals the depth-20 mate score on the same board, for every board where both report one.

## Predictions, each with the range that kills it
S1  250 searches complete. KILLED if fewer.
S2  0 PVs with an illegal move. KILLED if >= 1.
S3  mate scores seen: 5 to 20 (runs 2 and 3 saw 12 and 6 on similar sets). KILLED if outside [2, 30].
S4  mate scores whose PV does NOT end in checkmate: 0 to 2. KILLED if > 4.
S5  For every board with a mate score at depth 12, the depth-20 mate number is EQUAL or SHORTER (never longer).
    This is the S-C32 mechanism stated as a prediction on new data. KILLED if any board's depth-20 mate number is
    LONGER than its depth-12 number.
S6  Positions where the depth-12 search reports a mate but depth 20 does NOT: 0. KILLED if >= 1. (A found mate
    should not vanish with more search.)
