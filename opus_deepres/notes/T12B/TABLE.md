# T12B candidates and the lock's fixed-buffer inventory

## A. Fixed buffers in the lock FD3A5190 (full read of search.hpp/.cpp, board.hpp/.cpp, uci.cpp, nnue.hpp; grep of
nnue.cpp, eval.cpp, eval_params.hpp). "Safe by X" = a bound that holds for every FEN set_fen accepts; "needs
fixture" = the bound is not enforced or not proven.

| # | buffer (decl) | write site | bound enforced? | worst case known | verdict |
|---|---|---|---|---|---|
| A1 | MovePicker::bad_captures_ std::array<Move, 64> (search.cpp:453) | search.cpp:361 `bad_captures_[bad_count_++]` | NO | 68 SEE-losing noisy moves in a set_fen-accepted, not-in-check FEN (fable-review-buffix fixture "many-losing", tests/bad_capture_tests.cpp:141) | OVERFLOW PROVEN -> T12B-01 |
| A2 | MoveList data_ std::array<Move, 256> (board.hpp:51, 71) | board.hpp:55 push_back, `assert(size_ < Capacity)` only; generator board.cpp:425-540 | assert only - compiled out in every CI build (NDEBUG; the kit's flags were not checked) | 218 legal = pseudo-legal in the classic maximum position; no known pseudo-legal maximum (pinned pieces and king steps into check are generated) | needs fixture + census (T12B-02) |
| A3 | MovePicker::moves_ std::array<Scored, 256> (search.cpp:450) | search.cpp:518, 533, 552 `moves_[count_++]` | inherits A2 (copies at most buffer_.size() entries) | as A2 | covered by A2 |
| A4 | quiets_tried std::array<Move, 128> / captures_tried std::array<Move, 64> (search.cpp:1034-1035) | search.cpp:1186-1187 | YES (size check) | beyond 128 / 64 the history malus is silently skipped (T04 row 8) | safe; stats-only fixture |
| A5 | Worker::stack_ std::array<SearchStack, MaxPly + 8 = 136> (search.hpp:324), root at stack_[4] (search.cpp:1360) | (ss + 1) / (ss + 2) writes at search.cpp:843, 904-907, 975, 1012, 1122 | YES: `ply >= MaxPly` returns before any child write (search.cpp:781 qsearch, :894 search); deepest index 4 + 128 + 1 = 133 < 136 | ply 128 reachable only through extension chains (check extension keeps depth, search.cpp:1112-1115) | safe; deep-ply fixture still useful |
| A6 | SearchStack::pv std::array<Move, MaxPly + 1> (search.hpp:263) | search.cpp:857, 1176 copy_n | YES by recursion: pv_length(ply) <= 128 - ply | 128 at the root | safe |
| A7 | root_effort_moves_ / root_move_nodes_ std::array<., 256> (search.hpp:325-326) | search.cpp:1377 std::copy of root_candidates | assert only (:1376), but root_candidates <= legal moves <= 218 | 218 | safe while A2 holds |
| A8 | nnue::DirtyPieces changes std::array<PieceChange, 4> (nnue.hpp:43) | nnue.hpp:45-46 `count++`; dirty_pieces nnue.cpp:218-236 | by move type: castling = exactly 4, capture-promotion = 3 | 4 | safe |
| A9 | promotion_recapture_exchange gain std::array<int, 64> (board.cpp:25) | board.cpp:86, 94 | YES (`depth + 1 < gain.size()`, :41) | at most 32 pieces | safe |
| A10 | ReductionTable 64 x 64 (search.cpp:125-147) | read with std::min(depth, 63), std::min(moves, 63) | YES | - | safe |
| A11 | eval index tables: Knight/Bishop/Rook/QueenMobility 9/14/15/28, KnightPawnAdjust/RookPawnAdjust 9, KingDanger 100 (eval_params.hpp:13-16, 50-51; eval.cpp:112-113, 137-143, 250-252) | eval.cpp | YES: popcount bounds by geometry, queen clamped min(m, 27), units clamped [0, 99] | 9 queens / 10 knights do not index past a table | safe |
| A12 | Board::key_history_ std::vector (board.hpp:184) | board.cpp:788, 838 push_back | dynamic | long `position ... moves` lists grow it; repetition scans bounded by min(halfmove, plies_from_null) (board.cpp:895, 905) | safe; time-only fixture |
| A13 | 16-bit counters halfmove_ / fullmove_ / plies_from_null_ (board.hpp:177-183) | board.cpp:344-345, 737, 780, 787, 835 | YES: saturate at 65535 / 1024; TT rule50 byte min(., 100) (search.cpp:297) | FEN halfmove 65535 is accepted | safe; fixture checks the draw path |

## B. Candidates (idea | source + link | licence | logged numbers | Forge has it | verdict)
| idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|
| Size bad_captures_ to MoveList::Capacity (node-identical where the lock does not overflow) | own fable-review-buffix 8632e8ab (fix a9cea71f) | own | 68 > 64 fixture; mutant aborts under -D_GLIBCXX_ASSERTIONS; fixed 6/6 | NO: search.cpp:361 / :453; also absent in every O30 tree checked (D:/o30/plain/spsa_1, v2port_1, harness/h1: `std::array<Move, 64> bad_captures_`) and in no R15 patch (grep 0 hits under D:/o15/cands) | CARD T12B-01 |
| Per-buffer limit fixtures (F1-F8) + an assert-enabled ASan/UBSan CI row + own non-GPL annealer | own TABLE A1-A13; Stockfish 7316ef4 / 5380403 / 1548538 / c56bd10 (https://github.com/official-stockfish/Stockfish/commit/7316ef4e86 ...); https://talkchess.com/viewtopic.php?p=801104 | own; GPL-3.0 messages only; forum facts | 75 instrumented tests on a debug ASan+UBSan build (7316ef4); 1548538 non-regression STC 154,752 / LTC 55,782 games; no Elo | partly: opus-r13-san.yml (self-play smoke only, start positions not stated, NDEBUG), forge_bad_capture_tests on fable-review-buffix only | CARD T12B-02 |
| position command: short (4/5-field) FEN or an illegal move token keeps the previous position silently | own read src/uci.cpp:30-38, 46-51; https://github.com/official-stockfish/Stockfish/commit/23df82905b (input hardening class) | own; GPL-3.0 message only | none | NO (uci.cpp:30-38, 46-51) | ONE-LINE T12B-03 |
| MoveList::Capacity 256 is assert-only (board.hpp:55); no proof that pseudo-legal generation stays <= 256 | own; https://talkchess.com/viewtopic.php?p=801104 ("so 256 is needed" for 218; one engine sized its list from a testing maximum of 100) | own; forum facts | no pseudo-legal maximum published (searched once, none found) | assert only, compiled out | TABLE only: fixture F2 of T12B-02 records the census maximum; if it ever reaches 256, raise Capacity (node-identical, nps ABBA) |
| chained extensions reaching MAX_PLY (deep recursion) | https://github.com/official-stockfish/Stockfish/commit/1548538ede (issue 7156, PR 7170) | GPL-3.0 message only | non-regression STC 154,752 / LTC 55,782 games, LLR 2.94 both | safe: LMR depth clamped to [1, new_depth] (search.cpp:1147) so LMR never extends; check / singular extensions are stopped by the ply guard (search.cpp:894, 781) | no card; fixture F4 |
| always write, grow the size only for valid entries (branch-free list push) | https://github.com/official-stockfish/Stockfish/commit/df01cb7ed3 (PR 6703) | GPL-3.0 message only | STC 205,760 games LLR 2.95 <0,2>; local +0.67 % +- 0.19 | n/a (speed idea, T05 territory) | dropped (speed, not robustness; below the 1 % nps line) |
| reject an oversized symbol count read from a tablebase file | https://github.com/official-stockfish/Stockfish/commit/7316ef4e86 (PR 7237) | GPL-3.0 message only | bench unchanged; no runtime reproducer | lock has no TB prober; the R14 P6 Syzygy port should get the same check (own code: validate every count read from a file against the buffer it fills) | no card; note for the Syzygy port |
| clamp negative clock values | https://github.com/official-stockfish/Stockfish/commit/23df82905b (PR 7257) | GPL-3.0 message only | "No functional change" | YES: std::max(0, .) at uci.cpp:99-102 (T07 case 28: -> 1 ms move) | evidence for notes/T07/UCI_EDGE_CASES.md case 28 |

## C. Evidence for existing items (not new cards)
- notes/T04/BUG_CHECKLIST.md row 9 says "likely unreachable": WRONG. The engine-census fixture "many-losing"
  (`3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2 w - - 0 1`, noisy 69, SEE-losing 68, 4 promotions,
  accepted by set_fen, not in check) makes the 64-entry lock abort under -D_GLIBCXX_ASSERTIONS (F:/opus_scratch/
  fable_review/buffix64/final_mutant.log, exit 127); fix a9cea71f on fable-review-buffix 8632e8ab. Row 9 status should
  read OVERFLOW PROVEN, fix not on the lock line (T12B-01).
- cards/T12/T12-03 level 6 (saturation) + level 8 (ASan/UBSan self-play): concrete FENs for level 6 = T12B-02 F1/F2;
  the existing sanitizer row cannot fire asserts (every CI build defines NDEBUG) and is a self-play smoke with no
  crafted positions (its start positions are not stated in the skill).
- cards/T05C/T05C-02 (no zero-fill): T12B-01 grows the zero-filled bad_captures_ from 256 B to 1 KiB per picker; with
  T05C-02's default-initialised arrays the growth costs nothing, so the two belong in one ABBA.
- notes/T07/UCI_EDGE_CASES.md case 28: Stockfish 23df829 (2026-10-25) states that some GUIs do send negative remaining
  time; the lock already clamps to 0 (uci.cpp:99-102).
