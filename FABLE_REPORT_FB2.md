# FABLE_REPORT_FB2.md — pack FB2 (Fable 5.1, 2026-10-28) — IN PROGRESS

Base of every `fable-fb2-*` branch: `fable-nnue-arch` head `08b589e1` (= AL1 lock `d4f4312` + CI baseline + the FB1
NNUE v3 engine/trainer). No Elo claims anywhere (no gate was run); no speed claims (loaded PC: gates, self-play and
production NNUE training ran throughout; my work at `nice -n 19`, one training thread). Machine exclusive: no.
No sub-agents were used (user instruction); nothing under `F:\forge_nnue_train`, `selfplay_out` or `forge_push` was
written; all outputs are under `F:\opus_scratch\fable\`.

| job | branch | status |
|---|---|---|
| J1 real v3 net at scale | `fable-fb2-j1` | data split DONE, trainer upgrade DONE, training RUNNING (checkpoints every 30 min) |
| J2 datagen upgrade | `fable-fb2-j2` | not started |
| J3 search improvements | `fable-fb2-j3` | not started |
| J4 time management v2 | `fable-fb2-j4` | not started |
| J5 SMP v2 | `fable-fb2-j5` | not started |
| J6 gate design | (file) `F:\opus_scratch\fable\GATE_BOUNDS.md` | not started |
| J7 NNUE v4 ideas | `fable-fb2-j7` | not started |

## J1 — real v3 net, trained at scale (`fable-fb2-j1`, folder `fable_fb2/j1/`)

### Data split (DONE)

`tools/nnue/fable_nnue_data.py split` (new; unit test `tools/nnue/test_fable_nnue_data.py` PASS on synthetic shards
with a Python-set reference: dedup, holdout/training disjointness, unaltered rows, FPOS/FHCE round trip, phase
targets, manifest check, determinism). Real run on the 35 production shards (6.4 min, one thread, read-only
inputs; log `fable_fb2/j1/logs/split_real.log`, manifest copy `fable_fb2/j1/logs/MANIFEST.json`):

| item | value |
|---|---|
| input rows | 288,302,469 (33 training shards 271,913,894 + holdout shards 013/014 16,388,575) |
| exact duplicates (board + side to move), first copy kept, holdout rows win | 85,223 removed (0.030%); 1,352 inside 013/014 |
| training rows written | **271,830,023** in 64 globally shuffled shards `F:\opus_scratch\fable\data\train\fb2_train_000..063.pos/.hce` (4.24-4.25M rows each, 9.4 GB, read-only) |
| holdout | **200,000 rows** `F:\opus_scratch\fable\data\holdout\fb2_holdout_200k.pos/.hce`, drawn from the deduplicated 013/014 pool (16,387,223 rows), phase-stratified |
| phase histogram (piece-count buckets 0..7) train | 5.77 / 18.95 / 15.31 / 12.15 / 10.81 / 10.99 / 12.73 / 13.29 % |
| phase histogram holdout | identical to 4 decimals (11549 / 37896 / 30627 / 24294 / 21614 / 21971 / 25464 / 26585 rows) |
| scratch left in place (owner may delete) | `F:\opus_scratch\fable\data\work\` 14 GB of hash partitions and scatter records |

Why 013/014 only for the holdout: the AL1 net never trained on those shards, so AL1 and every J1 net are scored on
positions neither has seen; the rest of 013/014 is used nowhere (other plies of the same games would leak).

### Reference scores on the 200k holdout (exact, S31 scorer; `fable_fb2/j1/logs/al1_fb2_holdout_score.json`)

| net | MSE b0.6 (lock blend, the decision metric) | b0.8 | b1.0 |
|---|---|---|---|
| HCE alone | 0.017141 | 0.008421 | 0.005131 |
| **AL1 lock net e32f003rec** (`src/nnue_weights.inc`, md5 f5f6a34a) | **0.014417** | 0.006808 | 0.004629 |

(The run's `--target-loss` was set to 0.014310, the AL1 value on the full 1M-row S16 subset, before this number
existed; it is stricter than 0.014417, so a net that reaches 0.014417 keeps training, which is harmless. The report
compares every checkpoint with 0.014417.)

### Trainer upgrade (DONE; `tools/nnue/fable_nnue_train.py`, driver `tools/nnue/fable_nnue_chunks.py`)

New: `--resume` (model, Adam state, schedule position, numpy and torch RNG state; a checkpoint's config must match the
command line), `--ckpt-every-minutes` (atomic `ckpt.pt`, exported `ckNN_stepS.fnn3`, exact integer holdout score at
b0.6/b0.8/b1.0 with a per-phase breakdown, engine parity through `forge_nnue_v3_tool eval` on 10,000 positions,
`status.json`, `best.fnn3`), stop rules `--target-loss` and `--plateau N` (N checkpoints without improving the best
exact b0.6 by `--plateau-eps` 1e-5), `--max-minutes` pauses a chunk and the driver resumes it, LR warmup
(`--warmup-steps`) and the WDL-lambda schedule (`--blend-schedule linear|cosine --blend-start --blend-end`).
Smoke tests (H128, 300k rows of the S16 holdout subset; logs `fable_fb2/j1/logs/smoke_train*_log.txt`): checkpoints
with exact score + parity PASS (10000/10000, max float-int 1.02 cp), pause after `--max-minutes`, resume continues
step/seen/schedules/checkpoint numbering, stop at the horizon.

### Training run (RUNNING; `F:\opus_scratch\fable\fb2\train_j1\`, log copy `fable_fb2/j1/logs/train_j1_log.txt`)

Standalone (non-residual) H512, 8 mirrored king buckets, 8 output buckets, factoriser, QAT int16 (FB1 M3), batch
8192, Adam, LR 1e-3 cosine to 5e-5 over 93,000 steps (762M positions, about 10 h at the measured 22.6k positions/s on
one thread), warmup 500 steps, WDL lambda 0.9 -> 0.6 linear, shards sampled proportional to rows, buffer 8 x 250k rows.
Checkpoint every 30 min; stop when exact b0.6 <= target or 3 checkpoints without improvement. Chunks of 240 min.

| ckpt | step | positions | train min | exact b0.6 | b0.8 | b1.0 | vs AL1 0.014417 | parity 10k |
|---|---|---|---|---|---|---|---|---|
| (filled in as checkpoints arrive; see `status.json`) | | | | | | | | |

### Left for J1
Build `forge_fable_v3.exe` (box recipe, OFF identity pins), NPS vs AL1 with the best net, 200 fast sanity games vs
AL1 (crash / illegal-move check only). Done after the training stops.

## J2-J7
Not started yet (in order after J1's training is running).

## Next steps for the next model
1. If the training is still running: `status.json` and `chunks_log.txt` in `F:\opus_scratch\fable\fb2\train_j1\` show
   the state; the driver resumes automatically after a crash; to restart by hand use the command in
   `fable_fb2/j1/README.md` with `--resume F:/opus_scratch/fable/fb2/train_j1/ckpt.pt`.
2. The best net is `best.fnn3` in the run dir; score it on the full 1M-row subset with
   `fable_nnue_train.py score --net best.fnn3 --pos F:/opus_scratch/sol_S31/inputs/prod/holdout_013_014_s16.pos --hce ...hce --phases`
   and compare with AL1's 0.014310.
