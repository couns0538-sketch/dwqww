# Round 5–6 Clean-Room Search Prototypes Summary (`streamA_search_packets\`)

## 1. Executive Summary

Implemented, stacked, compiled (sequentially, `<= 2` threads, `-Wl,--thinlto-jobs=2`, non-PGO), and gated two orthogonal clean-room Round 5–6 search prototypes against `C:\nnue-lab\forge\r15dsg\`, plus fail-before/pass-after test suites and Opus placement review packets for `SF20_killer_lmr_relief`, `SF17_tm_bestmove_avg_eval` & `SF18_tm_ply_curve`, and `LmrDeeperShallower=true`.

- **Zero Conflict Verified (`git apply` stack check `RC=0`):** Both `proto_5_hist_malus_lmp.patch` and `proto_6_nmp_probcut_refine.patch` apply cleanly on `C:\nnue-lab\forge\r15dsg\` (`RC=0`) **and** apply cleanly together in a combined temp copy alongside `V3P_pairwise_psqt.patch`, `SF8_conthist_6ply.patch`, and `SF20_killer_lmr_relief.patch` (`5/5` patches, `RC=0`).
- **All Deterministic Gates Pass:** Both prototypes pass `perft 5 = 4,865,609`, `6/6` fast `perft_suite` positions, `v3_parity` (`0` diff across `8/8` king buckets & `8/8` output buckets on `r0067` + planted bug caught), `r0067 startpos eval = 87`, and `B4/FULL bench 13` within `[-25%, +10%]` vs `base_r15dsg.exe`.
- **Standalone Pytest Suite (`pytest -B -p no:cacheprovider`):** **`12/12 PASSED`** (`RC=0`) against target executables; **`8 FAILED, 4 PASSED`** (`RC=1`) against `base_r15dsg.exe` (all 8 feature/behavioral assertions fail on base while shared baseline invariants hold).
- **Footprint & Clean Exit:** Total `streamA_search_packets\` size is `~4.65 MiB` (`~4.88 MB`), with zero `_work_*`, `.o`, `.obj`, `__pycache__`, `.pytest_cache`, `.pyc`, or `.part` files remaining.

---

## 2. Prototype Designs, Patch Stats & Compatibility

### 2.1 `proto_5_hist_malus_lmp` (`patches\proto_5_hist_malus_lmp.patch`)
- **Stats:** `116` diff lines (`6,149` B, `SHA-256: C4D9336F1E347894056269CF7418520E65304CA874FFCEC62C5D303044CF8BE8`).
- **Binary:** `builds\proto_5_hist_malus_lmp.exe` (`2,383,360` B, `SHA-256: 092D587EC350998E9C6663FE9307C9DDF2D39EABD2AEBFC52AF0C92E30B74E48`, built in `6.7s`).
- **Clean-Room Inspiration:** Stockfish / Stormphrax asymmetric quiet history bonus vs malus scaling and cut-node-aware LMP scaling.
- **UCI Gate:** `option name HistMalusLmpRefine type spin default 1 min 0 max 1` (via `tune::parameters()`). Setting `HistMalusLmpRefine=0` reproduces `base_r15dsg.exe` bit-identically (`B4`: `187,930 / 632,195`; `FULL`: `218,410 / 576,076`).
- **Exact Hunks (`C:\nnue-lab\forge\r15dsg\`):**
  - `include/forge/search.hpp`: lines `283` (`extern int HistMalusLmpRefine`), `592` (`update_rework_history(..., int bonus, int malus, ...)`).
  - `src/search.cpp`:
    - lines `132` (`int HistMalusLmpRefine = 1`), `211` (`tune::parameters()` registration);
    - lines `322-344`: `lmp_threshold(depth, improving, cut_node)` tightens LMP on non-PV `cut_node` (`thresh = std::max(2, thresh * 3 / 4)`) while keeping `improving` scaling (`base` vs `base / 2`), and `history_malus(depth) = std::min(HistoryBonusMax * 3 / 4, HistoryBonusQuadratic * depth^2 * 2 / 3 + HistoryBonusLinear * depth * 3 / 4)`;
    - lines `1662-1669`, `1747-1762`: `Worker::update_quiet_stats` and `Worker::update_rework_history` apply `-malus` to failed quiet moves across `main_history_`, `threat_quiet`, `pawn_history`, `update_continuation`, and `B4` `rework_history_` while preserving `+bonus` for the cutoff move (20 lines clear of `SF8`'s `1705-1713` hunk);
    - line `2287`: passes `!pv_node && cut_node` to `lmp_threshold(depth, improving, !pv_node && cut_node)`.

### 2.2 `proto_6_nmp_probcut_refine` (`patches\proto_6_nmp_probcut_refine.patch`)
- **Stats:** `88` diff lines (`5,357` B, `SHA-256: 9A7A0BF51B9548F07BA4EE670B6353FD02E053F2686ED2129F248A5478A4B824`).
- **Binary:** `builds\proto_6_nmp_probcut_refine.exe` (`2,383,360` B, `SHA-256: C621D88819447E901781D2E6811B14F3BA53B97DEAD19ADA5FA4041DFD5C00C8`, built in `6.5s`).
- **Clean-Room Inspiration:** Stockfish / Viridithas NMP eval-excess cap + ProbCut TT-fail guard and depth/capture refinement.
- **UCI Gate:** `option name NmpProbcutRefine type spin default 1 min 0 max 1` (via `tune::parameters()`). Setting `NmpProbcutRefine=0` reproduces `base_r15dsg.exe` bit-identically (`B4`: `187,930 / 632,195`; `FULL`: `218,410 / 576,076`).
- **Exact Hunks (`C:\nnue-lab\forge\r15dsg\`):**
  - `include/forge/search.hpp`: line `258` (`extern int NmpProbcutRefine`).
  - `src/search.cpp`:
    - lines `107` (`int NmpProbcutRefine = 1`), `195` (`tune::parameters()` registration);
    - lines `2103-2107` (NMP): caps NMP eval-excess reduction contribution at `2` plies (vs `3`) and adds `+ (!improving ? 1 : 0)` to `reduction`;
    - lines `2152-2196` (ProbCut): fixes `probcut_tt_fail` to require `tt_bound != BoundLower` (so a `BoundLower` TT entry below `probcut_beta` no longer falsely suppresses ProbCut), bounds ProbCut capture trials to `probcut_max = 2 + 2 * static_cast<int>(cut_node)`, clamps `pc_depth = std::max(1, depth - 4)`, and stores `pc_store_depth = pc_depth + 1`.

---

## 3. Exact Deterministic Gate & `bench 11/13` Matrix

All checks run single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` | `proto_5_hist_malus_lmp.exe` | `proto_6_nmp_probcut_refine.exe` | Gate Requirement |
|---|---:|---:|---:|---|
| `git apply --check` vs `r15dsg` | — | `RC=0` | `RC=0` | `RC=0` |
| `git apply` stack (`V3P+SF8+SF20+P5+P6`) | — | `RC=0` | `RC=0` | Zero conflict |
| `go perft 5` (`startpos`) | `4,865,609` | `4,865,609` | `4,865,609` | `4,865,609` |
| `run_master_gates --quick` `perft` (`6/6`) | PASS | PASS (`6/6`) | PASS (`6/6`) | PASS |
| `r0067 startpos eval` | `87` | `87` | `87` | `87` |
| `v3_parity.py <exe> cand.fnn3 200 0` | `0/200 differ` | `0/200 differ` (`PASS`, `RC=0`) | `0/200 differ` (`PASS`, `RC=0`) | `0` diff `8/8` KB & `8/8` OB |
| `v3_parity.py <exe> cand.fnn3 200 1` (planted) | — | `15 differ` (`RC=0`, caught) | `15 differ` (`RC=0`, caught) | Planted fault caught |
| `run_master_gates --quick` `v3_parity` (`120` FENs) | `0 differ` | `0 differ` (`8/8` OB, PASS) | `0 differ` (`8/8` OB, PASS) | PASS |
| HCE Default `bench 11 / 13` | `312,866 / 862,329` | `316,914 / 845,351` (`-1.97%`) | `336,219 / 868,877` (`+0.76%`) | — |
| `r0067` Default `bench 11 / 13` | `259,695 / 725,158` | `289,844 / 904,042` (`+24.67%`) | `255,346 / 644,060` (`-11.18%`) | — |
| `B4+r0067 bench 11 / 13` | `187,930 / 632,195` | `255,982 / 684,792` (**`+8.32%`**) | `208,355 / 675,077` (**`+6.78%`**) | `[-25%, +10%]` **PASS** |
| `FULL+r0067 bench 11 / 13` | `218,410 / 576,076` | `213,698 / 566,371` (**`-1.68%`**) | `210,871 / 447,654` (**`-22.29%`**) | `[-25%, +10%]` **PASS** |
| `FULL+DS bench 11 / 13` | `225,025 / 533,003` | `203,844 / 583,164` (`+9.41%`) | `255,227 / 493,619` (`-7.39%`) | — |
| Ablation (`option=0`) `B4` / `FULL` | `187,930 / 632,195` \| `218,410 / 576,076` | `187,930 / 632,195` \| `218,410 / 576,076` | `187,930 / 632,195` \| `218,410 / 576,076` | Bit-exact `0` diff |

---

## 4. Exact Pytest Fail-Before / Pass-After Outputs

Command (run with `HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`):

1. **Target Exes (`FORGE_TEST_EXE=""`):**
   ```powershell
   C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave3\streamA_search_packets\tests
   ```
   Raw result: **`12 passed in 34.19s`** (`ALL_TARGET_RC=0`), covering:
   - `test_proto_5_hist_malus_lmp.py` (`3/3 PASSED`)
   - `test_proto_6_nmp_probcut_refine.py` (`3/3 PASSED`)
   - `test_sf17_sf18_tm.py` (`3/3 PASSED`)
   - `test_sf20_killer_lmr.py` (`3/3 PASSED`)

2. **Base Exe (`FORGE_TEST_EXE=C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe`):**
   Raw result: **`8 failed, 4 passed in 25.22s`** (`ALL_BASE_RC=1`):
   - Failed all 8 feature/divergence tests: `test_proto_5_hist_malus_lmp` (`test_1`, `test_2`), `test_proto_6_nmp_probcut_refine` (`test_1`, `test_2`), `test_sf17_sf18_tm` (`test_2`, `test_3`), `test_sf20_killer_lmr` (`test_1`, `test_2`).
   - Passed the 4 shared invariants (`perft 5`, `r0067 eval`, `v3_parity`, and `4/4` fixed-depth `bench` identity).

---

## 5. Ready-to-Run `50k` Screening Match Commands (For Main Neon Session)

```powershell
# Proto 5: Asymmetric quiet malus + cut-node LMP scaling
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\run_net_match.py --name proto_5_hist_malus_lmp_vs_base_1000g_50k --cand-exe C:\nnue-lab\neon\forge_fixes\teamwork_wave3\streamA_search_packets\builds\proto_5_hist_malus_lmp.exe --base-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe --cand-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --base-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --games 1000 --nodes 50000 --concurrency 6 --seed 202611325

# Proto 6: NMP eval-excess cap + ProbCut TT-fail guard & depth refinement
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\run_net_match.py --name proto_6_nmp_probcut_refine_vs_base_1000g_50k --cand-exe C:\nnue-lab\neon\forge_fixes\teamwork_wave3\streamA_search_packets\builds\proto_6_nmp_probcut_refine.exe --base-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe --cand-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --base-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --games 1000 --nodes 50000 --concurrency 6 --seed 202611326
```

*(Note: Both `builds\proto_5_hist_malus_lmp.exe` and `builds\proto_6_nmp_probcut_refine.exe` are non-PGO builds for fixed-node `50k` screening vs non-PGO `base_r15dsg.exe`; rebuild any winner with PGO before `6+0.06` clock confirmation.)*
