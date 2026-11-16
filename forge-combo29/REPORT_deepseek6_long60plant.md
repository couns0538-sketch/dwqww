# REPORT — deepseek6, the long-60 plant (a fake engine that plays an illegal move)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long60plant/`
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 1. What was asked, the answer, how sure

**Asked:** file 22, *"long 60: the fake-engine plant through `selfplay60.py` (file 20) is still owed."*

**Answer:** the plant is done and it **works, with a control that makes it mean something.**
A fake engine answering `bestmove e1e8` (illegal everywhere) is caught on **4 of 4 games** with
`reason ILLEGAL MOVE e1e8` and **0 plies played**; a fake engine answering a **legal** move is caught on **0 of 4**
and the games actually run (12–14 plies, ending by threefold). So long 60's "every move legal" claim is now backed
by a checker that is demonstrated to fire on an illegal move and to stay silent on a legal one.

**How sure:** certain — both runs are committed with their per-game records, and the driver is long 60's own
`selfplay60.py` with **one** change (the FEN path, see F2), stated below.

## 2. Honesty numbers

- Driver: **long 60's committed `selfplay60.py`**, taken unchanged from the branch except for the input path
  (`/tmp/o40.fens` → `/tmp/o40_plant.fens` so the plant runs 4 games instead of 40 — see F2).
- The two fakes: `fake_illegal_engine.py` (always `e1e8`) and `fake_legal_engine.py` (the first legal move in
  sorted order). Both are text, in this folder.
- No engine build is involved: the plant tests the **driver's** legality check, not the engine.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed, verified on origin | done | `CLAIM.txt` | 23:47:10Z |
| fake illegal engine written | done | `fake_illegal_engine.py` | answers `e1e8` to every `go` |
| plant run through long 60's driver | done | `out_plant/game_*.txt`, `plant_out.txt` | **4 of 4 ILLEGAL, 0 plies** |
| control: a fake legal engine | done | `out_control/game_*.txt`, `control_out.txt` | **0 of 4 flagged**, games played |

## 4. The two runs

**Plant (illegal engine):**

```
game 0: plies 0, reason ILLEGAL MOVE e1e8, san 0, exit 0
game 1: plies 0, reason ILLEGAL MOVE e1e8, san 0, exit 0
game 2: plies 0, reason ILLEGAL MOVE e1e8, san 0, exit 0
game 3: plies 0, reason ILLEGAL MOVE e1e8, san 0, exit 0
games 4; crashes 0; sanitizer lines 0; illegal 4
reasons: {'ILLEGAL MOVE e1e8': 4}
```

**Control (legal engine):**

```
game 0: plies 14, reason threefold, san 0, exit 0
game 1: plies 13, reason threefold, san 0, exit 0
game 2: plies 12, reason threefold, san 0, exit 0
game 3: plies 13, reason threefold, san 0, exit 0
games 4; crashes 0; sanitizer lines 0; illegal 0
reasons: {'threefold': 4}
```

## 5. Findings

**F1. The legality check fires, and only on illegal moves.** The driver's guard (`selfplay60.py:99`,
`if mv not in b.legal_moves`) catches the illegal fake **before pushing a single move** (0 plies on all four
games) and never touches the legal fake. A checker that fires on everything would have flagged the control; it did
not, so the 0-illegal result in long 60's report is a real measurement.

**F2. The one change I made to the driver, and why.** `selfplay60.py` reads its positions from the hardcoded path
`/tmp/o40.fens` and its options from `/tmp/ds6_work/.../s14.txt`. For the plant I pointed the FEN path at a
4-position file so the run takes a second instead of several minutes. **The legality code is untouched**, which is
the only part the plant exercises. Anyone repeating this needs the same two files present — the paths are a real
fragility of long 60's driver, worth noting beside the result it produced.

**F3. `e1e8` is the right probe because it is a well-formed move that is illegal from every position in O.** A
garbage string (`zzzz`) would have been caught by the earlier `chess.Move.from_uci` parse guard
(`UNPARSEABLE MOVE`), testing a different branch. The plant tests the branch that matters: a syntactically valid
move the position does not allow.

**F4. The control also proves the driver can play a full game with a trivial engine.** Threefold at 12–14 plies is
what you expect when both sides always play the alphabetically first legal move; it shows the loop, the ending
detection and the record writer all work independently of the real engine.

## 6. What I did NOT do

- **Did not re-run long 60's 40 real games.** That result stands on its own; this item owes the plant, not a redo.
- **Did not plant other failure modes** (`0000`, unparseable, no bestmove). The driver has guards for each and
  they are visible at lines 87–97; only the illegal-move branch was owed.
- Did not modify `selfplay60.py` in the repository — the copy with the changed path lives in `/tmp`.
- No pull request, no branch but mine, no engine source.

## 7. What I am NOT sure about

- Whether long 60's 40-game run would have caught an illegal move **from the real engine** at the same rate; the
  plant proves the check is wired, not that the engine never produces one. That is what long 60's 0-illegal result
  asserts, and it now has a working instrument behind it.
- The hardcoded `/tmp` paths (F2) mean long 60's run is not reproducible from the repository alone — the s14.txt
  and FEN file it reads are not committed in that folder. I sourced them from the branch for this plant.

## 8. The model

Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.
Times: `stamps.txt`.
