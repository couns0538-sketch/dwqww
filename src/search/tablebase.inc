// Search module: tablebase glue (job C1, forge/syzygy.hpp) — the WDL probe
// inside the search, root move filtering by DTZ (or WDL) rank, and the score
// reported for tablebase roots. Only reached while tables are loaded
// (UCI SyzygyPath): the search tests syzygy::search_cardinality and the driver
// tests syzygy::max_pieces() before calling in here.
// Compiled as part of src/search.cpp, after the search modules; every
// function here is [[gnu::cold]] (placed after all search code).

namespace forge {

// Called from Worker::search (alphabeta.inc) after the TT cutoff. Returns the
// value to return from the node, or ValueNone to search on.
// Probes right after a capture or pawn move (50-move counter 0: the stored
// WDL is exact), never with castling rights, not at the root, not in a
// singular verification search. Wins and losses are bounds (a mate may be
// shorter than the TB win), draws exact. PV nodes take the TB value as well
// (it is the game-theoretic result).
[[gnu::cold]] int Worker::probe_tablebase(Board& board, SearchStack* ss, int depth, int alpha, int beta,
                                          const TTProbe& tt_probe) {
    if (ss->ply == 0 || !ss->excluded_move.is_none()) return ValueNone;
    if (board.halfmove_clock() != 0 || board.castling_rights() != 0) return ValueNone;
    const int limit = syzygy::search_cardinality.load(std::memory_order_relaxed);
    const int pieces = popcount(board.occupied());
    if (pieces > limit || (pieces == limit && depth < options::syzygy_probe_depth)) return ValueNone;
    int wdl = 0;
    if (!syzygy::probe_wdl(board, wdl)) return ValueNone;
    syzygy::probe_hits.fetch_add(1, std::memory_order_relaxed);
    const int draw_band = options::syzygy_50_move_rule ? 1 : 0;
    int value = 0;
    Bound bound = BoundExact;
    if (wdl > draw_band) {
        value = syzygy::TbWin - ss->ply;
        bound = BoundLower;
    } else if (wdl < -draw_band) {
        value = -syzygy::TbWin + ss->ply;
        bound = BoundUpper;
    } else {
        value = syzygy::TbCursed * wdl;
    }
    const bool pv_node = beta - alpha > 1;
    if (bound != BoundExact && !pv_node && !(bound == BoundLower ? value >= beta : value <= alpha)) return ValueNone;
    shared_.tt.store(tt_probe, board.key(), score_to_tt(value, ss->ply), ValueNone, Move::none(),
                     std::min(depth + 6, MaxPly - 1), bound, ss->tt_pv, static_cast<std::uint16_t>(board.halfmove_clock()));
    return value;
}

namespace syzygy {

namespace {

// Reported score of a root rank (see rank_root_moves in syzygy.inc).
[[gnu::cold]] int rank_score(int rank) {
    if (rank > 1000) return TbWin - 1;
    if (rank > 0) return TbCursed;
    if (rank == 0) return 0;
    if (rank >= -1000) return -TbCursed;
    return -(TbWin - 1);
}

} // namespace

// Runs once per search before the workers start (Searcher::search).
[[gnu::cold]] void prepare_root(const Board& root, SearchLimits& limits) {
    const int largest = max_pieces();
    search_cardinality.store(largest, std::memory_order_relaxed);
    root_display.store(0, std::memory_order_relaxed);
    if (largest == 0 || root.castling_rights() != 0 || popcount(root.occupied()) > largest) return;
    Board board = root;
    std::vector<RootRank> ranks;
    bool used_dtz = false;
    if (!rank_root_moves(board, options::syzygy_50_move_rule, ranks, used_dtz) || ranks.empty()) return;
    int best = ranks.front().rank;
    for (const RootRank& r : ranks) best = std::max(best, r.rank);
    // Search only the best-ranked moves (de Man: "a regular search on the set
    // of moves with the highest rank"), within a given searchmoves list.
    std::vector<Move> keep;
    for (const RootRank& r : ranks) {
        if (r.rank != best) continue;
        if (limits.search_moves_specified &&
            std::find(limits.search_moves.begin(), limits.search_moves.end(), r.move) == limits.search_moves.end()) {
            continue;
        }
        keep.push_back(r.move);
    }
    if (keep.empty()) return;  // searchmoves exclude every best move: search them as given
    limits.search_moves = std::move(keep);
    limits.search_moves_specified = true;
    // With DTZ ranks the kept moves already secure the result and progress;
    // probes inside the search would only flatten their scores. With WDL ranks
    // keep probing while winning, so that the search finds the conversion.
    if (used_dtz || best <= 0) search_cardinality.store(0, std::memory_order_relaxed);
    root_display_score.store(rank_score(best), std::memory_order_relaxed);
    root_display.store(1, std::memory_order_relaxed);
}

[[gnu::cold]] int display_score(int search_score) {
    if (root_display.load(std::memory_order_relaxed) == 0 || is_mate_score(search_score)) return search_score;
    return root_display_score.load(std::memory_order_relaxed);
}

} // namespace syzygy
} // namespace forge
