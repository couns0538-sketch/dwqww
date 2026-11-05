# T07 sources (time management) - one line per source read
Format: n | url or repo@sha | licence tier | what it gave | card id or "no card"

(baseline, not counted: lock FD3A5190 own source read-only - src/search.cpp 1249-1271 time allocation, 1430-1453 soft-stop
factors (best-move stability 3/6 iterations, node-fraction effort, falling eval vs previous iteration, min factor),
679-690 hard stop every 1024 nodes; src/uci.cpp 65-110 go parser, 287-420 go / ponderhit / stop; Move Overhead 10 ms)
1 | official-stockfish/Stockfish commit titles 2021-06..2026-10 (tools/mine_commits.py --grep TM words) | GPL-3.0 ideas only | TM change list with fishtest W/L/D: time-disadvantage 5ca4bfe, complexity TM 2b03723 (later simplified away 38a80c0), eval TM e636f73 (removed ec8288f), smoother reduction fe7b9b1, sudden death 23493de | T07-01, T07-02
2 | https://github.com/official-stockfish/Stockfish/pull/7113 (commit 5ca4bfe72b, PR text + 4 fishtest links) | GPL-3.0 ideas only | time-disadvantage TM: STC 10+0.1 +1.13+-0.90 n=127360 LLR 2.97 [0,2]; LTC 60+0.6 +1.08+-0.69 n=191328 [0.5,2.5]; SD 15+0 and 40/10 non-reg | T07-01
3 | PGG106/Alexandria commit titles (tools/mine_commits.py --grep TM words) + commits 49391d7b70, 8e3fc66e52, 807a16c597 | GPL-3.0 ideas only | score stability TM #618: STC 8+0.08 +4.24+-2.63 n=16560 LLR 2.89 [0,3]; LTC 40+0.4 +4.00+-2.49 n=16844; older eval stability #438 STC +1.42+-1.15 n=92920 / LTC +1.71+-1.37 n=56588 | T07-02
4 | https://github.com/PGG106/Alexandria/pull/618 (PR text) | GPL-3.0 ideas only | OpenBench links chess.swehosting.se/test/14309 (STC) and /14310 (LTC); no mechanism text in the PR body | T07-02
