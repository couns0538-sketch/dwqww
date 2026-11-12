# Match M5 (6 s + 0.06 s): declared before the first game (2026-11-12 00:00 PC clock, while M3 was still running)

Not the crew gate and not a lock claim. The final candidate's own match under the phase-1 conditions.

| Item | Value |
|---|---|
| Candidate exe | `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`, md5 `5c46cd2d43bc051df1a39e841487b95f` (the phase-1 exe, not rebuilt), options `NNUEArchFile` = the net below, `NNUEArch` = true |
| Net | the eligible net with the lowest selection loss when M3 ends. Expected: **candidate 3**, `_work\nets\h512_cand_W2_seen10000023552.fnn3`, md5 `aab64b3342d7c1c33e82845f5d2d1fa4` (selection loss 0.013882). It is replaced only if a checkpoint of the decay-0.3 continuation is at least 0.00002 below that by then; the net actually played is in `RUN_INFO.txt` and in the report |
| Opponent | original lock exe `forge-combo29/windows/forge_clang_combo29_trial_w6.exe`, md5 `c0051c99695f48bf93272d96fe7548c3` |
| Budget | **2,000 games = 1,000 opening pairs**, fixed, no early stop (addendum 8) |
| Openings | `UHO_Lichess_4852_v1.epd`, random order, seed 2026111110, each opening with both colours |
| Clock | 6 s + 0.06 s per move for both engines, time margin 1000 ms |
| Engines | Threads 1, Hash 16 MB, OwnBook false |
| Concurrency | 12 games at once on the 16 logical CPUs |
| Adjudication | none |
| Runner | Job D's `fair_eval/tools/run_match.sh` (fastchess, `-recover`), via `h512/results/phase2/launch_match2.sh m5` |
| Analysis | `h512/tools/match_elo.py`, opening pairs as units, 95 % interval; time losses and crashes by side |

Stated in advance:
- The GPU trainer of this job runs during the match, using the GPU and one CPU thread.
- Known hazard as in M2 and M3: 5-second suspensions of the match process by the owner's resource guard when its CPU
  reading goes over 90 C. Affected games are reported by side, with the result without the affected opening pairs.
- Known when this was written: M2's result (candidate 2: +41.3 Elo at this clock) and M3's running score after about
  1,200 of 2,000 games (+55, error 12).
