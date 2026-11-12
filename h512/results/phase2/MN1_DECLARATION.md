# Match MN1 (fixed nodes): declared before the first game (2026-11-11 20:43 PC clock)

Not the crew gate and not a lock claim.

| Item | Value |
|---|---|
| Question | At equal nodes per move (speed taken out), is the stand-alone H512 evaluation better or worse than combo29's? |
| Candidate | `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`, md5 `5c46cd2d43bc051df1a39e841487b95f`, options `NNUEArchFile` = candidate 1, `NNUEArch` = true |
| Net | candidate 1, `_work\nets\h512_cand_seen02000003072.fnn3`, md5 `d920a15c5b05040a3ef71a872192ec1b` |
| Opponent | original lock exe `forge-combo29/windows/forge_clang_combo29_trial_w6.exe`, md5 `c0051c99695f48bf93272d96fe7548c3` |
| Limit | **250,000 nodes per move for both engines, no clock** (`go nodes 250000`) |
| Budget | **3,000 games = 1,500 opening pairs**, fixed, no early stop |
| Openings | `UHO_Lichess_4852_v1.epd`, random order, seed 2026111108, each opening with both colours |
| Engines | Threads 1, Hash 16 MB, OwnBook false |
| Concurrency | 12 games at once. The GPU trainer of this job runs at the same time (owner's instruction); a clock-free match is not affected by that |
| Adjudication | none |
| Runner | `h512/tools/run_match_nodes.sh` (fastchess 1.8.2 alpha, `-recover`) |
| Analysis | `h512/tools/match_elo.py`, opening pairs as units, 95 % interval |

Checked before the start with an 8-game run (`_work\match\nodes_smoke8`, not counted): both engines accept the node
limit, games end normally, no clock is used. The node count in the PGN comments is the engine's last `info` line
before its move, so it reads below 250,000; the search itself stops at the limit.

How to read the result: both engines have the same search code. At equal nodes the candidate spends about 17 % less
time per move (it is 1.20x as fast). So equal nodes is a handicap for the candidate compared with equal time.
