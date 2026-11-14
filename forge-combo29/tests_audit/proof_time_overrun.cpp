// Proof for Finding 5 (HIGH):
// src/search.cpp:1529-1548, 1611, 897-900, 992, 1125 — Time management clamps `available`,
// `soft_limit_ms_`, and `hard_limit_ms_` up to `>= 1 ms` even when `time_ms <= move_overhead_ms`
// (or `time_ms == 0` / `movetime_ms == 0`). Because `hard_limit_ms_ == 1`, the pre-search check
// `elapsed_ms() >= hard_limit_ms_` (`0 >= 1`) fails to return immediately, spawning all helper
// threads and searching 1000+ nodes past a 0 ms remaining budget (flagging on time).
// In addition, when `increment_ms` is large relative to `time_ms`, `soft_limit_ms_` exceeds
// `hard_limit_ms_`, and `soft_limit_ms_ * factor` plans more time than `time_ms`.
//
// Build & run (ASan + UBSan):
//   g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
//     -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
//     -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
//     -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
//     -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
//     -Iforge-combo29/include forge-combo29/tests_audit/proof_time_overrun.cpp \
//     forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
//     forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
//     forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
//     -lpthread -o /tmp/proof_time_overrun
//   /tmp/proof_time_overrun

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <chrono>
#include <iostream>

int main() {
    forge::Board b;
    (void)b.set_fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");

    // 1. Remaining clock is 0 ms (`wtime = 0`, `Move Overhead = 10`):
    //    Usable time left is 0 ms, yet Forge plans 1 ms and searches hundreds/thousands of nodes!
    {
        forge::Searcher s(16, 4);
        forge::SearchLimits lim;
        lim.time_ms = 0;
        lim.move_overhead_ms = 10;
        const auto t0 = std::chrono::steady_clock::now();
        const auto info = s.search(b, lim, false);
        const auto wall_us = std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now() - t0).count();
        std::cout << "Case 1 (wtime=0 ms, Move Overhead=10 ms, Threads=4):\n"
                  << "  expected immediate depth=0 return (0 ms left), got depth=" << info.depth
                  << " nodes=" << info.nodes << " wall_time=" << wall_us << " us\n";
    }

    // 2. Remaining clock is 5 ms (`wtime = 5 ms`), `Move Overhead = 50 ms` (usable budget <= 0 ms):
    //    With 16 threads under ASan/UBSan (or loaded system), wall time exceeds the entire 5 ms clock!
    {
        forge::Searcher s(16, 16);
        forge::SearchLimits lim;
        lim.time_ms = 5;
        lim.move_overhead_ms = 50;
        const auto t0 = std::chrono::steady_clock::now();
        const auto info = s.search(b, lim, false);
        const auto wall_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - t0).count();
        std::cout << "Case 2 (wtime=5 ms, Move Overhead=50 ms, Threads=16):\n"
                  << "  usable_after_overhead=0 ms, got depth=" << info.depth
                  << " nodes=" << info.nodes << " wall_time=" << wall_ms << " ms\n";
    }
    return 0;
}
