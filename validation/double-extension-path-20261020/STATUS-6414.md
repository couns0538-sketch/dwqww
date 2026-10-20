# Forge 6.4.14 extension-path repair

Frozen source21538ec5416c909fc98a08688242a0b3b9710b25 preserves parent6.4.13
and all accepted work. The search captures its inherited double-extension
budget before pruning, restores it after both same-ply verification calls,
and assigns every child from that budget. The existing <=6 threshold is unchanged.

All9CTest suites passed in each of Release, ASan/UBSan and TSan; seven actual
TT API groups passed in each profile. Eight active-UCI TSan transitions passed.
Eight Wine checks and914independent Windows artifact checks passed. The actual
normal trace's5038child-count mismatches become zero. Synthetic inherited-count
fixtures demonstrate old count8 versus repaired maximum7; this does not claim
natural-root overflow or stronger play. Complete original failure attempts remain.

One original bare Linux bench invocation hit60seconds with empty output. Three
later fixed5-second syscall diagnostics on unchanged parent/candidate binaries
completed normally at419798nodes; Windows stays351063nodes. This does not
explain or erase the original timeout. Finite correctness tests passed, but full
operational readiness remains qualified. No measured NPS or Elo gain is accepted.
The designated integration branch remains unchanged; candidate stays isolated.

The prior TT strength run was invalidated by a baseline time forfeit. It does
not test6.4.14. Causal replay is a separate diagnostic, with fixed historical
clocks rather than new games. Do not retry or pool the old match.
