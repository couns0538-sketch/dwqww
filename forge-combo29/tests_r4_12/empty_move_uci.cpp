#include "forge/board.hpp"
#include "forge/search.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
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

int fail(const std::string& message) {
    std::cerr << "FAIL " << message << '\n';
    return 1;
}

forge::Move quiet_move(int from, int to) {
    forge::Move move{};
    move.from = static_cast<std::uint8_t>(from);
    move.to = static_cast<std::uint8_t>(to);
    return move;
}

forge::Move promotion_move(int from, int to, forge::PieceType piece) {
    forge::Move move = quiet_move(from, to);
    move.promotion = static_cast<std::uint8_t>(piece);
    move.flags = forge::Promotion;
    return move;
}

int check_empty_move_format() {
    const std::string none = forge::Board::move_to_uci(forge::Move::none());
    std::cout << "move_to_uci(none)=" << none << '\n';
    if (none != "0000") {
        return fail("empty move formatted as \"" + none + "\" expected \"0000\"");
    }

    const std::string e2e4 = forge::Board::move_to_uci(quiet_move(12, 28));
    const std::string a1b1 = forge::Board::move_to_uci(quiet_move(0, 1));
    const std::string a7a8q = forge::Board::move_to_uci(promotion_move(48, 56, forge::Queen));
    std::cout << "move_to_uci(e2e4)=" << e2e4
              << " move_to_uci(a1b1)=" << a1b1
              << " move_to_uci(a7a8q)=" << a7a8q << '\n';
    if (e2e4 != "e2e4" || a1b1 != "a1b1" || a7a8q != "a7a8q") {
        return fail("ordinary move formatting changed");
    }
    return 0;
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

bool pv_is_legal(const forge::Board& root, const forge::SearchInfo& info) {
    if (info.best_move.is_none() || !root.is_legal(info.best_move)) return false;
    if (forge::Board::move_to_uci(info.best_move) == "0000") return false;
    forge::Board parsed_board = root;
    const std::optional<forge::Move> parsed = parsed_board.parse_uci(forge::Board::move_to_uci(info.best_move));
    if (!parsed || !(*parsed == info.best_move)) return false;
    if (info.pv.empty()) return true;
    if (!(info.pv.front() == info.best_move)) return false;

    forge::Board cursor = root;
    for (const forge::Move& move : info.pv) {
        if (move.is_none() || !cursor.is_legal(move)) return false;
        if (forge::Board::move_to_uci(move) == "0000") return false;
        forge::Undo undo;
        if (!cursor.make_move(move, undo)) return false;
    }
    return true;
}

int check_depth10_searches() {
    const std::vector<forge::Board> positions = build_200_positions();
    if (positions.size() != 200) {
        return fail("expected 200 positions, built " + std::to_string(positions.size()));
    }

    forge::Searcher searcher(16, 1);
    int illegal = 0;
    std::uint64_t total_nodes = 0;
    for (std::size_t i = 0; i < positions.size(); ++i) {
        if (i % 25 == 0) {
            searcher.clear();
            std::cout << "depth10 progress " << i << '\n' << std::flush;
        }
        forge::SearchLimits limits;
        limits.depth = 10;
        const forge::SearchInfo info =
            searcher.search(positions[i], limits, false, forge::Searcher::TTAccess::Exclusive);
        total_nodes += info.nodes;
        if (!pv_is_legal(positions[i], info)) {
            std::cerr << "FAIL illegal move at position " << i
                      << " best " << forge::Board::move_to_uci(info.best_move)
                      << " pv";
            for (const forge::Move& move : info.pv) std::cerr << ' ' << forge::Board::move_to_uci(move);
            std::cerr << '\n';
            ++illegal;
            break;
        }
    }
    std::cout << "depth10 searches " << positions.size()
              << " legal_ok " << (illegal == 0 ? 1 : 0)
              << " total_nodes " << total_nodes << '\n';
    if (illegal != 0) return 1;
    return 0;
}

}  // namespace

int main() {
    if (const int format = check_empty_move_format()) return format;

    const std::uint64_t bench11 = run_bench(11);
    const std::uint64_t bench13 = run_bench(13);
    forge::Board start;
    if (!start.set_fen(forge::Board::StandardStartFen)) return fail("startpos fen");
    const std::uint64_t perft5 = start.perft(5);
    std::cout << "bench11 " << bench11 << " bench13 " << bench13 << " perft5 " << perft5 << '\n';
    if (bench11 != ExpectedBench11 || bench13 != ExpectedBench13 || perft5 != ExpectedPerft5) {
        return fail("pin mismatch");
    }

    if (const int searches = check_depth10_searches()) return searches;
    std::cout << "PASS r4_12 empty move uci\n";
    return 0;
}
