# PREDICTION — seat 25, area 5, job 1 THIRD RUN (seed 2521)

Written before the first measuring command of this run. Never edited afterwards.

## What differs from runs 1 and 2
- Seed 2521 (SEED + 20), new position set R3 (250 random-game positions, one every 7 plies).
- I now ALSO record, for every mate score, whether the reported `mate N` is consistent with the PV length,
  and I classify each bad one as "PV short" or "score wrong", using the engine's own deeper PV as the
  reference for the true distance (play it with python-chess; if it checkmates in d plies, the true score is
  the one matching d). This is the method that settled S-F1, applied systematically this time.

## Predictions, each with the range that kills it
R1  250 searches complete. KILLED if fewer.
R2  0 PVs with an illegal move. KILLED if >= 1.
R3  number of mate scores: 5 to 20 (run 2 had 12; run 1 on endgames had 10). KILLED if outside [2, 30].
R4  number of mate scores whose PV does NOT end in checkmate: 1 to 4. KILLED if 0 or if > 8.
R5  Of those, the share where the engine's OWN deeper search gives a DIFFERENT mate number (i.e. the score
    itself is wrong, not just the PV): I predict at least half. KILLED if 0 (then only PVs are truncated and
    every score is right).
R6  For every mate score, the engine's deeper PV (depth 24) will itself end in checkmate at the distance it
    claims: I predict at least 80% of them. KILLED if below 50%, which would mean even deep mate PVs are
    untrustworthy.
