// Would a stored 0 at clock 100 poison the board? Plant it and ask the real probe.
//
// exp_bail.py shows the drawn-root bail stores nothing, so this hazard does not
// arise from the bail. This harness measures how bad it WOULD be, which is the
// form the assignment's question ("if it DID store a 0 at clock 100, that entry
// would poison every subsequent search") can actually be answered in.
//
// Three plantings on the same key:
//   1. BoundExact score 0 at clock 100      -> what the bail would write
//   2. BoundExact score 0 at clock 90       -> same payload, legal clock
//   3. BoundExact score 120 at clock 100    -> a real score, to show the mechanism
//      is the clock and not the value
//
// For each: does `score_usable` accept it at clock 100? At clock 99? At clock 50?
// A branch-A accept at clock 100 means the entry is reusable by any later search
// of that board at clock 100 (the key does not carry the clock), which is the
// poisoning. Whether such a read can reach the SCORE is a separate question,
// answered by guard_power.py (the main-search cutoff is gated on clock < 90).
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdio>

int main() {
    forge::TranspositionTable tt(16);
    forge::Board board;
    std::string err;
    const char* fen = "7k/8/8/R7/8/8/8/K7 w - - 100 60";
    if (!board.set_fen(fen, &err)) {
        std::fprintf(stderr, "refused: %s\n", err.c_str());
        return 2;
    }
    const std::uint64_t key = board.key();

    struct P { const char* label; int clock; int score; };
    const P plants[] = {
        {"bail-like 0 @100", 100, 0},
        {"bail-like 0 @90", 90, 0},
        {"real 120 @100", 100, 120},
        {"mate15 @100", 100, forge::MateValue - 15},
    };

    std::printf("%-20s %-8s %-8s %-8s %-8s\n", "planted", "probe100", "probe99", "probe50", "probe0");
    for (const P& p : plants) {
        tt.clear();
        const forge::TTProbe probe = tt.probe(key);
        tt.store(probe, key, p.score, 0, forge::Move::none(), 10, forge::BoundExact, true, p.clock);
        const forge::TTProbe after = tt.probe(key);
        if (!after.hit) {
            std::printf("%-20s STORE DID NOT LAND\n", p.label);
            continue;
        }
        std::printf("%-20s %-8d %-8d %-8d %-8d\n", p.label,
                    after.entry.score_usable(100) ? 1 : 0,
                    after.entry.score_usable(99) ? 1 : 0,
                    after.entry.score_usable(50) ? 1 : 0,
                    after.entry.score_usable(0) ? 1 : 0);
    }

    // The comparison the answer turns on: is a clock-100 accept distinguishable
    // from a clock-99 accept? If both accept, the entry is not clock-specific and
    // the "poison at 100" framing is too narrow.
    std::printf("\nkey does not include the clock: ");
    forge::Board b99 = board;
    (void)b99.set_fen("7k/8/8/R7/8/8/8/K7 w - - 99 60", &err);
    std::printf("key(clock 100) %s key(clock 99)\n",
                board.key() == b99.key() ? "==" : "!=");
    return 0;
}
