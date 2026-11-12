# Match MN2 (fixed nodes): declared before the first game (2026-11-11 23:58 PC clock, while M3 was still running)

Not the crew gate and not a lock claim. The same question MN1 answered for candidate 1, now for a weight-decay net.

| Item | Value |
|---|---|
| Question | At equal nodes per move (speed taken out), is the weight-decay net's evaluation better than combo29's? |
| Candidate exe | `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`, md5 `5c46cd2d43bc051df1a39e841487b95f`, options `NNUEArchFile` = the net below, `NNUEArch` = true |
| Net | the same net that plays M5. Expected: **candidate 3**, `_work\nets\h512_cand_W2_seen10000023552.fnn3`, md5 `aab64b3342d7c1c33e82845f5d2d1fa4`; the net actually played is in `RUN_INFO.txt` and in the report |
| Opponent | original lock exe `forge-combo29/windows/forge_clang_combo29_trial_w6.exe`, md5 `c0051c99695f48bf93272d96fe7548c3` |
| Limit | **250,000 nodes per move for both engines, no clock** (`go nodes 250000`), as in MN1 |
| Budget | **3,000 games = 1,500 opening pairs**, fixed, no early stop |
| Openings | `UHO_Lichess_4852_v1.epd`, random order, seed 2026111109, each opening with both colours |
| Engines | Threads 1, Hash 16 MB, OwnBook false |
| Concurrency | 12 games at once; the GPU trainer runs at the same time; a clock-free match is not affected by load or by a suspension |
| Adjudication | none |
| Runner | `h512/tools/run_match_nodes.sh` (fastchess, `-recover`), via `h512/results/phase2/launch_match2.sh mn2` |
| Analysis | `h512/tools/match_elo.py`, opening pairs as units, 95 % interval |

- Starts when M5 has ended, if that is by 02:00 (addendum 8).
- Reference: MN1, candidate 1 under the same settings (seed 2026111108): -4.8 Elo, 95 % interval -12.5 to +3.0.
- How to read it: both engines have the same search code. At equal nodes the candidate spends about 17 % less time
  per move, so equal nodes is a handicap for it compared with equal time.
