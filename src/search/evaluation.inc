// Search module: static evaluation glue (lazy NNUE accumulators, residual
// HCE + network) and pawn/material correction history.
// Compiled as part of src/search.cpp (included exactly once).

// Padding bytes in a cold branch (see Worker::static_evaluate). Only for the
// MinGW g++ build whose layout was measured; elsewhere a no-op.
#if defined(__MINGW32__) && defined(__GNUC__) && !defined(__clang__) && defined(__x86_64__)
#define FORGE_LAYOUT_PAD(bytes) asm volatile(".nops " #bytes)
#else
#define FORGE_LAYOUT_PAD(bytes) ((void)0)
#endif

namespace forge {

namespace {
// Hash of the piece counts of both sides, for material-indexed statistics.
// Always inlined: it also has a call site in the cold CorrHistPlus path, and an
// out-of-line copy would be emitted at the start of the hot .text.
[[gnu::always_inline]] [[nodiscard]] inline std::uint64_t material_key(const Board& board) {
#ifdef FORGE_SPEEDSTACK
    // Speed stack (S29, piece S11): the same 64-bit key as the polynomial below, from a contribution table.
    return matkey::table_key(board);
#else
    // S11 MaterialKeyTable: the same key from a contribution table (forge/material_key_table.hpp).
    if (options::material_key_table) [[unlikely]] return matkey::table_key(board);
    std::uint64_t key = 0;
    for (const Color color : {White, Black}) {
        for (int type = Pawn; type <= Queen; ++type) {
            key = key * 1099511628211ULL + static_cast<std::uint64_t>(popcount(board.pieces(color, static_cast<PieceType>(type))) + 1);
        }
    }
    return key * 0x9E3779B97F4A7C15ULL;
#endif
}
} // namespace

int Worker::static_evaluate(const Board& board, SearchStack* ss) {
    if (options::nnue_v2) [[unlikely]] {
        // Layout pad: with it the dispatch grows this function by exactly 64
        // bytes in the PC build (MinGW g++ 15.2), so the search functions
        // emitted after it keep their AL1 s198 addresses mod 64.
        FORGE_LAYOUT_PAD(32);
        return static_evaluate_v2(board, ss);
    }
    if (!nnue::enabled || !nnue::available()) return evaluator_.evaluate(board);
    const bool residual = nnue::residual();
    if (!ss->accumulator.valid) {
        // Walk back to the nearest valid accumulator, then replay the moves.
        int back = 0;
        while (back < ss->ply && !(ss - back - 1)->accumulator.valid) ++back;
        if (back >= ss->ply && !(ss - back - 1)->accumulator.valid) {
            nnue::refresh(board, ss->accumulator);
            if (residual) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
        } else {
            for (int i = back; i >= 0; --i) {
                nnue::update((ss - i - 1)->accumulator, (ss - i)->accumulator, (ss - i)->dirty);
                if (residual) Evaluator::update_runtime_psqt((ss - i - 1)->runtime_psqt, (ss - i)->runtime_psqt, (ss - i)->dirty);
            }
        }
    }
    const int network = nnue::evaluate(board, ss->accumulator);
    if (!residual) return network;
    if (!ss->runtime_psqt.valid) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    // A residual network is a learned correction on top of the hand-crafted evaluation.
    return std::clamp(evaluator_.evaluate_runtime(board, ss->runtime_psqt) + network, -MateInMaxPly + 1, MateInMaxPly - 1);
}

void Worker::record_move(SearchStack* ss, const Board& board, const Move& move) {
    // Called before make_move: the child's accumulator becomes stale and the
    // piece changes are remembered for the lazy update.
    if (!nnue::enabled || !nnue::available()) return;
    (ss + 1)->dirty = nnue::dirty_pieces(board, move);
    (ss + 1)->accumulator.valid = false;
    (ss + 1)->runtime_psqt.valid = false;
}

void Worker::record_null_move(SearchStack* ss) {
    (ss + 1)->dirty.count = 0;
    (ss + 1)->accumulator.valid = false;
    (ss + 1)->runtime_psqt.valid = false;
}

int Worker::corrected_eval(const Board& board, int raw_eval) const {
    // CorrHistPlus (default 0 = off): one predictable branch; the cold path
    // computes this correction plus the extra keys (correction_plus.inc).
    if (options::corr_hist_plus != 0) [[unlikely]] return corrected_eval_plus(board, raw_eval);
    const std::size_t side = static_cast<std::size_t>(board.side_to_move());
    std::int32_t correction = (*correction_history_)[side][board.pawn_key() & (CorrectionSize - 1U)];
    if (tune::MaterialCorrectionWeight > 0) {
        correction += (*material_correction_)[side][material_key(board) & (CorrectionSize - 1U)] * tune::MaterialCorrectionWeight / 100;
    }
    return std::clamp(raw_eval + correction / CorrectionGrain, -MateInMaxPly + 1, MateInMaxPly - 1);
}

void Worker::update_correction(const Board& board, int depth, int best_score, int static_eval) {
    // CorrHistPlus (default 0 = off): one predictable branch; the cold path
    // performs this update plus the extra keys (correction_plus.inc).
    if (options::corr_hist_plus != 0) [[unlikely]] return update_correction_plus(board, depth, best_score, static_eval);
    const std::size_t side = static_cast<std::size_t>(board.side_to_move());
    const int diff = std::clamp((best_score - static_eval) * CorrectionGrain, -CorrectionLimit / 4, CorrectionLimit / 4);
    const int weight = std::min(depth + 1, 16);
    auto apply = [&](std::int32_t& entry) {
        entry = std::clamp(entry + diff * weight / 256, -CorrectionLimit, CorrectionLimit);
    };
    apply((*correction_history_)[side][board.pawn_key() & (CorrectionSize - 1U)]);
    if (tune::MaterialCorrectionWeight > 0) apply((*material_correction_)[side][material_key(board) & (CorrectionSize - 1U)]);
}

} // namespace forge
