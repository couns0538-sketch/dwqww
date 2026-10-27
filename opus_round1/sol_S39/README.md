# S39 — train_resid_v3c.py: fixed-size epochs for the v3b trainer (both options default OFF)

`train_resid_v3c.py` = the lock archive's `train_resid_v3b.py` (md5 b6758004) plus two options:

| option | default | effect |
|---|---|---|
| `--epoch-positions N` | `0` (off) | every epoch trains on `N` positions drawn with a seeded RNG (`default_rng(seed*1000+epoch)`, as v3b) from all training files, no repeats within an epoch. steps/epoch = `N // batch` (then `--steps-per-epoch` caps it as in v3b), so the lr/blend schedule no longer grows with the data. `N >= train size` = full epochs = v3b exactly. |
| `--recent-weight W` | `1.0` (uniform) | only with `--epoch-positions`: per-position weight of each training file, linear from 1.0 for the first to `W` for the last file of the trainer's sorted file list (file names = age on the PC: `forge_selfplay_NNN`). Each file contributes its exact share `N * rows * weight / sum(rows * weight)` rounded by largest remainder (capped at the file's rows, the excess re-split), drawn uniformly inside the file; one shuffle then interleaves the files. |

- Off (neither option given): the code path, stdout, settings dump, `.pt/.inc/.bin/.json` are v3b's (proven below).
- On: per-step code is unchanged (the training loop is source-identical to v3b); only the epoch order built at the epoch boundary
  changes, in v3b's reused int32 order buffer (no new array of size N). The settings dump lists the v3c options only when set; the
  `.json`/`.pt` config gets `epoch_positions` and `recent_weight` only when fixed-size epochs are active.
- Uniform draw = the first `N` entries of v3b's own epoch permutation, so a run with `N` close to the data size trains on almost
  the same positions as v3b in the same order.
- Resume: the epoch draw depends only on (seed, epoch, file sizes, N, W), so `--resume` reproduces the remaining epochs (tested).
  If new data files appear between launch and resume (the supervisor re-expands `--train`), steps/epoch stays `N // batch`, so the
  schedule stays consistent (v3b would change steps/epoch mid-run); the drawn positions then come from the larger set.
- Errors (before the run dir is created): `--epoch-positions` < 0 or smaller than one batch, `--recent-weight` <= 0 / not finite,
  `--recent-weight` without `--epoch-positions`.

## Files
- `train_resid_v3c.py` — the trainer (deliverable; never run under this name on the PC).
- `v3b_to_v3c.diff` — unified diff against the lock archive's v3b.
- `CHANGES_v3c.md` — change log, results, RAM notes (style of `CHANGES_v3b.md`).
- `opus_nnue_smoke_s39.py` — CPU smoke runner (stage, suite, compare, 10k-step memory trace).
- `test_v3c_s39.py` — 17 unit / order-capture / code-identity tests (`--v3c <copy>` tests another copy).
- `mutation_check_s39.py` — planted-bug check: 8 mutants, each must be caught by its named test.
- `logs/` — step logs and the run outputs archive; `REPORT.md`, `IDEA_SOURCE.md`, `FILES.txt`, `SHA256SUMS`.

## How to run (PC rules: renamed copies only, Idle, 1 thread, scratch on F:)
```
cd /f/opus_scratch/sol_S39
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP='F:\opus_scratch\sol_S39\tmp' TEMP='F:\opus_scratch\sol_S39\tmp'
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe; J=/f/opus_scratch/worktrees/opus_sol_s39/opus_round1/sol_S39
nice -n 19 $PY -I -B $J/opus_nnue_smoke_s39.py --stage        # pinned copies: opus_nnue_smoke_s39_v3b.py / _v3c.py + data32 sample
nice -n 19 $PY -I -B $J/test_v3c_s39.py -v
nice -n 19 $PY -I -B $J/opus_nnue_smoke_s39.py --suite r1 && nice -n 19 $PY -I -B $J/opus_nnue_smoke_s39.py --compare r1
nice -n 19 $PY -I -B $J/opus_nnue_smoke_s39.py --rss t1
nice -n 19 $PY -I -B $J/mutation_check_s39.py
```
The runner starts each trainer run as `python -I -B opus_nnue_smoke_s39.py --child <case dir>` (no `train_resid` on any
command line), at Idle priority, only with >= 6 GiB available RAM (stopped below it), and stops the suite on any new
"adopted running job" line in `F:\forge_nnue_train\supervisor.log`.

## Use on the PC (not done here: needs CR PASS + crew vote)
Copy `train_resid_v3c.py` (md5 in `CHANGES_v3c.md`) and `qa_adam_dml.py` to the trainer tools folder and add e.g.
`--script train_resid_v3c.py --epoch-positions 137000000` to a queue line. Never deployed by this job.
