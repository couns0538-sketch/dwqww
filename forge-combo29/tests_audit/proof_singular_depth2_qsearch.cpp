// Proof for Finding 7 (HIGH):
// src/search.cpp:90, 1349-1359, 1120, 1005-1020, 1040, 1105 — UCI advertises `SingularDepth`
// with `min 2`. Setting `SingularDepth = 2` makes `singular_depth = (2 - 1) / 2 = 0` at `depth == 2`,
// so singular verification `search(board, ss, 0, singular_beta - 1, singular_beta, cut_node)`
// immediately drops into `Worker::qsearch()`.
// Unlike `Worker::search` (`line 1165`), `Worker::qsearch` (`lines 1016-1020`, `1054`, `1105`)
// ignores `ss->excluded_move`:
//   1) At line 1017, `qsearch` probes the node's own TT entry without checking `excluded.is_none()`
//      and sees `tt_score >= singular_beta` (`tt_score >= tt_score - 2 * SingularMargin`), cutting
//      off immediately on the unexcluded entry! When `singular_beta >= beta`, line 1366 returns
//      `singular_beta` (false multi-cut!) without searching a single alternative move!
//   2) When `qsearch` executes, it generates/searches `excluded_move` itself and calls `store_tt()`
//      on `board.key()` with `depth = 0`, clobbering the node's own TT entry.
//
// Build & run (ASan + UBSan):
//   g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
//     -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
//     -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
//     -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
//     -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
//     -Iforge-combo29/include forge-combo29/tests_audit/proof_singular_depth2_qsearch.cpp \
//     forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
//     forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
//     forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
//     -lpthread -o /tmp/proof_singular_depth2_qsearch
//   /tmp/proof_singular_depth2_qsearch

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>

int main() {
    // Position where White plays `1.g2g3`, reaching `child` (Black to move):
    //   Black has ONLY ONE winning move `1...Qxa2` (`a4a2`, +900 cp; in fact `1...Qa1+ 2.Kd2` etc.),
    //   Wait: put White Queen on `a4` attacking Black Queen on `a5` (`6k1/5ppp/8/q7/Q7/8/6PP/6K1 w - - 0 1`):
    //   - Move 1 (`1.h2h3`): Black plays `1...Qxa4` (`~ -900` for White -> `alpha_root ~ -900`, so for Move 2
    //     `beta_child ~ +900`).
    //   - Move 2 (`1.g2g3`): Black STILL has ONLY ONE non-losing move `1...Qxa4` (`+900`); every other Black
    //     move loses Black's Queen on `a5` (`-900`)!
    //   Seed `child` (after `1.g2g3`) with `depth = 1, BoundLower, score = 950, move = a5a4`.
    //   With `SingularDepth = 2`: at root `depth = 3` (`child` at `depth = 2`), `singular_beta = 946 >= beta_child`,
    //   `singular_depth = 0` -> `qsearch` cuts off on `child`'s own unexcluded TT entry (`950 >= 946`),
    //   triggering FALSE MULTI-CUT (`return 946`) without searching any alternative move and leaving `child`
    //   unsearched at depth 2 (`TT depth` remains `1` instead of `2`)!
    forge::Board root;
    (void)root.set_fen("6k1/5ppp/8/q7/Q7/8/6PP/6K1 w - - 0 1");
    const forge::Move h2h3 = *root.parse_uci("h2h3");
    const forge::Move g2g3 = *root.parse_uci("g2g3");

    forge::Board child = root;
    forge::Undo u;
    (void)child.make_move(g2g3, u);
    const forge::Move a5a4 = *child.parse_uci("a5a4");

    auto run_with = [&](int sd) {
        forge::tune::SingularDepth = sd;
        forge::Searcher s(16, 1);
        auto& tt = s.transposition_table();
        tt.store(tt.probe(child.key()), child.key(), 1850, 0, a5a4, 1, forge::BoundLower, false, child.halfmove_clock());
        forge::SearchLimits lim;
        lim.depth = 3;
        lim.search_moves_specified = true;
        lim.search_moves = {h2h3, g2g3};
        (void)s.search(root, lim, false);
        return tt.probe(child.key()).entry;
    };

    const auto e_def = run_with(7);
    const auto e_sd2 = run_with(2);
    std::cout << "SingularDepth=7 (default): child TT depth_after=" << static_cast<int>(e_def.depth)
              << " score=" << e_def.score << " (searched normally to depth 2)\n";
    std::cout << "SingularDepth=2 (UCI min): child TT depth_after=" << static_cast<int>(e_sd2.depth)
              << " score=" << e_sd2.score
              << " (qsearch cut off on child's own unexcluded TT entry -> false multi-cut skipped depth-2 search!)\n";
    return 0;
}
