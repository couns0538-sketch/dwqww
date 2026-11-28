# Opus Placement Packet: `SF32_qs_see1_futility_pruning` (Stockfish QS SEE<=0 Futility Pruning)

> **Status:** Clean-room Stockfish method, built, Master-Gated (`hard_pass=True`, `git apply --check RC=0`), queued for 600g @ 50k screen (`SF32_qs_see1_futility_pruning_600g_50k`) + combined QS overhaul screen (`SF33_qs_overhaul_SF13_plus_SF32_600g_50k`).
> **Patch:** `C:\nnue-lab\neon\forge_fixes\patches\SF32_qs_see1_futility_pruning.patch`
> **Target File:** `src/search.cpp` (`Worker::qsearch()`, 7 lines inserted)
> **Source Citation:** Clean-room re-implementation of Stockfish `src/search.cpp` `qsearch()` futility pruning (`futilityBase <= alpha && !pos.see_ge(move, 1)` -> `bestValue = std::max(bestValue, futilityBase); continue;`), zero verbatim GPL code copied.

---

## 1. Exact Mechanism & Why Forge Was Missing It

In live `forge/r15dsg/src/search.cpp` lines 1850–1858 (`Worker::qsearch`):
```cpp
if (mate_moves_ == 0 && !in_check && best_score > -MateInMaxPly) {
    const bool gives_check = board.gives_check(move);
    if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
        best_score = std::max(best_score, futility_base + capture_value(board, move));
        continue;
    }
    if (!board.see_ge(move, -tune::QsSeeMargin)) continue;
}
```
- **Defect:** When `futility_base <= alpha` (`static_eval + QsFutilityMargin <= alpha`), Forge ONLY skipped captures where `futility_base + capture_value(victim) <= alpha`. Consequently, whenever the side to move was down material (e.g. down a Rook: `static_eval = -500`, `alpha = -100`, `futility_base = -377`) and had a **defended equal Queen or Rook trade** (`Qxd8`, `Rxd8`, `SEE == 0`), `futility_base + capture_value(Q) = +523 > -100` bypassed futility pruning and expanded the entire equal-exchange quiescence subtree!
- **Fix (`SF32`):** Before checking `capture_value`, if `!gives_check && !move.is_promotion() && !is_mate_score(alpha) && futility_base <= alpha && !board.see_ge(move, 1)` (capture does NOT win net material via SEE), raise `best_score = std::max(best_score, futility_base)` (fail-soft safe) and prune immediately!

## 2. Soundness & Mate-Safety Audit
- Guarded by `mate_moves_ == 0`, `!in_check`, `best_score > -MateInMaxPly`, `!is_mate_score(alpha)`, `!gives_check`, and `!move.is_promotion()`.
- Never prunes checking captures, promotions, mate searches, check evasions, or any capture with `SEE >= 1`.
- Fail-soft safe (`best_score = std::max(best_score, futility_base)` guarantees returned upper bound is never below `futility_base`).

## 3. Verification Commands & Gates
- `git -C C:\nnue-lab\forge\r15dsg apply --check C:\nnue-lab\neon\forge_fixes\patches\SF32_qs_see1_futility_pruning.patch` -> `RC=0`
- `run_master_gates.py --quick` (`builds/SF32_qs_see1_futility_pruning_gate.json`): `hard_pass = True`, `perft 5 = 4,865,609`, `B4 bench 13 = 831,528` (`+31.53%` tree shape change).
- Fail-before / pass-after behavioral test: `C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\test_sf32_qs_see1_futility.py`.
- Playing strength decided strictly by declared `fastchess` matches (`SF32_qs_see1_futility_pruning_600g_50k` + independent 1,000g confirmation if positive).
