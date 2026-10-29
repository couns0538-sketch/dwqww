// Search module: R7 J3 node-exact speed options (forge/search_options.hpp), all default OFF.
// Compiled as part of src/search.cpp (included exactly once, right after tt.inc).
//
// R7TtExclusive: TranspositionTable::probe_exclusive / store_exclusive are probe() / store() (tt.inc) without
// lock_stripe(). A one-worker search with TTAccess::Exclusive holds the table's ExclusiveLease for its whole
// run, so lock_stripe() only ever returns a deferred lock for it; but it first calls has_exclusive_access(), which
// reads the thread_local lease chain (an __emutls_get_address call per probe and per store in the MinGW build).
// Every other accessor still goes through lock_stripe() and waits at the gate while the lease is held. The
// functions live in .text.forge_r7, so the default .text keeps its layout except at the call sites below.

#define FORGE_R7_TEXT __attribute__((section(".text.forge_r7")))

// Search-side dispatch (main search and quiescence): the twins only while this one-worker search holds the lease.
#define FORGE_TT_PROBE(key) (shared_.r7_tt_exclusive ? shared_.tt.probe_exclusive(key) : shared_.tt.probe(key))
#define FORGE_TT_STORE(...)                                                                                         \
    do {                                                                                                            \
        if (shared_.r7_tt_exclusive) shared_.tt.store_exclusive(__VA_ARGS__);                                       \
        else shared_.tt.store(__VA_ARGS__);                                                                         \
    } while (false)

namespace forge {

FORGE_R7_TEXT TTProbe TranspositionTable::probe_exclusive(std::uint64_t key) const {
    assert(has_exclusive_access());
    if (lockless_) [[unlikely]] return probe_lockless(key);
    TTCluster& cluster = cluster_for(key);
    const std::size_t index = static_cast<std::size_t>(&cluster - clusters_.get());
    auto snapshot = [&](const TTEntry& entry, bool hit) {
#ifdef FORGE_PROF
        prof::count(prof::Counter::TtProbes);
        prof::count(hit ? prof::Counter::TtHits : prof::Counter::TtMisses);
#endif
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

FORGE_R7_TEXT void TranspositionTable::store_exclusive(const TTProbe& probe, std::uint64_t key, int score, int eval,
                                                       Move move, int depth, Bound bound, bool pv,
                                                       std::uint16_t halfmove_clock) {
    assert(has_exclusive_access());
    if (lockless_) [[unlikely]] return store_lockless(probe, key, score, eval, move, depth, bound, pv, halfmove_clock);
    if (probe.owner_ != this || probe.epoch_ != epoch_ || probe.key_ != key ||
        probe.cluster_ >= cluster_count_ || probe.slot_ >= 4) return;
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

} // namespace forge
