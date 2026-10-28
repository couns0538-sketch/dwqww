#pragma once

#include "forge/search_tune.hpp"
#include "forge/search_types.hpp"

#include <algorithm>
#include <cstdlib>

// UCI CorrExt: correction-history extensions (test plan G-C5).
//
// The correction history (src/search/evaluation.inc) learns how far search
// results have differed from the static evaluation for this pawn structure and
// material; the size of the correction applied at a node,
//     |correction| = |ss->static_eval - ss->raw_eval|   (centipawns),
// says how little the static evaluation can be trusted there. With CorrExt on,
// the main search (the second instance of src/search/alphabeta.inc,
// Worker::search_corr_ext) extends singular moves more at such nodes:
//   - the double-extension margin (AL1 s198: 24 cp below the singular beta)
//     shrinks with |correction|;
//   - a triple extension is added for nodes with a large correction whose TT
//     move is singular by a wide margin;
// and every extension beyond one ply is paid from a per-path budget.
//
// Per-path budget. SearchStack::double_extensions counts the extra plies
// (extension - 1 for extensions above 1) granted by double and triple
// extensions on the path to a node. AL1 s198 allows a double extension while
// at most 6 have been granted, so a path holds at most 7 extra plies; CorrExt
// grants an extension of e > 1 only while the count plus e - 1 stays within
// tune::CorrExtBudget (default 7, the AL1 s198 allowance). With
// |correction| = 0 (or every CorrExt weight 0) the rule is the AL1 s198 rule.
namespace forge::corr_ext {

// |correction| at a node; 0 when the node is in check (no static evaluation).
// (The same measure as UCI CorrMargins, branch opus-O5.)
[[nodiscard]] inline int correction_size(bool in_check, int static_eval, int raw_eval) {
    if (in_check || static_eval == ValueNone || raw_eval == ValueNone) return 0;
    return std::abs(static_eval - raw_eval);
}

// Distance below the singular beta that earns a double extension.
// AL1 s198: 24; minus CorrExtDoublePct percent of |correction|, at least 0.
[[nodiscard]] inline int double_margin(int correction) {
    return std::max(0, 24 - correction * tune::CorrExtDoublePct / 100);
}

// Whether a triple extension is possible at this node: CorrExtTripleCorr > 0
// and |correction| >= CorrExtTripleCorr.
[[nodiscard]] inline bool triple_allowed(int correction) {
    return tune::CorrExtTripleCorr > 0 && correction >= tune::CorrExtTripleCorr;
}

// Extension of a singular TT move (singular_score < singular_beta) at a node
// whose path already holds `path_extra` extra plies: 1, 2 (double) or 3
// (triple). PV nodes get 1, as in AL1 s198.
[[nodiscard]] inline int singular_extension(bool pv_node, int singular_score, int singular_beta, int correction,
                                            int path_extra) {
    if (pv_node) return 1;
    const int room = tune::CorrExtBudget - path_extra;  // extra plies still allowed on this path
    if (room >= 2 && triple_allowed(correction) && singular_score < singular_beta - tune::CorrExtTripleMargin) return 3;
    if (room >= 1 && singular_score < singular_beta - double_margin(correction)) return 2;
    return 1;
}

// Extra plies on the path after a move searched with `extension`.
// AL1 s198: path_extra + (extension == 2).
[[nodiscard]] inline int path_extra_after(int path_extra, int extension) {
    return path_extra + std::max(0, extension - 1);
}

} // namespace forge::corr_ext
