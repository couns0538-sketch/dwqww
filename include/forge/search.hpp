#pragma once

#include "forge/board.hpp"
#include "forge/eval.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <functional>
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
// Quiet-move history indexed by a hash of the pawn structure, then piece and
// destination square.
constexpr std::size_t PawnHistorySize = 512;
using PawnHistory = std::array<PieceToHistory, PawnHistorySize>;
// Evaluation correction: running averages of (search score - static eval)
// indexed by features of the position, in units of 1/CorrectionGrain pawn.
constexpr std::size_t CorrectionSize = 1U << 14U;
constexpr int CorrectionGrain = 256;
constexpr int CorrectionLimit = 32 * CorrectionGrain;
using CorrectionEntry = std::int16_t;
// [side to move][key hash]
using CorrectionHistory = std::array<std::array<CorrectionEntry, CorrectionSize>, 2>;
// [piece moved two plies ago][its square][piece moved one ply ago][its square]
using ContinuationCorrectionHistory =
    std::array<std::array<std::array<std::array<CorrectionEntry, 64>, 13>, 64>, 13>;

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
    // Fail highs seen at this ply while the parent iterated its moves.
    int cutoff_count = 0;
    bool in_check = false;
    bool tt_pv = false;
    bool null_move_allowed = true;
    PieceToHistory* continuation = nullptr;
};

class Searcher {
public:
    // A stand-alone searcher owns its transposition table.
    explicit Searcher(std::size_t hash_mb = 32);
    // A pool member shares the table; thread 0 is the main thread, which alone
    // manages time, node limits, table ageing and output.
    Searcher(TranspositionTable& shared_tt, int thread_id);
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
    void reset_histories();
    void resize_hash(std::size_t hash_mb);
    [[nodiscard]] int hashfull_permille() const { return tt_->hashfull(); }
    [[nodiscard]] static int evaluate(const Board& board) { return Evaluator::evaluate_uncached(board); }
    [[nodiscard]] std::uint64_t nodes() const { return nodes_; }
    // Node count as last published by this thread; safe to read from others.
    [[nodiscard]] std::uint64_t published_nodes() const { return published_nodes_.load(std::memory_order_relaxed); }
    // Nodes searched by the other threads of the pool, added to UCI output.
    void set_helper_node_source(std::function<std::uint64_t()> source) { helper_nodes_ = std::move(source); }
    // Result of the most recent search() call (valid once it has returned).
    [[nodiscard]] const SearchInfo& last_result() const { return last_result_; }
    // Prints a UCI info line for a result (used when the pool adopts a
    // helper thread's line).
    void report(const SearchInfo& info) const;

private:
    friend struct SearcherTestProbe;
    friend class MovePicker;

    std::unique_ptr<TranspositionTable> owned_tt_;
    TranspositionTable* tt_;
    int thread_id_ = 0;
    std::atomic<std::uint64_t> published_nodes_{0};
    std::function<std::uint64_t()> helper_nodes_;
    Evaluator evaluator_;
    std::unique_ptr<ButterflyHistory> main_history_;
    std::unique_ptr<CaptureHistory> capture_history_;
    std::unique_ptr<ContinuationHistory> continuation_history_;
    std::unique_ptr<CounterMoveTable> counter_moves_;
    std::unique_ptr<PawnHistory> pawn_history_;
    std::unique_ptr<CorrectionHistory> pawn_correction_;
    std::array<std::unique_ptr<CorrectionHistory>, 2> non_pawn_correction_;
    std::unique_ptr<CorrectionHistory> minor_correction_;
    std::unique_ptr<CorrectionHistory> major_correction_;
    std::unique_ptr<ContinuationCorrectionHistory> continuation_correction_;
    std::array<SearchStack, MaxPly + 8> stack_{};
    std::array<std::uint64_t, 256> root_move_nodes_{};
    int root_best_index_ = -1;
    SearchInfo last_result_;

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

    SearchInfo iterative_deepening(Board board, const SearchLimits& limits, bool emit_info);
    int search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    // depth 0 is the first quiescence ply (which also tries quiet checks);
    // deeper plies are negative.
    int qsearch(Board& board, SearchStack* ss, int alpha, int beta, int depth = 0);
    [[nodiscard]] bool should_stop();
    [[nodiscard]] std::int64_t elapsed_ms() const;
    [[nodiscard]] bool is_draw(const Board& board, int ply) const;
    void update_quiet_stats(const Board& board, SearchStack* ss, Move move, int depth,
                            const Move* quiets, int quiet_count);
    void update_capture_stats(const Board& board, Move best, int depth, const Move* captures, int capture_count);
    void update_continuation(SearchStack* ss, Piece piece, int to, int bonus);
    // Butterfly plus continuation history: drives pruning and reductions.
    [[nodiscard]] int quiet_history(const Board& board, const SearchStack* ss, Move move) const;
    // quiet_history plus the pawn-structure history: orders the quiet moves.
    [[nodiscard]] int ordering_history(const Board& board, const SearchStack* ss, Move move) const;
    [[nodiscard]] int capture_history_value(const Board& board, Move move) const;
    [[nodiscard]] int corrected_eval(const Board& board, const SearchStack* ss, int raw_eval) const;
    void update_correction(const Board& board, const SearchStack* ss, int depth, int best_score, int static_eval);
};

// Lazy SMP: every thread runs the same iterative deepening on the same root
// and shares the transposition table; the main thread owns the clock and the
// result, and the helpers are stopped when it finishes.
class ThreadPool {
public:
    explicit ThreadPool(std::size_t hash_mb = 32, int threads = 1);
    ~ThreadPool();
    ThreadPool(const ThreadPool&) = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;

    void set_threads(int threads);
    [[nodiscard]] int threads() const { return static_cast<int>(searchers_.size()); }
    SearchInfo search(Board board, const SearchLimits& limits, bool emit_info = false);
    void stop();
    void reset_stop();
    void ponderhit() { searchers_.front()->ponderhit(); }
    void clear();
    void clear_hash();
    void resize_hash(std::size_t hash_mb);
    [[nodiscard]] int hashfull_permille() const { return tt_.hashfull(); }
    [[nodiscard]] std::uint64_t nodes() const;

private:
    TranspositionTable tt_;
    std::vector<std::unique_ptr<Searcher>> searchers_;

    [[nodiscard]] std::uint64_t helper_nodes() const;
    [[nodiscard]] const SearchInfo& vote(const SearchInfo& main_result) const;
};

} // namespace forge
