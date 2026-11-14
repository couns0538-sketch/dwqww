#pragma once

#include <algorithm>
#include <charconv>
#include <cstdint>
#include <limits>
#include <optional>
#include <string>
#include <system_error>

namespace forge {

// Ceiling for wtime/btime/winc/binc/movetime. The time formula multiplies an
// increment by TmIncrementPercent (option max 150) and a soft limit by
// TmHardSoftMultiple (option max 20), so the stored value has to leave
// headroom in int64. 3000000000 ms fits.
inline constexpr std::int64_t kMaxClockMs = std::numeric_limits<std::int64_t>::max() / 150;
static_assert(kMaxClockMs > 3000000000LL);
static_assert(kMaxClockMs / 5 + (kMaxClockMs * 150) / 100 <=
              std::numeric_limits<std::int64_t>::max() / 20);

// One go-command integer. Accepts a single leading '+', which std::from_chars
// rejects. A value outside int64 clamps to that range. Junk or a second sign
// yields 0, matching the old failed parse.
[[nodiscard]] inline std::int64_t parse_i64_token(const std::string& text) {
    if (text.empty()) return 0;
    const char* begin = text.data();
    const char* end = text.data() + text.size();
    if (*begin == '+') {
        ++begin;
        if (begin == end || *begin == '+' || *begin == '-') return 0;
    }
    std::int64_t value = 0;
    const auto result = std::from_chars(begin, end, value);
    if (result.ptr != end) return 0;
    if (result.ec == std::errc::result_out_of_range) {
        return text[0] == '-' ? std::numeric_limits<std::int64_t>::min()
                              : std::numeric_limits<std::int64_t>::max();
    }
    if (result.ec != std::errc{}) return 0;
    return value;
}

[[nodiscard]] inline std::int64_t clamp_clock_ms(std::int64_t value) {
    return std::clamp(value, std::int64_t{0}, kMaxClockMs);
}

// Node budget. A single leading '+' is accepted. Overflow clamps to the top
// of uint64. A minus sign or junk returns nullopt so the limit stays unset,
// which is what the old uint64 parse did for those tokens.
[[nodiscard]] inline std::optional<std::uint64_t> parse_u64_token(const std::string& text) {
    if (text.empty()) return std::nullopt;
    const char* begin = text.data();
    const char* end = text.data() + text.size();
    if (*begin == '+') {
        ++begin;
        if (begin == end || *begin == '+' || *begin == '-') return std::nullopt;
    }
    if (begin != end && *begin == '-') return std::nullopt;
    std::uint64_t value = 0;
    const auto result = std::from_chars(begin, end, value);
    if (result.ptr != end) return std::nullopt;
    if (result.ec == std::errc::result_out_of_range) {
        return std::numeric_limits<std::uint64_t>::max();
    }
    if (result.ec != std::errc{}) return std::nullopt;
    return value;
}

} // namespace forge
