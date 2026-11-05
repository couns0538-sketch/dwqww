# T12B candidates and the lock's fixed-buffer inventory

## A. Fixed buffers in the lock FD3A5190 (full read of search.hpp/.cpp, board.hpp/.cpp, uci.cpp, nnue.hpp; grep of
nnue.cpp, eval.cpp, eval_params.hpp). "Safe by X" = a bound that holds for every FEN set_fen accepts; "needs
fixture" = the bound is not enforced or not proven.

| # | buffer (decl) | write site | bound enforced? | worst case known | verdict |
|---|---|---|---|---|---|
| A1 | MovePicker::bad_captures_ std::array<Move, 64> (search.cpp:453) | search.cpp:361 `bad_captures_[bad_count_++]` | NO | 68 SEE-losing noisy moves in a set_fen-accepted, not-in-check FEN (fable-review-buffix fixture "many-losing", tests/bad_capture_tests.cpp:141) | OVERFLOW PROVEN -> T12B-01 |
| A2 | MoveList data_ std::array<Move, 256> (board.hpp:51, 71) | board.hpp:55 push_back, `assert(size_ < Capacity)` only; generator board.cpp:425-540 | assert only - compiled out (all CI builds and the kit define NDEBUG) | 218 legal = pseudo-legal in the classic maximum position; no known pseudo-legal maximum (pinned pieces and king steps into check are generated) | needs fixture + census (T12B-02) |
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
| Per-buffer limit fixtures + assert-enabled sanitizer CI row | PENDING | PENDING | PENDING | sanitizer row exists (opus-r13-san.yml, startpos self-play only, NDEBUG) | CARD T12B-02 |
