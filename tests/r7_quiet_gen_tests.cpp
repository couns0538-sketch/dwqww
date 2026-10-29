// R7 J3 (UCI R7QuietGen): Board::generate_quiets_r7 must list exactly the moves of
// generate_pseudo_legal(moves, false) that are neither captures nor promotions, in the same order (the move
// picker's quiet stage scores and sorts that list, so any difference in content or order would change the search).
// Positions: every position of the opening suite, every position of seeded random games from each of them, and
// the full perft-3 trees of hand-picked positions with castling rights, en passant, promotions and checks.
// usage: forge_r7_quiet_gen_tests <tools/openings/forge-10000.epd>
#include "forge/board.hpp"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

std::uint64_t comparisons = 0;
std::uint64_t quiet_moves = 0;
std::uint64_t castles = 0;
std::uint64_t double_pushes = 0;
std::uint64_t random_state = 0x9e3779b97f4a7c15ULL;

std::uint64_t random_word() {
    random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
    return random_state >> 11U;
}

void compare(const forge::Board& board) {
    forge::MoveList full;
    board.generate_pseudo_legal(full, false);
    std::vector<forge::Move> expected;
    for (const forge::Move move : full) {
        if (move.is_capture() || move.is_promotion()) continue;
        expected.push_back(move);
    }
    forge::MoveList quiets;
    board.generate_quiets_r7(quiets);
    std::size_t i = 0;
    for (const forge::Move move : quiets) {
        if (i >= expected.size() || !(move == expected[i])) {
            throw std::runtime_error("quiet list differs at index " + std::to_string(i) + " in " + board.fen());
        }
        if (move.is_castle()) ++castles;
        if (move.flags == forge::DoublePush) ++double_pushes;
        ++i;
    }
    if (i != expected.size()) {
        throw std::runtime_error("quiet list too short (" + std::to_string(i) + " of " + std::to_string(expected.size()) +
                                 ") in " + board.fen());
    }
    quiet_moves += i;
    ++comparisons;
}

void random_game(forge::Board board, int plies) {
    for (int ply = 0; ply < plies; ++ply) {
        compare(board);
        const forge::MoveList legal = board.legal_moves();
        if (legal.size() == 0) return;
        const forge::Move move = legal[static_cast<std::size_t>(random_word() % legal.size())];
        forge::Undo undo;
        (void)board.make_move(move, undo);
    }
}

void tree(forge::Board& board, int depth) {
    compare(board);
    if (depth == 0) return;
    const forge::MoveList legal = board.legal_moves();
    for (const forge::Move move : legal) {
        forge::Undo undo;
        (void)board.make_move(move, undo);
        tree(board, depth - 1);
        board.unmake_move(move, undo);
    }
}

std::string fen_of_epd(const std::string& line) {
    std::istringstream in(line);
    std::string placement, side, castling, ep;
    in >> placement >> side >> castling >> ep;
    return placement + " " + side + " " + castling + " " + ep + " 0 1";
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2) throw std::runtime_error("usage: forge_r7_quiet_gen_tests <forge-10000.epd>");
        const std::vector<std::string> picked = {
            std::string(forge::Board::StandardStartFen),
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",   // kiwipete
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b KQkq - 0 1",
            "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",                              // en passant lines
            "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",      // promotions, castling
            "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",              // promotion with capture
            "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
            "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1",                                       // castling only
            "r3k2r/8/8/8/8/8/8/4K3 b kq - 0 1",
            "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
            "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",          // en passant available
            "4k3/1P6/8/8/8/8/6p1/4K3 w - - 0 1",                                      // quiet promotions both sides
            "4k3/8/8/8/8/8/4q3/4K3 w - - 0 1",                                        // in check
            "r3k2r/8/8/8/4Q3/8/8/R3K2R b KQkq - 0 1",                                 // in check, castling rights kept
        };
        for (const std::string& fen : picked) {
            forge::Board board;
            if (!board.set_fen(fen)) throw std::runtime_error("bad picked fen " + fen);
            tree(board, 3);
            random_game(board, 120);
        }
        std::ifstream epd(argv[1]);
        if (!epd) throw std::runtime_error(std::string("cannot open ") + argv[1]);
        std::string line;
        int suite = 0;
        while (std::getline(epd, line)) {
            if (line.empty()) continue;
            forge::Board board;
            if (!board.set_fen(fen_of_epd(line))) throw std::runtime_error("bad epd line " + line);
            random_game(board, 40);
            ++suite;
        }
        if (suite < 10000) throw std::runtime_error("opening suite too small: " + std::to_string(suite));
        if (comparisons < 500000 || castles < 1000 || double_pushes < 10000) {
            throw std::runtime_error("coverage too small: " + std::to_string(comparisons) + " positions, " +
                                     std::to_string(castles) + " castles, " + std::to_string(double_pushes) +
                                     " double pushes");
        }
        std::cout << "r7 quiet gen: " << comparisons << " positions, " << quiet_moves << " quiet moves (" << castles
                  << " castles, " << double_pushes << " double pushes) identical in content and order\nPASS\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << "\n";
        return 1;
    }
}
