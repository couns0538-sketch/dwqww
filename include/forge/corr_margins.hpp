#pragma once

#include "forge/search_tune.hpp"
#include "forge/search_types.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdlib>

// UCI CorrMargins: correction-size pruning margins (test plan G-B3).
//
// The correction history (src/search/evaluation.inc) learns how far search
// results have differed from the static evaluation for this pawn structure and
// material. The size of the correction applied at a node,
//     |correction| = |ss->static_eval - ss->raw_eval|   (centipawns),
// is therefore a measure of how little the static evaluation can be trusted
// there. With CorrMargins on, the main search (the second instance of
// src/search/alphabeta.inc, Worker::search_corr_margins) widens the static-eval
// margins of reverse futility pruning, futility pruning and null-move pruning
// and cuts the late-move reduction by a share that grows with |correction|:
// the larger the correction, the less it prunes and reduces.
//
// Every function here is the AL1 s198 formula plus a term that is 0 at
// |correction| = 0, monotonic in |correction|, and 0 for every |correction|
// when its tunable is 0 (tests/corr_margins_tests.cpp checks all three).
// With the default weights |correction| is at most 64 cp (pawn table +-32 cp
// plus material table +-32 cp); MaterialCorrectionWeight 300 allows 128 cp.
namespace forge::corr_margins {

// |correction| at a node; 0 when the node is in check (no static evaluation).
[[nodiscard]] inline int correction_size(bool in_check, int static_eval, int raw_eval) {
    if (in_check || static_eval == ValueNone || raw_eval == ValueNone) return 0;
    return std::abs(static_eval - raw_eval);
}

// R5A: |correction| * weight percent, with every weight applied at tune::CorrMarginsScale percent (UCI
// CorrMarginsScale, advertised, default 100). Exact integer arithmetic in 64 bits: for correction, weight >= 0,
// c * w * 100 / 10000 == c * w / 100, so the default scale gives the O5 formula bit for bit.
[[nodiscard]] inline int scaled_term(int correction, int weight_pct) {
    return static_cast<int>(static_cast<std::int64_t>(correction) * weight_pct * tune::CorrMarginsScale / 10000);
}

// Reverse futility pruning: the node returns eval when
// eval - rfp_margin(...) >= beta. AL1 s198: RfpMargin * depth - RfpImproving * improving.
[[nodiscard]] inline int rfp_margin(int depth, bool improving, int correction) {
    return tune::RfpMargin * depth - tune::RfpImproving * improving + scaled_term(correction, tune::CorrRfpPct);
}

// Futility pruning of quiet moves: the move is skipped when
// static_eval + futility_margin(...) <= alpha. AL1 s198: FutilityBase + FutilityMultiplier * lmr_depth.
[[nodiscard]] inline int futility_margin(int lmr_depth, int correction) {
    return tune::FutilityBase + tune::FutilityMultiplier * lmr_depth + scaled_term(correction, tune::CorrFutilityPct);
}

// Null-move pruning is tried only when static_eval >= null_move_threshold(...).
// AL1 s198: beta - 24 * depth + 180 (R3-4: tune::NullMoveMarginDepth = 24, tune::NullMoveMarginBase = 180).
[[nodiscard]] inline int null_move_threshold(int beta, int depth, int correction) {
    return beta - tune::NullMoveMarginDepth * depth + tune::NullMoveMarginBase + scaled_term(correction, tune::CorrNullMovePct);
}

// Late-move reduction after all AL1 s198 adjustments (r) minus a share of it:
// CorrLmrPct percent of r per 64 cp of |correction| (times CorrMarginsScale percent), rounded down, at most r.
// Reductions of 0 or less are returned unchanged. 64-bit product: r * c * pct * scale can pass 2^31 at the
// tunable limits.
[[nodiscard]] inline int lmr_reduction(int r, int correction) {
    if (r <= 0) return r;
    const std::int64_t relief =
        static_cast<std::int64_t>(r) * correction * tune::CorrLmrPct * tune::CorrMarginsScale / 640000;
    return r - static_cast<int>(std::min<std::int64_t>(r, relief));
}

} // namespace forge::corr_margins
