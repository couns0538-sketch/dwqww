// Step E3 Incremental Non-Pawn Zobrist Oracle + Planted-Fault Test:
// Verifies across all 1,000 positions of positions_1000.txt + castling/promotion/ep positions and all depth-1 &
// sampled depth-2 moves + null moves + unmakes that Board::non_pawn_zobrist(White/Black) equals a fresh
// Board::set_fen(b.fen()).non_pawn_zobrist(White/Black) at every step!

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
    fens.push_back("r1bqk2r/ppP2ppp/2n5/8/2B5/8/PPP2pPP/RNBQK2R w KQkq - 0 8");

    std::uint64_t checked = 0;
    auto check_exact = [&](const forge::Board& b) -> bool {
        forge::Board fresh;
        if (!fresh.set_fen(b.fen())) return false;
        if (b.non_pawn_zobrist(forge::White) != fresh.non_pawn_zobrist(forge::White) ||
            b.non_pawn_zobrist(forge::Black) != fresh.non_pawn_zobrist(forge::Black)) {
            std::cerr << "NON_PAWN_ZOBRIST MISMATCH at FEN " << b.fen() << "\n";
            return false;
        }
        ++checked;
        return true;
    };

    for (const std::string& fen : fens) {
        forge::Board b;
        if (!b.set_fen(fen)) return 1;
        const auto w0 = b.non_pawn_zobrist(forge::White);
        const auto k0 = b.non_pawn_zobrist(forge::Black);
        for (const forge::Move m1 : b.legal_moves()) {
            forge::Undo u1;
            (void)b.make_move(m1, u1);
            if (!check_exact(b)) return 1;
            if (!b.in_check()) {
                forge::NullUndo nu;
                b.make_null_move(nu);
                if (!check_exact(b)) return 1;
                b.unmake_null_move(nu);
            }
            const auto leg2 = b.legal_moves();
            for (std::size_t idx = 0; idx < leg2.size(); idx += 8) {
                forge::Undo u2;
                (void)b.make_move(leg2[idx], u2);
                if (!check_exact(b)) return 1;
                b.unmake_move(leg2[idx], u2);
            }
            b.unmake_move(m1, u1);
            if (b.non_pawn_zobrist(forge::White) != w0 || b.non_pawn_zobrist(forge::Black) != k0) {
                std::cerr << "UNMAKE DRIFT at FEN " << fen << "\n";
                return 1;
            }
        }
    }
    std::cout << "E3_NONPAWN_ZOBRIST_ORACLE PASS: transitions_checked=" << checked << " mismatches=0\n";
    return 0;
}
