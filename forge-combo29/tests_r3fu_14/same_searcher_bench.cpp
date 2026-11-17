// One Searcher, DrawJitter 0 then 8 then 0. The last pass is bench depth 13.
// The setter clears the hash when the value changes, so the last pass is the
// default signature even though this object already searched at 8.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <array>
#include <iostream>
#include <string_view>

namespace {

std::uint64_t bench_depth(forge::Searcher& searcher, int depth) {
    constexpr std::array<std::string_view, 8> fens{
        forge::Board::StandardStartFen,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    };
    std::uint64_t total = 0;
    for (const std::string_view fen : fens) {
        forge::Board board;
        if (!board.set_fen(fen)) return 0;
        forge::SearchLimits limits;
        limits.depth = depth;
        searcher.clear();
        total += searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive).nodes;
    }
    return total;
}

} // namespace

int main() {
    forge::Searcher searcher(16);
    if (searcher.threads() != 1) {
        std::cout << "FAIL threads " << searcher.threads() << std::endl;
        return 1;
    }

    forge::set_draw_jitter(0, searcher);
    const std::uint64_t at_zero = bench_depth(searcher, 13);
    std::cout << "bench 13 after 0 " << at_zero << " hashfull " << searcher.hashfull_permille() << std::endl;
    if (at_zero != 862329) {
        std::cout << "FAIL first pass" << std::endl;
        return 1;
    }
    if (searcher.hashfull_permille() == 0) {
        std::cout << "FAIL hash was empty after the first pass" << std::endl;
        return 1;
    }

    forge::set_draw_jitter(8, searcher);
    if (searcher.hashfull_permille() != 0) {
        std::cout << "FAIL hash survived the change to 8" << std::endl;
        return 1;
    }
    const std::uint64_t at_eight = bench_depth(searcher, 13);
    std::cout << "bench 13 after 8 " << at_eight << " hashfull " << searcher.hashfull_permille() << std::endl;
    if (at_eight == 862329 || searcher.hashfull_permille() == 0) {
        std::cout << "FAIL value 8 did not search a filled table" << std::endl;
        return 1;
    }

    forge::set_draw_jitter(0, searcher);
    const int hash_after = searcher.hashfull_permille();
    std::cout << "hashfull after return to 0 " << hash_after << std::endl;
    if (hash_after != 0) {
        std::cout << "FAIL hash survived the return to 0" << std::endl;
        return 1;
    }
    const std::uint64_t at_zero_again = bench_depth(searcher, 13);
    std::cout << "bench 13 after 0 again " << at_zero_again << std::endl;
    if (at_zero_again != 862329) {
        std::cout << "FAIL restored pass" << std::endl;
        return 1;
    }
    std::cout << "OK bench 13 " << at_zero_again << std::endl;
    return 0;
}
