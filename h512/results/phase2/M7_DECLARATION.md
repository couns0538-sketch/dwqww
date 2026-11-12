# Match M7 (6 s + 0.06 s, rebuilt executable): declared before the first game (2026-11-12 02:45 PC clock; first game 02:45:59)

Not the crew gate and not a lock claim. Declared in addendum 11; this file adds the hashes of the rebuilt executable.

| Item | Value |
|---|---|
| Candidate exe | **rebuilt**: `_work\builds\h512_v3_c3_29ea1b67b2dd\forge_fair_h512_v3_c3.exe`, md5 `0b9da97c2a859d6e75642db23536de90`, sha256 `81d58b04ba1b8fbd56a6c94475fc2048a0692e1fe7a23d31647c4913b922a598`. Same source and flags as the phase-1 executable; PGO profile collected with candidate 3's net loaded (config `h512_v3_c3`) |
| Net | candidate 3, `_work\nets\h512_cand_W2_seen10000023552.fnn3`, md5 `aab64b3342d7c1c33e82845f5d2d1fa4` |
| Opponent | original lock exe `forge-combo29/windows/forge_clang_combo29_trial_w6.exe`, md5 `c0051c99695f48bf93272d96fe7548c3` |
| Budget | **1,500 games = 750 opening pairs**, fixed, no early stop |
| Openings | `UHO_Lichess_4852_v1.epd`, random order, seed 2026111112, each opening with both colours |
| Clock | 6 s + 0.06 s per move for both engines, time margin 1000 ms |
| Engines | Threads 1, Hash 16 MB, OwnBook false |
| Concurrency | 12 games at once. **The GPU is idle and nothing else of this job runs** (the phase-1 conditions) |
| Adjudication | none |
| Runner | Job D's `fair_eval/tools/run_match.sh` (fastchess, `-recover`), via `h512/results/phase2/launch_match4.sh m7` |
| Analysis | `h512/tools/match_elo.py`, opening pairs as units, 95 % interval; time losses and crashes by side |

Checked before the start:
- Build receipt and coverage proof pass (`h512/results/phase2/build_c3/`): v3 evaluation entered 2,619,188 times, the
  compiled-in residual net and the hand-crafted evaluation 0 times.
- Bench nodes with the net are 348,651 / 743,566 / 2,890,515 at depths 11 / 13 / 16, the same as the phase-1 executable.
- Quiet ABBA timing, `bench 20`, 16 pairs: rebuilt exe with candidate 3's net against the lock **1.0952** (95 % CI
  1.0931 to 1.0974); phase-1 exe against rebuilt exe on the same net and the same 13,407,897 nodes 0.9985 (0.9962 to
  1.0007). So the rebuild did not change the speed, and with candidate 3's net the engine is about 9.5 % faster than
  the lock in nodes per second, not the 19.8 % measured in phase 1 with candidate 1's net: the net changes the tree
  that `bench` searches.
- Known when this was written: all results of phase 2 (M5: the phase-1 executable with this net scored +66.6 Elo at
  this clock).
