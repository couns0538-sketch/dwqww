// Finding 7: SingularDepth = 2 used to set singular_depth = (depth - 1) / 2 = 0,
// and search() handed that call to qsearch(), which ignores excluded_move.
// Also checks the lock pins and 200 depth-10 searches (every reported move legal).
// Any failed check returns non-zero.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
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

bool move_in_legal(const forge::Board& board, forge::Move move) {
    if (move.is_none() || !board.is_legal(move)) return false;
    const forge::MoveList legal = board.legal_moves();
    for (const forge::Move candidate : legal) {
        if (candidate == move) return true;
    }
    return false;
}

bool line_legal(forge::Board board, const std::vector<forge::Move>& line) {
    for (const forge::Move move : line) {
        if (!move_in_legal(board, move)) return false;
        forge::Undo undo;
        (void)board.make_move(move, undo);
    }
    return true;
}

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

// Audit proof position. White to move; after 1.g2g3 Black's only non-losing move is Qxa4.
// A depth-1 lower bound on that move used to satisfy the singular window inside qsearch.
int test_singular_depth2() {
    forge::Board root;
    if (!root.set_fen("6k1/5ppp/8/q7/Q7/8/6PP/6K1 w - - 0 1")) {
        std::cerr << "FAIL singular: could not parse proof fen\n";
        return 1;
    }
    const std::optional<forge::Move> h2h3 = root.parse_uci("h2h3");
    const std::optional<forge::Move> g2g3 = root.parse_uci("g2g3");
    if (!h2h3 || !g2g3 || !move_in_legal(root, *h2h3) || !move_in_legal(root, *g2g3)) {
        std::cerr << "FAIL singular: proof root moves are not legal\n";
        return 1;
    }

    forge::Board child = root;
    forge::Undo undo;
    (void)child.make_move(*g2g3, undo);
    const std::optional<forge::Move> a5a4 = child.parse_uci("a5a4");
    if (!a5a4 || !move_in_legal(child, *a5a4)) {
        std::cerr << "FAIL singular: a5a4 is not legal in the child\n";
        return 1;
    }

    const int saved = forge::tune::SingularDepth;
    auto run_with = [&](int singular_depth_option) {
        forge::tune::SingularDepth = singular_depth_option;
        forge::Searcher searcher(16, 1);
        auto& tt = searcher.transposition_table();
        tt.store(tt.probe(child.key()), child.key(), 1850, 0, *a5a4, 1, forge::BoundLower, false,
                 child.halfmove_clock());
        forge::SearchLimits limits;
        limits.depth = 3;
        limits.search_moves_specified = true;
        limits.search_moves = {*h2h3, *g2g3};
        const forge::SearchInfo info = searcher.search(root, limits, false);
        return std::pair<forge::TTEntry, forge::SearchInfo>{tt.probe(child.key()).entry, info};
    };

    const auto def = run_with(7);
    const auto low = run_with(2);
    forge::tune::SingularDepth = saved;

    const forge::TTEntry& e_def = def.first;
    const forge::TTEntry& e_low = low.first;
    std::cout << "SingularDepth=7 child TT depth=" << static_cast<int>(e_def.depth)
              << " score=" << e_def.score << '\n';
    std::cout << "SingularDepth=2 child TT depth=" << static_cast<int>(e_low.depth)
              << " score=" << e_low.score << '\n';

    int failures = 0;
    if (e_def.depth < 2) {
        std::cerr << "FAIL singular: default SingularDepth did not store a depth-2 child entry\n";
        ++failures;
    }
    // The bug leaves the seeded depth-1 score 1850 in place (qsearch cutoff / false multi-cut).
    if (e_low.depth < 2 || (e_low.depth == 1 && e_low.score == 1850)) {
        std::cerr << "FAIL singular: SingularDepth=2 still drops into qsearch "
                     "(child TT depth="
                  << static_cast<int>(e_low.depth) << " score=" << e_low.score << ")\n";
        ++failures;
    }
    for (const auto& info : {def.second, low.second}) {
        if (!move_in_legal(root, info.best_move) || !line_legal(root, info.pv)) {
            std::cerr << "FAIL singular: reported move is illegal ("
                      << forge::Board::move_to_uci(info.best_move) << ")\n";
            ++failures;
        }
    }
    return failures;
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
            if (board.legal_moves().empty()) {
                (void)board.set_fen(SeedFens[(s + 1) % SeedFens.size()]);
            }
            if (!board.legal_moves().empty()) positions.push_back(board);
            const forge::MoveList step_moves = board.legal_moves();
            if (step_moves.empty()) break;
            const forge::Move chosen = step_moves[static_cast<std::size_t>(next_u64() % step_moves.size())];
            forge::Undo undo;
            (void)board.make_move(chosen, undo);
        }
    }
    return positions;
}

int test_depth10_legal() {
    const std::vector<forge::Board> positions = build_200_positions();
    if (positions.size() != 200) {
        std::cerr << "FAIL expected 200 positions, built " << positions.size() << '\n';
        return 1;
    }

    forge::Searcher searcher(16, 1);
    int failures = 0;
    for (std::size_t i = 0; i < positions.size(); ++i) {
        if (i % 25 == 0) searcher.clear();
        const forge::Board& pos = positions[i];
        forge::SearchLimits limits;
        limits.depth = 10;
        const forge::SearchInfo info = searcher.search(pos, limits, false, forge::Searcher::TTAccess::Exclusive);
        if (info.pv.empty() || info.pv.front() != info.best_move || !move_in_legal(pos, info.best_move) ||
            !line_legal(pos, info.pv)) {
            std::cerr << "FAIL depth-10 search " << i << " illegal move "
                      << forge::Board::move_to_uci(info.best_move) << " fen " << pos.fen() << '\n';
            ++failures;
        }
    }
    if (failures != 0) {
        std::cerr << "FAIL " << failures << " of 200 depth-10 searches reported an illegal move\n";
        return failures;
    }
    std::cout << "PASS 200 depth-10 searches, every reported move legal\n";
    return 0;
}

int test_pins() {
    if (forge::tune::SingularDepth != 7) {
        std::cerr << "FAIL pins: SingularDepth is " << forge::tune::SingularDepth << ", expected the default 7\n";
        return 1;
    }
    const std::uint64_t bench11 = run_bench(11);
    const std::uint64_t bench13 = run_bench(13);
    forge::Board start;
    if (!start.set_fen(forge::Board::StandardStartFen)) {
        std::cerr << "FAIL pins: could not parse the start position\n";
        return 1;
    }
    const std::uint64_t perft5 = start.perft(5);
    std::cout << "pins bench11 " << bench11 << " bench13 " << bench13 << " perft5 " << perft5 << '\n';
    int failures = 0;
    if (bench11 != ExpectedBench11) {
        std::cerr << "FAIL pin bench 11: got " << bench11 << " expected " << ExpectedBench11 << '\n';
        ++failures;
    }
    if (bench13 != ExpectedBench13) {
        std::cerr << "FAIL pin bench 13: got " << bench13 << " expected " << ExpectedBench13 << '\n';
        ++failures;
    }
    if (perft5 != ExpectedPerft5) {
        std::cerr << "FAIL pin perft 5: got " << perft5 << " expected " << ExpectedPerft5 << '\n';
        ++failures;
    }
    if (failures == 0) std::cout << "PASS pins 312866 862329 4865609\n";
    return failures;
}

} // namespace

int main() {
    int failures = 0;
    failures += test_singular_depth2();
    failures += test_pins();
    failures += test_depth10_legal();
    if (failures != 0) {
        std::cerr << "FAIL r4_08 total " << failures << '\n';
        return 1;
    }
    std::cout << "PASS r4_08\n";
    return 0;
}
