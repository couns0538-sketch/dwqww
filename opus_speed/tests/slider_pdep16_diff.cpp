// slider_pdep16_diff.cpp - FORGE_SPD_SLIDER_PDEP16 proof harness (speed hunt vs trial_w6, own code).
// attacks::rook / attacks::bishop (PEXT index, 16-bit entries rebuilt with PDEP) must equal an independent ray walk for
// every square and every subset of the relevant occupancy mask, each also with 3 random sets of bits outside the mask
// (a lookup must ignore them), plus 2M random full-board occupancies. -DMUTANT=1 flips bit 0 of one rook entry
// through the public table pointer (must FAIL). Build from a hunt tree root:
//   g++ -std=c++20 -O2 -march=znver5 -Iinclude -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_SLIDER_PDEP16=1
//   tests/slider_pdep16_diff.cpp src/bitboard.cpp -o slider_diff.exe
#include "forge/bitboard.hpp"

#include <cstdio>
#include <cstdint>

#if !FORGE_SPD_SLIDER_PDEP16
#error "build with -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_SLIDER_PDEP16=1"
#endif

namespace {
using forge::Bitboard;

Bitboard walk(int square, Bitboard occupancy, bool rook) {
    static const int rd[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    static const int bd[4][2] = {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}};
    const int (*d)[2] = rook ? rd : bd;
    Bitboard result = 0;
    for (int k = 0; k < 4; ++k) {
        int f = square % 8, r = square / 8;
        for (;;) {
            f += d[k][0];
            r += d[k][1];
            if (f < 0 || f > 7 || r < 0 || r > 7) break;
            const Bitboard bit = 1ULL << (r * 8 + f);
            result |= bit;
            if (occupancy & bit) break;
        }
    }
    return result;
}

std::uint64_t rng_state = 0x9E3779B97F4A7C15ULL;
std::uint64_t next() {
    rng_state ^= rng_state >> 12;
    rng_state ^= rng_state << 25;
    rng_state ^= rng_state >> 27;
    return rng_state * 2685821657736338717ULL;
}
} // namespace

int main() {
    forge::attacks::init();
#if MUTANT
    forge::attacks::RookMagics[27].table[5] ^= 1U;
#endif
    std::uint64_t compared = 0, mismatches = 0;
    for (int rook = 0; rook < 2; ++rook) {
        for (int square = 0; square < 64; ++square) {
            const forge::attacks::Magic& m = rook ? forge::attacks::RookMagics[static_cast<std::size_t>(square)]
                                                  : forge::attacks::BishopMagics[static_cast<std::size_t>(square)];
            Bitboard subset = 0;
            do {
                for (int noise = 0; noise < 4; ++noise) {
                    const Bitboard occ = subset | (noise == 0 ? 0 : (next() & ~m.mask));
                    const Bitboard got = rook ? forge::attacks::rook(square, occ) : forge::attacks::bishop(square, occ);
                    ++compared;
                    if (got != walk(square, occ, rook != 0) && ++mismatches <= 5) {
                        std::printf("MISMATCH %s square %d occ %016llx\n", rook ? "rook" : "bishop", square,
                                    static_cast<unsigned long long>(occ));
                    }
                }
                subset = (subset - m.mask) & m.mask;
            } while (subset != 0);
        }
    }
    for (int i = 0; i < 2000000; ++i) {
        const Bitboard occ = next() & next();
        const int square = static_cast<int>(next() & 63U);
        compared += 2;
        if (forge::attacks::rook(square, occ) != walk(square, occ, true)) ++mismatches;
        if (forge::attacks::bishop(square, occ) != walk(square, occ, false)) ++mismatches;
    }
    std::printf("slider_pdep16_diff: %llu lookups compared, %llu mismatches -> %s\n",
                static_cast<unsigned long long>(compared), static_cast<unsigned long long>(mismatches),
                mismatches == 0 ? "PASS" : "FAIL");
    return mismatches == 0 ? 0 : 1;
}
