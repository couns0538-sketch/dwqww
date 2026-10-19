// Forge 6.4 multithreaded TT race reproducer.
//
// This diagnostic intentionally exercises the shared transposition table
// concurrently.  It is expected to trigger ThreadSanitizer with the current
// unsynchronized TTEntry::probe/store implementation.  Do NOT add to the
// normal passing CTest suite until the table has been made race-safe.
//
// Build from the repository root with a TSan-instrumented forge_core:
//
//   cmake -S . -B build-tsan -DCMAKE_BUILD_TYPE=Debug \
//     -DCMAKE_CXX_FLAGS="-O1 -g -fsanitize=thread -fno-omit-frame-pointer"
//   cmake --build build-tsan --target forge_core -j
//   c++ -std=c++20 -O1 -g -fsanitize=thread -fno-omit-frame-pointer \
//     -Iinclude tools/audit/tt_thread_tsan.cpp build-tsan/libforge_core.a \
//     -pthread -o build-tsan/tt_thread_tsan
//   TSAN_OPTIONS="halt_on_error=0" build-tsan/tt_thread_tsan
//
// A non-TSan run succeeding is not a proof of race freedom.
#include "forge/search.hpp"

#include <atomic>
#include <cstdint>
#include <iostream>
#include <thread>

int main() {
    forge::TranspositionTable tt(1);
    constexpr std::uint64_t key = 0x12345678abcdef01ULL;
    bool hit = false;
    auto* initial = tt.probe(key, hit);
    tt.store(initial, key, 1, 0, forge::Move::none(), 1, forge::BoundExact, false);

    std::atomic<int> ready{0};
    std::atomic<bool> start{false};
    std::uint64_t observed_checksum = 0;
    constexpr int iterations = 250000;

    auto synchronize = [&] {
        ready.fetch_add(1, std::memory_order_release);
        while (!start.load(std::memory_order_acquire)) std::this_thread::yield();
    };

    std::thread writer([&] {
        synchronize();
        for (int i = 1; i <= iterations; ++i) {
            bool found = false;
            auto* entry = tt.probe(key, found);
            if (found) {
                tt.store(entry, key, i & 0x7fff, i & 0x1fff,
                         forge::Move::none(), 1 + i % 32, forge::BoundExact, false);
            }
            if ((i & 15) == 0) std::this_thread::yield();
        }
    });

    std::thread reader([&] {
        synchronize();
        std::uint64_t sum = 0;
        for (int i = 1; i <= iterations; ++i) {
            bool found = false;
            const auto* entry = tt.probe(key, found);
            if (found) {
                sum += static_cast<std::uint64_t>(static_cast<std::uint16_t>(entry->score));
                sum += entry->depth;
                sum += entry->gen_bound;
            }
            if ((i & 15) == 0) std::this_thread::yield();
        }
        observed_checksum = sum;
    });

    while (ready.load(std::memory_order_acquire) < 2) std::this_thread::yield();
    start.store(true, std::memory_order_release);
    writer.join();
    reader.join();
    std::cout << "probe/store checksum " << observed_checksum << "\n";
}
