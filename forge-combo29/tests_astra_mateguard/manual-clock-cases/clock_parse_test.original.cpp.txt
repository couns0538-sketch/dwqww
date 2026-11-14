// Clock tokens used by `go wtime`, `go btime`, `go winc`, `go binc`, and
// `go movetime`. Compile against include/:
//   g++ -std=c++20 -Wall -Wextra -Werror -I forge-combo29/include
//       forge-combo29/tests_t3/clock_parse_test.cpp -o /tmp/clock_parse_test
// The lock tree has no parse_clock_ms, so this file does not build there.
#include "forge/uci_clock.hpp"

#include <cstdint>
#include <iostream>
#include <string_view>

namespace {

int failures = 0;

void expect(std::string_view text, std::int64_t want, std::string_view name) {
    const std::int64_t got = forge::parse_clock_ms(text);
    if (got == want) return;
    std::cerr << "FAIL " << name << " text=[" << text << "] got " << got << " want " << want << '\n';
    ++failures;
}

} // namespace

int main() {
    expect("3000000000", 3000000000LL, "wtime above 32 bits");
    expect("+80", 80, "movetime plus 80");
    expect("+00080", 80, "plus and leading zeros");
    expect("80", 80, "plain 80");
    expect("0", 0, "zero");
    expect("-80", 0, "negative clamps to zero");
    expect("-0", 0, "negative zero");
    expect("-", 0, "bare minus");
    expect("+", 0, "bare plus");
    expect("++80", 0, "double plus is malformed");
    expect("+-80", 0, "plus then minus is malformed");
    expect("-+80", 0, "minus then plus is malformed");
    expect("+80x", 0, "trailing junk");
    expect("9223372036854775808x", 0, "overflow with trailing junk");
    expect("999999999999999999999abc", 0, "far overflow with trailing junk");
    expect("12x", 0, "trailing letter");
    expect("abc", 0, "letters");
    expect("1.5", 0, "decimal");
    expect("", 0, "empty");
    expect("9223372036854775807", forge::kMaxClockMs, "int64 max clamps");
    expect("9223372036854775808", forge::kMaxClockMs, "one past int64 max clamps");
    expect("999999999999999999999", forge::kMaxClockMs, "far overflow clamps");
    expect("-999999999999999999999", 0, "negative overflow clamps to zero");
    if (3000000000LL > forge::kMaxClockMs) {
        std::cerr << "FAIL ceiling is below 3000000000\n";
        ++failures;
    }
    if (failures != 0) {
        std::cerr << failures << " failed\n";
        return 1;
    }
    std::cout << "clock_parse_test passed\n";
    return 0;
}
