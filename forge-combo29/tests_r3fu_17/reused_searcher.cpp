// One Searcher. Normal searches at Threads 2, then Threads 4, then a mated
// root, a stalemated root, and a drawn root. A terminal root must not report
// the node counts those helper threads published on the earlier searches.
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>
#include <string>
#include <string_view>

namespace {

int failures = 0;

void expect(bool ok, std::string_view name) {
    if (ok) {
        std::cout << "ok " << name << '\n';
        return;
    }
    std::cout << "FAIL " << name << '\n';
    ++failures;
}

forge::Board board_from(std::string_view fen) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        std::cout << "FAIL bad fen " << fen << '\n';
        ++failures;
    }
    return board;
}

}  // namespace

int main() {
    constexpr std::string_view Start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    constexpr std::string_view Mated = "7k/6Q1/5K2/8/8/8/8/8 b - - 0 1";
    constexpr std::string_view Stalemate = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1";
    constexpr std::string_view Drawn = "8/8/8/8/4k3/8/3R4/4K3 w - - 100 1";

    forge::Searcher searcher(32, 2);
    forge::SearchLimits limits;
    limits.depth = 8;

    const forge::Board start = board_from(Start);
    const forge::SearchInfo two = searcher.search(start, limits, false);
    std::cout << "threads 2 nodes " << two.nodes << " move " << forge::Board::move_to_uci(two.best_move) << '\n';
    expect(searcher.threads() == 2, "searcher has 2 threads");
    expect(two.nodes > 1000, "threads 2 search counted nodes");

    searcher.set_threads(4);
    const forge::SearchInfo four = searcher.search(start, limits, false);
    std::cout << "threads 4 nodes " << four.nodes << " move " << forge::Board::move_to_uci(four.best_move) << '\n';
    expect(searcher.threads() == 4, "searcher has 4 threads");
    expect(four.nodes > 1000, "threads 4 search counted nodes");

    const forge::Board mated = board_from(Mated);
    expect(mated.legal_moves().empty() && mated.in_check(), "mated root has no legal move");
    const forge::SearchInfo mate_info = searcher.search(mated, limits, false);
    std::cout << "mated nodes " << mate_info.nodes << " score " << mate_info.score << '\n';
    expect(mate_info.nodes == 0, "mated root does not count old helper nodes");
    expect(mate_info.score == -forge::MateValue, "mated root scores mate");

    const forge::Board stale = board_from(Stalemate);
    expect(stale.legal_moves().empty() && !stale.in_check(), "stalemated root has no legal move");
    const forge::SearchInfo stale_info = searcher.search(stale, limits, false);
    std::cout << "stalemate nodes " << stale_info.nodes << " score " << stale_info.score << '\n';
    expect(stale_info.nodes == 0, "stalemated root does not count old helper nodes");
    expect(stale_info.score == 0, "stalemated root scores a draw");

    const forge::Board drawn = board_from(Drawn);
    expect(!drawn.legal_moves().empty() && drawn.halfmove_clock() >= 100, "drawn root is a fifty-move position");
    const forge::SearchInfo drawn_info = searcher.search(drawn, limits, false);
    std::cout << "drawn nodes " << drawn_info.nodes << " score " << drawn_info.score << '\n';
    expect(drawn_info.nodes == 0, "drawn root does not count old helper nodes");
    expect(drawn_info.score == 0, "drawn root scores a draw");

    expect(searcher.threads() == 4, "terminal searches kept the same searcher");
    if (failures != 0) {
        std::cout << failures << " failed\n";
        return 1;
    }
    std::cout << "PASS reused searcher\n";
    return 0;
}
