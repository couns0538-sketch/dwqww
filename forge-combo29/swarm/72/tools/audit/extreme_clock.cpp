#include "forge/board.hpp"
#include "forge/search.hpp"
#include <iostream>
#include <limits>
int main() {
    forge::Board board;
    forge::Searcher searcher(4);
    forge::SearchLimits limits;
    limits.depth = 1;
    limits.time_ms = std::numeric_limits<int>::max();
    limits.increment_ms = std::numeric_limits<int>::max();
    const auto result = searcher.search(board, limits);
    std::cout << "depth=" << result.depth << " bestmove=" << forge::Board::move_to_uci(result.best_move) << '\n';
}
