#include "forge/board.hpp"
#include "forge/search.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <string_view>

namespace {

constexpr std::uint64_t Bench11Off = 312866;
constexpr std::uint64_t Bench13Off = 862329;
constexpr std::uint64_t Bench13On = 870398;
constexpr std::uint64_t Perft5 = 4865609;

constexpr std::array<std::string_view, 8> BenchFens{
    forge::Board::StandardStartFen,
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
};

std::uint64_t bench_nodes(int depth) {
    std::uint64_t total = 0;
    forge::Searcher searcher(16, 1);
    for (const std::string_view fen : BenchFens) {
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
    int failures = 0;
    forge::tune::AspArmLate = false;
    const std::uint64_t b11 = bench_nodes(11);
    const std::uint64_t b13 = bench_nodes(13);
    forge::Board start;
    const bool fen_ok = start.set_fen(forge::Board::StandardStartFen);
    const std::uint64_t perft = fen_ok ? start.perft(5) : 0;
    std::cout << "off bench11 " << b11 << " bench13 " << b13 << " perft5 " << perft << std::endl;
    if (b11 != Bench11Off || b13 != Bench13Off || perft != Perft5) {
        std::cerr << "FAIL option-off pins\n";
        ++failures;
    }

    forge::tune::AspArmLate = true;
    const std::uint64_t b13_on = bench_nodes(13);
    std::cout << "on bench13 " << b13_on << std::endl;
    if (b13_on != Bench13On || b13_on == Bench13Off) {
        std::cerr << "FAIL option-on bench 13\n";
        ++failures;
    }

    forge::tune::AspArmLate = false;
    const std::uint64_t b13_again = bench_nodes(13);
    std::cout << "off_again bench13 " << b13_again << std::endl;
    if (b13_again != Bench13Off) {
        std::cerr << "FAIL option-off bench 13 after reset\n";
        ++failures;
    }

    if (failures != 0) return 1;
    std::cout << "PASS followup_bench" << std::endl;
    return 0;
}
