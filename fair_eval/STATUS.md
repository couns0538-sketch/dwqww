# JOB D - Fair evaluation-candidate builds - STATUS

**Clone made:** 2026-11-11 12:38:35 PC clock (PST label). **Last update:** 2026-11-11 13:35 PC clock.
**Elapsed:** about 0.9 h of execution since the clone. Read-only exploration and planning before the clone were not clocked.
Earlier versions of this file carried "last update" times that were my estimates, not clock readings; the times here are read from the PC.
**Branch:** `fable/fair-eval-builds-20261111`, cut from lock `16833ecc03b425586f91f4c8834dea8807bf4c22`.
**State: COMPLETE** - all five steps of the plan are done; `REPORT.md` is the result (it includes one extra robustness timing run at depth 22).

## Completed
1. Evidence: identities verified, original lock exe pins reproduced, `EVIDENCE_MATRIX.md`.
2. Per-configuration profiling: source switches (macro-0 identity for all eight units), `build_fair.ps1`, `configs.json`,
   coverage proof from each profile. Built: `base_resid`, `int8`, `int8_cold`, `v2kb8_lockrep`, `v2kb8_lockrep_hot`,
   `v2kb8_U8`, `v2kb8_r5`, a diag twin of each except `int8_cold`, and three plain reference exes.
3. Arithmetic controls on 12,000 FENs: control and v2 KB8 replica exact; INT8 inside its pre-registered bounds.
4. ABBA vs the lock: 16 pairs per arm for eight arms, 8 pairs for five arms on the earlier gate exes, and the
   per-evaluation microbenchmark.
5. `REPORT.md`.

## Failed
Nothing failed. Two plain clang reference builds first failed at link (missing `-rtlib=libgcc -unwindlib=libgcc`); fixed in `tools/plain_build.sh`.

## Not done, by decision
- No standalone build: all three candidate nets are residual (headers checked).
- No GPU work: the job has no training step.
- No strength test: outside this job.

## Artifacts (local, not in the repository)
`D:\forge_jobs_20261111\fairD\_work\builds\<config>_<identity>\forge_fair_<config>.exe` (md5 list in REPORT.md),
`_work\nets\` (replica, U8, run 5), `_work\plain\`, `_work\evals\` (twelve 12k dumps, sha256 in `results/evals/dumps.sha256`),
`_work\abba\` (copied to `results/abba/`). About 0.3 GB in total; D: has 35 GB free.

## Process ownership
No process of this job is alive. Everything it started was a short foreground child (compiler, engine runs, python tools)
that has exited. Six `python` processes existed before the job; not mine, untouched.

## Resume point
Nothing is owed. To extend: `pwsh -NoProfile -File fair_eval\build_fair.ps1 -Config <id>` rebuilds any configuration
(a finished identity folder is detected and left alone), then the commands in REPORT.md "Reproduction".

## Blockers
None.
