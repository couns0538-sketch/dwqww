// Search module: per-node checks — the clock (ponder-aware), node totals over
// all workers, the hard stop test (stop flag, node limit, hard time limit) and
// draw detection.
// Compiled as part of src/search.cpp (included exactly once).

namespace forge {

std::int64_t Worker::elapsed_ms() const {
    auto origin = start_;
    if (pondering_) {
        const std::int64_t hit_ns = shared_.ponder_hit_ns.load(std::memory_order_relaxed);
        if (hit_ns == 0) return 0;
        origin = std::chrono::steady_clock::time_point(
            std::chrono::duration_cast<std::chrono::steady_clock::duration>(std::chrono::nanoseconds(hit_ns)));
    }
    return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - origin).count();
}

std::uint64_t Worker::total_nodes() const {
    std::uint64_t total = local_nodes_;
    if (all_workers_ != nullptr) {
        for (const Worker* worker : *all_workers_) {
            if (worker != this) total += worker->nodes();
        }
    }
    return total;
}

bool Worker::should_stop() {
    // Publish this thread's node count for the others at the same cadence.
    nodes_.store(local_nodes_, std::memory_order_relaxed);
    if (shared_.stop.load(std::memory_order_relaxed)) return true;
    if (!is_main()) return false;
    if (node_limit_specified_ && total_nodes() >= node_limit_) return true;
    if (hard_limit_ms_ > 0) {
        if (pondering_ && shared_.ponder_hit_ns.load(std::memory_order_relaxed) == 0) return false;
        if (elapsed_ms() >= hard_limit_ms_) return true;
    }
    return false;
}

bool Worker::is_draw(const Board& board, int ply) const {
    (void)ply;
    if (board.halfmove_clock() >= 100) {
        // Checkmate on the hundredth half-move still wins; everything else is a draw.
        return !board.in_check() || board.has_legal_move();
    }
    // Detect stalemate before TT cutoffs, stand pat or forward pruning can
    // replace its terminal draw score with a material evaluation.
    return board.is_repetition(root_history_index_) || board.is_insufficient_material() ||
           (!board.in_check() && !board.has_legal_move());
}

} // namespace forge
