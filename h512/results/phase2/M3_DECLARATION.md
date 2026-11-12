# Match M3 (10 s + 0.1 s): declared before the first game (2026-11-11 23:04 PC clock; first game 23:04:27)

Not the crew gate and not a lock claim. A longer clock than the other timed matches, to see whether the result holds.

| Item | Value |
|---|---|
| Candidate exe | `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`, md5 `5c46cd2d43bc051df1a39e841487b95f` (the phase-1 exe, not rebuilt), options `NNUEArchFile` = candidate 3, `NNUEArch` = true |
| Net | **candidate 3**, `_work\nets\h512_cand_W2_seen10000023552.fnn3`, md5 `aab64b3342d7c1c33e82845f5d2d1fa4`, sha256 `6d2cf71467e95a96d36b9c8fee808090269cf42b9c455ff428926243e5171903` |
| What it is | candidate 2's run (weight decay 1.0 on `w1`) continued through three more cosine cycles to 10,000,023,552 presentations. Selection loss 0.013882 (candidate 2: 0.014081, candidate 1: 0.014480, s198 + HCE: 0.014311). Frozen by the selection rule (`FROZEN_CANDIDATE_3.json`): the lowest selection loss of all eligible nets when M2 ended |
| Opponent | original lock exe `forge-combo29/windows/forge_clang_combo29_trial_w6.exe`, md5 `c0051c99695f48bf93272d96fe7548c3` |
| Budget | **2,000 games = 1,000 opening pairs**, fixed, no early stop (addendum 7: 2,000 instead of 3,000 to leave room for two more matches) |
| Openings | `UHO_Lichess_4852_v1.epd`, random order, seed 2026111107, each opening with both colours |
| Clock | 10 s + 0.1 s per move for both engines, time margin 1000 ms |
| Engines | Threads 1, Hash 16 MB, OwnBook false |
| Concurrency | 12 games at once on the 16 logical CPUs |
| Adjudication | none |
| Runner | Job D's `fair_eval/tools/run_match.sh` (fastchess, `-recover`), via `h512/results/phase2/launch_match.sh m3` |
| Analysis | `h512/tools/match_elo.py`, opening pairs as units, 95 % interval; time losses and crashes by side |

Stated in advance:
- The GPU trainer of this job runs during the match (the second pilot round), using the GPU and one CPU thread.
- Known hazard: in M2 the owner's resource guard suspended the match process several times for 5 s (CPU reading over
  90 C) and 44 games ended on time, 19 lost by the candidate and 25 by the lock. The same can happen here. Affected
  games are reported by side, with the result without the affected opening pairs. The guard is not bypassed.
- Checked before the start: integer parity of candidate 3 on 14,000 positions (0 mismatches, `parity_candidate3.json`);
  bench nodes with the net 348,651 / 743,566 / 2,890,515 at depths 11 / 13 / 16 (`pins_candidate3.txt`).
- Known when this was written: M2's result (candidate 2: +41.3 Elo at 6 s + 0.06 s).
