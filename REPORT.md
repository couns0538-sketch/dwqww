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

## In progress / left (in order)
1. **C4 code-review fixes and finishing C5:** a sub-agent is on it. A previous sub-agent's process ended before
   C5 was done.
2. **O1-LTT LocklessTT:** code, tests and local evidence are pushed; the CI evidence (TSan stress at T2/4/8,
   scaling off/on, self-play) is running; the report is left.
3. **O5 CorrMargins, then O8 CorrExt:** a sub-agent is on them.
4. **O4 PureNnue, O6 NNUEThreats, O7 NNUEPawnPairs:** not started; they build on C4's v2 loader/export.
5. **Sol's queue** (`SOL_LEFTOVERS_FOR_CLAUDE.md`): section 2 first (S11, S18, S13, ...), then the section 3
   fix-ups.

## ATTENTION: our smoke runs disturbed the PC training supervisor (found 2026-10-27 10:24 PST)
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
- **Not fixed here.** Nothing was written to `F:\forge_nnue_train`, because that is not allowed. **The owner
  may want to reset the supervisor's `fails` counter**, or let a run finish DONE, so that it returns to its
  queue.

## Environment notes (read before re-using numbers)
- **Machine load.** The PC ran a fastchess gate, self-play datagen and NNUE training the whole time (machine
  exclusive: no). With the owner's OK, all work ran at BelowNormal priority with at most 3 threads. PC speed
  numbers are noisy; the quiet-runner A/Bs (GitHub Actions) are the cleaner speed evidence.
- **No local Linux sanitizers.** WSL2 needs the Virtual Machine Platform feature and a reboot, which was not
  done. Linux identity, ASan+UBSan and TSan come from `.github/workflows/opus-ci.yml` on each `opus-*` branch.
- **Paths.** The lock archive and the build scripts moved from the session scratchpad to
  `D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg` and `...\b\tools` (2026-10-27). NNUE smoke runs write only to
  `F:\opus_scratch`, with renamed trainer copies; `F:\forge_nnue_train` was never written.
- **Left for the owner to delete by hand** (deletes were not allowed in this session):
  - `C:\Users\Administrator\.wslconfig` (created by the attempted WSL install; caps WSL2 at 2 CPUs / 6 GB);
  - `C:\Program Files\Git\tmp_c6_search.cpp` and `C:\Program Files\Git\tmp_nnue.o` (stray files from two
    sub-agents' mistyped paths);
  - scratch build folders under `D:\grok-pc-data\dwqww\.claude\worktrees\b\`.
