// Search module: the upcoming-repetition draw bound (UCI CuckooRep, default off).
// Compiled as part of src/search.cpp (included exactly once), after the
// CuckooRep instances of the quiescence and main search (qsearch_cuckoo_body,
// search_cuckoo_body and, R3 stack, search_{cm,ce,cm_ce}_cu_body), whose
// quiescence and child calls come here.
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

namespace {
// Board::upcoming_repetition() is false below a halfmove clock of 3 (no earlier
// position at distance 3 inside the window); testing that inline first skips the
// call at the many nodes just after a capture or pawn move.
[[nodiscard]] inline bool may_repeat(const Board& board) { return board.halfmove_clock() >= 3; }
} // namespace

// One wrapper per CuckooRep instance of the main search (R3 stack: CuckooRep
// alone, as on opus-C6, and with CorrMargins / CorrExt); BODY is the instance.
#define FORGE_CUCKOO_SEARCH_WRAPPER(WRAPPER, BODY)                                                              \
    int Worker::WRAPPER(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {          \
        constexpr int DrawScore = 0;                                                                             \
        if (depth > 0 && alpha < DrawScore && ss->ply != 0 && ss->excluded_move.is_none() && may_repeat(board) && \
            board.upcoming_repetition(root_history_index_)) {                                                    \
            if (beta <= DrawScore) return DrawScore;                                                             \
            return std::max(BODY(board, ss, depth, DrawScore, beta, cut_node), DrawScore);                      \
        }                                                                                                        \
        return BODY(board, ss, depth, alpha, beta, cut_node);                                                   \
    }

FORGE_CUCKOO_SEARCH_WRAPPER(search_cuckoo, search_cuckoo_body)
FORGE_CUCKOO_SEARCH_WRAPPER(search_cm_cu, search_cm_cu_body)
FORGE_CUCKOO_SEARCH_WRAPPER(search_ce_cu, search_ce_cu_body)
FORGE_CUCKOO_SEARCH_WRAPPER(search_cm_ce_cu, search_cm_ce_cu_body)
#undef FORGE_CUCKOO_SEARCH_WRAPPER

int Worker::qsearch_cuckoo(Board& board, SearchStack* ss, int alpha, int beta) {
    constexpr int DrawScore = 0;
    if (alpha < DrawScore && may_repeat(board) && board.upcoming_repetition(root_history_index_)) {
        if (beta <= DrawScore) return DrawScore;
        return std::max(qsearch_cuckoo_body(board, ss, DrawScore, beta), DrawScore);
    }
    return qsearch_cuckoo_body(board, ss, alpha, beta);
}

} // namespace forge
