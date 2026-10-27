# S50 — train_resid_v3c.py with warm start `--init-weights PATH` (default OFF; shares v3c with S39)

`train_resid_v3c.py` here = the S39 v3c (fixed-size epochs, `../sol_S39/`) + `--init-weights`; it supersedes the S39 file
(S39 code unchanged: `v3c_s39_to_s50.diff`). All options default off; off = v3b exactly.

| option | default | effect |
|---|---|---|
| `--epoch-positions N` | `0` (off) | S39: fixed-size epochs, N positions per epoch, seeded, no repeats within an epoch |
| `--recent-weight W` | `1.0` | S39: per-file weight 1.0 (first file) .. W (last file) for the fixed-size draw |
| `--init-weights PATH` | off | S50: warm start: model weights only from a finished run's `.pt` (trainer checkpoint or bare state_dict); fresh Adam, step 0, fresh lr warmup/cosine and blend ramp; md5 of PATH in the settings dump, the config and stdout |

Warm start details:
- Refused: other hidden size / residual mode (`ValueError`), any shape mismatch, non-finite weights; a missing PATH is an argparse
  error before the run dir exists. QAT mismatch -> WARNING.
- `--init-check` + `--init-weights`: the loaded net must reproduce the checkpoint's stored holdout `val` (1e-6, as v3b's check),
  so use the source run's `--holdout` and `--val-positions`; otherwise `INIT CHECK FAILED` and exit 3. Bare state_dict: skipped.
- `--resume` + `--init-weights` (what the supervisor does on a relaunch): resume wins, the init file is not loaded (and may be gone).
- To keep the source's final target mix, pass `--blend-start` = the source run's `--blend-end`.
- Example queue line (not applied; needs CR PASS + crew vote): `<name> --script train_resid_v3c.py --init-weights <runs\e48 run>\epoch048-....pt --epochs 16 --lr 7e-4 --blend-start 0.6 --blend-end 0.6 --shape 256 ...`

## Files
- `train_resid_v3c.py` — the trainer (deliverable; never run under this name on the PC).
- `v3b_to_v3c.diff` (vs the lock archive's v3b), `v3c_s39_to_s50.diff` (the S50 increment), `CHANGES_v3c.md`.
- `opus_nnue_smoke_s50.py` — CPU smoke runner (S39 cases + 7 warm-start cases, compare, 10k-step memory trace).
- `test_v3c_s50.py` — 27 tests (17 from S39 + 10 warm-start); `mutation_check_s50.py` — 17 planted bugs, each caught by its named test.
- `logs/` — step logs and `s50_outputs.tar.gz`; `README.md`, `IDEA_SOURCE.md`, `FILES.txt`, `SHA256SUMS`.

## How to run (PC rules: renamed copies only, Idle, 1 thread, scratch on F:)
```
cd /f/opus_scratch/sol_S50
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP='F:\opus_scratch\sol_S50\tmp' TEMP='F:\opus_scratch\sol_S50\tmp'
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe; J=/f/opus_scratch/worktrees/opus_sol_s50/opus_round1/sol_S50
nice -n 19 $PY -I -B $J/opus_nnue_smoke_s50.py --stage        # opus_nnue_smoke_s50_v3b.py / _v3c.py + data32 sample, pinned
nice -n 19 $PY -I -B $J/test_v3c_s50.py -v
nice -n 19 $PY -I -B $J/opus_nnue_smoke_s50.py --suite r1 && nice -n 19 $PY -I -B $J/opus_nnue_smoke_s50.py --compare r1
nice -n 19 $PY -I -B $J/opus_nnue_smoke_s50.py --rss t1
nice -n 19 $PY -I -B $J/mutation_check_s50.py
```
Each trainer run is a `python -I -B opus_nnue_smoke_s50.py --child <case dir>` process (no `train_resid` on any command line),
Idle priority, started only with >= 6 GiB available RAM and stopped below it; any new "adopted running job" line in
`F:\forge_nnue_train\supervisor.log` stops the suite.
