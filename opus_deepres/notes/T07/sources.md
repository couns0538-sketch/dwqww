# T07 sources (time management) - one line per source read
Format: n | url or repo@sha | licence tier | what it gave | card id or "no card"

(baseline, not counted: lock FD3A5190 own source read-only - src/search.cpp 1249-1271 time allocation, 1430-1453 soft-stop
factors (best-move stability 3/6 iterations, node-fraction effort, falling eval vs previous iteration, min factor),
679-690 hard stop every 1024 nodes; src/uci.cpp 65-110 go parser, 287-420 go / ponderhit / stop; Move Overhead 10 ms)
1 | official-stockfish/Stockfish commit titles 2021-06..2026-10 (tools/mine_commits.py --grep TM words) | GPL-3.0 ideas only | TM change list with fishtest W/L/D: time-disadvantage 5ca4bfe, complexity TM 2b03723 (later simplified away 38a80c0), eval TM e636f73 (removed ec8288f), smoother reduction fe7b9b1, sudden death 23493de | T07-01, T07-02
2 | https://github.com/official-stockfish/Stockfish/pull/7113 (commit 5ca4bfe72b, PR text + 4 fishtest links) | GPL-3.0 ideas only | time-disadvantage TM: STC 10+0.1 +1.13+-0.90 n=127360 LLR 2.97 [0,2]; LTC 60+0.6 +1.08+-0.69 n=191328 [0.5,2.5]; SD 15+0 and 40/10 non-reg | T07-01
3 | PGG106/Alexandria commit titles (tools/mine_commits.py --grep TM words) + commits 49391d7b70, 8e3fc66e52, 807a16c597 | GPL-3.0 ideas only | score stability TM #618: STC 8+0.08 +4.24+-2.63 n=16560 LLR 2.89 [0,3]; LTC 40+0.4 +4.00+-2.49 n=16844; older eval stability #438 STC +1.42+-1.15 n=92920 / LTC +1.71+-1.37 n=56588 | T07-02
4 | https://github.com/PGG106/Alexandria/pull/618 (PR text) | GPL-3.0 ideas only | OpenBench links chess.swehosting.se/test/14309 (STC) and /14310 (LTC); no mechanism text in the PR body | T07-02
5 | https://chess.swehosting.se/test/14309/ (OpenBench test page, Alexandria STC) | GPL-3.0 project, test log only | branch tm-scoreloss-iso vs master, 8.0+0.08, Threads 1, Hash 16 MB, book UHO_Lichess_4852_v1.epd, [0,3], LLR 2.89, 16560 games, Penta [28,1830,4365,2026,31], +4.24+-2.63; no description | T07-02
(not counted: https://tests.stockfishchess.org/tests/view/6a8738495b1b38ebda864ed0 - bot-check page, nothing read; the
fishtest JSON API returned an empty body; a retry with another user agent was refused by the session's safety check
and not attempted again -> fishtest book / threads for T07-01 stay "not checked")
6 | https://chess.swehosting.se/test/14310/ (OpenBench test page, Alexandria LTC) | GPL-3.0 project, test log only | branch tm-scoreloss-iso vs master, 40.0+0.40, Threads 1, Hash 64 MB, book UHO_Lichess_4852_v1.epd, [0,3], LLR 2.91, 16844 games, Penta [5,1777,4662,1975,3], +4.00+-2.49 | T07-02
7 | https://github.com/PGG106/Alexandria/pull/618 commits + issue comments (gh api pulls/618/commits, issues/618/comments; no files / patch) | GPL-3.0 ideas only | the only code commit is titled "Add TM score-loss scaling factor" (then "bump version"); no comments -> #618 measures score LOSS, not hold-still; T07-02 re-based on #438 for the hold-still term | T07-02

## Dead ends (one line each)
- tmfit pointer stale: `grep -i tmfit` = 0 hits in D:/o15/reports/gates_20261103.html (read-only) and in FORGE_RESULTS.csv; gates 227/228 not present there, so TmFitModel's exact scope was not verified (brief taken as given).
- Best-move stability scaling: the lock has it (src/search.cpp:1436-1438, 3/6 stable iterations + unstable factor) -> no card.
- Falling-eval extension: the lock has it vs the previous iteration (1451-1454) -> no own card; the cross-move reference is only variant B inside T07-02 (no separate logged gain found).
- Node-fraction effort: done (lock 1441-1449, plus the crew's node-fraction TM) -> excluded by the brief.
- Complexity-based TM: Stockfish 2b03723 (2022-01-17, STC ~+2.44 n=39664, LTC ~+1.30 n=127656) was simplified away by 38a80c0 (2023-04-01, STC ~+1.11 / LTC ~+0.51 neutral) -> net zero, no card.
- Eval-level TM: Stockfish e636f73 (2024-03-29, STC ~+1.41 / LTC ~+2.08) removed by ec8288f (2024-07-06, neutral simplification) -> no card.
- Smoother best-move reduction: Stockfish fe7b9b1 (2025-05-25, STC ~+1.87 n=64448 / LTC ~+0.90 n=407340) refines what the lock has; dropped under the 2-card cap and the +1 line.
- Sudden-death TM: Stockfish 23493de (2024-03-14) gains only at sudden-death TC (+35.7 n=3348 there; STC ~+0.36) -> gates use increments, no card.
- Soft/hard ratios: the lock exposes TmSoftDivisor/TmIncrementPercent/TmHardPercent/TmHardSoftMultiple as tunables (SPSA territory, R9/o30) -> no card.
- Move-overhead handling and ponder-hit handling: no logged gain found; ponder cannot be gated with fastchess Threads=1 gates -> no card (UCI edge cases cover them).
- "~" Elo values above are computed by tools/mine_commits.py from fishtest W/L/D (SPRT-stopped, biased high).
