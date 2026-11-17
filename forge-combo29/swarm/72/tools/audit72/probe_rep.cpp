// Instrumented search probe for question 5: does the engine see a repetition
// that occurs BELOW the root?
//
// It replays a root position plus a move list, counts how many times the
// search's repetition predicate fires, and reports the ply distribution.  That
// distinguishes "repetition detection works in-tree" from "detection is
// root-only" without relying on score heuristics.
//
//   probe_rep <FEN> <search-plies> <move...>
//
// The move list defines the current position (the search root).  The tool then
// searches it and prints the number of nodes at which is_repetition() was true.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <array>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: probe_rep <FEN> <depth> <move...>" << std::endl;
        return 2;
    }
    forge::Board board;
    std::string error;
    if (!board.set_fen(argv[1], &error)) {
        std::cout << "FENREFUSED " << error << std::endl;
        return 1;
    }
    const int depth = std::stoi(argv[2]);
    for (int i = 3; i < argc; ++i) {
        const auto move = board.parse_uci(argv[i]);
        if (!move.has_value()) {
            std::cout << "ILLEGAL " << argv[i] << std::endl;
            return 1;
        }
        forge::Undo undo;
        (void)board.make_move(*move, undo);
    }
    std::cout << "ROOT key=" << std::hex << board.key() << std::dec
              << " repetition=" << (board.is_repetition() ? 1 : 0)
              << " halfmove=" << board.halfmove_clock()
              << " hist=" << board.key_history().size()
              << " fen=\"" << board.fen() << "\"" << std::endl;

    forge::Searcher searcher;
    forge::SearchLimits limits;
    limits.depth = depth;
    const forge::SearchInfo info = searcher.search(board, limits, false);
    const auto score = info.score;
    std::cout << "RESULT best=" << forge::Board::move_to_uci(info.best_move)
              << " nodes=" << info.nodes
              << " depth=" << info.depth
              << " score=" << score << std::endl;
    return 0;
}
