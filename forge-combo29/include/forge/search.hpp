#pragma once

#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>

#ifndef FORGE_SPD_TT_NOTLS
// Build switch, default 0 (= the lock's code): the Worker that runs on the thread
// holding the table's ExclusiveLease calls TT probe / store without lock_stripe.
#define FORGE_SPD_TT_NOTLS 0
#endif

namespace forge {

struct SearchLimits {
    int depth = 64;
    std::uint64_t nodes = 0;
    bool nodes_specified = false;
    // `go softnodes`: finish the iteration that passes `nodes`, hard-stop at 4x.
    // Left false for bench, `go depth`, and `go nodes`.
    bool soft_nodes = false;
    // Milliseconds. -1 means that limit was not given. parse_clock_ms stores
    // only non-negative values, including clocks that do not fit in 32 bits.
    std::int64_t movetime_ms = -1;
    std::int64_t time_ms = -1;
    std::int64_t increment_ms = 0;
    // 0 means the increment/sudden-death time control (no movestogo given).
    int moves_to_go = 0;
    int mate_moves = 0;
    int move_overhead_ms = 10;
    bool infinite = false;
    bool ponder = false;
    bool search_moves_specified = false;
    std::vector<Move> search_moves;
    // 1 keeps the single-line search. 2..8 also report the next root moves.
    int multipv = 1;
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

// Half-width, in centipawns, of repetition and fifty-move leaf scores.
// 0 keeps those leaves at exactly 0. Mate scores are never adjusted.
constexpr int DrawJitterMax = 8;
extern int DrawJitter;

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
#if FORGE_SPD_TT_NOTLS
    // One body per access with a compile-time "take the stripe lock" parameter.
    // probe / store keep lock_stripe; probe_owned / store_owned run the same body
    // without it and are only for the Worker on the lease's thread (tt_owned_).
    friend class Worker;
    template <bool TakeLock>
    [[nodiscard]] TTProbe probe_body(std::uint64_t key) const;
    template <bool TakeLock>
    void store_body(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth, Bound bound,
                    bool pv, std::uint16_t halfmove_clock);
    [[nodiscard]] TTProbe probe_owned(std::uint64_t key) const;
    void store_owned(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth, Bound bound,
                     bool pv, std::uint16_t halfmove_clock);
#endif
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
extern bool ContHist4PlyRead;        // read 4-ply-back continuation history in quiet scoring (false = off)
extern bool NonPawnCorrection;       // per-color non-pawn static-eval correction history (false = off)
extern bool LmrDeeperShallower;      // adjust new_depth by +/-1 after LMR before re-search (false = off)
extern bool EvalRule50Damp;          // shrink a node's static eval toward 0 as the half-move clock rises (false = off)
extern bool ThreatHistory;           // second quiet history keyed by cheaper-attacker threats (false = off)
extern bool LmrSignedCorrection;     // quiet LMR: signed fraction of a ply from correction history (false = off)
extern bool LmrLateParentRelief;     // one ply less reduction on the first few replies after a late parent (false = off)
extern bool HindsightDepth;          // off-PV depth step after a reduced move (false = off)
extern bool NullThreatVerify;        // null cutoff needs a reduced non-null search when a cheaper enemy piece attacks a dearer piece (false = off)
extern bool NullSeeVeto;             // refuse a null-move cutoff on a cheaper capture of a dearer piece that SEE does not call a loss (false = off)
extern bool AspCappedReopen;         // root fail: capped reopen, or full open when decisive (false = off)
extern bool AspArmLate;              // after a root iteration that failed high or low, the next iteration uses a full window (false = off)
extern bool EvasionOrdering;         // in check, history-order evasions (false = off)
extern bool QuietExtinction;         // non-root quiet-tail cutoff after wide fail-lows (false = off)
extern bool TmFinishIteration;       // on a clock, skip an iteration the last two times say cannot finish (false = off)
extern bool TmNodeShare;             // clock-only soft target from the root-node split (false = off)
extern bool SoundMatePruning;        // skip move-loop pruning on PV, in check, and mate alpha (false = off)
// Per-case arms. FollowOption tracks SoundMatePruning. Tests force one arm
// without the other two. Defaults leave the option's on/off behavior unchanged.
enum class SoundPruneArm : std::uint8_t { FollowOption, ForceOff, ForceOn };
inline SoundPruneArm SoundArmPv = SoundPruneArm::FollowOption;
inline SoundPruneArm SoundArmInCheck = SoundPruneArm::FollowOption;
inline SoundPruneArm SoundArmMateAlpha = SoundPruneArm::FollowOption;
[[nodiscard]] inline bool sound_arm_enabled(SoundPruneArm arm) {
    switch (arm) {
    case SoundPruneArm::ForceOn:
        return true;
    case SoundPruneArm::ForceOff:
        return false;
    case SoundPruneArm::FollowOption:
        return SoundMatePruning;
    }
    return SoundMatePruning;
}
// Counting is off unless a test turns it on. The search does not read the counts.
inline bool SoundPruneTrace = false;
struct SoundPruneTraceCounts {
    std::uint64_t pv = 0;
    std::uint64_t in_check = 0;
    std::uint64_t mate_alpha = 0;
    std::uint64_t quiet_check_after_quiet_fail = 0;
    std::uint64_t quiet_check_on_pv = 0;
    std::uint64_t quiet_check_in_check = 0;
    std::uint64_t quiet_check_on_mate_alpha = 0;
};
inline SoundPruneTraceCounts sound_prune_trace{};
[[nodiscard]] const std::vector<Parameter>& parameters();
// Call after changing LMR parameters.
void refresh();
} // namespace tune

// Static evaluation as a node reads it. Clock 0 keeps the whole score. Each
// half-move already played drops one percent, so a clock near 100 keeps only
// a sliver. Mate scores and ValueNone are never scaled. The hash table stores
// the unscaled raw evaluation; this is not applied on the way in.
[[nodiscard]] inline int rule50_damped_static(int score, int halfmove) {
    if (!tune::EvalRule50Damp || score == ValueNone || is_mate_score(score)) return score;
    const int clock = halfmove < 0 ? 0 : (halfmove > 100 ? 100 : halfmove);
    return score * (100 - clock) / 100;
}

// Quiet late-move reduction with a signed fraction of a ply from the eval
// correction. correction_cp is the corrected static eval minus the uncorrected
// eval (negative when results came back worse). The adjustment is
// correction_cp/64 rounded toward zero, then limited to -1..+1 ply. The
// returned reduction is never negative.
[[nodiscard]] inline int apply_lmr_signed_correction(int reduction_plies, int correction_cp) {
    int delta = correction_cp / 64;
    if (delta > 1) delta = 1;
    if (delta < -1) delta = -1;
    const int adjusted = reduction_plies - delta;
    return adjusted > 0 ? adjusted : 0;
}

// True when an enemy piece of strictly lower SEE value attacks a piece of the side to move.
[[nodiscard]] bool cheaper_enemy_attacks_dearer(const Board& board);

// Side to move is the defender. True when the opponent has a legal capture of a
// dearer piece by a cheaper piece and static exchange evaluation does not call
// that capture a material loss. A capture SEE calls losing is not a threat.
[[nodiscard]] bool null_see_veto_threat(Board& board);

// Move-ordering statistics.
using ButterflyHistory = std::array<std::array<std::array<std::int16_t, 64>, 64>, 2>;
// [side][threat 0..3][from][to]. Threat bit 1: mover attacked by a cheaper enemy.
// Threat bit 0: the destination square is attacked by a cheaper enemy than the mover.
using ThreatQuietHistory = std::array<std::array<std::array<std::array<std::int16_t, 64>, 64>, 4>, 2>;
[[nodiscard]] int quiet_threat_index(const Board& board, Move move);
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
    // 1-based index of the move that entered this node. 0 means the node was not
    // reached by a counted move (root, null move, or a probcut capture).
    int arrival_index = 0;
    int cutoff_count = 0;
    int double_extensions = 0;
    // Plies the parent withheld when it searched the move that reached this node.
    // Zero means that call was not a reduced search. Read only when HindsightDepth is on.
    int withheld_plies = 0;
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
    // Zero the count other workers add into a node budget. Searcher::search does
    // this for every worker before it starts any of them.
    void reset_node_count() {
        local_nodes_ = 0;
        nodes_.store(0, std::memory_order_relaxed);
    }
    [[nodiscard]] bool is_main() const { return id_ == 0; }

private:
    friend struct SearcherTestProbe;
    friend class MovePicker;
#if FORGE_SPD_TT_NOTLS
    friend class Searcher;
#endif

    SharedSearchState& shared_;
    int id_ = 0;
    Evaluator evaluator_;
    std::unique_ptr<ButterflyHistory> main_history_;
    std::unique_ptr<ThreatQuietHistory> threat_history_;
    std::unique_ptr<CaptureHistory> capture_history_;
    std::unique_ptr<ContinuationHistory> continuation_history_;
    std::unique_ptr<CounterMoveTable> counter_moves_;
    std::unique_ptr<CorrectionHistory> correction_history_;
    std::unique_ptr<CorrectionHistory> material_correction_;
    std::unique_ptr<CorrectionHistory> non_pawn_white_correction_;
    std::unique_ptr<CorrectionHistory> non_pawn_black_correction_;
    std::array<SearchStack, MaxPly + 8> stack_{};
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
    // Nonzero only for a main-thread `go softnodes` search. 0 leaves the loop alone.
    std::uint64_t soft_node_limit_ = 0;
    std::int64_t soft_limit_ms_ = 0;
    std::int64_t hard_limit_ms_ = 0;
    bool time_managed_ = false;
    // Clock play with no time left after Move Overhead. A hard limit of 0
    // means "not on a clock", so this flag is what makes the search stop.
    bool clock_reserve_empty_ = false;
    bool aborted_ = false;
    // Set only when the node budget itself trips should_stop. A clock stop or an
    // external stop leaves this false so those paths keep the partial root move.
    bool stopped_by_nodes_ = false;
    Worker* parent_worker_ = nullptr;
    std::uint64_t extra_nodes_ = 0;
#if FORGE_SPD_TT_NOTLS
    // True only while Searcher::search runs this (main) worker on the thread that
    // holds the table's ExclusiveLease; lock_stripe would hand back a deferred lock.
    bool tt_owned_ = false;
#endif
    int seldepth_ = 0;
    int root_depth_ = 0;
    int mate_moves_ = 0;
    std::size_t root_history_index_ = 0;
    std::vector<Move> root_moves_;
    bool root_restricted_ = false;
    std::uint64_t null_tries_ = 0;
    std::uint64_t null_cutoffs_ = 0;
    // True only inside a NullThreatVerify confirmation, so that reduced search
    // does not use null moves. Stays false for the whole default search.
    bool null_blocked_ = false;

#if FORGE_SPD_TT_NOTLS
    // The six TT call sites of search / qsearch: one predictable branch per access.
    [[nodiscard]] TTProbe probe_tt(std::uint64_t key) const {
        return tt_owned_ ? shared_.tt.probe_owned(key) : shared_.tt.probe(key);
    }
    void store_tt(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth, Bound bound,
                  bool pv, std::uint16_t halfmove_clock) {
        if (tt_owned_) shared_.tt.store_owned(probe, key, score, eval, move, depth, bound, pv, halfmove_clock);
        else shared_.tt.store(probe, key, score, eval, move, depth, bound, pv, halfmove_clock);
    }
#endif
    int search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    int qsearch(Board& board, SearchStack* ss, int alpha, int beta);
    [[nodiscard]] bool should_stop();
    [[nodiscard]] bool should_stop_with(std::uint64_t pending_nodes);
    [[nodiscard]] std::int64_t elapsed_ms() const;
    [[nodiscard]] std::uint64_t total_nodes() const;
    [[nodiscard]] bool is_draw(const Board& board, int ply) const;
    // Score for a repetition or fifty-move leaf. Other draws stay at 0.
    [[nodiscard]] int draw_leaf_score(const Board& board) const;
    void update_quiet_stats(const Board& board, SearchStack* ss, Move move, int depth,
                            const Move* quiets, int quiet_count);
    void update_capture_stats(const Board& board, Move best, int depth, const Move* captures, int capture_count);
    void update_continuation(SearchStack* ss, Piece piece, int to, int bonus);
    [[nodiscard]] int quiet_history(const Board& board, const SearchStack* ss, Move move) const;
    [[nodiscard]] int threat_quiet_bonus(const Board& board, Move move) const;
    void update_threat_quiet(const Board& board, Move move, int bonus);
    [[nodiscard]] int capture_history_value(const Board& board, Move move) const;
    [[nodiscard]] int corrected_eval(const Board& board, int raw_eval) const;
    void update_correction(const Board& board, int depth, int best_score, int static_eval);
    [[nodiscard]] int static_evaluate(const Board& board, SearchStack* ss);
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

// Updates DrawJitter. A changed value drops that searcher's hash, so scores
// stored under the previous width are not reused. An unchanged value does not.
void set_draw_jitter(int value, Searcher& searcher);

} // namespace forge
