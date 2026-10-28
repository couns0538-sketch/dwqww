#pragma once

#include "forge/board.hpp"

#include <atomic>
#include <chrono>
#include <cstdint>
#include <vector>

namespace forge {

#ifndef FORGE_NNUE_LAZY_ACC
#define FORGE_NNUE_LAZY_ACC 0
#endif

#if FORGE_NNUE_LAZY_ACC
namespace lazy_acc {
// UCI joins all search workers before changing this pending configuration.
extern std::atomic<bool> requested;
}
struct LazyAccStats {
    std::uint64_t refreshes = 0;
    std::uint64_t updates = 0;
    std::uint64_t zero_dirty_edges = 0;
    std::uint64_t copies_avoided = 0;
    std::uint64_t alias_hits = 0;
    std::uint64_t evaluations = 0;
};
#endif

struct SearchLimits {
#ifdef FORGE_S13_TT_CHILD_PREFETCH
    bool s13_tt_child_prefetch = false;
#endif
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
#if FORGE_NNUE_LAZY_ACC
    LazyAccStats lazy_acc_stats{};
#endif
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
