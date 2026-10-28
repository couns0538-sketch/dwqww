# H512 GPU recipe (for the crew; NOT run by this job)

**Rules:** the crew starts it, never this job. GPU thermal limit ≤ 80 °C (gpu_guard). Never stop or pause the current
training: queue it behind the running run. Needs CR PASS + a crew vote first (CR: "H256 nets are float-only by
crew/Couns rule"; H512 is a new architecture).

## Trainer
`opus_round1/sol_SA2/trainer_v3c_clip.py` (= v3c of opus-sol-S50 + `--weight-clip`, default off). The crew copies it
into the training folder under the name the supervisor expects (e.g. `train_resid_v3c_clip.py`); `--guard-tag
train_resid_v2.py` keeps gpu_guard matching, as in the current runs. `--weight-clip` (bare, K 21704) keeps every export
inside int16 with headroom and makes the net NnueInt16-eligible by construction; it never bound in the smoke runs.

## Queue lines (format of `F:\forge_nnue_train\queue.txt`: `<run-name> [--script X] <args>`; standard args are added)
Primary — from scratch, the current production recipe with `--shape 512`:
```
resid_h512_e48_a4_lr7e4_b06_s512 --script train_resid_v3c_clip.py --shape 512 --epochs 48 --lr 7.07e-4 --blend-end 0.6 --seed 512 --batch-size 8192 --warmup-steps 300 --val-positions 1000000 --weight-clip
```
Optional — warm start from the lock net widened to 512 units (`widen_net_sa4.py --mode zero`: units 0-255 = lock,
256 new units with N(0, 0.02) inputs and zero output weights, so step 0 == the lock net's function; shorter schedule):
```
resid_h512_e16_a4w_lr7e4_b06_s513 --script train_resid_v3c_clip.py --shape 512 --epochs 16 --lr 7.07e-4 --blend-start 0.6 --blend-end 0.6 --seed 513 --batch-size 8192 --warmup-steps 300 --val-positions 1000000 --weight-clip --init-weights <path>\h512_widened_lock_zero.pt
```
(`h512_widened_lock_zero.pt`: sha256 `dffb8100…`, made from the lock net `a7ebcf3a…`; regenerate with
`widen_net_sa4.py --net <lock .inc> --mode zero --out x.inc --pt x.pt`; the CPU smoke case `warm_zero_lr0` (suite w1,
`logs/smoke_compare_w1_warmstart.log`) shows the H512 warm start has the lock's holdout loss at step 0 and exports the
unchanged net after an lr-0 epoch.)

## Expectations (estimates, not measurements on the GPU)
- Time: H256 epochs take ~194 s on the 7900 XT (f071 log: 28,309 steps of 8192). The feature transformer is about
  half of the step cost; H512 is estimated at ~1.5–2× per epoch (~5–7 min), 48 epochs ≈ 4–5.5 h.
- Memory: parameters 0.79 M (H512) vs 0.39 M; Adam state ×3; batch activations [8192, 1024] float32 = 32 MiB. Fits.
- Engine: build with `-DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS='"<net>.inc"'` (or CMake
  `-DFORGE_NNUE_WEIGHTS_FILE=<net>.inc` + `-DFORGE_NNUE_HIDDEN=512` in CMAKE_CXX_FLAGS); then the usual net checks
  (parity: `sa2_parity.py`, 10k FENs), NPS H512 vs H256 at d16/d20, and its own SPRT [0,10] gate G-A4 (srand 507544535).
  No strength claim before that gate.
