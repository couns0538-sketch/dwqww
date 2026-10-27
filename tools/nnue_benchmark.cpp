// Isolated output-layer timing; this does not measure engine strength.
#include "forge/nnue.hpp"
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>

int main() {
    if (!forge::nnue::available()) throw std::runtime_error("NNUE weights are required");
    std::array<forge::Board, 64> boards;
    std::array<forge::nnue::Accumulator, 64> accumulators;
    std::uint64_t random = 20261019;
    for (std::size_t i = 0; i < boards.size(); ++i) {
        if (i != 0) {
            boards[i] = boards[i - 1];
            const auto moves = boards[i].legal_moves();
            random = random * 6364136223846793005ULL + 1442695040888963407ULL;
            if (!moves.empty()) {
                forge::Undo undo;
                if (!boards[i].make_move(moves[static_cast<std::size_t>(random % moves.size())], undo))
                    throw std::runtime_error("legal move rejected");
            }
        }
        forge::nnue::refresh(boards[i], accumulators[i]);
    }
    constexpr std::uint64_t Calls = 5000000;
    std::int64_t checksum = 0;
    const auto start = std::chrono::steady_clock::now();
    for (std::uint64_t i = 0; i < Calls; ++i) {
        const auto index = static_cast<std::size_t>(i % boards.size());
        checksum += forge::nnue::evaluate(boards[index], accumulators[index]);
    }
    const auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now() - start).count();
    std::cout << "{\"calls\":" << Calls << ",\"elapsed_ns\":" << elapsed
              << ",\"checksum\":" << checksum << "}\n";
}
