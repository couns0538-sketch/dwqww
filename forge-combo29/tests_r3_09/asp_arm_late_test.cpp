#include "forge/board.hpp"
#include "forge/search.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <string_view>
#include <vector>

namespace {

constexpr std::uint64_t Bench11Off = 312866;
constexpr std::uint64_t Bench13Off = 862329;
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

bool move_is_legal(const forge::Board& board, const forge::Move& move) {
    if (move.is_none()) return false;
    const forge::MoveList legal = board.legal_moves();
    for (const forge::Move candidate : legal) {
        if (candidate == move) return board.is_legal(move);
    }
    return false;
}

std::vector<forge::Board> two_hundred_positions() {
    std::vector<forge::Board> positions;
    positions.reserve(200);
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) return positions;
    std::uint64_t rng = 0xA11CE5EEDULL;
    auto step = [&]() {
        rng = rng * 0xD1B54A32D192ED03ULL + 0x94D049BB133111EBULL;
        rng ^= rng >> 29U;
        return rng;
    };
    for (int guard = 0; positions.size() < 200 && guard < 4000; ++guard) {
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty() || board.halfmove_clock() >= 80) {
            if (!board.set_fen(forge::Board::StandardStartFen)) break;
            continue;
        }
        positions.push_back(board);
        const forge::Move chosen = legal[static_cast<std::size_t>(step() % legal.size())];
        forge::Undo undo;
        if (!board.make_move(chosen, undo)) {
            if (!board.set_fen(forge::Board::StandardStartFen)) break;
        }
    }
    return positions;
}

int search_two_hundred() {
    const std::vector<forge::Board> positions = two_hundred_positions();
    if (positions.size() != 200) {
        std::cerr << "FAIL built " << positions.size() << " positions\n";
        return 1;
    }
    forge::Searcher searcher(16, 1);
    int illegal = 0;
    for (std::size_t i = 0; i < positions.size(); ++i) {
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = 10;
        const forge::SearchInfo info =
            searcher.search(positions[i], limits, false, forge::Searcher::TTAccess::Exclusive);
        if (!move_is_legal(positions[i], info.best_move)) {
            std::cerr << "FAIL illegal move index " << i << " move "
                      << forge::Board::move_to_uci(info.best_move) << std::endl;
            ++illegal;
            break;
        }
        if ((i + 1) % 25 == 0) {
            std::cout << "depth10 progress " << (i + 1) << std::endl;
        }
    }
    std::cout << "depth10 searches " << positions.size() << " illegal " << illegal << std::endl;
    return illegal;
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
    std::cout << "defaults bench11 " << b11 << " bench13 " << b13 << " perft5 " << perft << std::endl;
    if (b11 != Bench11Off || b13 != Bench13Off || perft != Perft5) {
        std::cerr << "FAIL default bench or perft\n";
        ++failures;
    }

    forge::tune::AspArmLate = true;
    const std::uint64_t b13_on = bench_nodes(13);
    std::cout << "asparmlate bench13 " << b13_on << std::endl;
    if (b13_on == 0 || b13_on == Bench13Off) {
        std::cerr << "FAIL bench 13 did not change with AspArmLate on\n";
        ++failures;
    }

    failures += search_two_hundred();

    // Short clock searches exercise the soft-time gate with the option on.
    // Only legality is checked; the clock makes node totals vary.
    {
        forge::Searcher searcher(16, 1);
        const std::vector<forge::Board> positions = two_hundred_positions();
        constexpr int samples = 20;
        int illegal = 0;
        for (int i = 0; i < samples; ++i) {
            searcher.clear();
            forge::SearchLimits limits;
            limits.time_ms = 40;
            limits.increment_ms = 0;
            const forge::SearchInfo info = searcher.search(
                positions[static_cast<std::size_t>(i)], limits, false,
                forge::Searcher::TTAccess::Exclusive);
            if (!move_is_legal(positions[static_cast<std::size_t>(i)], info.best_move)) {
                std::cerr << "FAIL timed illegal sample " << i << " move "
                          << forge::Board::move_to_uci(info.best_move) << std::endl;
                ++illegal;
                break;
            }
        }
        std::cout << "timed samples " << samples << " illegal " << illegal << std::endl;
        failures += illegal;
    }

    forge::tune::AspArmLate = false;
    const std::uint64_t b13_again = bench_nodes(13);
    std::cout << "defaults_after bench13 " << b13_again << std::endl;
    if (b13_again != Bench13Off) {
        std::cerr << "FAIL bench 13 stayed changed after AspArmLate off\n";
        ++failures;
    }

    if (failures != 0) {
        std::cerr << "FAIL asparmlate_test failures " << failures << '\n';
        return 1;
    }
    std::cout << "PASS asparmlate_test" << std::endl;
    return 0;
}
