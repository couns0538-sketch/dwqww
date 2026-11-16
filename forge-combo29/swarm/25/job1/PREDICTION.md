# PREDICTION — seat 25, area 5, job 1 (PV legality and mate scores)

Written before the first measuring command of this job. Never edited afterwards.

## What I am about to measure
Every search at depth 12, S14 settings, Threads 1, Hash 16, on set O (200 positions, first200.fens) and set G
(353 positions, set_G.epd) — 553 searches. For each search I take the LAST `info ... pv` line and play its moves
with python-chess from the search position. I also check every `mate N` score against the length of its PV.

## Predictions, each with the range that kills it
P1  searches run (out of 553): 553. KILLED if fewer than 553 (a lost search is itself a finding).
P2  PVs with every move legal: 553 of 553 = 100 %. KILLED if the count of PVs with an illegal move is >= 1.
P3  `mate N` scores seen in 553 depth-12 searches on these game positions: between 0 and 3.
    KILLED if more than 10 are seen.
P4  Of the `mate N` scores seen, PVs whose length matches the rule (2N-1 plies for N>0, 2|N| plies for N<0):
    all of them. KILLED if any mate PV has the wrong length by more than 0 plies.
P5  My checker catches a planted illegal last move in a PV (the control): yes, exactly 1 catch in 1 attempt.
    KILLED if it reports 0 catches on the control.
P6  Searches whose last info line carries NO pv at all: 0. KILLED if more than 5.

## Notes on the method
- A PV is validated by playing it from the search position; "legal" means python-chess accepts every move in order.
- The mate check: after playing the whole PV, the side to move must be checkmated and the PV must be a mate line of
  the stated length. I count "wrong length" as: the position after the PV is checkmate but len(pv) != required, or
  the position after the PV is not checkmate at all.
