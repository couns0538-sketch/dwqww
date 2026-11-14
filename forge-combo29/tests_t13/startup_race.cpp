// Extra t13 driver: concurrent first Board construction, then a search whose
// info line runs while helpers are still probing, and a stop from another thread.
// No files, processes, or network.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

int main() {
    constexpr int constructors = 4;
    std::atomic<int> bad_legal{0};
    std::vector<std::thread> construction;
    construction.reserve(constructors);
    for (int i = 0; i < constructors; ++i) {
        construction.emplace_back([&bad_legal] {
            forge::Board board;
            const forge::MoveList legal = board.legal_moves();
            if (legal.size() != 20) bad_legal.fetch_add(1, std::memory_order_relaxed);
        });
    }
    for (std::thread& thread : construction) thread.join();
    std::cout << "startup constructors " << constructors << " bad " << bad_legal.load() << '\n';
    if (bad_legal.load() != 0) return 1;

    forge::Board board;
    forge::Searcher searcher(16, 4);
    forge::SearchLimits limits;
    limits.depth = 8;
    std::thread stopper([&searcher] {
        searcher.stop();
        searcher.reset_stop();
    });
    const forge::SearchInfo info = searcher.search(board, limits, true);
    stopper.join();
    const bool legal = [&] {
        if (info.best_move.is_none()) return false;
        for (const forge::Move move : board.legal_moves()) {
            if (move == info.best_move) return true;
        }
        return false;
    }();
    std::cout << "stopped-search move " << forge::Board::move_to_uci(info.best_move) << " score " << info.score
              << " depth " << info.depth << (legal ? " legal" : " ILLEGAL") << '\n';
    if (!legal) return 1;
    std::cout << "PASS startup\n";
    return 0;
}
