// Search module: scoring and update rules of the move-ordering history tables
// (Worker::histories_; tables, bonus and gravity in forge/history.hpp).
// Compiled as part of src/search.cpp (included exactly once).

namespace forge {

static_assert(hist_rework::HistoryLimit == HistoryMax, "HistRework bounds assume the lock's history limit");
static_assert(hist_rework::CorrectionEntryLimit == CorrectionLimit, "HistRework bounds assume the lock's correction limit");

// HistRework: the threat-keyed butterfly slot of a quiet move at the node of `ss` (its maps are threat_maps_[ply]).
std::int16_t& Worker::threat_history_entry(const Board& board, const SearchStack* ss, Move move) const {
    const hist_rework::LesserThreats& threats = threat_maps_[static_cast<std::size_t>(ss->ply)];
    const Bitboard set = threats.by_type[static_cast<std::size_t>(piece_type(board.moved_piece(move)))];
    return (*threat_history_)[static_cast<std::size_t>(board.side_to_move())][hist_rework::square_bit(set, move.from)]
                             [hist_rework::square_bit(set, move.to)][move.from][move.to];
}

void Worker::update_threat_history(const Board& board, const SearchStack* ss, Move best, int bonus, const Move* quiets,
                                   int quiet_count) {
    apply_history(threat_history_entry(board, ss, best), bonus);
    for (int i = 0; i < quiet_count; ++i) {
        if (quiets[i] == best) continue;
        apply_history(threat_history_entry(board, ss, quiets[i]), -bonus);
    }
}

int Worker::quiet_history(const Board& board, const SearchStack* ss, Move move) const {
    const Piece piece = board.moved_piece(move);
    int score = (*histories_.main_history)[static_cast<std::size_t>(board.side_to_move())][move.from][move.to];
    if (const int level = search_options::hist_rework; level != 0 && ss != nullptr) [[unlikely]] {
        // |score| <= 16384 after the blend, as for the lock table alone (hist_rework::blend).
        score = hist_rework::blend(score, threat_history_entry(board, ss, move), hist_rework::threat_quarters(level));
    }
    if (ss != nullptr) {
        if ((ss - 1)->continuation != nullptr) score += (*(ss - 1)->continuation)[static_cast<std::size_t>(piece)][move.to];
        if ((ss - 2)->continuation != nullptr) score += (*(ss - 2)->continuation)[static_cast<std::size_t>(piece)][move.to];
    }
    return score;
}

int Worker::capture_history_value(const Board& board, Move move) const {
    const Piece piece = board.moved_piece(move);
    const int captured = piece_type(board.captured_piece(move));
    return (*histories_.capture_history)[static_cast<std::size_t>(piece)][move.to][static_cast<std::size_t>(captured)];
}

void Worker::update_continuation(SearchStack* ss, Piece piece, int to, int bonus) {
    for (const int back : {1, 2, 4}) {
        const SearchStack* previous = ss - back;
        if (previous->continuation == nullptr || previous->current_move.is_none()) continue;
        apply_history((*previous->continuation)[static_cast<std::size_t>(piece)][static_cast<std::size_t>(to)],
                      back == 4 ? bonus / 2 : bonus);
    }
}

void Worker::update_quiet_stats(const Board& board, SearchStack* ss, Move move, int depth, const Move* quiets,
                                  int quiet_count) {
    const int bonus = history_bonus(depth);
    const Color us = board.side_to_move();
    if (ss->killers[0] != move) {
        ss->killers[1] = ss->killers[0];
        ss->killers[0] = move;
    }
    const SearchStack* previous = ss - 1;
    if (!previous->current_move.is_none() && previous->moved_piece != Empty) {
        (*histories_.counter_moves)[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to] = move;
    }
    const Piece piece = board.moved_piece(move);
    apply_history((*histories_.main_history)[static_cast<std::size_t>(us)][move.from][move.to], bonus);
    update_continuation(ss, piece, move.to, bonus);
    for (int i = 0; i < quiet_count; ++i) {
        const Move quiet = quiets[i];
        if (quiet == move) continue;
        apply_history((*histories_.main_history)[static_cast<std::size_t>(us)][quiet.from][quiet.to], -bonus);
        update_continuation(ss, board.moved_piece(quiet), quiet.to, -bonus);
    }
    // HistRework: the threat-keyed twin learns the same bonus and maluses (lock gravity, apply_history).
    if (search_options::hist_rework != 0) [[unlikely]] update_threat_history(board, ss, move, bonus, quiets, quiet_count);
}

void Worker::update_capture_stats(const Board& board, Move best, int depth, const Move* captures, int capture_count) {
    const int bonus = history_bonus(depth);
    if (best.is_capture()) {
        const Piece piece = board.moved_piece(best);
        const int captured = piece_type(board.captured_piece(best));
        apply_history((*histories_.capture_history)[static_cast<std::size_t>(piece)][best.to][static_cast<std::size_t>(captured)], bonus);
    }
    for (int i = 0; i < capture_count; ++i) {
        const Move capture = captures[i];
        if (capture == best) continue;
        const Piece piece = board.moved_piece(capture);
        const int captured = piece_type(board.captured_piece(capture));
        apply_history((*histories_.capture_history)[static_cast<std::size_t>(piece)][capture.to][static_cast<std::size_t>(captured)], -bonus);
    }
}

} // namespace forge
