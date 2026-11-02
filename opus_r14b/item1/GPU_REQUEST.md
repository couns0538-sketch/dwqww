# GPU window request - R14-B item 1 (fast npt loader), for Engine NNUE / Engine QA

**Ask:** one queue gap of **30 minutes** between two npt runs (the run itself is expected to take 12-20 minutes; the
rest is margin). Never start it while an npt line trains: the GPU and CPUs 0-3 must be free of the npt trainer. QA
inserts the gap; Opus (or QA) runs exactly the commands below. UNPROVEN: the result is a speed / GPU-use measurement
of the loader, not a net for gating.

## What it measures
One full trainer epoch of the live recipe (K32H3^, L1 1024, batch 16384, epoch 152.5M positions = 9,307 steps,
`--num-workers 4 --threads 2`, seed 5117) with `--fast-loader` (candidate DLL b5 sha256
9eb29b7d134a73eb58d47b2ced38587ed450ffaf11fdfcb108898652cefcd935): it/s, epoch minutes, GPU utilisation, RAM-floor
trips, loss. Control = the existing epochs of the live line with the default loader (e.g. w4_s24: epoch 0
train_loss_epoch 0.000948, val 0.000550, 15.6-20.5 min per epoch, GPU 25-50 %, `npt_try1.log`), so no control run
is needed in the window.

## Pre-checks (all must pass, else do not start)
1. No npt trainer alive: `Get-CimInstance Win32_Process | ? CommandLine -match 'nnue-pytorch-amd\\train.py'` is empty,
   and the keeper STATUS says the next line is held for this gap.
2. Free RAM >= 12 GB (guard floor 6 GB like the queue, plus margin), C: >= 52 GB (Couns: keep C: >= 50 GB; the run writes one 1.5 GB checkpoint there), D: >= 50 GB.
3. `D:\o14b\fl\b5_install\forge_fastloader.dll` has the sha256 above; `D:\o14b\npt` is the trainer copy with the
   `--fast-loader` switch (`tools/install_fast_loader.py`; files verified against `F:\opus_scratch\r6\nnue-pytorch-amd`).

## Command (PowerShell; Idle on CPUs 0-3 like the queue's trainer; GPU visible)
```powershell
$env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'; $env:TORCHINDUCTOR_COMPILE_THREADS='1'
$env:TMP='F:\opus_scratch\r6\tmp'; $env:TEMP='F:\opus_scratch\r6\tmp'
$env:TRITON_CACHE_DIR='F:\opus_scratch\r6\triton_cache'; $env:TORCHINDUCTOR_CACHE_DIR='F:\opus_scratch\r6\inductor_cache'
$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONUTF8='1'; $env:NNUE_FT_BACKEND='auto'
$env:NNUE_DATA_LOADER_LIB='D:\o14b\ref\libtraining_data_loader.dll'   # still imported by the trainer; not used for batches
$env:FORGE_FAST_LOADER_DIR='D:\o14b\fl\b5_install'
$env:R6_MIN_FREE_GB='6'; $env:R6_GUARD_LOG='C:\o14b\gpu\fl_e1_guard.jsonl'
Set-Location D:\o14b\npt
powershell -NoProfile -File D:\grok-pc-data\dwqww\.claude\worktrees\o14b-l1\opus_r14b\item1\tools\lowrun.ps1 -Mask 0xF -Priority Idle `
  -Exe F:\nnue_pytorch\venv\Scripts\python.exe -Out C:\o14b\gpu\fl_e1_stdout.log -Err C:\o14b\gpu\fl_e1_stderr.log -ArgLine `
  '-B opus_tools\guard_exec.py train.py F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack --validation-datasets F:\forge_j1_data\forge_holdout_013-014_j2.binpack --validation-size 1000000 --default-root-dir C:\o14b\gpu\fl_e1 --features K32H3^ --l1 1024 --batch-size 16384 --num-workers 4 --threads 2 --epoch-size 152500000 --max-epochs 1 --network-save-period 1 --save-top-k 1 --save-last-network False --swa-start-epoch -1 --seed 5117 --lr 0.000875 --start-lambda 1.0 --end-lambda 1.0 --no-filtered --no-wld-filtered --accelerator cuda --gamma 0.72 --fast-loader'
```
(The command line contains no `train_resid` name, so the NNUE supervisor does not adopt it; the output folder does
not start with `runs_`. `C:\o14b\gpu` must not exist before; create it right before the run.)

## During and after
- GPU utilisation: the keeper's own source, HWiNFO CSV `C:\Users\Administrator\grok-pc\nnue\tools\hwinfo\gpu_sensors.csv`
  (column `GPU Utilization [%]`), averaged over the training minutes only (from the first progress line to
  "Epoch 0 (Train): 100%"), plus the 20 % / 40 % / 60 % / 80 % it/s lines of `fl_e1_stdout.log`.
- Record: epoch minutes and it/s vs the control epochs; the startup line `Fast loader: ON (..., sha256 9eb29b7d...)`;
  `fl_e1_guard.jsonl` (`aborted: false`, min free RAM, peak private); train / val loss (sanity only: w4 and w1 streams
  are different samples, see RESULTS.md); checkpoint path (kept, never deleted).
- Done criteria for item 1 (Couns): >= 90 % GPU use in this window **or** >= 3x loader positions/s in the CPU ABBA;
  no RAM-floor trip over the full epoch.
- Expected minutes: if the loader stops being the limit, the epoch is GPU-bound. The live line now runs 7.4-10.3 it/s
  with GPU 25-50 %, so a GPU-bound epoch should be roughly 2x faster: 8-12 minutes of training plus ~2 minutes of
  start-up, validation (61 batches) and the checkpoint. Couns's estimate of ~100 minutes is not needed.
