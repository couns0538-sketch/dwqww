// The first Board in this process is constructed behind the eight-thread gate.
#include "forge/board.hpp"

#include <array>
#include <barrier>
#include <cstdint>
#include <exception>
#include <iostream>
#include <string>
#include <thread>

namespace {
constexpr int Workers = 8;
struct Result {
    bool start_fen = false;
    bool restored_fen = false;
    bool kiwi_parsed = false;
    std::uint64_t start_nodes = 0;
    std::uint64_t kiwi_nodes = 0;
    std::string error;
};
}

int main() {
    // No controller Board or attacks::init call is permitted before this gate.
    std::barrier gate(Workers);
    std::array<Result, Workers> results{};
    std::array<std::thread, Workers> threads;
    for (int i = 0; i < Workers; ++i) {
        threads[static_cast<std::size_t>(i)] = std::thread([&, i] {
            gate.arrive_and_wait();
            auto& row = results[static_cast<std::size_t>(i)];
            try {
                forge::Board board;
                row.start_fen = board.fen() == forge::Board::StandardStartFen;
                row.start_nodes = board.perft(3);
                row.restored_fen = board.fen() == forge::Board::StandardStartFen;
                row.kiwi_parsed = board.set_fen(
                    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
                if (row.kiwi_parsed) row.kiwi_nodes = board.perft(2);
            } catch (const std::exception& error) {
                row.error = error.what();
            }
        });
    }
    for (auto& thread : threads) thread.join();
    bool okay = true;
    for (int i = 0; i < Workers; ++i) {
        const auto& row = results[static_cast<std::size_t>(i)];
        if (!row.start_fen || !row.restored_fen || !row.kiwi_parsed ||
            row.start_nodes != 8902 || row.kiwi_nodes != 2039 || !row.error.empty()) {
            std::cerr << "FAIL: cold first Board worker " << i
                      << " start_nodes=" << row.start_nodes << " kiwi_nodes=" << row.kiwi_nodes
                      << " start_fen=" << row.start_fen << " restored_fen=" << row.restored_fen
                      << " kiwi_parsed=" << row.kiwi_parsed << " error=" << row.error << '\n';
            okay = false;
        }
    }
    if (!okay) return 1;
    std::cout << "COLD_FIRST_BOARD_PASS workers=8 startpos_d3=8902 kiwipete_d2=2039\n";
    return 0;
}
