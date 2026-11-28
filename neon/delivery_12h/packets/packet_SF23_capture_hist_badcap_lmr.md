# Opus Placement Review Packet: `SF23_capture_hist_badcap_lmr`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF — NOTE `SF20` HUNK OVERLAP)** — Clean-room capture-history LMR scaling (`-clamp(history / 6000, -1, 1)`), cached bad-capture LMR `+1`, and post-LMR `score > alpha` `capture_history_` boost (`git apply --check RC=0` against base `r15dsg`), passes all deterministic gates (`perft 5 = 4,865,609`, `v3_parity 0 differ` across `8/8` KB and `8/8` OB on `r0067`), and moves `B4+r0067 bench 13` by **`+18.90%`** (`751,693` vs `632,195`) and `FULL+r0067 bench 13` by **`+8.90%`** (`627,372` vs `576,076`). **Overlap warning:** `SF23` edits `src/search.cpp:2416`, the exact same line modified by `SF20_killer_lmr_relief.patch`; sequential stacking with `SF20` requires a manual 4-line merge. A pre-declared `1,000g @ 50k` match (plus `6+0.06` PGO confirmation) is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF23_capture_hist_badcap_lmr.patch` (`1,912` B, `36` lines, `SHA-256: A9F015D28BA40FB0BD262F68EBC2FC77CB744338E173872654860D6B7DA66698`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF23_capture_hist_badcap_lmr.exe` (`2,382,848` B, `SHA-256: 1A4663A4844C06275EC0EED35ABCC840FA13D1041C075F31879C96D396C75869`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF23_capture_hist_badcap_lmr_gate.json` (`overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf23_capture_hist_badcap_lmr.py`

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2413,7 +2413,13 @@
             if (gives_check) r -= 1;
             if (in_check) r -= 1;
             if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;
-            if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);
+            if (quiet) {
+                r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);
+            } else if (capture) {
+                // Clean-room Stockfish capture-history & cached bad-capture LMR adjustment.
+                r -= std::clamp(history / 6000, -1, 1);
+                if (!gives_check && !picker.last_move_see_nonnegative()) ++r;
+            }
             if (tune::LmrSignedCorrection && quiet && ss->static_eval != ValueNone &&
                 ss->raw_eval != ValueNone) {
                 const int correction_cp = ss->static_eval - ss->raw_eval;
@@ -2439,9 +2445,15 @@
                 }
                 full_depth_needed = false;
             }
-            if (!aborted_ && quiet && score > alpha) {
-                // A late quiet move that beat expectations deserves a history boost.
-                update_continuation(ss, moved, move.to, history_bonus(depth) / 2);
+            if (!aborted_ && score > alpha) {
+                if (quiet) {
+                    // A late quiet move that beat expectations deserves a history boost.
+                    update_continuation(ss, moved, move.to, history_bonus(depth) / 2);
+                } else if (capture) {
+                    const int captured = piece_type(board.captured_piece(move));
+                    apply_history((*capture_history_)[static_cast<std::size_t>(moved)][move.to][static_cast<std::size_t>(captured)],
+                                  history_bonus(depth) / 2);
+                }
             }
         }
         if (full_depth_needed && !aborted_) {
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:2413-2420, 2445-2454`):**
  1. Previously, `r15dsg` adjusted LMR by history only when `quiet` (`search.cpp:2416`), leaving captures unadjusted by capture history or cached SEE status, and only gave post-LMR `score > alpha` continuation boosts to `quiet` moves (`search.cpp:2442-2445`).
  2. `SF23` adds an `else if (capture)` branch in LMR: subtracts `std::clamp(history / 6000, -1, 1)` and adds `+1` reduction for non-checking bad captures (`!gives_check && !picker.last_move_see_nonnegative()`).
  3. When a late `capture` fails high over `alpha` in the LMR search (`!aborted_ && score > alpha`), `SF23` boosts `(*capture_history_)[moved][move.to][captured]` by `history_bonus(depth) / 2`.
- **Bounds & Interaction Checks:**
  1. **Lower bound safety:** `reduced_depth = std::clamp(new_depth - r, 1, new_depth)` (`search.cpp:2426`) prevents extensions when `r <= 0`.
  2. **CRITICAL — Overlap with `SF20_killer_lmr_relief.patch`:** Both `SF20` and `SF23` edit `src/search.cpp:2416` (`if (quiet) r -= std::clamp(...)`). `git apply --check SF20.patch SF23.patch` passes only because `git apply --check` checks each patch independently against base `r15dsg`; sequential `git apply` fails at hunk `@@ -2413,7`. If both `SF20` and `SF23` are promoted, combine the `if (quiet) { ... if (move == ss->killers[0] || move == ss->killers[1]) r -= 1; } else if (capture) { ... }` blocks manually.
  3. **No overlap with `proto_7` (`2409`) or `proto_8` (`2272, 2307-2313`):** `search.cpp:2410-2412` remains untouched.
- **Caveat 1 (No Match Played Yet):** Only deterministic gates and fail-before/pass-after tests have run. Note `B4+r0067 bench 13` grows by `+18.90%` (`751,693` vs `632,195`), while `FULL+r0067` is `+8.90%`; a `1,000g @ 50k` match will decide whether the extra search pays off.
- **Caveat 2 (Non-PGO Binary):** `SF23_capture_hist_badcap_lmr.exe` is non-PGO. Rebuild with `PGO` if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish capture-history LMR adjustment, bad-capture `+1` LMR, and post-LMR `capture_history_` bonus on `score > alpha`, using Forge's `MovePicker::last_move_see_nonnegative()` and `CaptureHistory`.
- **License Status:** 100% clean-room implementation (`12` net C++ lines), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5e6f333b...`) | `SF23_capture_hist_badcap_lmr.exe` (`1a4663a4...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `326,654 / 847,444` | `+4.41% / -1.73%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `256,095 / 832,227` | `-1.39% / +14.76%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `192,084 / 751,693` | `+2.21% / +18.90%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `224,965 / 627,372` | `+3.00% / +8.90%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 200 balanced FENs, `8/8` KB, `8/8` OB) | `0/200 differ` | `0/200 differ` (planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF23_capture_hist_badcap_lmr.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf23_capture_hist_badcap_lmr.py
```

Observed output (`RC=0`):
- `test_1_patch_apply_and_divergence`: **PASSED** (`git apply --check RC=0`; `B4` `4/4` diverge on `kiwipete/bench3/bench5/bench8`; `FULL` `4/4` diverge including `bench3 d9` bestmove flip `h2h3 -> c4b3` (`('c4b3', 1, 10379)`))
- `test_2_bench13_delta_vs_base`: **PASSED** (`B4+r0067`: `751,693` vs `632,195`, `+18.90%`; `FULL+r0067`: `627,372` vs `576,076`, `+8.90%`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, `v3_parity 0/200`, planted bug caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf23_capture_hist_badcap_lmr.py
```

Observed output (`RC=1`):
- `test_1_patch_apply_and_divergence`: **FAILED** (`AssertionError: 0 != 4 : Expected 4 B4 divergences, got 0`)
- `test_2_bench13_delta_vs_base`: **FAILED** (`AssertionError: 632195 == 632195 : B4+r0067 bench 13 must differ from base_r15dsg`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (shared baseline invariants)

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:2413-2454` and `SF23_capture_hist_badcap_lmr.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Merge the `if (quiet) { ... }` block with `SF20_killer_lmr_relief.patch` if both `SF20` and `SF23` are stacked.
- [ ] Run pre-declared `1,000g @ 50k` match (`SF23_capture_hist_badcap_lmr.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_sf23_capture_hist_badcap_lmr.py --exe <placed_exe>` and `run_master_gates.py --quick`.
