#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <string_view>

// `go nodes` used to keep the previous iteration's score and take a best move
// from the iteration the limit cut off. Every node budget must report the
// score and the move of the last iteration that actually finished.

namespace {

int g_failures = 0;
int g_checks = 0;

struct Outcome {
    int score = 0;
    int depth = 0;
    std::uint64_t nodes = 0;
    std::string move;
    bool pv_matches = false;
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
    const bool pv_move = !info.pv.empty() && info.pv.front() == info.best_move;
    const bool ponder = info.pv.size() <= 1 ? info.ponder_move.is_none() : info.ponder_move == info.pv[1];
    out.pv_matches = info.depth <= 0 || (pv_move && ponder);
    return out;
}

void check_fen(std::string_view fen, int max_depth) {
    std::cout << "fen " << fen << std::endl;
    Outcome previous = search_fen(fen, 1, 0, false);
    std::cout << "depth 1 score " << previous.score << " move " << previous.move
              << " nodes " << previous.nodes << std::endl;
    const Outcome early = search_fen(fen, 0, 1, true);
    std::cout << "nodes 1 depth " << early.depth << " score " << early.score << " move " << early.move
              << std::endl;
    if (early.depth != 0 || early.score != 0) {
        std::cout << "FAIL node budget 1 published a score" << std::endl;
        ++g_failures;
    }
    for (int depth = 2; depth <= max_depth; ++depth) {
        const Outcome current = search_fen(fen, depth, 0, false);
        std::cout << "depth " << depth << " score " << current.score << " move " << current.move
                  << " nodes " << current.nodes << std::endl;
        if (current.nodes <= previous.nodes + 1) {
            previous = current;
            continue;
        }
        const std::uint64_t step = std::max<std::uint64_t>(1, (current.nodes - previous.nodes) / 8);
        for (std::uint64_t budget = previous.nodes + 1; budget < current.nodes; budget += step) {
            const Outcome limited = search_fen(fen, 0, budget, true);
            ++g_checks;
            if (limited.depth <= 0) {
                if (limited.score != 0) {
                    std::cout << "nodes " << budget << " depth 0 score " << limited.score
                              << " FAIL" << std::endl;
                    ++g_failures;
                }
                continue;
            }
            const Outcome finished = search_fen(fen, limited.depth, 0, false);
            const bool match = limited.score == finished.score && limited.move == finished.move &&
                               limited.pv_matches;
            if (!match) {
                std::cout << "nodes " << budget << " depth " << limited.depth << " score "
                          << limited.score << " move " << limited.move << " finished-score "
                          << finished.score << " finished-move " << finished.move << " FAIL"
                          << std::endl;
                ++g_failures;
            }
        }
        previous = current;
    }
}

} // namespace

int main() {
    check_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 6);
    check_fen("8/8/8/8/4k3/8/3R4/4K3 w - - 0 1", 6);
    check_fen("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3", 6);
    check_fen("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 6);
    if (g_failures != 0) {
        std::cout << "FAIL failures " << g_failures << " checks " << g_checks << std::endl;
        return 1;
    }
    std::cout << "PASS fixed-node score and move agree checks " << g_checks << std::endl;
    return 0;
}
