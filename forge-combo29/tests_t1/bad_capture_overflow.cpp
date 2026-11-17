// A legal position whose main-search capture picker stores more than 64
// SEE-losing captures. On the lock, that write runs past bad_captures_.
#include "forge/search.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

namespace {

constexpr std::string_view Fen =
    "3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2 w - - 0 1";

int losing_captures(const forge::Board& board) {
    int count = 0;
    for (const forge::Move move : board.pseudo_legal_moves(true)) {
        if (!board.see_ge(move, 0)) ++count;
    }
    return count;
}

} // namespace

int main() {
    forge::Board board;
    std::string error;
    if (!board.set_fen(Fen, &error)) {
        std::cerr << "fen rejected: " << error << "\n";
        return 1;
    }
    const int losing = losing_captures(board);
    std::cout << "in_check " << (board.in_check() ? 1 : 0) << std::endl;
    std::cout << "losing_captures " << losing << std::endl;
    if (board.in_check() || losing <= 64) {
        std::cerr << "position does not force the 64-slot capture list\n";
        return 1;
    }

    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.depth = 1;
    const forge::SearchInfo result = searcher.search(board, limits, false);
    if (result.best_move.is_none() || !board.is_legal(result.best_move)) {
        std::cerr << "search did not return a legal move\n";
        return 1;
    }
    std::cout << "bestmove " << forge::Board::move_to_uci(result.best_move) << "\n";
    std::cout << "nodes " << result.nodes << "\n";
    return 0;
}
