// One Searcher is used at Threads 2, then Threads 4, then from a mated root,
// a stalemated root, and a drawn root. Counts published by the earlier
// workers must not be added into the later search.
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

forge::SearchInfo search_nodes(forge::Searcher& searcher, std::string_view fen, std::uint64_t budget) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        expect(false, "fen parses");
        return {};
    }
    forge::SearchLimits limits;
    limits.depth = 16;
    limits.nodes = budget;
    limits.nodes_specified = true;
    return searcher.search(board, limits, false);
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
    // Queen on g7, white king on g6, black to move from g8.
    constexpr std::string_view Mated = "6k1/6Q1/6K1/8/8/8/8/8 b - - 0 1";
    // Queen on f7, white king on g6, black king on h8. Not in check, no legal move.
    constexpr std::string_view Stalemate = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1";
    // Kings only.
    constexpr std::string_view Drawn = "4k3/8/8/8/8/8/8/4K3 w - - 0 1";

    forge::Board probe;
    expect(probe.set_fen(Mated) && probe.in_check() && !probe.has_legal_move(), "mated root is checkmate");
    expect(probe.set_fen(Stalemate) && !probe.in_check() && !probe.has_legal_move(), "stalemate root has no move");
    expect(probe.set_fen(Drawn) && probe.is_insufficient_material(), "drawn root is insufficient material");

    forge::Searcher reused(16, 2);
    const auto warm = search_nodes(reused, Start, 8000);
    std::cout << "threads 2 budget 8000 nodes " << warm.nodes << '\n';
    expect(warm.nodes >= 8000 && warm.nodes <= 8000 + 32, "threads 2 reaches its budget");

    reused.set_threads(4);
    const auto next = search_nodes(reused, Start, 400);
    std::cout << "threads 4 budget 400 nodes " << next.nodes << '\n';
    expect(next.nodes >= 400 && next.nodes <= 400 + 48, "threads 4 stays on the new budget");
    expect(next.nodes + 1000 < warm.nodes, "old helper counts are not added");

    const struct {
        std::string_view name;
        std::string_view fen;
    } terminals[] = {
        {"mated", Mated},
        {"stalemated", Stalemate},
        {"drawn", Drawn},
    };
    for (const auto& terminal : terminals) {
        const auto again = search_depth(reused, terminal.fen, 6);
        forge::Searcher clean(16, 4);
        const auto clean_info = search_depth(clean, terminal.fen, 6);
        std::cout << terminal.name << " reused nodes " << again.nodes << " fresh " << clean_info.nodes << '\n';
        expect(again.nodes < 64 && clean_info.nodes < 64, std::string(terminal.name) + " root does not keep old helper counts");
        expect(again.nodes + 1000 < warm.nodes, std::string(terminal.name) + " root is not the previous search");
    }

    if (failures != 0) {
        std::cout << failures << " failed\n";
        return 1;
    }
    std::cout << "PASS reused searcher\n";
    return 0;
}
