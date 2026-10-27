# train_resid_v3c.py: fixed-size epochs for train_resid_v3b.py (S39; UNPROVEN on the PC until CR PASS + crew vote)

- **v3c md5 `b130a31ed30e9a92f9fff8806d0eb847`** (sha256 `5f54458e4df331bda1c2a106fa887b5e21afc9e2fea412f5361b41c51ab9efe4`).
  Base: v3b md5 `b6758004d19837c8d34d401ee7af5fd5` (lock archive `5_nnue/trainers/cpu_smoke/train_resid_v3b.py`).
- Unified diff: `v3b_to_v3c.diff` (md5 `a192d5ff89403b628e42ffd66daddcab`, 154 lines, +86/-3 lines).
- Needs `qa_adam_dml.py` (QA's file, unchanged, sha256 799faa89…) next to it, as v3b. The `--guard-tag` line is unchanged.
- Both new options default OFF. Off = v3b: same code path, same stdout, same settings dump, same `.pt/.inc/.bin/.json` bytes.

## Why (S39 spec)
- The PC's sealed self-play grows by ~1.76M positions/h. A v3b epoch is all data, so steps/epoch, the run time and the lr
  (warmup + cosine over `steps/epoch x epochs`) and blend schedules change with the data size: later runs are not comparable
  and get slower. The supervisor also re-expands `--train` on a resume, so v3b's steps/epoch can change mid-run.

## Changes
1. **`--epoch-positions N` (default 0 = off)**
   - Each epoch trains on N positions drawn from all training files with the epoch's seeded RNG
     (`default_rng(seed*1000+epoch)`, v3b's own per-epoch seed), no repeats within an epoch. steps/epoch = `N // batch`
     (tail dropped as in v3b), then `--steps-per-epoch` still caps it.
   - Uniform draw = v3b's own shuffle of the reused int32 order buffer, then the first N entries. So the fixed-size epoch is the
     prefix of v3b's epoch permutation, and `N >= train size` is v3b exactly (one info line is printed:
     `epoch-positions N >= train M: full epochs (v3b order)`).
   - `0 < N < batch` and `N < 0` are rejected before the run dir is created.
2. **`--recent-weight W` (default 1.0 = uniform; needs `--epoch-positions`)**
   - Per-position weight per training file, linear in the file's rank in the trainer's sorted file list: 1.0 for the first,
     W for the last (`recent_weights()`). With the supervisor's default `--train` (all `forge_selfplay_NNN.pos` except the
     013/014 holdout, sorted by name) rank = generation, so W > 1 favours newer self-play. A file sorting after them (e.g. an
     explicit `sol_indep_train.pos` on a queue line) would get the top weight: keep W = 1 for mixed sources.
   - Per-file quotas (`epoch_quotas()`): exact share `N * rows * weight / sum(rows * weight)` with largest-remainder rounding
     (ties -> lower file index), a file whose share reaches its row count is capped at it and the rest is re-split
     (water-filling). Exact rational arithmetic (`fractions.Fraction` of the float weights). The plan is printed once:
     `epoch-positions per file (weight drawn/rows): ...`.
   - Per epoch (`draw_weighted()`): each file's rows are shuffled in place inside the reused buffer, the first `quota` rows are
     compacted to the front (chunks of <= 2^24 rows, like v3b's arange fill), then `buf[:N]` is shuffled once so files are
     interleaved. Uniform without repeats inside each file; inclusion probability per position = quota / rows of its file.
   - W <= 0 / NaN / inf, or W != 1 without `--epoch-positions`, are rejected before the run dir is created.
3. **Settings dump / checkpoint config**: the v3c options are written to `settings_<t>.txt` only when set (off -> v3b's dump,
   byte-identical apart from the script path and run dir). `epoch_positions` and `recent_weight` go into the `.json`/`.pt`
   config only when fixed-size epochs are active (N < train size).
4. **Unchanged (tested)**: every v3b function/class other than `main` is source-identical (24 definitions); `main` from
   `sc_dev = torch.zeros(...)` to its end (training loop, save, final eval) is source-identical. So no per-step code changed:
   the draw runs in the existing background `EpochPrep` thread at epoch boundaries.

## RAM
- No new array of size N: the uniform path is v3b's shuffle of the same reused int32 buffer(s); the weighted path shuffles each
  file's slice in place and compacts in <= 2^24-row chunks (<= 64 MiB temporary, the size of v3b's existing arange chunk).
  New state is O(files) Python lists. `--order-buffers 2` and `--mmap-data` work unchanged (order-buffers 2 tested).
- Measured (CPU smoke below): peak private / peak working set of ON runs equal to v3b within run-to-run noise
  (v3b 238.7-239.2 / 241.5-241.9 MiB; ON 238.1-239.5 / 241.2-242.4 MiB over runs r1+r2; mean ON 238.9 vs v3b 238.9 MiB private).

## PC CPU smoke (2026-10-27; Idle priority, 1 Torch thread, renamed copies, scratch F:\opus_scratch\sol_S39)
Recipe: seed 99, 2 epochs, CPU, data32_sample_50k (4 x 50,000 train, h000 50,000 holdout; synthetic), H64, residual, QAT,
bs 1024, lr 7.07e-4, warmup 20, blend 1.0->0.6, val 16,384, init-check, final-full-val, `--log-every 1e9` (no wall-clock
dependent loss syncs). v3b: 195 steps/epoch. `--epoch-positions 100000`: 97 steps/epoch.

| case | result |
|---|---|
| v3c, options off (x2) vs v3b | all 8 artifacts (.pt .inc .bin .json x 2 epochs) sha256-equal; full stdout equal (timing fields and MEM lines masked); settings dump equal |
| `--epoch-positions 200000` (= N) and `10000000 --recent-weight 3` | 8 artifacts sha256-equal to v3b; stdout equal apart from the one info line |
| `--epoch-positions 100000` (x2) | deterministic (8 artifacts equal; ep2 .inc md5 `2cfbdee79f730f883dff0e2048c49b51`); steps/epoch=97, `Finished: 198,656 positions` |
| `--epoch-positions 100000 --recent-weight 3` (x2) | deterministic (ep2 .inc md5 `317f0dcaf6990764230686844c4f344e`); quotas 12,500/20,833/29,167/37,500 of 50,000 per file |
| same with `--order-buffers 2` | 8 artifacts equal to `--order-buffers 1` |
| resume from epoch 1 (uniform, weighted, and v3b itself) | epoch-2 .inc/.bin/.json sha256-equal and .pt content bitwise-equal to the uninterrupted run (.pt bytes differ in v3b too: pickle memo, see REPORT finding) |
| r1 vs r2 (separate suite runs) | all 11 common cases: artifacts identical |

Loss lines (holdout subset n=16,384; HCE 0.021899 / 0.045332):
- v3b / off: EPOCH 2 mse_teacher 0.021902, b0.6 0.045335; FINAL full 0.021846 / 0.045543 / 0.023712.
- uniform N=100k: EPOCH 2 0.021899 / 0.045330; FINAL 0.021842 / 0.045539 / 0.023709.
- recent-weight 3: EPOCH 2 0.021901 / 0.045330; FINAL 0.021842 / 0.045538 / 0.023709.
- Synthetic data, 2 tiny epochs: pipeline numbers only, no quality claim.

## 10k-step memory trace (H32, bs 64, 4 epochs x 2,500 steps; private bytes sampled at every progress line, ~0.5 s)
| run | trace t1: slope from step 1000 / after step 2600 | trace t2 | changes between samples |
|---|---|---|---|
| v3b `--steps-per-epoch 2500` | +88.0 / -6.6 B/step | +56.7 / -7.1 B/step | +1024 KiB once in epoch 1, +784 KiB at the first epoch end, -36 KiB at the third |
| v3c `--epoch-positions 160000 --recent-weight 3` | +65.1 / -6.8 B/step | +67.4 / -7.1 B/step | the same steps (+1024, +784, -32/-36 KiB) |
- Flat per step in both: after the first epoch's eval/save the private bytes stay within 36-72 KiB for 7,400 steps.
  For scale: v3b's DirectML leak was ~24 KB/step (~240 MB per 10k steps); CPU cannot show that leak (CHANGES_v3b.md).

## Not done here (UNVERIFIED)
- DirectML/GPU run, real 137M-position data, draw time at that scale (uniform = v3b's shuffle cost; weighted = one in-place
  shuffle per file + compaction + one shuffle of N), effect on net strength. Never deployed: needs CR PASS + crew vote, and
  `train_resid_v3c.py` + `qa_adam_dml.py` copied to the trainer tools folder by the crew.
