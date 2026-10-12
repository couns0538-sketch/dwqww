#pragma once

#include "forge/board.hpp"
#include "forge/eval.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <memory>
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
constexpr int TbWinValue = 0;

[[nodiscard]] constexpr bool is_mate_score(int score) {
    return score >= MateInMaxPly || score <= -MateInMaxPly;
}

enum Bound : std::uint8_t { BoundNone = 0, BoundUpper = 1, BoundLower = 2, BoundExact = 3 };

struct TTEntry {
    std::uint32_t key32 = 0;
    Move move{};
    std::int16_t score = 0;
    std::int16_t eval = 0;
    std::uint8_t depth = 0;
    // Bits 0..1 bound, bit 2 was-PV, bits 3..7 generation.
    std::uint8_t gen_bound = 0;
    std::uint16_t padding = 0;

    [[nodiscard]] Bound bound() const { return static_cast<Bound>(gen_bound & 3U); }
    [[nodiscard]] bool pv() const { return (gen_bound & 4U) != 0; }
    [[nodiscard]] std::uint8_t generation() const { return static_cast<std::uint8_t>(gen_bound >> 3U); }
    [[nodiscard]] bool occupied() const { return bound() != BoundNone; }
};

struct alignas(64) TTCluster {
    std::array<TTEntry, 4> entries{};
};

class TranspositionTable {
public:
    explicit TranspositionTable(std::size_t mb = 32) { resize(mb); }
    void resize(std::size_t mb);
    void clear();
    void new_search() { generation_ = static_cast<std::uint8_t>((generation_ + 1U) & 31U); }
    [[nodiscard]] TTEntry* probe(std::uint64_t key, bool& hit);
    void prefetch(std::uint64_t key) const {
#if defined(__GNUC__) || defined(__clang__)
        __builtin_prefetch(&cluster_for(key));
#else
        (void)key;
#endif
    }
    void store(TTEntry* entry, std::uint64_t key, int score, int eval, Move move, int depth, Bound bound, bool pv);
    [[nodiscard]] int hashfull() const;
    [[nodiscard]] std::uint8_t generation() const { return generation_; }
    [[nodiscard]] std::size_t cluster_count() const { return cluster_count_; }

private:
    std::unique_ptr<TTCluster[]> clusters_;
    std::size_t cluster_count_ = 0;
    std::uint8_t generation_ = 0;

    [[nodiscard]] TTCluster& cluster_for(std::uint64_t key) const {
#if defined(__SIZEOF_INT128__)
        __extension__ using u128 = unsigned __int128;
        return clusters_[static_cast<std::size_t>((static_cast<u128>(key) * cluster_count_) >> 64U)];
#else
        return clusters_[static_cast<std::size_t>(key % cluster_count_)];
#endif
    }
};

// Move-ordering statistics.
using ButterflyHistory = std::array<std::array<std::array<std::int16_t, 64>, 64>, 2>;
using PieceToHistory = std::array<std::array<std::int16_t, 64>, 13>;
using ContinuationHistory = std::array<std::array<PieceToHistory, 64>, 13>;
using CaptureHistory = std::array<std::array<std::array<std::int16_t, 7>, 64>, 13>;
using CounterMoveTable = std::array<std::array<Move, 64>, 13>;
constexpr std::size_t CorrectionSize = 1U << 14U;
constexpr int CorrectionGrain = 256;
constexpr int CorrectionLimit = 32 * CorrectionGrain;
using CorrectionHistory = std::array<std::array<std::int32_t, CorrectionSize>, 2>;

struct SearchStack {
    std::array<Move, MaxPly + 1> pv{};
    int pv_length = 0;
    int ply = 0;
    Move current_move{};
    Move excluded_move{};
    std::array<Move, 2> killers{};
    Piece moved_piece = Empty;
    int static_eval = ValueNone;
    int raw_eval = ValueNone;
    int move_count = 0;
    int double_extensions = 0;
    bool in_check = false;
    bool tt_pv = false;
    bool null_move_allowed = true;
    PieceToHistory* continuation = nullptr;
};

class Searcher {
public:
    explicit Searcher(std::size_t hash_mb = 32);
    ~Searcher();
    Searcher(const Searcher&) = delete;
    Searcher& operator=(const Searcher&) = delete;

    SearchInfo search(Board board, const SearchLimits& limits, bool emit_info = false);
    void stop() { stop_.store(true, std::memory_order_relaxed); }
    void reset_stop() {
        stop_.store(false, std::memory_order_relaxed);
        ponder_hit_ns_.store(0, std::memory_order_relaxed);
    }
    void ponderhit() {
        const auto now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();
        std::int64_t expected = 0;
        (void)ponder_hit_ns_.compare_exchange_strong(expected, now_ns);
    }
    void clear();
    void clear_hash();
    void resize_hash(std::size_t hash_mb);
    [[nodiscard]] int hashfull_permille() const { return tt_.hashfull(); }
    [[nodiscard]] static int evaluate(const Board& board) { return Evaluator::evaluate_uncached(board); }
    [[nodiscard]] std::uint64_t nodes() const { return nodes_; }

private:
    friend struct SearcherTestProbe;
    friend class MovePicker;

    TranspositionTable tt_;
    Evaluator evaluator_;
    std::unique_ptr<ButterflyHistory> main_history_;
    std::unique_ptr<CaptureHistory> capture_history_;
    std::unique_ptr<ContinuationHistory> continuation_history_;
    std::unique_ptr<CounterMoveTable> counter_moves_;
    std::unique_ptr<CorrectionHistory> correction_history_;
    std::array<SearchStack, MaxPly + 8> stack_{};
    std::array<std::uint64_t, 256> root_move_nodes_{};
    int root_best_index_ = -1;

    std::atomic<bool> stop_{false};
    std::atomic<std::int64_t> ponder_hit_ns_{0};
    bool pondering_ = false;
    std::chrono::steady_clock::time_point start_{};
    std::uint64_t nodes_ = 0;
    std::uint64_t node_limit_ = 0;
    bool node_limit_specified_ = false;
    std::int64_t soft_limit_ms_ = 0;
    std::int64_t hard_limit_ms_ = 0;
    bool time_managed_ = false;
    bool aborted_ = false;
    int seldepth_ = 0;
    int root_depth_ = 0;
    std::size_t root_history_index_ = 0;
    std::vector<Move> root_moves_;
    bool root_restricted_ = false;
    std::uint64_t null_tries_ = 0;
    std::uint64_t null_cutoffs_ = 0;

    int search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    int qsearch(Board& board, SearchStack* ss, int alpha, int beta);
    [[nodiscard]] bool should_stop();
    [[nodiscard]] std::int64_t elapsed_ms() const;
    [[nodiscard]] bool is_draw(const Board& board, int ply) const;
    void update_quiet_stats(const Board& board, SearchStack* ss, Move move, int depth,
                            const Move* quiets, int quiet_count);
    void update_capture_stats(const Board& board, Move best, int depth, const Move* captures, int capture_count);
    void update_continuation(SearchStack* ss, Piece piece, int to, int bonus);
    [[nodiscard]] int quiet_history(const Board& board, const SearchStack* ss, Move move) const;
    [[nodiscard]] int capture_history_value(const Board& board, Move move) const;
    [[nodiscard]] int corrected_eval(const Board& board, int raw_eval) const;
    void update_correction(const Board& board, int depth, int best_score, int static_eval);
};

} // namespace forge
