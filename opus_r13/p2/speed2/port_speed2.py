#!/usr/bin/env python3
"""port_speed2.py - R14 Main item 2 (own code): build switch FORGE_SEARCH_SPEED2 (default 0) on a fresh lock copy.

usage: python -I -B port_speed2.py <lock copy dir> [--default 0|1]
ON (= 1), node-identical by construction, speed only:
  1. TT prefetch right after every make on the search paths: the lock prefetches the child cluster after make_move in
     qsearch and in the main move loop; FORGE_SEARCH_SPEED2 adds the same call after make_null_move (null-move search) and
     after the ProbCut make_move (its qsearch / search probe the child TT first).
  2. MovePicker hoist (form of the crew's speedmp2_h256e12, CR PASS 2026-10-24): quiet scores via quiet_history_sum() with
     the side's history row and both continuation tables read once per generation (QuietScorer), the moved piece read
     once per quiet move, capture scores with moved / captured piece read once (same sums, same order).
  3. piece_type() by a 16-entry table instead of the modulo (same speedmp2 form; same value for every valid Piece).
OFF (= 0, the default): the preprocessor keeps exactly the lock's lines. --default 1 writes the variant whose default is
ON (the kit takes no -D flags). Every anchor must occur exactly once; files are read and written as LF bytes.
"""
import pathlib
import sys

GUARD = '#ifndef FORGE_SEARCH_SPEED2\n#define FORGE_SEARCH_SPEED2 {d}\n#endif\n'


def edit(path, old, new):
    data = path.read_bytes().decode('utf-8')
    if '\r' in data:
        raise SystemExit(f'{path}: CRLF in a lock copy (use fresh_lock.sh)')
    n = data.count(old)
    if n != 1:
        raise SystemExit(f'{path}: anchor found {n} times, need 1:\n{old[:200]}')
    path.write_bytes(data.replace(old, new).encode('utf-8'))


def main():
    root = pathlib.Path(sys.argv[1])
    default = sys.argv[3] if len(sys.argv) == 4 and sys.argv[2] == '--default' else '0'
    if default not in ('0', '1'):
        raise SystemExit('--default must be 0 or 1')
    board = root / 'include' / 'forge' / 'board.hpp'
    search = root / 'src' / 'search.cpp'

    # board.hpp: the switch default (board.hpp is included by every unit that uses piece_type) + piece_type
    edit(board, '#include "forge/bitboard.hpp"\n',
         '#include "forge/bitboard.hpp"\n\n'
         '// FORGE_SEARCH_SPEED2 (R14 build switch, default 0 = lock code): speed-only, node-identical search changes\n'
         '// (TT prefetch after every make, MovePicker history / piece hoist, table piece_type). See src/search.cpp.\n'
         + GUARD.format(d=default))
    edit(board,
         '[[nodiscard]] constexpr int piece_type(Piece piece) { return piece == Empty ? 0 : ((static_cast<int>(piece) - 1) % 6) + 1; }\n',
         '#if FORGE_SEARCH_SPEED2\n'
         'namespace detail {\n'
         '// Piece type for every Piece value: Empty=0 -> 0, WP..WK=1..6 -> 1..6, BP..BK=7..12 -> 1..6. Entries 13..15 only pad\n'
         '// the table to 16 so the index mask stays in bounds; no valid Piece reaches them (same values as the modulo form).\n'
         'inline constexpr std::array<std::uint8_t, 16> PieceTypeTable{0, 1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6, 0, 0, 0};\n'
         '} // namespace detail\n'
         '[[nodiscard]] constexpr int piece_type(Piece piece) { return detail::PieceTypeTable[static_cast<unsigned>(piece) & 15U]; }\n'
         '#else\n'
         '[[nodiscard]] constexpr int piece_type(Piece piece) { return piece == Empty ? 0 : ((static_cast<int>(piece) - 1) % 6) + 1; }\n'
         '#endif\n')

    # search.cpp: shared quiet history sum (MovePicker + Worker::quiet_history use one formula)
    edit(search,
         'std::string format_score(int score) {\n',
         '#if FORGE_SEARCH_SPEED2\n'
         '// Quiet history of one move: main history row of the side to move plus the continuation history of the two\n'
         '// previous plies, summed in this order (= Worker::quiet_history).\n'
         '[[nodiscard]] inline int quiet_history_sum(const std::array<std::array<std::int16_t, 64>, 64>& main,\n'
         '                                           const PieceToHistory* cont1, const PieceToHistory* cont2, Piece piece,\n'
         '                                           Move move) {\n'
         '    const std::size_t p = static_cast<std::size_t>(piece);\n'
         '    int score = main[move.from][move.to];\n'
         '    if (cont1 != nullptr) score += (*cont1)[p][move.to];\n'
         '    if (cont2 != nullptr) score += (*cont2)[p][move.to];\n'
         '    return score;\n'
         '}\n'
         '#endif\n\n'
         'std::string format_score(int score) {\n')

    # MovePicker: QuietScorer next to direct_check
    edit(search,
         '    [[nodiscard]] static int move_score_threshold(Move) { return 0; }\n',
         '#if FORGE_SEARCH_SPEED2\n'
         '    // Quiet score = quiet_history_sum() + 12000 for a direct check; the history row and both continuation tables\n'
         '    // are fixed for one generation, so they are read once, and the moved piece once per move.\n'
         '    struct QuietScorer {\n'
         '        const std::array<std::array<std::int16_t, 64>, 64>& main;\n'
         '        const PieceToHistory* cont1;\n'
         '        const PieceToHistory* cont2;\n'
         '        const Board& board;\n'
         '\n'
         '        QuietScorer(const Board& b, const Worker& searcher, const SearchStack* ss)\n'
         '            : main((*searcher.main_history_)[static_cast<std::size_t>(b.side_to_move())]),\n'
         '              cont1(ss != nullptr ? (ss - 1)->continuation : nullptr),\n'
         '              cont2(ss != nullptr ? (ss - 2)->continuation : nullptr),\n'
         '              board(b) {}\n'
         '\n'
         '        [[nodiscard]] int score(Move move, const std::array<Bitboard, 7>& check_squares) const {\n'
         '            const Piece piece = board.piece_at(move.from);\n'
         '            int value = quiet_history_sum(main, cont1, cont2, piece, move);\n'
         '            if ((check_squares[static_cast<std::size_t>(piece_type(piece))] & square_bb(move.to)) != 0) value += 12000;\n'
         '            return value;\n'
         '        }\n'
         '    };\n'
         '#endif\n\n'
         '    [[nodiscard]] static int move_score_threshold(Move) { return 0; }\n')

    # captures: moved / captured piece read once (10 * capture_value + capture_history_value, same sum)
    edit(search,
         '        for (const Move move : buffer_) {\n'
         '            int score = 10 * capture_value(board_, move) + searcher_.capture_history_value(board_, move);\n',
         '#if FORGE_SEARCH_SPEED2\n'
         '        const CaptureHistory& capture_history = *searcher_.capture_history_;\n'
         '#endif\n'
         '        for (const Move move : buffer_) {\n'
         '#if FORGE_SEARCH_SPEED2\n'
         '            const std::size_t moved = static_cast<std::size_t>(board_.piece_at(move.from));\n'
         '            const std::size_t victim = static_cast<std::size_t>(piece_type(board_.captured_piece(move)));\n'
         '            int value = SeePieceValue[victim];\n'
         '            if (move.is_promotion()) value += SeePieceValue[move.promotion] - SeePieceValue[Pawn];\n'
         '            int score = 10 * value + capture_history[moved][move.to][victim];\n'
         '#else\n'
         '            int score = 10 * capture_value(board_, move) + searcher_.capture_history_value(board_, move);\n'
         '#endif\n')

    # quiets
    edit(search,
         '        for (const Move move : buffer_) {\n'
         '            if (move.is_capture() || move.is_promotion()) continue;\n'
         '            int score = searcher_.quiet_history(board_, ss_, move);\n'
         '            if (direct_check(move)) score += 12000;\n'
         '            moves_[count_++] = Scored{move, score};\n'
         '        }\n',
         '#if FORGE_SEARCH_SPEED2\n'
         '        const QuietScorer scorer(board_, searcher_, ss_);\n'
         '        for (const Move move : buffer_) {\n'
         '            if (move.is_capture() || move.is_promotion()) continue;\n'
         '            moves_[count_++] = Scored{move, scorer.score(move, check_squares_)};\n'
         '        }\n'
         '#else\n'
         '        for (const Move move : buffer_) {\n'
         '            if (move.is_capture() || move.is_promotion()) continue;\n'
         '            int score = searcher_.quiet_history(board_, ss_, move);\n'
         '            if (direct_check(move)) score += 12000;\n'
         '            moves_[count_++] = Scored{move, score};\n'
         '        }\n'
         '#endif\n')

    # evasions: quiet part through the scorer, capture part unchanged
    edit(search,
         '        count_ = 0;\n'
         '        for (const Move move : buffer_) {\n'
         '            int score;\n',
         '        count_ = 0;\n'
         '#if FORGE_SEARCH_SPEED2\n'
         '        const QuietScorer scorer(board_, searcher_, ss_);\n'
         '#endif\n'
         '        for (const Move move : buffer_) {\n'
         '            int score;\n')
    edit(search,
         '                score = searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? 12000 : 0);\n',
         '#if FORGE_SEARCH_SPEED2\n'
         '                score = scorer.score(move, check_squares_);\n'
         '#else\n'
         '                score = searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? 12000 : 0);\n'
         '#endif\n')

    # Worker::quiet_history through the same helper (LMR / pruning use it)
    edit(search,
         'int Worker::quiet_history(const Board& board, const SearchStack* ss, Move move) const {\n'
         '    const Piece piece = board.moved_piece(move);\n',
         'int Worker::quiet_history(const Board& board, const SearchStack* ss, Move move) const {\n'
         '#if FORGE_SEARCH_SPEED2\n'
         '    return quiet_history_sum((*main_history_)[static_cast<std::size_t>(board.side_to_move())],\n'
         '                             ss != nullptr ? (ss - 1)->continuation : nullptr,\n'
         '                             ss != nullptr ? (ss - 2)->continuation : nullptr, board.moved_piece(move), move);\n'
         '#else\n'
         '    const Piece piece = board.moved_piece(move);\n')
    edit(search,
         '        if ((ss - 2)->continuation != nullptr) score += (*(ss - 2)->continuation)[static_cast<std::size_t>(piece)][move.to];\n'
         '    }\n'
         '    return score;\n'
         '}\n',
         '        if ((ss - 2)->continuation != nullptr) score += (*(ss - 2)->continuation)[static_cast<std::size_t>(piece)][move.to];\n'
         '    }\n'
         '    return score;\n'
         '#endif\n'
         '}\n')

    # TT prefetch after the null move and after the ProbCut make
    edit(search,
         '            board.make_null_move(undo);\n'
         '            int null_score = -search(board, ss + 1, depth - reduction, -beta, -beta + 1, !cut_node);\n',
         '            board.make_null_move(undo);\n'
         '#if FORGE_SEARCH_SPEED2\n'
         '            shared_.tt.prefetch(board.key());\n'
         '#endif\n'
         '            int null_score = -search(board, ss + 1, depth - reduction, -beta, -beta + 1, !cut_node);\n')
    edit(search,
         '                (void)board.make_move(move, undo);\n'
         '                int value = -qsearch(board, ss + 1, -probcut_beta, -probcut_beta + 1);\n',
         '                (void)board.make_move(move, undo);\n'
         '#if FORGE_SEARCH_SPEED2\n'
         '                shared_.tt.prefetch(board.key());\n'
         '#endif\n'
         '                int value = -qsearch(board, ss + 1, -probcut_beta, -probcut_beta + 1);\n')
    print(f'port_speed2: {board} and {search} edited (default {default})')


if __name__ == '__main__':
    main()
