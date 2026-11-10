#include "forge/bitboard.hpp"
#include <barrier>
#include <thread>
#include <vector>
#include <iostream>
#include <array>
int main() {
    std::barrier gate(16);
    std::array<bool, 16> complete{};
    std::vector<std::thread> threads;
    for (int i = 0; i < 16; ++i) threads.emplace_back([&, i] {
        gate.arrive_and_wait();
        forge::attacks::init();
        complete[i] = forge::attacks::BetweenTable[0][7] == 0x7EULL;
    });
    for (auto& thread : threads) thread.join();
    for (bool result : complete) if (!result) {
        std::cerr << "FAIL: init returned before BetweenTable was ready\n";
        return 1;
    }
    std::cout << "PASS: concurrent initialization\n";
}
