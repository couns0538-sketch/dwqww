# CHECK of seat 17 S-F1 / S-F2 — CONFIRMS (with hard assertions on every parsed value)

## Seat 17's claims (verbatim from its FINDINGS.md)
- S-F1: "`go depth N searchmoves <name with no legal root move>` answers `bestmove 0000` on a position that
  HAS legal moves (startpos: 20 legal, 0000 returned) - UCI defines 0000 as 'no legal move exists', so a GUI
  reads it as an illegal move"
- S-F2: "source of S-F1: `src/search.cpp:2640` `if (result.best_move.is_none()) result.best_move =
  root_candidates.front();` reads `front()` of an EMPTY MoveList when `root_candidates` is empty but legal
  moves exist (line 2210 already detects exactly this state as `restricted_root_empty`)"

I wrote `checks/check_s17f1.py` from the S-F1 sentence; seat 17's script was not read or copied.

## Measurement integrity (seat 19's warning)
Every case's verdict is read through `bm_of()`, which FAILS HARD and prints `VERDICT: INVALID` if a case
produced no `bestmove` line at all — a missing line can never read as "not 0000" and slip through as a
confirmation. The run had 0 missing bestmove lines, so the assertions passed and the verdict stands.

## Raw result (ASan+UBSan build, sha256 37c0d256…)
```
case                       bestmove  info string                                                     san
c1 control, no searchmoves d2d4      (none)                                                          0
c2 searchmoves, no names   0000      searchmoves restriction has no legal root moves                  0
c3 searchmoves e2e4        e2e4      (none)                                                          0
c4 searchmoves a1a1        0000      searchmoves restriction has no legal root moves                  0
c5 searchmoves e2e5        0000      searchmoves restriction has no legal root moves                  0
c6 one-legal-move board    0000      (none)                                                          0
c7 searchmoves e2e4 d2d4   d2d4      (none)                                                          0
```
(`checks/s17f1/check_s17f1.txt` and `.json`)

## Verdict
- **CONFIRMS S-F1.** The control is a real move (d2d4), so the board genuinely has 20 legal moves; with
  `searchmoves` naming nothing legal the engine answers `bestmove 0000` and says so in an `info string` line.
  With a legal name it honours the restriction (e2e4, and one of e2e4/d2d4).
- **Partially confirms S-F2, with one correction.** The state is detected at search.cpp:2210 and announced at
  2211. The unguarded `root_candidates.front()` at 2640 is real. But ASan and UBSan report **nothing** on that
  path, so it is not an out-of-range *read* ASan can see: an empty `std::vector`'s `begin()` is a valid
  pointer in libstdc++, and `front()` on it yields a garbage `Move` that the UCI printer then renders as
  `0000`. So the fault is "undefined behaviour that happens to look like 'no legal move'", not a caught
  memory error. That distinction matters for anyone who tries to find it with a sanitizer.

## What this check does NOT show
- It does not test a restricted root where the restriction names a legal move at a deeper depth, nor
  `searchmoves` together with `go nodes`/`movetime`.
- Case c6 used a board with exactly one legal move and returned 0000 without an info line; I did not chase
  why that one is silent.
