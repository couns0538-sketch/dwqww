# train_resid_v3c.py: fixed-size epochs (S39) + warm start `--init-weights` (S50) for train_resid_v3b.py (UNPROVEN on the PC until CR PASS + crew vote)

- **v3c md5 `e7fefe7772fcf629f3b8f7a2a6e05241`** (sha256 `ddff28bb6801421793e1767cec8271fe3406a263b0c0dfec03ac0cd97dcadef8`): this
  file supersedes the S39-only v3c (`../sol_S39/train_resid_v3c.py`, md5 `b130a31e…`); the S39 code is unchanged in it.
  Base: v3b md5 `b6758004d19837c8d34d401ee7af5fd5` (lock archive `5_nnue/trainers/cpu_smoke/train_resid_v3b.py`).
- Diffs: `v3b_to_v3c.diff` (md5 `784a204c58c9ea6236946664c5a66e96`, 236 lines, +149/-4) and the S50 increment
  `v3c_s39_to_s50.diff` (md5 `c4720b34afbd6d69550e8ee4b567d215`, 128 lines, +64/-2).
- Needs `qa_adam_dml.py` (QA's file, unchanged, sha256 799faa89…) next to it, as v3b. The `--guard-tag` line is unchanged.
- All three new options default OFF. Off = v3b: same code path, same stdout, same settings dump, same `.pt/.inc/.bin/.json` bytes.

## Why
- S39: a v3b epoch is all data; the PC's sealed self-play grows by ~1.76M positions/h, so steps/epoch, run time and the lr/blend
  schedules change with the data size and later runs are not comparable.
- S50: e48 beats e32 so far (G104 +29.4 vs e32 +8.3/+9.5/+23.6, spec numbers), but e64/e96 from scratch cost 2-3x GPU time.
  Continuing a finished e48 net for +16-32 epochs on a fresh schedule tests "longer" for about a third of the cost.

## Changes
1. **`--epoch-positions N` (S39, default 0 = off)**: each epoch trains on N positions drawn with the epoch's seeded RNG
   (`default_rng(seed*1000+epoch)`, v3b's own), no repeats within an epoch; steps/epoch = `N // batch` (then `--steps-per-epoch`
   caps it). Uniform draw = the first N entries of v3b's own epoch permutation, so `N >= train size` is v3b exactly (one info line).
2. **`--recent-weight W` (S39, default 1.0 = uniform; needs `--epoch-positions`)**: per-position file weight linear in the file's
   rank in the sorted file list (1.0 first file, W last; on the PC rank = generation of `forge_selfplay_NNN`). Per-file quotas =
   exact share `N * rows * weight / sum(rows * weight)` (largest remainder, water-filling caps at the file's rows, exact rational
   arithmetic); per epoch an in-place shuffle of each file's rows in the reused int32 buffer, compaction in <= 2^24-row chunks,
   one shuffle of `buf[:N]` (files interleaved).
3. **`--init-weights PATH` (S50, default off)**
   - Loads the model weights only (`load_init_weights()`): a trainer `.pt` payload (`model` key) or a bare state_dict,
     `torch.load(..., weights_only=True)` as v3b's resume. Optimizer state, step and epoch are not taken: Adam starts empty, the
     step counter at 0, lr warmup + cosine and the blend ramp run over the new run's `--epochs`/`--warmup-steps`/`--blend-*`
     (pass `--blend-start` = the source's `--blend-end` to keep its final target mix).
   - Refused before training: another hidden size or residual mode (`ValueError`), any other shape mismatch (strict
     `load_state_dict`), non-finite weights; a missing file is an argparse error before the run dir is created (a stale empty run
     dir would make the supervisor skip the launch). A QAT mismatch prints a WARNING.
   - Provenance: the file's md5 goes to the settings dump (`init_weights_md5`, with the `init_weights` path), to the `.json`/`.pt`
     config (`init_weights_md5`) and to stdout (`init-weights: model weights from … (md5 …; checkpoint hidden=… residual=…
     next_epoch=… step=…); optimizer, lr and blend schedules start fresh`).
   - `--init-check` with a warm start: the loaded net's holdout-subset loss must equal the checkpoint's stored `val` (same 1e-6
     tolerance as v3b's check) -> `INIT CHECK OK (warm start == checkpoint val)`, else `INIT CHECK FAILED …` and exit code 3
     (as v3b). It needs the source run's `--holdout` and `--val-positions`: the supervisor adds the same 013/014 holdout to every
     line and `--init-check` to every fresh launch, so a warm-start queue line must keep the source line's `--val-positions`
     (default 4M). A bare state_dict has no val: the check is skipped with a note. Without `--init-weights`, v3b's check runs
     unchanged.
   - `--resume` wins: the supervisor relaunches a run with the queue line's args + `--resume <last .pt>`, so a resumed warm start
     still carries `--init-weights`; v3c then does not load it (`init-weights … not loaded, --resume restores model and
     optimizer`), and a missing init file is recorded as md5 `missing` instead of failing the resume.
4. **Settings dump / config**: the v3c options are written to the settings dump only when set (off -> v3b's dump, byte-identical
   apart from the script path and run dir); `epoch_positions`/`recent_weight` go into the config only when fixed-size epochs are
   active, `init_weights_md5` only with `--init-weights`.
5. **Unchanged (tested)**: all 24 v3b functions/classes other than `main` are source-identical, and `main` from
   `sc_dev = torch.zeros(...)` to its end (training loop, save, final eval) is source-identical: no per-step code changed.

## RAM
- `--epoch-positions`: no new array of size N (v3b's reused int32 buffer; <= 64 MiB compaction chunks); O(files) lists.
- `--init-weights`: the checkpoint payload is loaded once at start (model + optimizer state of the source, ~3x the model size:
  ~7 MB for H256) and dropped after copying the weights.
- Measured peaks of ON runs equal to v3b within run-to-run noise (S39; S50 r1 worst ON excess +0.83 MiB of ~240 MiB, inside the
  1 MiB tolerance).

## PC CPU smoke (2026-10-27; Idle, 1 Torch thread, renamed copies, scratch F:\opus_scratch\sol_S50)
Recipe as S39: seed 99, 2 epochs, CPU, data32_sample_50k (synthetic; 200,000 train / 50,000 holdout), H64, residual, QAT, bs 1024,
lr 7.07e-4, warmup 20, blend 1.0->0.6, val 16,384, init-check, final-full-val, `--log-every 1e9`. Warm-start source = the v3b run's
epoch-2 checkpoint (`epoch002-step000000390.pt`, md5 `5bd3de20e55b292b593307c8d987a983`).

| case | result |
|---|---|
| all S39 cases on this file (off x2, N = / > data size, ON x2 uniform and weighted, order-buffers 2, resumes) | 17/17 S39 checks PASS; artifacts byte-identical to the S39 file's runs for all 11 shared cases |
| (a) options off vs v3b | 8 artifacts sha256-equal, whole stdout and settings dump equal |
| (b) `--init-weights <ep2 .pt> --lr 0 --epochs 1` | .inc md5 `bf6d2812f517012b269ac25755d4ab4d` = the checkpoint's .inc; .bin equal; EPOCH 1/1 holdout part = the checkpoint's EPOCH 2/2 (`mse_teacher=0.021902 … mse_b0.6=0.045335 … mse_b0.8=0.023798`); .json val equal at full precision; FINAL line equal; INIT `0.021902/0.045335` = checkpoint val |
| (b) same + `--epoch-positions 100000 --recent-weight 3` | same .inc md5 and loss lines (97 steps/epoch) |
| warm start, normal lr (x2) | deterministic (ep2 .inc md5 `7168e53066deac79d4c376379de6f719`); epoch-1 checkpoint step 195 and Adam step 195 (source: 390): fresh optimizer and schedule (195 steps/epoch, 390 total) |
| (d) warm start + `--epoch-positions 100000 --recent-weight 3` (x2) | deterministic (ep2 .inc md5 `9059c1382a4b61e2e473eaa3c8d395fb`); INIT CHECK OK; 97 steps/epoch; config has epoch_positions, recent_weight, init_weights_md5 |
| supervisor-style resume of a warm start (same args + `--resume`) | epoch-2 .inc/.bin/.json equal, .pt content bitwise-equal; init file not loaded |
| provenance | md5 in the settings dump, the .json/.pt config and stdout |

Synthetic data, 2 tiny epochs: pipeline numbers only; the warm runs' higher holdout loss on this data says nothing about real data.

## 10k-step memory trace, (c) (H32, bs 64, 4 epochs x 2,500 steps; private bytes at every ~0.5 s progress line)
| run | slope from step 1000 / after step 2600 | range after step 2600 | changes between samples |
|---|---|---|---|
| v3b `--steps-per-epoch 2500` | +60.3 / -6.2 B/step | 36 KiB | +784 KiB at the first epoch end, then -8/+8/+4/-36 KiB |
| v3c `--init-weights <v3b trace ep4> --epoch-positions 160000 --recent-weight 3` | +70.8 / -6.1 B/step | 36 KiB | +788 KiB at the first epoch end, then -36/+4 KiB |
- Flat per step in both (the warm run's INIT CHECK OK too). For scale: v3b's DirectML leak was ~24 KB/step.

## Not done here (UNVERIFIED)
- A warm start from a finished PC run's `.pt` (e.g. an e48 net), DirectML/GPU, real data, the e48 + 16-32 epoch experiment
  itself and any strength effect. Never deployed: needs CR PASS + crew vote, then `train_resid_v3c.py` + `qa_adam_dml.py` in the
  trainer tools folder.
