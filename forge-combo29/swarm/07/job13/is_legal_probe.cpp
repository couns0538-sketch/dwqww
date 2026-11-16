// is_legal_probe.cpp -- cross-checks the fast legality path against brute force.
//
// Board::is_legal() (with FORGE_SPD_KING_LINES=1) takes a shortcut when the side is not in
// check, the move is not en passant and the mover is not the king: it only consults the pin
// set and the alignment test (board.cpp:747-751). The brute-force truth is: make the move and
// ask whether the mover's own king is attacked.
//
// For every legal-looking move generated over random play this program compares:
//   fast  = board.is_legal(move)          (the shipped shortcut)
//   brute = make + square_attacked(king)  (unmake)
// and reports every disagreement with its FEN and move.
#include "forge/board.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <string>

using namespace forge;

namespace {
bool brute_legal(const Board& board, Move move) {
    Board copy = board;
    Undo undo;
    (void)copy.make_move(move, undo);
    // After make_move the side to move is the opponent; the mover's king must not be attacked
    // by the new side to move.
    const Color mover = opposite(copy.side_to_move());
    return !copy.square_attacked(copy.king_square(mover), copy.side_to_move());
}
}  // namespace

int main(int argc, char** argv) {
    const int games = argc > 1 ? std::atoi(argv[1]) : 40;
    const unsigned seed = argc > 2 ? static_cast<unsigned>(std::atoi(argv[2])) : 701u;
    std::mt19937_64 rng(seed);

    std::uint64_t compared = 0, mismatches = 0, fast_true_brute_false = 0, fast_false_brute_true = 0;
    std::string first;
    for (int game = 0; game < games; ++game) {
        Board board;
        for (int ply = 0; ply < 250; ++ply) {
            MoveList pseudo;
            board.generate_pseudo_legal(pseudo, false);
            for (const Move move : pseudo) {
                const bool fast = board.is_legal(move);
                const bool brute = brute_legal(board, move);
                ++compared;
                if (fast != brute) {
                    ++mismatches;
                    if (fast && !brute) ++fast_true_brute_false;
                    if (!fast && brute) ++fast_false_brute_true;
                    if (first.empty()) {
                        first = "fen " + board.fen() + " move " + Board::move_to_uci(move) +
                                " fast " + (fast ? "legal" : "illegal") +
                                " brute " + (brute ? "legal" : "illegal");
                    }
                }
            }
            const auto legal = board.legal_moves();
            if (legal.size() == 0) break;
            const Move pick = legal[static_cast<std::size_t>(rng() % legal.size())];
            Undo undo;
            (void)board.make_move(pick, undo);
        }
    }
    std::printf("games %d seed %u\n", games, seed);
    std::printf("moves compared %llu  mismatches %llu (fast-says-legal-but-illegal %llu, "
                "fast-says-illegal-but-legal %llu)\n",
                static_cast<unsigned long long>(compared),
                static_cast<unsigned long long>(mismatches),
                static_cast<unsigned long long>(fast_true_brute_false),
                static_cast<unsigned long long>(fast_false_brute_true));
    if (compared == 0) {
        std::printf("FAIL nothing compared\n");
        return 2;
    }
    if (mismatches != 0) {
        std::printf("FIRST MISMATCH %s\n", first.c_str());
        return 1;
    }
    std::printf("OK the fast legality path agreed with make/unmake brute force on every move\n");
    return 0;
}
