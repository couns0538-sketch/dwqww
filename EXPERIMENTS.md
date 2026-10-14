# Chess Engine Forge 5.31.0 -> 6.4.0: experiment record

This document lists every measured experiment of the 6.x strength work
(12-14 October 2026, four release rounds): what was tried, how it was measured, the exact result and
whether it was adopted. Every match number below was re-read from the match
directory's `console.txt` (last `Games:` line, and for SPRT runs the last
`LLR`/`accepted` line) and from the game count of its `games.pgn`; the games
themselves are in `all-match-pgns.zip` next to this file (index at the end).

## Baseline and releases

| Version | `bench 11` | Summary |
| --- | --- | --- |
| 5.31.0 | - | Starting point: mailbox move generator, no LMR below depth 10, no futility/LMP/SEE pruning, crude evaluation. 10.0 % against Stockfish 19 at `UCI_Elo 2800`. |
| 6.0.0 | 513922 | Rewrote move generation (magic bitboards), search (PVS, modern pruning/reductions, correction history, staged move picker) and evaluation (parametrised tapered evaluation, Texel-tuned on 22k self-play games). |
| 6.1.0 | 422451 | Lazy SMP (`Threads`), unlisted tuning options for all search constants, NNUE infrastructure and trainer (`nnue_train`) next to the Texel tools (`forge_extract`, `forge_texel`), evaluation retuned on 61.5k games including random openings. |
| 6.2.0 | 340241 | Embedded opening book (2616 entries), cutoff-count LMR, material correction history, new evaluation terms with a retuned table, lazy move sorting, falling-evaluation time management, Zen 4 builds. |
| 6.3.0 | 344040 | Late-move pruning and history-bonus constants retuned by SPRT (`LmpBase=4`, `HistoryBonusQuadratic=20`, `HistoryBonusMax=2048`, +16 Elo at fixed nodes); four other search constants, two pawn-structure evaluation terms and a second NNUE net tested and rejected. |
| 6.4.0 | 417491 | First shipped neural network: a residual 768 -> 128x2 SCReLU net trained (new `--residual` trainer mode, pure search-score targets) on what the hand-crafted evaluation gets wrong and added to it at search time (+86 Elo at 20k nodes, +45 Elo at 10+0.1 over 6.3.0); five search constants tested by SPRT and rejected; `-ffp-contract=off` so every build shares one `bench` signature. |

The `bench 11` signatures were re-run on the binaries that played the matches
(`forge_final` = 6.0.0, `forge_v61` = 6.1.0, `forge_v62` = 6.2.0, `forge_v63` =
6.3.0, `forge_v64` = 6.4.0); the 6.2.0 pre-release binary `forge_v62a` gives 335062.

## How things were measured

- **Stockfish validation matches.** Stockfish 19 (`stockfish-linux-x86-64-universal`)
  with `UCI_LimitStrength=true`, `UCI_Elo` 2800 or 3000, `Threads=1`, `Hash=64`;
  Forge with `Hash=64` and default options, one thread. fastchess alpha 1.8.2
  (`20260726-f618e34`), `-repeat` colour-swapped pairs, `-recover`,
  `timemargin=200`, openings `8moves_v3.pgn` (random order, 16 plies), no
  adjudication. Concurrency 3-4 on a four-core VM. Every game of the nine
  matches (1120 games) has `[Termination "normal"]`; no time forfeits.
- **Fixed-node self-play tests.** Same fastchess, both engines limited to
  20,000 or 25,000 nodes per move (stated per test), `Hash=32`, `8moves_v3`
  openings (random order, 16 plies) unless noted, draw adjudication from move 40
  (8 consecutive moves within +/-10 cp), resign adjudication (4 moves beyond
  800 cp), 300-move limit, concurrency 2-4.
- **SPRT tests.** fastchess `-sprt elo0=0 elo1=5 alpha=0.05 beta=0.05
  model=normalized`, bounds (-2.94, 2.94), 20,000 nodes per move, test build
  with one UCI option changed (items 35 and 34: two or three options) vs the
  same binary with default options (`/tmp/tools/sprt.sh`), rating report every
  100 games, at most 4000 rounds (8000 games). The 6.3.0 round (14 October)
  used the pre-stated stopping rule "adopt if H1 is accepted, or if LLR >= 1.0
  with a score >= 51.5 % at a 60-minute cap; reject if H0 is accepted or the
  score is <= 50.5 % after 1500 or more games"; the `base` engine of that
  round is the 6.2.0 release source built with `-DFORGE_EXPOSE_TUNABLES=ON`
  (`bench 11` = 340241).
  The 6.4.0 round (14 October) used the same rule; its first two SPRTs (items
  36 and 37, 2 cores while a self-play data stream used the other two) ran on
  the 6.3.0 release source with tunables exposed (`bench 11` = 344040), the
  last three (items 41-43, 4 cores) on the same source with the adopted
  residual network compiled in (`bench 11` = 417491).
- **Real-clock self-play tests.** 10+0.1 or 8+0.08, `Hash=64` (item 39:
  `Hash=32`, `timemargin=200`, concurrency 4), no adjudication.
- **Tuning loss.** `forge_texel` and `nnue_train` report the mean squared error
  between the sigmoid of the evaluation and a 0.5/0.5 blend of game result and
  search score, on the stated position set.
  `nnue_train --lambda L` blends L parts game result with (1 - L) parts
  search score for both training targets and the reported validation loss, so
  losses are only comparable at the same lambda; the 6.4.0 tables state the
  lambda and give the hand-crafted evaluation's loss in the same metric
  (computed with a residual net whose output layer is zero).
- **Elo columns.** Both figures printed by fastchess are given: `Elo` (logistic
  estimate) and `nElo` (normalized Elo), each with its 95 % interval. The Elo
  figures quoted in the release notes for items 2-5 (+66, +158, +331, +224) are
  the `nElo` values; those for items 1, 6, 7 and 21 (-382, -16, +10, +21) are
  the `Elo` values.

### Verification notes

Differences between the pre-stated figures and the records:

1. Item 9 (`v3trial_vs_v2`) ran to 400 games (186W 122L 92D = 58.00 %); the
   figure "200 games, 99W 58L 43D = 60.25 %" is the interim report at game 200
   (line 414 of its `console.txt`). The 400-game result is used below.
2. Item 22 (`sprt_matcorr`) was stated approximately ("3000-3200 games,
   ~50.6-50.8 %, LLR ~0.3-0.6"); the console's last report is 3200 games,
   941W 892L 1367D = 50.77 %, LLR 0.60.
3. The four SPRT runs that were stopped before reaching a bound (`sprt_matcorr`,
   `sprt_nmp2`, `sprt_capfut`, `sprt_faillow`) report every 100 games, so the PGN files hold
   13, 81, 82 and 97 more games than the last console report (games finished
   between the last report and the stop). The console figures are used in the
   tables; the full-PGN tallies are given in the index.
4. Item 14: the NNUE training log (`train1.log`) ends at epoch 40 with loss
   0.015971; the pre-stated 0.0164 is the epoch-25 value. 0.0160 is used below.
5. Item 24: no `/tmp/matches/sprt_see100` or `/tmp/matches/sprt_asp12`
   directory exists (the runs were killed almost immediately and left no
   records); they are listed as not run and have no PGN in the archive.
6. The 25k/20k-node tests used `Hash=32`, the real-clock tests `Hash=64`.

Everything else matched exactly (games, W/L/D, percentages, LLR values, PGN
game counts, `bench 11` signatures).

## 1. Stockfish validation matches

| # | Forge build (binary) | SF19 `UCI_Elo` | TC | Games | W / L / D | Score | Elo | nElo | Directory | Archive file |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5.31.0, original upload (`base531`) | 2800 | 10+0.1 | 20 | 1 / 17 / 2 | 10.00 % | -382 (interval undefined) | -593 +/- 152 | `base531_vs_sf2800_073642` | `forge-5.31.0-vs-sf19-2800-10+0.1.pgn` |
| 2 | 6.0.0 initial rewrite, hand-set evaluation (`v1`) | 2800 | 10+0.1 | 100 | 47 / 32 / 21 | 57.50 % | +53 +/- 56 | +66 +/- 68 | `v1_vs_sf2800_080705` | `forge-6.0.0-handset-eval-vs-sf19-2800-10+0.1.pgn` |
| 3 | 6.0.0 shipped, Texel-tuned table (`v3`) | 2800 | 10+0.1 | 200 | 118 / 42 / 40 | 69.00 % | +139 +/- 48 | +158 +/- 48 | `v3_vs_sf2800_093253` | `forge-6.0.0-vs-sf19-2800-10+0.1.pgn` |
| 4 | 6.0.0 shipped (`final`) | 2800 | 30+0.3 | 100 | 79 / 14 / 7 | 82.50 % | +269 +/- 84 | +331 +/- 68 | `final_vs_sf2800_110852` | `forge-6.0.0-vs-sf19-2800-30+0.3.pgn` |
| 5 | 6.1.0 shipped (`v61`) | 2800 | 10+0.1 | 200 | 134 / 34 / 32 | 75.00 % | +191 +/- 50 | +224 +/- 48 | `v61_vs_sf2800_140715` | `forge-6.1.0-vs-sf19-2800-10+0.1.pgn` |
| 6 | 6.2.0 pre-release build, before the move-picker change, `bench 11` = 335062 (`v62a`); ran under heavy CPU load from parallel tests | 3000 | 10+0.1 | 200 | 66 / 75 / 59 | 47.75 % | -16 +/- 42 | -18 +/- 48 | `v62a_vs_sf3000_102121` | `forge-6.2.0pre-vs-sf19-3000-10+0.1.pgn` |
| 7 | 6.2.0 release build (`v62`) | 3000 | 20+0.2 | 100 | 35 / 32 / 33 | 51.50 % | +10 +/- 60 | +12 +/- 68 | `v62_vs_sf3000_123635` | `forge-6.2.0-vs-sf19-3000-20+0.2.pgn` |
| 8 | 6.3.0 release build (`v63`) | 3000 | 20+0.2 | 100 | 33 / 33 / 34 | 50.00 % | 0 +/- 54 | 0 +/- 68 | `v63_vs_sf3000_095408` | `forge-6.3.0-vs-sf19-3000-20+0.2.pgn` |
| 9 | 6.4.0 release build (`v64`, residual NNUE) | 3000 | 20+0.2 | 100 | 35 / 30 / 35 | 52.50 % | +17 +/- 53 | +23 +/- 68 | `v64_vs_sf3000_170334` | `forge-6.4.0-vs-sf19-3000-20+0.2.pgn` |

Stockfish's limited-strength play does not scale with the clock while Forge's
does, so the margin at 2800 grows from 69.0 % (10+0.1) to 82.5 % (30+0.3) for
the same 6.0.0 binary.

## 2. Adopted changes

Item numbers continue the numbering used during development (8-27 for the
6.0.0-6.2.0 work, 28-35 for the 6.3.0 round, 36-43 for the 6.4.0 round); the
order is chronological within each round. "vs" names the baseline binary.

| # | Change tried | Baseline | Measurement | Result (console) | Elo / nElo | Decision | Directory |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | Correction history (static-eval correction indexed by pawn hash), sorted staged move picker, TT prefetch (`v2`) | Initial rewrite with the same hand-set evaluation (`v1`) | 25k nodes/move, 300 games | 101W 82L 117D = 53.17 % | +22 +/- 32 / +27 +/- 39 | Adopted (6.0.0) | `v2_vs_v1_nodes` |
| 10 | Regularised Texel fit of the whole parameter table: 22,000 self-play games at 10k nodes/move -> 1,715,952 quiet positions (`forge_extract`), `forge_texel` Adam, lr 1.0 halved every 200 epochs, 600 epochs, lambda 0.5, regularisation 2e-9, rarity-scaled steps (threshold 0.5 %) (`tuned_full`) | `v2` (hand-set table) | 25k nodes/move, 300 games | 167W 59L 74D = 68.00 % | +131 +/- 39 / +147 +/- 39 | Adopted as the 6.0.0 table | `tuned_full_vs_v2` |
| 17 | Lazy SMP: `Threads=4` (shared TT and stop flag, private histories/eval caches) | Same binary with `Threads=1` (6.1.0 development build, identifies as 6.0.0) | 8+0.08 real clock, concurrency 1, no adjudication, 50 games | 26W 1L 23D = 75.00 % | +191 +/- 79 / +290 +/- 96 | Feature adopted (6.1.0) | `smp4_vs_1` |
| 15 | Retune on 61,536 games (44k from `8moves_v3` openings incl. 22k played by the tuned engine, plus 17.5k from random openings; 4,674,912 positions) (`t3`) | 6.0.0 table in the 6.1.0 development build (`cur`) | 20k nodes/move, `8moves_v3` openings, 300 games | 100W 81L 119D = 53.17 % | +22 +/- 29 / +30 +/- 39 | Adopted (6.1.0 table) | `t3_vs_cur_book` |
| 16 | Same comparison as 15 | `cur` | 20k nodes/move, random EPD openings (`book.epd`), 300 games | 130W 106L 64D = 54.00 % | +28 +/- 24 / +45 +/- 39 | Adopted (6.1.0 table) | `t3_vs_cur_epd` |
| 18 | New evaluation terms (material imbalance by own pawn count for knights and rooks, rooks behind own/enemy passed pawns, space, long-diagonal bishop, weak queen, weak unopposed pawn, king-pawn distance), king-safety attack weights as parameters, shelter divisor 8 -> 4, whole table refitted on the 61.5k-game data set (`t4`) | 6.1.0 release (`v61`) | 20k nodes/move, 400 games | 127W 115L 158D = 51.50 % | +10 +/- 27 / +13 +/- 34 | Adopted (6.2.0) | `t4_vs_v61` |
| 21 | Cutoff-count LMR: reduce a late move one ply more when the child node has already produced more than 3 beta cutoffs (`LmrCutoffThreshold=3`) | Same development binary, default options (`base`, 6.2.0 dev build with `-DFORGE_EXPOSE_TUNABLES=ON`) | SPRT elo0=0 elo1=5, 20k nodes/move | H1 accepted after 2804 games: 894W 726L 1184D = 53.00 %, LLR 2.96 (43 min 20 s) | +20.8 +/- 9.5 / +28.3 +/- 12.9 | Adopted (6.2.0, default 3) | `sprt_cutoff3` |
| 22 | Material correction history: second correction table indexed by the material configuration, added with the same weight as the pawn correction (`MaterialCorrectionWeight=100`) | `base` | SPRT elo0=0 elo1=5, 20k nodes/move, stopped early (45 min) | 3200 games: 941W 892L 1367D = 50.77 %, LLR 0.60 (inconclusive) | +5.3 +/- 9.1 / +7.1 +/- 12.0 | Adopted as a low-risk standard technique (default 100) | `sprt_matcorr` |
| 19 | Built-in opening book: embedded book of 2616 entries generated by the engine's own searches (`forge_bookgen expand`, 1.5M nodes per move), `OwnBook=true` | Same binary with `OwnBook=false` | 10+0.1 real clock from the start position (no opening file), no adjudication, 120 games (60 pairs) | 18W 11L 91D = 52.92 % | +20 +/- 30 / +42 +/- 62 | Adopted (book on by default) | `book_on_off` |
| 20 | Lazy move-list sorting: the first few moves are selected on demand, the rest of the list is sorted only when reached (`pick`) | Previous picker with a full sort (`v62a`, 6.2.0 pre-release) | 20k nodes/move, 400 games | 110W 98L 192D = 51.50 % | +10 +/- 24 / +15 +/- 34 | Adopted for speed; only tie-breaking among equally scored moves differs, so the result is treated as neutral at fixed nodes | `pick_vs_v62a` |
| 35 | Late-move pruning keeps one more quiet move per depth (`LmpBase=4`) together with a faster-growing, later-saturating history bonus (`HistoryBonusMax=2048`, `HistoryBonusQuadratic=20`); the two halves had each run to the 8000-game limit alone without reaching a bound (items 33 and 34), so the combination was tested in the round's spare time | `base` (6.2.0 release source, tunables exposed) | SPRT elo0=0 elo1=5, 20k nodes/move, concurrency 4 | H1 accepted after 3670 games: 1122W 948L 1600D = 52.37 %, LLR 2.97 (22 min 20 s) | +16.5 +/- 8.4 / +22.1 +/- 11.2 | Adopted (6.3.0 defaults; `bench 11` 340241 -> 344040) | `sprt63_lmp4_histbonus` |
| 38 | Residual NNUE: 768 -> 128x2 SCReLU net trained with the new `--residual` trainer mode (network output added to the hand-crafted evaluation before the sigmoid, output layer initialised to zero) on 13,428,686 self-play positions with pure search-score targets (`--lambda 0`, lr 0.001, batch 16384, best of 8 epochs = epoch 2); engine adds the net's centipawns to the hand-crafted score (`res128` = 6.3.0 source + `src/nnue_weights.inc`, `bench 11` = 417491) | 6.3.0 release (`v63`) | 20k nodes/move, 500 games, concurrency 4 | 209W 88L 203D = 62.10 % (2 min 44 s) | +86 +/- 24 / +114 +/- 30 | Passed the pre-stated fixed-node gate (>= 53 %); confirmed at a real clock in item 39 and adopted (6.4.0) | `res128_vs_v63` |
| 39 | Same `res128` build at a real clock | `v63` | 10+0.1, `Hash=32`, `timemargin=200`, concurrency 4, no adjudication, 200 games | 49W 23L 128D = 56.50 %; all 200 games terminated normally, no time losses | +45 +/- 26 / +84 +/- 48 | Passed the pre-stated real-clock gate (>= 51.5 %); the net ships in 6.4.0 | `resnnue_vs_v63_tc` |

## 3. Rejected or superseded changes

| # | Change tried | Baseline | Measurement | Result (console) | Elo / nElo | Decision | Directory |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | First Texel trial: unregularised fit on 10,996 games (858,954 positions) (`v3trial`) | `v2` (hand-set table) | 25k nodes/move, 400 games | 186W 122L 92D = 58.00 % (interim at 200 games: 99W 58L 43D = 60.25 %) | +56 +/- 31 / +63 +/- 34 | Superseded by the regularised fit on the full 22k-game data (item 10) | `v3trial_vs_v2` |
| 11 | Unregularised fit on the same 22k-game data as item 10 (`tuned_full_noreg`) | `v2` | 25k nodes/move, 300 games | 163W 79L 58D = 64.00 % | +100 +/- 34 / +123 +/- 39 | Not adopted: 4 points below the regularised fit (68.0 %) | `tuned_full_noreg_vs_v2` |
| 12 | Second Texel iteration on 44k games including 22k played by the tuned engine (`v4`) | 6.0.0 table (`v3`) | 25k nodes/move, 500 games | 150W 148L 202D = 50.20 % | +1.4 +/- 23.9 / +1.8 +/- 30.5 | Not adopted (no gain) | `v4_vs_v3` |
| 13 | Quiet checking moves generated at the first quiescence ply (`qschecks`) | 6.0.0 (`forge_final`) | 20k nodes/move, 500 games | 151W 149L 200D = 50.20 % | +1.4 +/- 23.2 / +1.8 +/- 30.5 | Not adopted: neutral at fixed nodes and costs time per node | `qschecks_vs_v3` |
| 14 | NNUE evaluation, 768 -> 256x2 SCReLU network trained 40 epochs on 3,522,718 self-play positions (training loss 0.0160; validation loss on 200,476 fresh positions 0.0405 vs 0.0294 for the hand-crafted evaluation) (`nnue1`) | Tuned hand-crafted evaluation, 6.0.0 (`hce` = `forge_final`) | 20k nodes/move, 300 games | 14W 257L 29D = 9.50 % | -392 +/- 64 / -522 +/- 39 | Not adopted; a 768 -> 128 variant with validation-based early stopping reached validation loss 0.0370 and was not played. Infrastructure (`UseNNUE`, trainer) shipped without weights in 6.1.0 | `nnue1_vs_hce` |
| 23 | Null-move pruning from depth 2 instead of 3 (`NullMoveMinDepth=2`) | `base` (6.2.0 dev build) | SPRT elo0=0 elo1=5, 20k nodes/move, stopped early (46 min) | 3000 games: 885W 874L 1241D = 50.18 %, LLR -0.06 | +1.3 +/- 8.0 / +2.0 +/- 12.4 | Not adopted | `sprt_nmp2` |
| 24 | `SeeNoisyMultiplier=100` (SEE pruning margin for captures) and `AspirationDelta=12` (initial aspiration window) | `base` | SPRT, started and killed almost immediately to free CPU | A handful of games, no directory or PGN kept | - | Not run | - |
| 25 | Futility pruning of captures (`CaptureFutilityBase=300`) | `base` | SPRT elo0=0 elo1=5, 20k nodes/move, 60-minute cap | 5800 games: 1686W 1645L 2469D = 50.35 %, LLR 0.22 at the cap | +2.5 +/- 6.5 / +3.4 +/- 8.9 | Not adopted; remains a tunable with default 0 | `sprt_capfut` |
| 26 | Continuation-history bonus for the parent move when a node fails low (`FailLowContinuationBonus=100`) | `base` | SPRT elo0=0 elo1=5, 20k nodes/move, stopped early (10 min, concurrency 4) | 2000 games: 555W 536L 909D = 50.48 %, LLR 0.17 | +3.3 +/- 11.0 / +4.6 +/- 15.2 | Not adopted; remains a tunable with default 0 | `sprt_faillow` |
| 27 | Time management: `TmSoftDivisor=18` (more time per move early in the game) | Default `TmSoftDivisor=22` | 10+0.1 real clock, no adjudication, 200 games (100 pairs) | 33W 34L 133D = 49.75 %, no time forfeits | -1.7 +/- 26.2 / -3.2 +/- 48.2 | Not adopted | `tm18` |
| 28 | Singular-extension margin halved (`SingularMargin=1`, i.e. a 1 cp per depth margin instead of 2) | `base` (6.2.0 release source, tunables exposed) | SPRT elo0=0 elo1=5, 20k nodes/move, concurrency 2, stopped under the 1500-game rule (16 min) | 1600 games: 462W 467L 671D = 49.84 %, LLR -0.26 | -1.1 +/- 12.4 / -1.5 +/- 17.0 | Not adopted | `sprt63_singmargin1` |
| 29 | Two new pawn-structure evaluation terms: `PawnIslands` (penalty per island beyond the first, initial S(-6,-10)) and `CandidatePasser[rank]` (bonus for an unopposed, non-passed pawn whose stop square is attacked by no more enemy pawns than it has supporters level with or behind it), whole table refitted with `forge_texel` on the 4,674,912-position set (500 epochs, lr 1.0 halved every 200, lambda 0.5, reg 2e-9): loss 0.028870 -> 0.028749; fitted values `PawnIslands` S(-7,12), `CandidatePasser` ranks 1-5 S(2,-4) S(3,-2) S(7,7) S(8,21) S(20,50); candidate `bench 11` 376422 (`evalb`) | 6.2.0 release (`v62`) | 20k nodes/move, 400 games, concurrency 2 | 110W 115L 175D = 49.38 % | -4.3 +/- 25.6 / -5.8 +/- 34.1 | Not adopted (threshold 51.0 %); the four evaluation files were reverted | `evalb_vs_v62` |
| 30 | ProbCut from depth 4 instead of 5 (`ProbcutDepth=4`) | `base` | SPRT elo0=0 elo1=5, 20k nodes/move, concurrency 3, stopped under the 1500-game rule (25 min) | 3800 games: 1060W 1066L 1674D = 49.92 %, LLR -0.51 | -0.6 +/- 8.1 / -0.8 +/- 11.1 | Not adopted | `sprt63_probcut4` |
| 31 | Stronger history influence on LMR (`LmrHistoryDivisor=4000` instead of 6000) | `base` | SPRT elo0=0 elo1=5, 20k nodes/move, concurrency 3, stopped under the 1500-game rule (11 min) | 1800 games: 506W 492L 802D = 50.39 %, LLR 0.09 | +2.7 +/- 11.7 / +3.7 +/- 16.1 | Not adopted | `sprt63_lmrhist4000` |
| 32 | Smaller reverse-futility margin (`RfpMargin=60` instead of 72) | `base` | SPRT elo0=0 elo1=5, 20k nodes/move, concurrency 3, stopped under the 1500-game rule (10 min) | 1600 games: 437W 440L 723D = 49.91 %, LLR -0.23 | -0.7 +/- 12.0 / -0.9 +/- 17.0 | Not adopted | `sprt63_rfp60` |
| 33 | Late-move pruning keeps one more quiet move per depth (`LmpBase=4` instead of 3) | `base` | SPRT elo0=0 elo1=5, 20k nodes/move, concurrency 3, ran to the 8000-game limit (50 min 28 s) | 8000 games: 2261W 2176L 3563D = 50.53 %, LLR 0.86 (no bound reached) | +3.7 +/- 5.5 / +5.1 +/- 7.6 | Not adopted alone (below the LLR >= 1.0 / 51.5 % bar); adopted as part of item 35 | `sprt63_lmp4` |
| 34 | History bonus grows faster and saturates later (`HistoryBonusMax=2048`, `HistoryBonusQuadratic=20` instead of 1536 and 16) | `base` | SPRT elo0=0 elo1=5, 20k nodes/move, concurrency 3, ran to the 8000-game limit (50 min 0 s) | 8000 games: 2295W 2247L 3458D = 50.30 %, LLR 0.10 (no bound reached) | +2.1 +/- 5.7 / +2.8 +/- 7.6 | Not adopted alone; adopted as part of item 35 | `sprt63_histbonus` |
| 36 | Futility pruning margins `FutilityBase=80` + `FutilityMultiplier=130` (defaults 100 / 110) | `base` (6.3.0 release source, tunables exposed, `bench 11` = 344040) | SPRT elo0=0 elo1=5, 20k nodes/move, 2 cores (54 min), stopped under the rule | 5600 games: 1589W 1567L 2444D = 50.20 %, LLR -0.14 | +1.4 +/- 6.5 / +1.9 +/- 9.1 | Not adopted | `sprt64_futility` |
| 37 | SEE pruning threshold for quiet moves `SeeQuietMultiplier=18` (default 24) | `base` (6.3.0) | SPRT as above, 2 cores (50 min), stopped under the rule | 5000 games: 1430W 1380L 2190D = 50.50 %, LLR 0.46 | +3.5 +/- 7.1 / +4.7 +/- 9.6 | Not adopted (at the 50.5 % boundary with a positive LLR; no spare time for a combination test) | `sprt64_seequiet` |
| 40 | Residual NNUE with 256 hidden units (`res256`, run 6 of the training table below, 6 epochs, best = epoch 2, lambda-0.5 validation 0.026439 vs 0.026498 for the 128 net; `bench 11` = 403670) | `v63` | 20k nodes/move, 500 games, concurrency 4 | 218W 98L 184D = 62.00 % | +85 +/- 26 / +105 +/- 30 | Superseded: same strength as the 128 net (item 38) at fixed nodes with a 2x larger include file and accumulator; the 128 net shipped | `res256_vs_v63` |
| 41 | Quiescence SEE pruning margin `QsSeeMargin=80` (default 40) | `base64` (6.3.0 source with the adopted residual net, tunables exposed, `bench 11` = 417491) | SPRT as above, 4 cores (15 min), stopped under the rule | 3198 games: 870W 870L 1458D = 50.00 %, LLR -0.66 (last 100-game report: 3000 games, 821W 821L 1358D = 50.00 %) | 0 / 0 | Not adopted | `sprt64_qssee` |
| 42 | History pruning threshold `HistoryPruneMultiplier=3000` (default 2048) | `base64` | SPRT as above, 4 cores (26 min), stopped under the rule | 4600 games: 1235W 1241L 2124D = 49.93 %, LLR -0.60 | -0.5 +/- 7.1 / -0.6 +/- 10.0 | Not adopted | `sprt64_histprune` |
| 43 | Null-move eval-margin divisor `NullMoveEvalDivisor=150` (default 200) | `base64` | SPRT as above, 4 cores (23 min), stopped under the rule | 4000 games: 1045W 1112L 1843D = 49.16 %, LLR -1.79 | -5.8 +/- 7.6 / -8.3 +/- 10.8 | Not adopted | `sprt64_nmpeval` |

## 4. Experiments without games

| Experiment | What was done | Measurement | Result | Outcome |
| --- | --- | --- | --- | --- |
| A/A artefact in the first SPRT runs | The first SPRT runs of cutoff-count LMR and material correction passed `option.LmrCutoffThreshold=3` / `option.MaterialCorrectionWeight=100` on the fastchess command line to a binary whose tuning options were unlisted (accepted by `setoption` but absent from the `uci` output) | fastchess score after 2200 (LMR) and 2000 (material correction) games | Exactly 50.0 % with wins equal to losses in both runs: fastchess silently refuses to send options the engine does not advertise, so both were A/A tests | Development builds now advertise every tunable (`-DFORGE_EXPOSE_TUNABLES=ON`, commit `985cd1a`); both tests were rerun as items 21 and 22. The A/A runs were overwritten and have no PGN |
| Texel regularisation scan | `forge_texel` fits on the 858,954-position set (10,996 games) with different L2 regularisation strengths | Loss of the fitted table on its own training data | No regularisation 0.0282, but rare parameters overfit (e.g. rook-on-h2 PSQT entry +119 cp); reg 5e-7: 0.0305; 1e-7: 0.0299; 2e-8: 0.0293; rarity-scaled steps + reg 1e-8: 0.0291; reg 2e-9: 0.0287. On the full 1,715,952 positions: reg 2e-9 0.02916 vs unregularised 0.02877 | Reg 2e-9 with rarity-scaled steps chosen: in play the regularised table scored 68.0 % vs 64.0 % for the unregularised one (items 10 and 11) |
| King-safety composition weights scan | The attack-unit weights of the king-danger index were made parameters (`forge_texel --king-safety knight,bishop,rook,queen,weak,rookcheck,bishopcheck,knightcheck,queencheck,shelterdiv`) and the table was refitted with each candidate fixed | `forge_texel` loss on 4,674,912 positions after 250 epochs | Default (knight 2, bishop 2, rook 3, queen 5, weak square 2, safe checks rook/bishop/knight/queen 6/4/5/5, shelter divisor 8): 0.0289185; piece weights 1/1/2/4: 0.0288961; 3/3/4/6: 0.0289134; weak squares x2 (4): 0.0289012; checks x1.5 (9/6/8/8): 0.0289492; checks x0.5 (3/2/3/3, weak square 1): 0.0289378; shelter divisor 4: 0.0288740; 1/1/2/4 + weak 4 + divisor 4: 0.0288855; divisor 2: 0.0290085; divisor 3 variant (1/1/2/4, weak 4): 0.0289403 | Shelter divisor 4 adopted (lowest loss, 6.2.0); other weights left at their defaults |
| NNUE training and validation | 768 -> 256x2 SCReLU net trained 40 epochs (Adam, lr 0.001 halved every 8 epochs) on 3,522,718 positions; 768 -> 128 variant trained with validation-based early stopping | Training loss per epoch; validation loss on 200,476 positions from 3,086 games the training set does not contain; hand-crafted evaluation scored on the same validation set | 768x256: training 0.0160 at epoch 40 / validation 0.0405; 768x128: best validation 0.0370 at epoch 9; hand-crafted evaluation 0.0294 | Both nets overfit the available data; no weights shipped (match in item 14) |
| Profiling | gprof-instrumented development build (`forge_prof`) searching the bench positions during the 6.2.0 work | Share of search time per function group | Evaluation ~26-27 %, move-list sorting ~16-20 %, TT probe ~12 % | Motivated the lazy move sorting of item 20 |
| Texel fit with the pawn-island and candidate-passer terms (item 29) | `forge_texel` on the 4,674,912-position set with the two new terms added to the parameter table (9 new entries), 500 epochs, lr 1.0 halved every 200, lambda 0.5, reg 2e-9 | Final training loss | 0.028749 against 0.028870 for the 6.2.0 table on the same data and settings | Better fit but no gain in play (49.4 % over 400 games); not adopted |
| Second NNUE training run (6.3.0 round) | 768 -> 256x2 SCReLU net, 30 epochs (Adam, lr 0.001 halved every 8 epochs, lambda 0.5), trained on 9,415,054 positions: 5,892,336 from 82,694 self-play games at 4k nodes/move with random EPD openings (`/tmp/data5/games1-5.pgn`: 34,452 played on 13 October by the `t4` development build of the 6.2.0 evaluation, 48,242 played during this round by the 6.2.0 release binary) plus the 3,522,718-position 6.1.0 set | Training loss per epoch; validation loss on 300,000 held-out random-opening positions (`/tmp/data3/random_positions.txt`, not in the training set); shipping threshold 0.0300 (hand-crafted evaluation about 0.0294 on this set) | Best validation 0.0333 at epoch 2 (training 0.0270), then rising every epoch: epoch 30 training 0.0166 / validation 0.0368 | Overfits like the 6.1.0 nets; no weights shipped and no match played |
| Residual-mode check (6.4.0 round) | `forge_nnue_train --residual` with the output layer at zero and `--lr 0`, i.e. the network contributes nothing, scored on the 300,000-position random-opening holdout (`/tmp/data5/holdout.txt`) at several `--k` and `--lambda` values | Validation loss of the hand-crafted evaluation in the trainer's own metric | lambda 0.5: k 1.0 0.03103, 1.2 0.02972, 1.4 0.02872, 1.6 0.02800, 1.8 0.02751, 2.0 0.02722, 2.25 (engine constant) 0.027083; lambda 0.1 (k 2.25): 0.008570; lambda 0.0: 0.007565; on the 300,000 held-out training-distribution positions (`holdout6.txt`, lambda 0.5): 0.029803 | Baselines for every residual run below; the pre-stated figure "0.0294" came from `forge_texel` with its own fitted K and is not comparable |
| Residual NNUE run 1 (6.4.0 round) | 768 -> 256x2, `--residual`, lambda 0.5, lr 0.001 (halved every 8 epochs), batch 16384, Adam, 4 threads, 30 epochs planned, trained on 13,728,686 positions (5,892,336 `positions5` + 4,313,632 `positions6` from the 53,656 new 6.3.0 self-play games at 4k nodes/move + 3,522,718 `nnue_all`); 15 s per epoch | Training loss per epoch; validation loss on the 300,000-position holdout (lambda 0.5; hand-crafted evaluation 0.027083) | Epoch 1: training 0.027672 / validation 0.027836 (best); then validation rose every epoch while training fell: epoch 8 0.020180 / 0.030515, epoch 19 0.019041 / 0.031511 (stopped) | Worse than the hand-crafted evaluation from the first epoch; not played |
| Residual NNUE runs 2-4 (6.4.0 round) | Same data minus the last 300,000 lines of `positions6` (13,428,686 positions), 8 epochs each: run 2 = 256 hidden, lr 0.0005; run 3 = 128 hidden (`-DFORGE_NNUE_HIDDEN=128`), lr 0.001; run 4 = 256 hidden, lr 0.001, lambda 0.1 | As above (run 4 in the lambda-0.1 metric, hand-crafted evaluation 0.008570) | Run 2: best validation 0.027365 at epoch 1 (training 0.028678), 0.030061 at epoch 8 (training 0.021458). Run 3: best 0.027402 at epoch 1 (training 0.028292), 0.029127 at epoch 8 (training 0.022845). Run 4: 0.008234 at epoch 1 (better than the hand-crafted 0.008570; training 0.007497), 0.008623 at epoch 8 (training 0.005690) | Result-weighted targets overfit from epoch 1 regardless of learning rate and width; the first setting to beat the hand-crafted evaluation was the score-heavy lambda 0.1 |
| Residual NNUE diagnostic (6.4.0 round) | Run-1 settings (256 hidden, lambda 0.5, lr 0.001, 6 epochs) validated on `holdout6.txt`, 300,000 positions from the last ~3,700 games of the new self-play stream (same opening book and node count as the training games) | Validation loss on the training distribution (hand-crafted evaluation 0.029803) | 0.030262 at epoch 1 rising to 0.032888 at epoch 6 (training 0.027654 -> 0.020697) | The nets fail on unseen games of the training distribution itself, i.e. they memorise game results of correlated positions; a distribution shift to the random-opening holdout is not the explanation |
| Residual NNUE runs 5-6, shipped net (6.4.0 round) | Pure search-score targets (lambda 0.0), lr 0.001, batch 16384, 13,428,686 positions: run 5 = 128 hidden (8 epochs, 4 s per epoch), run 6 = 256 hidden (6 epochs, 14 s per epoch) | Validation loss on the 300,000-position holdout in the lambda-0 metric (hand-crafted evaluation 0.007565), then the saved best net rescored in the lambda-0.5 metric (hand-crafted 0.027083) | Run 5: 0.007180 (epoch 1), 0.007121 (epoch 2, best, training 0.006200), then 0.007131, 0.007148, 0.007159, 0.007181, 0.007195, 0.007203; lambda-0.5 metric 0.026498. Run 6: 0.007163 (epoch 1), 0.007163 (epoch 2, best, training 0.005917), then rising to 0.007347 at epoch 6; lambda-0.5 metric 0.026439 | Both beat the hand-crafted evaluation by 6 % (lambda 0) / 2 % (lambda 0.5), passing the gate; run 5's epoch-2 net (`resnet_run5_h128_l0.inc`) is `src/nnue_weights.inc` in 6.4.0 (items 38 and 39); run 6 played item 40 |
| Residual-net zero check and speed (6.4.0 round) | Engine built with a residual include whose output layer is zero (`zero_check.inc`), and with the shipped net | `bench 11` signature and nodes per second on the development VM | Zero output layer: 344040 nodes, identical to the hand-crafted evaluation (1.20M nps vs 2.05M, the cost of running both evaluations); shipped 128 net: 417491 nodes, 1.75M nps idle (256 net: 403670 nodes, same speed) | Confirms that the engine adds the net to the hand-crafted score exactly as trained; the network costs about 15 % of the nodes per second |
| Output-layer code generation (6.4.0 round) | `nnue::evaluate` micro-benchmark (1M calls, start position) and `bench 11` of static builds per target, before and after rewriting the SCReLU output layer with SSE min/max/mul/add intrinsics over 16 fixed-order partial sums | Nanoseconds per call; nodes per second | Before: 155 ns (x86-64-v3), 148 ns (x86-64-v2), 32 ns (x86-64-v4); engine 0.86M / 0.76M / 1.75M nps. After: 35-37 ns on all three targets; engine 1.78M (v3), 1.62M (v2), 1.85M (znver4) nps on the test VM, `bench 11` unchanged at 417491 on every target | Shipped; GCC had compiled the float clamp as scalar branchy code on AVX2 targets without `-ffast-math` |

## 5. PGN archive index

`all-match-pgns.zip` (67,169,642 bytes, SHA-256
`acbd91b4a7f7829092eede5472e2c40de1e34f33e469f6b2927c61b58ad27960`) contains a
`pgns/` folder with 44 files, 281,063,155 bytes and 76,047 games uncompressed
(26 files / 22,367 games from the 6.0.0-6.2.0 work, 9 files / 29,385 games
from the 6.3.0 round, 9 files / 24,295 games from the 6.4.0 round). Each file is the unmodified `games.pgn` of its match
directory. The training self-play games used for tuning are not matches and
are not included.

| Archive file | Match | Item | Source directory | Games in file |
| --- | --- | --- | --- | --- |
| `forge-5.31.0-vs-sf19-2800-10+0.1.pgn` | Forge 5.31.0 vs Stockfish 19 at `UCI_Elo 2800`, 10+0.1 | 1 | `base531_vs_sf2800_073642` | 20 |
| `forge-6.0.0-handset-eval-vs-sf19-2800-10+0.1.pgn` | 6.0.0 initial rewrite (hand-set evaluation) vs SF19 2800, 10+0.1 | 2 | `v1_vs_sf2800_080705` | 100 |
| `forge-6.0.0-vs-sf19-2800-10+0.1.pgn` | 6.0.0 shipped vs SF19 2800, 10+0.1 | 3 | `v3_vs_sf2800_093253` | 200 |
| `forge-6.0.0-vs-sf19-2800-30+0.3.pgn` | 6.0.0 shipped vs SF19 2800, 30+0.3 | 4 | `final_vs_sf2800_110852` | 100 |
| `forge-6.1.0-vs-sf19-2800-10+0.1.pgn` | 6.1.0 shipped vs SF19 2800, 10+0.1 | 5 | `v61_vs_sf2800_140715` | 200 |
| `forge-6.2.0pre-vs-sf19-3000-10+0.1.pgn` | 6.2.0 pre-release build vs SF19 3000, 10+0.1 | 6 | `v62a_vs_sf3000_102121` | 200 |
| `forge-6.2.0-vs-sf19-3000-20+0.2.pgn` | 6.2.0 release vs SF19 3000, 20+0.2 | 7 | `v62_vs_sf3000_123635` | 100 |
| `dev-correction-history-vs-rewrite-25k.pgn` | Correction history + sorted picker + TT prefetch (`v2`) vs initial rewrite (`v1`), 25k nodes | 8 | `v2_vs_v1_nodes` | 300 |
| `dev-texel-trial-unregularised-vs-v2-25k.pgn` | First unregularised Texel trial (`v3trial`) vs `v2`, 25k nodes | 9 | `v3trial_vs_v2` | 400 |
| `dev-texel-regularised-vs-v2-25k.pgn` | Regularised Texel fit (`tuned_full`, 6.0.0 table) vs `v2`, 25k nodes | 10 | `tuned_full_vs_v2` | 300 |
| `dev-texel-unregularised-vs-v2-25k.pgn` | Unregularised fit on the same data (`tuned_full_noreg`) vs `v2`, 25k nodes | 11 | `tuned_full_noreg_vs_v2` | 300 |
| `dev-texel-second-iteration-vs-6.0.0-25k.pgn` | Second Texel iteration (`v4`) vs 6.0.0 table (`v3`), 25k nodes | 12 | `v4_vs_v3` | 500 |
| `dev-qsearch-quiet-checks-vs-6.0.0-20k.pgn` | Quiet checks in quiescence (`qschecks`) vs 6.0.0, 20k nodes | 13 | `qschecks_vs_v3` | 500 |
| `dev-nnue-768x256-vs-hce-20k.pgn` | NNUE 768x256 (`nnue1`) vs tuned hand-crafted evaluation, 20k nodes | 14 | `nnue1_vs_hce` | 300 |
| `dev-retune-random-openings-book-openings-20k.pgn` | 61.5k-game retune (`t3`) vs 6.0.0 table (`cur`), `8moves_v3` openings, 20k nodes | 15 | `t3_vs_cur_book` | 300 |
| `dev-retune-random-openings-epd-openings-20k.pgn` | Same retune vs `cur`, random EPD openings, 20k nodes | 16 | `t3_vs_cur_epd` | 300 |
| `dev-threads4-vs-threads1-8+0.08.pgn` | `Threads=4` vs `Threads=1`, same binary, 8+0.08 | 17 | `smp4_vs_1` | 50 |
| `dev-eval-terms-retune-vs-6.1.0-20k.pgn` | New evaluation terms + retune (`t4`) vs 6.1.0, 20k nodes | 18 | `t4_vs_v61` | 400 |
| `dev-book-on-vs-off-10+0.1.pgn` | Opening book on vs off, same binary, 10+0.1 from the start position | 19 | `book_on_off` | 120 |
| `dev-lazy-move-sorting-vs-full-sort-20k.pgn` | Lazy move sorting (`pick`) vs full sort (`v62a`), 20k nodes | 20 | `pick_vs_v62a` | 400 |
| `sprt-lmr-cutoff-count.pgn` | SPRT `LmrCutoffThreshold=3` vs default, 20k nodes | 21 | `sprt_cutoff3` | 2804 |
| `sprt-material-correction-history.pgn` | SPRT `MaterialCorrectionWeight=100` vs default, 20k nodes | 22 | `sprt_matcorr` | 3213 (console report at 3200; full file: 944W 898L 1371D = 50.72 %) |
| `sprt-null-move-min-depth-2.pgn` | SPRT `NullMoveMinDepth=2` vs default, 20k nodes | 23 | `sprt_nmp2` | 3081 (console report at 3000; full file: 910W 892L 1279D = 50.29 %) |
| `sprt-capture-futility.pgn` | SPRT `CaptureFutilityBase=300` vs default, 20k nodes | 25 | `sprt_capfut` | 5882 (console report at 5800; full file: 1709W 1674L 2499D = 50.30 %) |
| `sprt-fail-low-continuation-bonus.pgn` | SPRT `FailLowContinuationBonus=100` vs default, 20k nodes | 26 | `sprt_faillow` | 2097 (console report at 2000; full file: 576W 562L 959D = 50.33 %) |
| `dev-time-management-soft-divisor-18-10+0.1.pgn` | `TmSoftDivisor=18` vs default 22, 10+0.1 | 27 | `tm18` | 200 |
| `forge-6.3.0-vs-sf19-3000-20+0.2.pgn` | 6.3.0 release vs SF19 3000, 20+0.2 | 8 | `v63_vs_sf3000_095408` | 100 |
| `sprt-singular-margin-1.pgn` | SPRT `SingularMargin=1` vs default, 20k nodes (6.3.0 round) | 28 | `sprt63_singmargin1` | 1741 (console report at 1600; full file: 505W 513L 723D = 49.77 %) |
| `dev-pawn-islands-candidate-passer-retune-vs-6.2.0-20k.pgn` | Pawn-island and candidate-passer terms with refitted table (`evalb`) vs 6.2.0, 20k nodes | 29 | `evalb_vs_v62` | 400 |
| `sprt-probcut-depth-4.pgn` | SPRT `ProbcutDepth=4` vs default, 20k nodes | 30 | `sprt63_probcut4` | 3856 (console report at 3800; full file: 1077W 1086L 1693D = 49.88 %) |
| `sprt-lmr-history-divisor-4000.pgn` | SPRT `LmrHistoryDivisor=4000` vs default, 20k nodes | 31 | `sprt63_lmrhist4000` | 1869 (console report at 1800; full file: 527W 515L 827D = 50.32 %) |
| `sprt-rfp-margin-60.pgn` | SPRT `RfpMargin=60` vs default, 20k nodes | 32 | `sprt63_rfp60` | 1749 (console report at 1600; full file: 485W 475L 789D = 50.29 %) |
| `sprt-lmp-base-4.pgn` | SPRT `LmpBase=4` vs default, 20k nodes, 8000-game limit | 33 | `sprt63_lmp4` | 8000 |
| `sprt-history-bonus-max-2048-quadratic-20.pgn` | SPRT `HistoryBonusMax=2048` + `HistoryBonusQuadratic=20` vs default, 20k nodes, 8000-game limit | 34 | `sprt63_histbonus` | 8000 |
| `sprt-lmp-base-4-history-bonus-2048-20.pgn` | SPRT `LmpBase=4` + `HistoryBonusMax=2048` + `HistoryBonusQuadratic=20` vs default, 20k nodes, H1 accepted | 35 | `sprt63_lmp4_histbonus` | 3670 |
| `forge-6.4.0-vs-sf19-3000-20+0.2.pgn` | 6.4.0 release vs SF19 3000, 20+0.2 | 9 | `v64_vs_sf3000_170334` | 100 |
| `sprt-futility-base-80-multiplier-130.pgn` | SPRT `FutilityBase=80` + `FutilityMultiplier=130` vs default, 20k nodes (6.4.0 round, 6.3.0 source) | 36 | `sprt64_futility` | 5649 (console report at 5600; full file: 1606W 1583L 2460D = 50.20 %) |
| `sprt-see-quiet-multiplier-18.pgn` | SPRT `SeeQuietMultiplier=18` vs default, 20k nodes (6.3.0 source) | 37 | `sprt64_seequiet` | 5093 (console report at 5000; full file: 1458W 1409L 2226D = 50.48 %) |
| `dev-residual-nnue-128-vs-6.3.0-20k.pgn` | Residual NNUE 768x128 (`res128`) vs 6.3.0, 20k nodes | 38 | `res128_vs_v63` | 500 |
| `dev-residual-nnue-128-vs-6.3.0-10+0.1.pgn` | Residual NNUE 768x128 (`res128`) vs 6.3.0, 10+0.1 | 39 | `resnnue_vs_v63_tc` | 200 |
| `dev-residual-nnue-256-vs-6.3.0-20k.pgn` | Residual NNUE 768x256 (`res256`) vs 6.3.0, 20k nodes | 40 | `res256_vs_v63` | 500 |
| `sprt-qs-see-margin-80.pgn` | SPRT `QsSeeMargin=80` vs default, 20k nodes (residual net compiled in) | 41 | `sprt64_qssee` | 3394 (console report at 3198; full file: 923W 923L 1548D = 50.00 %) |
| `sprt-history-prune-multiplier-3000.pgn` | SPRT `HistoryPruneMultiplier=3000` vs default, 20k nodes (residual net compiled in) | 42 | `sprt64_histprune` | 4741 (console report at 4600; full file: 1274W 1279L 2188D = 49.95 %) |
| `sprt-null-move-eval-divisor-150.pgn` | SPRT `NullMoveEvalDivisor=150` vs default, 20k nodes (residual net compiled in) | 43 | `sprt64_nmpeval` | 4118 (console report at 4000; full file: 1086W 1140L 1892D = 49.34 %) |

Not in the archive: the `SeeNoisyMultiplier=100` and `AspirationDelta=12`
SPRTs of item 24 (killed after a handful of games, no records kept) and the two
A/A runs described in section 4 (overwritten by their reruns). The second NNUE
training run (section 4) produced no match. The 6.3.0-round SPRT files that
were stopped under the 1500-game rule contain the games finished between the
last 100-game console report and the stop, as noted in the last column.
