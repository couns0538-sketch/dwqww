#pragma once

#include "forge/board.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace forge {

struct SearchLimits {
    int depth = 64;
    std::uint64_t nodes = 0;
    bool nodes_specified = false;
    int movetime_ms = -1;
    int time_ms = -1;
    int increment_ms = 0;
    int moves_to_go = 30;
    int mate_moves = 0;
    int move_overhead_ms = 10;
    bool infinite = false;
    bool ponder = false;
    bool search_moves_specified = false;
    std::vector<Move> search_moves;
};

struct SearchInfo {
    Move best_move{};
    int score = 0;
    int depth = 0;
    int seldepth = 0;
    std::uint64_t nodes = 0;
    std::uint64_t elapsed_ms = 0;
    std::vector<Move> pv;
    // A searchmoves intersection with no legal moves is not checkmate or stalemate.
    bool restricted_root_empty = false;
};

class Searcher {
public:
    explicit Searcher(std::size_t hash_mb = 32);
    SearchInfo search(Board board, const SearchLimits& limits, bool emit_info = false);
    void stop() { stop_.store(true); }
    void reset_stop() { stop_.store(false); ponder_hit_ns_.store(0); }
    void ponderhit() {
        const auto now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();
        std::int64_t expected = 0;
        (void)ponder_hit_ns_.compare_exchange_strong(expected, now_ns);
    }
    void clear();
    void clear_hash();
    void resize_hash(std::size_t hash_mb);
    [[nodiscard]] int hashfull_permille() const;
    [[nodiscard]] static int evaluate(const Board& board);

private:
    friend struct SearcherTestProbe;

    enum Bound : std::uint8_t { Exact, Lower, Upper, Invalid };
    struct TTEntry {
        std::uint64_t key = 0;
        Move move{};
        std::int16_t score = 0;
        // Packed into the two bytes formerly occupied by depth + bound so TT capacity
        // is unchanged: bits 0..6 depth, 7..8 bound, 9..15 rule-50 context.
        // Bound=Invalid marks an empty slot. Context 0..100 is the exact halfmove
        // clock; 101 identifies synthetic-null branches, where draw adjudication is
        // deliberately suppressed.
        std::uint16_t meta = static_cast<std::uint16_t>(Invalid) << 7U;
    };
    struct EvalEntry {
        std::uint64_t key = 0;
        std::int16_t score = 0;
        bool valid = false;
    };
    struct PawnEntry {
        std::uint64_t key = 0;
        int mg = 0;
        int eg = 0;
        std::array<std::array<int, 8>, 2> by_file{};
        std::array<int, 8> white_min_rank{};
        std::array<int, 8> black_max_rank{};
        bool valid = false;
    };

    static constexpr std::size_t EvalCacheSize = 1U << 16U;
    static constexpr std::size_t PawnCacheSize = 1U << 14U;

    [[nodiscard]] static constexpr int tt_depth(const TTEntry& entry) {
        return tt_bound(entry) == Invalid ? -1 : static_cast<int>(entry.meta & 0x7FU);
    }
    [[nodiscard]] static constexpr Bound tt_bound(const TTEntry& entry) {
        return static_cast<Bound>((entry.meta >> 7U) & 0x3U);
    }
    [[nodiscard]] static constexpr std::uint8_t tt_context(const TTEntry& entry) {
        return static_cast<std::uint8_t>((entry.meta >> 9U) & 0x7FU);
    }
    // Far from the fifty-move boundary every clock shares one context, so
    // transpositions reuse each other's bounds. From clock 90 upward the exact
    // clock is required, because the search result then depends on it.
    [[nodiscard]] static constexpr std::uint8_t current_tt_context(const Board& board, bool null_branch) {
        if (null_branch) return 101U;
        const int clock = std::min(board.halfmove_clock(), 100);
        return clock < 90 ? 0U : static_cast<std::uint8_t>(clock - 89);
    }
    static constexpr void set_tt_meta(TTEntry& entry, int depth, Bound bound,
                                      std::uint8_t context) {
        entry.meta = static_cast<std::uint16_t>(static_cast<unsigned>(depth) & 0x7FU)
                   | static_cast<std::uint16_t>(static_cast<unsigned>(bound) << 7U)
                   | static_cast<std::uint16_t>(static_cast<unsigned>(context) << 9U);
    }

    std::vector<TTEntry> table_;
    std::size_t tt_mask_ = 0;
    std::vector<EvalEntry> eval_cache_;
    std::vector<PawnEntry> pawn_cache_;
    std::atomic<bool> stop_{false};
    // 0 means pondering has not been converted into a timed search. The UCI
    // thread publishes the monotonic timestamp, and the search thread reads it.
    std::atomic<std::int64_t> ponder_hit_ns_{0};
    bool pondering_ = false;
    std::chrono::steady_clock::time_point start_{};
    std::uint64_t nodes_ = 0;
    std::uint64_t null_tries_ = 0;
    std::uint64_t null_cutoffs_ = 0;
    std::uint64_t reverse_futility_cutoffs_ = 0;
    std::uint64_t node_limit_ = 0;
    bool node_limit_specified_ = false;
    // Hard limit: the search is interrupted once it is reached. Soft limit: no new
    // iteration is started after it has elapsed. Both are zero when unbounded.
    std::uint64_t time_limit_ms_ = 0;
    std::uint64_t soft_limit_ms_ = 0;
    std::uint64_t time_check_mask_ = 255;
    bool aborted_ = false;
    int seldepth_ = 0;
    int root_depth_ = 0;
    std::array<std::array<Move, 2>, 128> killers_{};
    std::array<std::array<std::array<int, 64>, 64>, 2> history_{};
    std::array<std::array<Move, 64>, 64> countermoves_{};
    // Static evaluation per ply, used for the "improving" heuristic.
    std::array<int, 130> eval_stack_{};
    std::vector<Move> root_moves_;
    bool root_restricted_ = false;
    Move root_best_move_{};
    // Index of the root position inside Board::key_history().
    std::size_t root_index_ = 0;

    int alpha_beta(Board& board, int depth, int ply, int alpha, int beta,
                   bool allow_null = true, bool null_branch = false, Move previous_move = {});
    int quiescence(Board& board, int ply, int alpha, int beta, bool null_branch = false);
    [[nodiscard]] std::uint64_t elapsed_budget_ms() const;
    [[nodiscard]] bool should_stop();
    bool abort_if_stopped();
    [[nodiscard]] std::size_t tt_index(std::uint64_t key) const {
        return tt_mask_ != 0 ? static_cast<std::size_t>(key) & tt_mask_
                             : static_cast<std::size_t>(key % table_.size());
    }
    // Hash entries are indexed by position only, so transpositions reached
    // through different move orders share bounds. Synthetic-null branches use
    // the same key under their dedicated context tag.
    [[nodiscard]] static std::uint64_t tt_key(const Board& board) { return board.key(); }
    // Draw by repetition inside the search: a position that already occurred
    // once after the root, or twice anywhere in the known history.
    [[nodiscard]] static bool is_search_repetition(const Board& board, std::size_t root_index);
    [[nodiscard]] static constexpr std::size_t eval_index(std::uint64_t key) {
        return static_cast<std::size_t>(key) & (EvalCacheSize - 1U);
    }
    [[nodiscard]] static constexpr std::size_t pawn_index(std::uint64_t key) {
        return static_cast<std::size_t>(key) & (PawnCacheSize - 1U);
    }
    int evaluate_cached(const Board& board);
    [[nodiscard]] static PawnEntry analyze_pawns(const Board& board);
    [[nodiscard]] static int evaluate_with_pawns(const Board& board, const PawnEntry& pawns);
    void order_moves(const Board& board, MoveList& moves, const Move& tt_move,
                     const Move& counter_move, int ply, bool in_quiescence) const;
    [[nodiscard]] int move_score(const Board& board, const Move& move, const Move& tt_move,
                                 const Move& counter_move, int ply, bool in_quiescence) const;
    [[nodiscard]] std::vector<Move> extract_pv(Board board, int depth) const;
};

} // namespace forge
