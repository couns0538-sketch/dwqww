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
    std::vector<std::thread> helpers;
    for (std::size_t i = 1; i < workers_.size(); ++i) {
        helpers.emplace_back([this, i, board, &worker_limits, &all]() {
            (void)workers_[i]->search(board, worker_limits, false, all);
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
    if (workers_.size() > 1 && options::smp_exact_nodes) {
        // Every worker published its final count before returning.
        result.nodes = 0;
        for (auto& worker : workers_) result.nodes += worker->nodes();
    }
    return result;
}

} // namespace forge
