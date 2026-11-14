// Proof for Finding 8 (MEDIUM):
// src/search.cpp:270-347 — `TranspositionTable::store` writes to the probe-time `probe.slot_`
// without re-scanning the 4-entry cluster. If `key` was stored into another slot while searching
// its subtree (via helper threads or transposition + cluster collision) and `probe.slot_` now
// holds a colliding key `other_key`, `same_position` is false, so `store` writes a duplicate
// shallow entry for `key` into `probe.slot_ = 0` that permanently shadows the deeper entry in
// `slot 1` (since `probe` returns the first matching slot).
//
// Build & run (ASan + UBSan):
//   g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
//     -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
//     -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
//     -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
//     -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
//     -Iforge-combo29/include forge-combo29/tests_audit/proof_tt_duplicate_shadow.cpp \
//     forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
//     forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
//     forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
//     -lpthread -o /tmp/proof_tt_duplicate_shadow
//   /tmp/proof_tt_duplicate_shadow

#include "forge/search.hpp"

#include <iostream>

int main() {
    forge::TranspositionTable tt(1); // 16384 clusters (high 14 bits select cluster under 128-bit mul-high)

    // Two distinct 64-bit keys with identical top 32 bits (same cluster) and distinct low 32 bits (verification_key):
    const std::uint64_t key_a     = 0x42424242'11111111ULL;
    const std::uint64_t key_other = 0x42424242'22222222ULL;

    // 1. Shallow search on Thread 1 probes `key_a` -> miss, selects empty `slot 0`.
    const forge::TTProbe p_shallow = tt.probe(key_a);

    // 2. Child node `key_other` (same cluster) probes -> miss (`slot 0`), stores `key_other` in `slot 0`.
    const forge::TTProbe p_other = tt.probe(key_other);
    tt.store(p_other, key_other, 15, 15, forge::Move{12, 28, 0, 0}, 3, forge::BoundExact, false, 0);

    // 3. Helper Thread 2 (or transposition) probes `key_a` -> sees `key_other` in `slot 0`, selects `slot 1`,
    //    and stores a DEEP `depth = 14` exact score `777` for `key_a` in `slot 1`!
    const forge::TTProbe p_deep = tt.probe(key_a);
    tt.store(p_deep, key_a, 777, 100, forge::Move{6, 21, 0, 0}, 14, forge::BoundExact, true, 0);
    std::cout << "After deep store: probe(key_a) hit=" << tt.probe(key_a).hit
              << " depth=" << static_cast<int>(tt.probe(key_a).entry.depth)
              << " score=" << tt.probe(key_a).entry.score << "\n";

    // 4. Thread 1 finishes its shallow `depth = 2` search and stores via `p_shallow` (`slot 0`):
    //    Because `slot 0` holds `key_other`, `same_position` is false, bypassing `depth + 4 > entry->depth`,
    //    creating a duplicate `key_a` in `slot 0` at `depth = 2` that shadows `slot 1` (`depth = 14`)!
    tt.store(p_shallow, key_a, -50, 100, forge::Move{8, 16, 0, 0}, 2, forge::BoundUpper, false, 0);

    const forge::TTProbe after = tt.probe(key_a);
    std::cout << "After late shallow store: probe(key_a) hit=" << after.hit
              << " depth=" << static_cast<int>(after.entry.depth)
              << " score=" << after.entry.score
              << " (depth=14 score=777 in slot 1 is now shadowed by duplicate depth=2 in slot 0!)\n";
    return 0;
}
