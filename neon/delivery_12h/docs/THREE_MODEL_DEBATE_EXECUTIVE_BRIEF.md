# FORGE — Three-Model Debate Executive Brief (`Astra / Opus / Neon`)

**Wave 7 Snapshot (UTC):** `2026-11-28T09:20Z` | **Prepared by:** Stream C (`streamC_debate_pack_w7`)
**Integrity Rule (R5):** Training loss, validation MSE, `M4`/`SF19` scorecards, and OLS piece weights are strictly diagnostic leads — never Elo claims. Screens (`600g @ 50k`), confirmations (`1,000g @ 50k`), `250k` decision matches, and equal-time (`6+0.06`) matches are NEVER pooled.

---

## 1. Executive Verdict: What Changed Through Equal-Time & `keep_noisy` Forensics

1. **Immediate `V3P` Live-Loop Placement Is OFF the Table Today (Neon + Opus Consensus):**
   `G3_FULL25` (`1024w` Pairwise+PSQT, `keep_noisy=true`, `353.45M` rows, `cand.fnn3` `sha256=7ff7789032491aa7...`) beat live `r0067` at `250k` (`+22.03` Elo) and `r0202` at `50k` (`+22.27` Elo), but tied at `250k` vs `r0202` (`-0.58` Elo) and landed at **`-0.35 [-8.35, +7.66]` Elo** (`480-1038-482`) at equal-time `6+0.06` on PGO builds. Its `-16.05%` to `-16.63%` clean idle NPS cost (`3.021M–3.042M` vs `3.623M` NPS) offsets its per-node edge. `V3P` (`1024w/kb16` or `1536w`) therefore waits for **Server Day (`1.4B–2.0B` quiet-filtered positions)**, while the verified 5-surface loop package (`teamwork_wave6/`) remains frozen for Server-Day readiness.
2. **Mandatory `--skip-fqs-noisy` Proven for `FORGENN3-P`:**
   Keeping `bit0=1` noisy capture/recapture rows (`17.12%` of CC0 `4k` positions) collapses `FORGENN3-P` (`G3b_skipnoisy` beats `G3a_keepnoisy` by **`+699.72`** eq-raw / **`+651.27`** eq-ret Elo), even with `r0067` distillation (`G3AB_DISTILL_REGIME_CHECK.json`). All `9/9` clean quiet Stage-2 GPU arms (`STAGE2_QUIET_GPU_SUMMARY.json`) restored `ols_Q = 988.5–1033.8 cp`. Whether removing `--keep-noisy` also helps the **live `768w` SCReLU** architecture is currently under test (`OPUS_R1_live768_skipnoisy` + required `R1-keep` twin).
3. **`1024p/kb16` Is the Clean Server-Day Hardware Sweet Spot:**
   Clean GPU+CPU-idle 5-architecture PGO benchmarks (`CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json`) show **`1024p/kb16`** (`2.941M` NPS, `0.8139x` vs live PGO `3.614M`) pays only **`-0.61%` (`-0.6%`)** NPS vs `1024p/kb8` (`2.959M`), whereas `1536p/kb8` (`2.665M`, `0.7374x`) pays **`-26.26%` (`-26.3%`)** vs live PGO (`-9.95%` vs `1024p/kb8`).

---

## 2. Verified Positive Findings & Core Artifacts

| Finding / Artifact | Verified Evidence (Exact Values from Disk) | Primary Source Path |
|---|---|---|
| **`G3b_skipnoisy` vs `G3a_keepnoisy` (eq-raw)** | **`+699.72 [+642.27, +784.63]` Elo** (`972-21-7`, `z=+141.30`, `LOS=100.0%`, `ptnml=[0, 0, 7, 21, 472]`, `0` TL/IL, `50k`) | `neon\forge_fixes\matches\G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k\summary.json` |
| **`G3b_skipnoisy` vs `G3a_eqret` (eq-ret)** | **`+651.27 [+597.55, +727.83]` Elo** (`967-20-13`, `z=+115.77`, `LOS=100.0%`, `ptnml=[0, 0, 13, 20, 467]`, `0` TL/IL, `50k`) | `neon\forge_fixes\matches\G3b_skipnoisy_vs_G3a_eqret_1000g_50k\summary.json` |
| **CC0 Noisy Physics Forensics** | `1,839,070` rows: `17.12%` noisy (`bit0=1`), `mean_stm_mat = -1.161` pawns vs `mean_sc = +35.9 cp`; `22.26%` vs `1.76%` (`12.6x`) hanging piece at `\|sc\|<100`; **`2.68%` vs `0.02%` (`134x`)** hanging Queen | `neon\forge_fixes\CC0_NOISY_VS_QUIET_FORENSIC.json` |
| **Distilled Regime Check (`r0067` `w=0.2`)** | `keep_noisy`: `OLS Q=201.8 cp`, `M4 MSE=0.02775`; `skip_noisy`: `OLS Q=1002.7 cp`, `M4 MSE=0.02252`, **`0` sanity flags** | `neon\forge_fixes\G3AB_DISTILL_REGIME_CHECK.json` |
| **`G3_FULL25` vs `r0067` (`250k`)** | **`+22.03 [+5.88, +38.28]` Elo** (`165-308-127`, `z=+2.675`, `LOS=99.63%`, `ptnml=[4, 60, 142, 82, 12]`; `50k` was `+4.86 [-8.49, +18.23]`) | `neon\forge_fixes\matches\G3_FULL25_vs_r0067_600g_250k\summary.json` |
| **`G3_FULL25` vs `r0202` (`50k`, same 25r)** | **`+22.27 [+8.64, +35.96]` Elo** (`298-468-234`, `z=+3.206`, `LOS=99.93%`, `ptnml=[16, 98, 217, 144, 25]`) | `neon\forge_fixes\matches\G3_FULL25_vs_r0202_1000g_50k\summary.json` |
| **Clean 2-Build Bit-Exact & PGO Speed** | `v3p_bit_exact_nodes = 869,964` (all 6 V3P builds); `v3_fused_PGO_A/B = 3,020,708 / 3,041,832` NPS (`0.8337x / 0.8395x` vs live `3,623,176`) | `neon\forge_fixes\CLEAN_IDLE_SPEED_2BUILDS.json` |
| **Clean 5-Arch Server-Day PGO NPS** | `live_pgo_r0067`: `3,613,642` (`1.000x`); `1024p/kb8`: `2,959,061` (`0.8189x`); **`1024p/kb16`: `2,940,975` (`0.8139x`, `-0.6%` vs `kb8`)**; `1536p/kb8`: `2,664,542` (`0.7374x`, `-26.3%`) | `neon\forge_fixes\CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json` |
| **Parity `7/8` Minimal Loop Patch** | `datagen_uci_parity_7_8_minimal.patch` (`sha256=184c6d2b...`): Opus verdict `YES WITH REMARKS` (`OPUS_TO_NEON.md:2834-2855`), ready at loop restart; targets live-loop `+153 cp / 61.4%` White bias (`200`-game `startpos` pilot cut bias `+127.12 -> +68.46 cp`, `57.75% -> 55.00%` White score) | `neon\forge_fixes\patches\datagen_uci_parity_7_8_minimal.patch` |
| **9/9 Quiet Stage-2 GPU Arms** | All 9 `--skip-fqs-noisy` arms trained on `1,442,765` kept rows: `ols_Q = 988.5–1033.8 cp`, `syz_win_ok_pct = 99.25–99.3%`, `syz_draw_med_cp = 26.9–29.4` | `neon\filter_quest\STAGE2_QUIET_GPU_SUMMARY.json` |
| **3 Frozen Disjoint Anchors** | `dead_draws_20k_s5disjoint.fqs.z` (`sha256=76532795...`), `won_endings_syzygy_20k.fqs.z` (`sha256=c2f51696...`), `opening_ply012_anchors.fqs.z` (`sha256=67038576...`): `0` S5/S7 & `0` heldout overlap | `neon\forge_fixes\anchors\heldout_integrity_verification.json` |

*(Baseline identity note: `C:\nnue-lab\runs\forge\r0067\train\cand.fnn3` verified SHA-256 is `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`, correcting the `34d2248d...` shorthand typo in `NEON_TO_OPUS.md:850`.)*

---

## 3. Preserved Negative / Null Results, Disagreements & Methodological Caveats

| Item | Exact Result / Evidence | Debate Caveat & Preserved Interpretation |
|---|---|---|
| **`G3_FULL25_PGO` Equal-Time (`6+0.06`)** | **`-0.35 [-8.35, +7.66]` Elo** (`480-1038-482`, `z=-0.085`, `LOS=46.61%`, `ptnml=[10, 239, 502, 241, 8]`, `0` TL/IL, `3,994.4s`) | Ran at `concurrency=10` on 8 physical cores (two 1T engines share cores). **Opus (`OPUS_TO_NEON.md:3013`):** stays a footnote — cannot turn `-0.35 +/- 8` into a placement case; all future clock tests use `concurrency <= 7`. Also `v3p_pgo_r0067_768screlu` ran at `3,450,211` NPS (`0.9548x` vs live `forge.exe`), so `FORGE_FINAL_G3_PGO.exe` must NOT replace live `forge.exe` for `768w` nets. |
| **`OPUS_r0202_vs_r0067_1000g_250k`** | **`-4.86 [-16.64, +6.90]` Elo** (`230-526-244`, `z=-0.811`, `LOS=20.88%`, `ptnml=[8, 126, 244, 116, 6]`, both on `base_r15dsg.exe`) | Refutes Opus's hypothesis that `r0202` was secretly stronger at `250k` and blocked by the `50k` SPRT gate (`OPUS_TO_NEON.md:2953-2955`). |
| **`G3_FULL25_vs_r0202_600g_250k`** | **`-0.58 [-16.30, +15.14]` Elo** (`152-295-153`, `z=-0.072`, `LOS=47.12%`, `ptnml=[4, 81, 130, 82, 3]`) | Depth reversal from `+22.27` (`50k`) to `-0.58` (`250k`) (`+22.9 +/- 20.8`, `z ~ 2.15`). |
| **`250k` Heterogeneity & Pooling Caution** | Weighted least squares across the three `250k` matches: **`chi-square = 4.5`** (1 df, `p ~ 0.03`), pooled `G3 - r0067 = +10.9 +/- 12.5`, `r0202 - r0067 = +1.0 +/- 10.4` | **Opus (`OPUS_TO_NEON.md:2957-2960`):** `+22.03` vs `r0067` is likely high; cautions against claiming `"G3_FULL25 broke through at 250k"` or `"768w plateau"` from single matches. |
| **Opus `OLS` Scale & Meaning Caveat** | Raw `OLS Q`: `r0067` `307.3` (`Q/P=5.97`), `G3_FULL25` `293.3` (`Q/P=6.21`), `G3b` `1016.0` (`Q/P=10.54`) | **Opus (`OPUS_TO_NEON.md:2994-3000`):** compare scale-free `Q/P` ratios (since `unit_raw_per_pawn` varies per net: `G3_FULL25` `172.2`). Self-play middlegame OLS is a probe reading, not proof of weakness (`S6` gives `r0067` `Q=1931`). Plus `G3b vs G3a` proves `keep_noisy` breaks V3P — **not** a gain over live `768w` yet. |
| **`M_SWA` + Quarantined `swa24_40`** | **`-29.95 [-43.27, -16.72]` Elo** (`229-456-315`, `z=-4.447`, `LOS=0.0%`, `ptnml=[26, 147, 226, 89, 12]`) | Cross-cycle `5e-4` LR-restart SWA causes basin drift; sibling `M_SWA_ctrl_swa24_40_vs_ctrl_n50k` quarantined (`v3_model_check` `3.02 cp > 3 cp`, no `summary.json`). |
| **`COMBO_v2` (`SF8+SF13+LmrDeeper`)** | **`-3.13 [-15.94, +9.68]` Elo** (`243-505-252`, `z=-0.479`, `LOS=31.61%`, `ptnml=[15, 128, 216, 133, 8]`) | Negative bundle interaction despite individual wins (`SF13 +8.34`, `LmrDeeper +8.34`, `SF8 +4.86`); rules out blind stacking. |
| **`SF4b1` Rejected (4-Match Set)** | `600g` screen `+15.06 [-0.35, +30.54]` (`154-318-128`), then **`-4.52`** (`SF4b1_alone`, `234-519-247`), **`-15.99 [-29.09, -2.95]`** (`SF4b1_SF8_noDeeper`, `236-482-282`), **`-5.21`** (`V3P_SF4b1_SF6b_scaled_SF8`, `241-503-256`) | Classic `600g` screen false positive rejected across all 3 `1,000g` confirmations. |

**Currently OPEN / RUNNING (Not Yet Frozen):**
- **`OPUS_R1_live768_skipnoisy`** (GPU training active in `neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy\`; `cand.fnn3` not written yet) + **Opus's required same-runner `R1-keep` twin** (`OPUS_TO_NEON.md:3016-3020`: train `--keep-noisy` in the identical standalone runner before `R1-skip vs R1-keep` at `250k`, `1,000g`; if positive, 2nd seed + `R1-skip vs r0067` at `250k` and `6+0.06` at `concurrency <= 7`).
- **10 Clean Quiet Stage-2 Matches (`S2Q_*`)** (`run_stage2_clean_skipnoisy_matches.py`, `1,000g @ 50k`): `S2Q_G4a_losspow25_vs_G3b_1000g_50k` finished (`+8.34 +/- 15.94`), `S2Q_G4b` running, 8 queued; per Opus (`OPUS_TO_NEON.md:3022`), `50k` matches are filters only — winners require `250k`.
- **`LmrDeeperShallower` SPRT `[0, 5]`** (`run_lmr_deeper_sprt.py`): queued (`not_started`), plus stale living docs (`HANDOFF_12H_DATA_QUALITY.md` has 6 `[PENDING*]`/`[TESTING*]` markers; `ALL_MATCHES_SCOREBOARD.md=57` vs `.json=47` vs `DEBATE_EVIDENCE_INDEX_W6.md=55`).

---

## 4. The Five Open Debate Decisions (`Astra / Opus / Neon`)

1. **Immediate Live-Loop Non-Placement vs Deferral to Server Day `2.0B` + Parity `7/8` & R1 `768w` A/B:**
   Confirm non-placement of `V3P` on `353M` keep-noisy rows (`G3_FULL25_PGO -0.35` Elo). Decide exact loop-restart sequencing for `datagen_uci_parity_7_8_minimal.patch` (`YES WITH REMARKS` approved) and whether `OPUS_R1` (`768w` without `--keep-noisy` vs same-runner `R1-keep` twin) earns interim live-loop placement if it wins at `250k` and `6+0.06` (`concurrency <= 7`).
2. **Tier-2 Filter Policy (Server Day & Live Loop):**
   Lock mandatory `--skip-fqs-noisy` (`bit0=0`) + `--skip-check` (`bit1=0`) for `FORGENN3-P` Server-Day training (`+699.72 / +651.27` Elo). Use the 10 `S2Q_*` filter matches -> `250k` confirmations to decide `--loss-pow 2.5` (`G4a`), `--ob-reweight cc0` (`G4b`), `EXP-F1` hard filter vs `EXP-W3` soft-weighting (`0` rows discarded), `EXP-F2` dedup (`first` vs `avg`), and `EXP-R1/R1b` selective `16k` Forge rescoring (`--prioritize-opp-castle`).
3. **Server-Day Net Width & King Buckets on `2.0B` Quiet-Filtered Positions:**
   Evaluate primary **`1024w/kb16`** (`2.941M` NPS, `-0.61%` vs `1024w/kb8` `2.959M`, `0 cp` parity with zero C++ changes) vs `1024w/kb8` vs **`1536w/kb8`** (`2.665M` NPS, `-26.26%` vs live PGO) using `SERVER_DAY_COST_MODEL.json` *(cloud EUR/hr & H100/4090 speeds are planning estimates; storage, `766.3k rec/s` dedup, `<0.72 GiB/worker`, `19.7 GB` `.fqs.z`, & 7900 XT `1.91M pos/s` are measured)*:
   - **Scenario A (`2.0B`, `4k`, `256c EPYC + 1x H100`, `1024w`):** `14.56h` datagen + `0.11h` dedup + `2.65h` H100 (`20 ep`) = **`€72.40`** (`€36.20/1B`).
   - **Scenario B (`2.0B`, `1536w`, `1x H100`):** `3.84h` H100 = **`€75.25`** (`+€2.85`, or `+€6.35–€9.21` for an extra standalone H100 arm).
   - **Scenario C (`1.5B`, `2k`, `256c EPYC + Local 7900 XT`, `1024w`):** **`€28.52`** (`€19.01/1B`); **Scenario D (`1.5B`, `4k`, `128c + 4090`):** **`€50.98`**.
4. **Search / TM 1-by-1 Placement Stack & Post-Placement SPSA:**
   Execute Opus's zero-C++ `LmrDeeperShallower=true` declared SPRT `[0, 5]` (`run_lmr_deeper_sprt.py`). Place ONLY independently confirmed orthogonal wins 1-by-1 (respecting `SF38` vs `SF39` mutual exclusion in `ROUND13_BUILD_REPORT.json`; never `SF4b1`, `SF15`, or unconfirmed bundles), then re-tune the 15 eval-dependent pruning margins warm-started from all 45 live Big Tune options (`POST_G3_SPSA_RECIPE.md`) with independent `2,000g @ 6+0.06` (`concurrency <= 7`) verification.
5. **Owner-Gated Escalation Policy (Residual Quiet `SF19` Blunders):**
   In `G3_RESIDUAL_BLUNDER_DIAGNOSIS.json` (`n=6,000`), **`63.43%` (`503/793`)** of `G3_FULL25_e40` `SF19` severe errors (`>=0.35`) are quiet (`137` opp-castle MG) and **`73.33%` (`88/120`)** persist at `400` nodes (`G3_QUIET_BLUNDER_DEPTH_PROBE.json`: `400n/4k/16k` resolve `27.0% / 36.0% / 40.0%`). If post-Server-Day `2.0B` + search stack blunders remain high, decide between **cross-architecture self-play (`1024w` Pairwise+PSQT vs `768w` SCReLU) + `random_multi_pv`** vs **external teacher/data** (owner-gated).
