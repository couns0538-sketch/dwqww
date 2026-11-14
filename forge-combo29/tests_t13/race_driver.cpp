// ThreadSanitizer driver for task t13.
// Searches 20 positions to depth 10 with Threads 2, then the same set with Threads 4.
// Hash is 16 MB. No files, processes, or network.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <string_view>

namespace {

struct Position {
    const char* name;
    const char* fen;
    bool forced_mate;
};

// Openings, middlegames, endings, and two positions with a forced mate.
constexpr Position kPositions[] = {
    {"start", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", false},
    {"e4", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", false},
    {"sicilian", "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2", false},
    {"french", "rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3", false},
    {"kings-indian", "rnbqkb1r/pppppp1p/5np1/8/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3", false},
    {"ruy", "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3", false},
    {"qgd", "rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 0 4", false},
    {"italian-middle", "r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 4 6", false},
    {"caro-middle", "r1bqk2r/pp1nbppp/2p1pn2/3p4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 7", false},
    {"kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", false},
    {"tactical-middle", "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1", false},
    {"queens-middle", "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9", false},
    {"rook-end", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", false},
    {"kp-end", "8/8/4k3/8/8/4K3/4P3/8 w - - 0 1", false},
    {"krk", "8/8/8/4k3/8/8/8/R3K3 w - - 0 1", false},
    {"pawn-end", "8/8/8/8/3k4/8/3P4/3K4 w - - 0 1", false},
    {"opposite-bishops", "8/5k2/2b5/8/8/2B5/5K2/8 w - - 0 1", false},
    {"queen-end", "8/8/4k3/8/8/4K3/3Q4/8 w - - 0 1", false},
    // Mate in 1: Ra8#.
    {"mate-1", "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", true},
    // Mate in 2: Rh8+ Ka7, Ra8#.
    {"mate-2", "k7/8/2K5/8/8/8/8/7R w - - 0 1", true},
};

static_assert(sizeof(kPositions) / sizeof(kPositions[0]) == 20);

[[nodiscard]] bool move_is_legal(const forge::Board& board, forge::Move move) {
    if (move.is_none()) return false;
    const forge::MoveList legal = board.legal_moves();
    for (const forge::Move candidate : legal) {
        if (candidate == move) return true;
    }
    return false;
}

} // namespace

int main(int argc, char** argv) {
    const int depth = argc >= 2 ? std::atoi(argv[1]) : 10;
    const int position_limit = argc >= 3 ? std::atoi(argv[2]) : 20;
    if (depth < 1 || position_limit < 1) {
        std::cerr << "usage: race_driver [depth] [position_count]\n";
        return 2;
    }

    int failures = 0;
    const int threads_list[] = {2, 4};
    for (const int threads : threads_list) {
        forge::Searcher searcher(16, threads);
        if (searcher.threads() != threads) {
            std::cerr << "FAIL thread count " << searcher.threads() << " expected " << threads << '\n';
            return 1;
        }
        int index = 0;
        for (const Position& position : kPositions) {
            if (index >= position_limit) break;
            ++index;
            forge::Board board;
            std::string error;
            if (!board.set_fen(position.fen, &error)) {
                std::cerr << "FAIL fen " << position.name << " " << error << '\n';
                ++failures;
                continue;
            }
            forge::SearchLimits limits;
            limits.depth = depth;
            const forge::SearchInfo info = searcher.search(board, limits, false);
            const bool legal = move_is_legal(board, info.best_move);
            // White is to move in both mate fixtures, so a loss for White is not a pass.
            const bool mate_score = !position.forced_mate || info.score >= forge::MateInMaxPly;
            if (!legal || !mate_score) ++failures;
            std::cout << "threads " << threads << " depth " << depth << " " << position.name << " move "
                      << forge::Board::move_to_uci(info.best_move) << " score " << info.score << " nodes " << info.nodes
                      << " depth_reached " << info.depth << (legal ? " legal" : " ILLEGAL")
                      << (position.forced_mate ? (mate_score ? " mate_ok" : " MATE_MISSED") : "") << '\n';
        }
    }
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " failures " << failures << '\n';
    return failures == 0 ? 0 : 1;
}
