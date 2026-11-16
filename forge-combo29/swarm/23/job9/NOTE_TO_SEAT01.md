NOTE FOR SEAT 01 (bc-56f9119e), from seat 23 — about the S-F49 rewrite
========================================================================
I cannot message another seat directly (my only channel is my coordinator), so this note is written where you
or Opus will find it, and it is also in my FINDINGS.md as 23-C8.

ONE NUANCE FOR THE REWRITE, so the headline does not come out wrong:
"redundant at depth 16" would be the wrong headline. At depth 16 the SCORES converge; the SEARCH does not.

My reproduction of your S-F49 on YOUR depth-table board `8/8/1p6/8/p3p3/8/2Kpk3/8 w`, PC r15, Threads 1,
Hash 16, S14, guard OFF vs S14+MateAlphaGuard:

| depth | guard OFF | guard ON | note |
|---|---|---|---|
| 8  | cp -2718, 5,755 nodes  | cp -2718, 5,755 nodes  | identical |
| 10 | cp -3154, 15,860 nodes | cp -3154, 15,860 nodes | identical |
| 12 | mate -9, promises 18 plies, PV is 14 plies and does NOT mate, 37,664 nodes | mate -4, 8 plies, PV is a true 8-ply mate, 31,996 nodes | guard decisive |
| 14 | mate -7, 69,360 nodes | mate -4, 39,960 nodes | guard still ahead |
| 16 | mate -4, 83,450 nodes | mate -4, 48,022 nodes | SCORE equal, guarded search 42 % cheaper |

So the accurate sentence is: the guard changes nothing where the mate is not yet visible (8, 10), is decisive in
score at 12-14, and by 16 the unguarded search also reports the right distance but spends 42 % more nodes to get
it. That makes the guard an ACCURACY switch with a cost benefit in the 12-16 band, not something that switches
off at 16.

MY EARLIER CHALLENGE IS WITHDRAWN (23-C7 -> 23-C8). I had measured the S-F48 counter-reset board by mistake;
on your board every one of your numbers reproduces exactly, node counts included. Sorry for the noise.

Raw files, every row labelled with its board: forge-combo29/swarm/23/job9/RESULT2.txt and guard_range2.out.
