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
    // O6 / O7: a net with threat or pawn-pair inputs has its own update path (evaluation_extra.inc);
    // apply_nnue_v2 activates one only with the matching NNUEThreats / NNUEPawnPairs.
    if (net.threats || net.pawn_pairs) [[unlikely]] return static_evaluate_extra(board, ss);
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
    // O6 / O7: NNUEThreats 1 or NNUEPawnPairs 1 with NNUEKingBuckets 0 asks for a net without king buckets
    // (R3 stack: with NNUEOutputBuckets 0 as well that is a request for one king bucket; with NNUEOutputBuckets
    // N > 0, C5's rule applies: king count 0 = one unmirrored king bucket).
    const bool threats = nnue_threats != 0;
    const bool pawns = nnue_pawn_pairs != 0;
    const int wanted = nnue_king_buckets > 0 ? nnue_king_buckets : ((threats || pawns) && nnue_output_buckets <= 0 ? 1 : 0);
    const nnue::v2::Net* net = nnue::v2::select(nnue::enabled ? wanted : 0, nnue::enabled ? nnue_output_buckets : 0, message);
    if (net != nullptr && (net->threats != threats || net->pawn_pairs != pawns)) {
        // O6 / O7: the header's extra-input bits must agree with NNUEThreats / NNUEPawnPairs (nnue_v2_problem
        // names the mismatch).
        (void)nnue::v2::select(0, 0, nullptr);
        net = nullptr;
        if (message != nullptr) *message = "the loaded net's threat / pawn-pair inputs differ from NNUEThreats / NNUEPawnPairs (not selected)";
    }
    if (!nnue::enabled && message != nullptr) *message = "UseNNUE is false: hand-crafted evaluation only";
    nnue_v2 = net != nullptr;
    return nnue_v2;
}

[[gnu::cold]] std::string nnue_v2_problem(const std::string& file, const std::string& load_error) {
    const bool threats = nnue_threats != 0;
    const bool pawns = nnue_pawn_pairs != 0;
    const bool extras = threats || pawns;
    if (!nnue::enabled) return {};   // UseNNUE false: every network off on purpose
    const int kb = nnue_king_buckets;
    const int ob = nnue_output_buckets;
    if (file.empty() && kb <= 0 && ob <= 0 && !extras) return {};   // nothing requested
    if (!file.empty() && !load_error.empty()) return "cannot load NNUEFile " + file + ": " + load_error;
    const nnue::v2::Net* net = nnue::v2::loaded();
    if (net == nullptr) {
        if (!file.empty()) return "NNUEFile " + file + " is not loaded";
        if (kb <= 0 && ob <= 0) {   // O6 / O7: NNUEThreats or NNUEPawnPairs alone
            return threats ? "NNUEThreats is 1 but no v2 net is loaded (NNUEFile is empty); NNUEThreats needs a net with threat "
                             "inputs (trainer --threats)"
                           : "NNUEPawnPairs is 1 but no v2 net is loaded (NNUEFile is empty); NNUEPawnPairs needs a net with "
                             "pawn-pair inputs (trainer --pawn-pairs)";
        }
        const std::string set = kb > 0 && ob > 0 ? "NNUEKingBuckets " + std::to_string(kb) + " and NNUEOutputBuckets " +
                                                       std::to_string(ob) + " are"
                                : kb > 0 ? "NNUEKingBuckets " + std::to_string(kb) + " is"
                                         : "NNUEOutputBuckets " + std::to_string(ob) + " is";
        return set + " set but no v2 net is loaded (NNUEFile is empty)";
    }
    if (nnue_v2 && nnue::v2::active() == net) return {};
    const std::string buckets = std::to_string(net->king_buckets) + (net->mirror ? " mirrored" : "") + " king buckets";
    // O6 / O7: the extra-input bits of the file and NNUEThreats / NNUEPawnPairs must agree.
    const std::string threat_net = "NNUEFile " + net->path + " has threat inputs (trainer --threats); set NNUEThreats 1 to use it";
    const std::string pawn_net = "NNUEFile " + net->path + " has pawn-pair inputs (trainer --pawn-pairs); set NNUEPawnPairs 1 to use it";
    // C4 / C5: the bucket counts that select this net (select(): 0 stands for one unmirrored king bucket / one
    // output bucket); the extra-input options the net needs are named as well.
    int want_kb = net->king_buckets == 1 && !net->mirror ? 0 : net->king_buckets;
    const int want_ob = net->output_buckets == 1 ? 0 : net->output_buckets;
    if (want_kb == 0 && want_ob == 0) want_kb = 1;
    const std::string shape = buckets + ", " + std::to_string(net->output_buckets) + " output buckets";
    const std::string hint = "; to use it set NNUEKingBuckets " + std::to_string(want_kb) + ", NNUEOutputBuckets " +
                             std::to_string(want_ob) + (net->threats ? ", NNUEThreats 1" : "") +
                             (net->pawn_pairs ? ", NNUEPawnPairs 1" : "");
    // The request as apply_nnue_v2() passes it to select().
    const int wanted_kb = kb > 0 ? kb : (extras && ob <= 0 ? 1 : 0);
    const bool king_ok = wanted_kb > 0 ? net->king_buckets == wanted_kb : (net->king_buckets == 1 && !net->mirror);
    const bool output_ok = ob > 0 ? net->output_buckets == ob : net->output_buckets == 1;
    if (kb <= 0 && ob <= 0 && !extras) {   // a file without any bucket or extra-input option
        if (net->king_buckets == 1 && net->output_buckets == 1 && net->threats) return threat_net;
        if (net->king_buckets == 1 && net->output_buckets == 1 && net->pawn_pairs) return pawn_net;
        return "NNUEFile " + net->path + " is loaded (" + shape + ") but NNUEKingBuckets is 0 and NNUEOutputBuckets is 0" + hint;
    }
    if (!king_ok && kb <= 0 && ob <= 0 && extras) {
        return std::string(threats ? "NNUEThreats" : "NNUEPawnPairs") + " is 1 and NNUEKingBuckets is 0, which selects a net "
               "without king buckets, but NNUEFile " + net->path + " has " + buckets + "; set NNUEKingBuckets " +
               std::to_string(net->king_buckets) + " as well";
    }
    if (!king_ok || !output_ok) {
        return "NNUEFile " + net->path + " (" + shape + ") does not match NNUEKingBuckets " + std::to_string(kb) +
               ", NNUEOutputBuckets " + std::to_string(ob) + hint;
    }
    if (threats && !net->threats) {
        return "NNUEThreats is 1 but NNUEFile " + net->path + " has no threat inputs; NNUEThreats needs a net trained with "
               "--threats";
    }
    if (pawns && !net->pawn_pairs) {
        return "NNUEPawnPairs is 1 but NNUEFile " + net->path + " has no pawn-pair inputs; NNUEPawnPairs needs a net trained "
               "with --pawn-pairs";
    }
    if (!threats && net->threats) return threat_net;
    if (!pawns && net->pawn_pairs) return pawn_net;
    return "NNUEFile " + net->path + " was not selected";   // not reached: every unselected case is named above
}


} // namespace options

} // namespace forge
