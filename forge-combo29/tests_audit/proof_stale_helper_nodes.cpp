// Proof for Finding 2 (HIGH):
// src/search.cpp:881-889, 895-896, 1509-1510, 1803-1809 — Helper threads' `Worker::nodes_`
// retain stale node counts from the previous search until each newly spawned std::thread
// starts executing Worker::search(). On the main thread, `total_nodes() >= node_limit_`
// reads those stale helper counts at depth 1 before searching a single move, aborting at
// `depth == 0` and falling back to `root_candidates.front()` (blundering a forced mate in 3).
//
// Build & run (ASan + UBSan):
//   g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
//     -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
//     -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
//     -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
//     -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
//     -Iforge-combo29/include forge-combo29/tests_audit/proof_stale_helper_nodes.cpp \
//     forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
//     forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
//     forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
//     -lpthread -o /tmp/proof_stale_helper_nodes
//   /tmp/proof_stale_helper_nodes

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>

int main() {
    forge::Searcher searcher(16, 8);

    forge::Board start_board;
    forge::SearchLimits warmup_limits;
    warmup_limits.depth = 12;

    // Forced mate in 3 for Black: 1...Bc5+! 2.Kxc5 Qb6+ 3.Kd5 Qd6# (bestmove f8c5).
    // With 1 thread and `go nodes 5000`, Forge finds f8c5 (mate in 3) in ~1859 nodes.
    forge::Board mate_board;
    (void)mate_board.set_fen("r1b1kb1r/pppp1ppp/5q2/4n3/3KP3/2N3PN/PPP4P/R1BQ1B1R b kq - 0 1");

    forge::Searcher single_threaded(16, 1);
    forge::SearchLimits node_limits;
    node_limits.nodes = 5000;
    node_limits.nodes_specified = true;
    const forge::SearchInfo baseline = single_threaded.search(mate_board, node_limits, false);
    std::cout << "1-thread baseline (nodes=5000): depth=" << baseline.depth
              << " score=" << baseline.score
              << " best=" << forge::Board::move_to_uci(baseline.best_move)
              << " nodes=" << baseline.nodes << "\n";

    int zero_depth_aborts = 0;
    for (int trial = 1; trial <= 20; ++trial) {
        (void)searcher.search(start_board, warmup_limits, false);
        const forge::SearchInfo info = searcher.search(mate_board, node_limits, false);
        if (info.depth == 0) {
            ++zero_depth_aborts;
            if (zero_depth_aborts <= 3) {
                std::cout << "8-thread trial " << trial << " ABORTED AT DEPTH 0: depth=" << info.depth
                          << " score=" << info.score
                          << " best=" << forge::Board::move_to_uci(info.best_move)
                          << " reported_nodes=" << info.nodes << "\n";
            }
        }
    }
    std::cout << "Total depth-0 aborts out of 20 trials: " << zero_depth_aborts << "/20\n";
    return zero_depth_aborts > 0 ? 0 : 1;
}
