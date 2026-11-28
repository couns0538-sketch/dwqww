# Keep-Noisy Root-Cause Analysis Report (Stream A — Wave 7)

**Audience:** Three-Model Debate (Astra, Opus, Neon)  
**Scope:** Forensic root-cause evidence for the `+699.72` / `+651.27` Elo `G3b_skipnoisy vs G3a_keepnoisy` finding, middlegame OLS compression across `keep_noisy=true` vs `skip_noisy=true` regimes, and separation of proven Server-Day requirements from the open `OPUS_R1` live-`768w` SCReLU test.  
**Integrity Notice:** All numerical values below are quoted directly from verified JSON artifacts under `C:\nnue-lab\neon\forge_fixes\` and `C:\nnue-lab\neon\filter_quest\`. Loss, MSE, correlation, and OLS regression metrics are strictly diagnostic and are never treated as Elo.

---

## 1. Executive Summary

Training `FORGENN3-P` (`1024w` Pairwise CReLU + Direct Factorized PSQT) on `bit0=1` noisy capture/recapture positions (`keep_noisy=true`) causes a catastrophic evaluation collapse:

- **Fixed-node match proof (`50,000` nodes, `1,000` games, `0` time losses / `0` illegal moves):**
  - **Equal-raw (`G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k`):** **`+699.72` Elo** (`95% CI [642.27, 784.63]`, `elo_err=71.10`, `972–7–21` W–L–D, `score_pct=98.25%`, `ptnml=[0, 0, 7, 21, 472]`, `z=141.297`, `los_pct=100.0%`).
  - **Equal-retained (`G3b_skipnoisy_vs_G3a_eqret_1000g_50k`):** **`+651.27` Elo** (`95% CI [597.55, 727.83]`, `elo_err=65.07`, `967–13–20` W–L–D, `score_pct=97.7%`, `ptnml=[0, 0, 13, 20, 467]`, `z=115.771`, `los_pct=100.0%`).
- **Root cause (`CC0_NOISY_VS_QUIET_FORENSIC.json`):** Zero code bug — pure chess physics. In `1,839,070` total CC0 self-play rows (`chk_pct=0.0%`), **`17.12%`** are `bit0=1` noisy positions (capture/recapture mid-exchange leaves) with `mean_stm_mat = -1.161` pawns versus `mean_sc = +35.9` cp, **`22.26%`** vs **`1.76%`** (`12.65x`) hanging pieces (`|mat| >= 3`) at near-equal search eval (`|sc| < 100`), and **`2.68%`** vs **`0.02%`** (**`134x`**) hanging Queens (`|mat| >= 8`) at `|sc| < 100`.
- **Teacher distillation does NOT prevent the collapse (`G3AB_DISTILL_REGIME_CHECK.json`):** Even with `r0067` teacher distillation (`w=0.2`), `G3a_distill_keep_noisy` still collapses middlegame `OLS Q` to **`201.8` cp** (`R=132.9 < N=140.5`, `2` sanity flags `["S1_startpos", "S5_dead_draws"]`), whereas `G3b_distill_skip_noisy` achieves `OLS Q = 1002.7` cp and **`0` sanity flags**.
- **9/9 quiet Stage-2 recovery (`STAGE2_QUIET_GPU_SUMMARY.json`):** Retraining all 9 remaining Stage-2 Filter Quest arms with `--skip-fqs-noisy` (`f1_quiet_kept=1,442,765`) restored `OLS Q` to **`988.5–1033.8` cp** across `9/9` arms.
- **Proven vs. Open boundary:** `--skip-fqs-noisy` (`bit0=0`) is **proven and mandatory** for Server Day `1.4B–2.0B` `FORGENN3-P` training (zero debate). What remains **open and under active test** is Opus Request R1 (`OPUS_R1_live768_skipnoisy`), which tests whether removing `--keep-noisy` also strengthens the live `768w` SCReLU architecture (which lacks a direct PSQT path), pending a twin `--keep-noisy` run in the identical standalone runner and `250k` + equal-time `6+0.06` (`concurrency <= 7`) matches.

---

## 2. Chess-Physics Root Cause: `CC0_NOISY_VS_QUIET_FORENSIC.json`

`C:\nnue-lab\neon\forge_fixes\CC0_NOISY_VS_QUIET_FORENSIC.json` audits `1,839,070` total rows (`noisy_pct=17.12%`, `chk_pct=0.0%`) sampled into `quiet_bit0_0` (`sampled_n=304,797`), `noisy_bit0_1` (`sampled_n=63,017`), and `all_noncheck` (`sampled_n=367,814`):

| Metric | `quiet_bit0_0` (`82.88%`) | `noisy_bit0_1` (`17.12%`) | `all_noncheck` (`100%`) | Noisy / Quiet Ratio or Delta |
|---|---:|---:|---:|---:|
| `sampled_n` | `304,797` | `63,017` | `367,814` | — |
| `corr_mat_sc` (material vs search score) | `0.8563` | `0.6163` | `0.7838` | `-0.2400` |
| `corr_mat_res` (material vs game result) | `0.642` | `0.4545` | `0.5849` | `-0.1875` |
| `corr_sc_res` (search score vs game result) | `0.7414` | `0.7228` | `0.7376` | `-0.0186` |
| `mean_stm_mat` (STM material, pawns) | `-0.005` | **`-1.161`** | `-0.203` | **`-1.156` pawns** |
| `mean_sc` (STM search score, cp) | `+1.5` | **`+35.9`** | `+7.4` | **`+34.4` cp** |
| `mean_abs_stm_mat` (pawns) | `1.406` | `1.994` | `1.506` | `1.418x` |
| `pct_eq_sc_with_mat_ge3` (`|sc|<100`, `|mat|>=3`) | `1.76%` | **`22.26%`** | `5.41%` | **`12.65x`** (`12.6477x`) |
| `pct_eq_sc_with_mat_ge8` (`|sc|<100`, `|mat|>=8`) | `0.02%` | **`2.68%`** | `0.5%` | **`134.0x`** |
| `pct_opposite_mat_vs_sc_ge3` (`|mat|>=3`) | `0.07%` | **`2.87%`** | `0.55%` | **`41.0x`** |

### Mechanism of Failure
1. **Mid-capture / mid-recapture imbalance:** A `bit0=1` noisy position occurs when the engine's best move is a capture (often a recapture after an opponent just captured a piece). At the leaf *before* the recapture is played, the side to move (`STM`) is temporarily down a Queen (`-9`), Rook (`-5`), or minor piece (`-3`) — hence `mean_stm_mat = -1.161` pawns — yet the 4k-node search score sees the immediate recapture and evaluates the position as slightly favorable (`mean_sc = +35.9` cp).
2. **Direct PSQT / Feature-Transformer cancellation:** Static NNUE evaluation cannot run quiescence search. When `FORGENN3-P` (which exposes a direct linear Piece-Square Table `psqt` path alongside `1024w` Pairwise CReLU) is trained on `22.26%` hanging-piece equal-eval rows and `2.68%` hanging-Queen equal-eval rows (`134x` higher than quiet rows), gradient descent resolves the contradiction (`STM` down a Queen yet `target >= 0`) by **shrinking static material weights (`Q`, `R`, `B`, `N`)** so a missing Queen does not cause a massive static MSE penalty.
3. **Why `G3a_eqret` confirms it is poison, not data volume:** Truncating the `keep_noisy` dataset to the exact retained row count (`G3a_cc0_keep_noisy_eqret`) still yields `+651.27` Elo (`[597.55, 727.83]`) in favor of `G3b_skipnoisy`. Excluding the `17.12%` noisy rows raises strength by over `650` Elo even when the quiet arm sees fewer raw source rows (`eq-raw` `+699.72` Elo).

---

## 3. Match Proof: `G3b_skipnoisy` vs `G3a_keepnoisy` (`50k` Fixed Nodes)

Verified directly from `summary.json` under `C:\nnue-lab\neon\forge_fixes\matches\` (both sides use identical `v3p_fused_v3_engine.exe`, `sha256=c5c939f52f9a139d71c3287e7591a48347577f57aec0caf7c2c0cafc8ebe68f6`, `Threads=1`, `Hash=16`, identical 45 Big Tune UCI options, `UHO_Lichess_4852_v1.epd`, `concurrency=6`, `0` time losses, `0` illegal moves):

| Match | `elo` (`elo_err`) | `95% CI` | `games` (`W–L–D`) | `score_pct` | `ptnml` | `z` | `los_pct` | `seconds` |
|---|---|---|---|---:|---|---:|---:|---:|
| `G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k` (eq-raw) | **`+699.72`** (`71.10`) | `[642.27, 784.63]` | `1000` (`972–7–21`) | `98.25%` | `[0, 0, 7, 21, 472]` | `141.297` | `100.0%` | `285.6` |
| `G3b_skipnoisy_vs_G3a_eqret_1000g_50k` (eq-ret) | **`+651.27`** (`65.07`) | `[597.55, 727.83]` | `1000` (`967–13–20`) | `97.7%` | `[0, 0, 13, 20, 467]` | `115.771` | `100.0%` | `288.7` |

Both comparisons establish beyond statistical doubt (`z > 115`, `LOS = 100.0%`) that `keep_noisy=true` breaks `FORGENN3-P` on 2M CC0 positions.

---

## 4. Distillation Regime Check & Scratch Ablations (`G3AB_DISTILL_REGIME_CHECK.json` + `eval_full.json`)

To test whether `r0067` teacher distillation (`w=0.2`, matching `G3_FULL25` and the live loop) rescues `keep_noisy`, `G3AB_DISTILL_REGIME_CHECK.json` and companion `eval_full.json` files compare scratch (`G3a`/`G3a_eqret`/`G3b`) and distilled (`G3a_distill_keep_noisy`/`G3b_distill_skip_noisy`) 2M CC0 runs:

| Run (`1024w` `FORGENN3-P`, 2M CC0) | `skip_noisy` | Teacher `r0067` | `train_loss` | `r0203_quiet_mix60` | `m4_wdl_mse` | `m4_corr` | `OLS (P / N / B / R / Q)` cp | `Q/P` | `sanity_flags` (`count`) | `S6 Q` / `S6 R` |
|---|---|---|---|---:|---:|---:|---|---:|---|---:|
| `G3a_cc0_keep_noisy` | `false` | none | `0.000847` | `0.034220` | `0.02941` | `0.5074` | `54.9 / 138.4 / 142.4 / 125.9 / 199.3` | `3.63` | `["S1_startpos", "S5_dead_draws"]` (`2`) | `905` / `489` |
| `G3a_cc0_keep_noisy_eqret` | `false` | none | `0.000761` | `0.034481` | `0.02918` | `0.5081` | `52.4 / 125.6 / 131.4 / 123.7 / 185.1` | `3.53` | `["S1_startpos", "S5_dead_draws"]` (`2`) | `912` / `442` |
| `G3b_cc0_skip_noisy` | `true` | none | `0.000407` | `0.022602` | `0.02339` | `0.6334` | `96.4 / 373.9 / 400.8 / 522.0 / 1016.0` | `10.54` | `["S1_startpos", "S5_dead_draws"]` (`2`) | `1039` / `517` |
| **`G3a_distill_keep_noisy`** | `false` | `w=0.2` | `0.000668` | `0.031349` | `0.02775` | `0.5298` | `55.1 / 140.5 / 147.6 / 132.9 /` **`201.8`** | `3.66` | `["S1_startpos", "S5_dead_draws"]` (`2`) | `893` / `479` |
| **`G3b_distill_skip_noisy`** | `true` | `w=0.2` | `0.000314` | `0.021371` | `0.02252` | `0.639` | `95.1 / 366.0 / 394.0 / 515.8 /` **`1002.7`** | `10.54` | **`[]` (`0`)** | `1052` / `532` |

### Key Takeaways from `G3AB_DISTILL_REGIME_CHECK`
1. **Distillation fails to prevent the collapse:** `G3a_distill_keep_noisy` still exhibits severe middlegame OLS compression (`OLS Q = 201.8` cp vs `1002.7` cp for `G3b_distill_skip_noisy`), retains the `R < N < B` piece-value inversion (`132.9 < 140.5 < 147.6`), more than doubles `train_loss` (`0.000668` vs `0.000314`), worsens `r0203_quiet_mix60` (`0.031349` vs `0.021371`), worsens `m4_wdl_mse` (`0.02775` vs `0.02252`, `m4_opp_wing_wdl_mse` `0.0399` vs `0.02977`), drops `m4_corr` (`0.5298` vs `0.639`), and keeps `2` sanity flags.
2. **Clean zero-flag parity on `G3b_distill_skip_noisy`:** `G3b_distill_skip_noisy` achieves `0` sanity flags (`S1_startpos=-7`, `S1_after_1e4=18`, `S2_start_plus_e4=11`, `S5_dead_draws={"K-K": 9, "KN-K": 10, "KB-K": 42, "KNN-K": 10}`, `S7_won_endings={"KQ-K": 1045, "KR-K": 572}`, `ob0_ob1_cliff_median_jump_cp=177.5` vs `182.5` for `G3a_distill`).

---

## 5. Anchoring Against 25-Round Nets (`r0067` & `G3_FULL25`) and Opus's Scale-Free Caution

In `OPUS-2811-R0202-AND-KEEP-NOISY` (Request R2) and `OPUS-2811-OLS-CAUTION` (`OPUS_TO_NEON.md:2970, 2990–3000`), Opus asked whether `G3_FULL25` used `keep_noisy=true` and cautioned against comparing raw OLS cp across nets with different output scales (`unit_raw_per_pawn`).

Verified directly from `baseline_r0067_scorecard.json`, `G3_FULL25_v3p_1024_cc0_anchored/post_g3_summary.json`, and `G3_FULL25_v3p_1024_cc0_anchored/metrics.json`:
- **Confirmed training flag (`metrics.json`):** `G3_FULL25` trained with `args.skip_fqs_noisy = false` (`keep_noisy = true` on both `r0178..r0202` and `cc0_shards_4k_v2`, matching the live loop `train_cmd`).
- **Exact `r0067` SHA-256 note:** The verified SHA-256 of `C:\nnue-lab\runs\forge\r0067\train\cand.fnn3` (across `G3_FULL25_PGO_vs_live_r0067_2000g_6p006/summary.json`, `OPUS_r0202_vs_r0067_1000g_250k/summary.json`, and `OPUS_R1_live768_skipnoisy/declaration.json`) is `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28` (correcting the `34d2248d...` shorthand typo in `NEON_TO_OPUS.md:850`).

| Net (`eval_net_full.py` probe) | `keep_noisy` | `OLS (P / N / B / R / Q / tempo)` cp | Scale-free `Q/P` | Scale-free `R/P` | `S6 (Q / R / B / N / P)` | `m4_wdl_mse` | `m4_corr` | `eval_full` flags |
|---|---|---|---:|---:|---|---:|---:|---:|
| **`r0067`** (`768w` SCReLU, 25r) | `true` | `51.5 / 135.7 / 167.0 / 202.1 /` **`307.3`** `/ 18.8` | **`5.97`** (`5.967`) | `3.92` | `1931 / 678 / 623 / 559 / 203` | `0.01302` | `0.7754` | `3` (`S1, S2, S5`) |
| **`G3_FULL25`** (`1024w` V3P, 25r) | `true` | `47.2 / 121.8 / 154.5 / 199.1 /` **`293.3`** `/ 18.4` | **`6.21`** (`6.214`) | `4.22` | `1502 / 795 / 589 / 558 / 201` | `0.0114` | `0.8041` | `3` (`S1, S2, S5`; v2: `1`) |
| `G3b_cc0_skip_noisy` (`1024w`, 2M) | `false` | `96.4 / 373.9 / 400.8 / 522.0 /` **`1016.0`** `/ -10.6` | **`10.54`** (`10.539`) | `5.41` | `1039 / 517 / 479 / 464 / 164` | `0.02339` | `0.6334` | `2` (`S1, S5`) |
| `G3b_distill_skip_noisy` (`1024w`, 2M) | `false` | `95.1 / 366.0 / 394.0 / 515.8 /` **`1002.7`** `/ -2.9` | **`10.54`** (`10.544`) | `5.42` | `1052 / 532 / 490 / 456 / 144` | `0.02252` | `0.639` | `0` |

### Additional `G3_FULL25` Verified Scorecard Details (`post_g3_summary.json` & `metrics.json`)
- **Net artifact:** `sha256 = 7ff7789032491aa732846db17ad24ec7fc95c6cb9ad177490f5a06fcccbb9763`, `bytes = 12,798,184`, `master_gates_rc = 0`, `master_gates_ok = true`.
- **Training stats (`metrics.json`):** `train_seconds = 9157.4`, `gpu_paused_s = 1950.3` (`75` pauses, `gpu_max_c = 98.0`), `final_train_loss = 0.006042`, `legacy_val_quiet_mix60 = 0.015013`, `final_eval_r0203_quiet_mix60 = 0.012138`.
- **Heldout Syzygy 4k (`heldout_syzygy_4k`):** `unit_raw_per_pawn = 172.2`; `heldout_draws_2000` (`n=2000`): `mean_abs_cp = 16.4`, `median_abs_cp = 9.9`, `p95_abs_cp = 55.2`, `pct_le_50cp = 93.9%`, `pct_le_100cp = 98.05%`; `heldout_wins_2000` (`n=2000`): `sign_correct_pct = 99.6%`, `mean_signed_cp = 542.9`, `median_signed_cp = 451.5`, `p05_signed_cp = 223.6`, `pct_ge_400cp = 61.1%`, `pct_ge_800cp = 20.45%`.
- **SF19 slice (`sf19_slice`):** `overall` (`n=6000`): `wdl_mse = 0.052914`, `wdl_mae = 0.17777`, `corr = 0.7854`, `severe_ge25_pct = 27.77%`, `severe_ge35_pct = 13.22%`, `sign_flip_ge150_pct = 3.98%`; `OB0` (`n=125`): `wdl_mse = 0.011963`, `sign_flip_ge150_pct = 0.0%`; `OB1` (`n=512`): `wdl_mse = 0.016922`, `sign_flip_ge150_pct = 0.0%`.
- **`r0067` baseline comparison points (`baseline_r0067_scorecard.json`):** `S1_startpos = 87`, `S2_start_plus_e4 = 113`, `S5_dead_draws = {"K-K": 5, "KN-K": -29, "KB-K": -6, "KNN-K": 101}`, `S7_won_endings = {"KQ-K": 1697, "KR-K": 442}`, `ob0_ob1_cliff_median_jump_cp = 143.5` (vs `133.0` for `G3_FULL25`).

### Opus's Scale-Free `Q/P` Caution (Critical Debate Guardrail)
1. **Unit normalization:** Raw `m4_mid20_26_ols_piece_cp` values depend on each net's internal output scale (`unit_raw_per_pawn`, `172.2` for `G3_FULL25`; `net_sanity` uses `u = (Q+R+B+N)/20`). Comparing `307.3` (`r0067`) vs `293.3` (`G3_FULL25`) raw cp is only meaningful via **scale-free ratios**: `Q/P = 5.97` (`r0067`) and `6.21` (`G3_FULL25`), vs **`10.54`** (`G3b_skip_noisy`), and `R/P = 3.92` (`r0067`) and `4.22` (`G3_FULL25`), vs **`5.41–5.42`** (`G3b_skip_noisy`).
2. **Probe semantics:** Even with scale-free `Q/P = 5.97`–`6.21`, middlegame OLS measures how eval responds to material imbalances in dynamic self-play middlegames (where temporary tactical imbalances and compensation occur), NOT quiet-leaf material weights (`S6 Q = 1931` for `r0067` and `1502` for `G3_FULL25` in the quiet anchor). Therefore, `OLS Q` compression is a diagnostic reading of the probe, **not** standalone proof of lost Elo on `768w` SCReLU; only `fastchess` games decide.

---

## 6. Stage-2 Quiet GPU Retraining (`STAGE2_QUIET_GPU_SUMMARY.json`)

After discovering the `keep_noisy` collapse, all `9` remaining Stage-2 Filter Quest arms were retrained cleanly with `--skip-fqs-noisy` (`C:\nnue-lab\neon\filter_quest\STAGE2_QUIET_GPU_SUMMARY.json`, `timestamp = "2026-11-27 23:30:03"`, `f1_quiet_kept = 1,442,765`). **All `9/9` arms restored `ols_Q = 988.5–1033.8` cp:**

| # | Arm (`name`) | `train_loss` | `r0203_quiet_mix60` | `m4_wdl_mse` | `m4_corr` | `ols_Q` (cp) | `syz_draw_med_cp` | `syz_win_ok_pct` |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `s2q_g4a_losspow25` | `0.000123` | `0.022562` | `0.0231` | `0.634` | **`988.5`** | `29.3` | `99.3` |
| 2 | `s2q_g4b_obreweight` | `0.000406` | `0.022586` | `0.0235` | `0.6335` | **`1022.3`** | `28.3` | `99.3` |
| 3 | `s2q_f1_hard` | `0.000404` | `0.022626` | `0.02311` | `0.631` | **`1009.1`** | `29.4` | `99.3` |
| 4 | `s2q_f1_ctrl_eqret` | `0.000379` | `0.022717` | `0.02353` | `0.6288` | **`1011.8`** | `27.5` | `99.3` |
| 5 | `s2q_f2_dedup_first` | `0.000444` | `0.022601` | `0.02318` | `0.6344` | **`1033.8`** | `27.5` | `99.3` |
| 6 | `s2q_f2_dedup_avg` | `0.000441` | `0.022652` | `0.02336` | `0.633` | **`1026.5`** | `27.4` | `99.3` |
| 7 | `s2q_r1_rescore16k_0p5pct` | `0.000444` | `0.022611` | `0.02325` | `0.6339` | **`1033.1`** | `26.9` | `99.3` |
| 8 | `s2q_r1b_rescore16k_2pct_oppcastle` | `0.000441` | `0.022605` | `0.02318` | `0.6344` | **`1025.2`** | `27.4` | `99.3` |
| 9 | `s2q_w3_soft_weight` | `0.000444` | `0.022667` | `0.02308` | `0.6309` | **`1017.0`** | `26.9` | `99.25` |

*(Note: All `10` Stage-2 quiet-filtered `50k` CPU matches from `run_stage2_clean_skipnoisy_matches.py` are still executing; `50k` matches act only as screens, and any winning arm requires `250k` confirmation.)*

---

## 7. What IS Proven vs. What Is Currently Being Tested

| Claim / Question | Status | Evidence & Exact Next Protocol |
|---|---|---|
| `keep_noisy=true` collapses `FORGENN3-P` (`1024w` Pairwise+PSQT) from scratch and under `r0067` `w=0.2` distillation | **PROVEN** | `+699.72` (eq-raw) / `+651.27` (eq-ret) Elo (`G3b vs G3a`); `G3a_distill` `OLS Q=201.8` vs `G3b_distill` `1002.7` (`0` flags); `9/9` Stage-2 quiet arms `OLS Q=988.5–1033.8`. |
| Server Day `1.4B–2.0B` datagen/training MUST enforce `--skip-fqs-noisy` (`bit0=0`) | **PROVEN (Zero Debate)** | `17.12%` noisy CC0 rows have `mean_stm_mat=-1.161`, `134x` hanging Queens at `|sc|<100`, collapsing PSQT/Pairwise nets. |
| Does removing `--keep-noisy` improve the **live `768w` SCReLU** loop net? | **OPEN / ACTIVE TEST (Opus Request R1)** | `768w` SCReLU has no direct PSQT path and has run `--keep-noisy` since round 7 (`OPUS_TO_NEON.md:2964–2969`). `OPUS_R1_live768_skipnoisy` is currently training on GPU (`r0178..r0202`, `b_full.pt w=0.2`, `40` ep, `lr=0.0005`, zero writes to `runs/forge/`). |
| **Opus Twin Requirement for R1 (`OPUS_TO_NEON.md:3016–3020`)** | **REQUIRED BEFORE VERDICT** | `r0202` was trained by the loop runner, so comparing standalone `OPUS_R1` directly to `r0202` mixes `--keep-noisy` with runner differences. Must train a twin **WITH `--keep-noisy`** in the **exact same standalone runner** (`seed=1`), then decide `R1-skip vs R1-keep` at **`250k` nodes (`1,000` games, 95% CI lower bound `> 0`)**. If positive, train a second seed of both and test vs `r0067` at `250k` and equal-time **`6+0.06` at `concurrency <= 7`**. |
