// Where 07-F2 went wrong, and the corrected bound.
// 07-F2 enumerated ONE correction table and concluded correction_cp is bounded to +-32 cp, so
// correction_cp/64 is always 0. But corrected_eval (src/search.cpp:1217-1226) builds `correction`
// as a SUM:  pawn table  +  material table (when MaterialCorrectionWeight > 0)  +  optionally
// (np_w + np_b)/2 when NonPawnCorrection is on. Each table is clamped to +-CorrectionLimit, so the
// sum is what matters, and it crosses the 64 cp threshold that produces delta = 1.
#include <cstdio>
constexpr int Grain = 256;
constexpr int Limit = 32 * Grain;      // per table, in table units = 32 cp
constexpr int TableCp() { return Limit / Grain; }   // 32 cp per table

int apply(int r, int cp) {
    int delta = cp / 64;
    if (delta > 1) delta = 1;
    if (delta < -1) delta = -1;
    const int adjusted = r - delta;
    return adjusted > 0 ? adjusted : 0;
}

int main() {
    const int per = TableCp();
    std::printf("per-table cap: %d cp\n", per);
    std::printf("default tables summed (pawn + material): %d cp\n", 2 * per);
    std::printf("with NonPawnCorrection (pawn + material + avg of 2 nonpawn): %d cp\n", 3 * per);
    int changes = 0, total = 0;
    for (int cp = -3 * per; cp <= 3 * per; ++cp) {
        for (int r = 0; r <= 30; ++r) {
            ++total;
            if (apply(r, cp) != r) ++changes;
        }
    }
    std::printf("reachable (reduction, correction_cp) pairs where the reduction CHANGES: %d of %d\n",
                changes, total);
    std::printf("=> the option is NOT inert; it is inert only on trees where the tables do not\n"
                "   saturate in the same direction (REPORT_r3_03.md line 87 says exactly this).\n");
    return 0;
}
