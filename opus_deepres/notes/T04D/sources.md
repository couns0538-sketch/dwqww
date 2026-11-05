# T04D sources (one line per source read: time | source | licence tier | what it gave | card id)
| time | source | licence | gave | card |
|---|---|---|---|---|
| 00:00 | github.com/official-stockfish/Stockfish commit titles + fishtest blocks since 2024-01-01 (tools/mine_commits.py, cache 22:50, 1,368 commits) | GPL-3.0 ideas only (titles/messages) | candidate list: 250 search-ish commits with STC+LTC blocks | listing |
| 00:03 | Stockfish@9cc15b3049 message + fishtest runs 67abc9aaa04df5eb8dbeb452 (STC) / 67abcd7ba04df5eb8dbeb96c (LTC) via api/get_run | GPL-3.0 ideas only | more LMR at cut nodes without TT move: STC 10+0.1 +2.72 +-1.74 n=42,304 [0,2]; LTC 60+0.6 +3.35 +-1.81 n=32,334 [0.5,2.5]; UHO_Lichess_4852_v1, 1 thread | T04D-01 |
| 00:03 | Stockfish@c19a6ea53c message (PR 5895) | GPL-3.0 ideas only | shallower PV re-search when the (unreduced) result is bad: STC +3.65 +-2.05 n=29,216 [0,2]; LTC +3.25 +-1.77 n=33,168 [0.5,2.5] (TC/book not fetched; fishtest STC/LTC defaults) | evidence for T04-02 (no card) |
