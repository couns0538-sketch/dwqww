#include "forge/board.hpp"
#include "forge/search.hpp"

#include <chrono>
#include <array>
#include <cstdint>
#include <iostream>
#include <string_view>

namespace {

struct SearchCase {
    std::string_view name;
    std::string_view fen;
    int depth;
};

constexpr std::array<SearchCase, 4> SearchCases{{
    {"start", forge::Board::StandardStartFen, 7},
    {"kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 6},
    {"middlegame", "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10", 6},
    {"endgame", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 7},
}};

} // namespace

int main() {
    using Clock = std::chrono::steady_clock;
    forge::Board board;
    const auto perft_start = Clock::now();
    const std::uint64_t perft_nodes = board.perft(5);
    const auto perft_ms = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - perft_start).count();
    const auto perft_nps = perft_ms > 0 ? perft_nodes * 1000ULL / static_cast<std::uint64_t>(perft_ms) : 0;
    std::cout << "perft depth=5 nodes=" << perft_nodes << " time_ms=" << perft_ms << " nps=" << perft_nps << '\n';

    for (const SearchCase& item : SearchCases) {
        if (!board.set_fen(item.fen)) return 2;
        forge::Searcher searcher(32);
        forge::SearchLimits limits;
        limits.depth = item.depth;
        const forge::SearchInfo result = searcher.search(board, limits);
        const auto search_nps = result.elapsed_ms > 0 ? result.nodes * 1000ULL / result.elapsed_ms : 0;
        std::cout << "search position=" << item.name << " depth=" << result.depth << " nodes=" << result.nodes
                  << " time_ms=" << result.elapsed_ms << " nps=" << search_nps
                  << " score_cp=" << result.score << " bestmove=" << forge::Board::move_to_uci(result.best_move) << '\n';
    }
    return perft_nodes == 4865609 ? 0 : 1;
}
