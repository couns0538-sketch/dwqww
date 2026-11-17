#pragma once

#include <cstdint>

namespace forge {

// Clock decision for one iterative-deepening step.
//
// prev_ms and last_ms are the durations, in milliseconds, of the two iterations
// that just finished. last_ms is the later one. remaining_ms is how much of
// this move's budget is left.
//
// Steady growth (last no more than twice prev) is extended one step:
// last * last / prev. A larger jump is one deep iteration, not a new rate.
// Compounding it predicted several times the real next iteration on this
// engine's own depth curves (one measured step was about 84 ms after 16 ms,
// and the following iteration was about 38 ms, not about 440). After that
// kind of jump the estimate is the geometric mean of the two durations,
// sqrt(last * prev). The iteration cannot finish when the estimate is
// strictly longer than remaining_ms. The caller then keeps the move from the
// iteration that already finished.
//
// A non-positive duration is not a measurement, so this returns false and the
// search does what it did without the estimate. A budget that is already used
// up cannot hold another iteration.
[[nodiscard]] constexpr bool iteration_will_not_finish(std::int64_t prev_ms, std::int64_t last_ms,
                                                        std::int64_t remaining_ms) noexcept {
    if (remaining_ms <= 0) return true;
    if (prev_ms <= 0 || last_ms <= 0) return false;
    const auto prev = static_cast<unsigned __int128>(static_cast<std::uint64_t>(prev_ms));
    const auto last = static_cast<unsigned __int128>(static_cast<std::uint64_t>(last_ms));
    const auto left = static_cast<unsigned __int128>(static_cast<std::uint64_t>(remaining_ms));
    // Twice prev still fits in 64 bits: prev_ms is a non-negative int64.
    const bool spike = static_cast<std::uint64_t>(last_ms) > static_cast<std::uint64_t>(prev_ms) * 2ULL;
    if (spike) return last * prev > left * left;
    return last * last > left * prev;
}

}  // namespace forge
