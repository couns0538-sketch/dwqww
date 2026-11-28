# Server-Day 2.0B Final Execution Specification (`FORGENN3-P` + `FQS1` Streaming Pipeline)

**Document ID:** `WAVE7-STREAMB-SERVERDAY-2B-FINAL-SPEC`
**Status:** Production-ready execution blueprint (CPU/GPU-verified pipeline; zero servers rented yet)
**Supersedes:** `SERVER_DAY_2B_RUNBOOK.md` (Wave 3) and `SERVER_DAY_V2_RUNBOOK.md` (Wave 5) by incorporating every Wave 6–7 verified finding (`--skip-fqs-noisy` `+699.72 / +651.27` Elo proof, `134x` hanging-Queen forensic, `9/9` Stage-2 quiet arms, clean idle 5-arch PGO NPS table with `1024p/kb16` at `-0.6%` NPS, `G3_FULL25_PGO` equal-time `-0.35` Elo deferral, and `concurrency <= 7` clock-match rule).

> **Evidence & Integrity Standard:** Training loss, validation MSE, and offline scorecards are diagnostic leads — **never** Elo claims. Final adoption of any Server-Day net is decided solely by a pre-declared, GPU-idle, PGO equal-time `fastchess` match (`2,000g @ 6+0.06` / `10+0.1`, `concurrency <= 7` on 8-core hosts), never pooling screens with confirmations.

---

## 1. Executive Summary & Architectural Decisions

1. **Mandatory Tier-1/Tier-2 Noise Filtering (`--skip-fqs-noisy` + `--skip-check`):**
   - Both `bit0=0` (`--skip-fqs-noisy`, excluding captures/promotions) and `bit1=0` (default check exclusion in `partition_fqs_buckets.py` and `train_v3p_stream.py`) are **strictly mandatory**.
   - **Verified Elo Proof:**
     - `G3b_skipnoisy vs G3a_keepnoisy` (`1,000g @ 50k`, equal-raw): **`+699.72 Elo`** (`972-21-7`, `98.25%`, `ptnml=[0, 0, 7, 21, 472]`, `95% CI [+642.27, +784.63]`, `z=141.297`, `LOS=100.0%`).
     - `G3b_skipnoisy vs G3a_eqret` (`1,000g @ 50k`, equal-retained rows): **`+651.27 Elo`** (`967-20-13`, `97.70%`, `ptnml=[0, 0, 13, 20, 467]`, `95% CI [+597.55, +727.83]`, `z=115.771`, `LOS=100.0%`).
   - **Forensic Root Cause (`CC0_NOISY_VS_QUIET_FORENSIC.json`, `1,839,070` rows):**
     - `17.12%` of non-check CC0 rows are `bit0=1` noisy captures/promotions.
     - Noisy rows carry `mean_stm_mat = -1.161` pawns against `mean_sc = +35.9 cp` (vs quiet `mean_stm_mat = -0.005`, `mean_sc = +1.5 cp`), dropping `corr(mat, score)` from `0.8563` (quiet) to `0.6163` (noisy).
     - Equal-eval (`|sc| < 100 cp`) hanging-piece rate (`|mat| >= 3` pawns) is `22.26%` vs `1.76%` (`12.65x`), and hanging-Queen rate (`|mat| >= 8` pawns) is `2.68%` vs `0.02%` (**`134.0x`**).
   - **Distillation Does NOT Fix `keep_noisy` (`G3AB_DISTILL_REGIME_CHECK.json`):**
     - Even with `r0067` teacher distillation (`w=0.2`), `G3a_distill_keep_noisy` collapses middlegame OLS Queen value to **`201.8 cp`** (`m4_wdl_mse=0.02775`, `m4_corr=0.5298`, `2` sanity flags: `S1_startpos`, `S5_dead_draws`), whereas `G3b_distill_skip_noisy` reaches **`1002.7 cp`** (`m4_wdl_mse=0.02252`, `m4_corr=0.639`, `0` sanity flags).
     - Across all `9/9` Stage-2 quiet-filtered GPU arms (`STAGE2_QUIET_GPU_SUMMARY.json`, `f1_quiet_kept=1,442,765`), `--skip-fqs-noisy` restored `ols_Q = 988.5–1033.8 cp` and `syz_win_ok_pct = 99.25–99.3%`.
   - **Proven vs. Open Scope Note:** `FORGENN3-P` scratch/distilled collapse under `keep_noisy=true` is 100% proven; whether removing `--keep-noisy` also improves live `768w` SCReLU (`pipeline/forge_train_v3.py` on `r0178..r0202`) is currently being tested separately via `run_opus_r1_live768_skipnoisy.py` (plus Opus's requested `--keep-noisy` twin in the same standalone runner).

2. **Why V3P Waits for Server Day (`2.0B` Quiet Positions) Instead of Live-Loop Placement Today:**
   - `G3_FULL25_PGO_vs_live_r0067_2000g_6p006` (`2,000g @ 6+0.06`, `0` TL, `0` IL, `0` DC) landed at **`-0.35 [-8.35, +7.66] Elo`** (`480-1038-482`, `ptnml=[10, 239, 502, 241, 8]`), while clean idle PGO NPS (`CLEAN_IDLE_SPEED_2BUILDS.json`, `v3p_bit_exact_nodes=869,964`) showed `1024w/kb8` runs at `3.021M–3.042M` NPS (`0.8337x–0.8395x` vs `live_pgo_r0067` `3.623M` NPS).
   - Therefore, V3P is NOT placed into the live loop on `353M` `keep_noisy` rows; it deploys on **Server Day `2.0B` quiet-filtered positions** where both scale and clean `--skip-fqs-noisy` data apply.

3. **Primary & Optional Server-Day Architectures (`CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json`):**
   - **Primary Candidate:** **`--hidden 1024 --king-buckets 16` (`1024p/kb16`, `25,577,704` B = `24.39 MiB`)**. Clean idle PGO speed is **`2,940,975` (`2.941M`) NPS** (`0.8139x` vs `live_pgo_r0067_768screlu` `3,613,642` NPS) — paying only **`-0.6%` (`-0.61%`)** NPS vs `1024p/kb8` (`2,959,061` NPS, `0.8189x`), while doubling king-bucket resolution (`SF19` `opp_side_castling` motivation) with `0 cp` C++ parity verified on `v3p_fused_v3_engine.exe`.
   - **Optional Secondary Arm (`+€9` H100):** **`--hidden 1536 --king-buckets 8` (`1536p/kb8`, `19,098,856` B = `18.21 MiB`)**. Clean idle PGO speed is **`2,664,542` (`2.665M`) NPS** (`0.7374x` = **`-26.3%`** vs `live_pgo_r0067_768screlu`, `-9.95%` vs `1024p/kb8`). Train on the exact same deduped `2.0B` shards as a standalone `3.84h` H100 arm (`€9.21` GPU cost; `+€2.85` if substituted for `1024w` in Scenario B, or `+€9.21` as an extra arm alongside Scenario A) and decide strictly by Rule R5 equal-time `fastchess`.

---

## 2. End-to-End 2.0B Pipeline Specification & Exact CLI Flags

### Stage 1 — Parity-Balanced CC0 Self-Play Datagen (`gen_cc0_selfgame_fqs.py`)
- **Path:** `neon/forge_fixes/gen_cc0_selfgame_fqs.py` (cross-platform via `FORGE_LAB_ROOT`, Linux wrapper `neon/forge_fixes/teamwork_wave5/streamB_serverday_v2/run_datagen_epyc_v2.sh`).
- **Parity & Diversity Mechanics (Verified in Source):**
  - Alternates `target_turn = WHITE if (games % 2 == 0) else BLACK` per game (`50/50` exact post-random STM parity regardless of `book_cc0_clean.epd` `58.38%` White skew).
  - Standard CC0 (`--random-plies 2`): picks `rp = 2 if (b0.turn == target_turn) else 1`.
  - Wide diversity (`--wide-div-frac 0.15`): picks `rp = 4 if (b0.turn == target_turn) else 5` to boost material/opposite-castle entropy.
  - Startpos calibration (`--startpos-frac 0.10`): uses `rp = games % 3` (`0/1/2` random plies, avoiding `k=0` deterministic replay which caused `60.30%` of duplicates in `cc0_shards_4k_v2`; live-loop `datagen_uci_startpos_only.patch` uses `startpos k=3/4` / `sp_k=4`) with `writeminply = 0`.
  - Syzygy 3-4-5 adjudication (`--tablebase-dir`): for drawn `<= 5`-piece endings without castling rights, `wdl in {2, -2}` relabels `end_res_w` to true forced TB win.
  - Integrity drops: `ply_limit_skip` (6 tail plies `>= 300 cp`), decisive conflicts (`res_stm != 0 and sc * res_stm <= -600`), and draw conflicts (`--drop-draw-conflicts` default `True`: `res_stm == 0 and |sc| >= 600`).
  - Packs 38-byte `FQS1` records (`bit0=noisy`, `bit1=in_check`, `bit2=swing>=200`, `bit3=draw_conf>=600`, `bits4..6=ob0..7`, `weight_u8=128`) and writes atomic `.part -> os.replace` shards (`cc0_w{wid:02d}_s{shard_idx:03d}.fqs.z`).
- **Exact Production Command (Scenario A/B `2.5B` raw -> `~2.0B` pre-noisy / `~1.65B–1.75B` quiet usable; scale `--positions` to `3000000000` if targeting `2.0B` post-`skip-noisy` usable):**
  ```bash
  export HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES=""
  export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
  export FORGE_LAB_ROOT=/workspace/nnue-lab
  export PYTHONPATH="${FORGE_LAB_ROOT}/pipeline${PYTHONPATH:+:${PYTHONPATH}}"

  python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/gen_cc0_selfgame_fqs.py" \
    --out-dir "${FORGE_LAB_ROOT}/data/raw_2b" \
    --book "${FORGE_LAB_ROOT}/neon/forge_fixes/book_cc0_clean.epd" \
    --config "${FORGE_LAB_ROOT}/pipeline/config.forge.toml" \
    --tablebase-dir "${FORGE_LAB_ROOT}/tablebases/syzygy345" \
    --exe "${FORGE_LAB_ROOT}/builds/v3p_engine" \
    --net "${FORGE_LAB_ROOT}/runs/forge/r0067/train/cand.fnn3" \
    --positions 2500000000 \
    --shard-size 500000 \
    --soft-nodes 4000 \
    --write-min-ply 2 \
    --random-plies 2 \
    --startpos-frac 0.10 \
    --wide-div-frac 0.15 \
    --drop-draw-conflicts \
    --max-temp-c 0 \
    --workers 128 \
    --seed 20261130 \
    --resume
  ```
  - **Note on `run_datagen_epyc_v2.sh`:** The wrapper maps `--syzygy-dir` -> `--tablebase-dir` and runs an inline post-datagen parity gate asserting `0` `.part` files, valid `FQS1` headers, and `47.0% <= white_stm_pct <= 53.0%` (since `gen_cc0_selfgame_fqs.py` `summary.json` omits `white_stm`).
  - **Note on Raw Volume for `2.0B` Quiet Usable:** Measured CC0 `bit0=1` noisy fraction is `17.12%` (`CC0_NOISY_VS_QUIET_FORENSIC.json`), in-check `bit1=1` is `7.72%` (`0%` in `gen_cc0_selfgame_fqs.py` because line 299 already filters `not in_chk`), draw conflicts `0.32%`, and dedup merge `~8–12%`. Under `--skip-noisy`, raw `2.5B` yields `~1.8B` quiet deduped rows (`~72%`); to guarantee `>= 2.0B` quiet deduped rows, increase `--positions` to `2800000000`–`3000000000` (`+12–20%` CPU time).

### Stage 2 — Optional Selective `16k` Forge-Only Rescoring (`rescore_fqs_selective.py`)
- **Path:** `neon/forge_fixes/rescore_fqs_selective.py` (NOT `filter_quest/`).
- **Critical Linux Operational Requirement:** `rescore_fqs_selective.py` hardcodes `LAB = Path(r"C:\nnue-lab")` and unconditionally runs `from nnloop.heat import cpu_temp`. On Linux you **MUST** set `PYTHONPATH="${FORGE_LAB_ROOT}/pipeline"` AND pass `--exe`, `--net`, and `--config` explicitly:
  ```bash
  export HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES=""
  export PYTHONPATH="${FORGE_LAB_ROOT}/pipeline${PYTHONPATH:+:${PYTHONPATH}}"

  python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/rescore_fqs_selective.py" \
    --in-dir "${FORGE_LAB_ROOT}/data/raw_2b" \
    --out-dir "${FORGE_LAB_ROOT}/data/raw_2b_rescored" \
    --soft-nodes 16000 \
    --max-frac 0.005 \
    --workers 128 \
    --prioritize-opp-castle \
    --exe "${FORGE_LAB_ROOT}/builds/v3p_engine" \
    --net "${FORGE_LAB_ROOT}/runs/forge/r0067/train/cand.fnn3" \
    --config "${FORGE_LAB_ROOT}/pipeline/config.forge.toml"
  ```
- **Note:** Gate final Server-Day adoption of `--prioritize-opp-castle` (`0.5%` vs `2.0%` vs `0%`) on the pending `S2Q_EXP_R1` / `S2Q_EXP_R1b` `250k` results if completed prior to launch.

### Stage 3 — Bucketed Parallel Vectorized Dedup (`partition_fqs_buckets.py`)
- **Path:** `neon/filter_quest/partition_fqs_buckets.py`.
- **Verified Performance (`partition_fqs_buckets_bench.json`):** `2,000,004 -> 1,612,164` kept (`154,497` in-check, `6,437` draw conflict, `226,906` dedup merged) in `2.61s` (`4` workers, `32` buckets) = **`766,285.1 rec/s`**, `0/9` stat diffs vs `filter_fqs_to_fqs.py`, and **`< 0.72 GiB RAM/worker`** at `2.0B` rows / `128` buckets (`~23.0 GiB` total RAM on `32` workers, eliminating the `400–600 GiB` single-dict OOM).
- **Exact `--dedup-mode avg` Encoding:**
  - Groups by 33-byte key (`packed[0..31] + stm`) via SplitMix64 64-bit hash into `B=128` buckets, then runs `S33` stable `mergesort` + `np.add.reduceat`.
  - `score16 = clip(rint(score_sum / cnt), -30000, 30000)`
  - `res8 = sign(res_sum)` (`-1, 0, +1`)
  - `weight_u8 = clip(rint(128.0 * sqrt(cnt)), 128, 192)` (used by `train_v3p_stream.py --use-shard-weights` as `weight_u8 / 128.0`, bounded `[1.0, 1.5]`).
- **Exact Production Command (NOTE: `--skip-noisy` MUST be passed explicitly; `run_dedup_buckets.sh` omits it unless forwarded!):**
  ```bash
  export HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES=""
  export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1

  python3 -B "${FORGE_LAB_ROOT}/neon/filter_quest/partition_fqs_buckets.py" \
    --in-dir "${FORGE_LAB_ROOT}/data/raw_2b_rescored" \
    --out-dir "${FORGE_LAB_ROOT}/data/clean_2b_quiet_avg" \
    --buckets 128 \
    --workers 32 \
    --skip-noisy \
    --drop-draw-conflict 600 \
    --dedup-mode avg \
    --shard-rows 500000 \
    --flush-rows 65536 \
    --comp-level 3
  ```
  - Do **NOT** pass `--keep-in-check` (`skip_in_check = not args.keep_in_check` -> `bit1=0` enforced).
  - Verify `summary.json` shows `t1_corrupt == 0`, `_buckets_tmp/` removed, and `0` `.part` files.

### Stage 4 — Frozen 3-Shard Anchors (`S1 / S2 / S5 / S7` + `OB0` Starvation Fix)
Every superbatch injects the following 3 frozen shards under `neon/forge_fixes/anchors/` (exact sizes and SHA-256s verified on disk and in `heldout_integrity_verification.json` / `opening_ply012_anchors_meta.json`):

| Anchor File | Rows (Unique) | Bytes | Exact SHA-256 | Purpose & Overlap Guarantee |
|---|---:|---:|---|---|
| `dead_draws_20k_s5disjoint.fqs.z` | `20,000` (`20,000`) | `125,433` | `7653279511862abc7d5bd856f14e61a594932ba625be09107e168d43e9b775a5` | Fixes `S5` dead draws (`K-K`, `KN-K`, `KB-K`, `KNN-K`) & `OB0` starvation; **`0` heldout & `0` S5/S7 exact/symmetry hits** (replaces `dead_draws_20k.fqs.z` / `dead_draws_20k_clean.fqs.z`). |
| `won_endings_syzygy_20k.fqs.z` | `20,000` (`19,966`) | `154,309` | `c2f51696b886c6cad78da2cca253352d79e6a188778c5ab35526b6321a4a96de` | Fixes `S7` won endings (`KQ-K`, `KR-K`, `wdl in {2,-2}` across 14 TB categories) & `OB0` scaling; **`0` heldout & `0` S5/S7 exact/symmetry hits**. |
| `opening_ply012_anchors.fqs.z` | `421` (`421`) | `2,200` | `6703857609240a6cbdf07d85e95d1747d939ccb307b685eb0c6c76675e4540d0` | Forge-only (`v3-r15dsg-sp-clang + r0067 @ 16k`): startpos + 20 ply-1 + 400 ply-2; fixes `S1`/`S2` ply 0–2 starvation without `k=0` deterministic replay. |

- **Held-Out Integrity (`heldout_syzygy_4k.json`):** `4,000` unique rows (`2,000` draws + `2,000` wins), `324,677` bytes, `sha256=b363d7843ea696008ced1d37699b255469202d9577a0c43f8849bd81979f1429`, `0` Syzygy WDL mismatches, `0` S5/S7 symmetry hits.
- **Anchor Weight-Exemption Rule (`train_v3p_stream.py:310, 327-329`):** Anchor rows (`idx >= n_main`) are **exempt** from `--use-shard-weights` and `--ob-reweight` (`w_g[n_main:] = 1.0`) and are pinned to exact WDL targets `0.5 * (res_g + 1.0)` (never diluted by score blend or distillation).

### Stage 5 — Double-Buffered Streaming GPU Training (`train_v3p_stream.py`)
- **Path:** `neon/forge_fixes/train_v3p_stream.py`.
- **Mandatory Operational Caveats (Directly Verified in `train_v3p_stream.py`):**
  1. **`--skip-fqs-noisy` MUST be passed** (double-defense even on already-filtered shards; `keep_fqs_in_check` stays `False` by default so `bit1=0` is also enforced).
  2. **`--save-ckpt-every` does NOT exist** in `train_v3p_stream.py` (passing it exits with code `2`: `unrecognized arguments: --save-ckpt-every`). Instead, `train_v3p_stream.py` writes `resume_ckpt.pt` atomically (`tmp_resume_ckpt.pt -> os.replace`) after every superbatch, and `--save-cycles` saves `cand_e{ep}.pt` at cosine cycle boundaries.
  3. **Wrapper Caution:** `run_train_stream_gpu_v2.sh` (Wave 5) defaults `KING_BUCKETS=8` and does NOT pass `--skip-fqs-noisy` by default; always pass `--king-buckets 16 --skip-fqs-noisy` (or invoke `train_v3p_stream.py` directly as below).
  4. **Distillation Note:** Only pass `--distill-net` if pointing to a clean non-collapsed checkpoint (e.g., `G3b` or `cand.pt` trained with `--skip-fqs-noisy`); otherwise omit `--distill-net` for pure scratch (`--mix 0.85`), since `G3b_cc0_skip_noisy` scratch achieved `OLS Q = 1016.0 cp` vs `1002.7 cp` distilled.
  5. **SWA Caution (`M_SWA` `-29.95 Elo`):** Never blindly average across `5e-4` cosine LR restarts (`cand_e12 + cand_e20` lost `-29.95 [-43.27, -16.72] Elo`). Evaluate `cand.fnn3` directly; use `--save-cycles` checkpoints only for rollback or explicitly gated late-tail evaluation.
- **Exact Primary Production Command (`1024w`, `kb=16`):**
  ```bash
  unset HIP_VISIBLE_DEVICES CUDA_VISIBLE_DEVICES ROCR_VISIBLE_DEVICES
  export TORCHDYNAMO_DISABLE=1
  export PYTHONDONTWRITEBYTECODE=1
  export FORGE_LAB_ROOT=/workspace/nnue-lab

  python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/train_v3p_stream.py" \
    --fqs-shards "${FORGE_LAB_ROOT}/data/clean_2b_quiet_avg" \
    --anchor-shards \
      "${FORGE_LAB_ROOT}/neon/forge_fixes/anchors/dead_draws_20k_s5disjoint.fqs.z" \
      "${FORGE_LAB_ROOT}/neon/forge_fixes/anchors/won_endings_syzygy_20k.fqs.z" \
      "${FORGE_LAB_ROOT}/neon/forge_fixes/anchors/opening_ply012_anchors.fqs.z" \
    --anchor-repeat-per-sb 25 \
    --shards-per-superbatch 400 \
    --skip-fqs-noisy \
    --use-shard-weights \
    --hidden 1024 \
    --king-buckets 16 \
    --epochs 20 \
    --batch-size 8192 \
    --lr 0.0005 \
    --min-lr-frac 0.05 \
    --warmup-steps 500 \
    --lr-cycles auto \
    --w1-decay 0.3 \
    --ob-smooth 2e-6 \
    --mix 0.85 \
    --loss-pow 2.0 \
    --save-cycles \
    --seed 1 \
    --gpu-hot-pause-c 98.0 \
    --gpu-hot-resume-c 84.0 \
    --mem-need-gb 0 \
    --resume \
    --out-dir "${FORGE_LAB_ROOT}/runs/serverday_2b_1024p_kb16"
  ```
- **Optional `+€9` H100 Arm (`1536w`, `kb=8` or `kb=16`):** Re-run on the identical `clean_2b_quiet_avg` shards with `--hidden 1536 --king-buckets 8 --out-dir "${FORGE_LAB_ROOT}/runs/serverday_2b_1536p_kb8"` (`~3.84h` H100, `€9.21` GPU cost).

---

## 3. Exact Cost & Time Budget (`SERVER_DAY_COST_MODEL.json`)

> **Measured vs. Planning-Estimate Disclosure:**
> - **Directly Measured on Owner's PC:** `.fqs.z` compressed footprint (`19.7 GB` @ `2.0B` usable = `13.5x` smaller than `~280 GB` `.plain`), bucketed dedup throughput (`766.3k–769.2k rec/s`, `< 0.72 GiB/worker` -> `23.0 GiB` total on `32` workers), and local RX 7900 XT throughput (`1.91M pos/s`).
> - **Planning Estimates (Zero Servers Rented):** Cloud hourly EUR rates and H100 (`4.2M pos/s`) / RTX 4090 (`2.8M pos/s`) / `1536w` (`~1.45x` slower) speeds are planning estimates — confirm real `pos/s` in an Hour-1 pilot before scaling.

| Scenario | Usable (`Raw`) | SoftNodes / `16k` Rescore | CPU Cores / `pos/s` | Datagen + Rescore (h) | Dedup (h) / RAM | Raw / Usable `.fqs.z` | Peak NVMe / `1 Gbps` Xfer | GPU (`20 ep`) / Train (h) | CPU EUR | GPU EUR | Total EUR | `EUR / 1B` |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| **A** (`1024w`, EPYC+H100) | `2.0B` (`2.5B`) | `4k` / `0.5%` | `256c` / `48,640` | `14.56h` | `0.11h` / `23.0 GiB` | `24.7` / `19.7 GB` | `130.6 GB` / `2.6 min` | `1x H100 80GB` (`4.2M est`) / `2.65h` | `€66.05` | `€6.35` | **`€72.40`** | `€36.20` |
| **B** (`1536w`, EPYC+H100) | `2.0B` (`2.5B`) | `4k` / `0.5%` | `256c` / `48,640` | `14.56h` | `0.11h` / `23.0 GiB` | `24.7` / `19.7 GB` | `130.6 GB` / `2.6 min` | `1x H100 80GB` (`~1.45x`) / `3.84h` | `€66.05` | `€9.21` | **`€75.25`** | `€37.63` |
| **C** (`1024w`, Local 7900XT) | `1.5B` (`1.875B`) | `2k` / `1.0%` | `256c` / `89,984` | `6.25h` | `0.09h` / `23.0 GiB` | `18.5` / `14.8 GB` | `97.9 GB` / `2.0 min` | `Local RX 7900 XT` (`1.91M meas`) / `4.36h` | `€28.52` | `€0.00` | **`€28.52`** | `€19.01` |
| **D** (`1024w`, 128c+4090) | `1.5B` (`1.875B`) | `4k` / `0.5%` | `128c` / `24,320` | `21.84h` | `0.09h` / `23.0 GiB` | `18.5` / `14.8 GB` | `97.9 GB` / `2.0 min` | `1x RTX 4090` (`2.8M est`) / `2.98h` | `€49.34` | `€1.64` | **`€50.98`** | `€33.99` |

*NVMe Floor:* Provision `>= 160 GB` free NVMe on the dedup/training node (`130.6 GB` peak NVMe during `2.0B` bucketed dedup).

---

## 4. Crash-Recovery & Thermal-Guard Runbook

1. **Datagen Crash / Spot Preemption (`gen_cc0_selfgame_fqs.py --resume`):**
   - Workers write `cc0_w{wid:02d}_s{shard_idx:03d}.fqs.z.part` and atomically rename via `os.replace`.
   - Recovery: delete incomplete `.part` files only (`find "${OUT_DIR}" -maxdepth 1 -name '*.part' -delete`), preserve all complete `.fqs.z` shards, and relaunch with `--resume` (`--resume` scans existing `cc0_wXX_sYYY.fqs.z` shards, advances `shard_idx`, `total_written`, and RNG seed offset cleanly).
2. **Bucketed Dedup Failure (`partition_fqs_buckets.py` Pass-1 / Pass-2):**
   - Pass 1 writes `_buckets_tmp/bXXX/pYYYYY.fqs.z` atomically; Pass 2 writes `fqs_bXXX_sYYYY.fqs.z` atomically.
   - Recovery: delete scratch and partial files (`rm -rf "${OUT_DIR}/_buckets_tmp" "${OUT_DIR}"/*.part`) and re-run `partition_fqs_buckets.py` (100% deterministic output for fixed inputs).
3. **GPU Training Preemption (`train_v3p_stream.py --resume` + `resume_ckpt.pt`):**
   - Every superbatch finishes by writing `tmp_resume_ckpt.pt` and atomically replacing `resume_ckpt.pt` with `(epoch, sb_idx, step, tl, model, opt)`.
   - Recovery: delete any orphaned `tmp_resume_ckpt.pt` (`rm -f "${OUT_DIR}/tmp_resume_ckpt.pt"`), preserve `resume_ckpt.pt`, and relaunch with `--resume` using the **exact same** `--fqs-shards`, `--shards-per-superbatch`, `--seed`, `--hidden`, and `--king-buckets` so `group_shards_into_superbatches()` reproduces identical epoch groupings. Confirm stdout prints `RESUMED STREAM at ep=... sb=... step=...`.
4. **Thermal Guard (`--gpu-hot-pause-c` / `--gpu-hot-resume-c` & `--max-temp-c`):**
   - `train_v3p_stream.py` checks `ft.GpuHeatGuard(args.gpu_hot_pause_c, args.gpu_hot_resume_c)` (default `98.0 C` pause / `84.0 C` resume) and `ft.RamGuard` every 20 batches (`FORGE_MIN_FREE_RAM_GB=1.5` default; set `0` on Linux containers if using `linux_guards.py`).
   - `gen_cc0_selfgame_fqs.py` checks `--max-temp-c` every 25 games on Windows (`0` on Linux EPYC).
5. **Late-Epoch Regression Rollback:**
   - `--save-cycles` writes `cand_e{ep}.pt` at each cosine LR cycle boundary (`auto` at `20` epochs -> `e3, e6, e12, e20`). Export an earlier cycle checkpoint with `neon/forge_fixes/make_swa_v3p.py --ckpts cand_e12.pt --out-dir rollback_dir` and re-run post-training gates. (Note: `make_swa_v3p.py` hardcodes `FIX_ROOT = Path(r"C:\nnue-lab\neon\forge_fixes")`, so run it on Windows or override/set `PYTHONPATH="${FORGE_LAB_ROOT}/neon/forge_fixes:${FORGE_LAB_ROOT}/pipeline"` on Linux if adapting `FIX_ROOT`.)

---

## 5. Pre-Flight Verification, Parity `7/8` Status & Post-Training Gates

### A. Pre-Flight Commands (Run Before Paid Server Launch)
1. **CPU-Only Pipeline Self-Tests & Wave 5/7 Pytest Suites (`CUDA_VISIBLE_DEVICES=""`):**
   ```bash
   export HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES=""
   export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
   export FORGE_LAB_ROOT=/workspace/nnue-lab   # or C:\nnue-lab on Windows
   export PYTHONPATH="${FORGE_LAB_ROOT}/pipeline${PYTHONPATH:+:${PYTHONPATH}}"

   python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/gen_cc0_selfgame_fqs.py" --selftest
   python3 -B "${FORGE_LAB_ROOT}/neon/filter_quest/partition_fqs_buckets.py" --selftest
   python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/train_v3p_stream.py" --selftest
   python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/rescore_fqs_selective.py" --selftest \
     --in-dir "${FORGE_LAB_ROOT}/neon/forge_fixes/_tmp_rs_in" \
     --out-dir "${FORGE_LAB_ROOT}/neon/forge_fixes/_tmp_rs_out" \
     --exe "${FORGE_LAB_ROOT}/builds/v3p_engine" \
     --net "${FORGE_LAB_ROOT}/runs/forge/r0067/train/cand.fnn3" \
     --config "${FORGE_LAB_ROOT}/pipeline/config.forge.toml"
   # Note: On Linux, rescore_fqs_selective.py --selftest requires --exe, --net, and --config explicitly (since LAB defaults to Path(r"C:\nnue-lab")).
   python3 -B -m pytest -p no:cacheprovider -v \
     "${FORGE_LAB_ROOT}/neon/forge_fixes/teamwork_wave5/streamB_serverday_v2/tests/test_serverday_v2_pipeline.py" \
     "${FORGE_LAB_ROOT}/neon/forge_fixes/teamwork_wave7/streamB_serverday_final_spec/tests/test_serverday_skipnoisy_and_scripts_w7.py"
   ```
2. **Anchor SHA-256 Verification (Must Match Frozen Hashes):**
   ```bash
   python3 -B -c "
   import hashlib; from pathlib import Path
   exp = {
     'dead_draws_20k_s5disjoint.fqs.z': '7653279511862abc7d5bd856f14e61a594932ba625be09107e168d43e9b775a5',
     'won_endings_syzygy_20k.fqs.z': 'c2f51696b886c6cad78da2cca253352d79e6a188778c5ab35526b6321a4a96de',
     'opening_ply012_anchors.fqs.z': '6703857609240a6cbdf07d85e95d1747d939ccb307b685eb0c6c76675e4540d0',
     'heldout_syzygy_4k.json': 'b363d7843ea696008ced1d37699b255469202d9577a0c43f8849bd81979f1429',
   }
   anc = Path('${FORGE_LAB_ROOT}/neon/forge_fixes/anchors')
   for k, v in exp.items():
     got = hashlib.sha256((anc / k).read_bytes()).hexdigest()
     assert got == v, f'{k}: {got} != {v}'
   print('ANCHOR_SHA256_ALL_OK')
   "
   ```
3. **Host GPU / RAM / NVMe / Engine Preflight:**
   ```bash
   python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/teamwork_wave4/streamB_linux_serverday/linux_guards.py" --status
   python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/teamwork_wave4/streamB_linux_serverday/linux_guards.py" --check-ram-gb 16 --keep-ram-gb 5
   df -BG "${FORGE_LAB_ROOT}"   # require >= 160 GB free NVMe
   nvidia-smi || rocm-smi
   printf 'uci\nsetoption name NNUEArchFile value runs/forge/r0067/train/cand.fnn3\nsetoption name NNUEArch value true\nisready\nposition startpos\ngo perft 5\nbench 11\nbench 13\nquit\n' | "${FORGE_LAB_ROOT}/builds/v3p_engine"
   # Assert: perft 5 == 4865609 nodes
   ```

### B. Parity `7/8` Status (Non-Blocking for Server Day)
- **Live-Loop Patch (`patches/datagen_uci_parity_7_8_minimal.patch`, `111` lines, `sha256=184c6d2b8f880a7a22d23667e5b9ab38df53037c9736e14a115c84b9efa556c7`):** Opus issued `YES WITH REMARKS (PLAN-2711-OPUS-PARITY-PATCH-READ)` (`OPUS_TO_NEON.md:2834-2855`) approving placement into `pipeline/nnloop/datagen_uci.py` + `config.forge.toml` (`random_move_count_alt = 7`) at live-loop restart (`pilot_datagen_parity_7_8.json`: `white_stm=50.01%`, `mean_white_cp` cut from `+127.12` to `+68.46 cp`; `pilot_datagen_parity_7_8_G3_R4.json`: `white_stm=49.99%`, `mean_white_cp` cut from `+86.04` to `+69.99 cp`).
- **Non-Blocking Note for Server Day:** Server-Day datagen runs `gen_cc0_selfgame_fqs.py`, which **already implements exact 50/50 target-STM parity** (`rp in {1,2}` / `{4,5}` / `games % 3`) independently of `pipeline/nnloop/datagen_uci.py`. Server Day is therefore **NOT blocked** on live-loop restart.

### C. Post-Training Verification Gates (Mandatory Before Any Live Placement)
1. **CPU Correctness & Integrity Gates (`CUDA_VISIBLE_DEVICES=""`):**
   ```bash
   python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/teamwork_wave2/streamC_gates/run_master_gates.py" \
     --exe "${FORGE_LAB_ROOT}/builds/v3p_engine" --net "<cand.fnn3>" --full
   python3 -B -I "${FORGE_LAB_ROOT}/tmp/opus_scratch/netcheck/net_sanity.py" \
     --gate --exe-cmd '["./builds/v3p_engine"]' "<cand.fnn3>"
   python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/eval_heldout_syzygy.py" "<cand.fnn3>" --exe "${FORGE_LAB_ROOT}/builds/v3p_engine"
   python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/eval_net_full.py" "<cand.fnn3>" --exe "${FORGE_LAB_ROOT}/builds/v3p_engine"
   ```
   - **Pass Criteria:** `master_gates_ok == True` (`0 cp` parity across `8/8` or `16/16` KB & `8/8` OB), `net_sanity.py --gate` exits `0` (`0` FLAGs, `S5` passes), `OLS Q >= 950 cp` (and scale-free `Q/P ~ 10x`), `syz_win_ok_pct >= 99.0%`.
2. **PGO Equal-Time Match Gate (Rule R5):**
   - Build PGO binary (`FORGE_FINAL_V3P_PGO.exe`) supporting the candidate net, verify clean idle NPS (`bench 15`), and run a pre-declared GPU-idle PGO equal-time `fastchess` confirmation (**`2,000g @ 6+0.06` / `10+0.1`**, **`concurrency <= 7`** on 8-core hosts to avoid SMT core-sharing penalty observed in the `concurrency=10` `G3_FULL25_PGO` test) against live `forge.exe + r0067` (and `1024p/kb16` vs `1536p` if both arms are trained).
3. **Post-Net Search Stack & SPSA Retune:** Place independently confirmed orthogonal search wins 1-by-1 (plus `LmrDeeperShallower=true` if its `[0, 5]` SPRT passes; never `SF4b1` or unconfirmed combos), then run focused `pipeline/tools/spsa_tune.py` retune over eval-coupled options per `POST_G3_SPSA_RECIPE.md` and confirm in a fresh `2,000g @ 6+0.06` match before updating `config.forge.toml`.
