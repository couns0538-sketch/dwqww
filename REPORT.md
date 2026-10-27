# Opus round report (Forge, AL1 s198) — overall status, 2026-10-27

**Brief.** `OPUS_PROMPT.md` + `OPUS_TEST_PLAN.md`, then `SOL_LEFTOVERS_FOR_CLAUDE.md` (on the PC, `D:\grok-pc-data\dwqww`).

**Where things are.**
- This branch, `opus-summary`, holds this report, the job table (`opus_round1/SUMMARY.md`) and the Sol-queue
  progress (`SOL_LEFTOVERS_PROGRESS.md`).
- Each job is on its own branch `opus-<JOB>`, with its folder `opus_round1/<JOB>/` (REPORT.md, IDEA_SOURCE.md,
  patch.diff, logs, SHA256SUMS). Nothing was pushed to main or to anyone else's branch, and nothing was
  force-pushed.

## Done (details and numbers: opus_round1/SUMMARY.md and each job's REPORT.md)
- **00_baseline:** the lock was reproduced on the PC before any job (bench x5, perft, kiwipete, FMA 0; exe
  byte-identical to the PC lock exe except the PE timestamp/checksum).
- **O3** search.cpp split into modules. Code-review fix: hot functions pinned to 64 bytes (speed-neutral on a
  quiet runner), and the "machine-code identical" claim is reworded to what was measured.
- **O1** Lazy SMP audit: 2 bugs fixed (stale helper node counters → `SmpExactNodes`; dangling worker-list
  pointer), plus `SmpBestThread`. Code-review fix: a deeper helper never overrides a mate score.
- **C3** HardDeadline watchdog (the WAC stalls were process starvation).
- **O2** NNUE kernels: bit-identical on every target; +3.3% bench NPS. The +10% target was NOT reached, and the
  report explains why.
- **C6** CuckooRep upcoming-repetition detection.
- **C2** CorrHistPlus (continuation / minor / non-pawn keys).
- **C1** own Syzygy prober. Code-review fix: TB scores keep their distance in the TT.

## Also done since (2026-10-27)
- **All Opus jobs:** O1-O8 and C1-C6 are DONE, each on its branch with its REPORT.md. That includes C4 + C5,
  O1-LTT (+ the "info string LocklessTT active" line), O5/O8 and O4/O6/O7.
- **User follow-ups:**
  - C3: the watchdog's fallback bestmove obeys `searchmoves`, and DebugSearchDelayMs is compiled only in debug and
    test builds (CI green incl. the TSan hook).
  - S29: a PC FORGE_SPEEDSTACK build is node-exact; PC NPS under load is inside noise.
  - S-IT: the intended-threefold claim (GitHub issue #7) on the AL1 base, UCI `IntendedThreefold` default off
    (CI release/ASan/TSan green; quiet-runner NPS A/B in its REPORT). A code review found no correctness bug but a
    claim-check cost in shuffling positions, a test gap at the draw floor and two tooling bugs; fixes are in
    progress on the same branch.
- **Sol queue (`SOL_LEFTOVERS_FOR_CLAUDE.md`):** one line per job in `SOL_LEFTOVERS_PROGRESS.md`.
  - Section 2: S11-S50 done (S22 covered by O1).
  - Astra A1 (`HistRework`, CI green) and A7 (long-training recipe) are done.
  - Test-plan jobs done: S-A1 (more-data recipe), S-A3 (v3d trainer with LR-schedule arguments), S-A6 (SPSA re-tune
    plan) and S-C4 (hidden 768-1024 plan with a measured width cost).
  - Section 3 fix-ups done: S09, S10, S25, S26, S27, S28, S33, S48.

## In progress / left
- **Sub-agents still working:**
  - S41/S45/S49;
  - fix-ups S04-S08;
  - A2 + A3 (king-bucket doc, full-NNUE pipeline);
  - S-A2 + S-A4 (int16 port with trainer weight clipping, hidden 512);
  - the S-IT code-review fixes.
- **Main session:** S20, a 1M-position depth-8 rescoring, is finishing (the run is at its last chunks).

## Incident: our smoke runs disturbed the PC training supervisor (found 2026-10-27 10:24 PST; RESOLVED, QA reset the fail count to 0)
- **What happened.** `F:\forge_nnue_train\supervisor.log` (read only) shows that the supervisor adopted five
  CPU smoke-training processes from earlier C4/C5 sub-agents as if they were its own queue jobs:
  - `runs_kb4_test`, `smoke_kb4`, `smoke_kb8` on 2026-10-26 21:45-21:52;
  - `smoke_kb4ob8`, `runs_c5_kb4` on 2026-10-27 08:54-08:55.
- **Effect.** It counted them as FAILED runs, backed off (no new launches for 10 min at 26 Oct 23:07 and 5 min
  at 27 Oct 08:57), and since 09:03 it logs "QA never-idle: 2 consecutive fails -> skipping queue/resume,
  launching auto fallback": it runs auto-fallback jobs instead of its queue.
- **Current state.** `queue_state.json` still shows `fails = 2`, `last_fail_t = 2026-10-27T08:57:35`.
- **Cause.** The trainer ran under its own name, with run folders named `runs_*` / `smoke_kb*`. All of this was
  before the renaming rule reached those sub-agents.
- **Since then.** Runs use a renamed copy (`opus_nnue_smoke.py`) and write only under `F:\opus_scratch`, and
  were not adopted. The NNUE sub-agent has also been told to avoid such names and to check the supervisor log
  after starting any run.
- **Resolved.** QA reset the supervisor's fail count to 0 (reported by the owner on 2026-10-27). Nothing was
  written to the supervisor's directory from this session. The binding rules now: smoke scripts are named
  `opus_nnue_smoke*.py`, never `train_resid*`, and all new build and smoke output goes under `F:\opus_scratch`.

## Environment notes (read before re-using numbers)
- **Machine load.** The PC ran a fastchess gate, self-play datagen and NNUE training the whole time (machine
  exclusive: no). Work first ran at BelowNormal with at most 3 threads. From 2026-10-27 afternoon the owner asked
  for maximum parallelism: up to about 10 sub-agents at once, every process single-threaded at Idle priority
  (below the BelowNormal gates), RAM floor 6 GB (free RAM stayed at 9-12 GB). PC speed numbers are noisy; the
  quiet-runner A/Bs (GitHub Actions) are the cleaner speed evidence.
- **No local Linux sanitizers.** WSL2 needs the Virtual Machine Platform feature and a reboot, which was not
  done. Linux identity, ASan+UBSan and TSan come from `.github/workflows/opus-ci.yml` on each `opus-*` branch.
- **Paths.** The lock archive and the build scripts moved from the session scratchpad to
  `D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg` and `...\b\tools` (2026-10-27). NNUE smoke runs write only to
  `F:\opus_scratch`, with renamed trainer copies; `F:\forge_nnue_train` was never written.
- **Left for the owner to delete by hand** (deletes were not allowed in this session):
  - `C:\Users\Administrator\.wslconfig` (created by the attempted WSL install; caps WSL2 at 2 CPUs / 6 GB);
  - `C:\Program Files\Git\tmp_c6_search.cpp` and `C:\Program Files\Git\tmp_nnue.o` (stray files from two
    sub-agents' mistyped paths);
  - scratch build folders under `D:\grok-pc-data\dwqww\.claude\worktrees\b\`;
  - `F:\opus_scratch\tmp_sol_fix_listing.txt` (a stray listing at the top of scratch) and six empty `wt_err_*.txt`
    files in the user Temp folder (both from the S25-S48 fix-up agent);
  - `F:\opus_scratch\worktrees\opus_sol_s43` (an early copy of the S43 tool, not a git worktree; the real
    worktree is `opus_sol_s43_wt`) and `F:\opus_scratch\sol_S40\fixture_v2\second\newdir` (planted-bug output);
  - the empty untracked folder `opus_round1/sol_S27fix/old_attempt_check` in the S27fix worktree;
  - all of `F:\opus_scratch` (worktrees, builds, scratch) once the branches are reviewed.
- **Published outside git branches:** the GitHub prerelease `opus-sol-S48fix-grids-20261027` (tag on the S48fix
  branch, `main` untouched). S48-4 asked for simulation grids to go to release assets instead of git; delete the
  release if you don't want it.
- **Rule slips by sub-agents (no effect):**
  - Two agents (S09fix, S40) put the trainer's name `train_resid_v3b.py` into read-only `git show`, `grep`, `sed`
    and `sha256sum` command lines. Nothing ran under that name, and the supervisor's "adopted running job" count
    stayed at 7.
  - One `rm -rf` on a not-yet-created scratch folder was denied by the permission system; nothing was deleted.
  - The briefs and skills now spell out both rules.
