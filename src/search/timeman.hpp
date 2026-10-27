#pragma once

// Search module: time management.
//   allocate()            budgets of one search from the UCI limits;
//   stability_factor(), effort_scale(), eval_fell() / falling_eval_scale(),
//   factor_floor()        the iteration-level soft-stop rule, applied by the
//                         driver (src/search/iterative.inc) in this order.
// The per-node clock checks are Worker::elapsed_ms() and Worker::should_stop()
// in src/search/checks.inc. Header-only and inline: the inlined code is the
// AL1 s198 driver code statement for statement.
// Included by src/search.cpp and by tests/timeman_tests.cpp.

#include "forge/search.hpp"

#include <algorithm>
#include <cstdint>

namespace forge::timeman {

// Soft/hard budgets (ms) and whether the search is clock-managed (only those
// stop early on the soft budget): movetime -> soft = hard = movetime - overhead;
// clock -> from the remaining time, increment and movestogo; infinite, depth,
// nodes and mate searches -> no budget.
inline void allocate(const SearchLimits& limits, std::int64_t& soft_ms, std::int64_t& hard_ms, bool& managed) {
    const std::int64_t overhead = std::max<std::int64_t>(0, limits.move_overhead_ms);
    soft_ms = hard_ms = 0;
    managed = false;
    if (limits.infinite) {
        soft_ms = hard_ms = 0;
    } else if (limits.movetime_ms >= 0) {
        hard_ms = std::max<std::int64_t>(1, limits.movetime_ms - overhead);
        soft_ms = hard_ms;
    } else if (limits.time_ms >= 0) {
        const std::int64_t time = limits.time_ms;
        const std::int64_t increment = std::max<std::int64_t>(0, limits.increment_ms);
        const std::int64_t available = std::max<std::int64_t>(1, time - overhead);
        std::int64_t soft;
        std::int64_t hard;
        if (limits.moves_to_go > 0) {
            const std::int64_t mtg = std::min<std::int64_t>(limits.moves_to_go, 50);
            soft = available / (mtg + 1) + increment * 3 / 4;
            hard = std::min(available * 4 / 5, soft * 4);
        } else {
            soft = available / tune::TmSoftDivisor + increment * tune::TmIncrementPercent / 100;
            hard = std::min(available * tune::TmHardPercent / 100, soft * tune::TmHardSoftMultiple);
        }
        soft_ms = std::max<std::int64_t>(1, std::min(soft, available));
        hard_ms = std::max<std::int64_t>(1, std::min(hard, available));
        managed = true;
    }
}

// Stop early when the best move has been stable; spend longer when it keeps changing.
[[nodiscard]] inline double stability_factor(int stable_iterations, int depth) {
    double factor = 1.0;
    if (stable_iterations >= 6) factor = tune::TmStableFactor / 100.0;
    else if (stable_iterations >= 3) factor = tune::TmSemiStableFactor / 100.0;
    else if (stable_iterations == 0 && depth >= 6) factor = tune::TmUnstableFactor / 100.0;
    return factor;
}

// A best move that absorbed most of the effort (share of the iteration's
// nodes spent below it) is clearly best; spend longer when the alternatives
// still draw attention.
[[nodiscard]] inline double effort_scale(double effort) {
    return std::clamp(tune::TmEffortBase / 100.0 - effort, 0.6, 1.4);
}

// A falling evaluation deserves more thought.
[[nodiscard]] inline bool eval_fell(int previous_score, int score) {
    return previous_score != ValueNone && !is_mate_score(score) && score < previous_score;
}

[[nodiscard]] inline double falling_eval_scale(int previous_score, int score) {
    const int drop = std::min(previous_score - score, 150);
    return 1.0 + drop * tune::TmFallingEvalPercent / 10000.0;
}

[[nodiscard]] inline double factor_floor(double factor) {
    return std::max(factor, tune::TmMinFactorPercent / 100.0);
}

} // namespace forge::timeman
