#include "forge/bitboard.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>

using namespace forge;

static_assert(nearest_square_distance(0, 0) == 7);
static_assert(nearest_square_distance(0, square_bb(63)) == 7);
static_assert(nearest_square_distance(0, square_bb(0) | square_bb(63)) == 0);
static_assert(nearest_square_distance(7, square_bb(8) | square_bb(63)) == 7);
static_assert(nearest_square_distance(27, square_bb(36) | square_bb(56)) == 1);
static_assert(nearest_square_distance(0, ~square_bb(0)) == 1);

// Explicit minimum, independent of the production table and index decisions.
int scalar_reference(int square, Bitboard targets) {
    int nearest = 7;
    for (int target = 0; target < 64; ++target) {
        if ((targets & square_bb(target)) == 0) continue;
        const int df = std::abs(square % 8 - target % 8);
        const int dr = std::abs(square / 8 - target / 8);
        nearest = std::min(nearest, std::max(df, dr));
    }
    return nearest;
}

// Independent geometric oracle: grow king-reachable squares one step at a time.
int flood_reference(int square, Bitboard targets) {
    Bitboard reachable = square_bb(square);
    for (int distance = 0; distance < 8; ++distance) {
        if ((reachable & targets) != 0) return distance;
        const Bitboard vertical = reachable | (reachable << 8) | (reachable >> 8);
        reachable = vertical | ((vertical & ~FileABB) >> 1) | ((vertical & ~FileHBB) << 1);
    }
    return 7;
}

int main() {
    std::uint64_t sets = 0, checks = 0, failures = 0;
    auto verify = [&](int square, Bitboard targets) {
        ++sets;
        const int actual = nearest_square_distance(square, targets);
        const std::array<int, 2> expected{scalar_reference(square, targets), flood_reference(square, targets)};
        for (int answer : expected) {
            ++checks;
            if (actual == answer) continue;
            ++failures;
            if (failures <= 20)
                std::cerr << "nearest mismatch square=" << square << " targets=" << targets
                          << " actual=" << actual << " expected=" << answer << '\n';
        }
    };
    for (int square = 0; square < 64; ++square) {
        verify(square, 0);
        for (int first = 0; first < 64; ++first) {
            verify(square, square_bb(first));
            for (int second = first + 1; second < 64; ++second)
                verify(square, square_bb(first) | square_bb(second));
        }
        for (int rank = 0; rank < 8; ++rank)
            for (std::uint64_t subset = 0; subset < 256; ++subset)
                verify(square, subset << (rank * 8));
        std::uint64_t state = 0x6a09e667f3bcc909ULL ^ (0x9e3779b97f4a7c15ULL * static_cast<std::uint64_t>(square + 1));
        for (int index = 0; index < 2048; ++index) {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            verify(square, state);
        }
        constexpr std::array<Bitboard, 8> dense{
            ~Bitboard{0}, FileABB, FileHBB, Rank1BB, Rank8BB,
            DarkSquares, LightSquares, 0x00ffffffffffff00ULL};
        for (Bitboard targets : dense) verify(square, targets);
    }
    std::cout << "Nearest pawn distance: sets " << sets << " checks " << checks
              << " failures " << failures << '\n';
    return failures == 0 ? 0 : 1;
}
