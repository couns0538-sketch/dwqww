# PREDICTION — seat 25, area 5, job 1 SECOND RUN (cycle c: next seed, new position set)

Written before the first measuring command of this run. Never edited afterwards.

## What differs from my first run (required by the brief)
- Seed: **2511** (SEED + 10), not 2501. New R position set generated from it.
- Position set: a FRESH random-game set R2 (SEED 2511), 250 positions, one every 7 plies, never used before.
- Depth 12 and S14 unchanged, so the comparison with the first run is like-for-like on settings.
- Additionally I re-check the specific position of S-F1 as a control: it MUST still show `mate -12`, otherwise
  my first finding does not reproduce and I would have to withdraw it.

## Predictions, each with the range that kills it
Q1  searches run on R2 (250 positions): 250. KILLED if fewer.
Q2  PVs with an illegal move: 0 of 250. KILLED if >= 1.
Q3  mate scores seen across 250 fresh game positions at depth 12: between 0 and 5. KILLED if > 10.
Q4  Of those mate scores, the count whose PV is the wrong length or not checkmate: I predict 0, because S-F1
    needed a very specific endgame position. KILLED if > 2 (which would mean the fault is common, not rare).
Q5  Control: re-running S-F1's position at depth 12 with S14 still prints `mate -12` and an 18-ply PV.
    KILLED if it prints anything else (then S-F1 is not reproducible and must be withdrawn).
Q6  Random-game positions are mostly middlegame, so I predict the mean nodes per search is between 20,000 and
    120,000 at depth 12. KILLED if the mean is outside [5,000, 500,000].
