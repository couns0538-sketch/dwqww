# S-A3 — train_resid_v3d.py: LR schedule options (defaults = v3b's schedule)

`train_resid_v3d.py` = opus-sol-S50's `train_resid_v3c.py` (v3b + fixed-size epochs + warm start) + three LR-schedule arguments.
With all defaults it is v3b: same LR at every step (bit for bit), same stdout, settings dump and `.pt/.inc/.bin/.json`.

| option | default | effect |
|---|---|---|
| `--lr-schedule {cosine,linear,wsd}` | `cosine` (v3b) | shape after the linear warmup: half-cosine (v3b's expression), straight line, or warmup-stable-decay (peak lr, then a straight line over the last `--lr-decay-frac` of the horizon); all end at `--min-lr-frac` x `--lr` |
| `--lr-schedule-epochs E` | `0` (= `--epochs`) | schedule horizon = steps/epoch x E; the run may stop before it (planned long run, stopped early) or go past it (lr stays at the floor); with E fixed, `--resume` with a larger `--epochs` extends a run on the same lr curve |
| `--lr-decay-frac F` | `0.2` | wsd only: decay steps = round-half-up(F x horizon), at least 1, never inside the warmup |

- The floor is v3b's existing `--min-lr-frac` (default 0.01), used by every schedule; `--warmup-steps` and `--lr` as in v3b.
- A non-default schedule is recorded: the settings dump lists all three options, the `.json`/`.pt` config gets `lr_schedule`,
  `lr_schedule_steps` (+ `lr_decay_frac`, `lr_decay_start_step` for wsd), stdout gets `lr schedule: …`, and the
  `steps/epoch=…` line names the schedule. With the defaults none of this appears.
- The blend ramp is unchanged (follows `--epochs`): an extended run keeps its lr curve but the blend ramp changes unless
  `--blend-start` = `--blend-end`.
- Errors (before the run dir exists): unknown schedule, `--lr-schedule-epochs` < 0, `--lr-decay-frac` outside (0, 1] or not
  finite, `--lr-decay-frac` without `--lr-schedule wsd`.

## Files
- `train_resid_v3d.py` (deliverable; never run under this name), `v3c_to_v3d.diff`, `v3b_to_v3d.diff`, `CHANGES_v3d.md`.
- `sa3_queue_lines.txt`: 3 proposed queue lines (UNPROVEN, not queued), `opus_sa3_queue_dryparse.py`: dry parse + GPU hours.
- `opus_nnue_smoke_sa3.py`: CPU smoke runner (stage, suite, compare, memory trace); `test_v3d_sa3.py` (38 tests);
  `mutation_check_sa3.py` (28 planted bugs); `logs/`; `README.md`, `IDEA_SOURCE.md`, `FILES.txt`, `SHA256SUMS`.

## How to run (PC rules: renamed copies only, Idle, 1 thread, scratch on F:)
```
cd /f/opus_scratch/sol_SA3
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP='F:\opus_scratch\sol_SA3\tmp' TEMP='F:\opus_scratch\sol_SA3\tmp'
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe; J=/f/opus_scratch/worktrees/opus_sol_sa3/opus_round1/sol_SA3
nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa3.py --stage     # copies opus_nnue_smoke_sa3_v3b/_v3c/_v3d.py + data32 sample (pinned)
nice -n 19 $PY -I -B $J/test_v3d_sa3.py -v
nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa3.py --suite r1 && nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa3.py --compare r1
nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa3.py --rss t1
nice -n 19 $PY -I -B $J/mutation_check_sa3.py
nice -n 19 $PY -I -B $J/opus_sa3_queue_dryparse.py          # reads sa3_queue_lines.txt (no train_resid name on any command line)
```
