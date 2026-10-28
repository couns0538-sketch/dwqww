// R3-5 reproduction (finding 1 of REPORT.md): how often a Threads-2 search of the K+R v K mate in 3
// 4R3/8/8/k2K4/8/8/8/8 w reports a longer mate, and what a single-thread search on the same TT reports afterwards.
// build: g++ -std=c++20 -O2 -DNDEBUG -march=x86-64-v3 -ffp-contract=off -DFORGE_NNUE_HIDDEN=256 -Iinclude
//        smp_mate_probe.cpp <build>/libforge_core.a -static -pthread -o smp_mate_probe.exe; run: smp_mate_probe.exe [runs]
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>

int main(int argc, char** argv) {
    const int runs = argc > 1 ? std::atoi(argv[1]) : 40;
    forge::Board root;
    if (!root.set_fen("4R3/8/8/k2K4/8/8/8/8 w - - 0 1")) return 2;
    int longer = 0;
    for (int i = 0; i < runs; ++i) {
        forge::Searcher smp(16, 2);
        forge::SearchLimits limits;
        limits.depth = 14;
        const forge::SearchInfo a = smp.search(root, limits);
        const forge::SearchInfo b = smp.search(root, limits);
        if (a.score != forge::MateValue - 5 || b.score != forge::MateValue - 5) {
            ++longer;
            smp.set_threads(1);
            limits.depth = 12;
            const forge::SearchInfo c = smp.search(root, limits);
            limits.depth = 20;
            const forge::SearchInfo d = smp.search(root, limits);
            forge::Searcher fresh(16, 1);
            limits.depth = 12;
            const forge::SearchInfo e = fresh.search(root, limits);
            std::cout << "run " << i << ": smp " << a.score << " " << forge::Board::move_to_uci(a.best_move) << " / "
                      << b.score << " " << forge::Board::move_to_uci(b.best_move) << "; then 1 thread d12 " << c.score
                      << " " << forge::Board::move_to_uci(c.best_move) << ", d20 " << d.score << " "
                      << forge::Board::move_to_uci(d.best_move) << "; fresh 1 thread d12 " << e.score << '\n';
        }
    }
    std::cout << "longer mates: " << longer << " / " << runs << '\n';
    return 0;
}
