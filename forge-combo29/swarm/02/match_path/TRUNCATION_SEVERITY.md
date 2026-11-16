# Is the truncated MultiPV line set (S-F10) presentational or a correctness bug?

**Answer: PRESENTATIONAL.** `truncated_bestmove.py`, PC r15 + PC20, Threads 1, Hash 16, OwnBook false, fresh
process per search, 3 positions x 5 budgets (500, 1000, 2000, 5000, 20000).

## the test
For every cell, compare three things:
- the `bestmove` the engine sent,
- the first move of its OWN `multipv 1` line at the deepest depth it reported,
- the `bestmove` of a MultiPV 1 search on the same node budget (the deeper reference).

## the answer
**bestmove equals its own multipv-1 line in 15 of 15 cells.** Zero illegal bestmoves. The truncated line set never
makes the engine play a move it did not report as its first line.

| position | N | MPV 8 deepest depth | lines at that depth | bestmove | its own mpv1 move | MultiPV-1 ref move |
|---|---|---|---|---|---|---|
| game_mid2 | 500 | 2 | 3 | b8a8 | b8a8 | f6d7 |
| game_mid2 | 1000 | 2 | 3 | f6d7 | f6d7 | g7g6 |
| game_mid2 | 5000 | 4 | 5 | e5e4 | e5e4 | g7g6 |
| game_end | 1000 | 3 | 5 | b4c4 | b4c4 | b4f4 |
| game_end | 2000 | 4 | 3 | b4c4 | b4c4 | b4f4 |
| game_end | 20000 | 7 | 5 | b4f4 | b4f4 | b4f4 |

14 of 15 cells had fewer than 8 lines at the deepest depth, so the truncation itself is common under a tight
budget — but the move is always consistent with the line the engine reports.

## the one thing that IS different, and what causes it
In 8 of 15 cells the MultiPV-8 bestmove differs from the MultiPV-1 **reference** move. That is real, but it is
**not the truncation**: a MultiPV 8 search on the same budget reaches depths 2-7 where MultiPV 1 reaches 4-11, so it
plays the move a shallower search would choose. The cause is the depth dilution of **S-F9**, already measured
separately, not the missing lines.

So the two defects stay separate and their severities are now pinned:
- **S-F9 (dilution)**: changes the MOVE, because it costs depth. This is the one that matters.
- **S-F10 (truncation)**: changes only how many PV lines are shown at the deepest depth. Presentational.

## what a GUI author should do
If you display a MultiPV table, do not assume the deepest reported depth has M lines: keep the previous depth's
lines for the missing indices rather than showing a blank or a stale line as if it were current. The move to play
is safe to read from `bestmove`.
