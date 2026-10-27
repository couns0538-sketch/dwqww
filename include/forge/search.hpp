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
    // SmpBestThread: replace thread 0's move/PV/score by the best helper's.
    void select_best_thread(SearchInfo& result, const std::vector<SearchInfo>& helper_results, bool emit_info);

    SharedSearchState shared_;
    std::vector<std::unique_ptr<Worker>> workers_;
};

} // namespace forge
