#pragma once

#include <charconv>
#include <cstdint>
#include <limits>
#include <string_view>
#include <system_error>

namespace forge {

// Ceiling for a parsed clock. Time allocation multiplies a clock by a small
// tunable (at most 150), so the product has to stay inside a signed 64-bit
// integer. 3000000000, the value that overflows a 32-bit int, is below this.
inline constexpr std::int64_t kMaxClockMs = std::numeric_limits<std::int64_t>::max() / 256;

// One UCI clock token, in milliseconds, clamped to [0, kMaxClockMs].
// A leading '+' is accepted. A leading '-' clamps to 0. Anything that is not
// a complete integer, including a missing token, is 0. A magnitude that does
// not fit in 64 bits clamps to the ceiling instead of becoming 0.
[[nodiscard]] inline std::int64_t parse_clock_ms(std::string_view text) {
    if (text.empty()) return 0;
    bool negative = false;
    if (text.front() == '+' || text.front() == '-') {
        negative = text.front() == '-';
        text.remove_prefix(1);
        if (text.empty()) return 0;
    }
    std::int64_t value = 0;
    const char* const first = text.data();
    const char* const last = text.data() + text.size();
    const std::from_chars_result parsed = std::from_chars(first, last, value);
    if (parsed.ec == std::errc::result_out_of_range) return negative ? 0 : kMaxClockMs;
    if (parsed.ec != std::errc{} || parsed.ptr != last) return 0;
    if (negative) return 0;
    return value > kMaxClockMs ? kMaxClockMs : value;
}

} // namespace forge
