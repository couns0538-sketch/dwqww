# JOB E screening match: declared before the first game (2026-11-11 18:14 PC clock)

Not the crew gate and not a lock claim. Settings are Job D's match protocol unchanged (`fair_eval/tools/run_match.sh`).

| Item | Value |
|---|---|
| Candidate | `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`, md5 `5c46cd2d43bc051df1a39e841487b95f`, options `NNUEArchFile` = frozen net, `NNUEArch` = true |
| Frozen net | `_work\nets\h512_cand_seen02000003072.fnn3`, md5 `d920a15c5b05040a3ef71a872192ec1b` |
| Opponent | original lock exe `forge-combo29/windows/forge_clang_combo29_trial_w6.exe`, md5 `c0051c99695f48bf93272d96fe7548c3` |
| Budget | **3,000 games = 1,500 opening pairs**, fixed. No early stop for a favourable or unfavourable score |
| Openings | `C:/Users/Administrator/grok-pc/coder-fuzz/UHO_Lichess_4852_v1.epd`, random order, seed 2026111105, each opening played with both colours |
| Clock | 6 s + 0.06 s per move for both engines, time margin 1000 ms |
| Engines | Threads 1, Hash 16 MB, OwnBook false |
| Concurrency | 12 games at once on the 16 logical CPUs; no other heavy work of this job during the match |
| Adjudication | none (games end by mate, stalemate, rule draws or time) |
| Runner | fastchess `C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe`, `-recover` |
| Analysis | pentanomial over opening pairs: mean pair score, 95 % normal interval with pairs as units, mapped to Elo (`h512/tools/match_elo.py`, checked against fastchess's own figure on Job D's U8 match). W/D/L, crashes and time losses per side reported |
| Stop conditions | only: the fixed budget, a crash loop, or a resource boundary |

Known hazard, stated in advance: the owner's `resource_guard.ps1` suspends this fastchess process for about 5 s when
its thermal latch trips (CPU above 90 C or GPU edge above 83 C). That happened three times during Job D's matches
and cost both sides games on time. If it happens here, the affected games are reported by side, together with the
result without games that ended on time.
