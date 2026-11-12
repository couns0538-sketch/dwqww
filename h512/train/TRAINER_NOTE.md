# JOB E trainer note (own; replaces Engine NNUE's v3 pack, which was not available)

`TRAINER_NOTE_v3` (md5 `0fdc8755...`) and `h512_stage1_config_v3` (md5 `1691ca5b...`) were named in the brief. They are not
on the PC and the owner does not have them, so nothing here was checked against them. This note and
`stage1_config.json` are this job's own.

## What is trained

FB1/FB2's standalone net, unchanged: FORGENN3, hidden 512, 8 mirrored king buckets (`king_layout(8)`), 8 output
buckets by piece count, SCReLU on both perspectives, int16 inference (QA 255, QB 64, eval scale 400).
Quantization-aware training as in FB2: the forward pass uses weights rounded to the engine grid with a
straight-through gradient; a 768 x 512 factoriser shared by the king buckets is added to each bucket and merged at
export. After every step the parameters are clipped to the exportable ranges.

## Trainer

`train_h512_gpu.py` runs in the ROCm venv `F:\nnue_pytorch\venv` (torch 2.11.0+rocm7.13.0, Triton 3.6.0).

| Part | Source |
|---|---|
| Model, clipping, exporter, FPOS reader, numpy reference scorer | `fable_nnue_train.py`, `fable_nnue_v3.py` from branch `fable-fb2-j1` (copied unchanged) |
| Feature transformer forward/backward on the GPU | R7 `forge_v2_kernels.py` (GPL-3.0), imported from `D:\grok-pc-data\dwqww\.claude\worktrees\opus-r7-speed\tools\nnue_pytorch_amd\forge_v2`, md5 `916539cef784f791d7d3ed91e61e05f1`. Not copied into this repository |
| 8 king buckets | The kernel takes a lookup table. This trainer computes Forge indices for FB2's 8-bucket layout itself and passes an identity table, so no change to the kernel was needed |
| Data path, schedule, checkpoints, integer scorer, holds | new in `train_h512_gpu.py` |

### Data and sampling

- All 271,830,023 training rows (FB2's 64 shards) are held on the GPU: 32 board bytes, int16 score, one meta byte per
  row, about 9.5 GB of the 20 GB.
- One epoch is one permutation of all rows, `numpy PCG64([seed, epoch]).permutation(rows)`. Every row is presented
  exactly once per epoch, so sampling is row-weighted with no shard bias. FB2's CPU trainer already sampled shards in
  proportion to their rows (`--shard-weighting rows`), so the repository had fixed the shard bias before this job.
- The data position is (epoch, offset) and is stored in every checkpoint.

### Target

`target = (1 - alpha) * sigmoid(score * 2.25 / 400) + alpha * result`, with `score` the stored search score in
centipawns from the side to move, clamped to +-40 after scaling, and `result` 1 / 0.5 / 0 from the side to move.
Prediction: `sigmoid(cp * 2.25 / 400)` with `cp` the net output in centipawns. Loss: mean squared error.
FB2's "blend b" equals `1 - alpha`.

### Schedule

A plan file lists stages. Each stage is 500 warm-up steps and a cosine from the peak learning rate to 5 % of it,
ending at a cumulative number of presentations. Adam (default betas), batch 8192, as FB2.

### Checkpoints

`latest.pt` holds model, Adam state, stage and step, epoch and offset, torch CPU and GPU generator states, and the
plan. Written to a temporary file, synced, then renamed. `best.pt` and `stage_<name>.pt` are copies at those points.
Every checkpoint also exports `net_seen<presentations>.fnn3` and scores it.

Resume was tested (`results/step2/`): the data order after a resume is identical; the arithmetic is not bit-exact
between runs because the kernel's backward pass adds with atomics (final selection loss differed by 3e-7).

### Scoring

Exported nets are scored with an exact integer forward on the GPU (the engine's arithmetic, truncating divisions,
float64 loss). On the FB2 200k holdout it equals FB2's numpy scorer to 1.7e-18 and equals the engine on 14,000
positions (`results/step3/parity_fb2_step93000.json`).

### Holds

The trainer runs outside the owner's guard matching, as the owner chose on 10 November. It reads the same sensor
feeds and pauses at GPU hot spot >= 76 C or memory junction >= 86 C (resume at <= 72 / <= 83), throttles in between,
pauses without a fresh feed (after 300 s: half duty), and pauses while C:, D: or F: has under 20.5 GiB free.

## Environment note

`venv\Lib\site-packages\_rocm_sdk_devel\include` denies access to this account (2026-11-11). Triton compiles a small
HIP helper and needs `hip/hip_runtime.h`. The trainer adds the readable `_rocm_sdk_core\include` to Triton's
include list inside its own process. No file or permission of the installation was changed.

## Commands

```
source h512/train/env_h512.sh
$PY -I -B h512/train/train_h512_gpu.py selfcheck --pos <holdout.pos> --ckpt <fb2 ckpt.pt> --net <best.fnn3>
$PY -I -B h512/train/make_splits.py --out-dir _work/data --manifest h512/manifests/splits_manifest.json
bash h512/train/run_pilots.sh          # six pilot arms, restartable
bash h512/train/run_main.sh            # staged run from stage1_config.json, restartable (--resume)
$PY -I -B h512/train/train_h512_gpu.py score --net <net.fnn3> --pos _work/data/select_2m.pos
```
