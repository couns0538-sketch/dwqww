// Deterministic legal playout fixture generator; no external chess package.
#include "forge/board.hpp"
#include <cstdint>
#include <iostream>
#include <set>
#include <string>

int main() {
    constexpr const char* corners[] = {
        forge::Board::StandardStartFen.data(),
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1",
        "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
        "7k/8/8/8/8/8/8/K7 w - - 0 1",
        "7k/P7/5K2/8/8/8/8/8 w - - 0 1",
        "8/8/8/8/8/5k2/p7/7K b - - 0 1",
        "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
        "4r2k/8/8/8/8/8/8/4K3 w - - 0 1",
        "7k/8/8/8/8/8/8/R3K3 w - - 99 1",
        "7k/8/8/8/8/8/8/R3K3 w - - 100 1",
        "7k/8/8/8/8/8/8/2B1K3 w - - 0 1",
        "7k/8/8/8/8/8/8/2N1K3 w - - 0 1",
    };
    std::set<std::string> seen;
    auto emit = [&](const forge::Board& board) {
        const std::string fen = board.fen();
        if (seen.insert(fen).second) std::cout << fen << '\n';
    };
    for (const char* fen : corners) {
        forge::Board board;
        std::string error;
        if (!board.set_fen(fen, &error)) {
            std::cerr << "Invalid corner: " << fen << ": " << error << '\n';
            return 1;
        }
        emit(board);
    }
    std::uint64_t state = 0x464F524745202611ULL;
    auto random = [&]() {
        std::uint64_t z = (state += 0x9e3779b97f4a7c15ULL);
        z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
        z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
        return z ^ (z >> 31);
    };
    for (int game = 0; seen.size() < 128; ++game) {
        forge::Board board;
        const int lengths[] = {4, 12, 32, 64, 96, 160, 240};
        const int plies = lengths[game % 7] + static_cast<int>(random() % 8);
        for (int ply = 0; ply < plies; ++ply) {
            const auto moves = board.legal_moves();
            if (moves.empty() || board.halfmove_clock() >= 100) break;
            const auto move = moves[static_cast<std::size_t>(random() % moves.size())];
            forge::Undo undo;
            if (!board.make_move(move, undo)) return 2;
        }
        emit(board);
    }
}
