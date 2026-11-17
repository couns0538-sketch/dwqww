// Exact readout of the clock plan, computed by the engine's own header.
//
// Why a compiled harness rather than the Python mirror: the mirror can only
// reproduce what I believe parse_limits does. This links the real
// clock_plan.hpp and applies the real parse_limits transform, so a disagreement
// between the two is a finding rather than a rounding note.
//
// Build:
//   LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 /usr/bin/g++ -std=c++20 -O2 \
//     -I<forge>/include plan_table.cpp -o plan_table
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include <forge/clock_plan.hpp>

// Mirror of the transforms parse_limits applies before the planner sees a value.
// base 6b98f217, src/uci.cpp:117:  limits.moves_to_go = std::max(1, read_int());
static int parse_movestogo(int raw) { return raw > 1 ? raw : 1; }

struct Row {
    const char* label;
    std::int64_t time_ms;
    std::int64_t inc_ms;
    int raw_mtg;      // the token a GUI would send; 0 here means "no movestogo"
    bool mtg_given;
};

int main(int argc, char** argv) {
    const std::int64_t overhead = argc > 1 ? std::atoll(argv[1]) : 10;
    // Defaults are the engine's own (search.cpp:79-82).
    const int soft_divisor = 22, inc_pct = 75, hard_pct = 60, hard_mult = 5;

    std::vector<Row> rows;
    for (int raw : {0, 1, -1, 2, 20, 49, 50, 51, 100}) {
        rows.push_back({"mtg_given", 2000, 0, raw, true});
    }
    rows.push_back({"mtg_absent", 2000, 0, 0, false});
    // Same shapes at a clock where the increment dominates the divisor term.
    rows.push_back({"mtg_given", 200, 100, 0, true});
    rows.push_back({"mtg_given", 200, 100, 20, true});
    rows.push_back({"mtg_absent", 200, 100, 0, false});
    // The floor: clock below the overhead.
    rows.push_back({"mtg_given", 5, 0, 20, true});
    rows.push_back({"mtg_given", 111, 0, 20, true});
    rows.push_back({"mtg_given", 111, 0, -1, true});

    std::printf("overhead=%lld  soft_div=%d inc_pct=%d hard_pct=%d hard_mult=%d\n",
                static_cast<long long>(overhead), soft_divisor, inc_pct, hard_pct, hard_mult);
    std::printf("%-10s %8s %6s %6s %6s %8s %8s %s\n",
                "label", "time", "inc", "token", "parsed", "soft", "hard", "reserve_empty");
    for (const Row& r : rows) {
        const int parsed = r.mtg_given ? parse_movestogo(r.raw_mtg) : 0;
        const forge::ClockPlan p = forge::plan_clock_budget(
            r.time_ms, r.inc_ms, parsed, overhead, soft_divisor, inc_pct, hard_pct, hard_mult);
        std::printf("%-10s %8lld %6lld %6d %6d %8lld %8lld %s\n", r.label,
                    static_cast<long long>(r.time_ms), static_cast<long long>(r.inc_ms),
                    r.mtg_given ? r.raw_mtg : 0, parsed,
                    static_cast<long long>(p.soft_ms), static_cast<long long>(p.hard_ms),
                    p.reserve_empty ? "yes" : "no");
    }
    return 0;
}
