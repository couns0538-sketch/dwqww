// tm_probe.cpp -- exhaustive checks of the time manager's pure functions.
//
// include/forge/tm_finish.hpp   iteration_will_not_finish(prev_ms, last_ms, remaining_ms)
// include/forge/tm_node_share.hpp decide_node_share_timing(...), effort_share_factor(...)
// include/forge/clock_plan.hpp  plan_clock_budget(...)
//
// These are pure and total, so every stated property can be checked directly rather than inferred
// from a search. Each check prints its own line, and the program exits non-zero if any fails.
//
// Properties checked (each a property the header COMMENTS claim):
//   tm_finish
//     F1 remaining <= 0 -> true (a spent budget cannot hold another iteration)
//     F2 prev <= 0 or last <= 0 -> false (not a measurement)
//     F3 monotonic in remaining: if it will not finish with R, it will not finish with R' < R
//     F4 no overflow / UB for extreme inputs (this is where UBSan would fire)
//   node share
//     N1 soft <= 0 -> unchanged and not reached
//     N2 result is at least 1 ms when soft > 0
//     N3 result never exceeds hard when hard > 0
//     N4 0% share lengthens, 100% share shortens, 50% leaves it alone (the documented scale)
//   clock plan
//     P1 time <= overhead -> reserve_empty, soft == hard == 0
//     P2 otherwise 1 <= soft <= hard <= available
//     P3 extreme clocks do not overflow
#include "forge/clock_plan.hpp"
#include "forge/tm_finish.hpp"
#include "forge/tm_node_share.hpp"

#include <cstdint>
#include <cstdio>
#include <limits>
#include <string>

namespace {
int failures = 0;
void check(bool cond, const std::string& what) {
    if (cond) return;
    std::printf("FAIL %s\n", what.c_str());
    ++failures;
}
}  // namespace

int main() {
    using forge::iteration_will_not_finish;
    using forge::decide_node_share_timing;
    using forge::effort_share_factor;
    using forge::plan_clock_budget;
    using forge::NodeShareTiming;

    // ---------- tm_finish ----------
    check(iteration_will_not_finish(10, 20, 0), "F1 remaining 0 must say it will not finish");
    check(iteration_will_not_finish(10, 20, -5), "F1 negative remaining must say it will not finish");
    check(!iteration_will_not_finish(0, 20, 1000), "F2 prev 0 is not a measurement -> false");
    check(!iteration_will_not_finish(10, 0, 1000), "F2 last 0 is not a measurement -> false");
    check(!iteration_will_not_finish(-3, 20, 1000), "F2 negative prev -> false");

    // F3 monotonicity + F4 extremes over a grid
    long f3_checked = 0, f4_checked = 0;
    const long long grid[] = {1, 2, 7, 16, 38, 84, 200, 1000, 100000, 1000000};
    for (long long prev : grid) {
        for (long long last : grid) {
            for (long long rem : grid) {
                const bool a = iteration_will_not_finish(prev, last, rem - 1);
                const bool b = iteration_will_not_finish(prev, last, rem);
                // if it will not finish with a larger budget, it must not finish with a smaller one
                check(!(b && !a), "F3 monotonicity violated at prev " + std::to_string(prev) +
                                      " last " + std::to_string(last) + " rem " + std::to_string(rem));
                ++f3_checked;
            }
        }
    }
    const std::int64_t imax = std::numeric_limits<std::int64_t>::max();
    for (std::int64_t v : {imax, imax - 1, imax / 2, static_cast<std::int64_t>(1) << 62}) {
        (void)iteration_will_not_finish(v, v, v);
        (void)iteration_will_not_finish(v, 1, v);
        (void)iteration_will_not_finish(1, v, v);
        f4_checked += 3;
    }
    std::printf("tm_finish: monotonicity checked %ld, extreme inputs %ld\n", f3_checked, f4_checked);

    // ---------- node share ----------
    {
        NodeShareTiming in{0, 100, 50, 10, 100};
        const auto d = decide_node_share_timing(in);
        check(d.soft_ms == 0, "N1 soft 0 must stay 0");
        check(!d.reached, "N1 soft 0 must not count as reached");
    }
    {
        NodeShareTiming in{-5, 100, 50, 10, 100};
        const auto d = decide_node_share_timing(in);
        check(d.soft_ms == -5 && !d.reached, "N1 negative soft unchanged and not reached");
    }
    long n_checked = 0;
    for (std::int64_t soft : {1LL, 2LL, 3LL, 50LL, 179LL, 1000LL, 100000LL}) {
        for (std::uint64_t best : {0ULL, 1ULL, 50ULL, 100ULL, 1000ULL}) {
            for (std::uint64_t root : {0ULL, 1ULL, 100ULL, 1000ULL}) {
                for (std::int64_t hard : {0LL, 100LL, 431LL, 100000LL}) {
                    const auto d = decide_node_share_timing(NodeShareTiming{soft, hard, 10, best, root});
                    check(d.soft_ms >= 1, "N2 result below 1 ms (soft>0)");
                    if (hard > 0) {
                        check(d.soft_ms <= hard, "N3 result above hard limit");
                    }
                    ++n_checked;
                }
            }
        }
    }
    std::printf("node share: %ld grid cases checked for N2/N3\n", n_checked);
    {
        // N4: the documented linear scale, on a share of exactly 0 / 500 / 1000 thousandths.
        const auto low = decide_node_share_timing(NodeShareTiming{1000, 0, 0, 0, 1000});
        const auto mid = decide_node_share_timing(NodeShareTiming{1000, 0, 0, 500, 1000});
        const auto high = decide_node_share_timing(NodeShareTiming{1000, 0, 0, 1000, 1000});
        check(low.soft_ms == 1500, "N4 0% share must give 3/2 of soft, got " + std::to_string(low.soft_ms));
        check(mid.soft_ms == 1000, "N4 50% share must leave soft alone, got " + std::to_string(mid.soft_ms));
        check(high.soft_ms == 500, "N4 100% share must give 1/2 of soft, got " + std::to_string(high.soft_ms));
        std::printf("node share scale: 0%% -> %lld, 50%% -> %lld, 100%% -> %lld (want 1500/1000/500)\n",
                    static_cast<long long>(low.soft_ms), static_cast<long long>(mid.soft_ms),
                    static_cast<long long>(high.soft_ms));
        // effort_share_factor must be exactly 1 when node share is on (so the share is not counted twice)
        check(effort_share_factor(0.0, 155, true) == 1.0, "effort factor must be 1 with node share on");
        check(effort_share_factor(1.0, 155, true) == 1.0, "effort factor must be 1 with node share on (share 1)");
    }

    // ---------- clock plan ----------
    {
        const auto p = plan_clock_budget(5, 0, 0, 10, 22, 75, 60, 5);
        check(p.reserve_empty, "P1 time <= overhead must reserve empty");
        check(p.soft_ms == 0 && p.hard_ms == 0, "P1 empty reserve must have zero limits");
    }
    {
        const auto p = plan_clock_budget(10, 0, 0, 10, 22, 75, 60, 5);
        check(p.reserve_empty, "P1 time == overhead must reserve empty");
    }
    long p_checked = 0, p_clamped = 0;
    for (std::int64_t time : {11LL, 50LL, 100LL, 1000LL, 10000LL, 100000LL}) {
        for (std::int64_t inc : {0LL, 10LL, 100LL, 1000LL}) {
            for (std::int64_t mtg : {0LL, 1LL, 2LL, 40LL, 49LL, 50LL, 1000LL}) {
                for (std::int64_t oh : {0LL, 10LL, 100LL}) {
                    const auto p = plan_clock_budget(time, inc, mtg, oh, 22, 75, 60, 5);
                    if (time <= oh) {
                        check(p.reserve_empty, "P1 reserve_empty missed");
                        continue;
                    }
                    const std::int64_t available = time - oh;
                    check(!p.reserve_empty, "P2 reserve_empty set with time > overhead");
                    check(p.soft_ms >= 1, "P2 soft below 1");
                    check(p.soft_ms <= p.hard_ms, "P2 soft > hard");
                    check(p.hard_ms <= available, "P2 hard > available");
                    if (p.soft_ms != p.hard_ms || p.hard_ms != available) ++p_clamped;
                    ++p_checked;
                }
            }
        }
    }
    std::printf("clock plan: %ld cases satisfied 1 <= soft <= hard <= available\n", p_checked);
    {
        // P3: the parse ceiling must not overflow available*4 or available*hard_percent/100
        const std::int64_t kMaxClockMs = std::numeric_limits<std::int64_t>::max() / 256;
        const auto p = plan_clock_budget(kMaxClockMs, kMaxClockMs, 3, 0, 22, 75, 60, 5);
        check(p.hard_ms >= p.soft_ms && p.hard_ms > 0, "P3 extreme clock produced nonsensical limits");
        std::printf("clock plan at the parse ceiling %lld: soft %lld hard %lld\n",
                    static_cast<long long>(kMaxClockMs), static_cast<long long>(p.soft_ms),
                    static_cast<long long>(p.hard_ms));
    }

    std::printf("\n%s (%d failure(s))\n",
                failures == 0 ? "ALL TIME-MANAGER PROPERTIES HELD" : "PROPERTIES VIOLATED",
                failures);
    return failures == 0 ? 0 : 1;
}
