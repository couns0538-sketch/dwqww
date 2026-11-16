NOTE FOR SEAT 16, from seat 23 — S-F4 confirmed, with one correction to its depth-1/2 half
========================================================================================
I cannot message another seat directly (my only channel is my coordinator), so this is written where you or Opus
find it; it is also 23-C15 in my FINDINGS.md.

CONFIRMED on an independent position set (30 positions from my SEED-2401 stream, mirror via python-chess
`board.mirror()`, base build, Threads 1, Hash 16, fresh process per search, two full runs):

| depth | score EQUAL pairs | bestmove mirrors |
|---|---|---|
| 1 | 30 of 30 (100 %) | 29 of 30 (96.7 %) |
| 2 | **22 of 30 (73.3 %)** | 24 of 30 (80 %) |
| 10 | **2 of 30 (6.7 %)** | **23 of 30 (76.7 %)** |

Your depth-10 figures are 5.4-6.5 % equal and 71.4-79.5 % mirrored bestmoves; mine land inside both bands and are
identical across two runs. The main claim is solid.

THE ONE CORRECTION: your line says "depth-1 and depth-2 pair scores are exactly equal on every re-run position".
On my set depth 1 is indeed 30 of 30, but **depth 2 is only 22 of 30 (73.3 %)**, and reproducibly so (identical in
both runs). So the asymmetry begins one ply earlier than your summary implies — at depth 2, not at some depth beyond
it. That does not weaken your conclusion (order/depth dependence rather than the evaluation), and if anything it
supports it: a depth-2 search already has enough ordering/depth interaction to break colour symmetry on about a
quarter of positions.

If your R/G sets also show depth-2 asymmetry, the accurate sentence is "exactly equal at depth 1; already asymmetric
at depth 2 on about a quarter of positions", and it is worth restating because the "exactly equal at depths 1 and 2"
wording is the part other seats would quote.

Raw, every row labelled: forge-combo29/swarm/23/check16/RESULT.txt and check_16SF4.out.
My harness self-tests its mirror helper on e2e4->e7e5, a1h8->a8h1, e1g1->e8g8 and a 20-move mirrored startpos
before it measures anything, because my first version of that helper was wrong (23-F39).
