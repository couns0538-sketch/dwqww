// Search module: static evaluation with a v2 network that has extra input blocks: threat inputs (O6; UCI
// NNUEThreats) and / or pawn-pair inputs (O7; UCI NNUEPawnPairs), both OFF by default; the feature definitions are
// in forge/nnue_v2.hpp at ThreatFeatures and PawnPairFeatures. Compiled as part of src/search.cpp (included exactly
// once, before evaluation_v2.inc, whose static_evaluate_v2 calls it: GCC emits a caller after its callees). The
// function lives in section .text.forge_v2 like the rest of the v2 code, so the default build's .text is unchanged.
//
// Reached only through static_evaluate_v2 when the active net has an extra block. Accumulators follow C4's lazy
// scheme: an invalid ply walks back to the nearest valid ancestor and replays the recorded piece changes; every
// replayed ply becomes valid. Per replayed ply, the child's piece placement is the parent's with that ply's piece
// changes applied (starting from the board with every replayed ply taken back). Threat inputs: the child's threat
// list is generated and the multiset difference to the parent's list is applied (each computed ply's list is kept
// in the worker's cache, RefreshCache::ply_threats, so the valid ancestor's list is read). Pawn-pair inputs: each
// perspective's pawn-pair list is kept per ply in the worker's cache (RefreshCache::ply_pawns) next to the accumulator;
// it is regenerated only on a ply that moves,
// captures or promotes a pawn (other plies cannot change pawn pairs), and the difference is applied. All changes of
// a ply go through one chunked pass over each perspective's accumulator. On a king-key change the perspective is
// refreshed: piece-square inputs through the refresh cache, then every threat / pawn-pair column of the child.
// All weights are int16 / 4096, so every accumulator value is an exact multiple of 2^-12 and incremental, cached
// and from-scratch accumulators are bit-identical (tests/nnue_threat_tests.cpp, tests/nnue_pawn_pair_tests.cpp).

namespace forge {

__attribute__((section(".text.forge_v2"), noinline)) int Worker::static_evaluate_extra(const Board& board, SearchStack* ss) {
    const nnue::v2::Net& net = *nnue::v2::active();
    const bool residual = net.residual;
    const bool threats = net.threats;
    const bool pawns = net.pawn_pairs;
    if (!ss->accumulator.valid) {
        nnue::v2::RefreshCache& cache = nnue::v2::cache(net, id_);
        if (threats && cache.ply_threats.empty()) [[unlikely]] cache.ply_threats.resize(static_cast<std::size_t>(MaxPly + 8));
        auto list_of = [&cache](const SearchStack* entry) -> nnue::v2::ThreatList& {
            return cache.ply_threats[static_cast<std::size_t>(entry->ply + 4)];
        };
        if (pawns && cache.ply_pawns.empty()) [[unlikely]] cache.ply_pawns.resize(static_cast<std::size_t>(MaxPly + 8));
        auto pawns_of = [&cache](const SearchStack* entry) -> std::array<nnue::v2::PawnPairList, 2>& {
            return cache.ply_pawns[static_cast<std::size_t>(entry->ply + 4)];
        };
        int back = 0;
        while (back < ss->ply && !(ss - back - 1)->accumulator.valid) ++back;
        nnue::v2::Pieces pieces = nnue::v2::pieces_of(board);
        if (back >= ss->ply && !(ss - back - 1)->accumulator.valid) {
            if (threats) nnue::v2::threat_keys(pieces, list_of(ss));
            for (const Color color : {White, Black}) {
                const std::size_t c = static_cast<std::size_t>(color);
                nnue::v2::refresh_full_cached(net, cache, pieces, threats ? &list_of(ss) : nullptr, board.king_square(color), color,
                                              ss->accumulator.values[c].data(), pawns ? &pawns_of(ss)[c] : nullptr);
            }
            ss->accumulator.valid = true;
            if (residual) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
        } else {
            for (int k = 0; k <= back; ++k) nnue::v2::undo(pieces, (ss - k)->dirty);   // the valid ancestor's placement
            auto king_of = [&pieces](Color color) { return lsb(pieces[static_cast<std::size_t>(make_piece(color, King))]); };
            std::array<nnue::v2::KingKey, 2> key{nnue::v2::king_key(net, White, king_of(White)),
                                                 nnue::v2::king_key(net, Black, king_of(Black))};
            nnue::v2::ThreatDelta delta;
            nnue::v2::PawnPairDelta pawn_delta;
            constexpr std::size_t MaxColumns = nnue::v2::MaxThreatPairs + nnue::v2::MaxPawnPairs + 4;
            std::array<const float*, MaxColumns> sub;
            std::array<const float*, MaxColumns> add;
            for (int i = back; i >= 0; --i) {
                const SearchStack* parent = ss - i - 1;
                SearchStack* child = ss - i;
                const nnue::DirtyPieces& dirty = child->dirty;
                nnue::v2::redo(pieces, dirty);   // the child's placement
                nnue::v2::ThreatList* after = nullptr;
                if (threats) {
                    after = &list_of(child);   // the parent's list is valid: computed with the parent's accumulator
                    nnue::v2::threat_keys(pieces, *after);
                    nnue::v2::threat_delta(list_of(parent), *after, cache.threat_counts.data(), delta);
                }
                const bool pawn_move = pawns && nnue::v2::touches_pawns(dirty);
                // The parent's pawn-pair lists are valid (computed with the parent's accumulator); a ply that touches
                // no pawn keeps them (copied to the child's slot, a king-key refresh below may still replace one).
                if (pawns && !pawn_move) pawns_of(child) = pawns_of(parent);
                for (const Color color : {White, Black}) {
                    const std::size_t c = static_cast<std::size_t>(color);
                    const int king_square = king_of(color);
                    const nnue::v2::KingKey moved = nnue::v2::king_key(net, color, king_square);
                    if (!(moved == key[c])) [[unlikely]] {
                        key[c] = moved;
                        nnue::v2::refresh_full_cached(net, cache, pieces, after, king_square, color,
                                                      child->accumulator.values[c].data(), pawns ? &pawns_of(child)[c] : nullptr);
                        continue;
                    }
                    int subs = 0;
                    int adds = 0;
                    for (int k = 0; k < dirty.count; ++k) {
                        const nnue::PieceChange& change = dirty.changes[static_cast<std::size_t>(k)];
                        const float* col = nnue::v2::column(net, color, key[c], change.piece, change.square);
                        if (change.add) add[static_cast<std::size_t>(adds++)] = col;
                        else sub[static_cast<std::size_t>(subs++)] = col;
                    }
                    if (threats) {
                        for (int k = 0; k < delta.removed; ++k) {
                            sub[static_cast<std::size_t>(subs++)] = nnue::v2::threat_column(net, color, key[c], delta.remove_keys[static_cast<std::size_t>(k)]);
                        }
                        for (int k = 0; k < delta.added; ++k) {
                            add[static_cast<std::size_t>(adds++)] = nnue::v2::threat_column(net, color, key[c], delta.add_keys[static_cast<std::size_t>(k)]);
                        }
                    }
                    if (pawn_move) {
                        nnue::v2::PawnPairList& pawn_child = pawns_of(child)[c];
                        nnue::v2::pawn_pair_features(pieces, color, key[c].flip, pawn_child);
                        nnue::v2::pawn_pair_delta(pawns_of(parent)[c], pawn_child, cache.pawn_counts.data(), pawn_delta);
                        for (int k = 0; k < pawn_delta.removed; ++k) {
                            sub[static_cast<std::size_t>(subs++)] = nnue::v2::pawn_pair_column(net, pawn_delta.remove_features[static_cast<std::size_t>(k)]);
                        }
                        for (int k = 0; k < pawn_delta.added; ++k) {
                            add[static_cast<std::size_t>(adds++)] = nnue::v2::pawn_pair_column(net, pawn_delta.add_features[static_cast<std::size_t>(k)]);
                        }
                    }
                    nnue::v2::apply_lists(parent->accumulator.values[c].data(), child->accumulator.values[c].data(), sub.data(), subs,
                                          add.data(), adds);
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

} // namespace forge
