# T07 adversarial verify (start 23:09 PC clock, stop by 23:24)
Format: card | claim | verdict | evidence

## 1. Source numbers (both cards are full cards; every cited number re-opened)
T07-01 | STC 10+0.1, 127,360 games, LLR 2.97 (-2.94, 2.94) [0, 2], Ptnml 169/13235/36487/13589/200 | CONFIRMED | commit message of https://github.com/official-stockfish/Stockfish/commit/5ca4bfe72b (gh api, message only) and fishtest API https://tests.stockfishchess.org/api/get_run/6a8738495b1b38ebda864ed0 (W 32487 L 32071 D 62802, llr 2.970)
T07-01 | STC +1.13 +- 0.90 (own pentanomial calc) | CONFIRMED | recomputed from the printed Ptnml: +1.13 +- 0.90
T07-01 | LTC 60+0.6 +1.08 +- 0.69, 191,328 games, LLR 2.94 [0.5, 2.5] | CONFIRMED | commit message + https://tests.stockfishchess.org/api/get_run/6a8ade7a08c0f6a39c9e79cc ; recomputed +1.08 +- 0.69
T07-01 | non-regression 15+0 +2.23 +- 1.81 (33,984) and 40/10 +1.44 +- 1.51 (47,872), both [-1.75, 0.25] | CONFIRMED (recomputed) | commit message; note added to card: the 40/10 run also includes the cyclic-TM fix of PR 7117 (commit text), so it is not this change alone
T07-01 | "Book and thread count: not checked (pages unreadable)" | CORRECTED | fishtest API get_run (no bot check at 23:12): STC and LTC both Threads 1, book UHO_Lichess_4852_v1.epd, dev tag time_advantage_linear3 vs master; 15+0 and 40/10 runs not checked
T07-01 | 40/10 link printed cut short in the commit | CONFIRMED | commit message shows .../6a967e3408c0f6a39c9e91 (22 hex, fishtest ids are 24)
T07-01 | date 2026-09-09, title, two skip cases (nodestime; cyclic TC at movestogo 1) | CONFIRMED | commit message (2026-09-09T16:44:29Z); the commit also says "No functional change" (bench unchanged), in line with the card's point that bench pins prove nothing about ON
T07-02 | PR 438 / 8e3fc66e52: STC 8.0+0.08 Threads=1 Hash=16MB +1.42 +- 1.15, 92,920 games, LLR 2.91 (-2.25, 2.89) [0, 3], Penta [382, 10602, 24096, 11014, 366] | CONFIRMED | commit message of https://github.com/PGG106/Alexandria/commit/8e3fc66e52 ; recomputed +1.42 +- 1.15
T07-02 | PR 438 LTC 40.0+0.40 Threads=1 Hash=64MB +1.71 +- 1.37, 56,588 games, LLR 2.90 [0, 3] | CONFIRMED | same commit message; recomputed +1.71 +- 1.37
T07-02 | PR 438 book | UNVERIFIABLE | the commit message has no book and no test link (the card says so)
T07-02 | PR 438 date 2024-06-24 and title | CONFIRMED | gh api pulls/438: merged 2024-06-24T09:11:38Z, merge commit 8e3fc66e52
T07-02 | PR 618 / 49391d7b70: STC +4.24 +- 2.63, 16,560 games, LLR 2.89 [0, 3]; LTC +4.00 +- 2.49, 16,844 games, LLR 2.91 | CONFIRMED | commit message + https://chess.swehosting.se/test/14309/ and /14310/ ; recomputed +4.24 +- 2.63 / +4.00 +- 2.49
T07-02 | PR 618 branch tm-scoreloss-iso vs master, book UHO_Lichess_4852_v1.epd, Threads 1, Hash 16 / 64 MB | CONFIRMED | OpenBench pages 14309 and 14310
T07-02 | PR 618 commits = "Add TM score-loss scaling factor" + "bump version"; date 2026-07-22 | CONFIRMED | gh api pulls/618/commits (7efa3248c8, 7fe94b9fec); commit 2026-07-22T20:50:51Z
T07-02 | "618 most likely measures score LOSS" | CONFIRMED as a reading of titles only (commit title + branch name); mechanism itself UNVERIFIABLE by rule (source not read) | PR 618 commit title + OpenBench branch tm-scoreloss-iso
T07-02 | PR 438 has no test links in commit or PR | CONFIRMED | gh api pulls/438: body empty (23:17); commit message has none
T07-01 | book / threads of the 15+0 and 40/10 runs | UNVERIFIABLE | not opened (time box); the 40/10 link is truncated in the commit

## 2. Reading rule
T07-01, T07-02, notes | no /blob/, raw or source-file links of GPL / AGPL / unlicensed repos | CONFIRMED | grep of cards/T07 and notes/T07: links are commit pages, PR pages, fishtest / OpenBench test logs only
T07-01, T07-02 | what was read = commit messages, PR text, PR commit titles, test logs | CONFIRMED (as far as the files and sources.md show) | this verify read only commit messages (gh api --jq .commit.message), PR text, PR commit titles and test pages; no diff
T07-01, T07-02 | own option values, not the source's tuned constants | UNVERIFIABLE (the source must not be read) | no number in either OFF design appears in the commit / PR / test text read; the STC test message of T07-01 says "linear function instead of sqrt", consistent with the card's own linear f, no constant carried over
process | helper ptnml.py written to the session scratchpad on C: | VIOLATION of the where-to-write rule (self-reported by the worker; no card content affected; not a reading-rule violation, Status lines unchanged) | worker hand-back, pending list

## 3. Licence rows (tools/licence_at.py --row re-run 23:10)
licences.md | official-stockfish/Stockfish 5ca4bfe72b text guess AGPL-3.0 | CORRECTED | re-run gives GPL-3.0 in the text column too (Copying.txt, api GPL-3.0); use (ideas only) unchanged
licences.md | PGG106/Alexandria 49391d7b70 text guess AGPL-3.0 | CORRECTED | re-run gives GPL-3.0 (LICENSE.md, api GPL-3.0); use unchanged
licences.md | PGG106/Alexandria 8e3fc66e52 GPL-3.0 | CONFIRMED | re-run identical

## 4. Forge has it (lock src_al1s198_clean)
T07-01 | forge_has.sh 'opponent|time_advantage|their_time' -> 2 unrelated hits nnue.hpp:12, board.cpp:1018 | CONFIRMED | re-run, same 2 hits
T07-01 | src/uci.cpp:99-102 keeps only the side to move's clock / increment | CONFIRMED | 99 wtime, 100 btime, 101 winc, 102 binc, each stored only if side matches
T07-01 | include/forge/search.hpp:19-41 SearchLimits has no opponent fields | CONFIRMED | struct at 19-40
T07-01 | Forge has no nodestime | CONFIRMED | forge_has.sh 'nodestime|nodes_time|NodesTime' -> 0 hits (23:17)
T07-01 | search.cpp 1268-1270 increment / sudden-death branch, 1264-1267 cyclic | CONFIRMED | 1264 `if (limits.moves_to_go > 0)`, 1268 `} else {`, 1269 soft, 1270 hard
T07-02 | forge_has.sh 'score_stab|stable_score|eval_stab' -> 0 hits | CONFIRMED | re-run, 0 hits
T07-02 | 1436-1438 best-move stability, 1441-1449 node effort, 1451-1454 falling eval (extend-only, drop capped at 150), 1455 TmMinFactorPercent, 1374 previous_score = ValueNone per search, 1428-1429 | CONFIRMED | lock search.cpp read at those lines

## 5. Local records, labels, lint
T07-01 | CPU 10-19 h at "640-980 games/h seen in D:/o15/reports/gates_20261103.html" | CORRECTED | games/h column: 643.1 (gate13) and ~963-1011 are the older gates vs h256e12 / ep10; the UHO gates vs the lock (uho*_vs_AL1lp) ran 430.6-455.7 games/h and all *_vs_AL1* rows 430-502 -> 10-12k games = about 20-28 h (card note added)
T07-02 | CPU 7-28 h at the same 640-980 games/h | CORRECTED | same file -> 7k-18k games = about 14-42 h (card note added)
T07-01 | crew gates stop at 1000-1500 games ("Cap with no decision") | CONFIRMED (1000 end) | notes/TRIED_GATES.md: 79 rows "Cap with no decision", e.g. gate12 / gate14 / gate15 at 1000 games; the 1500 end not checked
T07-01, T07-02 | Forge-side estimates labelled UNPROVEN | CONFIRMED | one **UNPROVEN** on each Forge-estimate line; the game counts in Effort refer to those estimates
all T07 files | no vendor / model-company names | CONFIRMED | grep: 0 hits in cards/T07 and notes/T07
UCI_EDGE_CASES.md | case 4 movestogo 1 -> soft 4995, hard 7992 | CONFIRMED | search.cpp 1264-1267 with available 9990
UCI_EDGE_CASES.md | case 5 movestogo 0 -> 1 (up to 80 % of the clock) | CONFIRMED | uci.cpp:95 max(1, value); hard = available * 4 / 5
UCI_EDGE_CASES.md | case 7 movestogo 200 -> mtg 50, soft 195, hard 780 | CONFIRMED | search.cpp 1265-1267
cards/T07/*.md | card_lint after the verify edits (23:15) | CONFIRMED clean | 0 findings, 0 PENDING in both cards (T07-01 kept at <= 60 lines)
Totals: 40 checks - 31 CONFIRMED, 5 CORRECTED (T07-01 book / threads + fishtest readable, 2 CPU-hour rates, 2 licence text guesses), 3 UNVERIFIABLE (PR 438 book; 15+0 and 40/10 book / threads; own option values vs the sources' constants; PR 618's mechanism is also unverifiable by rule), 1 VIOLATION (process: helper written to the C: scratchpad, self-reported); no reading-rule violation, Status lines unchanged.
