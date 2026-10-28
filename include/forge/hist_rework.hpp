#pragma once
// UCI HistRework (Astra A1), default 0 = the AL1 s198 lock search. Levels 1..3 rework how the quiet history
// and the static-eval correction learn and blend:
//   - the butterfly history gets a twin keyed by whether the move's from/to square is attacked by a LESSER
//     enemy piece; quiet_history reads a blend of the lock table and the threat-keyed twin;
//   - a correction table keyed by pawn structure x non-pawn material (one joint key) is added to the
//     pawn + material corrections; it learns with a gravity-style (self-damping) update.
// The lock's own tables keep their exact update and read rules. Design, overflow proof and tuning ranges:
// opus_round1/sol_A1/forge_astra_A1_design_20261027.md.
#include "forge/bitboard.hpp"
#include "forge/board.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace forge {

namespace search_options {
// 0 = off (the lock). 1..3 = the tune steps below. Set only between searches (UCI setoption stops the search).
extern int hist_rework;
} // namespace search_options

namespace hist_rework {

constexpr int MaxLevel = 3;
constexpr int HistoryLimit = 16384;        // the lock's HistoryMax (search.cpp asserts the equality)
constexpr int CorrectionEntryLimit = 8192; // the lock's CorrectionLimit (search.cpp asserts the equality)

[[nodiscard]] constexpr int clamp_level(int level) { return level < 1 ? 1 : (level > MaxLevel ? MaxLevel : level); }
// Quarters of the butterfly term read from the threat-keyed twin: level 1, 2, 3 -> 2, 3, 4 (50 %, 75 %, 100 %).
[[nodiscard]] constexpr int threat_quarters(int level) { return clamp_level(level) + 1; }
// Read weight (x0.01) of the pawn x non-pawn-material correction: level 1, 2, 3 -> 50, 75, 100.
[[nodiscard]] constexpr int joint_weight(int level) { return 25 * clamp_level(level) + 25; }

// Squares attacked by a lesser enemy piece, indexed by the type of the piece that stands (or would stand)
// there. Pawns, knights, bishops: enemy pawn attacks. Rooks: + enemy knights and bishops. Queens: + enemy
// rooks. King and NoPieceType: empty (a king never moves onto an attacked square; evasions are their own
// stage). The side to move is "us"; attacks use the current occupancy (no x-rays, pins ignored).
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

// Butterfly term read by quiet_history: quarters/4 from the threat-keyed twin, the rest from the lock table.
// |plain|, |threat| <= HistoryLimit and 0 <= quarters <= 4 give |numerator| <= 4 * HistoryLimit = 65536 and
// |result| <= HistoryLimit (C++ division truncates toward zero).
[[nodiscard]] constexpr int blend(int plain, int threat, int quarters) {
    return (plain * (4 - quarters) + threat * quarters) / 4;
}

// Gravity-style update of a joint-correction entry: entry + step - entry * |step| / limit. For |entry| <= limit
// and |step| <= limit the result stays within +-limit (design note, section 4); the clamp is a guard that the
// unit test shows never changes a value on that domain. |entry * step| <= limit^2 = 2^26 fits int32.
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

// Key of the pawn-structure x non-pawn-material correction: the Zobrist pawn key (pawn placement of both
// colours) mixed with the non-pawn material signature. Unsigned arithmetic only (wraps by definition).
[[nodiscard]] inline std::uint64_t joint_key(const Board& board) {
    return board.pawn_key() ^ mix64(static_cast<std::uint64_t>(non_pawn_material(board)) + 1U);
}

} // namespace hist_rework
} // namespace forge
