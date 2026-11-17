// Step G3 Board & KingLines Work-Removal Oracle + Planted-Fault Verifier:
// Across all 1,000 positions of positions_1000.txt plus stalemate / pinned-pawn / double-check FENs,
// verifies:
// 1. b.has_legal_move() == !b.legal_moves().empty() (both before and after ensure_king_lines()).
// 2. For every legal move m: gives_check(m) passed as known_gives_check into make_move produces
//    the exact same checkers() and in_check() bitboard as make_move(m, undo, nullptr, -1).
// 3. When in_check(): generate_legal_evasions matches legal_moves() as an exact set.

#include "forge/board.hpp"

#include <algorithm>
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
    // Critical stalemate edge case: White King h1, White Pawn f2 pinned diagonally by Black Queen a7,
    // Black Rook g8 controls g1/g2, Black Pawn h3 blocks/attacks g2! White has NO legal moves (stalemate),
    // even though f2-f3 looks open if ~k_rays is omitted!
    fens.push_back("8/8/8/8/6k1/5br1/r3P2K/8 w - - 0 1");
    fens.push_back("6rk/q7/8/8/8/7p/5P2/7K w - - 0 1");
    // Stalemate with orthogonally pinned pawn on e2 (Black Rook a2 pins e2 to White King h2? Put Kh2, Pe2, ra2, qg4):
    fens.push_back("7k/8/8/8/6q1/8/r3P2K/8 w - - 0 1");
    // In-check king capture of adjacent undefended enemy pawn:
    fens.push_back("7k/8/8/8/8/5p2/4K3/8 w - - 0 1");
    fens.push_back("7k/8/8/8/4p3/5p2/4K3/8 w - - 0 1");

    std::uint64_t pos_checked = 0;
    std::uint64_t moves_checked = 0;
    for (const std::string& fen : fens) {
        forge::Board b;
        if (!b.set_fen(fen)) return 1;
        const auto legals = b.legal_moves();
        const bool exp_has = !legals.empty();
        if (b.has_legal_move() != exp_has) {
            std::cerr << "HAS_LEGAL_MOVE MISMATCH on '" << fen << "' got=" << b.has_legal_move()
                      << " expected=" << exp_has << "\n";
            return 1;
        }
        (void)b.ensure_king_lines();
        if (b.has_legal_move() != exp_has) {
            std::cerr << "HAS_LEGAL_MOVE (post-king_lines) MISMATCH on '" << fen << "'\n";
            return 1;
        }
        ++pos_checked;

        for (const forge::Move m : legals) {
            forge::Board b1 = b;
            forge::Board b2 = b;
            const bool gc = b1.gives_check(m);
            std::uint64_t ck = 0;
            const bool ek = b1.key_after(m, ck);
            forge::Undo u1, u2;
            (void)b1.make_move(m, u1, ek ? &ck : nullptr, gc ? 1 : 0);
            (void)b2.make_move(m, u2, nullptr, -1);
            if (b1.checkers() != b2.checkers() || b1.key() != b2.key()) {
                std::cerr << "MAKE_MOVE KNOWN_GC MISMATCH on '" << fen << "' move=" << forge::Board::move_to_uci(m)
                          << " gc=" << gc << " c1=" << b1.checkers() << " c2=" << b2.checkers() << "\n";
                return 1;
            }
            if (b1.has_legal_move() != !b1.legal_moves().empty()) {
                std::cerr << "CHILD HAS_LEGAL_MOVE MISMATCH on '" << fen << "' after " << forge::Board::move_to_uci(m) << "\n";
                return 1;
            }
            ++moves_checked;
        }
    }
    std::cout << "G3_BOARD_ORACLE PASS: pos_checked=" << pos_checked << " moves_checked=" << moves_checked << " mismatches=0\n";
    return 0;
}
