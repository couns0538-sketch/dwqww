// B2: the allocation invariant and its iteration-level scaled deadline.
// IDEA_SOURCE: user's soft <= hard invariant and this repository's time manager.
#include "forge/search.hpp"
#include "forge/search_options.hpp"
#include "search/timeman.hpp"
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>

using namespace forge;
#if !defined(ASTRA2_TM_PRE_FIX) && !defined(ASTRA2_TM_HEADER_ONLY)
namespace forge {
struct SearcherTestProbe {
    static std::int64_t soft(const Worker& worker) { return worker.soft_limit_ms_; }
    static std::int64_t hard(const Worker& worker) { return worker.hard_limit_ms_; }
};
}
#endif
namespace {
int checks = 0, failures = 0;
void check(bool ok, const std::string& label) {
    ++checks;
    if (!ok) { ++failures; if (failures <= 30) std::cout << "FAIL " << label << '\n'; }
}
struct Budget { std::int64_t soft, hard; bool managed; };
Budget budget(SearchLimits limits, bool enabled) {
#ifndef ASTRA2_TM_PRE_FIX
    limits.fb2.tm_soft_hard_clamp = enabled;
#else
    (void)enabled; // Before the fix: invoke the unchanged production allocator.
#endif
    Budget b{-7, -7, true};
    timeman::allocate(limits, b.soft, b.hard, b.managed);
    return b;
}
std::int64_t scaled(std::int64_t soft, std::int64_t hard, double factor, bool enabled) {
#ifdef ASTRA2_TM_PRE_FIX
    (void)hard; (void)enabled;
    // Exact pre-fix iteration deadline expression from src/search/iterative.inc.
    return static_cast<std::int64_t>(static_cast<double>(soft) * factor);
#else
    return timeman::scaled_soft_limit(soft, hard, factor, enabled);
#endif
}
}
int main() {
    const auto maximum = std::numeric_limits<int>::max();
    for (const bool ponder : {false, true}) {
        for (const int mtg : {0, 1, 2, 40, 50, 80}) {
            for (const int time : {0, 1, 9, 10, 11, 100, 1000, 60000, maximum}) {
                for (const int increment : {0, 1, 100, 10000, maximum}) {
                    for (const int overhead : {0, 10, 1000}) {
                        SearchLimits limits;
                        limits.time_ms = time; limits.increment_ms = increment;
                        limits.move_overhead_ms = overhead; limits.moves_to_go = mtg; limits.ponder = ponder;
                        const auto off = budget(limits, false), on = budget(limits, true);
                        const auto available = std::max<std::int64_t>(1, static_cast<std::int64_t>(time) - overhead);
                        check(on.managed && on.soft >= 1 && on.soft <= on.hard && on.hard <= available,
                              "clock soft<=hard: time=" + std::to_string(time) + " inc=" + std::to_string(increment) +
                              " mtg=" + std::to_string(mtg) + " overhead=" + std::to_string(overhead) +
                              " ponder=" + std::to_string(ponder));
                        check(on.hard == off.hard && on.soft == std::min(off.soft, off.hard), "only soft is capped");
                        for (const double factor : {0.45, 0.8, 1.0, 1.4, 4.9, 29.4}) {
                            const auto old = static_cast<std::int64_t>(static_cast<double>(off.soft) * factor);
                            check(scaled(off.soft, off.hard, factor, false) == old, "OFF scaled expression preserved");
                            const auto actual = scaled(on.soft, on.hard, factor, true);
                            check(actual >= 0 && actual <= on.hard, "ON scaled soft<=hard");
                            check(actual == std::min(static_cast<std::int64_t>(static_cast<double>(on.soft) * factor), on.hard),
                                  "ON deadline clips exactly at hard");
                        }
                    }
                }
            }
        }
    }
    for (const bool ponder : {false, true}) {
        SearchLimits large_inc;
        large_inc.time_ms = 100; large_inc.increment_ms = 10000; large_inc.ponder = ponder;
        auto off = budget(large_inc, false), on = budget(large_inc, true);
        check(off.soft == 90 && off.hard == 54, "RED trigger preserved OFF: 90/54");
        check(on.soft == 54 && on.hard == 54, "large increment capped ON: 54/54");
        std::cout << "inc>>time ponder=" << ponder << " OFF=" << off.soft << '/' << off.hard
                  << " ON=" << on.soft << '/' << on.hard << '\n';
        large_inc.moves_to_go = 1;
        off = budget(large_inc, false); on = budget(large_inc, true);
        check(off.soft == 90 && off.hard == 72 && on.soft == 72 && on.hard == 72, "movestogo=1 cap: 90/72 -> 72/72");
    }
    for (const int movetime : {0, 1, 10, 100, maximum}) {
        SearchLimits limits;
        limits.movetime_ms = movetime; limits.time_ms = 1000; limits.increment_ms = maximum;
        for (const bool enabled : {false, true}) {
            const auto b = budget(limits, enabled);
            check(!b.managed && b.soft == b.hard && b.hard == std::max(1, movetime - 10), "movetime unchanged");
        }
    }
    for (const bool infinite : {false, true}) {
        SearchLimits limits;
        limits.infinite = infinite;
        if (infinite) limits.time_ms = 100;
        for (const bool enabled : {false, true}) {
            const auto b = budget(limits, enabled);
            check(b.soft == 0 && b.hard == 0 && !b.managed, "unmanaged search unchanged");
            check(scaled(b.soft, b.hard, 1.4, enabled) == 0, "unmanaged scaled deadline remains zero");
        }
    }
#if !defined(ASTRA2_TM_PRE_FIX) && !defined(ASTRA2_TM_HEADER_ONLY)
    {
        SharedSearchState shared(16);
        Worker worker(shared, 0);
        Board board;
        SearchLimits limits;
        limits.time_ms = 100; limits.increment_ms = 10000;
        limits.nodes_specified = true; limits.nodes = 0; // allocation is exercised before the zero-node return
        for (const bool enabled : {false, true}) {
            limits.fb2.tm_soft_hard_clamp = enabled;
            (void)worker.search(board, limits, false, {});
            check(SearcherTestProbe::soft(worker) == (enabled ? 54 : 90) && SearcherTestProbe::hard(worker) == 54,
                  "actual Worker allocation uses the frozen mode");
            worker.end_search();
        }
    }
    check(!fb2::requested.tm_soft_hard_clamp, "option defaults OFF");
    fb2::requested.tm_soft_hard_clamp = true;
    const auto snapshot = fb2::effective(fb2::requested, 0);
    fb2::requested.tm_soft_hard_clamp = false;
    check(snapshot.tm_soft_hard_clamp, "per-search snapshot survives later requested value");
    fb2::requested.tm_soft_hard_clamp = true;
    for (const auto preset : {fb2::Bundle::B1, fb2::Bundle::B2, fb2::Bundle::B3, fb2::Bundle::B4, fb2::Bundle::Off}) {
        fb2::apply_bundle(preset);
        check(fb2::requested.tm_soft_hard_clamp, "preset preserves independent clamp option");
    }
    fb2::requested.tm_soft_hard_clamp = false;
#endif
    std::cout << "tm_softhard: checks=" << checks << " failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
