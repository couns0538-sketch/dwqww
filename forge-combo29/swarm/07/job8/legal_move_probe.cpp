// legal_move_probe.cpp -- is Board::has_legal_move() ever wrong?
//
// has_legal_move() decides stalemate and checkmate at the search root and in
// is_draw()/draw_leaf_score(), so a wrong answer is a wrong game result, not a
// cosmetic difference.
//
// The reference is python-chess over a pipe: this program prints, for every position it
// reaches, the FEN and the engine's answer; a python driver recomputes the truth from the
// same FEN and compares. Positions are reached by random legal play plus the special
// families that stress the fast witness path: pawn pushes blocked, promotions only,
// en passant only, pinned-pawn-only pushes.
#include "forge/board.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <random>
#include <string>

using namespace forge;

namespace {
void emit(const Board& board) {
    std::printf("%s | has_legal_move=%d legal_count=%zu\n", board.fen().c_str(),
                int(board.has_legal_move()), board.legal_moves().size());
}
}  // namespace

int main(int argc, char** argv) {
    const int games = argc > 1 ? std::atoi(argv[1]) : 60;
    const unsigned seed = argc > 2 ? static_cast<unsigned>(std::atoi(argv[2])) : 701u;
    std::mt19937_64 rng(seed);
    std::printf("GAMES %d SEED %u\n", games, seed);

    long positions = 0;
    for (int game = 0; game < games; ++game) {
        Board board;
        emit(board);
        ++positions;
        for (int ply = 0; ply < 300; ++ply) {
            const auto moves = board.legal_moves();
            if (moves.size() == 0) break;
            const Move pick = moves[static_cast<std::size_t>(rng() % moves.size())];
            Undo undo;
            (void)board.make_move(pick, undo);
            // Bias toward endings where the fast witness path matters: once few pieces are
            // left, emit every position (promotion races, blocked pawns, lone kings).
            const int pieces = popcount(board.occupied());
            if (pieces <= 12 || (rng() % 8) == 0) {
                emit(board);
                ++positions;
            }
        }
    }

    // Targeted families, each a handful of FENs.
    const char* family[] = {
        // blocked pawns with a king that has no square: stalemate
        "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
        // checkmate
        "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1",
        // lone king with moves
        "8/8/8/8/8/8/8/K6k w - - 0 1",
        // only move is a promotion
        "8/8/8/8/8/8/6p1/6Kk b - - 0 1",
        // pawn blocked, king stalemated
        "8/8/8/8/8/5k2/5p2/5K2 w - - 0 1",
        // en passant is the only legal move
        "8/8/8/8/3pP3/8/8/K6k b - e3 0 1",
        // pinned pawn cannot push, king has no square
        "8/8/8/8/8/2k5/2p5/2K5 w - - 0 1",
    };
    for (const char* fen : family) {
        Board board;
        if (!board.set_fen(fen)) {
            std::printf("REFUSED %s\n", fen);
            continue;
        }
        emit(board);
        ++positions;
    }
    std::printf("END %ld\n", positions);
    return 0;
}
