#pragma once

#include "forge/board.hpp"
#include "forge/search_tune.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <memory>

namespace forge {

struct SearchStack;

// Move-ordering statistics.
using ButterflyHistory = std::array<std::array<std::array<std::int16_t, 64>, 64>, 2>;
using PieceToHistory = std::array<std::array<std::int16_t, 64>, 13>;
using ContinuationHistory = std::array<std::array<PieceToHistory, 64>, 13>;
using CaptureHistory = std::array<std::array<std::array<std::int16_t, 7>, 64>, 13>;
using CounterMoveTable = std::array<std::array<Move, 64>, 13>;
constexpr std::size_t CorrectionSize = 1U << 14U;
constexpr int CorrectionGrain = 256;
constexpr int CorrectionLimit = 32 * CorrectionGrain;
using CorrectionHistory = std::array<std::array<std::int32_t, CorrectionSize>, 2>;

// History entries saturate at +/-HistoryMax.
constexpr int HistoryMax = 16384;

// Bonus earned by a move that produced a cutoff at `depth` (tunable shape).
[[nodiscard]] inline int history_bonus(int depth) {
    return std::min(tune::HistoryBonusMax, tune::HistoryBonusQuadratic * depth * depth + tune::HistoryBonusLinear * depth - 32);
}

// History gravity: entry += bonus - entry * |bonus| / HistoryMax, with the
// bonus clamped to +/-HistoryMax, so entries stay inside +/-HistoryMax.
inline void apply_history(std::int16_t& entry, int bonus) {
    const int clamped = std::clamp(bonus, -HistoryMax, HistoryMax);
    entry = static_cast<std::int16_t>(entry + clamped - entry * std::abs(clamped) / HistoryMax);
}

// The move-ordering tables of one search thread: main (butterfly) history,
// capture history, continuation history and counter moves. Their scoring and
// update rules (quiet_history, capture_history_value, update_continuation,
// update_quiet_stats, update_capture_stats) are Worker members defined in
// src/search/history.inc, so the search calls them exactly as in AL1 s198.
struct HistoryTables {
    void clear() {
        *main_history = ButterflyHistory{};
        *capture_history = CaptureHistory{};
        *continuation_history = ContinuationHistory{};
        *counter_moves = CounterMoveTable{};
    }

    std::unique_ptr<ButterflyHistory> main_history = std::make_unique<ButterflyHistory>();
    std::unique_ptr<CaptureHistory> capture_history = std::make_unique<CaptureHistory>();
    std::unique_ptr<ContinuationHistory> continuation_history = std::make_unique<ContinuationHistory>();
    std::unique_ptr<CounterMoveTable> counter_moves = std::make_unique<CounterMoveTable>();
};

} // namespace forge
