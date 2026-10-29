#pragma once

#include "forge/board.hpp"

#include <cstdint>
#include <vector>

namespace forge {

namespace nnue { struct DirtyPieces; }
class Worker;

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
    // Search-local state only: public evaluation and tuning always recompute.
    // Phase is deliberately not capped until the final evaluation taper.
    struct RuntimePsqt {
        Score score = 0;
        int phase = 0;
        bool valid = false;
    };

    Evaluator();
    // Static evaluation from the side to move's point of view, in centipawns.
    [[nodiscard]] int evaluate(const Board& board);
    void clear();

    // Evaluation without any cache, for tests and tools.
    [[nodiscard]] static int evaluate_uncached(const Board& board);

    struct PawnEntry {
        std::uint64_t key = 0;
        Score score = 0;
        std::array<Bitboard, 2> passed{};
        bool valid = false;
    };

private:
    friend class Worker;
    [[nodiscard]] static RuntimePsqt refresh_runtime_psqt(const Board& board);
    static void update_runtime_psqt(const RuntimePsqt& parent, RuntimePsqt& child, const nnue::DirtyPieces& dirty);
    [[nodiscard]] int evaluate_runtime(const Board& board, const RuntimePsqt& psqt);
    static constexpr std::size_t PawnCacheSize = 1U << 15U;
    // R7 J3 (UCI R7EvalPrefetch): start loading the pawn-cache entry that evaluating a board with this pawn key
    // will read (Worker, after make_move). A hint only: no state changes.
    void prefetch_pawn_entry(std::uint64_t pawn_key) const {
#if defined(__GNUC__) || defined(__clang__)
        __builtin_prefetch(&pawn_cache_[static_cast<std::size_t>(pawn_key) & (PawnCacheSize - 1U)]);
#else
        (void)pawn_key;
#endif
    }
    std::vector<PawnEntry> pawn_cache_;
};

} // namespace forge
