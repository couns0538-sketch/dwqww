#pragma once

// Extended correction history (UCI option CorrHistPlus, default 0 = off).
//
// AL1 s198 corrects the static evaluation with two learned tables, keyed by the
// pawn structure and by the material signature (src/search/evaluation.inc).
// CorrHistPlus adds three more keys, one option bit each, so that every key can
// be gated on its own:
//   1  Continuation: the previous two moves (our move two plies ago and the
//      opponent's reply) as (piece type, destination) pairs        -> gate G-B1
//   2  MinorPiece:   placement of both sides' knights, bishops and kings -> G-B2
//   4  NonPawn:      placement of one side's non-pawn pieces incl. its king;
//                    one table per side, both read at every node
// This header holds everything that does not depend on search state: the keys
// (hashes of piece bitboards computed on demand, so forge::Board is unchanged),
// the table layout and the fixed-point update and blend rules. The search glue
// is src/search/correction_plus.inc. tests/correction_history_tests.cpp checks
// these functions against independent reference implementations.

#include "forge/board.hpp"
#include "forge/history.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>

namespace forge::corrplus {

// Bits of forge::options::corr_hist_plus.
constexpr int Continuation = 1;
constexpr int MinorPiece = 2;
constexpr int NonPawn = 4;
constexpr int AllKeys = Continuation | MinorPiece | NonPawn;

// ---------------------------------------------------------------- keys
// One odd multiplier per piece role (own random draw), summed, then avalanched
// so that the low bits used as the table index depend on every input bit.
inline constexpr std::array<std::uint64_t, 6> KeyMultipliers{
    0xccc786391d0cc457ULL, 0xac43abac3a456cc1ULL, 0xd2773bee220bddebULL,
    0x678b09c87c6dca51ULL, 0x16efdac28abd75dbULL, 0xd508421d0238c1a9ULL,
};

// xor-shift-multiply finaliser (the output step of the public-domain SplitMix64 generator).
[[nodiscard]] constexpr std::uint64_t avalanche(std::uint64_t x) {
    x = (x ^ (x >> 30U)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27U)) * 0x94d049bb133111ebULL;
    return x ^ (x >> 31U);
}

// Knights, bishops and kings of both sides.
[[gnu::always_inline]] [[nodiscard]] inline std::uint64_t minor_piece_key(const Board& board) {
    return avalanche(board.pieces(WN) * KeyMultipliers[0] + board.pieces(WB) * KeyMultipliers[1] +
                     board.pieces(BN) * KeyMultipliers[2] + board.pieces(BB) * KeyMultipliers[3] +
                     board.pieces(WK) * KeyMultipliers[4] + board.pieces(BK) * KeyMultipliers[5]);
}

// Knights, bishops, rooks, queens and the king of one side.
[[gnu::always_inline]] [[nodiscard]] inline std::uint64_t non_pawn_key(const Board& board, Color color) {
    return avalanche(board.pieces(color, Knight) * KeyMultipliers[0] + board.pieces(color, Bishop) * KeyMultipliers[1] +
                     board.pieces(color, Rook) * KeyMultipliers[2] + board.pieces(color, Queen) * KeyMultipliers[3] +
                     board.pieces(color, King) * KeyMultipliers[4]);
}

// Slot of a hashed key in a CorrectionSize table (same rule as the pawn table).
[[nodiscard]] constexpr std::size_t key_index(std::uint64_t key) {
    return static_cast<std::size_t>(key & (CorrectionSize - 1U));
}

// ---------------------------------------------------------------- tables
// Continuation table, directly indexed:
// [side to move][type of our move two plies ago][its destination]
//               [type of the opponent's last move][its destination].
// The colours of both moved pieces follow from the side to move (a null move
// in between gives no key), so piece types (1..6) suffice.
constexpr std::size_t PieceTypes = 6;
constexpr std::size_t ContinuationSize = 2 * PieceTypes * 64 * PieceTypes * 64;

[[nodiscard]] constexpr std::size_t continuation_index(Color side, int our_type, int our_to, int their_type, int their_to) {
    std::size_t index = static_cast<std::size_t>(side);
    index = index * PieceTypes + static_cast<std::size_t>(our_type - 1);
    index = index * 64 + static_cast<std::size_t>(our_to);
    index = index * PieceTypes + static_cast<std::size_t>(their_type - 1);
    return index * 64 + static_cast<std::size_t>(their_to);
}

// Entries are CorrectionGrain fixed point like the pawn table and never leave
// +/-CorrectionLimit (8192), so 16 bits suffice: 768 KiB per search thread.
using Entry = std::int16_t;
struct Tables {
    std::array<std::array<Entry, CorrectionSize>, 2> minor;                    // [side to move][key]
    std::array<std::array<std::array<Entry, CorrectionSize>, 2>, 2> non_pawn;  // [key's colour][side to move][key]
    std::array<Entry, ContinuationSize> continuation;                          // continuation_index()
};

// ---------------------------------------------------------------- division
// The search glue (src/search/correction_plus.inc) is [[gnu::cold]], i.e.
// optimised for size, and there GCC divides by a constant with idiv, even by a
// power of two. These helpers give exactly the C++ quotient (rounded toward
// zero) with the multiply / shift sequences GCC uses in hot code; the tests
// check them against the / operator over the whole reachable range.

// x / 2^Shift, for |x| < 2^31 - 2^Shift.
template <int Shift>
[[nodiscard]] constexpr int div_pow2(int x) {
    return (x + ((x >> 31) & ((1 << Shift) - 1))) >> Shift;
}

// x / 100, for every 32-bit x.
[[nodiscard]] constexpr int div100(int x) {
    const long long scaled = static_cast<long long>(x) * 1374389535LL;  // ceil(2^37 / 100)
    return static_cast<int>(scaled >> 37) + (x < 0 ? 1 : 0);
}

static_assert(CorrectionGrain == 1 << 8 && CorrectionLimit == 1 << 13, "div_pow2 shifts below assume these values");

// ---------------------------------------------------------------- update
// Step: the residual and depth weight of the pawn/material update
// (Worker::update_correction): (search score - corrected static eval) in
// CorrectionGrain units, clipped to +/-CorrectionLimit/4, times min(depth+1,16)/256.
[[nodiscard]] constexpr int step(int best_score, int static_eval, int depth) {
    const int residual = std::clamp((best_score - static_eval) * CorrectionGrain, -CorrectionLimit / 4, CorrectionLimit / 4);
    return div_pow2<8>(residual * std::min(depth + 1, 16));
}

// One entry: add the step and decay the entry toward 0 by entry * |step| /
// CorrectionLimit (a saturated entry moves less in its own direction and is
// unlearned faster; at zero residual nothing changes), then clamp. The decay
// keeps |entry| <= CorrectionLimit for |step| <= CorrectionLimit; the clamp
// is the guarantee.
[[nodiscard]] constexpr int apply(int entry, int step) {
    const int magnitude = step < 0 ? -step : step;
    return std::clamp(entry + step - div_pow2<13>(entry * magnitude), -CorrectionLimit, CorrectionLimit);
}

// ---------------------------------------------------------------- blend
// Contribution of the enabled keys: sum of entry * weight (weights x0.01,
// tune::Corr*Weight), in CorrectionGrain units, clamped to +/-TotalLimit
// (64 cp) before it is added to the pawn + material correction.
constexpr int TotalLimit = 2 * CorrectionLimit;

[[nodiscard]] constexpr int blend(int weighted_sum) {
    return std::clamp(div100(weighted_sum), -TotalLimit, TotalLimit);
}

} // namespace forge::corrplus
