// Job 4 part B: a table test of parse_limits itself.
//
// How the function is reached without touching engine source: src/uci.cpp is
// #included as text into this program's own translation unit, with `main` renamed
// by a macro, so everything in it keeps internal linkage here and parse_limits can
// be called directly. The program runs a table of token lists and checks the exact
// SearchLimits fields of each row.
//
// Build:  g++ -std=c++20 -O1 -DFORGE_MARCH=x86-64-v3 -DFORGE_NNUE_V3=1 \
//             -DUCI_SOURCE_PATH='"<tree>/src/uci.cpp"' -I<tree>/include -I<tree>/src \
//             table_test.cpp -o table_test -pthread
// Run:    ./table_test            (all rows must pass)
//         ./table_test --self-check  (also shows a deliberately wrong row failing)
//
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#define main forge_uci_loop_main
#include UCI_SOURCE_PATH
#undef main

namespace {

struct Expect {
    const char* line;
    const char* side;        // "w" or "b"
    long long time_ms;       // -9999 == do not care
    long long increment_ms;
    long long movetime_ms;
    int depth;
    unsigned long long nodes;
    int nodes_specified;
    int soft_nodes;
    int moves_to_go;
    int mate_moves;
    int infinite;
};

// A wrong expectation, used only by --self-check: it must FAIL.
const Expect kWrong = {"go wtime 2000 btime 2000", "w", 1, 0, -1, 64, 0, 0, 0, 0, 0, 0};

std::string field(long long v) {
    return v == -9999 ? std::string("*") : std::to_string(v);
}

bool check(const Expect& e, const forge::SearchLimits& l, std::string& why) {
    auto bad = [&](const char* name, long long got, long long want) {
        if (want == -9999) return false;
        if (got != want) {
            why = std::string(name) + " got " + std::to_string(got) + " want " + std::to_string(want);
            return true;
        }
        return false;
    };
    if (bad("time_ms", l.time_ms, e.time_ms)) return false;
    if (bad("increment_ms", l.increment_ms, e.increment_ms)) return false;
    if (bad("movetime_ms", l.movetime_ms, e.movetime_ms)) return false;
    if (bad("depth", l.depth, e.depth)) return false;
    if (bad("nodes", static_cast<long long>(l.nodes), static_cast<long long>(e.nodes))) return false;
    if (bad("nodes_specified", l.nodes_specified ? 1 : 0, e.nodes_specified)) return false;
    if (bad("soft_nodes", l.soft_nodes ? 1 : 0, e.soft_nodes)) return false;
    if (bad("moves_to_go", l.moves_to_go, e.moves_to_go)) return false;
    if (bad("mate_moves", l.mate_moves, e.mate_moves)) return false;
    if (bad("infinite", l.infinite ? 1 : 0, e.infinite)) return false;
    return true;
}

} // namespace

int main(int argc, char** argv) {
    const bool self_check = argc > 1 && std::strcmp(argv[1], "--self-check") == 0;

    // time_ms / increment_ms / movetime_ms / moves_to_go / mate_moves start at -1
    // and depth at 0 in SearchLimits; nodes_specified, soft_nodes and infinite at 0.
    // Defaults from include/forge/search.hpp: depth = 64, time_ms = -1,
    // increment_ms = 0, movetime_ms = -1, moves_to_go = 0, mate_moves = 0,
    // nodes = 0 with nodes_specified = false, soft_nodes = false, infinite = false.
    const Expect rows[] = {
        // --- well formed
        {"go wtime 2000 btime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go wtime 2000 btime 3000", "b", 3000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go wtime 2000 winc 50 binc 60", "w", 2000, 50, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go btime 2000 binc 60 winc 50", "b", 2000, 60, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go movetime 1234", "w", -1, 0, 1234, 64, 0, 0, 0, 0, 0, 0},
        {"go depth 7", "w", -1, 0, -1, 7, 0, 0, 0, 0, 0, 0},
        {"go nodes 5000", "w", -1, 0, -1, 64, 5000, 1, 0, 0, 0, 0},
        {"go softnodes 5000", "w", -1, 0, -1, 64, 5000, 1, 1, 0, 0, 0},
        {"go movestogo 40 wtime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 40, 0, 0},
        {"go mate 5", "w", -1, 0, -1, 64, 0, 0, 0, 0, 5, 0},
        {"go infinite", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 1},
        {"go wtime 2000 btime 2000 depth 9 nodes 12345", "w", 2000, 0, -1, 9, 12345, 1, 0, 0, 0, 0},
        // --- keyword as a value: the parameter is absent, nothing consumed
        {"go wtime btime 50", "b", 50, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go btime wtime 2000 btime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go depth wtime 2000 btime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go nodes wtime 2000 btime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go movestogo wtime 2000 btime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go mate wtime 2000 btime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go movetime wtime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go winc wtime 2000 btime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go depth", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go nodes", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go wtime", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go movetime", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        // --- not a complete integer: consumed, parameter absent
        {"go depth abc", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go depth 7x", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go depth +-7", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go wtime abc btime 300", "b", 300, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go wtime 20x0 btime 300", "b", 300, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go nodes abc wtime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go movestogo abc wtime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go mate abc wtime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go movetime abc wtime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        // --- negative clocks clamp to 0 (they mean "no time left")
        {"go wtime -50 btime -50", "w", 0, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go wtime -1 winc -5", "w", 0, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go movetime -1", "w", -1, 0, 0, 64, 0, 0, 0, 0, 0, 0},
        {"go btime -50 wtime 0", "b", 0, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        // --- too large: clocks clamp to the ceiling, not to 0
        {"go wtime 99999999999999999999", "w", 9223372036854775807LL / 256, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go movetime 99999999999999999999", "w", -1, 0, 9223372036854775807LL / 256, 64, 0, 0, 0, 0, 0, 0},
        // --- depth / movestogo / mate clamp the old way
        {"go depth 0", "w", -1, 0, -1, 1, 0, 0, 0, 0, 0, 0},
        {"go depth -3", "w", -1, 0, -1, 1, 0, 0, 0, 0, 0, 0},
        {"go depth 99", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go movestogo 0", "w", -1, 0, -1, 64, 0, 0, 0, 1, 0, 0},
        {"go movestogo -7", "w", -1, 0, -1, 64, 0, 0, 0, 1, 0, 0},
        {"go movestogo 40", "w", -1, 0, -1, 64, 0, 0, 0, 40, 0, 0},
        {"go mate 0", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go mate -2", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go mate 40", "w", -1, 0, -1, 64, 0, 0, 0, 0, 32, 0},
        // --- nodes: negative or 0 becomes one node, specified
        {"go nodes -1", "w", -1, 0, -1, 64, 1, 1, 0, 0, 0, 0},
        {"go nodes 0", "w", -1, 0, -1, 64, 1, 1, 0, 0, 0, 0},
        {"go nodes -99999999999999999999", "w", -1, 0, -1, 64, 1, 1, 0, 0, 0, 0},
        {"go nodes 99999999999999999999", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go softnodes 0", "w", -1, 0, -1, 64, 1, 1, 1, 0, 0, 0},
        // --- combinations
        {"go wtime 2000 btime 2000 movestogo 0", "w", 2000, 0, -1, 64, 0, 0, 0, 1, 0, 0},
        {"go nodes -1 wtime 2000 btime 2000", "w", 2000, 0, -1, 64, 1, 1, 0, 0, 0, 0},
        {"go infinite wtime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 1},
        {"go wtime 2000 btime 2000 movetime 99999999999999999999", "w", 2000, 0, 2000, 64, 0, 0, 0, 0, 0, 0},
        {"go wtime 2000 movetime 500", "w", 2000, 0, 500, 64, 0, 0, 0, 0, 0, 0},
        {"go wtime 500 movetime 2000", "w", 500, 0, 500, 64, 0, 0, 0, 0, 0, 0},
        {"go movetime 2000", "w", -1, 0, 2000, 64, 0, 0, 0, 0, 0, 0},
        {"go depth 5 nodes 100 wtime 1000 btime 3000 movestogo 20 mate 3", "w", 1000, 0, -1, 5, 100, 1, 0, 20, 3, 0},
        {"go btime 3000 wtime 1000 searchmoves e2e4 d2d4", "w", 1000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go winc -20 binc -30", "w", -1, 0, -1, 64, 0, 0, 0, 0, 0, 0},
        {"go ponder wtime 2000", "w", 2000, 0, -1, 64, 0, 0, 0, 0, 0, 0},
    };

    int pass = 0;
    int fail = 0;
    for (const Expect& e : rows) {
        forge::Board board;
        (void)board.set_fen(forge::Board::StandardStartFen);
        if (std::strcmp(e.side, "b") == 0) {
            forge::Undo undo;
            (void)board.make_move(*board.parse_uci("e2e4"), undo);
        }
        std::istringstream input(e.line + 3);   // skip "go "
        const forge::SearchLimits l = parse_limits(input, board);
        std::string why;
        if (check(e, l, why)) {
            ++pass;
        } else {
            ++fail;
            std::printf("FAIL  %-58s %s\n", e.line, why.c_str());
        }
    }
    std::printf("table rows: %d pass, %d fail\n", pass, fail);

    if (self_check) {
        forge::Board board;
        (void)board.set_fen(forge::Board::StandardStartFen);
        std::istringstream input("wtime 2000 btime 2000");
        const forge::SearchLimits l = parse_limits(input, board);
        std::string why;
        const bool accepted = check(kWrong, l, why);
        std::printf("self-check row (deliberately wrong) was %s%s%s\n",
                    accepted ? "ACCEPTED -- TABLE HAS NO POWER" : "REJECTED as required",
                    accepted ? "" : ": ", accepted ? "" : why.c_str());
        if (accepted) ++fail;
    }
    return fail == 0 ? 0 : 1;
}
