# R3-6Q — Lazy SMP time-to-depth on quiet GitHub runners

Re-measures R3-6 (`opus_r3/R3-6/`) on GitHub ubuntu-24.04 runners, to settle whether `SmpHelpersPastDepth`
shortens time-to-depth when the engine gets all its CPUs.

## What runs (`.github/workflows/opus-r3-smpq.yml`, push to `opus-r3-smpq` or workflow_dispatch)
1. **prep**:
   - `ci_build.sh`: g++-14, CMake Release, Ninja, `--target forge`, CMAKE_CXX_FLAGS
     `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`;
     identity (sha256, FMA count), `uci_check.py` quick (must print ALL OK), and the four SMP options in `uci`.
   - `ci_speed.sh`: nproc and lscpu, then Threads=1 `off` at full depth on every 5th position (6 of 30).
   - `choose_depth.py` compares those times with the PC's R3-6 times and estimates one job. The estimate is
     the speed ratio times the PC's 1209 s per job, scaled by the runner's own time-to-(D-k)/time-to-D. It
     picks the smallest uniform depth offset k in 0..2 whose estimate is ≤ 2520 s. The same k is used by
     every repetition, and it is recorded in every JSONL line (`depth_offset`, `base_depth`).
2. **ttd** (matrix rep 1/2/3, timeout 60 min): `ci_matrix.sh` runs the prep job's binary (uci_check again) on
   all 30 positions:
   - configs: off and on (SmpExactNodes + SmpBestThread + LocklessTT) at Threads 1,2,3; offP and onP
     (+ SmpHelpersPastDepth=true) at Threads 2,3;
   - Hash 64, one fresh process per run, each (config, threads, position) once;
   - order: positions shuffled per repetition, (config, threads) shuffled within a position;
   - no new position starts after 2700 s, so a slow runner leaves complete positions.
   Artifacts `smpq-rep<r>`: `ttd_rep<r>.jsonl`, `ttd_rep<r>.log`, `runner_rep<r>.txt` (nproc, lscpu, uptime
   before/after, binary sha256), `uci_check_rep<r>.log`.
3. **summary** (`needs: [prep, ttd]`, always): `report_q.py` on all repetitions. Artifact `smpq-summary`
   (`summary.md`, also the run's step summary).

## Tables (`report_q.py`, which uses R3-6 `summarize.py` unchanged)
- Pooled: per-position medians over the repetitions.
  - R3-6 main table: time-to-depth sum, speedup, per-position speedup gmean, node inflation, NPS scaling,
    CPUs got, other load.
  - Paired wall/CPU/nodes ratios for offP vs off, onP vs on, on vs off and onP vs off, with 95% bootstrap CIs
    over positions.
- Per repetition: the same tables.
- Side by side with the PC (R3-6 numbers embedded in `report_q.py`).
- Run header: steal time (VM neighbours), CPUs got per cell, and Threads=1 determinism (identical nodes in
  every repetition).

## Collect a finished run (PC, from inside the worktree)
```
gh run list --branch opus-r3-smpq --workflow opus-r3-smpq --limit 3
bash opus_r3/R3-6Q/collect.sh <run_id> /f/opus_scratch/r3/R3-6Q/run_<run_id>
```
`collect.sh` downloads each artifact into its own directory and writes `summary_local.md`. It runs
`report_q.py` with the venv Python `-I -B`. To summarise by hand:
`python -I -B opus_r3/R3-6Q/report_q.py <dir>/smpq-rep1/ttd_rep1.jsonl <dir>/smpq-rep2/ttd_rep2.jsonl <dir>/smpq-rep3/ttd_rep3.jsonl`.

## Local smoke test (PC, nice 19)
`smp_ttd_linux.py` falls back to GetProcessTimes/GetSystemTimes and IDLE priority on Windows, so its
argument, scheduling, parse and output logic can run on the PC. `--plan-only` prints the run order.
