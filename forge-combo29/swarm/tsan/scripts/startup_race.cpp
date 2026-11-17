// Startup-init check under ThreadSanitizer.
//
// The prior branch (grok47/t13-thread-sanitizer, base 16833ecc) found a real
// data race in attacks::init(): a plain `static bool initialized` was stored
// BEFORE the tables were filled, so a second thread could skip the fill and
// read half-built attack tables, and could index through a null Magic::table.
//
// On 6b98f217 that code is `std::call_once` (src/bitboard.cpp:139-143).
// This harness constructs Boards concurrently from a cold process, which is
// the only condition that ever exposed the old race: the first Board is
// normally built on one thread, and Searcher builds its workers only after the
// caller's Board already exists.
//
// It reports the start-position legal-move count from every thread, because a
// torn attack-table fill shows up as a move count other than 20.
#include "forge/board.hpp"

#include <array>
#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

int main() {
    constexpr int kThreads = 4;
    constexpr int kRounds = 50;

    // A barrier so every thread enters Board() as close together as possible.
    std::atomic<int> ready{0};
    std::atomic<bool> go{false};
    std::array<int, kThreads> counts{};
    std::array<unsigned long, kThreads> perfts{};

    std::vector<std::thread> ts;
    for (int t = 0; t < kThreads; ++t) {
        ts.emplace_back([&, t] {
            ready.fetch_add(1);
            while (!go.load(std::memory_order_acquire)) {
            }
            int first_count = -1;
            unsigned long total = 0;
            for (int r = 0; r < kRounds; ++r) {
                forge::Board b;  // first construction calls attacks::init()
                const auto moves = b.legal_moves();
                if (first_count < 0) first_count = static_cast<int>(moves.size());
                // perft reads the pawn/knight/king tables and the magic sliders.
                total += b.perft(2);
            }
            counts[t] = first_count;
            perfts[t] = total;
        });
    }
    while (ready.load() != kThreads) {
    }
    go.store(true, std::memory_order_release);
    for (auto& th : ts) th.join();

    bool ok = true;
    for (int t = 0; t < kThreads; ++t) {
        const bool this_ok = counts[t] == 20 && perfts[t] == 50UL * 400UL;
        if (!this_ok) ok = false;
        std::cout << "thread " << t << " legal_moves " << counts[t] << " perft2_total " << perfts[t]
                  << (this_ok ? " OK" : " BAD") << "\n";
    }
    std::cout << (ok ? "STARTUP_INIT_CLEAN" : "STARTUP_INIT_BROKEN") << std::endl;
    return ok ? 0 : 1;
}
