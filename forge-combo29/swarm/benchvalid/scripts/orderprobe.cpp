// Variants of the bench loop used to answer "is each position independent?".
//   mode=forward   : bench's own order, bench_searcher.clear() before each position
//   mode=reverse   : the same eight FENs in reverse order, clear() before each
//   mode=noclear   : forward order, clear() REMOVED (the control that proves clear() does work)
//   mode=fresh     : a brand-new Searcher per position (the strongest independence available)
// Prints one line per position plus the total, so the totals of every mode are comparable
// to the real pin.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>
#include <string_view>

#include "forge/board.hpp"
#include "forge/search.hpp"

namespace {
constexpr std::array<std::string_view, 8> Fens{
    forge::Board::StandardStartFen,
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
};
}  // namespace

int main(int argc, char** argv) {
    const int depth = argc > 1 ? std::stoi(argv[1]) : 13;
    const std::string mode = argc > 2 ? argv[2] : "forward";

    std::array<std::size_t, 8> order{0, 1, 2, 3, 4, 5, 6, 7};
    if (mode == "reverse") std::reverse(order.begin(), order.end());

    auto searcher = std::make_unique<forge::Searcher>(16);
    std::uint64_t total = 0;
    for (const std::size_t idx : order) {
        forge::Board board;
        if (!board.set_fen(Fens[idx])) {
            std::cout << "REFUSED " << idx << std::endl;
            continue;
        }
        forge::SearchLimits limits;
        limits.depth = depth;
        if (mode == "noclear") {
            // deliberately nothing
        } else if (mode == "fresh") {
            searcher = std::make_unique<forge::Searcher>(16);
        } else {
            searcher->clear();
        }
        const forge::SearchInfo info =
            searcher->search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
        total += info.nodes;
        std::cout << idx << '\t' << info.nodes << '\t' << info.score << '\t'
                  << forge::Board::move_to_uci(info.best_move) << std::endl;
    }
    std::cout << "TOTAL\t" << total << std::endl;
    return 0;
}
