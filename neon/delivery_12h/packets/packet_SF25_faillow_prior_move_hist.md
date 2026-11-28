# Opus Placement Review Packet: `SF25_faillow_prior_move_hist`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room fail-low prior-move butterfly/capture history credit (`depth >= 3` parent quiet `main_history_` `+history_bonus(depth)/2` and parent capture `capture_history_` `+history_bonus(depth)/2` when `best_move.is_none()`, preserving `FailLowContinuationBonus`, `git apply --check RC=0`), passes all deterministic gates (`perft 5 = 4,865,609`, `v3_parity 0 differ` across `8/8` KB and `8/8` OB on `r0067`), and moves `B4+r0067 bench 13` by **`+8.91%`** (`688,554` vs `632,195`) and `FULL+r0067 bench 13` by **`+0.48%`** (`578,851` vs `576,076`). A pre-declared `1,000g @ 50k` match (plus `6+0.06` PGO confirmation) is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF25_faillow_prior_move_hist.patch` (`2,168` B, `34` lines, `SHA-256: 4617216E6CDDB66052BA5B01174A19600E714B0195F75B345EFA1A7C1CDB1996`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF25_faillow_prior_move_hist.exe` (`2,383,360` B, `SHA-256: FA49057C9F4141A5D8916F4A9F457553656AD0951FA2D649CD4A435A2A95CA1F`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF25_faillow_prior_move_hist_gate.json` (`overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf25_faillow_prior_move_hist.py`

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2507,11 +2507,26 @@
 #endif
         // B4 HistRework: the twin gets the same bonus.
         if (tune::HistRework != 0) apply_history(rework_entry(board, ss, best_move), history_bonus(depth) / 4);
-    } else if (tune::FailLowContinuationBonus > 0 && best_move.is_none() && !(ss - 1)->current_move.is_none() &&
-               (ss - 1)->moved_piece != Empty && !(ss - 1)->current_move.is_capture() && ply > 0) {
-        // Every move failed low: the parent's quiet move refuted this line.
-        update_continuation(ss - 1, (ss - 1)->moved_piece, (ss - 1)->current_move.to,
-                            history_bonus(depth) * tune::FailLowContinuationBonus / 100);
+    } else if (best_move.is_none() && !(ss - 1)->current_move.is_none() &&
+               (ss - 1)->moved_piece != Empty && ply > 0) {
+        const Move prev = (ss - 1)->current_move;
+        if (!prev.is_capture() && !prev.is_promotion()) {
+            if (tune::FailLowContinuationBonus > 0) {
+                // Every move failed low: the parent's quiet move refuted this line.
+                update_continuation(ss - 1, (ss - 1)->moved_piece, prev.to,
+                                    history_bonus(depth) * tune::FailLowContinuationBonus / 100);
+            }
+            if (depth >= 3) {
+                // Clean-room Stockfish prior quiet move butterfly bonus on fail-low.
+                apply_history((*main_history_)[static_cast<std::size_t>(opposite(board.side_to_move()))][prev.from][prev.to],
+                              history_bonus(depth) / 2);
+            }
+        } else if (depth >= 3 && prev.is_capture() && ss->entered_capture != Empty) {
+            // Clean-room Stockfish prior capture bonus on fail-low.
+            const int cap_pt = piece_type(ss->entered_capture);
+            apply_history((*capture_history_)[static_cast<std::size_t>((ss - 1)->moved_piece)][prev.to][static_cast<std::size_t>(cap_pt)],
+                          history_bonus(depth) / 2);
+        }
     }
 
     const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:2507-2515`):**
  1. When a node fails low completely (`best_move.is_none()`), the parent move `(ss - 1)->current_move` refuted the opponent's line. Previously, `r15dsg` only credited `update_continuation` when `tune::FailLowContinuationBonus > 0` (off in `B4`/Default, `41` in `FULL`) and ignored `main_history_` and parent captures.
  2. `SF25` preserves `FailLowContinuationBonus` for quiet parent moves and adds a `depth >= 3` `+history_bonus(depth) / 2` credit to `main_history_[opposite(stm)][prev.from][prev.to]` when the parent move was quiet (`!prev.is_capture() && !prev.is_promotion()`), or to `capture_history_[(ss - 1)->moved_piece][prev.to][piece_type(ss->entered_capture)]` when the parent move was a capture (`prev.is_capture() && ss->entered_capture != Empty`).
- **Bounds & Interaction Checks:**
  1. **Null-move / ply safety:** Guarded by `!(ss - 1)->current_move.is_none() && (ss - 1)->moved_piece != Empty && ply > 0` (null moves set `moved_piece = Empty`, so null moves are excluded).
  2. **Interaction with `V3P`, `SF8`, `SF20`, `proto_7`, `proto_8`:** Zero hunk overlap (`2507-2515` is untouched by all other patches).
- **Caveat 1 (No Match Played Yet):** Only deterministic gates and fail-before/pass-after tests have run. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (Non-PGO Binary):** `SF25_faillow_prior_move_hist.exe` (`2,383,360` B) is non-PGO. Rebuild with `PGO` if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish prior-move butterfly / capture-history credit on all-moves fail-low (`depth >= 3`, `best_move.is_none()`) adapted to Forge's `SearchStack::entered_capture` and `FailLowContinuationBonus` scaffolding (`src/search.cpp:2507-2515`).
- **License Status:** 100% clean-room implementation (`15` net C++ lines), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5e6f333b...`) | `SF25_faillow_prior_move_hist.exe` (`fa49057c...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `334,674 / 877,771` | `+6.97% / +1.79%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `275,219 / 717,731` | `+5.98% / -1.02%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `245,237 / 688,554` | `+30.49% / +8.91%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `203,215 / 578,851` | `-6.96% / +0.48%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 200 balanced FENs, `8/8` KB, `8/8` OB) | `0/200 differ` | `0/200 differ` (planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF25_faillow_prior_move_hist.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf25_faillow_prior_move_hist.py
```

Observed output (`RC=0`):
- `test_1_patch_apply_and_divergence`: **PASSED** (`git apply --check RC=0`; `B4` `5/5` diverge including `bench5 d9` bestmove flip `c4d5 -> a2a3` (`('a2a3', -320, 15741)`); `FULL` `5/5` diverge including `bench3 d9` flip `h2h3 -> c4b3`)
- `test_2_bench13_delta_vs_base`: **PASSED** (`B4+r0067`: `688,554` vs `632,195`, `+8.91%`; `FULL+r0067`: `578,851` vs `576,076`, `+0.48%`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, `v3_parity 0/200`, planted bug caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf25_faillow_prior_move_hist.py
```

Observed output (`RC=1`):
- `test_1_patch_apply_and_divergence`: **FAILED** (`AssertionError: 0 != 5 : Expected 5 B4 divergences, got 0`)
- `test_2_bench13_delta_vs_base`: **FAILED** (`AssertionError: 632195 == 632195 : B4+r0067 bench 13 must differ from base_r15dsg`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (shared baseline invariants)

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:2507-2525` and `SF25_faillow_prior_move_hist.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`SF25_faillow_prior_move_hist.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_sf25_faillow_prior_move_hist.py --exe <placed_exe>` and `run_master_gates.py --quick`.
