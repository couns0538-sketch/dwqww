# Opus Placement Review Packet: `SF30_probcut_tt_and_corrhist_promo_fix`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room Stockfish refinement combining (1) an immediate ProbCut transposition-table cutoff when a stored `BoundLower` / `BoundExact` entry at `tt_depth >= depth - 3` already beats `probcut_beta` (plus `!bare_king_mode` and `probcut_beta < MateInMaxPly` safety guards), and (2) excluding promotions (`!best_move.is_promotion()`) from `update_correction` so tactical quiet promotions do not pollute static-evaluation correction history. Passes all `--quick` Master Gates (`hard_pass: true`, `perft 5 = 4,865,609`, `v3_parity 0 cp` max diff across `8/8` OB on `r0067`), diverges on `7/8` `B4` FENs (flipping `kiwipete_d10` `e2a6->d5e6`) and `4/8` `FULL` FENs, and sharply shrinks `FULL+r0067 bench 13` by **`-24.42%`** (`435,414` vs `576,076`), `HCE Default` by **`-15.59%`** (`727,913` vs `862,329`), and `r0067 Default` by **`-6.94%`** (`674,807` vs `725,158`) while shifting `B4+r0067` by **`+8.88%`** (`688,325`). Completely orthogonal to the 6-patch Super-Stack and all Wave 4/5 patches. Zero completed `fastchess` matches exist; a pre-declared `1,000g @ 50k` match is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF30_probcut_tt_and_corrhist_promo_fix.patch` (`1,814` B, `28` lines, `SHA-256: 092F8F2145EB5CABF916BAEB495AFDD995FBCB0D737C310BA8C55ECA1CC3960F`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF30_probcut_tt_and_corrhist_promo_fix.exe` (`2,382,336` B, `SHA-256: F78D67D32D0F90ECE8C14CEFDE3E01CF1876CB65A382114AD03E7A79E3731859`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF30_probcut_tt_and_corrhist_promo_fix_gate.json` (`8,888` B, `275` lines, `SHA-256: 13545CCB566FC28FEFF9329830516FCF3B483DCC11942EE9973B2356375AF567`, `overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py` (`test_04_sf30_behavioral_and_bench`, full suite `9/9`)

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2144,7 +2144,13 @@
         }
         // ProbCut: a good capture that beats beta by a margin at reduced depth.
         const int probcut_beta = beta + tune::ProbcutMargin - 50 * improving;
-        if (depth >= tune::ProbcutDepth && !is_mate_score(beta) &&
+        // SF30 (clean-room Stockfish ProbCut): immediate TT cutoff when stored bound already beats probcut_beta.
+        if (!bare_king_mode && depth >= tune::ProbcutDepth && !is_mate_score(beta) && probcut_beta < MateInMaxPly &&
+            tt_hit && tt_depth >= depth - 3 && tt_score != ValueNone && tt_score >= probcut_beta &&
+            (tt_bound == BoundLower || tt_bound == BoundExact)) {
+            return tt_score;
+        }
+        if (!bare_king_mode && depth >= tune::ProbcutDepth && !is_mate_score(beta) && probcut_beta < MateInMaxPly &&
             !(tt_hit && tt_depth >= depth - 3 && tt_score != ValueNone && tt_score < probcut_beta)) {
             MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Quiescence);
             Move move;
@@ -2524,8 +2530,9 @@
     }
     // Teach the static evaluation about this pawn structure when the search
     // result is a usable bound in the direction of the difference.
+    // SF30 (clean-room Stockfish CorrHist): exclude quiet promotions too so tactical promotions don't bias corrhist.
     if (!in_check && excluded.is_none() && !is_mate_score(best_score) &&
-        (best_move.is_none() || !best_move.is_capture()) &&
+        (best_move.is_none() || (!best_move.is_capture() && !best_move.is_promotion())) &&
         !(bound == BoundLower && best_score <= ss->static_eval) &&
         !(bound == BoundUpper && best_score >= ss->static_eval)) {
         update_correction(board, depth, best_score, ss->static_eval, ss);
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:2144-2156, 2524-2534` inside `Worker::search`):**
  1. **Hunk 1 — ProbCut TT Fast-Cutoff & Safety Guards (`search.cpp:2146-2148`):** Before constructing `MovePicker(..., Mode::Quiescence)`, checks if a TT entry with `tt_depth >= depth - 3`, `tt_score != ValueNone`, `tt_score >= probcut_beta`, and `tt_bound` in `{BoundLower, BoundExact}` already proves the `probcut_beta` fail-high, returning `tt_score` immediately without running quiescence/reduced ProbCut searches. Also adds `!bare_king_mode` and `probcut_beta < MateInMaxPly` guards to both the TT fast-cutoff and the ProbCut search loop (`2147`).
  2. **Hunk 2 — Correction-History Promotion Exclusion (`search.cpp:2528`):** Tightens `(best_move.is_none() || !best_move.is_capture())` to `(best_move.is_none() || (!best_move.is_capture() && !best_move.is_promotion()))` in the `update_correction(...)` gate so non-capture tactical promotions (e.g., quiet pawn push to the 8th rank) do not distort pawn/material/non-pawn correction tables.
- **Bounds & Interaction Checks:**
  1. **Mate & Bare-King Soundness:** `probcut_beta = beta + tune::ProbcutMargin - 50 * improving` can reach or exceed `MateInMaxPly` when `beta` is close to mate; the new `probcut_beta < MateInMaxPly` and `!bare_king_mode` guards prevent ProbCut (and its TT cutoff) from firing on near-mate windows or bare-king endings. Note also that `FULL` sets `ProbcutDepth=7, ProbcutMargin=168, MaterialCorrectionWeight=48, NonPawnCorrection=true`, driving the stronger `-24.42%` `FULL bench 13` reduction vs `+8.88%` under `B4`.
  2. **Zero Patch Overlap:** Verified completely disjoint from all 6 Super-Stack patches (`V3P_v3`, `SF33`, `SF8`, `proto_1`, `SF15`, `SF27`) as well as `SF28`, `SF29`, `SF31`, `proto_7`, `proto_8`, `proto_9`, and `proto_10` (applies cleanly on top of the 6-patch Super-Stack).
- **Caveat 1 (No Match Played Yet):** `ALL_MATCHES_SCOREBOARD.md` records **0 completed `fastchess` matches** for `SF30`. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (Non-PGO Binary):** `SF30_probcut_tt_and_corrhist_promo_fix.exe` is non-PGO. Rebuild with PGO if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish ProbCut TT fast-cutoff (reusing a stored lower/exact TT entry at `tt_depth >= depth - 3` when `tt_score >= probcut_beta`) + near-mate bound guard (`probcut_beta < MateInMaxPly`), paired with clean-room Stockfish correction-history promotion exclusion (`!best_move.is_promotion()`), implemented cleanly on Forge's `Worker::search`.
- **License Status:** 100% clean-room implementation (`+9 / -2`, `7` net C++ lines), zero verbatim GPL code copied, zero Stockfish eval labels.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5E6F333B...`) | `SF30_probcut_tt_and_corrhist_promo_fix.exe` (`F78D67D3...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `run_master_gates --quick` (`perft 6/6`, `eval_net_full`, `loader 13/13`) | — | `PASS_WITH_ADVISORY_FLAGS` (`hard_pass: true`) | PASS |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `298,049 / 727,913` | `-4.74% / -15.59%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `244,101 / 674,807` | `-6.00% / -6.94%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `217,490 / 688,325` | `+15.73% / +8.88%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `196,218 / 435,414` | `-10.16% / -24.42%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 120/200 balanced FENs, `8/8` KB, `8/8` OB) | `0` differ | `0` differ (`max_diff_cp = 0`, planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF30_probcut_tt_and_corrhist_promo_fix.exe` (`FORGE_TEST_EXE=""`)

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
```

*(Primary `C:\nnue-lab\venv\Scripts\python.exe` lacks `pytest`; run via `unittest discover -s ... -p ...` rather than a bare `.py` path: `C:\nnue-lab\venv\Scripts\python.exe -B -m unittest discover -s C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests -p test_round9_11_and_wave5_search.py -v` — `RC=0`, `9/9 OK` when `FORGE_TEST_EXE=""`; `RC=1`, `7 failed` when `FORGE_TEST_EXE=base_r15dsg.exe`.)*

Observed live output (`RC=0`, `9 passed in 31.38s`):
```text
TestRound911AndWave5Search::test_01_all_patches_apply_cleanly PASSED [ 11%]
TestRound911AndWave5Search::test_04_sf30_behavioral_and_bench PASSED [ 44%]
...
TestRound911AndWave5Search::test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity PASSED [100%]
============================= 9 passed in 31.38s ==============================
```
- `test_01_all_patches_apply_cleanly`: **PASSED** (`git -C C:\nnue-lab\forge\r15dsg apply --check` `RC=0` for `SF30` and all 6 peer patches)
- `test_04_sf30_behavioral_and_bench`: **PASSED** (`B4` diverges on `7/8` FENs including bestmove flip on `kiwipete_d10` `e2a6->d5e6` (`('d5e6', -157, 25746)`); `FULL bench 13` = `435,414` vs `576,076` (`-24.42%`))
- `test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, Mate-in-1 `d1d8`, `go mate 2`, `Qh4+` `g2g3`, `v3_parity 0/200` with planted `king_map[2]` fault caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
```

Observed live output (`RC=1`, `7 failed, 2 passed in 5.88s`):
```text
TestRound911AndWave5Search::test_01_all_patches_apply_cleanly PASSED [ 11%]
TestRound911AndWave5Search::test_04_sf30_behavioral_and_bench FAILED [ 44%]
...
E           AssertionError: ('c2c4', 22, 4022) == ('c2c4', 22, 4022) : SF30 B4 must diverge from base on startpos_d9
...
TestRound911AndWave5Search::test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity PASSED [100%]
========================= 7 failed, 2 passed in 5.88s =========================
```

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:2144-2156, 2524-2534` and `SF30_probcut_tt_and_corrhist_promo_fix.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`SF30_probcut_tt_and_corrhist_promo_fix.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_round9_11_and_wave5_search.py` and `run_master_gates.py --quick`.
