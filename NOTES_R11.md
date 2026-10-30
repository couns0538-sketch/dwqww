# R11 notes: automated NNUE pipeline (data -> train -> export -> parity -> bench -> package)

Branch `opus-r11-nnue-pipeline`, base `7f79c349` (qa-r10v2-fix1 = R10 HalfKA + CR fix1; engine source unchanged here).
Job folder `opus_r11/`, GPL trainer-side code in `tools/nnue_pytorch_amd/r11/`. Output root on D:
`D:\grok-pc-data\r11_nnue\` (F: is nearly full). Started 2026-10-30 10:14 PC clock.

## Status
WIP. See "Done" / "Next" below; every push updates this file.

## Facts found at the start (2026-10-30 10:14-10:30)
- Production on the PC: residual trainer (Idle, ~12.5 GB RAM, started 08:14:53 by the supervisor queue), self-play =
  R8 v5 driver `forge_selfplay_fast.exe --workers 5 --cpus 0-15` (Idle) writing into
  `D:\grok-pc-data\selfplay_out_r8v5_20261029` (live: `.part` files), a conc-8 fastchess gate (BelowNormal).
  Free RAM 9.8 GB, CPU 57%, D: 67 GB free, F: 45 GB free.
- The owner's queue already ran an nnue-pytorch adapter job `npt_k32h3_l1024_bs16k_e20x152m5_lam10_s1` (04:29-06:56,
  K32H3^ L1 1024, the R6 clone, guard_exec.py) on binpacks in `F:\forge_j1_data` (J1 conversion 2026-10-29 17:17:
  forge_push shards 001-039, 34 bytes/record, holdout = 013+014, no cross-source dedup, no r8v5 / Astra data).
  Train file 10,370,064,802 bytes = 304,999,573 records (the "~305M"; sum of the per-shard `records=` in
  `F:\forge_j1_data\convert.log`; the merged file is the byte concatenation of the shard binpacks), holdout
  557,215,814 bytes = 16,388,575 records.
- `selfplay_out` holds only text; its sealed shards are converted 1:1 by the supervisor to
  `D:\grok-pc-data\forge_push\nnue_data\pos\*.pos` + `hce\*.hce` (HCE = Forge 1ab50b2d evaluate_uncached). Those pairs
  are the pipeline's input for that source. r8v5 has `.dedup.pos` (final when `.dedup.json` exists) but no `.hce`.
- Astra's set (release astra-a1-data-results-20261030): 9,206,371 rows filtered from `forge_selfplay_003.pos`
  (same boards/scores; FPOS + matched FHCE + full-FEN sidecar). It is a filtered copy of forge_push shard 003, so the
  pipeline uses it IN PLACE OF shard 003 ("supersedes"), not as an extra source.
- Trainer (R6 clone `F:\opus_scratch\r6\nnue-pytorch-amd`, b2614500 + 3 AMD commits) has its own SimpleTrainer:
  `--resume-from-checkpoint`, `--save-top-k` (keeps newest k periodic, but only those saved by the current process),
  `--validation-datasets`. The epoch-end checkpoint is written BEFORE that epoch's validation and stores
  epoch=E; resuming restarts at epoch E (one epoch trained twice).

## Done
- (nothing pushed yet beyond this file)

## Next
1. Data stage (inventory, global dedup, holdout, C++ binpack writer, side-car .hce, manifests).
2. Train stage wrapper (resume, rotation last 2 + best, governor), export, check stage, package, one command.
3. Self-test; real conversion; end-to-end net; skills; review.

## How to resume (for someone else)
- Worktree: `git worktree add <dir> origin/opus-r11-nnue-pipeline`; read this file, then `opus_r11/README.md`.
- PC rules: `.claude/skills/forge-pc-rules/SKILL.md` (BelowNormal, <= 3 threads, never touch production / gates /
  queue_state.json / locks, never delete existing files, never type the production trainer's script name).
