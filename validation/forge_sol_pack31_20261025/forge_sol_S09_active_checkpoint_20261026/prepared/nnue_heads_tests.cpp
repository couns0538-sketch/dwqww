// buckets8 output heads: piece-count -> head mapping and loader contract.
#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <iostream>

using namespace forge;

static_assert(nnue::OutputHeads == 8);
// Every legal piece count 2..32 maps to its band; out-of-range counts clamp.
static_assert(nnue::output_head(0) == 0 && nnue::output_head(1) == 0);
static_assert(nnue::output_head(2) == 0 && nnue::output_head(4) == 0);
static_assert(nnue::output_head(5) == 1 && nnue::output_head(8) == 1);
static_assert(nnue::output_head(9) == 2 && nnue::output_head(12) == 2);
static_assert(nnue::output_head(13) == 3 && nnue::output_head(16) == 3);
static_assert(nnue::output_head(17) == 4 && nnue::output_head(20) == 4);
static_assert(nnue::output_head(21) == 5 && nnue::output_head(24) == 5);
static_assert(nnue::output_head(25) == 6 && nnue::output_head(28) == 6);
static_assert(nnue::output_head(29) == 7 && nnue::output_head(32) == 7);
static_assert(nnue::output_head(33) == 7 && nnue::output_head(64) == 7 && nnue::output_head(-5) == 0);

int main() {
    int failures = 0;
    auto check = [&](bool ok, const char* what) {
        if (!ok) { ++failures; std::cerr << "FAIL " << what << '\n'; }
    };
    // Each band is exactly 4 wide (band 0 starts at 1) and bands are monotone.
    for (int pieces = 1; pieces <= 32; ++pieces) {
        check(nnue::output_head(pieces) == (pieces - 1) / 4, "band formula");
        if (pieces > 1) check(nnue::output_head(pieces) >= nnue::output_head(pieces - 1), "monotone");
    }
    if (nnue::available()) {
        const int stored = nnue::stored_output_heads();
        check(stored == 1 || stored == nnue::OutputHeads, "stored heads is 1 or 8");
        // Positions spanning every head evaluate without touching invalid
        // memory (ASan builds catch out-of-bounds head reads) and refresh is
        // deterministic.
        const char* fens[] = {
            "4k3/8/8/8/8/8/8/4K3 w - - 0 1",                                   // 2 -> head 0
            "4k3/8/8/8/8/8/4P3/R3K3 w - - 0 1",                               // 4 -> 0
            "4k3/4p3/8/8/8/8/4P3/R3K3 b - - 0 1",                             // 5 -> 1
            "r3k3/pp6/8/8/8/8/PPP5/R3K2R w - - 0 1",                          // 9 -> 2
            "r3k2r/pppp4/8/8/8/8/PPPP4/R3K2R w KQkq - 0 1",                   // 14 -> 3
            "r1bqk2r/pppp4/8/8/8/8/PPPP4/R1BQK2R w KQkq - 0 1",               // 18 -> 4
            "r1bqk2r/pppppp2/8/8/8/8/PPPPPP2/R1BQK2R w KQkq - 0 1",           // 22 -> 5
            "rnbqk2r/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1",         // 28 -> 6
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",       // 32 -> 7
        };
        bool seen[nnue::OutputHeads] = {};
        for (const char* fen : fens) {
            Board board;
            check(board.set_fen(fen), "fixture fen");
            seen[nnue::output_head(popcount(board.occupied()))] = true;
            nnue::Accumulator a, b;
            nnue::refresh(board, a);
            nnue::refresh(board, b);
            check(nnue::evaluate(board, a) == nnue::evaluate(board, b), "deterministic eval");
        }
        for (int h = 0; h < nnue::OutputHeads; ++h) check(seen[h], "fixtures cover every head");
    }
    std::cout << (failures == 0 ? "nnue heads tests passed\n" : "nnue heads tests FAILED\n");
    return failures == 0 ? 0 : 1;
}
