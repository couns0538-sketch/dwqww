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
    // part 4 (fable bug hunt NIT-5): combined differences, low half (score, eval) AND high half (depth, bound/pv,
    // rule50). With a = the low-half difference, B = the high-half difference and u = a * Mul (mod 2^64):
    // y = delta * Mul = u + (B * Mul mod 2^32) * 2^32, so low32(y) = low32(u) and high32(y) = high32(u) + B * Mul
    // (mod 2^32). The delta can collide only for B = -high32(u) * Minv, or (with low32(u) != 0) B = (-high32(u) - 1) *
    // Minv (mod 2^32), Minv = Mul^-1 mod 2^32: at most two residues per a, exact. A residue is realistic if it equals
    // ddepth + 256 * dboundpv + 65536 * drule50 with |ddepth| <= 255, |dboundpv| <= 7, |drule50| <= 100 (padding 0).
    const auto m32 = static_cast<std::uint32_t>(Mul);
    std::uint32_t minv = m32;
    for (int i = 0; i < 5; ++i) minv *= 2U - m32 * minv;
    if (m32 * minv != 1U) { std::printf("modular inverse failed\n"); return 1; }
    constexpr long Box = 4096;   // |score difference|, |eval difference| <= Box as int16 values, with the uint16 wrap
    std::uint64_t scanned4 = 0, bad4 = 0;
    long best_max = -1, best_sum = -1;
    long rec[2][5] = {};   // [0] = smallest max(|ds|,|de|), [1] = smallest |ds|+|de|: ds, de, ddepth, dboundpv, dr50
    auto realistic = [](std::int64_t b, long out[3]) {
        for (std::int64_t dr = b / 65536 - 2; dr <= b / 65536 + 2; ++dr) {
            if (dr < -100 || dr > 100) continue;
            const std::int64_t rem = b - 65536 * dr;
            for (std::int64_t dg = rem / 256 - 2; dg <= rem / 256 + 2; ++dg) {
                if (dg < -7 || dg > 7) continue;
                const std::int64_t dd = rem - 256 * dg;
                if (dd < -255 || dd > 255) continue;
                out[0] = static_cast<long>(dd); out[1] = static_cast<long>(dg); out[2] = static_cast<long>(dr);
                return true;
            }
        }
        return false;
    };
    for (long ts = -Box; ts <= Box; ++ts) {
        const long sw[3] = {ts, ts > 0 ? ts - 65536 : (ts < 0 ? ts + 65536 : 0), 0};
        const int ns = ts == 0 ? 1 : 2;
        for (long te = -Box; te <= Box; ++te) {
            const long ew[3] = {te, te > 0 ? te - 65536 : (te < 0 ? te + 65536 : 0), 0};
            const int ne = te == 0 ? 1 : 2;
            for (int i = 0; i < ns; ++i) {
                for (int j = 0; j < ne; ++j) {
                    const std::int64_t a = static_cast<std::int64_t>(sw[i]) + 65536 * static_cast<std::int64_t>(ew[j]);
                    if (a == 0) continue;   // pure high-part differences: part 2
                    ++scanned4;
                    const std::uint64_t u = static_cast<std::uint64_t>(a) * Mul;
                    const auto uh = static_cast<std::uint32_t>(u >> 32U);
                    const auto ul = static_cast<std::uint32_t>(u);
                    const std::uint32_t cands[2] = {(0U - uh) * minv, (0U - uh - 1U) * minv};
                    for (int c = 0; c < (ul != 0U ? 2 : 1); ++c) {
                        const auto b = static_cast<std::int64_t>(static_cast<std::int32_t>(cands[c]));
                        if (b < -(255 + 256 * 7 + 65536 * 100) || b > 255 + 256 * 7 + 65536 * 100) continue;
                        long fields[3];
                        if (!realistic(b, fields)) continue;
                        ++bad4;
                        const long mx = std::labs(ts) > std::labs(te) ? std::labs(ts) : std::labs(te);
                        const long sm = std::labs(ts) + std::labs(te);
                        const long row[5] = {ts, te, fields[0], fields[1], fields[2]};
                        if (best_max < 0 || mx < best_max) { best_max = mx; for (int k = 0; k < 5; ++k) rec[0][k] = row[k]; }
                        if (best_sum < 0 || sm < best_sum) { best_sum = sm; for (int k = 0; k < 5; ++k) rec[1][k] = row[k]; }
                    }
                }
            }
        }
    }
    // Counts are of (score, eval) field-difference LABELS: through the uint16 wrap one stored low-half difference can
    // carry two labels, (ts, te) and (ts -+ 65536, te +- 1), so a delta may be counted twice (fable bug hunt NIT-7).
    // Numerator and denominator are counted the same way, so the density and the minima below are unaffected.
    std::printf("part4: combined deltas, |dscore|,|deval| <= %ld (int16, with the uint16 wrap) x every realistic depth/bound-pv/rule50 "
                "difference: %llu (score, eval) difference labels scanned, %llu (label, high-half) combinations can collide "
                "(a stored delta can carry two labels through the wrap)\n",
                Box, static_cast<unsigned long long>(scanned4), static_cast<unsigned long long>(bad4));
    if (best_max >= 0) {
        std::printf("  smallest max(|dscore|,|deval|) = %ld: dscore %ld deval %ld ddepth %ld dboundpv %ld drule50 %ld\n", best_max,
                    rec[0][0], rec[0][1], rec[0][2], rec[0][3], rec[0][4]);
        std::printf("  smallest |dscore|+|deval|     = %ld: dscore %ld deval %ld ddepth %ld dboundpv %ld drule50 %ld\n", best_sum,
                    rec[1][0], rec[1][1], rec[1][2], rec[1][3], rec[1][4]);
    }
    const bool ok = bad2 == 0 && bad3 == 0;
    std::printf("RESULT %s\n", ok ? "PASS (parts 2 and 3 never collide; parts 1 and 4 are censuses)" : "FAIL");
    return ok ? 0 : 1;
}
