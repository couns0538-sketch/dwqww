#pragma once

#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/nnue_v3.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <thread>
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

struct TTEntry {
    std::uint32_t key32 = 0;
    Move move{};
    std::int16_t score = 0;
    std::int16_t eval = 0;
    std::uint8_t depth = 0;
    // Bits 0..1 bound, bit 2 was-PV, bits 3..7 generation.
    std::uint8_t gen_bound = 0;
    std::uint8_t rule50_clock = 0; // Capped at100; belongs to admitted score payload.
    std::uint8_t padding = 0;

    [[nodiscard]] Bound bound() const { return static_cast<Bound>(gen_bound & 3U); }
    [[nodiscard]] bool pv() const { return (gen_bound & 4U) != 0; }
    [[nodiscard]] std::uint8_t generation() const { return static_cast<std::uint8_t>(gen_bound >> 3U); }
    [[nodiscard]] bool occupied() const { return bound() != BoundNone; }
    // Existing below90 policy, plus exact near50 context; not a repetition key.
    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        const int capped = current_clock < 100 ? current_clock : 100;
        return (rule50_clock < 90 && capped < 90) || rule50_clock == capped;
    }
};

struct alignas(64) TTCluster {
    std::array<TTEntry, 4> entries{};
};
static_assert(sizeof(TTEntry) == 16);
static_assert(sizeof(TTCluster) == 64);

class TranspositionTable;

// Immutable entry copy plus an opaque probe-time replacement destination.
struct TTProbe {
    TTEntry entry{};
    bool hit = false;
private:
    friend class TranspositionTable;
    const TranspositionTable* owner_ = nullptr;
    std::size_t cluster_ = 0;
    std::uint8_t slot_ = 0;
    std::uint64_t epoch_ = 0;
    std::uint64_t key_ = 0;
};

// Search reads and writes are coherent under striped locks. clear/resize/
// new_search/destruction require all accessors quiescent (including diagnostic
// readers and prefetch callers) and invalidate old probes. Handles must not
// outlive the table; lifecycle operations are not safe concurrently with search.
class TranspositionTable {
public:
    explicit TranspositionTable(std::size_t mb = 32) { resize(mb); }
    void resize(std::size_t mb);
    void clear();
    void new_search() { generation_ = static_cast<std::uint8_t>((generation_ + 1U) & 31U); ++epoch_; }
    [[nodiscard]] TTProbe probe(std::uint64_t key) const;
    void store(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth, Bound bound, bool pv, std::uint16_t halfmove_clock);
    [[nodiscard]] int hashfull() const;
    [[nodiscard]] std::uint8_t generation() const { return generation_; }
    [[nodiscard]] std::size_t cluster_count() const { return cluster_count_; }
    void prefetch(std::uint64_t key) const {
#if defined(__GNUC__) || defined(__clang__)
        __builtin_prefetch(&cluster_for(key));
#else
        (void)key;
#endif
    }

private:
    friend class Searcher;
    static constexpr std::size_t StripeCount = 1024;
    struct alignas(64) Stripe { std::mutex mutex; };
    // Opt-in controller ownership: request exclusive access, drain each stripe,
    // then publish TLS. Lifecycle mutations still require all users quiescent.
    class ExclusiveLease {
    public:
        explicit ExclusiveLease(TranspositionTable& table);
        ~ExclusiveLease();
        ExclusiveLease(const ExclusiveLease&) = delete;
        ExclusiveLease& operator=(const ExclusiveLease&) = delete;
        ExclusiveLease(ExclusiveLease&&) = delete;
        ExclusiveLease& operator=(ExclusiveLease&&) = delete;
    private:
        friend class TranspositionTable;
        TranspositionTable& table_;
        const ExclusiveLease* previous_;
        std::unique_lock<std::mutex> gate_;
    };
    static thread_local const ExclusiveLease* active_lease_;
    [[nodiscard]] bool has_exclusive_access() const;
    [[nodiscard]] std::unique_lock<std::mutex> lock_stripe(std::size_t index) const;
    mutable std::array<Stripe, StripeCount> stripes_{};
    mutable std::mutex exclusive_gate_;
    std::atomic<bool> exclusive_requested_{false};
    std::uint64_t epoch_ = 0;
    std::unique_ptr<TTCluster[]> clusters_;
    std::size_t cluster_count_ = 0;
    std::uint8_t generation_ = 0;

    [[nodiscard]] static constexpr std::uint32_t verification_key(std::uint64_t key) {
#if defined(__SIZEOF_INT128__)
        // Multiply-high indexing consumes high key bits. Keep the independent
        // low bits as the tag, rather than reusing the bucket's index bits.
        return static_cast<std::uint32_t>(key);
#else
        // Modulo indexing consumes low bits for power-of-two table sizes.
        return static_cast<std::uint32_t>(key >> 32U);
#endif
    }

    [[nodiscard]] TTCluster& cluster_for(std::uint64_t key) const {
#if defined(__SIZEOF_INT128__)
        __extension__ using u128 = unsigned __int128;
        return clusters_[static_cast<std::size_t>((static_cast<u128>(key) * cluster_count_) >> 64U)];
#else
        return clusters_[static_cast<std::size_t>(key % cluster_count_)];
#endif
    }
};

// Search constants exposed for tuning. The UCI layer accepts them as unlisted
// options (setoption name <Name> value <int>); defaults are the tested values.
namespace tune {
struct Parameter {
    const char* name;
    int* value;
    int minimum;
    int maximum;
};
extern int LmrQuietBase;      // x0.01
extern int LmrQuietDivisor;   // x0.01
extern int LmrNoisyBase;      // x0.01
extern int LmrNoisyDivisor;   // x0.01
extern int NullMoveMinDepth;
extern int NullMoveBase;
extern int NullMoveDepthDivisor;
extern int NullMoveEvalDivisor;
extern int RfpDepth;
extern int RfpMargin;
extern int RfpImproving;
extern int RazorDepth;
extern int RazorBase;
extern int RazorMultiplier;
extern int FutilityDepth;
extern int FutilityBase;
extern int FutilityMultiplier;
extern int LmpBase;
extern int HistoryPruneDepth;
extern int HistoryPruneMultiplier;
extern int SeeQuietMultiplier;
extern int SeeNoisyMultiplier;
extern int SingularDepth;
extern int SingularMargin;
extern int IirDepth;
extern int ProbcutDepth;
extern int ProbcutMargin;
extern int QsFutilityMargin;
extern int QsSeeMargin;
extern int AspirationDelta;
extern int HistoryBonusQuadratic;
extern int HistoryBonusLinear;
extern int HistoryBonusMax;
extern int LmrHistoryDivisor;
extern int CheckExtensionDepth;
extern int LmrCutoffThreshold;    // child cutoff count above which late moves are reduced more (0 = off)
extern int MaterialCorrectionWeight; // 0 = off, 100 = same weight as the pawn correction
// Time management (sudden-death / increment controls).
extern int TmSoftDivisor;         // soft limit = remaining / divisor + increment share
extern int TmIncrementPercent;    // share of the increment added to the soft limit
extern int TmHardPercent;         // hard limit as a percentage of the remaining time
extern int TmHardSoftMultiple;    // hard limit cap as a multiple of the soft limit
extern int TmStableFactor;        // x0.01 soft scale after 6 stable iterations
extern int TmSemiStableFactor;    // x0.01 soft scale after 3 stable iterations
extern int TmUnstableFactor;      // x0.01 soft scale when the best move just changed
extern int TmEffortBase;          // x0.01: factor *= clamp(base - effort, 0.6, 1.4)
extern int TmFallingEvalPercent;  // extra percent of soft time per 100 cp of score drop since the previous iteration
extern int TmMinFactorPercent;    // lower bound of the combined soft-limit factor (x0.01)
extern int CaptureFutilityBase;   // futility pruning of captures: base margin (0 = off)
extern int CaptureFutilityMultiplier;
extern int CaptureFutilityDepth;
extern int FailLowContinuationBonus; // x0.01 of the history bonus given to the parent move on fail low (0 = off)
[[nodiscard]] const std::vector<Parameter>& parameters();
// Call after changing LMR parameters.
void refresh();
} // namespace tune

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
    int cutoff_count = 0;
    int double_extensions = 0;
    bool in_check = false;
    bool tt_pv = false;
    bool null_move_allowed = true;
    PieceToHistory* continuation = nullptr;
    // NNUE state: the accumulator is refreshed lazily from the nearest valid
    // ancestor using the piece changes recorded for each ply.
    nnue::Accumulator accumulator{};
    Evaluator::RuntimePsqt runtime_psqt{};
    nnue::DirtyPieces dirty{};
};

// State shared by every worker of one Searcher.
struct SharedSearchState {
    explicit SharedSearchState(std::size_t hash_mb) : tt(hash_mb) {}
    TranspositionTable tt;
    std::atomic<bool> stop{false};
    // 0 means pondering has not been converted into a timed search.
    std::atomic<std::int64_t> ponder_hit_ns{0};
};

// One search thread: owns its histories, stack and evaluation cache.
class Worker {
public:
    Worker(SharedSearchState& shared, int id);
    ~Worker();
    Worker(const Worker&) = delete;
    Worker& operator=(const Worker&) = delete;

    // Thread 0 drives time management and reporting; helpers search the same
    // root until the shared stop flag is raised.
    SearchInfo search(Board board, const SearchLimits& limits, bool emit_info, const std::vector<Worker*>& all);
    void clear();
    void clear_caches() { evaluator_.clear(); }
    [[nodiscard]] std::uint64_t nodes() const { return nodes_.load(std::memory_order_relaxed); }
    [[nodiscard]] bool is_main() const { return id_ == 0; }

private:
    friend struct SearcherTestProbe;
    friend class MovePicker;

    SharedSearchState& shared_;
    int id_ = 0;
    Evaluator evaluator_;
    std::unique_ptr<ButterflyHistory> main_history_;
    std::unique_ptr<CaptureHistory> capture_history_;
    std::unique_ptr<ContinuationHistory> continuation_history_;
    std::unique_ptr<CounterMoveTable> counter_moves_;
    std::unique_ptr<CorrectionHistory> correction_history_;
    std::unique_ptr<CorrectionHistory> material_correction_;
    std::array<SearchStack, MaxPly + 8> stack_{};
    // NNUE v3 (UCI NNUEArch) per-worker state, allocated on first use; null with the option off.
    std::unique_ptr<nnue::v3::WorkerState> v3_state_;
    std::array<Move, 256> root_effort_moves_{};
    std::array<std::uint64_t, 256> root_move_nodes_{};
    std::size_t root_effort_count_ = 0;

    bool pondering_ = false;
    std::chrono::steady_clock::time_point start_{};
    std::atomic<std::uint64_t> nodes_{0};
    std::uint64_t local_nodes_ = 0;
    const std::vector<Worker*>* all_workers_ = nullptr;
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
    [[nodiscard]] std::uint64_t total_nodes() const;
    [[nodiscard]] bool is_draw(const Board& board, int ply) const;
    void update_quiet_stats(const Board& board, SearchStack* ss, Move move, int depth,
                            const Move* quiets, int quiet_count);
    void update_capture_stats(const Board& board, Move best, int depth, const Move* captures, int capture_count);
    void update_continuation(SearchStack* ss, Piece piece, int to, int bonus);
    [[nodiscard]] int quiet_history(const Board& board, const SearchStack* ss, Move move) const;
    [[nodiscard]] int capture_history_value(const Board& board, Move move) const;
    [[nodiscard]] int corrected_eval(const Board& board, int raw_eval) const;
    void update_correction(const Board& board, int depth, int best_score, int static_eval);
    [[nodiscard]] int static_evaluate(const Board& board, SearchStack* ss);
    [[nodiscard]] int static_evaluate_v3(const Board& board, SearchStack* ss);   // src/search_v3.cpp
    void record_move(SearchStack* ss, const Board& board, const Move& move);
    void record_null_move(SearchStack* ss);
};

// Public search facade: a shared transposition table plus one or more workers.
class Searcher {
public:
    // Exclusive is for a controller with no concurrent diagnostics: at one
    // worker it drains the stripes and holds an exclusive gate. Foreign TT calls
    // block for the whole search and must not hold locks needed by search.
    // Multiple workers and the default library entry retain shared locking.
    enum class TTAccess { Shared, Exclusive };
    explicit Searcher(std::size_t hash_mb = 32, int threads = 1);
    ~Searcher();
    Searcher(const Searcher&) = delete;
    Searcher& operator=(const Searcher&) = delete;

    SearchInfo search(Board board, const SearchLimits& limits, bool emit_info = false,
                      TTAccess table_access = TTAccess::Shared);
    void stop() { shared_.stop.store(true, std::memory_order_relaxed); }
    void reset_stop() {
        shared_.stop.store(false, std::memory_order_relaxed);
        shared_.ponder_hit_ns.store(0, std::memory_order_relaxed);
    }
    void ponderhit() {
        const auto now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();
        std::int64_t expected = 0;
        (void)shared_.ponder_hit_ns.compare_exchange_strong(expected, now_ns);
    }
    void clear();
    void clear_hash();
    void resize_hash(std::size_t hash_mb);
    void set_threads(int threads);
    [[nodiscard]] int threads() const { return static_cast<int>(workers_.size()); }
    [[nodiscard]] int hashfull_permille() const { return shared_.tt.hashfull(); }
    [[nodiscard]] static int evaluate(const Board& board) { return Evaluator::evaluate_uncached(board); }
    [[nodiscard]] Worker& main_worker() { return *workers_.front(); }
    [[nodiscard]] TranspositionTable& transposition_table() { return shared_.tt; }

private:
    SharedSearchState shared_;
    std::vector<std::unique_ptr<Worker>> workers_;
};

} // namespace forge
