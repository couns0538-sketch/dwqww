#include "forge/search.hpp"

#include <array>
#include <cstdint>
#include <iostream>

int main() {
    struct Case {
        int score;
        int depth;
        int stored_clock;
        int read_clock;
        bool expected;
    };
    const std::array<Case, 9> cases{{
        {forge::MateValue - 15, 16, 0, 88, false},
        {400, 16, 0, 88, false},
        {400, 5, 0, 88, true},
        {forge::MateValue - 15, 16, 0, 0, true},
        {forge::MateValue - 11, 9, 91, 91, true},
        {400, 8, 95, 95, true},
        {forge::MateValue - 5, 9, 91, 92, false},
        {400, 3, 90, 91, false},
        {forge::MateValue - 5, 9, 10, 40, true},
    }};
    int failures = 0;
    for (std::size_t index = 0; index < cases.size(); ++index) {
        const auto& test = cases[index];
        forge::TTEntry entry;
        entry.score = static_cast<std::int16_t>(test.score);
        entry.depth = static_cast<std::uint8_t>(test.depth);
        entry.rule50_clock = static_cast<std::uint8_t>(test.stored_clock);
        const bool got = entry.score_usable(static_cast<std::uint16_t>(test.read_clock));
        failures += got != test.expected;
        std::cout << "case=" << index + 1 << " score=" << test.score
                  << " depth=" << test.depth << " stored=" << test.stored_clock
                  << " read=" << test.read_clock << " expected=" << test.expected
                  << " got=" << got << '\n';
    }
    std::cout << "SUMMARY cases=" << cases.size() << " failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
