#include "forge/board.hpp"
#include "forge/search.hpp"
#include <iostream>
int main() {
    forge::Board ordinary, near;
    if (!ordinary.set_fen("7k/8/8/8/8/8/8/KR6 w - - 0 1") ||
        !near.set_fen("7k/8/8/8/8/8/8/KR6 w - - 98 1")) return 2;
    forge::Searcher warm(4), cold(4);
    forge::SearchLimits limits; limits.depth=4;
    const auto normal = warm.search(ordinary,limits);
    limits.depth=3;
    const auto cached = warm.search(near,limits);
    const auto fresh = cold.search(near,limits);
    std::cout << "public Searcher::search normal=" << normal.score << " warm98=" << cached.score
              << " cold98=" << fresh.score << " warm_move=" << forge::Board::move_to_uci(cached.best_move)
              << " cold_move=" << forge::Board::move_to_uci(fresh.best_move) << '\n';
}
