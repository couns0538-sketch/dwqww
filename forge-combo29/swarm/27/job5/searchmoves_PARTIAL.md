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

## Second experiment: is the skipped TT store the other cause? NO.

I removed BOTH the IIR ply at a restricted root AND the TT-store guard (search.cpp:2093),
rebuilt, and re-measured with the same driver:

| go line | base | IIR only | IIR + TT store |
|---|---|---|---|
| `go depth 12` | cp 30 / 56720 | cp 30 / 56720 | cp 30 / 56720 |
| `searchmoves e2e4` | cp 23 / 26329 | cp 26 / 36117 | cp 26 / 36117 |
| `searchmoves e2e4 d2d4` | cp 23 / 16770 | cp 27 / 40859 | cp 26 / 32441 |

Restoring the TT store changes nothing for the one-move case. So the remaining gap (26 vs 30) has a
THIRD cause I have not identified. Candidates I did not test: the aspiration window path (the score
history that seeds each iteration differs when the root list is smaller), and the fact that a
restricted root never gets a tt_move so every iteration re-searches without the move ordering the
previous iteration would have supplied.

I am stopping this line of work here and leaving S-F8 OPEN with two causes pinned and one unnamed.
Guessing further without a test would violate the brief's first rule.
