// Proof for Finding 3 (HIGH):
// src/search.cpp:1565-1567, 1704 — `go mate <N>` hard-caps `max_depth` to `2 * mate_moves - 1`,
// which fails to find forced mates in 2 and 3 because LMR, IIR, and pruning reduce effective
// depth below nominal `2 * N - 1`, and line 1704 also breaks early on `std::abs(score)` when
// `score < 0` (being mated).
//
// Build & run (ASan + UBSan):
//   g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
//     -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
//     -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
//     -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
//     -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
//     -Iforge-combo29/include forge-combo29/tests_audit/proof_go_mate_cap.cpp \
//     forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
//     forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
//     forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
//     -lpthread -o /tmp/proof_go_mate_cap
//   /tmp/proof_go_mate_cap

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>

int main() {
    // Case 1: Forced Mate in 2 (`1.Ra6! bxa6 2.Kxb8#`, or `1...B~ 2.Ra8#`).
    {
        forge::Board b;
        (void)b.set_fen("kbK5/pp6/1P6/8/8/8/7B/R7 w - - 0 1");

        forge::Searcher s_mate(16, 1);
        forge::SearchLimits lim_mate;
        lim_mate.mate_moves = 2;
        const auto r_mate = s_mate.search(b, lim_mate, false);

        forge::Searcher s_depth(16, 1);
        forge::SearchLimits lim_depth;
        lim_depth.depth = 6;
        const auto r_depth = s_depth.search(b, lim_depth, false);

        std::cout << "[Mate in 2] go mate 2: depth=" << r_mate.depth
                  << " best=" << forge::Board::move_to_uci(r_mate.best_move)
                  << " score=" << r_mate.score << "\n";
        std::cout << "[Mate in 2] go depth 6: depth=" << r_depth.depth
                  << " best=" << forge::Board::move_to_uci(r_depth.best_move)
                  << " score=" << r_depth.score << "\n";
    }

    // Case 2: Forced Mate in 3 (`1...Bc5+! 2.Kxc5 Qb6+ 3.Kd5 Qd6#`).
    {
        forge::Board b;
        (void)b.set_fen("r1b1kb1r/pppp1ppp/5q2/4n3/3KP3/2N3PN/PPP4P/R1BQ1B1R b kq - 0 1");

        forge::Searcher s_mate(16, 1);
        forge::SearchLimits lim_mate;
        lim_mate.mate_moves = 3;
        const auto r_mate = s_mate.search(b, lim_mate, false);

        forge::Searcher s_depth(16, 1);
        forge::SearchLimits lim_depth;
        lim_depth.depth = 6;
        const auto r_depth = s_depth.search(b, lim_depth, false);

        std::cout << "[Mate in 3] go mate 3: depth=" << r_mate.depth
                  << " best=" << forge::Board::move_to_uci(r_mate.best_move)
                  << " score=" << r_mate.score << "\n";
        std::cout << "[Mate in 3] go depth 6: depth=" << r_depth.depth
                  << " best=" << forge::Board::move_to_uci(r_depth.best_move)
                  << " score=" << r_depth.score << "\n";
    }
    return 0;
}
