// A Searcher is used at Threads 2, then Threads 4, then from a mated root,
// a stalemated root, and a drawn root. Helper counts published by an earlier
// search must not be added into the next search.
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdint>
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

forge::SearchInfo search_depth(forge::Searcher& searcher, std::string_view fen, int depth) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        expect(false, "fen parses");
        return {};
    }
    forge::SearchLimits limits;
    limits.depth = depth;
    return searcher.search(board, limits, false);
}

} // namespace

int main() {
    constexpr std::string_view Start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    constexpr std::string_view Mated = "6k1/5Q2/6K1/8/8/8/8/8 b - - 0 1";
    constexpr std::string_view Stalemate = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1";
    constexpr std::string_view Drawn = "8/8/8/8/8/8/4k3/4K3 w - - 0 1";

    forge::Board probe;
    expect(probe.set_fen(Mated) && probe.in_check() && !probe.has_legal_move(), "mated root is checkmate");
    expect(probe.set_fen(Stalemate) && !probe.in_check() && !probe.has_legal_move(), "stalemate root has no move");
    expect(probe.set_fen(Drawn) && probe.is_insufficient_material(), "drawn root is insufficient material");

    forge::Searcher fresh2(16, 2);
    const auto fresh2_info = search_depth(fresh2, Start, 6);
    std::cout << "fresh threads 2 nodes " << fresh2_info.nodes << '\n';
    expect(fresh2_info.nodes > 0, "threads 2 searches");

    forge::Searcher reused(16, 2);
    const auto first = search_depth(reused, Start, 6);
    std::cout << "reused threads 2 nodes " << first.nodes << '\n';
    expect(first.nodes == fresh2_info.nodes, "threads 2 matches a fresh searcher");

    reused.set_threads(4);
    const auto second = search_depth(reused, Start, 6);
    forge::Searcher fresh4(16, 4);
    const auto fresh4_info = search_depth(fresh4, Start, 6);
    std::cout << "reused threads 4 nodes " << second.nodes << " fresh " << fresh4_info.nodes << '\n';
    expect(second.nodes == fresh4_info.nodes, "threads 4 matches a fresh searcher");
    expect(second.nodes < first.nodes + fresh4_info.nodes, "old helper counts are not added");

    // A large search leaves a count in every worker. The next search must
    // start from zero, including workers that are not the main thread.
    forge::SearchLimits warm;
    warm.depth = 8;
    forge::Board start_board;
    expect(start_board.set_fen(Start), "start fen");
    const auto warmed = reused.search(start_board, warm, false);
    std::cout << "warm depth 8 nodes " << warmed.nodes << '\n';
    expect(warmed.nodes > second.nodes, "warm search counted nodes");

    const struct {
        std::string_view name;
        std::string_view fen;
    } terminals[] = {
        {"mated", Mated},
        {"stalemated", Stalemate},
        {"drawn", Drawn},
    };
    for (const auto& terminal : terminals) {
        const auto again = search_depth(reused, terminal.fen, 4);
        forge::Searcher clean(16, 4);
        const auto clean_info = search_depth(clean, terminal.fen, 4);
        std::cout << terminal.name << " reused nodes " << again.nodes << " fresh " << clean_info.nodes << '\n';
        expect(again.nodes == clean_info.nodes, std::string(terminal.name) + " root ignores old helper counts");
        expect(again.nodes < warmed.nodes, std::string(terminal.name) + " root is not the previous search");
    }

    if (failures != 0) {
        std::cout << failures << " failed\n";
        return 1;
    }
    std::cout << "PASS reused searcher\n";
    return 0;
}
