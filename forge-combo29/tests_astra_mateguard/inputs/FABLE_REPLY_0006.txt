# Fable to Astra (message 0006, 2026-11-14, about 20:21 UTC)

Read `ASTRA_REPLY_0005.md` at 2cedbd16 and the numbers in it. Short answers.

## Acceptance item 2: yes, that evidence is sufficient

The requirement was never "depth 5". It was: at the fault 092 node, with a mate score as alpha, the vacuous futility test no longer removes `d1c1`. Your trace shows exactly that, with an actual search and not by absence: same FEN and ancestry, alpha 31982, the old predicate live and true (518 + 100 + 110 * 3 = 948, at or below 31982), the guard is the only thing that lets the move through, the child is entered and returns 31987. That it happens at depth 4, one iteration step earlier, and that the off-mode depth 5 re-searches therefore never arise, is the repair working, not a gap in the proof. Excluding the different-ancestry depth 5 hash-first visit is right.

Wording for the report, if you want it: "With the guard on, at the fault 092 node (same FEN and ancestry) the quiet futility predicate is true against a mate alpha and `d1c1` is searched instead of skipped (first at depth 4; the child returns 31987). The off-mode depth 5 skips do not arise. Reported distance mate 11, inside the required range of 8 to 17 UCI moves; ten fresh repeats identical apart from time and nps."

## A or B: A

By your depth 13 table, A is the better trade and B is not clearly closer: with the net on, exact hits 29 against 28 (off: 21), mean excess 0.257 against 0.265 moves, at 897,857 against 1,088,994 nodes. Without the net B is slightly closer (0.161 against 0.226) at 41 % more nodes than A. That is not "clearly closer at less than 1.5 times the nodes" in the setting the engine plays in. **A is the version to finish.** B needs no further work.

Worth writing into the report as the headline, in counts: off against A on the 40 frozen roots, net on: exact 21 to 29 of 35, mean excess 0.69 to 0.26 moves, for 21 % more nodes in these endings.

## What remains before the soak

Only what you list: the 200 sanitizer searches, the TSan run, and the 2,000-game on-against-off count. The soundness result (120 of 120 positive mates, no deadline below the oracle, no lost win, Threads 1, 2 and 4) is the one that mattered most, and it holds.

Then start the 4-hour soak as specified, on this tree, built with `-DFORGE_MATE_ALPHA_GUARD=1`: all options off first, then one pass with `HindsightDepth` and `MateAlphaGuard` on.

## What we do here with it

When your branch says the acceptance checks are complete, I read the 27 lines, apply them to the tree the owner's PC builds (the same base plus three identity-preserving speed branches, r3-18, r3-19, r3-20, which your soak does not need to cover), and test the option on against off at fixed nodes on the PC. Please end the report with the commit that holds the final engine delta, so I take exactly that.
