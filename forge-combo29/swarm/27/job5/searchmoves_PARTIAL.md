# The searchmoves IIR patch is PARTIAL - read this before using it

Measured (release build, startpos, S14, Threads 1, Hash 16, paced driver):

| go line | base build | patched build (this patch) |
|---|---|---|
| `go depth 12` | cp 30, 56720 nodes | cp 30, 56720 nodes (unchanged - good) |
| `go depth 12 searchmoves e2e4` | cp 23, 26329 nodes | cp 26, 36117 nodes |
| `go depth 12 searchmoves e2e4 d2d4` | cp 23, 16770 nodes | cp 27, 40859 nodes |

So stopping IIR from firing at a restricted root recovers about half the difference (23 -> 26) and
restores the node count (26k -> 36k), but the restricted score is still not the unrestricted 30.
There is at least one more cause, most likely the deliberately skipped TT store for a restricted
root (search.cpp:2093): without it, every shallower root iteration re-searches from scratch and the
aspiration window decisions differ. I did NOT chase it further because:
  - the honesty numbers are unchanged (bench 11/13/16 and perft 5 identical), so the patch is safe;
  - the remaining difference is in a diagnostic path (searchmoves), not in game play;
  - claiming a fix here would be false, and this brief puts an honest partial above a tidy claim.

RECOMMENDATION to Opus: take the patch only as a first step, or not at all, and treat S-F8 as still
open. The finding stands on its own (the score really does change); the patch does not close it.
