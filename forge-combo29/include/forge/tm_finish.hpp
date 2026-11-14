#pragma once

#include <cstdint>

namespace forge {

// Clock decision for one iterative-deepening step.
//
// prev_ms and last_ms are the durations, in milliseconds, of the two iterations
// that just finished. last_ms is the later one. remaining_ms is how much of
// this move's budget is left.
//
// The next iteration is estimated in exact arithmetic as
// last_ms * last_ms / prev_ms: the last duration scaled by the growth from
// the one before it. The estimate cannot finish when it is strictly longer
// than remaining_ms. The caller then keeps the move from the iteration that
// already finished.
//
// A non-positive duration is not a measurement, so this returns false and the
// search does what it did without the estimate. A budget that is already used
// up cannot hold another iteration.
[[nodiscard]] constexpr bool iteration_will_not_finish(std::int64_t prev_ms, std::int64_t last_ms,
                                                        std::int64_t remaining_ms) noexcept {
    if (remaining_ms <= 0) return true;
    if (prev_ms <= 0 || last_ms <= 0) return false;
    const auto need = static_cast<unsigned __int128>(static_cast<std::uint64_t>(last_ms)) *
                      static_cast<unsigned __int128>(static_cast<std::uint64_t>(last_ms));
    const auto have = static_cast<unsigned __int128>(static_cast<std::uint64_t>(remaining_ms)) *
                      static_cast<unsigned __int128>(static_cast<std::uint64_t>(prev_ms));
    return need > have;
}

}  // namespace forge
