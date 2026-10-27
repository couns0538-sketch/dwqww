# IDEA_SOURCE — S50 trainer warm-start `--init-weights PATH` (v3c, default OFF)

- **Spec:** Sol's S50 (`17aa0cae:validation/forge_sol_pack31_20261025/forge_sol_all_jobs_recovery_20261026/forge_sol_all_jobs_inventory_20261026.json`,
  copy `F:\opus_scratch\sol_inventory_17aa0cae.json`, `jobs[]` id S50, NOT_STARTED, depends on S39; spec line 265) and
  `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 31. Sol left no S50 files on his branch.
- **Base:** the S39 v3c (`opus-sol-S39` @ `093869a2`, `opus_round1/sol_S39/train_resid_v3c.py`, md5 b130a31e), itself the lock
  archive's v3b (md5 b6758004) + fixed-size epochs. The spec asks for the same file (`train_resid_v3c.py`).
- **Reason (from the spec):** e48 beats e32 so far, e64/e96 from scratch cost 2-3x GPU time; continuing a finished net on a fresh
  schedule tests "longer" for about a third of the cost.
- **Method:** standard warm start / fine-tuning practice: copy the parameters, start a new optimizer and lr schedule (as in
  PyTorch's `load_state_dict` without the optimizer's state). Loading uses `torch.load(weights_only=True)` like v3b's own
  `--resume`. The `--init-check` reuse (loaded net must reproduce the checkpoint's stored holdout val) and the
  `--resume`-wins rule follow from the PC supervisor's launch rules (`Build-Args`: `--init-check` on fresh launches, queue args +
  `--resume` on relaunch; read from `F:\forge_nnue_train\tools\nnue_supervisor.ps1`, read only). Own code.
- No engine code, no engine option, no GPU/PC training run, no queue change: tool-only job.
