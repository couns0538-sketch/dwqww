// Exact geometry optimization: the original per-pawn span remains the oracle.
#include "forge/bitboard.hpp"

#include <array>
#include <cstdint>
#include <iostream>

using namespace forge;

static_assert(forward_fill(White, square_bb(0)) == FileABB);
static_assert(forward_fill(Black, square_bb(63)) == FileHBB);
static_assert(forward_fill(White, 0) == 0 && forward_fill(Black, 0) == 0);

namespace {
std::uint64_t checks = 0;
std::uint64_t failures = 0;

void check(Bitboard actual, Bitboard expected, Color color, Bitboard input, const char* label) {
    ++checks;
    if (actual == expected) return;
    ++failures;
    if (failures <= 12) {
        std::cerr << "FAIL " << label << " color " << static_cast<int>(color)
                  << " input " << input << " expected " << expected << " actual " << actual << '\n';
    }
}

Bitboard original_span(Color color, Bitboard pawns) {
    Bitboard span = 0;
    while (pawns != 0) {
        const int square = pop_lsb(pawns);
        span |= attacks::passed_pawn_mask(color, square) & ~attacks::forward_file(color, square);
    }
    return span;
}

Bitboard table_pawn_attacks(Color color, Bitboard pawns) {
    Bitboard result = 0;
    while (pawns != 0) result |= attacks::pawn(color, pop_lsb(pawns));
    return result;
}

Bitboard original_fill(Color color, Bitboard squares) {
    Bitboard result = squares;
    while (squares != 0) {
        const int square = pop_lsb(squares);
        for (int rank = rank_of(square) + (color == White ? 1 : -1);
             rank >= 0 && rank < 8; rank += color == White ? 1 : -1) {
            result |= square_bb(make_square(file_of(square), rank));
        }
    }
    return result;
}

void verify(Color color, Bitboard pawns) {
    const Bitboard expected = original_span(color, pawns);
    check(forward_fill(color, pawn_attacks_bb(color, pawns)), expected, color, pawns, "span from bitboard attacks");
    check(forward_fill(color, table_pawn_attacks(color, pawns)), expected, color, pawns, "span from stored pawn attack tables");
    check(forward_fill(color, pawns), original_fill(color, pawns), color, pawns, "inclusive arbitrary-square fill");
}

std::uint64_t next(std::uint64_t& state) {
    state ^= state << 13;
    state ^= state >> 7;
    state ^= state << 17;
    return state;
}
} // namespace

int main() {
    attacks::init();
    for (Color color : {White, Black}) {
        for (int square = 0; square < 64; ++square) verify(color, square_bb(square));
        // All 2^8 pawn subsets on each rank, including impossible tool positions
        // on the first/eighth ranks: exact bitboard behavior still applies.
        for (int rank = 0; rank < 8; ++rank) {
            for (std::uint64_t subset = 0; subset < 256; ++subset) verify(color, subset << (rank * 8));
        }
        for (Bitboard pawns : std::array<Bitboard, 12>{0, ~Bitboard{0}, FileABB, FileHBB,
                 FileABB | FileHBB, Rank1BB | Rank8BB, DarkSquares, LightSquares,
                 0x00FFFFFFFFFFFF00ULL, 0x0000001818000000ULL,
                 0x8100000000000081ULL, 0x00FF00000000FF00ULL}) verify(color, pawns);
        std::uint64_t seed = 20261020;
        for (int index = 0; index < 4096; ++index) verify(color, next(seed));
    }
    std::cout << "pawn_span_tests: " << checks << " checks, " << failures << " failures\n";
    return failures == 0 ? 0 : 1;
}
