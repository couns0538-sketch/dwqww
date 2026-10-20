# Forge 6.4 bug investigator — 2026-10-20 14:00 CEST

**Priority:** P2 candidate; source-grounded quiescence terminal-score regression, native run pending.
**Source branch:** `forge/6.4-hourly-20261019`
**Pinned source commit:** `356e863dbd86d2ce24b8ee9486d7406f1d525480`
**Status:** Geometry oracle PASS; UCI probe exercised against corrected/incorrect mocks; **no native Forge execution** (local Git DNS unavailable). No source modifications or merge.

## Suspected defect and minimal reproduction
In `src/search.cpp` lines 671–766, `Worker::qsearch`:
* Returns 0 for repetition/rule-50/insufficient material (line 680), but **does not check stalemate**.
* With no check, sets `best_score` to static evaluation and can stand-pat / fail high (lines 704–720).
* The quiescence move picker considers tactical moves, not all legal quiet moves; a quiet stalemate can therefore be returned as nonzero material evaluation.

Execute in a fresh native Forge process with `Threads=1`, `OwnBook=false`, `UseNNUE=false`, `Clear Hash`:

```uci
uci
setoption name OwnBook value false
setoption name UseNNUE value false
setoption name Threads value 1
setoption name Clear Hash
isready
position fen 7k/5K2/8/6Q1/8/8/8/8 w - - 0 1
go depth 1 searchmoves g5g6
```

After the forced legal quiet move `g5g6`, Black has no legal king moves, is not in check and has neither captures nor pawn moves. This is **stalemate**, so the depth-1 result must have `score cp 0` with `bestmove g5g6`. Source predicts a nonzero queen-advantage score, but the actual Forge output has **not** been collected.

An independent standard-library fixture oracle confirmed: before Qg6 Black can play `h8h7`; afterward Black has zero legal moves and is not in check. The attached investigation's Python UCI probe discriminated mock 0cp (PASS) vs mock +987cp (FAIL). This mock test is **not** native defect reproduction.

## Context / nonduplication
Earlier Forge versions explicitly repaired this class in `CHANGELOG.md` under 0.1.2, 0.4.0, and 5.22.0; the 6.4 implementation no longer exhibits a quiet stalemate probe in qsearch. This is **not** the previously reported terminal-root `go nodes 0` issue, TT rule-50 score reuse or synthetic null-move rule-50 issue. No existing GitHub issue titled stalemate was found.

## Next actions for pipeline
* **14:15 researcher:** compare historical quiet-stalemate guards against the 6.4 qsearch and design a narrow, performance-conscious fix. Avoid unconditional legal-move generation at every qsearch node until performance quantified.
* **14:30 tester:** run the exact UCI probe; save complete raw stdout/stderr, executable hash, options, commit, and exit status; test direct qsearch favorable-stalemate `5k1K/7P/8/8/8/8/8/8 w - - 0 1` as auxiliary fixture.
* **14:45 developer:** only if reproduced, add an isolated fix and regression tests, run CTest/perft/UCI and speed evaluation, and separately gate any strength claim with fastchess SPRT.

**GitHub policy:** This is a report on an isolated investigator branch. Do not merge/modify `forge/6.4-hourly-20261019`. No native PASS or Elo claim.
