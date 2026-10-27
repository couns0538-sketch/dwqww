# train_resid_v3d.py: LR schedule options for train_resid_v3c.py (S-A3 / gate G-A3; UNPROVEN on the PC until CR PASS + crew vote)

- **v3d md5 `e1a092247230996e91507c7149ec9e0a`** (sha256 `c1a42ecda23a79b899231a2796221e9532db11b07e15ee5e85853734c1ba7e5f`).
  Base: opus-sol-S50's `train_resid_v3c.py` (md5 `e7fefe77…` = lock-archive v3b md5 `b6758004` + S39 fixed-size epochs + S50 warm start).
- Diffs: `v3c_to_v3d.diff` (md5 `c1ccfc08c2c7192f5f8a4d1d1256140a`, 134 lines, +65/-5), `v3b_to_v3d.diff`
  (md5 `cd7477c5fdeae7d0d4233f06e4f5699d`, 319 lines, +214/-9).
- Needs `qa_adam_dml.py` (unchanged, sha256 799faa89…) next to it, as v3b.
- All new options default to v3b's schedule: with the defaults v3d gives v3b's lr at every step (bit for bit), v3b's stdout and
  settings dump, and v3b's `.pt/.inc/.bin/.json` bytes.

## v3b's schedule (read first; it stays the default)
- Warmup: `lr * (s+1) / W` for step s < W (`--warmup-steps`, default 300).
- Then a half-cosine over the rest of the run: `lr * (f + (1-f) * 0.5 * (1 + cos(pi * min(pr, 1))))`,
  `pr = (s-W) / max(1, T-W)`, `T` = steps/epoch x `--epochs`, floor `f` = `--min-lr-frac` (default 0.01: the run ends at 1 % of
  the peak lr; the last step is just above it).
- The horizon is the run length, so the shape is tied to `--epochs`; resuming with another `--epochs` re-shapes the curve.

## Changes
1. **`--lr-schedule {cosine,linear,wsd}`** (default `cosine`), in `lr_value()`; `main()`'s `lr_at()` now calls it.
   - `cosine` = v3b's expression, same operations in the same order: the lr Adam receives equals v3b's at every step (tested on
     real runs of both trainers, `float.hex()` equal).
   - `linear`: after the warmup `lr * (f + (1-f) * (1 - min(pr, 1)))`, a straight line from the peak to the floor.
   - `wsd` (warmup-stable-decay): the peak lr until the decay start `D`, then `lr * (f + (1-f) * (1 - min((s-D)/(T-D), 1)))`;
     `D = max(W, T - max(1, round_half_up(F * T)))` (`lr_decay_start()`): at least one decay step, never inside the warmup.
   - Every schedule keeps v3b's warmup and ends exactly at `f * lr` after the horizon.
2. **`--lr-schedule-epochs E`** (default 0 = `--epochs`): horizon `T` = steps/epoch x E (steps/epoch as in v3b/v3c, incl.
   `--epoch-positions`). A run can stop before the horizon (stdout: `…; the run stops at step S of the horizon`) or go past it
   at the floor (`…; the run goes S steps past the horizon at the floor`). With E fixed, a run stopped early and resumed with a
   larger `--epochs` stays on the same lr curve (tested bitwise). The blend ramp still follows `--epochs` (v3b), so a seamless
   extension also needs a constant blend (`--blend-start` = `--blend-end`); otherwise the blend ramp changes at the resume.
3. **`--lr-decay-frac F`** (default 0.2; wsd only): the last F of the horizon decays.
4. **Floor:** no new option: v3b's `--min-lr-frac` already is the floor and now applies to every schedule.
5. **Records (non-default schedule only):** the settings dump lists all three options; the `.json`/`.pt` config gets
   `lr_schedule`, `lr_schedule_steps` (+ `lr_decay_frac`, `lr_decay_start_step` for wsd); stdout gets one `lr schedule: …` line;
   the existing `steps/epoch=… lr=… cosine blend …` line now prints the schedule name (identical text for the default).
6. **Errors** (argparse error before the run dir exists): unknown schedule, `--lr-schedule-epochs` < 0, `--lr-decay-frac` outside
   (0, 1] or not finite, `--lr-decay-frac` without `--lr-schedule wsd`.
7. **Unchanged (tested):** every v3b function/class is source-identical; `main()` from `sc_dev = torch.zeros(...)` to its end
   (training loop, save, final eval) is source-identical. The loop calls `lr_at(step)` as before; per step that is one more
   Python function call and a few float operations (as v3b's inline expression): no tensors, no device scalars.

## PC CPU smoke (2026-10-27; Idle, 1 Torch thread, renamed copies, scratch F:\opus_scratch\sol_SA3)
Recipe: seed 99, 2 epochs, CPU, data32_sample_50k (synthetic; 200,000 train / 50,000 holdout), H64, residual, QAT, bs 1024,
lr 7.07e-4, warmup 20, blend 1.0->0.6, val 16,384, init-check, final-full-val, `--log-every 1e9`; 195 steps/epoch.

| case | result |
|---|---|
| v3d defaults (x2), defaults spelled out, S50 v3c off, v3b (x2) | all 8 artifacts sha256-equal across all of them (ep2 .inc md5 `bf6d2812f517012b269ac25755d4ab4d`); stdout and settings dump equal |
| `--lr-schedule-epochs 2` (= `--epochs`) | .inc/.bin of both epochs and all loss lines = v3b; config records cosine / 390 steps |
| linear (x2) | deterministic (ep2 .inc md5 `0fb0c666f451e2539a03f71296219cce`) |
| wsd (x2) | deterministic (`f48dbeb2471920fa494d64e2825de50e`); decay from step 312 of 390 |
| cosine, horizon 6 epochs (x2) | deterministic (`a124b0e7a0cbdca44ad44a5622c5e5e0`); `the run stops at step 390 of the horizon` |
| resume from epoch 1 (wsd; long cosine) | epoch-2 .inc/.bin/.json sha256-equal, .pt content bitwise-equal |
| extend (stop at epoch 1 of a 2-epoch horizon, resume with `--epochs 2`, constant blend) | epoch 1 .inc/.bin and epoch 2 .inc/.bin/.json/.pt content = the uninterrupted run |
| wsd + `--epoch-positions 100000 --recent-weight 3` + `--init-weights` (x2) | deterministic (`69eea37512f3e2c5613cf635864d57a1`); INIT CHECK OK; wsd over 194 steps, decay from 155; config has all records |
| schedules differ (sanity) | ep2 .inc: v3b `bf6d2812`, linear `0fb0c666`, wsd `f48dbeb2`, long cosine `a124b0e7` |

Holdout loss after 2 tiny epochs on synthetic data (pipeline numbers only, no quality claim): v3b/cosine teacher 0.021902,
linear 0.021902, wsd 0.021932, long cosine 0.021928 (HCE 0.021899).

## Per-step lr traces (unit tests, real in-process runs, H8, 48 steps/epoch, lr 1e-3, warmup 20, floor 0.01)
- The lr each Adam step used (`param_groups[0]["lr"]`, recorded by a wrapper) for every step of: default (= v3b's run, bitwise),
  linear, wsd F=0.3 (round-half-up case 28.8 -> 29), wsd with the decay clamped to the warmup end, each schedule with a 1-epoch
  horizon run for 2 epochs (exactly the floor after it), cosine with a 6-epoch horizon (stopped early), all equal to an independent
  numpy reference (rtol 1e-12; first warmup step exact; wsd stable phase exactly the peak).
- Resume from epoch 1 of a 3-epoch wsd run: the same lr at every later step (bitwise). Extend: a 1-epoch run with a 3-epoch
  horizon + a resume with `--epochs 3` = the uninterrupted 3-epoch run's lr at every step (bitwise).

## 10k-step memory trace (H32, bs 64, 4 x 2,500 steps; private bytes at every ~0.5 s progress line)
| run | slope from step 1000 / after step 2600 | range after step 2600 | changes between samples |
|---|---|---|---|
| v3b | +60.8 / -6.1 B/step | 36 KiB | +1028 KiB in epoch 1, +788 KiB at the first epoch end, then +4 / -36 KiB |
| v3d `--lr-schedule wsd` (decay from step 8,000) | +61.6 / -7.3 B/step | 36 KiB | +784 KiB at the first epoch end, then -36 KiB |

## Proposed gate lines (UNPROVEN; not queued) — `sa3_queue_lines.txt`, dry parse `logs/step07_queue_dryparse.log`
f006 recipe base (H256 residual, lr 7.07e-4, warmup 300, bs 8192, blend 1.0->0.6, seed 25, val 1M, floor 0.01); one schedule
per gate. Data today: 30 train shards, 241,913,894 rows -> 29,530 steps/epoch at bs 8192. GPU time at 1.22M positions/s:

| line | schedule | steps | positions | GPU hours |
|---|---|---|---|---|
| `resid_h256_e48_a3wsd02_lr707e4_b06_s25_bs8k` | wsd, peak until step 1,133,952, decay over the last 283,488 | 1,417,440 | 11,611,668,480 | 2.64 |
| `resid_h256_e48_a3lin_lr707e4_b06_s25_bs8k` | linear to 1 % (lr 3.57e-4 at half) | 1,417,440 | 11,611,668,480 | 2.64 |
| `resid_h256_e64_a3wsd02_lr707e4_b06_s25_bs8k` | wsd over 64 epochs, decay from step 1,511,936 | 1,889,920 | 15,482,224,640 | 3.53 |

Maths: epochs x floor(rows / 8192) x 8192 / 1.22e6 / 3600 (e.g. 48 x 29,530 x 8192 = 11,611,668,480; / 1.22e6 = 9,518 s = 2.64 h);
each extra sealed 10M-row shard adds 0.109 h (e48) / 0.146 h (e64); holdout evals not included. G-A3 srand 958591904 is for the
first G-A3 gate only; a second or third G-A3 gate needs a fresh srand from QA.

## Not done here (UNVERIFIED)
- Any GPU run, real-data loss, strength (no gate), the 1.22M positions/s figure (A7 spec value, not re-measured), the best
  schedule for the H256 net. Never deployed: needs CR PASS + a crew vote, then `train_resid_v3d.py` + `qa_adam_dml.py` copied to
  the trainer tools folder by the crew.
