# Opus Provenance & Composition Packet — `SF37` (`SF37_tm_combined_SF17_plus_SF18.exe`)

> **PROVENANCE DISCLOSURE (ZERO FABRICATION):**
> - **NO standalone `SF37*.patch` exists on disk** (`C:\nnue-lab\neon\forge_fixes\patches\` has zero `*SF37*` files).
> - **NO standalone `gate_SF37*` / `SF37*_gate.json`, `build_sf37*`, or `SF37` `fastchess` match exists on disk.**
> - `SF37` exists **solely** as `builds\SF37_tm_combined_SF17_plus_SF18.exe` (`mtime 2026-11-28T05:52:46Z`, `8s` after `run_clock_tm_screen.py`), compiled as the union of **`SF17_tm_bestmove_avg_eval.patch` + `SF18_tm_ply_curve.patch`** and queued in `run_clock_tm_screen.py:66-70`. **Status: UNSCREENED / HOLD FOR GPU-IDLE `6+0.06` CLOCK SCREEN (`CLOCK_MATCH_RUNNING` REQUIRED).**

---

## MANDATORY PRIOR RESULT DISCLOSURE (Opus Point 4 — `packet_SF17_SF18_tm.md:7-12`)

> **Explicit Prior Result Disclosure (`Task 2D S7`):**
> In `Task 2D` (`S7_tm_asp_safe_clock_6p006`, `400g @ 6+0.06`, `r0067 + FULL`, GPU idle), bundling `TmNodeShare=true + TmFinishIteration=true + AspCappedReopen=true + AspArmLate=true` against default `false` scored **`-32.2 [-49.0, -15.6]` Elo** (recounted by Opus from raw PGN/config: **`-32.23 [-49.02, -15.59]` Elo**, `z = -3.80`).
> - `SF17_tm_bestmove_avg_eval` and `SF18_tm_ply_curve` (and therefore `SF37 = SF17 + SF18`) are **separate C++ time-management changes** that do **not** enable `TmNodeShare`, `TmFinishIteration`, `AspCappedReopen`, or `AspArmLate` (all remain `false` by default).
> - Per `OPUS-2711-G2-CHECKED`, any `6+0.06` / `10+0.1` screen or declaration of `SF17`, `SF18`, or `SF37` **must explicitly cite this `-32.2 [-49.0, -15.6]` prior result** and run ONLY when the GPU is 100% idle with `C:\nnue-lab\neon\CLOCK_MATCH_RUNNING` active.

---

## 1. Live Artifact Inventory & Hashes

| Role | Path | Bytes | Lines | Live SHA-256 |
|---|---|---:|---:|---|
| Combined Exe | `C:\nnue-lab\neon\forge_fixes\builds\SF37_tm_combined_SF17_plus_SF18.exe` | 2,383,360 | — | `f7c9c47b3e9228b9a1f83058428c50a783614bc327da2f78792c4e69275583f9` |
| `SF17` Patch | `C:\nnue-lab\neon\forge_fixes\patches\SF17_tm_bestmove_avg_eval.patch` | 3,434 | 68 | `d7aaf51cde99336b021a87f38bab7b119a702f5cb96cd036d8bedd8ccfb7b88c` |
| `SF17` Exe | `C:\nnue-lab\neon\forge_fixes\builds\SF17_tm_bestmove_avg_eval.exe` | 2,383,360 | — | `2ce7817d36721187922e4ee122ed35c7fc41776fc770f368bae63503664330c5` |
| `SF17` Gate | `C:\nnue-lab\neon\forge_fixes\builds\SF17_tm_bestmove_avg_eval_gate.json` | 8,847 | 275 | `fdb17e0140d7cedeb370ea71eeddb0b7233cb0ed4ae4395bbed0b23a17cbc0ac` |
| `SF18` Patch | `C:\nnue-lab\neon\forge_fixes\patches\SF18_tm_ply_curve.patch` | 1,712 | 34 | `4b87a33856f12c14336323e102fbb62ea42ef2497873065c1f4b86cfe4f2f041` |
| `SF18` Exe | `C:\nnue-lab\neon\forge_fixes\builds\SF18_tm_ply_curve.exe` | 2,382,848 | — | `ef0e31382c6c21e5a8d6c9f770afad66f9afc484ae3c2e8a2663ff0f30301c5c` |
| `SF18` Gate | `C:\nnue-lab\neon\forge_fixes\builds\SF18_tm_ply_curve_gate.json` | 8,838 | 275 | `d5b2dfa3d81cb36476071156269ee1a6998e692a6376bd42ff28e1428fe3ed2c` |
| Clock Runner | `C:\nnue-lab\neon\forge_fixes\run_clock_tm_screen.py` | 3,672 | 88 | `41de9478a9de6cea091161e69f108398e99b2a8f2b1367c1db2b54d0def2150f` |
| Target Source | `C:\nnue-lab\forge\r15dsg\src\search.cpp` | 167,417 | 3,426 | `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` |

`run_clock_tm_screen.py:66-70` queues `SF37` as item 3 of 5:
```python
run_clock(
    f"CLK_SF37_tm_combined_{args.games}g", str(FIX / "builds/SF37_tm_combined_SF17_plus_SF18.exe"),
    args.games, args.tc, args.concurrency, 202611605,
    "Clean-room combined TM (SF17 decaying instability+avg eval + SF18 ply-adaptive sudden-death curve)",
)
```

---

## 2. Verbatim Constituent Patch Diffs (`SF17` + `SF18`)

### 2.1 `SF17_tm_bestmove_avg_eval.patch` (`68` lines, `4` hunks in `src/search.cpp`)

- **Enclosing methods:** `Worker::search(Board, const SearchLimits&, ...)` (`src/search.cpp:2623-3251`, hunks at `2931, 3142, 3163, 3177`).
- **Behavior:** Tracks decaying best-move instability `tot_best_changes` (`*= 0.5`, `+1.0` when `depth >= 4 && !previous_best.is_none() && result.best_move != previous_best`) and running average root score `avg_score = (avg_score == ValueNone) ? score : (2 * score + avg_score) / 3` (non-mate scores), using `max(1-ply drop, avg_score - score)` capped at `150` cp inside `if (time_managed_ && ...)`. Fixed-depth/fixed-node search is 100% untouched.

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2931,6 +2931,9 @@
     int stable_iterations = 0;
     int score = 0;
     int previous_score = ValueNone;
+    // Clean-room Stockfish/Viridithas TM: decaying best-move instability & running avg score.
+    double tot_best_changes = 0.0;
+    int avg_score = ValueNone;
     // AspArmLate: a finished root iteration that failed high or low at least
     // once makes the following iteration use a full window.
     bool reopen_full_window = false;
@@ -3142,11 +3145,18 @@
             emit(depth, score, result.pv);
         }
 
+        tot_best_changes *= 0.5;
         if (result.best_move == previous_best) ++stable_iterations;
-        else stable_iterations = 0;
+        else {
+            stable_iterations = 0;
+            if (depth >= 4 && !previous_best.is_none()) tot_best_changes += 1.0;
+        }
         previous_best = result.best_move;
         const int iteration_previous_score = previous_score;
         previous_score = score;
+        if (!is_mate_score(score)) {
+            avg_score = (avg_score == ValueNone) ? score : (2 * score + avg_score) / 3;
+        }
 
         if (mate_moves > 0 && score >= mate_in(mate_moves * 2 - 1)) break;
         // The iteration above is finished. Passing the soft budget stops here,
@@ -3163,7 +3173,10 @@
             double factor = 1.0;
             if (stable_iterations >= 6) factor = tune::TmStableFactor / 100.0;
             else if (stable_iterations >= 3) factor = tune::TmSemiStableFactor / 100.0;
-            else if (stable_iterations == 0 && depth >= 6) factor = tune::TmUnstableFactor / 100.0;
+            else if (depth >= 6) {
+                const double instab = 1.0 + 0.45 * std::min(tot_best_changes, 2.5);
+                factor = std::max(instab, stable_iterations == 0 ? tune::TmUnstableFactor / 100.0 : 1.0);
+            }
             // A best move that absorbed most of the effort is clearly best;
             // spend longer when the alternatives still draw attention.
             if (local_nodes_ > 0 && depth >= 6) {
@@ -3177,10 +3190,19 @@
                     factor *= effort_share_factor(effort, tune::TmEffortBase, tune::TmNodeShare);
                 }
             }
-            // A falling evaluation deserves more thought.
-            if (iteration_previous_score != ValueNone && !is_mate_score(score) && score < iteration_previous_score) {
-                const int drop = std::min(iteration_previous_score - score, 150);
-                factor *= 1.0 + drop * tune::TmFallingEvalPercent / 10000.0;
+            // A falling evaluation (either 1-ply or vs running average) deserves more thought.
+            if (!is_mate_score(score)) {
+                int drop = 0;
+                if (iteration_previous_score != ValueNone && score < iteration_previous_score) {
+                    drop = std::max(drop, iteration_previous_score - score);
+                }
+                if (avg_score != ValueNone && score < avg_score) {
+                    drop = std::max(drop, avg_score - score);
+                }
+                if (drop > 0) {
+                    drop = std::min(drop, 150);
+                    factor *= 1.0 + drop * tune::TmFallingEvalPercent / 10000.0;
+                }
             }
             factor = std::max(factor, tune::TmMinFactorPercent / 100.0);
             // TmNodeShare is clock play only: this block is skipped for depth,
```

### 2.2 `SF18_tm_ply_curve.patch` (`34` lines, `2` hunks in `src/search.cpp`)

- **Enclosing functions:** anonymous `clock_plan_for(const SearchLimits&, int fullmove = 0)` (`src/search.cpp:2593-2597`) and `Worker::search(...)` (`2680`).
- **Behavior:** For sudden-death games (`fullmove > 0 && limits.moves_to_go <= 0`), shifts `TmSoftDivisor` by `+4` (`fullmove <= 8`), ramps `+4 -> -4` (`9..13`), `-4` (`14..32`), ramps `-4 -> 0` (`33..43`), `0` (`>= 44`), clamped `[8, 80]`.

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2590,9 +2590,20 @@
 
 namespace {
 
-[[nodiscard]] ClockPlan clock_plan_for(const SearchLimits& limits) {
+[[nodiscard]] ClockPlan clock_plan_for(const SearchLimits& limits, int fullmove = 0) {
     const std::int64_t overhead = std::max<std::int64_t>(0, limits.move_overhead_ms);
-    return plan_clock_budget(limits.time_ms, limits.increment_ms, limits.moves_to_go, overhead, tune::TmSoftDivisor,
+    // Clean-room Stockfish/Stormphrax ply-adaptive sudden-death budget curve:
+    // conserve time in early opening, invest ~15% more in critical middlegame (moves 14..32).
+    int eff_divisor = tune::TmSoftDivisor;
+    if (fullmove > 0 && limits.moves_to_go <= 0) {
+        int shift = 0;
+        if (fullmove <= 8) shift = 4;
+        else if (fullmove < 14) shift = 4 - (fullmove - 8) * 8 / 6;
+        else if (fullmove <= 32) shift = -4;
+        else if (fullmove < 44) shift = -4 + (fullmove - 32) * 4 / 12;
+        eff_divisor = std::clamp(eff_divisor + shift, 8, 80);
+    }
+    return plan_clock_budget(limits.time_ms, limits.increment_ms, limits.moves_to_go, overhead, eff_divisor,
                              tune::TmIncrementPercent, tune::TmHardPercent, tune::TmHardSoftMultiple);
 }
 
@@ -2677,7 +2688,7 @@
         hard_limit_ms_ = std::max<std::int64_t>(1, limits.movetime_ms - overhead);
         soft_limit_ms_ = hard_limit_ms_;
     } else if (limits.time_ms >= 0) {
-        const ClockPlan plan = clock_plan_for(limits);
+        const ClockPlan plan = clock_plan_for(limits, board.fullmove_number());
         soft_limit_ms_ = plan.soft_ms;
         hard_limit_ms_ = plan.hard_ms;
         clock_reserve_empty_ = plan.reserve_empty;
```

---

## 3. Constituent Gate Results & Match Status (`ZERO` Matches Run)

- **`SF17_tm_bestmove_avg_eval_gate.json` (`quick`, `r0067`):** `hard_pass = true`, `perft 5 = 4,865,609` (`6/6`), `v3_parity = 120/120` (`0 cp`), `loader = 13/13`, **4/4 bit-identical** fixed-depth bench vs `base_r15dsg.exe` (`default_11=259,695`, `default_13=725,158`, `b4_11=187,930`, `b4_13=632,195`; `delta=0` on all 4).
- **`SF18_tm_ply_curve_gate.json` (`quick`, `r0067`):** `hard_pass = true`, `perft 5 = 4,865,609` (`6/6`), `v3_parity = 120/120` (`0 cp`), `loader = 13/13`, **4/4 bit-identical** fixed-depth bench vs `base_r15dsg.exe` (`delta=0` on all 4).
- **Unit & Clock-Allocation Suite (`packet_SF17_SF18_tm.md`, `test_sf17_sf18_tm.py`):** `3/3` PASS on `SF17`/`SF18` (`RC=0`), failing `2/3` on `base_r15dsg.exe` (`RC=1`).
- **`SF37_tm_combined_SF17_plus_SF18.exe`:** Has **no** standalone `gate_SF37*.json` on disk.
- **Elo Status:** **ZERO `fastchess` Elo matches** (`ALL_MATCHES_SCOREBOARD.md` / `matches/` contain zero `CLK_*` or `SF37` runs). Requires GPU-idle `6+0.06` (`run_clock_tm_screen.py` with `CLOCK_MATCH_RUNNING`) and `10+0.1` (`400g+`, LCB `> -10`) before any placement.

---

## 4. Overlap & Orthogonality Matrix (`round12_14_orthogonality.json`)

- **vs `V3P_pairwise_psqt_fused_v3.patch` (`sha256=57f3455f...`):** **100% file-disjoint** (`SF17` and `SF18` touch ONLY `src/search.cpp`).
- **`SF17` vs `SF18`:** Line-disjoint in `src/search.cpp` (`min_line_gap = 248` lines).
- **Combined stack (`V3P -> SF17 -> SF18 -> SF34 -> SF35 -> SF36 -> SF38 -> SF40`):** Verified `RC=0` across all 8 steps on an isolated temp copy of `forge/r15dsg` (`stack_sf38_with_tm` in `round12_14_orthogonality.json`).
