# S02 check of seat 17's S-F1 — CONFIRMS, on both builds, with the zero-node signature

Their finding: "`go depth N searchmoves <name with no legal root move>` answers `bestmove 0000` on a position
that HAS legal moves (startpos: 20 legal, 0000 returned) — UCI defines 0000 as 'no legal move exists', so a GUI
reads it as an illegal move."

This is the same phenomenon as **my own S-F2** ("an empty `searchmoves` restriction answers `bestmove 0000` on a
board with 20 legal moves"), found independently by two seats from different directions. Their description is the
more precise one — they add that the answer comes with **five zero-node depth lines**, which is the signature that
the root was filtered to nothing.

## my measurement, both builds

| build | `searchmoves` | bestmove | depth lines | zero-node lines |
|---|---|---|---|---|
| PC r15 + PC20 | `zzzz` | **0000** | 5 | **5** |
| PC r15 + PC20 | `e2e5` (illegal) | **0000** | 5 | **5** |
| PC r15 + PC20 | `a1a8` (illegal) | **0000** | 5 | **5** |
| PC r15 + PC20 | (empty clause) | **0000** | 5 | **5** |
| PC r15 + PC20 | `e2e4` (legal — CONTROL) | e2e4 | 5 | 0 |
| base + S14 | `zzzz` | **0000** | 5 | **5** |
| base + S14 | `e2e5` | **0000** | 5 | **5** |
| base + S14 | `a1a8` | **0000** | 5 | **5** |
| base + S14 | (empty clause) | **0000** | 5 | **5** |
| base + S14 | `e2e4` (CONTROL) | e2e4 | 5 | 0 |

Startpos has 20 legal moves in every row. Threads 1, Hash 16, OwnBook false, cold, interactive driver.

## verdict: CONFIRMS
- **`bestmove 0000` on a live 20-move position**, on both builds, for every form of "no legal root move" —
  a garbage name, an illegal move, and an empty clause.
- **The five zero-node depth lines** are present in every failing case and absent in the control, which is exactly
  the signature their finding names.
- **The control is clean**: a LEGAL `searchmoves e2e4` returns `e2e4` with no zero-node lines, so the harness can
  tell the two apart and the 0000 is not an artefact of the command being present.

## the one thing I would add to their finding
The `0000` is not specific to a *bad* `searchmoves` value: **it also happens with an empty restriction**, which is
my S-F2's case. So the condition is "the restriction admits no legal root move", however that came about, and a
GUI that sends `searchmoves` from a list it believes is populated will hit it if the list is stale or empty.

## relation to UCI
`0000` means "no legal move" and a GUI will typically score the position as a loss or resign. So the practical
impact is the same as their finding says: an engine that answers `0000` on a live position can make a GUI abandon
a playable game. That makes this worth a guard on the GUI side (never send an empty `searchmoves`) until the engine
answers something else.
