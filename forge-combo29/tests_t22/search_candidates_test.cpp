#include "forge/board.hpp"
#include "forge/search.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <string_view>
#include <vector>

namespace {

constexpr std::uint64_t ExpectedBench11 = 312866;
constexpr std::uint64_t ExpectedBench13 = 862329;
constexpr std::uint64_t ExpectedPerft5 = 4865609;

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

constexpr std::array<std::string_view, 25> SeedFens{
    forge::Board::StandardStartFen,
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "rnbqkb1r/pp2pppp/2p2n2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 0 4",
    "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 7",
    "2rq1rk1/pb1nbppp/1p2pn2/2pp4/3P4/1PN1PN2/PB1NBPPP/2RQ1RK1 w - - 0 10",
    "r2qkb1r/pp2pppp/2n2n2/3p1b2/3P1B2/2N2N2/PP2PPPP/R2QKB1R w KQkq - 4 6",
    "8/5pk1/4p1p1/3pP1P1/3P4/5K2/8/8 w - - 0 1",
    "8/8/2k5/4b3/8/3N4/4K3/8 w - - 0 1",
    "4r1k1/p1p2ppp/1p6/3p4/3P4/1P2R3/P1P2PPP/6K1 w - - 0 1",
    "r4rk1/pp1b1ppp/2n1p3/q2pP3/3P4/P1PB1N2/2Q2PPP/R3K2R w KQ - 1 13",
    "r1b1k2r/pp1n1ppp/2pbpn2/q7/1b1PP3/2NB1N2/PPQ2PPP/R1B1K2R w KQkq - 4 8",
    "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 3 8",
    "3r2k1/pp3ppp/2n1b3/8/3p4/1B3N2/PP3PPP/3R2K1 w - - 0 1",
    "2kr3r/ppp2ppp/2n1b3/3q4/3P4/2PB1N2/P4PPP/R2Q1RK1 w - - 0 12",
    "8/1p4k1/p1p2pp1/2P5/1P1R4/P5P1/5PK1/3r4 w - - 0 1",
    "r1b2rk1/ppq1bppp/2n1pn2/2pp4/3P4/1PN1PN2/PB1PBPPP/R2Q1RK1 w - - 4 9",
};

std::uint64_t run_bench(int depth) {
    std::uint64_t total_nodes = 0;
    forge::Searcher searcher(16, 1);
    for (const std::string_view fen : BenchFens) {
        forge::Board board;
        if (!board.set_fen(fen)) return 0;
        forge::SearchLimits limits;
        limits.depth = depth;
        searcher.clear();
        total_nodes += searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive).nodes;
    }
    return total_nodes;
}

std::vector<forge::Board> build_200_positions() {
    std::vector<forge::Board> positions;
    positions.reserve(200);
    std::uint64_t rng = 0x9E3779B97F4A7C15ULL;
    auto next_u64 = [&]() {
        rng ^= rng >> 12U;
        rng ^= rng << 25U;
        rng ^= rng >> 27U;
        return rng * 0x2545F4914F6CDD1DULL;
    };

    for (std::size_t s = 0; s < SeedFens.size() && positions.size() < 200; ++s) {
        forge::Board board;
        if (!board.set_fen(SeedFens[s])) continue;
        for (int step = 0; step < 8 && positions.size() < 200; ++step) {
            const forge::MoveList legal = board.legal_moves();
            if (legal.empty()) {
                (void)board.set_fen(SeedFens[(s + 1) % SeedFens.size()]);
            }
            if (!board.legal_moves().empty()) {
                positions.push_back(board);
            }
            const forge::MoveList step_moves = board.legal_moves();
            if (step_moves.empty()) break;
            const forge::Move chosen = step_moves[static_cast<std::size_t>(next_u64() % step_moves.size())];
            forge::Undo undo;
            (void)board.make_move(chosen, undo);
        }
    }
    return positions;
}

void reset_candidates() {
    forge::tune::ContHist4PlyRead = false;
    forge::tune::NonPawnCorrection = false;
    forge::tune::LmrDeeperShallower = false;
}

struct Candidate {
    const char* name;
    bool* flag;
};

int test_candidate(const Candidate& cand, const std::vector<forge::Board>& positions) {
    int failures = 0;
    reset_candidates();
    *cand.flag = true;

    const std::uint64_t bench13_on = run_bench(13);
    std::cout << "candidate " << cand.name << " bench13_on " << bench13_on
              << " bench13_off " << ExpectedBench13 << '\n';
    if (bench13_on == 0 || bench13_on == ExpectedBench13) {
        std::cerr << "FAIL " << cand.name << ": bench 13 did not change when enabled\n";
        ++failures;
    }

    forge::Searcher searcher(16, 1);
    std::uint64_t total_nodes = 0;
    for (std::size_t i = 0; i < positions.size(); ++i) {
        // Clear every 25 searches so cross-move history and correction tables
        // accumulate within mini-games as well as starting clean across games.
        if (i % 25 == 0) searcher.clear();
        const forge::Board& pos = positions[i];
        forge::SearchLimits limits;
        limits.depth = 10;
        const forge::SearchInfo info =
            searcher.search(pos, limits, false, forge::Searcher::TTAccess::Exclusive);
        total_nodes += info.nodes;

        const forge::MoveList legal = pos.legal_moves();
        bool found = false;
        for (const forge::Move m : legal) {
            if (m == info.best_move) {
                found = true;
                break;
            }
        }
        if (info.best_move.is_none() || !pos.is_legal(info.best_move) || !found) {
            std::cerr << "FAIL " << cand.name << ": illegal best_move at position " << i
                      << " (" << forge::Board::move_to_uci(info.best_move) << ")\n";
            ++failures;
            break;
        }
    }
    std::cout << "candidate " << cand.name << " searches " << positions.size()
              << " depth 10 legal_ok " << (failures == 0 ? 1 : 0)
              << " total_nodes " << total_nodes << '\n';

    reset_candidates();
    return failures;
}

} // namespace

int main() {
    int failures = 0;
    reset_candidates();

    const std::uint64_t b11 = run_bench(11);
    const std::uint64_t b13 = run_bench(13);
    forge::Board start;
    (void)start.set_fen(forge::Board::StandardStartFen);
    const std::uint64_t p5 = start.perft(5);

    std::cout << "defaults bench11 " << b11 << " bench13 " << b13 << " perft5 " << p5 << '\n';
    if (b11 != ExpectedBench11 || b13 != ExpectedBench13 || p5 != ExpectedPerft5) {
        std::cerr << "FAIL baseline parity mismatch with options off\n";
        ++failures;
    }

    const std::vector<forge::Board> positions = build_200_positions();
    if (positions.size() != 200) {
        std::cerr << "FAIL expected 200 test positions, built " << positions.size() << '\n';
        return 1;
    }

    const std::array<Candidate, 3> candidates{{
        {"ContHist4PlyRead", &forge::tune::ContHist4PlyRead},
        {"NonPawnCorrection", &forge::tune::NonPawnCorrection},
        {"LmrDeeperShallower", &forge::tune::LmrDeeperShallower},
    }};

    for (const Candidate& cand : candidates) {
        failures += test_candidate(cand, positions);
    }

    const std::uint64_t b13_after = run_bench(13);
    std::cout << "defaults_after bench13 " << b13_after << '\n';
    if (b13_after != ExpectedBench13) {
        std::cerr << "FAIL bench 13 changed after resetting options to false\n";
        ++failures;
    }

    if (failures != 0) {
        std::cerr << "FAIL total failures: " << failures << '\n';
        return 1;
    }
    std::cout << "PASS t22 search_candidates_test\n";
    return 0;
}
