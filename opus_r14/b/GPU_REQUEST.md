# R14 Main item 1 - GPU window request: v2-feature nets (FORGENN2, bullet ROCm) - for Engine NNUE to schedule

Status 2026-11-02 10:40 PC clock (01:40 PT): **waiting for a window; nothing started.** UNPROVEN, no Elo claim.
GPU at that time (read only, `grok-pc\forge_push\npt_keeper\STATUS.md` 10:28 PC clock): npt line
`npt_k32h3_l1024_bs16k_e8x152m5_g072_lam10_w4_s24` training, next pending `..._s25`, keeper window to 2026-11-08 00:00 PC with
~132 h of npt lines queued and fresh-seed npt lines inserted when the head is not npt -> no gap for another trainer.
Nothing here runs next to an npt line, and nothing here runs without a written window from Engine NNUE.

## Checks before every run (all must hold; the run wrapper - not written yet, it comes with the first window - must check them itself before and during each run, not only at start)
1. Engine NNUE gave a window (time span written in `opus_r14/b/WINDOW.md` by the owner or quoted from their note).
2. No production trainer on the GPU: no `nnue-pytorch` / `train.py` / `train_resid*` python process (process list) and the
   npt keeper STATUS says `npt trainer running | NO`; `rocm-smi` shows the GPU idle.
3. PC: total CPU <= 80 %, free RAM >= 8 GB during the run (stop at the next superbatch when the load stays > 90 %),
   BelowNormal, loader threads 2 (CR R13 run rule).
4. Disk: D: >= 50 GB + 1 GB per run before writing (outputs `D:\o14a\p4\runs\<stage>_h<H>_s<seed>`, one checkpoint per
   run: `save_rate` = superbatches; ~0.1-0.3 GB per run, ~3-4 GB for all 18). If D: is too low, stop and ask (C: would be a
   deviation from the D:\o14a scratch rule; F: is write-forbidden while below its reserve).

## Build (once, CPU only, Idle, 2 jobs; can be done before the window, it does not use the GPU)
Environment exactly as Engine NNUE's zero-install route (`F:\bullet_hip\PLAN.md` step 2.3, `launch_smoke.bat`), set in the
build process only (never machine-wide: a global HIP_PATH changes Triton's HIP lookup for the npt line):
`vcvars64.bat`, `HIP_PATH=F:\nnue_pytorch\venv\Lib\site-packages\_rocm_sdk_devel` (read only), PATH prefixed with cargo\bin and
the venv's ROCm bin dirs, `GCN_ARCH_NAME=gfx1100`, then
```powershell
$env:CARGO_HOME = 'C:\o13\p4\cargo_home'; $env:CARGO_TARGET_DIR = 'D:\o14a\p4\target_rocm'; $env:CARGO_BUILD_JOBS = '2'
& 'F:\bullet_hip\rust\rustup\toolchains\stable-x86_64-pc-windows-msvc\bin\cargo.exe' build --release --offline --features rocm `
  --manifest-path D:\grok-pc-data\dwqww\.claude\worktrees\o13-p4\opus_r13\p4\forge_v2_bullet\Cargo.toml
```
Known risk (Engine NNUE's CR LOW-1): bullet's build.rs emits `-lstdc++`, which MSVC link.exe should only warn about; if it
errors, the fix is their `lstdcxx_msvc_guard.diff` - third-party build code under F:\bullet_hip\src (not mine to change;
F:\bullet_hip\src has local changes by its owner), so that is a CR / owner item.
Source = opus-r13-p4-v2nets after CR's final delta d884c23b (main.rs md5 9ede6e56); the mock-backend build of the same source
is 70cbae12 (CPU parity proven at H 256 / 768 / 1024 / 1536, opus_r13/p4/RESULTS.md).

## Runs (one at a time, staged a -> b -> c; fresh R14 seeds, never used before)
`forge-v2-bullet.exe <stage> <binpack> <out_dir> <hidden> <superbatches> <batches_per_sb> <threads> <seed>`, data
`F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack` (read only; holdout 013/014 stays out), 40 superbatches x 1024
batches x 16384 = 671M positions per run, cosine LR 1e-3 -> 1e-4, WDL 0.4, eval scale 400 / 2.25.
| order | stage | hidden | seeds | est. GPU minutes per run | first window |
|---|---|---|---|---|---|
| 1 | a (768 + 8 output buckets) | 1024, 768, 1536 | 14411, 14412 | 5 / 4 / 7 | a 10-minute window covers a_h1024 with both seeds |
| 2 | b (a + O6 threats) | 1024, 768, 1536 | 14421, 14422 | 18 / 13 / 27 | - |
| 3 | c (b + O7 pawn pairs) | 1024, 768, 1536 | 14431, 14432 | 20 / 15 / 30 | - |
Minutes: stage a from the measured 2.30M pos/s at h1024 (R13 note); b / c scaled by the active inputs per position and
unmeasured until the first b run is timed. Whole grid 18 runs ~4.6 GPU h. Example (first run):
```powershell
D:\o14a\p4\target_rocm\release\forge-v2-bullet.exe a F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack `
  D:\o14a\p4\runs\a_h1024_s14411 1024 40 1024 2 14411
```
Stage rule: start b only after the a nets are scored; skip a width whose two a seeds both score worse than the H1024 a nets.

## After each run (CPU, Idle)
1. `python -I -B opus_r13\p4\export_v2.py <stage> <out>\...\quantised.bin D:\o14a\p4\nets\<stage>_h<H>_s<seed>.nnue2 --hidden <H>`;
   net md5 + sha256 first.
2. Trained-net parity: CR's parity_v2.sh flow with the H harness (`D:\o14a\p4\v2_eval_{avx2,sse}_h<H>.exe`) on the legal-only
   10k FENs, fresh dir: 10000/10000 exact on AVX2 and SSE.
3. Offline scoring with the crew's method (`grok-pc\qa_npt_*\pack`: lichess_quiet_20000 corr / MAE, `wac_tactics.py`
   WAC300 at 200 ms vs net-off 271-272) through a v2-capable engine of the same width.
4. Hand-over (best 1-2 nets only): net-swap LTO+PGO `-Expose` build. Deployment needs an engine built with
   FORGE_NNUE_HIDDEN = H whose compiled-in AL1 net is zero-padded to H (function-preserving widen, opus-sol-SC4 tool) so the
   OFF pins still hold; then net md5, null-move cutoff test on 3 FENs, bench recorded, the full R14 proof set.
   This port is its own job and starts only when a trained net beats the baseline offline.

## What exists now (no GPU needed)
- Trainer config forge_v2_bullet (stages a / b / c, own ForgeV2 input type), exporter export_v2.py, float32 reference
  eval_ref.py, random-net generator, legal-only FEN filter, CR-checked parity script; parity PASS at H 256 / 768 / 1024 / 1536.
- Not done: ROCm build (needs the HIP env of F:\bullet_hip), any training, any scoring, any engine build with a v2 net.
