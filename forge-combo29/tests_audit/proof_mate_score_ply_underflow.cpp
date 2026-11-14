// Proof for Finding 6 (HIGH):
// src/search.cpp:117-128 — `score_from_tt(int score, int ply)` subtracts `ply` from a TT mate
// score (`score >= MateInMaxPly`, where `MateInMaxPly = 32000 - 128 = 31872`) without checking
// whether `score - ply` drops below `MateInMaxPly`. When a valid TT mate entry (`tte.score = 31873`,
// `is_mate_score(31873) == true`) is probed at `ply = 2`, `score_from_tt(31873, 2)` returns
// `31871 < MateInMaxPly` (`is_mate_score(31871) == false`). That non-mate score is never
// ply-adjusted again and returns to the root as a bogus centipawn score (`score cp 31871`)!
//
// Build & run (ASan + UBSan):
//   g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
//     -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
//     -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
//     -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
//     -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
//     -Iforge-combo29/include forge-combo29/tests_audit/proof_mate_score_ply_underflow.cpp \
//     forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
//     forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
//     forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
//     -lpthread -o /tmp/proof_mate_score_ply_underflow
//   /tmp/proof_mate_score_ply_underflow

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>

int main() {
    // Boxed kings on a1/a8; White's only move is `1.g3g4`, Black's only reply is `1...h6h5`.
    forge::Board root;
    (void)root.set_fen("kb6/p1p5/P1P4p/8/8/p1p3P1/P1P5/KB6 w - - 0 1");

    forge::Board ply2 = root;
    forge::Undo u1, u2;
    (void)ply2.make_move(*ply2.parse_uci("g3g4"), u1);
    (void)ply2.make_move(*ply2.parse_uci("h6h5"), u2);

    forge::Searcher searcher(16, 1);
    forge::TranspositionTable& tt = searcher.transposition_table();
    const forge::TTProbe p = tt.probe(ply2.key());
    const int valid_mate_in_tt = forge::MateInMaxPly + 1; // 31873: is_mate_score(31873) == true!
    tt.store(p, ply2.key(), valid_mate_in_tt, 0, forge::Move::none(), 10, forge::BoundExact, true, ply2.halfmove_clock());

    std::cout << "Seeded ply-2 TT entry with score=" << valid_mate_in_tt
              << " (is_mate_score=" << forge::is_mate_score(valid_mate_in_tt) << ")\n";

    forge::SearchLimits lim;
    lim.depth = 2;
    const forge::SearchInfo info = searcher.search(root, lim, true);
    std::cout << "Root search returned: score=" << info.score
              << " is_mate_score=" << forge::is_mate_score(info.score)
              << " best=" << forge::Board::move_to_uci(info.best_move) << "\n";
    return 0;
}
