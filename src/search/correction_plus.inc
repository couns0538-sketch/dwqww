// Search module: CorrHistPlus, the extra correction-history keys
// (forge/correction_plus.hpp, UCI option CorrHistPlus, default 0 = off).
// Compiled as part of src/search.cpp (included exactly once, after
// evaluation.inc).
//
// How the default build stays the AL1 s198 build: Worker::corrected_eval and
// Worker::update_correction (evaluation.inc) only gained one branch at their
// top, `if (options::corr_hist_plus != 0) [[unlikely]] return <twin>(...)`,
// which jumps with the arguments untouched to the cold twins below. Each twin
// repeats the AL1 s198 statements of its hot counterpart and adds the extra
// keys. The twins are [[gnu::cold]], so GCC places them in .text.unlikely,
// away from the hot .text. corrected_eval_plus is also a leaf (all helpers
// are always_inline): GCC's interprocedural register allocation lets the
// callers of corrected_eval (search, qsearch) keep values in registers that
// corrected_eval leaves alone, so a twin that called other functions would
// clobber them and change the callers' code.

namespace forge {

// Frame of the node whose evaluation is being corrected. corrected_eval and
// update_correction run on the search board of that node, every make_move /
// make_null_move between the root and the node pushed one key onto the board
// history, the root frame is stack_[4] and the child of frame ss is ss + 1
// (iterative.inc, alphabeta.inc, qsearch.inc), so the board history gives the
// frame without passing it through the hot callers. The ply recorded in the
// frame confirms it; anything else (e.g. a probe outside a search) gets none.
inline const SearchStack* Worker::correction_frame(const Board& board) const {
    const std::size_t history = board.history_size();
    if (history <= root_history_index_) return nullptr;
    const std::size_t ply = history - 1 - root_history_index_;
    if (ply > static_cast<std::size_t>(MaxPly)) return nullptr;
    const SearchStack* ss = &stack_[4 + ply];
    return ss->ply == static_cast<int>(ply) ? ss : nullptr;
}

// Continuation-table slot of the node (forge::corrplus::continuation_index), or
// ContinuationSize when the previous two moves are not both known: next to the
// root (the sentinel frames hold no move) or after a null move.
inline std::size_t Worker::continuation_correction_index(const Board& board) const {
    const SearchStack* ss = correction_frame(board);
    if (ss == nullptr) return corrplus::ContinuationSize;
    const SearchStack* theirs = ss - 1;  // the move that led to this node
    const SearchStack* ours = ss - 2;    // our move before it
    const Color side = board.side_to_move();
    if (theirs->current_move.is_none() || ours->current_move.is_none() ||
        theirs->moved_piece == Empty || ours->moved_piece == Empty ||
        color_of(ours->moved_piece) != side || color_of(theirs->moved_piece) == side) {
        return corrplus::ContinuationSize;
    }
    // The colours are fixed by the side to move (checked above): the piece type
    // is the piece minus its colour offset (no modulo in this size-optimised code).
    const int ours_offset = side == White ? 0 : 6;
    return corrplus::continuation_index(side, static_cast<int>(ours->moved_piece) - ours_offset, ours->current_move.to,
                                        static_cast<int>(theirs->moved_piece) - (6 - ours_offset), theirs->current_move.to);
}

// Correction of the enabled extra keys in CorrectionGrain units (weighted,
// clamped by corrplus::blend); added to the pawn + material correction.
inline int Worker::correction_plus(const Board& board) const {
    const corrplus::Tables* tables = correction_plus_.get();
    if (tables == nullptr) return 0;  // nothing learned yet: the first update allocates the tables
    const int keys = options::corr_hist_plus;
    const std::size_t side = static_cast<std::size_t>(board.side_to_move());
    int sum = 0;
    if ((keys & corrplus::Continuation) != 0) {
        const std::size_t index = continuation_correction_index(board);
        if (index < corrplus::ContinuationSize) sum += tables->continuation[index] * tune::CorrContWeight;
    }
    if ((keys & corrplus::MinorPiece) != 0) {
        sum += tables->minor[side][corrplus::key_index(corrplus::minor_piece_key(board))] * tune::CorrMinorWeight;
    }
    if ((keys & corrplus::NonPawn) != 0) {
        const int white = tables->non_pawn[White][side][corrplus::key_index(corrplus::non_pawn_key(board, White))];
        const int black = tables->non_pawn[Black][side][corrplus::key_index(corrplus::non_pawn_key(board, Black))];
        sum += (white + black) * tune::CorrNonPawnWeight;
    }
    return corrplus::blend(sum);
}

// corrected_eval with CorrHistPlus on: the AL1 s198 statements of
// corrected_eval (pawn + material correction; the divisions written as
// corrplus::div100 / div_pow2, the same values) plus the extra keys.
int Worker::corrected_eval_plus(const Board& board, int raw_eval) const {
    const std::size_t side = static_cast<std::size_t>(board.side_to_move());
    std::int32_t correction = (*correction_history_)[side][board.pawn_key() & (CorrectionSize - 1U)];
    if (tune::MaterialCorrectionWeight > 0) {
        correction += corrplus::div100((*material_correction_)[side][material_key(board) & (CorrectionSize - 1U)] * tune::MaterialCorrectionWeight);
    }
    // R3 stack: HistRework's joint term as in corrected_eval, so HistRework and CorrHistPlus combine.
    if (const int level = search_options::hist_rework; level != 0) [[unlikely]] {
        // HistRework: pawn structure x non-pawn material. |entry| <= 8192, weight <= 100: |term| <= 8192.
        correction += (*joint_correction_)[side][hist_rework::joint_key(board) & (CorrectionSize - 1U)] *
                      hist_rework::joint_weight(level) / 100;
    }
    correction += correction_plus(board);
    return std::clamp(raw_eval + corrplus::div_pow2<8>(correction), -MateInMaxPly + 1, MateInMaxPly - 1);
}

// update_correction with CorrHistPlus on: the AL1 s198 statements of
// update_correction (pawn + material tables; / 256 written as div_pow2<8>,
// the same value) plus the extra keys. The search
// calls update_correction under one rule for all tables: not in check, no
// excluded move, no mate score, best move quiet (or none), and the bound on the
// side of the difference (alphabeta.inc). The extra entries take the same
// residual and depth weight (corrplus::step) with a decay (corrplus::apply).
void Worker::update_correction_plus(const Board& board, int depth, int best_score, int static_eval) {
    const std::size_t side = static_cast<std::size_t>(board.side_to_move());
    const int diff = std::clamp((best_score - static_eval) * CorrectionGrain, -CorrectionLimit / 4, CorrectionLimit / 4);
    const int weight = std::min(depth + 1, 16);
    auto apply = [&](std::int32_t& entry) {
        entry = std::clamp(entry + corrplus::div_pow2<8>(diff * weight), -CorrectionLimit, CorrectionLimit);
    };
    apply((*correction_history_)[side][board.pawn_key() & (CorrectionSize - 1U)]);
    if (tune::MaterialCorrectionWeight > 0) apply((*material_correction_)[side][material_key(board) & (CorrectionSize - 1U)]);
    // R3 stack: HistRework's joint update as in update_correction, so HistRework and CorrHistPlus combine.
    if (search_options::hist_rework != 0) [[unlikely]] {
        // HistRework: the joint table learns the same residual step (|step| <= 2048 * 16 / 256 = 128) with a
        // gravity-style damping instead of the lock's add-and-clamp; the lock tables above are unchanged.
        std::int32_t& entry = (*joint_correction_)[side][hist_rework::joint_key(board) & (CorrectionSize - 1U)];
        entry = hist_rework::gravity(entry, diff * weight / 256, CorrectionLimit);
    }

    if (!correction_plus_) {
        // Value-initialised (all entries 0). On allocation failure the extra keys stay unused.
        correction_plus_.reset(new (std::nothrow) corrplus::Tables());
        if (!correction_plus_) return;
    }
    corrplus::Tables& tables = *correction_plus_;
    const int keys = options::corr_hist_plus;
    const int step = corrplus::step(best_score, static_eval, depth);
    auto learn = [step](corrplus::Entry& entry) { entry = static_cast<corrplus::Entry>(corrplus::apply(entry, step)); };
    if ((keys & corrplus::Continuation) != 0) {
        const std::size_t index = continuation_correction_index(board);
        if (index < corrplus::ContinuationSize) learn(tables.continuation[index]);
    }
    if ((keys & corrplus::MinorPiece) != 0) {
        learn(tables.minor[side][corrplus::key_index(corrplus::minor_piece_key(board))]);
    }
    if ((keys & corrplus::NonPawn) != 0) {
        learn(tables.non_pawn[White][side][corrplus::key_index(corrplus::non_pawn_key(board, White))]);
        learn(tables.non_pawn[Black][side][corrplus::key_index(corrplus::non_pawn_key(board, Black))]);
    }
}

} // namespace forge
