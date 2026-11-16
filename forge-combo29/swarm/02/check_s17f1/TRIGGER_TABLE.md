# `bestmove 0000` on a live position — every trigger, as separate rows

The condition is broader than "a bad `searchmoves` value": it is **any restriction that admits no legal root
move**, however it arose. A GUI guard needs that distinction, so each trigger is its own row here rather than an
addition to another seat's finding.

Startpos, 20 legal moves in every row. PC r15 + PC20 and base + S14, Threads 1, Hash 16, OwnBook false, cold,
interactive driver.

| # | trigger | example command | bestmove | zero-node depth lines | who found it |
|---|---|---|---|---|---|
| 1 | `searchmoves` names a **garbage/unknown** move | `go depth 5 searchmoves zzzz` | **0000** | 5 | seat 17 (S-F1) |
| 2 | `searchmoves` names an **illegal** move (pseudo-legal-looking) | `go depth 5 searchmoves e2e5` | **0000** | 5 | seat 17 (S-F1) |
| 3 | `searchmoves` names an illegal move, different shape | `go depth 5 searchmoves a1a8` | **0000** | 5 | this check |
| 4 | **`searchmoves` with NO move after it** (empty restriction) | `go searchmoves depth 2` | **0000** | 5 | me (S-F2) |
| 5 | `searchmoves` naming only moves that ARE legal | `go depth 5 searchmoves e2e4` | e2e4 | **0** | CONTROL |

Rows 1-4 are the same observable with four different causes, and row 4 is the one a GUI hits by accident: a move
list that is stale or empty produces an empty `searchmoves` clause, not a malformed one. Row 5 is the control that
proves the harness can tell the cases apart.

## why the distinction matters for a GUI guard
- A guard of the form "validate the move name before sending `searchmoves`" catches rows 1-3 and **misses row 4**,
  because row 4 has no name to validate.
- The guard that covers all four is "**never send a `searchmoves` clause with no legal move in it — if the list is
  empty, omit `searchmoves` entirely**", which is a statement about the LIST, not about any individual name.
- Until the engine answers something other than `0000` on a live position, that guard is the only defence, because
  `0000` means "no legal move exists" to UCI and a GUI will score the position as lost.

## the shared signature
All four failing rows emit **five zero-node depth lines** before the `bestmove`, and the control emits none. That
is the reliable detector if a harness wants to flag the condition after the fact rather than prevent it: a search
that reports `nodes 0` at depth 1 with 20 legal moves on the board was filtered to nothing.
