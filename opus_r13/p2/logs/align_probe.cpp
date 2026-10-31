// R13 P2 1a probe: address mod 64 of the weight blocks as the engine allocates them (same helpers as nnue.cpp /
// nnue_halfka.cpp). Several allocations, interleaved with other heap use, like a real start-up.
#include "forge/large_pages.hpp"
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>
int main() {
    using namespace forge::large_pages;
    std::vector<std::string> noise;
    for (int round = 0; round < 4; ++round) {
        noise.emplace_back(std::string(37 + round * 13, 'x'));
        Report r;
        Array<float> w1 = make_weight_array<float>(768 * 256, false, r);
        WeightVector<std::int8_t> ft(static_cast<std::size_t>(22528) * 1024, 0);
        WeightVector<std::int16_t> bias(1024, 0);
        std::printf("round %d: w1 %%64 = %u, ft_weight %%64 = %u, ft_bias %%64 = %u\n", round,
                    static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(w1.get()) % 64),
                    static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(ft.data()) % 64),
                    static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(bias.data()) % 64));
    }
}
