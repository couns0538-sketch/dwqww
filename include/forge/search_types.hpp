#pragma once

#include "forge/board.hpp"

#include <chrono>
#include <cstdint>
#include <vector>

namespace forge {

struct SearchLimits {
    int depth = 64;
    std::uint64_t nodes = 0;
    bool nodes_specified = false;
    int movetime_ms = -1;
    int time_ms = -1;
    int increment_ms = 0;
    // 0 means the increment/sudden-death time control (no movestogo given).
    int moves_to_go = 0;
    int mate_moves = 0;
    int move_overhead_ms = 10;
    bool infinite = false;
    bool ponder = false;
    bool search_moves_specified = false;
    std::vector<Move> search_moves;
    // Optional steady-clock receipt origin. start_time takes precedence;
    // request_start remains a compatibility spelling for existing callers.
    // With both unset, finite timed searches start at Searcher entry; other
    // searches retain a worker-local origin. Ponder budgets start at ponderhit.
    std::chrono::steady_clock::time_point request_start{};
    std::chrono::steady_clock::time_point start_time{};
};

struct SearchInfo {
    Move best_move{};
    Move ponder_move{};
    int score = 0;
    int depth = 0;
    int seldepth = 0;
    std::uint64_t nodes = 0;
    std::uint64_t elapsed_ms = 0;
    std::vector<Move> pv;
    // A searchmoves intersection with no legal moves is not checkmate or stalemate.
    bool restricted_root_empty = false;
};

constexpr int MaxPly = 128;
constexpr int Infinite = 32001;
constexpr int MateValue = 32000;
constexpr int MateInMaxPly = MateValue - MaxPly;
constexpr int ValueNone = 32002;

[[nodiscard]] constexpr bool is_mate_score(int score) {
    return score >= MateInMaxPly || score <= -MateInMaxPly;
}

enum Bound : std::uint8_t { BoundNone = 0, BoundUpper = 1, BoundLower = 2, BoundExact = 3 };

} // namespace forge
