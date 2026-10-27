// Search module: the upcoming-repetition draw bound (UCI CuckooRep, default off).
// Compiled as part of src/search.cpp (included exactly once), after the
// CuckooRep instances of the quiescence and main search (qsearch_cuckoo_body,
// search_cuckoo_body), whose quiescence and child calls come here.
//
// At a node whose side to move has a legal reversible move into a position the
// search scores as a repetition draw (Board::upcoming_repetition: an earlier
// occurrence inside the rule-50 and null-move window, at or after the root, or
// two before it), the draw score is a lower bound. With alpha below it the node
// fails high at once when beta is at or below the draw score; otherwise it is
// searched with alpha raised to the draw score and its result is kept at or
// above the draw score (a fail-low there, e.g. because pruning skipped the
// drawing move, still proves no less than the draw). Nodes with an excluded
// move (singular verification) are left alone: the drawing move could be the
// excluded one. The root never gets the bound. Depth-0 nodes are handed to
// quiescence unchanged and get the bound there (one detector call per node).

namespace forge {

int Worker::search_cuckoo(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {
    constexpr int DrawScore = 0;
    if (depth > 0 && alpha < DrawScore && ss->ply != 0 && ss->excluded_move.is_none() &&
        board.upcoming_repetition(root_history_index_)) {
        if (beta <= DrawScore) return DrawScore;
        return std::max(search_cuckoo_body(board, ss, depth, DrawScore, beta, cut_node), DrawScore);
    }
    return search_cuckoo_body(board, ss, depth, alpha, beta, cut_node);
}

int Worker::qsearch_cuckoo(Board& board, SearchStack* ss, int alpha, int beta) {
    constexpr int DrawScore = 0;
    if (alpha < DrawScore && board.upcoming_repetition(root_history_index_)) {
        if (beta <= DrawScore) return DrawScore;
        return std::max(qsearch_cuckoo_body(board, ss, DrawScore, beta), DrawScore);
    }
    return qsearch_cuckoo_body(board, ss, alpha, beta);
}

} // namespace forge
