#include "forge/search.hpp"

#include <iostream>
#include <string>

// Depth-1 search of a legal position with 66 SEE-losing captures.
// Calling Searcher::search directly avoids the UCI loop, which stops an
// in-flight "go" as soon as stdin closes.

namespace {

constexpr const char* kFen =
    "3rQ2K/1n1Q1p2/1Q1n1Qp1/1p1Q1pRB/1Q1b1QpN/2bQ1pRB/4pQpN/kr3q2 w - - 0 1";

} // namespace

int main() {
    forge::Board board;
    std::string error;
    if (!board.set_fen(kFen, &error)) {
        std::cout << "fen " << error << "\n";
        return 1;
    }
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.depth = 1;
    const forge::SearchInfo info = searcher.search(
        board, limits, false, forge::Searcher::TTAccess::Exclusive);
    if (info.best_move.is_none()) {
        std::cout << "bestmove 0000\n";
        return 1;
    }
    const std::string move = forge::Board::move_to_uci(info.best_move);
    std::cout << "bestmove " << move << "\n";
    return move == "b4a3" ? 0 : 1;
}
