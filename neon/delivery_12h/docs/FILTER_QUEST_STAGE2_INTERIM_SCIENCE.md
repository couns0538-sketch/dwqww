# Filter Quest Stage-2 Interim Science & 19-Net Scale-Free OLS Analysis

**Document ID:** `W8-STREAM-B-INTERIM-SCIENCE`  
**Exclusive Deliverable Path:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave8\streamB_filter_science\FILTER_QUEST_STAGE2_INTERIM_SCIENCE.md`  
**Live Disk Snapshot Timestamp (UTC):** **`2026-11-28T10:15:52Z`**  
**Scope:** Synthesis of all completed Stage-2 Clean Quiet (`S2Q_*`) matches on disk, statistical mechanics of the `EXP-F1` quality-vs-volume discovery, empirical falsification of `EXP-F2_avg > EXP-F2_first` at `50k` with revised falsifiable predictions for `EXP-W3`, and the complete 19-net scale-free OLS & `net_sanity` unit-normalized diagnostic analysis.

---

## Executive Summary

1. **Stage-2 Clean Quiet (`S2Q_*`) Live Match Census (`6 / 10` Complete at `2026-11-28T10:15:52Z`):** Six of ten `1,000`-game `@ 50k`-node clean-quiet filter matches have finished with `0` time losses, illegal moves, or disconnects on `v3p_fused_v3_engine.exe` (`c5c939f5...`):
   - **Leading `50k` filter candidates vs `G3b` (`cb07450d...`):** `S2Q_G4b_obreweight` (`+14.95 [-1.47, +31.43]` Elo, `LOS 96.29%`) and `S2Q_G4a_losspow25` (`+8.34 [-7.60, +24.32]` Elo, `LOS 84.74%`). Both remain **`50k` filters only** and require `600g @ 250k` confirmation (`run_post_bundle_250k_queue.py`) per the Opus `01:12 PC` rule (`OPUS_TO_NEON.md:3022`).
   - **Equal-raw volume losses & `EXP-F2_avg` falsification:** Both `S2Q_EXP_F1_hard_vs_G3b_eqraw` (`-8.69 [-24.11, +6.70]` Elo, `LOS 13.43%`) and `S2Q_EXP_F2_first_vs_G3b` (`-10.43 [-26.46, +5.57]` Elo, `LOS 10.07%`) lost at equal-raw budget (`2,000,004` raw rows), whereas holding retained quiet rows constant (`1,442,765`) flipped `EXP-F1` to `+12.17 [-4.93, +29.32]` Elo (`LOS 91.84%`). Newly completed **`S2Q_EXP_F2_avg_vs_first_1000g_50k`** (`2026-11-28T10:11:12Z`) scored **`280–413–307` (`48.65%`), `-9.38 [-24.96, +6.16]` Elo (`z = -1.183`, `LOS 11.83%`)**, empirically **falsifying** the pre-registered `F2_avg > F2_first` hypothesis (`+3 to +12` Elo) at `50k` filter depth.
   - **Active & queued:** `S2Q_EXP_R1_rescore16k_vs_dedup_avg_1000g_50k` (`#7`) is actively running (`550 / 1,000` PGN games finished at `10:15:52Z`), with `3` matches queued (`#8 EXP-R1b`, `#9 EXP-W3 vs dedup_avg`, `#10 EXP-W3 vs F1_hard`).
2. **The `EXP-F1` Quality-vs-Volume Discovery & Revised `EXP-W3` Outlook:** Direct `.fqs.z` shard audits establish that `EXP-F1` drops **`5.344%`** (`81,448 / 1,524,213`) of quiet `(flags & 3) == 0` rows (reconciling an earlier `~16%` total-vs-quiet shorthand), while `EXP-F2` cross-shard deduplication drops **`13.026%`** (`198,550 / 1,524,213`). Comparing `EXP-F1` `eq-ret` vs `eq-raw` yields a two-sample separation of $\Delta\mu = +3.0000\text{ pp}$ ($z = +1.7766$, $p_{\text{two}} = 0.0756$), or **$\Delta\text{Elo} = +20.85 \pm 11.75$** (`95% CI [-2.17, +43.87]`, one-sided $P(\text{eq-ret} > \text{eq-raw}) = 96.21\%$). In the finite `2M` CC0 regime (`181–205` steps/epoch including `4x` anchors `161,684` per `train_v3p.py:603`, or `161–186` excluding anchors; `~1,000x–1,312x` smaller than Server Day's `2.0B` rows), discarding `5.3%–13.0%` of unique quiet rows imposes a net coverage/step penalty, and `score16` averaging + `sqrt(k)` weights (`F2_avg`, `ESS = 99.08%`) failed to recover `dedup`'s `-13.026%` deficit (`-9.38` Elo vs `F2_first` at `50k`). Consequently, while `EXP-W3` (`#9` vs `dedup_avg`, `0` rows dropped, boosting `100..399 cp` quiet weight share `31.97% -> 38.83%`, `ESS = 94.50%`) still isolates the `1.25x` contested-band boost on equal `1,325,663`-row footing (`0 to +8` Elo predicted), `EXP-W3 vs F1_hard` (`#10`) must overcome **both** its **`-8.12%` quiet-row (`-13.17%` ESS) structural headwind** (`1,325,663` vs `1,442,765`) **and** `dedup_avg`'s apparent `50k` penalty (`-12 to +3` Elo predicted).
3. **19-Net Scale-Free OLS & `net_sanity` Unit-Normalized Contrast (`OPUS-2811-OLS-CAUTION`):** Across all `19` audited nets in `OLS_SCALEFREE_COMPARISON.json` (`r0202_scorecard.json` is absent on disk), normalizing middlegame OLS slopes by pawn slope (`X/P`) and `net_sanity` unit `u = (S6_Q + S6_R + S6_B + S6_N) / 20` (`100 * X / u`) reveals a sharp structural split:
   - All `5` `2M`-CC0 `keep_noisy` nets (`G3a`, `G3a_distill`, `G5a`, `G5b`, `G5c`) exhibit severe ratio compression (`Q/P = 3.028..3.824`, `R/P = 2.092..2.431`) and **Rook-below-Knight inversion (`R < N` across 5/5 nets, including all 3 `G5a/b/c` architectures: `R - N = -16.4..-4.5` raw / `-15.6..-4.0` unit cp)**.
   - All `11` `--skip-fqs-noisy` nets (`G3b`, `G3b_distill`, and `9/9 S2Q`) recover tight classical ratios (`Q/P = 10.308..10.707`, `R/P = 5.349..5.481`, `B/P = 4.110..4.238`, `N/P = 3.799..3.956`), net-unit Queen values (`779.9..813.1 cp`), and `R > N` (`+140.9..+153.2` raw / `+110.7..+119.7` unit cp).
   - Per `OPUS-2811-OLS-CAUTION`, middlegame OLS over self-play positions is strictly a diagnostic probe of eval slope under temporary/compensated material imbalance (live `r0067` shows `S6_Q = 1931` / `1018.7` unit cp on quiet startpos-minus-Q); therefore OLS never determines live-loop changes. The live `768w` decision rests exclusively on `OPUS_R1_skip_vs_R1_keep_1000g_250k` (`95%` Elo LB `> 0`), where `OPUS_R1_live768_skipnoisy` is currently training on GPU (`declaration.json` present; no `.fnn3` yet at `2026-11-28T10:15:52Z`).

---

## Epistemic Governance & Integrity Header

- **Exact Live Disk Check Timestamp:** **`2026-11-28T10:15:52Z`**
  - `C:\nnue-lab\neon\forge_fixes\matches\S2Q_*`: `6` completed (`summary.json` present, now including `S2Q_EXP_F2_avg_vs_first_1000g_50k` finished at `2026-11-28T10:11:12Z`), `1` running (`S2Q_EXP_R1_rescore16k_vs_dedup_avg_1000g_50k`, `550/1,000` PGN results), `3` queued in `run_stage2_clean_skipnoisy_matches.py`.
  - `C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy\`: contains `['_tmp_cache', 'declaration.json']` (GPU training in progress; no `cand.pt`, `cand.fnn3`, `eval_full.json`, or `r1_summary.json` on disk). `C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_keepnoisy_twin\` does not exist yet.
- **R5 Integrity Mandate:** Training losses (`final_train_loss`), validation MSE (`m4_wdl_mse`), M4/SF19/r0203 quiet-mix60 scorecards (`final_eval_r0203_quiet_mix60`), Syzygy heldout probes (`syz_draw_med_cp`, `syz_win_ok_pct`), and middlegame OLS piece values/ratios are strictly diagnostic metrics — **never** claimed or implied as Elo strength.
- **No-Pooling Discipline:** `50k`-node filter matches (`1,000g`) are never pooled with `250k`-node confirmation matches (`600g` or `1,000g`), and `600g` screens are never pooled with `1,000g` confirmations.
- **Opus `01:12 PC` `50k`-Filter-Only Rule (`C:\nnue-lab\neon\OPUS_TO_NEON.md:3022`):**
  > *"The Stage-2 50k matches are filters only. A winner needs 250k before it counts."*
  Every `S2Q_*` Elo figure reported in Sections 1 and 2 is a `50k` filter reading and requires `250k` verification (`run_post_bundle_250k_queue.py`) before any placement or winner claim.
- **`OPUS-2811-OLS-CAUTION` (`C:\nnue-lab\neon\OPUS_TO_NEON.md:2990-3001`, `01:04 PC, 28 Nov`):**
  - **Unit discipline (`lines 2994–2996`):** Output scales differ across nets; raw OLS cp slopes are comparable across nets only via scale-free ratios (`Q/P`, `R/P`, `B/P`, `N/P`) or after division by each net's `net_sanity` unit `u = (S6_Q + S6_R + S6_B + S6_N) / 20` (`100 * raw / u`).
  - **Interpretive discipline (`lines 2998–3000`):** Self-play middlegame OLS measures eval sensitivity under dynamic imbalance/compensation, not quiet-leaf material value (`r0067` has `S6_Q = 1931` raw / `1018.7` unit cp). Thus OLS compression is a probe reading, not proof of playing weakness, and `R1-skip vs R1-keep` @ `250k` decides the live loop.

---

## Section 1 — Complete Stage-2 Clean Quiet (`S2Q_*`) Match Census

### 1.1 Shared Match Protocol & Baseline

All Stage-2 Clean Quiet GPU arms (`G3b` and the `9` `s2q_*` variants) were trained under identical `train_v3p.py` settings: `FORGENN3-P`, `hidden=1024`, `king_buckets=8`, `out_buckets=8`, `epochs=40`, `batch_size=8192`, `lr=0.0005`, `lr_cycles="auto"`, `w1_decay=0.3`, `ob_smooth=2e-6`, `mix=0.85`, `seed=1`, `--skip-fqs-noisy` (`(flags & 3) == 0`), plus `anchor_repeat=4` across three exact-anchor shards (`dead_draws_20k_s5disjoint.fqs.z` `20,000` + `won_endings_syzygy_20k.fqs.z` `20,000` + `opening_ply012_anchors.fqs.z` `421` = `40,421 x 4 = 161,684` anchor rows exempt at weight `1.0`).

All `S2Q_*` head-to-head filter matches in `C:\nnue-lab\neon\filter_quest\run_stage2_clean_skipnoisy_matches.py` share exact paired parameters (verified across all `summary.json` `declaration` blocks):
- **Engine binary (both sides):** `C:\nnue-lab\neon\forge_fixes\builds\v3p_fused_v3_engine.exe` (`sha256: c5c939f52f9a139d71c3287e7591a48347577f57aec0caf7c2c0cafc8ebe68f6`)
- **Opening book:** `C:/nnue-lab/tools/book/UHO_Lichess_4852_v1.epd` (`sha256: 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`)
- **Schedule:** `games = 1000` (`500` paired openings), `nodes = 50000`, `tc = ""`, `concurrency = 6`, `Threads = 1`, `Hash = 16`, `OwnBook = false`, `NNUEArch = true`, plus 46 identical Big Tune UCI options (`51` total keys in `cand_uci`/`base_uci`, `50` identical, minus `5` base/net keys `Threads`, `Hash`, `OwnBook`, `NNUEArch`, `NNUEArchFile`; e.g., `MateAlphaGuard=true`, `CuckooRep=true`, `HistRework=2`, `TtPruneV2=true`, `CorrHistV2=true`).
- **Common Stage-2 Baseline (`G3b`):** `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3b_cc0_skip_noisy\cand.fnn3` (`sha256: cb07450d3b22d2e6de0a54deee9fae9d3ec34fe0983e354aa1cf3f76e3331358`).

### 1.2 Completed `S2Q_*` Filter Matches (`6 / 10` at `2026-11-28T10:15:52Z`)

| Match Directory (`C:\nnue-lab\neon\forge_fixes\matches\...`) | Cand Net (`SHA-256` prefix) | Base Net (`SHA-256` prefix) | Seed | W–D–L | Score% | Ptnml `[0,1,2,3,4]` | Exact Ptnml Elo `[95% CI]` | `z` / Exact LOS% (`fastchess LOS%`) | TL/IL/DC (`Duration`) | `50k` Filter Status |
|---|---|---|---:|---|---:|---|---:|---:|---:|---|
| `S2Q_G4a_losspow25_vs_G3b_1000g_50k` | `s2q_g4a_losspow25` (`1d9604b9...`) | `G3b` (`cb07450d...`) | `202611801` | `319–386–295` | `51.20%` | `[40, 107, 177, 141, 35]` | **`+8.34`** `[-7.60, +24.32]` | `+1.025 / 84.74%` (`84.76%`) | `0/0/0` (`601.1s`) | `50k` filter (`>= +5.0`, queued for `250k`) |
| `S2Q_G4b_obreweight_vs_G3b_1000g_50k` | `s2q_g4b_obreweight` (`b378b753...`) | `G3b` (`cb07450d...`) | `202611802` | `327–389–284` | `52.15%` | `[39, 104, 181, 127, 49]` | **`+14.95`** `[-1.47, +31.43]` | `+1.785 / 96.29%` (`96.30%`) | `0/0/0` (`640.2s`) | `50k` filter (`>= +5.0`, queued for `250k`) |
| `S2Q_EXP_F1_hard_vs_G3b_eqraw_1000g_50k` | `s2q_f1_hard` (`4529b7f2...`) | `G3b` (`cb07450d...`) | `202611803` | `294–387–319` | `48.75%` | `[34, 131, 196, 104, 35]` | **`-8.69`** `[-24.11, +6.70]` | `-1.106 / 13.43%` (`13.41%`) | `0/0/0` (`634.3s`) | `50k` filter (equal-raw negative) |
| `S2Q_EXP_F1_hard_vs_ctrl_eqret_1000g_50k` | `s2q_f1_hard` (`4529b7f2...`) | `s2q_f1_ctrl_eqret` (`8a8f44ca...`) | `202611804` | `343–349–308` | `51.75%` | `[44, 110, 169, 121, 56]` | **`+12.17`** `[-4.93, +29.32]` | `+1.395 / 91.84%` (`91.86%`) | `0/0/0` (`596.8s`) | `50k` filter (`>= +5.0`, `eq-ret` lead) |
| `S2Q_EXP_F2_first_vs_G3b_1000g_50k` | `s2q_f2_dedup_first` (`d0adc6c6...`) | `G3b` (`cb07450d...`) | `202611805` | `294–382–324` | `48.50%` | `[40, 130, 191, 98, 41]` | **`-10.43`** `[-26.46, +5.57]` | `-1.278 / 10.07%` (`10.05%`) | `0/0/0` (`604.7s`) | `50k` filter (equal-raw negative) |
| `S2Q_EXP_F2_avg_vs_first_1000g_50k` | `s2q_f2_dedup_avg` (`b5d27d2d...`) | `s2q_f2_dedup_first` (`d0adc6c6...`) | `202611806` | `280–413–307` | `48.65%` | `[37, 128, 195, 105, 35]` | **`-9.38`** `[-24.96, +6.16]` | `-1.183 / 11.83%` (`11.81%`) | `0/0/0` (`580.8s`) | `50k` filter (falsifies `F2_avg > F2_first`) |

*Full candidate net SHA-256 digests (`cand.fnn3`):*
- `s2q_g4a_losspow25`: `1d9604b9c8068a759e8252323688be0f36d85de2431192aa3381a393c9bccd5e`
- `s2q_g4b_obreweight`: `b378b753e4799b0c7972b6c50a338e62afd0f408ddad9f4da348b3e3ab9c400a`
- `s2q_f1_hard`: `4529b7f2c7c111c0b0b77f526654e975869fe2664c1df0977ecadda519230cb1`
- `s2q_f1_ctrl_eqret`: `8a8f44ca6021f45f239814077cd62072b310a21894db13ceed8bcc359d9befb5`
- `s2q_f2_dedup_first`: `d0adc6c6dc46ef8bd51f1ffc5b2119a3d5b768e1a00d63e9ca5ca3034df04aea`
- `s2q_f2_dedup_avg`: `b5d27d2d18107e6485c9bcb56c31f3b8862377a3ac2350d781e158a33ca79a33`

### 1.3 Running & Queued `S2Q_*` Matches (`4 / 10` Remaining at `2026-11-28T10:15:52Z`)

| Queue # / Status | Match Directory | Cand Net (`SHA-256` prefix) | Base Net (`SHA-256` prefix) | Seed | Live State at `2026-11-28T10:15:52Z` |
|---|---|---|---|---:|---|
| **#7 (RUNNING)** | `S2Q_EXP_R1_rescore16k_vs_dedup_avg_1000g_50k` | `s2q_r1_rescore16k_0p5pct` (`55a55a50...`) | `s2q_f2_dedup_avg` (`b5d27d2d...`) | `202611807` | `declaration_20261128_021112.json` (`02:11:12 PC`); **`550 / 1,000`** PGN results recorded; no `summary.json` yet |
| **#8 (QUEUED)** | `S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_1000g_50k` | `s2q_r1b_rescore16k_2pct_oppcastle` (`611f21a1...`) | `s2q_f2_dedup_avg` (`b5d27d2d...`) | `202611808` | Queued in `run_stage2_clean_skipnoisy_matches.py:64-65` |
| **#9 (QUEUED)** | `S2Q_EXP_W3_softweight_vs_dedup_avg_1000g_50k` | `s2q_w3_soft_weight` (`930edd0f...`) | `s2q_f2_dedup_avg` (`b5d27d2d...`) | `202611809` | Queued in `run_stage2_clean_skipnoisy_matches.py:66-67` |
| **#10 (QUEUED)** | `S2Q_EXP_W3_softweight_vs_f1_hard_1000g_50k` | `s2q_w3_soft_weight` (`930edd0f...`) | `s2q_f1_hard` (`4529b7f2...`) | `202611810` | Queued in `run_stage2_clean_skipnoisy_matches.py:68-69` |

### 1.4 `250k` Confirmation Pipeline (`run_post_bundle_250k_queue.py`)

Under `C:\nnue-lab\neon\forge_fixes\run_post_bundle_250k_queue.py:64-80`, once the Owner Bundle clock phase and `OPUS_R1_skip_vs_R1_keep_1000g_250k` / `OPUS_R1_skip_vs_r0067_1000g_250k` complete, the top **3** `S2Q_*` `50k` filter matches with point estimate **`elo >= +5.0`** are automatically re-run at **`600g @ 250k`** (`v3p_fused_v3_engine.exe` both sides, `concurrency = 8`, fresh seeds `202611960 + idx`, suffix `_600g_250k_CONFIRM`), strictly **never pooled** with `50k` filter results. At the `2026-11-28T10:15:52Z` snapshot, the three provisional `>= +5.0` leads remain `S2Q_G4b_obreweight` (`+14.95`), `S2Q_EXP_F1_hard_vs_ctrl_eqret` (`+12.17`), and `S2Q_G4a_losspow25` (`+8.34`), subject to change if `#7..#10` score above them.

---

## Section 2 — Statistical Analysis of `EXP-F1` Quality-vs-Volume Discovery & `EXP-F2`/`EXP-W3` Predictions

### 2.1 Exact `.fqs.z` `(flags & 3) == 0` Dataset Census

Direct binary reads of all `.fqs.z` shards across `cc0_shards_4k_v2_nodrawconf` and `neon\filter_quest\stage2_data\cc0_*` establish exact quiet (`(flags & 3) == 0`, i.e., neither `bit0` noisy nor `bit1` in-check) and noisy (`bit0 = 1`) row counts, drops, `weight_u8` distributions, and Effective Sample Size (`ESS = (\sum w_i)^2 / \sum w_i^2`):

| Arm / Dataset | Raw Input Rows | `t1_in_check` (`bit1`) | `t2_draw_conf` (`>=600`) | `t2_hs800` / `t2_dedup` | Shard `kept_rows` (`noisy` + `quiet`) | Trained Main Quiet Rows (`(flags & 3)==0`) | Quiet Delta vs `G3b` | `train_v3p.py` Extra Flags | Quiet `weight_u8` (`mean / min / max`) | Quiet `ESS` (`ESS / N_q`) | Train Time (`s`) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| **`G3b`** (`cc0_shards_4k_v2_nodrawconf`) | `2,000,004` | `154,497` | `6,437` | `0` / `0` | `1,839,070` (`314,857` + `1,524,213`) | **`1,524,213`** | `0` (`0.000%`) | baseline (`loss_pow=2.0`) | `128.00 / 128 / 128` | `1,524,213.0` (`100.00%`) | `36.4` |
| **`G4a`** (`s2q_g4a_losspow25`) | `2,000,004` | `154,497` | `6,437` | `0` / `0` | `1,839,070` | **`1,524,213`** | `0` (`0.000%`) | `--loss-pow 2.5` | `128.00 / 128 / 128` | `1,524,213.0` (`100.00%`) | `34.8` |
| **`G4b`** (`s2q_g4b_obreweight`) | `2,000,004` | `154,497` | `6,437` | `0` / `0` | `1,839,070` | **`1,524,213`** | `0` (`0.000%`) | `--ob-reweight cc0` (`[1.50..0.70]`) | `128.00` (in-mem normalized `0.7002..1.5005`) | `1,474,995.3` (`96.77%`) | `34.4` |
| **`EXP-F1_hard`** (`cc0_f1_hard`) | `2,000,004` | `154,497` | `6,437` | **`93,886`** (`hs800`) / `0` | `1,745,184` (`302,419` + `1,442,765`) | **`1,442,765`** | **`-81,448`** (**`-5.344%`**) | none | `128.00 / 128 / 128` | `1,442,765.0` (`100.00%`) | `32.9` |
| **`EXP-F1 ctrl_eqret`** (`s2q_f1_ctrl_eqret`) | `2,000,004` | `154,497` | `6,437` | tail slice (`fqs_cat[fqs_drop:]`) | `1,839,070` (truncated) | **`1,442,765`** | **`-81,448`** (`-5.344%`) | `--max-rows 1442765` | `128.00 / 128 / 128` | `1,442,765.0` (`100.00%`) | `32.7` |
| **`EXP-F2_first`** (`cc0_f2_dedup_first`) | `2,000,004` | `154,497` | `6,437` | `0` / **`226,906`** | `1,612,164` (`286,501` + `1,325,663`) | **`1,325,663`** | **`-198,550`** (**`-13.026%`**) | none (`weight=128`) | `128.00 / 128 / 128` | `1,325,663.0` (`100.00%`) | `30.7` |
| **`EXP-F2_avg`** (`cc0_f2_dedup_avg`) | `2,000,004` | `154,497` | `6,437` | `0` / **`226,906`** | `1,612,164` (`286,501` + `1,325,663`) | **`1,325,663`** | **`-198,550`** (`-13.026%`) | `--use-shard-weights` (`sqrt(k)`) | `131.08 / 128 / 192` (all: `130.66`) | `1,313,489.6` (`99.08%`) | `30.7` |
| **`EXP-W3`** (`cc0_w3_soft_weight`) | `2,000,004` | `154,497` | `6,437` | `0` dropped from `F2_avg` (`226,906` merged) | `1,612,164` (`286,501` + `1,325,663`) | **`1,325,663`** | **`-198,550`** (`-13.026%` vs `G3b`; **`0%`** vs `F2_avg`) | `--use-shard-weights` (`0.25/0.50/1.25x`) | **`134.86`** `/ 32 / 240` (all: **`132.78`**) | **`1,252,773.3`** (**`94.50%`**) | `31.1` |
| **`EXP-R1`** (`cc0_r1_rescore16k_0p5pct`) | `2,000,004` | `154,497` | `6,437` | `8,061` sel / `8,060` rescored (`16k`) | `1,612,164` | **`1,325,663`** | `-198,550` (`-13.026%`) | `--use-shard-weights` (`0` sign flips, MAD `45.9–49.2 cp`) | `131.08 / 128 / 192` | `1,313,489.6` (`99.08%`) | `31.0` |
| **`EXP-R1b`** (`cc0_r1b_rescore16k_2pct_oppcastle`) | `2,000,004` | `154,497` | `6,437` | `32,243` sel / `32,241` rescored (`16k`) | `1,612,164` | **`1,325,663`** | `-198,550` (`-13.026%`) | `--use-shard-weights` (`26` sign flips, MAD `34.4–37.7 cp`) | `131.08 / 128 / 192` | `1,313,489.6` (`99.08%`) | `31.2` |

*Notes on exact shard accounting and prior shorthand reconciliation:*
- Across all seven `.fqs.z` shard directories above, `flags & 4` (`swing`) and `flags & 8` (`draw_conf`) are `0`, and `t1_in_check` (`154,497`) rows were already removed during shard creation (`chk = 0` in `.fqs.z`).
- `cc0_f1_hard` `t2_hs800 = 93,886` consists of **`81,448` quiet** rows plus `12,438` noisy rows (`314,857 -> 302,419`).
- `cc0_f2_dedup_first` / `cc0_f2_dedup_avg` `t2_dedup_merged = 226,906` consists of **`198,550` quiet** rows plus `28,356` noisy rows (`314,857 -> 286,501`).
- **Reconciliation of earlier `~16%` shorthand:** Earlier survey notes (`teamwork_explorer_survey_1/handoff.md:116`) cited `~16%` dropped by comparing `f1_quiet_kept` (`1,442,765`) against total `kept_rows` (`1,745,184` or `1,839,070`, which included `302,419`/`314,857` `bit0=1` noisy rows). Measured strictly on `(flags & 3) == 0` quiet rows, `EXP-F1_hard` drops **`5.344%`** (`81,448 / 1,524,213`), whereas `EXP-F2` dedup drops **`13.026%`** (`198,550 / 1,524,213`).
- In `cc0_r1_rescore16k_0p5pct/rescore_summary.json`, summing the four shards yields `2500 + 2500 + 2500 + 561 = 8,061` selected and `2500 + 2499 + 2500 + 561 = 8,060` rescored (`0` sign flips); in `cc0_r1b_rescore16k_2pct_oppcastle/rescore_summary.json`, summing yields `10000 + 10000 + 10000 + 2243 = 32,243` selected and `10000 + 9998 + 10000 + 2243 = 32,241` rescored (`9 + 7 + 8 + 2 = 26` sign flips).

### 2.2 Exact Pentanomial Statistics & Two-Sample `EXP-F1` Comparison

Recomputing all `N = 500` pair statistics directly from `ptnml = [c0, c1, c2, c3, c4]` over pair scores $x = [0, 0.25, 0.5, 0.75, 1.0]$:

| Match | $\mu$ | $s^2_{\text{pair}}$ | $\text{SE}_{\text{pair}}$ | $z$ | Two-Sided $p$ | Exact LOS% | Elo `[95% CI]` | Delta-Method $\text{SE}_{\text{Elo}}$ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `S2Q_G4a` | `0.512000` | `0.068493` | `0.011704` | `+1.025282` | `0.305230` | `84.74%` | `+8.3401 [-7.60, +24.32]` | `8.1375` |
| `S2Q_G4b` | `0.521500` | `0.072558` | `0.012046` | `+1.784766` | `0.074299` | `96.29%` | `+14.9489 [-1.47, +31.43]` | `8.3862` |
| `S2Q_EXP_F1_eqraw` | `0.487500` | `0.063846` | `0.011300` | `-1.106182` | `0.268648` | `13.43%` | `-8.6877 [-24.11, +6.70]` | `7.8570` |
| `S2Q_EXP_F1_eqret` | `0.517500` | `0.078726` | `0.012548` | `+1.394644` | `0.163123` | `91.84%` | `+12.1652 [-4.93, +29.32]` | `8.7299` |
| `S2Q_EXP_F2_first` | `0.485000` | `0.068913` | `0.011740` | `-1.277692` | `0.201358` | `10.07%` | `-10.4262 [-26.46, +5.57]` | `8.1651` |
| `S2Q_EXP_F2_avg` | `0.486500` | `0.065073` | `0.011408` | `-1.183365` | `0.236665` | `11.83%` | `-9.3830 [-24.96, +6.16]` | `7.9330` |

**Independent Two-Sample Comparison (`EXP-F1 eq-ret` minus `EXP-F1 eq-raw`):**
- **Score-space separation:**
  $$\Delta\mu = 0.517500 - 0.487500 = +0.030000 \text{ (+3.0000 pp)}, \quad \text{SE}_{\text{diff}} = \sqrt{0.011300^2 + 0.012548^2} = 0.016886$$
  $$z_{\text{diff}} = \frac{+0.030000}{0.016886} = \mathbf{+1.7766}, \quad p_{\text{two}} = 0.075635, \quad P(\text{eq-ret} > \text{eq-raw}) = \mathbf{96.22\%}$$
- **Elo-space separation (delta-method):**
  $$\Delta\text{Elo} = +12.1652 - (-8.6877) = \mathbf{+20.8529}, \quad \text{SE}_{\Delta\text{Elo}} = \sqrt{7.8570^2 + 8.7299^2} = \mathbf{11.7450}$$
  $$\text{95\% CI} = \mathbf{[-2.17, +43.87]} \text{ Elo}, \quad z_{\Delta\text{Elo}} = +1.7755, \quad p_{\text{two}} = 0.075820, \quad P(\text{eq-ret} > \text{eq-raw}) = \mathbf{96.21\%}$$

*(Note: Both matches share candidate net `s2q_f1_hard` and the same `UHO_Lichess_4852_v1.epd` opening book with adjacent seeds `202611803` and `202611804` against distinct baselines `G3b` and `s2q_f1_ctrl_eqret`; because `s2q_f1_hard`'s own net noise could induce modest positive covariance between its two win rates, the unadjusted two-sample `SE` is conservative relative to a correlated difference if both baselines behave similarly.)*

### 2.3 Causal Mechanism, `EXP-F1` + `EXP-F2_first` Corroboration, & `EXP-F2_avg` Falsification

1. **Per-Row Information Density Gain (`eq-ret: +12.17 Elo, LOS 91.84%`):**  
   `cc0_f1_hard` applies Tier-2 hash downsampling (`t2_hs800 = 93,886`) specifically to `|score| >= 800 cp`, reducing `800..1199 cp` quiet rows from `100,935 -> 52,614` (`52.13%` kept) and `>= 1200 cp` quiet rows from `47,002 -> 13,875` (`29.52%` kept). `|score| >= 800` accounts for `9.71%` of `G3b` quiet rows (`147,937 / 1,524,213 = 9.7058%`, consistent with `< 800 cp` `90.29%`), whereas across all `1,839,070` clean rows (quiet + `314,857` noisy) in `PHASE_B_NEARDUP_AND_GRADIENT_ADDENDUM.md:47-48`, `|score| >= 800` carries only **`1.20%`** of total WDL gradient energy ($g = |\sigma(s/400) - y|\,p(1-p)$). When `s2q_f1_ctrl_eqret` holds retained quiet volume fixed at `1,442,765` (`train_v3p.py:465` tail truncation `fqs_cat[fqs_drop:]`, whose band percentages match `G3b` within `0.05%`), replacing `5.344%` saturated mop-up positions with contested `< 800 cp` positions (raising `< 800 cp` share from `90.29%` to `95.39%`) yields **`+12.17` Elo (`50k` filter)**.
2. **Finite-`2M` Volume-Loss Penalty (`eq-raw: -8.69 Elo` & `EXP-F2_first: -10.43 Elo`):**  
   Under an equal-raw budget (`2,000,004` raw rows), `s2q_f1_hard` trains on `81,448` (`-5.344%`) fewer unique quiet rows (`1,442,765` vs `1,524,213`; `32.9s` vs `36.4s` over 40 epochs), losing **`-8.69 [-24.11, +6.70]` Elo**. **`S2Q_EXP_F2_first_vs_G3b_1000g_50k`** corroborates this mechanism: `cc0_f2_dedup_first` removes `226,906` cross-shard duplicates (`198,550` quiet = **`-13.026%`** vs `G3b`) and forces all surviving rows to uniform `weight_u8 = 128`, scoring **`-10.43 [-26.46, +5.57]` Elo (`LOS 10.07%`)**. In a `2M`-row dataset (`181–205` gradient steps/epoch including `4x` anchors `161,684` per `train_v3p.py:603`, or `161–186` excluding anchors; `~1,000x–1,312x` smaller than Server Day's `2.0B` rows since `2.0B / 2M = 1,000x` and `2.0B / 1.524M = 1,312x` quiet rows), discarding `5.3%–13.0%` of unique quiet positions measurably degrades coverage and total optimization steps.
3. **Empirical Falsification of `EXP-F2_avg > EXP-F2_first` at `50k` (`-9.38 [-24.96, +6.16]` Elo, `LOS 11.83%`):**  
   At `2026-11-28T10:11:12Z`, `S2Q_EXP_F2_avg_vs_first_1000g_50k` falsified the prior prediction (`+3 to +12` Elo, `Elo <= 0.0` falsification criterion). Holding quiet rows fixed at `1,325,663`, replacing first-occurrence labels (`weight_u8 = 128`) with `score16` averaging + `sqrt(k)` multiplicity weights (`ESS = 99.08%`, `5.64%` of quiet rows upweighted to `181`/`192`) did **not** recover `dedup`'s `-13.026%` volume deficit at `2M` CC0 `50k` and scored `-9.38` Elo below `F2_first`. One candidate mechanism is that averaging `score16` across distinct game/search contexts (or upweighting repeated `k >= 2` positions `1.41x–1.50x`) slightly blurs or overweights clustered positions in a small `2M`-row single-seed (`seed=1`) run — underscoring why `600g @ 250k` verification and multi-seed Server-Day scaling remain decisive.

### 2.4 `|score|` Band Shifts, `weight_u8` Distributions & `ESS`

After `train_v3p.py:592-597` normalizes non-anchor weights to mean `1.0` (while keeping the `161,684` anchor rows exempt at `1.0`), exact quiet `(flags & 3) == 0` distributions are:

| Arm | Quiet Rows $N_q$ | `< 100 cp` (rows / wt% / $\bar{w}$) | `100..399 cp` (rows / wt% / $\bar{w}$) | `400..799 cp` (rows / wt% / $\bar{w}$) | `800..1199 cp` (rows / wt% / $\bar{w}$) | `>= 1200 cp` (rows / wt% / $\bar{w}$) |
|---|---:|---|---|---|---|---|
| **`G3b`** | `1,524,213` | `670,129` (`43.97%`, `1.000`) | `479,884` (`31.48%`, `1.000`) | `226,263` (`14.84%`, `1.000`) | `100,935` (`6.62%`, `1.000`) | `47,002` (`3.08%`, `1.000`) |
| **`EXP-F1_hard`** | `1,442,765` | `670,129` (`46.45%`, `1.000`) | `479,884` (`33.26%`, `1.000`) | `226,263` (`15.68%`, `1.000`) | `52,614` (`3.65%`, `1.000`) | `13,875` (`0.96%`, `1.000`) |
| **`EXP-F1 ctrl_eqret`** | `1,442,765` | `634,012` (`43.94%`, `1.000`) | `454,926` (`31.53%`, `1.000`) | `213,719` (`14.81%`, `1.000`) | `95,668` (`6.63%`, `1.000`) | `44,440` (`3.08%`, `1.000`) |
| **`EXP-F2_first`** | `1,325,663` | `573,796` (`43.28%`, `1.000`) | `423,862` (`31.97%`, `1.000`) | `208,237` (`15.71%`, `1.000`) | `84,192` (`6.35%`, `1.000`) | `35,576` (`2.68%`, `1.000`) |
| **`EXP-F2_avg`** | `1,325,663` | `574,284` (`43.58%`, `1.006`) | `423,452` (`31.97%`, `1.001`) | `208,152` (`15.57%`, `0.991`) | `84,208` (`6.25%`, `0.985`) | `35,567` (`2.64%`, `0.983`) |
| **`EXP-W3`** | `1,325,663` | `574,284` (`42.36%`, `0.978`) | `423,452` (**`38.83%`**, **`1.216`**) | `208,152` (`15.13%`, `0.964`) | `84,208` (**`3.04%`**, `0.478`) | `35,567` (**`0.64%`**, `0.239`) |

- **`EXP-F2_avg` `weight_u8` & `ESS`:** Via `filter_fqs_to_fqs.py:212` (`clip(round(128 * sqrt(k)), 128, 192)`), quiet rows split as `{128: 1,250,800 (94.35%, k=1), 181: 64,467 (4.86%, k=2), 192: 10,396 (0.78%, k>=3)}`, yielding quiet `mean_weight_u8 = 131.08`, quiet `ESS = 1,313,489.6` (**`99.08%`**), and all-rows `mean_weight_u8 = 130.66`, `ESS = 1,599,121.1` (`99.19%`), with `0` quiet rows dropped relative to `EXP-F2_first`.
- **`EXP-W3` `weight_u8` & `ESS`:** Built directly on `cc0_f2_dedup_avg` (`make_stage2_soft_weight.py:26,62-72`), `EXP-W3` drops **`0` rows** (`discarded_rows = 0`) and modifies weights via `0.25x` on `|score| >= 1200` (`41,465` all / `35,567` quiet), `0.50x` on `800..1199` (`100,311` all / `84,208` quiet), `0.50x` on `swing` (`0` rows), and `1.25x` on quiet `100..399` (`423,452` quiet rows; `0` noisy rows boosted). Quiet `weight_u8` histogram is `{32: 35,050, 45: 372, 48: 145, 64: 82,581, 90: 1,303, 96: 324, 128: 734,478, 160: 398,691, 181: 40,798, 192: 7,160, 226: 21,994, 240: 2,767}`, giving quiet `mean_weight_u8 = 134.86` (all-rows `132.78`), quiet `ESS = 1,252,773.3` (**`94.50%`**), and all-rows `ESS = 1,528,272.1` (`94.80%`).
- **Critical `EXP-W3 vs EXP-F1_hard` Dataset Headwind:** Because `cc0_w3_soft_weight` inherits `cc0_f2_dedup_avg`'s deduplicated `1,325,663` quiet rows whereas `cc0_f1_hard` retains `1,442,765` non-deduped quiet rows, `EXP-W3` enters Match `#10` (`S2Q_EXP_W3_softweight_vs_f1_hard`) with **`-117,102` (`-8.12%`) fewer quiet rows** and **`-13.17%` lower quiet `ESS`** (`1,252,773.3` vs `1,442,765.0`) than `EXP-F1_hard`!

### 2.5 Empirical Falsification of `#6` & Revised Falsifiable `50k` Predictions (`250k` Verification Required)

All outcomes and pre-result predictions below apply to the `1,000g @ 50k` filter queue (`run_stage2_clean_skipnoisy_matches.py`) and explicitly require `250k` verification per the Opus `01:12 PC` rule before counting as confirmed strength:

| Match # | Design Contrast (Quiet Rows & Weights) | Pre-Result Prediction / Observed Outcome (`50k` Filter) | Falsification Criterion / Status |
|---|---|---|---|
| **#6 `S2Q_EXP_F2_avg_vs_first`** *(DONE `10:11:12Z`)* | Equal quiet volume (`1,325,663` vs `1,325,663`); `score16` averaging over `226,906` merged rows (`198,550` quiet) + `sqrt(k)` multiplicity (`ESS 99.08%`) | Pre-result prediction (`10:06:41Z`): `+3 to +12` Elo (`LOS >= 70%`). **Observed (`10:11:12Z`): `280–413–307` (`48.65%`), `-9.38 [-24.96, +6.16]` Elo (`z = -1.183`, `LOS 11.83%`)** | **FALSIFIED** (hit pre-registered `Elo <= 0.0` criterion; `score16` avg + `sqrt(k)` did NOT recover `-13.026%` dedup volume deficit) |
| **#9 `S2Q_EXP_W3_softweight_vs_dedup_avg`** *(QUEUED)* | Equal quiet volume (`1,325,663` vs `1,325,663`, `0` dropped); `100..399 cp` boosted `31.97% -> 38.83%` (`1.216x`, targeting `1.477x` gradient peak) + `>=800` soft-downweighted (`8.89% -> 3.68%`), `ESS 99.08% -> 94.50%` | **Revised `0 to +8` Elo** (`LOS ~50%–84%`), isolating `W3`'s `+21.6%` normalized boost on `100..399 cp` over the exact `dedup_avg` base (`M_W1` `soft800` alone was `+0.69` flat) | Falsified if `Elo <= -5.0` (`LOS < 27%`) or `>= +16 Elo (95% LB > 0)` |
| **#10 `S2Q_EXP_W3_softweight_vs_f1_hard`** *(QUEUED)* | Unequal quiet volume: `W3` (`1,325,663` quiet, `ESS 1,252,773`) vs `F1_hard` (`1,442,765` quiet, `ESS 1,442,765`) = **`-8.12%` quiet rows / `-13.17%` ESS headwind** from `dedup_avg` base | **Revised `-12 to +3` Elo** (`LOS ~7%–65%`): after `#6` (`-9.38` Elo), `W3`'s `1.25x` boost on `100..399 cp` must overcome **both** its `-8.12%` quiet-row (`-13.17%` ESS) headwind vs `F1_hard` **and** `dedup_avg`'s apparent `50k` penalty | Falsified if `W3` drops below `-20` Elo (`LOS < 1%`) or reaches **`>= +16 Elo (95% LB > 0)`**, which would show `100..399 cp` soft-weighting overcoming both deficits |

---

## Section 3 — Complete 19-Net Scale-Free OLS & `net_sanity` Unit-Normalized Analysis

### 3.1 Probe Definitions & Cohort Scope (`n = 19`)

- **Middlegame OLS regression (`C:\nnue-lab\neon\forge_fixes\eval_net_full.py:206-225`):** Linear least squares (`np.linalg.lstsq`) of static NNUE evaluation (`m4_ev`) on `[stm_sign * (count_W - count_B) for P, N, B, R, Q] + [1.0]` across M4 positions satisfying `20 <= npcs <= 26` (`m4_mid20_26_ols_piece_cp`).
- **Exact `net_sanity` unit `u` (`C:\nnue-lab\neon\forge_fixes\audit_ols_ratios_and_netunits.py:36-41`):**
  $$u = \frac{S6_Q + S6_R + S6_B + S6_N}{20}$$
  where `S6_startpos_minus` (`eval_net_full.py:55-61,185,246`) measures `eval(startpos) - eval(startpos_minus_piece)` for `Q, R, B, N, P` (scaling to the `9 + 5 + 3 + 3 = 20` classical pawn-unit non-pawn sum).
- **Scale-free normalization (`audit_ols_ratios_and_netunits.py:48-63`):**
  - **Ratios vs Pawn:** `N/P`, `B/P`, `R/P`, `Q/P` (invariant to arbitrary scalar rescaling of the network output).
  - **Net-unit centipawns:** `X_cp = 100.0 * X / u` for `X in {P, N, B, R, Q}`, plus `s6_Q_unit_cp = 100.0 * S6_Q / u` and `s6_Q_over_P = S6_Q / S6_P`.
- **Cohort completeness (`n = 19`):** `audit_ols_ratios_and_netunits.py:79` checks `C:\nnue-lab\neon\forge_fixes\r0202_scorecard.json`, which is absent on disk (`exists = False`), leaving **19** verified nets in `OLS_SCALEFREE_COMPARISON.json`. All 9 `S2Q` entries match `STAGE2_QUIET_GPU_SUMMARY.json` (`ols_Q` and `m4_wdl_mse`) character-for-character.

### 3.2 Complete 19-Net Comparison Table

#### Group 1 — Non-Skip / `keep_noisy` Nets (`n = 8`)
*(Subgroup A = `3` legacy/full-window `keep_noisy` nets; Subgroup B = `5` `2M`-CC0 `keep_noisy` nets including `G5a/b/c` trained via `run_serverday_arch_suite.py` without `--skip-fqs-noisy`)*

| Net | Subgroup | M4 WDL MSE | Raw OLS `P/N/B/R/Q` | `N/P` | `B/P` | `R/P` | `Q/P` | `u` | Net-Unit `P/N/B/R/Q` (cp) | `R - N` (raw / unit) | `R < N` | `S6_Q` (unit / `/P`) |
|---|---|---:|---|---:|---:|---:|---:|---:|---|---:|:---:|---:|
| `r0067 (live 768w, keep_noisy)` | A (25r) | `0.01302` | `51.5/135.7/167.0/202.1/307.3` | `2.635` | `3.243` | `3.924` | `5.967` | `189.55` | `27.2/71.6/88.1/106.6/162.1` | `+66.4 / +35.0` | No | `1018.7 / 9.51` |
| `G2_1024p (12r V3P, keep_noisy)` | A (12r) | `0.01234` | `47.3/132.1/160.1/194.2/295.3` | `2.793` | `3.385` | `4.106` | `6.243` | `180.60` | `26.2/73.1/88.6/107.5/163.5` | `+62.1 / +34.4` | No | `832.8 / 8.17` |
| `G3_FULL25 (25r V3P, keep_noisy)` | A (25r) | `0.01140` | `47.2/121.8/154.5/199.1/293.3` | `2.581` | `3.273` | `4.218` | `6.214` | `172.20` | `27.4/70.7/89.7/115.6/170.3` | `+77.3 / +44.9` | No | `872.2 / 7.47` |
| `G3a_cc0_keep_noisy (scratch V3P)` | B (2M CC0) | `0.02941` | `54.9/138.4/142.4/125.9/199.3` | `2.521` | `2.594` | `2.293` | `3.630` | `114.00` | `48.2/121.4/124.9/110.4/174.8` | **`-12.5 / -11.0`** | **Yes** | `793.9 / 5.66` |
| `G3a_distill_keep_noisy (r0067 w=0.2)` | B (2M CC0) | `0.02775` | `55.1/140.5/147.6/132.9/201.8` | `2.550` | `2.679` | `2.412` | `3.662` | `114.75` | `48.0/122.4/128.6/115.8/175.9` | **`-7.6 / -6.6`** | **Yes** | `778.2 / 5.62` |
| `G5a_cc0_768p_kb8` | B (2M CC0) | `0.02889` | `56.7/135.0/137.9/118.6/171.7` | `2.381` | `2.432` | `2.092` | `3.028` | `105.40` | `53.8/128.1/130.8/112.5/162.9` | **`-16.4 / -15.6`** | **Yes** | `778.9 / 5.82` |
| `G5b_cc0_1536p_kb8` | B (2M CC0) | `0.02915` | `59.4/136.2/140.9/131.3/193.6` | `2.293` | `2.372` | `2.210` | `3.259` | `114.35` | `51.9/119.1/123.2/114.8/169.3` | **`-4.9 / -4.3`** | **Yes** | `759.9 / 5.05` |
| `G5c_cc0_1024p_kb16` | B (2M CC0) | `0.02935` | `52.9/133.1/135.9/128.6/202.3` | `2.516` | `2.569` | `2.431` | `3.824` | `112.35` | `47.1/118.5/121.0/114.5/180.1` | **`-4.5 / -4.0`** | **Yes** | `783.3 / 5.71` |

#### Group 2 — `--skip-fqs-noisy` Nets (`n = 11`)

| Net | M4 WDL MSE | Raw OLS `P/N/B/R/Q` | `N/P` | `B/P` | `R/P` | `Q/P` | `u` | Net-Unit `P/N/B/R/Q` (cp) | `R - N` (raw / unit) | `R < N` | `S6_Q` (unit / `/P`) |
|---|---:|---|---:|---:|---:|---:|---:|---|---:|:---:|---:|
| `G3b_cc0_skip_noisy (scratch V3P)` | `0.02339` | `96.4/373.9/400.8/522.0/1016.0` | `3.879` | `4.158` | `5.415` | `10.539` | `124.95` | `77.2/299.2/320.8/417.8/813.1` | `+148.1 / +118.6` | No | `831.5 / 6.34` |
| `G3b_distill_skip_noisy (r0067 w=0.2)` | `0.02252` | `95.1/366.0/394.0/515.8/1002.7` | `3.849` | `4.143` | `5.424` | `10.544` | `126.50` | `75.2/289.3/311.5/407.7/792.6` | `+149.8 / +118.4` | No | `831.6 / 7.31` |
| `S2Q/s2q_f1_ctrl_eqret` | `0.02353` | `94.5/373.8/400.5/514.7/1011.8` | `3.956` | `4.238` | `5.447` | `10.707` | `127.20` | `74.3/293.9/314.9/404.6/795.4` | `+140.9 / +110.7` | No | `825.5 / 6.25` |
| `S2Q/s2q_f1_hard` | `0.02311` | `96.0/369.9/394.6/513.5/1009.1` | `3.853` | `4.110` | `5.349` | `10.511` | `126.05` | `76.2/293.5/313.1/407.4/800.6` | `+143.6 / +113.9` | No | `829.0 / 6.74` |
| `S2Q/s2q_f2_dedup_avg` | `0.02336` | `96.6/381.4/407.5/529.5/1026.5` | `3.948` | `4.218` | `5.481` | `10.626` | `131.50` | `73.5/290.0/309.9/402.7/780.6` | `+148.1 / +112.7` | No | `827.4 / 7.11` |
| `S2Q/s2q_f2_dedup_first` | `0.02318` | `97.7/379.1/408.1/530.8/1033.8` | `3.880` | `4.177` | `5.433` | `10.581` | `130.95` | `74.6/289.5/311.6/405.3/789.5` | `+151.7 / +115.8` | No | `834.7 / 7.29` |
| `S2Q/s2q_g4a_losspow25` | `0.02310` | `95.9/364.3/394.3/515.5/988.5` | `3.799` | `4.112` | `5.375` | `10.308` | `126.35` | `75.9/288.3/312.1/408.0/782.4` | `+151.2 / +119.7` | No | `838.1 / 7.11` |
| `S2Q/s2q_g4b_obreweight` | `0.02350` | `97.3/376.7/402.2/528.8/1022.3` | `3.872` | `4.134` | `5.435` | `10.507` | `127.10` | `76.6/296.4/316.4/416.1/804.3` | `+152.1 / +119.7` | No | `837.9 / 6.53` |
| `S2Q/s2q_r1_rescore16k_0p5pct` | `0.02325` | `96.9/379.0/406.7/528.5/1033.1` | `3.911` | `4.197` | `5.454` | `10.662` | `130.25` | `74.4/291.0/312.2/405.8/793.2` | `+149.5 / +114.8` | No | `824.6 / 8.14` |
| `S2Q/s2q_r1b_rescore16k_2pct_oppcastle` | `0.02318` | `96.7/376.8/405.1/529.8/1025.2` | `3.897` | `4.189` | `5.479` | `10.602` | `131.45` | `73.6/286.6/308.2/403.0/779.9` | `+153.0 / +116.4` | No | `823.9 / 7.63` |
| `S2Q/s2q_w3_soft_weight` | `0.02308` | `98.0/376.1/405.0/529.3/1017.0` | `3.838` | `4.133` | `5.401` | `10.378` | `129.95` | `75.4/289.4/311.7/407.3/782.6` | `+153.2 / +117.9` | No | `820.3 / 7.06` |

*(Rounding note: `unit R - N` values above and in Section 3.3 are computed directly from the 1-decimal `net_unit_cp` fields in `OLS_SCALEFREE_COMPARISON.json`; computing `100 * (R - N) / u` prior to 1-decimal rounding differs by `0.1` cp on three `--skip-fqs-noisy` nets — `G3b_cc0_skip_noisy`: `118.6` vs `118.53`, `s2q_f1_ctrl_eqret`: `110.7` vs `110.77`, `s2q_f2_dedup_avg`: `112.7` vs `112.62` — shifting the `n=11` group mean by `0.01` cp from `116.24` to `116.23`.)*

### 3.3 Group Summary Statistics (`Min / Max / Median / Mean`)

| Group | Metric | Min | Max | Median | Mean |
|---|---|---:|---:|---:|---:|
| **All non-skip (`n=8`)** | `m4_wdl_mse` | `0.01140` | `0.02941` | `0.02832` | `0.02266` |
| | `N/P` | `2.293` | `2.793` | `2.536` | `2.534` |
| | `B/P` | `2.372` | `3.385` | `2.637` | `2.818` |
| | `R/P` | `2.092` | `4.218` | `2.422` | `2.961` |
| | `Q/P` | `3.028` | `6.243` | `3.743` | `4.478` |
| | `unit_u` | `105.40` | `189.55` | `114.55` | `137.90` |
| | `Q_cp` (net-unit) | `162.1` | `180.1` | `169.8` | `169.9` |
| | `raw R - N` | `-16.4` | `+77.3` | `-4.7` | `+19.99` |
| | `unit R - N` | `-15.6` | `+44.9` | `-4.15` | `+9.10` |
| **Subgroup A: Legacy/full `keep_noisy` (`n=3`)** | `m4_wdl_mse` | `0.01140` | `0.01302` | `0.01234` | `0.01225` |
| | `R/P` | `3.924` | `4.218` | `4.106` | `4.083` |
| | `Q/P` | `5.967` | `6.243` | `6.214` | `6.141` |
| | `Q_cp` (net-unit) | `162.1` | `170.3` | `163.5` | `165.3` |
| | `raw R - N` | `+62.1` | `+77.3` | `+66.4` | `+68.60` |
| | `unit R - N` | `+34.4` | `+44.9` | `+35.0` | `+38.10` |
| **Subgroup B: `2M` CC0 `keep_noisy` (`n=5`)** | `m4_wdl_mse` | `0.02775` | `0.02941` | `0.02915` | `0.02891` |
| | `N/P` | `2.293` | `2.550` | `2.516` | `2.452` |
| | `B/P` | `2.372` | `2.679` | `2.569` | `2.529` |
| | `R/P` | `2.092` | `2.431` | `2.293` | `2.288` |
| | `Q/P` | `3.028` | `3.824` | `3.630` | `3.481` |
| | `unit_u` | `105.40` | `114.75` | `114.00` | `112.17` |
| | `Q_cp` (net-unit) | `162.9` | `180.1` | `174.8` | `172.6` |
| | `raw R - N` | `-16.4` | `-4.5` | `-7.6` | `-9.18` |
| | `unit R - N` | `-15.6` | `-4.0` | `-6.6` | `-8.30` |
| **All `--skip-fqs-noisy` (`n=11`)** | `m4_wdl_mse` | `0.02252` | `0.02353` | `0.02318` | `0.02320` |
| | `N/P` | `3.799` | `3.956` | `3.879` | `3.880` |
| | `B/P` | `4.110` | `4.238` | `4.158` | `4.165` |
| | `R/P` | `5.349` | `5.481` | `5.433` | `5.427` |
| | `Q/P` | `10.308` | `10.707` | `10.544` | `10.542` |
| | `unit_u` | `124.95` | `131.50` | `127.20` | `128.39` |
| | `Q_cp` (net-unit) | `779.9` | `813.1` | `792.6` | `792.2` |
| | `raw R - N` | `+140.9` | `+153.2` | `+149.8` | `+149.20` |
| | `unit R - N` | `+110.7` | `+119.7` | `+116.4` | `+116.24` |

### 3.4 Structural Findings, `OPUS-2811-OLS-CAUTION`, & Live `768w` Decision Path

1. **Invariance Across Architectures & Distillation under `2M` CC0 `keep_noisy`:**  
   Every single `2M`-CC0 `keep_noisy` net (`5 / 5`) — regardless of width (`768p`, `1024p`, `1536p`), king-bucket count (`kb8`, `kb16`), or `r0067` teacher distillation (`G3a_distill_keep_noisy`, `w=0.2`) — exhibits `R < N` (`raw R - N = -16.4..-4.5`; `unit R - N = -15.6..-4.0`) and collapsed `Q/P` (`3.028..3.824`) and `Q_cp` (`162.9..180.1 cp`). By contrast, all `11 / 11` `--skip-fqs-noisy` nets separate cleanly into `Q/P = 10.308..10.707`, `R/P = 5.349..5.481`, `Q_cp = 779.9..813.1 cp`, and `R - N = +140.9..+153.2` raw (`+110.7..+119.7` unit cp). On scratch `2M`-CC0 `V3P`, that separation coincides with `G3b_skipnoisy` beating `G3a_keepnoisy` by `+699.72 [+642.27, +784.63]` Elo (`972-21-7`, `50k` equal-raw) and `+651.27 [+597.55, +727.83]` Elo (`967-20-13`, `50k` equal-retained), where noisy `bit0=1` mid-exchange hanging-Queen rows distort the direct PSQT/FT material slope.
2. **`OPUS-2811-OLS-CAUTION` Interpretation (`OPUS_TO_NEON.md:2990-3001`):**  
   Live `768w` SCReLU (`r0067`) has no direct PSQT path (`OPUS_TO_NEON.md:2967`), uses `25` rounds (`r0043..r0067`), and already scores `S6_Q = 1931` raw (`1018.7` unit cp, `S6_Q/S6_P = 9.51`) on quiet startpos-minus-Q while showing `Q/P = 5.967` (`Q_cp = 162.1 cp`) in self-play middlegames. As Opus cautions, middlegame OLS over self-play positions captures temporary/compensated material imbalance rather than quiet-leaf material pricing; therefore, OLS compression alone **never** authorizes modifying the live loop.
3. **Live `768w` Twin Decision Path (`OPUS_R1_skip_vs_R1_keep_1000g_250k`):**  
   Per `OPUS-2811-CLOCK-RECOUNTED-AND-R1-TWIN` (`OPUS_TO_NEON.md:3016-3020`) and `run_post_bundle_250k_queue.py:49-62`:
   - `OPUS_R1_live768_skipnoisy` (`R1-skip`, `pipeline/forge_train_v3.py`, `hidden=768`, `r0178..r0202`, `b_full.pt` `w=0.2`, `epochs=40`, `seed=1`, omitting `--keep-noisy`) is actively training on GPU at `2026-11-28T10:15:52Z` (`declaration.json` written `2026-11-28 01:10:09` PC / `09:10:09Z`; no `.fnn3` on disk yet).
   - `run_opus_r1_keep_twin.py` (`R1-keep`, identical runner, seed, epochs, LR, teacher, and window, differing **only** by `--keep-noisy`) is scheduled after the Owner Bundle clock phase (`OPUS_R1_live768_keepnoisy_twin/` not yet created).
   - Decision rule declared prior to any result: `OPUS_R1_skip_vs_R1_keep_1000g_250k` (`base_r15dsg.exe`, `1,000g @ 250k`, `concurrency=8`, `seed=202611951`) requires **`95%` Elo lower bound `> 0`** (otherwise inconclusive; if positive, train seed-2 replicates of both and test `R1-skip vs r0067` at `250k` and `6+0.06` at `concurrency=7`).

---

## Section 4 — Verification Ledger & Reproducibility

All numbers in this report were independently verified read-only (`CPU-only`, `CUDA_VISIBLE_DEVICES=""`, `PYTHONDONTWRITEBYTECODE=1`, `python -B`) against on-disk sources at `2026-11-28T10:15:52Z`:
- **Match & Queue Sources:**
  - `C:\nnue-lab\neon\forge_fixes\matches\S2Q_*\summary.json` and `declaration_*.json` (`6` completed, `1` running PGN `games_*.pgn`)
  - `C:\nnue-lab\neon\forge_fixes\matches\G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k\summary.json` and `G3b_skipnoisy_vs_G3a_eqret_1000g_50k\summary.json`
  - `C:\nnue-lab\neon\filter_quest\run_stage2_clean_skipnoisy_matches.py` (`lines 1–78`)
  - `C:\nnue-lab\neon\forge_fixes\run_post_bundle_250k_queue.py` (`lines 1–87`)
- **Dataset & Training Sources:**
  - `C:\nnue-lab\neon\forge_fixes\cc0_shards_4k_v2_nodrawconf\summary.json` & `*.fqs.z`
  - `C:\nnue-lab\neon\filter_quest\stage2_data\cc0_{f1_hard,f2_dedup_first,f2_dedup_avg,w3_soft_weight}\summary.json` & `*.fqs.z`
  - `C:\nnue-lab\neon\filter_quest\stage2_data\cc0_{r1_rescore16k_0p5pct,r1b_rescore16k_2pct_oppcastle}\rescore_summary.json`
  - `C:\nnue-lab\neon\filter_quest\make_stage2_soft_weight.py` (`lines 1–110`), `run_stage2_clean_skipnoisy_gpu.py` (`lines 1–123`), `PHASE_B_NEARDUP_AND_GRADIENT_ADDENDUM.md` (`lines 1–53`)
  - `C:\nnue-lab\neon\forge_fixes\train_v3p.py` (`lines 405–470, 560–605`), `gpu_runs\G3b_cc0_skip_noisy\metrics.json`, `stage2_runs_quiet\*\metrics.json`, `STAGE2_QUIET_GPU_SUMMARY.json`
- **OLS & Governance Sources:**
  - `C:\nnue-lab\neon\forge_fixes\OLS_SCALEFREE_COMPARISON.json` (`517 lines`) & `.md` (`25 lines`)
  - `C:\nnue-lab\neon\forge_fixes\audit_ols_ratios_and_netunits.py` (`lines 1–136`), `eval_net_full.py` (`lines 175–264`), `baseline_r0067_scorecard.json` (`lines 1–46`)
  - `C:\nnue-lab\neon\OPUS_TO_NEON.md` (`lines 2980–3047`)
  - `C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy\declaration.json`
- **Reproducibility Commands (Read-Only):**
  1. Pentanomial two-sample & `S2Q_*` JSON check: `C:\nnue-lab\venv\Scripts\python.exe -B` over `C:\nnue-lab\neon\forge_fixes\matches\S2Q_*\summary.json` (`ptnml` -> `mu`, `se`, `z`, `los_pct`, `elo`, `se_elo`, `Delta_mu`, `Delta_Elo`).
  2. `.fqs.z` `(flags & 3) == 0` audit: `C:\nnue-lab\venv\Scripts\python.exe -B` decompressing `*.fqs.z` (`FQS1` header `8` bytes + `38`-byte records) to recompute quiet counts, `|score|` band weights, `weight_u8` histograms, and `ESS`.
  3. 19-net OLS group check: `C:\nnue-lab\venv\Scripts\python.exe -B` over `C:\nnue-lab\neon\forge_fixes\OLS_SCALEFREE_COMPARISON.json` verifying `n=19` (`n=8` non-skip split into `n=3` Subgroup A and `n=5` Subgroup B; `n=11` `--skip-fqs-noisy`) `min / max / median / mean`.
