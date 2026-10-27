# IDEA_SOURCE — S39 v3b trainer fixed-size epoch option (v3c)

- **Spec:** Sol's S39 (`17aa0cae:validation/forge_sol_pack31_20261025/forge_sol_all_jobs_recovery_20261026/forge_sol_all_jobs_inventory_20261026.json`,
  copy `F:\opus_scratch\sol_inventory_17aa0cae.json`, `jobs[]` id S39, NOT_STARTED; spec line 206) and
  `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 21. Sol left no S39 files on his branch (`git ls-tree 17aa0cae | grep -i -E "S39|v3c"`: none).
- **Base:** the lock archive's v3b trainer `5_nnue/trainers/cpu_smoke/train_resid_v3b.py` (md5 b6758004, sha256 5cebba4d…,
  the file named in `CHANGES_v3b.md`) with `qa_adam_dml.py` (799faa89…). The spec's path `files/07_nnue_context/train_resid_v3b.py`
  is Sol's packaging name for the same trainer; the lock archive copy is the one opus-sol-S18/S30 used.
- **Reason (from the spec):** the PC's sealed self-play data grows by ~1.76M positions/h, so a v3b epoch (= all data) grows with
  it: later runs get longer and their lr/blend schedules (which depend on steps/epoch) are not comparable.
- **Method:** fixed-size epochs = a seeded sample without replacement each epoch (standard "epoch = N samples" practice in
  large-data training loops, e.g. PyTorch `RandomSampler(replacement=False, num_samples=N)` semantics; no code copied). The uniform
  draw is the first N entries of v3b's own per-epoch permutation (`default_rng(seed*1000+epoch)`), so N >= data size is v3b
  exactly. `--recent-weight` uses per-file quotas proportional to rows x weight (largest-remainder rounding, the Hamilton
  apportionment method, with water-filling caps), a uniform draw inside each file, then one shuffle. Own code.
- No engine code, no engine option, no GPU/PC training run, no queue change: tool-only job.
