# STATUS — swarm/72 rules-correctness seat

**Branch:** `for-fable-and-opus/swarm-72` (pushed; 26-row table in `RULES_TABLE.md`)
**Work dir:** `forge-combo29/swarm/72/`
**Engine:** Chess Engine Forge 5.31.0 (C++20), g++ 13, `-O2`, Release.
**Oracle:** python-chess 1.11.2.

## State: all six questions answered

| # | Question | State | Rows |
|---|----------|-------|------|
| 1 | Position key contents (castling, ep) | DONE — correct | 1–3 |
| 2 | Threshold 3 occurrences / 2 matches | DONE — correct | 4–6, 14 |
| 3 | Fifty-move `halfmove >= 100`, resets | DONE — correct | 7–13 |
| 4 | Repetition × fifty-move interaction | DONE — **1 defect** | 26 |
| 5 | Threefold inside the search tree | DONE — fires; not decisive on fixtures | 15–16 |
| 6 | Insufficient material | DONE — all 9 sets agree | 17–25 |

**RULES_TABLE.md row count: 26.**

## Two answers that changed from my first draft

**The coordinator's two-knights claim is refuted.** KNN vs K is *not* a dead
position under FIDE 5.2.2, because a legal checkmate exists with that exact
material: `8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1` is valid and is checkmate. The
`knights == 0` condition at `board.cpp:864` is therefore correct, not a bug.
All nine material sets were checked the same way — by searching for a legal
mate witness rather than by reasoning — and the engine agrees with FIDE on
every one.

**One real defect, in the opposite direction.** The root bail at
`search.cpp:493-500` returns 0 before generating any move, so a *waivable*
draw claim suppresses a deliverable mate:

| position | engine |
|---|---|
| mate-in-1 at halfmove 99 | `mate 1`, plays `a1a8` |
| mate-in-1 at halfmove 100 | `cp 0`, plays `a1a2` |
| threefold root with mate-in-1 | `cp 0`, plays `a1a2` |

FIDE 9.2/9.3 are claims belonging to the mover, and 5.1.1 ends the game at
mate. python-chess agrees these boards are not terminal (`outcome() == None`)
while `can_claim_fifty_moves()` is `True`. The engine treats a waivable claim
as an automatic draw — the same modelling error in both places.

## Verified correct (no action needed)

- **Castling rights are in the key** — 3/3 differing-rights pairs produce
  different keys.
- **En-passant is in the key, and only when legally exercisable** — the
  FIDE-correct rule. Three shapes tested: legal capture (keys differ), no
  capturer (keys match), pseudo-legal but pinned (keys match). The pinned case
  is handled by replaying the capture with the removed pawn excluded from
  occupancy before the attack test.
- **Threshold** — occ 1 and 2 search normally (`cp+575`); occ 3, 4, 5 bail at
  the root (`cp 0`, 5 nodes).
- **Fifty-move** — 99 plays on, 100 and 101 bail; pawn moves and captures
  reset to 0; quiet moves increment; a reset available at hm 99 is visible to
  the search (`cp+748` rather than 0).
- **In-tree repetition detection executes** — instrumented counter shows 8
  hits at depth 6 and 158 at depth 10 below the root. Disabling it does not
  change any tested score, so I report "no measurable effect on these
  fixtures" rather than claiming a defect; the mechanism is documented in
  limitation L2.

## Fixture integrity

Every fixture passes: python-chess validation → both reply streams scanned for
`invalid FEN` → `go perft 1` count *and* move set equal to python-chess.
`test_guards.py` proves each gate can fail (5/5), including a stale-board trap
showing that a refused FEN leaves the previous board loaded and silently
measurable.

Two hand-written fixtures were caught by these gates during development —
`side that moved left its king in check`, and `inconsistent en-passant
square`. Both would otherwise have produced wrong numbers.

One verifier bug of mine is recorded in `verify_perpetual.py`: an early
version accepted a line where the "checking" move actually won a piece, which
is not a perpetual at all. The corrected version requires constant material
balance, so a fixture cannot be mistaken for a draw by repetition.

## Deliverables

- `forge-combo29/swarm/72/FINDINGS.md`
- `forge-combo29/swarm/72/RULES_TABLE.md` — **26 rows**
- `forge-combo29/swarm/72/STATUS.md` (this file)
- `forge-combo29/swarm/72/tools/audit72/` — harness, 6 suites, 2 C++ probes

## Reproduce

```bash
cd forge-combo29/swarm/72
CXX=/usr/bin/g++ cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j4
g++ -std=c++20 -O2 -Iinclude tools/audit72/probe.cpp src/board.cpp -o build/probe
python3 tools/audit72/test_guards.py      # gates must pass first
python3 tools/audit72/t_repetition.py
python3 tools/audit72/t_threshold.py
python3 tools/audit72/t_material.py
python3 tools/audit72/t_material_fide.py  # 9 sets, exhaustive witnesses (~70s)
python3 tools/audit72/t_intree.py
python3 tools/audit72/t_diffscan.py
```
