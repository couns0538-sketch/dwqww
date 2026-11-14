#include "forge/board.hpp"
#include "forge/search.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

// Finding 9: TTEntry::score_usable treated every pair of clocks below 90 as
// usable, so a depth-16 mate stored at clock 0 was a cutoff at clock 88.
// Quiescence hash cutoffs use that predicate, and they already refuse clocks
// at or above 90. These checks stay failures until that horizon is respected.
// Astra's eight depth-9 roots stay equality failures against the lock: search
// extensions reach the rule-50 gates from roots below 80, and that inequality
// is the intended behaviour.

namespace {

int g_failures = 0;

void fail(const std::string& message) {
    std::cerr << "FAIL " << message << '\n';
    ++g_failures;
}

void ok(const std::string& message) { std::cout << "OK " << message << '\n'; }

forge::TTEntry make_entry(int score, int depth, int rule50) {
    forge::TTEntry entry;
    entry.score = static_cast<std::int16_t>(score);
    entry.depth = static_cast<std::uint8_t>(depth);
    entry.rule50_clock = static_cast<std::uint8_t>(rule50);
    entry.eval = static_cast<std::int16_t>(forge::ValueNone);
    entry.gen_bound = static_cast<std::uint8_t>(forge::BoundExact);
    return entry;
}

void expect_usable(const char* label, const forge::TTEntry& entry, int clock, bool want) {
    const bool got = entry.score_usable(static_cast<std::uint16_t>(clock));
    if (got != want) {
        fail(std::string(label) + " clock " + std::to_string(clock) + " usable=" + (got ? "1" : "0") +
             " want=" + (want ? "1" : "0"));
        return;
    }
    ok(std::string(label) + " clock " + std::to_string(clock));
}

void test_score_usable() {
    // Audit trigger: 15-ply mate (31985) stored at clock 0, depth 16, probed at 88.
    // 88 + 15 = 103, past the 50-move draw. The old predicate returned true.
    expect_usable("mate15 depth16 from clock 0", make_entry(31985, 16, 0), 88, false);
    expect_usable("cp depth16 from clock 0", make_entry(400, 16, 0), 88, false);
    // 88 + 5 = 93 stays inside the horizon, and both clocks are below 90.
    expect_usable("cp depth5 from clock 0", make_entry(400, 5, 0), 88, true);
    // A 10-ply mate from clock 88 ends at clock 98, before the 50-move draw.
    expect_usable("mate10 depth10 from clock 0", make_entry(31990, 10, 0), 88, true);
    // 13-ply mate from clock 88 arrives at clock 101. Depth 10 would fit; the mate does not.
    expect_usable("mate13 depth10 from clock 0", make_entry(31987, 10, 0), 88, false);
    // Same clock: the search that stored the score already saw the draw, so a non-mate stays usable.
    expect_usable("cp depth16 exact clock 88", make_entry(400, 16, 88), 88, true);
    // Exact clocks do not rescue a mate the remaining half-moves cannot deliver.
    expect_usable("mate15 exact clock 88", make_entry(31985, 16, 88), 88, false);
    expect_usable("mate15 exact clock 95", make_entry(31985, 8, 95), 95, false);
    // Quiescence still sees an exact non-mate at clock 95 as usable. The hash
    // cutoff itself requires halfmove_clock < 90, so this score is not a cutoff.
    expect_usable("cp depth6 exact clock 95", make_entry(400, 6, 95), 95, true);
    expect_usable("mate15 at the clock that stored it", make_entry(31985, 16, 0), 0, true);
    // Depth 11 from clock 89 reaches clock 100, so the stored tree can cross the draw.
    // Depth 10 ends at clock 99 and stays usable.
    expect_usable("cp depth11 from clock 0 at 89", make_entry(400, 11, 0), 89, false);
    expect_usable("cp depth10 from clock 0 at 89", make_entry(400, 10, 0), 89, true);
}

void test_stored_entry() {
    forge::Board board;
    if (!board.set_fen("8/8/8/3k4/8/8/1Q6/3K4 b - - 88 50")) {
        fail("child fen for the stored mate");
        return;
    }
    forge::Searcher searcher(16, 1);
    const forge::TTProbe probe = searcher.transposition_table().probe(board.key());
    searcher.transposition_table().store(probe, board.key(), 31985, forge::ValueNone, forge::Move::none(), 16,
                                         forge::BoundExact, false, 0);
    const forge::TTProbe again = searcher.transposition_table().probe(board.key());
    if (!again.hit || again.entry.score != 31985 || again.entry.depth != 16 || again.entry.rule50_clock != 0) {
        fail("stored mate was not probed back");
        return;
    }
    if (again.entry.score_usable(88)) {
        fail("probed depth-16 mate from clock 0 is usable at clock 88");
        return;
    }
    if (!again.entry.score_usable(0)) {
        fail("probed mate is not usable at the clock that stored it");
        return;
    }
    ok("stored mate from clock 0 is not usable at clock 88");
}

forge::SearchInfo search_fen(forge::Searcher& searcher, std::string_view fen, int depth) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        fail(std::string("set_fen ") + std::string(fen));
        return {};
    }
    forge::SearchLimits limits;
    limits.depth = depth;
    return searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
}

bool move_is_legal(const forge::Board& board, forge::Move move) {
    if (move.is_none() || !board.is_legal(move)) return false;
    for (const forge::Move legal : board.legal_moves()) {
        if (legal == move) return true;
    }
    return false;
}

void test_clock95_draw_and_poison() {
    // No captures and no pawn moves: depth 4 from clock 95 ends on the 50-move draw.
    const char* fen = "8/8/8/3k4/8/8/2Q5/3K4 w - - 95 50";
    forge::Board drawn;
    forge::Searcher empty(16, 1);
    const forge::SearchInfo cold = search_fen(empty, fen, 4);
    if (!drawn.set_fen(fen) || cold.score != 0 || !move_is_legal(drawn, cold.best_move)) {
        fail("clock 95 depth 4 must be a legal 50-move draw, score " + std::to_string(cold.score));
    } else {
        ok("clock 95 depth 4 is a draw");
    }

    // A mate stored at clock 0 must not become the answer at clock 88.
    const char* parent = "8/8/8/3k4/8/8/2Q5/3K4 w - - 87 50";
    forge::Searcher cold_parent(16, 1);
    const forge::SearchInfo base = search_fen(cold_parent, parent, 5);
    forge::Board child;
    if (!child.set_fen(parent)) {
        fail("parent fen");
        return;
    }
    bool found = false;
    for (const forge::Move move : child.legal_moves()) {
        if (forge::Board::move_to_uci(move) != "c2b2") continue;
        forge::Undo undo;
        if (!child.make_move(move, undo)) {
            fail("c2b2 was not playable");
            return;
        }
        found = true;
        break;
    }
    if (!found || child.halfmove_clock() != 88) {
        fail("c2b2 did not reach clock 88");
        return;
    }
    forge::Searcher warm(16, 1);
    const forge::TTProbe probe = warm.transposition_table().probe(child.key());
    warm.transposition_table().store(probe, child.key(), 31985, forge::ValueNone, forge::Move::none(), 16,
                                     forge::BoundExact, false, 0);
    const forge::SearchInfo poisoned = search_fen(warm, parent, 5);
    if (poisoned.score != base.score) {
        fail("horizon-crossing mate changed the depth-5 score from " + std::to_string(base.score) + " to " +
             std::to_string(poisoned.score));
    } else if (forge::is_mate_score(poisoned.score) &&
               static_cast<int>(child.halfmove_clock()) + (forge::MateValue - std::abs(poisoned.score)) > 100) {
        fail("search returned a mate past the 50-move horizon");
    } else {
        ok("depth-5 score ignores a clock-0 mate at the clock-88 child (" + std::to_string(base.score) + ")");
    }
}

struct Depth9Case {
    int index;
    const char* fen;
    int root_clock;
    const char* move;
    int engine_score;
    std::uint64_t engine_nodes;
    int lock_score;
    std::uint64_t lock_nodes;
    const char* difference;
};

// Lock numbers are the unchanged combo29 binary in soak/combo29-all faults 084..091.
// Engine numbers are this tree at depth 9, Threads 1, Hash 16, the three t22 options off.
constexpr std::array<Depth9Case, 8> kDepth9{{
    {3228, "5k2/8/7p/1K5P/8/8/8/7q w - - 76 136", 76, "b5c4", -1689, 31749, -1689, 32435, "nodes"},
    {9834, "8/4k3/8/2q3b1/6K1/5B2/8/8 w - - 74 132", 74, "f3e2", -1164, 49669, -1117, 43672, "score nodes pv"},
    {10567, "1b6/6k1/6b1/3r3r/8/8/8/2K5 w - - 76 134", 76, "c1b2", -31984, 7582, -31984, 7581, "nodes"},
    {11000, "1k4r1/8/8/8/8/8/8/1K6 b - - 79 146", 79, "g8g2", 460, 14025, 460, 14618, "nodes pv"},
    {12276, "8/8/5R2/8/8/8/7K/2k5 w - - 79 151", 79, "f6f5", 443, 8688, 443, 8682, "nodes"},
    {12999, "8/1k6/5K2/B4N2/8/R7/8/8 w - - 79 147", 79, "f6e5", 1187, 12663, 1181, 12873, "score nodes pv"},
    {14002, "8/6b1/6k1/B7/7K/4q3/8/8 w - - 79 145", 79, "a5c7", -1178, 26217, -1214, 36360, "score nodes pv"},
    {25354, "8/r7/1k4n1/5p2/2K5/7n/8/8 w - - 72 141", 72, "c4d4", -1812, 29687, -1812, 29685, "nodes"},
}};

void test_eight_depth9() {
    std::cout << "Eight depth-9 roots stay equality failures. Extensions reach the rule-50\n"
                 "gates from these clocks below 80; matching the lock would weaken those gates.\n";
    for (const Depth9Case& item : kDepth9) {
        forge::Board board;
        if (!board.set_fen(item.fen) || board.halfmove_clock() != item.root_clock || item.root_clock >= 80) {
            fail(std::string("depth-9 fen ") + std::to_string(item.index));
            continue;
        }
        forge::Searcher searcher(16, 1);
        forge::SearchLimits limits;
        limits.depth = 9;
        const forge::SearchInfo info = searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
        const std::string move = forge::Board::move_to_uci(info.best_move);
        if (!move_is_legal(board, info.best_move) || move != item.move || info.score != item.engine_score ||
            info.nodes != item.engine_nodes) {
            fail("depth-9 " + std::to_string(item.index) + " move " + move + " score " + std::to_string(info.score) +
                 " nodes " + std::to_string(info.nodes));
            continue;
        }
        if (info.nodes == item.lock_nodes && info.score == item.lock_score) {
            fail("depth-9 " + std::to_string(item.index) + " restored lock equality");
            continue;
        }
        std::cout << "EQUALITY_FAIL " << item.index << " clock " << item.root_clock << " (" << item.difference
                  << ") lock score " << item.lock_score << " nodes " << item.lock_nodes << "; engine score "
                  << info.score << " nodes " << info.nodes << " move " << move << '\n';
    }
}

constexpr std::uint64_t kBench11 = 312866;
constexpr std::uint64_t kBench13 = 862329;
constexpr std::uint64_t kPerft5 = 4865609;

constexpr std::array<std::string_view, 8> kBenchFens{
    forge::Board::StandardStartFen,
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
};

std::uint64_t run_bench(int depth) {
    std::uint64_t total = 0;
    forge::Searcher searcher(16, 1);
    for (const std::string_view fen : kBenchFens) {
        forge::Board board;
        if (!board.set_fen(fen)) return 0;
        forge::SearchLimits limits;
        limits.depth = depth;
        searcher.clear();
        total += searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive).nodes;
    }
    return total;
}

void test_pins() {
    const std::uint64_t bench11 = run_bench(11);
    const std::uint64_t bench13 = run_bench(13);
    forge::Board start;
    if (!start.set_fen(forge::Board::StandardStartFen)) {
        fail("startpos");
        return;
    }
    const std::uint64_t perft5 = start.perft(5);
    std::cout << "pins bench11 " << bench11 << " bench13 " << bench13 << " perft5 " << perft5 << '\n';
    if (bench11 != kBench11 || bench13 != kBench13 || perft5 != kPerft5) {
        fail("pins changed");
    } else {
        ok("pins 312866 862329 4865609");
    }
}

constexpr std::array<std::string_view, 25> kSeedFens{
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
    for (std::size_t seed = 0; seed < kSeedFens.size() && positions.size() < 200; ++seed) {
        forge::Board board;
        if (!board.set_fen(kSeedFens[seed])) continue;
        for (int step = 0; step < 8 && positions.size() < 200; ++step) {
            const forge::MoveList legal = board.legal_moves();
            if (legal.empty()) {
                if (!board.set_fen(kSeedFens[(seed + 1) % kSeedFens.size()])) break;
            }
            if (!board.legal_moves().empty()) positions.push_back(board);
            const forge::MoveList step_moves = board.legal_moves();
            if (step_moves.empty()) break;
            const forge::Move chosen = step_moves[static_cast<std::size_t>(next_u64() % step_moves.size())];
            forge::Undo undo;
            if (!board.make_move(chosen, undo)) break;
        }
    }
    return positions;
}

void test_200_depth10() {
    const std::vector<forge::Board> positions = build_200_positions();
    if (positions.size() != 200) {
        fail("expected 200 positions, got " + std::to_string(positions.size()));
        return;
    }
    forge::Searcher searcher(16, 1);
    for (std::size_t i = 0; i < positions.size(); ++i) {
        if (i % 25 == 0) searcher.clear();
        const forge::Board& board = positions[i];
        forge::SearchLimits limits;
        limits.depth = 10;
        const forge::SearchInfo info = searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
        if (!move_is_legal(board, info.best_move)) {
            fail("illegal best move at depth 10 index " + std::to_string(i) + " " +
                 forge::Board::move_to_uci(info.best_move));
            return;
        }
    }
    ok("200 depth-10 searches, every move legal");
}

} // namespace

int main() {
    test_score_usable();
    test_stored_entry();
    test_clock95_draw_and_poison();
    test_eight_depth9();
    test_pins();
    test_200_depth10();
    if (g_failures != 0) {
        std::cerr << "FAILURES " << g_failures << '\n';
        return 1;
    }
    std::cout << "ALL CHECKS PASSED\n";
    return 0;
}
