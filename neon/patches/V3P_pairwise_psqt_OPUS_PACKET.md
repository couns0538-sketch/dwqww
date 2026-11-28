# Opus Placement Review Packet: `V3P_pairwise_psqt.patch` (`FORGENN3-P`)

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\V3P_pairwise_psqt.patch` (`494` lines, LF-normalized, plain `git -C C:\nnue-lab\forge\r15dsg apply --check` = **`RC=0`**)
- **Target Files (`forge/r15dsg`):** `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`
- **Built & Tested Binary:** `C:\nnue-lab\neon\forge_fixes\builds\v3p_engine.exe` (also composed in `V3P_SF8.exe`, `V3P_SF6b_scaled_SF8.exe`, `V3P_SF4b1_SF6b_scaled_SF8_combo.exe`)
- **Trainer & Format Reference:** `C:\nnue-lab\neon\forge_fixes\forge_v3p.py`, `C:\nnue-lab\neon\forge_fixes\train_v3p.py`
- **Fail-Before / Pass-After Test Script:** `C:\nnue-lab\neon\forge_fixes\test_v3p_engine_gate.py`

---

## 1. Summary & Architecture

Clean-room extension of Forge's stand-alone `FORGENN3` architecture (`FlagMirror=2`, `MaxHidden=1024`) adding two optional backward-compatible header flags:
- **`FlagPairwise = 4`:** Pairwise clipped-ReLU (`clamp(a[i], 0, QA) * clamp(a[i + H/2], 0, QA)`) halving `w2` input dimension per perspective while adding quadratic feature cross-terms (`H` multiple of `64`, up to `MaxHidden = 1536`).
- **`FlagPsqt = 8`:** Direct factorized king-bucketed Piece-Square Table (`int32 psqt[kb][768][ob]`, `MaxPsqt = 16 * QA * QB`) accumulated incrementally alongside the L1 feature transformer and added directly to the output bucket sum (`(stm_psqt - opp_psqt) / 2`).
- **100% Backward Compatibility:** When neither `FlagPairwise` nor `FlagPsqt` is set (e.g., live `r0067/train/cand.fnn3`), `v3p_engine.exe` runs the exact legacy `FORGENN3` path bit-for-bit (`perft 5 = 4,865,609`, `B4 bench 11/13 = 187,930 / 632,195`, `startpos eval = 87`, `0 cp` across 120 FENs).

## 2. Provenance & Clean-Room Status

- **Design inspiration:** Pairwise CReLU (Bullet / Viridithas / Stormphrax) and direct PSQT output head (Stockfish HalfKAv2_hm).
- **License status:** 100% clean-room C++ written against Forge's own `nnue::v3` accumulator, king-bucket mirror cache, and AVX-512 / AVX2 / scalar dot-product structure; zero GPL code copied.

## 3. Audit & Correctness Gates Passed

1. **Plain `git apply --check`:** `git -C C:\nnue-lab\forge\r15dsg apply --check C:\nnue-lab\neon\forge_fixes\patches\V3P_pairwise_psqt.patch` -> **`RC=0`**.
2. **Stream 2 C++ Audit Fixes Included:** `hsum_epi32_pair_avx2` int64 widening (eliminates int32 overflow at `H=1536`), `!pairwise` cap at `1024`, clean error diagnostics on invalid flags/hidden/PSQT bounds.
3. **3-ISA Bit-Exactness:** AVX-512 == AVX2 == Scalar (`bench 10 = 126,210`, `0 cp` max diff across 100 FENs); planted 1-cp verification fault caught with `rc=3`.
4. **Loader Safety (`40/40` full, `15/15` quick):** Truncated, trailing-byte, bad magic, bad version, unknown flags, bad checksum, odd/small pairwise hidden, OOB weights, and OOB PSQT all rejected loudly with `rc=2` (zero crash, zero silent HCE fallback).
5. **Fail-Before / Pass-After (`test_v3p_engine_gate.py`):**
   - `base_r15dsg.exe`: **FAIL (`rc=1`)** (rejects `FORGENN3-P` synthetic net with `rc=2`).
   - `v3p_engine.exe`: **PASS (`rc=0`)** (`r0067` bit-identical + synthetic `FORGENN3-P` `120` FENs `8/8` OB **`0 cp`** vs `forge_v3p.reference_eval()` + `go depth 6` + corrupted checksum `rc=2`).

## 4. Playing Strength & Equal-Time NPS Status

- **`G2_v3p_1024_pairwise_psqt` (`12r` `r0191..r0202` = `166.5M` + `dead_draws_20k`x20, SHA-256 `6a24996f9057c5b42a489c12c185de1673f30a0318b17e020514efbd647d587f`) — COMPLETE (`19:52:13 PC`):**
  - `final_train_loss = 0.004601` (`-5.37%` vs `G1` `768w` `0.004862` on exact same 12 rounds).
  - **Untouched whole-game holdout `final_eval_r0203_all_mix60 = 0.014689`** — beats live 25-round `r0067` (`0.014811`) with HALF the data (`G1`: `0.014875`, `r12_control`: `0.015235`).
  - **M4 & SF19 6k Slice:** `m4_wdl_mse = 0.01234` (vs `r0067` `0.01302`), `m4_corr = 0.7864` (vs `0.7754`), `m4_opp_wing_wdl_mse = 0.01612` (vs `0.01724`); SF19 6k slice `wdl_mse = 0.05502` (vs `0.05737`), `sign_flip_ge150 = 4.45%` (vs `5.10%`).
  - **Opus `net_sanity.py` v2:** `S5 dead draws` COMPLETELY CURED (`K-K +7, KN-K +9, KB-K -11, KNN-K +33`). Only `S2` (`M +21.9 cp`, borderline) & `S7` (`KR-K +313`) remain — targeted by `G3_FULL25`.
  - **Clean GPU+CPU-Idle 3x Interleaved `bench 13` NPS (`G2/nps_clean_idle.json`, `CLOCK_MATCH_RUNNING` set):**
    - `base_r15dsg + r0067` (`768w`): `3,064,234 NPS` (`576,076` nodes in `188 ms`).
    - `v3p_engine + r0067` (`768w`): `3,064,234 NPS` (`1.0000x`, zero legacy overhead).
    - `v3p_engine + G2` (`1024w` Pairwise+PSQT): `2,567,354 NPS` (`0.8378x`) AND `441,585` nodes in **`172 ms`** (`-23.3%` nodes, `9%` faster wall-clock to depth 13 pre-PGO!).
- **`G3_FULL25_v3p_1024_cc0_anchored` (`25r` + `5.52M` clean CC0 v2 + `1.0M` Syzygy clean anchors = `353.45M` pos):** Training now (ETA `~22:50 PC`), followed by true PGO build (`build_fast.py --pgo --pgo-net`) and clean GPU-idle `2,000g @ 6+0.06` equal-time confirmation vs live PGO `v3-r15dsg-sp-clang + r0067`.
- **Placement timing:** Hold placement until `G3_FULL25` PGO equal-time `6+0.06` confirmation demonstrates clear net+NPS gain over live `r0067`.
