// Regression for audit finding 8 (audit/lock-source 302a08a2).
// A store used to write the slot captured at probe time. After a colliding key
// takes that slot and a deeper entry for the same position lands elsewhere,
// the late shallow store duplicated the key and probe returned the shallow copy.
// This is the proof sequence from tests_audit/proof_tt_duplicate_shadow.cpp.
//
// Build (ASan + UBSan), from the repo root:
//   g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer
//   -ffp-contract=off -fno-fast-math -march=x86-64-v3
//   -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2
//   -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1
//   -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0
//   -Iforge-combo29/include forge-combo29/tests_r3_24/proof_tt_duplicate_shadow.cpp
//   forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp
//   forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp
//   forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp
//   -lpthread -o /tmp/proof_tt_duplicate_shadow

#include "forge/search.hpp"

#include <cstdint>
#include <iostream>

namespace {

bool visible(const forge::TTProbe& probe, int depth, int score) {
    return probe.hit && static_cast<int>(probe.entry.depth) == depth && probe.entry.score == score;
}

}  // namespace

int main() {
    forge::TranspositionTable tt(1);

    const std::uint64_t key_a = 0x4242424211111111ULL;
    const std::uint64_t key_other = 0x4242424222222222ULL;

    const forge::TTProbe p_shallow = tt.probe(key_a);

    const forge::TTProbe p_other = tt.probe(key_other);
    tt.store(p_other, key_other, 15, 15, forge::Move{12, 28, 0, 0}, 3, forge::BoundExact, false, 0);

    const forge::TTProbe p_deep = tt.probe(key_a);
    tt.store(p_deep, key_a, 777, 100, forge::Move{6, 21, 0, 0}, 14, forge::BoundExact, true, 0);
    const forge::TTProbe deep = tt.probe(key_a);
    std::cout << "After deep store: probe(key_a) hit=" << deep.hit
              << " depth=" << static_cast<int>(deep.entry.depth)
              << " score=" << deep.entry.score << "\n";
    if (!visible(deep, 14, 777)) {
        std::cerr << "FAIL deep store was not visible\n";
        return 1;
    }

    tt.store(p_shallow, key_a, -50, 100, forge::Move{8, 16, 0, 0}, 2, forge::BoundUpper, false, 0);

    const forge::TTProbe after = tt.probe(key_a);
    const forge::TTProbe other = tt.probe(key_other);
    std::cout << "After late shallow store: probe(key_a) hit=" << after.hit
              << " depth=" << static_cast<int>(after.entry.depth)
              << " score=" << after.entry.score
              << " bound=" << static_cast<int>(after.entry.bound()) << "\n";
    std::cout << "probe(key_other) hit=" << other.hit
              << " depth=" << static_cast<int>(other.entry.depth)
              << " score=" << other.entry.score << "\n";

    if (!visible(after, 14, 777) || after.entry.bound() != forge::BoundExact) {
        std::cerr << "FAIL shallow store shadowed the deeper entry\n";
        return 1;
    }
    if (after.entry.move.from != 6 || after.entry.move.to != 21) {
        std::cerr << "FAIL shallow store replaced the deeper move\n";
        return 1;
    }
    if (!visible(other, 3, 15) || other.entry.bound() != forge::BoundExact) {
        std::cerr << "FAIL colliding key was overwritten\n";
        return 1;
    }
    std::cout << "PASS deep entry stays visible\n";
    return 0;
}
