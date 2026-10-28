#pragma once

#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/history.hpp"
#include "forge/nnue.hpp"
#include "forge/search_options.hpp"
#include "forge/search_tune.hpp"
#include "forge/search_types.hpp"
#include "forge/thread_data.hpp"
#include "forge/tt.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <thread>
#include <utility>
#include <vector>

namespace forge {

// One search thread: owns its histories, stack and evaluation cache (ThreadData).
class Worker : private ThreadData {
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
    // Searcher housekeeping, only while this worker is not searching.
    void reset_published_nodes() { nodes_.store(0, std::memory_order_relaxed); }
    // The caller's worker list (all_workers_) is valid only during one search.
    void end_search() { all_workers_ = nullptr; }

private:
    friend struct SearcherTestProbe;
    friend class MovePicker;

    // Pinned to 64-byte boundaries (like MovePicker::next): their placement no
    // longer depends on the size of the code emitted before them.
    [[gnu::aligned(64)]] int search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    // UCI CorrMargins: the main search with correction-size pruning margins
    // (forge/corr_margins.hpp), a second instance of src/search/alphabeta.inc.
    int search_corr_margins(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    // UCI CorrExt: the main search with correction-history extensions
    // (forge/corr_ext.hpp), another instance of src/search/alphabeta.inc.
    int search_corr_ext(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    // R3 stack: CorrMargins and CorrExt together.
    int search_cm_ce(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    [[gnu::aligned(64)]] int qsearch(Board& board, SearchStack* ss, int alpha, int beta);
    // UCI CuckooRep: search / qsearch with the upcoming-repetition draw bound
    // (src/search/cuckoo.inc), wrapping second instances of the two functions
    // (src/search/{alphabeta,qsearch}.inc) whose child calls come back here.
    int search_cuckoo(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    int qsearch_cuckoo(Board& board, SearchStack* ss, int alpha, int beta);
    int search_cuckoo_body(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    int qsearch_cuckoo_body(Board& board, SearchStack* ss, int alpha, int beta);
    // R3 stack: CuckooRep together with CorrMargins and / or CorrExt (wrapper, instance).
    int search_cm_cu(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    int search_cm_cu_body(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    int search_ce_cu(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    int search_ce_cu_body(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    int search_cm_ce_cu(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
    int search_cm_ce_cu_body(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
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
    // CorrHistPlus (src/search/correction_plus.inc). corrected_eval and
    // update_correction jump to their cold twins only when
    // forge::options::corr_hist_plus != 0; the helpers are always inlined so
    // that corrected_eval_plus stays a leaf (see correction_plus.inc).
    [[gnu::cold]] [[nodiscard]] int corrected_eval_plus(const Board& board, int raw_eval) const;
    [[gnu::cold]] void update_correction_plus(const Board& board, int depth, int best_score, int static_eval);
    [[gnu::always_inline]] [[nodiscard]] inline int correction_plus(const Board& board) const;
    [[gnu::always_inline]] [[nodiscard]] inline const SearchStack* correction_frame(const Board& board) const;
    [[gnu::always_inline]] [[nodiscard]] inline std::size_t continuation_correction_index(const Board& board) const;
    // Pinned to a 64-byte boundary (its AL1 s198 placement): the hot search
    // functions after it then keep their alignment when the cold worker
    // lifecycle code before it in .text changes size (CorrHistPlus member).
    [[nodiscard, gnu::aligned(64)]] int static_evaluate(const Board& board, SearchStack* ss);
    // v2 network path (options::nnue_v2; src/search/evaluation_v2.inc).
    [[nodiscard]] int static_evaluate_v2(const Board& board, SearchStack* ss);
    // v2 network with threat and / or pawn-pair inputs (O6 / O7; src/search/evaluation_extra.inc).
    [[nodiscard]] int static_evaluate_extra(const Board& board, SearchStack* ss);
    void record_move(SearchStack* ss, const Board& board, const Move& move);
    void record_null_move(SearchStack* ss);
    // Syzygy WDL probe inside the search (src/search/tablebase.inc); only
    // called while tables are loaded. Returns ValueNone to search on.
    [[gnu::cold]] int probe_tablebase(Board& board, SearchStack* ss, int depth, int alpha, int beta,
                                      const TTProbe& tt_probe);
    // HardDeadline: publish the main worker's current best/ponder move pair.
    void publish_best_move(const SearchInfo& result);
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
#ifdef FORGE_S13_TT_CHILD_PREFETCH
    void set_s13_tt_child_prefetch(bool enabled) { shared_.s13_tt_child_prefetch.store(enabled, std::memory_order_relaxed); }
    [[nodiscard]] bool s13_tt_child_prefetch_enabled() const { return shared_.s13_tt_child_prefetch.load(std::memory_order_relaxed); }
#endif
    [[nodiscard]] int threads() const { return static_cast<int>(workers_.size()); }
    [[nodiscard]] int hashfull_permille() const { return shared_.tt.hashfull(); }
    [[nodiscard]] static int evaluate(const Board& board) { return Evaluator::evaluate_uncached(board); }
    [[nodiscard]] Worker& main_worker() { return *workers_.front(); }
    [[nodiscard]] TranspositionTable& transposition_table() { return shared_.tt; }
    // HardDeadline: best / ponder move pair of the main worker's last completed
    // iteration (Move::none() until the first one after reset_published_moves()).
    // Safe to call from any thread while a search runs.
    static void reset_published_moves() { options::published_moves.store(0, std::memory_order_relaxed); }
    [[nodiscard]] static std::pair<Move, Move> published_moves() {
        const std::uint64_t pair = options::published_moves.load(std::memory_order_relaxed);
        return {unpack_move(static_cast<std::uint32_t>(pair)), unpack_move(static_cast<std::uint32_t>(pair >> 32U))};
    }

private:
    // SmpBestThread: replace thread 0's move/PV/score by the best helper's
    // (ranking: better_thread_result below).
    void select_best_thread(SearchInfo& result, const std::vector<SearchInfo>& helper_results, bool emit_info);

    SharedSearchState shared_;
    std::vector<std::unique_ptr<Worker>> workers_;
};

// UCI SmpBestThread: whether a helper's result `candidate` replaces `best`
// (src/search/searcher.inc). With a mate score on either side the higher score
// wins; otherwise the deeper completed iteration, then the higher score.
[[nodiscard]] bool better_thread_result(const SearchInfo& candidate, const SearchInfo& best);

} // namespace forge
