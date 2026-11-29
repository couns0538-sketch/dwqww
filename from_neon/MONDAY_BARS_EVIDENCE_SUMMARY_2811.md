# Monday Bars Evidence Summary (`28 Nov 2026`) — Forge Wave 16 Master Ledger

- **Prepared For:** Opus, Fable, Astra, and Owner
- **Snapshot Timestamp:** `2026-11-29T01:00:24Z` (`2026-11-28 17:00:24` local PC)
- **Live Baselines:**
  - **Engine:** `forge/r15dsg` (`C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe`, `2,390,528` B, SHA-256 `cef2f215...`, `Opus verified` baseline; `3,604,157` clean idle d15 NPS `Neon's count`).
  - **250k Fixed-Node Engine:** `C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe` (`2,382,848` B, SHA-256 `5e6f333b...`, `Opus verified` identical search on `0/300` UHO d9 test `Neon's count`).
  - **Best Net:** `C:\nnue-lab\runs\forge\r0067\train\cand.fnn3` (`9,463,528` B, SHA-256 `737f1978...`, `768w` SCReLU `kb=8`, `ob=8`).

---

## 1. Executive Summary, Monday Readiness Matrix & Live Snapshot

### 1.1 Non-Elo & SPRT Bias Disclosure Box (Mandatory Evidence Rules)
1. **Strict Provenance (`Opus verified` vs `Neon's count`):** Every statistic below is tagged **`Opus verified`** (independently recounted from raw PGNs, `qc.json`, `r1_summary.json`, or source code by Opus in `C:\nnue-lab\neon\OPUS_TO_NEON.md` / `C:\nnue-lab\PLAN.md`) or **`Neon's count`** (measured by Neon / Teamwork scripts and not yet independently re-executed by Opus or Fable).
2. **SPRT Early-Stopping Upward Bias:** Every `SPRT [0, 10]` match that stops early at `H1` overstates its point estimate (`R1-skip` Seed 1 `+15.49` and Seed 2 `+12.57`; true effect on the same data is estimated by Opus at `~+8..+14` Elo @ `250k`). Fixed-horizon matches (`1,000g` / `2,000g`) carry zero SPRT early-stopping bias.
3. **Zero Elo Overclaiming:** Offline training/validation losses, `net_sanity` (`S1`/`S2`/`S5`), `OB0/OB1` cliff jumps, `heldout_syzygy_4k` MSE, filtered row/correlation counts, and `40`-UHO ms timing probes are **strictly diagnostic** and NEVER establish Elo. Only declared `fastchess` games decide playing strength.
4. **No Banned-Term Claims:** Neither own-side optimism (`SF19` `+0.38`/`+0.73` pawn vs RubiChess) nor `S2`/`S5` is claimed as resolved across all seeds without fresh net/match proof.

### 1.2 Monday Readiness Matrix (`PLAN.md:546-548` & `OPUS_TO_NEON.md:3486`)

| Monday Bar | Bar Requirement (`PLAN.md:546-548` + `OPUS_TO_NEON.md:3486`) | Verified Status Now (`2026-11-29T01:00:24Z`) | Remaining Gates / Blockers Before Monday Placement |
|---|---|---|---|
| **Bar 1 — Search Fixes (& TM Follow-Up)** | Every fix behind its own default-off UCI option (`default = today`); `bench 11/13`, `perft 5`, and `same_search` hold; bundle wins `SPRT [0, 10]` @ `250k` (`H1`); **`6+0.06` confirmation not negative**. | **IN PROGRESS (CPU):** `UNIFIED_SEARCH_TREE.patch` (`a7b59ec6...`) built into `forge_unified.exe` (`7c2a4a46...`); default gates & `3x b13` NPS measured (`Neon's count`); Fable `P1..P8` addressed (with `SF17/SF18` correction vs `STATE_TABLE_2811.md:71`); `UNIFIED_SEARCH_BUNDLE_250k_SPRT` (`Opus verified` sound declaration) **ACTIVE NOW** on CPU. Wave 16 M2 `TM_SOFTCAP_ON_UNIFIED.patch` (`ef55eba6...`) passed `18/18` pytest (`M2` Gate PASS). | 1. Finish `UNIFIED_SEARCH_BUNDLE_250k_SPRT` (`H1` -> `6+0.06` clock confirmation; `H0` -> split 3+3).<br>2. Fable Monday code read of `UNIFIED_SEARCH_TREE.patch`.<br>3. `AspFailHighReduce=1` (`+10.95` @ `250k`, `Opus verified`) awaits Fable Monday check (`CONFIG_EDIT_AFH_DRAFT.md`).<br>4. TM follow-up (`TM Test A` `TmFinishIteration` then `TM Test B` `TM_SOFTCAP_6P006`) gated on `600k` diag + `from_neon/` non-Stockfish citations + Astra check + clean PGO build. |
| **Bar 2 — NNUE Fixes** | `skip-noisy` placed (proven twice); next net passes `net_sanity` `S1` (`-10..+60`) & `S2` (`\|start + after 1.e4\| <= 40`), OR a net fixing them wins `250k` vs `r0067` with **`6+0.06` not negative** (`OPUS_TO_NEON.md:3486`, subject to Fable/Owner agreement). | **HALF MET / IN PROGRESS:** `--skip-noisy` proven twice (`+15.49` Seed 1, `+12.57` Seed 2, both `H1`, `Opus verified`, SPRT bias noted) + `+30.65` fixed @ `250k` vs `r0067` (`Opus verified`); `R1-skip` vs `r0067` @ `6+0.06` is `+6.43 [-1.47, +14.33]` (`Opus verified`, INCONCLUSIVE, not negative). Seed 1 passes `S1=+42, S2=32` (`Opus verified`), fails `S5` (`KNN-K=+97` raw, `Opus verified`; `108.5 cp` cliff, `Neon's count`); Seed 2 passes `S1=+56`, **fails `S2=55`** & `S5` (`KNN-K=+114` raw, `Neon's count`). | 1. Fable Monday second-read of `loop_place/` skip-noisy package (`8/8` `Opus verified`) + idle-CPU swap.<br>2. `OPUS_R1_skip_vs_r0067_1000g_600k` diagnostic (`4d4e4d30...`) to separate TM vs depth.<br>3. Train & test queued GPU #2 `R2_live768_skipnoisy_anchored` (`1104baf2...`, `0.2866%` anchors, targets `S5 <= 50 cp` & `OB0/OB1` cliff <= `102.8 cp`).<br>4. `F-02` parity (`datagen_uci_parity_7_8_minimal.patch`) & `SF19` optimism remain post-placement/Server-Day `2.0B` targets. |
| **Bar 3 — Filtering Improvement** | Faults measured with exact sizes; a net trained on improved filter beats today's filter at `250k` (`SPRT [0, 10]`, `H1`), same recipe/window/seeds as `R1` (+ `6+0.06` confirmation per `OPUS_TO_NEON.md:3543`). | **AUDIT COMPLETE / GPU #1 ACTIVE:** Two-half `r0202` audit complete (`16,005,733` raw / `15,156,682` kept / `849,051` dropped `Opus verified`; deep pathologies & sub-breakdowns `Neon's count`); `SyzygyPath` OFF in search (`Opus verified`). **GPU #1 `F_FIX_25R_v2`** (3 predicates: `F-03`, `F-03b`, `F-08`) finished `.plain` load & is training on GPU. **Wave 16 M1 `F_FIX_25R_v3`** (`run_f_fix_25r_v3.py`, `14/14` pytest + `--dry-run` PASS) addresses all 4 Opus Point 4 faults. | 1. Complete GPU #1 `F_FIX_25R_v2` training -> `250k` `SPRT [0, 10]` -> Seed-2 replicate + `2,000g @ 6+0.06`.<br>2. Launch queued `F_FIX_25R_v3` (using `FORGE_PARSE_PROCS=2` + `mem_room 16` against commit room per `OPUS_TO_NEON.md:3620`) -> `250k` + Seed-2 + `6+0.06`.<br>3. Fable Monday review of `filterqc_monday_fixes_DRAFT.patch` (`da9c3c16...`).<br>4. Astra first push expected ~`22:00 PC` (`astra_branch.py fetch`). |

### 1.3 Live Disk, Process & Queue Snapshot (`2026-11-29T01:00:24Z`)

- **GPU Stream #1 (`F_FIX_25R_v2`):** Finished its 25-round `.plain` load (`r0178..r0202`) by `00:47:54Z` (`NEON_TO_OPUS.md:1488`) and is actively training on GPU (`C:\nnue-lab\neon\forge_fixes\gpu_runs\F_FIX_25R_v2\` exists at `2026-11-29T01:00:24Z`, `0` files yet while pre-first-checkpoint).
- **CPU Stream (`UNIFIED_SEARCH_BUNDLE_250k_SPRT`, `fastchess.exe` + `forge_unified.exe` workers @ `concurrency=6`):** Auto-launched at `2026-11-29T00:47:54Z` (`16:47:54` local PC) immediately after `F_FIX_25R_v2` exited its load phase. As of `2026-11-29T01:00:24Z`, `C:\nnue-lab\neon\forge_fixes\matches\UNIFIED_SEARCH_BUNDLE_250k_SPRT\` holds `8` entries (Match #76 in `matches/`), including active `games_20261128_164754.pgn` (`2,045,717` B, `349` completed `[Result ` games, `Neon's count`), `fastchess_20261128_164754.out` (`47,240` B), and the initial failed-launch `summary.json` (`570` B, `00:47:29Z`).
- **Confirmed Absent / Not Yet Started:** `gpu_runs/R2_live768_anchored_skipnoisy` (`False`), `gpu_runs/F_FIX_25R_v3` (`False`), `matches/*600k*` (`[]`), `matches/TM_*` (`[]`), `matches/R2_*` (`[]`), `matches/F_FIX*` (`[]`).
- **Astra Bridge:** `C:\nnue-lab\from_neon\` does **not** exist locally (`False`); `C:\nnue-lab\neon\to_astra\` holds `18` staged files (including `STATE_TABLE_2811.md` and `TM_OPEN_ENGINE_LITERATURE_REVIEW_2811.md`).
- **Locked Execution Queue (`OPUS_TO_NEON.md:3608-3620` & Declarations):**
  - **Fixed-Node CPU Queue (beside GPU):** (1) `UNIFIED_SEARCH_BUNDLE_250k_SPRT` (**ACTIVE NOW**; `H0` -> split 3+3) -> (2) `OPUS_R1_skip_vs_r0067_1000g_600k` diagnostic -> (3) `F_FIX_25R_v2_vs_R1_skip_SPRT_0_10_250k` -> (4) `R2_anchored_vs_R1_skip_SPRT_0_10_250k` / `F_FIX_25R_v3_vs_R1_skip_SPRT_0_10_250k`.
  - **GPU Queue:** (1) `F_FIX_25R_v2` (**ACTIVE NOW**) -> (2) `R2_live768_skipnoisy_anchored` -> (3) `F_FIX_25R_v3` (and Seed-2 replicates for H1 winners).
  - **100% Idle-PC Clock Window (Strictly Zero GPU / Zero Concurrent CPU):** (1) Unified Bundle `6+0.06` (if `250k` H1) -> (2) `F_FIX_25R_v2` `6+0.06` (if `250k` H1 + Seed-2) -> (3) **`TM Test A`** (`TmFinishIteration=true` vs `false` on `r0067`, zero build) -> (4) **`TM Test B`** (`TM_SOFTCAP_6P006`, gated on `600k` diag + `from_neon/` open-engine check + clean PGO build) -> `R2` / `F_FIX_25R_v3` `6+0.06` confirmations.

---

## 2. Bar 1 — Search Fixes & Time Management

### 2.1 Unified Search Tree Gates & `3x bench 13` Clean Idle NPS
- **Artifacts:** `UNIFIED_SEARCH_TREE.patch` (`25,163` B, `442` lines, SHA-256 `a7b59ec6c1f4c7e87539e2fbb34f0eae44dfbcd1abf08efb70919de0df4ec5ee`), `forge_unified.exe` (`2,432,000` B, SHA-256 `7c2a4a4605039df9c04d0580564dfeb4ad64c37a98923f327405223d2ac9d399`), `UNIFIED_SEARCH_TREE_GATES_AND_NPS.json` (`9,336` B, SHA-256 `e3feefa72b5c31bf42a1f2e8d26efcdd28726d44d52e87ce1e8a11de8be0908c`).
- **Default-OFF Pins (`UNIFIED_SEARCH_TREE_GATES_AND_NPS.json:9-15`, `Neon's count` until Opus/Fable re-run):**
  - `bench_11 = 312866`, `bench_13 = 862329`, `perft_5 = 4865609`, `perft_suite = "12/12 ALL MATCH"`, `v3_parity_200 = "0 differ PASS"`.
- **`same_search` vs Live `v3-r15dsg-sp-clang/forge.exe` (`cef2f215...`) on `r0067` (`737f1978...`, `UNIFIED_SEARCH_TREE_GATES_AND_NPS.json:16-25`, `Neon's count`):**
  - `r0067_bench13_nodes = 576076` (exact match), `10` diverse FENs @ `depth 12`: `0` diffs (`436,798` total nodes), `same_search_book_50_d9`: `50 positions, depth 9: 0 diffs, 675878 nodes`.
- **`ContHist4PlyRead` vs `ContHist6PlyRead` Independence (`UNIFIED_SEARCH_TREE_GATES_AND_NPS.json:26-31`, `r0067` `bench 11`, `Neon's count`):**
  - `off = 218,410`, `4ply_only = 186,939`, `6ply_only = 185,689`, `both = 203,395`.
- **Positive Controls (`UNIFIED_SEARCH_TREE_GATES_AND_NPS.json:32-150`, `Neon's count`):** All `10` UCI options alter search or clock behavior when toggled individually (`LmrDeeperShallower` also independently **`Opus verified`** on live `forge.exe` in `OPUS_TO_NEON.md:3308`: `140,528` -> `120,828` nodes at d15).

**`3x bench 13` Clean Idle NPS on `r0067` (`UNIFIED_SEARCH_TREE_GATES_AND_NPS.json:152-350`, `Neon's count`):**

| Option (Toggled Individually ON) | `b13` Nodes | Node Delta vs Base | Median Wall (ms) | Median NPS | NPS Ratio vs Base | In `250k` Bundle? |
|---|---:|---:|---:|---:|---:|---|
| `baseline` (all 10 OFF) | `576,076` | `0.000%` | `181` | `3,182,740` | `1.0000x` | Reference |
| `LmrDeeperShallower` | `533,003` | `-7.477%` | `164` | `3,250,018` | `1.0211x` (`+2.11%`) | **ON** (built-in) |
| `MinorCorrHist` (`W2_proto_1`) | `568,605` | `-1.297%` | `177` | `3,212,457` | `1.0093x` (`+0.93%`) | **ON** (`e1cd152b...`) |
| `AspScoreScale` (`W13_S4`) | `509,383` | `-11.577%` | `155` | `3,286,341` | `1.0326x` (`+3.26%`) | **ON** (`39201777...`) |
| `BadCapLmr` (`W13_S5`) | `506,867` | `-12.014%` | `152` | `3,334,651` | `1.0477x` (`+4.77%`) | **ON** (`919eb38d...`) |
| `LmrFracCapHist` (`SF6`) | `493,256` | `-14.377%` | `153` | `3,223,895` | `1.0129x` (`+1.29%`) | **ON** (`41f59847...`) |
| `LmrTtPvCutExt` (`SF14`) | `606,012` | `+5.197%` | `178` | `3,404,561` | `1.0697x` (`+6.97%`) | **ON** (`8b2208d0...`) |
| `ContHist4PlyRead` (`SF8` split) | `495,885` | `-13.920%` | `149` | `3,328,087` | `1.0457x` (`+4.57%`) | **OFF both sides** (built-in) |
| `ContHist6PlyRead` (`SF8` split) | `490,519` | `-14.852%` | `151` | `3,248,470` | `1.0207x` (`+2.07%`) | **OFF both sides** (`62dcf1f3...`) |
| `ForcedRootClockStop` (`W12_S2`) | `576,076` | `0.000%` | `175` | `3,291,862` | `1.0343x` (`+3.43%`) | **OFF both sides** (clock-only) |
| `TmAspFailLowGuard` (`W12_S3`) | `576,076` | `0.000%` | `176` | `3,273,159` | `1.0284x` (`+2.84%`) | **OFF both sides** (clock-only) |

### 2.2 Fable Eight Points (`P1..P8`) & Explicit Correction of `STATE_TABLE_2811.md:71`
- **`P1` (Default-OFF UCI Options):** `UNIFIED_SEARCH_TREE.patch:22-29, 99-106, 412-419, 429-441` (`unified_search_tree/src_tree/include/forge/search.hpp:332-339`, `src/search.cpp:183-190`, `src/uci.cpp:779-786, 1045-1057`) adds **8 new default-`false` options** (`MinorCorrHist`, `AspScoreScale`, `BadCapLmr`, `LmrFracCapHist`, `LmrTtPvCutExt`, `ContHist6PlyRead`, `ForcedRootClockStop`, `TmAspFailLowGuard`); `LmrDeeperShallower` and `ContHist4PlyRead` were already built-in default-`false` options in `forge/r15dsg` (`src/search.cpp:161, 163`).
- **CORRECTION OF `STATE_TABLE_2811.md:71`:** `STATE_TABLE_2811.md:71` erroneously lists `SF17` (`SF17_tm_bestmove_avg_eval.patch`, `d7aaf51c...`) and `SF18` (`SF18_tm_ply_curve.patch`, `4b87a338...`) as `"IN TREE (clock-only TM opts, default false)"`. Direct search of `UNIFIED_SEARCH_TREE.patch` (`442` lines) and `unified_search_tree/src_tree/` yields **`0` occurrences** of `SF17`, `SF18`, `BestMoveAvg`, `PlyCurve`, `bestmove_avg`, or `ply_curve`. Only two clock-only TM options exist in `forge_unified.exe`: `ForcedRootClockStop` and `TmAspFailLowGuard`.
- **`P2` (`SF8` Split):** Split into independent `ContHist4PlyRead` & `ContHist6PlyRead` (`Neon's count`). Because standalone `SF8_conthist_6ply.patch` (`62dcf1f3...`) measured `0.9100x` (`-9.00%`) clean NPS (`Neon's count`, `OPUS_TO_NEON.md:3121`), BOTH stay `false` in the `250k` bundle until proven alone.
- **`P3` (`(ss-6)` Bounds):** Guarded by `ss->ply >= 2` (`UNIFIED_SEARCH_TREE.patch:159, 270, 280`; `unified_search_tree/src_tree/src/search.cpp:931, 1691, 1783`) with `stack_[MaxPly + 8]` (`unified_search_tree/src_tree/include/forge/search.hpp:543`; `UNIFIED_SEARCH_TREE.patch:77`; `forge/r15dsg/include/forge/search.hpp:510`) and root `&stack_[4]` (`STATE_TABLE_2811.md:54`; `unified_search_tree/src_tree/src/search.cpp:3021`).
- **`P4` (`SF4a` Guard):** Raw static eval (`tte.eval = ss->raw_eval`) is stored undamped, but TT search scores (`tte.score`) embed damped static evals; removing `rule50_score_for_this_clock` reuses a `clock=60`-damped score at `clock=2`. Guard preserved; `SF4a` (`5a08258a...`) excluded.
- **`P5` (`SF4b1` Planted-Case Test):** `test_sf4b1_p5_planted_cases.py` (`4f186cf6...`, **`4/4` PASS**, `Neon's count`) demonstrates `KBvK=0`, unscaled `KNNvK`, `KRvK=+500`, and wrong-sign `KRvK (-120)` clamped to `0` by `SF4b1`. `SF4b1` (`c5187847...`) excluded.
- **`P6` / `P7` / `P8`:** `LmrFracCapHist` (`SF6`) and `LmrTtPvCutExt` (`SF14`) included behind default-off options; `SF7`, `SF2`, `SF3`, `SF13`, `SF15`, `SF16` strictly excluded.

### 2.3 Active `250k` Bundle SPRT, Opus-Verified Exclusions & Separate Placement
- **Active `UNIFIED_SEARCH_BUNDLE_250k_SPRT` (`UNIFIED_SEARCH_BUNDLE_250K_DECLARATION.json`, `aa74aa81...`, `Opus verified` sound declaration at `OPUS_TO_NEON.md:3526-3530`):**
  - `forge_unified.exe` (`7c2a4a46...`) + `r0067` (`737f1978...`) on both sides, `250k` nodes, `SPRT [0, 10]` normalized (`alpha=beta=0.05`), `max_games = 2,000`, `seed = 202611971`, `concurrency = 6`.
  - **6 ON:** `LmrDeeperShallower`, `MinorCorrHist`, `AspScoreScale`, `BadCapLmr`, `LmrFracCapHist`, `LmrTtPvCutExt`.
  - **4 OFF both sides:** `ContHist4PlyRead`, `ContHist6PlyRead`, `ForcedRootClockStop`, `TmAspFailLowGuard`.
  - **Rule:** `H1` -> clean idle `6+0.06` clock confirmation (must be non-negative); `H0` -> split into declared halves (`H1: LmrDeeperShallower+MinorCorrHist+AspScoreScale` vs `H2: BadCapLmr+LmrFracCapHist+LmrTtPvCutExt`).
- **Opus-Verified Exclusions & Separate Placement:**
  - `SF13` (`SP_SF13_alone_SPRT_0_10_250k`, **`Opus verified`** at `OPUS_TO_NEON.md:3239`): `1,908g`, `404-1060-444`, `ptnml [14, 246, 465, 224, 5]`, **`-7.28 [-15.62, +1.04]`**, `LLR = -2.95` -> **`H0` REJECTED**.
  - `OWNER_BUNDLE` Arm A (`2,000g @ 6+0.06`, **`Opus verified`** at `OPUS_TO_NEON.md:3072`): `449-1059-492`, `ptnml [10, 260, 502, 219, 9]`, **`-7.47 [-15.49, +0.54]`** (DO NOT PLACE).
  - `OWNER_BUNDLE` Arm B (`2,000g @ 6+0.06`, **`Opus verified`** at `OPUS_TO_NEON.md:3082`): `439-1144-417`, `ptnml [5, 227, 516, 245, 7]`, **`+3.82 [-3.94, +11.59]`** (INCONCLUSIVE; DO NOT PLACE as bundle).
  - `SF4b1` (`-4.52 [-17.04, +7.99]` alone in `summary.json`, **`Opus verified`** `-4.52 [-17.02, +7.98]` at `OPUS_TO_NEON.md:2680`; `-15.99 [-29.09, -2.95]` with `SF8`, `Neon's count`, **`Opus agreed`** `-16` rejection at `OPUS_TO_NEON.md:2806`): excluded.
  - `SF8` standalone (`62dcf1f3...`): `0.9100x` (`-9.00%`) clean NPS (`Neon's count`), held out until proven alone.
  - `AspFailHighReduce=1` (`afh`, **`Opus verified`** at `OPUS_TO_NEON.md:660-663`): **`+10.95 [+5.23, +16.67]`** (`4,000g @ 250k`), neutral at self-play `2k` (`-0.54 [-2.33, +1.26]`, `74,000g`); **separate Opus config draft** (`tmp/opus_scratch/afh/CONFIG_EDIT_AFH_DRAFT.md`, awaiting Fable Monday).

### 2.4 Time Management Root Cause, Literature Review & Wave 16 M2 Deliverables
- **Code Mechanism (`Opus verified` at `OPUS_TO_NEON.md:3559, 3579`):** `forge/r15dsg/src/search.cpp:1537-1561` (`should_stop_with`) aborts a running iteration ONLY at `hard_limit_ms_` (`5x soft_basis` = `1,585 ms` at `6+0.06` is `Neon's count`), while soft limit is checked only between iterations (`search.cpp:3211`). Built-in `TmFinishIteration` (`search.cpp:175`, default `false`, used at `2962` and `3188-3219`) is OFF in loop/matches.
- **`40`-UHO Root-Cause Probe (`TM_CLOCK_GAP_ROOT_CAUSE.json`, `cd97a621...`):**
  - `go movetime 210` control (**`Opus verified` clean** at `OPUS_TO_NEON.md:3561`): `r0067` `200.25 ms` vs `R1-skip` `200.20 ms` (**`-0.02%`**), isolating 100% of the time gap inside `time_managed_`.
  - `go_6000` (`Neon's count`): `r0067` `209.92 ms` mean (`178.13` med) vs `R1-skip` `269.99 ms` mean (`207.55` med), **`+28.62%` mean / `+16.52%` med**. `final_iter_jump_mean` `85.2 ms` (`2/40 > 250 ms`) vs `135.1 ms` (`7/40 > 250 ms`) = `+49.9 ms` (`83.1%` of `+60.07 ms` mean gap); `effort_share_factor` `0.7017 -> 0.7444` (`+6.1%`), `final_stab_factor` `0.63 -> 0.68`, `final_fall_factor` `1.0445 -> 1.0648`.
  - `go_2500` (`Neon's count`): `114.06 ms` vs `141.12 ms` (**`+23.72%`**).
- **Open-Engine Literature Review (`to_astra/TM_OPEN_ENGINE_LITERATURE_REVIEW_2811.md`, `2e7814b2...`, Neon's reading of local repos, not yet checked by Opus/Astra per `OPUS_TO_NEON.md:3588`):**
  - Stockfish (`C:\nnue-lab\src\Stockfish`, commit `def601cc156f7d41f9ddea76d74515eddf232aaf`): `timeman.cpp:151-156` (`timeAdvantage`), `search.cpp:624-635` (`increaseDepth` while `elapsed <= 0.50 * totalTime`), `search.cpp:2155` (mid-iter abort ONLY at `tm.maximum()`).
  - Stockfish-tools (`C:\nnue-lab\src\Stockfish-tools`, commit `9a4c7cf4e311f8d9526b79295b80c4d0464c07cf`): `0.43 * totalTime` late-depth guard, mid-iter abort ONLY at `Time.maximum() - 10`.
- **Wave 15 & Wave 16 M2 Deliverables:**
  - Wave 15 pre-literature draft: `TM_SCALE_FIX_DRAFT.patch` (`3,033` B, `171b8cde...`, superseded by Wave 16 `soft_deadline` scaling).
  - **`TM_SOFTCAP_ON_UNIFIED.patch`** (`3,365` B, `ef55eba6...`, LF-only, 7 hunks, `-C0` zero-fuzz on `UNIFIED_SEARCH_TREE`): adds strictly default-off `TmSoftCapPercent = 0` (`[0, 500]`, 0 `uci.cpp` edits via `FORGE_EXPOSE_TUNABLES=1`), `int64_t` overflow-safe scaling of `soft_deadline = soft_basis * factor` at `depth >= 6` clamped `<= hard_limit_ms_`.
  - **`test_tm_softcap_edge_cases.py`** (`58,425` B, `812c6d0a...`): **`18/18` pytest PASS** (`M2` Gate PASS, covering `TmSoftCapPercent=0/200`, `ponder`, `infinite`, `nodes`, `depth`, `movetime`, `emergency_ply`, `mate_moves`, `ForcedRootClockStop`, `TmAspFailLowGuard`, `alt_worker`, `kMaxClockMs` overflow, and 10/10 mutation rejections).
  - **`TM_SOFTCAP_6P006_DECLARATION.json`** (`12,297` B, `0e444fe0...`): **CONDITIONAL / BLOCKED** (`TmSoftCapPercent=200` vs `0` on `r0067` first, `2,000g @ 6+0.06`, `seed=202612011`), gated on: (1) `600k` diag (`4d4e4d30...`, **NOT_YET_RUN**), (2) `from_neon/` push + 1–2 non-Stockfish open engines + Astra check (**NOT_YET_FULFILLED**), (3) queue order strictly after Unified Bundle + `F_FIX` + `600k` diag + **`TM Test A` (`TmFinishIteration`)**, and (4) clean Clang ThinLTO+PGO build & gates before Game 1 (`exe_sha256` placeholder). **Risk Disclosed:** Stockfish `def601cc` avoids mid-iteration cuts below `tm.maximum()` because cutting at `2.0x` can abort a resolving fail-low; therefore `Test B` remains a hypothesis run strictly after `Test A`.

---

## 3. Bar 2 — NNUE Fixes

### 3.1 `R1-skip` vs `R1-keep` (`Live 768w SCReLU`, `r0178..r0202`, `250k SPRT [0, 10]`)

| Match / Pairing | Scope / Horizon | Result (`W-D-L`) & `ptnml` | Elo (`95% CI`) & LLR / LOS | Provenance & Bias Disclosure |
|---|---|---|---|---|
| `OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k` | Seed 1 (`4902fe65...` vs `8b1158aa...`), `base_r15dsg.exe` | `1,526g` (`399-796-331`), `ptnml [9,154,368,224,8]` | **`+15.49 [+6.12, +24.88]`** (`summary.json` `[+6.12, +24.89]`), `LLR = +2.97` (Opus `+3.01 >= +2.94`) -> **`H1`** | **`Opus verified`** (`OPUS_TO_NEON.md:3128-3131`). **SPRT early-stopping upward bias disclosed** (`Opus estimate`: true effect `~+10..+15`). |
| `OPUS_R1_skip_vs_R1_keep_SEED2_SPRT_0_10_250k` | Seed 2 (`4f19f204...` vs `67fcfaea...`), `base_r15dsg.exe` | Raw PGN `2,019g` (`518-1056-445`; `1,009` pairs + `1` unpaired draw); `summary.json`/`Neon's count` `2,018g` (`D 1,055`), `ptnml [11,218,484,279,17]` | **`+12.57 [+4.28, +20.88]`** (`summary.json` `[+4.27, +20.89]`), fastchess `LLR = +2.99` (Opus `+3.01 >= +2.94`) -> **`H1`** | **`Opus verified`** (`OPUS_TO_NEON.md:3325-3327`, `PLAN.md:559-561`). **SPRT early-stopping upward bias disclosed** (`Opus two-seed estimate`: `~+8..+14`). |
| `OPUS_R1_keep_vs_r0202_1000g_250k` | Runner control (`8b1158aa...` vs `42fd3452...`), `250k` fixed | `1,000g` (`233-538-229`), `ptnml [10,110,252,122,6]` | **`+1.39 [-10.33, +13.11]`** (`summary.json` `[-10.34, +13.12]`) | **`Opus verified`** (`OPUS_TO_NEON.md:3268, 3428`). Dead-level trainer control, zero SPRT bias. |

### 3.2 `R1-skip` Seed 1 vs `r0067` (`250k` vs `6+0.06` Gap), `G3_FULL25` & Queued `600k` Diagnostic
- **`OPUS_R1_skip_vs_r0067_1000g_250k` (`Opus verified` at `OPUS_TO_NEON.md:3155`):** `1,000g` fixed (`277-534-189`, `ptnml [4,90,237,152,17]`), **`+30.65 [+18.59, +42.79]`** (`LOS 100.0%`, `summary.json` `[+18.58, +42.80]`, zero SPRT bias).
- **`OPUS_R1_skip_vs_r0067_2000g_6p006` (`Opus verified` at `OPUS_TO_NEON.md:3467-3469`):** `2,000g` fixed (`465-1107-428`, `ptnml [9,220,500,267,4]`), **`+6.43 [-1.47, +14.33]`** (`LOS 94.46%` `Neon's count`, **INCONCLUSIVE** by declared 3-outcome rule; not negative, so `R1-skip` is NOT proposed as best net on this result alone).
- **Clock Gap (`Opus verified` arithmetic at `OPUS_TO_NEON.md:3475`):** **`24.2 +/- 7.4` Elo (`z ~ 3.3`)**.
- **`G3_FULL25` (`FORGENN3-P` `1024p/kb8`, `keep_noisy=True`, `Opus verified` matches at `OPUS_TO_NEON.md:2876, 2888, 3009`):** `50k` vs `r0067`: `+4.86 [-8.47, +18.22]` (`1,000g`); `50k` vs `r0202`: `+22.27 [+8.66, +35.95]` (`1,000g`); **`250k` vs `r0067`**: **`+22.03 [+5.88, +38.28]`** (`600g`); `250k` vs `r0202`: `-0.58 [-16.28, +15.12]` (`600g`); **`6+0.06` vs `r0067`**: **`-0.35 [-8.35, +7.65]`** (`2,000g`, `480-1038-482`, `ptnml [10,239,502,241,8]`, `summary.json` `[-8.35, +7.66]`). Clean idle PGO speed `0.8189x` / `0.834x–0.840x` (`Neon's count`); deferred to Server Day `2.0B`.
- **`R1_SKIP_250K_VS_CLOCK_DIAG.json` (`cfa3e201...`, `Neon's count`):** `config_option_diffs = {}`; `same_search` (`base_r15dsg.exe` vs loop PGO `forge.exe`, `300` UHO pos d9): **`0/300` diffs** on `r0067` (`2,271,371` nodes) and **`0/300` diffs** on `R1-skip` (`2,251,493` nodes) — rules out Hypothesis (c). PGNs used `min=true` (0 per-move comments); SAN plies median `141.0` (`148.62` mean) @ `250k` vs `146.0` (`154.57` mean) @ `6+0.06`. Direct 40-UHO probe on loop PGO: `nodes_250k` `83.2` vs `82.9 ms` (`198k` vs `207k` nodes), `clock_6000_inc60` **`221.5 vs 280.2 ms` (`+26.5%`)**, `clock_2500_inc60` **`114.6 vs 137.9 ms` (`+20.3%`)**.
- **Queued `600k` Diagnostic (`R1_SKIP_VS_R0067_600K_DECLARATION.json`, `4d4e4d30...`):** `OPUS_R1_skip_vs_r0067_1000g_600k` (`1,000g @ 600k`, loop PGO `forge.exe`, `pgn_comments: nodes=true`, `seed=202611981`). Separates Hypothesis (a) TM (Elo stays near `+30`) vs Hypothesis (b) depth (Elo falls toward `+6`). **NOT YET RUN.**

### 3.3 `net_sanity` `S1`/`S2`/`S5` & `OB0/OB1` Cliff (Raw vs Unit-Normalized Reconciled)
- **Unit Reconciliation:** `eval_net_full.py` checks raw NNUE integer outputs directly (`S2 <= 40`, `S5` raw flags), whereas `net_sanity.py` normalizes to centipawns via `cp = 100 * raw / u`, where `u = (Q + R + B + N) / 20` from `S6`.
- **Seed 1 (`OPUS_R1_live768_skipnoisy/r1_summary.json`, `S1`/`S2`/`S5` raw `Opus verified` at `OPUS_TO_NEON.md:3434-3436`):**
  - `S1_startpos = +42` (PASS `[-10, +60]`), `S1_after_1e4 = -10`, **`S2_start_plus_e4 = 32` (PASS `<= 40`)**, **`S5_dead_draws` FLAGGED** (`K-K=16, KN-K=-52, KB-K=-45, KNN-K=+97` raw).
  - `u = (1417+700+593+533)/20 = 162.15` -> normalized `KNN-K = 59.82 cp` (`60 cp` in `R2_DECLARATION.json:75`, `> 50 cp`) and `ob0_ob1_cliff_median_jump_cp = 108.5 cp` (`Neon's count`).
- **Seed 2 (`OPUS_R1_live768_skipnoisy_seed2/eval_full.json`, `Neon's count` per `OPUS_TO_NEON.md:3437`):**
  - `S1_startpos = +56` (PASS), `S1_after_1e4 = -1`, **`S2_start_plus_e4 = 55` (FAIL `> 40` by `15` raw units)**, **`S5_dead_draws` FLAGGED** (`K-K=0, KN-K=-22, KB-K=-14, KNN-K=+114` raw).
  - `u = (1464+736+619+546)/20 = 168.25` -> normalized `KNN-K = 67.76 cp` (`68 cp` in `R2_DECLARATION.json:76`, `> 50 cp`), `S2` normalized `= 32.69 cp`, and `ob0_ob1_cliff_median_jump_cp = 116.5 cp` (`Neon's count`).

### 3.4 Skip-Noisy Loop Package & Queued GPU #2 `R2_live768_skipnoisy_anchored`
- **Skip-Noisy Loop Package (Awaiting Fable Monday Second-Read & Idle CPU Window):**
  - `loop_place/config_forge_skipnoisy_DRAFT.patch` (`c43172eb...`), `loop_place/cache_swap_skipnoisy.py` (`7a19c65e...`), `loop_place/test_cache_swap_skipnoisy.py` (`e082131a...`, **`8/8` pytest `Opus verified`** at `OPUS_TO_NEON.md:3234`), `teamwork_wave13/train_v3p_skipplain_DRAFT.patch` (`d353e6ba...`).
- **Queued GPU #2 `R2_live768_skipnoisy_anchored` (`R2_DECLARATION.json` `1104baf2...`, `run_r2_anchored_skipnoisy.py` `21abc352...`, `Neon's count`):**
  - Live `768w` SCReLU (`kb=8`, `FORGENN3 v3`, `9,463,528` B, `1.0000x` NPS), `r0178..r0202` (`281,241,466` quiet rows), distill `OPUS_R1_live768_skipnoisy/cand.pt` (`w=0.2`), `repeat=20` anchors = `808,420` rows/epoch out of `282,049,886` (`0.2866%`).
  - **Overlap Proof (`R2_ANCHOR_OVERLAP_PROOF.json`, `86a9475c...`, `Neon's count`):**
    - `dead_draws_20k_s5disjoint.fqs.z` (`76532795...`, `20,000` rows): `0` exact / `0` sym vs `heldout_4k`, `s5_s7`, `val.plain`, `uho_epd`.
    - `won_endings_syzygy_20k.fqs.z` (`c2f51696...`, `20,000` rows): `0` exact / `0` sym vs `heldout_4k`, `s5_s7`, `uho_epd`; `20` exact / `60` sym vs `val.plain` (`0.019%`).
    - `opening_ply012_anchors.fqs.z` (`67038576...`, `421` rows): `0` exact / `0` sym vs `heldout_4k`, `s5_s7`, `val.plain`; `5` exact / `6` sym vs `uho_epd` (`0.00019%`).
  - **Pre-Game Diagnostic Protocol (`R2_DECLARATION.json:60-101`):** `net_sanity.py --gate` (`S5 <= 50 cp` norm & `0 S5_dead_draws` flag), `eval_net_full.py` (`ob0_ob1_cliff_n == 100`, target `<= 102.8 cp` vs `r0067` `102.8 cp`), `run_master_gates.py --quick`, `eval_heldout_syzygy.py` -> then `250k SPRT [0, 10]` -> `2,000g @ 6+0.06` vs `R1-skip`. (`0` training/games run yet.)

---

## 4. Bar 3 — Filtering Improvement

### 4.1 Complete Two-Half `r0202` Audit & `SyzygyPath` Verification
- **Dropped Half vs `runs/forge/r0202/data/qc.json` (`899ff415...`) & `FILTER_DROPPED_AUDIT_R0202_2811.json` (`7905b8d8...`):**
  - **Totals (`Opus verified` at `OPUS_TO_NEON.md:3522-3524`):** Raw `16,005,733`; Kept `15,156,682` (`94.70%`); Total Dropped (`marked_skip_32002`) `849,051` (`5.3047%`) = **`duplicate` `526,611`** (`3.2901%`) + **`rule50` (`r50 > 80`) `206,406`** (`1.2896%`) + **`few_pieces` (`min_pieces=4`) `115,569`** (`0.7220%`) + **`score_result_conflict` (`|score|>=600`) `465`** (`0.0029%`) + `score_limit` `0` + `ply` `0` + `already_none` `0`.
  - **Sub-breakdowns (`FILTER_DROPPED_AUDIT_R0202_2811.json:498-567`, `Neon's count`):**
    - `few_pieces` (`115,569`, `mean_ply=177.0`, `mean |score|=702.31`): `KRvK` `55,940`, `KvKR` `36,450`, `KPvK` `13,236`, `KvKP` `9,499`, `KQvK` `244`, `KvKQ` `200`.
    - `rule50` (`206,406`): **`33,537` (`16.25%`) decisive (`res != 0`)**, `51,874` (`25.13%`) `|score| >= 200`.
    - `duplicate` (`526,611`): **`469,107` (`89.08%` / `89.1%`) at `ply 80+`**, `55,044` (`32-79`), `2,111` (`16-31`), `349` (`8-15`); `5,547` (`1.05%`) `result_disagree_vs_first`.
- **Kept Half (`FILTER_DEEP_AUDIT_R0202_2811.json`, `3ae50417...`, `Neon's count`):**
  - Quiet kept (`skip_noisy`): **`12,338,956`**; noisy kept (`bit0=1`): `2,817,726` (`18.591%`); `121,783` games -> **`101.32` quiet rows/game** (`0%` random skip).
  - Within-game correlation (`10,650,131` adj quiet pairs): **`lag1_score_corr_quiet = 0.99697`**, `mean_abs_swing = 22.78 cp`, swings `>= 200`: `81,728` (`0.767%`), `>= 400`: `14,274` (`0.134%`).
  - Ply skew & White bias: **`47.783%` (`5,895,909`) at `ply >= 80`**; mean White eval rises `+100.62 cp` (`ply 8..15`) -> `+181.80 cp` (`ply 80+`).
  - `score == 0` quiet flood: `364,905` (`2.957%`, `232,370` = `63.7%` adj `0->0` runs).
  - Extreme tail: `|score| >= 800` = `1,805,099` (`14.629%`); **`|score| >= 1200` = `844,346` (`6.843%`)**.
  - Missed conflicts: `res == 0 & |score| >= 400` = **`64,679`** (`0.5242%` quiet); `res != 0 & score*res <= -300` = **`6,319`** (`0.0512%` quiet).
  - `OB` skew: **`OB0` = `258,541` (`2.095%`)** vs `OB1` = `2,449,345` (`19.851%`).
- **Cross-Round Duplicates (`cross_round_dedup_r0178_r0202_m64.json`, `898e07e0...`, `Neon's count`):**
  - `1/64` mod-64 sample (`5,918,109` of `378,856,831` kept across `r0178..r0202`): `186,108` sampled dups = **`3.145%`** (`~11.91M` est. total), climbing `0.741%` (`r0179`) -> `4.837%` (`r0202`); **`87.38%` (`87.4%`) concentrated at `ply 81+`**.
- **`SyzygyPath` OFF in Live Search (`Opus verified` at `OPUS_TO_NEON.md:3494-3497`):** `pipeline/config.forge.toml:313-314` (`adjudicate_tablebase = true`) applies only to drawn `<=5`-piece self-play game-end adjudication; `SyzygyPath` is absent from `config.forge.toml` and all 51 match UCI options (`min_pieces = 4` at `line 336`), leaving `F-06` active in live search.

### 4.2 All 4 Opus Point 4 Faults, Live GPU #1 `F_FIX_25R_v2`, Queued `F_FIX_25R_v3` & Monday Patch

| Stream / Artifact | Faults Addressed | Technical Spec, Provenance & Live Status |
|---|---|---|
| **Opus Point 4 Remaining Faults** (`OPUS_TO_NEON.md:3542-3549`) | 1. Within-game corr (`101.32` quiet/game, `corr=0.99697`, `Neon's count`)<br>2. `F-06` (`115,569`/r `Opus verified`; `KRvK/KPvK/KQvK` `Neon's count`; `SyzygyPath` OFF `Opus verified`)<br>3. `rule50` decisive (`206,406`/r `Opus verified`; `33,537` `res!=0` `Neon's count`)<br>4. `ply-80+` dups (`526,611`/r `Opus verified`; `469,107` `80+` & `3.145%` cross-round `87.4%` `81+` `Neon's count`) | All 4 faults lie outside `F_FIX_25R_v2` and are targeted by Wave 16 M1 `F_FIX_25R_v3` (and `F-06` partially by Monday `filterqc_monday_fixes_DRAFT.patch`). |
| **Live GPU #1: `F_FIX_25R_v2`** (`run_f_fix_25r_v2.py` `0008a503...`, `F_FIX_25R_V2_DECLARATION.json` `c7f8dba5...`, `test_f_fix_25r_v2_filter.py` `e709fee3...`) | 3 quiet-row score predicates ONLY: `F-03` (`res==0 & \|score\|>=400`), `F-03b` (`res!=0 & score*res<=-300`), `F-08` (`\|score\|>1200`), pre-run `~7.42%` drop -> `~260.4M` rows (`r0178..r0202`, Seed 1); post-load actual: **`261,866,722`** quiet rows kept, **`19,374,744`** (`6.889%`) dropped (`NEON_TO_OPUS.md:1488`, `Neon's count`) | **DISCREPANCY NOTED:** Disk `run_f_fix_25r_v2.py` is **`0008a5034ec8edda7ed2584468aa73725d67378d8a48c737fd41f4e0a8febaef`** (matching `F_FIX_25R_V2_DECLARATION.json:11` & `STATE_TABLE_2811.md:27`), whereas `NEON_TO_OPUS.md:1388` (`16740986...`) and `:1398` (`46a4d7a1...`) carry stale/typo hashes.<br>**Live Status:** Finished `.plain` load & actively training on GPU (`gpu_runs/F_FIX_25R_v2/` pre-checkpoint empty). Gated on `250k SPRT [0, 10]` -> Seed-2 replicate + `2,000g @ 6+0.06` (`must not be negative`). |
| **Queued Wave 16 M1: `F_FIX_25R_v3`** (`run_f_fix_25r_v3.py` `bdca5794...`, `test_f_fix_25r_v3.py` `8b666d0c...`, `F_FIX_25R_V3_DECLARATION.json` `18a2957b...`) | `F-03`, `F-03b`, `F-08` + **ALL 4 Opus Point 4 faults**: `D-01` Zobrist+SplitMix64 subsample on `pieces >= 6` (100% keep on `pieces <= 5` so `OB0` is boosted), `--recover-f06-from-binpack` (`2 <= pieces < 4`) + `--recover-rule50-decisive` (`r50 > 80 & res != 0`) via isolated `SF_TOOLS` + `hce_dump.exe` (or `--merge-3pc-anchor`), `--dedup-cross-round` (`Uint64DedupStore`, `pieces <= 5` exempt). | **M1 Gate PASS:** **`14/14` pytest PASS**, `--dry-run` **EXIT 0 PASS**, zero writes to `runs/`.<br>**OPERATIONAL NOTE:** `run_f_fix_25r_v3.py` defaults to `FORGE_PARSE_PROCS=3` / `mem_room 12`, but per `NEON_TO_OPUS.md:1461,1486` and `OPUS_TO_NEON.md:3620`, set **`FORGE_PARSE_PROCS=2` + `mem_room 16`** against commit room before live launch! Declared for `250k SPRT [0, 10]` + Seed-2 + `2,000g @ 6+0.06`. |
| **Monday Loop Draft Patch** (`teamwork_wave15/filterqc_monday_fixes_DRAFT.patch` `da9c3c16...`, `test_filterqc_monday_fixes.py` `a0b52a39...`) | Modifies ONLY `pipeline/nnloop/filterqc.py` & `pipeline/config.forge.toml`: `max_abs_score=1200`, `conflict_score=300`, `draw_conflict_score=400`, `min_pieces=2`. | `D-01` & cross-round dedup stay OFF in loop until `F_FIX_25R_v3` wins `250k` + `6+0.06`. `test_filterqc_monday_fixes.py` (`2` `both_ways` tests; reported `2/2` PASS in `NEON_TO_OPUS.md:1429`, `Neon's count`). |

---

## 5. Consolidated Full 64-Char SHA-256 Appendix (All Disk-Verified `2026-11-29T01:00:24Z`)

| Group | Exact Disk Path | Bytes | Exact 64-Char SHA-256 |
|---|---|---:|---|
| Baseline | `C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe` | 2,390,528 | `cef2f21589102392fdd7e3cbde74bfd01baa94f9677a2be33365f68e4bceb03d` |
| Baseline | `C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe` | 2,382,848 | `5e6f333b95b7ceda01a599a713d6bad536633b235dc73b409e1f12c1bb809011` |
| Baseline | `C:\nnue-lab\runs\forge\r0067\train\cand.fnn3` | 9,463,528 | `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28` |
| Baseline | `C:\nnue-lab\runs\forge\r0202\train\cand.fnn3` | 9,463,528 | `42fd34526c3126096b33c34776184246ed0a01bb542febcc6942f584afad5fbd` |
| Baseline | `C:\nnue-lab\runs\forge\teachers\b_full.pt` | 791,911 | `52be981d04cc92cadbabb12d84b82c19b0ac3299557a9179968dc7d872039430` |
| Bar 1 Unified | `C:\nnue-lab\neon\forge_fixes\unified_search_tree\forge_unified.exe` | 2,432,000 | `7c2a4a4605039df9c04d0580564dfeb4ad64c37a98923f327405223d2ac9d399` |
| Bar 1 Unified | `C:\nnue-lab\neon\forge_fixes\unified_search_tree\UNIFIED_SEARCH_TREE.patch` | 25,163 | `a7b59ec6c1f4c7e87539e2fbb34f0eae44dfbcd1abf08efb70919de0df4ec5ee` |
| Bar 1 Unified | `C:\nnue-lab\neon\forge_fixes\unified_search_tree\UNIFIED_SEARCH_TREE_GATES_AND_NPS.json` | 9,336 | `e3feefa72b5c31bf42a1f2e8d26efcdd28726d44d52e87ce1e8a11de8be0908c` |
| Bar 1 Unified | `C:\nnue-lab\neon\forge_fixes\unified_search_tree\test_sf4b1_p5_planted_cases.py` | 6,787 | `4f186cf6e36de88480ef4fb0aaeb0291e93e2da4dcf1ad1920438130a0514835` |
| Bar 1 Decl | `C:\nnue-lab\neon\forge_fixes\UNIFIED_SEARCH_BUNDLE_250K_DECLARATION.json` | 2,605 | `aa74aa81fd8beb66241ea12d3bed755fe352b7883241376bfe4228311532235e` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\patches\FORGE_OWNER_BUNDLE_PGO.patch` | 54,707 | `f441957d44396bd022bbdb0dc723416af23d0921c5230d3aa3926431bccff0d8` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\patches\SF13_qs_evasion_pruning.patch` | 1,584 | `63eb3288af4712a7d641035177e561448e6fc94041d8ee916776ab3fced6b6e4` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\patches\SF8_conthist_6ply.patch` | 3,155 | `62dcf1f3da0ac212a3807e59eb61e144b3705ea2a8a716b70a391e81af4c8779` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\patches\SF6_lmr_fractional_caphist.patch` | 4,100 | `41f598471de6bf600fee0e837bd907ba32e5db5370207ff489f48b1aa4d74337` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\patches\SF14_lmr_ttpv_cutnode_ext.patch` | 1,180 | `8b2208d07d14090dfe5759126c0870a87fb4faa6036ce84c8fce7a61da29830d` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\patches\SF4b1_v3_endgame_scale.patch` | 2,335 | `c518784783300ff3b094eecd67bcc78b339eb3dd158ae8d08a74979e232037c7` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\patches\SF4a_sf_rule50_damping.patch` | 1,410 | `5a08258ad32b9cf007de9535aa108a51b41c38d0c2bce3e4ab0cfb486f26d339` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\patches\SF17_tm_bestmove_avg_eval.patch` | 3,434 | `d7aaf51cde99336b021a87f38bab7b119a702f5cb96cd036d8bedd8ccfb7b88c` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\patches\SF18_tm_ply_curve.patch` | 1,712 | `4b87a33856f12c14336323e102fbb62ea42ef2497873065c1f4b86cfe4f2f041` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamA_search\patches\proto_1_corrhist_minor.patch` | 7,602 | `e1cd152b4d78cd7880f55dd8967eb561fe246fe5773232ce22825df5b2071b14` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\teamwork_wave12\W12_S2_forced_root_clock_stop.patch` | 1,251 | `a99e9b716254d2f3651c84a72febb21980ea56a99b45efb02a80c8aceafa8e9d` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\teamwork_wave12\W12_S3_tm_aspiration_faillow_scale.patch` | 1,931 | `be4079b8f5046f74cd154e9084c9909af48fc8b1b55104a78d69f400ca378ec9` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\teamwork_wave13\W13_S4_aspiration_score_scale.patch` | 1,688 | `39201777c067e7b3996b1b0c4f5e7fb908bf02d7f761fada31a9289eeb0f56ef` |
| Bar 1 Patches | `C:\nnue-lab\neon\forge_fixes\teamwork_wave13\W13_S5_bad_capture_lmr_reduction.patch` | 1,386 | `919eb38d1e35cb5a9a64f099c1b30f1185c9d5e068785e9c283d881fbdfce5f1` |
| Bar 1 TM | `C:\nnue-lab\neon\forge_fixes\teamwork_wave15\TM_CLOCK_GAP_ROOT_CAUSE.json` | 5,320 | `cd97a6218870b9cb1fe178940005bbe1afe84dd442c45ba01982c5d9d780c47e` |
| Bar 1 TM | `C:\nnue-lab\neon\forge_fixes\teamwork_wave15\TM_CLOCK_GAP_ROOT_CAUSE.md` | 6,660 | `8e228d6d50157d0035fc9d3cf8baa9141792c4f3f7f2742b59deb8df0f1c524a` |
| Bar 1 TM | `C:\nnue-lab\neon\forge_fixes\teamwork_wave15\TM_SCALE_FIX_DRAFT.patch` | 3,033 | `171b8cde8c171a925fef50791744c6570d0f60cbd319c98638c4266414f70268` |
| Bar 1 TM (W16 M2) | `C:\nnue-lab\neon\forge_fixes\teamwork_wave16\TM_SOFTCAP_ON_UNIFIED.patch` | 3,365 | `ef55eba677b070324a97b050145ea9d83c181159b33f0d347a6384fd705b3e87` |
| Bar 1 TM (W16 M2) | `C:\nnue-lab\neon\forge_fixes\teamwork_wave16\test_tm_softcap_edge_cases.py` | 58,425 | `812c6d0a3fa514e80f049147e31b1abec2b98fd5a4f09d1e8899358f9f9b9319` |
| Bar 1 TM (W16 M2) | `C:\nnue-lab\neon\forge_fixes\teamwork_wave16\TM_SOFTCAP_6P006_DECLARATION.json` | 12,297 | `0e444fe02d1715a7af49d55c1f5690b71d040cd40c653f02444591f07c203741` |
| Shared / TM Lit | `C:\nnue-lab\neon\to_astra\STATE_TABLE_2811.md` | 25,438 | `d0e858e576344806e2789e7c7d33ff2518ec385ce77f4461e62fe285aaebc1c9` |
| Shared / TM Lit | `C:\nnue-lab\neon\to_astra\TM_OPEN_ENGINE_LITERATURE_REVIEW_2811.md` | 7,782 | `2e7814b21e76e847676252dd8e4b95d1311de7a4ece92542e35f62fbd2756ae7` |
| Bar 2 Diag | `C:\nnue-lab\neon\forge_fixes\R1_SKIP_250K_VS_CLOCK_DIAG.json` | 6,079 | `cfa3e2012907edcffb9c771da9a6c35bae237cd4e263e7e70111fa55c98475e5` |
| Bar 2 Diag | `C:\nnue-lab\neon\forge_fixes\R1_SKIP_VS_R0067_600K_DECLARATION.json` | 1,626 | `4d4e4d30471e337ce16c7cdfecd0c640ff6b2efd9f8fb6bcf45fc4d55ff90df0` |
| Bar 2 Nets | `C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy\cand.fnn3` | 9,463,528 | `4902fe653e575c0c73ab78aed18fb6d2a10c8f33c895160cb5b68b1bdb9b21ec` |
| Bar 2 Nets | `C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_keepnoisy_twin\cand.fnn3` | 9,463,528 | `8b1158aad16d882063da6673efa1584ac0cb4382cb3358964bdb03bb487b02e7` |
| Bar 2 Nets | `C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy_seed2\cand.fnn3` | 9,463,528 | `4f19f204ca3e96750dd1ddd0c06440733c197ec12a9e7dd845c3d5f38c604384` |
| Bar 2 Nets | `C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_keepnoisy_seed2\cand.fnn3` | 9,463,528 | `67fcfaea93bf41b378d5ac4591b0159c5b36d32b39dd90f9a6ecf7f7ad31377e` |
| Bar 2 Seed 2 | `C:\nnue-lab\neon\forge_fixes\R1_SEED2_GATES_SUMMARY.json` | 941 | `b933a568677c7ac26138698c9323c5efa931ed024901b8e63f5638a79c012750` |
| Bar 2 Seed 2 | `C:\nnue-lab\neon\forge_fixes\R1_SEED2_DECLARATION.json` | 2,590 | `0779652cc296f1a03e19de86ca6c698ff031ad3b19657278976ff7b9272f0b68` |
| Bar 2 Loop Pkg | `C:\nnue-lab\neon\forge_fixes\loop_place\config_forge_skipnoisy_DRAFT.patch` | 2,847 | `c43172ebce23d7654fd08f104a7df97a6fb8329b9dec7f0cae162db502fd31d2` |
| Bar 2 Loop Pkg | `C:\nnue-lab\neon\forge_fixes\loop_place\cache_swap_skipnoisy.py` | 14,064 | `7a19c65efd4b72771495dbcb541ed4be4cd054ef4da86c0110ad075ebaa0ce68` |
| Bar 2 Loop Pkg | `C:\nnue-lab\neon\forge_fixes\loop_place\test_cache_swap_skipnoisy.py` | 10,209 | `e082131ae02a4d55ea905ba18ee17910eb65adb535c899300eccc52f10a41b3c` |
| Bar 2 Draft | `C:\nnue-lab\neon\forge_fixes\teamwork_wave13\train_v3p_skipplain_DRAFT.patch` | 1,866 | `d353e6ba2fd8d2d1f5fb2cf12100d3aadcc9cf30874fa84c969ab99fb614ff3d` |
| Bar 2 R2 | `C:\nnue-lab\neon\forge_fixes\teamwork_wave15\R2_DECLARATION.json` | 8,057 | `1104baf2c675e194c24e938be55bd398332d0f459bd015a5e521e3e067202a09` |
| Bar 2 R2 | `C:\nnue-lab\neon\forge_fixes\teamwork_wave15\R2_ANCHOR_OVERLAP_PROOF.json` | 3,439 | `86a9475c9f813bac05f261fee0bf6ef5c58b96b5d442e454deba5dec13461c88` |
| Bar 2 R2 | `C:\nnue-lab\neon\forge_fixes\teamwork_wave15\run_r2_anchored_skipnoisy.py` | 17,535 | `21abc35259afd18fa056af0750de9d66cd03dcdee90180444dff8c72b7e13b31` |
| Bar 2 Anchors | `C:\nnue-lab\neon\forge_fixes\anchors\dead_draws_20k_s5disjoint.fqs.z` | 125,433 | `7653279511862abc7d5bd856f14e61a594932ba625be09107e168d43e9b775a5` |
| Bar 2 Anchors | `C:\nnue-lab\neon\forge_fixes\anchors\won_endings_syzygy_20k.fqs.z` | 154,309 | `c2f51696b886c6cad78da2cca253352d79e6a188778c5ab35526b6321a4a96de` |
| Bar 2 Anchors | `C:\nnue-lab\neon\forge_fixes\anchors\opening_ply012_anchors.fqs.z` | 2,200 | `6703857609240a6cbdf07d85e95d1747d939ccb307b685eb0c6c76675e4540d0` |
| Bar 2 Holdout | `C:\nnue-lab\neon\forge_fixes\anchors\heldout_syzygy_4k.json` | 324,677 | `b363d7843ea696008ced1d37699b255469202d9577a0c43f8849bd81979f1429` |
| Bar 3 Audits | `C:\nnue-lab\neon\to_astra\FILTER_DEEP_AUDIT_R0202_2811.json` | 5,116 | `3ae50417c85a6d2b77015a6cf7a716cc790ab47faa37688009cf7cb17b1e2f15` |
| Bar 3 Audits | `C:\nnue-lab\neon\to_astra\FILTER_DROPPED_AUDIT_R0202_2811.json` | 14,100 | `7905b8d837884a73e246bdb1be79899293453a75935df68dcd912229a50a7a9b` |
| Bar 3 Audits | `C:\nnue-lab\neon\filter_quest\results\cross_round_dedup_r0178_r0202_m64.json` | 7,772 | `898e07e0bd81a5194e52c46dd9886917d1ee22390a390e938bcc41d680f95b62` |
| Bar 3 Audits | `C:\nnue-lab\runs\forge\r0202\data\qc.json` | 1,725 | `899ff415baad26b3e4c7e8c3f3305b05f605162e2a909a2953abb96a712c0b00` |
| Bar 3 `F_FIX` v2 | `C:\nnue-lab\neon\forge_fixes\run_f_fix_25r_v2.py` | 12,661 | `0008a5034ec8edda7ed2584468aa73725d67378d8a48c737fd41f4e0a8febaef` |
| Bar 3 `F_FIX` v2 | `C:\nnue-lab\neon\forge_fixes\F_FIX_25R_V2_DECLARATION.json` | 3,244 | `c7f8dba553a8e697417cae449d62b367ce4a1cfb5fb40952388b0b0092aca265` |
| Bar 3 `F_FIX` v2 | `C:\nnue-lab\neon\forge_fixes\test_f_fix_25r_v2_filter.py` | 2,173 | `e709fee31ad9c723da291b2166e317f7fcd6b321150b71e7880b162de390c1db` |
| Bar 3 `F_FIX` v3 (W16 M1) | `C:\nnue-lab\neon\forge_fixes\teamwork_wave16\run_f_fix_25r_v3.py` | 45,215 | `bdca5794257d76eb4c2544d26a0794b01e340deef1a43d84fb87940b131fec31` |
| Bar 3 `F_FIX` v3 (W16 M1) | `C:\nnue-lab\neon\forge_fixes\teamwork_wave16\test_f_fix_25r_v3.py` | 29,945 | `8b666d0cb0b9ea3d0814bbcf62b700c55f9d60c099e902b5c711601f187c089b` |
| Bar 3 `F_FIX` v3 (W16 M1) | `C:\nnue-lab\neon\forge_fixes\teamwork_wave16\F_FIX_25R_V3_DECLARATION.json` | 8,563 | `18a2957be2576fd96382d5ac8de28b0aa33d9911ba67f0f520f33b63851d060d` |
| Bar 3 Monday | `C:\nnue-lab\neon\forge_fixes\teamwork_wave15\filterqc_monday_fixes_DRAFT.patch` | 2,318 | `da9c3c1620d2999c248f190827a484e1e78f6f9eb529e443266595bdae9da069` |
| Bar 3 Monday | `C:\nnue-lab\neon\forge_fixes\teamwork_wave15\test_filterqc_monday_fixes.py` | 11,188 | `a0b52a39e758fb2f6c5e729006abc46caf629e3dfdabe476579ff2ff15a2032d` |
| Match Infra | `C:\nnue-lab\tools\book\UHO_Lichess_4852_v1.epd` | 174,889,110 | `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` |
| Match Infra | `C:\nnue-lab\tools\fastchess\fastchess-windows-x86-64\fastchess.exe` | 4,239,360 | `a7aa6762058e1f699809e9f3d1a35b609e90dbb2c3dde32d99099d641780eb9b` |
