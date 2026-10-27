// Search module: Searcher facade (workers / helper threads, TT lifecycle).
// Compiled as part of src/search.cpp (included exactly once).

namespace forge {

Searcher::Searcher(std::size_t hash_mb, int threads) : shared_(hash_mb) {
    set_threads(threads);
}

Searcher::~Searcher() = default;

void Searcher::set_threads(int threads) {
    const std::size_t count = static_cast<std::size_t>(std::clamp(threads, 1, 256));
    while (workers_.size() > count) workers_.pop_back();
    while (workers_.size() < count) {
        workers_.push_back(std::make_unique<Worker>(shared_, static_cast<int>(workers_.size())));
    }
}

void Searcher::resize_hash(std::size_t hash_mb) { shared_.tt.resize(hash_mb); }

void Searcher::clear_hash() {
    shared_.tt.clear();
    for (auto& worker : workers_) worker->clear_caches();
}

void Searcher::clear() {
    shared_.tt.clear();
    for (auto& worker : workers_) worker->clear();
}

SearchInfo Searcher::search(Board board, const SearchLimits& limits, bool emit_info, TTAccess table_access) {
    const auto supplied_start = limits.start_time != std::chrono::steady_clock::time_point{}
        ? limits.start_time : limits.request_start;
    const bool clocked = !limits.infinite && !limits.ponder &&
        (limits.time_ms >= 0 || limits.movetime_ms >= 0);
    const auto origin = supplied_start == std::chrono::steady_clock::time_point{} && clocked
        ? std::chrono::steady_clock::now() : supplied_start;
    SearchLimits worker_limits = limits;
    worker_limits.start_time = origin;
    std::vector<Worker*> all;
    all.reserve(workers_.size());
    for (auto& worker : workers_) all.push_back(worker.get());
    // Age the table once per search, before any worker can probe it.
    shared_.tt.new_search();
    std::optional<TranspositionTable::ExclusiveLease> exclusive;
    if (table_access == TTAccess::Exclusive && workers_.size() == 1) {
        exclusive.emplace(shared_.tt);
    }
    if (options::smp_exact_nodes) {
        // A helper publishes its count only from inside its own search; until it
        // has started, total_nodes() would read the previous search's count.
        for (auto& worker : workers_) worker->reset_published_nodes();
    }
    // Per-helper results for SmpBestThread (each slot written by one helper,
    // read after join).
    std::vector<SearchInfo> helper_results(options::smp_best_thread ? workers_.size() : 0);
    std::vector<std::thread> helpers;
    for (std::size_t i = 1; i < workers_.size(); ++i) {
        helpers.emplace_back([this, i, board, &worker_limits, &all, &helper_results]() {
            SearchInfo info = workers_[i]->search(board, worker_limits, false, all);
            if (!helper_results.empty()) helper_results[i] = std::move(info);
        });
    }
    SearchInfo result = workers_.front()->search(board, worker_limits, emit_info, all);
    // Wind down the helpers without clobbering an externally requested stop.
    const bool external_stop = shared_.stop.load(std::memory_order_relaxed);
    shared_.stop.store(true, std::memory_order_relaxed);
    for (auto& helper : helpers) helper.join();
    shared_.stop.store(external_stop, std::memory_order_relaxed);
    // `all` dies with this call: no worker may keep pointing at it.
    for (auto& worker : workers_) worker->end_search();
    if (workers_.size() > 1) {
        if (options::smp_exact_nodes) {
            // Every worker published its final count before returning.
            result.nodes = 0;
            for (auto& worker : workers_) result.nodes += worker->nodes();
        }
        if (options::smp_best_thread) select_best_thread(result, helper_results, emit_info);
    }
    return result;
}

// SmpBestThread ranking. A mate score does not become less true at a greater
// depth, so as soon as either result carries one, the higher score wins: a
// found mate is never replaced by a deeper line without one, a shorter mate
// beats a longer one, and any line that is not mated beats a mated one.
// Without mate scores the deeper completed iteration wins, then the higher
// score. Cold: called once per helper and search.
[[gnu::cold]] bool better_thread_result(const SearchInfo& candidate, const SearchInfo& best) {
    if (is_mate_score(candidate.score) || is_mate_score(best.score)) return candidate.score > best.score;
    return candidate.depth > best.depth || (candidate.depth == best.depth && candidate.score > best.score);
}

// Cold: runs once per search; keeps the hot search functions' placement unchanged.
[[gnu::cold]] void Searcher::select_best_thread(SearchInfo& result, const std::vector<SearchInfo>& helper_results,
                                               bool emit_info) {
    const SearchInfo* best = &result;
    for (std::size_t i = 1; i < helper_results.size(); ++i) {
        const SearchInfo& candidate = helper_results[i];
        if (candidate.best_move.is_none() || candidate.depth <= 0 || candidate.pv.empty()) continue;
        if (better_thread_result(candidate, *best)) best = &candidate;
    }
    if (best == &result || best->best_move == result.best_move) return;
    result.best_move = best->best_move;
    result.ponder_move = best->ponder_move;
    result.pv = best->pv;
    result.score = best->score;
    result.depth = best->depth;
    result.seldepth = std::max(result.seldepth, best->seldepth);
    if (!emit_info) return;
    // Publish the chosen line so GUIs see a PV consistent with the best move.
    const std::uint64_t nps = result.elapsed_ms > 0 ? result.nodes * 1000U / result.elapsed_ms : 0;
    const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
    std::cout << "info depth " << result.depth << " seldepth " << std::max(result.seldepth, result.depth)
              << " score " << format_score(result.score) << " nodes " << result.nodes << " nps " << nps
              << " hashfull " << shared_.tt.hashfull() << " time " << result.elapsed_ms << " pv";
    for (const Move move : result.pv) std::cout << ' ' << Board::move_to_uci(move);
    std::cout << std::endl;
}

} // namespace forge
