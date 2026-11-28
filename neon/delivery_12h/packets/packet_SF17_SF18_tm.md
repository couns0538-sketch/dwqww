# Opus Review Packet: `SF17_tm_bestmove_avg_eval` & `SF18_tm_ply_curve`

**Recommendation:** **HOLD FOR GPU-IDLE `6+0.06` CLOCK SCREEN (`CLOCK_MATCH_RUNNING` REQUIRED)** — Both time-management patches are clean-room (`git apply --check RC=0`), pass all deterministic gates (`perft 5 = 4,865,609`, `v3_parity 0 differ` across `8/8` KB & `8/8` OB on `r0067`), are **4/4 bit-identical** on fixed-depth `bench 11` and `bench 13` (Default, `B4+r0067`, and `FULL`), and demonstrate distinct clock-allocation behavior in `test_sf17_sf18_tm.py`. Neither has completed its GPU-idle `6+0.06` clock match yet (`run_clock_tm_screen.py` is queued for GPU-idle window).

---

## MANDATORY PRIOR RESULT DISCLOSURE (Opus Point 4 — `OPUS-2711-G2-CHECKED`)

> **Explicit Prior Result Disclosure (`Task 2D S7`):**
> In `Task 2D` (`S7_tm_asp_safe_clock_6p006`, `400g @ 6+0.06`, `r0067 + FULL`, GPU idle), bundling **`TmNodeShare=true` + `TmFinishIteration=true` + `AspCappedReopen=true` + `AspArmLate=true`** against default `false` scored **`-32.2 [-49.0, -15.6]` Elo** (recounted by Opus from raw PGN/config: **`-32.23 [-49.02, -15.59]` Elo**, `z = -3.80`).
> - `SF17_tm_bestmove_avg_eval` and `SF18_tm_ply_curve` are **separate C++ time-management improvements** that do **not** enable `TmNodeShare`, `TmFinishIteration`, `AspCappedReopen`, or `AspArmLate` (all remain `false` by default).
> - Because `Task 2D S7` showed `-32.2 Elo` on clock-TM changes, any `6+0.06` / `10+0.1` screen or declaration of `SF17`, `SF18`, `TmNodeShare`, or `TmFinishIteration` **must explicitly cite this `-32.2 [-49.0, -15.6]` prior result** and be tested only when the GPU is 100% idle with `neon\CLOCK_MATCH_RUNNING` active.

---

## 1. Artifacts & Hashes

- **`SF17_tm_bestmove_avg_eval`:**
  - Patch: `C:\nnue-lab\neon\forge_fixes\patches\SF17_tm_bestmove_avg_eval.patch` (`68` lines, `git apply --check RC=0`)
  - Exe: `C:\nnue-lab\neon\forge_fixes\builds\SF17_tm_bestmove_avg_eval.exe` (`2,383,360` B, `SHA-256: 2CE7817D36721187922E4EE122ED35C7FC41776FC770F368BAE63503664330C5`)
  - Gate JSON: `C:\nnue-lab\neon\forge_fixes\builds\SF17_tm_bestmove_avg_eval_gate.json` (`hard_pass: true`)
- **`SF18_tm_ply_curve`:**
  - Patch: `C:\nnue-lab\neon\forge_fixes\patches\SF18_tm_ply_curve.patch` (`34` lines, `git apply --check RC=0`)
  - Exe: `C:\nnue-lab\neon\forge_fixes\builds\SF18_tm_ply_curve.exe` (`2,382,848` B, `SHA-256: EF0E31382C6C21E5A8D6C9F770AFAD66F9AFC484AE3C2E8A2663FF0F30301C5C`)
  - Gate JSON: `C:\nnue-lab\neon\forge_fixes\builds\SF18_tm_ply_curve_gate.json` (`hard_pass: true`)
- **Test Suite:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave3\streamA_search_packets\tests\test_sf17_sf18_tm.py`

---

## 2. Verbatim Patch Diffs & Mechanisms

### 2.1 `SF17_tm_bestmove_avg_eval.patch` (Clean-Room Stockfish `timeman.cpp` / Viridithas `timemgmt.rs`)

- **Mechanism (`src/search.cpp:2931-2936, 3145-3195`):**
  1. Tracks exponentially decaying best-move instability (`tot_best_changes *= 0.5; if (depth >= 4 && !previous_best.is_none() && result.best_move != previous_best) tot_best_changes += 1.0;`).
  2. When `depth >= 6` and `stable_iterations < 3`, computes `instab = 1.0 + 0.45 * std::min(tot_best_changes, 2.5)` and takes `std::max(instab, stable_iterations == 0 ? TmUnstableFactor / 100.0 : 1.0)`, preserving unstable-position thought even for 1–2 iterations after a best-move flip.
  3. Tracks running average root score `avg_score = (avg_score == ValueNone) ? score : (2 * score + avg_score) / 3` (excluding mate scores) and uses `max(1-ply drop, avg_score - score)` capped at `150` cp so gradual multi-ply score slides extend soft time.
  4. Strictly inside `if (time_managed_ && ...)` (`search.cpp:3156`), so fixed-depth/fixed-node search is 100% untouched.

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

### 2.2 `SF18_tm_ply_curve.patch` (Clean-Room Stockfish `timeman.cpp` / Stormphrax `time.cpp`)

- **Mechanism (`src/search.cpp:2593-2597, 2680`):**
  1. Passes `board.fullmove_number()` into `clock_plan_for(limits, fullmove)` for sudden-death games (`fullmove > 0 && limits.moves_to_go <= 0`).
  2. Applies a piecewise-linear divisor shift: `+4` for `fullmove <= 8` (conserve early opening time), linear ramp `+4 -> -4` across `9..13`, `-4` for `14..32` (invest ~15–22% more soft time in critical middlegames), linear ramp `-4 -> 0` across `33..43`, and `0` for `fullmove >= 44`. Clamps `eff_divisor` to `[8, 80]` before calling `plan_clock_budget` (preserving `1 <= soft <= hard <= available`).
  3. Notice `clock_plan_for(worker_limits)` at `search.cpp:3301` uses the default `fullmove = 0` (`shift = 0`, checking only `reserve_empty`, which depends solely on `time_ms <= overhead`).

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

## 3. Fixed-Depth Bit-Identity & Clock-Allocation Verification

### 3.1 Fixed-Depth 4/4 `bench 11/13` Bit-Identity Table

| Check | `base_r15dsg.exe` | `SF17_tm_bestmove_avg_eval.exe` | `SF18_tm_ply_curve.exe` | Status |
|---|---:|---:|---:|---|
| `go perft 5` | `4,865,609` | `4,865,609` | `4,865,609` | PASS |
| Default `bench 11` | `259,695` | `259,695` (`0` diff) | `259,695` (`0` diff) | **1/4 BIT-IDENTICAL** |
| Default `bench 13` | `725,158` | `725,158` (`0` diff) | `725,158` (`0` diff) | **2/4 BIT-IDENTICAL** |
| `B4+r0067` `bench 11` | `187,930` | `187,930` (`0` diff) | `187,930` (`0` diff) | **3/4 BIT-IDENTICAL** |
| `B4+r0067` `bench 13` | `632,195` | `632,195` (`0` diff) | `632,195` (`0` diff) | **4/4 BIT-IDENTICAL** |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `218,410 / 576,076` (`0` diff) | `218,410 / 576,076` (`0` diff) | BIT-IDENTICAL |
| `v3_parity` (`r0067`, `8/8` KB, `8/8` OB) | `0 differ` | `0 differ` | `0 differ` | PASS |

*(Note: Default HCE `bench 11/13` without `r0067` is `312,866 / 862,329` on all three binaries.)*

### 3.2 Distinct Clock-Allocation Verification (`test_sf17_sf18_tm.py`)

- **`SF18` (`TmNodeShare=true` exact `soft` diagnostic, `go wtime 6000 btime 6000 winc 0 binc 0`):**
  - `base_r15dsg.exe`: `fullmove=1` -> `soft 272 ms`, `fullmove=22` -> `soft 272 ms`, `movestogo 20` -> `soft 285 ms`.
  - `SF18_tm_ply_curve.exe`: `fullmove=1` -> **`soft 230 ms`** (`-15.4%`), `fullmove=22` -> **`soft 332 ms`** (`+22.1%`), `movestogo 20` -> **`soft 285 ms`** (`== base`).
- **`SF17` (`bench5`, `TmSoftDivisor=80, TmUnstableFactor=100, TmFallingEvalPercent=0`, `go wtime 2400 btime 2400`):**
  - `base_r15dsg.exe`: stops at `depth 13`, `nodes = 99,809` (`~34 ms` >= `soft 29 ms * 1.0`).
  - `SF17_tm_bestmove_avg_eval.exe`: `tot_best_changes` instability memory raises factor above `1.0`, extending to `depth 14`, `nodes = 167,386` (`~60 ms`).
- **Pytest Run (`pytest -B -p no:cacheprovider`):**
  - Target (`SF17` + `SF18`): **3/3 PASSED** (`RC=0`).
  - Baseline (`FORGE_TEST_EXE=base_r15dsg.exe`): `test_1` PASSED (identical fixed-depth), **`test_2` FAILED (`272 not less than 272`)**, **`test_3` FAILED (`13 not greater than or equal to 14`)** (`RC=1`).

---

## 4. Compatibility & Next-Step Requirements

- `SF17` and `SF18` touch disjoint lines in `src/search.cpp` (`2931, 3145-3195` vs `2590-2688`) and have zero conflict with `V3P_pairwise_psqt.patch`, `SF8`, `SF20`, `proto_5`, or `proto_6`.
- **Before placement:** Wait for GPU-idle window (`CLOCK_MATCH_RUNNING` created), run pre-declared `fastchess` `6+0.06` matches (already scripted in `C:\nnue-lab\neon\forge_fixes\run_clock_tm_screen.py` with `PRIOR_S7_NOTE` `-32.2 [-49.0, -15.6]`), confirm positive Elo at `10+0.1` (`400g+`, LCB `> -10`), and rebuild with PGO.
