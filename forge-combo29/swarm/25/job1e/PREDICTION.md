# PREDICTION — seat 25, area 5, job 1 FIFTH RUN (seed 2541, set R5)

Written before the first measuring command of this run, and pushed alone. Never edited afterwards.

## The question this run is built around

Cycle (c) measured, on 250 random middlegame positions, that MultiPV 1 and MultiPV 3 disagree about the best move
on 18.8% of them at depth 12 and 16.4% at depth 16, that neither setting is more accurate when the disagreement is
resolved at depth 20 (27 vs 20, p=0.38), and that the gaps are large (median 43 cp).

The obvious follow-up, and the one my own S-F29 points at: **does the disagreement rate rise when the search is near
its horizon?** S-F29 established that file 6's half-move test needs depth 18 - at depth 16 a board with a forced mate
still reports `cp 1359`. If a display setting can change the answer at depth 12-16, it has more room to do so where
the search is shallow *relative to the position's difficulty*. So: pick positions that are HARD at a given depth and
measure the same quantity there.

Two proxies for "hard at depth 12", both computable without extra searches:
- **(a) big score swing between depth 12 and depth 16** - the search is still changing its mind.
- **(b) large best-move change between depth 12 and depth 16** - I already have 30 such boards from R4.

I will use R5 (250 fresh positions, seed 2541) as the honest replication set, and the R4 "unstable" boards as the
enriched set, and compare the disagreement rate between the two. That is a two-group measurement, and I commit to the
direction I expect before measuring.

## Predictions, each with the range that kills it

S1  250 searches complete at depth 12 for both MultiPV settings. KILLED if fewer than 250 records, or if either
    configuration is missing a record.

S2  The MultiPV-1 vs MultiPV-3 bestmove disagreement rate on R5 (a fresh random set, seed 2541, same build and
    settings) reproduces the R4 figure: predicted **10-25%**. KILLED if above 35% or below 5%. This is a
    replication of my own S-C48 number on data the number was not computed from, so it is a real test rather
    than a re-description. If R5 comes in far from R4, S-C48 is population-specific and I will say so.

S3  On the R4 boards where depth 12 and depth 16 chose DIFFERENT best moves (the 30 "unstable" boards), the
    MultiPV disagreement rate is **HIGHER** than on R5's random boards. Predicted rate on the unstable set:
    **25-60%**. KILLED if the unstable-set rate is not above the R5 rate at all. This is the "near the horizon
    there is more room to differ" hypothesis, and it is the one I expect to be the finding.

S4  Every MultiPV disagreement is also a score disagreement (0 score ties), as in both R4 depth families.
    KILLED if any differing bestmove has an EQUAL top-line score.

S5  Mate scores remain rare on a random set: **2-12** top-line mate scores across the 500 searches (250 boards x 2
    settings). KILLED if above 25. Runs so far saw 4 (R4 d12), 4 (R4 d12 mpv3), 6 (R4 d16).

S6  No NEW board shows the S-C47 pattern (a mate number apparently falling with depth while the MOVE is unchanged).
    I will check any mate boards with a pinned `searchmoves` ladder. KILLED if a pinned ladder shows a fall.

S7  The planted-case control still passes: MultiPV 1 re-run against its own stored record gives 0 differences over
    40 boards, and the three planted corruptions (wrong depth, wrong bestmove, score off by 1) are all caught.
    KILLED if the true control reports any difference or any plant is missed.

## What I will NOT do
- I will not run more than the planned searches to make a prediction look better; if a rate lands outside its
  predicted range I record the near miss or the miss as such.
- I will not claim a direction for "which MultiPV setting is better" on any new data without the pinned-reference
  treatment S-C50 used, because R4 taught me that the naive comparison (agreement with a free-search reference)
  is confounded by construction.
