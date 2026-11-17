# REPORT job19 — the 20,000-mutation FEN sweep on the PC build under PC20

**What was asked.** Re-run my area's core measurement on the engine the owner's PC really
plays, under PC20, Threads 1, and say which build and settings each finding used.

**The answer.** **Identical to the base tree, case for case.** 18,775 refused, 1,225 accepted,
1,186 python-valid, 39 python-invalid, 0 crashes, 0 hangs, 0 sanitizer lines, 0 illegal
bestmoves. A `diff` of the per-FEN verdict column against job1's base-tree run is **empty** —
all 20,000 rows agree. The PC patch changes `src/board.cpp` but not the FEN acceptance
behaviour at all.

**How sure.** High. Same input file (`job1/mutations.tsv`, SEED 2101), same driver discipline,
ASan+UBSan PC build, every one of the 20 PC20 options verified accepted (`option_reject 0`),
Threads 1 throughout.

## Settings actually in force

```
Hash 16, Threads 1, then the 14 S14 settings, then
CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false
```
Each `setoption` followed by `isready`/`readyok` and checked for `unknown option` /
`invalid value` / `ERROR`: 0 rejections.

## Table (pasted from `job19/out/pc20_summary.txt`)

| measure | PC build under PC20 | base tree, default options (job1) |
|---|---|---|
| total FENs | 20,000 | 20,000 |
| refused | 18,775 | 18,775 |
| accepted | 1,225 | 1,225 |
| accepted & python-valid | 1,186 | 1,186 |
| accepted & python-INVALID | 39 | 39 |
| crashes / hangs | 0 / 0 | 0 / 0 |
| sanitizer lines | 0 | 0 |
| illegal bestmoves | 0 | 0 |
| per-FEN verdict differences | **0** | – |

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 refused/accepted split identical to base | **held exactly** (0 row differences) |
| P2 0 crash / hang / sanitizer | held |
| P3 0 illegal bestmoves | held |
| P4 same 39 invalid rows | held |
| P5 `fullmove 0` still refused | held (21-F8 confirmed separately in job18) |
| P6 pins hold on this binary | held (see `pins_*.txt` in job17: default row is the pin regime) |

## Findings

`21-F10b | CONFIRMS 21-F10 on the PC build` — the parser's behaviour on 20,000 mutated FENs is
byte-for-byte the base tree's, on the PC build under PC20 with Threads 1. This also strengthens
21-F8: the PC build still refuses `fullmove 0` (it was refused 39-ways in this sweep as well).

## Suspicions, not proven

- The patch touches `src/board.cpp`, which contains `set_fen`, yet acceptance is unchanged. That
  is a good sign (the patch's board.cpp changes are elsewhere), but I did not read the board.cpp
  hunk line by line to say which functions it touches.

## What I did NOT do

- Did not run the sweep on the Release PC build (ASan+UBSan only). Node counts do not matter
  here; acceptance and crashes do, and a sanitizer build is the stricter instrument.
- Did not extend to a wider mutation alphabet.

## What I am NOT sure about

- Whether the PC's own trained net would change any accepted-invalid case. My area's assertions
  are about parsing and bestmove legality, which the net does not touch, so this is unlikely —
  but I did not test with a net file, and the PC's net is not shared.

## Times

see `job19/stamps.txt`.
