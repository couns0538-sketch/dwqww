#pragma once

#include "forge/board.hpp"

#include <cstdint>
#include <vector>

namespace forge {

// Packed tapered score: middlegame in the low 16 bits, endgame in the high 16.
using Score = int;

[[nodiscard]] constexpr Score S(int mg, int eg) {
    return static_cast<Score>(static_cast<unsigned>(eg) << 16U) + mg;
}
[[nodiscard]] constexpr int mg_value(Score s) {
    return static_cast<std::int16_t>(static_cast<std::uint16_t>(static_cast<unsigned>(s)));
}
[[nodiscard]] constexpr int eg_value(Score s) {
    return static_cast<std::int16_t>(static_cast<std::uint16_t>((static_cast<unsigned>(s) + 0x8000U) >> 16U));
}

constexpr int MaxPhase = 24;
constexpr std::array<int, 7> PhaseValue{0, 0, 1, 1, 2, 4, 0};

// Piece values used by the search for pruning margins and move ordering.
constexpr std::array<int, 7> PieceValueMg{0, 82, 337, 365, 477, 1025, 0};
constexpr std::array<int, 7> PieceValueEg{0, 94, 281, 297, 512, 936, 0};
constexpr std::array<int, 7> SeePieceValue{0, 100, 300, 300, 500, 900, 0};

class Evaluator {
public:
    Evaluator();
    // Static evaluation from the side to move's point of view, in centipawns.
    [[nodiscard]] int evaluate(const Board& board);
    void clear();

    // Evaluation without any cache, for tests and tools.
    [[nodiscard]] static int evaluate_uncached(const Board& board);

private:
    struct PawnEntry {
        std::uint64_t key = 0;
        Score score = 0;
        std::array<Bitboard, 2> passed{};
        bool valid = false;
    };
    static constexpr std::size_t PawnCacheSize = 1U << 15U;
    std::vector<PawnEntry> pawn_cache_;

    [[nodiscard]] int evaluate_impl(const Board& board, PawnEntry* cache);
};

} // namespace forge
