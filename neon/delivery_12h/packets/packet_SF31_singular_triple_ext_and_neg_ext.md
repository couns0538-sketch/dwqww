# Opus Placement Review Packet: `SF31_singular_triple_ext_and_neg_ext`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room Stockfish singular-extension refinement featuring (1) `tt_capture`-aware double-extension margins (`32` for captures vs `16` for quiet TT moves), (2) a bounded quiet triple extension (`extension = 3`) when `!tt_capture && singular_score < singular_beta - 120 && inherited_double_extensions <= 4`, (3) stronger `-2` cut-node negative extension and `-1` `tt_score <= alpha` negative extension, and (4) fixing `ss->double_extensions` tracking from `(extension == 2)` to `(extension >= 2)` so triple extensions remain strictly bounded. Passes all `--quick` Master Gates (`hard_pass: true`, `perft 5 = 4,865,609`, `v3_parity 0 cp` max diff across `8/8` OB on `r0067`), diverges on `4/8` `B4` and `5/8` `FULL` benchmark FENs (flipping `FULL` `tactical_d9` `b2b4->c1g5`), and shifts `bench 13` by **`-8.48%`** on `FULL+r0067` (`527,197` vs `576,076`), **`+20.50%`** on `B4+r0067` (`761,780`), **`+12.89%`** on `r0067 Default` (`818,642`), and **`-0.43%`** on `HCE Default` (`858,594`). Completely orthogonal to the 6-patch Super-Stack and all Wave 4/5 patches. Zero completed `fastchess` matches exist; a pre-declared `1,000g @ 50k` match is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF31_singular_triple_ext_and_neg_ext.patch` (`1,629` B, `33` lines, `SHA-256: 51DD9DCC0736019018246CADB7D196DBF034E90F85A91DEE4A2C1A5FD5358E03`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF31_singular_triple_ext_and_neg_ext.exe` (`2,382,848` B, `SHA-256: 46F27107D294D67A5B664859582FAA2706F49B0416BEA016623FD080184D4930`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF31_singular_triple_ext_and_neg_ext_gate.json` (`8,888` B, `275` lines, `SHA-256: ACA70FD2D896451A0BFB3226910FD462FCB3C1DFA00331C27144AC9F7CD95D46`, `overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py` (`test_05_sf31_behavioral_and_bench`, full suite `9/9`)

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2356,21 +2356,28 @@
             if (aborted_) return 0;
             if (singular_score < singular_beta) {
                 extension = 1;
-                if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) {
+                // SF31 (clean-room Stockfish Singular): capture-aware double extension + bounded quiet triple extension.
+                const int dbl_margin = tt_capture ? 32 : 16;
+                if (!pv_node && singular_score < singular_beta - dbl_margin && inherited_double_extensions <= 6) {
                     extension = 2;
+                    if (!tt_capture && singular_score < singular_beta - 120 && inherited_double_extensions <= 4) {
+                        extension = 3;
+                    }
                 }
             } else if (singular_beta >= beta) {
                 return singular_beta;
             } else if (tt_score >= beta) {
                 extension = -2;
             } else if (cut_node) {
+                extension = -2;
+            } else if (tt_score <= alpha) {
                 extension = -1;
             }
         } else if (mate_moves_ == 0 && gives_check && depth >= tune::CheckExtensionDepth && !root_node &&
                    (picker.last_move_see_nonnegative() || board.see_ge(move, 0))) {
             extension = 1;
         }
-        ss->double_extensions = inherited_double_extensions + (extension == 2);
+        ss->double_extensions = inherited_double_extensions + (extension >= 2);
         int new_depth = depth - 1 + extension;
 
 #if FORGE_SPD_PREFETCH_EARLY
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:2356-2386` inside `Worker::search` singular extensions):**
  1. **`tt_capture`-Aware Double & Quiet Triple Extension (`search.cpp:2359-2361`):** Replaces the fixed double-extension threshold `24` with `const int dbl_margin = tt_capture ? 32 : 16;`, granting double extensions slightly easier on quiet singular moves (`16` vs `24`) and harder on capture singular moves (`32` vs `24`). Adds a bounded quiet triple extension (`extension = 3`) when `!tt_capture && singular_score < singular_beta - 120 && inherited_double_extensions <= 4`.
  2. **Stronger Negative Extensions (`search.cpp:2366-2368`):** When singular verification fails high (`singular_score >= singular_beta` and `singular_beta < beta` and `tt_score < beta`), upgrades `else if (cut_node)` from `extension = -1;` to `extension = -2;`, and adds `else if (tt_score <= alpha) { extension = -1; }` to trim non-singular TT moves whose cached score was already at or below `alpha`.
  3. **`double_extensions` Accounting Fix (`search.cpp:2373`):** Changes `inherited_double_extensions + (extension == 2)` to `inherited_double_extensions + (extension >= 2)`, ensuring triple extensions (`extension == 3`) increment `double_extensions` and obey the `<= 4` / `<= 6` inheritance caps.
- **Bounds & Interaction Checks:**
  1. **Extension Explosion Prevention:** Triple extensions are restricted to `!pv_node && !tt_capture && inherited_double_extensions <= 4` and increment `ss->double_extensions` via `(extension >= 2)`, capping cumulative multi-extensions along any root-to-leaf path. Note that `singular_beta = tt_score - tune::SingularMargin * depth` (`2345`), and `singular_score` comes from `search_child` in `[-Infinite, Infinite]`, while `singular_beta - 120` cannot overflow `int` (entry guard requires `std::abs(tt_score) < MateInMaxPly`).
  2. **Zero Patch Overlap:** Completely disjoint from all 6 Super-Stack patches (`V3P_v3`, `SF33`, `SF8`, `proto_1`, `SF15`, `SF27`), `SF28`, `SF29`, `SF30`, `proto_7`, `proto_8`, `proto_9`, and `proto_10` (applies cleanly on top of the 6-patch Super-Stack).
- **Caveat 1 (No Match Played Yet):** `ALL_MATCHES_SCOREBOARD.md` records **0 completed `fastchess` matches** for `SF31`. (Note: an earlier Wave 2 variant `SF11_quiet_refutation_hist_triple_ext_600g_50k` scored `+1.74 [-13.81, +17.30]` Elo, whereas `SF31` adds `dbl_margin = tt_capture ? 32 : 16`, `cut_node` `-2`, `tt_score <= alpha` `-1`, and the `(extension >= 2)` bound fix.) A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (Non-PGO Binary):** `SF31_singular_triple_ext_and_neg_ext.exe` is non-PGO. Rebuild with PGO if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish singular extension (`tt_capture`-differentiated double-extension margin, bounded quiet triple extension at `singular_beta - 120`, `-2` `cut_node` / `-1` `tt_score <= alpha` negative extensions, and `extension >= 2` `ss->double_extensions` increment), implemented cleanly on Forge's `Worker::search`.
- **License Status:** 100% clean-room implementation (`+9 / -2`, `7` net C++ lines), zero verbatim GPL code copied, zero Stockfish eval labels.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5E6F333B...`) | `SF31_singular_triple_ext_and_neg_ext.exe` (`46F27107...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `run_master_gates --quick` (`perft 6/6`, `eval_net_full`, `loader 13/13`) | — | `PASS_WITH_ADVISORY_FLAGS` (`hard_pass: true`) | PASS |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `323,381 / 858,594` | `+3.36% / -0.43%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `259,559 / 818,642` | `-0.05% / +12.89%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `244,790 / 761,780` | `+30.26% / +20.50%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `228,066 / 527,197` | `+4.42% / -8.48%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 120/200 balanced FENs, `8/8` KB, `8/8` OB) | `0` differ | `0` differ (`max_diff_cp = 0`, planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF31_singular_triple_ext_and_neg_ext.exe` (`FORGE_TEST_EXE=""`)

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
```

*(Primary `C:\nnue-lab\venv\Scripts\python.exe` lacks `pytest`; run via `unittest discover -s ... -p ...` rather than a bare `.py` path: `C:\nnue-lab\venv\Scripts\python.exe -B -m unittest discover -s C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests -p test_round9_11_and_wave5_search.py -v` — `RC=0`, `9/9 OK` when `FORGE_TEST_EXE=""`; `RC=1`, `7 failed` when `FORGE_TEST_EXE=base_r15dsg.exe`.)*

Observed live output (`RC=0`, `9 passed in 31.38s`):
```text
TestRound911AndWave5Search::test_01_all_patches_apply_cleanly PASSED [ 11%]
TestRound911AndWave5Search::test_05_sf31_behavioral_and_bench PASSED [ 55%]
...
TestRound911AndWave5Search::test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity PASSED [100%]
============================= 9 passed in 31.38s ==============================
```
- `test_01_all_patches_apply_cleanly`: **PASSED** (`git -C C:\nnue-lab\forge\r15dsg apply --check` `RC=0` for `SF31` and all 6 peer patches)
- `test_05_sf31_behavioral_and_bench`: **PASSED** (`B4` diverges on `4/8` FENs: `kiwipete_d10` `20623->20258`, `bench3_d9` `(10, 12494)->(-1, 13632)`, `bench5_d9` `(-326, 10472)->(-306, 8512)`, `tactical_d9`; `FULL` diverges on `5/8` FENs including bestmove flip on `tactical_d9` `b2b4->c1g5` (`('c1g5', 95, 11309)`); `B4 bench 13` = `761,780` (`+20.50%`) and `FULL bench 13` = `527,197` (`-8.48%`))
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
TestRound911AndWave5Search::test_05_sf31_behavioral_and_bench FAILED [ 55%]
...
E           AssertionError: ('e2a6', -134, 20623) == ('e2a6', -134, 20623) : SF31 B4 must diverge from base on kiwipete_d10
...
TestRound911AndWave5Search::test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity PASSED [100%]
========================= 7 failed, 2 passed in 5.88s =========================
```

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:2356-2386` and `SF31_singular_triple_ext_and_neg_ext.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`SF31_singular_triple_ext_and_neg_ext.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_round9_11_and_wave5_search.py` and `run_master_gates.py --quick`.
