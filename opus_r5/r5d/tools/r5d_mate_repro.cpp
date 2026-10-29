// R5D: loop a forced-mate search with several threads and count the runs that do not report the mate.
// Each run uses a fresh Searcher (an empty TT, as round 1 of tests/tt_mate_tb_tests.cpp) and searches the root to a
// fixed depth; a run fails when the score is not a mate for the side to move or claims a mate shorter than the
// true one. With --capture the main thread's info lines of every failing run are printed (diagnosis).
// usage: r5d_mate_repro <runs> <threads> <smpv2 0|1> <depth> [--fen FEN] [--plies N] [--capture] [--show N]
//        [--reuse] [--best-thread]   (--reuse: one Searcher for all runs, warm TT as in round 2; --best-thread:
//        UCI SmpBestThread=true) [--hash MB] [--prefill D]  (--prefill: a depth-D search of the root first)
#include "forge/board.hpp"
#include "forge/fb2.hpp"
#include "forge/search.hpp"
#include "forge/search_options.hpp"

#include <chrono>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 5) {
        std::cout << "usage: r5d_mate_repro <runs> <threads> <smpv2 0|1> <depth> [--fen FEN] [--plies N] [--capture] "
                     "[--show N] [--reuse]\n";
        return 2;
    }
    const int runs = std::atoi(argv[1]);
    const int threads = std::atoi(argv[2]);
    const bool smpv2 = std::atoi(argv[3]) != 0;
    const int depth = std::atoi(argv[4]);
    std::string fen = "4R3/8/8/k2K4/8/8/8/8 w - - 0 1";  // KRK, mate in 3 (5 plies), key move Kd5-c5 only
    int plies = 5;
    bool capture = false, reuse = false;
    int show = 5;
    int hash_mb = 16;
    int prefill = 0;
    for (int i = 5; i < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--fen" && i + 1 < argc) fen = argv[++i];
        else if (a == "--plies" && i + 1 < argc) plies = std::atoi(argv[++i]);
        else if (a == "--capture") capture = true;
        else if (a == "--reuse") reuse = true;
        else if (a == "--best-thread") forge::options::smp_best_thread = true;
        else if (a == "--hash" && i + 1 < argc) hash_mb = std::atoi(argv[++i]);
        else if (a == "--prefill" && i + 1 < argc) prefill = std::atoi(argv[++i]);
        else if (a == "--show" && i + 1 < argc) show = std::atoi(argv[++i]);
    }
    forge::fb2::requested.smp_v2 = smpv2;
    forge::Board root;
    if (!root.set_fen(fen)) {
        std::cout << "bad FEN\n";
        return 2;
    }
    std::unique_ptr<forge::Searcher> shared;
    if (reuse) shared = std::make_unique<forge::Searcher>(hash_mb, threads);
    int failures = 0, shown = 0;
    std::uint64_t nodes = 0;
    const auto t0 = std::chrono::steady_clock::now();
    for (int r = 0; r < runs; ++r) {
        std::unique_ptr<forge::Searcher> fresh;
        if (!reuse) fresh = std::make_unique<forge::Searcher>(hash_mb, threads);
        forge::Searcher& searcher = reuse ? *shared : *fresh;
        if (prefill > 0) {  // a shallower search of the same root first (warm TT, different entry history)
            forge::SearchLimits warm;
            warm.depth = prefill;
            (void)searcher.search(root, warm);
        }
        forge::SearchLimits limits;
        limits.depth = depth;
        std::ostringstream lines;
        std::streambuf* old = nullptr;
        if (capture) old = std::cout.rdbuf(lines.rdbuf());
        const forge::SearchInfo info = searcher.search(root, limits, capture);
        if (capture) std::cout.rdbuf(old);
        nodes += info.nodes;
        const bool ok = info.score >= forge::MateInMaxPly && info.score <= forge::MateValue - plies;
        if (!ok) {
            ++failures;
            if (shown < show) {
                ++shown;
                std::cout << "FAIL run " << r << ": score " << info.score << " depth " << info.depth << " move "
                          << forge::Board::move_to_uci(info.best_move) << " pv";
                for (const forge::Move m : info.pv) std::cout << ' ' << forge::Board::move_to_uci(m);
                std::cout << '\n';
                if (capture) std::cout << lines.str();
            }
        }
    }
    const double s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    std::cout << "runs " << runs << " threads " << threads << " smpv2 " << smpv2 << " depth " << depth
              << " hash " << hash_mb << (prefill > 0 ? " prefill " + std::to_string(prefill) : std::string())
              << (reuse ? " reuse" : " fresh") << (forge::options::smp_best_thread ? " best-thread" : "") << ": failures " << failures << " (" << 100.0 * failures / runs
              << "%), " << s << " s, mean nodes " << nodes / static_cast<std::uint64_t>(runs ? runs : 1) << '\n';
    return failures == 0 ? 0 : 1;
}
