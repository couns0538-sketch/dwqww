#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <string_view>

// `go nodes` used to keep the previous iteration's score and take a best move
// from the iteration the limit cut off. The score and the move must be the
// pair produced by the last iteration that actually finished.

namespace {

int g_failures = 0;

struct Outcome {
    int score = 0;
    int depth = 0;
    std::uint64_t nodes = 0;
    std::string move;
};

Outcome search_fen(std::string_view fen, int depth, std::uint64_t nodes, bool use_nodes) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        std::cerr << "bad fen " << fen << std::endl;
        std::exit(2);
    }
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    if (use_nodes) {
        limits.nodes = nodes;
        limits.nodes_specified = true;
        limits.depth = 32;
    } else {
        limits.depth = depth;
    }
    const forge::SearchInfo info =
        searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
    Outcome out;
    out.score = info.score;
    out.depth = info.depth;
    out.nodes = info.nodes;
    out.move = info.best_move.is_none() ? "none" : forge::Board::move_to_uci(info.best_move);
    return out;
}

void check_span(std::string_view fen) {
    std::cout << "fen " << fen << std::endl;
    Outcome previous = search_fen(fen, 1, 0, false);
    std::cout << "depth 1 score " << previous.score << " move " << previous.move
              << " nodes " << previous.nodes << std::endl;
    bool saw_change = false;
    for (int depth = 2; depth <= 8 && !saw_change; ++depth) {
        const Outcome current = search_fen(fen, depth, 0, false);
        std::cout << "depth " << depth << " score " << current.score << " move " << current.move
                  << " nodes " << current.nodes << std::endl;
        if (current.move == previous.move) {
            previous = current;
            continue;
        }
        saw_change = true;
        std::cout << "span depth " << previous.depth << " nodes " << previous.nodes << " -> depth "
                  << current.depth << " nodes " << current.nodes << std::endl;
        if (current.nodes <= previous.nodes + 1) {
            std::cout << "FAIL span too small" << std::endl;
            ++g_failures;
            return;
        }
        const std::uint64_t step = std::max<std::uint64_t>(1, (current.nodes - previous.nodes) / 8);
        for (std::uint64_t budget = previous.nodes + 1; budget < current.nodes; budget += step) {
            const Outcome limited = search_fen(fen, 0, budget, true);
            if (limited.depth <= 0) {
                std::cout << "nodes " << budget << " depth 0 score " << limited.score << " move "
                          << limited.move << std::endl;
                if (limited.score != 0) {
                    std::cout << "FAIL unfinished search published a score" << std::endl;
                    ++g_failures;
                }
                continue;
            }
            const Outcome finished = search_fen(fen, limited.depth, 0, false);
            const bool match = limited.score == finished.score && limited.move == finished.move;
            std::cout << "nodes " << budget << " depth " << limited.depth << " score " << limited.score
                      << " move " << limited.move << " finished-score " << finished.score
                      << " finished-move " << finished.move << (match ? " PASS" : " FAIL") << std::endl;
            if (!match) ++g_failures;
        }
    }
    if (!saw_change) {
        std::cout << "FAIL no depth changed the best move" << std::endl;
        ++g_failures;
    }
}

} // namespace

int main() {
    check_span("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    check_span("8/8/8/8/4k3/8/3R4/4K3 w - - 0 1");
    if (g_failures != 0) {
        std::cout << "FAIL failures " << g_failures << std::endl;
        return 1;
    }
    std::cout << "PASS fixed-node score and move agree" << std::endl;
    return 0;
}
