# GPU_REQUEST - R13 P4 v2-feature nets (bullet, HIP, RX 7900 XT) - for Engine NNUE to schedule

Nothing here runs without a window from Engine NNUE. Never start next to a training npt line: check `rocm-smi` and the npt
supervisor log (read only) right before each run; if a production trainer is on the GPU, do not start. grok-pc rule: start only at CPU load <= 80% and >= 8 GB free RAM,
stop at the next superbatch if load stays > 90%; run at BelowNormal priority (the loader uses `threads` CPU threads).

## Build (once, CPU, Idle, 2 jobs; own CARGO_HOME copy and target dir, nothing written under F:\bullet_hip)
```powershell
$env:CARGO_HOME = 'C:\o13\p4\cargo_home'            # copy of F:\bullet_hip\rust\cargo\registry (56 MB)
$env:CARGO_TARGET_DIR = 'C:\o13\p4\target_rocm'
$env:CARGO_BUILD_JOBS = '2'
# HIP_PATH / GCN_ARCH_NAME as in Engine NNUE's working F:\bullet_hip setup (Astra tools/bullet/run_hip_smoke.ps1 checks them)
& 'F:\bullet_hip\rust\rustup\toolchains\stable-x86_64-pc-windows-msvc\bin\cargo.exe' build --release --offline `
  --features rocm --manifest-path D:\grok-pc-data\dwqww\.claude\worktrees\o13-p4\opus_r13\p4\forge_v2_bullet\Cargo.toml
```

## Runs (one at a time; `forge_v2_bullet <stage> <binpack> <out_dir> <hidden> <superbatches> <batches_per_sb> <threads> <seed>`)
Data: `F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack` (read only; 013/014 stay out). Per run 40 superbatches x 1024
batches x 16384 = 671M positions, cosine LR 1e-3 -> 1e-4, WDL 0.4, eval scale 400 / 2.25 (Forge's sigmoid K).
| stage | hidden | seeds (fresh) | est. minutes per run | out dir |
|---|---|---|---|---|
| a (768 + 8 output buckets) | 768 / 1024 / 1536 | 13411, 13412 | 4 / 5 / 7 | F:\o13\p4\runs\a_h<H>_s<seed> |
| b (a + O6 threats) | 768 / 1024 / 1536 | 13421, 13422 | 13 / 18 / 27 | F:\o13\p4\runs\b_h<H>_s<seed> |
| c (b + O7 pawn pairs) | 768 / 1024 / 1536 | 13431, 13432 | 15 / 20 / 30 | F:\o13\p4\runs\c_h<H>_s<seed> |
Estimates: stage a from the measured 2.30M pos/s at h1024 (sb08 run, 1.22B positions in ~23 min); b / c scale with the active
inputs per position (32 -> ~130), so they are guesses until the first b run is timed. Whole sweep ~4.6 GPU hours; a first
10-minute window is enough for stage a h1024 with both seeds. Example:
```powershell
C:\o13\p4\target_rocm\release\forge-v2-bullet.exe a F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack `
  F:\o13\p4\runs\a_h1024_s13411 1024 40 1024 3 13411
```
(F: scratch only when F: >= 50 GB + the run's size; else C:\o13\p4\runs.)

## After each run (CPU)
```powershell
python -I -B opus_r13\p4\export_v2.py a <out_dir>\forge_v2_a_h1024-40\quantised.bin C:\o13\p4\nets\a_h1024_s13411.nnue2 --hidden 1024
```
(cargo names the binary forge-v2-bullet.exe, after the package.) Then: feature parity (forge-v2-bullet features vs v2_eval on 10k FENs, AVX2 + SSE), offline scoring (corr / MAE on the 20k
quiet Lichess set if the crew scorer is present), WAC300 at 200 ms against net-off (271-272), net md5 first.

## Deployment note (for the net-swap builds)
FORGENN2's hidden size must equal the engine's compile-time `FORGE_NNUE_HIDDEN` (v2 loader check). A 768 / 1024 / 1536 net
needs an R3-stack engine built with that hidden size; the compiled-in AL1 net (256) then has to be zero-padded to that width
(function-preserving: opus-sol-SC4 widen tool) so that the OFF pins still hold.
