#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

// Regression test for Fault B: hash-table scores near the 50-move rule.
// Positions where the side ahead cannot make progress within the remaining
// half-moves are searched once with a low clock (filling the TT and worker
// tables), then searched at clocks 96..99 on the same Searcher (warm TT),
// with TT retained and worker histories cleared (tt_only), and on a fresh
// Searcher (empty TT). Warm and empty searches must agree on the 50-move draw.

namespace {

struct Rule50Case {
    const char* label;
    const char* base_fen4;
    int low_clock;
    int warm_depth;
    int high_clock;
    int search_depth;
};

const std::vector<Rule50Case>& test_cases() {
    static const std::vector<Rule50Case> cases = {
        // Clock 96 (4 half-moves to 100):
        {"C96_KQvK_d3",    "8/8/8/3k4/8/8/2Q5/3K4 w - -",       90, 8,  96, 3},
        {"C96_KQvK_d4",    "8/8/8/3k4/8/8/2Q5/3K4 w - -",       0,  8,  96, 4},
        {"C96_KBNvKp_d4",  "8/7p/6k1/8/8/1BN5/1K6/8 w - -",     0,  8,  96, 4},
        {"C96_KBNvKp_d6",  "8/7p/6k1/8/8/1BN5/1K6/8 w - -",     0,  8,  96, 6},
        {"C96_KBBvKp_d5",  "8/5kp1/8/8/8/2BB4/1K6/8 w - -",     0,  8,  96, 5},
        {"C96_KRBvKp_d4",  "8/7p/6k1/8/8/1RB5/1K6/8 w - -",     0,  8,  96, 4},
        {"C96_KRNvKp_d4",  "8/5kp1/8/8/8/1RN5/1K6/8 w - -",     0,  8,  96, 4},

        // Clock 97 (3 half-moves to 100):
        {"C97_KQvKNp_d3",  "8/7p/6k1/5n2/8/8/1KQ5/8 w - -",     0,  8,  97, 3},
        {"C97_KQvKNp_95",  "8/7p/6k1/5n2/8/8/1KQ5/8 w - -",     95, 8,  97, 3},
        {"C97_KQvKNp2_d3", "8/6kp/5n2/8/8/2Q5/1K6/8 w - -",     0,  8,  97, 3},
        {"C97_KBBvKp_d5",  "8/5kp1/8/8/8/2BB4/1K6/8 w - -",     90, 8,  97, 5},
        {"C97_KBNvKp_90d5","8/7p/6k1/8/8/1BN5/1K6/8 w - -",     90, 8,  97, 5},
        {"C97_KRNvP_96d3", "8/1k6/8/p1p1p3/P1P1P3/1K6/8/RN6 w - -", 96, 8, 97, 3},

        // Clock 98 (2 half-moves to 100):
        {"C98_KQNvKNp_d4", "8/7p/5k2/4nN2/8/8/1KQ5/8 w - -",    0,  10, 98, 4},
        {"C98_KQvKNp_d4",  "8/7p/6k1/5n2/8/8/1KQ5/8 w - -",     0,  8,  98, 4},
        {"C98_KRvK_d4",    "8/8/8/3k4/8/8/2R5/3K4 w - -",       0,  8,  98, 4},
        {"C98_KBNvKp_d4",  "8/7p/6k1/8/8/1BN5/1K6/8 w - -",     0,  8,  98, 4},

        // Clock 99 (1 half-move to 100):
        {"C99_KRvK_d4",    "8/8/8/3k4/8/8/2R5/3K4 w - -",       0,  8,  99, 4},
        {"C99_KQvKNp_d4",  "8/7p/6k1/5n2/8/8/1KQ5/8 w - -",     0,  8,  99, 4},
        {"C99_KQNvKNp_d4", "8/7p/5k2/4nN2/8/8/1KQ5/8 w - -",    0,  8,  99, 4},
    };
    return cases;
}

std::string make_fen(std::string_view base4, int clock) {
    return std::string(base4) + " " + std::to_string(clock) + " 50";
}

} // namespace

int main() {
    int failures = 0;

    for (const auto& tc : test_cases()) {
        forge::Board b_low, b_high;
        std::string err;
        if (!b_low.set_fen(make_fen(tc.base_fen4, tc.low_clock), &err) ||
            !b_high.set_fen(make_fen(tc.base_fen4, tc.high_clock), &err)) {
            std::cerr << "INVALID FEN [" << tc.label << "]: " << err << "\n";
            return 2;
        }

        forge::SearchLimits lim_low, lim_high;
        lim_low.depth = tc.warm_depth;
        lim_high.depth = tc.search_depth;

        // 1. Empty table search
        forge::Searcher s_empty(16, 1);
        const forge::SearchInfo r_empty =
            s_empty.search(b_high, lim_high, false, forge::Searcher::TTAccess::Exclusive);

        // 2. Warm table search (same Searcher, TT + worker state retained)
        forge::Searcher s_warm(16, 1);
        const forge::SearchInfo r_low =
            s_warm.search(b_low, lim_low, false, forge::Searcher::TTAccess::Exclusive);
        const forge::SearchInfo r_warm =
            s_warm.search(b_high, lim_high, false, forge::Searcher::TTAccess::Exclusive);

        // 3. Warm TT only (worker histories cleared, TT retained)
        forge::Searcher s_tt(16, 1);
        (void)s_tt.search(b_low, lim_low, false, forge::Searcher::TTAccess::Exclusive);
        s_tt.main_worker().clear();
        const forge::SearchInfo r_tt =
            s_tt.search(b_high, lim_high, false, forge::Searcher::TTAccess::Exclusive);

        const bool ok = (r_empty.score == 0) &&
                        (r_warm.score == r_empty.score) &&
                        (r_tt.score == r_empty.score) &&
                        !r_warm.best_move.is_none() && b_high.is_legal(r_warm.best_move);

        if (!ok) ++failures;

        std::cout << (ok ? "OK   " : "FAIL ") << "[" << tc.label << "]"
                  << " low=" << tc.low_clock << "@d" << tc.warm_depth << "(" << r_low.score << ")"
                  << " high=" << tc.high_clock << "@d" << tc.search_depth
                  << " | empty=" << r_empty.score << "(" << forge::Board::move_to_uci(r_empty.best_move) << ")"
                  << " warm=" << r_warm.score << "(" << forge::Board::move_to_uci(r_warm.best_move) << ")"
                  << " tt_only=" << r_tt.score << "(" << forge::Board::move_to_uci(r_tt.best_move) << ")\n";
    }

    std::cout << "SUMMARY: cases=" << test_cases().size() << " failures=" << failures << "\n";
    return failures == 0 ? 0 : 1;
}
