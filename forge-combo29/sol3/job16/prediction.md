# Job 16 prediction

Each entry predicts the first requested depth reporting `bestmove g3g6`
with a positive mate score on P. `None` is a possible endpoint in a range
and means no such report through depth 20. All ladders use the Part 2
speed-1 build, built-in evaluation, Hash 16, one thread, NullMateGuard 0,
and fresh game state at each requested depth from 1 through 20.

| Ladder | R1 R2 R3 plain switches | S14 point | S14 range | PC20 point | PC20 range |
| --- | --- | --- | --- | --- | --- |
| L1 | 1 0 0 | D16 | D12–D20 | D17 | D13–D20 |
| L2 | 0 1 0 | None | D18–None | None | D18–None |
| L3 | 0 0 1 | None | D16–None | None | D16–None |
| L4 | 0 1 1 | None | D18–None | None | D18–None |
| L5 | 1 0 1 | D16 | D13–D20 | D17 | D13–D20 |
| L6 | 1 1 0 | D17 | D13–None | D18 | D14–None |

S14 uses quiet 2 and correction 0. PC20 has HistRework 2 and both halves
following it. R1 can change how early the quiet non-check `Qg6` is tried
and the reply order deeper in the tree. R3 can change the reduced child
depth if the history term crosses its integer threshold. R2 cannot
prune `Qg6` at the root or prune a quiet move that gives check, but it
can change what survives elsewhere. I expect ordering to matter most and
the other effects to depend on the new search order. The point depths
are approximate because those changes affect subsequent histories and
transposition-table contents.
