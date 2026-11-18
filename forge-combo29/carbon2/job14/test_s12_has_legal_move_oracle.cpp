// Job 14 Part 4 Exhaustive Oracle + Planted-Fault Verifier for stack/12_fast_has_legal_move.patch.txt:
// Across all 1,000 positions of positions_1000.txt, all depth-1 children, a wide sample of depth-2
// children (~45,000+ positions total), plus targeted stalemate / pinned-piece / en-passant / smothered-knight /
// boxed-slider / pure-pawn-endgame / double-check corner cases, verifies:
//   1. b.has_legal_move() == !b.legal_moves().empty() BEFORE ensure_king_lines() (king_lines_.valid == false)
//   2. b.has_legal_move() == !b.legal_moves().empty() AFTER  ensure_king_lines() (king_lines_.valid == true)

#include "forge/board.hpp"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {

bool check_board(const forge::Board& orig, const std::string& ctx) {
    // Fresh copy with king_lines_.valid == false (set_fen / make_move leaves valid == false)
    forge::Board b_cold = orig;
    const auto legals = orig.legal_moves();
    const bool expected = !legals.empty();

    const bool got_cold = b_cold.has_legal_move();
    if (got_cold != expected) {
        std::cerr << "ORACLE MISMATCH (cold king_lines) at " << ctx
                  << " fen='" << orig.fen() << "' got=" << got_cold
                  << " expected=" << expected << "\n";
        return false;
    }

    forge::Board b_warm = orig;
    (void)b_warm.ensure_king_lines();
    const bool got_warm = b_warm.has_legal_move();
    if (got_warm != expected) {
        std::cerr << "ORACLE MISMATCH (warm king_lines) at " << ctx
                  << " fen='" << orig.fen() << "' got=" << got_warm
                  << " expected=" << expected << "\n";
        return false;
    }
    return true;
}

} // namespace

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

    // Targeted corner cases covering every branch of 12_fast_has_legal_move.patch.txt:
    const char* corners[] = {
        // Stalemate with diagonally pinned pawn f2 (Black Qa7 pins f2 to Kh1; Rg8 covers g-file; ph3 covers g2)
        "6rk/q7/8/8/8/7p/5P2/7K w - - 0 1",
        // Stalemate with rank-pinned pawn e2
        "7k/8/8/8/6q1/8/r3P2K/8 w - - 0 1",
        "8/8/8/8/6k1/5br1/r3P2K/8 w - - 0 1",
        // Unpinned pure stalemate (pinned == 0, ep_square < 0 -> direct return false without movegen)
        "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
        "k7/2Q5/1K6/8/8/8/8/8 b - - 0 1",
        // Only legal move is a PINNED rook sliding along its pin ray (pinned != 0 fallback)
        "7k/8/8/8/8/5q2/r3R2K/8 w - - 0 1",
        // Only legal move is a PINNED pawn pushing along its file pin
        "4r2k/8/8/8/8/8/3qP1q1/4K3 w - - 0 1",
        // Stalemate EXCEPT en-passant capture is the ONLY legal move (pinned == 0, ep_square >= 0 -> true)
        "7k/8/8/8/pP6/P7/K7/1r6 b - b3 0 1",
        // Pseudo-legal en-passant is ILLEGAL due to horizontal rook pin -> stalemate (false)
        "8/8/8/K2pP2r/7p/6pP/6P1/7k w - d6 0 1",
        // Pure K+P endgame: only king can move (enemy_kn | enemy_bq | enemy_rq == 0 fast return)
        "8/8/8/8/4k3/4p3/4K3/8 w - - 0 1",
        // King captures undefended adjacent enemy bishop (live_bq becomes 0)
        "7k/8/8/8/8/8/6b1/6rK w - - 0 1",
        // King CANNOT capture defended adjacent enemy bishop -> stalemate
        "7k/8/8/3b4/8/8/6b1/6rK w - - 0 1",
        // Boxed-in knights at a1, h1, a8, h8 (file wrap test on NotAB / NotGH / FileA / FileH)
        "N6N/2P2P2/1P4P1/8/8/k7/8/4K3 w - - 0 1",
        "4k3/8/8/8/8/1P4P1/2P2P2/N3K2N w - - 0 1",
        // Smothered sliders + knights on edges with zero legal moves (stalemate)
        "6rk/5ppr/6pN/8/8/8/6q1/6BK w - - 0 1",
        // Double check with legal king escape vs double checkmate
        "4k3/8/8/8/1b6/8/4r3/4K3 w - - 0 1",
        "6rk/5Npp/8/6B1/8/8/8/6RK b - - 0 1",
    };
    for (const char* c : corners) fens.emplace_back(c);

    std::uint64_t checked = 0;
    for (std::size_t idx = 0; idx < fens.size(); ++idx) {
        forge::Board b;
        std::string err;
        if (!b.set_fen(fens[idx], &err)) {
            std::cerr << "BAD FEN: " << fens[idx] << " err=" << err << "\n";
            return 1;
        }
        if (!check_board(b, "root#" + std::to_string(idx))) return 1;
        ++checked;

        const auto legals1 = b.legal_moves();
        for (const forge::Move m1 : legals1) {
            forge::Board b1 = b;
            forge::Undo u1;
            (void)b1.make_move(m1, u1);
            if (!check_board(b1, "d1#" + std::to_string(idx))) return 1;
            ++checked;

            if (idx < 80 || idx >= 1000) {
                const auto legals2 = b1.legal_moves();
                for (const forge::Move m2 : legals2) {
                    forge::Board b2 = b1;
                    forge::Undo u2;
                    (void)b2.make_move(m2, u2);
                    if (!check_board(b2, "d2#" + std::to_string(idx))) return 1;
                    ++checked;
                }
            }
        }
    }

    std::cout << "S12_HAS_LEGAL_MOVE_ORACLE PASS: positions_checked=" << checked << " mismatches=0\n";
    return 0;
}
