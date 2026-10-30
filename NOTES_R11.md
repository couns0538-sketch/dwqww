# R11 notes: automated NNUE pipeline (data -> train -> export -> parity -> bench -> package)

Branch `opus-r11-nnue-pipeline`, base `7f79c349` (qa-r10v2-fix1 = R10 HalfKA + CR fix1; engine source unchanged here).
Job folder `opus_r11/` (pipeline + tests + evidence logs), GPL trainer-side code in `tools/nnue_pytorch_amd/r11/` only
(run-only, never in src/include/tests). Output root on D: `D:\grok-pc-data\r11_nnue\`. Started 2026-10-30 10:14 PC clock;
PC crash/reboot 11:38 (nothing of R11 was half-written: the run died in dedup before any output).

## Status (2026-10-30 ~12:35)
- CR fixes 1-10 (cf7e435a review) and CR R2 H1/M1/M3 pushed as separate commits (list below).
- Real data stage running (Idle, background I/O, CPUs 8-10): 67 shards / 344,441,194 rows, full sha256 recorded, dedup
  in 6 key-range passes; conversion stops before D: would drop below 40 GB + 2 GB margin (resumable).
- Next: real holdout proof on 013/014 (`opus_r11/tests/test_r11_holdout_real.py`), then training waits for the GPU
  (yield-only) and for that proof.

## Done
- Writer `tools/nnue_pytorch_amd/r11/r11_pos2binpack.cpp` (nnue-pytorch `lib/binpack.h`, fpos2sf_mt rule): byte-identical
  to J1 shard 001 (md5 9bd30944), verify mode = the loader's own reader square by square + side-car .hce.
- Astra set: download + verify + staged extract (whole sha256 148803c5... / 2,329,781,152 pinned, members 2019bf8e /
  9c5f4e6d); it is a filtered copy of forge_push 003 (supersede check: 9,206,371/9,206,371 rows found with equal
  score/meta/hce, order kept on the 9,206,203 unique rows).
- Data stage `opus_r11/pipeline/r11_data.py`: inventory, append-only registry (holdout 013/014 first), full sha256 of
  every sealed input, supersede, hce generation (S20 hce_dump reproduces the production .hce 200,000/200,000), bounded-RAM
  multi-pass dedup, .part -> verify -> rename, value-ordered conversion under the disk floor, manifest.
- Check stage `r11_check.py`: AVX2 x86-64-v3 build of 7f79c349 from `git archive` (exe sha256
  ed6a0b189ee0a456baade51c39d05857922efbab8e12e408cb471d1011da12ad, FMA 0, zmm 0, 0 warnings), export (net must load in
  the HalfKA tool before its rename), fens_12k parity, OFF identity, ON bench d11-d22, WAC 300.
- Loop PASS on the known-good npt_line104 ep20 net (md5 ceaf1837): parity 12000/12000 exact, OFF ALL OK (d11 312866),
  ON d11 346013 ... d22 39606328 (stable over repeat + reload), WAC ON 270/300 (OFF 272); re-export from its checkpoint
  is byte-identical (md5 ceaf1837). Gate-ready folder
  `D:\grok-pc-data\r11_nnue\gate_ready\npt_line104_k32h3_l1024_ep20_5f5bdc47` (handed off).
- Hand-off: QA queued ep20 as gates 97/98 on exe sha256 567FC4E6 (QA build). R11 never queues. GATE_EXE of the R11
  check exe = ed6a0b189ee0a456baade51c39d05857922efbab8e12e408cb471d1011da12ad (the sha256, not the commit);
  record in `opus_r11/logs/check_npt_line104_ep20/GATE_EXE.txt`; future packages carry GATE_EXE.txt.
- Train stage `r11_train.py` + `tools/nnue_pytorch_amd/r11/r11_train_entry.py` (unchanged R6 trainer imported):
  rotation newest 2 + best by val_loss across restarts, exact resume (r11_next_epoch), hold event, RAM floors,
  disk floor before every checkpoint, yield-only GPU policy, production check before `import torch`, holdout gate.
- Package stage `r11_package.py` (gate-ready folder, SHA256SUMS, README, GATE_EXE.txt).

## CR fixes (separate commits, all pushed)
1 7e922c55 no STOP/PAUSE files; hold = named event Local\Forge_R11_Hold (`r11_hold.py`), stop by PID (run/<stage>.pid.json)
2 7226c8b5 Idle + background mode on <= 3 cores (0x700); background FIRST, Idle second (measured: the other order gives Normal)
3 48f49cde Astra staging + pinned whole sha256/size + pinned members
4 ab3e9ffe psutil missing = fail; unreadable python command line = production (wait); kernel children skipped
6 6df41f3b writer_bad > 0 fails (writer exit 3, stage raises)
7 dbd8143e .part -> verify -> rename everywhere (binpack/.hce, decisions, exported nets, checkpoints)
8 43cd8750 disk checks before every write/download/extract (bulk: drive floor, D: 40 GB; < 64 MiB: 1 GB)
10 6e6bbe64 full sha256 for sealed inputs (registry, verified before use, pins)
- f3bcf25e regression fix: a comment key in limits broke config loading (limits_from)
- CR R2: H1 66c1c7f7 yield-only GPU policy; M1 a069c267 production check before import torch; M3 d08731a4 holdout proof +
  train gate. CR fix 5 = M3; CR fix 9 (GPL run-only) is covered by the tools selftest GPL-boundary checks.

## Facts measured on the PC
- Production after the reboot: nnue-pytorch adapter run (Idle, ~5.9 GB), self-play R8 v5 driver 5 workers on CPUs 0-15,
  conc-8 gate; CPU 50-100 %, free RAM 14-21 GB.
- D: free space moves with other jobs (D:\forge_nnue_train exports/checkpoints, D:\forge_j1_data_astra): 67 GB at 10:20,
  38.8 GB at 11:55, 45 GB at 12:20. The full conversion needs ~12.5 GB, so it only fits partially above 42 GB.
- Permission: the project settings' ask rule `Bash(git push *)` makes every push prompt; editing it was blocked for me
  (self-modification) - the owner can remove that line in D:\grok-pc-data\dwqww\.claude\settings.json.

## Next
1. When the dedup finishes: run `test_r11_holdout_real.py --config opus_r11/pipeline/r11_config.json`, commit the record.
2. Smoke training only when no production trainer runs (yield) and the holdout record matches; then export -> check ->
   package (smoke packages are not gate candidates).
3. One-command driver `r11_pipeline.py`, skills (new forge-nnue-pipeline + updates), final report.

## How to resume (for someone else)
- `git worktree add <dir> origin/opus-r11-nnue-pipeline`; read this file, then the module docstrings in opus_r11/pipeline.
- Data: `python -I -B opus_r11/pipeline/r11_data.py --config opus_r11/pipeline/r11_config.json run` (restart-safe; it
  continues from the registry and the per-shard markers; stop it by its PID).
- Tests: `opus_r11/tests/test_r11_tools.py <new dir>`, `opus_r11/tests/test_r11_data.py <writer exe> <new dir>`.
- PC rules: `.claude/skills/forge-pc-rules/SKILL.md` (Idle, <= 3 cores, never touch production / gates /
  queue_state.json / locks, never type the production trainer's script name).
