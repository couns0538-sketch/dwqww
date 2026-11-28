# Opus Placement Review Packet: `SF21_corrhist_gravity_clean`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Minimal `1`-line clean-room replacement of linear `std::clamp` correction-history update with Forge's `b4::gravity` saturating decay (`git apply --check RC=0`), passes all deterministic gates (`perft 5 = 4,865,609`, `v3_parity 0 differ` across `8/8` KB and `8/8` OB on `r0067`), shifts `B4+r0067 bench 13` by **`+10.69%`** (`699,746` vs `632,195`), and shrinks `FULL+r0067 bench 13` by **`-14.32%`** (`493,565` vs `576,076`) once `MaterialCorrectionWeight=48` and `NonPawnCorrection=true` are active. Node-count change is not strength; a pre-declared `1,000g @ 50k` match (plus `6+0.06` PGO confirmation if promoted) is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF21_corrhist_gravity_clean.patch` (`669` B, `11` lines, `SHA-256: 157A5407D4B029FFC967C470C3C4B8C0E3BD00986A4C27DEF1C3C7B796712A72`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF21_corrhist_gravity_clean.exe` (`2,382,848` B, `SHA-256: 9556B9C74CB495F00D8F63AE87C6855898C85DEC6683F1B859A06F59E9EFEC1F`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF21_corrhist_gravity_clean_gate.json` (`overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf21_corrhist_gravity_clean.py`

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -1477,7 +1477,7 @@
     const int diff = std::clamp((best_score - static_eval) * CorrectionGrain, -CorrectionLimit / 4, CorrectionLimit / 4);
     const int weight = std::min(depth + 1, 16);
     auto apply = [&](std::int32_t& entry) {
-        entry = std::clamp(entry + diff * weight / 256, -CorrectionLimit, CorrectionLimit);
+        entry = b4::gravity(entry, diff * weight / 256, CorrectionLimit);
     };
     apply((*correction_history_)[side][board.pawn_key() & (CorrectionSize - 1U)]);
     if (tune::MaterialCorrectionWeight > 0) apply((*material_correction_)[side][material_key(board) & (CorrectionSize - 1U)]);
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:1477-1484`):**
  1. In `Worker::update_correction`, `r15dsg` previously updated correction-history entries linearly (`std::clamp(entry + diff * weight / 256, -CorrectionLimit, CorrectionLimit)`), which causes old saturated values to resist reversal until overridden by large errors.
  2. `SF21` switches the lambda `apply` to `b4::gravity(entry, diff * weight / 256, CorrectionLimit)` (`entry + delta - entry * |delta| / CorrectionLimit`), softly decaying existing correction bias proportional to the incoming update magnitude.
  3. Because `apply` is shared across `correction_history_` (pawn key), `material_correction_` (when `MaterialCorrectionWeight > 0`, `48` in `FULL` vs `0` in `B4`/`Default`), and `non_pawn_correction_` (when `NonPawnCorrection=true` in `FULL`), `SF21` has a much stronger tree-reduction signature under `FULL` (`-14.32%`) than `B4` (`+10.69%`).
- **Bounds & Interaction Checks:**
  1. **Range safety:** `b4::gravity(..., CorrectionLimit)` keeps entries bounded within `[-CorrectionLimit, CorrectionLimit]`, matching Forge's existing B4 gravity helper.
  2. **Interaction with `V3P`, `SF8`, `SF20`, `proto_7`, `proto_8`:** Zero hunk overlap (`V3P` touches `nnue_v3.*`; `SF8` touches `893-937, 1617-1627, 1703-1713`; `SF20` touches `2416`; `proto_7` touches `123+, 204+, 2184-2188, 2409`; `proto_8` touches `148+, 220+, 2272, 2307-2313`).
- **Caveat 1 (No Match Played Yet):** Only deterministic gates (`perft`, `bench`, `v3_parity`, `eval_net_full`, `loader_safety`) and fail-before/pass-after behavioral tests have run. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (`B4` `bench 13` `+10.69%` vs `FULL` `-14.32%`):** `B4` does not enable `MaterialCorrectionWeight` or `NonPawnCorrection`; `FULL` is the intended target configuration for evaluation.
- **Caveat 3 (Non-PGO Binary):** `SF21_corrhist_gravity_clean.exe` is non-PGO. Rebuild with `PGO` if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish / B4 gravity update for static-eval correction history (`b4::gravity`, `src/search.cpp:1480`).
- **License Status:** 100% clean-room implementation (`1` net C++ line), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5e6f333b...`) | `SF21_corrhist_gravity_clean.exe` (`9556b9c7...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `272,312 / 574,546` | `-12.96% / -33.37%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `232,306 / 724,852` | `-10.55% / -0.04%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `168,487 / 699,746` | `-10.35% / +10.69%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `176,680 / 493,565` | `-19.11% / -14.32%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 200 balanced FENs, `8/8` KB, `8/8` OB) | `0/200 differ` | `0/200 differ` (planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF21_corrhist_gravity_clean.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf21_corrhist_gravity_clean.py
```

Observed output (`RC=0`):
- `test_1_patch_apply_and_divergence`: **PASSED** (`git apply --check RC=0`; `B4` `3/3` diverge including `bench5 d9` bestmove flip `c4d5 -> f1e2` (`('f1e2', -321, 13690)`); `FULL` `3/3` diverge)
- `test_2_bench13_delta_vs_base`: **PASSED** (`B4+r0067`: `699,746` vs `632,195`, `+10.69%`; `FULL+r0067`: `493,565` vs `576,076`, `-14.32%`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, `v3_parity 0/200`, planted bug caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf21_corrhist_gravity_clean.py
```

Observed output (`RC=1`):
- `test_1_patch_apply_and_divergence`: **FAILED** (`AssertionError: 0 != 3 : Expected 3 B4 divergences, got 0`)
- `test_2_bench13_delta_vs_base`: **FAILED** (`AssertionError: 632195 == 632195 : B4+r0067 bench 13 must differ from base_r15dsg`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (shared baseline invariants)

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:1477-1484` and `SF21_corrhist_gravity_clean.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`SF21_corrhist_gravity_clean.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_sf21_corrhist_gravity_clean.py --exe <placed_exe>` and `run_master_gates.py --quick`.
