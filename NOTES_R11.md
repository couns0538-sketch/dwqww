# R11 notes: automated NNUE pipeline (data -> train -> export -> parity -> bench -> package)

Branch `opus-r11-nnue-pipeline`, base `7f79c349` (qa-r10v2-fix1 = R10 HalfKA + CR fix1; engine source unchanged here).
Job folder `opus_r11/` (pipeline + tests + evidence logs), GPL trainer-side code in `tools/nnue_pytorch_amd/r11/` only
(run-only, never in src/include/tests). Output root on D: `D:\grok-pc-data\r11_nnue\`. Started 2026-10-30 10:14 PC clock;
PC crash/reboot 11:38 (nothing of R11 was half-written: the run died in dedup before any output).

## Status (2026-10-30 ~13:00)
- CR fixes 1-10 (cf7e435a review) and CR R2 H1/M1/M3 pushed as separate commits (list below).
- **CR fix 2 amendment (for CR re-review):** background mode is gone - it capped every R11 process at a 32 MB working
  set (details and numbers under "Facts"). Now: Idle + I/O priority very low + memory priority low + mask 0x700, all
  inherited by children; test 1e checks the values, the inheritance, the missing cap and that no code enters
  background mode.
- Real data stage running (started before the amendment): 67 shards / 344,441,194 rows, full sha256 recorded, dedup in
  6 key-range passes (pass 1 1718.2 s under the cap, pass 2 139.8 s after the lift: 12.3x); conversion stops before D: would drop below 40 GB + 2 GB
  margin (resumable). Its cap was lifted from outside at 12:52 (see Facts); log `r11_nnue\logs\lift_wscap.log`.
- One-command driver `opus_r11/pipeline/r11_pipeline.py` (run/status/selftest; exit 0 PASS, 1 FAIL, 3 WAIT).
  Real net: `run --net <ep20>` -> R11 PIPELINE PASS in 192 s (13:00-13:04: parity 12000/12000, OFF d11 312866, ON d11-d22
  equal, WAC ON 267 / OFF 272 at 200 ms under 93 % CPU load; existing package recognised, not rewritten); the same
  command again: check reused, PASS in 0 s. Evidence `opus_r11/logs/onecmd_ep20/`.
- E2E CPU test `test_r11_train.py` (e2e_3): data, holdout test and train gate passed; production trainers started at
  12:44:54-57 while the entry was still importing torch (11 min under the 32 MB cap; its pre-import check had passed at
  12:39); the first in-training check (12:51:15, 17 s after fit start) saw production, saved stop-epoch=0-step=1.ckpt and
  exited 76; the test waits for the GPU queue. Hardening (M1): the entry now also checks right after the imports
  (exit 76 before the trainer's main) and at fit start (exit 76, nothing trained, no save); stub-clone test in
  test_r11_tools.
- Next: real holdout proof on 013/014 (`opus_r11/tests/test_r11_holdout_real.py`) after the dedup, then training waits
  for the GPU (yield-only) and for that proof.

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
  AMENDED (commit "CR fix 2 amendment"): no background mode (32 MB working-set cap); Idle + I/O very low + memory low
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
- **Background mode (PROCESS_MODE_BACKGROUND_BEGIN) = hard 32 MB working-set max** (GetProcessWorkingSetSizeEx: max
  32 MB, flags 0x6 = HARDWS_MAX_ENABLE) + memory priority 1 (very low). 300 MB numpy array touched once per second:
  background 32 MB working set, 76,800 page faults and 0.13 s per touch; Idle + I/O very low + memory low: 318-332 MB,
  no new faults, 0.01 s. Real cost: dedup pass 1 1718.2 s, pass 2 after lifting the cap 139.8 s (same data size); the E2E train entry ran
  user 20.7 s / system 178.7 s with 117M page faults (445k/s). Children inherit Idle, I/O very low (0), memory low (2)
  and the mask (psutil + GetProcessInformation, test 1e).
- The cap can be lifted from outside without stopping the process: SetProcessWorkingSetSizeEx(pid, 200 KB, 1.35 MB,
  HARDWS_MIN_DISABLE | HARDWS_MAX_DISABLE) (+ memory priority low) -> the probe went 32 -> 329 MB at once, faults
  stopped. Done at 12:52 for the two R11 trees started before the amendment (data PID 3240, E2E 11452) by a watcher that
  only touches those trees and only processes with a HARD max (job tmp `bgcap/lift_wscap_watch.py`, log
  `D:\grok-pc-data\r11_nnue\logs\lift_wscap.log`); priority class, I/O priority and mask unchanged.
- Amended writer `r11_pos2binpack_9f191c200e4b.exe` (sha256 a09a5b2f...): shard 001 all-train md5 9bd30944 = J1 again,
  HCE side-car identical, verify OK.

## Next
1. When the dedup finishes: run `test_r11_holdout_real.py --config opus_r11/pipeline/r11_config.json`, commit the record.
2. Smoke training only when no production trainer runs (yield) and the holdout record matches; then export -> check ->
   package (smoke packages are not gate candidates). The E2E test finishes by itself when the GPU queue is idle.
3. Format-patch files of the CR commits for re-review, final review pass, report.

## How to resume (for someone else)
- `git worktree add <dir> origin/opus-r11-nnue-pipeline`; read this file, then the module docstrings in opus_r11/pipeline.
- Data: `python -I -B opus_r11/pipeline/r11_data.py --config opus_r11/pipeline/r11_config.json run` (restart-safe; it
  continues from the registry and the per-shard markers; stop it by its PID).
- Tests: `opus_r11/tests/test_r11_tools.py <new dir>`, `opus_r11/tests/test_r11_data.py <writer exe> <new dir>`.
- PC rules: `.claude/skills/forge-pc-rules/SKILL.md` (Idle, <= 3 cores, never touch production / gates /
  queue_state.json / locks, never type the production trainer's script name).
