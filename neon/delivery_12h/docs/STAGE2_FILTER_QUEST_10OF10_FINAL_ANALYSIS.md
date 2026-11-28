# Stage-2 Filter Quest `10 / 10` Final Scientific Analysis (`FORGENN3-P` Clean Quiet + `OPUS_R1` Status)

**Document ID:** `W9-STREAM-B-STAGE2-10OF10-FINAL`  
**Exclusive Deliverable Path:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave9\streamB_stage2_10of10_science\STAGE2_FILTER_QUEST_10OF10_FINAL_ANALYSIS.md`  
**Live Disk Snapshot Timestamp (UTC):** **`2026-11-28T14:11:22Z`**  
**Supersedes:** `C:\nnue-lab\neon\filter_quest\STAGE2_FILTER_QUEST_SUMMARY.md` (`2026-11-27 22:42:28`, pre-skipnoisy runs) and `C:\nnue-lab\neon\forge_fixes\teamwork_wave8\streamB_filter_science\FILTER_QUEST_STAGE2_INTERIM_SCIENCE.md` (`2026-11-28T10:15:52Z`, `6/10` interim snapshot).

---

## Executive Summary & Epistemic Governance Header

### Governance & Integrity Rules (Mandatory)
1. **R5 Integrity Mandate (Diagnostics $\neq$ Elo):** Training loss (`final_train_loss`), validation MSE (`m4_wdl_mse`), M4/SF19/`r0203` quiet-mix60 scorecards, Syzygy heldout probes (`syz_draw_med_cp`, `syz_win_ok_pct`), and middlegame OLS piece slopes/ratios are **strictly diagnostic** — NEVER claimed, implied, or used as substitutes for fastchess Elo.
2. **Opus `01:12 PC` Rule (`OPUS_TO_NEON.md:3022`):** *"The Stage-2 50k matches are filters only. A winner needs 250k before it counts."* Every `S2Q_*` and `G3b vs G3a` match in Section 1 is a `1,000`-game `@ 50k`-node filter/ablation reading; no Stage-2 filter lead is declared a Server-Day winner until its declared `600g @ 250k` confirmation completes.
3. **No-Pooling Rule (`STAGE2_250K_CONFIRMATIONS_DECLARATION.json:10`):** `50k` filter matches are NEVER pooled with `250k` confirmation matches (`"Fresh seeds; NEVER pooled with 50k filter matches. Each arm is judged solely by its own 600g @ 250k 95% pentanomial Elo CI."`).
4. **`OPUS-2811-OLS-CAUTION` (`OPUS_TO_NEON.md:2990–3001`):** Different nets have different output scales. Cross-net OLS material comparisons MUST use **scale-free ratios** (`Q/P`, `R/P`, `B/P`, `N/P`) or **`net_sanity` unit-normalized centipawns** (`u = (S6_Q + S6_R + S6_B + S6_N) / 20`, `X_cp = 100 * X / u`), never unscaled raw OLS piece values. Moreover, middlegame OLS over self-play positions reflects dynamic imbalance/compensation, not quiet-leaf material pricing.
5. **Direct On-Disk Grounding:** Every number in this report is verified directly from JSONs, binary `.fqs.z` shards, and source scripts on disk at `2026-11-28T14:11:22Z`. No partial `.out` game scores from actively running jobs are cited as match outcomes.

### Live Active Job Check (`2026-11-28T14:11:22Z`)
- **`S2Q_G4b_obreweight_vs_G3b_600g_250k_CONFIRM` (`task-7698`, `seed=202611960`):** **ACTIVELY RUNNING** (`declaration_20261128_055501.json`, `fastchess_20261128_055501.out`, and `games_20261128_055501.pgn` present on disk; `summary.json` does **not** exist yet).
- **`S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_600g_250k_CONFIRM` (`seed=202611961`) & `S2Q_G4a_losspow25_vs_G3b_600g_250k_CONFIRM` (`seed=202611962`):** **PENDING** in `STAGE2_250K_CONFIRMATIONS_DECLARATION.json` (match directories not yet created).
- **`OPUS_R1_live768_keepnoisy_twin` (`task-7697`):** **ACTIVELY TRAINING ON GPU** (`declaration.json` present at `996 B`; `cand.fnn3` and `r1_keep_summary.json` do **not** exist yet).
- **`OPUS_R1_skip_vs_R1_keep_1000g_250k` (`seed=202611951`) & `OPUS_R1_skip_vs_r0067_1000g_250k` (`seed=202611952`):** **PENDING** in `R1_TWIN_DECLARATION.json` (awaiting `OPUS_R1_live768_keepnoisy_twin` completion).

### Five-Part Scientific Overview
1. **Proven Mandatory (`FORGENN3-P`):** `--skip-fqs-noisy` (`bit0=0`) + `--skip-check` (`bit1=0`) are mandatory on `FORGENN3-P`, backed by `G3b vs G3a` `+699.72` Elo (equal-raw) and `+651.27` Elo (equal-retained) and enforced in `serverday_v3/run_dedup_buckets_v3.sh` and `run_train_stream_gpu_v3.sh`.
2. **Top-3 `50k` Leads Under Active `600g @ 250k` Confirmation:** `S2Q_G4b_obreweight` (`+14.95`, `LOS 96.29%`), `S2Q_EXP_R1b_2pct_oppcastle` (`+14.25`, `LOS 96.33%`, showing a clear dose-response over `0.5%` `EXP-R1` `+3.82`), and `S2Q_G4a_losspow25` (`+8.34`, `LOS 84.74%`).
3. **Quality-vs-Volume Discovery (`EXP-F1`):** Dropping `5.344%` (`81,448 / 1,524,213`) saturated `|score| >= 800 cp` quiet rows improves per-row quality (`+12.17`, `LOS 91.84%` at equal retained rows `1,442,765`), but loses `-8.69` (`LOS 13.43%`) at equal raw budget (`2,000,004`) in the finite `2M`-row regime.
4. **Falsified / Rejected Tier-2 Ideas (`50k` / `2M`):** Unweighted `first` dedup (`-10.43`, `-13.026%` quiet rows), `sqrt(k)`-capped `dedup_avg` (`-9.38` vs `first`), and `EXP-W3` soft weighting (`-13.21` vs `dedup_avg`; `-1.04` vs `F1_hard`) all fail to improve `50k` playing strength on `2M` CC0 and are **not** enabled on Server Day.
5. **Open Live `768w` Question (`OPUS_R1`):** Completed `OPUS_R1_live768_skipnoisy` passed `Master Gates --quick` (`hard_pass: true`, `PASS_WITH_ADVISORY_FLAGS`) and shifted diagnostic probes (`Q/P = 9.01`, `R/P = 5.01`, `ob0_ob1_cliff = 108.5 cp`, `S1`/`S2` pass), which are **strictly diagnostic**. The live `768w` verdict awaits `OPUS_R1_live768_keepnoisy_twin` and `OPUS_R1_skip_vs_R1_keep_1000g_250k` (`95%` Elo CI lower bound `> 0`).

---

## Section 1 — Complete 12-Row Stage-2 Match Table (`1,000g @ 50k`)

### 1.1 Shared Match Protocol & Integrity Verification
Verified directly against all `12` `C:\nnue-lab\neon\forge_fixes\matches\<name>\summary.json` files and disk binaries/books/nets:
- **Engine Binary (both `cand_exe` and `base_exe` across `12/12`):** `C:\nnue-lab\neon\forge_fixes\builds\v3p_fused_v3_engine.exe`  
  `sha256`: `c5c939f52f9a139d71c3287e7591a48347577f57aec0caf7c2c0cafc8ebe68f6`
- **Opening Book (`12/12`):** `C:/nnue-lab/tools/book/UHO_Lichess_4852_v1.epd`  
  `sha256`: `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`
- **Fixed Schedule & UCI Options:** `games = 1000` (`500` paired openings), `nodes = 50000`, `tc = ""`, `concurrency = 6`, `Threads = 1`, `Hash = 16`, `OwnBook = false`, `NNUEArch = true`, plus `47` identical search UCI flags (`51` total keys in both `cand_uci` and `base_uci`, differing ONLY in `NNUEArchFile`).
- **Execution Integrity (`12/12`):** `time_losses = 0`, `illegal_moves = 0`, `disconnects = 0` (`0/0/0`), `exit_code = 0`, `finished = true`, `heat.seconds_lost = 0`, `heat.changes = 0` (`heat.cpu_max_c` between `76.0°C` and `86.0°C`).

### 1.2 All 12 Completed Stage-2 `1,000g @ 50k` Matches (`2` Noisy-Ablation + `10/10` Clean Quiet)

| # | Exact Match Folder (`C:\nnue-lab\neon\forge_fixes\matches\...`) | Cand Net -> Base Net | Seed | W–D–L | Score% | `pentanomial_exact` Elo `[95% CI]` | `z` | Exact LOS% (`top` fastchess LOS%, `Δ`) | `ptnml` `[0,1,2,3,4]` | Sec | TL/IL/DC |
|---:|---|---|---:|---|---:|---|---:|---:|---|---:|---:|
| 1 | `G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k` | `G3b_cc0_skip_noisy` -> `G3a_cc0_keep_noisy` | `202611601` | `972–21–7` | `98.25%` | **`+699.72`** `[+642.27, +784.63]` | `+141.297` | `100.00%` (`100.00%`, `0.00`) | `[0, 0, 7, 21, 472]` | `285.6` | `0/0/0` |
| 2 | `G3b_skipnoisy_vs_G3a_eqret_1000g_50k` | `G3b_cc0_skip_noisy` -> `G3a_cc0_keep_noisy_eqret` | `202611608` | `967–20–13` | `97.70%` | **`+651.27`** `[+597.55, +727.83]` | `+115.771` | `100.00%` (`100.00%`, `0.00`) | `[0, 0, 13, 20, 467]` | `288.7` | `0/0/0` |
| 3 | `S2Q_G4a_losspow25_vs_G3b_1000g_50k` | `s2q_g4a_losspow25` -> `G3b_cc0_skip_noisy` | `202611801` | `319–386–295` | `51.20%` | **`+8.34`** `[-7.60, +24.32]` | `+1.025` | `84.74%` (`84.76%`, `-0.02`) | `[40, 107, 177, 141, 35]` | `601.1` | `0/0/0` |
| 4 | `S2Q_G4b_obreweight_vs_G3b_1000g_50k` | `s2q_g4b_obreweight` -> `G3b_cc0_skip_noisy` | `202611802` | `327–389–284` | `52.15%` | **`+14.95`** `[-1.47, +31.43]` | `+1.785` | `96.29%` (`96.30%`, `-0.01`) | `[39, 104, 181, 127, 49]` | `640.2` | `0/0/0` |
| 5 | `S2Q_EXP_F1_hard_vs_G3b_eqraw_1000g_50k` | `s2q_f1_hard` -> `G3b_cc0_skip_noisy` | `202611803` | `294–387–319` | `48.75%` | **`-8.69`** `[-24.11, +6.70]` | `-1.106` | `13.43%` (`13.41%`, `+0.02`) | `[34, 131, 196, 104, 35]` | `634.3` | `0/0/0` |
| 6 | `S2Q_EXP_F1_hard_vs_ctrl_eqret_1000g_50k` | `s2q_f1_hard` -> `s2q_f1_ctrl_eqret` | `202611804` | `343–349–308` | `51.75%` | **`+12.17`** `[-4.93, +29.32]` | `+1.395` | `91.84%` (`91.86%`, `-0.02`) | `[44, 110, 169, 121, 56]` | `596.8` | `0/0/0` |
| 7 | `S2Q_EXP_F2_first_vs_G3b_1000g_50k` | `s2q_f2_dedup_first` -> `G3b_cc0_skip_noisy` | `202611805` | `294–382–324` | `48.50%` | **`-10.43`** `[-26.46, +5.57]` | `-1.278` | `10.07%` (`10.05%`, `+0.02`) | `[40, 130, 191, 98, 41]` | `604.7` | `0/0/0` |
| 8 | `S2Q_EXP_F2_avg_vs_first_1000g_50k` | `s2q_f2_dedup_avg` -> `s2q_f2_dedup_first` | `202611806` | `280–413–307` | `48.65%` | **`-9.38`** `[-24.96, +6.16]` | `-1.183` | `11.83%` (`11.81%`, `+0.02`) | `[37, 128, 195, 105, 35]` | `580.8` | `0/0/0` |
| 9 | `S2Q_EXP_R1_rescore16k_vs_dedup_avg_1000g_50k` | `s2q_r1_rescore16k_0p5pct` -> `s2q_f2_dedup_avg` | `202611807` | `291–429–280` | `50.55%` | **`+3.82`** `[-11.16, +18.82]` | `+0.500` | `69.15%` (`69.17%`, `-0.02`) | `[29, 115, 206, 116, 34]` | `505.4` | `0/0/0` |
| 10 | `S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_1000g_50k` | `s2q_r1b_rescore16k_2pct_oppcastle` -> `s2q_f2_dedup_avg` | `202611808` | `316–409–275` | `52.05%` | **`+14.25`** `[-1.35, +29.92]` | `+1.790` | `96.33%` (`96.34%`, `-0.01`) | `[32, 106, 192, 129, 41]` | `507.4` | `0/0/0` |
| 11 | `S2Q_EXP_W3_softweight_vs_dedup_avg_1000g_50k` | `s2q_w3_soft_weight` -> `s2q_f2_dedup_avg` | `202611809` | `277–408–315` | `48.10%` | **`-13.21`** `[-28.86, +2.39]` | `-1.660` | `4.85%` (`4.83%`, `+0.02`) | `[43, 123, 193, 111, 30]` | `501.4` | `0/0/0` |
| 12 | `S2Q_EXP_W3_softweight_vs_f1_hard_1000g_50k` | `s2q_w3_soft_weight` -> `s2q_f1_hard` | `202611810` | `315–367–318` | `49.85%` | **`-1.04`** `[-17.11, +15.03]` | `-0.127` | `44.94%` (`44.93%`, `+0.01`) | `[42, 116, 182, 123, 37]` | `472.4` | `0/0/0` |

**LOS Rounding Explanation (`0.01%–0.02%`):** Across all 10 `S2Q_*` matches (`#3..#12`), `pentanomial_exact.los_pct` differs from top-level `summary.json` fastchess `los_pct` by **`0.01%`** on `#4, #10, #12` and **`0.02%`** on `#3, #5, #6, #7, #8, #9, #11`. This arises because `pentanomial_exact` uses sample Bessel-corrected pair variance (`N - 1 = 499` denominator) with exact $\Phi(z)$, whereas fastchess reports its own normal-approximation LOS (`N = 500` denominator / internal rounding). Throughout this report, `pentanomial_exact` values are cited as primary, with top-level fastchess `los_pct` shown in parentheses above.

### 1.3 Verified Disk SHA-256 Checksums for All 12 Nets

| Net Name | Exact File Path on Disk | Verified Full SHA-256 Digest |
|---|---|---|
| `G3b_cc0_skip_noisy` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3b_cc0_skip_noisy\cand.fnn3` | `cb07450d3b22d2e6de0a54deee9fae9d3ec34fe0983e354aa1cf3f76e3331358` |
| `G3a_cc0_keep_noisy` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3a_cc0_keep_noisy\cand.fnn3` | `5c9a4164d44bccbebd5f8c2a371e73a673ed0a8c5720425ead4b1758c6ee3dc8` |
| `G3a_cc0_keep_noisy_eqret` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3a_cc0_keep_noisy_eqret\cand.fnn3` | `56563e49185959fac1ff80410e7a7084e5fb6d0e8b926adeba201990bfde861e` |
| `s2q_g4a_losspow25` | `C:\nnue-lab\neon\filter_quest\stage2_runs_quiet\s2q_g4a_losspow25\cand.fnn3` | `1d9604b9c8068a759e8252323688be0f36d85de2431192aa3381a393c9bccd5e` |
| `s2q_g4b_obreweight` | `C:\nnue-lab\neon\filter_quest\stage2_runs_quiet\s2q_g4b_obreweight\cand.fnn3` | `b378b753e4799b0c7972b6c50a338e62afd0f408ddad9f4da348b3e3ab9c400a` |
| `s2q_f1_hard` | `C:\nnue-lab\neon\filter_quest\stage2_runs_quiet\s2q_f1_hard\cand.fnn3` | `4529b7f2c7c111c0b0b77f526654e975869fe2664c1df0977ecadda519230cb1` |
| `s2q_f1_ctrl_eqret` | `C:\nnue-lab\neon\filter_quest\stage2_runs_quiet\s2q_f1_ctrl_eqret\cand.fnn3` | `8a8f44ca6021f45f239814077cd62072b310a21894db13ceed8bcc359d9befb5` |
| `s2q_f2_dedup_first` | `C:\nnue-lab\neon\filter_quest\stage2_runs_quiet\s2q_f2_dedup_first\cand.fnn3` | `d0adc6c6dc46ef8bd51f1ffc5b2119a3d5b768e1a00d63e9ca5ca3034df04aea` |
| `s2q_f2_dedup_avg` | `C:\nnue-lab\neon\filter_quest\stage2_runs_quiet\s2q_f2_dedup_avg\cand.fnn3` | `b5d27d2d18107e6485c9bcb56c31f3b8862377a3ac2350d781e158a33ca79a33` |
| `s2q_r1_rescore16k_0p5pct` | `C:\nnue-lab\neon\filter_quest\stage2_runs_quiet\s2q_r1_rescore16k_0p5pct\cand.fnn3` | `55a55a507f61a49910ca91c619583cb2b6d8c462169a31cdbc46aead6ef9511a` |
| `s2q_r1b_rescore16k_2pct_oppcastle` | `C:\nnue-lab\neon\filter_quest\stage2_runs_quiet\s2q_r1b_rescore16k_2pct_oppcastle\cand.fnn3` | `611f21a1498b0736cb0847a7a3b0d607b3ec975c764e5cd4cbabc5d0206c4f59` |
| `s2q_w3_soft_weight` | `C:\nnue-lab\neon\filter_quest\stage2_runs_quiet\s2q_w3_soft_weight\cand.fnn3` | `930edd0f4e95e0bce75e74e414cbc79f8466fe23ccb3b332aafe3acbddd12dff` |

---

## Section 2 — Five-Part Scientific Synthesis

### Part 1 — Proven Mandatory (`FORGENN3-P`): `--skip-fqs-noisy` (`bit0=0`) + `--skip-check` (`bit1=0`)

1. **Decisive Ablation Proof (`50k`):**
   - **Equal-Raw (`2,000,004` raw rows):** `G3b_cc0_skip_noisy` (`1,524,213` quiet rows) defeats `G3a_cc0_keep_noisy` (`1,839,070` rows = `1,524,213` quiet + `314,857` `bit0=1` noisy) by **`+699.72 [+642.27, +784.63]` Elo** (`972–21–7`, `98.25%`, `z = +141.297`, `ptnml = [0, 0, 7, 21, 472]`).
   - **Equal-Retained (`1,524,213` rows):** Controlling for exact training row count via `--max-rows 1524213` (`G3a_cc0_keep_noisy_eqret`), `G3b_cc0_skip_noisy` still wins by **`+651.27 [+597.55, +727.83]` Elo** (`967–20–13`, `97.70%`, `z = +115.771`, `ptnml = [0, 0, 13, 20, 467]`).
2. **Diagnostic Mechanism & Scope Boundary:**
   - In `cc0_shards_4k_v2_nodrawconf`, `314,857 / 1,839,070` (`17.12%`) kept records carry `bit0=1` (captures/promotions). Retaining those noisy mid-exchange rows on scratch `FORGENN3-P` collapses middlegame OLS ratios (diagnostic only: `G3a` `Q/P = 3.630`, `R/P = 2.293`, `R < N` inversion; `G3a_eqret` `Q/P = 3.532`, `R/P = 2.361`) versus `G3b` (`Q/P = 10.539`, `R/P = 5.415`).
   - **Scope Discipline (`OPUS_TO_NEON.md:2963–2969`, `NEON_TO_OPUS.md:807–812`):** `G3b vs G3a` proves that `--keep-noisy` breaks a `FORGENN3-P` net trained from `2M` CC0 shards; it does **not** prove a gain on live `768w` SCReLU (`r0067` has `Q/P = 5.967`, `R/P = 3.924`, no `R < N` inversion), which is tested separately by `OPUS_R1` (Part 5).
3. **Production Enforcement in `serverday_v3`:**
   - `train_v3p.py:409,436–438`: constructs `mask_bits = (1 if skip_noisy else 0) | (2 if skip_check else 0)` where `skip_check = not args.keep_fqs_check` (default `True`, enforcing `bit1=0`), and `--skip-fqs-noisy` sets `bit0=0`.
   - `serverday_v3/run_dedup_buckets_v3.sh:4–6,22–32`: invokes `partition_fqs_buckets.py` with `--skip-noisy` (`bit0=0`), omits `--keep-in-check` (`bit1=0`), and enforces `--drop-draw-conflict 600` + `--dedup-mode avg`.
   - `serverday_v3/run_train_stream_gpu_v3.sh:5–8,38–58`: double-defense wrapper — unconditionally passes `--skip-fqs-noisy`, keeps `bit1=0`, `--use-shard-weights`, injects all `3` frozen disjoint anchors (`ANCHOR_REPEAT=25` per superbatch), and defaults to `--hidden 1024 --king-buckets 16 --ob-reweight cc0 --loss-pow 2.0`.

---

### Part 2 — Top-3 Positive `50k` Filter Leads Under Active `600g @ 250k` Confirmation

Per `C:\nnue-lab\neon\forge_fixes\run_post_bundle_250k_queue.py:72–90` and `STAGE2_250K_CONFIRMATIONS_DECLARATION.json` (`written: "2026-11-28 04:47:31 PC"`, `concurrency = 8 <= 12`, `no_pooling_rule` enforced), scanning all `10` completed `S2Q_*/summary.json` files, excluding the `eqret` volume control, filtering `pentanomial_exact.elo >= 5.0`, and sorting descending yields the exact Top-3 `50k` filter leads now queued for fresh-seed `600g @ 250k` confirmation (`v3p_fused_v3_engine.exe` both sides):

| Rank | Declared `250k` Match Name | Origin `50k` Filter Result (`LOS%`) | `250k` Seed | Status at `2026-11-28T14:11:22Z` |
|---:|---|---|---:|---|
| 1 | `S2Q_G4b_obreweight_vs_G3b_600g_250k_CONFIRM` | **`+14.95`** `[-1.47, +31.43]` (`96.29%`) | `202611960` | **ACTIVE** (`declaration_20261128_055501.json`; `summary.json` pending) |
| 2 | `S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_600g_250k_CONFIRM` | **`+14.25`** `[-1.35, +29.92]` (`96.33%`) | `202611961` | **PENDING** (queued behind #1) |
| 3 | `S2Q_G4a_losspow25_vs_G3b_600g_250k_CONFIRM` | **`+8.34`** `[-7.60, +24.32]` (`84.74%`) | `202611962` | **PENDING** (queued behind #2) |

#### Exact Filter / Training Mechanics & Telemetry for the Top-3 Leads
1. **`S2Q_G4b_obreweight` (`+14.95 [-1.47, +31.43]`, `LOS 96.29%` at `50k`):**
   - **Mechanics (`train_v3p.py:577–598`):** With `--ob-reweight cc0`, computes piece count `npcs` directly from `packed` nibbles (`(pk & 0x0F != 0) + ((pk >> 4) & 0x0F != 0)` clamped to `[2, 32]`), maps to output bucket `ob = ((npcs - 2) // 4).clamp(0, 7)`, and multiplies sample weights by `ob_lut = [1.50, 1.089, 1.167, 0.978, 0.922, 0.883, 0.891, 0.70]` (upweighting sparse endgame buckets `OB0..OB2`, downweighting opening/early middlegame `OB7` at `0.70x`), then mean-normalizes non-anchor weights to `1.0` while keeping the `161,684` anchor rows strictly exempt at `1.0`.
   - **Note:** `G4b` uses the exact same `1,524,213` quiet rows as `G3b` (`0` rows dropped, `34.4s` GPU train time) and is already wired as `OB_REWEIGHT="${OB_REWEIGHT:-cc0}"` in `serverday_v3/run_train_stream_gpu_v3.sh:26`, pending `seed=202611960` `250k` confirmation.
2. **`S2Q_EXP_R1b_rescore16k_2pct_oppcastle` (`+14.25 [-1.35, +29.92]`, `LOS 96.33%` at `50k` vs `dedup_avg`):**
   - **Dose-Response Over `EXP-R1` (`0.5%`):** Selective `16k`-softnode Forge-only (`r0067` + `ucinewgame` per FEN) rescoring on top of `cc0_f2_dedup_avg` scales cleanly with fraction and opposite-side-castled prioritization:
     - `EXP-R1` (`0.5%`, `prioritize_opp_castle=False`, `seed=202611807`): `8,061` selected / `8,060` rescored (`2500+2499+2500+561`), `0` sign flips, shard `mad_delta_cp = 45.86, 48.10, 48.40, 49.19` -> **`+3.82 [-11.16, +18.82]`** (`LOS 69.15%`).
     - `EXP-R1b` (`2.0%`, `--prioritize-opp-castle`, `seed=202611808`): `32,243` selected / `32,241` rescored (`10000+9998+10000+2243`), `26` sign flips (`9+7+8+2`), shard `mad_delta_cp = 35.68, 35.78, 37.68, 34.39` -> **`+14.25 [-1.35, +29.92]`** (`LOS 96.33%`).
   - **Exact Priority Tier Mechanics (`rescore_fqs_selective.py:73–128, 175–177`):** Deterministic stride sampling up to `cap = round(len(arr) * max_frac)` across ordered tiers: `p1` (`flags & 12 != 0` or `res==0 & |sc|>=400`), `p2` (`res!=0 & sc*res<=-200`), `p_opp` (`_opp_side_castle_mask`: White king on files `a–c` and Black king on `f–h` or vice versa, `npcs >= 14`, `|sc| < 450`, targeting the `20.67%` severe WDL error cohort in `SF19_ERROR_TAXONOMY.json`), `p3` (`ob <= 1 & |sc| in [150, 900]`), `p4` (`flags & 1 != 0 & |sc| < 350`). Notice `R1b` tests rescoring **on top of `dedup_avg`** (`1,325,663` quiet rows); if `250k` confirms `+`, testing `R1b` directly on un-deduped `G3b` (`1,524,213` quiet rows) is a natural Server-Day follow-up.
3. **`S2Q_G4a_losspow25` (`+8.34 [-7.60, +24.32]`, `LOS 84.74%` at `50k`):**
   - **Mechanics (`train_v3p.py:662–665`):** Replaces quadratic WDL MSE `(pred - target).pow(2)` (`G3b`) with `--loss-pow 2.5`: `err = (pred - target).abs().clamp(min=1e-7).pow(2.5)` over the identical `1,524,213` quiet rows (`34.8s` GPU train time), penalizing large WDL outliers super-quadratically while flattening tiny-residual gradients.

---

### Part 3 — Quality-vs-Volume Discovery (`EXP-F1`)

1. **Direct Empirical Contrast (`S2Q_EXP_F1_hard` vs `ctrl_eqret` vs `G3b_eqraw`):**
   - **Equal Retained Quiet Volume (`1,442,765` vs `1,442,765`):** `s2q_f1_hard` vs `s2q_f1_ctrl_eqret` (`train_v3p.py:444–466`, `--max-rows 1442765` keeping tail slice `fqs_cat[fqs_drop:]`) scores **`+12.17 [-4.93, +29.32]` Elo** (`343–349–308`, `51.75%`, `z = +1.395`, `LOS 91.84%`).
   - **Equal Raw Input Budget (`2,000,004` raw rows):** `s2q_f1_hard` (`1,442,765` quiet) vs `G3b` (`1,524,213` quiet) scores **`-8.69 [-24.11, +6.70]` Elo** (`294–387–319`, `48.75%`, `z = -1.106`, `LOS 13.43%`).
   - **Two-Sample Separation (`eq-ret` minus `eq-raw`):** $\Delta\mu = 0.5175 - 0.4875 = +3.0000\text{ pp}$ ($z_{\text{diff}} = +1.7766$, $p_{\text{two}} = 0.0756$), corresponding to $\Delta\text{Elo} = +20.85 \pm 23.02$ (`95% CI [-2.17, +43.87]`, one-sided $P(\text{eq-ret} > \text{eq-raw}) = 96.21\%$).
2. **Exact `.fqs.z` Accounting & Filter Mechanism (`filter_fqs_to_fqs.py:136–150`):**
   - Starting from `2,000,004` raw rows (`154,497` `t1_in_check` dropped, `6,437` `t2_draw_conflict >= 600` dropped -> `1,839,070` total = `1,524,213` quiet + `314,857` noisy), `cc0_f1_hard` applies deterministic modulo-100 board hash downsampling (`hs800_p1 = 50` for `|score| in [800, 1199]`, `hs800_p2 = 25` for `|score| >= 1200`), dropping `t2_hs800 = 93,886` rows (`81,448` quiet + `12,438` noisy) to leave **`1,442,765` quiet rows (`-81,448` = `-5.344%` vs `G3b`)**.
   - Removing `5.344%` of saturated mop-up positions (`|score| >= 800`, which carry only `1.20%` of total WDL gradient energy per `PHASE_B_NEARDUP_AND_GRADIENT_ADDENDUM.md`) increases per-row information density (`+12.17` Elo when row count is held equal), **but** in the finite `2M`-row regime (`~181–205` steps/epoch including `161,684` `4x` anchor rows, or `~161–186` excluding anchors), losing `81,448` unique quiet rows imposes a net coverage/step penalty (`-8.69` Elo at equal raw rows).
3. **`2M` vs `2.0B` Server-Day Scaling Implication (`PACKET_IMMEDIATE_LOOP_AND_SERVERDAY_DELTAS.md:82`):**
   - Server Day trains on `~1.4B–2.0B` positions (`~1,000x–1,312x` larger than `2M` CC0). Because hard Tier-2 `hs800` discarding lost `-8.69` Elo at equal raw budget (`2M`), hard Tier-2 discarding (`EXP-F1`) is **not** enabled on Server Day unless re-validated without a volume bottleneck.

---

### Part 4 — Falsified / Rejected Tier-2 Ideas (`50k` / `2M`) & Wave 8 Supersession

All four Tier-2 dataset experiments below delivered **negative** `50k` filter readings on `2M` CC0 and are rejected from Server-Day defaults (`PACKET_IMMEDIATE_LOOP_AND_SERVERDAY_DELTAS.md:82`):

1. **`EXP-F2_first` (`S2Q_EXP_F2_first_vs_G3b_1000g_50k`):** **`-10.43 [-26.46, +5.57]` Elo** (`294–382–324`, `48.50%`, `z = -1.278`, `LOS 10.07%`).
   - **Mechanics (`filter_fqs_to_fqs.py:163–183`):** Cross-shard `blake2b(packed + stm, digest_size=12)` deduplication merges `t2_dedup_merged = 226,906` rows (`198,550` quiet + `28,356` noisy), leaving **`1,325,663` quiet rows (`-198,550` = `-13.026%` vs `G3b`)** at uniform `weight_u8 = 128`. Corroborates `EXP-F1`'s `2M` volume-loss penalty.
2. **`EXP-F2_avg` vs `first` (`S2Q_EXP_F2_avg_vs_first_1000g_50k`):** **`-9.38 [-24.96, +6.16]` Elo** (`280–413–307`, `48.65%`, `z = -1.183`, `LOS 11.83%`).
   - **Mechanics (`filter_fqs_to_fqs.py:184–219`):** Holds exact `1,325,663` quiet rows constant (`0` rows dropped vs `first`), averages `score16` across duplicates (`round(sc_sum / cnt)`), takes majority `res8`, and applies `sqrt(k)`-capped multiplicity weighting `weight_u8 = min(192, max(128, round(128.0 * sqrt(cnt))))` (`mean_weight_u8 = 130.66` all / `131.08` quiet) via `--use-shard-weights`.
   - **Verdict:** Empirically **falsifies** Wave 8's pre-registered `+3 to +12` Elo prediction (`Elo <= 0.0` falsification criterion) at `50k` / `2M`: `score16` averaging + `sqrt(k)` weights did not recover the `-13.026%` dedup volume deficit and underperformed `first` at `50k`. *(Note: `serverday_v3/run_dedup_buckets_v3.sh` keeps `DEDUP_MODE="${DEDUP_MODE:-avg}"` configurable for `2.0B`-row scale where `13%` duplicate suppression behaves differently than `2M`, but at `2M`/`50k` `F2_avg` is negative.)*
3. **`EXP-W3` Soft Weighting (`make_stage2_soft_weight.py:58–73`):**
   - **Mechanics:** Built directly on `cc0_f2_dedup_avg` (`0` rows discarded; `1,612,164` total / `1,325,663` quiet), multiplies `weight_u8` by `0.25` for `|score| >= 1200` (`41,465` all), `0.50` for `800..1199` (`100,311` all), `0.50` for `swing` (`0` rows), and `1.25` for quiet `100..399` (`423,452` quiet rows), clamped to `[16, 255]` (`mean_weight_u8 = 132.78` all / `134.86` quiet).
   - **Match `#11` (`S2Q_EXP_W3_softweight_vs_dedup_avg_1000g_50k`):** **`-13.21 [-28.86, +2.39]` Elo** (`277–408–315`, `48.10%`, `z = -1.660`, `LOS 4.85%`). **Falsifies** Wave 8's `0 to +8` Elo prediction (`<= -5.0` falsification criterion): aggressive `0.25x/0.50x` blowout downweighting + `1.25x` mid-band boost hurt vs `dedup_avg` on identical rows.
   - **Match `#12` (`S2Q_EXP_W3_softweight_vs_f1_hard_1000g_50k`):** **`-1.04 [-17.11, +15.03]` Elo** (`315–367–318`, `49.85%`, `z = -0.127`, `LOS 44.94%`). Statistically flat within Wave 8's predicted `-12 to +3` Elo band while carrying an `-8.12%` quiet-row deficit (`1,325,663` vs `1,442,765`).
4. **How `10/10` Completion Supersedes Wave 8 Interim (`6/10` at `2026-11-28T10:15:52Z`):**
   - At Wave 8 (`6/10`), `#7` was `550/1000` games and `#8..#10` were queued, leaving `S2Q_EXP_F1_hard_vs_ctrl_eqret` (`+12.17`) provisionally listed in the top-3 `>= +5.0` `50k` leads.
   - Completing `#7..#10` changed two conclusions cleanly: (a) `#10` (`#8` in `S2Q_*`) **`S2Q_EXP_R1b` scored `+14.25` (`LOS 96.33%`)**, jumping above `+12.17` to enter the declared `600g @ 250k` Top-3 (`STAGE2_250K_CONFIRMATIONS_DECLARATION.json`, while `run_post_bundle_250k_queue.py:75` also explicitly excludes `eqret`); and (b) `#11` **`S2Q_EXP_W3_softweight_vs_dedup_avg` scored `-13.21` (`LOS 4.85%`)**, decisively falsifying soft weighting (`W3`) at `2M`/`50k`.

---

### Part 5 — Open Live `768w` Question (`OPUS_R1`)

1. **Completed `OPUS_R1_live768_skipnoisy` Artifacts & Gate Status (Strictly Diagnostic — NEVER Elo):**
   - **Net:** `C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy\cand.fnn3` (`9,463,528` bytes, `sha256: 4902fe653e575c0c73ab78aed18fb6d2a10c8f33c895160cb5b68b1bdb9b21ec`, trained `5447.2s`, `finished: "2026-11-28 02:40:58"`).
   - **Recipe (`declaration.json`):** Exact live `FORGENN3` `hidden=768`, `r0178..r0202`, `epochs=40`, `lr=0.0005`, `batch=8192`, `mix=0.75`, `w1-decay=0.3`, `distill=b_full.pt` (`w=0.2`), `seed=1`, differing from live training ONLY by omitting `--keep-noisy`.
   - **`Master Gates --quick` (`master_gate_quick.json` on `base_r15dsg.exe`, `4.3433s`):** `overall_status = "PASS_WITH_ADVISORY_FLAGS"`, **`hard_pass = true`**:
     - `perft`: `PASS` (`6/6`, `perft_5_nodes = 4865609`).
     - `bench`: `PASS` (`default_bench_11`: `371,870 / 122 ms / 3,048,114 nps`; `default_bench_13`: `913,862 / 291 ms / 3,140,419 nps`; `b4_bench_11`: `375,559 / 131 ms / 2,866,862 nps`; `b4_bench_13`: `773,738 / 273 ms / 2,834,205 nps`).
     - `v3_parity`: `PASS` (`FORGENN3`, `hidden=768`, `kb=8`, `ob=8`, `mirror=true`, `120/120` FENs `max_diff_cp = 0`, `ob_covered = "8/8"`, `min_ob_count = 15`).
     - `loader_safety`: `PASS` (`13/13` cases).
     - `net_sanity`: `ADVISORY_FLAGS` (`hard_pass = true`, `flags = ["S5 dead draws", "S7 won endings"]`).

2. **Diagnostic Scorecard Comparison (`OPUS_R1_skip` vs `r0067` vs `G3_FULL25` vs `G3b` — Strictly Diagnostic):**

| Diagnostic Probe | `OPUS_R1_skip` (`768w`, `skip_noisy`) | `r0067` (`768w`, `keep_noisy`) | `G3_FULL25` (`1024p`, `keep_noisy`) | `G3b_cc0_skip_noisy` (`1024p`, `skip_noisy`) |
|---|---:|---:|---:|---:|
| **`unit u = (S6_Q+R+B+N)/20`** | **`162.15`** (`162.2` in `net_sanity`) | `189.55` (`189.6`) | `172.20` (`172.2`) | `124.95` (`125.0`) |
| **`S1_startpos` raw (`unit cp`)** | **`+42` (`+25.9 cp`, PASS)** | `+87` (`+45.9 cp`, flagged) | `-25` (`-14.5 cp`, flagged) | `-25` (`-20.0 cp`, flagged) |
| **`S1_after_1e4` raw (`unit cp`)** | `-10` (`-6.2 cp`) | *(omitted in scorecard)* | `-34` (`-19.7 cp`) | `+33` (`+26.4 cp`) |
| **`S2_start_plus_e4` raw (`unit cp`)** | **`+32` (`+19.7 cp`, PASS)** | `+113` (`+59.6 cp`, flagged) | `-59` (`-34.3 cp`, flagged) | `+8` (`+6.4 cp`) |
| **`S2_white_part` / `S2_stm_part` raw (`cp`)** | `+26.0` (`+16.0 cp`) / `+16.0` (`+9.9 cp`) | *(omitted)* | `+4.5` (`+2.6 cp`) / `-29.5` (`-17.1 cp`) | `-29.0` (`-23.2 cp`) / `+4.0` (`+3.2 cp`) |
| **`S3_flip_max_diff` / `S4_mirror_max_diff`** | `0` / `0` | `0` / `0` | `0` / `0` | `0` / `0` |
| **`S5_dead_draws` raw (`K-K, KN-K, KB-K, KNN-K`)** | `16, -52, -45, 97` | `5, -29, -6, 101` | `15, 5, 23, 51` | `5, 9, 59, 17` |
| **`S6_startpos_minus` raw (`Q, R, B, N, P`)** | `1417, 700, 593, 533, 179` | `1931, 678, 623, 559, 203` | `1502, 795, 589, 558, 201` | `1039, 517, 479, 464, 164` |
| **`S7_won_endings` raw (`KQ-K, KR-K`)** | `1218, 467` (`+751, +288 cp`) | `1697, 442` (`+895, +233 cp`) | `1918, 818` (`+1114, +475 cp`) | `1074, 585` (`+860, +468 cp`) |
| **`m4_wdl_mse` (`n=4000`) / `m4_corr`** | `0.01314` / `0.7601` | `0.01302` / `0.7754` | `0.0114` / `0.8041` | `0.02339` / `0.6334` |
| **`m4_opp_wing_wdl_mse` (`n=718`)** | `0.01606` | `0.01724` | `0.01421` | `0.03083` |
| **`ob0_ob1_cliff_median_jump_cp` (`n=100`)** | **`108.5 cp`** | `143.5 cp` | `133.0 cp` | `203.0 cp` |
| **OLS raw (`P, N, B, R, Q, tempo`)** | `76.7, 267.6, 304.1, 383.9, 691.1, 1.6` | `51.5, 135.7, 167.0, 202.1, 307.3, 18.8` | `47.2, 121.8, 154.5, 199.1, 293.3, 18.4` | `96.4, 373.9, 400.8, 522.0, 1016.0, -10.6` |
| **Scale-free OLS ratios (`Q/P, R/P, B/P, N/P`)** | **`9.01, 5.01, 3.96, 3.49`** (`9.010, 5.005, 3.965, 3.489`) | `5.97, 3.92, 3.24, 2.63` (`5.967, 3.924, 3.243, 2.635`) | `6.21, 4.22, 3.27, 2.58` (`6.214, 4.218, 3.273, 2.581`) | `10.54, 5.41, 4.16, 3.88` (`10.539, 5.415, 4.158, 3.879`) |
| **Unit-normalized OLS (`P/N/B/R/Q` cp)** | `47.3 / 165.0 / 187.5 / 236.8 / 426.2` | `27.2 / 71.6 / 88.1 / 106.6 / 162.1` | `27.4 / 70.7 / 89.7 / 115.6 / 170.3` | `77.2 / 299.2 / 320.8 / 417.8 / 813.1` |
| **`eval_full` `sanity_flags`** | `["S5_dead_draws"]` (`1`) | `["S1_startpos", "S2_start_vs_e4", "S5_dead_draws"]` (`3`) | `["S1_startpos", "S2_start_vs_e4", "S5_dead_draws"]` (`3`) | `["S1_startpos", "S5_dead_draws"]` (`2`) |
| **`master_gate` `net_sanity` v2 flags** | `["S5 dead draws", "S7 won endings"]` (`hard_pass: true`) | *(not run in scorecard)* | `["S1 startpos"]` (`hard_pass: true`) | `["S1 startpos", "S2w start vs 1.e4, White part"]` (`hard_pass: true`) |

3. **Exact Root Cause of `r1_summary.json` (`1` flag) vs `master_gate_quick.json` (`2` flags):**
   - `eval_net_full.py:188–195` (producing `eval_full.json` and `r1_summary.json`) checks Opus v1 thresholds against **raw** eval integers (`KQ-K >= 800`, `KR-K >= 400`, `|draw| <= 50`). Because `OPUS_R1_skip` has raw `KQ-K = 1218 >= 800` and `KR-K = 467 >= 400`, `S7` passes and only `S5` (`KN-K = -52`, `KNN-K = +97`) triggers (`1` flag: `["S5_dead_draws"]`).
   - `C:\nnue-lab\tmp\opus_scratch\netcheck\net_sanity.py` v2 (`lines 13–16, 156–186`, invoked by `master_gate_quick.json`) first divides by `unit u = (1417 + 700 + 593 + 533) / 20 = 162.15` (`162.2` raw/cp): in unit-normalized centipawns, `KQ-K = 100 * 1218 / 162.15 = +751 cp < 800` and `KR-K = 100 * 467 / 162.15 = +288 cp < 400`, triggering `FLAG S7 won endings` alongside `FLAG S5 dead draws` (`KNN-K = +60 cp > 50`). With `strict_net_sanity = false`, `hard_pass = true`.
4. **Declared Decision Path (`R1_TWIN_DECLARATION.json`):**
   - `OPUS_R1_skip` diagnostic shifts (`S1/S2` pass, `Q/P = 9.010`, `R/P = 5.005`, `cliff = 108.5 cp`) are strictly diagnostic (`R5` & `OPUS-2811-OLS-CAUTION`).
   - Playing strength will be decided strictly by fastchess `1,000g @ 250k` (`base_r15dsg.exe` `5e6f333b...`, `concurrency = 8`) once `OPUS_R1_live768_keepnoisy_twin` finishes GPU training:
     1. `OPUS_R1_skip_vs_R1_keep_1000g_250k` (`seed = 202611951`): requires **`95%` Elo CI lower bound `> 0`** to advance to seed-2 replicates and `6+0.06` (`conc = 7`).
     2. `OPUS_R1_skip_vs_r0067_1000g_250k` (`seed = 202611952`): direct `250k` strength check against live `r0067` (`737f1978...`).

---

## Section 3 — Complete GPU Diagnostic & `.fqs.z` Dataset Accounting Appendix

> **STRICTLY DIAGNOSTIC (R5 & `OPUS-2811-OLS-CAUTION`):** None of the training losses, M4 MSEs, `r0203` losses, Syzygy probes, or OLS ratios/values below represent playing strength or Elo. Output scales vary across `G3a` (`u = 114.00`) vs `G3b/S2Q` (`u = 124.95..131.50`), so OLS is reported with scale-free ratios (`Q/P`, `R/P`) and `net_sanity` unit-normalized `Q_cp = 100 * ols_Q / u`.

### 3.1 All 12 Stage-2 GPU Arms (`STAGE2_QUIET_GPU_SUMMARY.json` + `G3a`/`G3b` `metrics.json`)

| Arm (`FORGENN3-P` 1024w kb8, ep=40, seed=1) | Quiet Rows (`max_rows`) | Train (`s`) | Train Loss | `r0203` Quiet Mix60 | `r0203` All Mix60 | M4 WDL MSE | M4 Corr | `ols_Q` (raw) | `Q/P` | `R/P` | `u` | Unit `Q_cp` | Cliff (`cp`) | Syz Draw Med (`cp`) | Syz Win OK% | `eval_full` Flags |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `G3a_cc0_keep_noisy` | `1,524,213` quiet + `314,857` noisy (`0`) | `44.5` | `0.000847` | `0.034220` | `0.038178` | `0.02941` | `0.5074` | `199.3` | `3.630` | `2.293` | `114.00` | `174.8` | `188.5` | `36.0` | `99.40%` | `S1, S5` |
| `G3a_cc0_keep_noisy_eqret` | `1,524,213` total (`max_rows=1524213`) | `36.7` | `0.000761` | `0.034481` | `0.038408` | `0.02918` | `0.5081` | `185.1` | `3.532` | `2.361` | `112.45` | `164.6` | `170.5` | `33.8` | `99.35%` | `S1, S5` |
| `G3b_cc0_skip_noisy` | `1,524,213` (`0`) | `36.4` | `0.000407` | `0.022602` | `0.031738` | `0.02339` | `0.6334` | `1016.0` | `10.539` | `5.415` | `124.95` | `813.1` | `203.0` | `29.6` | `99.30%` | `S1, S5` |
| `s2q_g4a_losspow25` | `1,524,213` (`0`) | `34.8` | `0.000123` | `0.022562` | `0.031496` | `0.02310` | `0.6340` | `988.5` | `10.308` | `5.375` | `126.35` | `782.4` | `180.5` | `29.3` | `99.30%` | `S1` |
| `s2q_g4b_obreweight` | `1,524,213` (`0`) | `34.4` | `0.000406` | `0.022586` | `0.031777` | `0.02350` | `0.6335` | `1022.3` | `10.507` | `5.435` | `127.10` | `804.3` | `197.0` | `28.3` | `99.30%` | `S1` |
| `s2q_f1_hard` | `1,442,765` (`0`) | `32.9` | `0.000404` | `0.022626` | `0.031527` | `0.02311` | `0.6310` | `1009.1` | `10.511` | `5.349` | `126.05` | `800.6` | `200.0` | `29.4` | `99.30%` | `S1` |
| `s2q_f1_ctrl_eqret` | `1,442,765` (`max_rows=1442765`) | `32.7` | `0.000379` | `0.022717` | `0.031688` | `0.02353` | `0.6288` | `1011.8` | `10.707` | `5.447` | `127.20` | `795.4` | `203.5` | `27.5` | `99.30%` | `S1, S5` |
| `s2q_f2_dedup_first` | `1,325,663` (`0`) | `30.7` | `0.000444` | `0.022601` | `0.031632` | `0.02318` | `0.6344` | `1033.8` | `10.581` | `5.433` | `130.95` | `789.5` | `181.0` | `27.5` | `99.30%` | `[]` |
| `s2q_f2_dedup_avg` | `1,325,663` (`0`) | `30.7` | `0.000441` | `0.022652` | `0.031685` | `0.02336` | `0.6330` | `1026.5` | `10.626` | `5.481` | `131.50` | `780.6` | `179.0` | `27.4` | `99.30%` | `[]` |
| `s2q_r1_rescore16k_0p5pct` | `1,325,663` (`0`) | `31.0` | `0.000444` | `0.022611` | `0.031689` | `0.02325` | `0.6339` | `1033.1` | `10.662` | `5.454` | `130.25` | `793.2` | `189.0` | `26.9` | `99.30%` | `S5` |
| `s2q_r1b_rescore16k_2pct_oppcastle` | `1,325,663` (`0`) | `31.2` | `0.000441` | `0.022605` | `0.031604` | `0.02318` | `0.6344` | `1025.2` | `10.602` | `5.479` | `131.45` | `779.9` | `180.0` | `27.4` | `99.30%` | `[]` |
| `s2q_w3_soft_weight` | `1,325,663` (`0`) | `31.1` | `0.000444` | `0.022667` | `0.031659` | `0.02308` | `0.6309` | `1017.0` | `10.378` | `5.401` | `129.95` | `782.6` | `175.5` | `26.9` | `99.25%` | `[]` |

### 3.2 Binary `.fqs.z` Shard & Anchor Row Accounting

Verified directly by decompressing every `FQS1` shard (`8B` header + `38B` records) via `zlib`:
- **`cc0_shards_4k_v2_nodrawconf`:** `raw_rows = 2,000,004`, `t1_corrupt = 0`, `t1_in_check = 154,497` (`bit1`), `t2_draw_conflict = 6,437` (`res8==0 & |score16|>=600`), `kept_rows = 1,839,070` = **`1,524,213` quiet** (`(flags & 3) == 0`) + **`314,857` noisy** (`bit0=1, bit1=0`, `17.12%`).
- **`cc0_f1_hard`:** drops `t2_hs800 = 93,886` (`81,448` quiet + `12,438` noisy) -> `kept_rows = 1,745,184` = **`1,442,765` quiet (`-5.344%`)** + `302,419` noisy (`mean_weight_u8 = 128.00`).
- **`cc0_f2_dedup_first`:** `t2_dedup_merged = 226,906` (`198,550` quiet + `28,356` noisy) -> `kept_rows = 1,612,164` = **`1,325,663` quiet (`-13.026%`)** + `286,501` noisy (`mean_weight_u8 = 128.00`).
- **`cc0_f2_dedup_avg`:** identical `1,612,164` (`1,325,663` quiet + `286,501` noisy), `sqrt(k)` weights -> `mean_weight_u8 = 130.66` all (`131.08` quiet).
- **`cc0_r1_rescore16k_0p5pct`:** `1,612,164` (`1,325,663` quiet), `8,061` selected / `8,060` rescored (`0` sign flips, shard `mad_delta_cp = 45.86, 48.10, 48.40, 49.19`), `mean_weight_u8 = 130.66`.
- **`cc0_r1b_rescore16k_2pct_oppcastle`:** `1,612,164` (`1,325,663` quiet), `32,243` selected / `32,241` rescored (`26` sign flips, shard `mad_delta_cp = 35.68, 35.78, 37.68, 34.39`), `mean_weight_u8 = 130.66`.
- **`cc0_w3_soft_weight`:** `1,612,164` (`1,325,663` quiet), `discarded_rows = 0`, `downweighted_ge1200 = 41,465`, `downweighted_800_1199 = 100,311`, `downweighted_swing = 0`, `boosted_info_100_399_quiet = 423,452`, `mean_weight_u8 = 132.78` all (`134.86` quiet).
- **Disjoint Anchors (`train_v3p.py:440,516–524,554–556,591–598`):** All `G3*` & `s2q_*` runs inject `3` anchors (`dead_draws_20k_s5disjoint.fqs.z` `20,000` + `won_endings_syzygy_20k.fqs.z` `20,000` + `opening_ply012_anchors.fqs.z` `421` = `40,421 x 4 = 161,684` rows), strictly exempt from non-anchor mean normalization (`w = 1.0`).

---

## Section 4 — Source & Verification Ledger

All facts, SHA-256 digests, match records, GPU diagnostics, and `.fqs.z` counts in this document were verified read-only (`CPU-only`, `CUDA_VISIBLE_DEVICES="" HIP_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1`, `C:\nnue-lab\venv101\Scripts\python.exe -B`) against:
- **Match Summaries & Declarations:** `C:\nnue-lab\neon\forge_fixes\matches\{G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k,G3b_skipnoisy_vs_G3a_eqret_1000g_50k,S2Q_*}\summary.json`, `C:\nnue-lab\neon\forge_fixes\STAGE2_250K_CONFIRMATIONS_DECLARATION.json`, `C:\nnue-lab\neon\forge_fixes\R1_TWIN_DECLARATION.json`, plus active status checks on `S2Q_G4b_obreweight_vs_G3b_600g_250k_CONFIRM\` and `gpu_runs\OPUS_R1_live768_keepnoisy_twin\`.
- **GPU Diagnostics & Scorecards:** `C:\nnue-lab\neon\filter_quest\STAGE2_QUIET_GPU_SUMMARY.json`, `C:\nnue-lab\neon\forge_fixes\gpu_runs\{G3a_cc0_keep_noisy,G3a_cc0_keep_noisy_eqret,G3b_cc0_skip_noisy}\{metrics,eval_full,heldout_syzygy_4k}.json`, `C:\nnue-lab\neon\filter_quest\stage2_runs_quiet\s2q_*\{metrics,eval_full,heldout_syzygy_4k}.json`, `C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy\{r1_summary,master_gate_quick,eval_full,declaration}.json`, `C:\nnue-lab\neon\forge_fixes\baseline_r0067_scorecard.json`, `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\{eval_full_cand,master_gate_full_cand}.json`, `C:\nnue-lab\neon\forge_fixes\OLS_SCALEFREE_COMPARISON.md`.
- **Filter, Pipeline, & Governance Sources:** `C:\nnue-lab\neon\filter_quest\{filter_fqs_to_fqs.py,make_stage2_soft_weight.py,run_stage2_clean_skipnoisy_gpu.py,run_stage2_filter_ablations.py}`, `C:\nnue-lab\neon\forge_fixes\{rescore_fqs_selective.py,train_v3p.py,run_post_bundle_250k_queue.py,eval_net_full.py,PACKET_IMMEDIATE_LOOP_AND_SERVERDAY_DELTAS.md}`, `C:\nnue-lab\neon\forge_fixes\serverday_v3\{run_dedup_buckets_v3.sh,run_train_stream_gpu_v3.sh}`, `C:\nnue-lab\tmp\opus_scratch\netcheck\net_sanity.py`, `C:\nnue-lab\neon\filter_quest\stage2_data\cc0_*\{summary,rescore_summary}.json`, `C:\nnue-lab\neon\forge_fixes\cc0_shards_4k_v2_nodrawconf\summary.json`, and `C:\nnue-lab\neon\{OPUS_TO_NEON,NEON_TO_OPUS}.md`.
