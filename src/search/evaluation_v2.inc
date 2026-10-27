// Search module: static evaluation with a v2 network (C4: king-bucketed input
// layer, C5: output buckets; UCI NNUEFile + NNUEKingBuckets / NNUEOutputBuckets,
// OFF by default; forge/nnue_v2.hpp).
// Compiled as part of src/search.cpp (included exactly once, before
// evaluation.inc so that GCC keeps emitting static_evaluate at its AL1 s198
// position: a caller is emitted after its callees).
//
// Reached only through the options::nnue_v2 branch at the top of
// Worker::static_evaluate. This code lives in section .text.forge_v2 (or is
// cold), so the default build's search functions keep their addresses.
//
// Accumulators reuse SearchStack::accumulator (a v2 net has the engine's
// HiddenSize) with the lazy scheme of the compiled-in network: an invalid ply
// walks back to the nearest valid ancestor and replays the recorded piece
// changes, and every replayed ply becomes valid. New for king buckets: on a ply
// where a king changes its own perspective's (bucket, flip) key, that
// perspective is refreshed through the worker's refresh cache. The piece
// placement of that ply is the board with the later plies' piece changes taken
// back, so no board copy is kept per ply.

#define FORGE_SEARCH_V2 __attribute__((section(".text.forge_v2"), noinline))

namespace forge {

FORGE_SEARCH_V2 int Worker::static_evaluate_v2(const Board& board, SearchStack* ss) {
    // nnue_v2 is only set while a v2 net is active; the UCI layer re-selects
    // after every change, so this fallback is defensive.
    const nnue::v2::Net* active = nnue::v2::active();
    if (active == nullptr || !nnue::enabled) return evaluator_.evaluate(board);
    const nnue::v2::Net& net = *active;
    const bool residual = net.residual;
    if (!ss->accumulator.valid) {
        int back = 0;
        while (back < ss->ply && !(ss - back - 1)->accumulator.valid) ++back;
        if (back >= ss->ply && !(ss - back - 1)->accumulator.valid) {
            nnue::v2::RefreshCache& cache = nnue::v2::cache(net, id_);
            const nnue::v2::Pieces pieces = nnue::v2::pieces_of(board);
            nnue::v2::refresh_cached(net, cache, pieces, board.king_square(White), White, ss->accumulator.values[White].data());
            nnue::v2::refresh_cached(net, cache, pieces, board.king_square(Black), Black, ss->accumulator.values[Black].data());
            ss->accumulator.valid = true;
            if (residual) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
        } else {
            // King squares of the ancestor position: take back the replayed king
            // moves (changes[0] is always the moving piece, removed from `from`).
            std::array<int, 2> king{board.king_square(White), board.king_square(Black)};
            for (int i = 0; i <= back; ++i) {
                const nnue::DirtyPieces& dirty = (ss - i)->dirty;
                if (dirty.count > 0 && piece_type(dirty.changes[0].piece) == King) {
                    king[static_cast<std::size_t>(color_of(dirty.changes[0].piece))] = dirty.changes[0].square;
                }
            }
            std::array<nnue::v2::KingKey, 2> key{nnue::v2::king_key(net, White, king[0]),
                                                 nnue::v2::king_key(net, Black, king[1])};
            for (int i = back; i >= 0; --i) {
                const SearchStack* parent = ss - i - 1;
                SearchStack* child = ss - i;
                const nnue::DirtyPieces& dirty = child->dirty;
                for (const Color color : {White, Black}) {
                    const std::size_t c = static_cast<std::size_t>(color);
                    if (dirty.count > 0 && dirty.changes[0].piece == make_piece(color, King)) {
                        // The king's destination: the added change of the same piece.
                        int to = dirty.changes[0].square;
                        for (int k = 1; k < dirty.count; ++k) {
                            const nnue::PieceChange& change = dirty.changes[static_cast<std::size_t>(k)];
                            if (change.add && change.piece == dirty.changes[0].piece) to = change.square;
                        }
                        const nnue::v2::KingKey moved = nnue::v2::king_key(net, color, to);
                        if (!(moved == key[c])) [[unlikely]] {
                            key[c] = moved;
                            nnue::v2::Pieces pieces = nnue::v2::pieces_of(board);
                            for (int k = 0; k < i; ++k) nnue::v2::undo(pieces, (ss - k)->dirty);
                            nnue::v2::refresh_cached(net, nnue::v2::cache(net, id_), pieces, to, color,
                                                     child->accumulator.values[c].data());
                            continue;
                        }
                    }
                    nnue::v2::update(net, color, key[c], parent->accumulator.values[c].data(),
                                     child->accumulator.values[c].data(), dirty);
                }
                child->accumulator.valid = true;
                if (residual) Evaluator::update_runtime_psqt(parent->runtime_psqt, child->runtime_psqt, dirty);
            }
        }
    }
    const int network = nnue::v2::evaluate(net, board, ss->accumulator);
    if (!residual) return network;
    if (!ss->runtime_psqt.valid) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    // A residual network is a learned correction on top of the hand-crafted evaluation.
    return std::clamp(evaluator_.evaluate_runtime(board, ss->runtime_psqt) + network, -MateInMaxPly + 1, MateInMaxPly - 1);
}

namespace options {

[[gnu::cold]] bool apply_nnue_v2(std::string* message) {
    // UseNNUE false disables every network (hand-crafted evaluation only).
    const nnue::v2::Net* net = nnue::v2::select(nnue::enabled ? nnue_king_buckets : 0,
                                                nnue::enabled ? nnue_output_buckets : 0, message);
    if (!nnue::enabled && (nnue_king_buckets > 0 || nnue_output_buckets > 0) && message != nullptr) {
        *message = "UseNNUE is false: hand-crafted evaluation only";
    }
    nnue_v2 = net != nullptr;
    return nnue_v2;
}

} // namespace options

} // namespace forge
