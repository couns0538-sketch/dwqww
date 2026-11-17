// Unit-level truth table for TTEntry::score_usable().
// Compiles against the shipped header only; no engine sources are linked because
// the function and its helpers are header-inline / constexpr.
//
// usage: score_usable_table <out.json>
#include "forge/search.hpp"

#include <cstdio>
#include <string>
#include <vector>

namespace {

struct Row {
    int stored_clock;   // what went into entry.rule50_clock
    int depth;          // entry.depth
    int score;          // entry.score (TT form: score_to_tt already applied)
    int current;        // the board's halfmove clock at probe time
    bool usable;
    const char* branch;
};

// The four-branch decomposition, expressed independently of the code under
// test, so a mismatch is evidence rather than a restatement.
const char* branch_of(int stored, int depth, int score, int current) {
    const int capped = current < 100 ? current : 100;
    if (stored == capped) return "A:exact-clock";
    const bool mate = score >= forge::MateInMaxPly || score <= -forge::MateInMaxPly;
    if (mate) {
        const int mag = score < 0 ? -score : score;
        const int distance = forge::MateValue - mag;
        if (current + distance > 100) return "B:mate-too-long";
    }
    const bool inside = stored + depth < 100 && current + depth < 100 && stored < 90 && capped < 90;
    return inside ? "C:inside-horizon" : "D:outside-horizon";
}

void emit(std::vector<Row>& rows, int stored, int depth, int score, int current) {
    forge::TTEntry e{};
    e.rule50_clock = static_cast<std::uint8_t>(stored);
    e.depth = static_cast<std::uint8_t>(depth);
    e.score = static_cast<std::int16_t>(score);
    e.gen_bound = 1;  // bound != BoundNone so the entry counts as occupied
    rows.push_back({stored, depth, score, current, e.score_usable(static_cast<std::uint16_t>(current)),
                    branch_of(stored, depth, score, current)});
}

}  // namespace

int main(int argc, char** argv) {
    const std::string out = argc > 1 ? argv[1] : "-";
    std::vector<Row> rows;

    // --- Branch A: exact clock match, every clock value 0..100.
    for (int c = 0; c <= 100; ++c) emit(rows, c, 0, 120, c);
    // Exact match at >=100: 100 and 120 both cap to 100.
    emit(rows, 100, 0, 120, 100);
    emit(rows, 100, 0, 120, 120);   // current 120 caps to 100 -> exact
    emit(rows, 99, 0, 120, 120);    // stored 99, capped 100 -> not exact

    // --- Branch B: mate score whose distance cannot fit in the remaining clock.
    // 90 + 15 > 100 with clocks differing.
    emit(rows, 90, 4, forge::MateValue - 15, 95);
    emit(rows, 90, 4, forge::MateValue - 15, 91);
    emit(rows, 90, 4, forge::MateValue - 15, 85);   // 85 + 15 = 100, not > 100
    emit(rows, 90, 4, forge::MateValue - 15, 86);   // 86 + 15 = 101 > 100 -> reject
    // Same mate entry probed at the clock it was stored with: 90 + 15 > 100.
    emit(rows, 90, 4, forge::MateValue - 15, 90);
    // Losing side of the same mate.
    emit(rows, 90, 4, -(forge::MateValue - 15), 91);
    emit(rows, 80, 4, forge::MateValue - 15, 90);   // 90+15>100, clocks differ
    emit(rows, 80, 4, forge::MateValue - 15, 80);   // exact match, 80+15<=100
    emit(rows, 99, 2, forge::MateValue - 3, 100);   // 100+3>100 reject

    // --- Branch C: inside horizon, clocks differ, both < 90.
    emit(rows, 10, 8, 120, 20);
    emit(rows, 10, 8, 120, 89);
    emit(rows, 89, 8, 120, 10);
    emit(rows, 10, 8, 120, 99);     // capped 99 >= 90 -> D
    emit(rows, 10, 90, 120, 20);    // depth 90 pushes past 100 -> D
    emit(rows, 95, 4, 120, 10);     // stored >= 90 -> D

    // --- Branch D: outside horizon, clocks differ.
    emit(rows, 95, 4, 120, 10);
    emit(rows, 10, 4, 120, 95);
    emit(rows, 50, 49, 120, 50);    // 50+49=99 <100 and both<90 -> C
    emit(rows, 50, 50, 120, 50);    // 50+50=100 not <100 -> D

    // --- Exhaustive grid: every stored clock x depth x current, cp and mate.
    for (int stored = 0; stored <= 100; ++stored)
        for (int depth = 0; depth <= 64; ++depth)
            for (int current = 0; current <= 100; ++current)
                emit(rows, stored, depth, 120, current);

    std::FILE* f = out == "-" ? stdout : std::fopen(out.c_str(), "w");
    if (f == nullptr) return 1;
    std::fprintf(f, "{\n  \"rows\": [\n");
    for (std::size_t i = 0; i < rows.size(); ++i) {
        const Row& r = rows[i];
        std::fprintf(f,
                     "    {\"stored\": %d, \"depth\": %d, \"score\": %d, \"current\": %d, "
                     "\"usable\": %s, \"branch\": \"%s\"}%s\n",
                     r.stored_clock, r.depth, r.score, r.current, r.usable ? "true" : "false",
                     r.branch, i + 1 == rows.size() ? "" : ",");
    }
    std::fprintf(f, "  ]\n}\n");
    if (f != stdout) std::fclose(f);
    return 0;
}
