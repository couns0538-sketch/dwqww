// R5D: a forced mate stays a mate in multi-threaded searches (opus_r5/r5d/MATEFIX_REPORT.md).
//
//   forge_r5d_matefix_tests [runs per configuration, default 50]
//
// Before the R5D fix about 1 in 27 fresh two-thread searches of the K+R v K mate in 3 below (go depth 14) ended on
// a centipawn score (about +470 with Re8-e4): at shallow depths late-move pruning and LMR dropped the quiet zugzwang
// move of the mating line (1.Kc5 Ka6 2.Re7 Ka5 3.Ra7#), and the bounds that this pruning wrote into the shared TT
// kept the main thread from re-searching the key move Kc5. The fix (src/search/alphabeta.inc, mating mode: no
// quiet-move pruning and no LMR at a node whose side not to move has only its king, in multi-worker searches only)
// makes every run a mate. Checked: fresh searches with Threads 2 and 3, SmpV2 off and on, and Threads 2 on a TT and
// histories left by an unrelated depth-9 search (the openings below; after them a Threads 1 search of the same
// position misses the mate on the AL1 tree, which the fix leaves unchanged). Every score must be a real mate for
// the side to move and never shorter than the true mate in 3 (proved by the oracle of tests/tt_mate_tb_tests.cpp).
#include "forge/board.hpp"
#include "forge/fb2.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

using forge::Board;

constexpr std::string_view KrkFen = "4R3/8/8/k2K4/8/8/8/8 w - - 0 1";  // mate in 3, key move Kd5-c5 only
constexpr int KrkPlies = 5;
constexpr int KrkDepth = 14;

// opus_r5/r5d/diag/prefill40.fen lines 1, 3, 13, 14, 22, 36 (positions of tests/data/nnue_selfplay_sample_916.txt):
// a depth-9 search of one of them, then KrkFen at depth 14 on the same one-thread Searcher reports cp 437..478.
constexpr std::string_view WarmFens[] = {
    "r1bqkbnr/pppppp2/n6p/8/4P1P1/1PN5/P1PP2PP/R1BQKBNR b KQkq - 0 5",
    "r1bqk1nr/ppppppb1/n6p/8/4P1P1/1PN2N2/P1PP2PP/R1BQKB1R b KQkq - 2 6",
    "r1b1k2r/pp2ppb1/2p4p/8/1nB3P1/1PP2N1P/PBP3P1/3R1RK1 w - - 1 15",
    "r1b1k2r/pp2ppb1/2p4p/8/1nB3P1/1PP4P/PBPN2P1/3R1RK1 b - - 2 15",
    "r3k3/pp2ppbr/2p1n2p/7N/6P1/1PP4P/PBP3P1/3RR1K1 b - - 3 20",
    "7r/1p2pkn1/2p2p2/8/pPPR4/3P3P/P2B2P1/6K1 b - - 5 30",
};

int checks = 0;
int failures = 0;

void check(bool condition, const std::string& message) {
    ++checks;
    std::cout << (condition ? "PASS " : "FAIL ") << message << '\n';
    if (!condition) ++failures;
}

Board board_of(std::string_view fen) {
    Board board;
    if (!board.set_fen(fen)) throw std::runtime_error("invalid FEN: " + std::string(fen));
    return board;
}

forge::SearchInfo search_depth(forge::Searcher& searcher, const Board& board, int depth) {
    forge::SearchLimits limits;
    limits.depth = depth;
    return searcher.search(board, limits);
}

bool real_mate(int score) { return score >= forge::MateInMaxPly && score <= forge::MateValue - KrkPlies; }

std::string describe(const forge::SearchInfo& info) {
    return "score " + std::to_string(info.score) + " depth " + std::to_string(info.depth) + " move " +
           Board::move_to_uci(info.best_move);
}

// Fresh Searcher per run (empty TT), as in round 1 of tests/tt_mate_tb_tests.cpp.
void fresh_runs(int threads, bool smp_v2, int runs) {
    forge::fb2::requested.smp_v2 = smp_v2;
    const Board root = board_of(KrkFen);
    int bad = 0;
    int exact = 0;
    std::string first_bad;
    for (int run = 0; run < runs; ++run) {
        forge::Searcher searcher(16, threads);
        const forge::SearchInfo info = search_depth(searcher, root, KrkDepth);
        if (!real_mate(info.score)) {
            if (bad++ == 0) first_bad = " (first miss: run " + std::to_string(run) + ", " + describe(info) + ")";
        } else if (info.score == forge::MateValue - KrkPlies) {
            ++exact;
        }
    }
    forge::fb2::requested.smp_v2 = false;
    check(bad == 0, "fresh TT, Threads " + std::to_string(threads) + (smp_v2 ? " SmpV2" : "") + ", depth " +
                        std::to_string(KrkDepth) + ": " + std::to_string(runs - bad) + "/" + std::to_string(runs) +
                        " runs report a real mate (" + std::to_string(exact) + " exactly mate in 3)" + first_bad);
}

// One Searcher per run: an unrelated depth-9 search first (its TT entries and histories stay), then the mate.
void warm_runs(int threads, int repeats) {
    const Board root = board_of(KrkFen);
    int runs = 0;
    int bad = 0;
    std::string first_bad;
    for (int repeat = 0; repeat < repeats; ++repeat) {
        for (const std::string_view fen : WarmFens) {
            forge::Searcher searcher(16, threads);
            (void)search_depth(searcher, board_of(fen), 9);
            const forge::SearchInfo info = search_depth(searcher, root, KrkDepth);
            ++runs;
            if (!real_mate(info.score) && bad++ == 0) {
                first_bad = " (first miss: after " + std::string(fen) + ", " + describe(info) + ")";
            }
        }
    }
    check(bad == 0, "warm TT (an unrelated depth-9 search first), Threads " + std::to_string(threads) + ": " +
                        std::to_string(runs - bad) + "/" + std::to_string(runs) + " runs report a real mate" +
                        first_bad);
}

}  // namespace

int main(int argc, char** argv) {
    const int runs = argc >= 2 ? std::max(1, std::atoi(argv[1])) : 50;
    try {
        for (const int threads : {2, 3}) {
            fresh_runs(threads, false, runs);
            fresh_runs(threads, true, runs);
        }
        warm_runs(2, std::max(1, runs / 10));
    } catch (const std::exception& error) {
        std::cout << "FAIL exception: " << error.what() << '\n';
        return 2;
    }
    std::cout << "r5d matefix: " << checks << " checks, " << failures << " failures\n";
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " forge_r5d_matefix_tests\n";
    return failures == 0 ? 0 : 1;
}
