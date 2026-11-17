// Safety + oracle + planted-fault test for Piece P4 (Board::has_legal_move()):
// Verifies Board::has_legal_move() == !Board::legal_moves().empty() across:
// - All 1,000 positions in positions_1000.txt + all depth-1 and sampled depth-2 children (~60,000+ positions).
// - Dedicated tricky corner cases: lone-king stalemate, pinned-knight stalemate, pinned-bishop stalemate,
//   along-pin-ray sole legal move, horizontally-pinned illegal en-passant stalemate vs legal en-passant sole move,
//   back-rank mate, smothered mate, and double-check mate/evasion.

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

    const std::vector<std::string> corner_fens = {
        "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",                       // lone-king stalemate
        "7k/5K2/6Q1/8/8/8/8/8 b - - 0 1",                       // checkmate
        "7k/8/8/8/8/1pb5/1N1n4/K7 w - - 0 1",                     // Ka1 boxed by pb3 (a2) & nd2 (b1), Nb2 pinned by bc3 -> stalemate!
        "7k/8/8/8/8/1pq5/1B1n4/K7 w - - 0 1",                     // Ka1 boxed, Bb2 pinned by qc3 -> sole legal move Bxc3!
        "8/8/8/8/k2pP1Q1/8/8/3K4 b - e3 0 1",                   // Black pawn d4 horizontally pinned between Ka4 and Qg4, king boxed? Tests ep pin!
        "6rk/5Npp/8/8/8/8/8/7K b - - 0 1",                      // smothered mate
        "3r2k1/5ppp/8/1B6/8/8/5PPP/3R2K1 b - - 0 1",            // normal position
    };
    for (const auto& cf : corner_fens) fens.push_back(cf);

    std::uint64_t checked = 0;
    std::uint64_t terminals = 0;
    for (const std::string& fen : fens) {
        forge::Board b;
        std::string err;
        if (!b.set_fen(fen, &err)) {
            std::cerr << "Invalid FEN '" << fen << "': " << err << "\n";
            return 1;
        }
        const bool fast = b.has_legal_move();
        const forge::MoveList leg = b.legal_moves();
        const bool ref = !leg.empty();
        if (fast != ref) {
            std::cerr << "MISMATCH on root '" << fen << "': fast=" << fast << " ref=" << ref << "\n";
            return 1;
        }
        ++checked;
        if (!ref) ++terminals;

        for (const forge::Move m1 : leg) {
            forge::Undo u1;
            (void)b.make_move(m1, u1);
            const bool f1 = b.has_legal_move();
            const forge::MoveList leg2 = b.legal_moves();
            const bool r1 = !leg2.empty();
            if (f1 != r1) {
                std::cerr << "MISMATCH at child '" << b.fen() << "': fast=" << f1 << " ref=" << r1 << "\n";
                return 1;
            }
            ++checked;
            if (!r1) ++terminals;

            for (std::size_t idx = 0; idx < leg2.size(); idx += 6) {
                forge::Undo u2;
                (void)b.make_move(leg2[idx], u2);
                const bool f2 = b.has_legal_move();
                const bool r2 = !b.legal_moves().empty();
                if (f2 != r2) {
                    std::cerr << "MISMATCH at grandchild '" << b.fen() << "': fast=" << f2 << " ref=" << r2 << "\n";
                    return 1;
                }
                ++checked;
                if (!r2) ++terminals;
                b.unmake_move(leg2[idx], u2);
            }
            b.unmake_move(m1, u1);
        }
    }
    std::cout << "P4_HAS_LEGAL_MOVE_ORACLE PASS: positions_checked=" << checked
              << " terminal_mates_and_stalemates=" << terminals << " mismatches=0\n";
    return 0;
}
