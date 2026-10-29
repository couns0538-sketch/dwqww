// R5D diagnosis driver (scratch, never committed): run the KRK search until N failures and print the main thread's
// TT log at the node after the key move d5c5 for each failing run.
#include "forge/board.hpp"
#include "forge/fb2.hpp"
#include "forge/search.hpp"

#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>

#include <mutex>
namespace r5d_diag { extern std::uint64_t key; extern std::string log; extern bool on; extern std::mutex mutex; extern std::string stores; }

int main(int argc, char** argv) {
    const int runs = argc > 1 ? std::atoi(argv[1]) : 400;
    const int threads = argc > 2 ? std::atoi(argv[2]) : 2;
    const int want = argc > 3 ? std::atoi(argv[3]) : 2;
    const char* key_move = argc > 4 ? argv[4] : "d5c5";
    forge::Board root;
    (void)root.set_fen("4R3/8/8/k2K4/8/8/8/8 w - - 0 1");
    forge::Board child = root;
    forge::Undo undo;
    (void)child.make_move(*child.parse_uci(key_move), undo);
    r5d_diag::key = child.key();
    r5d_diag::on = true;
    int failures = 0;
    for (int r = 0; r < runs && failures < want; ++r) {
        r5d_diag::log.clear();
        r5d_diag::stores.clear();
        forge::Searcher searcher(16, threads);
        forge::SearchLimits limits;
        limits.depth = 14;
        const forge::SearchInfo info = searcher.search(root, limits);
        if (info.score >= forge::MateInMaxPly) continue;
        ++failures;
        std::cout << "FAIL run " << r << " score " << info.score << " move " << forge::Board::move_to_uci(info.best_move)
                  << "\n" << r5d_diag::stores << r5d_diag::log;
    }
    if (failures == 0) std::cout << "no failure in " << runs << " runs\n";
    // One passing run for comparison.
    r5d_diag::log.clear();
    forge::Searcher one(16, 1);
    forge::SearchLimits limits;
    limits.depth = 14;
    const forge::SearchInfo info = one.search(root, limits);
    std::cout << "single thread: score " << info.score << " move " << forge::Board::move_to_uci(info.best_move) << "\n"
              << r5d_diag::log;
    return 0;
}
