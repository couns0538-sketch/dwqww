// Warm-initialized, private-board float NNUE workers; not a cold-init race test.
// Reuses the earlier standalone worker-parity test idea with the current API.
#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <functional>
#include <iostream>
#include <random>
#include <stdexcept>
#include <thread>

namespace {
using Accumulator = forge::nnue::Accumulator;
static_assert(forge::nnue::HiddenSize == 256, "S05 qualification requires H256");
constexpr int Workers = 4;
constexpr int Transitions = 2000;

struct Result {
    std::uint64_t transitions = 0, lane_mismatches = 0, score_mismatches = 0;
    std::uint64_t parent_mismatches = 0, alias_mismatches = 0, errors = 0;
};

bool same(const Accumulator& a, const Accumulator& b) {
    if (a.valid != b.valid) return false;
    for (std::size_t side = 0; side < a.values.size(); ++side)
        for (std::size_t h = 0; h < a.values[side].size(); ++h)
            if (!std::isfinite(a.values[side][h]) || !std::isfinite(b.values[side][h]) ||
                std::bit_cast<std::uint32_t>(a.values[side][h]) !=
                    std::bit_cast<std::uint32_t>(b.values[side][h])) return false;
    return true;
}

void worker(int index, Result& result) {
    try {
        forge::Board board;
        Accumulator current;
        forge::nnue::refresh(board, current);
        std::mt19937_64 random(20261025U + static_cast<unsigned>(index));
        int ply = 0;
        for (int n = 0; n < Transitions; ++n) {
            auto legal = board.legal_moves();
            if (legal.empty() || ply == 80) {
                if (!board.set_fen(forge::Board::StandardStartFen)) throw std::runtime_error("worker reset failed");
                forge::nnue::refresh(board, current);
                legal = board.legal_moves();
                ply = 0;
            }
            if (legal.empty() || !current.valid) throw std::runtime_error("invalid worker position");
            const auto move = legal[static_cast<std::size_t>(random() % legal.size())];
            const auto dirty = forge::nnue::dirty_pieces(board, move);
            const auto saved = current;
            Accumulator child;
            forge::nnue::update(current, child, dirty);
            if (!same(saved, current)) ++result.parent_mismatches;
            auto alias = current;
            forge::nnue::update(alias, alias, dirty);
            if (!same(alias, child)) ++result.alias_mismatches;
            forge::Undo undo;
            if (!board.make_move(move, undo)) throw std::runtime_error("worker legal move rejected");
            Accumulator fresh;
            forge::nnue::refresh(board, fresh);
            if (!fresh.valid || !child.valid) throw std::runtime_error("worker invalid accumulator");
            if (!same(child, fresh)) ++result.lane_mismatches;
            if (forge::nnue::evaluate(board, child) != forge::nnue::evaluate(board, fresh)) ++result.score_mismatches;
            current = child;
            ++result.transitions;
            ++ply;
        }
    } catch (...) {
        ++result.errors;
    }
}
} // namespace

int main() {
    try {
        if (!forge::nnue::available()) throw std::runtime_error("no compiled NNUE network");
        // Board initialization and weight initialization finish before workers exist.
        forge::Board controller;
        Accumulator warmed;
        forge::nnue::refresh(controller, warmed);
        if (!warmed.valid || controller.legal_moves().empty()) throw std::runtime_error("serial bootstrap failed");
        (void)forge::nnue::evaluate(controller, warmed);
        std::array<Result, Workers> results{};
        std::array<std::jthread, Workers> threads;
        for (int index = 0; index < Workers; ++index)
            threads[static_cast<std::size_t>(index)] = std::jthread(worker, index, std::ref(results[static_cast<std::size_t>(index)]));
        for (auto& thread : threads) thread.join();
        Result total;
        for (const auto& result : results) {
            total.transitions += result.transitions;
            total.lane_mismatches += result.lane_mismatches;
            total.score_mismatches += result.score_mismatches;
            total.parent_mismatches += result.parent_mismatches;
            total.alias_mismatches += result.alias_mismatches;
            total.errors += result.errors;
        }
        const bool pass = total.transitions == Workers * Transitions && total.lane_mismatches == 0 &&
            total.score_mismatches == 0 && total.parent_mismatches == 0 && total.alias_mismatches == 0 && total.errors == 0;
        std::cout << "{\"status\":\"" << (pass ? "PASS" : "FAIL") << "\",\"workers\":" << Workers
            << ",\"transitions\":" << total.transitions << ",\"lane_mismatches\":" << total.lane_mismatches
            << ",\"score_mismatches\":" << total.score_mismatches
            << ",\"parent_mismatches\":" << total.parent_mismatches
            << ",\"alias_mismatches\":" << total.alias_mismatches << ",\"errors\":" << total.errors << "}\n";
        return pass ? 0 : 1;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
