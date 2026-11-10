// tag_scan.cpp - opus2 SMP pack tool (NOT part of the engine; needs FORGE_SMP_LAYOUT=1).
// Exact census of the data-word differences that can keep the lockless tag forge::ttlockless::tag32 (SPEC 3.3).
// For D1 != D2 (generation bits cleared) with delta = D1 - D2 mod 2^64: tag32(D1) == tag32(D2) is possible only if the
// high 32 bits of delta * TagMul mod 2^64 are all zeros or all ones (tag = high32(x + y) vs high32(x), y = delta *
// TagMul, high32(x + y) = high32(x) + high32(y) + carry). Every other delta can never collide, whatever D1 and D2 are.
//   part 1: all 2^32 - 1 positive deltas below 2^32 (score/eval-only differences; -delta is symmetric) - exhaustive;
//   part 2: deltas confined to bits 32..63 (depth, bound, pv, rule50): never (odd multiplier, no carry), checked for all
//           2 * (2^24 - 1) differences of bits 32..55 that real entries can carry (padding is always 0);
//   part 3: every single-bit delta (both signs) outside the generation bits.
// Usage: tag_scan   (single-threaded; pin it from outside: run_pinned.ps1, CPUs 12-15, Idle)
#include "forge/search.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>

#if !FORGE_SMP_LAYOUT
#error "tag_scan needs FORGE_SMP_LAYOUT=1"
#endif

namespace {
constexpr std::uint64_t Mul = forge::ttlockless::TagMul;

// Exact: high32(x + y) == high32(x) for some x iff high32(y) == 0 (no carry needed) or high32(y) == 0xFFFFFFFF with a
// non-zero low half (a carry is then possible).
bool can_collide(std::uint64_t delta) {
    const std::uint64_t y = delta * Mul;
    const auto high = static_cast<std::uint32_t>(y >> 32U);
    const auto low = static_cast<std::uint32_t>(y);
    return high == 0U || (high == 0xFFFFFFFFU && low != 0U);
}

// Smallest signed difference of two int16 fields whose uint16 words differ by u (mod 2^16).
long small16(long u) {
    u = ((u % 65536) + 65536) % 65536;
    return u <= 32768 ? u : u - 65536;
}
} // namespace

int main() {
    std::printf("tag_scan: TagMul 0x%016llX\n", static_cast<unsigned long long>(Mul));
    // part 1
    std::uint64_t bad1 = 0;
    long best_cost = -1;
    for (std::uint64_t a = 1; a < (1ULL << 32U); ++a) {
        if (!can_collide(a)) continue;
        ++bad1;
        // a = dscore + 65536 * deval with dscore in [0, 65536) (or dscore - 65536 with deval + 1): the int16 views.
        const long ds = small16(static_cast<long>(a & 0xFFFFU));
        const long de = small16(static_cast<long>(a >> 16U) + (ds < 0 ? 1 : 0));
        const long cost = std::labs(ds) + std::labs(de);
        if (best_cost < 0 || cost < best_cost) best_cost = cost;
        if (bad1 <= 40) {
            std::printf("  part1 delta 0x%08llX: score diff %ld, eval diff %ld (as int16 field differences)\n",
                        static_cast<unsigned long long>(a), ds, de);
        }
    }
    std::printf("part1: score/eval-only deltas that can collide: %llu of %llu (x2 with the negative ones); smallest |dscore|+|deval| %ld\n",
                static_cast<unsigned long long>(bad1), static_cast<unsigned long long>((1ULL << 32U) - 1U), best_cost);
    // part 2: two entries that differ only in bits 32..55 differ by B * 2^32 with 0 < |B| < 2^24 (borrows included).
    std::uint64_t bad2 = 0, scanned2 = 0;
    for (std::int64_t b = -((std::int64_t{1} << 24) - 1); b < (std::int64_t{1} << 24); ++b) {
        if (b == 0) continue;
        ++scanned2;
        if (can_collide(static_cast<std::uint64_t>(b) << 32U)) ++bad2;
    }
    std::printf("part2: high-part-only deltas (bits 32..55, all differences incl. borrows): %llu scanned, %llu can collide\n",
                static_cast<unsigned long long>(scanned2), static_cast<unsigned long long>(bad2));
    // part 3
    int bad3 = 0, scanned3 = 0;
    for (int bit = 0; bit < 64; ++bit) {
        if ((forge::ttlockless::GenMask >> bit) & 1U) continue;
        ++scanned3;
        const std::uint64_t up = 1ULL << bit;
        if (can_collide(up) || can_collide(0U - up)) ++bad3;
    }
    std::printf("part3: single-bit deltas: %d bits x 2 signs, %d can collide\n", scanned3, bad3);
    const bool ok = bad2 == 0 && bad3 == 0;
    std::printf("RESULT %s\n", ok ? "PASS (parts 2 and 3 never collide; part 1 census above)" : "FAIL");
    return ok ? 0 : 1;
}
