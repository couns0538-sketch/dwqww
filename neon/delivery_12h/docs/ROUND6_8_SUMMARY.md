# Round 6–8 Search Packets & Wave 4 Clean-Room Prototypes Summary (`streamA_search_packets\`)

## 1. Executive Summary

Implemented, stacked, compiled (sequentially with `build_fast.py --jobs 2`, non-PGO), and master-gated (`run_master_gates.py --quick`) two new orthogonal clean-room Wave 4 search prototypes (`proto_7_ttpv_lmr_and_iir` and `proto_8_eval_lmp_and_capfut`) against `C:\nnue-lab\forge\r15dsg\`, alongside 8 Opus placement review packets and 8 fail-before/pass-after CPU pytest suites covering `SF21..SF26`, `proto_7`, and `proto_8`.

- **Zero Conflict Verified (Multi-Arg & Sequential Stack `RC=0`):** Both `proto_7_ttpv_lmr_and_iir.patch` and `proto_8_eval_lmp_and_capfut.patch` pass `git -C C:\nnue-lab\forge\r15dsg apply --check` (`RC=0`) individually **and** together with `V3P_pairwise_psqt_fused.patch`, `SF8_conthist_6ply.patch`, and `SF20_killer_lmr_relief.patch` (`MULTI_CHECK_RC=0`), **and** apply sequentially (`git apply`, 5/5 `RC=0`) onto a clean copy of `r15dsg` and compile cleanly (`build_fast.py --jobs 2`, `6.1s`).
- **Sequential Overlap Warnings Documented (`SF22` & `SF23`):** `git apply --check p1 p2` checks each patch independently against the unchanged `r15dsg` tree rather than sequentially in memory. Direct line inspection shows `SF22_low_ply_history.patch` overlaps `SF8_conthist_6ply.patch` at `src/search.cpp:893, 907, 933, 1620`, and `SF23_capture_hist_badcap_lmr.patch` overlaps `SF20_killer_lmr_relief.patch` at `src/search.cpp:2416`. Both are explicitly flagged in `packet_SF22` and `packet_SF23` for manual merge if stacked with `SF8`/`SF20`.
- **All Deterministic Gates Pass:** Both `proto_7` and `proto_8` pass `run_master_gates.py --quick` (`PASS_WITH_ADVISORY_FLAGS`, `hard_pass: true`, `perft 6/6` with `perft 5 = 4,865,609`, `v3_parity 0/120` + `0/200` across `8/8` KB and `8/8` OB on `r0067` with planted bug caught, `eval_net_full` PASS, `loader_safety 13/13`), with `=0` UCI ablation bit-identical to `base_r15dsg.exe` and `B4+r0067` / `FULL+r0067` `bench 13` deltas inside `[-25%, +10%]`.
- **Standalone Pytest Suite (`pytest -B -p no:cacheprovider`):** **`24 passed in 60.24s`** (`RC=0`) against target executables (`FORGE_TEST_EXE=""`); **`16 failed, 8 passed in 48.32s`** (`RC=1`) against `base_r15dsg.exe` (all 16 feature/behavioral/UCI/bench assertions fail on base while all 8 shared baseline invariant checks pass).

---

## 2. Prototype & Round 6–8 Designs, Patch Stats & Compatibility

### 2.1 Wave 4 Prototypes (`streamA_search_packets\patches\` & `builds\`)

#### `proto_7_ttpv_lmr_and_iir`
- **Patch:** `patches\proto_7_ttpv_lmr_and_iir.patch` (`75` lines, `4,172` B, `SHA-256: 6F08B20178DEF1D47C4C5C40CD1FD983426331D7D64A8B02CC86835DD9CB7BCB`)
- **Binary:** `builds\proto_7_ttpv_lmr_and_iir.exe` (`2,383,360` B, `SHA-256: A37BC49D7D61A74913B661DC34C0C6B19DF68481840D2217F66BCE57422AFB31`, built in `5.8s`)
- **Gate JSON:** `builds\proto_7_gate.json` (`8,916` B, `SHA-256: 98A2C0F1F37804CF8E24ADE78EF428948AA6CFC95C1F6FC37112D7164F9B25CE`, `hard_pass: true`)
- **Clean-Room Inspiration:** Stockfish `tt_pv` LMR score/depth gating, upper-bound non-`tt_pv` cut-node tightening, and deeper non-`tt_pv` non-TT-move IIR.
- **UCI Gate:** `option name TtPvLmrIirRefine type spin default 1 min 0 max 1` (via `tune::parameters()`). `TtPvLmrIirRefine=0` reproduces `base_r15dsg.exe` bit-identically (`B4`: `187,930 / 632,195`; `FULL`: `218,410 / 576,076`).
- **Exact Hunks (`C:\nnue-lab\forge\r15dsg\`):**
  - `include/forge/search.hpp:274+` (`extern int TtPvLmrIirRefine`)
  - `src/search.cpp:123+, 204+` (definition & `tune::parameters()`)
  - `src/search.cpp:2184-2188` (IIR on non-`tt_pv` ALL-nodes at `depth >= IirDepth + 2` and second `-1` ply on non-`tt_pv` cut nodes at `depth >= IirDepth + 3`, preserving `tt_prune_v2_` `else if`)
  - `src/search.cpp:2409` (replaces ONLY `if (ss->tt_pv) r -= 1;`, keeping `2410-2412` untouched as a clean buffer before `SF20`'s `2413-2419`)

#### `proto_8_eval_lmp_and_capfut`
- **Patch:** `patches\proto_8_eval_lmp_and_capfut.patch` (`71` lines, `4,958` B, `SHA-256: 1862CEA0B89387BE43BEF0A74BE9CDA2BBF2A41AB6E3921406F93B385E62AF63`)
- **Binary:** `builds\proto_8_eval_lmp_and_capfut.exe` (`2,382,848` B, `SHA-256: B0AADE3D8132957F4215B2408E79AA66E7569554B722EC82409011B70D6E5C22`, built in `5.9s`)
- **Gate JSON:** `builds\proto_8_gate.json` (`8,909` B, `SHA-256: 4BD548CD7C63380763553CAD1F362FECDDDCD63F584218B361063D4C769789D7`, `hard_pass: true`)
- **Clean-Room Inspiration:** Stockfish / Stormphrax eval-margin LMP tightening (`3/4` when `static_eval + 120 + 60*depth <= alpha`, `depth <= 6`, `!in_check`, `!is_mate_score(alpha)`) and improving-aware capture futility (`+/-35` cp when `CaptureFutilityBase > 0`, and non-improving `40 + 180*lmr_depth` at `lmr_depth <= 3` when `CaptureFutilityBase == 0`).
- **UCI Gate:** `option name EvalLmpRefine type spin default 1 min 0 max 1` (via `tune::parameters()`). `EvalLmpRefine=0` reproduces `base_r15dsg.exe` bit-identically (`B4`: `187,930 / 632,195`; `FULL`: `218,410 / 576,076`).
- **Exact Hunks (`C:\nnue-lab\forge\r15dsg\`):**
  - `include/forge/search.hpp:300+` (`extern int EvalLmpRefine`)
  - `src/search.cpp:148+, 220+` (definition & `tune::parameters()`)
  - `src/search.cpp:2272` (eval-margin LMP tightening)
  - `src/search.cpp:2307-2313` (improving-aware capture futility)

### 2.2 Round 6–8 Patches (`C:\nnue-lab\neon\forge_fixes\{patches,builds}\`) & Stack Compatibility

| Patch | Bytes / Lines | `git apply --check` vs `r15dsg` | Stack Compatibility Notes (`V3P + SF8 + SF20 + proto_7 + proto_8`) |
|---|---:|---|---|
| `SF21_corrhist_gravity_clean.patch` | `669` B / `11` | `RC=0` | Clean (`search.cpp:1477-1484`, zero overlap) |
| `SF22_low_ply_history.patch` | `4,599` B / `86` | `RC=0` | **Overlaps `SF8_conthist_6ply.patch`** at `search.cpp:893, 907, 933, 1620` (manual merge required if stacked with `SF8`) |
| `SF23_capture_hist_badcap_lmr.patch` | `1,912` B / `36` | `RC=0` | **Overlaps `SF20_killer_lmr_relief.patch`** at `search.cpp:2416` (manual merge required if stacked with `SF20`) |
| `SF24_qs_evasion_pruning.patch` | `1,693` B / `29` | `RC=0` | Clean (`search.cpp:1847-1859`, zero overlap) |
| `SF25_faillow_prior_move_hist.patch` | `2,168` B / `34` | `RC=0` | Clean (`search.cpp:2507-2515`, zero overlap) |
| `SF26_cutoff_surprise_hist_depth.patch` | `1,118` B / `18` | `RC=0` | Clean (`search.cpp:2491-2498`, zero overlap) |
| `proto_7_ttpv_lmr_and_iir.patch` | `4,172` B / `75` | `RC=0` | **Verified sequential stack `RC=0` + clean compile** (`V3P_fused + SF8 + SF20 + proto_7 + proto_8`) |
| `proto_8_eval_lmp_and_capfut.patch` | `4,958` B / `71` | `RC=0` | **Verified sequential stack `RC=0` + clean compile** (`V3P_fused + SF8 + SF20 + proto_7 + proto_8`) |

---

## 3. Exact Deterministic Gate & `bench 11/13` Matrix

All checks run single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Engine | `perft 5` / `r0067 eval` | `v3_parity` (`200` FENs, `8/8` KB & OB) | HCE Default `b11 / b13` (`Δ13`) | `r0067` Default `b11 / b13` (`Δ13`) | `B4+r0067` `b11 / b13` (`Δ13`) | `FULL+r0067` `b11 / b13` (`Δ13`) |
|---|---:|---|---|---|---|---|
| `base_r15dsg.exe` | `4,865,609` / `87` | `0/200` | `312,866 / 862,329` (`+0.00%`) | `259,695 / 725,158` (`+0.00%`) | `187,930 / 632,195` (`+0.00%`) | `218,410 / 576,076` (`+0.00%`) |
| `SF21_corrhist_gravity_clean.exe` | `4,865,609` / `87` | `0/200` (fault caught) | `272,312 / 574,546` (`-33.37%`) | `232,306 / 724,852` (`-0.04%`) | `168,487 / 699,746` (`+10.69%`) | `176,680 / 493,565` (`-14.32%`) |
| `SF22_low_ply_history.exe` | `4,865,609` / `87` | `0/200` (fault caught) | `290,403 / 925,813` (`+7.36%`) | `272,131 / 613,455` (`-15.40%`) | `171,693 / 703,535` (`+11.28%`) | `193,168 / 640,887` (`+11.25%`) |
| `SF23_capture_hist_badcap_lmr.exe` | `4,865,609` / `87` | `0/200` (fault caught) | `326,654 / 847,444` (`-1.73%`) | `256,095 / 832,227` (`+14.76%`) | `192,084 / 751,693` (`+18.90%`) | `224,965 / 627,372` (`+8.90%`) |
| `SF24_qs_evasion_pruning.exe` | `4,865,609` / `87` | `0/200` (fault caught) | `370,523 / 826,673` (`-4.13%`) | `231,693 / 677,083` (`-6.63%`) | `178,890 / 650,576` (`+2.91%`) | `168,361 / 592,974` (`+2.93%`) |
| `SF25_faillow_prior_move_hist.exe` | `4,865,609` / `87` | `0/200` (fault caught) | `334,674 / 877,771` (`+1.79%`) | `275,219 / 717,731` (`-1.02%`) | `245,237 / 688,554` (`+8.91%`) | `203,215 / 578,851` (`+0.48%`) |
| `SF26_cutoff_surprise_hist_depth.exe` | `4,865,609` / `87` | `0/200` (fault caught) | `331,288 / 802,501` (`-6.94%`) | `273,822 / 712,399` (`-1.76%`) | `199,086 / 620,806` (`-1.80%`) | `193,418 / 501,280` (`-12.98%`) |
| `proto_7_ttpv_lmr_and_iir.exe` | `4,865,609` / `87` | `0/200` (fault caught) | `292,457 / 649,751` (`-24.65%`) | `260,150 / 651,160` (`-10.20%`) | `183,614 / 475,386` (**`-24.80%`**) | `210,039 / 438,736` (**`-23.84%`**) |
| `proto_8_eval_lmp_and_capfut.exe` | `4,865,609` / `87` | `0/200` (fault caught) | `297,435 / 904,823` (`+4.93%`) | `275,663 / 725,537` (`+0.05%`) | `187,255 / 639,724` (**`+1.19%`**) | `218,657 / 567,725` (**`-1.45%`**) |

- **Ablation (`option=0`) for `proto_7` & `proto_8`:** Both reproduce `base_r15dsg.exe` bit-identically (`B4`: `187,930 / 632,195`; `FULL`: `218,410 / 576,076`).

---

## 4. Exact Pytest Fail-Before / Pass-After Outputs

Command (run with `HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`):

1. **Target Exes (`FORGE_TEST_EXE=""`):**
   ```powershell
   C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests
   ```
   Raw result: **`24 passed in 60.24s`** (`PASS_AFTER_RC=0`), covering `3/3` tests across all 8 files (`test_proto_7`, `test_proto_8`, `test_sf21..26`).

2. **Base Exe (`FORGE_TEST_EXE=C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe`):**
   Raw result: **`16 failed, 8 passed in 48.32s`** (`FAIL_BEFORE_RC=1`):
   - Failed all 16 behavioral / UCI-option / `bench 13` assertions (`test_1` & `test_2` across all 8 files).
   - Passed all 8 shared invariant assertions (`test_3`: `perft 5 = 4,865,609` on Default/B4/FULL, `r0067 startpos eval = 87`, `v3_parity 0/200` + planted bug caught).

---

## 5. Ready-to-Run `50k` Screening Match Commands (For Main Neon Session)

```powershell
# Proto 7: tt_pv LMR refinement + deeper non-TT-move IIR
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\run_net_match.py --name proto_7_ttpv_lmr_and_iir_vs_base_1000g_50k --cand-exe C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\builds\proto_7_ttpv_lmr_and_iir.exe --base-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe --cand-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --base-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --games 1000 --nodes 50000 --concurrency 6 --seed 202611407

# Proto 8: Eval-margin LMP tightening + improving-aware capture futility
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\run_net_match.py --name proto_8_eval_lmp_and_capfut_vs_base_1000g_50k --cand-exe C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\builds\proto_8_eval_lmp_and_capfut.exe --base-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe --cand-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --base-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --games 1000 --nodes 50000 --concurrency 6 --seed 202611408
```

*(Note: Both `builds\proto_7_ttpv_lmr_and_iir.exe` and `builds\proto_8_eval_lmp_and_capfut.exe` are non-PGO builds for fixed-node `50k` screening vs non-PGO `base_r15dsg.exe`; rebuild any winner with PGO before `6+0.06` clock confirmation.)*
