// Brute-force mate checker: a THIRD implementation, used only to adjudicate
// disagreements between the Python prover and the engine under audit.
//
// No alpha-beta, no transposition table, no mate-distance pruning, no
// heuristics. Plain minimax over python-chess-equivalent legal move generation
// would be ideal, but this uses the engine's own Board, which is a weakness and
// is stated as one: it can only adjudicate MATE EXISTENCE, not move legality.
// Since a mate proof is a property of the move tree and both sides use the same
// generator, an agreement here means the two searches agree about the TREE, and
// a disagreement means one of the two SEARCHES is wrong.
//
// Usage:  forge_brute <fen> <max_plies>
// Prints: "PROVED <sign> <plies>" or "NOMATE <max_plies>"
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "forge/board.hpp"

namespace {

constexpr int MATE = 100000;

// Full-width minimax. Returns the score with mate encoded as MATE - ply.
int minimax(forge::Board& board, int depth, int ply) {
    forge::MoveList moves = board.legal_moves();
    if (moves.empty()) return board.in_check() ? -MATE + ply : 0;
    if (depth <= 0) return 0;
    int best = -MATE - 1;
    for (const forge::Move move : moves) {
        forge::Undo undo;
        (void)board.make_move(move, undo);
        const int value = -minimax(board, depth - 1, ply + 1);
        board.unmake_move(move, undo);
        if (value > best) best = value;
    }
    return best;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::fprintf(stderr, "usage: %s <fen> <max_plies>\n", argv[0]);
        return 2;
    }
    forge::Board board;
    if (!board.set_fen(argv[1])) {
        std::fprintf(stderr, "invalid fen: %s\n", argv[1]);
        return 2;
    }
    const int limit = std::atoi(argv[2]);
    for (int d = 1; d <= limit; ++d) {
        const int score = minimax(board, d, 0);
        if (score >= MATE - d) {
            std::printf("PROVED 1 %d\n", MATE - score);
            return 0;
        }
        if (score <= -MATE + d) {
            std::printf("PROVED -1 %d\n", MATE + score);
            return 0;
        }
    }
    std::printf("NOMATE %d\n", limit);
    return 1;
}
