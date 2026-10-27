// Search module: transposition table (interface in forge/tt.hpp).
// Compiled as part of src/search.cpp (included exactly once).

namespace forge {

thread_local const TranspositionTable::ExclusiveLease* TranspositionTable::active_lease_ = nullptr;

TranspositionTable::ExclusiveLease::ExclusiveLease(TranspositionTable& table)
    : table_(table), previous_(active_lease_), gate_(table.exclusive_gate_, std::defer_lock) {
    if (!table_.has_exclusive_access()) {
        gate_.lock();
        table_.exclusive_requested_.store(true, std::memory_order_release);
        try {
            // A foreign accessor either completes before its stripe drains,
            // or observes the request after acquiring that drained stripe.
            for (std::size_t i = 0; i < StripeCount; ++i) {
                const std::lock_guard<std::mutex> drain(table_.stripes_[i].mutex);
            }
        } catch (...) {
            table_.exclusive_requested_.store(false, std::memory_order_release);
            throw;
        }
    }
    active_lease_ = this;
}

TranspositionTable::ExclusiveLease::~ExclusiveLease() {
    // Publish completed writes before member destruction releases the gate.
    active_lease_ = previous_;
    if (gate_.owns_lock()) table_.exclusive_requested_.store(false, std::memory_order_release);
}

bool TranspositionTable::has_exclusive_access() const {
    for (const ExclusiveLease* lease = active_lease_; lease != nullptr; lease = lease->previous_) {
        if (&lease->table_ == this) return true;
    }
    return false;
}

std::unique_lock<std::mutex> TranspositionTable::lock_stripe(std::size_t index) const {
    std::mutex& stripe = stripes_[index % StripeCount].mutex;
    if (has_exclusive_access()) return std::unique_lock<std::mutex>(stripe, std::defer_lock);
    for (;;) {
        std::unique_lock<std::mutex> lock(stripe);
        if (!exclusive_requested_.load(std::memory_order_acquire)) return lock;
        // Never wait for the gate while holding a stripe: the owner drains it.
        lock.unlock();
        const std::lock_guard<std::mutex> wait(exclusive_gate_);
    }
}

void TranspositionTable::resize(std::size_t mb) {
    const std::size_t bytes = std::max<std::size_t>(1, mb) * 1024U * 1024U;
    const std::size_t new_count = std::max<std::size_t>(1, bytes / sizeof(TTCluster));
    auto new_clusters = std::make_unique<TTCluster[]>(new_count);
    clusters_ = std::move(new_clusters);
    cluster_count_ = new_count;
    generation_ = 0;
    ++epoch_;
}

void TranspositionTable::clear() {
    for (std::size_t i = 0; i < cluster_count_; ++i) clusters_[i] = TTCluster{};
    generation_ = 0;
    ++epoch_;
}

TTProbe TranspositionTable::probe(std::uint64_t key) const {
    if (lockless_) [[unlikely]] return probe_lockless(key);
    TTCluster& cluster = cluster_for(key);
    const std::size_t index = static_cast<std::size_t>(&cluster - clusters_.get());
    const auto lock = lock_stripe(index);
    auto snapshot = [&](const TTEntry& entry, bool hit) {
        TTProbe result;
        result.entry = entry;
        result.hit = hit;
        result.owner_ = this;
        result.cluster_ = index;
        result.slot_ = static_cast<std::uint8_t>(&entry - cluster.entries.data());
        result.epoch_ = epoch_;
        result.key_ = key;
        return result;
    };
    const std::uint32_t key32 = verification_key(key);
    for (TTEntry& entry : cluster.entries) {
        if (entry.key32 == key32 && entry.occupied()) {
            // Reused entries remain recent even when search returns a TT cutoff.
            if (entry.generation() != generation_) {
                entry.gen_bound = static_cast<std::uint8_t>(
                    (static_cast<unsigned>(generation_) << 3U) | (entry.gen_bound & 7U));
            }
            return snapshot(entry, true);
        }
    }
    const TTEntry* replace = &cluster.entries[0];
    auto relative_age = [this](const TTEntry& entry) {
        return static_cast<int>((32 + generation_ - entry.generation()) & 31U);
    };
    for (const TTEntry& entry : cluster.entries) {
        if (!entry.occupied()) return snapshot(entry, false);
        if (entry.depth - 4 * relative_age(entry) < replace->depth - 4 * relative_age(*replace)) replace = &entry;
    }
    return snapshot(*replace, false);
}

void TranspositionTable::store(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth,
                               Bound bound, bool pv, std::uint16_t halfmove_clock) {
    // Reject default, foreign or lifecycle-stale handles without touching storage.
    // Lifecycle operations themselves must not run concurrently with search.
    if (probe.owner_ != this || probe.epoch_ != epoch_ || probe.key_ != key ||
        probe.cluster_ >= cluster_count_ || probe.slot_ >= 4) return;
    if (lockless_) [[unlikely]] {
        store_lockless(probe, key, score, eval, move, depth, bound, pv, halfmove_clock);
        return;
    }
    const auto lock = lock_stripe(probe.cluster_);
    TTEntry* entry = &clusters_[probe.cluster_].entries[probe.slot_];
    const std::uint32_t key32 = verification_key(key);
    const bool same_position = entry->key32 == key32 && entry->occupied();
    if (!move.is_none() || !same_position) entry->move = move;
    if (bound == BoundExact || !same_position || depth + 4 > entry->depth || entry->generation() != generation_) {
        entry->key32 = key32;
        entry->score = static_cast<std::int16_t>(std::clamp(score, -32767, 32767));
        entry->rule50_clock = static_cast<std::uint8_t>(std::min<int>(halfmove_clock, 100));
        entry->eval = static_cast<std::int16_t>(std::clamp(eval, -32767, 32767));
        entry->depth = static_cast<std::uint8_t>(std::clamp(depth, 0, 255));
        entry->gen_bound = static_cast<std::uint8_t>((static_cast<unsigned>(generation_) << 3U) | (pv ? 4U : 0U) | static_cast<unsigned>(bound));
    }
}

int TranspositionTable::hashfull() const {
    if (lockless_) return hashfull_lockless();
    int count = 0;
    const std::size_t sample = std::min<std::size_t>(1000, cluster_count_);
    for (std::size_t i = 0; i < sample; ++i) {
        const auto lock = lock_stripe(i);
        for (const TTEntry& entry : clusters_[i].entries) {
            if (entry.occupied() && entry.generation() == generation_) ++count;
        }
    }
    return sample == 0 ? 0 : count * 1000 / (4 * static_cast<int>(sample));
}

} // namespace forge
