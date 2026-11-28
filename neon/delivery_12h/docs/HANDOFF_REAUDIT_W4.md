# Wave 4 Post-Fix Re-Audit Report: `HANDOFF_12H_DATA_QUALITY.md`

- **Audited Document:** `C:\nnue-lab\neon\filter_quest\HANDOFF_12H_DATA_QUALITY.md`
- **Snapshot Metadata:** `158` lines, `26,067` bytes, SHA-256 `25be20002af7f0b54c1105f7b5980eea477e856b2607cb5015dbb0b58703b48b` *(vs Wave 3 snapshot: `149` lines, `21,401` bytes, SHA-256 `5072b9c02bdc5f55a291a461c5e7953993aa516420a0de167dafa1a3f114d11c`)*
- **Audit Mode:** Strictly read-only, CPU-only (`PYTHONDONTWRITEBYTECODE=1`), zero `fastchess` invocations, independent verification against raw `summary.json`, `declaration_*.json`, `metrics.json`, `audit*.json`, `CHECKPOINT_LATEST.md`, `ALL_MATCHES_SCOREBOARD.md`, and binary files on disk.
- **R5 Clean-Room Compliance:**
  - **Forbidden-word scan (`re.compile(r"\b" + "cur" + r"ed?\b", re.IGNORECASE)`):** **`0` hits** (`[]`).
  - **Pooled-match check:** **`0` pooled matches**. Section 4 (`L63`) explicitly reports `SF8` independent `1,000g` confirmation `(+4.86)` separately from its screen `(+17.97, not pooled per R5!)`; `L68` reports `SF4b1` `1,000g` confirmation `(-4.52)` separately from screen `(+15.06)`; `L65` (`COMBO+Deeper`) and `L69` (`SF9`) are explicitly tagged `(600g screen)`.
- **Freeze Gate Status:** **`UNFROZEN`** — **`8` markers across `5` lines** (`L3`, `L72` x2, `L73` x2, `L109`, `L110`, `L111`). **DO NOT freeze or stage live into `C:\nnue-lab\teamwork\`.**

---

## 1. Executive Verdict

**`VERIFIED AS LIVING DRAFT — ALL 8 WAVE 3 FINDINGS RESOLVED (5 MINOR RESIDUAL NOTES; DO NOT FREEZE UNTIL [PENDING] / [TRAINING] / [TESTING NEXT] GATES CLEAR)`**

Every one of the `8` discrepancies flagged by Wave 3 Stream C (`HANDOFF_AUDIT_REPORT.md`) has been addressed in the updated `HANDOFF_12H_DATA_QUALITY.md`:
- `71/71` explicit file/directory paths resolve on disk (`0` broken paths).
- `17/17` completed Section 4 match rows (`L55–L71`) and all cited secondary match figures (`SF8` screen, `SF4b1` screen, `SF4b1+SF6b+SF8`, `SF4b1+SF8`, `COMBO_v1`, `SF5a`, `SF4b2`, `SF7`) match their raw `summary.json` files on disk.
- All key SHA-256 digests (`forge.exe`, `r0067\cand.fnn3`, `final_eval_r0203_w14_w15.plain`, Syzygy/opening anchors, `book_cc0_clean.epd`, `datagen_uci_startpos_only.patch`) and raw dataset/training/rescore metrics (`G1`, `G2`, `G3_FULL25`, `cc0_shards_4k_v2`, `rescore_depth_curve.json`, `EXP-R1`, `net_sanity.py` / `baseline_r0067_scorecard.json`) match disk artifacts.
- `5` minor residual text discrepancies remain for Neon to polish before final freeze (`L82` `47/47` vs Wave 3 `44/44`; `L146` `SF1..SF26` vs actual `SF1..SF9, SF11..SF33`; `L38` `G2` `dead_draws_20k.fqs.z` filename nuance; `L25` unprefixed `gen_cc0_selfgame_fqs_v2.py`; `L28/103/134` unpersisted `769k rec/s` benchmark JSON), alongside expected ongoing progress drift in live GPU training (`G3_FULL25` now at Epoch `18+/40` in `CHECKPOINT_LATEST.md`) and the live CPU match queue (`37` completed matches in `ALL_MATCHES_SCOREBOARD.md`).

---

## 2. Wave 3 Audit Findings — Resolution Verification Matrix (`8/8` Resolved)

| Wave 3 Finding | Updated Handoff Evidence (Line & Quote) | Raw Disk Evidence | Resolution Status |
|---|---|---|---|
| **#1 (HIGH): Broken `filter_quest\rescore_fqs_selective.py` path in Sec 11** | `L146` lists `rescore_fqs_selective.py` under `NNUE & Search Fixes (C:\nnue-lab\neon\forge_fixes\)`; `L148` (`Filter Quest Core`) no longer lists it. Also cited as `forge_fixes\rescore_fqs_selective.py` at `L47`, `L101`, `L130`. | `C:\nnue-lab\neon\forge_fixes\rescore_fqs_selective.py` exists (`True`); `C:\nnue-lab\neon\filter_quest\rescore_fqs_selective.py` does not exist (`False`). | **RESOLVED** |
| **#2 (HIGH): S5-overlapping `dead_draws_20k_clean.fqs.z` in Sec 3.2** | `L38` cites `anchors\dead_draws_20k_s5disjoint.fqs.z` (`20,000` unique, `0` exact & `0` 4-symmetry overlap with all 6 S5/S7 FENs and `heldout_syzygy_4k.json`) + `anchors\won_endings_syzygy_20k.fqs.z` + `anchors\opening_ply012_anchors.fqs.z` (`421` rows), plus explicit transparency note on `G2` and `G3_FULL25` launching with `dead_draws_20k_clean.fqs.z` and held-out generalization `19.0 -> 8.9 cp`. | `anchors\heldout_integrity_verification.json` confirms `dead_draws_20k_s5disjoint.fqs.z` has `0` heldout and `0` S5/S7 overlap (`sha256=76532795...`). `anchors\opening_ply012_anchors_meta.json` confirms `positions=421`, `bytes=2200`, `sha256=67038576...`. `launch_g3_full25.py:43` uses `dead_draws_20k_clean.fqs.z`. *(Minor nuance: `G2\metrics.json` `args.anchor_shards` records `dead_draws_20k.fqs.z`, which also hits `S5_K-K` in `s5_s7_overlap_audit.json`.)* | **RESOLVED** *(1 filename nuance on `G2`)* |
| **#3 (HIGH): Misattributed `\|score\| >= 800` rate (`5.52%` vs `10.18%`/`9.40%`)** | `L42` and `L89` now report `10.18%` raw / `9.40%` clean (`6.52%` in `800..1199` + `2.88%` in `>=1200`) for `cc0_shards_4k_v2`, explicitly attributing `5.52%` to `early 200k pilot_k0`. | `forge_fixes\cc0_shards_4k_v2\audit.json`: `"abs_ge800_pct": 10.18`. `filter_quest\results\audit_cc0_v2_dedup_phase.json`: `"800_1199": 6.52`, `"1200_plus": 2.88` (sum `9.40%`). | **RESOLVED** |
| **#4 (HIGH): Unverified Ep-24 loss `0.004685` & stale/inconsistent `G3_FULL25` progress** | (a) `L98` replaces unverified `0.004685` with `"G2 achieved verified final_train_loss = 0.004601 (-5.37% vs G1 0.004862 in G2/metrics.json)"`. (b) `L72`, `L98`, `L139` are internally synchronized (`Epoch 10+/40`, `353.45M` pos, `LOSS 0.006550`, `1.855M pos/s`, ETA `~22:25 PC`). | (a) `G2\metrics.json`: `final_train_loss=0.004601`; `G1\metrics.json`: `final_train_loss=0.004862` (`-5.368%`). (b) Expected live-run progression: `filter_quest\CHECKPOINT_LATEST.md` (`21:14 PC`) now shows `G3_FULL25` at `Epoch 18+/40` (`LOSS 0.006569`, `1,904,296 pos/s`, `cand_e6.pt`, `cand_e12.pt`, `diag_e12/cand.fnn3` with `0` `net_sanity.py` v2 flags). | **RESOLVED** *(4a fully; 4b internal sync resolved, live run advancing as expected)* |
| **#5 (MEDIUM): `L35` `datagen_uci_startpos_only.patch` `sp_k=4` / `k=3/4` consistency** | `L36` specifies `"10% startpos (write_min_ply=0) using k = rng.choice((3, 4)) default (or explicit sp_k=4, NEVER k=0!)"`, citing `white_score=51.50%` (vs `55.25%` at `k=4`), `dup=2.61%`, `0.0%` ply 0–15 dups, matching `L99`, `L129`, `L146`. | `patches\datagen_uci_startpos_only.patch` (`78` lines, `3,816` B, `sha256=c0c92cb7...`); `startpos_k34_pilot\pilot_summary.json` confirms `sp_k34_alt` (`white_score_pct: 51.5`, `dup_pct: 2.607`, `0_7`/`8_15` `dup_pct: 0.0`) vs `sp_k4` (`white_score_pct: 55.25`). | **RESOLVED** |
| **#6 (MEDIUM): `rescore_depth_curve.json` `2k -> 8k` vs `4k -> 8k/16k`** | `L44–L47` now show BOTH legacy `2k -> 8k` (`-20.5%` / `-23.5%` middlegame) AND CC0 `4k -> 8k` (`-12.34%`, `0.00770 -> 0.00675`) and `4k -> 16k` (`-19.22%`, `0.00770 -> 0.00622`), plus `EXP-R1` (`8,060` positions, `37.3s`, `215 pos/s`, `mad_delta_cp = 45.86-49.19 cp`, `0` sign flips). | `forge_fixes\rescore_depth_curve.json`: `2000` (`0.00849`, mid `0.01212`), `4000` (`0.0077`), `8000` (`0.00675`, mid `0.00927`), `16000` (`0.00622`). `filter_quest\stage2_data\cc0_r1_rescore16k_0p5pct\rescore_summary.json`: `2500+2499+2500+561 = 8060` rescored, `11.59+11.18+11.79+2.74 = 37.30s`, `mad_delta_cp` `45.86..49.19`, `sign_flips=0` across all 4 shards. | **RESOLVED** |
| **#7 (MEDIUM): Missing 3 completed post-Wave-2 matches in Sec 4** | `L65` (`COMBO+Deeper`), `L66` (`SF6b+SF8`), `L67` (`V3P+4b1+8+D`), and `L69` (`SF9`) added to Sec 4. | All 4 match their raw `summary.json` files (Section 3 below). *(Ongoing CPU queue has since completed additional matches recorded in `ALL_MATCHES_SCOREBOARD.md`, currently `37` completed matches.)* | **RESOLVED** *(live CPU queue adds newer matches)* |
| **#8 (LOW): Precision nuances (`~8.45%`, `M_SWA 438g/446g`, `net_sanity` vs scorecard)** | `L16` states `"exact 8.43% (8.4268% window; 8.467% on r0202)"`; `L88` states `"438g at last fastchess interval / 446 finished PGN games"`; `L37` cites both `"baseline_r0067_scorecard.json flags S1,S2,S5; net_sanity.py v2 flags S2,S5,S7"`. | `r0178..r0202`: `(378856831-346931328)/378856831 = 8.4268%`; `baseline_r0067_scorecard.json` has `["S1_startpos", "S2_start_vs_e4", "S5_dead_draws"]`; `net_sanity.py` v2 flags `S2, S5, S7` on `r0067`. | **RESOLVED** |

---

## 3. Section 4 Match Verification Table (`17/17` Completed Rows vs Raw `summary.json`)

All `17` completed match rows in Section 4 (`L55–L71`) were verified directly against their raw `summary.json` files:

| ID (Line) | Raw `summary.json` Path | Handoff `Games / W–D–L / Elo [95% CI] / z / LOS / Ptnml` | Raw `summary.json` (`games / W-D-L / pe.elo [ci95] / z / pe.los (top.los) / ptnml`) | Verdict |
|---|---|---|---|---|
| `M0a` (`L55`) | `filter_quest\matches\M0a_noteach_vs_ctrl_n50k\summary.json` | `1,000 / 234–456–310 / -26.46 [-40.02, -12.98] / -3.85 / 0.01% / [27,144,220,96,13]` | `1000 / 234-456-310 / -26.46 [-40.02, -12.98] / -3.852 / 0.01% (0.01%) / [27, 144, 220, 96, 13]` | **EXACT MATCH** |
| `M0b` (`L56`) | `filter_quest\matches\M0b_mix65_vs_ctrl_n50k\summary.json` | `1,000 / 241–457–302 / -21.22 [-34.87, -7.64] / -3.06 / 0.11% / [25,142,217,101,15]` | `1000 / 241-457-302 / -21.22 [-34.87, -7.64] / -3.064 / 0.11% (0.11%) / [25, 142, 217, 101, 15]` | **EXACT MATCH** |
| `M0c` (`L57`) | `filter_quest\matches\M0c_bundle_r9_vs_ctrl_n50k\summary.json` | `1,000 / 217–449–334 / -40.84 [-55.04, -26.77] / -5.72 / 0.00% / [38,158,196,99,9]` | `1000 / 217-449-334 / -40.84 [-55.04, -26.77] / -5.72 / 0.0% (0.0%) / [38, 158, 196, 99, 9]` | **EXACT MATCH** |
| `M0d` (`L58`) | `filter_quest\matches\M0d_cyc40_wd01_vs_ctrl_n50k\summary.json` | `1,000 / 236–486–278 / -14.60 [-28.23, -1.02] / -2.11 / 1.75% / [18,147,214,101,20]` | `1000 / 236-486-278 / -14.6 [-28.23, -1.02] / -2.107 / 1.75% (1.75%) / [18, 147, 214, 101, 20]` | **EXACT MATCH** |
| `M0e` (`L59`) | `filter_quest\matches\M0e_r12ctrl_vs_r0067_n50k\summary.json` | `1,000 / 209–479–312 / -35.91 [-49.26, -22.67] / -5.34 / 0.00% / [25,165,206,96,8]` | `1000 / 209-479-312 / -35.91 [-49.26, -22.67] / -5.337 / 0.0% (0.0%) / [25, 165, 206, 96, 8]` | **EXACT MATCH** |
| `M_F0` (`L60`) | `filter_quest\matches\M_F0_base_vs_min_r203_n50k\summary.json` | `1,000 / 364–298–338 / +9.04 [-8.22, +26.34] / +1.03 / 84.8% / [53,91,191,107,58]` | `1000 / 364-298-338 / 9.04 [-8.22, 26.34] / 1.026 / 84.76% (84.78%) / [53, 91, 191, 107, 58]` | **EXACT MATCH** |
| `M_W1` (`L61`) | `filter_quest\matches\M_W1_soft800_vs_noteach_n50k\summary.json` | `1,000 / 276–450–274 / +0.69 [-13.21, +14.61] / +0.10 / 53.9% / [20,126,207,126,21]` | `1000 / 276-450-274 / 0.69 [-13.21, 14.61] / 0.098 / 53.9% (53.91%) / [20, 126, 207, 126, 21]` | **EXACT MATCH** |
| `G1` (`L62`) | `forge_fixes\matches\G1_selfdistill_mix85_vs_r0067_1000g_50k\summary.json` | `1,000 / 233–479–288 / -19.13 [-32.65, -5.67] / -2.79 / 0.27% / [25,137,219,106,13]` | `1000 / 233-479-288 / -19.13 [-32.65, -5.67] / -2.786 / 0.27% (0.26%) / [25, 137, 219, 106, 13]` | **EXACT MATCH** |
| `SF8` (`L63`) | `forge_fixes\matches\SF8_alone_vs_base_1000g_50k\summary.json` | `1,000 / 251–512–237 / +4.86 [-7.77, +17.51] / +0.76 / 77.5% / [9,125,222,131,13]` *(screen `+17.97`)* | `1000 / 251-512-237 / 4.86 [-7.77, 17.51] / 0.755 / 77.47% (77.5%) / [9, 125, 222, 131, 13]` *(screen `SF8_conthist_6ply`: `17.97`)* | **EXACT MATCH** |
| `LmrDeeper` (`L64`) | `forge_fixes\matches\LmrDeeper_alone_vs_base_1000g_50k\summary.json` | `1,000 / 255–514–231 / +8.34 [-4.06, +20.76] / +1.32 / 90.7% / [5,122,234,122,17]` | `1000 / 255-514-231 / 8.34 [-4.06, 20.76] / 1.318 / 90.63% (90.65%) / [5, 122, 234, 122, 17]` | **EXACT MATCH** |
| `COMBO+Deeper` (`L65`) | `forge_fixes\matches\COMBO_v1_plus_LmrDeeper_600g_50k\summary.json` | `600 / 148–324–128 / +11.59 [-4.52, +27.74] / +1.41 / 92.1% / [3,72,137,78,10]` | `600 / 148-324-128 / 11.59 [-4.52, 27.74] / 1.41 / 92.07% (92.1%) / [3, 72, 137, 78, 10]` | **EXACT MATCH** |
| `SF6b+SF8` (`L66`) | `forge_fixes\matches\V3P_SF6b_scaled_SF8_no4b1_vs_base_1000g_50k\summary.json` | `1,000 / 234–545–221 / +4.52 [-8.18, +17.22] / +0.70 / 75.7% / [10,125,219,134,12]` | `1000 / 234-545-221 / 4.52 [-8.18, 17.22] / 0.698 / 75.73% (75.75%) / [10, 125, 219, 134, 12]` | **EXACT MATCH** |
| `V3P+4b1+8+D` (`L67`) | `forge_fixes\matches\V3P_SF4b1_SF8_LmrDeeper_vs_base_1000g_50k\summary.json` | `1,000 / 251–507–242 / +3.13 [-10.21, +16.48] / +0.46 / 67.7% / [16,124,210,135,15]` | `1000 / 251-507-242 / 3.13 [-10.21, 16.48] / 0.46 / 67.71% (67.72%) / [16, 124, 210, 135, 15]` | **EXACT MATCH** |
| `SF4b1` (`L68`) | `forge_fixes\matches\SF4b1_alone_vs_base_1000g_50k\summary.json` | `1,000 / 234–519–247 / -4.52 [-17.04, +7.99] / -0.71 / 24.0% / [13,126,232,119,10]` *(`-5.21` w/ SF6b+SF8, `-15.99 [-29.09,-2.95]` w/ SF8)* | `1000 / 234-519-247 / -4.52 [-17.04, 7.99] / -0.708 / 23.95% (23.93%) / [13, 126, 232, 119, 10]` *(and `-5.21 [-17.81, 7.37]`, `-15.99 [-29.09, -2.95]`)* | **EXACT MATCH** |
| `SF9` (`L69`) | `forge_fixes\matches\SF9_minor_corrhist_conservative_600g_50k\summary.json` | `600 / 157–295–148 / +5.21 [-12.80, +23.25] / +0.57 / 71.5% / [12,69,133,70,16]` | `600 / 157-295-148 / 5.21 [-12.8, 23.25] / 0.567 / 71.48% (71.51%) / [12, 69, 133, 70, 16]` | **EXACT MATCH** |
| `G2 vs G1` (`L70`) | `forge_fixes\matches\G2_1024p_vs_G1_768_1000g_50k\summary.json` | `1,000 / 287–470–243 / +15.30 [+1.65, +28.99] / +2.20 / 98.6% / [12,120,204,140,24]` | `1000 / 287-470-243 / 15.3 [1.65, 28.99] / 2.197 / 98.6% (98.61%) / [12, 120, 204, 140, 24]` | **EXACT MATCH** |
| `G2 vs r0067` (`L71`) | `forge_fixes\matches\G2_1024p_vs_r0067_1000g_50k\summary.json` | `1,000 / 238–469–293 / -19.13 [-33.23, -5.09] / -2.67 / 0.38% / [28,137,218,96,21]` | `1000 / 238-469-293 / -19.13 [-33.23, -5.09] / -2.672 / 0.38% (0.37%) / [28, 137, 218, 96, 21]` | **EXACT MATCH** |

- **Secondary matches cited in Section 6 (`L89`, `L91`):** `SF5a` (`-101.21`), `SF4b2` (`-19.71`), `SF7` (`-13.90`), `COMBO_v1` (`-0.35`), and `M_W1` (`+0.69 ± 13.90`) all match their raw `summary.json` files on disk.
- **Live CPU Queue Delta (`ALL_MATCHES_SCOREBOARD.md`):** Because `task-5161` continues running in parallel, `ALL_MATCHES_SCOREBOARD.md` already lists **`37` completed matches** (adding newer screens not yet in this draft snapshot: `SF13 +20.87`, `W2_proto_1 +11.01`, `SF6 +10.43`, `SF15 +7.53`, `SF14 +5.21`, `SF1 +2.90`, `SF11 +1.74`, `SF16 -0.00`, `SF12 -4.05`, `SF2 -4.05`, `SF3 -6.37`, plus `W2_proto_2 -0.00` and `W2_proto_3 -6.37` in `forge_fixes\matches\`).

---

## 4. Path Existence, SHA-256, and Raw Metric Verification

### 4.1 Explicit Path Existence (`71/71` Exist, `0` Broken)
- `C:\nnue-lab\neon\forge_fixes\` items in Sec 11 (`L146`, excluding glob `patches\SF*.patch`): **`35/35` exist** (`0` missing).
- `C:\nnue-lab\neon\filter_quest\` items in Sec 11 (`L148`): **`14/14` exist** (`0` missing).
- Explicit paths across Sec 1–10 (`forge.exe`, `r0067\cand.fnn3`, `final_eval_r0203_w14_w15.plain`, `datagen_uci.py`, `filterqc.py`, `results\*.json`, `matches\`, `ALL_MATCHES_SCOREBOARD.md`, `run_master_gates.py`, `teamwork_wave2`, `teamwork_wave3`, `SERVER_DAY_2B_RUNBOOK.md`, `rescore_depth_curve.json`, `gen_cc0_selfgame_fqs_v2.py`, `G3_FULL25`, `CHECKPOINT_LATEST.md`): **`22/22` exist** (`0` missing).

### 4.2 SHA-256 & Byte-Size Verification

| Artifact | Path | Verified Bytes | Verified Full SHA-256 | Match vs Handoff |
|---|---|---:|---|---|
| `forge.exe` | `C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe` | 2,390,528 | `cef2f21589102392fdd7e3cbde74bfd01baa94f9677a2be33365f68e4bceb03d` | **EXACT MATCH** |
| `r0067` `cand.fnn3` | `C:\nnue-lab\runs\forge\r0067\train\cand.fnn3` | 9,463,528 | `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28` | **EXACT MATCH** |
| `final_eval_r0203_w14_w15.plain` | `C:\nnue-lab\neon\filter_quest\eval_sets\final_eval_r0203_w14_w15.plain` | 19,356,333 | `b8ff64590bd511584dbcf603dbedb30dd1a2c54f3b4aae844904bd33cf96175b` | **EXACT MATCH** |
| `dead_draws_20k_s5disjoint.fqs.z` | `C:\nnue-lab\neon\forge_fixes\anchors\dead_draws_20k_s5disjoint.fqs.z` | 125,433 | `7653279511862abc7d5bd856f14e61a594932ba625be09107e168d43e9b775a5` | **EXACT MATCH** |
| `dead_draws_20k_clean.fqs.z` | `C:\nnue-lab\neon\forge_fixes\anchors\dead_draws_20k_clean.fqs.z` | 127,484 | `f2073b88b95d109c5b130fce503f8f9126baf852c47db4af4e31f9c5e0976716` | **EXACT MATCH** *(hits `S5_K-K`)* |
| `won_endings_syzygy_20k.fqs.z` | `C:\nnue-lab\neon\forge_fixes\anchors\won_endings_syzygy_20k.fqs.z` | 154,309 | `c2f51696b886c6cad78da2cca253352d79e6a188778c5ab35526b6321a4a96de` | **EXACT MATCH** |
| `opening_ply012_anchors.fqs.z` | `C:\nnue-lab\neon\forge_fixes\anchors\opening_ply012_anchors.fqs.z` | 2,200 | `6703857609240a6cbdf07d85e95d1747d939ccb307b685eb0c6c76675e4540d0` | **EXACT MATCH** |
| `book_cc0_clean.epd` | `C:\nnue-lab\neon\forge_fixes\book_cc0_clean.epd` | 15,793,891 | `d49523f18e004126fca3914ffb92a89cfc3c8b4427ce4c18d4405faeb1102191` | **EXACT MATCH** (`233,104` pos, `0` UHO overlap) |
| `datagen_uci_startpos_only.patch` | `C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_startpos_only.patch` | 3,816 | `c0c92cb75a56b8a5e0d9670befd6509e21a912ac6facf2124e62e1734494eba8` | **EXACT MATCH** (`78` lines) |

### 4.3 Raw Dataset, Training, and Rescore Metrics
- **`G1` & `G2` (`metrics.json`, `net_sanity_v2.txt`, `heldout_eval_*.json`):** `G1` `final_train_loss=0.004862` (`eval=0.014875`); `G2` `final_train_loss=0.004601` (`eval=0.014689`, `-5.37%` train loss vs `G1`); `G2` `net_sanity_v2.txt` confirms `S5` OK (`K-K +7`, `KN-K +9`, `KB-K -11`, `KNN-K +33`); `heldout_eval_r0067.json` `median_abs_cp=19.0` vs `heldout_eval_G2.json` `8.9`.
- **`G3_FULL25` (`diag_e12/eval_full.json`, `diag_e12/sf19_slice.json`, `CHECKPOINT_LATEST.md`):** `sanity_flag_count=0`, `m4_wdl_mse=0.01185`, `sf19_slice.overall.wdl_mse=0.053505`. `CHECKPOINT_LATEST.md` (`21:14 PC`) records live advancement to Epoch `18+/40`, `LOSS 0.006569`, `1,904,296 pos/s` (handoff snapshot was Epoch `10+/40`, `LOSS 0.006550`, `1.855M pos/s`).
- **`cc0_shards_4k_v2` & Dedup (`audit.json`, `audit_cc0_v2_dedup_phase.json`, `cc0_v2_dup_split.json`, `cc0_f2_dedup_{avg,first}/summary.json`):** `2,000,004` raw (`10.09 B/row`, `stm_white_pct=50.04%`, `abs_ge800_pct=10.18%`) -> `1,839,070` clean -> `1,612,164` unique (`226,906` dups = `12.338%`; `800_1199=6.52%`, `1200_plus=2.88%` = `9.40%` clean). `cc0_v2_dup_split.json`: `k0_replay_ge100=33.07%` + `k1_replay_15_99=27.23%` (`60.30%` of dups; `4.08% + 3.36% = 7.44%` of clean rows).
- **Streaming `.plain -> .fqs.z` (`f0_base_filter/summary.json`, `f0_min_integrity/summary.json`):** `596,748.1 rec/s` (`26.493s`, `10.52 B/kept`) and `605,135.4 rec/s` (`26.126s`, `10.33 B/kept`).
- **Rescore (`rescore_depth_curve.json`, `cc0_r1_rescore16k_0p5pct/rescore_summary.json`):** `2k=0.00849` (mid `0.01212`), `4k=0.00770`, `8k=0.00675` (mid `0.00927`, `-12.34%` vs `4k`), `16k=0.00622` (`-19.22%` vs `4k`); `EXP-R1` `8,060` positions rescored in `37.30s` (`mad_delta_cp=45.86..49.19`, `0` sign flips).
- **Scorecard (`baseline_r0067_scorecard.json`):** `sanity_flags=["S1_startpos", "S2_start_vs_e4", "S5_dead_draws"]`, `ob0_ob1_cliff_median_jump_cp=143.5`.

---

## 5. Residual Minor Text Discrepancies & Freeze Marker Inventory

### 5.1 Five Minor Residual Text Discrepancies (Polish Before Final Freeze)
1. **`L82` (`Wave 3 Stream C verify_all_patches.py (47/47 patches RC=0)`):** Wave 3's `PATCH_AUDIT_MATRIX.md` verified **`44/44`** patches (`32` `forge_fixes/patches` + `9` `wave2/streamA_search/patches` + `3` `filter_quest/patches`). (`47` is the current `.patch` count in `forge_fixes\patches\` alone after Rounds 9–11; Wave 4's `verify_all_patches_w4.py` verifies **`63/63`** across all 5 folders.)
2. **`L146` (`patches\SF*.patch (SF1..SF26)`):** `C:\nnue-lab\neon\forge_fixes\patches\` contains **35** `SF*.patch` files spanning **`SF1..SF9` and `SF11..SF33`** (`SF10` does **not** exist in `patches\`, and Rounds 9–11 added `SF27..SF33`).
3. **`L38` (`G2` anchor filename nuance):** `L38` states `G2` and `G3_FULL25` launched with `dead_draws_20k_clean.fqs.z`, whereas `G2_v3p_1024_pairwise_psqt\metrics.json` `args.anchor_shards` actually records `dead_draws_20k.fqs.z` (while `launch_g3_full25.py:43` uses `dead_draws_20k_clean.fqs.z`). Both hit `S5_K-K` (`s5_s7_overlap_audit.json`), so the substantive transparency note stands.
4. **`L25` (`gen_cc0_selfgame_fqs_v2.py` unprefixed path):** Listed alongside `filter_quest\` scripts, whereas `gen_cc0_selfgame_fqs_v2.py` resides at `C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\gen_cc0_selfgame_fqs_v2.py` (covered by `teamwork_wave2\` on `L147`; `forge_fixes\gen_cc0_selfgame_fqs.py` is v1).
5. **`L28 / L103 / L134` (`769k` / `769,232 rec/s`, `5.58x` speedup, `0/9` stat diffs):** Internally consistent with `cc0_f2_dedup_avg\summary.json` (`769,232 / 137,741.3 = 5.58x`) and `partition_fqs_buckets.py` (`< 0.72 GiB RAM/worker` at 2.0B/128 buckets), **but** no persisted benchmark JSON storing `769,232 rec/s` exists under `filter_quest\results\` or `stage2_data\`.

### 5.2 Living-Draft Progression (Expected During Parallel Runs)
- `G3_FULL25` (`L72`, `L98`, `L139`): Draft snapshot shows Epoch `10+/40`, `LOSS 0.006550`, `1.855M pos/s`; `CHECKPOINT_LATEST.md` (`21:14 PC`) shows Epoch `18+/40`, `LOSS 0.006569`, `1,904,296 pos/s`, and `diag_e12\cand.fnn3` (`0` `net_sanity.py` v2 flags).
- Section 4 vs `ALL_MATCHES_SCOREBOARD.md`: Live CPU queue has grown to `37` completed matches.

### 5.3 Exact Freeze Marker Enumeration (`8` Markers Across `5` Lines)
These markers currently cause `stage_teamwork_delivery_w4.py --live` to refuse execution (`RC=2`):
1. **`L3`:** `[PENDING POST-G2/G3]`
2. **`L72` (x2):** `[TRAINING]` | `[TRAINING]`
3. **`L73` (x2):** `[PENDING]` | `[PENDING]`
4. **`L109`:** `[TESTING NEXT]`
5. **`L110`:** `[TESTING NEXT]`
6. **`L111`:** `[TESTING NEXT]`
