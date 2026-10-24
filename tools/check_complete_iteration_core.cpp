// Original public-API check of the complete-iteration result tuple.
#include "forge/search.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace forge;
constexpr const char* StartFen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
const std::vector<std::string> Restricted{"e2e4", "h2h3", "c2c4", "d2d4"};

SearchInfo run(int depth, bool limited, std::uint64_t nodes, bool restricted) {
    Board board;
    if (!board.set_fen(StartFen)) throw std::runtime_error("initial FEN rejected");
    Searcher owner(16, 1);
    SearchLimits limits;
    limits.depth = depth;
    limits.nodes_specified = limited;
    limits.nodes = nodes;
    limits.search_moves_specified = restricted;
    if (restricted) {
        for (const auto& text : Restricted) {
            const auto move = board.parse_uci(text);
            if (!move) throw std::runtime_error("restricted root move rejected");
            limits.search_moves.push_back(*move);
        }
    }
    return owner.search(board, limits, false);
}

void describe(const std::string& label, const SearchInfo& info) {
    std::cout << "CASE " << label << " depth=" << info.depth << " score=" << info.score
              << " nodes=" << info.nodes << " best=" << Board::move_to_uci(info.best_move)
              << " ponder=" << (info.ponder_move.is_none() ? "none" : Board::move_to_uci(info.ponder_move))
              << " pv=";
    for (const auto& move : info.pv) std::cout << Board::move_to_uci(move) << ' ';
    std::cout << '\n';
}

bool same_tuple(const SearchInfo& left, const SearchInfo& right) {
    return left.depth == right.depth && left.score == right.score && left.pv == right.pv &&
           left.best_move == right.best_move && left.ponder_move == right.ponder_move;
}

bool legal_pv(const SearchInfo& info) {
    Board board;
    if (!board.set_fen(StartFen)) return false;
    for (const auto move : info.pv) {
        if (!board.is_legal(move)) return false;
        Undo undo;
        if (!board.make_move(move, undo)) return false;
    }
    return true;
}
} // namespace

int main() {
    using namespace forge;
    int assertions = 0;
    int failures = 0;
    const auto check = [&](bool okay, const std::string& label) {
        ++assertions;
        if (!okay) {
            ++failures;
            std::cerr << "FAIL " << label << '\n';
        }
    };
    for (const bool restricted : {false, true}) {
        const std::string prefix = restricted ? "restricted" : "plain";
        const int complete_depth = restricted ? 7 : 3;
        const std::uint64_t stop_nodes = restricted ? 1800 : 600;
        const auto completed = run(complete_depth, false, 0, restricted);
        const auto interrupted = run(64, true, stop_nodes, restricted);
        describe(prefix + "-completed", completed);
        describe(prefix + "-interrupted", interrupted);
        check(same_tuple(completed, interrupted), prefix + " completed tuple preserved on node stop");
        check(interrupted.nodes == stop_nodes, prefix + " total nodes includes unfinished iteration");
        check(legal_pv(interrupted), prefix + " retained PV is legal");
        check(!interrupted.pv.empty() && interrupted.best_move == interrupted.pv.front(),
              prefix + " best move agrees with retained PV");
        check(interrupted.pv.size() > 1 && interrupted.ponder_move == interrupted.pv[1],
              prefix + " ponder agrees with retained PV");

        const auto zero = run(64, true, 0, restricted);
        const auto first = run(64, true, 2, restricted);
        describe(prefix + "-zero-fallback", zero);
        describe(prefix + "-first-interrupted", first);
        Board root;
        check(root.set_fen(StartFen), prefix + " root parses");
        check(first.depth == 0 && first.score == 0 && first.pv.empty() && first.ponder_move.is_none(),
              prefix + " first interrupted result has no completed score/PV");
        check(first.nodes == 2, prefix + " first interrupted total nodes retained");
        check(first.best_move == zero.best_move && root.is_legal(first.best_move),
              prefix + " first interrupted move uses existing legal fallback");
        if (restricted) {
            const auto text = Board::move_to_uci(first.best_move);
            check(std::find(Restricted.begin(), Restricted.end(), text) != Restricted.end(),
                  "restricted fallback belongs to allowed roots");
        }
    }
    for (const int depth : {4, 10}) describe("normal-depth" + std::to_string(depth), run(depth, false, 0, false));
    std::cout << "Complete iteration core: assertions " << assertions << " failures " << failures << '\n';
    return failures ? 1 : 0;
}
