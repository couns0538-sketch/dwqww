# Owner's Bundle Pre-Match Forensic Technical Dossier (`OPUS-2811-OWNER-BUNDLE-TEST`)

**Status:** **PRE-MATCH FORENSIC DOSSIER** (verified against on-disk artifacts prior to Arm A and Arm B execution; `clean_idle_nps: null` in `OWNER_BUNDLE_DECLARATION.json`, and `OWNER_BUNDLE_RESULTS.json` is pending 100% idle GPU+CPU execution).  
**Declaration Reference:** `OPUS-2811-OWNER-BUNDLE-TEST (01:18 PC)` & `OPUS-2811-BUNDLE-EXE-CHECKED (01:36 PC)`  
**Integrity Rule (R5) & `OPUS-2811-OLS-CAUTION`:** Training loss, validation MSE, M4/SF19 scorecards, and OLS material values are strictly diagnostic leads — never Elo claims. Scale-free OLS ratios (`Q/P`, `R/P`) or net-unit cp (`u = (S6_Q+S6_R+S6_B+S6_N)/20`) are quoted when comparing nets. Match scales (`600g @ 50k` screens, `1,000g @ 50k` confirmations, `250k` node matches, and `2,000g @ 6+0.06` clock runs) are kept strictly separated and never pooled.

---

## 1. Executive Summary, SHA-256 Registry & Pre-Match Gates

The Owner's Bundle test (`C:\nnue-lab\neon\forge_fixes\run_owner_bundle_clock_test.py`) evaluates the combined search-and-NNUE candidate (`FORGE_OWNER_BUNDLE_PGO.exe`) built from `C:\nnue-lab\forge\r15dsg` plus **4 verified patches (`52` hunks across `4` files)** and UCI flag `LmrDeeperShallower=true` against the live engine (`v3-r15dsg-sp-clang\forge.exe`) and live best `768w` net (`r0067`).

### 1.1 Exact Artifact & SHA-256 Registry (`OWNER_BUNDLE_DECLARATION.json`)

Every SHA-256 digest and byte size below is verified directly against `C:\nnue-lab\neon\forge_fixes\OWNER_BUNDLE_DECLARATION.json` (`written: 2026-11-28 01:34:29`, `126` lines, `4,705` B) and on-disk files:

| Artifact Role | Exact Path on Disk | Size (Bytes) | Verified SHA-256 |
|---|---|---:|---|
| `bundle_exe` | `C:\nnue-lab\neon\forge_fixes\builds\FORGE_OWNER_BUNDLE_PGO.exe` | 2,447,872 | `95d0608e1a6c4c4ba6606a6ba2a8e4562280f71129b33d5d71f65b7e3c8941b0` |
| `bundle_patch` | `C:\nnue-lab\neon\forge_fixes\patches\FORGE_OWNER_BUNDLE_PGO.patch` | 54,707 | `f441957d44396bd022bbdb0dc723416af23d0921c5230d3aa3926431bccff0d8` |
| `live_pgo_exe` | `C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe` | 2,390,528 | `cef2f21589102392fdd7e3cbde74bfd01baa94f9677a2be33365f68e4bceb03d` |
| `g3_net` (`1024p/kb8`) | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\cand.fnn3` | 12,798,184 | `7ff7789032491aa732846db17ad24ec7fc95c6cb9ad177490f5a06fcccbb9763` |
| `r0067_net` (`768w`) | `C:\nnue-lab\runs\forge\r0067\train\cand.fnn3` | 9,463,528 | `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28` |
| `patches_included[0]` | `C:\nnue-lab\neon\forge_fixes\patches\V3P_pairwise_psqt_fused_v3.patch` | 43,075 | `57f3455f185463cfa7859727da9c6a91bcaadb3934da4492a6e78029dcaac763` |
| `patches_included[1]` | `C:\nnue-lab\neon\forge_fixes\patches\SF13_qs_evasion_pruning.patch` | 1,584 | `63eb3288af4712a7d641035177e561448e6fc94041d8ee916776ab3fced6b6e4` |
| `patches_included[2]` | `C:\nnue-lab\neon\forge_fixes\patches\SF8_conthist_6ply.patch` | 3,155 | `62dcf1f3da0ac212a3807e59eb61e144b3705ea2a8a716b70a391e81af4c8779` |
| `patches_included[3]` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamA_search\patches\proto_1_corrhist_minor.patch` | 7,602 | `e1cd152b4d78cd7880f55dd8967eb561fe246fe5773232ce22825df5b2071b14` |
| Prior `FORGE_FINAL_G3_PGO.exe` *(superseded for bundle)* | `C:\nnue-lab\neon\forge_fixes\builds\FORGE_FINAL_G3_PGO.exe` | 2,438,144 | `f8dcc4a2f42aead08d1174118b0f2d9d8f0d246ddfe96f068b32e74d5fbe3082` |

*Hash Reconciliation Note:* `NEON_TO_OPUS.md:850` contained a truncated typo (`34d2248d...`) for `r0067/train/cand.fnn3`; `OWNER_BUNDLE_DECLARATION.json:14`, `HANDOFF_12H_DATA_QUALITY.md:11`, and direct SHA-256 computation on disk all confirm `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`.

---

## 2. Dual-Net Clang ThinLTO+PGO Rationale & Independent Gate Verification

### 2.1 Fixing the `-4.52%` Cold-768w Penalty on `FORGE_FINAL_G3_PGO.exe`

The earlier `FORGE_FINAL_G3_PGO.exe` binary (`compose_winner_pgo.py --pgo-net`) was PGO-profiled single-net on `G3_FULL25` (`1024w` Pairwise+PSQT) only. Clean GPU+CPU-idle `bench 15` measurements across 5 interleaved rounds with all 45 live `v3_uci_options` (`C:\nnue-lab\neon\forge_fixes\CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json`) showed:

| Binary / Net Configuration | Nodes (d15) | Median NPS | Ratio vs Live `r0067` | Notes |
|---|---:|---:|---:|---|
| `live_pgo_r0067_768screlu` (`forge.exe`) | 1,373,184 | 3,613,642.0 | `1.0000x` | Live PGO baseline |
| `v3p_pgo_r0067_768screlu` (`FORGE_FINAL_G3_PGO.exe`) | 1,373,184 | 3,450,211.0 | `0.9548x` | **`-4.52%` cold-768w branch penalty** |
| `v3p_pgo_768p_kb8` | 1,782,594 | 3,047,169.0 | `0.8432x` | Server-Day 768p candidate |
| `v3p_pgo_1024p_kb8_G3` (`G3_FULL25`) | 869,964 | 2,959,061.0 | `0.8189x` | `0.8337x–0.8395x` (`3.02–3.04M` in `CLEAN_IDLE_SPEED_2BUILDS.json`) |
| `v3p_pgo_1024p_kb16` | 1,529,307 | 2,940,975.0 | `0.8139x` | Only `-0.6%` vs `kb8` (`2.96M`) |
| `v3p_pgo_1536p_kb8` | 1,409,543 | 2,664,542.0 | `0.7374x` | Wide 1536p Server-Day candidate |

Because Opus (`OPUS-2811-CLOCK-RECOUNTED-AND-R1-TWIN`, `OPUS_TO_NEON.md:3014`) flagged the `0.955x` penalty on `768w`, `FORGE_OWNER_BUNDLE_PGO.exe` uses **Dual-Net Clang ThinLTO+PGO** (`run_owner_bundle_clock_test.py:138-166`):
1. Compiles instrumented binary (`-fprofile-instr-generate`, `-std=c++20 -O3 -march=znver5 -flto=thin -fuse-ld=lld -ffp-contract=off -fno-fast-math`).
2. Runs **two** PGO profile passes with `NNUEArch=true`, `MateAlphaGuard=true`, all `45` live `v3_uci_options`, and `LmrDeeperShallower=true`:
   - `G3_FULL25` at `bench 11 / 13 / 16` (`forge_g3.profraw`)
   - `r0067` at `bench 11 / 13 / 15` (`forge_r0067.profraw`)
3. Merges both `.profraw` profiles with `llvm-profdata.exe merge` and relinks with `-fprofile-instr-use=forge_dual.profdata`. This keeps both `G3_FULL25` (Arm A) and `r0067` (Arm B) PGO-hot. *(Clean 3x idle `bench 13` NPS comparison on `FORGE_OWNER_BUNDLE_PGO.exe` runs immediately before Arm A when GPU+CPU are idle.)*

### 2.2 Opus Independent `gates_exe.py` vs Neon Declaration & Master Gates

Opus independently verified both `FORGE_FINAL_G3_PGO.exe` and `FORGE_OWNER_BUNDLE_PGO.exe` using `C:\nnue-lab\tmp\opus_scratch\neon_check\gates_exe.py` (`OPUS_TO_NEON.md:3028-3032, 3043-3047`):

1. **`FORGE_FINAL_G3_PGO.exe` (`f8dcc4a2...`, prior clock test):**
   - `perft 5 = 4865609`; built-in `bench 11/13 = 312,866 / 862,329`; `r0067` + 4 B4 opts `bench 11/13 = 187,930 / 632,195` — identical to live `v3-r15dsg-sp-clang/forge.exe`, confirming **zero** search changes were active in `G3_FULL25_PGO_vs_live_r0067_2000g_6p006`.
2. **`FORGE_OWNER_BUNDLE_PGO.exe` (`95d0608e1a6c4c4b...`):**
   - `perft 5 = 4865609`; built-in `bench 11/13 = 313,265 / 773,794` (exact match between Opus `gates_exe.py` and `OWNER_BUNDLE_DECLARATION.json:55-65`).
   - Opus 4-B4-opt (`CuckooRep`, `HistRework 2`, `TtPruneV2`, `CorrHistV2`) `r0067` `bench 11/13 = 240,329 / 656,210` (matches `FORGE_OWNER_BUNDLE_PGO_gate_r0067_quick.json:88-99`).
   - Neon 45-opt live `v3_uci_options` `r0067` `bench 11/13 = 209,374 / 493,972` (`OWNER_BUNDLE_DECLARATION.json:67-78`) — reconciled cleanly in `OPUS_TO_NEON.md:3046` because 4 opts vs 45 opts differ by design.
   - Neon 45-opt + `LmrDeeperShallower=true`: `r0067` `bench 11/13 = 223,638 / 528,382`; `G3_FULL25` `bench 11/13 = 222,600 / 419,338` (`OWNER_BUNDLE_DECLARATION.json:79-101`).

### 2.3 Master Gates, `VERIFY=1`, UBSan, & Multithread Proofs

| Verification Gate / Proof | File on Disk | Verified Results |
|---|---|---|
| Quick Gate (`r0067`) | `builds\FORGE_OWNER_BUNDLE_PGO_gate_r0067_quick.json` | `hard_pass = true` (`6.5715s`); `perft 6/6` (`perft 5 = 4865609`); `v3_parity` `120` FENs `max_diff_cp = 0`; `loader_safety` **`15/15` PASS** (`missing_file`, `empty_0B`, `trunc_7B`, `trunc_192B`, `trunc_minus1B`, `trailing_plus4B`, `bad_magic`, `bad_version`, `unknown_flag`, `bad_checksum`, `residual_refused`, `oob_w2_128`, `oob_acc_32768`, `pairwise_h32`, `oob_psqt_261121`) |
| Full Gate (`G3_FULL25`) | `builds\FORGE_OWNER_BUNDLE_PGO_gate_g3_full.json` | `hard_pass = true` (`24.0907s`); `perft 12/12` (`perft 5 = 4865609`); `v3_parity` `1,120` FENs `max_diff_cp = 0`, `ob_covered = "8/8"`; `loader_safety` **`37/37` PASS** + `uci_multi_net_switching.ok = true` |
| Incremental `VERIFY=1` | `V3P_FUSED_V3_VERIFY_PROOF.json` | `-DFORGE_NNUE_V3_VERIFY=1`: **`448,340` nodes verified, `0` verify failures** (`G3_FULL25_e12_1024w_kb8`: `230,952`; `r0067_legacy_768w_screlu`: `172,811`; `syn_1536w_kb8_pairwise_psqt`: `23,873`; `syn_1024w_kb16_pairwise_psqt`: `20,704`) |
| UBSan Stack Proof | `UBSAN_STACK_PROOF.json` | `STACK_V3Pv3_SF13_SF8_W2P1.patch` (byte-identical to `FORGE_OWNER_BUNDLE_PGO.patch`), `-O1 -g -fsanitize=undefined -fno-sanitize-recover=all`, `bench 10`, `14.4s`, **`ubsan_all_clean: true`** on both `G3_e12_1024w_pairwise_psqt` and `r0067_768w_legacy_screlu` |
| Multithread Stress | `MULTITHREAD_STRESS_PROOF.json` | `60/60` mates (`t4_stop_ms = 0.0`) |

---

## 3. Experimental Design — Arm A vs Arm B (`2,000g @ 6+0.06`, `concurrency=7`)

In the earlier `G3_FULL25_PGO_vs_live_r0067_2000g_6p006` equal-time match (`ALL_MATCHES_SCOREBOARD.md:39`, `concurrency=10`), `FORGE_FINAL_G3_PGO.exe` + `G3_FULL25` scored **`-0.35 [-8.35, +7.66] Elo`** (`480-1038-482`, `z=-0.09`, `LOS 46.6%`, `ptnml [10, 239, 502, 241, 8]`, `3,994.4s`) because V3P (`1024w` trained with `keep_noisy=true`) ran without any search patches (`-16%` clean NPS offsetting its `250k` per-node gain).

To cleanly test the Owner's proposal (`OPUS-2811-OWNER-BUNDLE-TEST`) and attribute any Elo difference between search changes and the net, `run_owner_bundle_clock_test.py` runs two pre-declared `2,000g` equal-time arms at **`6+0.06`**, **`concurrency=7`**, on **100% idle GPU + 100% idle CPU** with `C:\nnue-lab\neon\CLOCK_MATCH_RUNNING` set in `try/finally`:

| Arm | Match Name (`Seed`) | Candidate (`cand`) | Baseline (`base`) | Isolates |
|---|---|---|---|---|
| **Arm A (`ARM_A_owners`)** | `OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006` (`202611901`) | `FORGE_OWNER_BUNDLE_PGO.exe` (`LmrDeeperShallower=true`) + `G3_FULL25/cand.fnn3` | Live `forge.exe` + `r0067/train/cand.fnn3` | Full Owner Bundle (4 patches + `LmrDeeper` + `G3_FULL25`) vs live baseline |
| **Arm B (`ARM_B_control`)** | `OWNER_BUNDLE_ARMB_bundleR0067_vs_liveR0067_2000g_6p006` (`202611902`) | `FORGE_OWNER_BUNDLE_PGO.exe` (`LmrDeeperShallower=true`) + `r0067/train/cand.fnn3` | Live `forge.exe` + `r0067/train/cand.fnn3` | Holds `r0067` constant to isolate the 4 search patches + `LmrDeeper` + Dual-Net PGO exe |

**Decision Rule (`OWNER_BUNDLE_DECLARATION.json:125`):** Evaluate each arm on its own 95% pentanomial Elo CI; any placement still goes by `lab-place-a-change`.

---

## 4. Hunk-Level Patch Breakdown (`52` Hunks), Individual `50k` Evidence & Honest Exclusions

### 4.1 Concise Hunk-Level Breakdown (`FORGE_OWNER_BUNDLE_PGO.patch` = `896` lines, `52` hunks across `4` files)

Verified directly on disk (`34 + 1 + 5 + 12 = 52` hunks; passes `git apply --check` with `rc=0` on `forge/r15dsg`):

1. **`V3P_pairwise_psqt_fused_v3.patch` (`679` lines, `34` hunks across `2` files):**
   - `include/forge/nnue_v3.hpp` (`12` hunks): raises `MaxHidden = 1536`, adds `MaxPsqt = 16 * QA * QB` (`261120`), `FlagPairwise = 4U`, `FlagPsqt = 8U`; extends `Net`, `Accumulator`, and `RefreshCache::Entry` with `pairwise`/`has_psqt`/`psqt` state; adds `psqt_column()`, `apply_psqt_changes()`, incremental PSQT propagation in `update_accumulator`, and `file_size_for(..., pairwise, has_psqt)`.
   - `src/nnue_v3.cpp` (`22` hunks): widens `hsum_epi32_pair_avx2` to 64-bit per-vector (`_mm256_cvtepi32_epi64`) to prevent `int32` overflow up to `H=1536`; implements pairwise CReLU output (`output_sum_avx2`, `output_sum_avx512`, `output_sum_scalar`), fused AVX-512 kernel `apply_pair_and_sum_pairwise_avx512`, `apply_psqt_changes` (AVX2 `ob == 8` fast path + scalar), PSQT evaluation `(stm_psqt - opp_psqt) / 2`, and strict `load_file` bounds/header validation (`15/15` quick / `37/37` full).
2. **`SF13_qs_evasion_pruning.patch` (`28` lines, `1` hunk in `src/search.cpp:1847`):**
   - Inside `Worker::quiescence`, preserves `!in_check` futility and SEE pruning and adds check-evasion pruning when `in_check` (`mate_moves_ == 0 && best_score > -MateInMaxPly`): prunes late (`move_count > 2`) non-capture, non-promotion, non-checking evasions with `!board.see_ge(move, 0)`.
3. **`SF8_conthist_6ply.patch` (`58` lines, `5` hunks in `src/search.cpp:893,905,933,1617,1703`):**
   - Removes `tune::ContHist4PlyRead` guard on 4-ply continuation read and adds 6-ply continuation history (`const PieceToHistory* cont6` in `QuietScorer`, `ss->ply >= 2`, scaled `bonus / 4` in scoring and `Worker::update_continuation` over `back : {1, 2, 4, 6}`).
4. **`proto_1_corrhist_minor.patch` (`139` lines, `12` hunks across `2` files):**
   - `include/forge/search.hpp` (`3` hunks: `L284,452,505`): declares `MinorCorrectionWeight`, adds `corr_minor_idx` on `SearchStack` and `minor_correction_` on `Worker`.
   - `src/search.cpp` (`9` hunks: `L133,211,1204,1228,1260,1348,1394,1420,1481`): adds tunable `MinorCorrectionWeight = 22` (`0..200`), `minor_piece_key` (`Knight`/`Bishop` `b4::mix64`), incremental `corr_valid` bit `8U` invalidation in `record_move` / propagation in `record_null_move`, application in `corrected_eval`, and `b4::gravity` updates in `update_correction`.
5. **UCI Flag `LmrDeeperShallower=true` (already in `forge/r15dsg`, zero C++ patch):**
   - `include/forge/search.hpp:304`, `src/search.cpp:163` (`bool LmrDeeperShallower = false;` default), `src/search.cpp:2432-2437` (`do_deeper = score > best_score + 40 + 2 * new_depth`, `do_shallower = score < best_score + new_depth`), `src/uci.cpp:756,970,976`. Enabled on the bundle via UCI option (`--cand-opt LmrDeeperShallower=true`).

### 4.2 Unpooled `600g` Screens vs `1,000g @ 50k` Confirmations (`ALL_MATCHES_SCOREBOARD.md`, `0` TL/IL)

| Component | `600g @ 50k` Screen (W–D–L, Elo [95% CI], LOS%) | `1,000g @ 50k` Confirmation (W–D–L, Elo [95% CI], LOS%) |
|---|---|---|
| `SF13_qs_evasion_pruning` | `169-298-133`, **`+20.87 [+4.86, +36.97]`** (`z=+2.56`, `99.5%`) | `256-512-232`, **`+8.34 [-4.39, +21.10]`** (`z=+1.28`, `90.0%`) |
| `SF8_conthist_6ply` | `163-305-132`, **`+17.97 [+2.21, +33.80]`** (`z=+2.23`, `98.7%`) | `251-512-237`, **`+4.86 [-7.77, +17.51]`** (`z=+0.76`, `77.5%`) |
| `proto_1_corrhist_minor` (`W2_proto_1`) | `155-309-136`, **`+11.01 [-4.82, +26.88]`** (`z=+1.36`, `91.3%`) | `260-502-238`, **`+7.64 [-4.34, +19.65]`** (`z=+1.25`, `89.4%`) |
| `LmrDeeperShallower=true` | *(in `COMBO_v1+LmrDeeper`: `148-324-128`, `+11.59 [-4.52, +27.74]`, `92.1%`)* | `255-514-231`, **`+8.34 [-4.06, +20.76]`** (`z=+1.32`, `90.6%`) |

*(Opus `OPUS-2811-OWNER-BUNDLE-TEST` note: no single search fix cleared 95% CI LB > 0 at `50k`; individual `1,000g` confirmations are positive in point estimate, while `6+0.06` may differ from the sum of `50k` point estimates.)*

### 4.3 Honest Disclosures & Explicit Exclusions (`OWNER_BUNDLE_DECLARATION.json:42-48`)

- **Honest `COMBO_v2` Disclosure (`ALL_MATCHES_SCOREBOARD.md:42`):** `COMBO_v2_SF8_SF13_LmrDeeper_1000g_50k` scored **`-3.13 [-15.94, +9.68]`** (`243-505-252`, `z=-0.48`, `LOS 31.6%`, `ptnml [15, 128, 216, 133, 8]`), proving search changes can interact non-linearly and explaining why Arm A and Arm B must be tested as a complete declared bundle rather than assuming additivity.
- **Explicitly Excluded:**
  - `SF4b1_v3_endgame_scale`: `+15.06 [-0.35, +30.54]` (`600g` screen) -> **`-4.52 [-17.04, +7.99]`** (`1,000g` alone), `-5.21` w/ `SF6b+SF8`, and **`-15.99 [-29.09, -2.95]`** (`LOS 0.8%`) w/ `SF8` alone.
  - `SF15_rfp_failsoft_blend`: `+7.53 [-8.65, +23.74]` (`600g` screen) -> **`-0.35 [-12.75, +12.06]`** (`1,000g` confirm).
  - Negative/flat patches (`600g` unless noted): `SF7` (`-13.90`), `SF4b2` (`-19.71 [-36.22, -3.29]`), `SF5a` (`-101.21 [-119.74, -83.22]`), `UCI_EvasionOrdering` (`-15.65 [-30.99, -0.36]`), `W2_proto_3` (`-6.37`), `W2_proto_4` (`-7.53`), `SF12` (`-4.05`), `SF2` (`-4.05`), `UCI_AspFailHighReduce1` (`-4.05`), `SF3` (`-6.37`), `SF16` (`0.00`), `W2_proto_2` (`0.00`), `COMBO_v1` (`-0.35`, `1,000g`).
  - Unscreened Wave 4–6 patches: `SF17..SF40` (note `SF37` is combined `SF17+SF18` exe with no standalone `.patch`), `proto_7`, `proto_8`, `proto_9`, `proto_10`.
  - **`obm4` Clarification:** `M_W2_obm4_vs_noteach_1000g_50k` (`+7.30 [-6.54, +21.16]`, `279-463-258`, `LOS 84.9%`) is an output-bucket training reweighting recipe already represented via `G3_FULL25` anchors — **not** a C++ search patch.

---

## 5. Engineering Separation for the Owner (Datagen/Net Pipeline vs Loader Safety vs Search Tuning)

1. **Live Datagen & Net Pipeline Defects (Real Root Causes in `pipeline/` & `r0001..r0202`):**
   - **Even `random_move_count = 8` (`config.forge.toml:274`):** Ply 7 is always Black's blind random move and ply 8 is White's first searched move, creating `+151.39..+153.94 cp` (`r0202: +152.8 cp`) mean White eval bias and `61.21%–61.46%` White score (`LIVE_LOOP_PARITY_BIAS_AUDIT.json`), plus `ob0=0.562x / ob7=1.663x` skew (`m4_vs_train_shift.json`).
   - **`min_pieces = 4` (`config.forge.toml:336`, `filterqc.py:114-116`):** Drops `28,711,019` (`0.8969%`) `few_pieces` positions over `r0001..r0202`, starving `OB0` (`r0067` `KNN-K=+53 cp`, `KR-K=+233 cp`, `143.5 cp` `OB0<->OB1` cliff).
   - **`--keep-noisy` (`config.forge.toml:357,433`, `forge_train_v3.py:554`):** Retains `17.12%` noisy rows (`134x` more hanging-Queen equal-eval rows `2.68%` vs `0.02%`, `mean_stm_mat=-1.161` vs `mean_sc=+35.9 cp` in `CC0_NOISY_VS_QUIET_FORENSIC.json`), collapsing `FORGENN3-P` (`G3b` vs `G3a`: **`+699.72`** eq-raw / **`+651.27`** eq-ret Elo at `50k`). On scale-free OLS (`OLS_SCALEFREE_COMPARISON.md`, diagnostic only per `OPUS-2811-OLS-CAUTION`), `keep_noisy` yields `Q/P = 5.97` (`r0067`, net-unit `Q=162.1 cp`), `6.21` (`G3_FULL25`, `170.3 cp`), `3.63` (`G3a`), whereas `11/11` `--skip-fqs-noisy` nets have `Q/P = 10.31..10.71`, `R/P = 5.35..5.48`, net-unit `Q = 780..813 cp`. Whether removing `--keep-noisy` improves live `768w` SCReLU is decided strictly by `R1-skip vs R1-keep` (`1,000g @ 250k`).
   - **Missing Cross-Round Dedup & Draw-Conflict Filter (`filterqc.py:64,109,117-122`):** `3.145%` cumulative cross-round duplicates in `r0178..r0202` (`~11.91M` rows, `87.4%` at `ply >= 81`) plus `14,542` `res==0, |score|>=600` draw-conflict leaks in `r0202`.
   - **Leaked `val.plain`:** `1.861%` (`1,993 / 107,084`) internal duplicates and `501` (`0.477%`) unique FENs overlapping `r0202` (replaced in offline audits by whole-game `final_eval_r0203_w14_w15.plain`).
2. **Engine Loader Safety (`V3P_v3`):**
   - `FORGE_OWNER_BUNDLE_PGO.exe` passes `15/15` quick (`r0067`) and `37/37` full (`G3_FULL25`) adversarial header/bounds/checksum probes (`rc=2`, zero silent fallback, zero crash) + `uci_multi_net_switching` + `448,340` `VERIFY=1` nodes (`0` failures).
3. **Search Engine Correctness (`forge/r15dsg` & Bundle Stack):**
   - `forge/r15dsg` and the full bundle stack (`FORGE_OWNER_BUNDLE_PGO.patch` == `STACK_V3Pv3_SF13_SF8_W2P1.patch`) pass `perft 5` (`4865609`, `12/12` full suite), `UBSAN_STACK_PROOF.json` (`ubsan_all_clean: true`), and `MULTITHREAD_STRESS_PROOF.json` (`60/60` mates).

---

## 6. R1 Twin, Post-Bundle 250k Queue & `serverday_v3/*.sh` Governance

- **Clock Runners (`concurrency=7` default & `CLOCK_MATCH_RUNNING`):** `run_owner_bundle_clock_test.py` and `run_clock_tm_screen.py` both default to `--concurrency 7` and delegate clock games (`--nodes 0 --tc`) to `run_net_match.py`, which sets and removes `C:\nnue-lab\neon\CLOCK_MATCH_RUNNING` inside `try/finally` (`run_owner_bundle_clock_test.py` also manages `CLOCK_MATCH_RUNNING` in `try/finally` around its idle 3x `bench 13` check).
- **LMR Deeper SPRT (`run_lmr_deeper_sprt.py`):** Defaults to `--nodes 50000`, `--tc ""`, and `--concurrency 8` for fixed-node `50k` normalized SPRT `[0.0, 5.0]` (`max_rounds=2000`); when `--tc` is supplied (`is_clock=True`), it writes/unlinks `CLOCK_MATCH_RUNNING` in `try/finally` (note: it does not clamp `--concurrency <= 7` automatically if `--tc` is passed).
- **Opus R1 Keep Twin (`run_opus_r1_keep_twin.py`):** Exact twin of `OPUS_R1_live768_skipnoisy` on `r0178..r0202` (`seed=1`, `40` epochs, `b_full.pt` teacher, `--keep-noisy` enabled unless `--skip-noisy` for seed-2); monkey-patches `ft._load_one` and `ft._count_one` to use existing `.cache.npz` strictly read-only (`if existing_cache.exists()`) and parse uncached files in-memory so zero `.cache.npz` files are ever written into `C:\nnue-lab\runs\forge\`.
- **Post-Bundle 250k Queue (`run_post_bundle_250k_queue.py`):** Queues `1,000g @ 250k` (`conc=8`) for `OPUS_R1_skip_vs_R1_keep` and `OPUS_R1_skip_vs_r0067`, followed by `600g @ 250k` confirmations (`v3p_fused_v3_engine.exe`) for up to the top 3 `S2Q_*` Stage-2 winners (`>= +5.0` Elo at `50k`) per Opus's `01:12 PC` rule.
- **Server-Day v3 Shell Wrappers (`serverday_v3/run_dedup_buckets_v3.sh`, `serverday_v3/run_train_stream_gpu_v3.sh`):** Both are LF-only (`0` `\r` bytes), default `--king-buckets 16`, enforce `--skip-noisy` / `--skip-fqs-noisy` (`bit0=0`) and `--drop-draw-conflict 600` / `--dedup-mode avg`, and never pass `--save-ckpt-every` or `--keep-in-check` in active commands.
