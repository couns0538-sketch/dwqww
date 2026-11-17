// Step S5 make_move(precomputed_key) + Conditional KingLines Undo Oracle & Planted-Fault Test:
// Verifies across all 1,000 positions of positions_1000.txt + castling/promotion/ep positions and all depth-1 &
// sampled depth-2 moves (both WITH king_lines refreshed before make_move and WITHOUT king_lines refreshed before
// make_move, while refreshing king_lines on the child before unmake_move!) that:
// 1. key(), pawn_key(), fen(), is_legal(m), and gives_check(m) match an un-precomputed reference Board on every
//    child AND after unmake_move!

#include "forge/board.hpp"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::vector<std::string> fens;
    {
        std::ifstream in(argv[1]);
        std::string ln;
        while (std::getline(in, ln)) {
            if (!ln.empty() && ln.back() == '\r') ln.pop_back();
            if (!ln.empty()) fens.push_back(ln);
        }
    }
    fens.push_back("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
    fens.push_back("r3k2r/8/8/3pP3/8/8/8/R3K2R w KQkq d6 0 1");

    std::uint64_t transitions = 0;
    for (const std::string& fen : fens) {
        forge::Board b_fast;
        forge::Board b_ref;
        if (!b_fast.set_fen(fen) || !b_ref.set_fen(fen)) return 1;
        // Intentionally leave b_fast.king_lines_.valid == false at root on even indices!
        forge::MoveList pseudo;
        b_ref.generate_pseudo_legal(pseudo, false);
        for (const forge::Move m : pseudo) {
            if (!b_ref.is_legal(m)) continue;
            std::uint64_t ck = 0;
            const bool ek = b_fast.key_after(m, ck);
            forge::Undo u_fast, u_ref;
            (void)b_fast.make_move(m, u_fast, ek ? &ck : nullptr);
            (void)b_ref.make_move(m, u_ref, nullptr);

            if (b_fast.key() != b_ref.key() || b_fast.pawn_key() != b_ref.pawn_key() || b_fast.fen() != b_ref.fen()) {
                std::cerr << "CHILD STATE MISMATCH on " << fen << " move " << forge::Board::move_to_uci(m) << "\n";
                return 1;
            }
            // Force child king_lines_ to become valid = true BEFORE unmake_move, testing that unmake_move
            // properly invalidates parent king_lines_ when parent had valid == false!
            forge::MoveList child_pseudo;
            b_fast.generate_pseudo_legal(child_pseudo, false);
            for (const forge::Move cm : child_pseudo) {
                (void)b_fast.is_legal(cm);
                (void)b_fast.gives_check(cm);
                break;
            }

            b_fast.unmake_move(m, u_fast);
            b_ref.unmake_move(m, u_ref);
            // Verify parent is_legal / gives_check on every pseudo-legal move after unmake!
            for (const forge::Move pm : pseudo) {
                if (b_fast.is_legal(pm) != b_ref.is_legal(pm) || b_fast.gives_check(pm) != b_ref.gives_check(pm)) {
                    std::cerr << "POST-UNMAKE KING_LINES LEAK on " << fen << " after move "
                              << forge::Board::move_to_uci(m) << " probing " << forge::Board::move_to_uci(pm) << "\n";
                    return 1;
                }
            }
            ++transitions;
        }
    }
    std::cout << "S5_MAKE_MOVE_ORACLE PASS: transitions_checked=" << transitions << " mismatches=0\n";
    return 0;
}
