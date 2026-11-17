# STATUS — swarm/72 rules-correctness seat

**Branch:** `for-fable-and-opus/swarm-72`
**Work dir:** `forge-combo29/swarm/72/`
**Engine under test:** Chess Engine Forge 5.31.0 (C++20), built with `g++ 13`,
`cmake -DCMAKE_BUILD_TYPE=Release`.
**Oracle:** python-chess 1.11.2.

## State: measurement harness complete, five of six questions answered

| # | Question | State |
|---|----------|-------|
| 1 | Repetition key contents (castling, ep) | DONE — all pass |
| 2 | Threshold 3 occurrences / 2 matches | DONE — correct |
| 3 | Fifty-move `halfmove >= 100`, resets | DONE — correct |
| 4 | Repetition × fifty-move interaction | DONE — 1 finding |
| 5 | Threefold inside the search tree | IN PROGRESS |
| 6 | Insufficient material | DONE — 1 claim refuted |

## Harness guards (all proven to fail before being trusted)

`tools/audit72/test_guards.py` — 5/5 pass:

- python-chess rejects a malformed FEN before it reaches the engine;
- the engine's `info string invalid FEN` is caught in the **position reply**;
- the same diagnostic is caught in the **go output** when `isready` is absent;
- a **stale-board trap**: after a refused FEN the perft-1 gate reports the
  *previous* board's move count, proving the silent-stale-board failure mode
  is real and that the gate catches it;
- known-good baseline: startpos perft-1 = 20.

Every fixture in every suite goes through this gate. Two fixtures were
rejected by it during development (a king-in-check placement and a
`side that moved left its king in check` FEN); both had been written by hand
from memory and would otherwise have silently measured the wrong board.

## Findings so far

1. **Castling rights are in the key.** Positions differing only in rights
   produce different keys (3/3 cases).
2. **En-passant is in the key, and only when a legal capture exists** —
   the FIDE-correct rule (9.2.2.1). Verified in three shapes: legal capture
   (keys differ), no capturer (keys match), pseudo-legal but pinned (keys
   match). This is the subtle case and the engine gets it right.
3. **Threshold is 3 occurrences.** Occurrences 1 and 2 score normally; 3, 4
   and 5 all bail at the root with score 0 and 5 nodes.
4. **Fifty-move triggers at `halfmove >= 100`.** 99 plays on, 100 and 101
   bail. Pawn moves and captures reset the clock to 0 and the reset is
   visible to the search (hm=99 with a pawn move scores +748 rather than 0).
5. **Insufficient material: the coordinator's two-knights claim is REFUTED.**
   See `RULES_TABLE.md`. KNN vs K is *not* a dead position under FIDE 5.2.2,
   because a legal checkmate exists with exactly that material — verified
   constructively, not by argument.

## Outstanding

- Q5 (in-tree repetition) needs a fixture whose half-point depends *only* on
  reaching a repetition. A solver (`select_fixture.py`) is running to select
  one by the criterion `rep_score == 0 and norep_score <= -300`, which is
  checkable by machine rather than by eye.

## Commands

```bash
cd forge-combo29/swarm/72
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++
cmake --build build -j4
python3 tools/audit72/test_guards.py     # must pass before trusting anything
python3 tools/audit72/t_repetition.py
python3 tools/audit72/t_threshold.py
python3 tools/audit72/t_material.py
```
