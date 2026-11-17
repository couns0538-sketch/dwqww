// 100 searches of `go nodes 20000` with Threads 4.
// The count is SearchInfo::nodes, the total `go nodes` returns.
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <iostream>
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

}  // namespace

int main() {
    constexpr std::string_view Start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    constexpr std::uint64_t budget = 20000;
    constexpr int searches = 100;
    std::uint64_t largest = 0;
    std::uint64_t smallest = ~std::uint64_t{0};
    int largest_index = -1;

    for (int i = 0; i < searches; ++i) {
        forge::Board board;
        if (!board.set_fen(Start)) {
            std::cout << "FAIL start fen\n";
            return 1;
        }
        forge::Searcher searcher(32, 4);
        forge::SearchLimits limits;
        limits.nodes = budget;
        limits.nodes_specified = true;
        limits.depth = 64;
        const forge::SearchInfo info = searcher.search(board, limits, false);
        const std::uint64_t nodes = info.nodes;
        if (nodes < smallest) smallest = nodes;
        if (nodes >= largest) {
            largest = nodes;
            largest_index = i;
        }
        std::cout << "search " << i << " nodes " << nodes << '\n';
        if (nodes < budget) {
            std::cout << "FAIL search " << i << " stopped short at " << nodes << '\n';
            ++failures;
        }
    }

    const std::uint64_t overshoot = largest >= budget ? largest - budget : 0;
    std::cout << "searches " << searches << '\n';
    std::cout << "budget " << budget << '\n';
    std::cout << "smallest " << smallest << '\n';
    std::cout << "largest " << largest << '\n';
    std::cout << "largest_index " << largest_index << '\n';
    std::cout << "largest_overshoot " << overshoot << '\n';
    expect(failures == 0, "every search reached the budget");
    if (failures != 0) {
        std::cout << failures << " failed\n";
        return 1;
    }
    std::cout << "PASS nodes 20000\n";
    return 0;
}
