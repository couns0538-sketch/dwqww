#include "forge/search.hpp"
#include <array>
#include <iostream>

int main() {
    struct Case { int score; unsigned depth, stored, read; bool expected; };
    const std::array<Case, 9> cases{{
        {forge::MateValue - 15, 16, 0, 88, false},
        {400, 16, 0, 88, false},
        {400, 5, 0, 88, true},
        {forge::MateValue - 15, 16, 0, 0, true},
        {forge::MateValue - 11, 9, 91, 91, true},
        {400, 8, 95, 95, true},
        {forge::MateValue - 5, 9, 91, 92, false},
        {400, 3, 90, 91, false},
        {forge::MateValue - 5, 9, 10, 40, true}
    }};
    unsigned failures = 0;
    for (unsigned i = 0; i < cases.size(); ++i) {
        const auto& c = cases[i];
        forge::TTEntry entry{};
        entry.score = static_cast<std::int16_t>(c.score);
        entry.depth = static_cast<std::uint8_t>(c.depth);
        entry.rule50_clock = static_cast<std::uint8_t>(c.stored);
        const bool got = entry.score_usable(static_cast<std::uint16_t>(c.read));
        failures += got != c.expected;
        std::cout << "row=" << i + 1 << " score=" << c.score
                  << " depth=" << c.depth << " stored=" << c.stored
                  << " read=" << c.read << " expected=" << c.expected
                  << " got=" << got << '\n';
    }
    std::cout << "cases=" << cases.size() << " failures=" << failures << '\n';
    return failures ? 1 : 0;
}
