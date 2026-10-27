// Time management (src/search/timeman.hpp) against the AL1 s198 formulas:
// budget allocation for movetime / sudden death / increment / movestogo and
// the iteration-level soft-limit factor (stability -> effort -> falling eval -> floor).
#include "forge/search.hpp"
#include "search/timeman.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

using namespace forge;

namespace {

int failures = 0;
int checks = 0;

void check(bool okay, const std::string& name) {
    ++checks;
    if (!okay) {
        ++failures;
        if (failures <= 50) std::cout << "FAIL " << name << '\n';
    }
}

struct Budget {
    std::int64_t soft_ms = 0;
    std::int64_t hard_ms = 0;
    bool managed = false;
};

Budget allocated(const SearchLimits& limits) {
    Budget b;
    b.soft_ms = b.hard_ms = -7; // must be overwritten
    b.managed = true;
    timeman::allocate(limits, b.soft_ms, b.hard_ms, b.managed);
    return b;
}

Budget reference_budget(const SearchLimits& limits) {
    Budget b;
    const std::int64_t overhead = std::max<std::int64_t>(0, limits.move_overhead_ms);
    if (limits.infinite) return b;
    if (limits.movetime_ms >= 0) {
        b.hard_ms = std::max<std::int64_t>(1, limits.movetime_ms - overhead);
        b.soft_ms = b.hard_ms;
        return b;
    }
    if (limits.time_ms < 0) return b;
    const std::int64_t increment = std::max<std::int64_t>(0, limits.increment_ms);
    const std::int64_t available = std::max<std::int64_t>(1, limits.time_ms - overhead);
    std::int64_t soft, hard;
    if (limits.moves_to_go > 0) {
        const std::int64_t mtg = std::min<std::int64_t>(limits.moves_to_go, 50);
        soft = available / (mtg + 1) + increment * 3 / 4;
        hard = std::min(available * 4 / 5, soft * 4);
    } else {
        soft = available / 22 + increment * 75 / 100;
        hard = std::min(available * 60 / 100, soft * 5);
    }
    b.soft_ms = std::max<std::int64_t>(1, std::min(soft, available));
    b.hard_ms = std::max<std::int64_t>(1, std::min(hard, available));
    b.managed = true;
    return b;
}

// The driver's composition of the time-module pieces (src/search/iterative.inc).
double driver_factor(int stable, int depth, std::uint64_t nodes, bool tracked, std::uint64_t best_nodes, int previous,
                     int score) {
    double factor = timeman::stability_factor(stable, depth);
    if (nodes > 0 && depth >= 6 && tracked) {
        factor *= timeman::effort_scale(static_cast<double>(best_nodes) / static_cast<double>(nodes));
    }
    if (timeman::eval_fell(previous, score)) factor *= timeman::falling_eval_scale(previous, score);
    return timeman::factor_floor(factor);
}

double reference_factor(int stable, int depth, std::uint64_t nodes, bool tracked, std::uint64_t best_nodes, int previous,
                        int score) {
    double factor = 1.0;
    if (stable >= 6) factor = 0.60;
    else if (stable >= 3) factor = 0.80;
    else if (stable == 0 && depth >= 6) factor = 1.40;
    if (nodes > 0 && depth >= 6 && tracked) {
        const double effort = static_cast<double>(best_nodes) / static_cast<double>(nodes);
        factor *= std::clamp(1.55 - effort, 0.6, 1.4);
    }
    if (previous != ValueNone && !is_mate_score(score) && score < previous) {
        factor *= 1.0 + std::min(previous - score, 150) / 100.0;
    }
    return std::max(factor, 0.45);
}

} // namespace

int main() {
    const std::vector<int> times{-1, 0, 1, 9, 10, 11, 50, 999, 1000, 10000, 60000, 3600000};
    const std::vector<int> increments{0, 100, 1000, 5000};
    const std::vector<int> mtgs{0, 1, 2, 40, 50, 80};
    const std::vector<int> overheads{0, 10, 1000};
    int cases = 0;
    for (const int time : times)
        for (const int inc : increments)
            for (const int mtg : mtgs)
                for (const int overhead : overheads) {
                    SearchLimits limits;
                    limits.time_ms = time;
                    limits.increment_ms = inc;
                    limits.moves_to_go = mtg;
                    limits.move_overhead_ms = overhead;
                    const Budget got = allocated(limits);
                    const Budget want = reference_budget(limits);
                    ++cases;
                    check(got.soft_ms == want.soft_ms && got.hard_ms == want.hard_ms && got.managed == want.managed,
                          "clock budget time=" + std::to_string(time) + " inc=" + std::to_string(inc) +
                              " mtg=" + std::to_string(mtg) + " overhead=" + std::to_string(overhead));
                    if (want.managed) check(got.hard_ms >= 1 && got.soft_ms >= 1, "budgets are at least 1 ms");
                }
    for (const int movetime : {0, 1, 5, 10, 11, 100, 1000}) {
        for (const int overhead : {0, 10, 1000}) {
            SearchLimits limits;
            limits.movetime_ms = movetime;
            limits.time_ms = 5000; // movetime takes precedence over the clock
            limits.move_overhead_ms = overhead;
            const Budget got = allocated(limits);
            const Budget want = reference_budget(limits);
            ++cases;
            check(got.soft_ms == want.soft_ms && got.hard_ms == want.hard_ms && !got.managed,
                  "movetime budget " + std::to_string(movetime) + " overhead " + std::to_string(overhead));
        }
    }
    {
        SearchLimits limits;
        limits.infinite = true;
        limits.time_ms = 1000;
        const Budget got = allocated(limits);
        check(got.soft_ms == 0 && got.hard_ms == 0 && !got.managed, "infinite search has no budget");
        SearchLimits depth_only;
        depth_only.depth = 12;
        const Budget none = allocated(depth_only);
        check(none.soft_ms == 0 && none.hard_ms == 0 && !none.managed, "depth search has no budget");
    }

    int factor_cases = 0;
    for (const int stable : {0, 1, 2, 3, 5, 6, 9})
        for (const int depth : {1, 5, 6, 12})
            for (const std::uint64_t nodes : {std::uint64_t{0}, std::uint64_t{1000}, std::uint64_t{123457}})
                for (const bool tracked : {false, true})
                    for (const std::uint64_t best : {std::uint64_t{0}, std::uint64_t{500}, std::uint64_t{999}})
                        for (const int previous : {ValueNone, -50, 0, 120, 400})
                            for (const int score : {-31990, -200, 0, 30, 119, 400}) {
                                const double got = driver_factor(stable, depth, nodes, tracked, best, previous, score);
                                const double want = reference_factor(stable, depth, nodes, tracked, best, previous, score);
                                ++factor_cases;
                                check(got == want, "soft factor stable=" + std::to_string(stable) + " depth=" + std::to_string(depth));
                            }
    std::cout << "time management: budget cases=" << cases << " factor cases=" << factor_cases << " checks=" << checks
              << " failures=" << failures << '\n';
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " timeman_tests\n";
    return failures == 0 ? 0 : 1;
}
