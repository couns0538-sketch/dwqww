# Opus Placement Review Packet: `SF26_cutoff_surprise_hist_depth`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Minimal `5`-line clean-room surprise-cutoff bonus depth (`+1` history depth when `!in_check && ss->static_eval <= alpha` on quiet beta cutoffs, plus `+(best_score > beta + 100)` shared on capture cutoffs, `git apply --check RC=0`), passes all deterministic gates (`perft 5 = 4,865,609`, `v3_parity 0 differ` across `8/8` KB and `8/8` OB on `r0067`), and shrinks `B4+r0067 bench 13` by **`-1.80%`** (`620,806` vs `632,195`) and `FULL+r0067 bench 13` by **`-12.98%`** (`501,280` vs `576,076`). A pre-declared `1,000g @ 50k` match (plus `6+0.06` PGO confirmation) is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF26_cutoff_surprise_hist_depth.patch` (`1,118` B, `18` lines, `SHA-256: 20875F4E37743DF312274458EF07E20FB1C3018EF24F9FEC7BF1A687C106FDF9`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF26_cutoff_surprise_hist_depth.exe` (`2,382,848` B, `SHA-256: 19B8ED6B808597DE65454E899C700516B4B88FCB63464689857A63723EEAD343`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF26_cutoff_surprise_hist_depth_gate.json` (`overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf26_cutoff_surprise_hist_depth.py`

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2491,10 +2491,12 @@
     }
 
     if (best_score >= beta) {
+        const int extra_d = static_cast<int>(best_score > beta + 100) +
+                            static_cast<int>(!in_check && ss->static_eval != ValueNone && ss->static_eval <= alpha);
         if (!best_move.is_capture() && !best_move.is_promotion()) {
-            update_quiet_stats(board, ss, best_move, depth + (best_score > beta + 100), quiets_tried.data(), quiet_count);
-        }
-        update_capture_stats(board, best_move, depth, captures_tried.data(), capture_count);
+            update_quiet_stats(board, ss, best_move, depth + extra_d, quiets_tried.data(), quiet_count);
+        }
+        update_capture_stats(board, best_move, depth + (best_score > beta + 100), captures_tried.data(), capture_count);
     } else if (!best_move.is_none() && (!best_move.is_capture() && !best_move.is_promotion())) {
         // Even without a cutoff, a new PV move earned its place.
         apply_history((*main_history_)[static_cast<std::size_t>(board.side_to_move())][best_move.from][best_move.to],
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:2491-2498`):**
  1. On a beta cutoff (`best_score >= beta`), `r15dsg` previously added `+1` to history depth only when `best_score > beta + 100` for quiet cutoffs, and used plain `depth` for `update_capture_stats`.
  2. `SF26` adds a second `+1` ("surprise cutoff" depth) for quiet beta cutoffs when `!in_check && ss->static_eval != ValueNone && ss->static_eval <= alpha` (static eval suggested failing low, yet a quiet move cut off), and passes `depth + (best_score > beta + 100)` to `update_capture_stats`.
- **Bounds & Interaction Checks:**
  1. **History clamp safety:** `history_bonus(depth)` is clamped inside `HistoryBonusMax` (`2048` in B4 / `2429` in FULL), so `depth + 2` never overflows `int16_t` history tables.
  2. **Interaction with `V3P`, `SF8`, `SF20`, `proto_7`, `proto_8`:** Zero hunk overlap (`2491-2498` is untouched by all other patches, and is `9` lines clear of `SF25`'s `2507-2515` hunk).
- **Caveat 1 (No Match Played Yet):** Only deterministic gates and fail-before/pass-after tests have run. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (Non-PGO Binary):** `SF26_cutoff_surprise_hist_depth.exe` is non-PGO. Rebuild with `PGO` if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish cutoff-surprise history depth (`static_eval <= alpha` on beta cutoff -> `+1` bonus depth; capture cutoff margin `+1`) in Forge's `update_quiet_stats` / `update_capture_stats` path (`src/search.cpp:2491-2498`).
- **License Status:** 100% clean-room implementation (`2` net C++ lines), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5e6f333b...`) | `SF26_cutoff_surprise_hist_depth.exe` (`19b8ed6b...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `331,288 / 802,501` | `+5.89% / -6.94%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `273,822 / 712,399` | `+5.44% / -1.76%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `199,086 / 620,806` | `+5.94% / -1.80%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `193,418 / 501,280` | `-11.44% / -12.98%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 200 balanced FENs, `8/8` KB, `8/8` OB) | `0/200 differ` | `0/200 differ` (planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF26_cutoff_surprise_hist_depth.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf26_cutoff_surprise_hist_depth.py
```

Observed output (`RC=0`):
- `test_1_patch_apply_and_divergence`: **PASSED** (`git apply --check RC=0`; `B4` `5/5` diverge including `startpos d9` bestmove flip `c2c4 -> e2e3` (`('e2e3', 27, 5225)`) and `bench3 d9` flip `c4d5 -> c3d5`; `FULL` `5/5` diverge including `bench3 d9` flip `h2h3 -> c4d5`)
- `test_2_bench13_delta_vs_base`: **PASSED** (`B4+r0067`: `620,806` vs `632,195`, `-1.80%`; `FULL+r0067`: `501,280` vs `576,076`, `-12.98%`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, `v3_parity 0/200`, planted bug caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf26_cutoff_surprise_hist_depth.py
```

Observed output (`RC=1`):
- `test_1_patch_apply_and_divergence`: **FAILED** (`AssertionError: 0 != 5 : Expected 5 B4 divergences, got 0`)
- `test_2_bench13_delta_vs_base`: **FAILED** (`AssertionError: 632195 == 632195 : B4+r0067 bench 13 must differ from base_r15dsg`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (shared baseline invariants)

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:2491-2498` and `SF26_cutoff_surprise_hist_depth.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`SF26_cutoff_surprise_hist_depth.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_sf26_cutoff_surprise_hist_depth.py --exe <placed_exe>` and `run_master_gates.py --quick`.
