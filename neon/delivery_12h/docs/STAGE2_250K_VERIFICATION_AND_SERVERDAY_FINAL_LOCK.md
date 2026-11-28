# Stage-2 250k Confirmation Postmortem & Server-Day 2.0B Final Lock (Wave 10 — Stream B)

> **Integrity Rule (R5) & Statistical Governance (`OPUS-2811-G4B-250K-AND-POWER`):**
> - Training loss, WDL MSE (`m4_wdl_mse`), `M4`/`SF19` scorecards, `net_sanity` flags, and scale-free OLS piece ratios (`Q/P`, `R/P`) are **strictly diagnostic** — NEVER claims of Elo. Strength is decided exclusively by declared `fastchess` matches with zero pooling across independent runs.
> - All `3/3` Stage-2 `600g @ 250k` confirmations carry a `±19 Elo` 95% confidence band (`~25%` statistical power for a `+10 Elo` true effect) and MUST be classified strictly as **`NOT CONFIRMED`**.
> - Per `OPUS-2811-R1-SIZE-TOO-LATE` (`C:\nnue-lab\neon\OPUS_TO_NEON.md:3113-3115`), the `G3b vs G3a` match outcomes (`+699.72` / `+651.27` Elo) are reported strictly as **"keep-noisy breaks V3P nets on CC0 data"**, never as an Elo gain of `skip-noisy` on live `768w` SCReLU (which is currently being tested independently by `OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k`).

---

## 1. Executive Summary

1. **All `3/3` Stage-2 `600g @ 250k` confirmations (`S2Q_G4b`, `S2Q_EXP_R1b`, `S2Q_G4a`) are `NOT CONFIRMED`:** None of the three `1,000g @ 50k` filter leads (`+14.95`, `+14.25`, `+8.34`) reproduced a positive signal at `600g @ 250k` (`-5.21`, `-12.75`, `-16.23` Elo; `0/0/0` time/illegal/disconnect faults). Per `OPUS-2811-G4B-250K-AND-POWER`, `600` games at `250k` provides only `~25%` power for a `+10 Elo` effect (`~2,800` games needed for `80%` power), so each arm is **`NOT CONFIRMED`** rather than falsified, and future confirmations will use normalized `SPRT [0, 10]` at `250k` with a `3,000`-game cap.
2. **Server-Day `2.0B` default recipe locked clean and minimalist:** Without positive `250k` confirmation for `--ob-reweight cc0`, `--loss-pow 2.5`, or selective `16k` opposite-castled rescoring, Server-Day `2.0B` defaults remain locked to **`OB_REWEIGHT=none`**, **`LOSS_POW=2.0`**, mandatory **`--skip-fqs-noisy` (`bit0=0`) + `bit1=0` in-check drop**, **50/50 CC0 parity**, **`--dedup-mode avg`** (`sqrt(k)` weights, `--drop-draw-conflict 600`), and **3 frozen disjoint anchors**.
3. **Quiet Server-Day Architecture Suite (`G5a`, `G5b`, `G5c`) verified at `0 cp` parity:** Retraining all three Server-Day `FORGENN3-P` architectures with `--skip-fqs-noisy` + `bit1=0` restored non-collapsed scale-free ratios (`Q/P = 10.59..10.69`, `R/P = 5.357..5.542`, matching the `24`-net `OLS_SCALEFREE_COMPARISON.json` quiet cohort) and passed `Master Gates --quick` (`hard_pass: true`, `0 cp` max parity diff across `120/120` FENs and `8/8` output buckets, `perft 5 = 4865609`, `15/15` loader safety). `G5c_quiet_1024p_kb16` (`25,577,704` bytes, `0.8139x` clean-idle NPS) exhibits slight overfitting on `~2M` CC0 rows (`m4_wdl_mse 0.02369` vs `0.02320` for `G5a`), demonstrating why Server-Day `2.0B` scale (`~23.1M` perspectives even in the rarest of 16 king buckets) is required before judging `1024p/kb16` and optional `1536p/kb8` (`0.7374x` NPS) by declared `2,000g @ 6+0.06` equal-time matches.
4. **`OPUS_R1` live `768w` twin diagnostic complete; SPRT active:** `OPUS_R1_live768_skipnoisy` (`4902fe65...`) and `OPUS_R1_live768_keepnoisy_twin` (`8b1158aa...`) completed diagnostic evaluation; the declared `OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k` (`SPRT [0, 10]`, cap `3,000` games, `task-7807`) is actively running and pending.

---

## 2. Stage-2 `600g @ 250k` Confirmation Postmortem & Statistical Power Analysis

### 2.1 Declaration & Match Isolation (`STAGE2_250K_CONFIRMATIONS_DECLARATION.json`)

All three Stage-2 `600g @ 250k` confirmations were declared in `C:\nnue-lab\neon\forge_fixes\STAGE2_250K_CONFIRMATIONS_DECLARATION.json` (`written: "2026-11-28 04:47:31 PC"`) under a strict **`no_pooling_rule`** (fresh seeds, never pooled with prior `1,000g @ 50k` filter matches):
- **Shared Engine (`exe_both`):** `C:\nnue-lab\neon\forge_fixes\builds\v3p_fused_v3_engine.exe` (`sha256: c5c939f52f9a139d71c3287e7591a48347577f57aec0caf7c2c0cafc8ebe68f6`)
- **Opening Book (`book`):** `C:\nnue-lab\tools\book\UHO_Lichess_4852_v1.epd` (`sha256: 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`)
- **Search & Concurrency:** `nodes = 250000`, `games = 600`, `Threads = 1`, `Hash = 16`, `OwnBook = false`, `MateAlphaGuard = true`, all 45 live `v3_uci_options`, `concurrency = 8` (`max_threads_beside_gpu = 12`).

### 2.2 Complete `3/3` Results vs Prior `1,000g @ 50k` Filters

Every number below is quoted directly from `STAGE2_250K_CONFIRMATIONS_DECLARATION.json`, `ALL_MATCHES_SCOREBOARD.json`, and the three match `summary.json` files under `C:\nnue-lab\neon\forge_fixes\matches\`:

| Match (`C:\nnue-lab\neon\forge_fixes\matches\...`) | Prior `1,000g @ 50k` Filter (`ALL_MATCHES_SCOREBOARD.json`) | `600g @ 250k` Confirmation (`pentanomial_exact`) | `250k` W–D–L (`score_pct`) | `250k` `ptnml` | `250k` `z` / `LOS%` (`top` / `exact`) | Seed / Elapsed / `TL-IL-DC` | Statistical Verdict |
|---|---|---|---|---|---|---:|---|
| `S2Q_G4b_obreweight_vs_G3b_600g_250k_CONFIRM` | `+14.95 [-1.47, +31.43]` (`327-389-284`, `z = 1.785`, `LOS 96.29%`) | **`-5.21 [-24.09, +13.64]`** (`elo_err: 18.83`) | `168–255–177` (`49.25%`) | `[19, 70, 127, 69, 15]` | `-0.542` / `29.36%` / **`29.39%`** | `202611960` / `1196.3s` / `0/0/0` | **`NOT CONFIRMED`** |
| `S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_600g_250k_CONFIRM` | `+14.25 [-1.35, +29.92]` (`316-409-275`, `z = 1.790`, `LOS 96.33%`) | **`-12.75 [-31.52, +5.95]`** (`elo_err: 18.71`) | `161–256–183` (`48.17%` / `48.167%`) | `[20, 76, 121, 72, 11]` | `-1.336` / `9.05%` / **`9.08%`** | `202611961` / `1209.2s` / `0/0/0` | **`NOT CONFIRMED`** |
| `S2Q_G4a_losspow25_vs_G3b_600g_250k_CONFIRM` | `+8.34 [-7.60, +24.32]` (`319-386-295`, `z = 1.025`, `LOS 84.74%`) | **`-16.23 [-35.75, +3.19]`** (`elo_err: 19.44`) | `158–256–186` (`47.67%` / `47.667%`) | `[19, 86, 117, 60, 18]` | `-1.638` / `5.05%` / **`5.08%`** | `202611962` / `1094.2s` / `0/0/0` | **`NOT CONFIRMED`** |

**Verified Candidate/Baseline Net SHA-256 & Telemetry Details:**
1. **`S2Q_G4b_obreweight_vs_G3b_600g_250k_CONFIRM` (`--ob-reweight cc0` vs `G3b`):**
   - `cand_net`: `neon\filter_quest\stage2_runs_quiet\s2q_g4b_obreweight\cand.fnn3` (`sha256: b378b753e4799b0c7972b6c50a338e62afd0f408ddad9f4da348b3e3ab9c400a`)
   - `base_net`: `neon\forge_fixes\gpu_runs\G3b_cc0_skip_noisy\cand.fnn3` (`sha256: cb07450d3b22d2e6de0a54deee9fae9d3ec34fe0983e354aa1cf3f76e3331358`)
   - `nelo = -7.70 ± 27.80`, `heat.cpu_max_c = 86.8°C`, `seconds_at_limit = 0`, `stopped_for_heat = false`.
2. **`S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_600g_250k_CONFIRM` (`2%` opposite-side-castled `16k` rescore vs `dedup_avg`):**
   - `cand_net`: `neon\filter_quest\stage2_runs_quiet\s2q_r1b_rescore16k_2pct_oppcastle\cand.fnn3` (`sha256: 611f21a1498b0736cb0847a7a3b0d607b3ec975c764e5cd4cbabc5d0206c4f59`)
   - `base_net`: `neon\filter_quest\stage2_runs_quiet\s2q_f2_dedup_avg\cand.fnn3` (`sha256: b5d27d2d18107e6485c9bcb56c31f3b8862377a3ac2350d781e158a33ca79a33`)
   - `nelo = -18.98 ± 27.80`, `heat.cpu_max_c = 87.4°C`, `seconds_at_limit = 0`, `stopped_for_heat = false`.
3. **`S2Q_G4a_losspow25_vs_G3b_600g_250k_CONFIRM` (`--loss-pow 2.5` vs `G3b`):**
   - `cand_net`: `neon\filter_quest\stage2_runs_quiet\s2q_g4a_losspow25\cand.fnn3` (`sha256: 1d9604b9c8068a759e8252323688be0f36d85de2431192aa3381a393c9bccd5e`)
   - `base_net`: `neon\forge_fixes\gpu_runs\G3b_cc0_skip_noisy\cand.fnn3` (`sha256: cb07450d3b22d2e6de0a54deee9fae9d3ec34fe0983e354aa1cf3f76e3331358`)
   - `nelo = -23.27 ± 27.80`, `heat.cpu_max_c = 86.6°C`, `seconds_at_limit = 0`, `stopped_for_heat = false`.

### 2.3 Opus's Statistical Power Analysis (`OPUS-2811-G4B-250K-AND-POWER`)

In `C:\nnue-lab\neon\OPUS_TO_NEON.md:3091-3099` (`OPUS-2811-G4B-250K-AND-POWER`, `06:24 PC`, recounting `S2Q_G4b` at `-5.21 [-24.06, +13.61]` normal approx vs `-5.21 [-24.09, +13.64]` `pentanomial_exact`), Opus established the governing statistical rule for `600g @ 250k` confirmations:

- **Underpowered 95% Band (`±19 Elo`):** With `600` games (`300` pentanomial pairs) at `250k` nodes, the 95% confidence interval half-width is **`±19 Elo`** (`18.71..19.44` across the 3 matches).
- **Low Power (`~25%` for `+10 Elo`):** A `600`-game test at `250k` has only **`~25%` statistical power** to detect a true `+10 Elo` effect; achieving **`80%` power** at `250k` requires **`~2,800` games**.
- **Required Terminology (`NOT CONFIRMED`):** Because all three 95% CIs span across `0` (upper bounds `+13.64`, `+5.95`, `+3.19`) and power is only `~25%`, these tests can neither confirm nor rule out a modest `+5..+10 Elo` effect. Therefore, every `600g @ 250k` confirmation result MUST be reported as **`NOT CONFIRMED`**. Simultaneously, keeping the Server-Day defaults clean (`OB_REWEIGHT=none`, `LOSS_POW=2.0`, no selective rescore complexity) is justified because zero `250k` evidence supports turning them on.
- **Future Confirmation Protocol (`SPRT [0, 10]` cap `3,000g`):** Future confirmations of real candidates at `250k` MUST use **normalized `SPRT [0, 10]` with a declared game cap (e.g., `3,000` games)** so genuine gains or nulls terminate cleanly without dying in low-power fixed-`600g` noise. *(Note: `serverday_v3/run_train_stream_gpu_v3.sh:8` retains an earlier pre-`OPUS-2811-G4B-250K-AND-POWER` inline comment on `S2Q_G4b`, while its active `OB_REWEIGHT="${OB_REWEIGHT:-none}"` default on line 26 already matches the final lock.)*

---

## 3. Quiet Server-Day Architecture Suite & 24-Net Scale-Free OLS Synthesis

### 3.1 Quiet Arch Suite (`SERVERDAY_ARCH_SUITE_QUIET_SUMMARY.json`), `Master Gates --quick`, & Clean-Idle NPS

All three Server-Day `FORGENN3-P` candidate architectures were trained from scratch (`run_serverday_arch_suite_quiet.py`) on `C:\nnue-lab\neon\forge_fixes\cc0_shards_4k_v2_nodrawconf` (`2,000,004` raw rows -> `1,839,070` rows after dropping `154,497` `in_check` and `6,437` `draw_conflict` rows in `summary.json`, filtered further by `--skip-fqs-noisy` `bit0=0`) plus all 3 frozen disjoint anchors (`repeat=4`), `epochs=40`, `batch_size=8192`, `lr=0.0005`, `mix=0.85`, `loss_pow=2.0`, `w1_decay=0.3`, `ob_smooth=2e-6`, `seed=1`.

Clean GPU+CPU-idle `bench 15` (`5` rounds) NPS ratios were measured in `C:\nnue-lab\neon\forge_fixes\CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json` (`v3p_pgo_*` vs `live_pgo_r0067_768screlu = 3,613,642` NPS), and correctness gates were verified in each architecture's `master_gate_quick.json` (`v3p_fused_v3_engine.exe`):

| Architecture (`FORGENN3-P`) | Net Bytes | Train (`s`) | Final Train Loss | `r0203_quiet_mix60` | `m4_wdl_mse` / `m4_corr` | Scale-Free `Q/P` / `R/P` | Unit `u` | Syz Draw Med / Win% | Clean-Idle PGO NPS (`5ARCH_NPS`) | `Master Gates --quick` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `G5a_quiet_768p_kb8` | `9,647,848` | `28.1` | `0.00053` (`0.000530`) | `0.022675` | `0.0232` / `0.6339` | **`10.69` / `5.357`** | `127.75` | `27.4 cp` / `99.25%` | `3,047,169` (`0.8432x`) | `PASS` (`0 cp` parity `120/120`, `8/8` OB, `perft 5 = 4865609`, `15/15` loader) |
| `G5b_quiet_1536p_kb8` | `19,098,856` | `57.3` | `0.000302` | `0.022353` | `0.02324` / `0.6313` | **`10.59` / `5.542`** | `131.15` | `28.2 cp` / `99.25%` | `2,664,542` (`0.7374x`) | `PASS` (`0 cp` parity `120/120`, `8/8` OB, `perft 5 = 4865609`, `15/15` loader) |
| `G5c_quiet_1024p_kb16` | `25,577,704` | `48.3` | `0.000323` | `0.023211` | `0.02369` / `0.6253` | **`10.661` / `5.505`** | `127.30` | `43.6 cp` / `99.3%` | `2,940,975` (`0.8139x`) | `PASS` (`0 cp` parity `120/120`, `8/8` OB, `perft 5 = 4865609`, `15/15` loader) |

*Reference `1024p_kb8` (`v3p_pgo_1024p_kb8_G3`) in `CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json`:* `2,959,061` NPS (`0.8189x`), so `kb=8 -> kb=16` at `1024p` (`2,940,975` NPS, `0.8139x`) costs only **`-0.61%` NPS** (`~-0.6%`).

### 3.2 Complete 24-Net Scale-Free OLS Comparison (`OLS_SCALEFREE_COMPARISON.json`)

Strictly diagnostic per R5 and `OPUS-2811-OLS-CAUTION` (scale-free ratios `Q/P`, `R/P`, `B/P`, `N/P` are invariant to each net's output scale `u = (Q+R+B+N)/20`), all `24` rows in `C:\nnue-lab\neon\forge_fixes\OLS_SCALEFREE_COMPARISON.json` demonstrate the structural separation between keep-noisy CC0 collapse and quiet CC0 training:

| # | Net (`OLS_SCALEFREE_COMPARISON.json`) | Regime / Dataset | `m4_wdl_mse` | `N/P` | `B/P` | `R/P` | `Q/P` | `u` | `P/N/B/R/Q` (`net_unit_cp`) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `r0067 (live 768w, keep_noisy)` | Live `768w` SCReLU (`25r`) | `0.01302` | `2.635` | `3.243` | `3.924` | `5.967` | `189.55` | `27.2 / 71.6 / 88.1 / 106.6 / 162.1` |
| 2 | `G2_1024p (12r V3P, keep_noisy)` | `12r` V3P (`keep_noisy`) | `0.01234` | `2.793` | `3.385` | `4.106` | `6.243` | `180.6` | `26.2 / 73.1 / 88.6 / 107.5 / 163.5` |
| 3 | `G3_FULL25 (25r V3P, keep_noisy)` | `25r` V3P (`keep_noisy`) | `0.0114` | `2.581` | `3.273` | `4.218` | `6.214` | `172.2` | `27.4 / 70.7 / 89.7 / 115.6 / 170.3` |
| 4 | `G3a_cc0_keep_noisy (scratch V3P)` | CC0 `keep-noisy` (collapsed) | `0.02941` | `2.521` | `2.594` | `2.293` | **`3.63`** | `114.0` | `48.2 / 121.4 / 124.9 / 110.4 / 174.8` |
| 5 | `G3b_cc0_skip_noisy (scratch V3P)` | CC0 `skip-noisy` | `0.02339` | `3.879` | `4.158` | `5.415` | **`10.539`** | `124.95` | `77.2 / 299.2 / 320.8 / 417.8 / 813.1` |
| 6 | `G3a_distill_keep_noisy (r0067 w=0.2)` | CC0 `keep-noisy` (collapsed) | `0.02775` | `2.55` | `2.679` | `2.412` | **`3.662`** | `114.75` | `48.0 / 122.4 / 128.6 / 115.8 / 175.9` |
| 7 | `G3b_distill_skip_noisy (r0067 w=0.2)` | CC0 `skip-noisy` | `0.02252` | `3.849` | `4.143` | `5.424` | **`10.544`** | `126.5` | `75.2 / 289.3 / 311.5 / 407.7 / 792.6` |
| 8 | `OPUS_R1_live768_keepnoisy_twin (25r)` | Live `768w` twin (`keep-noisy`) | `0.01226` | `2.553` | `3.137` | `3.934` | `6.124` | `201.05` | `26.5 / 67.5 / 83.0 / 104.1 / 162.0` |
| 9 | `OPUS_R1_live768_skipnoisy (25r)` | Live `768w` twin (`skip-noisy`) | `0.01314` | `3.489` | `3.965` | `5.005` | `9.01` | `162.15` | `47.3 / 165.0 / 187.5 / 236.8 / 426.2` |
| 10 | `S2Q/s2q_f1_ctrl_eqret` | Stage-2 Quiet CC0 | `0.02353` | `3.956` | `4.238` | `5.447` | **`10.707`** | `127.2` | `74.3 / 293.9 / 314.9 / 404.6 / 795.4` |
| 11 | `S2Q/s2q_f1_hard` | Stage-2 Quiet CC0 | `0.02311` | `3.853` | `4.11` | `5.349` | **`10.511`** | `126.05` | `76.2 / 293.5 / 313.1 / 407.4 / 800.6` |
| 12 | `S2Q/s2q_f2_dedup_avg` | Stage-2 Quiet CC0 | `0.02336` | `3.948` | `4.218` | `5.481` | **`10.626`** | `131.5` | `73.5 / 290.0 / 309.9 / 402.7 / 780.6` |
| 13 | `S2Q/s2q_f2_dedup_first` | Stage-2 Quiet CC0 | `0.02318` | `3.88` | `4.177` | `5.433` | **`10.581`** | `130.95` | `74.6 / 289.5 / 311.6 / 405.3 / 789.5` |
| 14 | `S2Q/s2q_g4a_losspow25` | Stage-2 Quiet CC0 | `0.0231` | `3.799` | `4.112` | `5.375` | **`10.308`** | `126.35` | `75.9 / 288.3 / 312.1 / 408.0 / 782.4` |
| 15 | `S2Q/s2q_g4b_obreweight` | Stage-2 Quiet CC0 | `0.0235` | `3.872` | `4.134` | `5.435` | **`10.507`** | `127.1` | `76.6 / 296.4 / 316.4 / 416.1 / 804.3` |
| 16 | `S2Q/s2q_r1_rescore16k_0p5pct` | Stage-2 Quiet CC0 | `0.02325` | `3.911` | `4.197` | `5.454` | **`10.662`** | `130.25` | `74.4 / 291.0 / 312.2 / 405.8 / 793.2` |
| 17 | `S2Q/s2q_r1b_rescore16k_2pct_oppcastle` | Stage-2 Quiet CC0 | `0.02318` | `3.897` | `4.189` | `5.479` | **`10.602`** | `131.45` | `73.6 / 286.6 / 308.2 / 403.0 / 779.9` |
| 18 | `S2Q/s2q_w3_soft_weight` | Stage-2 Quiet CC0 | `0.02308` | `3.838` | `4.133` | `5.401` | **`10.378`** | `129.95` | `75.4 / 289.4 / 311.7 / 407.3 / 782.6` |
| 19 | `G5a_cc0_768p_kb8` | Pre-quiet CC0 `keep-noisy` (collapsed) | `0.02889` | `2.381` | `2.432` | `2.092` | **`3.028`** | `105.4` | `53.8 / 128.1 / 130.8 / 112.5 / 162.9` |
| 20 | `G5a_quiet_768p_kb8` | Quiet CC0 `768p/kb8` | `0.0232` | `3.928` | `4.226` | `5.357` | **`10.69`** | `127.75` | `76.9 / 302.2 / 325.2 / 412.2 / 822.5` |
| 21 | `G5b_cc0_1536p_kb8` | Pre-quiet CC0 `keep-noisy` (collapsed) | `0.02915` | `2.293` | `2.372` | `2.21` | **`3.259`** | `114.35` | `51.9 / 119.1 / 123.2 / 114.8 / 169.3` |
| 22 | `G5b_quiet_1536p_kb8` | Quiet CC0 `1536p/kb8` | `0.02324` | `3.938` | `4.248` | `5.542` | **`10.59`** | `131.15` | `72.9 / 287.1 / 309.6 / 404.0 / 771.9` |
| 23 | `G5c_cc0_1024p_kb16` | Pre-quiet CC0 `keep-noisy` (collapsed) | `0.02935` | `2.516` | `2.569` | `2.431` | **`3.824`** | `112.35` | `47.1 / 118.5 / 121.0 / 114.5 / 180.1` |
| 24 | `G5c_quiet_1024p_kb16` | Quiet CC0 `1024p/kb16` | `0.02369` | `3.941` | `4.232` | `5.505` | **`10.661`** | `127.3` | `74.9 / 295.4 / 317.1 / 412.6 / 799.0` |

**Key Structural Observations & Why `G5c` (`kb=16`) Requires Server-Day `2.0B` Scale:**
- **Pre-quiet CC0 collapse vs quiet restoration:** All five pre-quiet `keep-noisy` CC0 nets (`G3a_cc0`, `G3a_distill`, `G5a/b/c_cc0`) collapsed (`Q/P = 3.028..3.824`, `R/P = 2.092..2.431` with `R < N` piece inversion, `m4_wdl_mse = 0.02775..0.02941`). All fourteen quiet CC0 nets (`G3b`, `G3b_distill`, `9/9 S2Q`, `G5a/b/c_quiet`) consistently show non-collapsed ratios (`Q/P = 10.308..10.707`, `R/P = 5.349..5.542`, `m4_wdl_mse = 0.02252..0.02369`).
- **Why `G5c_quiet_1024p_kb16` slightly overfits at `~2M` CC0 rows:** `kb=16` (`25,577,704` bytes = `24.39 MiB`) doubles the input-feature bucket parameter table relative to `kb=8` (`1024p/kb8 = 12.21 MiB`), splitting `2,000,004` raw CC0 rows (`1,839,070` post-in-check/conflict, further filtered by `--skip-fqs-noisy`) across 16 king zones. Consequently, `G5c_quiet_1024p_kb16` fits training loss tighter (`0.000323` vs `0.00053` for `G5a`) while slightly degrading held-out diagnostics: `m4_wdl_mse` (`0.02369` vs `0.0232` for `G5a`), `r0203_quiet_mix60` (`0.023211` vs `0.022675`), and `syz_draw_med_cp` (`43.6 cp` vs `27.4 cp`).
- **Why Server-Day `2.0B` resolves `kb=16` capacity (`SERVER_DAY_ARCH_SCALING_BRIEF.md:50`):** At `2.0B` usable positions (`~1,000x` larger than the `2M` suite), `forge_v3p.king_layout(16)` achieves `3.333` bits entropy with **`0.578%` minimum bucket share = `~23.1M` perspectives even in the rarest king bucket**, eliminating `2M` bucket sparsity while incurring only `-0.61%` NPS (`2,940,975` vs `2,959,061`) to target opposite-side castling (`opp_side_castling`). Final `1024p/kb16` vs `1536p/kb8` (`0.7374x` NPS) selection remains strictly governed by declared `2,000g @ 6+0.06` matches on Server Day.

---

## 4. `OPUS_R1` Live `768w` Twin Diagnostics & Mandatory Wording Boundary

### 4.1 Completed Twin Diagnostics (`r1_summary.json` & `r1_keep_summary.json`)

Both standalone `768w` SCReLU twins trained on the identical `r0178..r0202` (`25`-round) `.cache-n0c1.npz` window via `pipeline/forge_train_v3.py` (`hidden=768`, `epochs=40`, `lr=0.0005`, `batch_size=8192`, `lr_cycles=auto`, `w1_decay=0.3`, `mix=0.75`, `distill_net=b_full.pt`, `distill_weight=0.2`, `teacher_once=true`, `seed=1`), differing solely by omitting vs passing `--keep-noisy`:

| Diagnostic Metric (`eval_full`) | `OPUS_R1_live768_skipnoisy` (`r1_summary.json`) | `OPUS_R1_live768_keepnoisy_twin` (`r1_keep_summary.json`) |
|---|---|---|
| Finished / Elapsed (`s`) | `2026-11-28 02:40:58` / `5447.2s` | `2026-11-28 06:37:53` / `2575.4s` |
| `net_bytes` / `net_sha256` | `9,463,528` / `4902fe653e575c0c73ab78aed18fb6d2a10c8f33c895160cb5b68b1bdb9b21ec` | `9,463,528` / `8b1158aad16d882063da6673efa1584ac0cb4382cb3358964bdb03bb487b02e7` |
| `sanity_flag_count` (`sanity_flags`) | `1` (`S5_dead_draws`) | `3` (`S1_startpos`, `S2_start_vs_e4`, `S5_dead_draws`) |
| `S1_startpos` / `S1_after_1e4` | `+42` / `-10` | `+101` / `+25` |
| `S2_start_plus_e4` / `S2_white_part` / `S2_stm_part` | `+32` / `26.0` / `16.0` | `+126` / `38.0` / `63.0` |
| `S3_flip_max_diff` / `S4_mirror_max_diff` | `0` / `0` | `0` / `0` |
| `m4_wdl_mse` / `m4_corr` (`m4_n=4000`) | `0.01314` / `0.7601` | `0.01226` / `0.7849` |
| `m4_opp_wing_wdl_mse` (`n=718`) | `0.01606` | `0.01612` |
| `m4_mid20_26_ols_piece_cp` (`P/N/B/R/Q`, `tempo`) | `76.7 / 267.6 / 304.1 / 383.9 / 691.1`, `1.6` | `53.2 / 135.8 / 166.9 / 209.3 / 325.8`, `18.8` |
| Scale-Free `Q/P` / `R/P` (`OLS_SCALEFREE_COMPARISON.json`) | `9.01` / `5.005` (`u = 162.15`) | `6.124` / `3.934` (`u = 201.05`) |
| `ob0_ob1_cliff_median_jump_cp` (`n=100`) | `108.5 cp` | `126.0 cp` |

### 4.2 Active `OPUS_R1` SPRT Match & Mandatory `G3b vs G3a` Wording Rule

- **Active Match (`R1_TWIN_DECLARATION.json`, `amendment_for_r1_test_size`):** `OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k` (`task-7807`) is currently running and **pending**. Both sides run `C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe` (`sha256: 5e6f333b95b7ceda01a599a713d6bad536633b235dc73b409e1f12c1bb809011`) on `UHO_Lichess_4852_v1.epd`, `nodes = 250000`, `concurrency = 8`, `seed = 202611951`, normalized `SPRT [0, 10]` (`elo0 = 0`, `elo1 = 10`, `alpha = 0.05`, `beta = 0.05`, `max_games = 3000`). The `7` blind games from the cancelled initial `1,000g` launch remain excluded and preserved intact (`OPUS-2811-KEEP-THE-SPRT`).
- **Mandatory Wording Rule (`OPUS_TO_NEON.md:3113-3115`):** The `G3b vs G3a` CC0 match results (`G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k`: `+699.72 [+642.27, +784.63]`, `972-21-7`; `G3b_skipnoisy_vs_G3a_eqret_1000g_50k`: `+651.27 [+597.55, +727.83]`, `967-20-13`) strictly establish that **"keep-noisy breaks V3P nets on CC0 data"**. They MUST NEVER be cited as an Elo gain of `skip-noisy` on live `768w` SCReLU; the live `768w` decision rests solely on the active `OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k` match.

---

## 5. Locked Server-Day `2.0B` Default Recipe

All scripts on disk in `C:\nnue-lab\neon\forge_fixes\` and `C:\nnue-lab\neon\forge_fixes\serverday_v3\` enforce the clean, minimalist Server-Day `2.0B` pipeline without unconfirmed Stage-2 weighting or rescoring heuristics:

### 5.1 Stage 1 — CC0 Self-Play Datagen (`gen_cc0_selfgame_fqs.py`)
- **Opening Book:** `C:\nnue-lab\neon\forge_fixes\book_cc0_clean.epd` (`233,104` openings, `0` UHO overlap) + `startpos_frac = 0.10` (`write_min_ply = 0` on startpos, `2` on book games) + optional `wide_div_frac` (`4`/`5` random plies).
- **Exact 50/50 Post-Random STM Parity (`gen_cc0_selfgame_fqs.py:211-222`):**
  - `target_turn = chess.WHITE if (games % 2 == 0) else chess.BLACK`
  - Book games (`random_plies == 2`): `rp = 2 if (b0.turn == target_turn) else 1`
  - Wide-diversity games: `rp = 4 if (b0.turn == target_turn) else 5`
  - Startpos games: `rp = games % 3`
- **Integrity Rules & Crash Safety:** `plylimit_skipped` filter, Syzygy 3-4-5 endgame adjudication (`--tablebase-dir`), `--drop-draw-conflicts` (`default=True`), FQS1 metadata bit-flags (`bit0=noisy`, `bit1=in_check`, `bit2=swing_ge200`, `bit3=draw_conflict_ge600`, `bits4..6=output_bucket`), and atomic `.part -> os.replace` `.fqs.z` shard writes with `--resume`.

### 5.2 Stage 2 — Bucketed Parallel Dedup (`serverday_v3/run_dedup_buckets_v3.sh` -> `partition_fqs_buckets.py`)
- **Locked Parameters (`run_dedup_buckets_v3.sh:16-32`):**
  - `BUCKETS=128`, `WORKERS=32`, `DEDUP_MODE=avg` (`sqrt(k)` weights clamped `[128, 192]`), `SHARD_ROWS=500000`, `--flush-rows 65536`, `COMP_LEVEL=3`, `--drop-draw-conflict 600`.
- **Mandatory Flag Discipline (Conceptual `--skip-noisy` + `--skip-check`):**
  - Passes **`--skip-noisy`** explicitly (`bit0=0`, mandatory because keep-noisy breaks V3P nets on CC0 data).
  - Enforces **`bit1=0` (in-check drop)** by **omitting** `--keep-in-check` (`partition_fqs_buckets.py:439`: `skip_in_check=(not args.keep_in_check)` defaults to `True`).
- **Post-Dedup Integrity Gate (`run_dedup_buckets_v3.sh:35-45`):** Asserts zero `.part` leftovers, `summary.json` present, and `t1_corrupt == 0`.

### 5.3 Stage 3 — Streaming GPU Training (`serverday_v3/run_train_stream_gpu_v3.sh` -> `train_v3p_stream.py`)
- **Locked Minimalist Hyperparameters (`run_train_stream_gpu_v3.sh:18-28`):**
  - **Primary Architecture:** `HIDDEN=1024`, `KING_BUCKETS=16` (`1024p/kb16`, `-0.61%` NPS vs `kb8`).
  - **Optional Second Arm:** `HIDDEN=1536`, `KING_BUCKETS=8` (`1536p/kb8`, `0.7374x` NPS, run on the exact same deduped shards and judged solely by declared `2,000g @ 6+0.06` matches).
  - **Optimizer & Loss Defaults:** `EPOCHS=20`, `LR=0.0008`, `LR_CYCLES=2`, `BATCH_SIZE=16384`, `MIX=0.85`, **`LOSS_POW=2.0`**, **`OB_REWEIGHT=none`** (omits `--ob-reweight` when `"none"`), `ANCHOR_REPEAT=25`, `SEED=1`, `--use-shard-weights`, `--save-cycles`.
- **Mandatory Quiet / In-Check Flag Discipline (Conceptual `--skip-fqs-noisy` + `--skip-check`):**
  - Passes **`--skip-fqs-noisy`** explicitly (`bit0=0`).
  - Enforces **`bit1=0` (in-check drop)** by **omitting** `--keep-fqs-in-check` in `train_v3p_stream.py:202` (`mask_bits = (1 if args.skip_fqs_noisy else 0) | (0 if args.keep_fqs_in_check else 2)` -> `mask_bits = 3`). *(Equivalently, standalone `train_v3p.py:313,437` drops `bit1` by default unless `--keep-fqs-check` / `--keep-fqs-in-check` is passed.)*
- **3 Frozen Disjoint Anchors (`C:\nnue-lab\neon\forge_fixes\anchors\`):**
  1. `dead_draws_20k_s5disjoint.fqs.z`
  2. `won_endings_syzygy_20k.fqs.z`
  3. `opening_ply012_anchors.fqs.z`
