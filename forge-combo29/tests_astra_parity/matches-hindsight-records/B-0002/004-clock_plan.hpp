#pragma once

#include <algorithm>
#include <cstdint>

namespace forge {

// One move of clock time (wtime/btime, increment, movestogo, Move Overhead).
// movetime is a separate limit and is not planned here.
struct ClockPlan {
    std::int64_t soft_ms = 0;
    std::int64_t hard_ms = 0;
    // Nothing remains after Move Overhead. A hard limit of 0 would mean the
    // search is not on a clock, so the caller must stop instead of searching.
    bool reserve_empty = false;
};

// usable = max(0, time - overhead), with negatives treated as zero.
// The plan never asks for more than usable. Soft never exceeds hard.
// When usable is positive both limits stay in 1..usable, using the same
// sudden-death and moves-to-go split as before. That split is left alone
// when it already obeyed the bounds. It is pulled back when no time remains
// after overhead, or when increment would place soft above hard.
// soft_divisor must be positive; the UCI spin starts at 5.
[[nodiscard]] inline ClockPlan plan_clock_budget(std::int64_t time_ms, std::int64_t increment_ms,
                                                 std::int64_t moves_to_go, std::int64_t overhead_ms,
                                                 int soft_divisor, int increment_percent, int hard_percent,
                                                 int hard_soft_multiple) {
    const std::int64_t overhead = overhead_ms > 0 ? overhead_ms : 0;
    const std::int64_t time = time_ms > 0 ? time_ms : 0;
    const std::int64_t increment = increment_ms > 0 ? increment_ms : 0;
    if (time <= overhead) return ClockPlan{0, 0, true};

    const std::int64_t available = time - overhead;
    std::int64_t soft = 0;
    std::int64_t hard = 0;
    if (moves_to_go > 0) {
        const std::int64_t mtg = moves_to_go < 50 ? moves_to_go : 50;
        soft = available / (mtg + 1) + increment * 3 / 4;
        hard = std::min(available * 4 / 5, soft * 4);
    } else {
        const int divisor = soft_divisor > 0 ? soft_divisor : 1;
        soft = available / divisor + increment * increment_percent / 100;
        hard = std::min(available * hard_percent / 100, soft * hard_soft_multiple);
    }
    soft = std::max<std::int64_t>(1, std::min(soft, available));
    hard = std::max<std::int64_t>(1, std::min(hard, available));
    if (soft > hard) soft = hard;
    return ClockPlan{soft, hard, false};
}

} // namespace forge
