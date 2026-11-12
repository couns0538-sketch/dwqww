# Match M2 (6 s + 0.06 s): declared before the first game (2026-11-11 21:41 PC clock; first game 21:41:40)

Not the crew gate and not a lock claim. Same settings as the phase-1 match, new net, new opening seed.

| Item | Value |
|---|---|
| Candidate exe | `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`, md5 `5c46cd2d43bc051df1a39e841487b95f` (the phase-1 exe, not rebuilt), options `NNUEArchFile` = candidate 2, `NNUEArch` = true |
| Net | **candidate 2**, `_work\nets\h512_cand_W2_seen02000003072.fnn3`, md5 `ae0d372e3748fc6d4e27c2885b164d46`, sha256 `df88ae380196c796cc8ded28095194d1fb67ce4ea42dc2b50621dc347b06208b` |
| What it is | phase-1 state at 1.0B plus one cosine cycle to 2.0B with weight decay 1.0 on the king-bucketed first-layer weights. Selection loss 0.014081 (candidate 1: 0.014480, s198 + HCE: 0.014311). Frozen by the selection rule (`FROZEN_CANDIDATE_2.json`) |
| Opponent | original lock exe `forge-combo29/windows/forge_clang_combo29_trial_w6.exe`, md5 `c0051c99695f48bf93272d96fe7548c3` |
| Budget | **3,000 games = 1,500 opening pairs**, fixed, no early stop |
| Openings | `UHO_Lichess_4852_v1.epd`, random order, seed 2026111106, each opening with both colours |
| Clock | 6 s + 0.06 s per move for both engines, time margin 1000 ms |
| Engines | Threads 1, Hash 16 MB, OwnBook false |
| Concurrency | 12 games at once on the 16 logical CPUs |
| Adjudication | none |
| Runner | Job D's `fair_eval/tools/run_match.sh` (fastchess, `-recover`), via `h512/results/phase2/launch_match.sh m2` |
| Analysis | `h512/tools/match_elo.py`, opening pairs as units, 95 % interval; time losses and crashes by side |

Different from phase 1, stated in advance:
- **The GPU trainer of this job runs during the match** (owner's instruction to use GPU and CPU together). It uses the
  GPU and one CPU thread. Both engines play under the same load and every opening is played with both colours.
- Known hazard as before: the owner's `resource_guard.ps1` suspends fastchess for about 5 s when its thermal latch trips;
  with the GPU busy the machine runs warmer, so this is more likely than in phase 1. Affected games are reported by
  side, with the result without the affected opening pairs. The guard is not bypassed.
- Checked before the start: integer parity of candidate 2 on 14,000 positions (0 mismatches, `parity_candidate2.json`);
  bench nodes with the net 293,818 / 900,174 / 2,610,509 at depths 11 / 13 / 16 (`pins_candidate2.txt`).
