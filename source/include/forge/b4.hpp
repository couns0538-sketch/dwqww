#pragma once
// B4 bundle helpers (forge/r9, 2026-11-15; see R9_NOTE.txt for where every line comes from).
// HistRework (UCI spin 0..3, default 0 = off), from the old engine's Astra A1 as ported to the lock tree in
// opus-r13-p1-nearmiss-ports:opus_r13/p1/b1/b1_port.patch (include/forge/hist_rework.hpp):
//   - a twin of the butterfly history keyed by whether the move's from / to square is attacked by a LESSER enemy
//     piece; quiet move scores read a blend of the plain table and the twin;
//   - a correction table keyed by pawn structure x non-pawn material, learning with a self-damping update.
// CorrHistV2 (UCI check, default off), from forge-bundle-int b7c17722 src/search/fb2.inc: a correction keyed by the
// last two moves (moved piece x to-square).
// Nothing here is used while the options are off.
#include "forge/bitboard.hpp"
#include "forge/board.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace forge::b4 {

constexpr int MaxReworkLevel = 3;
constexpr int HistoryLimit = 16384;        // search.cpp asserts that this is its HistoryMax
constexpr int CorrectionEntryLimit = 8192; // search.cpp asserts that this is CorrectionLimit

[[nodiscard]] constexpr int clamp_level(int level) {
    return level < 1 ? 1 : (level > MaxReworkLevel ? MaxReworkLevel : level);
}
// Quarters of the butterfly term read from the threat-keyed twin: level 1, 2, 3 -> 2, 3, 4 (50 %, 75 %, 100 %).
[[nodiscard]] constexpr int threat_quarters(int level) { return clamp_level(level) + 1; }
// Read weight (x0.01) of the pawn x non-pawn-material correction: level 1, 2, 3 -> 50, 75, 100.
[[nodiscard]] constexpr int joint_weight(int level) { return 25 * clamp_level(level) + 25; }

// Squares attacked by a lesser enemy piece, indexed by the type of the piece that stands (or would stand) there.
// Pawns, knights, bishops: enemy pawn attacks. Rooks: + enemy knights and bishops. Queens: + enemy rooks. King and
// NoPieceType: empty. The side to move is "us"; attacks use the current occupancy (no x-rays, pins ignored).
struct LesserThreats {
    std::array<Bitboard, 7> by_type{};
};

[[nodiscard]] inline LesserThreats lesser_threats(const Board& board) {
    const Color them = opposite(board.side_to_move());
    const Bitboard occupancy = board.occupied();
    const Bitboard by_pawn = pawn_attacks_bb(them, board.pieces(them, Pawn));
    Bitboard by_minor = by_pawn;
    for (Bitboard bb = board.pieces(them, Knight); bb != 0;) by_minor |= attacks::knight(pop_lsb(bb));
    for (Bitboard bb = board.pieces(them, Bishop); bb != 0;) by_minor |= attacks::bishop(pop_lsb(bb), occupancy);
    Bitboard by_rook = by_minor;
    for (Bitboard bb = board.pieces(them, Rook); bb != 0;) by_rook |= attacks::rook(pop_lsb(bb), occupancy);
    LesserThreats threats;
    threats.by_type[static_cast<std::size_t>(Pawn)] = by_pawn;
    threats.by_type[static_cast<std::size_t>(Knight)] = by_pawn;
    threats.by_type[static_cast<std::size_t>(Bishop)] = by_pawn;
    threats.by_type[static_cast<std::size_t>(Rook)] = by_minor;
    threats.by_type[static_cast<std::size_t>(Queen)] = by_rook;
    return threats;
}

// 0 or 1: is `square` (0..63) in `set`.
[[nodiscard]] constexpr std::size_t square_bit(Bitboard set, int square) {
    return static_cast<std::size_t>((set >> square) & 1U);
}

// Butterfly term of a quiet move: quarters/4 from the threat-keyed twin, the rest from the plain table.
// |plain|, |threat| <= HistoryLimit and 0 <= quarters <= 4 give |numerator| <= 65536 and |result| <= HistoryLimit
// (C++ division truncates toward zero).
[[nodiscard]] constexpr int blend(int plain, int threat, int quarters) {
    return (plain * (4 - quarters) + threat * quarters) / 4;
}

// Self-damping update of a joint-correction entry: entry + step - entry * |step| / limit. For |entry| <= limit and
// |step| <= limit the result stays within +-limit; the clamp is a guard. |entry * step| <= limit^2 = 2^26 fits int32.
[[nodiscard]] constexpr std::int32_t gravity(std::int32_t entry, std::int32_t step, std::int32_t limit) {
    const std::int32_t magnitude = step < 0 ? -step : step;
    const std::int32_t next = entry + step - entry * magnitude / limit;
    return next < -limit ? -limit : (next > limit ? limit : next);
}

// Non-pawn material signature: 4 bits per (colour, knight/bishop/rook/queen) count, saturated at 15.
[[nodiscard]] inline std::uint32_t non_pawn_material(const Board& board) {
    std::uint32_t signature = 0;
    for (const Color color : {White, Black}) {
        for (int type = Knight; type <= Queen; ++type) {
            const int count = popcount(board.pieces(color, static_cast<PieceType>(type)));
            signature = (signature << 4U) | static_cast<std::uint32_t>(count < 15 ? count : 15);
        }
    }
    return signature;
}

// SplitMix64 finaliser (a public-domain mixing function): every signature bit reaches the low index bits.
[[nodiscard]] constexpr std::uint64_t mix64(std::uint64_t z) {
    z = (z ^ (z >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27U)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31U);
}

// Key of the pawn-structure x non-pawn-material correction: the Zobrist pawn key mixed with the signature.
[[nodiscard]] inline std::uint64_t joint_key(const Board& board) {
    return board.pawn_key() ^ mix64(static_cast<std::uint64_t>(non_pawn_material(board)) + 1U);
}

} // namespace forge::b4

namespace forge {
// HistRework's twin: [side][from attacked by a lesser enemy][to attacked by a lesser enemy][from][to] (32 KiB).
using LesserThreatHistory =
    std::array<std::array<std::array<std::array<std::array<std::int16_t, 64>, 64>, 2>, 2>, 2>;
// CorrHistV2: [0 = the move that led here, 1 = the move before it][moved piece][to square] (6.5 KiB).
using ContinuationCorrection = std::array<std::array<std::array<std::int32_t, 64>, 13>, 2>;
} // namespace forge
