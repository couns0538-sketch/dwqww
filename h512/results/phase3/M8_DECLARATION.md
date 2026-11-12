# Match M8 (30 s + 0.3 s): declared before the first game (2026-11-12 07:15 PC clock)

Not the crew gate and not a lock claim. Question: how much of candidate 3's advantage is left at a clock five times
longer than the 6 s + 0.06 s matches? Rating lists use long clocks, so this bears on any absolute-rating goal.
Run after JOB E was reported complete, at the owner's request to keep using the PC.

| Item | Value |
|---|---|
| Candidate exe | `_work\builds\h512_v3_c3_29ea1b67b2dd\forge_fair_h512_v3_c3.exe`, md5 `0b9da97c2a859d6e75642db23536de90` |
| Net | candidate 3, `_work\nets\h512_cand_W2_seen10000023552.fnn3`, md5 `aab64b3342d7c1c33e82845f5d2d1fa4` |
| Opponent | original lock exe `forge-combo29/windows/forge_clang_combo29_trial_w6.exe`, md5 `c0051c99695f48bf93272d96fe7548c3` |
| Budget | **1,000 games = 500 opening pairs**, fixed, no early stop |
| Openings | `UHO_Lichess_4852_v1.epd`, random order, seed 2026111201, each opening with both colours |
| Clock | 30 s + 0.3 s per move for both engines, time margin 1000 ms |
| Engines | Threads 1, Hash 16 MB (kept as in the earlier matches; small for this clock, the same for both), OwnBook false |
| Concurrency | 12 games at once. **The GPU is busy** (the 1024-unit training pilot runs beside it) |
| Adjudication | none |
| Runner | `fair_eval/tools/run_match.sh` (fastchess, `-recover`), via `h512/results/phase3/launch_m8.sh` |
| Analysis | `h512/tools/match_elo.py`, opening pairs as units, 95 % interval; time losses and crashes by side |

Estimated duration: about 2 h 15 min (a game lasts about five times as long as at 6 s + 0.06 s).

Known when this was written: all JOB E results (+66.6 and +67.3 Elo at 6 s + 0.06 s, +57.0 at 10 s + 0.1 s,
+54.9 at 250,000 nodes). With 500 pairs the 95 % interval will be about 15 Elo either side, so this match can show
a large loss of advantage, not a small one.
