// Proof for Finding 1 (HIGH):
// src/bitboard.cpp:136-140 — attacks::init() uses an unsynchronized `static bool initialized`
// and sets `initialized = true` BEFORE populating RookMagics / BishopMagics / attack tables.
// Concurrent construction of forge::Board on two threads at startup triggers a data race
// (ThreadSanitizer) and a nullptr dereference SIGSEGV in attacks::bishop/rook (AddressSanitizer).
//
// Build & run (ThreadSanitizer):
//   g++ -std=c++20 -O2 -g -fsanitize=thread -fno-omit-frame-pointer \
//     -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
//     -Iforge-combo29/include forge-combo29/tests_audit/proof_attacks_init_race.cpp \
//     forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp -lpthread -o /tmp/proof_init_tsan
//   /tmp/proof_init_tsan
//
// Build & run (AddressSanitizer + UBSan):
//   g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
//     -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
//     -Iforge-combo29/include forge-combo29/tests_audit/proof_attacks_init_race.cpp \
//     forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp -lpthread -o /tmp/proof_init_asan
//   /tmp/proof_init_asan

#include "forge/board.hpp"

#include <atomic>
#include <chrono>
#include <iostream>
#include <thread>

int main() {
    std::atomic<int> ready{0};
    std::atomic<bool> go{false};
    std::uint64_t sum = 0;

    std::thread t1([&] {
        ready.fetch_add(1, std::memory_order_release);
        while (!go.load(std::memory_order_acquire)) {}
        forge::Board b1;
        sum += b1.legal_moves().size();
    });

    std::thread t2([&] {
        ready.fetch_add(1, std::memory_order_release);
        while (!go.load(std::memory_order_acquire)) {}
        // Delay ~100 us so t1 enters attacks::init() and sets initialized = true
        // while still searching for RookMagics / BishopMagics.
        std::this_thread::sleep_for(std::chrono::microseconds(100));
        forge::Board b2;
        sum += b2.legal_moves().size();
    });

    while (ready.load(std::memory_order_acquire) < 2) {}
    go.store(true, std::memory_order_release);

    t1.join();
    t2.join();
    std::cout << "Completed with legal move sum: " << sum << "\n";
    return 0;
}
