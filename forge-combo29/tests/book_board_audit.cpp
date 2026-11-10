// Preserved from the earlier stdin-only board audit, with explicit nodiscard
// casts and formatting added. Independent of the opening-book experiment.
#include "forge/board.hpp"
#include <cstdlib>
#include <iostream>
#include <random>
using namespace forge;
int main() {
    std::mt19937 rng(20261110);
    Board board;
    size_t positions = 0, tested_moves = 0;
    const char* corners[] = {
        "8/6bb/8/8/R1pP2k1/4P3/P7/K7 b - d3 0 1",
        "8/8/8/r4pPK/8/8/8/4k3 w - f6 0 1",
        "4k3/8/8/3pP3/4K3/8/8/8 w - d6 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "4k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
        "4r2k/8/8/8/1b6/8/8/4K3 w - - 0 1"};
    auto check = [&]() {
        ++positions;
        const auto fen = board.fen();
        const auto key = board.key(), pawn_key = board.pawn_key();
        const auto history = board.key_history();
        const auto legal = board.legal_moves();
        if (board.has_legal_move() != !legal.empty()) { std::cerr << "has legal " << fen; std::exit(1); }
        for (auto move : legal) {
            ++tested_moves;
            if (!board.is_pseudo_legal(move)) { std::cerr << "pseudo " << fen; std::exit(2); }
            const bool gives_check = board.gives_check(move);
            Undo undo;
            (void)board.make_move(move, undo);
            if (gives_check != board.in_check()) { std::cerr << "check " << fen << " " << Board::move_to_uci(move); std::exit(3); }
            Board round;
            std::string error;
            if (!round.set_fen(board.fen(), &error) || round.key() != board.key() ||
                round.pawn_key() != board.pawn_key() || round.checkers() != board.checkers()) {
                std::cerr << "round " << fen << " " << Board::move_to_uci(move) << " " << error; std::exit(4);
            }
            board.unmake_move(move, undo);
            if (board.fen() != fen || board.key() != key || board.pawn_key() != pawn_key || board.key_history() != history) {
                std::cerr << "undo " << fen; std::exit(5);
            }
        }
    };
    for (auto fen : corners) {
        std::string error;
        if (!board.set_fen(fen, &error)) { std::cerr << error << " " << fen; return 6; }
        check();
        std::cout << fen << " :";
        for (auto move : board.legal_moves()) std::cout << " " << Board::move_to_uci(move);
        std::cout << '\n';
    }
    for (int game = 0; game < 100; ++game) {
        (void)board.set_fen(Board::StandardStartFen);
        for (int ply = 0; ply < 180; ++ply) {
            check();
            const auto legal = board.legal_moves();
            if (legal.empty()) break;
            Undo undo;
            (void)board.make_move(legal[rng() % legal.size()], undo);
        }
    }
    std::cout << "PASS positions=" << positions << " moves=" << tested_moves << " seed=20261110\n";
}
