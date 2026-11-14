// Proof for Finding 4 (HIGH):
// src/search.cpp:1321-1345, 1482-1488 — Move-loop forward pruning omits `!pv_node`,
// `!in_check`, and `!is_mate_score(alpha)`.
// 1) Once an earlier root capture (`1.Bxb8`, mate in 5 = 31991) raises `alpha >= MateInMaxPly`,
//    `ss->static_eval + FutilityBase + FutilityMultiplier * lmr_depth <= alpha` is unconditionally
//    true (and SEE pruning also fires) at ply 2 on `1.Ra1! h4 2.Ra6!`, causing Forge at depth 8
//    and depth 9 to miss a forced Mate in 3 (`b1a1`, 31995) and play `h2b8` (Mate in 5, 31991).
// 2) On PV nodes (`pv_node == true`), forward pruning skips quiet moves and line 1482 still
//    stores `BoundExact` in the transposition table.
//
// Build & run (ASan + UBSan):
//   g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
//     -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
//     -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
//     -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
//     -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
//     -Iforge-combo29/include forge-combo29/tests_audit/proof_pruning_mating_and_check.cpp \
//     forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
//     forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
//     forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
//     -lpthread -o /tmp/proof_pruning_mating_and_check
//   /tmp/proof_pruning_mating_and_check

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>

int main() {
    // Forced Mate in 3 (`1.Ra1!`, 5 plies -> score = 32000 - 5 = 31995):
    //   - if `1...Bxh2`, `2.Rxa7#` (3 plies)
    //   - if `1...a6`,   `2.Rxa6+! bxa6 3.Kxb8#` (5 plies)
    //   - if `1...h4`,   `2.Ra6! bxa6 3.Kxb8#` (5 plies)
    forge::Board b;
    (void)b.set_fen("kbK5/pp6/1P6/7p/8/7P/7B/1R6 w - - 0 1");

    // Verify with `searchmoves b1a1` that `b1a1` is indeed a forced Mate in 3 (score 31995):
    {
        forge::Searcher s_only_ra1(16, 1);
        forge::SearchLimits lim;
        lim.depth = 8;
        lim.search_moves_specified = true;
        lim.search_moves.push_back(*b.parse_uci("b1a1"));
        const auto r_ra1 = s_only_ra1.search(b, lim, false);
        std::cout << "Restricted to b1a1 (depth 8): best=" << forge::Board::move_to_uci(r_ra1.best_move)
                  << " score=" << r_ra1.score << " (Mate in 3 = 31995)\n";
    }

    // Unrestricted search at depth 8 and depth 9: `1.Bxb8` (`h2b8`, Mate in 5 = 31991) raises
    // alpha to 31991 (>= MateInMaxPly), causing move-loop forward pruning at ply 2 to prune
    // `2.Ra6!` after `1.Ra1 h4` and miss the forced Mate in 3!
    for (int d : {8, 9}) {
        forge::Searcher s_full(16, 1);
        forge::SearchLimits lim;
        lim.depth = d;
        const auto r_full = s_full.search(b, lim, false);
        std::cout << "Unrestricted search (depth " << d << "): best="
                  << forge::Board::move_to_uci(r_full.best_move)
                  << " score=" << r_full.score << "\n";
    }
    return 0;
}
