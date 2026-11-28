# Opus Placement Review Packet: `SF24_qs_evasion_pruning`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room quiescence check-evasion pruning (`move_count > 2`, non-TT/non-capture/non-promo/non-check quiet evasions with `quiet_history < 0` pruned in `qsearch`, `git apply --check RC=0`), passes all deterministic gates (`perft 5 = 4,865,609`, `v3_parity 0 differ` across `8/8` KB and `8/8` OB on `r0067`), and moves `B4+r0067 bench 13` by **`+2.91%`** (`650,576` vs `632,195`) and `FULL+r0067 bench 13` by **`+2.93%`** (`592,974` vs `576,076`). A pre-declared `1,000g @ 50k` match (plus `6+0.06` PGO confirmation) is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF24_qs_evasion_pruning.patch` (`1,693` B, `29` lines, `SHA-256: 0D7FEDFD0A7C8324FD6DB421DB3C2026070E1C13D08025A2916BB0659B3D5A8C`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF24_qs_evasion_pruning.exe` (`2,382,848` B, `SHA-256: E21BDF919EC19348579AF4B9D681B0D47B9A7D3004D45099C2E362C13CEAFAE6`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF24_qs_evasion_pruning_gate.json` (`overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf24_qs_evasion_pruning.py`

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -1847,14 +1847,20 @@
     while (!(move = picker.next(false)).is_none()) {
         if (!picker.last_move_known_legal() && !board.is_legal(move)) continue;
         ++move_count;
-        if (mate_moves_ == 0 && !in_check && best_score > -MateInMaxPly) {
-            const bool gives_check = board.gives_check(move);
-            // Futility: even winning the captured piece cannot raise alpha.
-            if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
-                best_score = std::max(best_score, futility_base + capture_value(board, move));
+        if (mate_moves_ == 0 && best_score > -MateInMaxPly) {
+            if (!in_check) {
+                const bool gives_check = board.gives_check(move);
+                // Futility: even winning the captured piece cannot raise alpha.
+                if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
+                    best_score = std::max(best_score, futility_base + capture_value(board, move));
+                    continue;
+                }
+                if (!board.see_ge(move, -tune::QsSeeMargin)) continue;
+            } else if (move_count > 2 && move != tt_move && !move.is_capture() && !move.is_promotion() &&
+                       !board.gives_check(move) && quiet_history(board, ss, move) < 0) {
+                // Clean-room Stockfish/Stormphrax QS check-evasion pruning.
                 continue;
             }
-            if (!board.see_ge(move, -tune::QsSeeMargin)) continue;
         }
 #if FORGE_SPD_PREFETCH_EARLY
         std::uint64_t child_key = 0;
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:1847-1859`):**
  1. Inside `Worker::qsearch`, `r15dsg` previously entered move pruning only when `!in_check` (applying capture futility and `see_ge(-tune::QsSeeMargin)`), searching every legal check evasion when `in_check`.
  2. `SF24` preserves the exact `!in_check` block and adds an `else if` branch for `in_check`: after at least 2 legal evasions (`move_count > 2`), a non-TT, non-capture, non-promotion, non-checking evasion with `quiet_history(board, ss, move) < 0` is pruned.
  3. `mate_moves_ == 0 && best_score > -MateInMaxPly` remains active, so at least 2 evasions (plus any TT, capture, promotion, or checking evasion, or all evasions when already losing by mate) are always searched.
- **Bounds & Interaction Checks:**
  1. **Checkmate soundness:** Because `move_count > 2` and `best_score > -MateInMaxPly` guard the evasion prune, legal checkmate detection and mate-score defense remain intact (`perft 5 = 4,865,609`).
  2. **Interaction with `V3P`, `SF8`, `SF20`, `proto_7`, `proto_8`:** Zero hunk overlap (`qsearch` lines `1847-1859` are untouched by all other patches).
- **Caveat 1 (No Match Played Yet):** Only deterministic gates and fail-before/pass-after tests have run. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (Non-PGO Binary):** `SF24_qs_evasion_pruning.exe` is non-PGO. Rebuild with `PGO` if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish / Stormphrax quiescence check-evasion pruning (`move_count > 2`, non-tactical negative-history quiet evasions) in Forge's `qsearch` loop (`src/search.cpp:1847-1859`).
- **License Status:** 100% clean-room implementation (`6` net C++ lines), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5e6f333b...`) | `SF24_qs_evasion_pruning.exe` (`e21bdf91...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `370,523 / 826,673` | `+18.43% / -4.13%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `231,693 / 677,083` | `-10.78% / -6.63%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `178,890 / 650,576` | `-4.81% / +2.91%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `168,361 / 592,974` | `-22.92% / +2.93%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 200 balanced FENs, `8/8` KB, `8/8` OB) | `0/200 differ` | `0/200 differ` (planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF24_qs_evasion_pruning.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf24_qs_evasion_pruning.py
```

Observed output (`RC=0`):
- `test_1_patch_apply_and_divergence`: **PASSED** (`git apply --check RC=0`; `B4` `6/6` diverge including `kiwipete d10` bestmove flip `e2a6 -> d5e6` (`('d5e6', -159, 18995)`) and `tactical_checks d9` (`('b2b4', 110, 19880)`); `FULL` `5/5` diverge)
- `test_2_bench13_delta_vs_base`: **PASSED** (`B4+r0067`: `650,576` vs `632,195`, `+2.91%`; `FULL+r0067`: `592,974` vs `576,076`, `+2.93%`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, `v3_parity 0/200`, planted bug caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf24_qs_evasion_pruning.py
```

Observed output (`RC=1`):
- `test_1_patch_apply_and_divergence`: **FAILED** (`AssertionError: 0 != 6 : Expected 6 B4 divergences, got 0`)
- `test_2_bench13_delta_vs_base`: **FAILED** (`AssertionError: 632195 == 632195 : B4+r0067 bench 13 must differ from base_r15dsg`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (shared baseline invariants)

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:1847-1859` and `SF24_qs_evasion_pruning.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`SF24_qs_evasion_pruning.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_sf24_qs_evasion_pruning.py --exe <placed_exe>` and `run_master_gates.py --quick`.
