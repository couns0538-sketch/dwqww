#include "forge/go_numbers.hpp"

#include <cstdint>
#include <iostream>
#include <limits>
#include <optional>
#include <string>

namespace {

int failures = 0;

void expect_i64(const char* text, std::int64_t want) {
    const std::int64_t got = forge::parse_i64_token(text);
    if (got != want) {
        std::cout << "fail parse_i64_token(\"" << text << "\") got " << got << " want " << want << "\n";
        ++failures;
    }
}

void expect_clock(const char* text, std::int64_t want) {
    const std::int64_t got = forge::clamp_clock_ms(forge::parse_i64_token(text));
    if (got != want) {
        std::cout << "fail clamp_clock_ms(parse(\"" << text << "\")) got " << got << " want " << want << "\n";
        ++failures;
    }
}

void expect_u64(const char* text, std::optional<std::uint64_t> want) {
    const std::optional<std::uint64_t> got = forge::parse_u64_token(text);
    if (got != want) {
        std::cout << "fail parse_u64_token(\"" << text << "\") got ";
        if (got) std::cout << *got;
        else std::cout << "nullopt";
        std::cout << " want ";
        if (want) std::cout << *want;
        else std::cout << "nullopt";
        std::cout << "\n";
        ++failures;
    }
}

} // namespace

int main() {
    expect_i64("3000000000", 3000000000LL);
    expect_i64("+3000000000", 3000000000LL);
    expect_i64("03000000000", 3000000000LL);
    expect_i64("+03000000000", 3000000000LL);
    expect_i64("2147483647", 2147483647LL);
    expect_i64("2147483648", 2147483648LL);
    expect_i64("+80", 80);
    expect_i64("+00080", 80);
    expect_i64("80", 80);
    expect_i64("0", 0);
    expect_i64("+0", 0);
    expect_i64("-0", 0);
    expect_i64("-80", -80);
    expect_i64("-3000000000", -3000000000LL);
    expect_clock("-80", 0);
    expect_clock("-3000000000", 0);
    expect_clock("3000000000", 3000000000LL);
    expect_clock("+3000000000", 3000000000LL);
    expect_clock("0", 0);
    expect_clock("+0", 0);

    expect_i64("zz", 0);
    expect_i64("", 0);
    expect_i64("+", 0);
    expect_i64("++80", 0);
    expect_i64("+-80", 0);
    expect_i64("+80ms", 0);
    expect_i64("80ms", 0);
    expect_clock("zz", 0);
    expect_clock("+80ms", 0);

    constexpr std::int64_t kInt64Max = std::numeric_limits<std::int64_t>::max();
    expect_i64("9223372036854775807", kInt64Max);
    expect_i64("9223372036854775808", kInt64Max);
    expect_i64("+999999999999999999999", kInt64Max);
    expect_i64("-9223372036854775808", std::numeric_limits<std::int64_t>::min());
    expect_i64("-999999999999999999999", std::numeric_limits<std::int64_t>::min());
    expect_clock("999999999999999999999", forge::kMaxClockMs);
    expect_clock("+999999999999999999999", forge::kMaxClockMs);
    expect_clock("-999999999999999999999", 0);
    expect_clock("9223372036854775807", forge::kMaxClockMs);

    expect_u64("1000", 1000ULL);
    expect_u64("+1000", 1000ULL);
    expect_u64("+0001000", 1000ULL);
    expect_u64("0", 0ULL);
    expect_u64("+0", 0ULL);
    expect_u64("18446744073709551615", std::numeric_limits<std::uint64_t>::max());
    expect_u64("+18446744073709551615", std::numeric_limits<std::uint64_t>::max());
    expect_u64("18446744073709551616", std::numeric_limits<std::uint64_t>::max());
    expect_u64("+999999999999999999999", std::numeric_limits<std::uint64_t>::max());
    expect_u64("-1", std::nullopt);
    expect_u64("-1000", std::nullopt);
    expect_u64("zz", std::nullopt);
    expect_u64("+", std::nullopt);
    expect_u64("++1000", std::nullopt);
    expect_u64("+1000ms", std::nullopt);
    expect_u64("", std::nullopt);

    if (failures != 0) {
        std::cout << "fail " << failures << "\n";
        return 1;
    }
    std::cout << "pass\n";
    return 0;
}
