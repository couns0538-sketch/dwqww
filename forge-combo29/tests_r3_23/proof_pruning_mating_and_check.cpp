// Proof for audit finding 4, kept as the r3-23 test.
// Position: kbK5/pp6/1P6/7p/8/7P/7B/1R6 w - - 0 1
// A separate legal-move mate search finds no forced mate in 6 plies or fewer.
// The shortest forced mate is 7 plies (score 32000 - 7 = 31993). With
// SoundMatePruning left off, depth 8 and 9 report the slower score 31991.
// With the option on, those depths must return 31993 and a principal
// variation that is checkmate in 7 plies.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>
#include <string>

namespace {

constexpr const char* Fen = "kbK5/pp6/1P6/7p/8/7P/7B/1R6 w - - 0 1";
constexpr int FasterMate = 31993;
constexpr int SlowerScore = 31991;

forge::SearchInfo search_depth(const forge::Board& board, int depth, forge::Searcher::TTAccess access) {
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.depth = depth;
    return searcher.search(board, limits, false, access);
}

std::string pv_text(const forge::SearchInfo& info) {
    std::string text;
    for (const forge::Move move : info.pv) {
        if (!text.empty()) text += ' ';
        text += forge::Board::move_to_uci(move);
    }
    return text;
}

bool pv_is_checkmate(const forge::Board& start, const forge::SearchInfo& info) {
    if (info.pv.empty() || info.best_move != info.pv.front()) return false;
    forge::Board board = start;
    for (const forge::Move move : info.pv) {
        if (!board.is_legal(move)) return false;
        forge::Undo undo;
        (void)board.make_move(move, undo);
    }
    return board.legal_moves().empty() && board.in_check();
}

int fail(const std::string& message) {
    std::cerr << "FAIL " << message << '\n';
    return 1;
}

} // namespace

int main() {
    if (forge::tune::SoundMatePruning) {
        return fail("SoundMatePruning must default to false");
    }

    forge::Board board;
    if (!board.set_fen(Fen)) return fail("position fen rejected");

    for (const int depth : {8, 9}) {
        forge::tune::SoundMatePruning = false;
        const forge::SearchInfo off =
            search_depth(board, depth, forge::Searcher::TTAccess::Exclusive);
        std::cout << "option off depth " << depth
                  << " best=" << forge::Board::move_to_uci(off.best_move)
                  << " score=" << off.score
                  << " pv=" << pv_text(off) << '\n';
        const bool off_mate = pv_is_checkmate(board, off);
        if (off.score != SlowerScore || off.score >= FasterMate ||
            (off_mate && static_cast<int>(off.pv.size()) <= 7)) {
            return fail("option off depth " + std::to_string(depth) +
                        " no longer shows the slower mate score");
        }

        forge::tune::SoundMatePruning = true;
        const forge::SearchInfo on =
            search_depth(board, depth, forge::Searcher::TTAccess::Exclusive);
        std::cout << "option on depth " << depth
                  << " best=" << forge::Board::move_to_uci(on.best_move)
                  << " score=" << on.score
                  << " pv=" << pv_text(on) << '\n';
        const bool mate = pv_is_checkmate(board, on);
        const int mate_score = forge::MateValue - static_cast<int>(on.pv.size());
        if (!mate || on.score != FasterMate || on.score != mate_score || on.score <= off.score ||
            !forge::is_mate_score(on.score)) {
            return fail("option on depth " + std::to_string(depth) + " missed the faster mate");
        }
    }

    forge::tune::SoundMatePruning = true;
    const forge::SearchInfo shared =
        search_depth(board, 8, forge::Searcher::TTAccess::Shared);
    std::cout << "option on depth 8 shared best=" << forge::Board::move_to_uci(shared.best_move)
              << " score=" << shared.score << " pv=" << pv_text(shared) << '\n';
    if (shared.score != FasterMate || !pv_is_checkmate(board, shared)) {
        return fail("shared-table search missed the faster mate");
    }

    forge::tune::SoundMatePruning = false;
    std::cout << "PASS sound mate pruning proof\n";
    return 0;
}
