// Regression for MovePicker's deferred SEE-losing capture buffer.
// many-losing has more than 64 SEE-losing noisy moves. The lock stored those
// in std::array<Move, 64> with no bounds check, so this search aborts under
// _GLIBCXX_ASSERTIONS on the unfixed engine.
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>
#include <string>

namespace {

int failures = 0;

void check(bool okay, const std::string& message) {
    if (!okay) {
        ++failures;
        std::cerr << "FAIL: " << message << '\n';
    }
}

} // namespace

int main() {
    using namespace forge;
    constexpr const char* fen =
        "3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2 w - - 0 1";
    Board board;
    std::string error;
    const bool parsed = board.set_fen(fen, &error);
    std::cout << "many-losing accepted=" << parsed;
    if (!parsed) std::cout << " reason=" << error;
    std::cout << std::endl;
    check(parsed, std::string("many-losing parses: ") + error);
    if (!parsed) return 1;

    const auto saved_fen = board.fen();
    const auto key = board.key();
    const auto noisy = board.pseudo_legal_moves(true);
    std::size_t losing = 0;
    std::size_t legal_losing = 0;
    for (const Move move : noisy) {
        check(move.is_capture() || move.is_promotion(), "noisy generator emits captures or promotions only");
        if (!board.see_ge(move, 0)) {
            ++losing;
            if (board.is_legal(move)) ++legal_losing;
        }
    }
    std::cout << "in_check=" << board.in_check() << " noisy=" << noisy.size()
              << " see_losing=" << losing << " legal_see_losing=" << legal_losing << std::endl;
    check(!board.in_check(), "many-losing uses the main capture stages");
    check(losing > 64 && legal_losing > 64, "more SEE-losing noisy moves than the old 64-entry buffer");
    check(noisy.size() <= MoveList::Capacity, "noisy moves fit the generator capacity");
    check(board.fen() == saved_fen && board.key() == key, "SEE census preserves the board");

    SearchLimits limits;
    limits.depth = 3;
    Searcher searcher(16, 1);
    const SearchInfo result = searcher.search(board, limits);
    check(result.depth > 0 && result.nodes > 0, "depth-3 search completes an iteration");
    check(!result.best_move.is_none() && board.is_legal(result.best_move), "search returns a legal best move");
    check(!result.pv.empty() && result.pv.front() == result.best_move, "PV starts with the selected move");
    Board replay = board;
    for (const Move move : result.pv) {
        if (!replay.is_legal(move)) {
            check(false, "PV contains an illegal move");
            break;
        }
        Undo undo;
        (void)replay.make_move(move, undo);
    }
    check(board.fen() == saved_fen && board.key() == key, "search preserves the caller board");
    std::cout << "bestmove=" << Board::move_to_uci(result.best_move) << " depth=" << result.depth
              << " nodes=" << result.nodes << " pv=" << result.pv.size() << '\n';
    std::cout << "bad capture regression failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
