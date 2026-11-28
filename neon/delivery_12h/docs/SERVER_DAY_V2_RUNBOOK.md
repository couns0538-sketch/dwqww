# Server-Day v2 Operator Runbook (`FORGENN3-P` + `FQS1` Streaming Pipeline)

**Scope:** Reproducible Linux/CPU+GPU execution checklist for Server-Day v2 using `gen_cc0_selfgame_fqs.py` (parity-balanced CC0 self-play), optional `rescore_fqs_selective.py --prioritize-opp-castle`, `partition_fqs_buckets.py` (`--dedup-mode avg`), and `train_v3p_stream.py` (`1024w|1536w`, `kb=8|16`).

> **Rule R5 (Evidence Integrity):** Training loss, validation MSE, WDL ECE, and offline scorecards are strictly diagnostic leads — never Elo claims. Adoption of any net (`kb=16`, `1536w`, or new 2B candidate) is decided solely by a pre-declared, GPU-idle, PGO equal-time `fastchess` match (`2,000g @ 6+0.06` / `10+0.1`), never pooling screens with confirmations.

---

## 1. What Changed in Server-Day v2 (Parity & Pipeline Fixes)

### A. Live-Loop `+153 cp / 61.4%` White-Win Bias Root Cause & Fix
- **Root Cause (`LIVE_LOOP_PARITY_BIAS_AUDIT.json`):** `C:\nnue-lab\pipeline\config.forge.toml` fixed even `random_move_count = 8` from `startpos`. Ply 7 was always Black's blind random move, giving White the first searched move on ply 8.
- **Measured Live-Loop Skew (`r0180`..`r0202`, `13.87M–13.88M` rows/round):** `mean_white_cp` = `+151.39` to `+153.94 cp` (`r0202`: `+152.8 cp`, `white_score_pct = 61.41%`; `r0202` 1M sample: `W/D/L = 41.87% / 39.03% / 19.11%`, `2.2:1` win skew). Raw `book_cc0_clean.epd` (`233,104` openings) also leans `58.38%` White-to-move (`136,082` W).
- **Parity Fix (`gen_cc0_selfgame_fqs.py`):**
  - Alternates `target_turn` (`WHITE` / `BLACK`, `50/50`) per game and picks `rp in {1, 2}` (standard) or `rp in {4, 5}` (`--wide-div-frac 0.15`), while `startpos` uses `rp = games % 3`.
  - **20,000-row (`202`-game) live verification (`HANDOFF_12H_DATA_QUALITY.md`):** `white_stm = 49.79%`, `mean_white_cp = +21.87 cp`, `white_score_pct = 53.79%`.
  - **Post-Run Wrapper Gate (`run_datagen_epyc_v2.sh`):** Because `gen_cc0_selfgame_fqs.py` `summary.json` omits `white_stm`, `run_datagen_epyc_v2.sh` runs synchronously (no `exec`) and executes an inline Python shard scan verifying `summary.json` exists, `0` `.part` files remain, `FQS1` magic + 38-byte alignment pass, and `47.0% <= white_stm_pct <= 53.0%`.

### B. `kb=16` & `1536w` Architecture Options
| Config | `.fnn3` Size | Verified Parity / Notes | When to Use |
|---|---:|---|---|
| **`1024w, kb=8`** *(default)* | `12.21 MiB` | Baseline Server-Day target (`12,798,184 B`) | **Primary 2.0B baseline first** |
| **`1024w, kb=16`** | `24.39 MiB` | `0 cp` max diff on `v3p_fused_v3_engine.exe` (`V3P_KB16_FEASIBILITY.json`, ZERO C++ change); `3.3331 bits` (`cc0_v2`) / `3.5224 bits` (`r0202`) entropy; `0.578%` min bucket (`23.12M` perspectives @ 2B); motivated by `SF19` `opp_side_castling` `20.81%` severe error (`G3_FULL25_e24`) vs `11.76%` `quiet_positional` | Optional second candidate (`KING_BUCKETS=16`) if GPU budget permits; adopt only via Rule R5 PGO `fastchess` |
| **`1536w, kb=8`** | `18.21 MiB` | `~1.45x` GPU training time vs `1024w`; higher L1/cache footprint | Optional head-to-head candidate (`HIDDEN=1536`) on same deduped shards; adopt only via Rule R5 PGO `fastchess` |

---

## 2. Cost & Sizing Table (`SERVER_DAY_COST_MODEL.json`)

> **Measurement vs Estimate Disclosure:** Compressed `.fqs.z` size (`19.7 GB` @ 2.0B usable, `13.5x` smaller than `.plain`), bucketed dedup (`23.0 GiB` total RAM on 32w / `766.3k rec/s`), and local RX 7900 XT throughput (`1.91M pos/s`) are **directly measured**. Cloud hourly rates (`EUR`) and H100/RTX 4090 throughput are **planning estimates** — confirm real throughput in an Hour-1 pilot before scaling.

| Scenario | Target Usable (`Raw`) | Nodes / Rescore | CPU Node (`Datagen+Rescore`, `Dedup`) | Transfer @ `1 Gbps` | GPU Training (`20 ep`) | Est. CPU + GPU Cost | `EUR / 1B` |
|---|---:|---:|---|---:|---|---:|---:|
| **A (`1024w`, EPYC + H100)** | `2.0B` (`2.5B`) | `4k`, `0.5%` 16k | `256c` EPYC (`14.56h`, `0.11h` / `23 GiB` RAM) | `19.7 GB` (`2.6 min`) | `1x H100 80GB` (`2.65h`, est `4.2M pos/s`) | `€66.05 + €6.35 = €72.40` | `€36.20` |
| **B (`1536w`, EPYC + H100)** | `2.0B` (`2.5B`) | `4k`, `0.5%` 16k | `256c` EPYC (`14.56h`, `0.11h` / `23 GiB` RAM) | `19.7 GB` (`2.6 min`) | `1x H100 80GB` (`3.84h`, `~1.45x` slower) | `€66.05 + €9.21 = €75.25` | `€37.63` |
| **C (`1024w`, Hybrid Local)** | `1.5B` (`1.875B`) | `2k`, `1.0%` 16k | `256c` EPYC (`6.25h`, `0.09h` / `23 GiB` RAM) | `14.8 GB` (`2.0 min`) | Local RX 7900 XT (`4.36h`, `1.91M pos/s`) | `€28.52 + €0.00 = €28.52` | `€19.01` |
| **D (`1024w`, EPYC + 4090)** | `1.5B` (`1.875B`) | `4k`, `0.5%` 16k | `128c` EPYC (`21.84h`, `0.09h` / `23 GiB` RAM) | `14.8 GB` (`2.0 min`) | `1x RTX 4090` (`2.98h`, est `2.8M pos/s`) | `€49.34 + €1.64 = €50.98` | `€33.99` |

*NVMe headroom:* Maintain `>= 150 GB` free NVMe during `130.6 GB` peak dedup scratch (`2.0B` scenario).

---

## 3. End-to-End Operator Checklist

### Step 0 — Preflight & Qualification (Hour 1)
1. Verify portable RAM/thermal guards and host readings:
   ```bash
   python3 -B neon/forge_fixes/teamwork_wave4/streamB_linux_serverday/linux_guards.py --status
   python3 -B neon/forge_fixes/teamwork_wave4/streamB_linux_serverday/linux_guards.py --check-ram-gb 16 --keep-ram-gb 5
   ```
2. Verify engine correctness (`perft 5 == 4865609`, `bench 11`, `bench 13`) on `./builds/v3p_engine` with `runs/forge/r0067/train/cand.fnn3`.
3. Run CPU-only pipeline regression tests (with `HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 FORGE_MIN_FREE_RAM_GB=0`):
   ```bash
   python3 -B -m pytest -p no:cacheprovider -v neon/forge_fixes/teamwork_wave5/streamB_serverday_v2/tests/test_serverday_v2_pipeline.py
   ```

### Step 1 — Parity-Balanced CC0 Datagen (`run_datagen_epyc_v2.sh`)
1. Dry-run and inspect exact flags (`--wide-div-frac 0.15`, `--tablebase-dir`, `--shard-size`, `--resume`):
   ```bash
   FORGE_LAB_ROOT=/workspace/nnue-lab bash neon/forge_fixes/teamwork_wave5/streamB_serverday_v2/run_datagen_epyc_v2.sh --dry-run --syzygy-dir /workspace/nnue-lab/tablebases/syzygy345
   ```
   *(Note: `--syzygy-dir` or `SYZYGY_DIR` is a shell-wrapper alias mapped cleanly to `gen_cc0_selfgame_fqs.py --tablebase-dir`.)*
2. Launch live datagen (with Hour-1 `10M` pilot first to verify `pos/s`):
   ```bash
   FORGE_LAB_ROOT=/workspace/nnue-lab OUT_DIR=/workspace/nnue-lab/data/raw_2b WORKERS=128 \
     bash neon/forge_fixes/teamwork_wave5/streamB_serverday_v2/run_datagen_epyc_v2.sh --syzygy-dir /workspace/nnue-lab/tablebases/syzygy345
   ```
3. Confirm stdout ends with `PARITY_CHECK_PASS: ... white_stm_pct=...` inside `[47.0%, 53.0%]` and `0` `.part` files.

### Step 2 — Optional Selective `16k` Rescoring (`rescore_fqs_selective.py`)
- **Script Location & Linux Caveat:** `rescore_fqs_selective.py` lives at `neon/forge_fixes/rescore_fqs_selective.py` (NOT `neon/filter_quest/`). It hardcodes `LAB = Path(r"C:\nnue-lab")` and unconditionally runs `from nnloop.heat import cpu_temp`. On Linux, you **MUST** export `PYTHONPATH="${FORGE_LAB_ROOT}/pipeline"` and pass `--exe`, `--net`, and `--config` explicitly:
  ```bash
  export HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
  export PYTHONPATH="${FORGE_LAB_ROOT}/pipeline${PYTHONPATH:+:${PYTHONPATH}}"
  python3 -B neon/forge_fixes/rescore_fqs_selective.py \
    --in-dir /workspace/nnue-lab/data/raw_2b \
    --out-dir /workspace/nnue-lab/data/raw_2b_rescored \
    --soft-nodes 16000 --max-frac 0.005 --workers 128 --prioritize-opp-castle \
    --exe /workspace/nnue-lab/builds/v3p_engine \
    --net /workspace/nnue-lab/runs/forge/r0067/train/cand.fnn3 \
    --config /workspace/nnue-lab/pipeline/config.forge.toml
  ```
- Inspect `raw_2b_rescored/rescore_summary.json` (`rescored == selected`, zero `.part` files).

### Step 3 — Bucketed `avg` Dedup (`partition_fqs_buckets.py`)
1. Run `neon/forge_fixes/teamwork_wave4/streamB_linux_serverday/run_dedup_buckets.sh` (`--buckets 128 --workers 64 --dedup-mode avg --drop-draw-conflict 600 --shard-rows 500000`) pointing `IN_DIR` at the raw/rescored shards and `OUT_DIR=/workspace/nnue-lab/data/clean_2b_avg`.
2. Confirm `summary.json` shows `kept_rows` on target, `_buckets_tmp/` removed, and zero `.part` files.

### Step 4 — GPU Stream Training (`run_train_stream_gpu_v2.sh`)
1. Dry-run and inspect both `linux_guards.py` preflight and `train_v3p_stream.py` command:
   ```bash
   FORGE_LAB_ROOT=/workspace/nnue-lab bash neon/forge_fixes/teamwork_wave5/streamB_serverday_v2/run_train_stream_gpu_v2.sh --dry-run
   ```
   - Optional overrides: `--hidden 1536` (or `HIDDEN=1536`) and/or `--king-buckets 16` (or `KING_BUCKETS=16`).
   - Override `DISTILL_NET` to the gated `G3_FULL25` checkpoint once `G3_FULL25` completes and passes gates (default is `G2_v3p_1024_pairwise_psqt/cand.pt`; set `DISTILL_NET=""` to disable).
   - **Why `--save-ckpt-every` is omitted:** `train_v3p_stream.py` does **not** define `--save-ckpt-every` (passing it exits with code `2`). It already writes `resume_ckpt.pt` atomically (`tmp_resume_ckpt.pt -> os.replace`) after every superbatch, while `--save-cycles` writes `cand_e{ep}.pt` at each cosine LR cycle boundary.
2. Launch live GPU training:
   ```bash
   FORGE_LAB_ROOT=/workspace/nnue-lab OUT_DIR=/workspace/nnue-lab/runs/serverday_2b_1024p \
     bash neon/forge_fixes/teamwork_wave5/streamB_serverday_v2/run_train_stream_gpu_v2.sh
   ```

### Step 5 — Export, CPU Correctness Gates & Rule R5 `fastchess`
1. **SWA Caution (`M_SWA` `-29.95 Elo`):** Cross-cycle SWA across `5e-4` LR restarts (`cand_e12 + cand_e20`) degraded strength by `-29.95 Elo` due to basin drift. Evaluate `cand.fnn3` directly or export individual cycle checkpoints (`make_swa_v3p.py --ckpts ... --out-dir ...`) / final-tail SWA only if verified.
2. Run all mandatory CPU-only gates (`HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES=""`):
   - `python3 -B neon/forge_fixes/teamwork_wave2/streamC_gates/run_master_gates.py --exe ./builds/v3p_engine --net <cand.fnn3> --full` (`hard_pass == True`, `0 cp` parity)
   - `python3 -B -I tmp/opus_scratch/netcheck/net_sanity.py --gate --exe-cmd '["./builds/v3p_engine"]' <cand.fnn3>` (`0` FLAGs, `S5 passes`)
   - `python3 -B neon/forge_fixes/eval_heldout_syzygy.py <cand.fnn3> --exe ./builds/v3p_engine`
3. Run a GPU-idle PGO equal-time `2,000g @ 6+0.06` / `10+0.1` `fastchess` confirmation against the current best net (Rule R5).

---

## 4. Exact Recovery & Rollback Procedures

1. **Datagen Preemption / Crash:**
   - Remove incomplete `.part` files only: `find "${OUT_DIR}" -maxdepth 1 -name '*.part' -delete`
   - Keep all intact `cc0_wXX_sYYY.fqs.z` shards and relaunch `run_datagen_epyc_v2.sh` (`RESUME=1` is default, passing `--resume` to skip existing valid shards).
2. **Bucketed Dedup Failure:**
   - Delete scratch `_buckets_tmp/` and any `.part` files in `OUT_DIR`: `rm -rf "${OUT_DIR}/_buckets_tmp" "${OUT_DIR}"/*.part`
   - Rerun `run_dedup_buckets.sh` (deterministic inputs -> identical output).
3. **GPU Training Interruption / Spot Preemption:**
   - Check `OUT_DIR`: remove any orphaned `tmp_resume_ckpt.pt` (`rm -f "${OUT_DIR}/tmp_resume_ckpt.pt"`), preserving `resume_ckpt.pt` (automatically written atomically after every superbatch).
   - Relaunch `run_train_stream_gpu_v2.sh` with the **exact same** `FQS_SHARDS`, `SHARDS_PER_SB`, `SEED`, `HIDDEN`, `KING_BUCKETS`, and `RESUME=1` (`--resume`), and confirm stdout prints `RESUMED STREAM at ep=... sb=... step=...`.
4. **Late-Epoch Regression or Gate Failure:**
   - Export an earlier cosine cycle checkpoint (`cand_e6.pt`, `cand_e12.pt`, etc. saved by `--save-cycles`) using `make_swa_v3p.py --ckpts <cand_eN.pt> --out-dir <rollback_dir>`, then re-run Step 5 CPU gates and Rule R5 `fastchess`.
