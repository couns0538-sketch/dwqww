# JOB D - Fair evaluation-candidate builds - STATUS

**Clone made:** 2026-11-11 12:38:35 PC clock (PST label). **Last update:** 2026-11-11 14:38 PC clock (read from the PC).
**Branch:** `fable/fair-eval-builds-20261111`, cut from lock `16833ecc03b425586f91f4c8834dea8807bf4c22`.
**State: main job COMPLETE (REPORT.md). Follow-up requested by the owner at about 13:55 is IN PROGRESS: three matches are running unattended.**

## Follow-up: done so far
1. **v2 KB8 cost.** Breakdown on one exe, identical trees: KB1 0.963, KB4 0.934, KB8 0.927 of the lock; output buckets cost nothing.
   New switch `FORGE_NNUE_V2_FAST` (bit mask; 512-bit output kernel, fused update, refresh rule), bit-exact
   (ten pins + perft, 12,000 / 12,000): replica 0.936 (was 0.927), U8 0.817 (was 0.808), run 5 0.931 (was 0.914).
   Most of the remaining cost is the king-bucket refresh and was not removed.
2. **Stand-alone 1024 nets.** Every gate row used `forge_ltopgo_x_r10fix1_halfka_9e5cb644.exe`. On its HalfKA path a plain
   build of the same source is 16.7 % faster (same tree). The path is now ported to combo29 behind `FORGE_NNUE_HALFKA`
   (node counts equal the old exe's). Config `halfka_1024` (own profile) is 1.446x the old gate exe on the same tree;
   `halfka_1024_cold` reproduces the cold recipe (own / cold = 1.108).
3. `EVIDENCE_MATRIX.md` corrected: run 5 has a gate row (+16.11, H1); the U8 confirm gate played a v2p4 exe two locks
   behind its base.

## Running now (started 14:36:03, this job's own processes, NOT the gate queue)
Detached queue `fair_eval/tools/match_queue_20261111.sh` (Windows pid 2296 `bash.exe`, started with Start-Process), which runs
`tools/run_match.sh` three times against the original lock exe: fastchess, tc 6+0.06, 12 games at once, UHO book, both colours:
1. `halfka_1024` 300 games, 2. `v2kb8_U8_fast` 2000 games, 3. `int8` 1100 games. Expected end about 16:10.
Children: `fastchess.exe`, `forge_fair_*.exe`, `forge_clang_combo29_trial_w6.exe`.
Progress and results: `D:\forge_jobs_20261111\fairD\_work\match\queue.log` and `_work\match\<name>\match.log`.
To stop it cleanly: `Stop-Process -Id 2296`, then stop the `fastchess.exe` whose command line names `_work\match`.
No build or timing may run while the matches run.

## Pending after the matches
1. Read the three results (fastchess prints Elo, error and the pentanomial at the end of each `match.log`).
2. Optional same-architecture control for the stand-alone path: `build_fair.ps1 -Config halfka_1024 -Diag`, a plain scalar
   build, and a 12k dump comparison.
3. Add the follow-up section to `REPORT.md`, copy `_work\abba_*` and match logs to `results/`, commit, push.

## Next exact command
`cat /d/forge_jobs_20261111/fairD/_work/match/queue.log` (the last line is `QUEUE DONE` when all three are finished).

## Process ownership
Mine: the queue above and its children. Six `python` processes existed before the job; not mine, untouched.

## Blockers
None.
