#pragma once

#include "forge/search_types.hpp"

// SingularV2 port of this repository's FB2-J3 search rules. These helpers are
// used only by the default-off option; the original OFF decisions stay in place.
// Unlike CorrExt's extra-ply budget, J3 counts each double/triple extension as
// one event. The two options are therefore exclusive in UCI and the snapshot.
namespace forge::singular_v2 {

// Called only after the excluded-move search failed below singular_beta.
[[nodiscard]] constexpr int positive_extension(bool pv, bool tt_capture, int score, int singular_beta,
                                               int prior_events) {
    if (!pv && !tt_capture && prior_events <= 4 && score < singular_beta - 80) return 3;
    if (pv) return prior_events <= 3 && score < singular_beta - 60 ? 2 : 1;
    return prior_events <= 6 && score < singular_beta - 24 ? 2 : 1;
}

// Reached only after the existing singular_beta >= beta cutoff has been tested.
[[nodiscard]] constexpr bool multicut(int excluded_score, int beta) {
    return excluded_score >= beta && !is_mate_score(excluded_score);
}

[[nodiscard]] constexpr int negative_extension(bool pv, bool tt_fails_high, bool cut_node) {
    if (tt_fails_high) return pv ? -2 : -3;
    return cut_node ? -2 : 0;
}

[[nodiscard]] constexpr int events_after(int prior_events, int extension) {
    return prior_events + (extension >= 2 ? 1 : 0);
}

} // namespace forge::singular_v2
