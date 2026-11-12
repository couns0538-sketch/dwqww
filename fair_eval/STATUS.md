# JOB D - Fair evaluation-candidate builds - STATUS

**Clone made:** 2026-11-11 12:38:35 PC clock (PST label). **Last update:** 2026-11-11 16:47 PC clock (read from the PC).
**Branch:** `fable/fair-eval-builds-20261111`, cut from lock `16833ecc03b425586f91f4c8834dea8807bf4c22`.
**State: COMPLETE**, main job and the follow-up the owner asked for at about 13:55. `REPORT.md` is the result; its
"Follow-up" section holds the three later items.

## Completed (main job, 12:38 - 13:35)
Evidence matrix; INT8 and v2 KB8 paths on the lock source behind switches; `build_fair.ps1` with coverage proof from
each profile; arithmetic controls on 12,000 FENs; ABBA timing against the lock; report.

## Completed (follow-up, 13:55 - 16:45)
1. **v2 KB8 cost traced and partly removed.** KB1 0.963, KB4 0.934, KB8 0.927 of the lock on identical trees.
   `FORGE_NNUE_V2_FAST=7` is bit-exact and brings the replica to 0.936, U8 to 0.817, run 5 to 0.931.
2. **Stand-alone 1024 nets checked.** Their gate exe was cold-profiled on the HalfKA path (a plain build of the same source
   is 16.7 % faster) and two speed locks behind. The path is ported to combo29 behind `FORGE_NNUE_HALFKA`; `halfka_1024`
   is 1.446x the old gate exe on the same tree.
3. **Matches** (own processes, fastchess, 6+0.06, 12 at once, UHO book; NOT the crew gate):
   - `v2kb8_U8_fast` vs lock: 2000 games, **+17.2 +/- 8.3 Elo**, no time losses.
   - `int8` vs lock: 2 x 1100 games, +12.0 +/- 11.6 and +9.8 +/- 11.7, pooled **+10.9 +/- 8.2 Elo**; 28 time losses
     (14 each side) in three machine stalls; +11.0 without them.
   - `halfka_1024` vs lock: 300 games, **-97.4 +/- 25.0 Elo**.
4. `EVIDENCE_MATRIX.md` corrected (run 5 has a gate row; the U8 confirm gate used an exe two locks behind its base).

## Failed or left open
- About 6 points of the v2 KB8 cost remain (2.7 % unexplained code path, about 3.7 % king-bucket refresh).
- The cause of the periodic machine stalls during the INT8 matches was not identified; not one of this job's processes.
- Run 5 was built (`v2kb8_r5_fast`) and timed but not played.

## Artifacts (local, not in the repository)
`D:\forge_jobs_20261111\fairD\_work\builds\<config>_<identity>\forge_fair_<config>.exe` (md5 list in REPORT.md),
`_work\nets\`, `_work\plain\`, `_work\evals\`, `_work\match\<name>\games.pgn` (md5 in `results/match/pgn.md5`).
About 0.6 GB in total.

## Process ownership
No process of this job is alive: the match queue (Windows pids 2296 and 6032) and its fastchess and engine children
have exited. Processes that existed before the job or were started by others were not touched.

## Resume point
Nothing is owed. Suggested next step for the crew: gate `v2kb8_U8_fast`, `v2kb8_r5_fast` and `int8` against the
combo29 lock (REPORT.md, F4). Any configuration rebuilds with
`pwsh -NoProfile -File fair_eval\build_fair.ps1 -Config <id>`.

## Blockers
None.
