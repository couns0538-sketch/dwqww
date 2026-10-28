# R3-5 idea sources

Job R3-5 (user, verbatim): "Test suite: add a regression test set (perft 20 positions to depth 5+,
repetition/threefold incl. GitHub issue #7, 50-move, TB score and mate-in-TT, SMP stop/ponder, UCI option parsing)
wired into CTest and CI."

## Perft reference node counts (tests/data/perft_suite.tsv)

Every count in the suite is a published number; every one was also recomputed with python-chess 1.11.2
(`tools/perft_crosscheck.py`, logs `logs/perft_crosscheck.log` and `logs/perft_crosscheck_big.log`).

- **CPW**: Chessprogramming wiki, "Perft Results", https://www.chessprogramming.org/Perft_Results (read
  2026-10-27): initial position d5 4,865,609 / d6 119,060,324; position 2 "Kiwipete" d4 4,085,603 / d5
  193,690,690; position 3 d5 674,624 / d6 11,030,083; position 4 and its mirrored version d5 15,833,292;
  position 5 d4 2,103,487 / d5 89,941,194; position 6 (Steven Edwards) d4 3,894,594 / d5 164,075,551.
- **SEDLAK**: Martin Sedlak ("mar"), "A few positions to test movegen", TalkChess programming forum, topic 47318,
  2013-02-24, https://talkchess.com/viewtopic.php?t=47318 (each theme with a colour-swapped twin). The same list,
  with the theme names used here, in Steve Maughan, "Perfect Perft!", https://www.chessprogramming.net/perfect-perft
  (2013-04-22): illegal en passant #1 (rank pin) d6 1,134,888; illegal en passant #2 (diagonal pin) d6 1,015,133;
  en passant capture checks the opponent d6 1,440,467; short castling gives check d6 661,072; long castling gives
  check d6 803,711; promote out of check d6 3,821,001; discovered check d5 1,004,658; promote to give check d6
  217,342; underpromote to give check d6 92,683; stalemate & checkmate d7 567,584.
- **ROCE**: Roman Hartmann's ROCE perft suite (`perftsuite.epd`, rocechess.ch), as quoted in TalkChess topic 78241
  ("perft test"): `r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1` D5 7,594,526 D6 179,862,938 (confirmed to depth 8 with
  JetChess 1.0.0.0 in TalkChess topic 47318, post 597736); `n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1` D5 3,605,103
  D6 71,179,139.
- **JVM**: John Merlino's positions, TalkChess topic 77949 (post 902361), listed with every depth in
  gflohr/Chess-Plisco `t/05perft.t` (https://github.com/gflohr/Chess-Plisco, file read 2026-10-27, sha256
  e7522e3a39d7172fb718a49732edc34d76136bc55bf8fb3991e2566214bd9ef8): `r3k2r/8/8/8/3pPp2/8/8/R3K1RR b KQkq e3 0 1`
  d4 624,871 / d5 15,446,339 (perft(6) 485,647,607 also in TalkChess topic 80952); `n1n5/PPPk4/...` as ROCE.
- **PLISCO**: the same file lists the CPW and ROCE counts as well (second listing).

Selection: the six CPW positions plus the mirrored position 4 (spec: "startpos, kiwipete, chessprogramming-wiki
positions 3-6"), and 13 edge cases chosen for en passant (two illegal-pin cases, check by en passant, two
en-passant captures with castling), castling (check by castling both sides, rights lost by rook captures),
promotion (out of check, giving check, underpromotion giving check, promotions and capture-promotions of both
sides), discovered checks, stalemate and mate.

## Draw rules (tests/draw_rules_tests.cpp)

- FIDE Laws of Chess (handbook.fide.com, chapter E012023): 9.2 threefold repetition (9.2.1: claim before an
  intended move that would create the third occurrence; 9.2.2: the position has just appeared the third time),
  9.3 50-move rule, 5.1.1 checkmate ends the game (so a mate delivered on the 100th half-move stands).
- GitHub issue #7 (this repository, couns0538-sketch: "Forge experimental: intended-threefold (FIDE 9.2.1) missed
  by non-root qsearch"; `gh issue view 7`): FEN `8/7k/8/8/8/8/8/K1R5 w - - 0 1`, positive history `a1a2 h7h8 a2a1
  h8h7 a1a2 h7h8 a2a1`, control `a1b1 h7h8 b1b2 h8h7 b2a2 h7h8 a2a1`, the native non-root qsearch at ply 1 with one
  worker and Hash 4 MiB, and the expectation "positive 0 cp, control unchanged" (-439 cp in the issue's engine).
- Engine conventions (src/board.cpp `is_repetition(root_index)`, src/search/checks.inc `is_draw`,
  src/search/iterative.inc root adjudication): one earlier occurrence at or after the search root is a draw
  (twofold in search), positions before the root need two; half-move clock >= 100 is a draw unless the side to
  move is checkmated; a root with clock >= 100 or a game-level threefold is reported as a draw without a search.
- The perpetual-check fixture `6k1/5p1p/8/8/8/8/qr1Q4/7K w - - 0 1` was constructed for this job (White, a rook
  down, checks on g5/d8/f6) and calibrated on the stack.

## Mate and tablebase scores in the TT (tests/tt_mate_tb_tests.cpp)

- Mate-distance encoding in transposition tables (scores stored relative to the storing node, read back relative
  to the reading node): Chessprogramming wiki "Transposition Table" (mate scores) and "Mate Scores"; the same
  scheme as Stockfish's `value_to_tt` / `value_from_tt`. The engine's version is src/search/scores.inc.
- The mate-in-3 fixture `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` (unique key move Kd5-c5) was found for this job with a
  python-chess brute-force search; the test re-proves it with its own brute-force mate oracle on the engine's move
  generator.
- Syzygy tablebases (Ronald de Man): reference answers are those of job C1 (tests/syzygy_reference.tsv,
  python-chess 1.11.2 on the 3-4-5 files); the in-search probe fixture is C1's
  `4k3/8/8/8/3r4/8/3Q4/3RK2n w - - 0 1`.

## UCI option parsing and SMP stop / ponder (tools/uci_options_regression.py, tools/smp_uci_regression.py)

- Stefan Meyer-Kahlen, "Description of the universal chess interface (UCI)", April 2006: `setoption name <id>
  [value <x>]` (names and values may contain spaces), option types check / spin (min / max) / string / button,
  `go ponder` + `ponderhit` / `stop`, "the engine must not send bestmove while pondering before ponderhit or stop",
  one `bestmove` per `go`.
- The documented behaviour of src/uci.cpp (invalid values reported as `info string invalid value for option
  <name>`, spins clamped to their bounds, NNUEThreats / NNUEPawnPairs / PureNnue accepting 0 / 1 / true / false,
  Book File / SyzygyPath / NNUEFile taking the rest of the line, the NNUE v2 fail-loud rule of
  include/forge/search_options.hpp).
- Reused: tools/uci_regression.py `Engine` (process driver); legality through the engine's own `go perft 1`
  (the approach of opus_round1/O1/ucilib.py `LegalMoves` without python-chess, which CI does not install).

## Planted bugs

- forge-engine-verify section 4 (one-line mutants, the new test must fail). Mutants in `tools/mutation_check.py`.
