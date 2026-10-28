#pragma once

#include "forge/board.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

// Job S11 (node-exact speed), UCI MaterialKeyTable (default off).
//
// The material-correction key of the search (src/search.cpp material_key) is a
// Horner polynomial in the ten piece counts c0..c9 (white pawn..queen, then
// black pawn..queen), evaluated in unsigned 64-bit arithmetic:
//
//     key = (((c0+1)*P + (c1+1))*P + ... + (c9+1)) * M  =  sum_s (c_s+1) * M * P^(9-s)   (mod 2^64)
//
// Multiplication distributes over addition modulo 2^64, so the key is a sum of
// ten independent per-slot terms. Contributions[s][c] holds (c+1) * M * P^(9-s)
// for every popcount c = 0..64, and table_key() adds ten table entries instead
// of running ten dependent multiply-adds and the final multiply. The two keys
// are equal for every board (tests/material_key_tests.cpp checks the table
// against the polynomial on the whole count domain and on real positions).
namespace forge::matkey {

inline constexpr std::uint64_t HornerMultiplier = 1099511628211ULL;  // P, as in material_key
inline constexpr std::uint64_t FinalMix = 0x9E3779B97F4A7C15ULL;     // M, as in material_key
inline constexpr std::size_t Slots = 10;                             // 2 colours x pawn..queen
inline constexpr std::size_t CountValues = 65;                       // popcount of a bitboard: 0..64

using ContributionTable = std::array<std::array<std::uint64_t, CountValues>, Slots>;

[[nodiscard]] constexpr ContributionTable make_contributions() {
    ContributionTable values{};
    std::uint64_t factor = FinalMix;  // slot 9 (black queens) is multiplied by M only
    for (std::size_t slot = Slots; slot-- > 0;) {
        for (std::size_t count = 0; count < CountValues; ++count) {
            values[slot][count] = factor * (static_cast<std::uint64_t>(count) + 1U);
        }
        factor *= HornerMultiplier;
    }
    return values;
}

alignas(64) inline constexpr ContributionTable Contributions = make_contributions();

// The search's material key, from the table.
[[nodiscard, gnu::always_inline]] inline std::uint64_t table_key(const Board& board) {
    std::uint64_t key = 0;
    std::size_t slot = 0;
    for (const Color color : {White, Black}) {
        for (int type = Pawn; type <= Queen; ++type) {
            const auto count = static_cast<std::size_t>(popcount(board.pieces(color, static_cast<PieceType>(type))));
            key += Contributions[slot++][count];
        }
    }
    return key;
}

} // namespace forge::matkey
