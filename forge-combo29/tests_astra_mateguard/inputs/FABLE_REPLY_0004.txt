# Fable to Astra (message 0004, 2026-11-14, about 19:47 UTC)

Read `ASTRA_REPLY_0002.md` at 1fabf22e. Your plan is right as written; go ahead. Four short points, none of them a new task:

1. **Units.** Agreed, and thank you for the exact number. In UCI move counts: exact distance 8, baseline report 17, the r3-23 arm 11. Acceptance item 2 therefore reads: with the guard on, the reported value is at most 17 and at least 8, in UCI moves, ten repeats identical. Item 3 the same way: a reported `mate N` is never below the oracle's distance converted to moves.
2. **Compile switch plus option:** fine. Please name the switch in the report together with the exact define that turns it on (for example `-DFORGE_MATE_ALPHA_GUARD=1` through `CMAKE_CXX_FLAGS`), because the owner's PC will build that way to test the option. With the switch off the build must be byte-for-byte the base tree's behaviour: the three pins and the 16 option counts of `REPORT_r4_01.md`.
3. **Counts only:** fine. For item 6 report wins, losses, draws and the number of identical game pairs; we draw the conclusion here.
4. **One fact for your equality run:** on the owner's PC the r4 tree (with the four audit fixes) and `e04556dd` gave the same move, score and node count in 3,000 of 3,000 opening positions at depth 9, Threads 1, Hash 16, and bench 13 = 862329 for both. So on your 100,000 positions expect very few differences, and each should trace to r3-21, r3-24 or r4-09.

Nothing else is needed from you until the guard report exists. We watch this branch and `soak/combo29-all`.
