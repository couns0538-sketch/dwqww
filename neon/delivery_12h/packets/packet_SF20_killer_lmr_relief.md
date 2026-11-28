# Opus Placement Review Packet: `SF20_killer_lmr_relief`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Minimal `4`-line clean-room LMR relief for quiet killer moves (`git apply --check RC=0`, zero conflict with `V3P`, `SF8`, `proto_5`, `proto_6`), passes all deterministic gates (`perft 5 = 4,865,609`, `v3_parity 0 differ` across `8/8` KB and `8/8` OB on `r0067`), and shrinks `B4+r0067 bench 13` by **`-11.77%`** (`557,782` vs `632,195`) and `FULL bench 13` by **`-13.34%`** (`499,211` vs `576,076`). Tree size reduction is not strength; a pre-declared `1,000g @ 50k` match (plus `6+0.06` equal-time confirmation) is still owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF20_killer_lmr_relief.patch`
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF20_killer_lmr_relief.exe` (`2,382,848` B, `SHA-256: A1A8411B1A2E3852F8E7175599DF86FE50D29CE1D92DF97615B25969D04CC7C4`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF20_killer_lmr_relief_gate.json` (`hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave3\streamA_search_packets\tests\test_sf20_killer_lmr.py`

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2413,7 +2413,11 @@
             if (gives_check) r -= 1;
             if (in_check) r -= 1;
             if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;
-            if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);
+            if (quiet) {
+                r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);
+                // Clean-room Stockfish/Stormphrax: reduce LMR by 1 ply for quiet killer moves.
+                if (move == ss->killers[0] || move == ss->killers[1]) r -= 1;
+            }
             if (tune::LmrSignedCorrection && quiet && ss->static_eval != ValueNone &&
                 ss->raw_eval != ValueNone) {
                 const int correction_cp = ss->static_eval - ss->raw_eval;
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:2416` before / `2416-2420` after):**
  1. In `Worker::search`, quiet moves tried after `move_count > 1 + (root_node ? 1 : 0)` enter LMR (`search.cpp:2405-2446`), including killer moves (`ss->killers[0]` and `ss->killers[1]`) whenever a TT move or capture precedes them (making a killer `move_count >= 2` or `>= 3`).
  2. Previously, Forge treated quiet killer moves identically to ordinary quiet moves in LMR (`r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2)`), even though killers recently produced beta cutoffs at the same ply (`update_quiet_stats`, `search.cpp:1718-1721`).
  3. `SF20` subtracts `1` from `r` when `quiet && (move == ss->killers[0] || move == ss->killers[1])`.
- **Bounds & Interaction Checks:**
  1. **Lower bound safety:** `reduced_depth = std::clamp(new_depth - r, 1, new_depth)` (`search.cpp:2426`) clamps `reduced_depth <= new_depth` even if `r <= 0`, preventing unintended search extensions. (If `LmrSignedCorrection` is off, `r < 0` still yields `reduced_depth = new_depth`.)
  2. **Interaction with `LmrDeeperShallower`:** With `LmrDeeperShallower=false` (live default), `reduced_depth < new_depth` skips re-search cleanly. With `LmrDeeperShallower=true`, fewer killers get reduced (`reduced_depth == new_depth`), so `full_depth_needed` skips `do_deeper`/`do_shallower` on those killers.
  3. **Interaction with `V3P` and `SF8`:** Zero hunk overlap (`V3P` touches `nnue_v3.*`; `SF8` touches `search.cpp:893-937, 1617-1627, 1705-1716`). Compatible with `SF20` + `proto_5` + `proto_6` (`git apply --check RC=0`).
- **Caveat 1 (No Match Played Yet):** Only deterministic gates (`perft`, `bench`, `v3_parity`) and fail-before/pass-after behavioral tests have run so far. A pre-declared `1,000g @ 50k` match (and `6+0.06` PGO confirmation if combined) is required before `GO LIVE`.
- **Caveat 2 (Non-PGO Binary):** `SF20_killer_lmr_relief.exe` is non-PGO. Rebuild with `PGO` if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room re-implementation of Stockfish / Stormphrax killer-move LMR relief (reducing LMR by 1 ply on quiet killer moves) in Forge's `SearchStack::killers` idiom (`src/search.cpp:2416-2420`).
- **License Status:** 100% clean-room implementation (`4` net C++ lines), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5e6f333b...`) | `SF20_killer_lmr_relief.exe` (`a1a8411b...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (Default & B4) | `4,865,609` | `4,865,609` | `0` (PASS) |
| Default HCE `bench 11 / 13` | `259,695 / 725,158` | `241,700 / 612,778` | `-6.93% / -15.50%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `211,634 / 557,782` | `+12.61% / -11.77%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `155,173 / 499,211` | `-28.95% / -13.34%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 200 balanced FENs, `8/8` KB, `8/8` OB) | `0/200 differ` | `0/200 differ` (planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF20_killer_lmr_relief.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave3\streamA_search_packets\tests\test_sf20_killer_lmr.py
```

Observed output:
- `test_1_isolated_killer_lmr_relief_divergence`: **PASSED** (isolated `LmrHistoryDivisor=30000`: `startpos d9` `3649 -> 4583`; `bench3 d9` `('c4d5', 5, 12242) -> ('c4b3', 29, 11875)`; `bench5 d9` `('c4d5', -324, 11215) -> ('c4d5', -327, 10202)`)
- `test_2_bench13_reduction_vs_base`: **PASSED** (`B4+r0067`: `557,782` vs `632,195`, `-11.77%`; `FULL`: `499,211` vs `576,076`, `-13.34%`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, `v3_parity 0/200`, planted bug caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave3\streamA_search_packets\tests\test_sf20_killer_lmr.py
```

Observed output (`RC=1`):
- `test_1_isolated_killer_lmr_relief_divergence`: **FAILED** (`AssertionError: 0 != 3`)
- `test_2_bench13_reduction_vs_base`: **FAILED** (`AssertionError: 0.0 not less than -0.05 ... got 632195 (+0.00%)`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (shared baseline invariants)

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:2413-2425` and `SF20_killer_lmr_relief.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`SF20_killer_lmr_relief.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_sf20_killer_lmr.py --exe <placed_exe>` and `perft_suite.py` / `v3_parity.py`.
