# Opus Placement Packet: `SF15_rfp_failsoft_blend` (1-Line Stockfish RFP Fail-Soft Blend)

> **Status:** Built, Master-Gated (`hard_pass=True`, `git apply --check RC=0`), screened **`+7.53 [-8.65, +23.74] Elo` (`151-311-138`, `LOS 81.92%`, 600g @ 50k)**, queued #3 for independent unbiased fresh-seed 1,000g @ 50k confirmation (`SF15_confirm_vs_base_1000g_50k`, seed `202611498`, never pooled!).
> **Patch:** `C:\nnue-lab\neon\forge_fixes\patches\SF15_rfp_failsoft_blend.patch` (`11` lines total; **1 line changed**)
> **Target File:** `src/search.cpp:2091` (`Worker::search()` Reverse Futility Pruning return)
> **Source Citation:** Clean-room re-implementation of Stockfish / Stormphrax / Viridithas fail-soft RFP return `(eval + beta) / 2` (Stockfish `src/search.cpp`, Razoring/RFP fail-soft damping), zero verbatim GPL code copied.

---

## 1. Exact 1-Line Diff
```diff
-            return eval;
+            return (eval + beta) / 2;
```
- **Mechanism:** When Reverse Futility Pruning (`eval - margin >= beta`) cuts off, returning raw `eval` can return an inflated static overestimate far above `beta` into the parent's fail-soft `best_score` and TT lower bound (distorting parent aspiration/fail-soft bounds). Blending `(eval + beta) / 2` stays strictly `>= beta` (since `eval >= beta + margin >= beta` and `margin >= 0`) while damping static-eval overshoot!
- **Overflow & Mate Safety:**
  - `eval < MateInMaxPly` AND `!is_mate_score(beta)` AND `mate_moves_ == 0` are ALREADY enforced on lines 2074 & 2090!
  - `|eval| < 30,000` and `|beta| < 30,000` -> `|eval + beta| < 60,000 << INT_MAX` (zero int32 overflow possible).
  - Since `eval >= beta`, `(eval + beta) / 2 >= beta` holds whenever `eval + beta >= 2 * beta` (note: C++ truncates toward zero for negative odd sums, e.g. if `eval = -100, beta = -101`, `(-201)/2 = -100 >= -101` — in fact for negative sums truncation toward zero rounds UP, so `(eval + beta) / 2 >= beta` ALWAYS holds for ALL integers `eval >= beta`! Proof: let `eval = beta + d` with `d >= 0`; if `2*beta + d >= 0`, `(2*beta+d)/2 = beta + floor(d/2) >= beta`; if `2*beta + d < 0`, trunc-toward-zero `= ceil((2*beta+d)/2) = beta + ceil(d/2) >= beta`. QED!).

## 2. Verification & Gates
- `git -C C:\nnue-lab\forge\r15dsg apply --check C:\nnue-lab\neon\forge_fixes\patches\SF15_rfp_failsoft_blend.patch` -> `RC=0`.
- `builds/SF15_rfp_failsoft_blend_gate.json`: `hard_pass = True`, `perft 5 = 4,865,609`.
- Fail-before / pass-after test: `C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\test_sf15_and_sf27.py --only sf15`.
- Playing strength decided strictly by independent 1,000g confirmation (`SF15_confirm_vs_base_1000g_50k`) + equal-time confirmation if stacked.
