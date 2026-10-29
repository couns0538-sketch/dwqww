#pragma once
// FB2-J4 time management v2 (UCI option TimeManV2, default off). Pure functions, shared by the engine
// (Worker::search / should_stop) and by the flag-loss simulator (tools/timeman_sim.cpp), so the simulation
// exercises exactly the decision code that runs in games.
#include <algorithm>
#include <cstdint>

namespace forge::timeman {

struct Budget {
    std::int64_t soft_ms = 0;   // planned thinking time
    std::int64_t hard_ms = 0;   // never exceeded (plus one check interval); already net of the move overhead
    bool managed = false;       // clock-driven search
};

struct Allocation {
    int soft_divisor = 20;      // tune::TmSoftDivisor
    int increment_percent = 75; // tune::TmIncrementPercent
    int hard_percent = 50;      // tune::TmHardPercent
    int hard_soft_multiple = 4; // tune::TmHardSoftMultiple
};

// The lock's clock allocation (the same formula as Worker::search), as a pure function.
inline Budget allocate(std::int64_t time_ms, std::int64_t increment_ms, int moves_to_go, int overhead_ms, const Allocation& a) {
    Budget b;
    if (time_ms < 0) return b;
    const std::int64_t overhead = std::max<std::int64_t>(0, overhead_ms);
    const std::int64_t increment = std::max<std::int64_t>(0, increment_ms);
    const std::int64_t available = std::max<std::int64_t>(1, time_ms - overhead);
    std::int64_t soft;
    std::int64_t hard;
    if (moves_to_go > 0) {
        const std::int64_t mtg = std::min<std::int64_t>(moves_to_go, 50);
        soft = available / (mtg + 1) + increment * 3 / 4;
        hard = std::min(available * 4 / 5, soft * 4);
    } else {
        soft = available / a.soft_divisor + increment * a.increment_percent / 100;
        hard = std::min(available * a.hard_percent / 100, soft * a.hard_soft_multiple);
    }
    b.soft_ms = std::max<std::int64_t>(1, std::min(soft, available));
    b.hard_ms = std::max<std::int64_t>(1, std::min(hard, available));
    b.managed = true;
    return b;
}

struct Scaling {
    int stable_factor = 50;      // tune::TmStableFactor (percent), >= 6 stable iterations
    int semi_stable_factor = 75; // tune::TmSemiStableFactor, >= 3
    int unstable_factor = 150;   // tune::TmUnstableFactor, best move just changed (depth >= 6)
    int effort_base = 130;       // tune::TmEffortBase: factor *= clamp(base/100 - effort, 0.6, 1.4)
    int falling_eval_percent = 100; // tune::TmFallingEvalPercent per cp of drop (x 1e-4)
    int min_factor_percent = 30; // tune::TmMinFactorPercent
    // v2 additions
    int next_iteration_fraction = 50; // stop when the predicted next iteration would overshoot: nodes + pred * f% > budget
    int in_search_overshoot = 130;    // nodes may run to budget * this% inside an iteration before the soft stop
    int ebf_min_x100 = 130;           // effective branching factor clamp for the prediction
    int ebf_max_x100 = 300;
};

struct Iteration {
    int depth = 0;
    int score = 0;
    int previous_score = 32002;        // ValueNone when unknown
    bool score_is_mate = false;
    int stable_iterations = 0;         // consecutive iterations with the same best move
    std::uint64_t nodes_total = 0;     // all nodes so far (this search)
    std::uint64_t nodes_iteration = 0; // nodes of the iteration that just finished
    std::uint64_t nodes_previous_iteration = 0;
    std::uint64_t best_move_nodes = 0; // nodes spent under the best move (effort)
    std::int64_t elapsed_ms = 0;
};

struct Decision {
    bool stop = false;
    double factor = 1.0;
    std::uint64_t node_budget = 0;     // soft budget in nodes at the measured speed
    std::uint64_t soft_node_limit = 0; // in-search soft stop (budget * overshoot)
    std::uint64_t predicted_next = 0;  // predicted nodes of the next iteration
    double nps = 0.0;                  // nodes per millisecond
};

// The scaling factor shared by the lock's rule (v1) and v2.
inline double scale_factor(const Scaling& s, const Iteration& it) {
    double factor = 1.0;
    if (it.stable_iterations >= 6) factor = s.stable_factor / 100.0;
    else if (it.stable_iterations >= 3) factor = s.semi_stable_factor / 100.0;
    else if (it.stable_iterations == 0 && it.depth >= 6) factor = s.unstable_factor / 100.0;
    if (it.nodes_total > 0 && it.depth >= 6) {
        const double effort = static_cast<double>(it.best_move_nodes) / static_cast<double>(it.nodes_total);
        factor *= std::clamp(s.effort_base / 100.0 - effort, 0.6, 1.4);
    }
    if (it.previous_score != 32002 && !it.score_is_mate && it.score < it.previous_score) {
        const int drop = std::min(it.previous_score - it.score, 150);
        factor *= 1.0 + drop * s.falling_eval_percent / 10000.0;
    }
    return std::max(factor, s.min_factor_percent / 100.0);
}

// v1 (the lock): stop at an iteration boundary once elapsed >= soft * factor.
inline bool decide_v1(const Budget& b, const Scaling& s, const Iteration& it) {
    if (!b.managed) return false;
    const double factor = scale_factor(s, it);
    return it.elapsed_ms >= static_cast<std::int64_t>(static_cast<double>(b.soft_ms) * factor);
}

// v2: the soft budget is expressed in nodes at the speed measured so far; stop at an iteration boundary when
// the budget is spent or when the predicted next iteration would overshoot it; inside the iteration a soft node
// limit (budget * overshoot) stops the search early (the partial iteration's result is used when it raised alpha).
inline Decision decide_v2(const Budget& b, const Scaling& s, const Iteration& it) {
    Decision d;
    if (!b.managed) return d;
    d.factor = scale_factor(s, it);
    const double elapsed = static_cast<double>(std::max<std::int64_t>(it.elapsed_ms, 1));
    d.nps = static_cast<double>(it.nodes_total) / elapsed;
    if (it.elapsed_ms < 5 || it.nodes_total < 2000) {
        // Too early to trust the speed estimate: fall back to the time rule.
        d.stop = it.elapsed_ms >= static_cast<std::int64_t>(static_cast<double>(b.soft_ms) * d.factor);
        return d;
    }
    const double budget = static_cast<double>(b.soft_ms) * d.factor * d.nps;
    d.node_budget = static_cast<std::uint64_t>(budget);
    d.soft_node_limit = static_cast<std::uint64_t>(budget * s.in_search_overshoot / 100.0);
    double ebf = 2.0;
    if (it.nodes_previous_iteration > 0 && it.nodes_iteration > 0) {
        ebf = static_cast<double>(it.nodes_iteration) / static_cast<double>(it.nodes_previous_iteration);
    }
    ebf = std::clamp(ebf, s.ebf_min_x100 / 100.0, s.ebf_max_x100 / 100.0);
    d.predicted_next = static_cast<std::uint64_t>(static_cast<double>(it.nodes_iteration) * ebf);
    if (static_cast<double>(it.nodes_total) >= budget) d.stop = true;
    else if (it.depth >= 6 && static_cast<double>(it.nodes_total) + static_cast<double>(d.predicted_next) * s.next_iteration_fraction / 100.0 > budget) d.stop = true;
    return d;
}

// Hard-deadline check interval (nodes between clock reads) for v2: close to the deadline the clock is read more
// often, so the search returns at most one interval after hard_ms. Returns a power-of-two mask.
inline std::uint64_t check_mask(double nodes_per_ms, std::int64_t remaining_ms) {
    if (nodes_per_ms <= 0.0) return 1023;
    const double nodes = nodes_per_ms * static_cast<double>(std::max<std::int64_t>(remaining_ms, 1)) / 4.0;
    std::uint64_t mask = 1023;
    while (mask > 63 && static_cast<double>(mask + 1) > nodes) mask >>= 1U;
    return mask;
}

} // namespace forge::timeman
