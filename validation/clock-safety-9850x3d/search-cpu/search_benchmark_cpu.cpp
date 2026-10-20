// High-resolution paired benchmark driver. Original MIT-licensed support code.
#include "forge/board.hpp"
#include "forge/search.hpp"
#include <array>
#include <chrono>
#include <ctime>
#include <cstdint>
#include <iostream>
#include <string_view>

struct Case { std::string_view name; std::string_view fen; int depth; };
constexpr std::array<Case, 4> Cases{{
    {"start", forge::Board::StandardStartFen, 7},
    {"kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 6},
    {"middlegame", "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10", 6},
    {"endgame", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 7}
}};
int main(int argc, char** argv) {
    const bool deep = argc == 2 && std::string_view(argv[1]) == "--deep";
    if (argc > 2 || (argc == 2 && !deep)) return 2;
    using Clock = std::chrono::steady_clock;
    std::cout << "kind,position,depth,nodes,time_us,process_cpu_us,engine_ms,score_cp,bestmove\n";
    if (!deep) {
        forge::Board board;
        const auto cpu_start = std::clock();
        const auto start = Clock::now();
        const auto nodes = board.perft(5);
        const auto us = std::chrono::duration_cast<std::chrono::microseconds>(Clock::now() - start).count();
        const auto cpu_us = static_cast<long long>((std::clock() - cpu_start) * 1000000.0 / CLOCKS_PER_SEC);
        std::cout << "perft,start,5," << nodes << ',' << us << ',' << cpu_us << ",,,\n";
        if (nodes != 4865609) return 1;
    }
    for (const Case& item : Cases) {
        forge::Board board;
        if (!board.set_fen(item.fen)) return 2;
        forge::Searcher searcher(32);
        forge::SearchLimits limits;
        limits.depth = item.depth + (deep ? 2 : 0);
        const auto cpu_start = std::clock();
        const auto start = Clock::now();
        const auto result = searcher.search(board, limits);
        const auto us = std::chrono::duration_cast<std::chrono::microseconds>(Clock::now() - start).count();
        const auto cpu_us = static_cast<long long>((std::clock() - cpu_start) * 1000000.0 / CLOCKS_PER_SEC);
        std::cout << (deep ? "deep" : "shallow") << ',' << item.name << ',' << result.depth << ','
                  << result.nodes << ',' << us << ',' << cpu_us << ',' << result.elapsed_ms << ',' << result.score << ','
                  << forge::Board::move_to_uci(result.best_move) << '\n';
    }
}
